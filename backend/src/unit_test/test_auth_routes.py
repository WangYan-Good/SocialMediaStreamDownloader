##<<Base>>
from datetime import datetime, timedelta
import json
import unittest

##<<Extension>>
from flask import Flask, g

##<<Third-part>>
from backend.src.auth.errors import AuthUnavailable
from backend.src.auth.service import AuthenticationService
from backend.src.unit_test.test_auth_service import FakeRepository
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


def build(repository=None, *, unavailable=None, cookie_secure=False):
  repository = repository if repository is not None else FakeRepository()
  service = AuthenticationService(
    repository, session_ttl_seconds=3600, clock=lambda: NOW
  )
  runtime = FakeRuntime(service=service, unavailable=unavailable, cookie_secure=cookie_secure)
  app = Flask(__name__)
  app.register_blueprint(build_auth_blueprint(runtime=runtime))
  return app, repository, service


def body_of(response):
  return json.loads(response.get_data(as_text=True))


def cookie_header(response):
  return response.headers.get("Set-Cookie", "")


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
    repository.users[1]["is_active"] = False

    response = app.test_client().post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )

    self.assertEqual(401, response.status_code)

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

    response = client.post("/api/auth/logout")

    self.assertEqual(200, response.status_code)
    self.assertEqual(0, len(repository.sessions))

  def test_the_revoked_token_stops_working_immediately(self):
    app, _, _ = with_account()
    client = app.test_client()
    client.post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )
    client.post("/api/auth/logout")

    self.assertEqual(401, client.get("/api/auth/me").status_code)

  def test_it_clears_the_cookie(self):
    app, _, _ = with_account()
    client = app.test_client()
    client.post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )

    response = client.post("/api/auth/logout")

    header = cookie_header(response)
    self.assertIn(SESSION_COOKIE_NAME, header)
    self.assertTrue("Expires=" in header or "Max-Age=0" in header)

  def test_signing_out_twice_is_still_fine(self):
    app, _, _ = with_account()
    client = app.test_client()
    client.post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )
    client.post("/api/auth/logout")

    self.assertEqual(200, client.post("/api/auth/logout").status_code)

  def test_signing_out_without_ever_signing_in_is_fine(self):
    app, _, _ = with_account()

    self.assertEqual(200, app.test_client().post("/api/auth/logout").status_code)


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
  def test_the_signed_in_user_is_available_to_later_code(self):
    ##
    ## What Phase 7 will read.  Resolving the cookie once per request and
    ## putting the answer on ``g`` means ownership checks will not each have to
    ## re-parse and re-hash it.
    ##
    app, _, service = with_account()
    service_holder = {}

    @app.route("/probe")
    def probe():
      service_holder["user"] = getattr(g, "current_user", None)
      return "ok"

    client = app.test_client()
    client.post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct horse battery"},
    )
    client.get("/probe")

    self.assertIsNotNone(service_holder["user"])
    self.assertEqual("alice", service_holder["user"].username)

  def test_an_anonymous_request_carries_nobody_rather_than_failing(self):
    ##
    ## Identity is established, not enforced.  An unauthenticated request still
    ## reaches its route - this phase adds no authorization at all.
    ##
    app, _, _ = with_account()
    seen = {}

    @app.route("/probe")
    def probe():
      seen["user"] = getattr(g, "current_user", None)
      return "ok"

    response = app.test_client().get("/probe")

    self.assertEqual(200, response.status_code)
    self.assertIsNone(seen["user"])


if __name__ == "__main__":
  unittest.main()
