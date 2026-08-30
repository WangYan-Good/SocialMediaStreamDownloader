##
## Publishing a journal note so that a crash cannot leave half of one.
##
## The failure this guards against is subtle: a note that exists but is
## truncated looks exactly like a real note to whatever reads the directory
## later, and a replay driven by half a JSON document is worse than a replay
## that never happens.  So nothing is ever written at the final name - bytes go
## to a hidden temporary, are committed, and only then does the final name come
## into existence, atomically.
##
## The same two-part durability argument as the media itself: ``fsync`` on the
## file commits the bytes, and ``fsync`` on the parent commits the *name* that
## reaches them.
##
from datetime import datetime
from pathlib import Path
import errno
import json
import os
import stat
import tempfile
import unittest
from unittest import mock

from backend.src.service.recording_recovery_journal import (
  JOURNAL_DIRECTORY_NAME,
  RecordingJournalConflict,
  RecordingJournalUnavailable,
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


class _Log:
  def __init__(self):
    self.entries = []

  def note(self, entry):
    self.entries.append(entry)


def instrument(service, log, *, fail=None):
  """Name each durability step so the order can be asserted, not just the calls."""
  fail = fail or {}
  real_sync_file = service._sync_file
  real_sync_directory = service._sync_directory
  real_link = os.link

  def sync_file(fd):
    log.note("fsync-temp")
    if "sync_file" in fail:
      raise fail["sync_file"]
    return real_sync_file(fd)

  def sync_directory(path):
    name = "fsync-dir-publish" if "link" in log.entries else "fsync-dir-pre"
    if "fsync-dir-publish" in log.entries:
      name = "fsync-dir-cleanup"
    log.note(name)
    key = {
      "fsync-dir-publish": "sync_dir_publish",
      "fsync-dir-cleanup": "sync_dir_cleanup",
    }.get(name)
    if key and key in fail:
      raise fail[key]
    return real_sync_directory(path)

  def link(a, b):
    log.note("link")
    if "link" in fail:
      raise fail["link"]
    return real_link(a, b)

  service._sync_file = sync_file
  service._sync_directory = sync_directory
  return mock.patch.object(os, "link", link)


class DurablePublicationTest(unittest.TestCase):
  def test_a_published_note_is_readable_json_at_the_canonical_name(self):
    with tempfile.TemporaryDirectory() as root:
      published = journal(root).publish(intent(), KEY)

      expected = Path(root).resolve() / JOURNAL_DIRECTORY_NAME / (KEY + ".json")
      self.assertEqual(expected, published)
      payload = json.loads(published.read_text(encoding="utf-8"))
      self.assertEqual(KEY, payload["recovery_key"])
      self.assertEqual(1, payload["schema_version"])

  def test_publication_follows_the_durable_order(self):
    ##
    ## Every adjacent pair is load-bearing:
    ##   fsync-dir-pre -> anything       : the journal directory's own name is
    ##                                     committed before it holds a note
    ##   write         -> fsync-temp     : bytes on the device before any name
    ##   fsync-temp    -> link           : the final name must not reach
    ##                                     uncommitted bytes
    ##   link       -> fsync-dir-publish : the new name is itself journalled
    ##   fsync-dir-publish -> (durable)  : only now may the caller proceed
    ##
    log = _Log()
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      with instrument(service, log):
        service.publish(intent(), KEY)

      self.assertEqual(
        [
          "fsync-dir-pre",
          "fsync-temp",
          "link",
          "fsync-dir-publish",
          "fsync-dir-cleanup",
        ],
        log.entries,
      )

  def test_the_journal_directory_is_committed_before_it_holds_a_note(self):
    ##
    ## First use only. Publishing into a directory whose own name is still
    ## uncommitted would build the note's durability on a parent that a crash
    ## could take away.
    ##
    log = _Log()
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      with instrument(service, log):
        service.publish(intent(), KEY)
        first = list(log.entries)
        log.entries.clear()
        service.publish(intent(), OTHER_KEY)

      self.assertEqual("fsync-dir-pre", first[0])
      ##
      ## The second note reuses the existing directory, so no parent commit.
      ##
      self.assertNotIn("fsync-dir-pre", log.entries)

  def test_the_final_name_is_created_by_link_not_by_writing_to_it(self):
    ##
    ## Nothing is ever opened at the final name. A crash mid-write would
    ## otherwise leave a truncated note that reads as a real one.
    ##
    opened = []
    real_open = os.open

    def spy(path, flags, *args, **kwargs):
      opened.append(str(path))
      return real_open(path, flags, *args, **kwargs)

    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      with mock.patch.object(os, "open", spy):
        published = service.publish(intent(), KEY)

      writes = [p for p in opened if p.endswith(".json")]
      self.assertEqual([], writes)
      self.assertTrue(published.is_file())

  def test_the_temporary_is_hidden_and_removed(self):
    with tempfile.TemporaryDirectory() as root:
      published = journal(root).publish(intent(), KEY)

      remaining = sorted(p.name for p in published.parent.iterdir())
      self.assertEqual([KEY + ".json"], remaining)

  def test_the_note_is_private_to_the_service_account(self):
    with tempfile.TemporaryDirectory() as root:
      published = journal(root).publish(intent(), KEY)

      self.assertEqual(0o600, stat.S_IMODE(published.stat().st_mode))

  def test_publication_leaks_no_descriptors(self):
    if not os.path.isdir("/proc/self/fd"):
      self.skipTest("requires /proc to count descriptors")
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      service.publish(intent(), OTHER_KEY)

      before = len(os.listdir("/proc/self/fd"))
      for index in range(20):
        service.publish(intent(), "{:032x}".format(index))
      after = len(os.listdir("/proc/self/fd"))

      self.assertEqual(before, after)

  def test_a_large_payload_is_written_completely(self):
    ##
    ## A single ``os.write`` is not obliged to consume the whole buffer. A note
    ## with a long title is the cheapest way to notice a missing write loop.
    ##
    with tempfile.TemporaryDirectory() as root:
      long_title = "标题" * 5000
      published = journal(root).publish(intent(title=long_title), KEY)

      payload = json.loads(published.read_text(encoding="utf-8"))
      self.assertEqual(long_title, payload["title"])


class PublicationFailureTest(unittest.TestCase):
  def test_a_temp_that_cannot_be_committed_publishes_nothing(self):
    log = _Log()
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      with instrument(
        service, log, fail={"sync_file": OSError(errno.EIO, "device failure")}
      ):
        with self.assertRaises(RecordingJournalUnavailable):
          service.publish(intent(), KEY)

      self.assertNotIn("link", log.entries)
      self.assertEqual(
        [], sorted(p.name for p in service.root().iterdir())
      )

  def test_a_publish_that_cannot_be_committed_withdraws_the_name(self):
    ##
    ## The name exists but is not durable, so it does not describe a note
    ## anything may act on. Leaving it would advertise a recoverable recording
    ## that is not recoverable, and would take the name from a later attempt.
    ##
    log = _Log()
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      with instrument(
        service, log, fail={"sync_dir_publish": OSError(errno.EIO, "journal")}
      ):
        with self.assertRaises(RecordingJournalUnavailable):
          service.publish(intent(), KEY)

      self.assertIn("link", log.entries)
      self.assertEqual(
        [], sorted(p.name for p in service.root().iterdir())
      )

  def test_a_temp_cleanup_failure_does_not_undo_a_durable_note(self):
    ##
    ## Past the publish commit the note is durable. A leftover hidden temp is
    ## storage hygiene, and refusing to catalogue the recording over it would
    ## be the wrong trade.
    ##
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      real_unlink = os.unlink

      def refuse_temp(path):
        if ".part" in str(path):
          raise OSError(errno.EIO, "cannot unlink temp")
        return real_unlink(path)

      with mock.patch.object(os, "unlink", refuse_temp):
        published = service.publish(intent(), KEY)

      self.assertTrue(published.is_file())
      payload = json.loads(published.read_text(encoding="utf-8"))
      self.assertEqual(KEY, payload["recovery_key"])


class PublicationConflictTest(unittest.TestCase):
  def test_an_existing_note_is_never_overwritten(self):
    ##
    ## Production generates a fresh key per attempt, so a collision means
    ## something is wrong - a reused key, or a replay calling publish when it
    ## should be calling load. Overwriting would destroy the note describing
    ## whatever was recorded first.
    ##
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      first = service.publish(intent(output_path="douyin/first.mp4"), KEY)
      original = first.read_bytes()

      with self.assertRaises(RecordingJournalConflict):
        service.publish(intent(output_path="douyin/second.mp4"), KEY)

      self.assertEqual(original, first.read_bytes())

  def test_a_conflict_leaves_no_temporary_behind(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      service.publish(intent(), KEY)
      try:
        service.publish(intent(), KEY)
      except RecordingJournalConflict:
        pass

      self.assertEqual(
        [KEY + ".json"],
        sorted(p.name for p in service.root().iterdir()),
      )


class PublicationKeyTest(unittest.TestCase):
  def test_only_a_canonical_key_may_name_a_note(self):
    ##
    ## The filename is derived from the key and nothing else, so the key is
    ## the only thing that could smuggle a path component in.
    ##
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      for bad in (
        "../escape", "a/b", "", "0" * 31, "0" * 33,
        "0123456789ABCDEF0123456789abcdef", None, 7,
      ):
        with self.subTest(key=repr(bad)):
          with self.assertRaises((ValueError, TypeError)):
            service.publish(intent(), bad)

  def test_the_output_path_never_reaches_the_filename(self):
    with tempfile.TemporaryDirectory() as root:
      published = journal(root).publish(
        intent(output_path="douyin/live/A/re_1_live.mp4"), KEY
      )

      self.assertEqual(KEY + ".json", published.name)
      self.assertNotIn("live", published.stem)


if __name__ == "__main__":
  unittest.main()


class AcknowledgeTest(unittest.TestCase):
  """Retiring a note once the database owns the recording.

  Removal is itself a durability question: an unlinked-but-uncommitted note can
  come back after a crash. That is survivable - Phase 11B-0 makes a replay of a
  key that already has a row resolve to the existing recording rather than
  insert a second one - but the directory change is still committed so the
  common case leaves nothing behind.
  """

  def test_acknowledging_removes_the_note(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      published = service.publish(intent(), KEY)

      service.acknowledge(KEY)

      self.assertFalse(published.exists())
      self.assertEqual([], sorted(p.name for p in service.root().iterdir()))

  def test_the_removal_is_committed(self):
    ##
    ## Otherwise the note is gone only in the kernel's view, and a crash
    ## restores a note for a recording the database already has.
    ##
    log = _Log()
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      service.publish(intent(), KEY)
      with instrument(service, log):
        log.entries.clear()
        service.acknowledge(KEY)

      self.assertIn("fsync-dir-pre", log.entries)

  def test_acknowledging_an_absent_note_is_not_an_error(self):
    ##
    ## The note may already be gone - acknowledged before a retry, or removed
    ## by an operator. Nothing is owed to a caller who asked twice.
    ##
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      service.ensure_root()

      service.acknowledge(KEY)
      service.acknowledge(KEY)

  def test_acknowledging_leaves_other_notes_alone(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      service.publish(intent(), KEY)
      other = service.publish(intent(), OTHER_KEY)

      service.acknowledge(KEY)

      self.assertTrue(other.is_file())

  def test_only_a_canonical_key_may_be_acknowledged(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      for bad in ("../escape", "a/b", "", "0" * 31, None, 7):
        with self.subTest(key=repr(bad)):
          with self.assertRaises((ValueError, TypeError)):
            service.acknowledge(bad)
