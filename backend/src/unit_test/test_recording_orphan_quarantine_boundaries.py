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
import stat
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


##
## Fail ``os.close`` only once the move is *finished*.
##
## Armed by watching the two events that finish it, in order: the source name
## being unlinked, and the first directory commit after that - which is the
## source parent's. Everything the operator asked for has happened by then;
## what is left is releasing descriptors.
##
## The distinction this exists to hold is not cosmetic. ``Incomplete`` tells an
## operator "retry and it will finish", and after the commit there is nothing to
## finish: the source name is durably gone, so a retry cannot even find the
## candidate again and would answer with a refusal instead. Reporting a
## completed destructive move as retry-required is worse than reporting nothing.
##
class fails_close_after_the_move_is_committed:
  def __init__(self, error, source_name):
    self.error = error
    self.source_name = source_name
    self.unlinked = False
    self.armed = False
    self._originals = {}

  def __enter__(self):
    owner = self
    for name in ("unlink", "fsync", "close"):
      self._originals[name] = getattr(os, name)

    def watching_unlink(path, *arguments, **options):
      result = owner._originals["unlink"](path, *arguments, **options)
      if str(path) == owner.source_name:
        owner.unlinked = True
      return result

    def watching_fsync(descriptor):
      result = owner._originals["fsync"](descriptor)
      ##
      ## The first commit after the unlink is the source parent's, and it is the
      ## last durable step of the move.
      ##
      if owner.unlinked:
        owner.armed = True
      return result

    def failing_close(descriptor):
      ##
      ## Released first and reported afterwards, which is what a writeback error
      ## surfacing at ``close`` really does - and the only way not to leak the
      ## descriptor the test is about.
      ##
      owner._originals["close"](descriptor)
      if owner.armed:
        raise owner.error

    os.unlink, os.fsync, os.close = watching_unlink, watching_fsync, failing_close
    return self

  def __exit__(self, *unused):
    os.unlink = self._originals["unlink"]
    os.fsync = self._originals["fsync"]
    os.close = self._originals["close"]
    return False


class ACommittedMoveIsNotRetryRequiredTest(QuarantineTestCase):
  ##
  ## The third state, and the one the ``linked`` boundary alone cannot express.
  ##
  ## ``linked`` divides "nothing happened" from "half happened". It does not
  ## divide "half happened" from "finished", and a failure released after the
  ## source parent is committed falls on the wrong side of the only line there
  ## was.
  ##
  def arrange(self):
    inventory = self.inventory()
    source = self.orphan()
    candidate = self.only_candidate(inventory)
    return inventory, source, candidate

  def assert_fully_quarantined(self, source, candidate):
    self.assertFalse(source.exists(), "the source name must be durably gone")

    moved = [
      path for path in self.quarantined_media()
      if not path.name.startswith(".")
    ]
    self.assertEqual(1, len(moved), "the quarantined media must be there")

    records = sorted(self.quarantine_root().glob("*.json"))
    self.assertEqual(1, len(records), "the quarantine record must be there")
    written = json.loads(records[0].read_text(encoding="utf-8"))

    ##
    ## The record has to describe *this* media, not merely exist beside it.
    ##
    self.assertEqual(candidate.relative_path, written["source_relative_path"])
    self.assertEqual(moved[0].name, written["quarantined_name"])
    self.assertEqual(candidate.size, written["size"])
    self.assertEqual(candidate.mtime_ns, written["mtime_ns"])
    self.assertEqual(os.stat(moved[0]).st_size, written["size"])

  def test_a_close_failure_after_the_commit_still_reports_success(self):
    inventory, source, candidate = self.arrange()

    with fails_close_after_the_move_is_committed(
      OSError(5, "input/output error"), source.name
    ) as injector:
      outcome = inventory.quarantine(candidate)

    self.assertTrue(
      injector.armed, "the injection never reached the committed state"
    )
    ##
    ## Committed success: the same answer an uninterrupted move gives.
    ##
    self.assertTrue(outcome.quarantined)
    self.assertEqual(candidate.relative_path, outcome.relative_path)
    self.assert_fully_quarantined(source, candidate)

  def test_a_close_failure_after_the_commit_is_never_incomplete(self):
    inventory, source, candidate = self.arrange()

    ##
    ## Stated separately from the success assertion because this is the whole
    ## defect: the move was reported as retry-required after it had finished.
    ##
    try:
      with fails_close_after_the_move_is_committed(
        OSError(5, "input/output error"), source.name
      ):
        inventory.quarantine(candidate)
    except OrphanQuarantineIncomplete as e:
      self.fail("a committed move was reported as retry-required: {}".format(e))
    except OrphanQuarantineRefused as e:
      self.fail("a committed move was reported as a refusal: {}".format(e))
    except OSError as e:
      self.fail("a raw storage error reached the caller: {!r}".format(e))

  ##
  ## And the operator's terminal says the same thing.
  ##
  def test_the_cli_reports_a_committed_move_as_success(self):
    from backend.src.service.recording_orphan_cli import EXIT_OK

    import io

    from backend.src.service.recording_orphan_cli import main

    inventory, source, candidate = self.arrange()
    relative = str(source.relative_to(self.root))
    out = io.StringIO()

    with fails_close_after_the_move_is_committed(
      OSError(5, "input/output error"), source.name
    ):
      code = main(
        ["quarantine", relative, "--confirm"],
        inventory_factory=lambda: inventory,
        out=out,
      )

    printed = out.getvalue()
    self.assertEqual(EXIT_OK, code, printed)
    self.assertNotIn("incomplete", printed)
    self.assertNotIn("OrphanQuarantineIncomplete", printed)
    self.assertNotIn("Traceback", printed)
    self.assertNotIn(str(self.root), printed)
    self.assert_fully_quarantined(source, candidate)

  ##
  ## The commit boundary is the *successful* source-parent fsync, not the
  ## unlink before it. A source name removed but not committed can come back
  ## after a crash, which is a half-finished move and nothing else - so the
  ## flag may not be set until the commit returns.
  ##
  def test_a_failing_source_parent_commit_is_still_a_partial_completion(self):
    inventory, source, candidate = self.arrange()

    unlinked = {"yes": False}
    original_unlink, original_fsync = os.unlink, os.fsync

    def watching_unlink(path, *arguments, **options):
      result = original_unlink(path, *arguments, **options)
      if str(path) == source.name:
        unlinked["yes"] = True
      return result

    def failing_fsync(descriptor):
      ##
      ## Only the commit that follows the unlink - the source parent's, and the
      ## last durable step there is.
      ##
      if unlinked["yes"]:
        raise OSError(5, "input/output error")
      return original_fsync(descriptor)

    os.unlink, os.fsync = watching_unlink, failing_fsync
    try:
      with self.assertRaises(OrphanQuarantineIncomplete):
        inventory.quarantine(candidate)
    finally:
      os.unlink, os.fsync = original_unlink, original_fsync

    ##
    ## And the media is safe either way: the quarantined name holds the bytes.
    ##
    moved = [
      path for path in self.quarantined_media()
      if not path.name.startswith(".")
    ]
    self.assertEqual(1, len(moved))

  ##
  ## The committed state is honoured in two independent places - the release
  ## helper swallows what it can, and the guard around the whole attempt
  ## catches whatever the helper did not. Each is tested on its own, because a
  ## pair that only works together is a pair where either half can rot
  ## unnoticed behind the other.
  ##
  ## This one is the guard: a failure after the commit that is *not* a
  ## descriptor release, so the helper never sees it.
  ##
  def test_any_failure_after_the_commit_still_reports_the_completed_move(self):
    from backend.src.service import recording_orphan as module

    inventory, source, candidate = self.arrange()

    ##
    ## The audit line, which is the last thing between the commit and the
    ## return. A logger that raises stands in for anything a later edit might
    ## put there.
    ##
    original_get_logger = module.get_logger
    committed = {"yes": False}
    original_fsync = os.fsync

    def watching_fsync(descriptor):
      result = original_fsync(descriptor)
      if not source.exists():
        committed["yes"] = True
      return result

    class ExplodingLogger:
      def warning(self, *unused, **also_unused):
        if committed["yes"]:
          raise RuntimeError("the log sink is gone")
        return None

    os.fsync = watching_fsync
    module.get_logger = lambda: ExplodingLogger()
    try:
      outcome = inventory.quarantine(candidate)
    finally:
      module.get_logger = original_get_logger
      os.fsync = original_fsync

    self.assertTrue(committed["yes"], "the move never reached the commit")
    self.assertTrue(outcome.quarantined)
    self.assertEqual(candidate.relative_path, outcome.relative_path)
    self.assert_fully_quarantined(source, candidate)

  ##
  ## And this one is the release helper, on its own terms: it decides what a
  ## failed release *means*, and that decision is the other half.
  ##
  def test_the_release_helper_reports_before_the_commit_and_not_after(self):
    from backend.src.service.recording_orphan import (
      _QuarantineProgress,
      _release_descriptors,
    )

    ##
    ## Real descriptors, opened before ``os.close`` is replaced so the setup
    ## does not run into the injection it is arranging.
    ##
    first_readable, first_writable = os.pipe()
    second_readable, second_writable = os.pipe()

    progress = _QuarantineProgress()
    original_close = os.close

    def failing_close(descriptor):
      original_close(descriptor)
      raise OSError(5, "input/output error")

    os.close = failing_close
    try:
      ##
      ## Before the commit a failed release is a real fault in the middle of a
      ## half-finished move, and the caller has to hear about it.
      ##
      with self.assertRaises(OSError):
        _release_descriptors(progress, first_readable, first_writable)

      ##
      ## After it, the same failure changes nothing on disk.
      ##
      progress.committed = True
      _release_descriptors(progress, second_readable, second_writable)
    finally:
      os.close = original_close

  ##
  ## One cleanup failure must not strand the descriptors after it. A leak here
  ## is unbounded: this command is run repeatedly against a library, and every
  ## run would keep three.
  ##
  def test_every_descriptor_is_released_even_when_one_release_fails(self):
    inventory, source, candidate = self.arrange()

    opened, closed = [], []
    original_open, original_close = os.open, os.close

    def watching_open(path, flags, *arguments, **options):
      descriptor = original_open(path, flags, *arguments, **options)
      if flags & os.O_DIRECTORY:
        opened.append(descriptor)
      return descriptor

    def failing_close(descriptor):
      original_close(descriptor)
      closed.append(descriptor)
      raise OSError(5, "input/output error")

    os.open = watching_open
    try:
      with fails_close_after_the_move_is_committed(
        OSError(5, "input/output error"), source.name
      ):
        ##
        ## Replace the injector's own close with one that fails for *every*
        ## descriptor once armed, so the first failure is the one that could
        ## strand the rest.
        ##
        armed_close = os.close

        def failing_every_close(descriptor):
          if getattr(failing_every_close, "armed", False):
            return failing_close(descriptor)
          return armed_close(descriptor)

        os.close = failing_every_close
        original_fsync = os.fsync

        def arming_fsync(descriptor):
          result = original_fsync(descriptor)
          if not source.exists():
            failing_every_close.armed = True
          return result

        os.fsync = arming_fsync
        try:
          inventory.quarantine(candidate)
        finally:
          os.fsync = original_fsync
    finally:
      os.open = original_open

    stranded = [descriptor for descriptor in opened if descriptor not in closed]
    self.assertEqual(
      [], stranded, "a failing release stranded the descriptors after it"
    )


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


##
## >>========= finishing a move whose source name is already gone =========>>
##
##
## The state the ``committed`` flag named but nothing could leave.
##
## After the source unlink succeeds and the source parent's commit does not,
## the move is one fsync short of finished - and ``Incomplete`` tells the
## operator to run the command again. That instruction was not true. The name
## the candidate was found under no longer exists, so the next scan does not
## find it, and the same command answered REFUSED: the one state that most
## needed a recovery path was the one that had none.
##
## What follows is that path, and the whole of it is about proving the thing
## being finished is the thing that was started. The source is gone, so there
## is nothing left to compare against; the only evidence is the quarantined
## media and the record beside it, and both have to be re-proved from scratch
## before a single durable action is taken. Anything that cannot be proved
## fails closed, because the alternative - treating "the source is missing" as
## "the move must have worked" - would report success for a file somebody else
## deleted.
##
class QuarantineRecoveryAfterSourceUnlinkTest(QuarantineTestCase):
  def cli(self, inventory, *argv):
    import io

    from backend.src.service.recording_orphan_cli import main

    out = io.StringIO()
    code = main(list(argv), inventory_factory=lambda: inventory, out=out)
    return code, out.getvalue()

  ##
  ## Drive one real quarantine to the exact point the defect lives at: source
  ## unlinked, source parent not committed.
  ##
  def interrupt_at_the_source_parent_commit(self, inventory, source, relative):
    unlinked = {"yes": False}
    original_unlink, original_fsync = os.unlink, os.fsync

    def watching_unlink(path, *arguments, **options):
      result = original_unlink(path, *arguments, **options)
      if str(path) == source.name:
        unlinked["yes"] = True
      return result

    def failing_fsync(descriptor):
      if unlinked["yes"]:
        raise OSError(5, "input/output error")
      return original_fsync(descriptor)

    os.unlink, os.fsync = watching_unlink, failing_fsync
    try:
      code, printed = self.cli(inventory, "quarantine", relative, "--confirm")
    finally:
      os.unlink, os.fsync = original_unlink, original_fsync
    return code, printed

  def arrange_interrupted(self):
    from backend.src.service.recording_orphan_cli import EXIT_INCOMPLETE

    inventory = self.inventory()
    source = self.orphan()
    relative = str(source.relative_to(self.root))

    code, printed = self.interrupt_at_the_source_parent_commit(
      inventory, source, relative
    )

    self.assertEqual(EXIT_INCOMPLETE, code, printed)
    ##
    ## And the state the second invocation has to work from.
    ##
    self.assertFalse(source.exists(), "the source name must already be gone")
    media = self.only_media()
    self.assertTrue(media.is_file())
    record = self.only_record()
    written = json.loads(record.read_text(encoding="utf-8"))
    self.assertEqual(relative, written["source_relative_path"])
    self.assertEqual(media.name, written["quarantined_name"])
    self.assertEqual(os.stat(media).st_size, written["size"])
    return inventory, source, relative

  def only_media(self):
    media = [
      path for path in self.quarantined_media()
      if not path.name.startswith(".")
    ]
    self.assertEqual(1, len(media))
    return media[0]

  def only_record(self):
    records = sorted(self.quarantine_root().glob("*.json"))
    self.assertEqual(1, len(records))
    return records[0]

  ##
  ## Everything under the root, by identity rather than by name, so "nothing
  ## was recreated, copied, overwritten or added" is one assertion instead of
  ## eight.
  ##
  def snapshot(self):
    entries = {}
    for path in sorted(self.root.rglob("*")):
      info = os.lstat(path)
      entries[str(path.relative_to(self.root))] = (
        stat.S_IFMT(info.st_mode),
        info.st_ino,
        info.st_size,
        info.st_mtime_ns,
      )
    return entries

  ##
  ## >>=================== the recovery, end to end ===================>>
  ##

  def test_the_same_command_run_again_finishes_the_move(self):
    from backend.src.service.recording_orphan_cli import EXIT_OK

    inventory, source, relative = self.arrange_interrupted()
    before = self.snapshot()
    record_bytes = self.only_record().read_bytes()
    media_identity = os.stat(self.only_media())

    ##
    ## The missing commit has to actually happen, and on the source's own
    ## parent - not on some other directory that would satisfy a call counter.
    ##
    parent_inode = os.stat(source.parent).st_ino
    committed_parents = []
    original_fsync = os.fsync

    def watching_fsync(descriptor):
      try:
        committed_parents.append(os.fstat(descriptor).st_ino)
      except OSError:
        pass
      return original_fsync(descriptor)

    ##
    ## Nothing may be linked, renamed or created this time round.
    ##
    original_link, original_rename = os.link, os.rename
    forbidden = []
    os.link = lambda *a, **k: forbidden.append("link")
    os.rename = lambda *a, **k: forbidden.append("rename")
    os.fsync = watching_fsync
    try:
      code, printed = self.cli(inventory, "quarantine", relative, "--confirm")
    finally:
      os.fsync, os.link, os.rename = original_fsync, original_link, original_rename

    self.assertEqual(EXIT_OK, code, printed)
    self.assertEqual([], forbidden, "the retry created or moved something")
    self.assertIn(
      parent_inode,
      committed_parents,
      "the missing source-parent commit was never performed",
    )

    ##
    ## Nothing on disk changed: not the media, not the record, not one extra
    ## file. A commit is the only thing this was allowed to do.
    ##
    self.assertEqual(before, self.snapshot())
    self.assertEqual(record_bytes, self.only_record().read_bytes())
    self.assertEqual(media_identity.st_ino, os.stat(self.only_media()).st_ino)
    self.assertFalse(source.exists())

    ##
    ## And it says nothing an operator should not paste into a ticket.
    ##
    self.assertNotIn(str(self.root), printed)
    self.assertNotIn("Traceback", printed)
    self.assertNotIn("OSError", printed)

  ##
  ## The recovery writes no row and infers no owner, so it has no reason to ask
  ## the claim authorities anything - and a repository that refuses every
  ## question must not change its answer.
  ##
  ## Driven against the service rather than the command: the CLI still has to
  ## scan first to find out whether the path is an ordinary candidate, and that
  ## scan legitimately needs the database. What is being proved here is that
  ## the recovery itself does not.
  ##
  def test_the_recovery_itself_never_consults_the_claim_authorities(self):
    inventory, source, relative = self.arrange_interrupted()

    self.references.error = RuntimeError("the database is down")
    outcome = inventory.complete_quarantine(relative)

    self.assertIsNotNone(outcome)
    self.assertTrue(outcome.quarantined)
    self.assertEqual(relative, outcome.relative_path)
    self.assertFalse(source.exists())

  ##
  ## >>================== and everything that must refuse ==================>>
  ##
  ## The recovery's whole risk is that "the source is missing" is the easiest
  ## condition in the world to satisfy - somebody deleting a recording by hand
  ## satisfies it. So each case below removes exactly one piece of the proof
  ## and requires the answer to stop being success.
  ##

  def assert_refuses(self, inventory, relative, why):
    from backend.src.service.recording_orphan_cli import EXIT_OK

    code, printed = self.cli(inventory, "quarantine", relative, "--confirm")
    self.assertNotEqual(EXIT_OK, code, "{}: {}".format(why, printed))
    self.assertNotIn(str(self.root), printed)
    self.assertNotIn("Traceback", printed)
    return code, printed

  def test_a_corrupt_record_refuses_to_finish_the_move(self):
    inventory, unused_source, relative = self.arrange_interrupted()
    self.only_record().write_bytes(b'{"schema_version":1,"sou')

    self.assert_refuses(inventory, relative, "a corrupt record was accepted")

  def test_a_record_describing_a_different_size_refuses(self):
    inventory, unused_source, relative = self.arrange_interrupted()
    record = self.only_record()
    payload = json.loads(record.read_text(encoding="utf-8"))
    payload["size"] = payload["size"] + 1
    record.write_text(json.dumps(payload), encoding="utf-8")

    self.assert_refuses(inventory, relative, "a size mismatch was accepted")

  def test_a_record_describing_a_different_mtime_refuses(self):
    inventory, unused_source, relative = self.arrange_interrupted()
    record = self.only_record()
    payload = json.loads(record.read_text(encoding="utf-8"))
    payload["mtime_ns"] = payload["mtime_ns"] + 1
    record.write_text(json.dumps(payload), encoding="utf-8")

    self.assert_refuses(inventory, relative, "an mtime mismatch was accepted")

  def test_a_record_naming_a_different_source_path_refuses(self):
    inventory, unused_source, relative = self.arrange_interrupted()
    record = self.only_record()
    payload = json.loads(record.read_text(encoding="utf-8"))
    payload["source_relative_path"] = "douyin/live/somebody-else/other.flv"
    record.write_text(json.dumps(payload), encoding="utf-8")

    self.assert_refuses(inventory, relative, "a foreign record was accepted")

  ##
  ## Half a quarantine is not a quarantine, and the refusal has to be a
  ## *decision* rather than a rescue.
  ##
  ## Both halves are checked explicitly before anything tries to read identity
  ## out of them. Without that check the code still refuses - but it refuses
  ## because it crashed on a record that is not there, and "the system happened
  ## to fall over safely" is not the same guarantee as "the system checked".
  ## The cause chain is what tells them apart: a decided refusal has none.
  ##
  def assert_decided_refusal(self, inventory, relative, why):
    from backend.src.service.recording_orphan import OrphanQuarantineRefused

    with self.assertRaises(OrphanQuarantineRefused) as caught:
      inventory.complete_quarantine(relative)
    self.assertIsNone(
      caught.exception.__cause__,
      "{}: the refusal was rescued from {!r} rather than decided".format(
        why, caught.exception.__cause__
      ),
    )
    return caught.exception

  def test_a_missing_record_refuses_even_though_the_media_is_there(self):
    inventory, source, relative = self.arrange_interrupted()
    self.only_record().unlink()

    self.assert_refuses(inventory, relative, "media without a record was accepted")
    self.assert_decided_refusal(inventory, relative, "a missing record")
    self.assertFalse(source.exists())

  def test_missing_quarantine_media_refuses_even_though_a_record_is_there(self):
    inventory, unused_source, relative = self.arrange_interrupted()
    self.only_media().unlink()

    self.assert_refuses(inventory, relative, "a record without media was accepted")
    self.assert_decided_refusal(inventory, relative, "missing media")

  def test_quarantine_media_replaced_by_a_symlink_refuses(self):
    inventory, unused_source, relative = self.arrange_interrupted()
    media = self.only_media()
    identity = os.stat(media)

    ##
    ## Deliberately indistinguishable by identity: same bytes, same size, same
    ## modification time to the nanosecond. Nothing the record stores can tell
    ## these apart, so the only thing that can refuse it is the type guard -
    ## which is exactly what this pins.
    ##
    elsewhere = self.root / "planted.flv"
    elsewhere.write_bytes(media.read_bytes())
    os.utime(elsewhere, ns=(identity.st_mtime_ns, identity.st_mtime_ns))
    media.unlink()
    os.symlink(elsewhere, media)

    self.assert_refuses(inventory, relative, "a symlinked media was accepted")

  def test_quarantine_media_replaced_by_a_different_file_refuses(self):
    inventory, unused_source, relative = self.arrange_interrupted()
    media = self.only_media()
    media.unlink()
    media.write_bytes(b"a different broadcast entirely")

    self.assert_refuses(inventory, relative, "substituted media was accepted")

  def test_a_source_parent_replaced_by_a_symlink_refuses(self):
    inventory, source, relative = self.arrange_interrupted()
    parent = source.parent
    elsewhere = self.root / "douyin" / "live" / "elsewhere"
    elsewhere.mkdir(parents=True, exist_ok=True)
    parent.rmdir()
    os.symlink(elsewhere, parent)

    self.assert_refuses(inventory, relative, "a symlinked parent was accepted")

  ##
  ## A path nobody ever quarantined. The old message, unchanged: the recovery
  ## must not turn "there is nothing here" into an answer of its own.
  ##
  def test_a_path_that_was_never_quarantined_still_reports_no_candidate(self):
    from backend.src.service.recording_orphan_cli import EXIT_REFUSED

    inventory = self.inventory()
    self.orphan()

    code, printed = self.cli(
      inventory, "quarantine", "douyin/live/nobody/never.flv", "--confirm"
    )

    self.assertEqual(EXIT_REFUSED, code)
    self.assertIn("no current orphan candidate names that path", printed)

  ##
  ## A directory that really exists, and a name in it that never did.
  ##
  ## The earlier "never quarantined" case stops at a missing parent directory,
  ## which is the easy half. This one gets all the way to the quarantine lookup
  ## with a real parent open, so the only thing left to refuse on is the
  ## absence of any quarantined media or record - the exact condition that
  ## would otherwise let "the source is missing" mean "the move must have
  ## worked".
  ##
  def test_a_never_quarantined_name_in_a_real_directory_reports_no_candidate(self):
    from backend.src.service.recording_orphan_cli import EXIT_REFUSED

    inventory, unused_source, unused_relative = self.arrange_interrupted()

    ##
    ## Same directory as the interrupted move, so the walk succeeds and the
    ## source name is genuinely absent.
    ##
    never = "douyin/live/broadcaster/never-existed.flv"
    self.assertFalse((self.root / never).exists())

    code, printed = self.cli(inventory, "quarantine", never, "--confirm")

    self.assertEqual(EXIT_REFUSED, code, printed)
    self.assertIn("no current orphan candidate names that path", printed)

  ##
  ## The source is back and something else claims it, so the scan skips it and
  ## the recovery is reached with the pathname present.
  ##
  ## This is the case where "the source is missing" being merely *assumed*
  ## rather than checked would commit a directory and report a move that never
  ## finished - with the original still sitting there.
  ##
  def test_a_present_but_unscanned_source_is_never_treated_as_finished(self):
    from backend.src.service.recording_orphan_cli import EXIT_OK

    inventory, source, relative = self.arrange_interrupted()

    ##
    ## Back under its own name, as the very inode that is in quarantine.
    ##
    os.link(self.only_media(), source)
    ##
    ## And claimed, so no scan will offer it as a candidate.
    ##
    self.references.paths = [str(source)]

    code, printed = self.cli(inventory, "quarantine", relative, "--confirm")

    self.assertNotEqual(EXIT_OK, code, printed)
    self.assertTrue(
      source.exists(), "the source is still there and must not be written off"
    )

  ##
  ## The commit failing a second time. Still recoverable, still not success.
  ##
  def test_a_second_failing_commit_stays_incomplete(self):
    from backend.src.service.recording_orphan_cli import EXIT_INCOMPLETE

    inventory, unused_source, relative = self.arrange_interrupted()

    original_fsync = os.fsync
    os.fsync = lambda descriptor: (_ for _ in ()).throw(
      OSError(5, "input/output error")
    )
    try:
      code, printed = self.cli(inventory, "quarantine", relative, "--confirm")
    finally:
      os.fsync = original_fsync

    self.assertEqual(EXIT_INCOMPLETE, code, printed)
    self.assertNotIn(str(self.root), printed)

    ##
    ## And it is still recoverable afterwards.
    ##
    from backend.src.service.recording_orphan_cli import EXIT_OK

    code, printed = self.cli(inventory, "quarantine", relative, "--confirm")
    self.assertEqual(EXIT_OK, code, printed)

  ##
  ## >>=========== the source coming back, which is not recovery ===========>>
  ##

  def test_a_source_that_reappears_as_the_same_inode_completes_normally(self):
    from backend.src.service.recording_orphan_cli import EXIT_OK

    inventory, source, relative = self.arrange_interrupted()
    ##
    ## Exactly what a crash before the unlink was committed can leave: the name
    ## back, pointing at the very inode already in quarantine.
    ##
    os.link(self.only_media(), source)

    code, printed = self.cli(inventory, "quarantine", relative, "--confirm")

    self.assertEqual(EXIT_OK, code, printed)
    self.assertFalse(source.exists())
    self.assertEqual(1, len(list(self.quarantine_root().glob("*.json"))))

  def test_a_source_that_reappears_as_a_different_inode_is_refused(self):
    from backend.src.service.recording_orphan_cli import EXIT_OK

    inventory, source, relative = self.arrange_interrupted()
    source.write_bytes(b"a completely different broadcast")

    code, printed = self.cli(inventory, "quarantine", relative, "--confirm")

    self.assertNotEqual(EXIT_OK, code, printed)
    self.assertTrue(source.exists(), "a different file must not be moved")


##
## The recovery's forbidden powers, read off its source.
##
## Requirements that are about what a function must *not* do are badly served by
## behavioural tests alone: a test proves today's call did not write a row, and
## says nothing about the branch somebody adds next month. These read the
## function instead.
##
class QuarantineRecoveryHasNoForbiddenPowersTest(unittest.TestCase):
  def recovery_source(self):
    import ast
    from pathlib import Path as _Path

    from backend.src.service import recording_orphan as module

    tree = ast.parse(_Path(module.__file__).read_text(encoding="utf-8"))
    return next(
      node for node in ast.walk(tree)
      if isinstance(node, ast.FunctionDef)
      and node.name == "_complete_quarantine_attempt"
    )

  def test_it_never_reaches_a_repository_a_journal_or_an_owner(self):
    import ast

    forbidden = []
    for node in ast.walk(self.recovery_source()):
      if isinstance(node, ast.Attribute) and node.attr in (
        "_references", "_journal", "referenced_output_paths", "link_post",
      ):
        forbidden.append(node.attr)
    self.assertEqual(
      [],
      forbidden,
      "the recovery must write no row and infer no owner: {}".format(forbidden),
    )

  def test_it_never_creates_links_renames_or_writes(self):
    import ast

    ##
    ## A commit is not a write. ``fsync`` is the only durable thing this may do,
    ## so every ``os`` call that could create, replace or move a name is banned
    ## outright rather than merely unused.
    ##
    banned = {
      "link", "rename", "replace", "symlink", "mkdir", "makedirs",
      "write", "truncate", "remove", "unlink", "rmdir", "chmod", "utime",
    }
    offenders = []
    for node in ast.walk(self.recovery_source()):
      if not isinstance(node, ast.Call):
        continue
      function = node.func
      if (
        isinstance(function, ast.Attribute)
        and isinstance(function.value, ast.Name)
        and function.value.id == "os"
        and function.attr in banned
      ):
        offenders.append(function.attr)
    self.assertEqual(
      [], offenders, "the recovery mutates storage: {}".format(offenders)
    )
