##
## The line the media hard-link draws, tested from both sides.
##
## ``test_recording_orphan_quarantine_records`` proves the named failure points
## an implementation was written to survive. This file proves the *rule* those
## points are instances of, because a rule that only holds where somebody
## remembered to check it is not a rule:
##
##   - Before the media link is published, a failure is
##     ``OrphanQuarantineRefused``: nothing was created and the operator may
##     believe the storage is untouched.
##   - After it, every failure is ``OrphanQuarantineIncomplete``. Not a
##     refusal, not a bare ``OSError``, and not whatever type the underlying
##     library happened to raise - the media is reachable under a second name
##     and the caller has to be told so.
##
## So the injection below is not a list of anticipated errors. It walks the
## ``os`` entry points the publication actually uses and fails each of them
## once the link exists, including the ones nobody writes a bespoke test for:
## the descriptor closes in a ``finally``, and the failures that are not
## ``OSError`` at all.
##
import json
import os
import unittest

from backend.src.service.recording_orphan import (
  OrphanQuarantineIncomplete,
  OrphanQuarantineRefused,
)

from backend.src.unit_test.test_recording_orphan_quarantine import (
  QuarantineTestCase,
)
from backend.src.unit_test.test_recording_orphan_quarantine_records import (
  fails_for,
  record_name_of,
)


##
## Fail one ``os`` entry point, but only once the media is durably linked.
##
## Armed by watching ``os.link`` itself: the media link is the one whose source
## is not the record's ``.part`` staging name, and it is the exact moment the
## contract changes meaning. Arming on anything earlier would be testing the
## refusal half by accident.
##
## The replacement calls through *first* and raises afterwards, which is both
## the honest shape of a failure like ``EIO`` on close and the only way not to
## leak the descriptors the real call would have released.
##
class fails_after_media_link:
  def __init__(self, function_name, error, predicate=None):
    self.function_name = function_name
    self.error = error
    self.predicate = predicate or (lambda *a, **k: True)
    self.armed = False
    self._original = None
    self._original_link = None

  def __enter__(self):
    self._original = getattr(os, self.function_name)
    self._original_link = os.link
    owner = self

    def watching_link(source, destination, *arguments, **options):
      ##
      ## ``EEXIST`` on the media link arms this too, and has to. It is how a
      ## retry discovers that an interrupted earlier attempt already published
      ## the media - the same durable fact, reached without linking anything,
      ## and the point after which this attempt's failures are partial
      ## completions just as much as a fresh link's are.
      ##
      try:
        result = owner._original_link(source, destination, *arguments, **options)
      except FileExistsError:
        if not str(source).endswith(".part"):
          owner.armed = True
        raise
      if not str(source).endswith(".part"):
        owner.armed = True
      return result

    def replacement(*arguments, **options):
      result = owner._original(*arguments, **options)
      if owner.armed and owner.predicate(*arguments, **options):
        raise owner.error
      return result

    ##
    ## When the injected point *is* ``link``, the watcher has to be the thing
    ## that fails, or the two patches would overwrite one another.
    ##
    if self.function_name == "link":
      def failing_link(source, destination, *arguments, **options):
        if owner.armed and owner.predicate(source, destination):
          raise owner.error
        return watching_link(source, destination, *arguments, **options)

      os.link = failing_link
    else:
      os.link = watching_link
      setattr(os, self.function_name, replacement)
    return self

  def __exit__(self, *unused):
    os.link = self._original_link
    setattr(os, self.function_name, self._original)
    return False


##
## Every ``os`` call the record publication and the source unlink can make,
## and a failure for each. The point of the list is that it is not curated by
## what the implementation currently does with them.
##
##
## The trailing flag says the point is only reachable when a record from an
## interrupted earlier attempt is already on disk - reading one back is not
## something a first attempt does. Without the flag those two rows would look
## like passing tests while exercising nothing at all.
##
POINTS_AFTER_THE_LINK = (
  ("open the record", "open", PermissionError("record cannot be staged"), False),
  ("write the record", "write", OSError(28, "no space left on device"), False),
  ("commit the record", "fsync", OSError(5, "input/output error"), False),
  ("publish the record", "link", OSError(31, "too many links"), False),
  ("read a record back", "read", OSError(5, "input/output error"), True),
  ("inspect a record", "fstat", OSError(5, "input/output error"), True),
  ("unlink the source", "unlink", PermissionError("read-only file system"), False),
  ##
  ## The descriptor closes. They live in ``finally`` blocks, which is exactly
  ## why they are easy to leave outside whatever maps failures to the partial
  ## completion type - and a close that reports ``EIO`` is a real thing a
  ## writeback error does.
  ##
  ("close a descriptor", "close", OSError(5, "input/output error"), False),
  ##
  ## And the failures that are not ``OSError`` at all. The contract is about
  ## what is true on disk, not about which exception family a helper picked,
  ## so an unanticipated type may not escape either.
  ##
  ("draw a temporary name", "urandom", NotImplementedError("no entropy"), False),
  ("write the record badly", "write", ValueError("payload is not bytes"), False),
)


##
## Leave behind exactly what a crash between the record and the unlink leaves:
## the media linked, a valid record beside it, and the source still there.
##
def interrupt_before_the_unlink(test, inventory, candidate, source):
  with fails_for(
    "unlink",
    lambda path, *a, **k: str(path) == source.name,
    PermissionError("read-only"),
  ):
    with test.assertRaises(OrphanQuarantineIncomplete):
      inventory.quarantine(candidate)
  test.assertTrue(source.exists())


class EveryFailureAfterTheLinkIsPartialCompletionTest(QuarantineTestCase):
  def test_no_failure_after_the_media_link_is_reported_as_a_refusal(self):
    for description, function_name, error, needs_record in POINTS_AFTER_THE_LINK:
      with self.subTest(point=description, function=function_name):
        self.setUp()
        inventory = self.inventory()
        source = self.orphan()
        candidate = self.only_candidate(inventory)
        if needs_record:
          interrupt_before_the_unlink(self, inventory, candidate, source)

        with fails_after_media_link(function_name, error):
          try:
            inventory.quarantine(candidate)
          except OrphanQuarantineIncomplete:
            pass
          except BaseException as escaped:
            self.fail(
              "failing {} after the link raised {}: {!r}".format(
                function_name, type(escaped).__name__, escaped
              )
            )

        ##
        ## Whatever was reported, nothing may have been lost: the bytes are
        ## reachable under the quarantined name, and where the source survives
        ## it is the same inode rather than a copy.
        ##
        moved = [
          path for path in self.quarantined_media()
          if not path.name.startswith(".")
        ]
        self.assertEqual(
          1, len(moved), "the media link must exist after it was published"
        )
        if source.exists():
          self.assertEqual(
            os.stat(source).st_ino,
            os.stat(moved[0]).st_ino,
            "the source must still be the file that was linked",
          )

  ##
  ## Not every failure below the line is a storage error. If anything down
  ## there ever raises a *refusal* - a later edit reusing the word, a helper
  ## whose contract changes - the caller must still be told the truth, because
  ## the link exists whatever the raiser called it.
  ##
  def test_a_refusal_raised_below_the_line_is_restated_as_partial(self):
    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)

    def refusing_publication(*unused, **also_unused):
      raise OrphanQuarantineRefused("nothing happened, allegedly")

    inventory._publish_record = refusing_publication

    with self.assertRaises(OrphanQuarantineIncomplete):
      inventory.quarantine(candidate)

    self.assertTrue(source.exists())
    self.assertEqual(1, len(self.quarantined_media()))

  ##
  ## The other half, restated as a rule rather than as three arranged cases: a
  ## refusal must leave the quarantine directory itself absent, so "nothing was
  ## created" is checkable rather than merely claimed.
  ##
  def test_a_refusal_still_means_no_quarantine_state_exists(self):
    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)
    self.references.paths = [str(source)]

    with self.assertRaises(OrphanQuarantineRefused) as caught:
      inventory.quarantine(candidate)

    self.assertNotIsInstance(caught.exception, OrphanQuarantineIncomplete)
    self.assertTrue(source.exists())
    self.assertFalse(self.quarantine_root().exists())


class RecordPublicationOrderTest(QuarantineTestCase):
  ##
  ## The required order is
  ##
  ##   hidden exclusive temporary -> write -> fsync the temporary
  ##     -> no-clobber publication of the final name
  ##     -> fsync the quarantine directory
  ##     -> remove the temporary
  ##
  ## and the last two are the pair that is easy to get backwards. Removing the
  ## temporary first folds two directory changes into one commit, so a crash
  ## between them can leave the final name uncommitted; committing first makes
  ## the record durable and reduces the leftover temporary to hygiene.
  ##
  def test_the_quarantine_directory_is_committed_before_the_temporary_goes(self):
    inventory = self.inventory()
    self.orphan()
    candidate = self.only_candidate(inventory)
    final = record_name_of(inventory, candidate)

    events = []
    original_link, original_fsync, original_unlink = os.link, os.fsync, os.unlink
    directories = set()
    original_open = os.open

    def watching_open(path, flags, *arguments, **options):
      descriptor = original_open(path, flags, *arguments, **options)
      if flags & os.O_DIRECTORY:
        directories.add(descriptor)
      return descriptor

    def watching_link(source, destination, *arguments, **options):
      result = original_link(source, destination, *arguments, **options)
      if str(destination) == final:
        events.append("publish record")
      return result

    def watching_fsync(descriptor):
      result = original_fsync(descriptor)
      ##
      ## Only directory commits matter here; the record's own file fsync
      ## happens earlier and is not what this orders against.
      ##
      if descriptor in directories:
        events.append("commit directory")
      return result

    def watching_unlink(path, *arguments, **options):
      if str(path).endswith(".part"):
        events.append("remove temporary")
      return original_unlink(path, *arguments, **options)

    os.open, os.link, os.fsync, os.unlink = (
      watching_open, watching_link, watching_fsync, watching_unlink
    )
    try:
      inventory.quarantine(candidate)
    finally:
      os.open, os.link, os.fsync, os.unlink = (
        original_open, original_link, original_fsync, original_unlink
      )

    self.assertIn("publish record", events)
    self.assertIn("remove temporary", events)
    published = events.index("publish record")
    removed = events.index("remove temporary")
    committed = [
      index for index, name in enumerate(events)
      if name == "commit directory" and index > published
    ]
    self.assertTrue(
      committed, "the quarantine directory is never committed after publication"
    )
    self.assertLess(
      committed[0],
      removed,
      "the temporary was removed before the publication was committed: {}".format(
        events
      ),
    )


class ExistingRecordIsAlwaysValidatedTest(QuarantineTestCase):
  ##
  ## An existing final record is evidence, never permission. Each shape below
  ## is one a crash or a collision can really leave, and none of them may end
  ## with the source unlinked.
  ##
  def plant(self, inventory, candidate, content):
    destination = inventory.quarantine_destination_for(candidate)
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    record = destination.parent / (destination.name + ".json")
    record.write_bytes(content)
    return record

  def valid_payload(self, inventory, candidate, **overrides):
    payload = {
      "schema_version": 1,
      "source_relative_path": candidate.relative_path,
      "quarantined_name": record_name_of(inventory, candidate)[:-5],
      "size": candidate.size,
      "mtime_ns": candidate.mtime_ns,
      "quarantined_at": "2026-09-06T00:00:00.000+00:00",
    }
    payload.update(overrides)
    return json.dumps(payload).encode("utf-8")

  def assert_refuses_to_unlink(self, inventory, candidate, source):
    with self.assertRaises(OrphanQuarantineIncomplete):
      inventory.quarantine(candidate)
    self.assertTrue(
      source.exists(), "an unvalidated record must never permit the unlink"
    )

  ##
  ## And it stops *before* it writes. An existing record this build cannot
  ## vouch for is a reason to do nothing at all, not a reason to stage a
  ## replacement and discover the collision afterwards - staging first is how
  ## "the name was taken" comes to stand in for "the record was checked".
  ##
  def test_an_unreadable_record_stops_the_move_before_anything_is_staged(self):
    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)
    self.plant(inventory, candidate, b"")

    staged = []
    original_open = os.open

    def watching_open(path, flags, *arguments, **options):
      if str(path).endswith(".part"):
        staged.append(str(path))
      return original_open(path, flags, *arguments, **options)

    os.open = watching_open
    try:
      with self.assertRaises(OrphanQuarantineIncomplete):
        inventory.quarantine(candidate)
    finally:
      os.open = original_open

    self.assertEqual([], staged, "a replacement was staged against an empty record")
    self.assertTrue(source.exists())
    self.assertEqual(b"", self.plant_path(inventory, candidate).read_bytes())

  def plant_path(self, inventory, candidate):
    destination = inventory.quarantine_destination_for(candidate)
    return destination.parent / (destination.name + ".json")

  def test_a_record_disagreeing_about_the_size_stops_the_move(self):
    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)
    self.plant(
      inventory, candidate, self.valid_payload(inventory, candidate, size=1)
    )
    self.assert_refuses_to_unlink(inventory, candidate, source)

  def test_a_record_disagreeing_about_the_mtime_stops_the_move(self):
    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)
    self.plant(
      inventory, candidate, self.valid_payload(inventory, candidate, mtime_ns=1)
    )
    self.assert_refuses_to_unlink(inventory, candidate, source)

  def test_a_record_naming_a_different_destination_stops_the_move(self):
    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)
    self.plant(
      inventory,
      candidate,
      self.valid_payload(inventory, candidate, quarantined_name="something-else"),
    )
    self.assert_refuses_to_unlink(inventory, candidate, source)

  def test_a_record_that_is_a_json_array_stops_the_move(self):
    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)
    self.plant(inventory, candidate, b"[]")
    self.assert_refuses_to_unlink(inventory, candidate, source)

  def test_a_record_larger_than_one_can_be_stops_the_move(self):
    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)
    self.plant(inventory, candidate, b"{" + b" " * 70000 + b"}")
    self.assert_refuses_to_unlink(inventory, candidate, source)


##
## >>=============== and what the operator's terminal is told ===============>>
##
##
## The service contract only matters if the command that fronts it keeps it.
## These drive the real CLI against the real inventory on a real directory,
## with the failure injected underneath - so what is asserted is the exit code
## and the text an operator would actually get, not a fake's behaviour.
##
class QuarantineCliReportsPartialCompletionTest(QuarantineTestCase):
  def run_cli(self, *argv):
    import io

    from backend.src.service.recording_orphan_cli import main

    out = io.StringIO()
    inventory = self.inventory()
    code = main(list(argv), inventory_factory=lambda: inventory, out=out)
    return code, out.getvalue()

  def test_a_failure_after_the_link_exits_incomplete_rather_than_unavailable(self):
    from backend.src.service.recording_orphan_cli import EXIT_INCOMPLETE

    for description, function_name, error, needs_record in POINTS_AFTER_THE_LINK:
      with self.subTest(point=description, function=function_name):
        self.setUp()
        source = self.orphan()
        relative = str(source.relative_to(self.root))
        if needs_record:
          inventory = self.inventory()
          interrupt_before_the_unlink(
            self, inventory, self.only_candidate(inventory), source
          )

        with fails_after_media_link(function_name, error):
          code, printed = self.run_cli("quarantine", relative, "--confirm")

        self.assertEqual(
          EXIT_INCOMPLETE,
          code,
          "failing {} reported {} instead of a partial completion: {}".format(
            function_name, code, printed
          ),
        )
        self.assertIn("OrphanQuarantineIncomplete", printed)
        self.assertNotIn("Traceback", printed)
        ##
        ## An ``OSError``'s text carries the absolute path it failed on, and a
        ## deployment's filesystem layout is not what an operator pastes into a
        ## ticket.
        ##
        self.assertNotIn(str(self.root), printed)

  def test_no_storage_failure_before_the_link_escapes_as_a_traceback(self):
    from backend.src.service.recording_orphan_cli import EXIT_REFUSED

    source = self.orphan()
    relative = str(source.relative_to(self.root))

    ##
    ## ``mkdir`` is the last thing that can fail while nothing durable exists,
    ## and it is not one of the errors the quarantine path names explicitly.
    ##
    original = os.mkdir

    def refusing_mkdir(*arguments, **options):
      raise NotImplementedError("no directory support")

    os.mkdir = refusing_mkdir
    try:
      code, printed = self.run_cli("quarantine", relative, "--confirm")
    finally:
      os.mkdir = original

    self.assertEqual(EXIT_REFUSED, code, printed)
    self.assertNotIn("Traceback", printed)
    self.assertTrue(source.exists(), "a refusal must leave the media alone")


if __name__ == "__main__":
  unittest.main()
