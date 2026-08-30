##
## One canonicalisation of "what gets persisted about a recording".
##
## Today a recording is validated and normalised on its way into the database,
## inside ``record()``.  A future replay reads a journal rather than a
## ``LiveDownloadResult``, and if it had to reach the same database row it
## would need either a second copy of those rules or a fabricated result
## object.  Both drift.
##
## So the normalisation is lifted into a value: ``prepare()`` turns a result
## into an intent, and ``record_prepared()`` is the only thing that writes.
## The ordinary path and the eventual replay path then share one set of rules
## by construction rather than by discipline.
##
from datetime import datetime
import unittest

from backend.src.service.recording_resource import (
  RecordingNotPersistable,
  RecordingPersistenceIntent,
  RecordingResourceService,
)


class FakeResult:
  def __init__(self, **overrides):
    self.ok = True
    self.recorded = True
    self.test_mode = False
    self.room_id = "998877"
    self.owner_user_id = "owner-1"
    self.title = "Launch title"
    self.protocol = "hls"
    self.output_path = "/media/douyin/live/A/live.mp4"
    self.started_at = datetime(2026, 8, 30, 9, 0, 0)
    self.finished_at = datetime(2026, 8, 30, 10, 0, 0)
    for name, value in overrides.items():
      setattr(self, name, value)


def service():
  return RecordingResourceService(repository_provider=lambda: None)


class PrepareTest(unittest.TestCase):
  """What ``prepare`` extracts, and what it refuses."""

  def test_a_recorded_result_becomes_an_intent(self):
    intent = service().prepare(
      FakeResult(), app_user_id=41, platform="douyin", source="task_api"
    )

    self.assertIsInstance(intent, RecordingPersistenceIntent)
    self.assertEqual(41, intent.app_user_id)
    self.assertEqual("douyin", intent.platform)
    self.assertEqual("998877", intent.room_id)
    self.assertEqual("owner-1", intent.owner_user_id)
    self.assertEqual("Launch title", intent.title)
    self.assertEqual("hls", intent.protocol)
    self.assertEqual("/media/douyin/live/A/live.mp4", intent.output_path)
    self.assertEqual(datetime(2026, 8, 30, 9, 0, 0), intent.started_at)
    self.assertEqual(datetime(2026, 8, 30, 10, 0, 0), intent.finished_at)
    self.assertEqual("task_api", intent.source)

  def test_an_intent_cannot_be_edited_after_it_is_built(self):
    ##
    ## It is handed to a journal writer and later to the database. A value that
    ## could be adjusted in between would make "what was journalled" and "what
    ## was stored" two different questions.
    ##
    intent = service().prepare(
      FakeResult(), app_user_id=41, platform="douyin", source="task_api"
    )
    with self.assertRaises(Exception):
      intent.output_path = "/media/elsewhere.mp4"

  def test_the_intent_carries_no_recovery_key(self):
    ##
    ## The key identifies an attempt to persist; the intent describes the
    ## recording. Folding them together would make the same recording
    ## un-replayable under a second key.
    ##
    intent = service().prepare(
      FakeResult(), app_user_id=41, platform="douyin", source="task_api"
    )
    self.assertNotIn("recovery_key", intent.__dataclass_fields__)

  def test_the_intent_carries_no_stream_access(self):
    intent = service().prepare(
      FakeResult(), app_user_id=41, platform="douyin", source="task_api"
    )
    for forbidden in (
      "stream_url", "url", "headers", "cookies", "token", "sign",
      "proxies", "authorization", "task_id",
    ):
      self.assertNotIn(forbidden, intent.__dataclass_fields__)

  def test_an_anonymous_recording_prepares_with_no_owner(self):
    intent = service().prepare(
      FakeResult(), app_user_id=None, platform="douyin", source="direct"
    )
    self.assertIsNone(intent.app_user_id)

  def test_optional_text_is_normalised_the_way_the_database_expects(self):
    intent = service().prepare(
      FakeResult(room_id="  ", owner_user_id=None, title="  Trimmed  "),
      app_user_id=41,
      platform="  douyin  ",
      source="  task_api  ",
    )
    self.assertIsNone(intent.room_id)
    self.assertIsNone(intent.owner_user_id)
    self.assertEqual("Trimmed", intent.title)
    self.assertEqual("douyin", intent.platform)
    self.assertEqual("task_api", intent.source)

  def test_the_output_path_is_preserved_verbatim(self):
    ##
    ## The recorder wrote this exact name. Normalising it here would name a
    ## file nobody created.
    ##
    path = "/media/douyin/live/A/re_1_live.mp4"
    intent = service().prepare(
      FakeResult(output_path=path),
      app_user_id=41, platform="douyin", source="task_api",
    )
    self.assertEqual(path, intent.output_path)

  def test_a_result_that_recorded_nothing_is_refused(self):
    for overrides in (
      {"recorded": False},
      {"test_mode": True},
      {"output_path": None},
      {"output_path": "   "},
    ):
      with self.subTest(overrides=overrides):
        with self.assertRaises(RecordingNotPersistable):
          service().prepare(
            FakeResult(**overrides),
            app_user_id=41, platform="douyin", source="task_api",
          )

  def test_invalid_arguments_are_refused_before_an_intent_exists(self):
    for kwargs in (
      {"app_user_id": 0},
      {"app_user_id": -1},
      {"app_user_id": "41"},
      {"platform": ""},
      {"platform": "   "},
      {"source": ""},
    ):
      with self.subTest(kwargs=kwargs):
        arguments = {
          "app_user_id": 41, "platform": "douyin", "source": "task_api"
        }
        arguments.update(kwargs)
        with self.assertRaises(ValueError):
          service().prepare(FakeResult(), **arguments)


class RecordCompatibilityTest(unittest.TestCase):
  """``record`` keeps answering exactly as it did before the refactor."""

  def repository(self):
    calls = []

    class FakeRepository:
      def create_recording(self, record, recovery_key=None):
        calls.append((record, recovery_key))
        return 73

    return FakeRepository(), calls

  def test_record_still_persists_the_same_facts(self):
    repository, calls = self.repository()
    resource = RecordingResourceService(repository_provider=lambda: repository)

    recording_id = resource.record(
      FakeResult(), app_user_id=41, platform="douyin", source="task_api"
    )

    self.assertEqual(73, recording_id)
    record, recovery_key = calls[0]
    self.assertIsNone(recovery_key)
    self.assertEqual(41, record["app_user_id"])
    self.assertEqual("douyin", record["platform"])
    self.assertEqual("/media/douyin/live/A/live.mp4", record["output_path"])
    self.assertEqual("task_api", record["source"])
    self.assertEqual(datetime(2026, 8, 30, 10, 0, 0), record["finished_at"])

  def test_record_prepared_writes_the_same_row_from_an_intent(self):
    ##
    ## The equivalence that lets a replay skip the result object entirely.
    ##
    repository, calls = self.repository()
    resource = RecordingResourceService(repository_provider=lambda: repository)
    intent = resource.prepare(
      FakeResult(), app_user_id=41, platform="douyin", source="task_api"
    )

    resource.record(
      FakeResult(), app_user_id=41, platform="douyin", source="task_api"
    )
    resource.record_prepared(intent)

    from_result, _ = calls[0]
    from_intent, _ = calls[1]
    self.assertEqual(from_result, from_intent)

  def test_record_prepared_carries_the_recovery_key_through(self):
    repository, calls = self.repository()
    resource = RecordingResourceService(repository_provider=lambda: repository)
    intent = resource.prepare(
      FakeResult(), app_user_id=41, platform="douyin", source="task_api"
    )
    key = "0123456789abcdef0123456789abcdef"

    resource.record_prepared(intent, recovery_key=key)

    self.assertEqual(key, calls[0][1])


if __name__ == "__main__":
  unittest.main()
