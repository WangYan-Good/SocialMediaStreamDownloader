import json
import unittest

from flask import Flask

from backend.src.database.schema_guard import GuardSnapshot, SchemaState
from backend.src.web.system_routes import (
  SYSTEM_CONFIG_KEY,
  build_system_blueprint,
  install_system_config,
)

from backend.src.unit_test.test_system_status import SECRETS, flatten


class FakeGuard:
  """Stands in for DatabaseSchemaGuard, recording how it was asked."""

  def __init__(self, state=SchemaState.READY, reason="ok", failure=None):
    self.snapshot_value = GuardSnapshot(state=state, reason=reason, checked_at=12345.6)
    self.failure = failure
    self.refresh_calls = []

  def refresh(self, force: bool = False):
    self.refresh_calls.append(force)
    if self.failure is not None:
      raise self.failure
    return self.snapshot_value


def app_with(config=None, guard=None):
  app = Flask(__name__)
  if guard is not None:
    app.extensions["smsd_schema_guard"] = guard
  if config is not None:
    install_system_config(app, config)
  app.register_blueprint(build_system_blueprint())
  return app


def body_of(response):
  return json.loads(response.data.decode("utf-8"))


class SystemStatusRouteTest(unittest.TestCase):
  def test_answers_with_the_project_envelope(self):
    app = app_with(SECRETS, FakeGuard())

    response = app.test_client().get("/api/system/status")
    payload = body_of(response)

    self.assertEqual(200, response.status_code)
    self.assertEqual("success", payload["status"])
    self.assertEqual(200, payload["code"])
    self.assertEqual({"database", "settings"}, set(payload["data"]))

  def test_no_secret_reaches_the_response(self):
    ##
    ## The whole page's reason for existing, asserted end to end rather than
    ## only against the snapshot builder.
    ##
    app = app_with(SECRETS, FakeGuard())

    response = app.test_client().get("/api/system/status")
    serialized = response.data.decode("utf-8")

    self.assertNotIn("SECRET", serialized)
    self.assertNotIn("ULTRA_SECRET", serialized)

  def test_the_settings_carry_exactly_the_designed_sections(self):
    app = app_with(SECRETS, FakeGuard())

    settings = body_of(app.test_client().get("/api/system/status"))["data"]["settings"]

    self.assertEqual(
      {"server", "logging", "download", "history", "douyin"}, set(settings)
    )
    self.assertEqual({"debug_mode"}, set(settings["server"]))

  def test_the_database_section_is_exactly_four_fields(self):
    app = app_with(SECRETS, FakeGuard())

    database = body_of(app.test_client().get("/api/system/status"))["data"]["database"]

    self.assertEqual({"enabled", "state", "write_ready", "message"}, set(database))

  def test_the_guard_is_refreshed_without_being_forced(self):
    ##
    ## The guard has its own retry window, and a schema probe is a real database
    ## round trip. Forcing it would let anybody turn a refresh button into a
    ## probe per click.
    ##
    guard = FakeGuard()
    app = app_with(SECRETS, guard)

    app.test_client().get("/api/system/status")

    self.assertEqual([False], guard.refresh_calls)


class DegradedDatabaseTest(unittest.TestCase):
  def test_an_unavailable_database_still_answers_200(self):
    ##
    ## Telling somebody the database is broken is one of the two things this
    ## endpoint is for. Answering 503 would take the page down exactly when it
    ## is the page they need.
    ##
    app = app_with(SECRETS, FakeGuard(state=SchemaState.UNAVAILABLE))

    response = app.test_client().get("/api/system/status")
    database = body_of(response)["data"]["database"]

    self.assertEqual(200, response.status_code)
    self.assertEqual("unavailable", database["state"])
    self.assertIs(False, database["write_ready"])

  def test_a_blocked_schema_still_answers_200(self):
    app = app_with(SECRETS, FakeGuard(state=SchemaState.BLOCKED))

    response = app.test_client().get("/api/system/status")

    self.assertEqual(200, response.status_code)
    self.assertEqual("blocked", body_of(response)["data"]["database"]["state"])

  def test_a_disabled_database_still_answers_200(self):
    config = dict(SECRETS)
    config["database"] = {"enable": False}
    app = app_with(config, FakeGuard(state=SchemaState.DISABLED))

    response = app.test_client().get("/api/system/status")
    database = body_of(response)["data"]["database"]

    self.assertEqual(200, response.status_code)
    self.assertIs(False, database["enabled"])
    self.assertEqual("disabled", database["state"])

  def test_a_missing_guard_is_unknown_rather_than_an_error(self):
    app = app_with(SECRETS, guard=None)

    response = app.test_client().get("/api/system/status")

    self.assertEqual(200, response.status_code)
    self.assertEqual("unknown", body_of(response)["data"]["database"]["state"])

  def test_a_guard_that_raises_is_unknown_rather_than_an_error(self):
    app = app_with(SECRETS, FakeGuard(failure=RuntimeError("probe exploded")))

    response = app.test_client().get("/api/system/status")

    self.assertEqual(200, response.status_code)
    self.assertEqual("unknown", body_of(response)["data"]["database"]["state"])

  def test_the_guards_own_reason_never_reaches_the_client(self):
    app = app_with(
      SECRETS,
      FakeGuard(
        state=SchemaState.UNAVAILABLE,
        reason="SECRET_DB_HOST=10.0.0.4 refused the connection",
      ),
    )

    serialized = app.test_client().get("/api/system/status").data.decode("utf-8")

    self.assertNotIn("SECRET_DB_HOST", serialized)
    self.assertNotIn("10.0.0.4", serialized)

  def test_the_monotonic_check_time_never_reaches_the_client(self):
    app = app_with(SECRETS, FakeGuard())

    serialized = app.test_client().get("/api/system/status").data.decode("utf-8")

    self.assertNotIn("checked_at", serialized)
    self.assertNotIn("12345", serialized)


class ReadOnlyRouteTest(unittest.TestCase):
  def test_the_status_endpoint_takes_nothing_but_GET(self):
    ##
    ## There is no mutation endpoint on this blueprint at all, deliberately: the
    ## configuration is loaded once at startup, so anything that appeared to
    ## change it here would report success while the process kept using the old
    ## values.
    ##
    client = app_with(SECRETS, FakeGuard()).test_client()

    for method in ("post", "patch", "put", "delete"):
      response = getattr(client, method)("/api/system/status")
      self.assertEqual(405, response.status_code, method)

  def test_the_blueprint_registers_only_the_status_route(self):
    app = app_with(SECRETS, FakeGuard())

    system_rules = [
      str(rule) for rule in app.url_map.iter_rules() if str(rule).startswith("/api/system")
    ]

    self.assertEqual(["/api/system/status"], system_rules)


class AppLocalConfigTest(unittest.TestCase):
  def test_two_applications_report_their_own_configuration(self):
    ##
    ## The architectural invariant. Reading a process global here would make one
    ## application report the other's settings, and a test app report the real
    ## server's.
    ##
    quiet = app_with(
      {"server": {"debug_mode": False}, "download": {"test_mode": False}},
      FakeGuard(),
    )
    loud = app_with(
      {"server": {"debug_mode": True}, "download": {"test_mode": True}},
      FakeGuard(),
    )

    quiet_settings = body_of(quiet.test_client().get("/api/system/status"))["data"]["settings"]
    loud_settings = body_of(loud.test_client().get("/api/system/status"))["data"]["settings"]

    self.assertIs(False, quiet_settings["server"]["debug_mode"])
    self.assertIs(False, quiet_settings["download"]["test_mode"])
    self.assertIs(True, loud_settings["server"]["debug_mode"])
    self.assertIs(True, loud_settings["download"]["test_mode"])

  def test_only_the_safe_snapshot_is_stored_on_the_application(self):
    ##
    ## Not the configuration itself. A route cannot leak what its application
    ## never held.
    ##
    app = app_with(SECRETS, FakeGuard())

    stored = app.extensions[SYSTEM_CONFIG_KEY]

    self.assertNotIn("SECRET", flatten(stored))
    self.assertEqual(
      {"server", "logging", "download", "history", "douyin"}, set(stored)
    )

  def test_editing_the_configuration_afterwards_changes_nothing(self):
    source = {"server": {"debug_mode": False}}
    app = app_with(source, FakeGuard())

    source["server"]["debug_mode"] = True

    settings = body_of(app.test_client().get("/api/system/status"))["data"]["settings"]
    self.assertIs(False, settings["server"]["debug_mode"])

  def test_the_snapshot_is_detached_from_the_configuration_it_was_built_from(self):
    ##
    ## Not "does the whitelist work" - that is asserted elsewhere - but "is what
    ## the application holds its own object". A snapshot that shared a nested
    ## mapping with the configuration would keep passing every secret test while
    ## quietly tracking whatever the configuration became afterwards, including
    ## keys added long after anybody reviewed this code.
    ##
    config = {
      "server": {"debug_mode": False},
      "log": {"log_enable": True, "log_level": "INFO", "log_save": True},
      "download": {"test_mode": False, "folderize": True},
      "history": {"page_size_limit": 10},
      "platform": {
        "douyin": {
          "aweme": {
            "concurrency": 3,
            "media": {"video": True, "images": True, "music": True, "cover": True},
          },
          "owner": {"page_size": 18},
          "live": {"probe": {"max_batch_size": 10}},
        }
      },
    }
    app = app_with(config, FakeGuard())

    ##
    ## Everything an attacker with a reference to the original could try: flip a
    ## top level flag, reach into a nested mapping, and introduce a key that did
    ## not exist when the snapshot was built.
    ##
    config["server"]["debug_mode"] = True
    config["platform"]["douyin"]["aweme"]["media"]["video"] = False
    config["platform"]["douyin"]["aweme"]["concurrency"] = 99
    config["future_secret"] = "SECRET_AFTER_INSTALL"

    response = app.test_client().get("/api/system/status")
    settings = body_of(response)["data"]["settings"]

    self.assertIs(False, settings["server"]["debug_mode"])
    self.assertIs(True, settings["douyin"]["aweme"]["media"]["video"])
    self.assertEqual(3, settings["douyin"]["aweme"]["concurrency"])
    self.assertNotIn("SECRET_AFTER_INSTALL", response.data.decode("utf-8"))

  def test_an_application_without_a_snapshot_reports_a_generic_failure(self):
    ##
    ## Wiring is missing, which is a server problem rather than a client one -
    ## and the answer says nothing about what was being wired.
    ##
    app = Flask(__name__)
    app.register_blueprint(build_system_blueprint())

    response = app.test_client().get("/api/system/status")
    payload = body_of(response)

    self.assertEqual(503, response.status_code)
    self.assertEqual("error", payload["status"])
    self.assertNotIn("config", payload["message"].lower())


class SystemBoundaryTest(unittest.TestCase):
  """The system modules read a configuration snapshot, and nothing else.

  Read from the syntax tree rather than the text: both modules explain at length
  what they refuse to touch, and a grep over the prose would fail on its own
  documentation.
  """

  FORBIDDEN_CALLS = (
    "open", "os.listdir", "os.walk", "os.stat", "os.getenv", "os.environ.get",
    "Path", "Path.read_text", "glob", "glob.glob", "subprocess.run",
    "subprocess.Popen", "subprocess.check_output", "send_file",
    "send_from_directory", "load_config",
  )
  FORBIDDEN_IMPORTS = ("subprocess", "requests", "httpx", "urllib", "aiohttp", "socket")

  def _trees(self):
    import ast
    from pathlib import Path as _Path

    root = _Path(__file__).resolve().parents[3]
    sources = {
      "service": root / "backend/src/service/system_status.py",
      "routes": root / "backend/src/web/system_routes.py",
    }
    return {
      name: ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
      for name, path in sources.items()
    }

  def test_nothing_reads_a_file_a_log_or_a_subprocess(self):
    import ast

    for name, tree in self._trees().items():
      for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
          continue
        called = ast.unparse(node.func)
        self.assertNotIn(
          called, self.FORBIDDEN_CALLS, "{} calls {}".format(name, called)
        )

  def test_nothing_reads_the_environment(self):
    ##
    ## The environment carries database passwords, tokens and proxy credentials
    ## on a normal deployment. The system page has no reason to look.
    ##
    import ast

    for name, tree in self._trees().items():
      text = ast.unparse(tree)
      self.assertNotIn("os.environ", text, name)
      self.assertNotIn("getenv", text, name)

  def test_nothing_reaches_a_platform_or_the_network(self):
    import ast

    for name, tree in self._trees().items():
      for node in ast.walk(tree):
        modules = []
        if isinstance(node, ast.Import):
          modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
          modules = [node.module or ""]
        for module in modules:
          self.assertNotIn(
            module.split(".")[0],
            self.FORBIDDEN_IMPORTS,
            "{} imports {}".format(name, module),
          )
          self.assertNotIn("platform.douyin", module, name)


class ServerWiringTest(unittest.TestCase):
  def test_the_status_route_is_reachable_alongside_everything_before_it(self):
    import server

    rules = {str(rule) for rule in server.app.url_map.iter_rules()}

    self.assertIn("/api/system/status", rules)
    ##
    ## Everything the earlier phases wired, still wired.
    ##
    for existing in (
      "/api/tasks",
      "/api/resolve",
      "/api/history/owners",
      "/api/owner",
      "/api/person",
      "/api/library/posts",
      "/api/library/lives",
    ):
      self.assertIn(existing, rules)

  def test_the_root_route_still_belongs_to_the_legacy_interface(self):
    ##
    ## The vue application stays under /app. Moving the root is a cutover
    ## decision that needs an overview worth landing on first.
    ##
    import server

    rules = {str(rule) for rule in server.app.url_map.iter_rules()}

    self.assertIn("/", rules)

  def test_an_application_built_from_a_configuration_reports_that_one(self):
    ##
    ## create_app is how a test - or a second process - builds an application
    ## around an explicit configuration. Its system page has to describe that
    ## configuration rather than whatever the process global happens to hold.
    ##
    import server

    built = server.create_app(
      config=_wiring_config(debug=True, test_mode=True),
      dispatcher=_NullDispatcher(),
      schema_guard_factory=lambda config: FakeGuard(),
    )

    settings = body_of(built.test_client().get("/api/system/status"))["data"]["settings"]

    self.assertIs(True, settings["server"]["debug_mode"])
    self.assertIs(True, settings["download"]["test_mode"])

  def test_two_applications_built_separately_stay_separate(self):
    import server

    quiet = server.create_app(
      config=_wiring_config(debug=False, test_mode=False),
      dispatcher=_NullDispatcher(),
      schema_guard_factory=lambda config: FakeGuard(),
    )
    loud = server.create_app(
      config=_wiring_config(debug=True, test_mode=True),
      dispatcher=_NullDispatcher(),
      schema_guard_factory=lambda config: FakeGuard(),
    )

    quiet_settings = body_of(quiet.test_client().get("/api/system/status"))["data"]["settings"]
    loud_settings = body_of(loud.test_client().get("/api/system/status"))["data"]["settings"]

    self.assertIs(False, quiet_settings["server"]["debug_mode"])
    self.assertIs(True, loud_settings["server"]["debug_mode"])

  def test_a_built_application_leaks_no_secret(self):
    import server

    built = server.create_app(
      config=_wiring_config(debug=False, test_mode=False, with_secrets=True),
      dispatcher=_NullDispatcher(),
      schema_guard_factory=lambda config: FakeGuard(),
    )

    serialized = built.test_client().get("/api/system/status").data.decode("utf-8")

    self.assertNotIn("SECRET", serialized)


class _NullDispatcher:
  def register(self):
    return None

  def dispatch(self, *unused, **also_unused):
    return None


def _wiring_config(debug: bool, test_mode: bool, with_secrets: bool = False) -> dict:
  """The smallest configuration create_app accepts, plus what is being asserted."""
  config = {
    "server": {"host": "127.0.0.1", "port": 5000, "debug_mode": debug},
    "log": {
      "log_enable": False,
      "log_level": "INFO",
      "log_save": False,
      "log_file_path": "/tmp/smsd-test.log",
    },
    "download": {"test_mode": test_mode, "folderize": True},
    "database": {"enable": False},
  }
  if with_secrets:
    config["database"] = {
      "enable": False,
      "host": "SECRET_DB_HOST",
      "password": "SECRET_DB_PASSWORD",
    }
    config["download"]["save_path"] = "SECRET_SAVE_PATH"
    config["log"]["log_file_path"] = "SECRET_LOG_PATH"
  return config
