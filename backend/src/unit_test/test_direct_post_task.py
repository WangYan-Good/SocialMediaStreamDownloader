import unittest
from concurrent.futures import Future

from backend.src.platform.douyin.douyin_aweme_downloader import AwemeDownloadResult
from backend.src.service.direct_post_download_task import (
  PLATFORM_DOUYIN,
  SOURCE_DIRECT,
  DirectPostDownloadTaskService,
)
from backend.src.task.model import (
  TASK_STATE_FAILED,
  TASK_STATE_PARTIAL,
  TASK_STATE_PENDING,
  TASK_STATE_RUNNING,
  TASK_STATE_SUCCESS,
  TASK_TYPE_POST_DOWNLOAD,
)
from backend.src.task.service import TaskService

SOURCE_URL = "https://v.douyin.com/abc/"
RESOLVED_URL = "https://www.douyin.com/video/7123456789012345678"
AWEME_ID = "7123456789012345678"


def token(url=SOURCE_URL, resolved_url=RESOLVED_URL, aweme_id=AWEME_ID, **extra):
  built = {"url": url, "resolved_url": resolved_url, "aweme_id": aweme_id}
  built.update(extra)
  return built


def complete_result(media_count=3, saved_count=3):
  return AwemeDownloadResult(
    ok=True,
    aweme_id=AWEME_ID,
    save_dir="/media/douyin/A/post",
    media_count=media_count,
    saved_count=saved_count,
  )


def skipped_result():
  return AwemeDownloadResult(
    ok=True,
    aweme_id=AWEME_ID,
    save_dir="/media/douyin/A/post",
    media_count=2,
    saved_count=2,
    skipped=True,
    reason="already downloaded",
  )


def refused_result(reason="作品已被删除"):
  return AwemeDownloadResult(ok=False, aweme_id=AWEME_ID, reason=reason)


class FakeConfig:
  """The part of the downloader's config the scheduling path reads."""

  def __init__(self, concurrency=3):
    self.concurrency = concurrency


class FakeDownloader:
  """Stands in for DouyinAwemeDownloader: one post per ``run`` call."""

  def __init__(self, result=None, results=None, crash=None, concurrency=3):
    self._result = result
    self._results = results or {}
    self._crash = crash
    ##
    ## Present because the real downloader has it: the post pool is sized from
    ## ``config.concurrency``, which is how this path keeps using the one shared
    ## executor rather than sizing a second one of its own.
    ##
    self.config = FakeConfig(concurrency)
    self.calls = []

  def run(self, token):
    self.calls.append(token)
    if self._crash is not None:
      raise self._crash
    key = token.get("aweme_id")
    if key in self._results:
      return self._results[key]
    return self._result if self._result is not None else complete_result()


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

  def submit(self, *args, **kwargs):
    raise self.failure


def build_service(downloader=None, executor=None, task_service=None):
  downloader = downloader if downloader is not None else FakeDownloader()
  executor = executor if executor is not None else ImmediateExecutor()
  return (
    DirectPostDownloadTaskService(
      task_service=task_service,
      downloader_factory=lambda: downloader,
      executor_factory=lambda *args, **kwargs: executor,
    ),
    downloader,
    executor,
  )


def only_task(tasks: TaskService) -> dict:
  listed = tasks.list_tasks()
  assert len(listed) == 1, listed
  return listed[0]


class DirectPostTaskCreationTest(unittest.TestCase):
  def test_a_confirmed_post_becomes_a_post_download_task(self):
    tasks = TaskService()
    service, downloader, executor = build_service(
      task_service=tasks, executor=DeferredExecutor()
    )

    service.submit(token())

    self.assertEqual(TASK_TYPE_POST_DOWNLOAD, only_task(tasks)["task_type"])

  def test_a_task_waits_as_pending_until_a_worker_picks_it_up(self):
    tasks = TaskService()
    service, downloader, executor = build_service(
      task_service=tasks, executor=DeferredExecutor()
    )

    service.submit(token())

    ##
    ## Queued is not running.  Marking it running at submission would claim work
    ## had begun while the pool is still busy with other posts.
    ##
    task = only_task(tasks)
    self.assertEqual(TASK_STATE_PENDING, task["state"])
    self.assertEqual({"current": 0, "total": 1}, task["progress"])
    self.assertEqual([], downloader.calls)

  def test_the_task_records_what_the_handler_resolved(self):
    tasks = TaskService()
    service, downloader, executor = build_service(
      task_service=tasks, executor=DeferredExecutor()
    )

    service.submit(token())

    metadata = only_task(tasks)["metadata"]
    self.assertEqual(PLATFORM_DOUYIN, metadata["platform"])
    self.assertEqual(SOURCE_DIRECT, metadata["source"])
    self.assertEqual(SOURCE_URL, metadata["source_url"])
    self.assertEqual(RESOLVED_URL, metadata["resolved_url"])
    self.assertEqual(AWEME_ID, metadata["aweme_id"])

  def test_the_task_is_titled_for_the_post(self):
    tasks = TaskService()
    service, downloader, executor = build_service(
      task_service=tasks, executor=DeferredExecutor()
    )

    service.submit(token())

    self.assertEqual("下载作品 {}".format(AWEME_ID), only_task(tasks)["title"])

  def test_a_post_without_a_known_id_still_gets_a_title(self):
    tasks = TaskService()
    service, downloader, executor = build_service(
      task_service=tasks, executor=DeferredExecutor()
    )

    service.submit(token(aweme_id=None))

    self.assertEqual("下载抖音作品", only_task(tasks)["title"])

  def test_the_task_carries_no_items(self):
    tasks = TaskService()
    service, downloader, executor = build_service(
      task_service=tasks, executor=DeferredExecutor()
    )

    service.submit(token())

    ##
    ## The task *is* the unit of work.  A single item beside it would be a second
    ## place to read the same outcome, and would force ``partial`` - a real
    ## outcome for one post - to be expressed by an item that cannot hold it.
    ##
    self.assertEqual([], only_task(tasks)["items"])

  def test_the_users_token_is_not_polluted(self):
    tasks = TaskService()
    service, downloader, executor = build_service(task_service=tasks)
    supplied = token(score=5)

    service.submit(supplied)

    self.assertEqual({"url", "resolved_url", "aweme_id", "score"}, set(supplied))


class DirectPostWorkerTest(unittest.TestCase):
  def test_the_task_starts_running_only_when_the_worker_does(self):
    tasks = TaskService()
    service, downloader, executor = build_service(
      task_service=tasks, executor=DeferredExecutor()
    )
    service.submit(token())
    self.assertEqual(TASK_STATE_PENDING, only_task(tasks)["state"])

    executor.drain()

    self.assertEqual([token()], downloader.calls)

  def test_the_downloader_is_handed_the_token_it_was_given(self):
    tasks = TaskService()
    service, downloader, executor = build_service(task_service=tasks)

    service.submit(token(score=5))

    self.assertEqual(1, len(downloader.calls))
    self.assertEqual(RESOLVED_URL, downloader.calls[0]["resolved_url"])
    self.assertEqual(5, downloader.calls[0]["score"])

  def test_an_inline_worker_never_skips_the_running_state(self):
    ##
    ## An executor that runs the work inside ``submit`` is the tightest possible
    ## timing: the task is created and finished within one call.  Going straight
    ## from pending to success would be rejected by the transition table, so a
    ## finished task here proves running was passed through.
    ##
    tasks = TaskService()
    service, downloader, executor = build_service(task_service=tasks)

    service.submit(token())

    task = only_task(tasks)
    self.assertEqual(TASK_STATE_SUCCESS, task["state"])
    self.assertIsNotNone(task["started_at"])


class DirectPostResultMappingTest(unittest.TestCase):
  def run_with(self, result=None, crash=None):
    tasks = TaskService()
    downloader = FakeDownloader(result=result, crash=crash)
    service, unused, executor = build_service(
      downloader=downloader, task_service=tasks
    )
    future = service.submit(token())
    return tasks, only_task(tasks), future

  def test_a_complete_download_is_a_success(self):
    tasks, task, future = self.run_with(complete_result())

    self.assertEqual(TASK_STATE_SUCCESS, task["state"])
    self.assertEqual({"current": 1, "total": 1}, task["progress"])

  def test_a_complete_download_records_what_it_saved(self):
    tasks, task, future = self.run_with(complete_result())

    self.assertEqual(
      {
        "ok": True,
        "skipped": False,
        "partial": False,
        "saved_count": 3,
        "media_count": 3,
        "save_dir": "/media/douyin/A/post",
        "reason": None,
      },
      task["metadata"]["result"],
    )

  def test_a_post_already_on_disk_is_a_success(self):
    tasks, task, future = self.run_with(skipped_result())

    ##
    ## The user wanted the post on disk and it is on disk.  Nothing was
    ## downloaded, but nothing needed to be.
    ##
    self.assertEqual(TASK_STATE_SUCCESS, task["state"])
    self.assertIs(True, task["metadata"]["result"]["skipped"])
    self.assertEqual("已经下载，无需重复下载", task["message"])

  def test_some_files_saved_is_partial(self):
    tasks, task, future = self.run_with(complete_result(media_count=3, saved_count=2))

    self.assertEqual(TASK_STATE_PARTIAL, task["state"])
    self.assertEqual({"current": 1, "total": 1}, task["progress"])
    self.assertEqual("已保存 2 / 3 个媒体文件", task["message"])
    self.assertIs(True, task["metadata"]["result"]["partial"])

  def test_saving_nothing_at_all_is_a_failure(self):
    ##
    ## The downloader reports ``ok`` for this - it reached the post and simply
    ## could not keep any of its files - and its ``partial`` flag is false
    ## because nothing was saved.  Read naively that shape looks like a complete
    ## success, which is exactly the trap: the user asked for a post and has no
    ## files.
    ##
    tasks, task, future = self.run_with(complete_result(media_count=3, saved_count=0))

    self.assertEqual(TASK_STATE_FAILED, task["state"])
    self.assertEqual({"current": 1, "total": 1}, task["progress"])
    self.assertEqual(0, task["metadata"]["result"]["saved_count"])

  def test_a_post_that_cannot_be_reached_is_a_failure(self):
    tasks, task, future = self.run_with(refused_result("作品已被删除"))

    self.assertEqual(TASK_STATE_FAILED, task["state"])
    self.assertEqual("作品已被删除", task["message"])
    self.assertEqual("作品已被删除", task["metadata"]["result"]["reason"])

  def test_a_refusal_without_a_reason_still_says_something(self):
    tasks, task, future = self.run_with(AwemeDownloadResult(ok=False))

    self.assertEqual(TASK_STATE_FAILED, task["state"])
    self.assertTrue(task["message"])

  def test_a_crashing_downloader_fails_the_task(self):
    tasks, task, future = self.run_with(crash=RuntimeError("connection reset"))

    self.assertEqual(TASK_STATE_FAILED, task["state"])
    self.assertEqual({"current": 1, "total": 1}, task["progress"])

  def test_a_crash_never_publishes_a_traceback(self):
    tasks, task, future = self.run_with(crash=RuntimeError("connection reset"))

    rendered = repr(task["metadata"]) + repr(task["message"])
    self.assertNotIn("Traceback", rendered)
    self.assertNotIn("File \"", rendered)

  def test_a_crash_still_reaches_the_future(self):
    tasks, task, future = self.run_with(crash=RuntimeError("connection reset"))

    ##
    ## Unchanged from the legacy path, where the downloader was submitted to the
    ## pool directly and its exception ended up in the future.
    ##
    with self.assertRaises(RuntimeError):
      future.result()


class DirectPostTerminalInvariantTest(unittest.TestCase):
  """Every way a post can end, held to the same two promises.

  Whatever happened, the one logical unit of work has been dealt with, so
  progress reads 1 / 1; and the task has reached an end state, so the store's
  retention can eventually reclaim it.  A task left pending or running is never
  evicted - expiry counts from the moment a task ends - so an ending that is not
  recorded is a permanent leak, not a cosmetic slip.

  Written as one sweep because the promise is the same for all of them: the
  earlier per-outcome tests each check their own state and message, and two of
  the seven used to check neither of these two invariants.
  """

  def end_via(self, result=None, crash=None, executor=None):
    tasks = TaskService()
    downloader = FakeDownloader(result=result, crash=crash)
    service, unused, chosen = build_service(
      downloader=downloader, task_service=tasks, executor=executor
    )
    service.submit(token())
    return only_task(tasks)

  def all_endings(self):
    return {
      "success": (self.end_via(complete_result()), TASK_STATE_SUCCESS),
      "already downloaded": (self.end_via(skipped_result()), TASK_STATE_SUCCESS),
      "partial": (
        self.end_via(complete_result(media_count=3, saved_count=2)),
        TASK_STATE_PARTIAL,
      ),
      "unavailable": (self.end_via(refused_result()), TASK_STATE_FAILED),
      "nothing saved": (
        self.end_via(complete_result(media_count=3, saved_count=0)),
        TASK_STATE_FAILED,
      ),
      "crashed": (self.end_via(crash=RuntimeError("boom")), TASK_STATE_FAILED),
      "never scheduled": (
        self.end_via(executor=RefusingExecutor()),
        TASK_STATE_FAILED,
      ),
    }

  def test_every_ending_reports_one_of_one(self):
    for label, (task, unused) in self.all_endings().items():
      with self.subTest(ending=label):
        self.assertEqual({"current": 1, "total": 1}, task["progress"])

  def test_every_ending_reaches_the_state_it_should(self):
    for label, (task, expected) in self.all_endings().items():
      with self.subTest(ending=label):
        self.assertEqual(expected, task["state"])

  def test_no_ending_leaves_a_task_running_or_pending(self):
    from backend.src.task.model import TERMINAL_TASK_STATES

    for label, (task, unused) in self.all_endings().items():
      with self.subTest(ending=label):
        self.assertIn(task["state"], TERMINAL_TASK_STATES)
        self.assertIsNotNone(task["finished_at"])

  def test_every_ending_is_eventually_reclaimed(self):
    from datetime import datetime, timedelta

    from backend.src.task.store import TaskStore

    class Clock:
      def __init__(self):
        self.wall = datetime(2026, 8, 14, 9, 0, 0)
        self.mono = 0.0

      def now(self):
        return self.wall

      def monotonic(self):
        return self.mono

      def advance(self, seconds):
        self.wall = self.wall + timedelta(seconds=seconds)
        self.mono += seconds

    for label, arguments in {
      "success": {"result": complete_result()},
      "already downloaded": {"result": skipped_result()},
      "partial": {"result": complete_result(media_count=3, saved_count=2)},
      "unavailable": {"result": refused_result()},
      "nothing saved": {"result": complete_result(media_count=3, saved_count=0)},
      "crashed": {"crash": RuntimeError("boom")},
      "never scheduled": {"executor": RefusingExecutor()},
    }.items():
      with self.subTest(ending=label):
        clock = Clock()
        tasks = TaskService(
          TaskStore(
            retention_seconds=600.0,
            clock=clock.now,
            monotonic_clock=clock.monotonic,
          )
        )
        downloader = FakeDownloader(
          result=arguments.get("result"), crash=arguments.get("crash")
        )
        service, unused, chosen = build_service(
          downloader=downloader,
          task_service=tasks,
          executor=arguments.get("executor"),
        )
        service.submit(token())
        self.assertEqual(1, len(tasks.list_tasks()))

        clock.advance(601.0)

        ##
        ## The store only expires tasks that have ended, so this passing is proof
        ## the ending was actually recorded.  A task stuck pending would still be
        ## here, and would stay here for the life of the process.
        ##
        self.assertEqual([], tasks.list_tasks())


class BrokenTaskService:
  """Every call fails, standing in for a task layer that has gone wrong."""

  def __init__(self):
    self.calls = []

  def _fail(self, name):
    self.calls.append(name)
    raise RuntimeError("task layer unavailable")

  def create_task(self, *args, **kwargs):
    self._fail("create_task")

  def start_task(self, *args, **kwargs):
    self._fail("start_task")

  def update_metadata(self, *args, **kwargs):
    self._fail("update_metadata")

  def update_progress(self, *args, **kwargs):
    self._fail("update_progress")

  def update_message(self, *args, **kwargs):
    self._fail("update_message")

  def get_task(self, *args, **kwargs):
    self._fail("get_task")

  def finish_success(self, *args, **kwargs):
    self._fail("finish_success")

  def finish_partial(self, *args, **kwargs):
    self._fail("finish_partial")

  def finish_failed(self, *args, **kwargs):
    self._fail("finish_failed")


class DirectPostTelemetryFailureTest(unittest.TestCase):
  """Reporting is observability; it can never decide whether a post downloads."""

  def test_a_post_downloads_with_no_task_service_at_all(self):
    service, downloader, executor = build_service()

    service.submit(token())

    self.assertEqual(1, len(downloader.calls))
    self.assertFalse(service.enabled)

  def test_a_post_downloads_when_the_whole_task_layer_is_broken(self):
    broken = BrokenTaskService()
    service, downloader, executor = build_service(task_service=broken)

    service.submit(token())

    self.assertEqual(1, len(downloader.calls))

  def test_nothing_further_is_attempted_once_creation_was_refused(self):
    broken = BrokenTaskService()
    service, downloader, executor = build_service(task_service=broken)

    service.submit(token())

    ##
    ## A post with no task has nothing to report against, so the worker does not
    ## keep trying and filling the log on every step.
    ##
    self.assertEqual(["create_task"], broken.calls)

  def test_a_refused_start_does_not_stop_the_download(self):
    class RefusesStart(TaskService):
      def start_task(self, *args, **kwargs):
        raise RuntimeError("start unavailable")

    tasks = RefusesStart()
    service, downloader, executor = build_service(task_service=tasks)

    service.submit(token())

    self.assertEqual(1, len(downloader.calls))

  def test_a_refused_metadata_write_still_ends_the_task_correctly(self):
    class RefusesMetadata(TaskService):
      def update_metadata(self, *args, **kwargs):
        raise RuntimeError("metadata unavailable")

    tasks = RefusesMetadata()
    service, downloader, executor = build_service(task_service=tasks)

    service.submit(token())

    task = only_task(tasks)
    self.assertEqual(1, len(downloader.calls))
    self.assertEqual(TASK_STATE_SUCCESS, task["state"])
    self.assertEqual({"current": 1, "total": 1}, task["progress"])

  def test_a_refused_progress_write_still_ends_the_task(self):
    class RefusesProgress(TaskService):
      def update_progress(self, *args, **kwargs):
        raise RuntimeError("progress unavailable")

    tasks = RefusesProgress()
    service, downloader, executor = build_service(task_service=tasks)

    service.submit(token())

    self.assertEqual(1, len(downloader.calls))
    self.assertEqual(TASK_STATE_SUCCESS, only_task(tasks)["state"])

  def test_a_refused_finish_does_not_undo_the_download(self):
    class RefusesFinish(TaskService):
      def finish_success(self, *args, **kwargs):
        raise RuntimeError("finish unavailable")

    tasks = RefusesFinish()
    service, downloader, executor = build_service(task_service=tasks)

    future = service.submit(token())

    self.assertEqual(1, len(downloader.calls))
    self.assertIsNotNone(future.result())
    ##
    ## Stranded in ``running`` rather than mislabelled - the reporting failed and
    ## says so - while the files are on disk either way.
    ##
    self.assertEqual(TASK_STATE_RUNNING, only_task(tasks)["state"])


class DirectPostSchedulingFailureTest(unittest.TestCase):
  def test_work_the_pool_refuses_does_not_leave_a_task_pending_forever(self):
    tasks = TaskService()
    service, downloader, executor = build_service(
      task_service=tasks, executor=RefusingExecutor()
    )

    returned = service.submit(token())

    ##
    ## Nothing will ever move this task, so leaving it ``pending`` would be a lie
    ## that never resolves.  It admits it never ran instead.
    ##
    task = only_task(tasks)
    self.assertIsNone(returned)
    self.assertEqual(TASK_STATE_FAILED, task["state"])
    self.assertEqual({"current": 1, "total": 1}, task["progress"])
    self.assertEqual("下载没有进入队列", task["message"])
    self.assertEqual([], downloader.calls)

  def test_a_refused_pool_without_a_task_service_is_survivable(self):
    service, downloader, executor = build_service(executor=RefusingExecutor())

    self.assertIsNone(service.submit(token()))


class DirectPostIndependenceTest(unittest.TestCase):
  def test_each_post_becomes_its_own_task(self):
    tasks = TaskService()
    downloader = FakeDownloader(
      results={
        "a": complete_result(),
        "b": complete_result(media_count=3, saved_count=1),
        "c": refused_result("作品已被删除"),
      }
    )
    service, unused, executor = build_service(
      downloader=downloader, task_service=tasks
    )

    for aweme_id in ("a", "b", "c"):
      service.submit(token(aweme_id=aweme_id))

    listed = {task["metadata"]["aweme_id"]: task for task in tasks.list_tasks()}
    self.assertEqual(3, len(listed))
    self.assertEqual(TASK_STATE_SUCCESS, listed["a"]["state"])
    self.assertEqual(TASK_STATE_PARTIAL, listed["b"]["state"])
    self.assertEqual(TASK_STATE_FAILED, listed["c"]["state"])

  def test_one_failure_does_not_disturb_another_posts_record(self):
    tasks = TaskService()
    downloader = FakeDownloader(
      results={"a": complete_result(), "c": refused_result("作品已被删除")}
    )
    service, unused, executor = build_service(
      downloader=downloader, task_service=tasks
    )

    service.submit(token(aweme_id="a"))
    service.submit(token(aweme_id="c"))

    listed = {task["metadata"]["aweme_id"]: task for task in tasks.list_tasks()}
    self.assertEqual(
      "/media/douyin/A/post", listed["a"]["metadata"]["result"]["save_dir"]
    )
    self.assertIsNone(listed["c"]["metadata"]["result"]["save_dir"])
    self.assertEqual({"current": 1, "total": 1}, listed["a"]["progress"])
    self.assertEqual({"current": 1, "total": 1}, listed["c"]["progress"])

  def test_the_same_link_pasted_twice_stays_two_submissions(self):
    tasks = TaskService()
    service, downloader, executor = build_service(task_service=tasks)

    service.submit(token())
    service.submit(token())

    ##
    ## Legacy submission semantics are not this stage's to change: two pastes are
    ## two downloads, and the downloader's own per-post lock and disk check are
    ## what make the second one cheap.
    ##
    self.assertEqual(2, len(downloader.calls))
    listed = tasks.list_tasks()
    self.assertEqual(2, len(listed))
    self.assertNotEqual(listed[0]["task_id"], listed[1]["task_id"])

  def test_posts_running_at_once_keep_their_own_records(self):
    from concurrent.futures import ThreadPoolExecutor

    tasks = TaskService()
    downloader = FakeDownloader(
      results={
        str(index): complete_result(media_count=3, saved_count=index % 4)
        for index in range(8)
      }
    )
    pool = ThreadPoolExecutor(max_workers=4)
    service, unused, executor = build_service(
      downloader=downloader, task_service=tasks, executor=pool
    )

    futures = [service.submit(token(aweme_id=str(index))) for index in range(8)]
    for future in futures:
      future.result()
    pool.shutdown(wait=True)

    listed = {task["metadata"]["aweme_id"]: task for task in tasks.list_tasks()}
    self.assertEqual(8, len(listed))
    for index in range(8):
      task = listed[str(index)]
      saved = index % 4
      self.assertEqual(saved, task["metadata"]["result"]["saved_count"])
      self.assertEqual({"current": 1, "total": 1}, task["progress"])
      expected = TASK_STATE_SUCCESS
      if saved == 0:
        expected = TASK_STATE_FAILED
      elif saved < 3:
        expected = TASK_STATE_PARTIAL
      self.assertEqual(expected, task["state"], task["metadata"])


if __name__ == "__main__":
  unittest.main()
