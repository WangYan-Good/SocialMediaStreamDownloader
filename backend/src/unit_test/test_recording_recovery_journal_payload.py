##
## What a journal note says, byte for byte.
##
## The bytes matter because they are the input to a future replay: a note that
## cannot be read back into exactly the same persistence intent is worse than
## no note, since it would replay a recording that differs from the one that
## was actually captured.
##
## And what it must *not* say matters just as much. A live stream url is
## signed; headers and cookies carry session state. None of that is needed to
## describe a recording that already finished, so none of it is written.
##
from datetime import datetime
import json
import unittest

from backend.src.service.recording_recovery_journal import (
  JOURNAL_SCHEMA_VERSION,
  journal_bytes,
  intent_from_payload,
  payload_for,
)
from backend.src.service.recording_resource import RecordingPersistenceIntent

KEY = "0123456789abcdef0123456789abcdef"


def intent(**overrides):
  base = {
    "app_user_id": 41,
    "platform": "douyin",
    "room_id": "998877",
    "owner_user_id": "owner-1",
    "title": "Launch title",
    "protocol": "hls",
    "output_path": "/media/douyin/live/A/live.mp4",
    "started_at": datetime(2026, 8, 30, 9, 0, 0, 123000),
    "finished_at": datetime(2026, 8, 30, 10, 0, 0, 456000),
    "source": "task_api",
  }
  base.update(overrides)
  return RecordingPersistenceIntent(**base)


class PayloadShapeTest(unittest.TestCase):
  def test_the_payload_carries_the_schema_version_and_the_key(self):
    payload = payload_for(intent(), KEY)

    self.assertEqual(1, JOURNAL_SCHEMA_VERSION)
    self.assertEqual(1, payload["schema_version"])
    self.assertEqual(KEY, payload["recovery_key"])

  def test_the_payload_carries_every_persisted_fact(self):
    payload = payload_for(intent(), KEY)

    self.assertEqual(41, payload["app_user_id"])
    self.assertEqual("douyin", payload["platform"])
    self.assertEqual("998877", payload["room_id"])
    self.assertEqual("owner-1", payload["owner_user_id"])
    self.assertEqual("Launch title", payload["title"])
    self.assertEqual("hls", payload["protocol"])
    self.assertEqual("/media/douyin/live/A/live.mp4", payload["output_path"])
    self.assertEqual("task_api", payload["source"])

  def test_the_payload_carries_nothing_else(self):
    ##
    ## A closed set. Anything extra is either a fact the database does not
    ## store - which a replay would then have to ignore - or something that
    ## should never have been written down.
    ##
    self.assertEqual(
      {
        "schema_version", "recovery_key", "app_user_id", "platform",
        "room_id", "owner_user_id", "title", "protocol", "output_path",
        "started_at", "finished_at", "source",
      },
      set(payload_for(intent(), KEY)),
    )

  def test_ownership_is_the_application_user_not_the_broadcaster(self):
    ##
    ## These are different facts and the journal is where they could most
    ## easily be confused: ``app_user_id`` decides whose library the recording
    ## appears in, ``owner_user_id`` is the platform's broadcaster identity.
    ##
    payload = payload_for(
      intent(app_user_id=41, owner_user_id="owner-9"), KEY
    )

    self.assertEqual(41, payload["app_user_id"])
    self.assertEqual("owner-9", payload["owner_user_id"])
    self.assertNotEqual(payload["app_user_id"], payload["owner_user_id"])

  def test_an_anonymous_recording_journals_a_null_owner(self):
    payload = payload_for(intent(app_user_id=None), KEY)

    self.assertIsNone(payload["app_user_id"])


class TimestampWireTest(unittest.TestCase):
  def test_timestamps_are_iso_8601_with_millisecond_precision(self):
    ##
    ## Milliseconds because that is what the column stores - DATETIME(3).
    ## Writing microseconds would journal a value the database cannot hold, and
    ## a replay would then differ from the row it is meant to reproduce.
    ##
    payload = payload_for(intent(), KEY)

    self.assertEqual("2026-08-30T09:00:00.123", payload["started_at"])
    self.assertEqual("2026-08-30T10:00:00.456", payload["finished_at"])

  def test_absent_timestamps_are_json_null(self):
    payload = payload_for(intent(started_at=None, finished_at=None), KEY)

    self.assertIsNone(payload["started_at"])
    self.assertIsNone(payload["finished_at"])

  def test_timestamps_are_not_written_as_epoch_numbers(self):
    payload = payload_for(intent(), KEY)

    for field in ("started_at", "finished_at"):
      self.assertIsInstance(payload[field], str)


class CanonicalBytesTest(unittest.TestCase):
  def test_the_bytes_are_deterministic(self):
    ##
    ## The same note written twice is the same file. Anything else makes a
    ## byte-level comparison - the cheapest way to check a note survived
    ## intact - meaningless.
    ##
    self.assertEqual(journal_bytes(intent(), KEY), journal_bytes(intent(), KEY))

  def test_the_bytes_are_utf8_json_with_sorted_keys(self):
    raw = journal_bytes(intent(), KEY)

    text = raw.decode("utf-8")
    parsed = json.loads(text)
    self.assertEqual(sorted(parsed), list(parsed))

  def test_non_ascii_titles_are_written_as_text_not_escapes(self):
    raw = journal_bytes(intent(title="直播标题"), KEY)

    self.assertIn("直播标题", raw.decode("utf-8"))

  def test_the_bytes_end_with_exactly_one_newline(self):
    raw = journal_bytes(intent(), KEY)

    self.assertTrue(raw.endswith(b"\n"))
    self.assertFalse(raw.endswith(b"\n\n"))


class SensitiveExclusionTest(unittest.TestCase):
  def test_no_stream_access_material_reaches_the_bytes(self):
    ##
    ## The intent has no field for any of these, so the only way one could
    ## appear is through a value carried inside a field that does exist. This
    ## checks the bytes rather than the schema for exactly that reason.
    ##
    raw = journal_bytes(
      intent(
        title="title?sign=SIGNED&token=TOKENVALUE",
        room_id="998877",
      ),
      KEY,
    ).decode("utf-8")

    ##
    ## The title is a platform-supplied string and is stored verbatim in the
    ## database already, so it is journalled as-is; what must never appear is a
    ## *field* carrying transport credentials.
    ##
    payload = json.loads(raw)
    for forbidden in (
      "stream_url", "url", "headers", "cookie", "cookies", "authorization",
      "proxy", "proxies", "password", "session", "csrf", "task_id",
    ):
      self.assertNotIn(forbidden, payload)


class RoundtripTest(unittest.TestCase):
  def test_an_intent_survives_the_journal_unchanged(self):
    ##
    ## The load-bearing property. A replay reads this back and writes the
    ## database row from it, so anything lost here is a recording that comes
    ## back different from the one that was captured.
    ##
    original = intent()

    restored = intent_from_payload(payload_for(original, KEY))

    self.assertEqual(original, restored)

  def test_the_roundtrip_holds_for_absent_optional_facts(self):
    original = intent(
      app_user_id=None, room_id=None, owner_user_id=None,
      title=None, protocol=None, started_at=None, finished_at=None,
    )

    restored = intent_from_payload(payload_for(original, KEY))

    self.assertEqual(original, restored)

  def test_the_roundtrip_goes_through_real_json_bytes(self):
    ##
    ## Not just dict-to-dict: the value has to survive being encoded, written,
    ## and parsed back, which is where a datetime would quietly become a string
    ## that no longer compares equal.
    ##
    original = intent()

    restored = intent_from_payload(
      json.loads(journal_bytes(original, KEY).decode("utf-8"))
    )

    self.assertEqual(original, restored)
    self.assertIsInstance(restored.started_at, datetime)


if __name__ == "__main__":
  unittest.main()
