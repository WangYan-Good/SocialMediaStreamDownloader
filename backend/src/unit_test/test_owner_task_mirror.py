import unittest
from datetime import datetime, timedelta

from backend.src.service.owner_task_mirror import PLATFORM_DOUYIN, OwnerTaskMirror
from backend.src.task.model import (
  ITEM_STATE_FAILED,
  ITEM_STATE_PENDING,
  ITEM_STATE_RUNNING,
  ITEM_STATE_SKIPPED,
  ITEM_STATE_SUCCESS,
  TASK_STATE_FAILED,
  TASK_STATE_PARTIAL,
  TASK_STATE_PENDING,
  TASK_STATE_RUNNING,
  TASK_STATE_SUCCESS,
  TASK_TYPE_OWNER_BATCH_DOWNLOAD,
)
from backend.src.task.service import TaskService
from backend.src.task.store import TaskStore


class FakeClock:
  def __init__(self, start=datetime(2026, 8, 13, 9, 0, 0)):
    self.wall = start
    self.mono = 0.0

  def now(self):
    return self.wall

  def monotonic(self):
    return self.mono

  def advance(self, seconds):
    self.wall = self.wall + timedelta(seconds=seconds)
    self.mono += seconds


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

  def update_message(self, *args, **kwargs):
    self._fail("update_message")

  def add_item(self, *args, **kwargs):
    self._fail("add_item")

  def update_item(self, *args, **kwargs):
    self._fail("update_item")

  def update_progress(self, *args, **kwargs):
    self._fail("update_progress")

  def get_task(self, *args, **kwargs):
    self._fail("get_task")

  def finish_success(self, *args, **kwargs):
    self._fail("finish_success")

  def finish_partial(self, *args, **kwargs):
    self._fail("finish_partial")

  def finish_failed(self, *args, **kwargs):
    self._fail("finish_failed")


def build_mirror(task_service=None):
  service = task_service if task_service is not None else TaskService()
  return OwnerTaskMirror(service), service


def open_job(mirror, job_id="job-1", items=None, total=None, mode="selected"):
  return mirror.open(
    job_id,
    title="下载主播作品",
    metadata={"platform": PLATFORM_DOUYIN, "legacy_job_id": job_id, "mode": mode},
    items=items,
    total=total,
  )


class MirrorCreationTest(unittest.TestCase):
  def test_opening_a_job_creates_an_owner_batch_task(self):
    mirror, service = build_mirror()

    task_id = open_job(mirror, items=["a", "b"], total=2)
    task = service.get_task(task_id)

    self.assertEqual(task["task_type"], TASK_TYPE_OWNER_BATCH_DOWNLOAD)
    self.assertEqual(task["state"], TASK_STATE_PENDING)
    self.assertEqual(task["title"], "下载主播作品")
    self.assertEqual(task["metadata"]["platform"], PLATFORM_DOUYIN)
    self.assertEqual(task["metadata"]["legacy_job_id"], "job-1")
    self.assertEqual([item["key"] for item in task["items"]], ["a", "b"])
    self.assertEqual(task["progress"], {"current": 0, "total": 2})

  def test_a_job_without_a_known_size_starts_with_no_total(self):
    """The owner walk does not know how many posts there are until it ends."""
    mirror, service = build_mirror()

    task_id = open_job(mirror, mode="all")

    self.assertEqual(
      service.get_task(task_id)["progress"], {"current": 0, "total": None}
    )

  def test_the_task_id_can_be_looked_up_by_job_id(self):
    """The association is recorded, never derived from the shape of an id."""
    mirror, service = build_mirror()

    task_id = open_job(mirror, job_id="job-7")

    self.assertEqual(mirror.task_id("job-7"), task_id)

  def test_an_unknown_job_has_no_task(self):
    mirror, service = build_mirror()

    self.assertIsNone(mirror.task_id("never-opened"))


class MirrorLifecycleTest(unittest.TestCase):
  def test_work_starting_moves_the_task_to_running(self):
    mirror, service = build_mirror()
    task_id = open_job(mirror, items=["a"], total=1)

    mirror.start("job-1", message="正在下载所选作品")
    task = service.get_task(task_id)

    self.assertEqual(task["state"], TASK_STATE_RUNNING)
    self.assertEqual(task["message"], "正在下载所选作品")

  def test_narrating_reports_a_stage_without_a_transition(self):
    mirror, service = build_mirror()
    task_id = open_job(mirror, mode="all")
    mirror.start("job-1")

    mirror.narrate("job-1", "已发现 3 个作品")
    task = service.get_task(task_id)

    self.assertEqual(task["state"], TASK_STATE_RUNNING)
    self.assertEqual(task["message"], "已发现 3 个作品")

  def test_an_item_runs_then_succeeds(self):
    mirror, service = build_mirror()
    task_id = open_job(mirror, items=["a"], total=1)
    mirror.start("job-1")

    mirror.item_running("job-1", "a")
    self.assertEqual(
      service.get_task(task_id)["items"][0]["state"], ITEM_STATE_RUNNING
    )

    mirror.item_finished(
      "job-1",
      "a",
      ITEM_STATE_SUCCESS,
      metadata={"saved_count": 3, "media_count": 3},
    )
    item = service.get_task(task_id)["items"][0]

    self.assertEqual(item["state"], ITEM_STATE_SUCCESS)
    self.assertEqual(item["metadata"], {"saved_count": 3, "media_count": 3})

  def test_finishing_items_advances_progress(self):
    mirror, service = build_mirror()
    task_id = open_job(mirror, items=["a", "b", "c"], total=3)
    mirror.start("job-1")

    mirror.item_finished("job-1", "a", ITEM_STATE_SUCCESS)
    mirror.item_finished("job-1", "b", ITEM_STATE_FAILED, message="下载超时")

    self.assertEqual(
      service.get_task(task_id)["progress"], {"current": 2, "total": 3}
    )

  def test_discovered_work_is_registered_once_and_keeps_its_order(self):
    mirror, service = build_mirror()
    task_id = open_job(mirror, mode="all")
    mirror.start("job-1")

    for key in ("3", "1", "3", "2"):
      mirror.add_item("job-1", key)
    items = service.get_task(task_id)["items"]

    self.assertEqual([item["key"] for item in items], ["3", "1", "2"])
    self.assertEqual({item["state"] for item in items}, {ITEM_STATE_PENDING})

  def test_re_discovering_a_finished_post_does_not_undo_it(self):
    mirror, service = build_mirror()
    task_id = open_job(mirror, mode="all")
    mirror.start("job-1")
    mirror.add_item("job-1", "a")
    mirror.item_finished("job-1", "a", ITEM_STATE_SUCCESS)

    mirror.add_item("job-1", "a")
    task = service.get_task(task_id)

    self.assertEqual(task["items"][0]["state"], ITEM_STATE_SUCCESS)
    self.assertEqual(task["progress"]["current"], 1)

  def test_the_final_count_becomes_the_total(self):
    mirror, service = build_mirror()
    task_id = open_job(mirror, mode="all")
    mirror.start("job-1")
    for key in ("a", "b"):
      mirror.add_item("job-1", key)
      mirror.item_finished("job-1", key, ITEM_STATE_SUCCESS)

    mirror.settle_total("job-1")

    self.assertEqual(
      service.get_task(task_id)["progress"], {"current": 2, "total": 2}
    )


class MirrorRepeatedUnitTest(unittest.TestCase):
  """A key is one logical unit of work, however many times it is handed over."""

  def test_a_repeated_unit_does_not_reopen_finished_work(self):
    mirror, service = build_mirror()
    task_id = open_job(mirror, items=["a", "b"], total=2)
    mirror.start("job-1")
    mirror.item_running("job-1", "a")
    mirror.item_finished("job-1", "a", ITEM_STATE_SUCCESS)

    ##
    ## The legacy list carried "a" twice, so a second worker pass reports it
    ## starting again.  The unit is already done; saying otherwise would be a
    ## lie about the work.
    ##
    mirror.item_running("job-1", "a")
    task = service.get_task(task_id)

    self.assertEqual(task["items"][0]["state"], ITEM_STATE_SUCCESS)
    self.assertEqual(task["progress"], {"current": 1, "total": 2})

  def test_progress_never_moves_backwards(self):
    """A bar that goes 2/2 then 1/2 then 2/2 reads as a fault to the user."""
    mirror, service = build_mirror()
    task_id = open_job(mirror, items=["a", "b"], total=2)
    mirror.start("job-1")
    seen = []

    for key in ("a", "b", "a"):
      mirror.item_running("job-1", key)
      seen.append(service.get_task(task_id)["progress"]["current"])
      mirror.item_finished("job-1", key, ITEM_STATE_SUCCESS)
      seen.append(service.get_task(task_id)["progress"]["current"])

    self.assertEqual(seen, sorted(seen))
    self.assertEqual(seen[-1], 2)

  def test_a_repeated_unit_may_still_correct_its_outcome(self):
    """Blocking the regression must not freeze the answer: the last pass wins."""
    mirror, service = build_mirror()
    task_id = open_job(mirror, items=["a"], total=1)
    mirror.start("job-1")
    mirror.item_finished("job-1", "a", ITEM_STATE_FAILED, message="下载超时")

    mirror.item_running("job-1", "a")
    mirror.item_finished("job-1", "a", ITEM_STATE_SUCCESS, message=None)
    task = service.get_task(task_id)

    self.assertEqual(task["items"][0]["state"], ITEM_STATE_SUCCESS)
    self.assertEqual(task["progress"], {"current": 1, "total": 1})

  def test_an_unfinished_unit_still_reports_that_it_started(self):
    mirror, service = build_mirror()
    task_id = open_job(mirror, items=["a"], total=1)
    mirror.start("job-1")

    mirror.item_running("job-1", "a")

    self.assertEqual(
      service.get_task(task_id)["items"][0]["state"], ITEM_STATE_RUNNING
    )

  def test_each_job_tracks_its_own_units(self):
    mirror, service = build_mirror()
    first = open_job(mirror, job_id="job-1", items=["a"], total=1)
    second = open_job(mirror, job_id="job-2", items=["a"], total=1)
    mirror.start("job-1")
    mirror.start("job-2")
    mirror.item_finished("job-1", "a", ITEM_STATE_SUCCESS)

    mirror.item_running("job-2", "a")

    self.assertEqual(
      service.get_task(second)["items"][0]["state"], ITEM_STATE_RUNNING
    )


class MirrorOutcomeAggregationTest(unittest.TestCase):
  """Repeated passes over one unit may improve its outcome, never undo it.

  For a batch download the outcomes rank ``failed < skipped < success``: skipped
  means the file is already on disk, so the goal is met, and a later pass that
  fails must not erase a post that is sitting there.
  """

  def two_passes(self, first, second):
    mirror, service = build_mirror()
    task_id = open_job(mirror, items=["a"], total=1)
    mirror.start("job-1")
    mirror.item_finished(
      "job-1", "a", first, message="第一次-" + first, metadata={"pass": 1}
    )
    mirror.item_finished(
      "job-1", "a", second, message="第二次-" + second, metadata={"pass": 2}
    )
    return service.get_task(task_id)["items"][0]

  def test_a_failure_cannot_undo_a_download(self):
    self.assertEqual(self.two_passes(ITEM_STATE_SUCCESS, ITEM_STATE_FAILED)["state"],
                     ITEM_STATE_SUCCESS)

  def test_already_downloaded_cannot_demote_a_download(self):
    self.assertEqual(self.two_passes(ITEM_STATE_SUCCESS, ITEM_STATE_SKIPPED)["state"],
                     ITEM_STATE_SUCCESS)

  def test_a_failure_cannot_undo_an_existing_file(self):
    self.assertEqual(self.two_passes(ITEM_STATE_SKIPPED, ITEM_STATE_FAILED)["state"],
                     ITEM_STATE_SKIPPED)

  def test_an_existing_file_improves_on_a_failure(self):
    self.assertEqual(self.two_passes(ITEM_STATE_FAILED, ITEM_STATE_SKIPPED)["state"],
                     ITEM_STATE_SKIPPED)

  def test_a_download_improves_on_a_failure(self):
    self.assertEqual(self.two_passes(ITEM_STATE_FAILED, ITEM_STATE_SUCCESS)["state"],
                     ITEM_STATE_SUCCESS)

  def test_a_download_improves_on_an_existing_file(self):
    self.assertEqual(self.two_passes(ITEM_STATE_SKIPPED, ITEM_STATE_SUCCESS)["state"],
                     ITEM_STATE_SUCCESS)

  def test_a_kept_outcome_keeps_its_own_message_and_metadata(self):
    """state=success with the failure's message would describe neither pass."""
    item = self.two_passes(ITEM_STATE_SUCCESS, ITEM_STATE_FAILED)

    self.assertEqual(item["state"], ITEM_STATE_SUCCESS)
    self.assertEqual(item["message"], "第一次-success")
    self.assertEqual(item["metadata"], {"pass": 1})

  def test_an_adopted_outcome_brings_its_own_message_and_metadata(self):
    item = self.two_passes(ITEM_STATE_FAILED, ITEM_STATE_SUCCESS)

    self.assertEqual(item["state"], ITEM_STATE_SUCCESS)
    self.assertEqual(item["message"], "第二次-success")
    self.assertEqual(item["metadata"], {"pass": 2})

  def test_three_passes_settle_on_the_best(self):
    mirror, service = build_mirror()
    task_id = open_job(mirror, items=["a"], total=1)
    mirror.start("job-1")

    for state in (ITEM_STATE_FAILED, ITEM_STATE_SKIPPED, ITEM_STATE_SUCCESS):
      mirror.item_finished("job-1", "a", state, message=state)
    item = service.get_task(task_id)["items"][0]

    self.assertEqual(item["state"], ITEM_STATE_SUCCESS)
    self.assertEqual(item["message"], ITEM_STATE_SUCCESS)

  def test_a_later_worse_pass_never_wins(self):
    mirror, service = build_mirror()
    task_id = open_job(mirror, items=["a"], total=1)
    mirror.start("job-1")

    for state in (ITEM_STATE_SUCCESS, ITEM_STATE_FAILED, ITEM_STATE_SKIPPED):
      mirror.item_finished("job-1", "a", state, message=state)

    self.assertEqual(
      service.get_task(task_id)["items"][0]["state"], ITEM_STATE_SUCCESS
    )

  def test_other_units_are_untouched(self):
    mirror, service = build_mirror()
    task_id = open_job(mirror, items=["a", "b"], total=2)
    mirror.start("job-1")

    mirror.item_finished("job-1", "a", ITEM_STATE_SUCCESS)
    mirror.item_finished("job-1", "b", ITEM_STATE_FAILED)
    mirror.item_finished("job-1", "a", ITEM_STATE_FAILED)
    states = [item["state"] for item in service.get_task(task_id)["items"]]

    self.assertEqual(states, [ITEM_STATE_SUCCESS, ITEM_STATE_FAILED])

  def test_a_repeat_does_not_move_progress(self):
    mirror, service = build_mirror()
    task_id = open_job(mirror, items=["a", "b"], total=2)
    mirror.start("job-1")

    mirror.item_finished("job-1", "a", ITEM_STATE_SUCCESS)
    mirror.item_finished("job-1", "a", ITEM_STATE_FAILED)

    self.assertEqual(
      service.get_task(task_id)["progress"], {"current": 1, "total": 2}
    )

  def test_the_best_outcome_wins_whichever_thread_lands_first(self):
    import threading

    for order in ((ITEM_STATE_SUCCESS, ITEM_STATE_FAILED),
                  (ITEM_STATE_FAILED, ITEM_STATE_SUCCESS)):
      mirror, service = build_mirror()
      task_id = open_job(mirror, items=["a"], total=1)
      mirror.start("job-1")
      ready = threading.Barrier(2)

      def report(state):
        ready.wait()
        mirror.item_finished("job-1", "a", state, message=state)

      threads = [threading.Thread(target=report, args=(state,)) for state in order]
      for thread in threads:
        thread.start()
      for thread in threads:
        thread.join()

      item = service.get_task(task_id)["items"][0]
      self.assertEqual(item["state"], ITEM_STATE_SUCCESS, order)
      self.assertEqual(item["message"], ITEM_STATE_SUCCESS, order)


class MirrorBookkeepingLifetimeTest(unittest.TestCase):
  """The mirror holds notes about live work, not a log of everything ever run."""

  def build_expiring(self, retention_seconds=100.0):
    clock = FakeClock()
    service = TaskService(
      store=TaskStore(
        retention_seconds=retention_seconds,
        clock=clock.now,
        monotonic_clock=clock.monotonic,
      )
    )
    return OwnerTaskMirror(service), service, clock

  def run_job(self, mirror, job_id, keys=("a", "b", "c")):
    open_job(mirror, job_id=job_id, items=list(keys))
    mirror.start(job_id)
    for key in keys:
      mirror.item_finished(job_id, key, ITEM_STATE_SUCCESS)
    mirror.finish(job_id)

  def test_per_unit_notes_are_released_when_the_job_ends(self):
    """One note per post is the bulk of it; a walk of 500 must not keep them."""
    mirror, service, clock = self.build_expiring()

    self.run_job(mirror, "job-1")

    self.assertEqual(mirror.tracked_units("job-1"), 0)

  def test_per_unit_notes_exist_while_the_job_runs(self):
    mirror, service, clock = self.build_expiring()
    open_job(mirror, job_id="job-1", items=["a", "b"])
    mirror.start("job-1")

    mirror.item_finished("job-1", "a", ITEM_STATE_SUCCESS)

    self.assertEqual(mirror.tracked_units("job-1"), 1)

  def test_the_task_id_still_answers_after_the_job_ends(self):
    """Releasing the notes must not cost the browser its task id."""
    mirror, service, clock = self.build_expiring()

    self.run_job(mirror, "job-1")

    self.assertIsNotNone(mirror.task_id("job-1"))

  def test_notes_do_not_pile_up_across_jobs(self):
    mirror, service, clock = self.build_expiring()

    for index in range(20):
      self.run_job(mirror, "job-{}".format(index))

    self.assertEqual(
      sum(mirror.tracked_units("job-{}".format(index)) for index in range(20)), 0
    )

  def test_an_association_does_not_outlive_the_task_it_points_at(self):
    mirror, service, clock = self.build_expiring(retention_seconds=100.0)
    self.run_job(mirror, "job-1")

    clock.advance(101)
    ##
    ## The task has expired from the store; opening the next job is when the
    ## mirror notices.
    ##
    self.run_job(mirror, "job-2")

    self.assertIsNone(mirror.task_id("job-1"))
    self.assertIsNotNone(mirror.task_id("job-2"))

  def test_associations_stay_bounded_over_many_jobs(self):
    """Every job start prunes, so the map tracks live work, not history."""
    mirror, service, clock = self.build_expiring(retention_seconds=10.0)

    for index in range(50):
      clock.advance(11)
      self.run_job(mirror, "job-{}".format(index))

    self.assertEqual(mirror.tracked(), 1)

  def test_a_running_job_is_never_pruned(self):
    """Long work keeps its association however many jobs come and go."""
    mirror, service, clock = self.build_expiring(retention_seconds=10.0)
    open_job(mirror, job_id="long", items=["a"])
    mirror.start("long")

    for index in range(20):
      clock.advance(11)
      self.run_job(mirror, "job-{}".format(index))

    self.assertIsNotNone(mirror.task_id("long"))


class MirrorTerminalStateTest(unittest.TestCase):
  """What the user is told the whole batch amounted to."""

  def run_job(self, states, stopped_early=False, message=None):
    mirror, service = build_mirror()
    keys = ["post-{}".format(index) for index in range(len(states))]
    task_id = open_job(mirror, items=keys, total=len(keys))
    mirror.start("job-1")
    for key, state in zip(keys, states):
      mirror.item_finished("job-1", key, state)
    mirror.finish("job-1", message=message, stopped_early=stopped_early)
    return service.get_task(task_id)

  def test_all_downloaded_is_a_success(self):
    task = self.run_job([ITEM_STATE_SUCCESS, ITEM_STATE_SUCCESS])

    self.assertEqual(task["state"], TASK_STATE_SUCCESS)

  def test_already_downloaded_still_counts_as_success(self):
    """Skipped means the goal was already met, not that something went wrong."""
    task = self.run_job([ITEM_STATE_SUCCESS, ITEM_STATE_SKIPPED])

    self.assertEqual(task["state"], TASK_STATE_SUCCESS)

  def test_everything_skipped_is_a_success(self):
    task = self.run_job([ITEM_STATE_SKIPPED, ITEM_STATE_SKIPPED])

    self.assertEqual(task["state"], TASK_STATE_SUCCESS)

  def test_some_failed_is_partial(self):
    task = self.run_job([ITEM_STATE_SUCCESS, ITEM_STATE_FAILED])

    self.assertEqual(task["state"], TASK_STATE_PARTIAL)
    self.assertIn("1", task["message"])

  def test_skipped_alongside_failed_is_still_partial(self):
    task = self.run_job([ITEM_STATE_SKIPPED, ITEM_STATE_FAILED])

    self.assertEqual(task["state"], TASK_STATE_PARTIAL)

  def test_all_failed_is_a_failure(self):
    task = self.run_job([ITEM_STATE_FAILED, ITEM_STATE_FAILED])

    self.assertEqual(task["state"], TASK_STATE_FAILED)

  def test_an_owner_with_no_posts_succeeds_with_an_explanation(self):
    """Nothing to download is not a failure, and not a fake 42/42 either."""
    mirror, service = build_mirror()
    task_id = open_job(mirror, mode="all")
    mirror.start("job-1")

    mirror.finish("job-1")
    task = service.get_task(task_id)

    self.assertEqual(task["state"], TASK_STATE_SUCCESS)
    self.assertEqual(task["progress"], {"current": 0, "total": 0})
    self.assertIsNotNone(task["message"])

  def test_a_walk_stopped_part_way_keeps_what_it_downloaded(self):
    task = self.run_job(
      [ITEM_STATE_SUCCESS], stopped_early=True, message="停在第 2 个作品：登录已失效"
    )

    self.assertEqual(task["state"], TASK_STATE_PARTIAL)
    self.assertEqual(task["message"], "停在第 2 个作品：登录已失效")

  def test_a_walk_that_downloaded_nothing_before_stopping_fails(self):
    task = self.run_job([], stopped_early=True, message="登录已失效")

    self.assertEqual(task["state"], TASK_STATE_FAILED)
    self.assertEqual(task["message"], "登录已失效")

  def test_a_task_only_ends_once(self):
    """Two owners finishing one job would otherwise fight over the end state."""
    mirror, service = build_mirror()
    task_id = open_job(mirror, items=["a"], total=1)
    mirror.start("job-1")
    mirror.item_finished("job-1", "a", ITEM_STATE_SUCCESS)

    mirror.finish("job-1")
    mirror.finish("job-1", message="迟到的结束", stopped_early=True)

    task = service.get_task(task_id)
    self.assertEqual(task["state"], TASK_STATE_SUCCESS)
    self.assertNotEqual(task["message"], "迟到的结束")

  def test_the_task_id_survives_the_end_of_the_job(self):
    """The browser polls a task after it ends; the association must hold."""
    mirror, service = build_mirror()
    task_id = open_job(mirror, items=["a"], total=1)
    mirror.start("job-1")
    mirror.item_finished("job-1", "a", ITEM_STATE_SUCCESS)
    mirror.finish("job-1")

    self.assertEqual(mirror.task_id("job-1"), task_id)


class MirrorFailureIsolationTest(unittest.TestCase):
  """Task mirroring is telemetry; a download must never fail because of it."""

  def test_no_mirror_call_raises_when_the_task_layer_is_broken(self):
    broken = BrokenTaskService()
    mirror = OwnerTaskMirror(broken)

    task_id = open_job(mirror, items=["a"], total=1)
    mirror.start("job-1")
    mirror.narrate("job-1", "正在下载")
    mirror.add_item("job-1", "b")
    mirror.item_running("job-1", "a")
    mirror.item_finished("job-1", "a", ITEM_STATE_SUCCESS)
    mirror.settle_total("job-1")
    mirror.finish("job-1")

    self.assertIsNone(task_id)
    self.assertIn("create_task", broken.calls)

  def test_a_failed_creation_leaves_later_calls_as_no_ops(self):
    broken = BrokenTaskService()
    mirror = OwnerTaskMirror(broken)

    open_job(mirror)
    broken.calls.clear()
    mirror.item_finished("job-1", "a", ITEM_STATE_SUCCESS)

    self.assertEqual(broken.calls, [])
    self.assertIsNone(mirror.task_id("job-1"))

  def test_a_mirror_without_a_task_service_does_nothing_quietly(self):
    """A runtime built without task wiring still downloads."""
    mirror = OwnerTaskMirror(None)

    task_id = open_job(mirror, items=["a"], total=1)
    mirror.start("job-1")
    mirror.item_finished("job-1", "a", ITEM_STATE_SUCCESS)
    mirror.finish("job-1")

    self.assertIsNone(task_id)
    self.assertIsNone(mirror.task_id("job-1"))
    self.assertFalse(mirror.enabled)

  def test_one_broken_call_does_not_stop_the_rest(self):
    """A single failing update must not silence every later report."""
    service = TaskService()
    calls = []
    original = service.update_item

    def flaky(task_id, key, **kwargs):
      calls.append(key)
      if key == "a":
        raise RuntimeError("mirror hiccup")
      return original(task_id, key, **kwargs)

    service.update_item = flaky
    mirror = OwnerTaskMirror(service)
    task_id = open_job(mirror, items=["a", "b"], total=2)
    mirror.start("job-1")

    mirror.item_finished("job-1", "a", ITEM_STATE_SUCCESS)
    mirror.item_finished("job-1", "b", ITEM_STATE_SUCCESS)

    self.assertEqual(calls, ["a", "b"])
    self.assertEqual(service.get_task(task_id)["progress"]["current"], 1)


class RecordingLogger:
  def __init__(self):
    self.errors = []
    self.warnings = []

  def error(self, message):
    self.errors.append(message)

  def warning(self, message):
    self.warnings.append(message)

  def info(self, message):
    pass


class MirrorLoggingTest(unittest.TestCase):
  """A reporting failure is never fatal, but it is never silent either."""

  def capture(self):
    from backend.src.service import owner_task_mirror as module

    logger = RecordingLogger()
    original = module.get_logger
    module.get_logger = lambda: logger
    self.addCleanup(lambda: setattr(module, "get_logger", original))
    return logger

  def test_a_broken_task_layer_is_logged_as_an_error(self):
    logger = self.capture()
    mirror = OwnerTaskMirror(BrokenTaskService())

    open_job(mirror)

    self.assertEqual(len(logger.errors), 1)
    self.assertIn("create", logger.errors[0])
    self.assertIn("job-1", logger.errors[0])

  def test_a_rejected_transition_is_logged_rather_than_swallowed(self):
    """Our own logic errors must be as visible as anyone else's."""
    logger = self.capture()
    mirror, service = build_mirror()
    open_job(mirror, items=["a"], total=1)
    mirror.start("job-1")
    ##
    ## Someone else ended the task behind the mirror's back, so the mirror's own
    ## finish is now an illegal transition.
    ##
    service.finish_failed(mirror.task_id("job-1"), message="别处结束的")

    mirror.finish("job-1")

    self.assertTrue(logger.warnings or logger.errors)

  def test_narrating_a_finished_task_is_reported(self):
    logger = self.capture()
    mirror, service = build_mirror()
    open_job(mirror, items=["a"], total=1)
    mirror.start("job-1")
    mirror.item_finished("job-1", "a", ITEM_STATE_SUCCESS)
    mirror.finish("job-1")

    mirror.narrate("job-1", "迟到的日志")

    self.assertEqual(len(logger.errors), 1)
    self.assertIn("narrate", logger.errors[0])

  def test_a_second_finish_says_so(self):
    logger = self.capture()
    mirror, service = build_mirror()
    open_job(mirror, items=["a"], total=1)
    mirror.start("job-1")
    mirror.item_finished("job-1", "a", ITEM_STATE_SUCCESS)

    mirror.finish("job-1")
    mirror.finish("job-1")

    self.assertEqual(len(logger.warnings), 1)
    self.assertIn("already", logger.warnings[0])


class MirrorConcurrentFinishTest(unittest.TestCase):
  """Two workers reaching the end of one job at the same moment."""

  def finish_from_two_threads(self, mirror, logger=None):
    import threading

    ready = threading.Barrier(2)
    escaped = []

    def run():
      ready.wait()
      try:
        mirror.finish("job-1")
      except Exception as e:
        escaped.append(e)

    threads = [threading.Thread(target=run) for _ in range(2)]
    for thread in threads:
      thread.start()
    for thread in threads:
      thread.join()
    return escaped

  def test_only_the_first_finish_decides_the_end_state(self):
    mirror, service = build_mirror()
    task_id = open_job(mirror, items=["a"], total=1)
    mirror.start("job-1")
    mirror.item_finished("job-1", "a", ITEM_STATE_SUCCESS)

    escaped = self.finish_from_two_threads(mirror)
    task = service.get_task(task_id)

    self.assertEqual(escaped, [])
    self.assertEqual(task["state"], TASK_STATE_SUCCESS)

  def test_the_loser_changes_nothing(self):
    mirror, service = build_mirror()
    task_id = open_job(mirror, items=["a", "b"], total=2)
    mirror.start("job-1")
    mirror.item_finished("job-1", "a", ITEM_STATE_SUCCESS)
    mirror.item_finished("job-1", "b", ITEM_STATE_FAILED)

    self.finish_from_two_threads(mirror)
    task = service.get_task(task_id)

    self.assertEqual(task["state"], TASK_STATE_PARTIAL)
    self.assertEqual(task["progress"], {"current": 2, "total": 2})

  def test_the_race_leaves_a_trace_in_the_log(self):
    from backend.src.service import owner_task_mirror as module

    logger = RecordingLogger()
    original = module.get_logger
    module.get_logger = lambda: logger
    self.addCleanup(lambda: setattr(module, "get_logger", original))

    mirror, service = build_mirror()
    open_job(mirror, items=["a"], total=1)
    mirror.start("job-1")
    mirror.item_finished("job-1", "a", ITEM_STATE_SUCCESS)

    self.finish_from_two_threads(mirror)

    ##
    ## Either door is acceptable - the pre-check that says "already finished", or
    ## the store rejecting the transition - but the event must be visible.
    ##
    self.assertTrue(logger.warnings or logger.errors)


class MirrorHousekeepingTest(unittest.TestCase):
  def test_associations_of_forgotten_tasks_are_dropped(self):
    """The map must not outlive the tasks it points at."""
    mirror, service = build_mirror()
    open_job(mirror, job_id="old")
    service.store._tasks.clear()

    open_job(mirror, job_id="new")

    self.assertIsNone(mirror.task_id("old"))
    self.assertIsNotNone(mirror.task_id("new"))


if __name__ == "__main__":
  unittest.main()
