from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from unittest import mock

from backend.src.platform.douyin.hls_mp4_normalizer import HlsMp4Normalizer


##
## Encoder names that must never appear in a normalization command.  The whole
## point of this stage is that it does not re-encode: if any of these ever
## reaches the command line, a recording that took an hour of wall clock is
## being decoded and re-compressed, which is a different feature with different
## costs and different failure modes.
##
FORBIDDEN_ENCODERS = (
  "libx264",
  "libx265",
  "h264",
  "hevc",
  "aac",
  "libfdk_aac",
  "mpeg4",
  "libvpx",
)


class _FakeProcess:
  """A stand-in ffmpeg that finishes immediately with a fixed return code."""

  pid = 4321

  def __init__(self, returncode=0):
    self.returncode = returncode
    self.terminated = []

  def poll(self):
    return self.returncode

  def wait(self, timeout=None):
    return self.returncode


class HlsMp4NormalizerCommandTest(unittest.TestCase):
  def test_normalize_builds_a_lossless_stream_copy_command(self):
    calls = []

    def process_factory(command, **kwargs):
      calls.append((command, kwargs))
      Path(command[-1]).write_bytes(b"fake-mp4")
      return _FakeProcess(0)

    with tempfile.TemporaryDirectory() as temporary_directory:
      source = Path(temporary_directory) / "live.ts"
      source.write_bytes(b"fake-ts")
      normalizer = HlsMp4Normalizer(
        "/test/ffmpeg",
        process_factory,
        token_factory=lambda: "deadbeef",
      )

      normalizer.normalize(source)

      self.assertEqual(1, len(calls))
      command, kwargs = calls[0]
      self.assertEqual("/test/ffmpeg", command[0])
      self.assertIn("-nostdin", command)
      self.assertIn("-hide_banner", command)
      self.assertIn("-nostats", command)
      self.assertEqual(
        ["-loglevel", "error"],
        command[command.index("-loglevel"):command.index("-loglevel") + 2],
      )
      self.assertEqual(
        ["-i", str(source)],
        command[command.index("-i"):command.index("-i") + 2],
      )
      self.assertEqual(
        ["-map", "0:v?"],
        command[command.index("0:v?") - 1:command.index("0:v?") + 1],
      )
      self.assertEqual(
        ["-map", "0:a?"],
        command[command.index("0:a?") - 1:command.index("0:a?") + 1],
      )
      self.assertEqual(
        ["-c", "copy"],
        command[command.index("-c"):command.index("-c") + 2],
      )
      self.assertEqual(
        ["-movflags", "+faststart"],
        command[command.index("-movflags"):command.index("-movflags") + 2],
      )
      self.assertEqual(
        ["-f", "mp4"],
        command[command.index("-f"):command.index("-f") + 2],
      )
      self.assertEqual(
        str(source.parent / ".live.remux-deadbeef.part.mp4"),
        command[-1],
      )
      self.assertEqual(
        {
          "stdout": subprocess.DEVNULL,
          "stderr": subprocess.DEVNULL,
          "shell": False,
          "start_new_session": True,
        },
        kwargs,
      )

  def test_normalization_command_carries_no_encoder(self):
    calls = []

    def process_factory(command, **kwargs):
      calls.append(command)
      Path(command[-1]).write_bytes(b"fake-mp4")
      return _FakeProcess(0)

    with tempfile.TemporaryDirectory() as temporary_directory:
      source = Path(temporary_directory) / "live.ts"
      source.write_bytes(b"fake-ts")
      HlsMp4Normalizer("/test/ffmpeg", process_factory).normalize(source)

    for token in calls[0]:
      self.assertNotIn(token, FORBIDDEN_ENCODERS)

  def test_normalization_does_not_hand_write_the_aac_bitstream_filter(self):
    ##
    ## The MOV/MP4 muxer inserts aac_adtstoasc itself where an ADTS AAC stream
    ## needs it.  Spelling it out here would be a second copy of muxer logic
    ## that has to be kept in step with FFmpeg by hand, and it fails outright
    ## on inputs that do not need it.
    ##
    calls = []

    def process_factory(command, **kwargs):
      calls.append(command)
      Path(command[-1]).write_bytes(b"fake-mp4")
      return _FakeProcess(0)

    with tempfile.TemporaryDirectory() as temporary_directory:
      source = Path(temporary_directory) / "live.ts"
      source.write_bytes(b"fake-ts")
      HlsMp4Normalizer("/test/ffmpeg", process_factory).normalize(source)

    self.assertNotIn("aac_adtstoasc", calls[0])
    self.assertNotIn("-bsf:a", calls[0])

  def test_normalization_maps_only_video_and_audio(self):
    calls = []

    def process_factory(command, **kwargs):
      calls.append(command)
      Path(command[-1]).write_bytes(b"fake-mp4")
      return _FakeProcess(0)

    with tempfile.TemporaryDirectory() as temporary_directory:
      source = Path(temporary_directory) / "live.ts"
      source.write_bytes(b"fake-ts")
      HlsMp4Normalizer("/test/ffmpeg", process_factory).normalize(source)

    command = calls[0]
    mapped = [
      command[index + 1]
      for index, token in enumerate(command)
      if token == "-map"
    ]
    self.assertEqual(["0:v?", "0:a?"], mapped)


class HlsMp4NormalizerSuccessTest(unittest.TestCase):
  def test_successful_remux_publishes_mp4_beside_the_source(self):
    def process_factory(command, **kwargs):
      Path(command[-1]).write_bytes(b"fake-mp4-bytes")
      return _FakeProcess(0)

    with tempfile.TemporaryDirectory() as temporary_directory:
      source = Path(temporary_directory) / "live.ts"
      source.write_bytes(b"fake-ts")

      result = HlsMp4Normalizer("/test/ffmpeg", process_factory).normalize(
        source
      )

      expected = source.parent / "live.mp4"
      self.assertEqual(expected, result)
      self.assertTrue(expected.is_file())
      self.assertEqual(b"fake-mp4-bytes", expected.read_bytes())

  def test_source_ts_is_removed_only_after_the_mp4_is_published(self):
    observed = []

    def process_factory(command, **kwargs):
      ##
      ## The source must still be the authoritative recording while ffmpeg
      ## runs: nothing may rename, truncate or replace it in place.
      ##
      observed.append(Path(command[command.index("-i") + 1]).read_bytes())
      Path(command[-1]).write_bytes(b"fake-mp4-bytes")
      return _FakeProcess(0)

    with tempfile.TemporaryDirectory() as temporary_directory:
      source = Path(temporary_directory) / "live.ts"
      source.write_bytes(b"fake-ts")

      result = HlsMp4Normalizer("/test/ffmpeg", process_factory).normalize(
        source
      )

      self.assertEqual([b"fake-ts"], observed)
      self.assertFalse(source.exists())
      self.assertTrue(result.is_file())

  def test_successful_remux_leaves_no_temporary_behind(self):
    def process_factory(command, **kwargs):
      Path(command[-1]).write_bytes(b"fake-mp4-bytes")
      return _FakeProcess(0)

    with tempfile.TemporaryDirectory() as temporary_directory:
      source = Path(temporary_directory) / "live.ts"
      source.write_bytes(b"fake-ts")

      HlsMp4Normalizer("/test/ffmpeg", process_factory).normalize(source)

      self.assertEqual(
        [],
        sorted(
          path.name
          for path in source.parent.iterdir()
          if "remux" in path.name
        ),
      )

  def test_source_delete_failure_still_reports_the_published_mp4(self):
    def process_factory(command, **kwargs):
      Path(command[-1]).write_bytes(b"fake-mp4-bytes")
      return _FakeProcess(0)

    with tempfile.TemporaryDirectory() as temporary_directory:
      source = Path(temporary_directory) / "live.ts"
      source.write_bytes(b"fake-ts")
      normalizer = HlsMp4Normalizer("/test/ffmpeg", process_factory)

      real_unlink = Path.unlink

      def refuse_source_unlink(self, *args, **kwargs):
        if self == source:
          raise PermissionError("source is pinned")
        return real_unlink(self, *args, **kwargs)

      with mock.patch.object(Path, "unlink", refuse_source_unlink):
        result = normalizer.normalize(source)

      ##
      ## A leftover .ts is an orphan-cleanup problem.  It cannot be allowed to
      ## undo a normalization that already published a complete MP4.
      ##
      self.assertEqual(source.parent / "live.mp4", result)
      self.assertTrue(result.is_file())
      self.assertTrue(source.exists())


class HlsMp4NormalizerFallbackTest(unittest.TestCase):
  def test_non_zero_ffmpeg_preserves_the_source_and_cleans_the_temporary(self):
    def process_factory(command, **kwargs):
      Path(command[-1]).write_bytes(b"half-written")
      return _FakeProcess(1)

    with tempfile.TemporaryDirectory() as temporary_directory:
      source = Path(temporary_directory) / "live.ts"
      source.write_bytes(b"fake-ts")

      result = HlsMp4Normalizer("/test/ffmpeg", process_factory).normalize(
        source
      )

      self.assertEqual(source, result)
      self.assertEqual(b"fake-ts", source.read_bytes())
      self.assertFalse((source.parent / "live.mp4").exists())
      self.assertEqual(
        ["live.ts"],
        sorted(path.name for path in source.parent.iterdir()),
      )

  def test_empty_output_is_not_published_even_when_ffmpeg_succeeds(self):
    def process_factory(command, **kwargs):
      Path(command[-1]).write_bytes(b"")
      return _FakeProcess(0)

    with tempfile.TemporaryDirectory() as temporary_directory:
      source = Path(temporary_directory) / "live.ts"
      source.write_bytes(b"fake-ts")

      result = HlsMp4Normalizer("/test/ffmpeg", process_factory).normalize(
        source
      )

      self.assertEqual(source, result)
      self.assertEqual(b"fake-ts", source.read_bytes())
      self.assertEqual(
        ["live.ts"],
        sorted(path.name for path in source.parent.iterdir()),
      )

  def test_missing_output_is_not_published_even_when_ffmpeg_succeeds(self):
    def process_factory(command, **kwargs):
      return _FakeProcess(0)

    with tempfile.TemporaryDirectory() as temporary_directory:
      source = Path(temporary_directory) / "live.ts"
      source.write_bytes(b"fake-ts")

      result = HlsMp4Normalizer("/test/ffmpeg", process_factory).normalize(
        source
      )

      self.assertEqual(source, result)
      self.assertFalse((source.parent / "live.mp4").exists())

  def test_spawn_failure_preserves_the_source_without_raising(self):
    def process_factory(command, **kwargs):
      raise OSError("ffmpeg is gone")

    with tempfile.TemporaryDirectory() as temporary_directory:
      source = Path(temporary_directory) / "live.ts"
      source.write_bytes(b"fake-ts")

      result = HlsMp4Normalizer("/test/ffmpeg", process_factory).normalize(
        source
      )

      self.assertEqual(source, result)
      self.assertEqual(b"fake-ts", source.read_bytes())
      self.assertEqual(
        ["live.ts"],
        sorted(path.name for path in source.parent.iterdir()),
      )

  def test_temporary_creation_failure_preserves_the_source(self):
    def process_factory(command, **kwargs):
      raise AssertionError("ffmpeg must not be spawned without a temporary")

    with tempfile.TemporaryDirectory() as temporary_directory:
      source = Path(temporary_directory) / "live.ts"
      source.write_bytes(b"fake-ts")
      normalizer = HlsMp4Normalizer("/test/ffmpeg", process_factory)

      with mock.patch.object(
        HlsMp4Normalizer,
        "_reserve_temporary",
        side_effect=OSError("read-only filesystem"),
      ):
        result = normalizer.normalize(source)

      self.assertEqual(source, result)
      self.assertEqual(b"fake-ts", source.read_bytes())

  def test_publish_never_overwrites_an_mp4_that_appeared_mid_remux(self):
    with tempfile.TemporaryDirectory() as temporary_directory:
      source = Path(temporary_directory) / "live.ts"
      source.write_bytes(b"fake-ts")
      rival = source.parent / "live.mp4"

      def process_factory(command, **kwargs):
        ##
        ## Another actor wins the name while this remux is still running.  The
        ## reservation happened before it existed, so only the publish step can
        ## still catch this.
        ##
        rival.write_bytes(b"another-recording")
        Path(command[-1]).write_bytes(b"fake-mp4-bytes")
        return _FakeProcess(0)

      result = HlsMp4Normalizer("/test/ffmpeg", process_factory).normalize(
        source
      )

      self.assertEqual(source, result)
      self.assertEqual(b"fake-ts", source.read_bytes())
      self.assertEqual(b"another-recording", rival.read_bytes())
      self.assertEqual(
        ["live.mp4", "live.ts"],
        sorted(path.name for path in source.parent.iterdir()),
      )

  def test_a_filesystem_without_no_clobber_publish_falls_back_to_ts(self):
    def process_factory(command, **kwargs):
      Path(command[-1]).write_bytes(b"fake-mp4-bytes")
      return _FakeProcess(0)

    with tempfile.TemporaryDirectory() as temporary_directory:
      source = Path(temporary_directory) / "live.ts"
      source.write_bytes(b"fake-ts")
      normalizer = HlsMp4Normalizer("/test/ffmpeg", process_factory)

      ##
      ## No hard links available.  Failing closed keeps the recording; the only
      ## alternative would be an overwriting publish, which can destroy another
      ## recording that already owns the name.
      ##
      with mock.patch.object(
        os, "link", side_effect=OSError("hard links unsupported")
      ):
        result = normalizer.normalize(source)

      self.assertEqual(source, result)
      self.assertEqual(b"fake-ts", source.read_bytes())
      self.assertFalse((source.parent / "live.mp4").exists())
      self.assertEqual(
        ["live.ts"],
        sorted(path.name for path in source.parent.iterdir()),
      )

  def test_a_missing_source_is_reported_back_unchanged(self):
    def process_factory(command, **kwargs):
      raise AssertionError("ffmpeg must not be spawned for a missing source")

    with tempfile.TemporaryDirectory() as temporary_directory:
      source = Path(temporary_directory) / "live.ts"

      result = HlsMp4Normalizer("/test/ffmpeg", process_factory).normalize(
        source
      )

      self.assertEqual(source, result)


class HlsMp4NormalizerCancellationTest(unittest.TestCase):
  def test_cancel_terminates_the_remux_and_preserves_the_source(self):
    signals = []

    class RunningProcess:
      pid = 9876

      def __init__(self):
        self.waits = 0

      def poll(self):
        return None

      def wait(self, timeout=None):
        self.waits += 1
        return -15

    normalizer_box = {}

    def process_factory(command, **kwargs):
      Path(command[-1]).write_bytes(b"partial-mp4")
      return RunningProcess()

    def sleeper(seconds):
      ##
      ## Server shutdown lands while the remux is in flight.
      ##
      normalizer_box["normalizer"].cancel_all()

    with tempfile.TemporaryDirectory() as temporary_directory:
      source = Path(temporary_directory) / "live.ts"
      source.write_bytes(b"fake-ts")
      normalizer = HlsMp4Normalizer(
        "/test/ffmpeg",
        process_factory,
        sleeper=sleeper,
        group_signaler=lambda pid, number: signals.append((pid, number)),
      )
      normalizer_box["normalizer"] = normalizer

      result = normalizer.normalize(source)

      self.assertEqual(source, result)
      self.assertEqual(b"fake-ts", source.read_bytes())
      self.assertEqual([(9876, 15)], signals)
      self.assertEqual(
        ["live.ts"],
        sorted(path.name for path in source.parent.iterdir()),
      )

  def test_an_interrupt_mid_remux_kills_ffmpeg_and_keeps_the_source(self):
    ##
    ## A remux is a child process in its own session, so an interrupt that
    ## unwinds this thread does not reach it.  Left alone it would keep writing
    ## an MP4 nobody is waiting for, into a directory the library scans.
    ##
    signals = []

    class RunningProcess:
      pid = 5150

      def poll(self):
        return None

      def wait(self, timeout=None):
        return -15

    def process_factory(command, **kwargs):
      Path(command[-1]).write_bytes(b"partial-mp4")
      return RunningProcess()

    def sleeper(seconds):
      raise KeyboardInterrupt()

    with tempfile.TemporaryDirectory() as temporary_directory:
      source = Path(temporary_directory) / "live.ts"
      source.write_bytes(b"fake-ts")
      normalizer = HlsMp4Normalizer(
        "/test/ffmpeg",
        process_factory,
        sleeper=sleeper,
        group_signaler=lambda pid, number: signals.append((pid, number)),
      )

      ##
      ## The interrupt still propagates - it is not this stage's to swallow.
      ##
      with self.assertRaises(KeyboardInterrupt):
        normalizer.normalize(source)

      self.assertEqual([(5150, 15)], signals)
      self.assertEqual(b"fake-ts", source.read_bytes())
      self.assertEqual(
        ["live.ts"],
        sorted(path.name for path in source.parent.iterdir()),
      )

  def test_a_cancelled_normalizer_skips_remux_entirely(self):
    def process_factory(command, **kwargs):
      raise AssertionError("a cancelled normalizer must not spawn ffmpeg")

    with tempfile.TemporaryDirectory() as temporary_directory:
      source = Path(temporary_directory) / "live.ts"
      source.write_bytes(b"fake-ts")
      normalizer = HlsMp4Normalizer("/test/ffmpeg", process_factory)
      normalizer.cancel_all()

      result = normalizer.normalize(source)

      self.assertEqual(source, result)
      self.assertEqual(b"fake-ts", source.read_bytes())


if __name__ == "__main__":
  unittest.main()
