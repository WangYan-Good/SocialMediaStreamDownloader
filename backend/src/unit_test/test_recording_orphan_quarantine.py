##
## Moving media out of the library, and every reason not to.
##
## Quarantine is the only destructive thing P18 adds, so it is deliberately the
## narrowest: an operator names one file, and that file is hard-linked into a
## hidden directory and unlinked from where it was. It never deletes, never
## writes a database row, never invents an owner, and never runs on its own -
## no startup path, no request path, no periodic job reaches it.
##
## The distance between "was an orphan a moment ago" and "is being moved now" is
## where this could go wrong, so everything the inventory proved is proved
## again here, against the descriptor actually being moved rather than against
## a path that could since have come to mean something else.
##
## The move is a hard link followed by an unlink rather than a rename, for the
## same reason the recovery journal and the remux publisher chose one:
## ``os.rename`` silently destroys whatever already holds the destination name.
## ``os.link`` refuses. A cross-device link fails outright rather than quietly
## degrading into copy-and-delete, which would be a second copy of somebody's
## recording written somewhere nobody asked for.
##
from datetime import datetime
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest

from backend.src.service.recording_recovery_journal import (
  RecordingRecoveryJournal,
)
from backend.src.service.recording_resource import RecordingPersistenceIntent

from backend.src.unit_test.test_recording_orphan_inventory import (
  FakeReferences,
  key,
  settings_for,
)


class QuarantineTestCase(unittest.TestCase):
  def setUp(self):
    self._temporary = tempfile.TemporaryDirectory()
    self.root = Path(self._temporary.name)
    self.media_root = self.root / "douyin" / "live"
    self.media_root.mkdir(parents=True)
    self.settings = settings_for(self.root)
    self.journal = RecordingRecoveryJournal(config_loader=lambda: self.settings)
    self.references = FakeReferences()
    self.addCleanup(self._temporary.cleanup)

  def inventory(self, references=None, journal=None):
    from backend.src.service.recording_orphan import RecordingOrphanInventory

    return RecordingOrphanInventory(
      journal=self.journal if journal is None else journal,
      references=self.references if references is None else references,
      config_loader=lambda: self.settings,
    )

  def orphan(self, name="orphan.flv", content=b"a whole broadcast"):
    directory = self.media_root / "broadcaster"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_bytes(content)
    return path

  def quarantine_root(self):
    from backend.src.service.recording_orphan import QUARANTINE_DIRECTORY_NAME

    return self.root / QUARANTINE_DIRECTORY_NAME

  def only_candidate(self, inventory=None):
    scan = (inventory or self.inventory()).scan()
    self.assertEqual(1, len(scan.candidates), "expected exactly one candidate")
    return scan.candidates[0]

  def quarantined_media(self):
    return sorted(
      path for path in self.quarantine_root().iterdir()
      if path.suffix != ".json"
    )


class QuarantineTransitionTest(QuarantineTestCase):
  def test_the_source_disappears_and_the_destination_holds_the_same_file(self):
    source = self.orphan()
    before = os.stat(source)
    inventory = self.inventory()

    outcome = inventory.quarantine(self.only_candidate(inventory))

    self.assertFalse(source.exists(), "the source must not survive")
    moved = self.quarantined_media()
    self.assertEqual(1, len(moved))
    after = os.stat(moved[0])
    ##
    ## Same inode, so this is the file that was there - not a copy of it, and
    ## not a truncated re-write.
    ##
    self.assertEqual(before.st_ino, after.st_ino)
    self.assertEqual(before.st_size, after.st_size)
    self.assertEqual(b"a whole broadcast", moved[0].read_bytes())
    self.assertTrue(outcome.quarantined)

  def test_the_quarantine_directory_is_hidden_and_not_world_readable(self):
    inventory = self.inventory()
    self.orphan()

    inventory.quarantine(self.only_candidate(inventory))

    root = self.quarantine_root()
    self.assertTrue(root.name.startswith("."), "quarantine must be hidden")
    mode = stat.S_IMODE(os.lstat(root).st_mode)
    self.assertEqual(0, mode & 0o077, "quarantine must not be group/world readable")

  def test_the_record_beside_it_is_owner_only_and_names_no_absolute_path(self):
    inventory = self.inventory()
    source = self.orphan()
    relative = str(source.relative_to(self.root))

    inventory.quarantine(self.only_candidate(inventory))

    records = sorted(self.quarantine_root().glob("*.json"))
    self.assertEqual(1, len(records))
    self.assertEqual(0o600, stat.S_IMODE(os.lstat(records[0]).st_mode))
    written = json.loads(records[0].read_text(encoding="utf-8"))
    self.assertEqual(relative, written["source_relative_path"])
    self.assertNotIn(str(self.root), records[0].read_text(encoding="utf-8"))

  def test_a_quarantined_file_is_not_offered_again(self):
    inventory = self.inventory()
    self.orphan()

    inventory.quarantine(self.only_candidate(inventory))

    self.assertEqual([], self.inventory().scan().candidates)


class QuarantineRefusalTest(QuarantineTestCase):
  def test_it_refuses_when_the_database_became_unreachable(self):
    from backend.src.service.recording_orphan import OrphanQuarantineRefused

    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)

    self.references.error = RuntimeError("database is down")

    with self.assertRaises(OrphanQuarantineRefused):
      inventory.quarantine(candidate)
    self.assertTrue(source.exists(), "a refused quarantine must change nothing")

  def test_it_refuses_when_the_database_started_referencing_the_file(self):
    from backend.src.service.recording_orphan import OrphanQuarantineRefused

    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)

    ##
    ## The race this closes: a recording finishes and is catalogued between the
    ## operator reading the inventory and acting on it.
    ##
    self.references.paths = [str(source)]

    with self.assertRaises(OrphanQuarantineRefused):
      inventory.quarantine(candidate)
    self.assertTrue(source.exists())

  def test_it_refuses_when_a_note_started_describing_the_file(self):
    from backend.src.service.recording_orphan import OrphanQuarantineRefused

    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)

    self.journal.publish(
      RecordingPersistenceIntent(
        app_user_id=1,
        platform="douyin",
        room_id="7700",
        owner_user_id="9001",
        title=None,
        protocol="flv",
        output_path=str(source),
        started_at=datetime(2026, 9, 3, 12, 0, 0),
        finished_at=datetime(2026, 9, 3, 13, 0, 0),
        source="live",
      ),
      key(4),
    )

    with self.assertRaises(OrphanQuarantineRefused):
      inventory.quarantine(candidate)
    self.assertTrue(source.exists())

  def test_it_refuses_when_the_journal_became_unreadable(self):
    from backend.src.service.recording_orphan import OrphanQuarantineRefused

    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)

    class BrokenJournal:
      def pending_keys_snapshot(self):
        raise RuntimeError("journal directory is unusable")

    broken = self.inventory(journal=BrokenJournal())
    with self.assertRaises(OrphanQuarantineRefused):
      broken.quarantine(candidate)
    self.assertTrue(source.exists())

  def test_it_refuses_a_file_that_changed_after_it_was_inventoried(self):
    from backend.src.service.recording_orphan import OrphanQuarantineRefused

    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)

    source.write_bytes(b"a different, longer broadcast entirely")

    with self.assertRaises(OrphanQuarantineRefused):
      inventory.quarantine(candidate)
    self.assertTrue(source.exists())
    self.assertEqual([], list(self.quarantine_root().iterdir())
                     if self.quarantine_root().exists() else [])

  def test_it_refuses_a_file_whose_inode_was_replaced(self):
    from backend.src.service.recording_orphan import OrphanQuarantineRefused

    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)

    ##
    ## Same name, same size, same content - a different file. Only the inode
    ## says so, which is why the inode is part of what is rechecked.
    ##
    replacement = source.with_name("replacement.flv")
    replacement.write_bytes(b"a whole broadcast")
    os.replace(replacement, source)

    with self.assertRaises(OrphanQuarantineRefused):
      inventory.quarantine(candidate)
    self.assertTrue(source.exists())

  def test_it_refuses_a_file_that_became_a_symlink(self):
    from backend.src.service.recording_orphan import OrphanQuarantineRefused

    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)

    elsewhere = self.root / "elsewhere.flv"
    elsewhere.write_bytes(b"somebody else's file")
    source.unlink()
    os.symlink(elsewhere, source)

    with self.assertRaises(OrphanQuarantineRefused):
      inventory.quarantine(candidate)
    self.assertTrue(elsewhere.exists(), "the link target must be untouched")

  def test_it_refuses_a_file_that_vanished(self):
    from backend.src.service.recording_orphan import OrphanQuarantineRefused

    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)

    source.unlink()

    with self.assertRaises(OrphanQuarantineRefused):
      inventory.quarantine(candidate)

  def test_it_refuses_a_candidate_pointing_outside_the_recording_root(self):
    from backend.src.service.recording_orphan import (
      OrphanCandidate,
      OrphanQuarantineRefused,
    )

    outside = self.root.parent / "not-mine.flv"
    outside.write_bytes(b"somebody else's file")
    self.addCleanup(lambda: outside.exists() and outside.unlink())
    info = os.stat(outside)
    forged = OrphanCandidate(
      relative_path="../{}".format(outside.name),
      size=info.st_size,
      device=info.st_dev,
      inode=info.st_ino,
      mtime_ns=info.st_mtime_ns,
    )

    with self.assertRaises(OrphanQuarantineRefused):
      self.inventory().quarantine(forged)
    self.assertTrue(outside.exists())

  def test_a_collision_never_overwrites_what_quarantine_already_holds(self):
    from backend.src.service.recording_orphan import OrphanQuarantineRefused

    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)
    destination = inventory.quarantine_destination_for(candidate)
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    destination.write_bytes(b"an earlier quarantine of something else")

    with self.assertRaises(OrphanQuarantineRefused):
      inventory.quarantine(candidate)

    self.assertEqual(
      b"an earlier quarantine of something else", destination.read_bytes()
    )
    self.assertTrue(source.exists())


class QuarantineAuthorityTest(QuarantineTestCase):
  def test_quarantine_never_creates_a_recording_row(self):
    class RefusingReferences(FakeReferences):
      def __init__(self):
        super().__init__()
        self.writes = 0

      def create_recording(self, *unused, **also_unused):
        self.writes += 1
        raise AssertionError("quarantine must never write a recording")

    references = RefusingReferences()
    inventory = self.inventory(references=references)
    self.orphan()

    inventory.quarantine(self.only_candidate(inventory))

    self.assertEqual(0, references.writes)

  def test_the_written_record_carries_no_owner_of_any_kind(self):
    inventory = self.inventory()
    self.orphan()

    inventory.quarantine(self.only_candidate(inventory))

    written = json.loads(
      sorted(self.quarantine_root().glob("*.json"))[0].read_text(encoding="utf-8")
    )
    for forbidden in (
      "app_user_id", "owner_user_id", "user_id", "owner", "nickname",
      "person_id", "room_id",
    ):
      self.assertNotIn(forbidden, written)

  def test_a_scan_alone_never_moves_or_removes_anything(self):
    source = self.orphan()

    self.inventory().scan()

    self.assertTrue(source.exists())
    self.assertFalse(self.quarantine_root().exists())

  def test_quarantine_never_deletes_the_media_it_moves(self):
    inventory = self.inventory()
    self.orphan(content=b"irreplaceable")

    inventory.quarantine(self.only_candidate(inventory))

    moved = self.quarantined_media()
    self.assertEqual(1, len(moved))
    self.assertEqual(b"irreplaceable", moved[0].read_bytes())

  def test_a_dry_run_reports_what_would_happen_and_changes_nothing(self):
    inventory = self.inventory()
    source = self.orphan()

    outcome = inventory.quarantine(self.only_candidate(inventory), dry_run=True)

    self.assertFalse(outcome.quarantined)
    self.assertTrue(source.exists())
    self.assertFalse(self.quarantine_root().exists())

  def test_the_quarantine_directory_is_never_the_recording_root(self):
    from backend.src.service.recording_orphan import QUARANTINE_DIRECTORY_NAME

    self.assertTrue(QUARANTINE_DIRECTORY_NAME.startswith("."))
    self.assertNotIn("/", QUARANTINE_DIRECTORY_NAME)


class QuarantineSourceInvariantTest(unittest.TestCase):
  ##
  ## Guarding the shape as well as the behaviour. A later edit that reached for
  ## ``shutil.move`` would pass every behavioural test above on a single
  ## filesystem and silently become copy-and-delete the first time a deployment
  ## mounted its media somewhere else.
  ##
  def test_the_service_never_copies_deletes_or_globs(self):
    source = (
      Path(__file__).resolve().parents[1] / "service" / "recording_orphan.py"
    ).read_text(encoding="utf-8")

    for forbidden in (
      "shutil.move",
      "shutil.copy",
      "shutil.rmtree",
      "os.removedirs",
      "rmtree",
      ".glob(",
      "os.walk",
    ):
      self.assertNotIn(
        forbidden, source, "quarantine must not use {}".format(forbidden)
      )

  def test_the_service_never_infers_an_owner(self):
    source = (
      Path(__file__).resolve().parents[1] / "service" / "recording_orphan.py"
    ).read_text(encoding="utf-8")

    for forbidden in ("app_user_id", "owner_user_id"):
      ##
      ## Mentioned in prose is fine and deliberate - the reasoning belongs in
      ## the file. Reading one into a variable is not.
      ##
      code = "\n".join(
        line for line in source.splitlines() if not line.strip().startswith("##")
      )
      self.assertNotIn(forbidden, code)


if __name__ == "__main__":
  unittest.main()


class QuarantineIncompleteTest(QuarantineTestCase):
  ##
  ## Past the link, the bytes cannot be lost - they are reachable through the
  ## quarantine name whatever happens next. What must not happen is reporting
  ## that as either a clean success or a clean refusal, because an operator's
  ## next action differs in each case.
  ##
  def test_a_failed_unlink_is_reported_as_incomplete_not_as_success(self):
    import os

    from backend.src.service.recording_orphan import OrphanQuarantineIncomplete

    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)

    real_unlink = os.unlink

    def refusing_unlink(path, *arguments, **options):
      if str(path) == source.name:
        raise PermissionError("the recording directory is read-only")
      return real_unlink(path, *arguments, **options)

    os.unlink = refusing_unlink
    try:
      with self.assertRaises(OrphanQuarantineIncomplete):
        inventory.quarantine(candidate)
    finally:
      os.unlink = real_unlink

    ##
    ## Both names now hold the same inode. Nothing is lost, which is the whole
    ## point of linking before unlinking.
    ##
    self.assertTrue(source.exists())
    moved = self.quarantined_media()
    self.assertEqual(1, len(moved))
    self.assertEqual(os.stat(source).st_ino, os.stat(moved[0]).st_ino)

  def test_an_incomplete_quarantine_is_completed_by_retrying(self):
    import os

    from backend.src.service.recording_orphan import OrphanQuarantineIncomplete

    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)

    real_unlink = os.unlink
    failures = {"remaining": 1}

    def flaky_unlink(path, *arguments, **options):
      if str(path) == source.name and failures["remaining"]:
        failures["remaining"] -= 1
        raise PermissionError("the recording directory is read-only")
      return real_unlink(path, *arguments, **options)

    os.unlink = flaky_unlink
    try:
      with self.assertRaises(OrphanQuarantineIncomplete):
        inventory.quarantine(candidate)
      ##
      ## The retry recomputes the same destination, finds its own inode there
      ## and finishes rather than writing a second copy under a new name.
      ##
      outcome = inventory.quarantine(candidate)
    finally:
      os.unlink = real_unlink

    self.assertTrue(outcome.quarantined)
    self.assertFalse(source.exists())
    self.assertEqual(1, len(self.quarantined_media()))

  def test_an_incomplete_quarantine_is_still_refused_by_callers(self):
    from backend.src.service.recording_orphan import (
      OrphanQuarantineIncomplete,
      OrphanQuarantineRefused,
    )

    ##
    ## A caller that already treats a refusal as "this did not happen" keeps
    ## doing so, which is why this is a subclass rather than a sibling.
    ##
    self.assertTrue(
      issubclass(OrphanQuarantineIncomplete, OrphanQuarantineRefused)
    )
