import unittest
from datetime import datetime

from backend.src.task.errors import (
  InvalidProgress,
  InvalidTaskItemState,
  InvalidTaskState,
  InvalidTaskTransition,
  UnknownTaskType,
)
from backend.src.task import model


class TaskStateVocabularyTest(unittest.TestCase):
  """The unified lifecycle owns exactly six words and no more."""

  def test_the_task_states_are_the_agreed_six(self):
    self.assertEqual(
      set(model.TASK_STATES),
      {"pending", "running", "success", "partial", "failed", "cancelled"},
    )

  def test_legacy_words_are_not_task_states(self):
    """``done``/``error``/``living`` belong to items or metadata, never here."""
    for legacy in ("done", "error", "skipped", "living", "offline"):
      self.assertNotIn(legacy, model.TASK_STATES)

  def test_the_item_states_are_the_agreed_five(self):
    self.assertEqual(
      set(model.TASK_ITEM_STATES),
      {"pending", "running", "success", "failed", "skipped"},
    )

  def test_item_states_and_task_states_are_separate_vocabularies(self):
    """An item may be ``skipped``; a task may be ``partial``.  Never swapped."""
    self.assertIn(model.ITEM_STATE_SKIPPED, model.TASK_ITEM_STATES)
    self.assertNotIn(model.ITEM_STATE_SKIPPED, model.TASK_STATES)
    self.assertIn(model.TASK_STATE_PARTIAL, model.TASK_STATES)
    self.assertNotIn(model.TASK_STATE_PARTIAL, model.TASK_ITEM_STATES)

  def test_a_finished_item_is_one_that_will_not_run_again(self):
    """Skipped counts as finished: an already downloaded post is not pending."""
    self.assertEqual(
      set(model.TERMINAL_ITEM_STATES), {"success", "failed", "skipped"}
    )

  def test_the_terminal_states_are_the_four_end_states(self):
    self.assertEqual(
      set(model.TERMINAL_TASK_STATES),
      {"success", "partial", "failed", "cancelled"},
    )


class TaskTypeTest(unittest.TestCase):
  def test_the_four_planned_types_are_reserved(self):
    self.assertEqual(
      set(model.TASK_TYPES),
      {"live_record", "post_download", "owner_batch_download", "live_probe"},
    )

  def test_no_task_type_names_a_platform(self):
    """Platform belongs in metadata, not in the type.

    Otherwise every platform added multiplies this list, and the task centre has
    to special-case each name to answer "show me the downloads".
    """
    for task_type in model.TASK_TYPES:
      for platform in ("douyin", "bilibili", "youtube", "kuaishou", "tiktok"):
        self.assertNotIn(platform, task_type)

  def test_a_second_platform_needs_no_new_type(self):
    """The same kind of work on another platform reuses the same type."""
    self.assertEqual(
      model.validate_task_type(model.TASK_TYPE_POST_DOWNLOAD), "post_download"
    )
    with self.assertRaises(UnknownTaskType):
      model.validate_task_type("bilibili_post_download")

  def test_a_reserved_type_validates(self):
    self.assertEqual(
      model.validate_task_type(model.TASK_TYPE_POST_DOWNLOAD), "post_download"
    )

  def test_an_unknown_type_is_rejected_by_name(self):
    with self.assertRaises(UnknownTaskType) as raised:
      model.validate_task_type("post_dowload")
    self.assertIn("post_dowload", str(raised.exception))

  def test_a_non_string_type_is_rejected(self):
    with self.assertRaises(UnknownTaskType):
      model.validate_task_type(None)


class TaskTransitionTest(unittest.TestCase):
  """Every state change goes through one table, so no caller invents a path."""

  def test_a_pending_task_may_start(self):
    self.assertEqual(
      model.validate_transition(
        model.TASK_STATE_PENDING, model.TASK_STATE_RUNNING
      ),
      "running",
    )

  def test_a_running_task_may_reach_every_end_state(self):
    for target in (
      model.TASK_STATE_SUCCESS,
      model.TASK_STATE_PARTIAL,
      model.TASK_STATE_FAILED,
      model.TASK_STATE_CANCELLED,
    ):
      self.assertEqual(
        model.validate_transition(model.TASK_STATE_RUNNING, target), target
      )

  def test_a_pending_task_may_be_cancelled_before_it_starts(self):
    self.assertEqual(
      model.validate_transition(
        model.TASK_STATE_PENDING, model.TASK_STATE_CANCELLED
      ),
      "cancelled",
    )

  def test_a_pending_task_may_fail_before_it_starts(self):
    """Submission can fail validation after the task is already visible."""
    self.assertEqual(
      model.validate_transition(
        model.TASK_STATE_PENDING, model.TASK_STATE_FAILED
      ),
      "failed",
    )

  def test_a_pending_task_may_not_succeed_without_running(self):
    with self.assertRaises(InvalidTaskTransition):
      model.validate_transition(
        model.TASK_STATE_PENDING, model.TASK_STATE_SUCCESS
      )

  def test_a_finished_task_never_changes_again(self):
    for terminal in model.TERMINAL_TASK_STATES:
      with self.assertRaises(InvalidTaskTransition):
        model.validate_transition(terminal, model.TASK_STATE_RUNNING)

  def test_restating_the_current_state_is_rejected(self):
    """A second ``finish_success`` is a bug in the caller, not a no-op."""
    with self.assertRaises(InvalidTaskTransition):
      model.validate_transition(
        model.TASK_STATE_RUNNING, model.TASK_STATE_RUNNING
      )

  def test_the_rejection_names_both_states(self):
    with self.assertRaises(InvalidTaskTransition) as raised:
      model.validate_transition(
        model.TASK_STATE_SUCCESS, model.TASK_STATE_FAILED
      )
    message = str(raised.exception)
    self.assertIn("success", message)
    self.assertIn("failed", message)

  def test_an_unknown_target_state_is_rejected_as_a_state_error(self):
    with self.assertRaises(InvalidTaskState):
      model.validate_transition(model.TASK_STATE_RUNNING, "done")

  def test_is_terminal_follows_the_table(self):
    self.assertTrue(model.is_terminal(model.TASK_STATE_CANCELLED))
    self.assertFalse(model.is_terminal(model.TASK_STATE_PENDING))
    self.assertFalse(model.is_terminal(model.TASK_STATE_RUNNING))


class TaskItemStateTest(unittest.TestCase):
  def test_a_known_item_state_validates(self):
    self.assertEqual(
      model.validate_item_state(model.ITEM_STATE_SKIPPED), "skipped"
    )

  def test_a_task_state_is_not_an_item_state(self):
    with self.assertRaises(InvalidTaskItemState):
      model.validate_item_state(model.TASK_STATE_PARTIAL)


class ProgressTest(unittest.TestCase):
  def test_progress_normalises_to_current_and_total(self):
    self.assertEqual(model.normalize_progress(18, 42), {"current": 18, "total": 42})

  def test_an_unknown_total_is_allowed(self):
    """A live recording has no fixed total; the UI shows no percentage."""
    self.assertEqual(model.normalize_progress(0, None), {"current": 0, "total": None})

  def test_a_negative_current_is_rejected(self):
    with self.assertRaises(InvalidProgress):
      model.normalize_progress(-1, 10)

  def test_a_negative_total_is_rejected(self):
    with self.assertRaises(InvalidProgress):
      model.normalize_progress(0, -1)

  def test_a_non_integer_is_rejected(self):
    with self.assertRaises(InvalidProgress):
      model.normalize_progress("18", 42)

  def test_a_boolean_is_not_an_integer(self):
    with self.assertRaises(InvalidProgress):
      model.normalize_progress(True, 42)


class TaskPayloadTest(unittest.TestCase):
  """The wire shape the API promises, built once and tested once."""

  def snapshot(self, **overrides):
    snapshot = {
      "task_id": "5f4c",
      "task_type": model.TASK_TYPE_POST_DOWNLOAD,
      "state": model.TASK_STATE_RUNNING,
      "title": "下载作品",
      "message": None,
      "created_at": datetime(2026, 8, 13, 9, 30, 15, 250000),
      "started_at": datetime(2026, 8, 13, 9, 30, 16),
      "finished_at": None,
      "progress": {"current": 2, "total": 10},
      "metadata": {"sec_user_id": "MS4w"},
      "items": [
        {
          "key": "7657271784144009946",
          "state": model.ITEM_STATE_RUNNING,
          "message": None,
          "metadata": {},
        }
      ],
    }
    snapshot.update(overrides)
    return snapshot

  def test_the_payload_carries_every_documented_field(self):
    payload = model.to_payload(self.snapshot())

    self.assertEqual(
      set(payload),
      {
        "task_id",
        "task_type",
        "state",
        "title",
        "message",
        "created_at",
        "started_at",
        "finished_at",
        "progress",
        "metadata",
        "items",
      },
    )

  def test_internal_ownership_is_not_exposed_on_the_wire(self):
    payload = model.to_payload(self.snapshot(app_user_id=42))

    self.assertNotIn("app_user_id", payload)

  def test_timestamps_are_iso_8601(self):
    payload = model.to_payload(self.snapshot())

    self.assertEqual(payload["created_at"], "2026-08-13T09:30:15.250")
    self.assertEqual(payload["started_at"], "2026-08-13T09:30:16.000")

  def test_a_missing_timestamp_stays_null(self):
    self.assertIsNone(model.to_payload(self.snapshot())["finished_at"])

  def test_items_keep_their_own_state_vocabulary(self):
    payload = model.to_payload(self.snapshot())

    self.assertEqual(payload["items"][0]["state"], "running")
    self.assertEqual(payload["items"][0]["key"], "7657271784144009946")

  def test_the_payload_does_not_share_nested_state_with_the_snapshot(self):
    snapshot = self.snapshot(
      metadata={"filters": {"types": ["video"]}},
      items=[
        {
          "key": "a",
          "state": model.ITEM_STATE_RUNNING,
          "message": None,
          "metadata": {"saved": {"urls": ["u1"]}},
        }
      ],
    )

    payload = model.to_payload(snapshot)
    payload["metadata"]["filters"]["types"].append("tampered")
    payload["items"][0]["metadata"]["saved"]["urls"].append("tampered")

    self.assertEqual(snapshot["metadata"], {"filters": {"types": ["video"]}})
    self.assertEqual(snapshot["items"][0]["metadata"], {"saved": {"urls": ["u1"]}})

  def test_the_payload_does_not_share_mutable_state_with_the_snapshot(self):
    snapshot = self.snapshot()

    payload = model.to_payload(snapshot)
    payload["metadata"]["sec_user_id"] = "tampered"
    payload["items"][0]["state"] = "tampered"

    self.assertEqual(snapshot["metadata"]["sec_user_id"], "MS4w")
    self.assertEqual(snapshot["items"][0]["state"], "running")


if __name__ == "__main__":
  unittest.main()
