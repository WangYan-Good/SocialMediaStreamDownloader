import unittest

from flask import Flask, g

from backend.src.auth.context import RequestAuthContext
from backend.src.auth.roles import ROLE_ADMIN, ROLE_USER
from backend.src.auth.service import AuthenticatedUser
from backend.src.service.task_creation import (
  InvalidTaskOptions,
  ResolutionNotFound,
  TaskCreationResult,
  TaskCreationUnavailable,
  UnknownTaskType,
  UnsupportedTaskForResource,
)
from backend.src.task.model import (
  TASK_TYPE_LIVE_RECORD,
  TASK_TYPE_OWNER_BATCH_DOWNLOAD,
  TASK_TYPE_POST_DOWNLOAD,
)
from backend.src.task.service import TaskService
from backend.src.unit_test.auth_context import TEST_CSRF_PROOF, install_test_auth
from backend.src.web.task_routes import (
  TASK_CREATION_SERVICE_KEY,
  build_task_blueprint,
  install_task_creation_service,
  install_task_service,
)


RESOLVE_ID = "receipt-1"
AWEME_ID = "7657271784144009946"


class FakeCreationService:
  """Stands in for TaskCreationService, so the route is tested as a route."""

  def __init__(self, task_id="task-1", error=None):
    self.task_id = task_id
    self.error = error
    self.calls = []

  def create(self, resolve_id, task_type, options=None, app_user_id=None):
    self.calls.append(
      {
        "resolve_id": resolve_id,
        "task_type": task_type,
        "options": options,
        "app_user_id": app_user_id,
      }
    )
    if self.error is not None:
      raise self.error
    return TaskCreationResult(
      task_id=self.task_id, task_type=task_type, resolve_id=resolve_id
    )


def build_app(creation=None, tasks=None, install_creation=True, auth_context=None):
  creation = creation if creation is not None else FakeCreationService()
  app = Flask(__name__)
  app.config["TESTING"] = True
  install_test_auth(app)
  if auth_context is not None:
    @app.before_request
    def install_auth_context():
      g.auth_context = auth_context
  install_task_service(app, tasks if tasks is not None else TaskService())
  if install_creation:
    install_task_creation_service(app, creation)
  app.register_blueprint(build_task_blueprint())
  return app, creation


def create(app, body):
  return app.test_client().post("/api/tasks", json=body)


def valid_body(**overrides):
  body = {"resolve_id": RESOLVE_ID, "task_type": TASK_TYPE_POST_DOWNLOAD}
  body.update(overrides)
  return body


class CreateTaskSuccessTest(unittest.TestCase):
  def test_authenticated_identity_is_taken_from_request_context(self):
    user = type("User", (), {"user_id": 71, "username": "alice"})()
    context = RequestAuthContext.authenticated(user, csrf_expected="proof")
    app, creation = build_app(auth_context=context)

    response = app.test_client().post(
      "/api/tasks",
      json=valid_body(),
      headers={"X-CSRF-Token": "proof"},
    )

    self.assertEqual(response.status_code, 202)
    self.assertEqual(creation.calls[0]["app_user_id"], 71)

  def test_anonymous_creation_is_refused_without_starting_work(self):
    app, creation = build_app(auth_context=RequestAuthContext.anonymous())

    response = create(app, valid_body())

    self.assertEqual(response.status_code, 401)
    self.assertEqual(creation.calls, [])

  def test_auth_unavailable_never_falls_back_to_an_unowned_task(self):
    app, creation = build_app(
      auth_context=RequestAuthContext.unavailable(csrf_expected="proof")
    )

    response = app.test_client().post(
      "/api/tasks",
      json=valid_body(),
      headers={"X-CSRF-Token": "proof"},
    )

    self.assertEqual(response.status_code, 503)
    self.assertEqual(creation.calls, [])

  def test_authenticated_creation_requires_the_existing_csrf_proof(self):
    user = type("User", (), {"user_id": 71, "username": "alice"})()
    app, creation = build_app(
      auth_context=RequestAuthContext.authenticated(user, csrf_expected="proof")
    )

    response = create(app, valid_body())

    self.assertEqual(response.status_code, 403)
    self.assertEqual(response.get_json()["kind"], "csrf_invalid")
    self.assertEqual(creation.calls, [])

  """What an accepted creation answers."""

  def test_it_is_accepted_rather_than_completed(self):
    """202, because the work has been taken on, not finished."""
    app, _ = build_app()

    response = create(app, valid_body())

    self.assertEqual(response.status_code, 202)
    body = response.get_json()
    self.assertEqual(body["status"], "success")
    self.assertEqual(body["code"], 202)

  def test_it_answers_exactly_the_documented_fields(self):
    app, _ = build_app()

    data = create(app, valid_body()).get_json()["data"]

    self.assertEqual(
      sorted(data.keys()), sorted(["task_id", "task_type", "resolve_id"])
    )
    self.assertEqual(data["task_id"], "task-1")
    self.assertEqual(data["task_type"], TASK_TYPE_POST_DOWNLOAD)
    self.assertEqual(data["resolve_id"], RESOLVE_ID)

  def test_no_legacy_job_id_reaches_the_client(self):
    """The job record stays internal; a new client depends on one id only."""
    app, _ = build_app()

    body = create(app, valid_body(task_type=TASK_TYPE_OWNER_BATCH_DOWNLOAD,
                                  options={"mode": "all"})).get_json()

    self.assertNotIn("job_id", str(body))

  def test_omitted_options_reach_the_service_as_nothing_stated(self):
    app, creation = build_app()

    create(app, valid_body())

    self.assertIsNone(creation.calls[0]["options"])

  def test_stated_options_are_passed_through(self):
    app, creation = build_app()

    create(
      app,
      valid_body(task_type=TASK_TYPE_OWNER_BATCH_DOWNLOAD,
                 options={"mode": "all"}),
    )

    self.assertEqual(creation.calls[0]["options"], {"mode": "all"})

  def test_each_task_type_is_forwarded_verbatim(self):
    for task_type in (TASK_TYPE_POST_DOWNLOAD, TASK_TYPE_LIVE_RECORD,
                      TASK_TYPE_OWNER_BATCH_DOWNLOAD):
      with self.subTest(task_type=task_type):
        app, creation = build_app()

        create(app, valid_body(task_type=task_type,
                               options=({"mode": "all"}
                                        if task_type == TASK_TYPE_OWNER_BATCH_DOWNLOAD
                                        else None)))

        self.assertEqual(creation.calls[0]["task_type"], task_type)

  def test_surrounding_whitespace_is_trimmed(self):
    app, creation = build_app()

    create(app, valid_body(resolve_id="  " + RESOLVE_ID + "  ",
                           task_type="  " + TASK_TYPE_POST_DOWNLOAD + "  "))

    self.assertEqual(creation.calls[0]["resolve_id"], RESOLVE_ID)
    self.assertEqual(creation.calls[0]["task_type"], TASK_TYPE_POST_DOWNLOAD)


class CreateTaskSchemaTest(unittest.TestCase):
  """Every way the request can be shaped wrong."""

  def assertRefused(self, body, code=400, raw=None):
    app, creation = build_app()

    if raw is not None:
      response = app.test_client().post("/api/tasks", **raw)
    else:
      response = create(app, body)

    self.assertEqual(response.status_code, code)
    payload = response.get_json()
    self.assertEqual(payload["status"], "error")
    self.assertEqual(payload["code"], code)
    self.assertTrue(payload["message"])
    self.assertEqual(creation.calls, [], "nothing may reach the service")
    return payload

  def test_a_body_that_is_not_json(self):
    self.assertRefused(None, raw={"data": "resolve_id=x"})

  def test_an_empty_body(self):
    self.assertRefused(
      None, raw={"data": "", "content_type": "application/json"}
    )

  def test_a_json_body_that_is_not_an_object(self):
    self.assertRefused(["resolve_id"])

  def test_a_missing_resolve_id(self):
    self.assertRefused({"task_type": TASK_TYPE_POST_DOWNLOAD})

  def test_an_empty_resolve_id(self):
    self.assertRefused(valid_body(resolve_id="   "))

  def test_a_resolve_id_that_is_not_a_string(self):
    for value in (None, 42, ["a"], {"a": 1}):
      with self.subTest(value=value):
        self.assertRefused(valid_body(resolve_id=value))

  def test_a_missing_task_type(self):
    self.assertRefused({"resolve_id": RESOLVE_ID})

  def test_a_task_type_that_is_not_a_string(self):
    for value in (None, 7, ["post_download"]):
      with self.subTest(value=value):
        self.assertRefused(valid_body(task_type=value))

  def test_options_that_are_not_an_object(self):
    for value in ([], "all", 3, True):
      with self.subTest(value=value):
        self.assertRefused(valid_body(options=value))


class ForgedFieldTest(unittest.TestCase):
  """The client describes what to do, never what the resource is."""

  def assertRejected(self, body):
    app, creation = build_app()

    response = create(app, body)

    self.assertEqual(response.status_code, 400)
    self.assertEqual(
      creation.calls, [], "a forged request must not reach the service at all"
    )
    return response.get_json()

  def test_a_client_supplied_identity_is_refused_outright(self):
    """Not ignored - refused.  "Accepted but had no effect" would leave the
    caller believing the server used the id they sent."""
    self.assertRejected(valid_body(aweme_id="999"))

  def test_a_client_supplied_url_is_refused(self):
    self.assertRejected(valid_body(resolved_url="https://evil.example/"))

  def test_a_client_supplied_platform_or_resource_type_is_refused(self):
    self.assertRejected(valid_body(platform="douyin"))
    self.assertRejected(valid_body(resource_type="post"))

  def test_a_client_cannot_choose_the_application_user_owner(self):
    self.assertRejected(valid_body(app_user_id=999))

  def test_the_refusal_names_the_field(self):
    payload = self.assertRejected(valid_body(aweme_id="999", sec_user_id="MS4w"))

    self.assertIn("aweme_id", payload["message"])
    self.assertIn("sec_user_id", payload["message"])

  def test_only_three_fields_are_accepted(self):
    app, creation = build_app()

    response = create(
      app,
      {
        "resolve_id": RESOLVE_ID,
        "task_type": TASK_TYPE_POST_DOWNLOAD,
        "options": {},
      },
    )

    self.assertEqual(response.status_code, 202)
    self.assertEqual(len(creation.calls), 1)


class ErrorMappingTest(unittest.TestCase):
  """Each business refusal reaches the browser as the status it means."""

  def build(self, error):
    return build_app(creation=FakeCreationService(error=error))

  def test_an_expired_receipt_is_not_found(self):
    app, _ = self.build(ResolutionNotFound("解析结果不存在或已过期，请重新解析"))

    response = create(app, valid_body())

    self.assertEqual(response.status_code, 404)
    self.assertIn("重新解析", response.get_json()["message"])

  def test_an_unknown_task_type_is_a_bad_request(self):
    app, _ = self.build(UnknownTaskType("不支持的任务类型"))

    self.assertEqual(create(app, valid_body()).status_code, 400)

  def test_an_incompatible_pair_is_a_bad_request(self):
    app, _ = self.build(UnsupportedTaskForResource("不支持"))

    self.assertEqual(create(app, valid_body()).status_code, 400)

  def test_bad_options_are_a_bad_request(self):
    app, _ = self.build(InvalidTaskOptions("需要 mode"))

    self.assertEqual(create(app, valid_body()).status_code, 400)

  def test_an_unwired_runner_is_unavailable(self):
    app, _ = self.build(TaskCreationUnavailable("任务创建失败，请稍后重试"))

    response = create(app, valid_body())

    self.assertEqual(response.status_code, 503)
    self.assertEqual(response.get_json()["code"], 503)

  def test_an_unexpected_failure_is_a_generic_five_hundred(self):
    app, _ = self.build(RuntimeError("boom: /srv/app/config/config.yml line 12"))

    response = create(app, valid_body())
    body = response.get_json()

    self.assertEqual(response.status_code, 500)
    self.assertNotIn("boom", body["message"])
    self.assertNotIn("config.yml", str(body))
    self.assertNotIn("traceback", body)

  def test_no_failure_leaks_internal_state(self):
    app, _ = self.build(TaskCreationUnavailable("任务创建失败"))

    body = str(create(app, valid_body()).get_json())

    for secret in ("cookie", "Cookie", "msToken", "Authorization",
                   "config.yml", "Traceback"):
      self.assertNotIn(secret, body)


class CreationWiringTest(unittest.TestCase):
  """One creation service per application, reachable as every extension is."""

  def test_the_service_is_reachable_through_the_app_extensions(self):
    app, creation = build_app()

    self.assertIs(app.extensions[TASK_CREATION_SERVICE_KEY], creation)

  def test_a_missing_service_is_reported_not_crashed(self):
    """Registering the blueprint without wiring is a deployment bug."""
    app, _ = build_app(install_creation=False)

    response = create(app, valid_body())

    self.assertEqual(response.status_code, 503)
    self.assertEqual(response.get_json()["status"], "error")

  def test_the_read_side_still_answers(self):
    """P6 adds a verb to the existing resource; it does not replace it."""
    tasks = TaskService()
    app, _ = build_app(tasks=tasks)

    listing = app.test_client().get("/api/tasks")

    self.assertEqual(listing.status_code, 200)
    self.assertEqual(listing.get_json()["data"], {"items": [], "total": 0})

  def test_the_created_task_is_readable_at_once(self):
    """202 promises something observable, so the id must resolve immediately."""
    tasks = TaskService()
    created = tasks.create_task(TASK_TYPE_POST_DOWNLOAD)
    app, _ = build_app(
      creation=FakeCreationService(task_id=created["task_id"]), tasks=tasks
    )

    task_id = create(app, valid_body()).get_json()["data"]["task_id"]

    read = app.test_client().get("/api/tasks/" + task_id)
    self.assertEqual(read.status_code, 200)
    self.assertEqual(read.get_json()["data"]["task_id"], task_id)


##
## >>============================= server wiring =============================>>
##
from unittest.mock import patch

from backend.src.service.task_creation import TaskCreationService
from backend.src.web.owner_routes import OWNER_RUNTIME_KEY, OwnerRuntime
from backend.src.web.resolve_routes import RESOLVE_SERVICE_KEY


SEC_UID = "MS4wLjABAAAAGZkW5n1EHZD_TFyQ-QiaISBPemtKFxVVdhLSeoXhh-U"
POST_URL = "https://www.douyin.com/video/" + AWEME_ID
OWNER_URL = "https://www.douyin.com/user/" + SEC_UID
LIVE_URL = "https://live.douyin.com/123456"


def configured_app():
  import server
  from backend.src.unit_test.config_fixture import unified_config

  app = server.create_app(
    config=unified_config(),
    schema_guard_factory=lambda config: object(),
  )
  return install_test_auth(app)


def resolve(app, url):
  return app.test_client().post("/api/resolve", json={"input": url})


class ApplicationWiringTest(unittest.TestCase):
  """The factory builds one of each and hands the same one to everybody."""

  def test_a_configured_app_carries_one_creation_service(self):
    app = configured_app()

    self.assertIsInstance(
      app.extensions[TASK_CREATION_SERVICE_KEY], TaskCreationService
    )

  def test_a_configured_app_carries_one_owner_runtime(self):
    app = configured_app()

    self.assertIsInstance(app.extensions[OWNER_RUNTIME_KEY], OwnerRuntime)

  def test_the_owner_page_and_the_task_api_share_one_runtime(self):
    """Two runtimes would mean two job stores and two payload caches.

    The same post could then be walked by one and downloaded by the other, each
    holding its own locks, which is how two writers end up in one file.
    """
    app = configured_app()

    creation = app.extensions[TASK_CREATION_SERVICE_KEY]
    runtime = app.extensions[OWNER_RUNTIME_KEY]

    self.assertEqual(creation.owner_service_factory, runtime.service)

  def test_the_creation_service_holds_the_applications_own_resolve_service(self):
    """Not an equivalent one - the same object.

    A second store would be indistinguishable from an expired receipt on every
    single request, which is the kind of fault that reads as "the feature is
    flaky" rather than "the wiring is wrong".
    """
    app = configured_app()

    creation = app.extensions[TASK_CREATION_SERVICE_KEY]

    self.assertIs(creation.resolve_service, app.extensions[RESOLVE_SERVICE_KEY])

  def test_the_creation_service_reads_the_applications_own_receipts(self):
    """Resolved here, redeemed here.

    A creation service that built its own resolve store would answer 404 to
    every receipt this application ever issued - so the proof is a receipt that
    is *found* and then refused for a different reason entirely.
    """
    app = configured_app()

    resolve_id = resolve(app, OWNER_URL).get_json()["data"]["resolve_id"]
    response = create(
      app, {"resolve_id": resolve_id, "task_type": TASK_TYPE_POST_DOWNLOAD}
    )

    self.assertEqual(
      response.status_code,
      400,
      "404 here would mean the receipt was looked up in a different store",
    )

  def test_an_unknown_receipt_is_not_found(self):
    app = configured_app()

    response = create(
      app, {"resolve_id": "never-issued", "task_type": TASK_TYPE_POST_DOWNLOAD}
    )

    self.assertEqual(response.status_code, 404)

  def test_creating_a_task_never_resolves_anything_again(self):
    """The receipt already holds the answer; re-following the link would spend
    a request to rediscover it, and could disagree with what was resolved."""
    app = configured_app()
    resolve_id = resolve(app, OWNER_URL).get_json()["data"]["resolve_id"]

    with patch(
      "backend.src.platform.douyin.douyin_resource_resolver.request",
      side_effect=AssertionError("task creation must not resolve"),
    ) as never:
      create(app, {"resolve_id": resolve_id,
                   "task_type": TASK_TYPE_POST_DOWNLOAD})

    never.assert_not_called()


class CrossApplicationIsolationTest(unittest.TestCase):
  """A receipt is one application's word, and means nothing to another."""

  def test_a_receipt_from_one_app_cannot_be_redeemed_in_another(self):
    first = configured_app()
    second = configured_app()

    resolve_id = resolve(first, POST_URL).get_json()["data"]["resolve_id"]

    response = create(
      second, {"resolve_id": resolve_id, "task_type": TASK_TYPE_POST_DOWNLOAD}
    )
    self.assertEqual(response.status_code, 404)

  def test_the_two_applications_hold_different_services(self):
    first = configured_app()
    second = configured_app()

    for key in (TASK_CREATION_SERVICE_KEY, RESOLVE_SERVICE_KEY,
                OWNER_RUNTIME_KEY):
      with self.subTest(key=key):
        self.assertIsNot(first.extensions[key], second.extensions[key])

  def test_a_task_created_in_one_app_is_invisible_in_the_other(self):
    first = configured_app()
    second = configured_app()

    first.extensions["smsd_task_service"].create_task(TASK_TYPE_POST_DOWNLOAD)

    listed = second.test_client().get("/api/tasks").get_json()
    self.assertEqual(listed["data"]["total"], 0)


##
## >>============================= end to end =============================>>
##
from backend.src.service.direct_post_download_task import DirectPostDownloadTaskService
from backend.src.service.job_store import JobStore
from backend.src.service.live_recording_task import LiveRecordingTaskService
from backend.src.service.post_download_job import PayloadCache, PostDownloadJobService
from backend.src.unit_test.test_post_download_job import (
  SWITCHES,
  StubApi,
  StubDownloader,
  page,
)
from backend.src.unit_test.test_task_creation_dispatch import (
  DeferredExecutor,
  DeferredListenerItem,
  FakeDownloader,
  FakeLiveDownloader,
)
from backend.src.web.task_routes import TASK_SERVICE_KEY


def offline_app():
  """A real application whose runners are stubs, so nothing leaves the process.

  The resolve service and the task service are the application's own - that is
  the point of the exercise - and only the three things that would reach the
  platform are replaced.
  """
  app = configured_app()
  tasks = app.extensions[TASK_SERVICE_KEY]
  post_executor = DeferredExecutor()

  post = DirectPostDownloadTaskService(
    task_service=tasks,
    downloader_factory=lambda: FakeDownloader(),
    executor_factory=lambda *args, **kwargs: post_executor,
  )
  live = LiveRecordingTaskService(
    task_service=tasks,
    downloader_factory=lambda: FakeLiveDownloader(),
    listener_factory=DeferredListenerItem,
  )
  owner = PostDownloadJobService(
    downloader=StubDownloader(),
    api=StubApi([page(["1"], 0, False)]),
    store=JobStore(),
    cache=PayloadCache(),
    media_switches=SWITCHES,
    task_service=tasks,
    executor=DeferredExecutor(),
  )
  install_task_creation_service(
    app,
    TaskCreationService(
      resolve_service=app.extensions[RESOLVE_SERVICE_KEY],
      direct_post_service=post,
      live_record_service=live,
      owner_service_factory=lambda: owner,
    ),
  )
  return app, tasks


def receipt_for(app, url):
  return resolve(app, url).get_json()["data"]["resolve_id"]


def task_count(app):
  return app.test_client().get("/api/tasks").get_json()["data"]["total"]


class EndToEndTest(unittest.TestCase):
  """The whole new road: paste, resolve, create, watch."""

  def assertCreated(self, app, url, task_type, options=None):
    resolve_id = receipt_for(app, url)
    body = {"resolve_id": resolve_id, "task_type": task_type}
    if options is not None:
      body["options"] = options

    response = create(app, body)

    self.assertEqual(response.status_code, 202)
    data = response.get_json()["data"]
    self.assertEqual(data["task_type"], task_type)
    self.assertEqual(data["resolve_id"], resolve_id)
    return data

  def test_a_post_link_becomes_a_watchable_download(self):
    app, _ = offline_app()

    data = self.assertCreated(app, POST_URL, TASK_TYPE_POST_DOWNLOAD)

    read = app.test_client().get("/api/tasks/" + data["task_id"])
    self.assertEqual(read.status_code, 200)
    task = read.get_json()["data"]
    self.assertEqual(task["task_type"], TASK_TYPE_POST_DOWNLOAD)
    self.assertEqual(task["metadata"]["source"], "task_api")
    self.assertEqual(task["metadata"]["resolve_id"], data["resolve_id"])
    self.assertEqual(task["metadata"]["aweme_id"], AWEME_ID)
    self.assertEqual(task["metadata"]["resolved_url"], POST_URL)

  def test_a_live_link_becomes_a_watchable_recording(self):
    app, _ = offline_app()

    data = self.assertCreated(app, LIVE_URL, TASK_TYPE_LIVE_RECORD)

    task = app.test_client().get(
      "/api/tasks/" + data["task_id"]
    ).get_json()["data"]
    self.assertEqual(task["task_type"], TASK_TYPE_LIVE_RECORD)
    self.assertEqual(task["metadata"]["source"], "task_api")
    self.assertEqual(task["metadata"]["resolved_url"], LIVE_URL)

  def test_an_owner_link_becomes_a_watchable_batch(self):
    app, _ = offline_app()

    data = self.assertCreated(
      app, OWNER_URL, TASK_TYPE_OWNER_BATCH_DOWNLOAD, {"mode": "all"}
    )

    self.assertNotIn("job_id", data)
    task = app.test_client().get(
      "/api/tasks/" + data["task_id"]
    ).get_json()["data"]
    self.assertEqual(task["task_type"], TASK_TYPE_OWNER_BATCH_DOWNLOAD)
    self.assertEqual(task["metadata"]["source"], "task_api")
    self.assertEqual(task["metadata"]["mode"], "all")
    self.assertEqual(task["metadata"]["sec_user_id"], SEC_UID)
    self.assertEqual(task["metadata"]["resolve_id"], data["resolve_id"])

  def test_the_task_appears_in_the_listing(self):
    app, _ = offline_app()

    self.assertCreated(app, POST_URL, TASK_TYPE_POST_DOWNLOAD)

    self.assertEqual(task_count(app), 1)


class ReceiptReuseTest(unittest.TestCase):
  """One receipt, as many tasks as the user asks for."""

  def test_the_same_receipt_creates_two_independent_tasks(self):
    app, _ = offline_app()
    resolve_id = receipt_for(app, POST_URL)
    body = {"resolve_id": resolve_id, "task_type": TASK_TYPE_POST_DOWNLOAD}

    first = create(app, body).get_json()["data"]["task_id"]
    second = create(app, body).get_json()["data"]["task_id"]

    self.assertNotEqual(first, second)
    for task_id in (first, second):
      with self.subTest(task_id=task_id):
        self.assertEqual(
          app.test_client().get("/api/tasks/" + task_id).status_code, 200
        )

  def test_the_receipt_survives_being_used(self):
    app, _ = offline_app()
    resolve_id = receipt_for(app, POST_URL)
    body = {"resolve_id": resolve_id, "task_type": TASK_TYPE_POST_DOWNLOAD}

    create(app, body)
    create(app, body)

    self.assertEqual(create(app, body).status_code, 202)
    self.assertEqual(task_count(app), 3)


class CrossUserReceiptIsolationTest(unittest.TestCase):
  def test_receipt_can_only_be_redeemed_by_the_account_that_created_it(self):
    app, tasks = offline_app()
    alice = AuthenticatedUser(71, "alice", ROLE_USER)
    bob = AuthenticatedUser(72, "bob", ROLE_USER)
    app.config["request_user"] = alice

    @app.before_request
    def current_test_user():
      g.auth_context = RequestAuthContext.authenticated(
        app.config["request_user"], csrf_expected=TEST_CSRF_PROOF
      )

    resolve_id = receipt_for(app, POST_URL)
    body = {"resolve_id": resolve_id, "task_type": TASK_TYPE_POST_DOWNLOAD}

    app.config["request_user"] = bob
    refused = create(app, body)
    self.assertEqual(404, refused.status_code)
    self.assertEqual([], tasks.list_tasks())

    app.config["request_user"] = alice
    accepted = create(app, body)
    self.assertEqual(202, accepted.status_code)
    self.assertEqual(71, tasks.list_tasks()[0]["app_user_id"])

  def test_admin_global_read_does_not_make_receipts_impersonable(self):
    app, tasks = offline_app()
    first = AuthenticatedUser(81, "admin-one", ROLE_ADMIN)
    second = AuthenticatedUser(82, "admin-two", ROLE_ADMIN)
    app.config["request_user"] = first

    @app.before_request
    def current_test_admin():
      g.auth_context = RequestAuthContext.authenticated(
        app.config["request_user"], csrf_expected=TEST_CSRF_PROOF
      )

    resolve_id = receipt_for(app, POST_URL)
    app.config["request_user"] = second

    response = create(
      app,
      {"resolve_id": resolve_id, "task_type": TASK_TYPE_POST_DOWNLOAD},
    )

    self.assertEqual(404, response.status_code)
    self.assertEqual([], tasks.list_tasks())


class RefusalsStartNothingTest(unittest.TestCase):
  """Every refusal leaves the task centre exactly as it was."""

  def assertNoTask(self, app, body, code):
    before = task_count(app)

    response = create(app, body)

    self.assertEqual(response.status_code, code)
    self.assertEqual(task_count(app), before)

  def test_selected_owner_downloads_are_refused(self):
    app, _ = offline_app()
    resolve_id = receipt_for(app, OWNER_URL)

    self.assertNoTask(
      app,
      {
        "resolve_id": resolve_id,
        "task_type": TASK_TYPE_OWNER_BATCH_DOWNLOAD,
        "options": {"mode": "selected"},
      },
      400,
    )

  def test_an_owner_download_without_a_mode_is_refused(self):
    app, _ = offline_app()
    resolve_id = receipt_for(app, OWNER_URL)

    self.assertNoTask(
      app,
      {"resolve_id": resolve_id, "task_type": TASK_TYPE_OWNER_BATCH_DOWNLOAD},
      400,
    )

  def test_live_probe_cannot_be_created_here(self):
    app, _ = offline_app()

    for url in (POST_URL, OWNER_URL, LIVE_URL):
      with self.subTest(url=url):
        self.assertNoTask(
          app,
          {"resolve_id": receipt_for(app, url), "task_type": "live_probe"},
          400,
        )

  def test_a_mismatched_pair_is_refused(self):
    app, _ = offline_app()

    self.assertNoTask(
      app,
      {"resolve_id": receipt_for(app, LIVE_URL),
       "task_type": TASK_TYPE_POST_DOWNLOAD},
      400,
    )

  def test_an_expired_receipt_is_refused(self):
    app, _ = offline_app()

    self.assertNoTask(
      app,
      {"resolve_id": "never-issued", "task_type": TASK_TYPE_POST_DOWNLOAD},
      404,
    )

  def test_a_forged_identity_is_refused(self):
    app, _ = offline_app()

    self.assertNoTask(
      app,
      {
        "resolve_id": receipt_for(app, POST_URL),
        "task_type": TASK_TYPE_POST_DOWNLOAD,
        "aweme_id": "999",
      },
      400,
    )


class AdjacentEndpointsTest(unittest.TestCase):
  """Modern owner and resolve APIs remain alongside task creation."""

  def test_the_owner_download_endpoint_still_validates(self):
    app, _ = offline_app()

    response = app.test_client().post("/api/owner/download", json={})

    self.assertEqual(response.status_code, 400)
    self.assertIn("aweme_ids", response.get_json()["message"])

  def test_the_resolve_endpoint_still_answers(self):
    app, _ = offline_app()

    response = resolve(app, POST_URL)

    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.get_json()["data"]["resource_type"], "post")


if __name__ == "__main__":
  unittest.main()
