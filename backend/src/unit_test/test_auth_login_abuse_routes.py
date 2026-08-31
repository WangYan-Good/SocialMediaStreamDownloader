import json
from io import BytesIO
import threading
import unittest

from flask import Flask, jsonify
from werkzeug.test import create_environ

from backend.src.auth.credentials import MAX_PASSWORD_LENGTH, MAX_USERNAME_LENGTH
from backend.src.auth.errors import AuthUnavailable, InvalidCredentials
from backend.src.auth.login_abuse import (
  LOGIN_GLOBAL_ATTEMPTS_PER_WINDOW,
  LOGIN_MAX_REQUEST_BYTES,
  LOGIN_PEER_ATTEMPTS_PER_WINDOW,
  LoginAbuseGuard,
  LoginAttemptOutcome,
)
from backend.src.auth.service import AuthenticatedUser, IssuedSession
from backend.src.web.auth_routes import (
  CSRF_COOKIE_NAME,
  SESSION_COOKIE_NAME,
  build_auth_blueprint,
)


class FakeService:
  def __init__(self):
    self.authenticate_calls = []
    self.create_session_calls = []
    self.outcome = "success"
    self.resolved_user = None

  def authenticate(self, username, password):
    self.authenticate_calls.append((username, password))
    if self.outcome == "invalid":
      raise InvalidCredentials("private invalid reason")
    if self.outcome == "unavailable":
      raise AuthUnavailable("private database reason")
    if self.outcome == "unexpected":
      raise RuntimeError("private unexpected reason")
    return AuthenticatedUser(user_id=1, username="alice", role="user")

  def create_session(self, user_id):
    self.create_session_calls.append(user_id)
    return IssuedSession(token="opaque-session-token", expires_at=None)

  def resolve_session(self, unused_token):
    return self.resolved_user


class FakeRuntime:
  def __init__(self, service):
    self._service = service

  def service(self):
    return self._service

  def cookie_secure(self):
    return False

  def session_ttl_seconds(self):
    return 3600


def build(service=None, guard=None):
  selected_service = service or FakeService()
  selected_guard = guard or LoginAbuseGuard()
  app = Flask(__name__)
  app.register_blueprint(
    build_auth_blueprint(
      runtime=FakeRuntime(selected_service),
      abuse_guard=selected_guard,
    )
  )

  @app.get("/harmless")
  def harmless():
    return jsonify({"status": "success"})

  return app, selected_service, selected_guard


def login(client, username="alice", password="correct horse battery", **kwargs):
  return client.post(
    "/api/auth/login",
    json={"username": username, "password": password},
    **kwargs,
  )


def payload(response):
  return json.loads(response.get_data(as_text=True))


class TestLoginInputBounds(unittest.TestCase):
  def test_request_limit_is_exactly_4096_bytes(self):
    self.assertEqual(4096, LOGIN_MAX_REQUEST_BYTES)

  def test_declared_oversized_body_is_json_413_before_authentication(self):
    app, service, _ = build()

    response = app.test_client().post(
      "/api/auth/login",
      data=b"{" + (b"x" * LOGIN_MAX_REQUEST_BYTES) + b"}",
      content_type="application/json",
    )

    self.assertEqual(413, response.status_code)
    self.assertEqual(413, payload(response)["code"])
    self.assertEqual([], service.authenticate_calls)

  def test_exactly_4096_bytes_remains_inside_the_route_limit(self):
    app, service, _ = build()
    compact = json.dumps(
      {"username": "alice", "password": "correct horse battery"},
      separators=(",", ":"),
    ).encode()
    body = compact + (b" " * (LOGIN_MAX_REQUEST_BYTES - len(compact)))

    response = app.test_client().post(
      "/api/auth/login",
      data=body,
      content_type="application/json",
    )

    self.assertEqual(200, response.status_code)
    self.assertEqual(1, len(service.authenticate_calls))

  def test_streamed_oversized_body_without_content_length_is_413(self):
    app, service, _ = build()
    body = json.dumps({
      "username": "alice",
      "password": "x" * LOGIN_MAX_REQUEST_BYTES,
    }).encode()

    environ = create_environ(
      path="/api/auth/login",
      method="POST",
      input_stream=BytesIO(body),
      content_type="application/json",
    )
    environ.pop("CONTENT_LENGTH", None)
    environ["wsgi.input_terminated"] = True

    response = app.test_client().open(environ)

    self.assertEqual(413, response.status_code)
    self.assertEqual([], service.authenticate_calls)

  def test_malformed_and_wrongly_typed_fields_remain_400(self):
    app, service, _ = build()
    client = app.test_client()

    responses = [
      client.post("/api/auth/login", data="not-json", content_type="application/json"),
      client.post("/api/auth/login", json={"username": 7, "password": "valid"}),
      client.post("/api/auth/login", json={"username": "alice", "password": None}),
      client.post("/api/auth/login", json={"username": "", "password": "valid"}),
    ]

    self.assertEqual([400, 400, 400, 400], [one.status_code for one in responses])
    self.assertEqual([], service.authenticate_calls)

  def test_oversized_username_is_generic_401_without_authentication(self):
    app, service, _ = build()

    response = login(app.test_client(), username="u" * (MAX_USERNAME_LENGTH + 1))

    self.assertEqual(401, response.status_code)
    self.assertEqual("用户名或密码错误", payload(response)["message"])
    self.assertEqual([], service.authenticate_calls)

  def test_oversized_password_is_generic_401_without_authentication(self):
    app, service, _ = build()

    response = login(
      app.test_client(),
      password="p" * (MAX_PASSWORD_LENGTH + 1),
    )

    self.assertEqual(401, response.status_code)
    self.assertEqual("用户名或密码错误", payload(response)["message"])
    self.assertEqual([], service.authenticate_calls)


class TestLoginRouteAbuseGuard(unittest.TestCase):
  def assert_rate_limited(self, response):
    self.assertEqual(429, response.status_code)
    self.assertEqual(
      {
        "status": "error",
        "code": 429,
        "message": "登录尝试过于频繁，请稍后重试",
        "kind": "rate_limited",
      },
      payload(response),
    )
    self.assertGreaterEqual(int(response.headers["Retry-After"]), 1)
    self.assertNotIn("reason", response.get_data(as_text=True).lower())
    self.assertEqual([], response.headers.getlist("Set-Cookie"))

  def test_peer_identity_ignores_spoofed_forwarding_headers(self):
    app, service, _ = build()
    client = app.test_client()
    for index in range(LOGIN_PEER_ATTEMPTS_PER_WINDOW):
      response = login(
        client,
        username=f"user-{index}",
        headers={"X-Forwarded-For": f"203.0.113.{index}"},
      )
      self.assertEqual(200, response.status_code)

    refused = login(
      client,
      username="overflow",
      headers={"X-Forwarded-For": "198.51.100.200", "X-Real-IP": "192.0.2.9"},
    )

    self.assert_rate_limited(refused)
    self.assertEqual(LOGIN_PEER_ATTEMPTS_PER_WINDOW, len(service.authenticate_calls))

  def test_global_bound_refuses_without_service_or_session_work(self):
    app, service, _ = build()
    for index in range(LOGIN_GLOBAL_ATTEMPTS_PER_WINDOW):
      response = login(
        app.test_client(),
        username=f"user-{index}",
        environ_base={"REMOTE_ADDR": f"10.0.0.{index}"},
      )
      self.assertEqual(200, response.status_code)

    refused = login(
      app.test_client(),
      username="overflow",
      environ_base={"REMOTE_ADDR": "10.1.1.1"},
    )

    self.assert_rate_limited(refused)
    self.assertEqual(LOGIN_GLOBAL_ATTEMPTS_PER_WINDOW, len(service.authenticate_calls))
    self.assertEqual(LOGIN_GLOBAL_ATTEMPTS_PER_WINDOW, len(service.create_session_calls))

  def test_third_invalid_credential_starts_username_backoff(self):
    service = FakeService()
    service.outcome = "invalid"
    app, _, _ = build(service=service)
    client = app.test_client()

    self.assertEqual(401, login(client).status_code)
    self.assertEqual(401, login(client).status_code)
    self.assertEqual(401, login(client).status_code)
    refused = login(client)

    self.assert_rate_limited(refused)
    self.assertEqual(3, len(service.authenticate_calls))
    self.assertEqual([], service.create_session_calls)

  def test_unavailable_is_503_without_username_failure_penalty(self):
    service = FakeService()
    service.outcome = "unavailable"
    app, _, guard = build(service=service)
    client = app.test_client()

    responses = [login(client) for _ in range(4)]

    self.assertEqual([503, 503, 503, 503], [one.status_code for one in responses])
    self.assertEqual(0, guard.inflight)

  def test_unexpected_error_releases_the_expensive_slot(self):
    service = FakeService()
    service.outcome = "unexpected"
    app, _, guard = build(service=service)
    app.testing = False

    first = login(app.test_client())
    second = login(app.test_client(), username="bob")

    self.assertEqual(500, first.status_code)
    self.assertEqual(500, second.status_code)
    self.assertEqual(0, guard.inflight)

  def test_rate_limited_known_and_unknown_credentials_are_identical(self):
    app, service, _ = build()
    for index in range(LOGIN_GLOBAL_ATTEMPTS_PER_WINDOW):
      response = login(
        app.test_client(),
        username=f"fill-{index}",
        environ_base={"REMOTE_ADDR": f"10.0.0.{index}"},
      )
      self.assertEqual(200, response.status_code)
    before = len(service.authenticate_calls)

    known = login(
      app.test_client(),
      username="alice",
      password="wrong",
      environ_base={"REMOTE_ADDR": "10.2.0.1"},
    )
    unknown = login(
      app.test_client(),
      username="unknown",
      password="wrong",
      environ_base={"REMOTE_ADDR": "10.2.0.2"},
    )

    self.assertEqual(payload(known), payload(unknown))
    self.assertEqual(known.headers["Retry-After"], unknown.headers["Retry-After"])
    self.assertEqual(before, len(service.authenticate_calls))

  def test_429_never_creates_a_session_or_either_auth_cookie(self):
    service = FakeService()
    guard = LoginAbuseGuard()
    app, _, _ = build(service=service, guard=guard)
    for index in range(LOGIN_GLOBAL_ATTEMPTS_PER_WINDOW):
      decision = guard.begin(f"peer-{index}", f"user-{index}")
      self.assertTrue(decision.allowed)
      guard.finish(decision.ticket, LoginAttemptOutcome.NEUTRAL)
    client = app.test_client()
    service.resolved_user = AuthenticatedUser(1, "alice", "user")
    client.set_cookie(SESSION_COOKIE_NAME, "existing-session")
    before = len(service.create_session_calls)

    response = login(client)

    self.assert_rate_limited(response)
    self.assertEqual(before, len(service.create_session_calls))
    self.assertNotIn(SESSION_COOKIE_NAME, response.headers.get("Set-Cookie", ""))
    self.assertNotIn(CSRF_COOKIE_NAME, response.headers.get("Set-Cookie", ""))


class BlockingService(FakeService):
  def __init__(self):
    super().__init__()
    self.entered = threading.Barrier(3)
    self.release = threading.Event()

  def authenticate(self, username, password):
    self.authenticate_calls.append((username, password))
    if len(self.authenticate_calls) <= 2:
      self.entered.wait(timeout=5)
      self.release.wait(timeout=5)
    return AuthenticatedUser(user_id=1, username=username, role="user")


class TestLoginConcurrencyIntegration(unittest.TestCase):
  def test_two_expensive_calls_do_not_block_unrelated_route_and_third_is_fast_429(self):
    service = BlockingService()
    app, _, guard = build(service=service)
    responses = []

    def submit(username):
      responses.append(login(app.test_client(), username=username))

    first = threading.Thread(target=submit, args=("first",))
    second = threading.Thread(target=submit, args=("second",))
    first.start()
    second.start()
    service.entered.wait(timeout=5)

    third = login(app.test_client(), username="third")
    harmless = app.test_client().get("/harmless")

    self.assertEqual(429, third.status_code)
    self.assertEqual(200, harmless.status_code)
    self.assertEqual(2, len(service.authenticate_calls))
    service.release.set()
    first.join(timeout=5)
    second.join(timeout=5)
    self.assertEqual([200, 200], sorted(one.status_code for one in responses))
    self.assertEqual(0, guard.inflight)

    next_login = login(app.test_client(), username="next")
    self.assertEqual(200, next_login.status_code)


if __name__ == "__main__":
  unittest.main()
