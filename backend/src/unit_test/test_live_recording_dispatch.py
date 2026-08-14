import json
import unittest
from concurrent.futures import Future

from backend.src.platform.douyin import douyin_handler as handler_module
from backend.src.platform.douyin.douyin_live_downloader import LiveDownloadResult
from backend.src.platform.platform_dispatcher import PlatformDispatcher
from backend.src.service.live_recording_task import LiveRecordingTaskService
from backend.src.task.model import (
  TASK_STATE_SUCCESS,
  TASK_TYPE_LIVE_PROBE,
  TASK_TYPE_LIVE_RECORD,
  TASK_TYPE_OWNER_BATCH_DOWNLOAD,
  TASK_TYPE_POST_DOWNLOAD,
)
from backend.src.task.service import TaskService

SHARE_URL = "https://v.douyin.com/abc/"
ROOM_URL = "https://live.douyin.com/123456"
SIGNED_STREAM = "https://pull.example.test/live.flv?sign=SECRETSIG&token=SECRETTOK"


class InlineExecutor:
  def submit(self, fn, *args, **kwargs):
    future = Future()
    try:
      future.set_result(fn(*args, **kwargs))
    except BaseException as e:
      future.set_exception(e)
    return future


class InlineListenerItem:
  def __init__(self, func=None, args=None):
    self.func = func
    self.args = args

  def start_item(self):
    self.func(*self.args)


class FakeResponse:
  def __init__(self, url, status_code=200):
    self.url = url
    self.status_code = status_code


class FakeLiveDownloader:
  def __init__(self, result=None):
    self.result = result
    self.calls = []

  def run_with_result(self, token):
    self.calls.append(token)
    if self.result is not None:
      return self.result
    return LiveDownloadResult(
      ok=True,
      recorded=True,
      room_status=2,
      room_id="998877",
      owner_user_id="owner-1",
      nickname="Test Host",
      protocol="flv",
      output_path="/media/douyin/live/Test Host/live.flv",
    )


def build_dispatcher():
  dispatcher = PlatformDispatcher()
  dispatcher.register()
  dispatcher.executors["douyin"] = InlineExecutor()
  dispatcher.executors["other"] = InlineExecutor()
  return dispatcher


def build_recorder(tasks, downloader=None):
  downloader = downloader if downloader is not None else FakeLiveDownloader()
  return (
    LiveRecordingTaskService(
      task_service=tasks,
      downloader_factory=lambda: downloader,
      listener_factory=InlineListenerItem,
    ),
    downloader,
  )


class LiveDispatchTestCase(unittest.TestCase):
  def setUp(self):
    self._original_request = handler_module.request
    handler_module.request = lambda method, url, *a, **k: FakeResponse(ROOM_URL)
    self.addCleanup(self._restore)

  def _restore(self):
    handler_module.request = self._original_request


class DispatchToLiveTaskTest(LiveDispatchTestCase):
  def test_a_dispatched_live_room_becomes_a_task(self):
    tasks = TaskService()
    recorder, downloader = build_recorder(tasks)

    build_dispatcher().dispatch(
      {"urls": [SHARE_URL]}, context={"live_record_service": recorder}
    )

    listed = tasks.list_tasks()
    self.assertEqual(1, len(listed))
    self.assertEqual(TASK_TYPE_LIVE_RECORD, listed[0]["task_type"])
    self.assertEqual(SHARE_URL, listed[0]["metadata"]["source_url"])
    self.assertEqual(ROOM_URL, listed[0]["metadata"]["resolved_url"])
    self.assertEqual(1, len(downloader.calls))

  def test_every_room_of_one_submission_gets_its_own_task(self):
    tasks = TaskService()
    recorder, downloader = build_recorder(tasks)

    build_dispatcher().dispatch(
      {"urls": [SHARE_URL, SHARE_URL, SHARE_URL]},
      context={"live_record_service": recorder},
    )

    ##
    ## Legacy semantics: one listener per link, so one task per link, even when
    ## the same room is submitted more than once.
    ##
    self.assertEqual(3, len(tasks.list_tasks()))
    self.assertEqual(3, len(downloader.calls))

  def test_a_dispatch_without_a_recorder_records_nothing(self):
    tasks = TaskService()
    submitted = []
    original = handler_module.download_multiple_live
    handler_module.download_multiple_live = submitted.append
    self.addCleanup(
      lambda: setattr(handler_module, "download_multiple_live", original)
    )

    build_dispatcher().dispatch({"urls": [SHARE_URL]})

    self.assertEqual([], tasks.list_tasks())
    self.assertEqual(1, len(submitted))


class LiveCrossApplicationIsolationTest(LiveDispatchTestCase):
  """Two applications must not see each other's recordings.

  Both the dispatcher and the live downloader are process-wide singletons, while
  a task service belongs to one Flask application.  The dependency therefore
  travels with each dispatch and is never stored on either singleton.
  """

  def test_a_recording_dispatched_for_one_application_stays_there(self):
    first_tasks = TaskService()
    second_tasks = TaskService()
    recorder, downloader = build_recorder(first_tasks)

    build_dispatcher().dispatch(
      {"urls": [SHARE_URL]}, context={"live_record_service": recorder}
    )

    self.assertEqual(1, len(first_tasks.list_tasks()))
    self.assertEqual([], second_tasks.list_tasks())

  def test_each_application_only_ever_sees_its_own(self):
    first_tasks = TaskService()
    second_tasks = TaskService()
    first_recorder, unused = build_recorder(first_tasks)
    second_recorder, unused_too = build_recorder(second_tasks)
    dispatcher = build_dispatcher()

    dispatcher.dispatch({"urls": [SHARE_URL]}, context={"live_record_service": first_recorder})
    dispatcher.dispatch({"urls": [SHARE_URL]}, context={"live_record_service": second_recorder})
    dispatcher.dispatch({"urls": [SHARE_URL]}, context={"live_record_service": first_recorder})

    self.assertEqual(2, len(first_tasks.list_tasks()))
    self.assertEqual(1, len(second_tasks.list_tasks()))

  def test_the_singletons_really_are_shared(self):
    ##
    ## Proving the isolation comes from the context rather than from two
    ## dispatchers happening to exist.
    ##
    self.assertIs(PlatformDispatcher(), PlatformDispatcher())


class LiveTaskCentreTest(LiveDispatchTestCase):
  def build_app(self, downloader=None):
    from flask import Flask

    from backend.src.web.task_routes import build_task_blueprint, install_task_service

    app = Flask(__name__)
    tasks = install_task_service(app)
    app.register_blueprint(build_task_blueprint())
    recorder, chosen = build_recorder(tasks, downloader=downloader)
    return app.test_client(), tasks, recorder

  def test_a_recording_can_be_found_by_type(self):
    client, tasks, recorder = self.build_app()
    build_dispatcher().dispatch(
      {"urls": [SHARE_URL]}, context={"live_record_service": recorder}
    )

    listed = client.get("/api/tasks?type=live_record").get_json()["data"]

    self.assertEqual(1, listed["total"])
    self.assertEqual(TASK_TYPE_LIVE_RECORD, listed["items"][0]["task_type"])
    self.assertEqual(TASK_STATE_SUCCESS, listed["items"][0]["state"])

  def test_all_four_businesses_share_one_store(self):
    client, tasks, recorder = self.build_app()
    tasks.create_task(TASK_TYPE_OWNER_BATCH_DOWNLOAD, title="下载主播作品")
    tasks.create_task(TASK_TYPE_LIVE_PROBE, title="检查主播直播状态")
    tasks.create_task(TASK_TYPE_POST_DOWNLOAD, title="下载作品")
    build_dispatcher().dispatch(
      {"urls": [SHARE_URL]}, context={"live_record_service": recorder}
    )

    listed = client.get("/api/tasks").get_json()["data"]

    self.assertEqual(4, listed["total"])
    self.assertEqual(
      {
        TASK_TYPE_OWNER_BATCH_DOWNLOAD,
        TASK_TYPE_LIVE_PROBE,
        TASK_TYPE_POST_DOWNLOAD,
        TASK_TYPE_LIVE_RECORD,
      },
      {task["task_type"] for task in listed["items"]},
    )

  def test_the_recording_says_where_it_wrote(self):
    client, tasks, recorder = self.build_app()
    build_dispatcher().dispatch(
      {"urls": [SHARE_URL]}, context={"live_record_service": recorder}
    )

    task_id = client.get("/api/tasks?type=live_record").get_json()["data"]["items"][0][
      "task_id"
    ]
    task = client.get("/api/tasks/{}".format(task_id)).get_json()["data"]

    result = task["metadata"]["result"]
    self.assertEqual("/media/douyin/live/Test Host/live.flv", result["output_path"])
    self.assertEqual("flv", result["protocol"])
    self.assertEqual("living", result["live_status"])
    self.assertIsNone(task["progress"]["total"])
    self.assertEqual([], task["items"])

  def test_a_signed_stream_url_never_reaches_the_api(self):
    downloader = FakeLiveDownloader(
      result=LiveDownloadResult(
        ok=True,
        recorded=True,
        room_status=2,
        room_id="998877",
        nickname="Test Host",
        protocol="flv",
        output_path="/media/douyin/live/Test Host/live.flv",
      )
    )
    client, tasks, recorder = self.build_app(downloader=downloader)
    build_dispatcher().dispatch(
      {"urls": [SHARE_URL]},
      context={"live_record_service": recorder},
    )

    body = json.dumps(client.get("/api/tasks").get_json())

    ##
    ## The stream url is signed - it grants access to the broadcast - so nothing
    ## derived from it may appear in anything a browser can read.
    ##
    self.assertNotIn("sign=", body)
    self.assertNotIn("token=", body)
    self.assertNotIn("SECRETSIG", body)
    self.assertNotIn("stream_url", body)
    self.assertNotIn(".flv?", body)

  def test_the_task_payload_is_json_serialisable(self):
    client, tasks, recorder = self.build_app()
    build_dispatcher().dispatch(
      {"urls": [SHARE_URL]}, context={"live_record_service": recorder}
    )

    response = client.get("/api/tasks?type=live_record")

    self.assertEqual(200, response.status_code)
    json.dumps(response.get_json())


if __name__ == "__main__":
  unittest.main()
