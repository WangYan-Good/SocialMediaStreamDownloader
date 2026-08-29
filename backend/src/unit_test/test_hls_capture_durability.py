##
## Crash durability for a *finished* HLS capture.
##
## Phase 10G made MP4 publication crash durable, and established a barrier at
## the start of normalization because the ``.ts`` arrived with its durability
## unknown: ``HlsRecorder`` ended an attempt with ``os.replace`` and never
## fsynced anything, so a successful ``record()`` return meant "the kernel
## shows this file", not "this file survives a power cut".
##
## This closes that gap at its source.  ``record()`` may only report success
## once the final ``.ts`` is genuinely on stable storage, so no caller can ever
## observe a successful return paired with a non-durable recording.
##
## What is deliberately *not* claimed:
##
##   - durability during an active recording.  ffmpeg is writing; a crash
##     mid-broadcast loses whatever had not reached the device.
##   - durability of failed partial attempts.  Those are a different scope.
##
## The guarantee is exactly: a successful return implies a durable final TS.
##
from pathlib import Path
import errno
import os
import subprocess
import tempfile
import unittest
from unittest import mock

from backend.src.platform.douyin.hls_recorder import (
  HlsDurabilityError,
  HlsDownloadError,
  HlsRecorder,
)


class DurabilityErrorTypeTest(unittest.TestCase):
  def test_a_durability_failure_is_a_recording_failure(self):
    ##
    ## It has to be catchable by everything that already handles a failed HLS
    ## download, because to every caller that is what it is: the recording did
    ## not finish in a state worth reporting as success.
    ##
    self.assertTrue(issubclass(HlsDurabilityError, HlsDownloadError))


class CaptureSyncHelperRealFilesystemTest(unittest.TestCase):
  """The helpers run against a real filesystem, not a stand-in."""

  def test_a_real_attempt_file_can_be_fsynced(self):
    with tempfile.TemporaryDirectory() as directory:
      attempt = Path(directory) / ".live.ts.attempt-1.part"
      attempt.write_bytes(b"captured-media")

      HlsRecorder()._sync_file(attempt)

  def test_a_real_directory_can_be_opened_and_fsynced(self):
    with tempfile.TemporaryDirectory() as directory:
      HlsRecorder()._sync_directory(Path(directory))

  def test_an_empty_attempt_is_refused(self):
    ##
    ## Re-asked on the descriptor that is about to be committed rather than
    ## trusted from the earlier path stat, which is a different question about
    ## a different moment.
    ##
    with tempfile.TemporaryDirectory() as directory:
      attempt = Path(directory) / ".live.ts.attempt-1.part"
      attempt.write_bytes(b"")

      with self.assertRaises(OSError):
        HlsRecorder()._sync_file(attempt)

  def test_a_directory_is_not_a_capturable_attempt(self):
    with tempfile.TemporaryDirectory() as directory:
      with self.assertRaises(OSError):
        HlsRecorder()._sync_file(Path(directory))

  @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "requires O_NOFOLLOW")
  def test_a_symlinked_attempt_is_not_followed(self):
    with tempfile.TemporaryDirectory() as directory:
      real = Path(directory) / "elsewhere.ts"
      real.write_bytes(b"not-this-capture")
      link = Path(directory) / ".live.ts.attempt-1.part"
      link.symlink_to(real)

      with self.assertRaises(OSError) as caught:
        HlsRecorder()._sync_file(link)

      self.assertEqual(errno.ELOOP, caught.exception.errno)

  def test_missing_paths_fail_rather_than_passing_quietly(self):
    with tempfile.TemporaryDirectory() as directory:
      with self.assertRaises(OSError):
        HlsRecorder()._sync_file(Path(directory) / "absent.part")
      with self.assertRaises(OSError):
        HlsRecorder()._sync_directory(Path(directory) / "absent")

  def test_descriptors_are_closed_on_both_paths(self):
    if not os.path.isdir("/proc/self/fd"):
      self.skipTest("requires /proc to count descriptors")
    with tempfile.TemporaryDirectory() as directory:
      good = Path(directory) / "good.part"
      good.write_bytes(b"captured-media")
      empty = Path(directory) / "empty.part"
      empty.write_bytes(b"")
      recorder = HlsRecorder()

      before = len(os.listdir("/proc/self/fd"))
      for _ in range(20):
        recorder._sync_file(good)
        recorder._sync_directory(Path(directory))
        with self.assertRaises(OSError):
          recorder._sync_file(empty)
      after = len(os.listdir("/proc/self/fd"))

      self.assertEqual(before, after)


class RealFilesystemFinalizerTest(unittest.TestCase):
  """The finalizer, end to end, with nothing faked and no ffmpeg involved."""

  def test_a_completed_attempt_becomes_the_destination(self):
    with tempfile.TemporaryDirectory() as directory:
      attempt = Path(directory) / ".live.ts.attempt-1.part"
      attempt.write_bytes(b"captured-media-bytes")
      ##
      ## The caller reserved this name with an empty placeholder before the
      ## recording started, which is why publication here is a rename rather
      ## than the no-clobber hard link the MP4 stage needs.
      ##
      destination = Path(directory) / "live.ts"
      destination.touch()

      result = HlsRecorder()._finalize_successful_attempt(attempt, destination)

      self.assertEqual(destination, result)
      self.assertTrue(destination.is_file())
      self.assertEqual(b"captured-media-bytes", destination.read_bytes())
      self.assertFalse(attempt.exists())
      self.assertEqual(
        ["live.ts"],
        sorted(path.name for path in Path(directory).iterdir()),
      )

  def test_the_finalizer_leaks_no_descriptors(self):
    if not os.path.isdir("/proc/self/fd"):
      self.skipTest("requires /proc to count descriptors")
    with tempfile.TemporaryDirectory() as directory:
      recorder = HlsRecorder()
      before = len(os.listdir("/proc/self/fd"))
      for index in range(20):
        attempt = Path(directory) / ".live.ts.attempt-{}.part".format(index)
        attempt.write_bytes(b"captured-media-bytes")
        destination = Path(directory) / "live-{}.ts".format(index)
        recorder._finalize_successful_attempt(attempt, destination)
      after = len(os.listdir("/proc/self/fd"))

      self.assertEqual(before, after)


class _Recorder:
  def __init__(self):
    self.entries = []

  def note(self, entry):
    self.entries.append(entry)


class _CompletedProcess:
  pid = 4321

  def poll(self):
    return 0

  def wait(self, timeout=None):
    return 0


def instrument(recorder, log, destination, *, fail=None, media=b"captured"):
  """Log the finalization steps ``record`` drives, in the order it drives them.

  Only leaf I/O is replaced; the sequencing under test is the real code.
  """
  fail = fail or {}
  real_sync_file = recorder._sync_file
  real_sync_directory = recorder._sync_directory
  real_replace = os.replace
  spawns = []

  def sync_file(path):
    log.note("sync-attempt-file")
    if "sync_file" in fail:
      raise fail["sync_file"]
    return real_sync_file(path)

  ##
  ## The same helper commits the directory before and after the rename; they
  ## are told apart by which side of the replace they fall on, which is exactly
  ## the ordering being asserted.
  ##
  def sync_directory(path):
    name = "sync-final-dir" if "replace" in log.entries else "sync-pre-rename-dir"
    log.note(name)
    key = "sync_final_dir" if name == "sync-final-dir" else "sync_pre_dir"
    if key in fail:
      raise fail[key]
    return real_sync_directory(path)

  def replace(a, b):
    log.note("replace")
    if "replace" in fail:
      raise fail["replace"]
    return real_replace(a, b)

  def process_factory(command, **kwargs):
    spawns.append(command)
    log.note("ffmpeg")
    Path(command[-1]).write_bytes(media)
    return _CompletedProcess()

  recorder._sync_file = sync_file
  recorder._sync_directory = sync_directory
  recorder.process_factory = process_factory
  return mock.patch.object(os, "replace", replace), spawns


class CaptureFinalizationOrderingTest(unittest.TestCase):
  def test_a_successful_capture_follows_the_durable_order(self):
    ##
    ## Every adjacent pair is load-bearing:
    ##   ffmpeg  -> sync-attempt-file : nothing to commit until ffmpeg exits
    ##   file    -> pre-rename-dir    : bytes on device before the namespace
    ##                                  holding them is committed
    ##   pre-dir -> replace           : the pre-rename state is durable, so a
    ##                                  crash inside the rename still leaves a
    ##                                  committed namespace naming the media
    ##   replace -> sync-final-dir    : the new name is itself only journalled
    ##
    log = _Recorder()
    with tempfile.TemporaryDirectory() as directory:
      destination = Path(directory) / "live.ts"
      destination.touch()
      recorder = HlsRecorder("/test/ffmpeg")
      replace_patch, spawns = instrument(recorder, log, destination)
      with replace_patch:
        result = recorder.record("https://s.test/i.m3u8", destination)

      self.assertEqual(
        [
          "ffmpeg",
          "sync-attempt-file",
          "sync-pre-rename-dir",
          "replace",
          "sync-final-dir",
        ],
        log.entries,
      )
      self.assertEqual(destination, result)
      self.assertEqual(b"captured", destination.read_bytes())

  def test_the_final_directory_is_committed_before_success_is_returned(self):
    ##
    ## The whole guarantee in one assertion: a caller cannot observe a
    ## successful return that precedes the commit of the recording's name.
    ##
    log = _Recorder()
    with tempfile.TemporaryDirectory() as directory:
      destination = Path(directory) / "live.ts"
      destination.touch()
      recorder = HlsRecorder("/test/ffmpeg")
      replace_patch, spawns = instrument(recorder, log, destination)
      with replace_patch:
        recorder.record("https://s.test/i.m3u8", destination)
      log.note("record-return")

      self.assertLess(
        log.entries.index("sync-final-dir"),
        log.entries.index("record-return"),
      )
      self.assertLess(log.entries.index("sync-attempt-file"), log.entries.index("replace"))
      self.assertLess(log.entries.index("sync-pre-rename-dir"), log.entries.index("replace"))
      self.assertLess(log.entries.index("replace"), log.entries.index("sync-final-dir"))


class CaptureDurabilityFailureTest(unittest.TestCase):
  """A capture that cannot be committed is not a capture that can be retried."""

  def attempt_failure(self, *, max_retry=0, **fail):
    log = _Recorder()
    directory = tempfile.TemporaryDirectory()
    destination = Path(directory.name) / "live.ts"
    destination.touch()
    recorder = HlsRecorder("/test/ffmpeg")
    replace_patch, spawns = instrument(recorder, log, destination, fail=fail)
    with replace_patch:
      with self.assertRaises(HlsDurabilityError):
        recorder.record(
          "https://s.test/i.m3u8", destination, max_retry=max_retry
        )
    return log, destination, spawns, directory

  def test_an_attempt_that_cannot_be_synced_never_reaches_the_rename(self):
    log, destination, spawns, directory = self.attempt_failure(
      sync_file=OSError(errno.EIO, "device failure")
    )
    with directory:
      self.assertNotIn("replace", log.entries)
      self.assertNotIn("sync-final-dir", log.entries)
      ##
      ## The completed capture is still on disk under its hidden name. It was
      ## not deliberately deleted and was not demoted to a failed partial -
      ## this attempt finished, it simply could not be proven durable.
      ##
      remaining = sorted(path.name for path in Path(directory.name).iterdir())
      self.assertIn(".live.ts.attempt-1.part", remaining)
      self.assertEqual(
        b"captured",
        (Path(directory.name) / ".live.ts.attempt-1.part").read_bytes(),
      )

  def test_a_pre_rename_directory_failure_never_reaches_the_rename(self):
    log, destination, spawns, directory = self.attempt_failure(
      sync_pre_dir=OSError(errno.EIO, "journal failure")
    )
    with directory:
      self.assertIn("sync-attempt-file", log.entries)
      self.assertNotIn("replace", log.entries)
      self.assertIn(
        ".live.ts.attempt-1.part",
        sorted(path.name for path in Path(directory.name).iterdir()),
      )

  def test_a_failed_rename_never_reaches_the_final_commit(self):
    log, destination, spawns, directory = self.attempt_failure(
      replace=OSError(errno.EXDEV, "cross-device")
    )
    with directory:
      self.assertIn("sync-pre-rename-dir", log.entries)
      self.assertNotIn("sync-final-dir", log.entries)
      self.assertIn(
        ".live.ts.attempt-1.part",
        sorted(path.name for path in Path(directory.name).iterdir()),
      )

  def test_a_failed_final_commit_keeps_the_destination_media(self):
    ##
    ## The rename succeeded, so the destination now holds the recording. The
    ## name is not committed, so success cannot be reported - but deleting the
    ## media to tidy up would destroy the very thing that was captured.
    ##
    log, destination, spawns, directory = self.attempt_failure(
      sync_final_dir=OSError(errno.EIO, "journal failure")
    )
    with directory:
      self.assertIn("replace", log.entries)
      self.assertTrue(destination.is_file())
      self.assertEqual(b"captured", destination.read_bytes())

  def test_a_durability_failure_never_reconnects_to_the_stream(self):
    ##
    ## The defining distinction. A stalled or refused capture is a network
    ## problem worth retrying; a capture that completed and could not be
    ## committed is a local storage problem, and the broadcast it recorded may
    ## already be over. Re-dialling would be pointless and would risk
    ## overwriting the media that is sitting right there.
    ##
    for stage in ("sync_file", "sync_pre_dir", "replace", "sync_final_dir"):
      with self.subTest(stage=stage):
        log, destination, spawns, directory = self.attempt_failure(
          max_retry=5, **{stage: OSError(errno.EIO, "failure")}
        )
        with directory:
          self.assertEqual(
            1,
            len(spawns),
            "durability failure at {} re-dialled the stream".format(stage),
          )


class CompletedCaptureIsNotCancellableTest(unittest.TestCase):
  def test_a_cancel_flag_set_after_ffmpeg_exits_does_not_cancel_the_capture(self):
    ##
    ## Once the media is captured there is nothing left to cancel. Re-reading
    ## the flag during finalization would turn a finished broadcast into a
    ## cancelled recording, throwing away media that is already on disk.
    ##
    log = _Recorder()
    with tempfile.TemporaryDirectory() as directory:
      destination = Path(directory) / "live.ts"
      destination.touch()
      recorder = HlsRecorder("/test/ffmpeg")
      replace_patch, spawns = instrument(recorder, log, destination)
      real_sync_file = recorder._sync_file

      def sync_then_cancel(path):
        ##
        ## Shutdown lands in the window between ffmpeg exiting and the
        ## recording being committed.
        ##
        recorder.cancel_all()
        return real_sync_file(path)

      recorder._sync_file = sync_then_cancel
      with replace_patch:
        result = recorder.record("https://s.test/i.m3u8", destination)

      self.assertEqual(destination, result)
      self.assertEqual(b"captured", destination.read_bytes())
      self.assertIn("sync-final-dir", log.entries)


class CallerCleanupTest(unittest.TestCase):
  """The downloader's exception cleanup must not destroy captured media."""

  def cleanup_after(self, recorder_error, *, destination_bytes):
    ##
    ## Mirrors the real cleanup in ``__request_file__``: on any exception it
    ## removes the reserved destination only when the destination is empty.
    ##
    with tempfile.TemporaryDirectory() as directory:
      destination = Path(directory) / "live.ts"
      destination.write_bytes(destination_bytes)
      try:
        raise recorder_error
      except BaseException:
        try:
          if destination.stat().st_size == 0:
            destination.unlink()
        except BaseException:
          pass
      return destination.exists(), (
        destination.read_bytes() if destination.exists() else b""
      )

  def test_an_empty_reserved_placeholder_is_still_cleaned_up(self):
    ##
    ## Durability failed before the rename, so the destination is still the
    ## zero-byte placeholder. Removing it is the existing behaviour and loses
    ## nothing - the captured bytes are in the hidden attempt.
    ##
    exists, _ = self.cleanup_after(
      HlsDurabilityError("could not commit"), destination_bytes=b""
    )
    self.assertFalse(exists)

  def test_a_non_empty_destination_is_never_cleaned_up(self):
    ##
    ## Durability failed after the rename, so the destination holds the whole
    ## recording. The cleanup must leave it alone.
    ##
    exists, content = self.cleanup_after(
      HlsDurabilityError("could not commit"),
      destination_bytes=b"captured-media-bytes",
    )
    self.assertTrue(exists)
    self.assertEqual(b"captured-media-bytes", content)


class NormalizerDefenceInDepthTest(unittest.TestCase):
  def test_the_normalizer_still_rechecks_a_source_the_recorder_made_durable(self):
    ##
    ## Deliberately duplicated work. The recorder's guarantee covers what the
    ## recorder returned; the normalizer is also reachable directly, with
    ## historical files, and from paths that never went through capture. It
    ## proves its own precondition rather than inheriting one.
    ##
    from backend.src.platform.douyin.hls_mp4_normalizer import HlsMp4Normalizer

    synced = []
    with tempfile.TemporaryDirectory() as directory:
      source = Path(directory) / "live.ts"
      source.write_bytes(b"captured-media-bytes")
      normalizer = HlsMp4Normalizer("/test/ffmpeg")
      real_sync_file = normalizer._sync_file
      real_sync_directory = normalizer._sync_directory

      def sync_file(path):
        synced.append(("file", Path(path)))
        return real_sync_file(path)

      def sync_directory(path):
        synced.append(("dir", Path(path)))
        return real_sync_directory(path)

      def process_factory(command, **kwargs):
        Path(command[-1]).write_bytes(b"remuxed")
        return _CompletedProcess()

      normalizer._sync_file = sync_file
      normalizer._sync_directory = sync_directory
      normalizer.process_factory = process_factory

      normalizer.normalize(source)

      self.assertEqual(("file", source), synced[0])
      self.assertEqual(("dir", source.parent), synced[1])


class CaptureDurabilityPrecedesTimestampTest(unittest.TestCase):
  """The capture is already durable when the recording clock is read.

  ``finished_at`` is taken by ``run_with_result`` the moment
  ``download_live_stream`` returns.  This proves the half that is new in this
  phase: that return now happens only after the final directory commit, so the
  timestamp cannot mark a recording that is not yet on stable storage.

  The other half - ``finished_at`` precedes MP4 normalization - is pinned by
  ``test_the_recording_interval_closes_before_normalization_runs`` in
  test_live_download_result.py, and is unchanged here.
  """

  def test_download_live_stream_returns_only_after_the_final_commit(self):
    from backend.src.library.baselib import load_yml
    from backend.src.platform.douyin import douyin_live_downloader as live_module

    project_root = Path(__file__).resolve().parents[3]
    config = load_yml(project_root / "docs" / "design" / "config.yml.example")
    config["database"]["enable"] = False
    config["download"]["test_mode"] = False
    config["download"]["tick_naming"] = False
    config["download"]["save_response"] = False
    config["download"]["save_error_response"] = False
    config["log"]["log_save"] = False
    config["server"]["debug_mode"] = False

    log = _Recorder()

    with tempfile.TemporaryDirectory() as directory:
      config["download"]["save_path"] = directory
      downloader = live_module.DouyinLiveDownloader(config)

      ##
      ## A real recorder, so the real finalization sequence runs; only the
      ## ffmpeg process itself is stood in for.
      ##
      recorder = HlsRecorder("/test/ffmpeg")
      real_sync_directory = recorder._sync_directory
      replaced = []

      def sync_directory(path):
        log.note("sync-final-dir" if replaced else "sync-pre-rename-dir")
        return real_sync_directory(path)

      real_replace = os.replace

      def replace(a, b):
        replaced.append(True)
        return real_replace(a, b)

      def process_factory(command, **kwargs):
        Path(command[-1]).write_bytes(b"captured-media")
        return _CompletedProcess()

      recorder._sync_directory = sync_directory
      recorder.process_factory = process_factory
      downloader.hls_recorder = recorder

      with mock.patch.object(os, "replace", replace):
        written = downloader.download_live_stream(
          "https://v.douyin.com/example/",
          {
            "summary": {
              "stream_url": "https://stream.example.test/index.m3u8",
              "stream_name": "stream-test.ts",
              "stream_protocol": "hls",
              "directory_name": "Test_Host",
              "nickname": "Test Host",
            },
            "external_info": {"data": {"room": {"owner_user_id": "owner-1"}}},
          },
        )
      log.note("download-live-stream-return")

      self.assertLess(
        log.entries.index("sync-final-dir"),
        log.entries.index("download-live-stream-return"),
      )
      self.assertEqual(b"captured-media", Path(written).read_bytes())


if __name__ == "__main__":
  unittest.main()
