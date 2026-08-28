import json
import unittest

from flask import Flask

from backend.src.auth.roles import ROLE_ADMIN, ROLE_USER
from backend.src.auth.service import AuthenticatedUser
from backend.src.database.query.library import LibraryPage
from backend.src.unit_test.auth_context import install_test_auth
from backend.src.web.library_routes import (
  LibraryRuntime,
  LibraryUnavailable,
  build_library_blueprint,
)


class FakeQuery:
  """Stands in for LibraryQuery, recording the filters it was handed."""

  def __init__(self, posts=None, lives=None, recordings=None, failure=None):
    self.posts_page = posts if posts is not None else LibraryPage(0, 1, 25, tuple())
    self.lives_page = lives if lives is not None else LibraryPage(0, 1, 25, tuple())
    self.recordings_page = (
      recordings if recordings is not None else LibraryPage(0, 1, 25, tuple())
    )
    self.failure = failure
    self.post_filters = []
    self.post_user_calls = []
    self.live_filters = []
    self.recording_filters = []
    self.recording_user_calls = []

  def posts(self, post_filter):
    self.post_filters.append(post_filter)
    if self.failure is not None:
      raise self.failure
    return self.posts_page

  def posts_for_user(self, app_user_id, post_filter):
    self.post_user_calls.append((app_user_id, post_filter))
    if self.failure is not None:
      raise self.failure
    return self.posts_page

  def recordings(self, recording_filter):
    self.recording_filters.append(recording_filter)
    if self.failure is not None:
      raise self.failure
    return self.recordings_page

  def recordings_for_user(self, app_user_id, recording_filter):
    self.recording_user_calls.append((app_user_id, recording_filter))
    if self.failure is not None:
      raise self.failure
    return self.recordings_page

  def lives(self, live_filter):
    self.live_filters.append(live_filter)
    if self.failure is not None:
      raise self.failure
    return self.lives_page


class FakeRuntime:
  def __init__(self, query=None, unavailable=None, page_size_limit=100):
    self._query = query
    self._unavailable = unavailable
    self._page_size_limit = page_size_limit
    self.query_calls = 0

  def page_size_limit(self):
    return self._page_size_limit

  def query(self):
    self.query_calls += 1
    if self._unavailable is not None:
      raise self._unavailable
    return self._query


def client_for(runtime, user=None):
  app = Flask(__name__)
  install_test_auth(
    app,
    user=user or AuthenticatedUser(9001, "test-admin", ROLE_ADMIN),
  )
  app.register_blueprint(build_library_blueprint(runtime=runtime))
  return app.test_client()


def body_of(response):
  return json.loads(response.data.decode("utf-8"))


class LibraryPostRouteTest(unittest.TestCase):
  def test_answers_with_the_project_envelope(self):
    page = LibraryPage(
      total=163,
      page=1,
      page_size=25,
      items=({"platform": "douyin", "aweme_id": "1", "downloaded_at": None},),
    )
    client = client_for(FakeRuntime(FakeQuery(posts=page)))

    response = client.get("/api/library/posts")
    payload = body_of(response)

    self.assertEqual(200, response.status_code)
    self.assertEqual("success", payload["status"])
    self.assertEqual(200, payload["code"])
    self.assertEqual(163, payload["data"]["total"])
    self.assertEqual(1, payload["data"]["page"])
    self.assertEqual(25, payload["data"]["page_size"])
    self.assertEqual(1, len(payload["data"]["items"]))

  def test_passes_every_filter_through_to_the_query(self):
    query = FakeQuery()
    client = client_for(FakeRuntime(query))

    client.get(
      "/api/library/posts?q=绿萝&person_id=12&aweme_type=image"
      "&completion=partial&source=html&sort=nickname&order=asc"
      "&page=2&page_size=10&owner_user_id=5885"
    )
    used = query.post_filters[0]

    self.assertEqual("绿萝", used.keyword)
    self.assertEqual(12, used.person_id)
    self.assertEqual("image", used.aweme_type)
    self.assertEqual("partial", used.completion)
    self.assertEqual("html", used.source)
    self.assertEqual("nickname", used.sort)
    self.assertEqual("asc", used.order)
    self.assertEqual(2, used.page)
    self.assertEqual(10, used.page_size)
    self.assertEqual("5885", used.owner_user_id)

  def test_a_bad_sort_is_a_client_error(self):
    client = client_for(FakeRuntime(FakeQuery()))

    response = client.get("/api/library/posts?sort=; DROP TABLE aweme_record")

    self.assertEqual(400, response.status_code)
    self.assertEqual("error", body_of(response)["status"])

  def test_a_bad_page_is_a_client_error(self):
    client = client_for(FakeRuntime(FakeQuery()))

    self.assertEqual(400, client.get("/api/library/posts?page=0").status_code)
    self.assertEqual(400, client.get("/api/library/posts?page=first").status_code)

  def test_a_bad_order_is_a_client_error(self):
    client = client_for(FakeRuntime(FakeQuery()))

    self.assertEqual(400, client.get("/api/library/posts?order=sideways").status_code)

  def test_an_unsupported_platform_is_a_client_error(self):
    client = client_for(FakeRuntime(FakeQuery()))

    self.assertEqual(400, client.get("/api/library/posts?platform=kuaishou").status_code)

  def test_a_disabled_database_is_not_an_empty_library(self):
    ##
    ## The distinction the whole page rests on: "nothing was downloaded" and
    ## "this server cannot tell you" are different answers, and 200 with an
    ## empty list says the first while meaning the second.
    ##
    runtime = FakeRuntime(unavailable=LibraryUnavailable("媒体库需要启用数据库"))
    client = client_for(runtime)

    response = client.get("/api/library/posts")

    self.assertEqual(503, response.status_code)
    self.assertEqual("error", body_of(response)["status"])

  def test_an_unreachable_database_is_also_503(self):
    runtime = FakeRuntime(unavailable=LibraryUnavailable("数据库暂时不可用"))
    client = client_for(runtime)

    self.assertEqual(503, client.get("/api/library/posts").status_code)

  def test_an_unexpected_failure_says_nothing_about_the_database(self):
    failure = RuntimeError(
      "(1045, \"Access denied for user 'root'@'10.0.0.2' (using password: YES)\")"
    )
    client = client_for(FakeRuntime(FakeQuery(failure=failure)))

    response = client.get("/api/library/posts")
    message = body_of(response)["message"]

    self.assertEqual(500, response.status_code)
    self.assertNotIn("root", message)
    self.assertNotIn("10.0.0.2", message)
    self.assertNotIn("password", message)


class LibraryLiveRouteTest(unittest.TestCase):
  def test_answers_with_the_project_envelope(self):
    page = LibraryPage(
      total=7,
      page=1,
      page_size=25,
      items=(
        {
          "observed_at": None,
          "room_id": "7123",
          "title": "晚间直播",
          "room_status": 4,
          "start_time": None,
          "finish_time": None,
          "status_code": 0,
        },
      ),
    )
    client = client_for(FakeRuntime(FakeQuery(lives=page)))

    response = client.get("/api/library/lives")
    payload = body_of(response)

    self.assertEqual(200, response.status_code)
    self.assertEqual(7, payload["data"]["total"])
    self.assertEqual("晚间直播", payload["data"]["items"][0]["title"])

  def test_never_reports_an_output_path(self):
    ##
    ## live_record has no such column.  Inventing one here would be a path the
    ## interface could offer to open, guessed rather than recorded.
    ##
    page = LibraryPage(total=1, page=1, page_size=25, items=({"room_id": "1"},))
    client = client_for(FakeRuntime(FakeQuery(lives=page)))

    payload = body_of(client.get("/api/library/lives"))

    self.assertNotIn("output_path", payload["data"]["items"][0])

  def test_passes_its_filters_through(self):
    query = FakeQuery()
    client = client_for(FakeRuntime(query))

    client.get("/api/library/lives?q=晚间&person_id=3&sort=start_time&order=asc&page=2")
    used = query.live_filters[0]

    self.assertEqual("晚间", used.keyword)
    self.assertEqual(3, used.person_id)
    self.assertEqual("start_time", used.sort)
    self.assertEqual("asc", used.order)
    self.assertEqual(2, used.page)

  def test_a_bad_sort_is_a_client_error(self):
    client = client_for(FakeRuntime(FakeQuery()))

    self.assertEqual(400, client.get("/api/library/lives?sort=room_id").status_code)

  def test_a_disabled_database_is_not_an_empty_library(self):
    runtime = FakeRuntime(unavailable=LibraryUnavailable("媒体库需要启用数据库"))
    client = client_for(runtime)

    self.assertEqual(503, client.get("/api/library/lives").status_code)


class LibraryRoleScopedRouteTest(unittest.TestCase):
  def test_user_posts_use_server_selected_scope_and_safe_serializer(self):
    row = {
      "platform": "douyin",
      "aweme_id": "A1",
      "nickname": "创作者",
      "aweme_type": "video",
      "desc": "作品",
      "media_count": 2,
      "saved_count": 2,
      "save_dir": "/srv/private",
      "directory_name": "internal",
      "person_id": 99,
      "person_display_name": "internal",
      "sec_user_id": "secret",
      "owner_user_id": "owner",
      "source": "api",
    }
    query = FakeQuery(posts=LibraryPage(1, 1, 25, (row,)))
    user = AuthenticatedUser(71, "alice", ROLE_USER)

    response = client_for(FakeRuntime(query), user=user).get(
      "/api/library/posts?app_user_id=72&user_id=72&role=admin"
    )
    item = response.get_json()["data"]["items"][0]

    self.assertEqual(200, response.status_code)
    self.assertEqual(71, query.post_user_calls[0][0])
    for field in (
      "save_dir", "directory_name", "person_id", "person_display_name",
      "sec_user_id", "owner_user_id", "source",
    ):
      self.assertNotIn(field, item)

  def test_admin_posts_remain_global(self):
    query = FakeQuery()
    client_for(FakeRuntime(query)).get("/api/library/posts")

    self.assertEqual(1, len(query.post_filters))
    self.assertEqual([], query.post_user_calls)

  def test_recordings_are_user_scoped_and_never_expose_paths(self):
    row = {
      ##
      ## An integer, because the column is one.  A recording's identity reaches
      ## the browser as decimal text, but it is never text in a row.
      ##
      "recording_id": 7,
      "app_user_id": 71,
      "platform": "douyin",
      "room_id": "room",
      "title": "晚间直播",
      "nickname": "主播",
      "output_path": "/srv/private/live.flv",
      "source": "task_api",
    }
    query = FakeQuery(recordings=LibraryPage(1, 1, 25, (row,)))
    user = AuthenticatedUser(71, "alice", ROLE_USER)

    response = client_for(FakeRuntime(query), user=user).get(
      "/api/library/recordings?app_user_id=72&role=admin"
    )
    item = response.get_json()["data"]["items"][0]

    self.assertEqual(71, query.recording_user_calls[0][0])
    self.assertNotIn("app_user_id", item)
    self.assertNotIn("output_path", item)
    self.assertNotIn("source", item)

  def test_admin_recordings_are_global_but_still_do_not_dump_output_path(self):
    row = {"recording_id": 8, "output_path": "/srv/private/live.flv"}
    query = FakeQuery(recordings=LibraryPage(1, 1, 25, (row,)))

    item = client_for(FakeRuntime(query)).get(
      "/api/library/recordings"
    ).get_json()["data"]["items"][0]

    self.assertEqual(1, len(query.recording_filters))
    self.assertEqual([], query.recording_user_calls)
    self.assertNotIn("output_path", item)


class LibraryRuntimeTest(unittest.TestCase):
  def test_reads_nothing_until_a_request_arrives(self):
    ##
    ## Importing the module, or building the app, must not open a connection:
    ## the server has to start on a machine whose database is down.
    ##
    opened = []

    def config_loader():
      opened.append("config")
      return {"database": {"enable": True}}

    LibraryRuntime(config_loader=config_loader)

    self.assertEqual([], opened)

  def test_a_disabled_database_is_refused_before_connecting(self):
    connections = []

    def database_factory(**unused):
      connections.append(unused)
      return object()

    runtime = LibraryRuntime(
      config_loader=lambda: {"database": {"enable": False}},
      database_factory=database_factory,
    )

    with self.assertRaises(LibraryUnavailable):
      runtime.query()
    self.assertEqual([], connections)

  def test_a_failing_connection_becomes_unavailable_rather_than_a_crash(self):
    def database_factory(**unused):
      raise OSError("connection refused")

    runtime = LibraryRuntime(
      config_loader=lambda: {"database": {"enable": True, "host": "h"}},
      database_factory=database_factory,
    )

    with self.assertRaises(LibraryUnavailable):
      runtime.query()

  def test_the_query_is_built_once_and_reused(self):
    built = []

    def database_factory(**unused):
      built.append(1)
      return object()

    runtime = LibraryRuntime(
      config_loader=lambda: {"database": {"enable": True}},
      database_factory=database_factory,
    )

    first = runtime.query()
    second = runtime.query()

    self.assertIs(first, second)
    self.assertEqual(1, len(built))


class ServerWiringTest(unittest.TestCase):
  def test_the_library_is_reachable_alongside_everything_that_came_before(self):
    ##
    ## The module level app is built with a lazy config, so importing it here
    ## opens nothing - which is also the property that lets the library runtime
    ## be registered at import time at all.
    ##
    import server

    rules = {str(rule) for rule in server.app.url_map.iter_rules()}

    self.assertIn("/api/library/posts", rules)
    self.assertIn("/api/library/lives", rules)

    ##
    ## Everything the earlier phases wired, still wired.
    ##
    self.assertIn("/api/tasks", rules)
    self.assertIn("/api/resolve", rules)
    self.assertIn("/api/history/owners", rules)
    self.assertIn("/api/owner", rules)
    self.assertIn("/api/person", rules)

  def test_the_library_routes_are_read_only(self):
    import server

    methods = set()
    for rule in server.app.url_map.iter_rules():
      if str(rule).startswith("/api/library"):
        methods.update(rule.methods or set())

    ##
    ## A read model has no write verbs.  Anything else here would be a way to
    ## change records this api only reports.
    ##
    self.assertNotIn("POST", methods)
    self.assertNotIn("PATCH", methods)
    self.assertNotIn("PUT", methods)
    self.assertNotIn("DELETE", methods)


class LibraryBoundaryTest(unittest.TestCase):
  """The library reports database records, and only that.

  Read from the syntax tree rather than exercised, because what is forbidden is
  a capability rather than a behaviour: one ``os.listdir`` added to answer "is
  the file still there" would be a working feature that passes every functional
  test, and a filesystem contract this phase deliberately does not have.

  The tree, not the text: these modules explain at length why they do not touch
  the disk or the platform, and a grep over the prose would fail on its own
  documentation.
  """

  ##
  ## Reaching the disk.  ``os`` itself is not listed - every module in this
  ## project opens with the sys.path preamble that imports it.
  ##
  FILESYSTEM_CALLS = (
    "os.listdir", "os.walk", "os.stat", "os.remove", "os.rename", "os.mkdir",
    "os.makedirs", "os.scandir", "os.open", "open", "glob", "glob.glob",
    "Path", "shutil.copy", "shutil.move", "send_file", "send_from_directory",
  )
  PLATFORM_IMPORTS = (
    "requests", "httpx", "urllib", "urllib.request", "aiohttp",
  )
  WRITE_STATEMENTS = ("INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER", "TRUNCATE")

  def _trees(self):
    import ast
    from pathlib import Path as _Path

    root = _Path(__file__).resolve().parents[3]
    sources = {
      "query": root / "backend/src/database/query/library.py",
      "routes": root / "backend/src/web/library_routes.py",
    }
    return {
      name: ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
      for name, path in sources.items()
    }

  def test_the_library_never_reaches_for_the_filesystem(self):
    ##
    ## save_dir is a string this program recorded.  Whether that directory still
    ## holds anything is a different question with a different security surface,
    ## and answering it here is how a record index turns into a file server.
    ##
    import ast

    for name, tree in self._trees().items():
      for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
          continue
        called = ast.unparse(node.func)
        self.assertNotIn(
          called,
          self.FILESYSTEM_CALLS,
          "{} reaches the filesystem via {}".format(name, called),
        )

  def test_the_library_never_reaches_for_a_platform(self):
    ##
    ## Opening the library must cost zero requests to a platform.  It reports
    ## what was already downloaded; going back to decorate those rows would make
    ## browsing a record index a rate limited operation, and would make the page
    ## fail when the platform does.
    ##
    import ast

    for name, tree in self._trees().items():
      for node in ast.walk(tree):
        imported = []
        if isinstance(node, ast.Import):
          imported = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
          imported = [node.module or ""]
        for module in imported:
          root = module.split(".")[0]
          self.assertNotIn(
            root,
            self.PLATFORM_IMPORTS,
            "{} imports {} to talk to a platform".format(name, module),
          )
          self.assertNotIn(
            "platform.douyin",
            module,
            "{} imports the douyin client".format(name),
          )

  def test_the_query_layer_only_reads(self):
    ##
    ## Checked against the sql literals themselves, so the prose around them is
    ## free to discuss what the library does not do.
    ##
    import ast

    tree = self._trees()["query"]
    for node in ast.walk(tree):
      if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
        continue
      text = node.value.upper()
      if "SELECT" not in text:
        continue
      for statement in self.WRITE_STATEMENTS:
        self.assertNotIn(
          statement, text, "the library query writes: {}".format(node.value)
        )
