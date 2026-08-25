import unittest

from flask import Flask, g

from backend.src.auth.context import RequestAuthContext
from backend.src.auth.roles import ROLE_ADMIN, ROLE_USER
from backend.src.auth.service import AuthenticatedUser
from backend.src.unit_test.auth_context import TEST_CSRF_PROOF
from backend.src.web.history_routes import build_history_blueprint
from backend.src.web.library_routes import LibraryUnavailable, build_library_blueprint
from backend.src.web.owner_routes import build_owner_blueprint
from backend.src.web.person_routes import PersonRuntime, build_person_blueprint
from backend.src.web.system_routes import build_system_blueprint


USER = AuthenticatedUser(71, "alice", ROLE_USER)
ADMIN = AuthenticatedUser(72, "operator", ROLE_ADMIN)


class UnavailableLibraryRuntime:
  def page_size_limit(self):
    return 100

  def query(self):
    raise LibraryUnavailable("数据库暂时不可用")


class RefusingTable:
  def __getattr__(self, name):
    def refuse(*args, **kwargs):
      raise RuntimeError("fixture route reached: {}".format(name))
    return refuse


ADMIN_READS = (
  "/api/history/owners",
  "/api/history/owners/owner-1/sessions",
  "/api/live/probe/missing",
  "/api/owner",
  "/api/owner/posts",
  "/api/person",
  "/api/person/1/detail",
  "/api/person/1/works",
  "/api/person/accounts",
  "/api/library/lives",
  "/api/system/status",
)

ADMIN_MUTATIONS = (
  ("PATCH", "/api/history/owners/owner-1/preference"),
  ("POST", "/api/live/probe"),
  ("POST", "/api/owner/download"),
  ("POST", "/api/person"),
  ("PATCH", "/api/person/1"),
  ("DELETE", "/api/person/1"),
  ("POST", "/api/person/account"),
  ("POST", "/api/person/account/by-link"),
  ("POST", "/api/person/assignment"),
  ("POST", "/api/person/inspect"),
  ("DELETE", "/api/person/account"),
  ("POST", "/api/person/collaboration"),
  ("DELETE", "/api/person/collaboration"),
)


def protected_app():
  app = Flask(__name__)
  app.config["TESTING"] = True
  app.config["principal"] = "anonymous"

  @app.before_request
  def select_principal():
    principal = app.config["principal"]
    if principal == "user":
      g.auth_context = RequestAuthContext.authenticated(
        USER, csrf_expected=TEST_CSRF_PROOF
      )
    elif principal == "admin":
      g.auth_context = RequestAuthContext.authenticated(
        ADMIN, csrf_expected=TEST_CSRF_PROOF
      )
    elif principal == "unavailable":
      g.auth_context = RequestAuthContext.unavailable(
        csrf_expected=TEST_CSRF_PROOF
      )
    else:
      g.auth_context = RequestAuthContext.anonymous()

  app.register_blueprint(build_history_blueprint())
  app.register_blueprint(build_owner_blueprint())
  app.register_blueprint(
    build_person_blueprint(PersonRuntime(table_factory=RefusingTable))
  )
  app.register_blueprint(
    build_library_blueprint(runtime=UnavailableLibraryRuntime())
  )
  app.register_blueprint(build_system_blueprint())
  return app


class AdminOnlyEndpointSweepTest(unittest.TestCase):
  def setUp(self):
    self.app = protected_app()
    self.client = self.app.test_client()

  def request(self, method, path, *, csrf=False):
    headers = {"X-CSRF-Token": TEST_CSRF_PROOF} if csrf else None
    return self.client.open(path, method=method, headers=headers)

  def test_every_admin_read_refuses_anonymous_and_user(self):
    for principal, expected in (("anonymous", 401), ("user", 403)):
      self.app.config["principal"] = principal
      for path in ADMIN_READS:
        with self.subTest(principal=principal, path=path):
          response = self.request("GET", path)
          self.assertEqual(expected, response.status_code)
          if expected == 403:
            self.assertEqual("forbidden", response.get_json()["kind"])

  def test_every_admin_mutation_checks_role_before_csrf(self):
    for principal, expected in (("anonymous", 401), ("user", 403)):
      self.app.config["principal"] = principal
      for method, path in ADMIN_MUTATIONS:
        with self.subTest(principal=principal, method=method, path=path):
          self.assertEqual(expected, self.request(method, path).status_code)

  def test_every_admin_mutation_requires_csrf(self):
    self.app.config["principal"] = "admin"
    for method, path in ADMIN_MUTATIONS:
      with self.subTest(method=method, path=path):
        response = self.request(method, path)
        self.assertEqual(403, response.status_code)
        self.assertEqual("csrf_invalid", response.get_json()["kind"])

  def test_admin_with_valid_proof_reaches_each_route(self):
    self.app.config["principal"] = "admin"
    for path in ADMIN_READS:
      with self.subTest(path=path):
        self.assertNotIn(self.request("GET", path).status_code, {401, 403})
    for method, path in ADMIN_MUTATIONS:
      with self.subTest(method=method, path=path):
        self.assertNotIn(
          self.request(method, path, csrf=True).status_code,
          {401, 403},
        )

  def test_auth_unavailable_fails_closed_before_business_logic(self):
    self.app.config["principal"] = "unavailable"
    for path in ADMIN_READS:
      with self.subTest(path=path):
        self.assertEqual(503, self.request("GET", path).status_code)
    for method, path in ADMIN_MUTATIONS:
      with self.subTest(method=method, path=path):
        self.assertEqual(503, self.request(method, path).status_code)


if __name__ == "__main__":
  unittest.main()
