import unittest
from concurrent.futures import Future

from backend.src.platform.douyin.douyin_aweme_downloader import AwemeDownloadResult
from backend.src.service.direct_post_download_task import (
  PLATFORM_DOUYIN,
  SOURCE_DIRECT,
  SOURCE_TASK_API,
  DirectPostDownloadTaskService,
)
from backend.src.platform.douyin.douyin_live_downloader import LiveDownloadResult
from backend.src.service.live_recording_task import (
  LiveRecordingTaskService,
)
from backend.src.service.live_recording_task import (
  SOURCE_TASK_API as LIVE_SOURCE_TASK_API,
)
from backend.src.service.task_creation import TaskCreationUnavailable
from backend.src.task.model import (
  TASK_STATE_FAILED,
  TASK_TYPE_LIVE_RECORD,
  TASK_TYPE_POST_DOWNLOAD,
  is_terminal,
)
from backend.src.task.service import TaskService


SOURCE_URL = "https://v.douyin.com/M-kmspLye0o/"
RESOLVED_URL = "https://www.douyin.com/video/7657271784144009946"
AWEME_ID = "7657271784144009946"
RESOLVE_ID = "receipt-1"


def complete_result():
  return AwemeDownloadResult(
    ok=True,
    aweme_id=AWEME_ID,
    save_dir="/media/douyin/A/post",
    media_count=1,
    saved_count=1,
  )


class FakeConfig:
  def __init__(self, concurrency=3):
    self.concurrency = concurrency


class FakeDownloader:
  """Stands in for DouyinAwemeDownloader: one post per ``run`` call."""

  def __init__(self, result=None, crash=None, concurrency=3, link_error=None):
    self._result = result
    self._crash = crash
    self.config = FakeConfig(concurrency)
    self.calls = []
    self.links = []
    self.link_error = link_error

  def run(self, token):
    self.calls.append(token)
    if self._crash is not None:
      raise self._crash
    return self._result if self._result is not None else complete_result()

  def link_post(self, app_user_id, aweme_id):
    self.links.append((app_user_id, aweme_id))
    if self.link_error is not None:
      raise self.link_error


class ImmediateExecutor:
  """Runs work inline but still answers with a Future, as a real pool does."""

  def __init__(self):
    self.submitted = 0

  def submit(self, fn, *args, **kwargs):
    self.submitted += 1
    future = Future()
    try:
      future.set_result(fn(*args, **kwargs))
    except BaseException as e:
      future.set_exception(e)
    return future


class RawInlineExecutor:
  """Runs work inline and lets the worker's exception travel out of ``submit``.

  Not how the production pool behaves, and that is the point: the tracked path
  must be able to tell "the pool refused the work" from "the work ran and
  failed", and only an executor shaped like this can prove it does.
  """

  def __init__(self):
    self.submitted = 0

  def submit(self, fn, *args, **kwargs):
    self.submitted += 1
    return fn(*args, **kwargs)


class DeferredExecutor:
  """Queues work so the state before a worker starts can be observed."""

  def __init__(self):
    self.queued = []

  def submit(self, fn, *args, **kwargs):
    future = Future()
    self.queued.append((future, fn, args, kwargs))
    return future

  def drain(self):
    pending, self.queued = self.queued, []
    for future, fn, args, kwargs in pending:
      try:
        future.set_result(fn(*args, **kwargs))
      except BaseException as e:
        future.set_exception(e)


class RefusingExecutor:
  """A pool that has been shut down, or is otherwise refusing work."""

  def __init__(self, failure=None):
    self.failure = failure or RuntimeError("cannot schedule new futures")
    self.submitted = 0

  def submit(self, *args, **kwargs):
    self.submitted += 1
    raise self.failure


class RefusingTaskService(TaskService):
  """A task layer that cannot record anything."""

  def __init__(self, failure=None):
    super().__init__()
    self.failure = failure or RuntimeError("task store unavailable")
    self.create_calls = 0

  def create_task(self, *args, **kwargs):
    self.create_calls += 1
    raise self.failure


def build_service(downloader=None, executor=None, task_service=None):
  downloader = downloader if downloader is not None else FakeDownloader()
  executor = executor if executor is not None else ImmediateExecutor()
  service = DirectPostDownloadTaskService(
    task_service=task_service,
    downloader_factory=lambda: downloader,
    executor_factory=lambda *args, **kwargs: executor,
  )
  return service, downloader, executor


def tracked(service, **overrides):
  call = {
    "aweme_id": AWEME_ID,
    "resolved_url": RESOLVED_URL,
    "source_url": SOURCE_URL,
    "resolve_id": RESOLVE_ID,
  }
  call.update(overrides)
  return service.submit_tracked(**call)


class PostTrackedCreationTest(unittest.TestCase):
  def test_owned_post_is_linked_before_the_task_finishes(self):
    tasks = TaskService()
    service, downloader, _ = build_service(task_service=tasks)

    task_id = tracked(service, app_user_id=41)

    task = tasks.get_task(task_id)
    self.assertEqual(task["app_user_id"], 41)
    self.assertEqual(downloader.links, [(41, AWEME_ID)])
    self.assertEqual(task["state"], "success")
    self.assertIs(task["metadata"]["result"]["ownership_linked"], True)

  def test_ownership_failure_keeps_files_but_prevents_false_full_success(self):
    tasks = TaskService()
    downloader = FakeDownloader(link_error=RuntimeError("foreign key failed"))
    service, _, _ = build_service(downloader=downloader, task_service=tasks)

    task_id = tracked(service, app_user_id=41)

    task = tasks.get_task(task_id)
    self.assertEqual(task["state"], "partial")
    self.assertIs(task["metadata"]["result"]["ownership_linked"], False)
    self.assertNotIn("foreign key", task["message"])

  def test_failed_post_never_creates_ownership(self):
    tasks = TaskService()
    downloader = FakeDownloader(
      result=AwemeDownloadResult(ok=False, aweme_id=AWEME_ID, reason="deleted")
    )
    service, _, _ = build_service(downloader=downloader, task_service=tasks)

    tracked(service, app_user_id=41)

    self.assertEqual(downloader.links, [])

  def test_zero_saved_non_skipped_post_never_creates_ownership(self):
    tasks = TaskService()
    downloader = FakeDownloader(
      result=AwemeDownloadResult(
        ok=True,
        aweme_id=AWEME_ID,
        media_count=0,
        saved_count=0,
      )
    )
    service, _, _ = build_service(downloader=downloader, task_service=tasks)

    task_id = tracked(service, app_user_id=41)

    self.assertEqual(downloader.links, [])
    self.assertEqual(tasks.get_task(task_id)["state"], "failed")

  def test_partial_and_already_downloaded_results_are_owned(self):
    results = (
      AwemeDownloadResult(
        ok=True,
        aweme_id=AWEME_ID,
        media_count=3,
        saved_count=2,
      ),
      AwemeDownloadResult(
        ok=True,
        aweme_id=AWEME_ID,
        media_count=3,
        saved_count=3,
        skipped=True,
      ),
    )
    for result in results:
      with self.subTest(result=result):
        tasks = TaskService()
        downloader = FakeDownloader(result=result)
        service, _, _ = build_service(downloader=downloader, task_service=tasks)

        tracked(service, app_user_id=41)

        self.assertEqual(downloader.links, [(41, AWEME_ID)])

  """The accepted request produces a task that can be watched."""

  def test_it_answers_with_the_id_of_a_post_download_task(self):
    tasks = TaskService()
    service, _, _ = build_service(task_service=tasks)

    task_id = tracked(service)

    task = tasks.get_task(task_id)
    self.assertIsNotNone(task)
    self.assertEqual(task["task_type"], TASK_TYPE_POST_DOWNLOAD)

  def test_the_task_records_where_the_request_came_from(self):
    tasks = TaskService()
    service, _, _ = build_service(
      task_service=tasks, executor=DeferredExecutor()
    )

    task_id = tracked(service)

    metadata = tasks.get_task(task_id)["metadata"]
    self.assertEqual(metadata["platform"], PLATFORM_DOUYIN)
    self.assertEqual(metadata["source"], SOURCE_TASK_API)
    self.assertEqual(metadata["resolve_id"], RESOLVE_ID)
    self.assertEqual(metadata["source_url"], SOURCE_URL)
    self.assertEqual(metadata["resolved_url"], RESOLVED_URL)
    self.assertEqual(metadata["aweme_id"], AWEME_ID)

  def test_the_task_api_source_is_distinct_from_the_legacy_one(self):
    """Two entry points to one business; the record has to say which ran."""
    self.assertEqual(SOURCE_TASK_API, "task_api")
    self.assertNotEqual(SOURCE_TASK_API, SOURCE_DIRECT)

  def test_the_downloader_runs_against_the_resolved_url(self):
    """The short link was followed once already, by the resolver, safely."""
    tasks = TaskService()
    service, downloader, _ = build_service(task_service=tasks)

    tracked(service)

    token = downloader.calls[0]
    self.assertEqual(token["url"], RESOLVED_URL)
    self.assertEqual(token["resolved_url"], RESOLVED_URL)
    self.assertEqual(token["aweme_id"], AWEME_ID)

  def test_the_execution_token_never_carries_the_short_link(self):
    tasks = TaskService()
    service, downloader, _ = build_service(task_service=tasks)

    tracked(service)

    self.assertNotIn(SOURCE_URL, downloader.calls[0].values())


class PostStrictCreationTest(unittest.TestCase):
  """The invariant this endpoint exists to keep: no task, no work."""

  def test_a_task_layer_that_refuses_starts_nothing(self):
    """``POST /api/tasks`` promises an observable task.  If none was created
    the honest answer is an error - not a download nobody can see."""
    refusing = RefusingTaskService()
    service, downloader, executor = build_service(task_service=refusing)

    with self.assertRaises(TaskCreationUnavailable):
      tracked(service)

    self.assertEqual(refusing.create_calls, 1)
    self.assertEqual(downloader.calls, [], "nothing may be downloaded")
    self.assertEqual(executor.submitted, 0, "nothing may be scheduled")

  def test_an_unwired_task_service_starts_nothing(self):
    service, downloader, executor = build_service(task_service=None)

    with self.assertRaises(TaskCreationUnavailable):
      tracked(service)

    self.assertEqual(downloader.calls, [])
    self.assertEqual(executor.submitted, 0)

  def test_the_refusal_is_raised_before_the_pool_is_touched(self):
    refusing = RefusingTaskService()
    executor = RefusingExecutor()
    service, downloader, _ = build_service(
      task_service=refusing, executor=executor
    )

    with self.assertRaises(TaskCreationUnavailable):
      tracked(service)

    self.assertEqual(executor.submitted, 0)


class PostSchedulingFailureTest(unittest.TestCase):
  """A task that exists but could not be scheduled ends, it does not linger."""

  def test_the_task_id_is_still_answered(self):
    """The server did create something observable; it just failed at once.

    Answering with an error instead would leave the caller unable to tell
    whether a task exists to look at.
    """
    tasks = TaskService()
    service, downloader, _ = build_service(
      task_service=tasks, executor=RefusingExecutor()
    )

    task_id = tracked(service)

    self.assertIsNotNone(task_id)
    self.assertIsNotNone(tasks.get_task(task_id))

  def test_the_task_is_ended_as_failed(self):
    """Only finished tasks are ever reclaimed, so one left pending would stay
    for the life of the process describing work nobody is doing."""
    tasks = TaskService()
    service, _, _ = build_service(
      task_service=tasks, executor=RefusingExecutor()
    )

    task_id = tracked(service)

    task = tasks.get_task(task_id)
    self.assertEqual(task["state"], TASK_STATE_FAILED)
    self.assertTrue(is_terminal(task["state"]))

  def test_nothing_was_downloaded(self):
    tasks = TaskService()
    service, downloader, _ = build_service(
      task_service=tasks, executor=RefusingExecutor()
    )

    tracked(service)

    self.assertEqual(downloader.calls, [])


class PostInlineWorkerTest(unittest.TestCase):
  """A worker that finishes inside ``submit`` has still been accepted."""

  def test_an_inline_success_still_answers_with_the_task_id(self):
    tasks = TaskService()
    service, _, _ = build_service(task_service=tasks)

    task_id = tracked(service)

    self.assertIsNotNone(task_id)
    self.assertEqual(tasks.get_task(task_id)["state"], "success")

  def test_an_inline_crash_is_not_mistaken_for_a_scheduling_failure(self):
    """The worker ran and failed, and has already said so on the task.

    Reporting "not scheduled" over the top would overwrite a truthful ending
    with a false one - and, worse, make the api claim no task was created.
    """
    tasks = TaskService()
    service, downloader, _ = build_service(
      task_service=tasks,
      downloader=FakeDownloader(crash=RuntimeError("boom")),
      executor=RawInlineExecutor(),
    )

    task_id = tracked(service)

    self.assertIsNotNone(task_id)
    task = tasks.get_task(task_id)
    self.assertEqual(task["state"], TASK_STATE_FAILED)
    self.assertEqual(len(downloader.calls), 1, "the work really did run")


class PostLegacyContractTest(unittest.TestCase):
  """``submit`` keeps the best-effort behaviour every earlier stage relies on."""

  def legacy_token(self):
    return {"url": SOURCE_URL, "resolved_url": RESOLVED_URL, "aweme_id": AWEME_ID}

  def test_it_still_answers_with_a_future(self):
    tasks = TaskService()
    service, _, _ = build_service(task_service=tasks)

    future = service.submit(self.legacy_token())

    self.assertIsInstance(future, Future)

  def test_a_refusing_task_layer_does_not_stop_the_download(self):
    """Telemetry, never workflow.  This is the rule the legacy path keeps and
    the tracked path deliberately does not."""
    refusing = RefusingTaskService()
    service, downloader, executor = build_service(task_service=refusing)

    future = service.submit(self.legacy_token())

    self.assertIsNotNone(future)
    self.assertEqual(len(downloader.calls), 1)
    self.assertEqual(executor.submitted, 1)

  def test_it_still_records_the_legacy_source(self):
    tasks = TaskService()
    service, _, _ = build_service(
      task_service=tasks, executor=DeferredExecutor()
    )

    service.submit(self.legacy_token())

    task = tasks.list_tasks()[0]
    self.assertEqual(task["metadata"]["source"], SOURCE_DIRECT)

  def test_it_still_downloads_against_the_url_it_was_given(self):
    tasks = TaskService()
    service, downloader, _ = build_service(task_service=tasks)

    service.submit(self.legacy_token())

    self.assertEqual(downloader.calls[0]["url"], SOURCE_URL)


LIVE_URL = "https://live.douyin.com/123456"


def recorded_result():
  return LiveDownloadResult(
    ok=True, recorded=True, room_status=2, room_id="998877", protocol="flv"
  )


class FakeLiveDownloader:
  def __init__(self, result=None, crash=None):
    self._result = result
    self._crash = crash
    self.calls = []

  def run_with_result(self, token):
    self.calls.append(token)
    if self._crash is not None:
      raise self._crash
    return self._result if self._result is not None else recorded_result()


class InlineListenerItem:
  """A listener whose thread runs inline, letting the worker's error travel out."""

  def __init__(self, func=None, args=None):
    if not isinstance(args, tuple):
      raise ValueError("args must be a tuple")
    self.func = func
    self.args = args
    self.started = False

  def start_item(self):
    self.started = True
    self.func(*self.args)


class DeferredListenerItem:
  """A listener that does not run until told, so queued state can be observed."""

  created = []

  def __init__(self, func=None, args=None):
    self.func = func
    self.args = args
    self.started = False
    DeferredListenerItem.created.append(self)

  def start_item(self):
    self.started = True

  def run_now(self):
    self.func(*self.args)


class RefusingListenerItem:
  """A listener whose thread cannot be started."""

  started = 0

  def __init__(self, func=None, args=None):
    self.func = func
    self.args = args

  def start_item(self):
    RefusingListenerItem.started += 1
    raise RuntimeError("can't start new thread")


def build_live_service(downloader=None, task_service=None,
                       listener=InlineListenerItem):
  downloader = downloader if downloader is not None else FakeLiveDownloader()
  service = LiveRecordingTaskService(
    task_service=task_service,
    downloader_factory=lambda: downloader,
    listener_factory=listener,
  )
  return service, downloader


def tracked_live(service, **overrides):
  call = {
    "resolved_url": LIVE_URL,
    "source_url": SOURCE_URL,
    "resolve_id": RESOLVE_ID,
  }
  call.update(overrides)
  return service.submit_tracked(**call)


class LiveTrackedCreationTest(unittest.TestCase):
  """A recording asked for through the task api is a task from the outset."""

  def test_it_answers_with_the_id_of_a_live_record_task(self):
    tasks = TaskService()
    service, _ = build_live_service(
      task_service=tasks, listener=DeferredListenerItem
    )

    task_id = tracked_live(service)

    task = tasks.get_task(task_id)
    self.assertIsNotNone(task)
    self.assertEqual(task["task_type"], TASK_TYPE_LIVE_RECORD)

  def test_the_task_records_where_the_request_came_from(self):
    tasks = TaskService()
    service, _ = build_live_service(
      task_service=tasks, listener=DeferredListenerItem
    )

    task_id = tracked_live(service)

    metadata = tasks.get_task(task_id)["metadata"]
    self.assertEqual(metadata["platform"], PLATFORM_DOUYIN)
    self.assertEqual(metadata["source"], LIVE_SOURCE_TASK_API)
    self.assertEqual(metadata["resolve_id"], RESOLVE_ID)
    self.assertEqual(metadata["source_url"], SOURCE_URL)
    self.assertEqual(metadata["resolved_url"], LIVE_URL)

  def test_the_recording_runs_against_the_resolved_url(self):
    """P5 already followed the share link.  The recorder starts from where it
    landed rather than resolving the same link a second time."""
    tasks = TaskService()
    service, downloader = build_live_service(task_service=tasks)

    tracked_live(service)

    token = downloader.calls[0]
    self.assertEqual(token["url"], LIVE_URL)
    self.assertEqual(token["resolved_url"], LIVE_URL)

  def test_no_live_probe_is_run_before_the_task_is_created(self):
    """Whether the room is on air is the recording's own question to ask.

    Probing here would spend a second platform request, and the answer would be
    stale by the time the recorder acted on it.
    """
    tasks = TaskService()
    service, downloader = build_live_service(
      task_service=tasks, listener=DeferredListenerItem
    )

    tracked_live(service)

    self.assertEqual(downloader.calls, [])


class LiveStrictCreationTest(unittest.TestCase):
  """No task, no recording thread."""

  def test_a_task_layer_that_refuses_starts_nothing(self):
    refusing = RefusingTaskService()
    RefusingListenerItem.started = 0
    service, downloader = build_live_service(
      task_service=refusing, listener=RefusingListenerItem
    )

    with self.assertRaises(TaskCreationUnavailable):
      tracked_live(service)

    self.assertEqual(refusing.create_calls, 1)
    self.assertEqual(downloader.calls, [])
    self.assertEqual(RefusingListenerItem.started, 0, "no thread may be started")

  def test_an_unwired_task_service_starts_nothing(self):
    RefusingListenerItem.started = 0
    service, downloader = build_live_service(
      task_service=None, listener=RefusingListenerItem
    )

    with self.assertRaises(TaskCreationUnavailable):
      tracked_live(service)

    self.assertEqual(downloader.calls, [])
    self.assertEqual(RefusingListenerItem.started, 0)


class LiveSchedulingFailureTest(unittest.TestCase):
  """A recording thread that never started leaves a finished task, not a stuck one."""

  def test_the_task_id_is_still_answered(self):
    tasks = TaskService()
    service, _ = build_live_service(
      task_service=tasks, listener=RefusingListenerItem
    )

    task_id = tracked_live(service)

    self.assertIsNotNone(task_id)
    self.assertIsNotNone(tasks.get_task(task_id))

  def test_the_task_is_ended_as_failed(self):
    tasks = TaskService()
    service, _ = build_live_service(
      task_service=tasks, listener=RefusingListenerItem
    )

    task_id = tracked_live(service)

    task = tasks.get_task(task_id)
    self.assertEqual(task["state"], TASK_STATE_FAILED)
    self.assertTrue(is_terminal(task["state"]))


class LiveInlineWorkerTest(unittest.TestCase):
  def test_live_recording_task_keeps_its_application_user_only_on_the_task(self):
    tasks = TaskService()
    service, _ = build_live_service(task_service=tasks)

    task_id = tracked_live(service, app_user_id=52)

    self.assertEqual(tasks.get_task(task_id)["app_user_id"], 52)

  """A recording that finishes inside ``start_item`` has still been accepted."""

  def test_an_inline_success_still_answers_with_the_task_id(self):
    tasks = TaskService()
    service, _ = build_live_service(task_service=tasks)

    task_id = tracked_live(service)

    self.assertIsNotNone(task_id)
    self.assertEqual(tasks.get_task(task_id)["state"], "success")

  def test_an_inline_crash_is_not_mistaken_for_a_thread_that_never_started(self):
    tasks = TaskService()
    service, downloader = build_live_service(
      task_service=tasks,
      downloader=FakeLiveDownloader(crash=RuntimeError("stream gone")),
    )

    task_id = tracked_live(service)

    self.assertIsNotNone(task_id)
    self.assertEqual(tasks.get_task(task_id)["state"], TASK_STATE_FAILED)
    self.assertEqual(len(downloader.calls), 1, "the recording really did run")


class LiveLegacyContractTest(unittest.TestCase):
  """``submit`` keeps exactly the behaviour the legacy dispatch relies on."""

  def legacy_token(self):
    return {"url": SOURCE_URL, "resolved_url": LIVE_URL}

  def test_it_still_answers_with_the_listener(self):
    tasks = TaskService()
    service, _ = build_live_service(
      task_service=tasks, listener=DeferredListenerItem
    )

    item = service.submit(self.legacy_token())

    self.assertIsInstance(item, DeferredListenerItem)

  def test_a_refusing_task_layer_does_not_stop_the_recording(self):
    refusing = RefusingTaskService()
    service, downloader = build_live_service(task_service=refusing)

    service.submit(self.legacy_token())

    self.assertEqual(len(downloader.calls), 1)

  def test_it_still_records_the_legacy_source(self):
    tasks = TaskService()
    service, _ = build_live_service(
      task_service=tasks, listener=DeferredListenerItem
    )

    service.submit(self.legacy_token())

    self.assertEqual(tasks.list_tasks()[0]["metadata"]["source"], SOURCE_DIRECT)


##
## >>============================= owner batch =============================>>
##
from backend.src.service.job_store import JOB_ERROR, JOB_RUNNING, JobStore
from backend.src.service.owner_task_mirror import SOURCE_TASK_API as OWNER_SOURCE
from backend.src.service.post_download_job import PayloadCache, PostDownloadJobService
from backend.src.task.model import TASK_TYPE_OWNER_BATCH_DOWNLOAD
from backend.src.unit_test.test_post_download_job import (
  SEC_UID,
  SWITCHES,
  OfflineTestCase,
  StubApi,
  StubDownloader,
  page,
  post_item,
)


OWNER_URL = "https://www.douyin.com/user/" + SEC_UID


class RecordingJobStore(JobStore):
  """A job store that remembers what was created and how each one ended."""

  def __init__(self):
    super().__init__()
    self.created = []
    self.finished = []

  def create(self, keys, payload=None):
    job_id = super().create(keys, payload)
    self.created.append(job_id)
    return job_id

  def finish(self, job_id, state=JOB_ERROR, message=None):
    self.finished.append((job_id, state))
    return super().finish(job_id, state=state, message=message)


def build_owner_service(api=None, task_service=None, store=None, executor=None,
                        downloader=None):
  return PostDownloadJobService(
    downloader=downloader if downloader is not None else StubDownloader(),
    api=api if api is not None else StubApi([page(["1"], 0, False)]),
    store=store if store is not None else RecordingJobStore(),
    cache=PayloadCache(),
    media_switches=SWITCHES,
    task_service=task_service,
    executor=executor,
  )


def tracked_owner(service, **overrides):
  call = {
    "sec_user_id": SEC_UID,
    "resolved_url": OWNER_URL,
    "source_url": SOURCE_URL,
    "resolve_id": RESOLVE_ID,
  }
  call.update(overrides)
  return service.start_all_tracked(**call)


class OwnerTrackedCreationTest(OfflineTestCase):
  def test_owned_batch_links_each_successful_or_skipped_post_only(self):
    tasks = TaskService()
    downloader = StubDownloader(
      failures={"2": RuntimeError("download failed")},
      skips={"3"},
    )
    service = build_owner_service(
      api=StubApi([page(["1", "2", "3"], 0, False)]),
      task_service=tasks,
      downloader=downloader,
    )

    task_id = tracked_owner(service, app_user_id=63)

    self.assertEqual(tasks.get_task(task_id)["app_user_id"], 63)
    self.assertEqual(downloader.links, [(63, "1"), (63, "3")])

  def test_one_batch_ownership_failure_marks_that_item_failed(self):
    tasks = TaskService()
    downloader = StubDownloader(ownership_failures={"2"})
    service = build_owner_service(
      api=StubApi([page(["1", "2"], 0, False)]),
      task_service=tasks,
      downloader=downloader,
    )

    task_id = tracked_owner(service, app_user_id=63)

    task = tasks.get_task(task_id)
    states = {item["key"]: item["state"] for item in task["items"]}
    self.assertEqual(states, {"1": "success", "2": "failed"})
    self.assertEqual(task["state"], "partial")
    failed = next(item for item in task["items"] if item["key"] == "2")
    self.assertNotIn("foreign key", failed["message"])

  def test_batch_does_not_own_a_zero_saved_non_skipped_post(self):
    class NothingSavedDownloader(StubDownloader):
      def download_detail(self, detail, share_url, owner_share_url=None):
        return AwemeDownloadResult(
          ok=True,
          aweme_id=detail.aweme_id,
          media_count=0,
          saved_count=0,
        )

    tasks = TaskService()
    downloader = NothingSavedDownloader()
    service = build_owner_service(
      api=StubApi([page(["1"], 0, False)]),
      task_service=tasks,
      downloader=downloader,
    )

    task_id = tracked_owner(service, app_user_id=63)

    self.assertEqual(downloader.links, [])
    self.assertEqual(tasks.get_task(task_id)["items"][0]["state"], "failed")

  """An owner walk asked for through the task api is a task from the outset."""

  def test_it_answers_with_a_task_id_not_a_job_id(self):
    """The legacy job id stays an internal compatibility detail.

    New clients read one identifier; handing them a second would make them
    depend on a record this migration means to retire.
    """
    tasks = TaskService()
    store = RecordingJobStore()
    service = build_owner_service(task_service=tasks, store=store)

    task_id = tracked_owner(service)

    self.assertIsNotNone(tasks.get_task(task_id))
    self.assertNotIn(task_id, store.created)

  def test_the_task_is_an_owner_batch_download(self):
    tasks = TaskService()
    service = build_owner_service(task_service=tasks)

    task_id = tracked_owner(service)

    self.assertEqual(
      tasks.get_task(task_id)["task_type"], TASK_TYPE_OWNER_BATCH_DOWNLOAD
    )

  def test_the_task_records_where_the_request_came_from(self):
    tasks = TaskService()
    store = RecordingJobStore()
    service = build_owner_service(task_service=tasks, store=store)

    task_id = tracked_owner(service)

    metadata = tasks.get_task(task_id)["metadata"]
    self.assertEqual(metadata["platform"], PLATFORM_DOUYIN)
    self.assertEqual(metadata["source"], OWNER_SOURCE)
    self.assertEqual(metadata["mode"], "all")
    self.assertEqual(metadata["sec_user_id"], SEC_UID)
    self.assertEqual(metadata["resolve_id"], RESOLVE_ID)
    self.assertEqual(metadata["source_url"], SOURCE_URL)
    self.assertEqual(metadata["resolved_url"], OWNER_URL)
    ##
    ## Kept for the legacy surface that still polls it, and never answered to a
    ## new client.
    ##
    self.assertEqual(metadata["legacy_job_id"], store.created[0])

  def test_the_walk_runs_against_the_trusted_sec_user_id(self):
    tasks = TaskService()
    api = StubApi([page(["1"], 0, False)])
    service = build_owner_service(api=api, task_service=tasks)

    tracked_owner(service)

    self.assertGreaterEqual(api.calls, 1)

  def test_creating_the_task_reads_nothing_from_the_platform(self):
    """A profile read needs a live cookie, and a task title is not worth
    making the creation depend on one.

    Observed with the walk still queued, because the walk itself does read the
    profile - to name the folder - and that is legacy behaviour this stage
    leaves exactly as it was.  What must not happen is a read *before* the task
    exists, which would let an expired cookie refuse a creation that needs only
    a ``sec_user_id``.
    """
    tasks = TaskService()
    api = StubApi([page(["1"], 0, False)])
    service = build_owner_service(
      api=api, task_service=tasks, executor=DeferredExecutor()
    )

    task_id = tracked_owner(service)

    self.assertIsNotNone(tasks.get_task(task_id))
    self.assertEqual(api.owner_calls, 0)
    self.assertEqual(api.calls, 0)


class OwnerStrictCreationTest(OfflineTestCase):
  """No task, no walk - and no legacy job left running either."""

  def test_a_task_layer_that_refuses_starts_no_walk(self):
    refusing = RefusingTaskService()
    api = StubApi([page(["1"], 0, False)])
    store = RecordingJobStore()
    service = build_owner_service(api=api, task_service=refusing, store=store)

    with self.assertRaises(TaskCreationUnavailable):
      tracked_owner(service)

    self.assertEqual(api.calls, 0, "the owner walk must not start")

  def test_the_legacy_job_is_ended_rather_than_left_running(self):
    """A job stuck in ``running`` would poll forever against work nobody does."""
    refusing = RefusingTaskService()
    store = RecordingJobStore()
    service = build_owner_service(task_service=refusing, store=store)

    with self.assertRaises(TaskCreationUnavailable):
      tracked_owner(service)

    job_id = store.created[0]
    self.assertEqual(store.snapshot(job_id)["state"], JOB_ERROR)
    self.assertNotEqual(store.snapshot(job_id)["state"], JOB_RUNNING)

  def test_an_unwired_task_service_starts_no_walk(self):
    api = StubApi([page(["1"], 0, False)])
    service = build_owner_service(api=api, task_service=None)

    with self.assertRaises(TaskCreationUnavailable):
      tracked_owner(service)

    self.assertEqual(api.calls, 0)

  def test_a_blank_sec_user_id_is_refused_before_anything_is_created(self):
    tasks = TaskService()
    store = RecordingJobStore()
    service = build_owner_service(task_service=tasks, store=store)

    for value in ("", "   ", None):
      with self.subTest(value=value):
        with self.assertRaises(ValueError):
          tracked_owner(service, sec_user_id=value)

    self.assertEqual(store.created, [])
    self.assertEqual(tasks.list_tasks(), [])


class OwnerSchedulingFailureTest(OfflineTestCase):
  """A walk that could not be scheduled ends both records, not just one."""

  def test_the_task_id_is_still_answered(self):
    tasks = TaskService()
    service = build_owner_service(
      task_service=tasks, executor=RefusingExecutor()
    )

    task_id = tracked_owner(service)

    self.assertIsNotNone(task_id)
    self.assertIsNotNone(tasks.get_task(task_id))

  def test_both_records_are_ended(self):
    tasks = TaskService()
    store = RecordingJobStore()
    service = build_owner_service(
      task_service=tasks, store=store, executor=RefusingExecutor()
    )

    task_id = tracked_owner(service)

    self.assertEqual(tasks.get_task(task_id)["state"], TASK_STATE_FAILED)
    self.assertEqual(store.snapshot(store.created[0])["state"], JOB_ERROR)


class OwnerLegacyContractTest(OfflineTestCase):
  """``start_all`` keeps answering with a job id, best-effort as before."""

  def test_it_still_answers_with_a_job_id(self):
    tasks = TaskService()
    store = RecordingJobStore()
    service = build_owner_service(task_service=tasks, store=store)

    job_id = service.start_all(SEC_UID, share_url="https://share/")

    self.assertIn(job_id, store.created)
    self.assertIsNotNone(service.task_id_for(job_id))

  def test_a_refusing_task_layer_does_not_stop_the_walk(self):
    refusing = RefusingTaskService()
    api = StubApi([page(["1"], 0, False)])
    service = build_owner_service(api=api, task_service=refusing)

    job_id = service.start_all(SEC_UID)

    self.assertIsNotNone(job_id)
    self.assertGreaterEqual(api.calls, 1, "the legacy walk still runs")

  def test_it_still_records_the_legacy_metadata(self):
    tasks = TaskService()
    service = build_owner_service(task_service=tasks)

    job_id = service.start_all(SEC_UID)

    metadata = tasks.get_task(service.task_id_for(job_id))["metadata"]
    self.assertEqual(metadata["mode"], "all")
    self.assertNotIn("source", metadata)
    self.assertNotIn("resolve_id", metadata)


if __name__ == "__main__":
  unittest.main()
