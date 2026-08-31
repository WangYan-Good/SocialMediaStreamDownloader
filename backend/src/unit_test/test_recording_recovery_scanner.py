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
import multiprocessing
import tempfile
import unittest
from unittest import mock

from backend.src.service import recording_recovery_journal as journal_module

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


def _scan_with_cursor_in_child(root, connection):
  try:
    connection.send((journal(root).scan_pending_keys(limit=1).keys, None))
  except BaseException as error:
    connection.send((None, type(error).__name__))
  finally:
    connection.close()


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

      self.assertEqual(
        {"{:032x}.json".format(value) for value in range(5)},
        {p.name for p in directory.iterdir() if p.name.endswith(".json")},
      )


class _SyntheticEntry:
  def __init__(self, name):
    self.name = name


class _BoundedScandir:
  """A scandir double that fails if the scanner asks past overflow proof."""

  def __init__(self, allowed):
    self.allowed = allowed
    self.observed = 0

  def __enter__(self):
    return self

  def __exit__(self, *unused):
    return False

  def __iter__(self):
    return self

  def __next__(self):
    self.observed += 1
    if self.observed > self.allowed:
      raise AssertionError("scanner requested an entry after overflow proof")
    return _SyntheticEntry("ignored-{:05d}".format(self.observed))


class TotalDirectoryEntryBoundTest(unittest.TestCase):
  """The startup bound applies to directory work, not only valid notes."""

  def test_the_total_entry_bound_is_4096(self):
    self.assertEqual(
      4096, getattr(journal_module, "MAX_RECOVERY_SCAN_ENTRIES", None)
    )

  def test_ignored_entries_trigger_explicit_overflow_at_bound_plus_one(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      service.ensure_root()
      entries = _BoundedScandir(4097)

      with mock.patch.object(os, "scandir", return_value=entries):
        with self.assertRaises(RuntimeError) as raised:
          service.scan_pending_keys()

      self.assertEqual("RecordingJournalScanOverflow", type(raised.exception).__name__)
      self.assertEqual(4097, entries.observed)

  def test_scan_never_requests_an_entry_after_overflow_is_known(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      service.ensure_root()
      entries = _BoundedScandir(4097)

      with mock.patch.object(os, "scandir", return_value=entries):
        with self.assertRaises(RuntimeError):
          service.scan_pending_keys()

      self.assertEqual(4097, entries.observed)

  def test_real_unknown_entries_count_and_remain_untouched(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      directory = service.ensure_root()
      names = (
        "README",
        ".{}.journal-deadbeef.part".format(KEY),
        ".scan-cursor",
        "{}.json".format(KEY),
      )
      for name in names:
        (directory / name).write_text("ignored", encoding="utf-8")

      with mock.patch.object(
        journal_module, "MAX_RECOVERY_SCAN_ENTRIES", 3, create=True
      ):
        with self.assertRaises(RuntimeError) as raised:
          service.scan_pending_keys()

      self.assertEqual("RecordingJournalScanOverflow", type(raised.exception).__name__)
      self.assertEqual(sorted(names), sorted(p.name for p in directory.iterdir()))

  def test_overflow_never_attempts_cursor_persistence(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      directory = service.ensure_root()
      for name in ("README", "backup", ".part", "{}.json".format(KEY)):
        (directory / name).write_text("ignored", encoding="utf-8")

      with mock.patch.object(journal_module, "MAX_RECOVERY_SCAN_ENTRIES", 3), \
           mock.patch.object(
             service,
             "_persist_scan_cursor",
             wraps=service._persist_scan_cursor,
           ) as persist:
        with self.assertRaises(RuntimeError):
          service.scan_pending_keys()

      persist.assert_not_called()

  def test_a_missing_cursor_reserves_capacity_before_replay(self):
    """Advisory metadata must not turn an accepted directory into overflow."""
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      keys = ["{:032x}".format(value) for value in range(1, 4)]
      for key in keys:
        note(service, key)

      with mock.patch.object(journal_module, "MAX_RECOVERY_SCAN_ENTRIES", 3):
        with self.assertRaises(RuntimeError) as raised:
          service.scan_pending_keys(limit=1)

      self.assertEqual("RecordingJournalScanOverflow", type(raised.exception).__name__)
      self.assertFalse((service.root() / ".scan-cursor").exists())

  def test_an_existing_cursor_consumes_its_entry_inside_the_bound(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      keys = ["{:032x}".format(value) for value in range(1, 3)]
      for key in keys:
        note(service, key)
      (service.root() / ".scan-cursor").write_text(keys[-1] + "\n")

      with mock.patch.object(journal_module, "MAX_RECOVERY_SCAN_ENTRIES", 3):
        first = service.scan_pending_keys(limit=1)
        second = service.scan_pending_keys(limit=1)

      self.assertEqual([keys[0]], first.keys)
      self.assertEqual([keys[1]], second.keys)


class AdvisoryCursorFairnessTest(unittest.TestCase):
  """Retained notes rotate through a bounded deterministic batch."""

  def keys(self, count):
    return ["{:032x}".format(value) for value in range(1, count + 1)]

  def test_cursor_name_format_and_size_are_closed(self):
    self.assertEqual(".scan-cursor", getattr(journal_module, "SCAN_CURSOR_NAME", None))
    self.assertEqual(64, getattr(journal_module, "SCAN_CURSOR_MAX_BYTES", None))

  def test_retained_prefix_does_not_monopolize_restarts(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      keys = self.keys(5)
      for key in keys:
        note(service, key)

      first = service.scan_pending_keys(limit=2)
      second = service.scan_pending_keys(limit=2)
      third = service.scan_pending_keys(limit=2)

      self.assertEqual(keys[:2], first.keys)
      self.assertEqual(keys[2:4], second.keys)
      self.assertEqual([keys[4], keys[0]], third.keys)
      self.assertTrue(first.truncated)
      self.assertEqual(keys[0] + "\n", (service.root() / ".scan-cursor").read_text())

  def test_every_key_is_selected_within_ceiling_n_over_limit_starts(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      keys = self.keys(7)
      for key in keys:
        note(service, key)

      selected = []
      for _ in range(3):
        selected.extend(service.scan_pending_keys(limit=3).keys)

      self.assertEqual(set(keys), set(selected))
      self.assertEqual(9, len(selected))

  def test_a_cursor_pointing_to_a_deleted_key_starts_after_that_key(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      keys = self.keys(4)
      for key in (keys[0], keys[2], keys[3]):
        note(service, key)
      (service.root() / ".scan-cursor").write_text(keys[1] + "\n")

      self.assertEqual(keys[2:4], service.scan_pending_keys(limit=2).keys)

  def test_missing_cursor_starts_at_the_beginning(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      keys = self.keys(3)
      for key in keys:
        note(service, key)

      self.assertEqual(keys[:2], service.scan_pending_keys(limit=2).keys)

  def test_empty_scan_does_not_create_a_cursor_or_directory(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)

      self.assertEqual([], service.scan_pending_keys(limit=2).keys)
      self.assertFalse(service.root().exists())

  def test_corrupt_cursor_fails_open_to_the_beginning(self):
    for raw in ("garbage", "A" * 32, "0" * 65, "0" * 31):
      with self.subTest(raw=raw[:12]):
        with tempfile.TemporaryDirectory() as root:
          service = journal(root)
          keys = self.keys(3)
          for key in keys:
            note(service, key)
          (service.root() / ".scan-cursor").write_text(raw, encoding="ascii")

          self.assertEqual(keys[0], service.scan_pending_keys(limit=1).keys[0])

  @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "requires O_NOFOLLOW")
  def test_cursor_symlink_is_not_followed(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      keys = self.keys(3)
      for key in keys:
        note(service, key)
      external = Path(root) / "external-cursor"
      external.write_text(keys[0] + "\n", encoding="ascii")
      (service.root() / ".scan-cursor").symlink_to(external)

      selected = service.scan_pending_keys(limit=1)

      self.assertEqual([keys[0]], selected.keys)
      self.assertEqual(keys[0] + "\n", external.read_text(encoding="ascii"))

  @unittest.skipUnless(hasattr(os, "mkfifo"), "requires named pipes")
  def test_nonregular_cursor_fails_open_without_blocking(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      key = self.keys(1)[0]
      note(service, key)
      os.mkfifo(service.root() / ".scan-cursor")

      context = multiprocessing.get_context("fork")
      parent, child = context.Pipe(duplex=False)
      process = context.Process(
        target=_scan_with_cursor_in_child,
        args=(root, child),
      )
      process.start()
      child.close()
      process.join(timeout=1.0)
      hung = process.is_alive()
      if hung:
        process.terminate()
        process.join(timeout=5.0)

      self.assertFalse(hung, "reading a writerless cursor FIFO blocked startup")
      self.assertTrue(parent.poll(0.5))
      keys, error_name = parent.recv()
      parent.close()
      self.assertIsNone(error_name)
      self.assertEqual([key], keys)

  def test_cursor_write_failure_does_not_block_selection(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      keys = self.keys(3)
      for key in keys:
        note(service, key)

      with mock.patch.object(
        service,
        "_persist_scan_cursor",
        side_effect=OSError("cursor storage unavailable"),
      ):
        selected = service.scan_pending_keys(limit=2)

      self.assertEqual(keys[:2], selected.keys)

  def test_missing_directory_relative_rename_is_advisory(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      keys = self.keys(2)
      for key in keys:
        note(service, key)

      with mock.patch.object(
        journal_module, "_SUPPORTS_DIRECTORY_RELATIVE_RENAME", False,
        create=True,
      ):
        selected = service.scan_pending_keys(limit=1)

      self.assertEqual([keys[0]], selected.keys)
      self.assertFalse((service.root() / ".scan-cursor").exists())

  def test_cursor_write_close_failure_is_advisory_and_cleans_temporary(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      key = self.keys(1)[0]
      note(service, key)
      real_open = os.open
      real_close = os.close
      cursor_descriptor = []
      close_calls = []

      def track_cursor_open(path, flags, *args, **kwargs):
        descriptor = real_open(path, flags, *args, **kwargs)
        if str(path).startswith(".scan-cursor-"):
          cursor_descriptor.append(descriptor)
        return descriptor

      def fail_cursor_close(descriptor):
        if cursor_descriptor == [descriptor]:
          close_calls.append(descriptor)
          real_close(descriptor)
          if len(close_calls) == 1:
            raise OSError("cursor write close failed")
          return
        real_close(descriptor)

      with mock.patch.object(os, "open", track_cursor_open), \
           mock.patch.object(os, "close", fail_cursor_close):
        selected = service.scan_pending_keys(limit=1)

      self.assertEqual([key], selected.keys)
      self.assertEqual(1, len(close_calls))
      self.assertEqual(
        [],
        [path.name for path in service.root().iterdir() if path.name.endswith(".part")],
      )
      self.assertFalse((service.root() / ".scan-cursor").exists())

  def test_cursor_write_and_cleanup_close_failure_still_unlinks_temporary(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      key = self.keys(1)[0]
      note(service, key)
      real_open = os.open
      real_close = os.close
      cursor_descriptor = []

      def track_cursor_open(path, flags, *args, **kwargs):
        descriptor = real_open(path, flags, *args, **kwargs)
        if str(path).startswith(".scan-cursor-"):
          cursor_descriptor.append(descriptor)
        return descriptor

      def fail_cursor_close(descriptor):
        real_close(descriptor)
        if cursor_descriptor == [descriptor]:
          raise OSError("cursor cleanup close failed")

      with mock.patch.object(os, "open", track_cursor_open), \
           mock.patch.object(os, "close", fail_cursor_close), \
           mock.patch.object(
             service,
             "_write_all",
             side_effect=OSError("cursor write failed"),
           ):
        selected = service.scan_pending_keys(limit=1)

      self.assertEqual([key], selected.keys)
      self.assertEqual(
        [],
        [path.name for path in service.root().iterdir() if path.name.endswith(".part")],
      )

  def test_cursor_descriptor_close_failure_is_advisory(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      keys = self.keys(2)
      for key in keys:
        note(service, key)
      (service.root() / ".scan-cursor").write_text(
        keys[0] + "\n", encoding="ascii"
      )

      real_open = os.open
      real_close = os.close
      cursor_descriptor = []
      failed = []

      def track_cursor_open(path, flags, *args, **kwargs):
        descriptor = real_open(path, flags, *args, **kwargs)
        if (
          path == ".scan-cursor"
          and flags & os.O_ACCMODE == os.O_RDONLY
          and not cursor_descriptor
        ):
          cursor_descriptor.append(descriptor)
        return descriptor

      def fail_cursor_close(descriptor):
        real_close(descriptor)
        if cursor_descriptor == [descriptor] and not failed:
          failed.append(True)
          raise OSError("cursor close failed")

      with mock.patch.object(os, "open", track_cursor_open), \
           mock.patch.object(os, "close", fail_cursor_close):
        selected = service.scan_pending_keys(limit=1)

      self.assertEqual([True], failed)
      self.assertEqual([keys[0]], selected.keys)

  def test_persisted_cursor_is_private_and_bounded(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      note(service, self.keys(1)[0])

      service.scan_pending_keys(limit=1)

      cursor = service.root() / ".scan-cursor"
      self.assertEqual(0o600, cursor.stat().st_mode & 0o777)
      self.assertLessEqual(cursor.stat().st_size, 64)


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
