##
## Reading a note back, and refusing the ones that cannot be trusted.
##
## ``load`` is the primitive Phase 11C will replay from, so every value it
## returns eventually becomes a database row.  That makes it the wrong place to
## be forgiving: a note whose version is unrecognised, whose key disagrees with
## its filename, or whose fields are the wrong shape describes a recording this
## build cannot faithfully reproduce, and guessing would insert something
## nobody recorded.
##
## It reads exactly one name.  Nothing here enumerates the directory - that is
## a scanner, and a scanner is a later phase.
##
from datetime import datetime
from pathlib import Path
import json
import os
import tempfile
import unittest

from backend.src.service.recording_recovery_journal import (
  JOURNAL_MAX_BYTES,
  payload_for,
  RecordingJournalCorrupt,
  RecordingJournalUnavailable,
  RecordingJournalUnsupportedVersion,
  RecordingRecoveryJournal,
)
from backend.src.service.recording_resource import RecordingPersistenceIntent

KEY = "0123456789abcdef0123456789abcdef"
OTHER_KEY = "fedcba9876543210fedcba9876543210"


def intent(**overrides):
  base = {
    "app_user_id": 41,
    "platform": "douyin",
    "room_id": "998877",
    "owner_user_id": "owner-1",
    "title": "Launch title",
    "protocol": "hls",
    "output_path": "douyin/live/A/live.mp4",
    "started_at": datetime(2026, 8, 30, 9, 0, 0, 123000),
    "finished_at": datetime(2026, 8, 30, 10, 0, 0, 456000),
    "source": "task_api",
  }
  base.update(overrides)
  return RecordingPersistenceIntent(**base)


def journal(root):
  return RecordingRecoveryJournal(
    config_loader=lambda: {"download": {"save_path": str(root)}}
  )


def write_note(service, key, payload, *, raw=None):
  directory = service.ensure_root()
  target = directory / "{}.json".format(key)
  if raw is not None:
    target.write_bytes(raw)
  else:
    target.write_text(json.dumps(payload), encoding="utf-8")
  return target


class LoadRoundtripTest(unittest.TestCase):
  def test_a_published_note_loads_back_as_the_same_intent(self):
    ##
    ## The property the whole design rests on: what a replay reconstructs is
    ## what was captured, through real bytes on a real filesystem.
    ##
    original = intent()
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      service.publish(original, KEY)

      restored = service.load(KEY)

      self.assertEqual(original, restored)
      self.assertIsInstance(restored.started_at, datetime)

  def test_absent_optional_facts_survive_the_roundtrip(self):
    original = intent(
      app_user_id=None, room_id=None, owner_user_id=None,
      title=None, protocol=None, started_at=None, finished_at=None,
    )
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      service.publish(original, KEY)

      self.assertEqual(original, service.load(KEY))

  def test_a_missing_note_is_absent_rather_than_an_error(self):
    ##
    ## Nothing to replay is an ordinary answer, not a fault - most keys a
    ## caller might ask about were acknowledged and removed on purpose.
    ##
    with tempfile.TemporaryDirectory() as root:
      self.assertIsNone(journal(root).load(KEY))

  def test_loading_reads_only_the_exact_canonical_name(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      service.publish(intent(), KEY)
      directory = service.root()
      ##
      ## Decoys a scanner might pick up. ``load`` addresses one name, so none
      ## of these can be reached.
      ##
      (directory / "{}.json.bak".format(KEY)).write_text("{}")
      (directory / ".{}.journal-abc.part".format(OTHER_KEY)).write_text("{}")

      self.assertIsNotNone(service.load(KEY))
      self.assertIsNone(service.load(OTHER_KEY))

  def test_loading_never_enumerates_the_directory(self):
    listed = []
    real_listdir = os.listdir

    def spy(path="."):
      listed.append(str(path))
      return real_listdir(path)

    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      service.publish(intent(), KEY)
      import unittest.mock as m
      with m.patch.object(os, "listdir", spy), m.patch.object(
        os, "scandir", side_effect=AssertionError("load must not scan")
      ):
        service.load(KEY)

      self.assertEqual([], listed)

  def test_only_a_canonical_key_may_be_loaded(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      for bad in ("../escape", "a/b", "", "0" * 31, "F" * 32, None, 7):
        with self.subTest(key=repr(bad)):
          with self.assertRaises((ValueError, TypeError)):
            service.load(bad)


class LoadValidationTest(unittest.TestCase):
  def test_an_unsupported_schema_version_fails_closed(self):
    ##
    ## A newer build wrote this. Reading it with today's rules would
    ## reconstruct a recording from fields that may have changed meaning, so
    ## the honest answer is to refuse.
    ##
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      body = payload_for(intent(), KEY)
      body["schema_version"] = 2
      write_note(service, KEY, body)

      with self.assertRaises(RecordingJournalUnsupportedVersion):
        service.load(KEY)

  def test_a_missing_schema_version_fails_closed(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      body = payload_for(intent(), KEY)
      del body["schema_version"]
      write_note(service, KEY, body)

      with self.assertRaises(RecordingJournalUnsupportedVersion):
        service.load(KEY)

  def test_malformed_json_is_reported_as_corruption(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      write_note(service, KEY, None, raw=b'{"schema_version": 1, "platf')

      with self.assertRaises(RecordingJournalCorrupt):
        service.load(KEY)

  def test_a_corrupt_note_is_neither_deleted_nor_quarantined(self):
    ##
    ## It is the only surviving description of a recording that may still be on
    ## disk. Removing it to tidy up would destroy the evidence an operator
    ## needs.
    ##
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      raw = b'{"schema_version": 1, "truncated'
      target = write_note(service, KEY, None, raw=raw)

      try:
        service.load(KEY)
      except RecordingJournalCorrupt:
        pass

      self.assertTrue(target.is_file())
      self.assertEqual(raw, target.read_bytes())

  def test_a_note_that_is_not_an_object_is_corrupt(self):
    for raw in (b"[]", b'"text"', b"7", b"null"):
      with self.subTest(raw=raw):
        with tempfile.TemporaryDirectory() as root:
          service = journal(root)
          write_note(service, KEY, None, raw=raw)
          with self.assertRaises(RecordingJournalCorrupt):
            service.load(KEY)

  def test_the_payload_key_must_match_the_filename(self):
    ##
    ## Otherwise a note could be renamed to claim another recording's identity,
    ## and a replay would attach these facts to that key.
    ##
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      body = payload_for(intent(), OTHER_KEY)
      write_note(service, KEY, body)

      with self.assertRaises(RecordingJournalCorrupt):
        service.load(KEY)

  def test_wrongly_typed_fields_are_corrupt(self):
    for field, value in (
      ("app_user_id", "41"),
      ("app_user_id", True),
      ("platform", 7),
      ("platform", None),
      ("output_path", None),
      ("output_path", 7),
      ("source", None),
      ("room_id", 7),
      ("title", 7),
      ("started_at", 1234567890),
      ("finished_at", "not-a-timestamp"),
    ):
      with self.subTest(field=field, value=repr(value)):
        with tempfile.TemporaryDirectory() as root:
          service = journal(root)
          body = payload_for(intent(), KEY)
          body[field] = value
          write_note(service, KEY, body)
          with self.assertRaises(RecordingJournalCorrupt):
            service.load(KEY)

  def test_a_missing_field_is_corrupt(self):
    for field in ("platform", "output_path", "source", "app_user_id"):
      with self.subTest(field=field):
        with tempfile.TemporaryDirectory() as root:
          service = journal(root)
          body = payload_for(intent(), KEY)
          del body[field]
          write_note(service, KEY, body)
          with self.assertRaises(RecordingJournalCorrupt):
            service.load(KEY)


class LoadBoundsTest(unittest.TestCase):
  def test_the_size_bound_is_small_and_explicit(self):
    self.assertEqual(64 * 1024, JOURNAL_MAX_BYTES)

  def test_an_oversized_note_is_refused_without_being_read_whole(self):
    ##
    ## A note is a few hundred bytes. A file that is not is either corrupt or
    ## something else entirely, and reading it into memory unbounded is how a
    ## damaged directory becomes an outage.
    ##
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      write_note(service, KEY, None, raw=b"{" + b"0" * (JOURNAL_MAX_BYTES + 10))

      with self.assertRaises(RecordingJournalCorrupt):
        service.load(KEY)


class LoadSymlinkTest(unittest.TestCase):
  @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "requires O_NOFOLLOW")
  def test_a_symlinked_note_is_not_followed(self):
    ##
    ## The link points at a note that is *perfectly valid* for this key. That
    ## is deliberate: if the target were malformed, refusing it would look the
    ## same as following it and finding bad content, and the test would pass
    ## even with the link being followed. Because the target would load
    ## cleanly, the only way to fail here is to have refused the link itself.
    ##
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      directory = service.ensure_root()
      elsewhere = Path(root) / "elsewhere.json"
      elsewhere.write_text(
        json.dumps(payload_for(intent(), KEY)), encoding="utf-8"
      )
      (directory / "{}.json".format(KEY)).symlink_to(elsewhere)

      with self.assertRaises(RecordingJournalUnavailable):
        service.load(KEY)

  def test_a_directory_at_the_note_name_is_refused(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      (service.ensure_root() / "{}.json".format(KEY)).mkdir()

      with self.assertRaises(RecordingJournalUnavailable):
        service.load(KEY)


if __name__ == "__main__":
  unittest.main()
