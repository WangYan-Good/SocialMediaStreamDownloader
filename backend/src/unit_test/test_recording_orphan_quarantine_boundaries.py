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
