##
## The crash P2-03 leaves behind, and what may be said about it.
##
## The recording pipeline makes media durable *before* it publishes the recovery
## note that would let a restart catalogue it. Between those two moments the
## bytes are on disk and nothing - no database row, no note - knows they exist.
## A process that dies there leaves a file the library can never see and no
## restart will ever recover, because the reconciler replays notes and is
## forbidden from scanning media.
##
## This is the detector for exactly that state, and almost all of it is about
## what it must refuse to say. Calling a file an orphan is the first half of a
## sentence whose second half is "so move it", and a wrong answer moves media a
## real recording still points at. So a candidate has to survive every check
## below, and the checks are deliberately conjunctive: the file is inside the
## configured recording root, is a plain regular file of a type this project
## actually records, is not a temporary, and is claimed by neither the database
## nor a pending note.
##
## What is not here, on purpose: any attempt to work out who a file belongs to.
## Nothing on disk carries an ``app_user_id``. A directory name comes from a
## broadcaster's nickname and several accounts may record the same broadcaster,
## a filename is a stream name, a timestamp is a time. Guessing from any of them
## attaches somebody's recording to somebody else's account, which is worse than
## leaving it where it is.
##
from datetime import datetime
import os
from pathlib import Path
import stat
import tempfile
import unittest

from backend.src.service.recording_recovery_journal import (
  JOURNAL_DIRECTORY_NAME,
  RecordingRecoveryJournal,
)
from backend.src.service.recording_resource import RecordingPersistenceIntent


def settings_for(root):
  return {
    "download": {"save_path": str(root)},
    "platform": {"douyin": {"download": {"type": "live"}}},
  }


def key(digit):
  return (str(digit) * 32)[:32]


class FakeReferences:
  """What the database currently claims, or why it cannot be asked."""

  def __init__(self, paths=(), error=None):
    self.paths = list(paths)
    self.error = error
    self.calls = 0

  def referenced_output_paths(self):
    self.calls += 1
    if self.error is not None:
      raise self.error
    return list(self.paths)


class OrphanTestCase(unittest.TestCase):
  def setUp(self):
    self._temporary = tempfile.TemporaryDirectory()
    self.root = Path(self._temporary.name)
    self.media_root = self.root / "douyin" / "live"
    self.media_root.mkdir(parents=True)
    self.settings = settings_for(self.root)
    self.journal = RecordingRecoveryJournal(config_loader=lambda: self.settings)
    self.addCleanup(self._temporary.cleanup)

  def inventory(self, references=None, journal=None):
    from backend.src.service.recording_orphan import RecordingOrphanInventory

    return RecordingOrphanInventory(
      journal=self.journal if journal is None else journal,
      references=FakeReferences() if references is None else references,
      config_loader=lambda: self.settings,
    )

  def recording(self, name, owner="broadcaster", content=b"media-bytes"):
    directory = self.media_root / owner
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_bytes(content)
    return path

  def publish_note(self, output_path, recovery_key):
    intent = RecordingPersistenceIntent(
      app_user_id=1,
      platform="douyin",
      room_id="7700",
      owner_user_id="9001",
      title="a broadcast",
      protocol="flv",
      output_path=str(output_path),
      started_at=datetime(2026, 9, 3, 12, 0, 0),
      finished_at=datetime(2026, 9, 3, 13, 0, 0),
      source="live",
    )
    self.journal.publish(intent, recovery_key)

  def relative_paths(self, scan):
    return sorted(candidate.relative_path for candidate in scan.candidates)


class OrphanAuthorityTest(OrphanTestCase):
  def test_a_recording_the_database_references_is_never_an_orphan(self):
    recorded = self.recording("kept.flv")

    scan = self.inventory(
      references=FakeReferences(paths=[str(recorded)])
    ).scan()

    self.assertEqual([], self.relative_paths(scan))

  def test_a_reference_spelled_relative_to_the_root_still_protects_the_file(self):
    recorded = self.recording("kept.flv")
    relative = recorded.relative_to(self.root)

    scan = self.inventory(references=FakeReferences(paths=[str(relative)])).scan()

    self.assertEqual([], self.relative_paths(scan))

  def test_media_a_pending_note_describes_is_never_an_orphan(self):
    pending = self.recording("pending.flv")
    self.publish_note(pending, key(1))

    scan = self.inventory().scan()

    self.assertEqual([], self.relative_paths(scan))

  def test_durable_media_nothing_claims_is_inventoried(self):
    orphan = self.recording("orphan.flv")

    scan = self.inventory().scan()

    self.assertEqual(
      [str(orphan.relative_to(self.root))], self.relative_paths(scan)
    )

  def test_every_recorded_media_type_can_be_inventoried(self):
    for name in ("capture.flv", "capture.ts", "capture.mp4"):
      self.recording(name)

    scan = self.inventory().scan()

    self.assertEqual(3, len(scan.candidates))

  def test_a_candidate_carries_the_identity_a_later_action_must_recheck(self):
    orphan = self.recording("orphan.flv")
    info = os.stat(orphan)

    candidate = self.inventory().scan().candidates[0]

    self.assertEqual(info.st_dev, candidate.device)
    self.assertEqual(info.st_ino, candidate.inode)
    self.assertEqual(info.st_size, candidate.size)
    self.assertEqual(info.st_mtime_ns, candidate.mtime_ns)

  def test_no_candidate_ever_carries_an_owner(self):
    self.recording("orphan.flv", owner="9001")

    candidate = self.inventory().scan().candidates[0]

    for forbidden in ("app_user_id", "owner_user_id", "owner", "user_id"):
      self.assertFalse(
        hasattr(candidate, forbidden),
        "a candidate must not carry {}".format(forbidden),
      )


class OrphanFilesystemRefusalTest(OrphanTestCase):
  def test_a_symlink_is_never_a_candidate(self):
    outside = self.root / "elsewhere.flv"
    outside.write_bytes(b"not a recording")
    link = self.media_root / "broadcaster"
    link.mkdir(parents=True)
    os.symlink(outside, link / "linked.flv")

    scan = self.inventory().scan()

    self.assertEqual([], self.relative_paths(scan))

  def test_a_symlinked_directory_is_not_descended_into(self):
    hidden = self.root / "hidden"
    hidden.mkdir()
    (hidden / "reachable.flv").write_bytes(b"media")
    os.symlink(hidden, self.media_root / "broadcaster")

    scan = self.inventory().scan()

    self.assertEqual([], self.relative_paths(scan))

  def test_a_fifo_is_never_a_candidate(self):
    directory = self.media_root / "broadcaster"
    directory.mkdir()
    os.mkfifo(directory / "stream.flv")

    scan = self.inventory().scan()

    self.assertEqual([], self.relative_paths(scan))

  def test_an_in_flight_remux_temporary_is_never_a_candidate(self):
    directory = self.media_root / "broadcaster"
    directory.mkdir()
    (directory / ".capture.remux-abcdef.part.mp4").write_bytes(b"partial")
    (directory / "capture.part.mp4").write_bytes(b"partial")

    scan = self.inventory().scan()

    self.assertEqual([], self.relative_paths(scan))

  def test_a_reserved_but_empty_capture_is_never_a_candidate(self):
    directory = self.media_root / "broadcaster"
    directory.mkdir()
    (directory / "reserved.ts").touch()

    scan = self.inventory().scan()

    self.assertEqual([], self.relative_paths(scan))

  def test_the_recovery_journal_directory_is_never_scanned(self):
    self.publish_note(self.recording("pending.flv"), key(2))
    ##
    ## Planted so a scanner that walked the journal directory would have
    ## something to find there.
    ##
    (self.root / JOURNAL_DIRECTORY_NAME / "decoy.flv").write_bytes(b"decoy")

    scan = self.inventory().scan()

    self.assertEqual([], self.relative_paths(scan))

  def test_media_outside_the_recording_root_is_never_a_candidate(self):
    (self.root / "loose.flv").write_bytes(b"media")
    (self.root / "douyin").mkdir(exist_ok=True)
    (self.root / "douyin" / "aweme").mkdir(parents=True)
    (self.root / "douyin" / "aweme" / "post.mp4").write_bytes(b"a download")

    scan = self.inventory().scan()

    self.assertEqual([], self.relative_paths(scan))

  def test_a_file_that_is_not_recorded_media_is_never_a_candidate(self):
    directory = self.media_root / "response"
    directory.mkdir()
    (directory / "snapshot.yml").write_bytes(b"external: info")

    scan = self.inventory().scan()

    self.assertEqual([], self.relative_paths(scan))


class OrphanBoundedScanTest(OrphanTestCase):
  def test_the_scan_stops_at_its_entry_bound_rather_than_walking_forever(self):
    from backend.src.service import recording_orphan
    from backend.src.service.recording_orphan import OrphanScanOverflow

    directory = self.media_root / "broadcaster"
    directory.mkdir()
    for index in range(12):
      (directory / "file-{:05d}.flv".format(index)).write_bytes(b"m")

    ##
    ## The bound is lowered rather than materialised. What has to be proved is
    ## that the walk refuses once it exceeds whatever bound is configured;
    ## creating two hundred thousand files would prove the same thing and turn
    ## this suite into a filesystem benchmark.
    ##
    original = recording_orphan.MAX_ORPHAN_SCAN_ENTRIES
    recording_orphan.MAX_ORPHAN_SCAN_ENTRIES = 4
    try:
      with self.assertRaises(OrphanScanOverflow):
        self.inventory().scan()
    finally:
      recording_orphan.MAX_ORPHAN_SCAN_ENTRIES = original

    ##
    ## And that the same tree is fine under the shipped bound, so the refusal
    ## above is the bound working rather than the walk being broken.
    ##
    self.assertEqual(12, len(self.inventory().scan().candidates))

  def test_the_shipped_entry_bound_fits_a_real_media_library(self):
    from backend.src.service.recording_orphan import MAX_ORPHAN_SCAN_ENTRIES

    ##
    ## A bound a genuine library exceeds would make this command refuse to run
    ## for exactly the deployments that need it. The recovery journal's own
    ## 4096 is right for a directory of pending notes and wrong for a media
    ## tree, so the two are deliberately not the same number.
    ##
    self.assertGreaterEqual(MAX_ORPHAN_SCAN_ENTRIES, 100000)

  def test_the_scan_stops_at_its_depth_bound(self):
    from backend.src.service.recording_orphan import MAX_ORPHAN_SCAN_DEPTH

    directory = self.media_root
    for level in range(MAX_ORPHAN_SCAN_DEPTH + 2):
      directory = directory / "level{}".format(level)
    directory.mkdir(parents=True)
    (directory / "deep.flv").write_bytes(b"media")

    scan = self.inventory().scan()

    self.assertEqual([], self.relative_paths(scan))

  def test_a_truncated_scan_says_so_rather_than_pretending_to_be_complete(self):
    for index in range(5):
      self.recording("orphan-{}.flv".format(index))

    scan = self.inventory().scan(limit=2)

    self.assertEqual(2, len(scan.candidates))
    self.assertTrue(scan.truncated)

  def test_continuation_is_deterministic_and_never_starves_a_candidate(self):
    for index in range(5):
      self.recording("orphan-{}.flv".format(index))

    seen = []
    cursor = None
    for unused in range(5):
      scan = self.inventory().scan(limit=2, after=cursor)
      if not scan.candidates:
        break
      seen.extend(candidate.relative_path for candidate in scan.candidates)
      cursor = scan.candidates[-1].relative_path

    self.assertEqual(sorted(seen), seen, "continuation must be ordered")
    self.assertEqual(5, len(set(seen)), "every candidate must eventually appear")

  def test_two_scans_of_an_unchanged_tree_report_the_same_order(self):
    for index in range(4):
      self.recording("orphan-{}.flv".format(index))

    first = self.relative_paths(self.inventory().scan())
    second = self.relative_paths(self.inventory().scan())

    self.assertEqual(first, second)


class OrphanFailClosedTest(OrphanTestCase):
  def test_an_unreachable_database_refuses_to_name_anything_an_orphan(self):
    from backend.src.service.recording_orphan import OrphanInventoryUnavailable

    self.recording("orphan.flv")
    references = FakeReferences(error=RuntimeError("database is down"))

    with self.assertRaises(OrphanInventoryUnavailable):
      self.inventory(references=references).scan()

  def test_an_unreadable_journal_refuses_to_name_anything_an_orphan(self):
    from backend.src.service.recording_orphan import OrphanInventoryUnavailable

    self.recording("orphan.flv")

    class BrokenJournal:
      def pending_keys_snapshot(self):
        raise RuntimeError("journal directory is unusable")

    with self.assertRaises(OrphanInventoryUnavailable):
      self.inventory(journal=BrokenJournal()).scan()

  def test_a_note_that_cannot_be_read_refuses_to_name_anything_an_orphan(self):
    from backend.src.service.recording_orphan import OrphanInventoryUnavailable

    self.recording("orphan.flv")
    self.publish_note(self.recording("pending.flv"), key(3))
    ##
    ## Corrupted after publication: the note exists, so a file it might name
    ## cannot be ruled out, and this build cannot read what it says.
    ##
    note = self.root / JOURNAL_DIRECTORY_NAME / "{}.json".format(key(3))
    note.write_bytes(b"{not json")

    with self.assertRaises(OrphanInventoryUnavailable):
      self.inventory().scan()

  def test_an_unconfigured_storage_root_refuses_rather_than_guessing(self):
    from backend.src.service.recording_orphan import (
      OrphanInventoryUnavailable,
      RecordingOrphanInventory,
    )

    inventory = RecordingOrphanInventory(
      journal=self.journal,
      references=FakeReferences(),
      config_loader=lambda: {"download": {}, "platform": {}},
    )

    with self.assertRaises(OrphanInventoryUnavailable):
      inventory.scan()

  def test_a_missing_recording_root_is_an_empty_inventory_not_a_failure(self):
    import shutil

    shutil.rmtree(self.media_root)

    scan = self.inventory().scan()

    self.assertEqual([], self.relative_paths(scan))


class OrphanExposureTest(OrphanTestCase):
  def test_a_candidate_is_described_only_by_its_root_relative_path(self):
    orphan = self.recording("orphan.flv")

    candidate = self.inventory().scan().candidates[0]

    self.assertFalse(Path(candidate.relative_path).is_absolute())
    self.assertNotIn(str(self.root), candidate.relative_path)
    self.assertEqual(
      str(orphan.relative_to(self.root)), candidate.relative_path
    )


if __name__ == "__main__":
  unittest.main()
