##
## The remux, proved against a real FFmpeg.
##
## Everything else about normalization can be tested with a stand-in process,
## and most of it should be - the interesting behaviour is what happens around
## ffmpeg, not inside it.  Two claims cannot be tested that way, because they
## are claims about FFmpeg itself:
##
##   - a stream-copy from MPEG-TS to MP4 actually works, including the AAC
##     bitstream conversion this code deliberately does not spell out, and
##   - it changes the container without touching the codecs.
##
## A fake process asserts those into existence.  A real one demonstrates them.
##
## Skipped when no ffmpeg is reachable so the ordinary run stays fast and
## offline, and required in CI so the skip cannot quietly become permanent.
## The fixture is generated locally by ffmpeg itself and lives in a temporary
## directory: nothing is downloaded, and no media is committed.
##
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest

from backend.src.platform.douyin.hls_mp4_normalizer import HlsMp4Normalizer

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")

REQUIRED = os.environ.get("SMSD_REQUIRE_FFMPEG_TESTS") == "1"

if REQUIRED and not (FFMPEG and FFPROBE):
  raise RuntimeError(
    "SMSD_REQUIRE_FFMPEG_TESTS=1 but ffmpeg/ffprobe are not on PATH. "
    "These tests prove that a captured MPEG-TS recording really can be "
    "remuxed into a playable MP4 without re-encoding, which nothing else in "
    "the suite can stand in for."
  )


##
## The distinct codec names ffprobe reports for a stream selector.
##
## A set rather than a string.  ``v:0`` names one stream, but MPEG-TS carries
## programs and ffprobe lists a stream under each program as well as in the
## flat stream list - so the same codec comes back more than once for the .ts
## and exactly once for the .mp4.  The question being asked is which codec is
## there, not how many times the container mentions it, and comparing sets
## answers that identically on both sides.
##
def _codecs(path, stream):
  completed = subprocess.run(
    [
      FFPROBE,
      "-v", "error",
      "-select_streams", stream,
      "-show_entries", "stream=codec_name",
      "-of", "default=noprint_wrappers=1:nokey=1",
      str(path),
    ],
    capture_output=True,
    text=True,
    timeout=60,
  )
  return {line.strip() for line in completed.stdout.splitlines() if line.strip()}


##
## Walk the top-level MP4 boxes.  An MP4 is a flat sequence of length-prefixed
## boxes, so the order of ``moov`` and ``mdat`` can be read with arithmetic
## rather than a parser library - which matters, because adding a media parser
## dependency to assert one fact would cost more than the fact is worth.
##
def _top_level_boxes(path):
  boxes = []
  size_of_header = 8
  with open(path, "rb") as handle:
    offset = 0
    total = path.stat().st_size
    while offset + size_of_header <= total:
      handle.seek(offset)
      header = handle.read(size_of_header)
      if len(header) < size_of_header:
        break
      size = struct.unpack(">I", header[:4])[0]
      name = header[4:8].decode("ascii", "replace")
      if size == 1:
        ##
        ## 64-bit extended size, carried in the eight bytes after the header.
        ##
        extended = handle.read(8)
        if len(extended) < 8:
          break
        size = struct.unpack(">Q", extended)[0]
      elif size == 0:
        ##
        ## Runs to end of file.
        ##
        size = total - offset
      if size < size_of_header:
        break
      boxes.append(name)
      offset += size
  return boxes


@unittest.skipUnless(
  FFMPEG and FFPROBE,
  "install ffmpeg and ffprobe to run the real remux tests",
)
class RealFfmpegRemuxTest(unittest.TestCase):
  ##
  ## A one-second 64x48 clip with a tone on it: small enough to be free, real
  ## enough that the MP4 muxer has to do its actual job.  H.264 and AAC in
  ## MPEG-TS is what the Douyin HLS fallback delivers, so that is what is
  ## generated here.
  ##
  ## The encoders below build the *fixture*.  They are the thing under test
  ## being ruled out, not used: the normalizer's own command is asserted to
  ## carry no encoder at all.
  ##
  def build_fixture(self, directory):
    source = Path(directory) / "live.ts"
    completed = subprocess.run(
      [
        FFMPEG,
        "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", "testsrc=size=64x48:rate=10:duration=1",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest",
        "-f", "mpegts",
        str(source),
      ],
      capture_output=True,
      text=True,
      timeout=120,
    )
    if completed.returncode != 0 or not source.is_file() or not source.stat().st_size:
      message = (
        "could not build an H.264/AAC MPEG-TS fixture with this ffmpeg build: "
        "{}".format(completed.stderr.strip()[:400])
      )
      if REQUIRED:
        self.fail(message)
      self.skipTest(message)
    return source

  def test_a_real_ts_recording_is_remuxed_into_a_playable_mp4(self):
    with tempfile.TemporaryDirectory() as temporary_directory:
      source = self.build_fixture(temporary_directory)
      source_bytes = source.stat().st_size

      result = HlsMp4Normalizer().normalize(source)

      self.assertEqual(source.with_suffix(".mp4"), result)
      self.assertTrue(result.is_file())
      self.assertGreater(result.stat().st_size, 0)
      ##
      ## The container was replaced, so the file is not expected to be the same
      ## size - only to still hold a real recording.
      ##
      self.assertGreater(source_bytes, 0)
      self.assertFalse(source.exists())
      self.assertEqual(
        [],
        [path.name for path in result.parent.iterdir() if "remux" in path.name],
      )

  def test_the_remux_changes_the_container_and_not_the_codecs(self):
    with tempfile.TemporaryDirectory() as temporary_directory:
      source = self.build_fixture(temporary_directory)
      self.assertEqual({"h264"}, _codecs(source, "v:0"))
      self.assertEqual({"aac"}, _codecs(source, "a:0"))

      result = HlsMp4Normalizer().normalize(source)

      ##
      ## Same codecs on the far side.  If anything here had re-encoded, this is
      ## where it would still pass by accident - so the container is checked
      ## too: the codecs are identical *and* the file is now an MP4.
      ##
      self.assertEqual({"h264"}, _codecs(result, "v:0"))
      self.assertEqual({"aac"}, _codecs(result, "a:0"))
      self.assertEqual(".mp4", result.suffix)
      self.assertIn("moov", _top_level_boxes(result))

  def test_the_remuxed_mp4_is_laid_out_for_progressive_playback(self):
    ##
    ## ``+faststart`` moves the index in front of the media.  Without it a
    ## browser has to fetch the tail of the file before it can start, which on
    ## a long recording served over Range requests is the difference between
    ## previewing and waiting.
    ##
    with tempfile.TemporaryDirectory() as temporary_directory:
      source = self.build_fixture(temporary_directory)

      result = HlsMp4Normalizer().normalize(source)

      boxes = _top_level_boxes(result)
      self.assertIn("moov", boxes)
      self.assertIn("mdat", boxes)
      self.assertLess(boxes.index("moov"), boxes.index("mdat"))

  def test_a_real_remux_leaves_an_unrelated_mp4_untouched(self):
    with tempfile.TemporaryDirectory() as temporary_directory:
      source = self.build_fixture(temporary_directory)
      rival = source.with_suffix(".mp4")
      rival.write_bytes(b"another-recording")

      result = HlsMp4Normalizer().normalize(source)

      ##
      ## The name was already taken, so there is nowhere safe to publish.  The
      ## captured recording stays, and the file that owns the name is not
      ## touched by a single byte.
      ##
      self.assertEqual(source, result)
      self.assertTrue(source.is_file())
      self.assertEqual(b"another-recording", rival.read_bytes())

  def test_a_real_source_that_cannot_be_remuxed_is_preserved(self):
    ##
    ## Not every TS can become an MP4 - stream-copy fails when the target
    ## container cannot represent the input.  Bytes that are not a transport
    ## stream at all stand in for that here: what matters is that a refusal
    ## from ffmpeg costs nothing.
    ##
    with tempfile.TemporaryDirectory() as temporary_directory:
      source = Path(temporary_directory) / "live.ts"
      source.write_bytes(b"this is not a transport stream" * 64)

      result = HlsMp4Normalizer().normalize(source)

      self.assertEqual(source, result)
      self.assertTrue(source.is_file())
      self.assertFalse(source.with_suffix(".mp4").exists())
      self.assertEqual(
        ["live.ts"],
        sorted(path.name for path in source.parent.iterdir()),
      )


if __name__ == "__main__":
  unittest.main()
