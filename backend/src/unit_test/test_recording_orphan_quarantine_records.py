##
## The half-finished quarantine, and what an operator is told about it.
##
## Quarantine is two durable publications, not one: the media hard-link, and the
## record beside it that says which file that link used to be. Between them is a
## window, and the whole of this file is about what may be claimed inside it.
##
## Two rules, and everything here follows from them:
##
##   - ``OrphanQuarantineRefused`` means *nothing was created*. An operator who
##     reads it is entitled to believe the storage is exactly as it was, and to
##     go and do something else. Saying it after a link already exists is a lie
##     that leaves a file nobody will look for.
##   - Once that link exists, every later failure is
##     ``OrphanQuarantineIncomplete``: the bytes are safe under two names, and
##     retrying is the fix.
##
## The record must therefore be published the same way the media is - a hidden
## exclusive temporary, written in full, fsynced, then linked into place under a
## name that cannot be clobbered. Writing straight to the final name looks
## simpler and is how the source of somebody's recording gets removed against a
## zero-length record: the crash leaves the final name existing but empty, and a
## retry that treats "the name exists" as "the record is good" then unlinks the
## original.
##
## So an existing record is never trusted for existing. It is read, parsed and
## checked against the candidate being moved, and anything that does not match -
## truncated, corrupt, or describing a different file - stops the move with the
## source still there.
##
import json
import os
from pathlib import Path
import unittest

from backend.src.service.recording_orphan import (
  OrphanQuarantineIncomplete,
  OrphanQuarantineRefused,
)

from backend.src.unit_test.test_recording_orphan_quarantine import (
  QuarantineTestCase,
)


##
## A narrowly targeted failure injector.
##
## Patches one ``os`` entry point and fails only for the one name the test cares
## about, so the surrounding machinery - opening directories, reading the
## journal, linking the media - keeps working normally. A blanket failure would
## prove that the code stops, not that it stops *here*.
##
class fails_for:
  def __init__(self, function_name, predicate, error):
    self.function_name = function_name
    self.predicate = predicate
    self.error = error
    self.original = None

  def __enter__(self):
    self.original = getattr(os, self.function_name)
    original = self.original
    predicate = self.predicate
    error = self.error

    def replacement(*arguments, **options):
      if predicate(*arguments, **options):
        raise error
      return original(*arguments, **options)

    setattr(os, self.function_name, replacement)
    return self

  def __exit__(self, *unused):
    setattr(os, self.function_name, self.original)
    return False


def record_name_of(inventory, candidate):
  return inventory.quarantine_destination_for(candidate).name + ".json"


class QuarantineRecordPublicationTest(QuarantineTestCase):
  ##
  ## >>================== the record is published atomically ==================>>
  ##

  def test_the_record_is_never_written_straight_to_its_final_name(self):
    inventory = self.inventory()
    self.orphan()
    candidate = self.only_candidate(inventory)
    final = record_name_of(inventory, candidate)

    opened = []
    original_open = os.open

    def watching_open(path, flags, *arguments, **options):
      opened.append((str(path), flags))
      return original_open(path, flags, *arguments, **options)

    os.open = watching_open
    try:
      inventory.quarantine(candidate)
    finally:
      os.open = original_open

    ##
    ## The final record name may be *read* - that is how an existing record is
    ## checked rather than assumed. What it must never be is created or written,
    ## because a name that comes into existence before its bytes do is exactly
    ## the zero-length record a later attempt would misread as proof.
    ##
    writable = os.O_WRONLY | os.O_RDWR | os.O_CREAT
    final_opens = [flags for path, flags in opened if path == final]
    self.assertTrue(final_opens, "an existing record must be looked for")
    for flags in final_opens:
      self.assertEqual(
        0, flags & writable, "the final record name must never be opened to write"
      )

    ##
    ## And the bytes went somewhere else first.
    ##
    self.assertTrue(
      any(
        path.endswith(".part") and flags & os.O_CREAT
        for path, flags in opened
      ),
      "the record must be staged through an exclusive temporary",
    )

  def test_no_temporary_survives_a_successful_publication(self):
    inventory = self.inventory()
    self.orphan()

    inventory.quarantine(self.only_candidate(inventory))

    leftovers = [
      path.name for path in self.quarantine_root().iterdir()
      if ".part" in path.name or path.name.startswith(".")
    ]
    self.assertEqual([], leftovers)

  ##
  ## >>============ every failure after the link is INCOMPLETE ============>>
  ##

  def assert_incomplete_and_media_preserved(self, inventory, candidate, source):
    with self.assertRaises(OrphanQuarantineIncomplete):
      inventory.quarantine(candidate)
    ##
    ## The source is still there, so nothing was lost - and the link is there
    ## too, which is why this is not a refusal.
    ##
    self.assertTrue(source.exists(), "a partial quarantine must not lose media")
    moved = self.quarantined_media()
    self.assertEqual(1, len(moved), "the media link must already exist")
    self.assertEqual(os.stat(source).st_ino, os.stat(moved[0]).st_ino)

  def test_a_record_that_cannot_be_opened_is_incomplete_not_refused(self):
    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)

    with fails_for(
      "open",
      lambda path, *a, **k: str(path).endswith(".part"),
      PermissionError("cannot create the quarantine record"),
    ):
      self.assert_incomplete_and_media_preserved(inventory, candidate, source)

  def test_a_record_that_cannot_be_written_is_incomplete_not_refused(self):
    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)

    with fails_for(
      "write",
      lambda *a, **k: True,
      OSError(28, "no space left on device"),
    ):
      self.assert_incomplete_and_media_preserved(inventory, candidate, source)

  def test_a_record_whose_bytes_cannot_be_committed_is_incomplete(self):
    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)

    ##
    ## The media link's own directory commit has already happened by this
    ## point, so this is the record's file fsync and nothing else.
    ##
    calls = {"seen": 0}

    def second_fsync(*unused, **also_unused):
      calls["seen"] += 1
      return calls["seen"] > 1

    with fails_for("fsync", second_fsync, OSError(5, "input/output error")):
      self.assert_incomplete_and_media_preserved(inventory, candidate, source)

  def test_a_directory_that_cannot_be_committed_is_incomplete(self):
    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)

    ##
    ## Every directory commit after the media link has landed. The link itself
    ## already exists, so none of these may be reported as "nothing happened".
    ##
    calls = {"seen": 0}

    def after_the_link(*unused, **also_unused):
      calls["seen"] += 1
      return calls["seen"] > 1

    with fails_for("fsync", after_the_link, OSError(5, "input/output error")):
      self.assert_incomplete_and_media_preserved(inventory, candidate, source)

  ##
  ## >>============== an existing record is read, never assumed ==============>>
  ##

  def plant_record(self, inventory, candidate, content):
    destination = inventory.quarantine_destination_for(candidate)
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    record = destination.parent / (destination.name + ".json")
    record.write_bytes(content)
    return record

  def test_a_zero_length_record_never_lets_the_source_be_unlinked(self):
    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)
    ##
    ## Exactly what a crash between "create the final name" and "write it"
    ## leaves behind. The old implementation read this as "already published".
    ##
    self.plant_record(inventory, candidate, b"")

    with self.assertRaises(OrphanQuarantineIncomplete):
      inventory.quarantine(candidate)
    self.assertTrue(source.exists(), "a truncated record must not permit unlink")

  def test_a_truncated_record_never_lets_the_source_be_unlinked(self):
    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)
    self.plant_record(inventory, candidate, b'{"schema_version":1,"sou')

    with self.assertRaises(OrphanQuarantineIncomplete):
      inventory.quarantine(candidate)
    self.assertTrue(source.exists())

  def test_a_record_describing_a_different_file_stops_the_move(self):
    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)
    self.plant_record(
      inventory,
      candidate,
      json.dumps(
        {
          "schema_version": 1,
          "source_relative_path": "douyin/live/somebody-else/other.flv",
          "quarantined_name": record_name_of(inventory, candidate)[:-5],
          "size": candidate.size,
          "mtime_ns": candidate.mtime_ns,
          "quarantined_at": "2026-09-04T00:00:00.000+00:00",
        }
      ).encode("utf-8"),
    )

    with self.assertRaises(OrphanQuarantineIncomplete):
      inventory.quarantine(candidate)
    self.assertTrue(source.exists())

  def test_a_record_from_an_unknown_schema_stops_the_move(self):
    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)
    self.plant_record(
      inventory,
      candidate,
      json.dumps(
        {
          "schema_version": 99,
          "source_relative_path": candidate.relative_path,
          "quarantined_name": record_name_of(inventory, candidate)[:-5],
          "size": candidate.size,
          "mtime_ns": candidate.mtime_ns,
          "quarantined_at": "2026-09-04T00:00:00.000+00:00",
        }
      ).encode("utf-8"),
    )

    with self.assertRaises(OrphanQuarantineIncomplete):
      inventory.quarantine(candidate)
    self.assertTrue(source.exists())

  def test_a_record_that_is_a_symlink_stops_the_move(self):
    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)
    destination = inventory.quarantine_destination_for(candidate)
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    elsewhere = self.root / "planted.json"
    elsewhere.write_text("{}", encoding="utf-8")
    os.symlink(elsewhere, destination.parent / (destination.name + ".json"))

    with self.assertRaises(OrphanQuarantineIncomplete):
      inventory.quarantine(candidate)
    self.assertTrue(source.exists())

  ##
  ## >>========================= retry is the fix =========================>>
  ##

  def test_a_valid_matching_record_lets_a_retry_complete_the_move(self):
    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)

    ##
    ## Interrupted after the media link and the record, before the unlink.
    ##
    with fails_for(
      "unlink",
      lambda path, *a, **k: str(path) == source.name,
      PermissionError("read-only"),
    ):
      with self.assertRaises(OrphanQuarantineIncomplete):
        inventory.quarantine(candidate)

    outcome = inventory.quarantine(candidate)

    self.assertTrue(outcome.quarantined)
    self.assertFalse(source.exists())
    self.assertEqual(1, len(self.quarantined_media()))
    ##
    ## Exactly one record, republished by nobody.
    ##
    self.assertEqual(1, len(list(self.quarantine_root().glob("*.json"))))

  def test_a_retry_after_a_failed_record_publication_completes(self):
    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)

    with fails_for(
      "open",
      lambda path, *a, **k: str(path).endswith(".part"),
      PermissionError("cannot create the quarantine record"),
    ):
      with self.assertRaises(OrphanQuarantineIncomplete):
        inventory.quarantine(candidate)

    outcome = inventory.quarantine(candidate)

    self.assertTrue(outcome.quarantined)
    self.assertFalse(source.exists())
    record = json.loads(
      sorted(self.quarantine_root().glob("*.json"))[0].read_text(encoding="utf-8")
    )
    self.assertEqual(candidate.relative_path, record["source_relative_path"])


class QuarantineRefusalMeansNothingHappenedTest(QuarantineTestCase):
  ##
  ## The other half of the contract. Everything that refuses must refuse before
  ## a single durable change, so the word keeps its meaning.
  ##
  def test_every_refusal_leaves_no_quarantine_state_at_all(self):
    refusals = (
      ("unreachable database", self.make_database_unreachable),
      ("newly referenced", self.make_newly_referenced),
      ("changed file", self.make_changed),
    )
    for name, arrange in refusals:
      with self.subTest(refusal=name):
        self.setUp()
        inventory = self.inventory()
        source = self.orphan()
        candidate = self.only_candidate(inventory)
        arrange(source)

        with self.assertRaises(OrphanQuarantineRefused) as caught:
          inventory.quarantine(candidate)

        self.assertNotIsInstance(caught.exception, OrphanQuarantineIncomplete)
        self.assertTrue(source.exists())
        self.assertFalse(
          self.quarantine_root().exists(),
          "a refusal must not create quarantine state",
        )

  def make_database_unreachable(self, unused):
    self.references.error = RuntimeError("database is down")

  def make_newly_referenced(self, source):
    self.references.paths = [str(source)]

  def make_changed(self, source):
    source.write_bytes(b"a different, longer broadcast entirely")


if __name__ == "__main__":
  unittest.main()
