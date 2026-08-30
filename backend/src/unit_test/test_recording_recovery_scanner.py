##
## Finding the notes that survived a crash.
##
## Phase 11B published notes and read them back one name at a time, and said so
## explicitly: enumerating the directory is a scanner, and a scanner is a later
## phase.  This is that phase.
##
## Enumeration changes what the journal directory *is*.  Until now nothing read
## it without already knowing the exact name it wanted, so a stray file there
## was inert.  A scanner walks whatever is present, and every name it hands
## back becomes a candidate for a database row - which makes this directory a
## trust boundary rather than a private scratch area.
##
## So the rules here are all refusals: exactly one filename shape is a note,
## the directory is opened as a directory or not at all, nothing unknown is
## touched, and the amount of work one startup may do is finite.
##
from pathlib import Path
import os
import tempfile
import unittest

from backend.src.service.recording_recovery_journal import (
  JOURNAL_DIRECTORY_NAME,
  MAX_RECOVERY_JOURNALS_PER_RUN,
  RecordingJournalUnavailable,
  RecordingRecoveryJournal,
)

KEY = "0123456789abcdef0123456789abcdef"
OTHER_KEY = "fedcba9876543210fedcba9876543210"


def journal(root):
  return RecordingRecoveryJournal(
    config_loader=lambda: {"download": {"save_path": str(root)}}
  )


def note(service, key, text="{}"):
  """Put a file at the canonical name for ``key`` without publishing it.

  The scanner's job is to decide which *names* are notes; whether the bytes
  behind a name are a valid note is ``load``'s job, and these tests must not
  depend on it.
  """
  directory = service.ensure_root()
  target = directory / "{}.json".format(key)
  target.write_text(text, encoding="utf-8")
  return target


class CanonicalNameTest(unittest.TestCase):
  """Only ``<32-lowercase-hex>.json`` is a note."""

  def test_a_canonical_note_is_discovered(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      note(service, KEY)

      self.assertEqual([KEY], service.scan_pending_keys().keys)

  def test_the_key_is_reported_not_the_filename(self):
    ##
    ## The reconciler feeds these straight back into ``load``/``acknowledge``,
    ## both of which take a recovery key. Handing back ``<key>.json`` would
    ## make every caller strip the suffix, and one of them would forget.
    ##
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      note(service, KEY)

      discovered = service.scan_pending_keys().keys
      self.assertEqual([KEY], discovered)
      self.assertNotIn(".json", discovered[0])

  def test_in_flight_temporaries_are_never_notes(self):
    ##
    ## Publication writes ``.<key>.journal-<random>.part`` in this same
    ## directory. Replaying one would replay a note whose bytes are still
    ## being written.
    ##
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      directory = service.ensure_root()
      (directory / ".{}.journal-abcdef01.part".format(KEY)).write_text("{}")

      self.assertEqual([], service.scan_pending_keys().keys)

  def test_unknown_files_are_never_notes(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      directory = service.ensure_root()
      for name in (
        "README",
        "foo.json",
        "{}.json.bak".format(KEY),
        "{}.JSON".format(KEY),
        "{}.json".format(KEY.upper()),
        "{}.json".format(KEY[:31]),
        "{}.json".format(KEY + "0"),
        "{}.json".format(KEY[:31] + "g"),
        ".hidden",
        "{}".format(KEY),
      ):
        (directory / name).write_text("{}")

      self.assertEqual([], service.scan_pending_keys().keys)

  def test_subdirectories_are_never_notes(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      directory = service.ensure_root()
      (directory / "{}.json".format(KEY)).mkdir()
      (directory / "nested").mkdir()

      ##
      ## A directory named like a note may be reported - deciding what a name
      ## *is* belongs to ``load``, which refuses a non-regular file - but a
      ## plainly-named subdirectory is not a candidate at all.
      ##
      self.assertNotIn("nested", service.scan_pending_keys().keys)

  def test_nothing_unknown_is_removed_renamed_or_quarantined(self):
    ##
    ## Phase 11C has no quarantine. A scanner that tidied up would need its own
    ## atomic publication and its own recovery semantics.
    ##
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      directory = service.ensure_root()
      names = (
        "README",
        "foo.json",
        "{}.json.bak".format(KEY),
        ".{}.journal-abcdef01.part".format(KEY),
      )
      for name in names:
        (directory / name).write_text("{}")

      service.scan_pending_keys()

      self.assertEqual(
        sorted(names), sorted(p.name for p in directory.iterdir())
      )


class DeterministicOrderTest(unittest.TestCase):
  def test_keys_come_back_sorted(self):
    ##
    ## Not filesystem enumeration order, which is neither stable across hosts
    ## nor reproducible in a test. Two restarts against the same directory must
    ## replay in the same order.
    ##
    keys = sorted(
      "{:032x}".format(value) for value in (0x9, 0x1, 0xF, 0x3, 0xB)
    )
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      for key in reversed(keys):
        note(service, key)

      self.assertEqual(keys, service.scan_pending_keys().keys)


class AbsentDirectoryTest(unittest.TestCase):
  """A server that never recorded has nothing to reconcile."""

  def test_an_absent_journal_directory_scans_empty(self):
    with tempfile.TemporaryDirectory() as root:
      self.assertEqual([], journal(root).scan_pending_keys().keys)

  def test_scanning_never_creates_the_journal_directory(self):
    ##
    ## The reason this matters: reconciliation runs on every startup, so a
    ## scanner that called ``ensure_root`` would make a directory appear under
    ## every deployment that has never recorded anything - including read-only
    ## storage, where it would fail the startup instead.
    ##
    with tempfile.TemporaryDirectory() as root:
      journal(root).scan_pending_keys()

      self.assertFalse((Path(root) / JOURNAL_DIRECTORY_NAME).exists())
      self.assertEqual([], sorted(p.name for p in Path(root).iterdir()))

  def test_an_absent_storage_root_scans_empty(self):
    with tempfile.TemporaryDirectory() as root:
      missing = Path(root) / "not-created-yet"

      self.assertEqual([], journal(missing).scan_pending_keys().keys)


class JournalRootTrustBoundaryTest(unittest.TestCase):
  """The directory being enumerated is now an input, so it is checked."""

  @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "requires O_NOFOLLOW")
  def test_a_symlinked_journal_directory_is_refused(self):
    ##
    ## The link points at a directory holding a perfectly well-named note. If
    ## the link were followed the scan would succeed and this test would pass
    ## for the wrong reason, so the target is deliberately valid.
    ##
    with tempfile.TemporaryDirectory() as root:
      elsewhere = Path(root) / "elsewhere"
      elsewhere.mkdir()
      (elsewhere / "{}.json".format(KEY)).write_text("{}")
      (Path(root) / JOURNAL_DIRECTORY_NAME).symlink_to(elsewhere)

      with self.assertRaises(RecordingJournalUnavailable):
        journal(root).scan_pending_keys()

  def test_a_journal_root_that_is_a_file_is_refused(self):
    with tempfile.TemporaryDirectory() as root:
      (Path(root) / JOURNAL_DIRECTORY_NAME).write_text("not a directory")

      with self.assertRaises(RecordingJournalUnavailable):
        journal(root).scan_pending_keys()

  def test_an_unconfigured_storage_root_is_refused(self):
    service = RecordingRecoveryJournal(config_loader=lambda: {"download": {}})

    with self.assertRaises(RecordingJournalUnavailable):
      service.scan_pending_keys()


class ScanLimitTest(unittest.TestCase):
  """One startup does a bounded amount of work."""

  def test_the_bound_is_a_thousand(self):
    self.assertEqual(1000, MAX_RECOVERY_JOURNALS_PER_RUN)

  def test_a_scan_within_the_bound_is_not_truncated(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      for value in range(3):
        note(service, "{:032x}".format(value))

      result = service.scan_pending_keys(limit=3)
      self.assertEqual(3, len(result.keys))
      self.assertFalse(result.truncated)

  def test_a_scan_beyond_the_bound_is_truncated_at_the_limit(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      for value in range(5):
        note(service, "{:032x}".format(value))

      result = service.scan_pending_keys(limit=3)

      self.assertEqual(3, len(result.keys))
      self.assertTrue(result.truncated)
      ##
      ## Which three a truncated scan happens to reach is enumeration order and
      ## nothing this may promise. What it replays them *in* is promised: a
      ## sorted run, so the same directory drains the same way twice.
      ##
      self.assertEqual(sorted(result.keys), result.keys)
      self.assertTrue(
        set(result.keys)
        <= {"{:032x}".format(value) for value in range(5)}
      )

  def test_the_remainder_is_left_in_place(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      directory = service.ensure_root()
      for value in range(5):
        note(service, "{:032x}".format(value))

      service.scan_pending_keys(limit=2)

      self.assertEqual(5, len(list(directory.iterdir())))


class LoadRootHardeningTest(unittest.TestCase):
  """``load`` must not reach its note through a link either."""

  @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "requires O_NOFOLLOW")
  def test_loading_refuses_a_symlinked_journal_directory(self):
    ##
    ## Phase 11B checked the final ``<key>.json`` with O_NOFOLLOW but reached
    ## it by path, so the intermediate journal directory was still followed.
    ## Once a scanner consumes this directory that is a way to have a replay
    ## read notes somebody else chose.
    ##
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      elsewhere = Path(root) / "elsewhere"
      elsewhere.mkdir()
      real = journal(elsewhere)
      real.ensure_root()
      import json

      from backend.src.service.recording_recovery_journal import payload_for
      from backend.src.unit_test.test_recording_recovery_journal_load import (
        intent,
      )

      (real.root() / "{}.json".format(KEY)).write_text(
        json.dumps(payload_for(intent(), KEY)), encoding="utf-8"
      )
      (Path(root) / JOURNAL_DIRECTORY_NAME).symlink_to(real.root())

      with self.assertRaises(RecordingJournalUnavailable):
        service.load(KEY)

  @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "requires O_NOFOLLOW")
  def test_acknowledging_refuses_a_symlinked_journal_directory(self):
    ##
    ## Worse than reading: this one deletes. A followed link would let a note
    ## outside the storage root be removed by a replay that never wrote it.
    ##
    with tempfile.TemporaryDirectory() as root:
      elsewhere = Path(root) / "elsewhere"
      elsewhere.mkdir()
      victim = elsewhere / "{}.json".format(KEY)
      victim.write_text("{}")
      (Path(root) / JOURNAL_DIRECTORY_NAME).symlink_to(elsewhere)

      with self.assertRaises(RecordingJournalUnavailable):
        journal(root).acknowledge(KEY)

      self.assertTrue(victim.exists())

  def test_loading_from_an_absent_journal_directory_is_absent(self):
    with tempfile.TemporaryDirectory() as root:
      self.assertIsNone(journal(root).load(KEY))

  def test_acknowledging_in_an_absent_journal_directory_is_success(self):
    with tempfile.TemporaryDirectory() as root:
      journal(root).acknowledge(KEY)

      self.assertFalse((Path(root) / JOURNAL_DIRECTORY_NAME).exists())


if __name__ == "__main__":
  unittest.main()
