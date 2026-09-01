##<<Base>>
from datetime import datetime, timedelta
import hashlib
import hmac
import json
import unittest
from unittest.mock import patch

##<<Extension>>
from flask import Flask, g, jsonify

##<<Third-part>>
from backend.src.auth.errors import AuthUnavailable
from backend.src.auth.login_abuse import LoginAbuseGuard
from backend.src.auth.roles import ROLE_ADMIN, ROLE_USER
from backend.src.auth.service import AuthenticationService
from backend.src.unit_test.test_auth_service import FakeRepository
from backend.src.web import auth_routes
from backend.src.web.auth_routes import (
  SESSION_COOKIE_NAME,
  AuthRuntime,
  build_auth_blueprint,
)


NOW = datetime(2026, 8, 24, 12, 0, 0)


class FakeRuntime:
  """Stands in for whatever assembles the service against a real database."""

  def __init__(self, service=None, unavailable=None, cookie_secure=False, ttl=3600):
    self._service = service
    self._unavailable = unavailable
    self._cookie_secure = cookie_secure
    self._ttl = ttl

  def service(self):
    if self._unavailable is not None:
      raise self._unavailable
    return self._service

  def cookie_secure(self):
    return self._cookie_secure

  def session_ttl_seconds(self):
    return self._ttl


class SequencedRuntime(FakeRuntime):
  """Return or raise one service outcome per request-bound lookup."""

  def __init__(self, outcomes, *, cookie_secure=False, ttl=3600):
    super().__init__(cookie_secure=cookie_secure, ttl=ttl)
    self._outcomes = iter(outcomes)

  def service(self):
    outcome = next(self._outcomes)
    if isinstance(outcome, BaseException):
      raise outcome
    return outcome


def build(
  repository=None,
  *,
  unavailable=None,
  cookie_secure=False,
  runtime=None,
):
  repository = repository if repository is not None else FakeRepository()
  service = AuthenticationService(
    repository, session_ttl_seconds=3600, clock=lambda: NOW
  )
  runtime = runtime or FakeRuntime(
    service=service,
    unavailable=unavailable,
    cookie_secure=cookie_secure,
  )
  app = Flask(__name__)
  app.register_blueprint(
    build_auth_blueprint(runtime=runtime, abuse_guard=LoginAbuseGuard())
  )
  return app, repository, service


def body_of(response):
  return json.loads(response.get_data(as_text=True))


def cookie_header(response):
  return response.headers.get("Set-Cookie", "")


def cookie_headers(response):
  return response.headers.getlist("Set-Cookie")


def auth_cookie_headers(response):
  prefixes = (f"{SESSION_COOKIE_NAME}=", "smsd_csrf=")
  return [
    header for header in cookie_headers(response) if header.startswith(prefixes)
  ]


def named_cookie_header(response, name):
  prefix = f"{name}="
  return next(
    (header for header in cookie_headers(response) if header.startswith(prefix)),
    "",
  )


def cookie_value(response, name):
  header = named_cookie_header(response, name)
  return header.split(f"{name}=", 1)[1].split(";", 1)[0] if header else None


def csrf_for(token):
  return hmac.new(
    token.encode("utf-8"),
    b"smsd-csrf-v1",
    hashlib.sha256,
  ).hexdigest()


def csrf_header(client):
  cookie = client.get_cookie("smsd_csrf")
  if cookie is not None:
    return {"X-CSRF-Token": cookie.value}
  session = client.get_cookie(SESSION_COOKIE_NAME)
  return {"X-CSRF-Token": csrf_for(session.value)}


def with_account(cookie_secure=False):
  app, repository, service = build(cookie_secure=cookie_secure)
  service.create_user("alice", "correct horse battery")
  return app, repository, service


class TestLogin(unittest.TestCase):
  def test_the_right_credentials_sign_somebody_in(self):
    app, _, _ = with_account()

    response = app.test_client().post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )

    self.assertEqual(200, response.status_code)
    payload = body_of(response)
    self.assertEqual("success", payload["status"])
    self.assertEqual("alice", payload["data"]["user"]["username"])
    self.assertEqual(1, payload["data"]["user"]["user_id"])
    self.assertEqual(ROLE_USER, payload["data"]["user"]["role"])

  def test_the_response_never_carries_the_hash_or_the_token(self):
    ##
    ## The two things that must never leave the server in a body: the stored
    ## hash, and the session token - which belongs in a Set-Cookie header the
    ## page's own JavaScript cannot read.
    ##
    app, repository, _ = with_account()

    response = app.test_client().post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )

    text = response.get_data(as_text=True)
    self.assertNotIn("password", text)
    self.assertNotIn("scrypt", text)
    for row in repository.sessions.values():
      self.assertNotIn(row["token_hash"], text)

  def test_a_wrong_password_and_an_unknown_account_look_identical(self):
    ##
    ## Same status, same body.  Any difference here is an oracle for which
    ## usernames exist.
    ##
    app, _, _ = with_account()
    client = app.test_client()

    wrong = client.post(
      "/api/auth/login", json={"username": "alice", "password": "not the password"}
    )
    unknown = client.post(
      "/api/auth/login", json={"username": "nobody", "password": "not the password"}
    )

    self.assertEqual(401, wrong.status_code)
    self.assertEqual(401, unknown.status_code)
    self.assertEqual(body_of(wrong), body_of(unknown))

  def test_a_refusal_names_neither_the_field_nor_the_reason(self):
    app, _, _ = with_account()

    response = app.test_client().post(
      "/api/auth/login", json={"username": "alice", "password": "not the password"}
    )

    text = response.get_data(as_text=True)
    for leak in ("user_not_found", "wrong_password", "no such user", "disabled"):
      self.assertNotIn(leak, text)

  def test_a_disabled_account_is_refused_like_any_other(self):
    app, repository, _ = with_account()
    client = app.test_client()
    wrong = client.post(
      "/api/auth/login",
      json={"username": "alice", "password": "not the password"},
    )
    repository.users[1]["is_active"] = False

    response = client.post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )

    self.assertEqual(401, response.status_code)
    self.assertEqual(body_of(wrong), body_of(response))

  def test_a_failed_login_sets_no_cookie(self):
    app, _, _ = with_account()

    response = app.test_client().post(
      "/api/auth/login", json={"username": "alice", "password": "not the password"}
    )

    self.assertNotIn(SESSION_COOKIE_NAME, cookie_header(response))

  def test_a_missing_body_is_a_bad_request_rather_than_a_crash(self):
    app, _, _ = with_account()

    for payload in ({}, {"username": "alice"}, {"password": "x"}):
      response = app.test_client().post("/api/auth/login", json=payload)
      self.assertEqual(400, response.status_code)

  def test_a_database_that_cannot_answer_is_not_a_wrong_password(self):
    ##
    ## 503, not 401.  Telling somebody their password is wrong when the
    ## database is simply down sends them to reset a password that was fine.
    ##
    app, _, _ = build(FakeRepository(unavailable=True))

    response = app.test_client().post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )

    self.assertEqual(503, response.status_code)
    self.assertNotIn("密码错误", response.get_data(as_text=True))

  def test_a_schema_behind_the_code_is_also_unavailable(self):
    app, _, _ = build(unavailable=AuthUnavailable("schema state is behind"))

    response = app.test_client().post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )

    self.assertEqual(503, response.status_code)

  def test_an_internal_reason_never_reaches_the_response(self):
    app, _, _ = build(
      unavailable=AuthUnavailable("pymysql OperationalError 2003 connect refused")
    )

    response = app.test_client().post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )

    text = response.get_data(as_text=True)
    for internal in ("pymysql", "OperationalError", "2003", "Traceback"):
      self.assertNotIn(internal, text)


class TestTheSessionCookie(unittest.TestCase):
  def response(self, cookie_secure=False):
    app, _, _ = with_account(cookie_secure=cookie_secure)
    return app.test_client().post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )

  def test_it_is_set_on_a_successful_login(self):
    self.assertIn(SESSION_COOKIE_NAME, cookie_header(self.response()))

  def test_the_page_script_cannot_read_it(self):
    ##
    ## HttpOnly is what makes an XSS on this page unable to walk off with the
    ## session.  It is the reason the token is in a cookie rather than in a
    ## body the SPA would have to store somewhere.
    ##
    self.assertIn("HttpOnly", cookie_header(self.response()))

  def test_it_is_not_sent_on_cross_site_requests(self):
    ##
    ## SameSite=Strict.  With cookie authentication this is the first line
    ## against CSRF - another origin can still cause a request, but the browser
    ## will not attach this cookie to it.
    ##
    self.assertIn("SameSite=Strict", cookie_header(self.response()))

  def test_it_covers_the_whole_application(self):
    self.assertIn("Path=/", cookie_header(self.response()))

  def test_the_secure_flag_follows_configuration(self):
    ##
    ## Not hard-coded either way.  Secure on plain HTTP means the browser
    ## silently discards the cookie and login appears to do nothing; absent in
    ## production means the session can travel in clear text.
    ##
    self.assertNotIn("Secure", cookie_header(self.response(cookie_secure=False)))
    self.assertIn("Secure", cookie_header(self.response(cookie_secure=True)))

  def test_the_raw_token_appears_only_in_the_cookie(self):
    app, repository, _ = with_account()

    response = app.test_client().post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )

    header = cookie_header(response)
    token = header.split(f"{SESSION_COOKIE_NAME}=")[1].split(";")[0]
    self.assertNotIn(token, response.get_data(as_text=True))
    self.assertNotIn(token, repository.sessions)


class TestTheCsrfCookie(unittest.TestCase):
  def response(self, cookie_secure=False):
    app, repository, _ = with_account(cookie_secure=cookie_secure)
    response = app.test_client().post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )
    return response, repository

  def test_login_sets_a_script_readable_csrf_cookie_beside_the_session(self):
    response, _ = self.response()

    session = named_cookie_header(response, SESSION_COOKIE_NAME)
    csrf = named_cookie_header(response, "smsd_csrf")
    self.assertTrue(session)
    self.assertTrue(csrf)
    self.assertIn("HttpOnly", session)
    self.assertNotIn("HttpOnly", csrf)

  def test_csrf_cookie_uses_the_session_cookie_policy(self):
    insecure, _ = self.response(cookie_secure=False)
    secure, _ = self.response(cookie_secure=True)

    insecure_header = named_cookie_header(insecure, "smsd_csrf")
    secure_header = named_cookie_header(secure, "smsd_csrf")
    self.assertIn("SameSite=Strict", insecure_header)
    self.assertIn("Path=/", insecure_header)
    self.assertNotIn("Secure", insecure_header)
    self.assertIn("Secure", secure_header)

  def test_csrf_is_bound_to_the_raw_session_without_exposing_it(self):
    response, repository = self.response()

    session = cookie_value(response, SESSION_COOKIE_NAME)
    csrf = cookie_value(response, "smsd_csrf")
    stored_hash = next(iter(repository.sessions))
    self.assertEqual(csrf_for(session), csrf)
    self.assertNotEqual(session, csrf)
    self.assertNotEqual(stored_hash, csrf)

  def test_each_new_session_gets_a_different_csrf_token(self):
    app, _, _ = with_account()
    first = app.test_client().post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )
    second = app.test_client().post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )

    self.assertNotEqual(
      cookie_value(first, "smsd_csrf"),
      cookie_value(second, "smsd_csrf"),
    )

  def test_an_old_valid_session_is_given_its_stable_csrf_cookie(self):
    app, _, _ = with_account()
    client = app.test_client()
    login = client.post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )
    session = cookie_value(login, SESSION_COOKIE_NAME)
    client.delete_cookie("smsd_csrf")

    first = client.get("/api/auth/me")
    expected = csrf_for(session)
    self.assertEqual(expected, cookie_value(first, "smsd_csrf"))

    client.delete_cookie("smsd_csrf")
    second = client.get("/api/auth/me")
    self.assertEqual(expected, cookie_value(second, "smsd_csrf"))

  def test_an_authenticated_response_repairs_a_wrong_csrf_cookie(self):
    app, _, _ = with_account()
    client = app.test_client()
    login = client.post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )
    expected = csrf_for(cookie_value(login, SESSION_COOKIE_NAME))
    client.set_cookie("smsd_csrf", "wrong")

    response = client.get("/api/auth/me")

    self.assertEqual(200, response.status_code)
    self.assertEqual(expected, cookie_value(response, "smsd_csrf"))

  def test_login_emits_only_the_new_session_cookie_pair(self):
    for previous_csrf in (None, "wrong"):
      with self.subTest(previous_csrf=previous_csrf):
        app, _, _ = with_account()
        client = app.test_client()
        client.post(
          "/api/auth/login",
          json={"username": "alice", "password": "correct horse battery"},
        )
        if previous_csrf is None:
          client.delete_cookie("smsd_csrf")
        else:
          client.set_cookie("smsd_csrf", previous_csrf)

        response = client.post(
          "/api/auth/login",
          json={"username": "alice", "password": "correct horse battery"},
        )

        session_headers = [
          header
          for header in cookie_headers(response)
          if header.startswith(f"{SESSION_COOKIE_NAME}=")
        ]
        csrf_headers = [
          header
          for header in cookie_headers(response)
          if header.startswith("smsd_csrf=")
        ]
        self.assertEqual(1, len(session_headers), cookie_headers(response))
        self.assertEqual(1, len(csrf_headers), cookie_headers(response))
        self.assertEqual(
          csrf_for(cookie_value(response, SESSION_COOKIE_NAME)),
          cookie_value(response, "smsd_csrf"),
        )


class TestWhoAmI(unittest.TestCase):
  def signed_in_client(self):
    app, repository, service = with_account()
    client = app.test_client()
    client.post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )
    return client, repository, service

  def test_a_signed_in_browser_is_told_who_it_is(self):
    client, _, _ = self.signed_in_client()

    response = client.get("/api/auth/me")

    self.assertEqual(200, response.status_code)
    self.assertEqual("alice", body_of(response)["data"]["user"]["username"])
    self.assertEqual(ROLE_USER, body_of(response)["data"]["user"]["role"])

  def test_role_changes_are_visible_without_replacing_the_session(self):
    client, _, service = self.signed_in_client()
    session_cookie = client.get_cookie(SESSION_COOKIE_NAME).value

    service.set_role("alice", ROLE_ADMIN)
    promoted = client.get("/api/auth/me")
    service.set_role("alice", ROLE_USER)
    demoted = client.get("/api/auth/me")

    self.assertEqual(ROLE_ADMIN, body_of(promoted)["data"]["user"]["role"])
    self.assertEqual(ROLE_USER, body_of(demoted)["data"]["user"]["role"])
    self.assertEqual(session_cookie, client.get_cookie(SESSION_COOKIE_NAME).value)

  def test_it_resolves_the_session_only_once(self):
    client, _, service = self.signed_in_client()
    calls = 0
    resolve = service.resolve_session

    def counted(token):
      nonlocal calls
      calls += 1
      return resolve(token)

    service.resolve_session = counted

    self.assertEqual(200, client.get("/api/auth/me").status_code)
    self.assertEqual(1, calls)

  def test_no_cookie_is_not_signed_in(self):
    app, _, _ = with_account()

    response = app.test_client().get("/api/auth/me")

    self.assertEqual(401, response.status_code)

  def test_an_unknown_token_is_not_signed_in(self):
    app, _, _ = with_account()
    client = app.test_client()
    client.set_cookie(SESSION_COOKIE_NAME, "a token nobody ever issued")

    self.assertEqual(401, client.get("/api/auth/me").status_code)

  def test_an_expired_session_is_not_signed_in(self):
    app, repository, service = with_account()
    client = app.test_client()
    client.post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )
    for row in repository.sessions.values():
      row["expires_at"] = NOW - timedelta(seconds=1)

    self.assertEqual(401, client.get("/api/auth/me").status_code)

  def test_disabling_an_account_ends_the_sessions_it_already_had(self):
    client, repository, _ = self.signed_in_client()
    repository.users[1]["is_active"] = False

    self.assertEqual(401, client.get("/api/auth/me").status_code)

  def test_it_never_returns_the_password_hash(self):
    client, _, _ = self.signed_in_client()

    text = client.get("/api/auth/me").get_data(as_text=True)

    self.assertNotIn("scrypt", text)
    self.assertNotIn("password", text)

  def test_a_database_outage_is_not_reported_as_signed_out(self):
    ##
    ## 503 rather than 401.  Answering "not signed in" during an outage would
    ## make every browser think it had been logged out.
    ##
    app, _, _ = build(FakeRepository(unavailable=True))
    client = app.test_client()
    client.set_cookie(SESSION_COOKIE_NAME, "anything")

    self.assertEqual(503, client.get("/api/auth/me").status_code)


class TestSigningOut(unittest.TestCase):
  def test_it_revokes_the_session_server_side(self):
    ##
    ## The point of an opaque server-side session: signing out actually ends
    ## it, rather than politely asking the browser to forget a token that would
    ## still work if kept.
    ##
    app, repository, _ = with_account()
    client = app.test_client()
    client.post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )
    self.assertEqual(1, len(repository.sessions))

    response = client.post("/api/auth/logout", headers=csrf_header(client))

    self.assertEqual(200, response.status_code)
    self.assertEqual(0, len(repository.sessions))

  def test_the_revoked_token_stops_working_immediately(self):
    app, _, _ = with_account()
    client = app.test_client()
    client.post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )
    client.post("/api/auth/logout", headers=csrf_header(client))

    self.assertEqual(401, client.get("/api/auth/me").status_code)

  def test_it_clears_the_cookie(self):
    app, _, _ = with_account()
    client = app.test_client()
    client.post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )

    response = client.post("/api/auth/logout", headers=csrf_header(client))

    for name in (SESSION_COOKIE_NAME, "smsd_csrf"):
      header = named_cookie_header(response, name)
      self.assertTrue(header)
      self.assertTrue("Expires=" in header or "Max-Age=0" in header)

  def test_logout_emits_only_one_deletion_for_each_cookie(self):
    app, _, _ = with_account()
    client = app.test_client()
    login = client.post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )
    expected = csrf_for(cookie_value(login, SESSION_COOKIE_NAME))
    client.set_cookie("smsd_csrf", "wrong")

    response = client.post(
      "/api/auth/logout",
      headers={"X-CSRF-Token": expected},
    )

    for name in (SESSION_COOKIE_NAME, "smsd_csrf"):
      matching = [
        header
        for header in cookie_headers(response)
        if header.startswith(f"{name}=")
      ]
      self.assertEqual(1, len(matching), cookie_headers(response))
      self.assertTrue("Expires=" in matching[0] or "Max-Age=0" in matching[0])

  def test_signing_out_twice_is_still_fine(self):
    app, _, _ = with_account()
    client = app.test_client()
    client.post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )
    client.post("/api/auth/logout", headers=csrf_header(client))

    self.assertEqual(200, client.post("/api/auth/logout").status_code)

  def test_signing_out_without_ever_signing_in_is_fine(self):
    app, _, _ = build(
      runtime=SequencedRuntime(
        [AssertionError("no-token logout must not request an auth service")]
      )
    )

    response = app.test_client().post("/api/auth/logout")

    self.assertEqual(200, response.status_code)
    self.assertEqual([], cookie_headers(response))

  def test_an_unknown_session_is_idempotent_without_a_second_revoke(self):
    app, _, service = with_account()
    client = app.test_client()
    client.set_cookie(SESSION_COOKIE_NAME, "unknown-session-token")

    with patch.object(service, "revoke_session", wraps=service.revoke_session) as revoke:
      response = client.post("/api/auth/logout")

    self.assertEqual(200, response.status_code)
    revoke.assert_not_called()
    for name in (SESSION_COOKIE_NAME, "smsd_csrf"):
      header = named_cookie_header(response, name)
      self.assertTrue("Expires=" in header or "Max-Age=0" in header)

  def test_revoke_false_is_still_an_idempotent_success(self):
    app, _, service = with_account()
    client = app.test_client()
    client.post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )

    with patch.object(service, "revoke_session", return_value=False):
      response = client.post("/api/auth/logout", headers=csrf_header(client))

    self.assertEqual(200, response.status_code)
    for name in (SESSION_COOKIE_NAME, "smsd_csrf"):
      header = named_cookie_header(response, name)
      self.assertTrue("Expires=" in header or "Max-Age=0" in header)

  def test_missing_csrf_does_not_revoke_or_clear_an_authenticated_session(self):
    app, repository, service = with_account()
    client = app.test_client()
    client.post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )

    with patch.object(service, "revoke_session", wraps=service.revoke_session) as revoke:
      response = client.post("/api/auth/logout")

    self.assertEqual(403, response.status_code)
    self.assertEqual("csrf_invalid", body_of(response)["kind"])
    revoke.assert_not_called()
    self.assertEqual(1, len(repository.sessions))
    self.assertFalse(named_cookie_header(response, SESSION_COOKIE_NAME))
    self.assertEqual(200, client.get("/api/auth/me").status_code)
    text = response.get_data(as_text=True)
    for secret in (
      client.get_cookie(SESSION_COOKIE_NAME).value,
      client.get_cookie("smsd_csrf").value,
    ):
      self.assertNotIn(secret, text)

  def test_wrong_or_malformed_csrf_is_safely_refused_without_revoking(self):
    for received in ("wrong", "not%a%token", "\x00"):
      with self.subTest(received=received):
        app, repository, _ = with_account()
        client = app.test_client()
        client.post(
          "/api/auth/login",
          json={"username": "alice", "password": "correct horse battery"},
        )

        response = client.post(
          "/api/auth/logout",
          headers={"X-CSRF-Token": received},
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual(1, len(repository.sessions))

  def test_validation_uses_constant_time_comparison(self):
    app, _, _ = with_account()
    client = app.test_client()
    client.post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )

    with patch("hmac.compare_digest", wraps=hmac.compare_digest) as compared:
      response = client.post("/api/auth/logout", headers=csrf_header(client))

    self.assertEqual(200, response.status_code)
    self.assertTrue(compared.called)

  def test_revoke_unavailable_returns_503_without_mutating_auth_cookies(self):
    app, repository, service = with_account()
    client = app.test_client()
    client.post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )
    session_before = client.get_cookie(SESSION_COOKIE_NAME).value
    csrf_before = client.get_cookie("smsd_csrf").value

    warnings = []

    class RecordingLogger:
      def warning(self, message):
        warnings.append(message)

    with (
      patch.object(
        service,
        "revoke_session",
        side_effect=AuthUnavailable("database-host secret detail"),
      ),
      patch.object(auth_routes, "get_logger", return_value=RecordingLogger()),
    ):
      response = client.post("/api/auth/logout", headers=csrf_header(client))

    self.assertEqual(503, response.status_code)
    self.assertEqual("logout_unavailable", body_of(response)["kind"])
    self.assertEqual(
      "退出登录暂时无法完成，请稍后重试",
      body_of(response)["message"],
    )
    self.assertEqual([], auth_cookie_headers(response))
    self.assertEqual(
      session_before, client.get_cookie(SESSION_COOKIE_NAME).value
    )
    self.assertEqual(csrf_before, client.get_cookie("smsd_csrf").value)
    self.assertEqual(1, len(repository.sessions))
    self.assertEqual(["logout revocation unavailable"], warnings)
    for forbidden in (
      session_before,
      csrf_before,
      "database-host",
      "secret detail",
    ):
      self.assertNotIn(forbidden, "\n".join(warnings))

  def test_revoke_unavailable_suppresses_after_request_csrf_repair(self):
    app, _, service = with_account()
    client = app.test_client()
    login = client.post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )
    expected_csrf = cookie_value(login, "smsd_csrf")
    session_before = client.get_cookie(SESSION_COOKIE_NAME).value
    client.delete_cookie("smsd_csrf")

    with patch.object(
      service,
      "revoke_session",
      side_effect=AuthUnavailable("database offline"),
    ):
      response = client.post(
        "/api/auth/logout",
        headers={"X-CSRF-Token": expected_csrf},
      )

    self.assertEqual(503, response.status_code)
    self.assertEqual([], auth_cookie_headers(response))
    self.assertEqual(
      session_before, client.get_cookie(SESSION_COOKIE_NAME).value
    )
    self.assertIsNone(client.get_cookie("smsd_csrf"))

  def test_unavailable_context_retries_revoke_when_storage_recovers(self):
    repository = FakeRepository()
    service = AuthenticationService(
      repository, session_ttl_seconds=3600, clock=lambda: NOW
    )
    service.create_user("alice", "correct horse battery")
    user = service.authenticate("alice", "correct horse battery")
    issued = service.create_session(user.user_id)
    runtime = SequencedRuntime(
      [AuthUnavailable("resolve unavailable"), service]
    )
    app, _, _ = build(repository, runtime=runtime)
    client = app.test_client()
    client.set_cookie(SESSION_COOKIE_NAME, issued.token)
    client.set_cookie("smsd_csrf", csrf_for(issued.token))

    response = client.post(
      "/api/auth/logout",
      headers={"X-CSRF-Token": csrf_for(issued.token)},
    )

    self.assertEqual(200, response.status_code)
    self.assertEqual({}, repository.sessions)
    self.assertIsNone(client.get_cookie(SESSION_COOKIE_NAME))
    self.assertIsNone(client.get_cookie("smsd_csrf"))

  def test_unavailable_context_preserves_cookies_when_revoke_is_still_down(self):
    token = "browser-held-session-token"
    runtime = SequencedRuntime(
      [
        AuthUnavailable("resolve unavailable"),
        AuthUnavailable("revoke unavailable"),
      ]
    )
    app, _, _ = build(runtime=runtime)
    client = app.test_client()
    client.set_cookie(SESSION_COOKIE_NAME, token)
    client.set_cookie("smsd_csrf", csrf_for(token))

    response = client.post(
      "/api/auth/logout",
      headers={"X-CSRF-Token": csrf_for(token)},
    )

    self.assertEqual(503, response.status_code)
    self.assertEqual("logout_unavailable", body_of(response)["kind"])
    self.assertEqual([], auth_cookie_headers(response))
    self.assertEqual(token, client.get_cookie(SESSION_COOKIE_NAME).value)
    self.assertEqual(csrf_for(token), client.get_cookie("smsd_csrf").value)

  def test_an_unavailable_backend_still_refuses_an_invalid_csrf_proof(self):
    app, _, _ = build(unavailable=AuthUnavailable("database offline"))
    client = app.test_client()
    client.set_cookie(SESSION_COOKIE_NAME, "browser-held-session-token")

    response = client.post(
      "/api/auth/logout",
      headers={"X-CSRF-Token": "wrong"},
    )

    self.assertEqual(403, response.status_code)
    self.assertIsNotNone(client.get_cookie(SESSION_COOKIE_NAME))
    self.assertFalse(named_cookie_header(response, SESSION_COOKIE_NAME))


class TestThereIsNoWayToSignUp(unittest.TestCase):
  def test_registration_is_not_an_endpoint(self):
    ##
    ## Deliberate.  Nothing is owned by anybody yet and no endpoint checks
    ## permissions, so a self-service account would be an account that can see
    ## everything.  Accounts are created by whoever runs the deployment.
    ##
    app, _, _ = with_account()
    client = app.test_client()

    for path in ("/api/auth/register", "/api/auth/signup", "/api/auth/users"):
      self.assertIn(client.post(path, json={}).status_code, (404, 405))


class TestRequestIdentity(unittest.TestCase):
  def context_seen_by(self, app):
    seen = {}

    @app.route("/probe")
    def probe():
      seen["context"] = getattr(g, "auth_context", None)
      return "ok"

    return seen

  def test_a_valid_session_is_explicitly_authenticated(self):
    ##
    ## What Phase 7 will read.  Resolving the cookie once per request and
    ## putting the answer on ``g`` means ownership checks will not each have to
    ## re-parse and re-hash it.
    ##
    app, _, service = with_account()
    seen = self.context_seen_by(app)

    client = app.test_client()
    client.post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )
    client.get("/probe")

    self.assertEqual("authenticated", seen["context"].status)
    self.assertEqual("alice", seen["context"].user.username)
    self.assertIsNotNone(seen["context"].csrf_expected)

  def test_no_cookie_is_explicitly_anonymous(self):
    ##
    ## Identity is established, not enforced.  An unauthenticated request still
    ## reaches its route - this phase adds no authorization at all.
    ##
    app, _, _ = with_account()
    seen = self.context_seen_by(app)

    response = app.test_client().get("/probe")

    self.assertEqual(200, response.status_code)
    self.assertEqual("anonymous", seen["context"].status)
    self.assertIsNone(seen["context"].user)
    self.assertIsNone(seen["context"].csrf_expected)

  def test_expired_revoked_and_unknown_sessions_are_anonymous(self):
    for kind in ("expired", "revoked", "unknown"):
      with self.subTest(kind=kind):
        app, repository, service = with_account()
        seen = self.context_seen_by(app)
        client = app.test_client()
        if kind == "unknown":
          client.set_cookie(SESSION_COOKIE_NAME, "unknown")
        else:
          client.post(
            "/api/auth/login",
            json={"username": "alice", "password": "correct horse battery"},
          )
          if kind == "expired":
            next(iter(repository.sessions.values()))["expires_at"] = NOW - timedelta(seconds=1)
          else:
            service.revoke_session(client.get_cookie(SESSION_COOKIE_NAME).value)

        self.assertEqual(200, client.get("/probe").status_code)
        self.assertEqual("anonymous", seen["context"].status)
        self.assertIsNone(seen["context"].user)

  def test_database_and_schema_outages_are_explicitly_unavailable(self):
    for reason in ("database offline", "schema state is behind"):
      with self.subTest(reason=reason):
        app, _, _ = build(unavailable=AuthUnavailable(reason))
        seen = self.context_seen_by(app)
        client = app.test_client()
        client.set_cookie(SESSION_COOKIE_NAME, "present-token")

        self.assertEqual(200, client.get("/probe").status_code)
        self.assertEqual("unavailable", seen["context"].status)
        self.assertIsNone(seen["context"].user)
        self.assertEqual(csrf_for("present-token"), seen["context"].csrf_expected)

  def test_authenticated_requests_resolve_at_most_once(self):
    app, _, service = with_account()
    self.context_seen_by(app)
    client = app.test_client()
    client.post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )
    calls = 0
    resolve = service.resolve_session

    def counted(token):
      nonlocal calls
      calls += 1
      return resolve(token)

    service.resolve_session = counted

    self.assertEqual(200, client.get("/probe").status_code)
    self.assertLessEqual(calls, 1)

  def test_csrf_is_not_globally_enforced_on_existing_business_mutations(self):
    app, _, _ = with_account()

    @app.post("/api/business-probe")
    def business_probe():
      return "unchanged"

    client = app.test_client()
    client.post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )

    self.assertEqual(200, client.post("/api/business-probe").status_code)


class TestRequireAuthenticated(unittest.TestCase):
  def protected_app(self, *, unavailable=None):
    app, repository, service = build(unavailable=unavailable)
    decorator = getattr(auth_routes, "require_authenticated", None)
    self.assertTrue(callable(decorator))

    @app.get("/protected")
    @decorator
    def protected():
      context = g.auth_context
      return jsonify({"username": context.user.username})

    return app, repository, service

  def test_anonymous_requests_are_401_even_with_csrf_material(self):
    app, _, _ = self.protected_app()
    client = app.test_client()
    client.set_cookie("smsd_csrf", "csrf-by-itself")

    response = client.get(
      "/protected",
      headers={"X-CSRF-Token": "csrf-by-itself"},
    )

    self.assertEqual(401, response.status_code)

  def test_authenticated_requests_receive_the_context_user(self):
    app, _, service = self.protected_app()
    service.create_user("alice", "correct horse battery")
    client = app.test_client()
    client.post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )

    response = client.get("/protected")

    self.assertEqual(200, response.status_code)
    self.assertEqual("alice", body_of(response)["username"])

  def test_unavailable_authentication_is_503_not_401(self):
    app, _, _ = self.protected_app(
      unavailable=AuthUnavailable("schema state is behind")
    )
    client = app.test_client()
    client.set_cookie(SESSION_COOKIE_NAME, "present-token")

    response = client.get("/protected")

    self.assertEqual(503, response.status_code)


class TestRoleAuthorizationHelpers(unittest.TestCase):
  def protected_app(self, decorator, *, unavailable=None):
    app, repository, service = build(unavailable=unavailable)

    @app.get("/role-probe")
    @decorator
    def role_probe():
      return jsonify({"role": g.auth_context.user.role})

    return app, repository, service

  def signed_in(self, decorator, role):
    app, _, service = self.protected_app(decorator)
    service.create_user("alice", "correct horse battery", role=role)
    client = app.test_client()
    client.post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )
    return client, service

  def test_require_admin_refuses_anonymous_with_401(self):
    app, _, _ = self.protected_app(auth_routes.require_admin)

    self.assertEqual(401, app.test_client().get("/role-probe").status_code)

  def test_require_admin_preserves_unavailable_as_503(self):
    app, _, _ = self.protected_app(
      auth_routes.require_admin,
      unavailable=AuthUnavailable("database offline"),
    )
    client = app.test_client()
    client.set_cookie(SESSION_COOKIE_NAME, "present-token")

    self.assertEqual(503, client.get("/role-probe").status_code)

  def test_require_admin_refuses_user_with_uniform_forbidden_contract(self):
    client, _ = self.signed_in(auth_routes.require_admin, ROLE_USER)

    response = client.get("/role-probe")

    self.assertEqual(403, response.status_code)
    self.assertEqual("forbidden", body_of(response)["kind"])
    self.assertEqual("没有权限执行此操作", body_of(response)["message"])

  def test_require_admin_allows_admin(self):
    client, _ = self.signed_in(auth_routes.require_admin, ROLE_ADMIN)

    self.assertEqual(200, client.get("/role-probe").status_code)

  def test_require_user_capability_allows_user_and_admin(self):
    decorator = auth_routes.require_role(ROLE_USER)
    for role in (ROLE_USER, ROLE_ADMIN):
      with self.subTest(role=role):
        client, _ = self.signed_in(decorator, role)
        self.assertEqual(200, client.get("/role-probe").status_code)

  def test_helper_consumes_context_without_resolving_again(self):
    client, service = self.signed_in(auth_routes.require_admin, ROLE_ADMIN)
    calls = 0
    resolve = service.resolve_session

    def counted(token):
      nonlocal calls
      calls += 1
      return resolve(token)

    service.resolve_session = counted

    self.assertEqual(200, client.get("/role-probe").status_code)
    self.assertEqual(1, calls)

  def test_role_changes_apply_to_the_same_session_on_the_next_request(self):
    client, service = self.signed_in(auth_routes.require_admin, ROLE_USER)

    self.assertEqual(403, client.get("/role-probe").status_code)
    service.set_role("alice", ROLE_ADMIN)
    self.assertEqual(200, client.get("/role-probe").status_code)
    service.set_role("alice", ROLE_USER)
    self.assertEqual(403, client.get("/role-probe").status_code)

  def test_a_disabled_admin_cannot_keep_using_admin_capabilities(self):
    client, service = self.signed_in(auth_routes.require_admin, ROLE_ADMIN)
    service._repository.users[1]["is_active"] = False

    self.assertEqual(401, client.get("/role-probe").status_code)

  def test_a_disabled_user_cannot_keep_using_user_capabilities(self):
    client, service = self.signed_in(
      auth_routes.require_role(ROLE_USER), ROLE_USER
    )
    service._repository.users[1]["is_active"] = False

    self.assertEqual(401, client.get("/role-probe").status_code)


if __name__ == "__main__":
  unittest.main()
