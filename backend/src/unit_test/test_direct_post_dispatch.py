import unittest
from concurrent.futures import Future

from backend.src.platform.douyin import douyin_handler as handler_module
from backend.src.platform.platform_dispatcher import PlatformDispatcher
from backend.src.service.direct_post_download_task import DirectPostDownloadTaskService
from backend.src.task.model import TASK_TYPE_POST_DOWNLOAD
from backend.src.task.service import TaskService

AWEME_ID = "7123456789012345678"
VIDEO_URL = "https://www.douyin.com/video/" + AWEME_ID
SHARE_URL = "https://v.douyin.com/abc/"


class InlineExecutor:
  """Runs dispatched handlers inline so a dispatch is finished when it returns."""

  def submit(self, fn, *args, **kwargs):
    future = Future()
    try:
      future.set_result(fn(*args, **kwargs))
    except BaseException as e:
      future.set_exception(e)
    return future


class FakeResponse:
  def __init__(self, url, status_code=200):
    self.url = url
    self.status_code = status_code


class FakeConfig:
  def __init__(self, concurrency=3):
    self.concurrency = concurrency


class FakeDownloader:
  def __init__(self, result=None):
    self.config = FakeConfig()
    self.result = result
    self.calls = []

  def run(self, token):
    self.calls.append(token)
    return self.result


def build_dispatcher(handler=None):
  """A dispatcher whose douyin path runs inline, for deterministic tests."""
  dispatcher = PlatformDispatcher()
  dispatcher.register()
  if handler is not None:
    dispatcher.handlers["douyin"] = handler
  dispatcher.executors["douyin"] = InlineExecutor()
  dispatcher.executors["other"] = InlineExecutor()
  return dispatcher


class DispatcherContextTest(unittest.TestCase):
  def test_a_dispatch_without_a_context_still_works(self):
    seen = []
    dispatcher = build_dispatcher(handler=lambda token, context=None: seen.append(context))

    dispatcher.dispatch({"urls": [VIDEO_URL]})

    ##
    ## The call every existing script and test makes. It must keep working, and
    ## the handler must see "no dependencies supplied".
    ##
    self.assertEqual([None], seen)

  def test_a_context_reaches_the_handler(self):
    seen = []
    dispatcher = build_dispatcher(handler=lambda token, context=None: seen.append(context))
    context = {"direct_post_service": object()}

    dispatcher.dispatch({"urls": [VIDEO_URL]}, context=context)

    self.assertEqual(1, len(seen))
    self.assertIs(context["direct_post_service"], seen[0]["direct_post_service"])

  def test_the_context_stays_out_of_the_token(self):
    seen = []
    dispatcher = build_dispatcher(handler=lambda token, context=None: seen.append(token))

    dispatcher.dispatch(
      {"urls": [VIDEO_URL], "score": 80}, context={"direct_post_service": object()}
    )

    ##
    ## The token is user data on its way to logs, downloaders and the database.
    ## A service object inside it would travel with it.
    ##
    token = seen[0]
    self.assertEqual({"url", "score", "favorite"}, set(token))
    self.assertEqual(VIDEO_URL, token["url"])

  def test_the_dispatcher_keeps_no_memory_of_a_context(self):
    seen = []
    dispatcher = build_dispatcher(handler=lambda token, context=None: seen.append(context))
    first = {"direct_post_service": "A"}

    dispatcher.dispatch({"urls": [VIDEO_URL]}, context=first)
    dispatcher.dispatch({"urls": [VIDEO_URL]})

    ##
    ## The dispatcher is a process-wide singleton and the dependency belongs to
    ## one application.  Anything remembered between dispatches would be handed
    ## to whoever dispatched next.
    ##
    self.assertEqual([first, None], seen)

  def test_two_contexts_in_a_row_do_not_bleed(self):
    seen = []
    dispatcher = build_dispatcher(handler=lambda token, context=None: seen.append(context))

    dispatcher.dispatch({"urls": [VIDEO_URL]}, context={"direct_post_service": "A"})
    dispatcher.dispatch({"urls": [VIDEO_URL]}, context={"direct_post_service": "B"})

    self.assertEqual(["A", "B"], [entry["direct_post_service"] for entry in seen])

  def test_every_url_of_one_dispatch_carries_the_same_context(self):
    seen = []
    dispatcher = build_dispatcher(handler=lambda token, context=None: seen.append(context))
    context = {"direct_post_service": object()}

    dispatcher.dispatch({"urls": [VIDEO_URL, VIDEO_URL]}, context=context)

    self.assertEqual(2, len(seen))
    self.assertTrue(all(entry is context for entry in seen))

  def test_a_handler_of_another_platform_tolerates_a_context(self):
    dispatcher = build_dispatcher()

    ##
    ## ``other`` is a stub today, but it is called with whatever the dispatcher
    ## passes, so its signature has to accept the context too.
    ##
    dispatcher.dispatch(
      {"urls": ["https://other.example/x"]}, context={"direct_post_service": object()}
    )

  def test_a_rejected_payload_is_still_rejected(self):
    dispatcher = build_dispatcher()

    with self.assertRaises(ValueError):
      dispatcher.dispatch(None, context={"direct_post_service": object()})
    with self.assertRaises(ValueError):
      dispatcher.dispatch({"urls": []}, context={"direct_post_service": object()})


class DispatchToTaskTest(unittest.TestCase):
  """The whole propagation, from a dispatched payload to a recorded task."""

  def setUp(self):
    self._original_request = handler_module.request
    handler_module.request = lambda method, url, *a, **k: FakeResponse(VIDEO_URL)
    self.addCleanup(self._restore)

  def _restore(self):
    handler_module.request = self._original_request

  def build_runner(self, tasks):
    downloader = FakeDownloader()
    return DirectPostDownloadTaskService(
      task_service=tasks,
      downloader_factory=lambda: downloader,
      executor_factory=lambda *a, **k: InlineExecutor(),
    ), downloader

  def test_a_dispatched_post_becomes_a_task(self):
    tasks = TaskService()
    runner, downloader = self.build_runner(tasks)
    dispatcher = build_dispatcher()

    dispatcher.dispatch(
      {"urls": [SHARE_URL]}, context={"direct_post_service": runner}
    )

    listed = tasks.list_tasks()
    self.assertEqual(1, len(listed))
    self.assertEqual(TASK_TYPE_POST_DOWNLOAD, listed[0]["task_type"])
    self.assertEqual(AWEME_ID, listed[0]["metadata"]["aweme_id"])
    self.assertEqual(SHARE_URL, listed[0]["metadata"]["source_url"])
    self.assertEqual(1, len(downloader.calls))

  def test_a_dispatch_without_a_runner_records_nothing(self):
    tasks = TaskService()
    dispatcher = build_dispatcher()
    submitted = []
    original = handler_module.download_multiple_aweme
    handler_module.download_multiple_aweme = submitted.append
    self.addCleanup(lambda: setattr(handler_module, "download_multiple_aweme", original))

    dispatcher.dispatch({"urls": [SHARE_URL]})

    self.assertEqual([], tasks.list_tasks())
    self.assertEqual(1, len(submitted))


class CrossApplicationIsolationTest(unittest.TestCase):
  """Two applications in one interpreter must not see each other's tasks.

  ``PlatformDispatcher`` is a process-wide singleton while a task service belongs
  to one Flask application.  If the dependency were held on the dispatcher, the
  second application to start would inherit - or overwrite - the first one's
  store, and each would report downloads the other performed.
  """

  def setUp(self):
    self._original_request = handler_module.request
    handler_module.request = lambda method, url, *a, **k: FakeResponse(VIDEO_URL)
    self.addCleanup(self._restore)

  def _restore(self):
    handler_module.request = self._original_request

  def build_runner(self, tasks):
    downloader = FakeDownloader()
    return DirectPostDownloadTaskService(
      task_service=tasks,
      downloader_factory=lambda: downloader,
      executor_factory=lambda *a, **k: InlineExecutor(),
    )

  def test_a_post_dispatched_for_one_application_stays_there(self):
    first_tasks = TaskService()
    second_tasks = TaskService()
    dispatcher = build_dispatcher()

    dispatcher.dispatch(
      {"urls": [SHARE_URL]},
      context={"direct_post_service": self.build_runner(first_tasks)},
    )

    self.assertEqual(1, len(first_tasks.list_tasks()))
    self.assertEqual([], second_tasks.list_tasks())

  def test_each_application_only_ever_sees_its_own(self):
    first_tasks = TaskService()
    second_tasks = TaskService()
    dispatcher = build_dispatcher()
    first_runner = self.build_runner(first_tasks)
    second_runner = self.build_runner(second_tasks)

    dispatcher.dispatch({"urls": [SHARE_URL]}, context={"direct_post_service": first_runner})
    dispatcher.dispatch({"urls": [SHARE_URL]}, context={"direct_post_service": second_runner})
    dispatcher.dispatch({"urls": [SHARE_URL]}, context={"direct_post_service": first_runner})

    self.assertEqual(2, len(first_tasks.list_tasks()))
    self.assertEqual(1, len(second_tasks.list_tasks()))

  def test_the_same_dispatcher_instance_serves_both(self):
    ##
    ## Proving the isolation is not an accident of two dispatchers existing: the
    ## singleton hands back one object, and it is the context that differs.
    ##
    self.assertIs(PlatformDispatcher(), PlatformDispatcher())


class DirectPostTaskCentreTest(unittest.TestCase):
  """What the task centre can answer about a pasted post link."""

  def setUp(self):
    self._original_request = handler_module.request
    handler_module.request = lambda method, url, *a, **k: FakeResponse(VIDEO_URL)
    self.addCleanup(self._restore)

  def _restore(self):
    handler_module.request = self._original_request

  def build_app(self):
    from flask import Flask

    from backend.src.web.task_routes import build_task_blueprint, install_task_service

    app = Flask(__name__)
    tasks = install_task_service(app)
    app.register_blueprint(build_task_blueprint())
    downloader = FakeDownloader()
    runner = DirectPostDownloadTaskService(
      task_service=tasks,
      downloader_factory=lambda: downloader,
      executor_factory=lambda *a, **k: InlineExecutor(),
    )
    return app.test_client(), tasks, runner

  def test_a_pasted_post_can_be_found_by_type(self):
    from backend.src.task.model import (
      TASK_TYPE_LIVE_PROBE,
      TASK_TYPE_OWNER_BATCH_DOWNLOAD,
    )

    client, tasks, runner = self.build_app()
    ##
    ## The other two businesses write straight onto the same service, as their
    ## own mirrors do.
    ##
    tasks.create_task(TASK_TYPE_OWNER_BATCH_DOWNLOAD, title="下载主播作品")
    tasks.create_task(TASK_TYPE_LIVE_PROBE, title="检查主播直播状态")
    build_dispatcher().dispatch(
      {"urls": [SHARE_URL]}, context={"direct_post_service": runner}
    )

    listed = client.get("/api/tasks?type=post_download").get_json()["data"]

    self.assertEqual(1, listed["total"])
    self.assertEqual(TASK_TYPE_POST_DOWNLOAD, listed["items"][0]["task_type"])

  def test_all_three_businesses_share_one_store(self):
    from backend.src.task.model import (
      TASK_TYPE_LIVE_PROBE,
      TASK_TYPE_OWNER_BATCH_DOWNLOAD,
    )

    client, tasks, runner = self.build_app()
    tasks.create_task(TASK_TYPE_OWNER_BATCH_DOWNLOAD, title="下载主播作品")
    tasks.create_task(TASK_TYPE_LIVE_PROBE, title="检查主播直播状态")
    build_dispatcher().dispatch(
      {"urls": [SHARE_URL]}, context={"direct_post_service": runner}
    )

    listed = client.get("/api/tasks").get_json()["data"]

    self.assertEqual(3, listed["total"])
    self.assertEqual(
      {TASK_TYPE_OWNER_BATCH_DOWNLOAD, TASK_TYPE_LIVE_PROBE, TASK_TYPE_POST_DOWNLOAD},
      {task["task_type"] for task in listed["items"]},
    )

  def test_the_task_says_which_link_it_came_from(self):
    client, tasks, runner = self.build_app()
    build_dispatcher().dispatch(
      {"urls": [SHARE_URL]}, context={"direct_post_service": runner}
    )

    task_id = client.get("/api/tasks?type=post_download").get_json()["data"]["items"][0][
      "task_id"
    ]
    task = client.get("/api/tasks/{}".format(task_id)).get_json()["data"]

    ##
    ## Until a submission can answer with its own task id, this metadata is how a
    ## caller matches a task back to the link it pasted.
    ##
    self.assertEqual("douyin", task["metadata"]["platform"])
    self.assertEqual("direct", task["metadata"]["source"])
    self.assertEqual(SHARE_URL, task["metadata"]["source_url"])
    self.assertEqual(VIDEO_URL, task["metadata"]["resolved_url"])
    self.assertEqual(AWEME_ID, task["metadata"]["aweme_id"])

  def test_the_finished_task_is_json_serialisable(self):
    import json

    from backend.src.platform.douyin.douyin_aweme_downloader import AwemeDownloadResult

    client, tasks, runner = self.build_app()
    runner._downloader_factory = lambda: FakeDownloader(
      result=AwemeDownloadResult(
        ok=True,
        aweme_id=AWEME_ID,
        save_dir="/media/douyin/A/post",
        media_count=2,
        saved_count=2,
      )
    )
    build_dispatcher().dispatch(
      {"urls": [SHARE_URL]}, context={"direct_post_service": runner}
    )

    response = client.get("/api/tasks?type=post_download")

    self.assertEqual(200, response.status_code)
    json.dumps(response.get_json())


if __name__ == "__main__":
  unittest.main()
