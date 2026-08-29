##
## Crash durability for a published MP4.
##
## Phase 10F established that publication cannot *clobber*: the final name is
## taken with a hard link, which refuses rather than overwrites.  That is a
## statement about the filesystem namespace as this process currently sees it,
## and it is not the same claim as "this recording survives the power going
## out".
##
## Two things are missing from that weaker claim, and this file pins both:
##
##   - ``os.link`` returning success means a directory entry exists in the
##     kernel's view.  The bytes ffmpeg wrote may still be in page cache, and
##     the new directory entry may still be in an uncommitted metadata journal.
##   - ``fsync`` on the file commits that file's data and inode.  It says
##     nothing about the *name*: a directory entry lives in the parent
##     directory, so the parent is what has to be synced for the name to exist
##     after a crash.
##
## The invariant everything here defends: the captured ``.ts`` is not deleted
## until the MP4 is durable under both, so a crash at any point *after the
## source durability barrier* leaves at least one durable copy of the
## recording.
##
## That qualifier is load-bearing.  ``HlsRecorder`` finishes an attempt with
## ``os.replace`` and never fsyncs the ``.ts``, so the recording arrives here
## with its durability unknown.  This stage commits it first and refuses to
## start otherwise - but a power loss *before* that barrier completes is the
## capture stage's exposure, not something normalization can promise away.
##
from pathlib import Path
import errno
import os
import stat
import tempfile
import unittest
from unittest import mock

from backend.src.platform.douyin.hls_mp4_normalizer import HlsMp4Normalizer


class SyncHelperRealFilesystemTest(unittest.TestCase):
  """The helpers run against a real filesystem, not a stand-in.

  Mocks can prove the *order* these are called in, but only a real directory
  file descriptor can prove the runtime filesystem lets this process open and
  fsync one at all.  If that is not possible here, publication must fail
  closed - so it has to be discovered, not assumed.
  """

  def test_a_real_directory_can_be_opened_and_fsynced(self):
    with tempfile.TemporaryDirectory() as directory:
      HlsMp4Normalizer()._sync_directory(Path(directory))

  def test_a_real_file_can_be_fsynced(self):
    with tempfile.TemporaryDirectory() as directory:
      target = Path(directory) / "live.mp4"
      target.write_bytes(b"recording-bytes")

      HlsMp4Normalizer()._sync_file(target)

  def test_the_full_durable_publication_primitive_works_here(self):
    ##
    ## The exact sequence publication depends on, end to end, with nothing
    ## faked: write, fsync the file, hard-link it into place, fsync the parent.
    ## This is the smallest thing that would break on a filesystem that cannot
    ## support the durability contract.
    ##
    with tempfile.TemporaryDirectory() as directory:
      normalizer = HlsMp4Normalizer()
      temporary = Path(directory) / ".live.remux-abc.part.mp4"
      final = Path(directory) / "live.mp4"
      temporary.write_bytes(b"recording-bytes")

      normalizer._sync_file(temporary)
      os.link(temporary, final)
      normalizer._sync_directory(final.parent)

      self.assertTrue(final.is_file())
      self.assertEqual(b"recording-bytes", final.read_bytes())
      self.assertEqual(temporary.stat().st_ino, final.stat().st_ino)

  def test_syncing_a_missing_directory_fails_rather_than_passing_quietly(self):
    ##
    ## Fail closed.  A durability step that cannot run must not report success:
    ## the caller decides to keep the .ts on exactly this signal.
    ##
    with tempfile.TemporaryDirectory() as directory:
      with self.assertRaises(OSError):
        HlsMp4Normalizer()._sync_directory(Path(directory) / "absent")

  def test_syncing_a_missing_file_fails_rather_than_passing_quietly(self):
    with tempfile.TemporaryDirectory() as directory:
      with self.assertRaises(OSError):
        HlsMp4Normalizer()._sync_file(Path(directory) / "absent.mp4")


class SyncFileValidationTest(unittest.TestCase):
  """What ``_sync_file`` refuses to call a publishable recording."""

  def test_an_empty_file_is_refused(self):
    ##
    ## Re-checked here rather than trusted from the earlier stat: this is the
    ## descriptor that is about to be committed to stable storage, so it is the
    ## one worth asking about.
    ##
    with tempfile.TemporaryDirectory() as directory:
      target = Path(directory) / "live.mp4"
      target.write_bytes(b"")

      with self.assertRaises(OSError):
        HlsMp4Normalizer()._sync_file(target)

  def test_a_directory_is_not_a_publishable_file(self):
    with tempfile.TemporaryDirectory() as directory:
      with self.assertRaises(OSError):
        HlsMp4Normalizer()._sync_file(Path(directory))

  @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "requires O_NOFOLLOW")
  def test_a_symlink_is_not_followed(self):
    ##
    ## The temporary name is this process's own, but the durability step opens
    ## it a second time, after ffmpeg has exited.  Refusing to follow a link
    ## keeps that second open from being redirected at something else.
    ##
    with tempfile.TemporaryDirectory() as directory:
      real = Path(directory) / "elsewhere.mp4"
      real.write_bytes(b"not-this-recording")
      link = Path(directory) / ".live.remux-abc.part.mp4"
      link.symlink_to(real)

      with self.assertRaises(OSError) as caught:
        HlsMp4Normalizer()._sync_file(link)

      self.assertEqual(errno.ELOOP, caught.exception.errno)

  def test_the_descriptor_is_closed_even_when_validation_refuses(self):
    ##
    ## Normalization runs once per finished recording in a long-lived server.
    ## A descriptor leaked on the refusal path would accumulate for exactly the
    ## recordings that already went wrong.
    ##
    if not os.path.isdir("/proc/self/fd"):
      self.skipTest("requires /proc to count descriptors")
    with tempfile.TemporaryDirectory() as directory:
      target = Path(directory) / "live.mp4"
      target.write_bytes(b"")
      normalizer = HlsMp4Normalizer()

      before = len(os.listdir("/proc/self/fd"))
      for _ in range(20):
        with self.assertRaises(OSError):
          normalizer._sync_file(target)
      after = len(os.listdir("/proc/self/fd"))

      self.assertEqual(before, after)

  def test_the_descriptor_is_closed_on_the_success_path(self):
    if not os.path.isdir("/proc/self/fd"):
      self.skipTest("requires /proc to count descriptors")
    with tempfile.TemporaryDirectory() as directory:
      target = Path(directory) / "live.mp4"
      target.write_bytes(b"recording-bytes")
      normalizer = HlsMp4Normalizer()

      before = len(os.listdir("/proc/self/fd"))
      for _ in range(20):
        normalizer._sync_file(target)
        normalizer._sync_directory(Path(directory))
      after = len(os.listdir("/proc/self/fd"))

      self.assertEqual(before, after)


##
## An operation log for the publication sequence.
##
## Durability is entirely a claim about *order*: the same set of calls in a
## different order is the difference between "a crash leaves a recording" and
## "a crash leaves nothing".  Asserting each step happened would pass on an
## implementation that deleted the .ts first, so these tests assert the
## sequence instead.
##
class _Recorder:
  def __init__(self):
    self.entries = []

  def note(self, entry):
    self.entries.append(entry)


class _DurableProcess:
  pid = 4321

  def poll(self):
    return 0

  def wait(self, timeout=None):
    return 0


def instrument(normalizer, log, source, temporary_holder, *, fail=None):
  """Wrap the leaf I/O of a normalizer so the order it drives them is visible.

  Only the leaves are replaced.  The orchestration under test - which step
  follows which, and what happens when one refuses - is the real code.

  Each fsync is named by *what* it commits rather than by which function ran,
  because the same two helpers are used for the source barrier, the
  publication and the cleanup, and the whole point of these tests is telling
  those apart.
  """
  fail = fail or {}
  real_sync_file = normalizer._sync_file
  real_sync_directory = normalizer._sync_directory
  real_link = os.link

  def sync_file(path):
    if Path(path) == source:
      log.note("fsync-source-file")
      key = "sync_source_file"
    else:
      log.note("fsync-temp-file")
      key = "sync_temp_file"
    if key in fail:
      raise fail[key]
    return real_sync_file(path)

  ##
  ## Directory syncs are told apart by ordinal: the source barrier commits the
  ## directory first, publication second, cleanup (or a rollback) third.
  ##
  DIRECTORY_STAGES = (
    ("fsync-source-dir", "sync_source_directory"),
    ("fsync-publish-dir", "sync_directory_publish"),
    ("fsync-cleanup-dir", "sync_directory_cleanup"),
  )

  def sync_directory(path):
    seen = len([e for e in log.entries if e.startswith("fsync-") and e.endswith("-dir")])
    name, key = DIRECTORY_STAGES[min(seen, len(DIRECTORY_STAGES) - 1)]
    log.note(name)
    if key in fail:
      raise fail[key]
    return real_sync_directory(path)

  def link(a, b):
    log.note("link")
    if "link" in fail:
      raise fail["link"]
    return real_link(a, b)

  def process_factory(command, **kwargs):
    log.note("ffmpeg")
    written = Path(command[-1])
    temporary_holder.append(written)
    written.write_bytes(b"remuxed-mp4-bytes")
    return _DurableProcess()

  normalizer._sync_file = sync_file
  normalizer._sync_directory = sync_directory
  normalizer.process_factory = process_factory

  real_unlink = Path.unlink

  def unlink(self, *args, **kwargs):
    if self == source:
      log.note("unlink-ts")
      if "unlink_ts" in fail:
        raise fail["unlink_ts"]
    elif "remux" in self.name:
      log.note("unlink-temp")
      if "unlink_temp" in fail:
        raise fail["unlink_temp"]
    else:
      log.note("unlink-final")
      if "unlink_final" in fail:
        raise fail["unlink_final"]
    return real_unlink(self, *args, **kwargs)

  return mock.patch.multiple(
    "backend.src.platform.douyin.hls_mp4_normalizer.os",
    link=link,
  ), mock.patch.object(Path, "unlink", unlink)


class DurablePublicationOrderingTest(unittest.TestCase):
  def run_normalize(self, *, fail=None):
    log = _Recorder()
    holder = []
    directory = tempfile.TemporaryDirectory()
    source = Path(directory.name) / "live.ts"
    source.write_bytes(b"captured-ts-bytes")
    normalizer = HlsMp4Normalizer("/test/ffmpeg", token_factory=lambda: "abc")
    link_patch, unlink_patch = instrument(
      normalizer, log, source, holder, fail=fail
    )
    with link_patch, unlink_patch:
      result = normalizer.normalize(source)
    return log, source, result, directory

  def test_a_successful_publication_follows_the_durable_order(self):
    ##
    ## Every adjacent pair here is load-bearing:
    ##   ffmpeg      -> fsync-file : nothing to commit before ffmpeg exits
    ##   fsync-file  -> link       : the name must not reach unsynced bytes
    ##   link        -> fsync-dir  : the new name is itself only in a journal
    ##   fsync-dir   -> unlink-ts  : the .ts may only go once MP4 is durable
    ##
    log, source, result, directory = self.run_normalize()
    with directory:
      self.assertEqual(
        [
          "fsync-source-file",
          "fsync-source-dir",
          "ffmpeg",
          "fsync-temp-file",
          "link",
          "fsync-publish-dir",
          "unlink-temp",
          "unlink-ts",
          "fsync-cleanup-dir",
        ],
        log.entries,
      )
      self.assertEqual(source.with_suffix(".mp4"), result)
      self.assertTrue(result.is_file())
      self.assertFalse(source.exists())

  def test_the_source_is_never_removed_before_the_publish_directory_fsync(self):
    log, source, result, directory = self.run_normalize()
    with directory:
      self.assertIn("unlink-ts", log.entries)
      self.assertLess(
        log.entries.index("fsync-publish-dir"),
        log.entries.index("unlink-ts"),
      )

  def test_the_final_name_is_never_created_before_the_file_is_synced(self):
    log, source, result, directory = self.run_normalize()
    with directory:
      self.assertLess(
        log.entries.index("fsync-temp-file"),
        log.entries.index("link"),
      )


class FileSyncFailureTest(unittest.TestCase):
  def test_a_temp_fsync_failure_publishes_nothing_and_keeps_the_ts(self):
    ##
    ## Crash point A. The bytes are not known to be on the device, so no name
    ## may be attached to them.
    ##
    log = _Recorder()
    holder = []
    with tempfile.TemporaryDirectory() as directory:
      source = Path(directory) / "live.ts"
      source.write_bytes(b"captured-ts-bytes")
      normalizer = HlsMp4Normalizer("/test/ffmpeg", token_factory=lambda: "abc")
      link_patch, unlink_patch = instrument(
        normalizer,
        log,
        source,
        holder,
        fail={"sync_temp_file": OSError(errno.EIO, "device failure")},
      )
      with link_patch, unlink_patch:
        result = normalizer.normalize(source)

      self.assertEqual(source, result)
      self.assertNotIn("link", log.entries)
      self.assertNotIn("unlink-ts", log.entries)
      self.assertTrue(source.is_file())
      self.assertEqual(b"captured-ts-bytes", source.read_bytes())
      self.assertFalse((Path(directory) / "live.mp4").exists())
      self.assertEqual(
        ["live.ts"],
        sorted(path.name for path in Path(directory).iterdir()),
      )


class SourceDurabilityBarrierTest(unittest.TestCase):
  """The captured ``.ts`` must be durable before anything may replace it.

  Everything downstream is built on "a crash here still leaves the .ts", and
  that sentence is only true if the .ts is on stable storage.  It is not, by
  the time it arrives: ``HlsRecorder`` finishes an attempt with
  ``os.replace(attempt, destination)`` and never fsyncs either the inode or
  the parent directory, so the recording exists in the kernel's view and may
  exist nowhere else.

  Publishing an MP4 on top of that would trade a recording whose durability is
  unknown for one whose durability is proven - and delete the former.  So the
  source is committed first, and normalization refuses to start if it cannot
  be.
  """

  def barrier_fails(self, **fail):
    log = _Recorder()
    holder = []
    directory = tempfile.TemporaryDirectory()
    source = Path(directory.name) / "live.ts"
    source.write_bytes(b"captured-ts-bytes")
    normalizer = HlsMp4Normalizer("/test/ffmpeg", token_factory=lambda: "abc")
    link_patch, unlink_patch = instrument(
      normalizer, log, source, holder, fail=fail
    )
    with link_patch, unlink_patch:
      result = normalizer.normalize(source)
    return log, source, result, directory

  def test_the_source_is_committed_before_ffmpeg_is_started(self):
    log = _Recorder()
    holder = []
    directory = tempfile.TemporaryDirectory()
    source = Path(directory.name) / "live.ts"
    source.write_bytes(b"captured-ts-bytes")
    normalizer = HlsMp4Normalizer("/test/ffmpeg", token_factory=lambda: "abc")
    link_patch, unlink_patch = instrument(normalizer, log, source, holder)
    with link_patch, unlink_patch:
      normalizer.normalize(source)
    with directory:
      self.assertLess(
        log.entries.index("fsync-source-file"),
        log.entries.index("ffmpeg"),
      )
      self.assertLess(
        log.entries.index("fsync-source-dir"),
        log.entries.index("ffmpeg"),
      )

  def test_a_source_that_cannot_be_committed_never_starts_a_remux(self):
    ##
    ## Refusing to start is the whole point.  Running the remux anyway would
    ## walk towards deleting a .ts this code cannot prove exists on disk.
    ##
    log, source, result, directory = self.barrier_fails(
      sync_source_file=OSError(errno.EIO, "device failure")
    )
    with directory:
      self.assertEqual(source, result)
      self.assertNotIn("ffmpeg", log.entries)
      self.assertNotIn("link", log.entries)
      self.assertNotIn("unlink-ts", log.entries)
      self.assertTrue(source.is_file())
      self.assertEqual(b"captured-ts-bytes", source.read_bytes())
      self.assertEqual(
        ["live.ts"],
        sorted(path.name for path in Path(directory.name).iterdir()),
      )

  def test_a_source_directory_that_cannot_be_committed_never_starts_a_remux(self):
    ##
    ## The file's bytes being durable is not enough: ``os.replace`` created the
    ## .ts name, and an uncommitted rename can leave the recording reachable
    ## under no name at all - or under the empty placeholder the name was
    ## reserved with.
    ##
    log, source, result, directory = self.barrier_fails(
      sync_source_directory=OSError(errno.EIO, "journal failure")
    )
    with directory:
      self.assertEqual(source, result)
      self.assertIn("fsync-source-file", log.entries)
      self.assertNotIn("ffmpeg", log.entries)
      self.assertNotIn("link", log.entries)
      self.assertNotIn("unlink-ts", log.entries)
      self.assertTrue(source.is_file())
      self.assertEqual(
        ["live.ts"],
        sorted(path.name for path in Path(directory.name).iterdir()),
      )

  def test_a_refused_barrier_is_still_a_successful_recording(self):
    ##
    ## Nothing was lost - the broadcast was captured and is on disk. Only the
    ## container improvement was declined, which is the same answer every other
    ## normalization failure gives.
    ##
    log, source, result, directory = self.barrier_fails(
      sync_source_file=OSError(errno.EIO, "device failure")
    )
    with directory:
      self.assertEqual(source, result)
      self.assertEqual(".ts", result.suffix)


class PublishDirectoryFsyncFailureTest(unittest.TestCase):
  """Crash point C: the link exists, but its name is not on stable storage.

  This is the case that makes rollback necessary at all.  A name that only
  exists in an uncommitted journal is not a published recording, so the .ts
  cannot be released - and the half-published name must not be left behind
  claiming to be one.
  """

  def publish_fails(self, *, unlink_final=None):
    log = _Recorder()
    holder = []
    directory = tempfile.TemporaryDirectory()
    source = Path(directory.name) / "live.ts"
    source.write_bytes(b"captured-ts-bytes")
    fail = {"sync_directory_publish": OSError(errno.EIO, "journal failure")}
    if unlink_final is not None:
      fail["unlink_final"] = unlink_final
    normalizer = HlsMp4Normalizer("/test/ffmpeg", token_factory=lambda: "abc")
    link_patch, unlink_patch = instrument(
      normalizer, log, source, holder, fail=fail
    )
    with link_patch, unlink_patch:
      result = normalizer.normalize(source)
    return log, source, result, directory

  def test_the_source_survives_a_publish_that_could_not_be_committed(self):
    log, source, result, directory = self.publish_fails()
    with directory:
      self.assertEqual(source, result)
      self.assertTrue(source.is_file())
      self.assertEqual(b"captured-ts-bytes", source.read_bytes())

  def test_the_uncommitted_final_link_is_rolled_back(self):
    log, source, result, directory = self.publish_fails()
    with directory:
      ##
      ## This attempt created the name, so this attempt takes it away.  Leaving
      ## it would advertise a durable recording that is not one.
      ##
      self.assertIn("unlink-final", log.entries)
      self.assertFalse((Path(directory.name) / "live.mp4").exists())

  def test_the_source_is_never_unlinked_when_publication_failed(self):
    log, source, result, directory = self.publish_fails()
    with directory:
      self.assertNotIn("unlink-ts", log.entries)

  def test_the_rollback_is_itself_committed(self):
    ##
    ## Removing the link is another directory-entry change, so it needs the
    ## same treatment the publication would have had.
    ##
    log, source, result, directory = self.publish_fails()
    with directory:
      ##
      ## Withdrawing the name is itself a directory-entry change, so it gets
      ## the same commit the publication would have had.
      ##
      self.assertIn("unlink-final", log.entries)
      self.assertIn("fsync-cleanup-dir", log.entries)
      self.assertLess(
        log.entries.index("unlink-final"),
        log.entries.index("fsync-cleanup-dir"),
      )

  def test_only_the_ts_is_left_behind(self):
    log, source, result, directory = self.publish_fails()
    with directory:
      self.assertEqual(
        ["live.ts"],
        sorted(path.name for path in Path(directory.name).iterdir()),
      )

  def test_a_rollback_that_also_fails_still_keeps_the_recording(self):
    ##
    ## Worst case: the name could not be committed and could not be withdrawn.
    ## That may leave a .ts and an .mp4 side by side, which is untidy - and
    ## strictly better than deleting the only copy of a broadcast. Duplicate
    ## beats data loss.
    ##
    log, source, result, directory = self.publish_fails(
      unlink_final=OSError(errno.EIO, "cannot unlink")
    )
    with directory:
      self.assertEqual(source, result)
      self.assertTrue(source.is_file())
      self.assertEqual(b"captured-ts-bytes", source.read_bytes())
      self.assertNotIn("unlink-ts", log.entries)


class PreexistingFinalTest(unittest.TestCase):
  def test_a_final_this_attempt_did_not_create_is_never_rolled_back(self):
    ##
    ## ``os.link`` failing with EEXIST means this attempt never took the name.
    ## The file sitting there belongs to another recording, and the rollback
    ## path must not be able to reach it.
    ##
    log = _Recorder()
    holder = []
    with tempfile.TemporaryDirectory() as directory:
      source = Path(directory) / "live.ts"
      source.write_bytes(b"captured-ts-bytes")
      rival = Path(directory) / "live.mp4"
      rival.write_bytes(b"another-recording")
      normalizer = HlsMp4Normalizer("/test/ffmpeg", token_factory=lambda: "abc")
      link_patch, unlink_patch = instrument(
        normalizer,
        log,
        source,
        holder,
        fail={"link": FileExistsError(errno.EEXIST, "taken")},
      )
      with link_patch, unlink_patch:
        result = normalizer.normalize(source)

      self.assertEqual(source, result)
      self.assertNotIn("unlink-final", log.entries)
      self.assertNotIn("unlink-ts", log.entries)
      self.assertEqual(b"another-recording", rival.read_bytes())
      self.assertTrue(source.is_file())
      self.assertEqual(
        ["live.mp4", "live.ts"],
        sorted(path.name for path in Path(directory).iterdir()),
      )


class CleanupAfterDurablePublicationTest(unittest.TestCase):
  """Once the MP4 is durable, nothing that follows can revoke the recording.

  Crash points D and E.  The bytes and the name are both committed before any
  of this runs, so every failure here is leftover housekeeping - never a reason
  to hand back the .ts, which may not even exist any more.
  """

  def cleanup_fails(self, **fail):
    log = _Recorder()
    holder = []
    directory = tempfile.TemporaryDirectory()
    source = Path(directory.name) / "live.ts"
    source.write_bytes(b"captured-ts-bytes")
    normalizer = HlsMp4Normalizer("/test/ffmpeg", token_factory=lambda: "abc")
    link_patch, unlink_patch = instrument(
      normalizer, log, source, holder, fail=fail
    )
    with link_patch, unlink_patch:
      result = normalizer.normalize(source)
    return log, source, result, directory

  def test_a_temp_that_will_not_unlink_does_not_hold_back_the_recording(self):
    ##
    ## The temporary is a second name for bytes the final name also holds, so
    ## a leftover is storage hygiene, not a damaged recording. The .ts is still
    ## released and the MP4 is still the answer.
    ##
    log, source, result, directory = self.cleanup_fails(
      unlink_temp=OSError(errno.EIO, "cannot unlink temp")
    )
    with directory:
      self.assertEqual(source.with_suffix(".mp4"), result)
      self.assertTrue(result.is_file())
      self.assertIn("unlink-ts", log.entries)
      self.assertFalse(source.exists())

  def test_a_ts_that_will_not_unlink_still_reports_the_durable_mp4(self):
    log, source, result, directory = self.cleanup_fails(
      unlink_ts=OSError(errno.EIO, "cannot unlink ts")
    )
    with directory:
      self.assertEqual(source.with_suffix(".mp4"), result)
      self.assertTrue(result.is_file())
      ##
      ## Orphaned, not authoritative. The recording is the MP4.
      ##
      self.assertTrue(source.is_file())

  def test_a_failed_cleanup_fsync_does_not_resurrect_the_ts(self):
    ##
    ## Crash point E. The MP4 was durable before the .ts was removed, so a
    ## cleanup that cannot be committed leaves a recording that is still
    ## correct - possibly beside a .ts that comes back. Inventing a .ts return
    ## value here would name a file this code just deleted.
    ##
    log, source, result, directory = self.cleanup_fails(
      sync_directory_cleanup=OSError(errno.EIO, "journal failure")
    )
    with directory:
      self.assertEqual(source.with_suffix(".mp4"), result)
      self.assertTrue(result.is_file())
      self.assertEqual(b"remuxed-mp4-bytes", result.read_bytes())

  def test_every_cleanup_failure_at_once_still_yields_the_mp4(self):
    log, source, result, directory = self.cleanup_fails(
      unlink_temp=OSError(errno.EIO, "a"),
      unlink_ts=OSError(errno.EIO, "b"),
      sync_directory_cleanup=OSError(errno.EIO, "c"),
    )
    with directory:
      self.assertEqual(source.with_suffix(".mp4"), result)
      self.assertTrue(result.is_file())


class CrashPointModelTest(unittest.TestCase):
  """What is on disk if the machine stops at each step.

  Not a simulation of power loss - it cannot be. This pins the code ordering
  that makes the reasoning valid, so that the claim in the docs and the claim
  in the code cannot drift apart.

  The guarantee starts at the source durability barrier, and not before it.
  ``HlsRecorder`` finishes with ``os.replace`` and never fsyncs the ``.ts``,
  so a power loss *before* the barrier completes is outside what this stage
  can promise - it is the capture stage's durability, not the normalization
  stage's. Naming that boundary is the point: an assertion covering the
  pre-barrier steps would claim more than the code establishes.
  """

  def survivors(self, *, stop_after):
    log = _Recorder()
    holder = []
    directory = tempfile.TemporaryDirectory()
    source = Path(directory.name) / "live.ts"
    source.write_bytes(b"captured-ts-bytes")

    class Stop(BaseException):
      pass

    fail = {stop_after: Stop()}
    normalizer = HlsMp4Normalizer("/test/ffmpeg", token_factory=lambda: "abc")
    link_patch, unlink_patch = instrument(
      normalizer, log, source, holder, fail=fail
    )
    with link_patch, unlink_patch:
      try:
        normalizer.normalize(source)
      except Stop:
        pass
    names = sorted(path.name for path in Path(directory.name).iterdir())
    directory.cleanup()
    return names

  def test_crash_point_a_before_the_file_is_synced_keeps_the_ts(self):
    self.assertIn("live.ts", self.survivors(stop_after="sync_temp_file"))

  def test_crash_point_b_after_file_sync_before_link_keeps_the_ts(self):
    names = self.survivors(stop_after="link")
    self.assertIn("live.ts", names)
    self.assertNotIn("live.mp4", names)

  def test_crash_point_c_after_link_before_commit_keeps_the_ts(self):
    ##
    ## The .mp4 name may or may not survive the crash - that is exactly what
    ## was not committed. What matters is that the .ts is still there, so the
    ## recording exists either way.
    ##
    self.assertIn(
      "live.ts", self.survivors(stop_after="sync_directory_publish")
    )

  def test_crash_point_d_after_the_publish_commit_has_a_durable_mp4(self):
    names = self.survivors(stop_after="unlink_temp")
    self.assertIn("live.mp4", names)
    self.assertIn("live.ts", names)

  def test_crash_point_e_after_the_ts_is_removed_has_a_durable_mp4(self):
    names = self.survivors(stop_after="sync_directory_cleanup")
    self.assertIn("live.mp4", names)
    self.assertNotIn("live.ts", names)

  def test_source_durability_barrier_precedes_remux(self):
    ##
    ## Stopping inside the barrier must stop everything: no ffmpeg, no
    ## temporary, no final name. The ``.ts`` is still the only copy, and this
    ## stage has not yet earned the right to replace it.
    ##
    ## What is deliberately *not* asserted here is that the ``.ts`` is durable.
    ## At these two points it is not known to be - that is precisely why the
    ## barrier exists and why nothing downstream may start.
    ##
    for stop_after in ("sync_source_file", "sync_source_directory"):
      with self.subTest(stop_after=stop_after):
        names = self.survivors(stop_after=stop_after)
        self.assertEqual(["live.ts"], names)

  def test_every_post_barrier_crash_point_retains_durable_media(self):
    ##
    ## The contract, stated over exactly the range it covers: once the source
    ## barrier has completed, there is no step at which neither a durable .ts
    ## nor a durable .mp4 is on disk.
    ##
    for stop_after in (
      "sync_temp_file",
      "link",
      "sync_directory_publish",
      "unlink_temp",
      "unlink_ts",
      "sync_directory_cleanup",
    ):
      with self.subTest(stop_after=stop_after):
        names = self.survivors(stop_after=stop_after)
        self.assertTrue(
          "live.ts" in names or "live.mp4" in names,
          "crash at {} left nothing: {}".format(stop_after, names),
        )


class CancellationCheckpointTest(unittest.TestCase):
  """Cancellation can stop a remux; it cannot un-publish a durable recording.

  There are exactly two checkpoints - the entry to ``normalize`` and the wait
  on ffmpeg - and both sit strictly before publication begins.  That placement
  is the design: once the file has been synced and the name committed, there is
  no correct way to answer "keep the .ts", because the .ts may already be gone
  and the MP4 is on stable storage.
  """

  def test_cancelling_before_the_remux_starts_keeps_the_ts(self):
    def process_factory(command, **kwargs):
      raise AssertionError("a cancelled normalizer must not spawn ffmpeg")

    with tempfile.TemporaryDirectory() as directory:
      source = Path(directory) / "live.ts"
      source.write_bytes(b"captured-ts-bytes")
      normalizer = HlsMp4Normalizer("/test/ffmpeg", process_factory)
      normalizer.cancel_all()

      result = normalizer.normalize(source)

      self.assertEqual(source, result)
      self.assertTrue(source.is_file())
      self.assertFalse((Path(directory) / "live.mp4").exists())

  def test_cancelling_during_the_remux_publishes_nothing(self):
    signals = []

    class RunningProcess:
      pid = 9876

      def poll(self):
        return None

      def wait(self, timeout=None):
        return -15

    box = {}

    def process_factory(command, **kwargs):
      Path(command[-1]).write_bytes(b"partial-mp4")
      return RunningProcess()

    with tempfile.TemporaryDirectory() as directory:
      source = Path(directory) / "live.ts"
      source.write_bytes(b"captured-ts-bytes")
      normalizer = HlsMp4Normalizer(
        "/test/ffmpeg",
        process_factory,
        sleeper=lambda seconds: box["n"].cancel_all(),
        group_signaler=lambda pid, number: signals.append((pid, number)),
      )
      box["n"] = normalizer

      result = normalizer.normalize(source)

      self.assertEqual(source, result)
      self.assertEqual([(9876, 15)], signals)
      self.assertEqual(
        ["live.ts"],
        sorted(path.name for path in Path(directory).iterdir()),
      )

  def test_cancelling_once_publication_has_begun_still_yields_the_mp4(self):
    ##
    ## Shutdown arrives after the file has been synced. Publication does not
    ## re-read the cancellation flag, so the durable MP4 is what gets reported -
    ## handing back a ``.ts`` that this code is about to delete would name a
    ## file that will not be there.
    ##
    log = _Recorder()
    holder = []
    with tempfile.TemporaryDirectory() as directory:
      source = Path(directory) / "live.ts"
      source.write_bytes(b"captured-ts-bytes")
      normalizer = HlsMp4Normalizer("/test/ffmpeg", token_factory=lambda: "abc")
      link_patch, unlink_patch = instrument(normalizer, log, source, holder)
      real_sync_file = normalizer._sync_file

      def sync_then_cancel(path):
        result = real_sync_file(path)
        ##
        ## Only once the temporary has been committed - the source barrier
        ## runs first, and cancelling there would simply decline to start.
        ##
        if Path(path) != source:
          normalizer.cancel_all()
        return result

      normalizer._sync_file = sync_then_cancel
      with link_patch, unlink_patch:
        result = normalizer.normalize(source)

      self.assertEqual(source.with_suffix(".mp4"), result)
      self.assertTrue(result.is_file())
      self.assertFalse(source.exists())

  def test_a_cancelled_normalizer_refuses_the_next_recording_before_publishing(self):
    ##
    ## The flag is sticky, which is right for shutdown: the recording that was
    ## mid-publish finishes, and the next one is not started.
    ##
    def process_factory(command, **kwargs):
      raise AssertionError("must not spawn ffmpeg after cancellation")

    with tempfile.TemporaryDirectory() as directory:
      normalizer = HlsMp4Normalizer("/test/ffmpeg", process_factory)
      normalizer.cancel_all()
      for name in ("first.ts", "second.ts"):
        source = Path(directory) / name
        source.write_bytes(b"captured-ts-bytes")

        self.assertEqual(source, normalizer.normalize(source))
        self.assertTrue(source.is_file())


if __name__ == "__main__":
  unittest.main()
