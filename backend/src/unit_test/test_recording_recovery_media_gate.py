##
## Proving the media is still there, before a replay tells the database it is.
##
## ``load`` proves a great deal about a note - its schema, that it claims its
## own key, the shape of every field, that its output path is inside the
## configured storage root.  It cannot prove the one fact a replay depends on:
## that the recording file still exists.  A note is durable and a file is not;
## between the crash and the restart the media may have been deleted, truncated
## to nothing, or replaced with a link to something else entirely.
##
## So a replay asks the filesystem before it asks the database.  Every refusal
## here means no database mutation at all - the note stays, and an operator
## still has the evidence.
##
## The check is the media layer's existing secure boundary, reached through one
## narrow wrapper rather than reimplemented.  There must be one answer in this
## codebase to "is this path really a regular file inside the root", not two
## that can drift.
##
from pathlib import Path
import os
import tempfile
import unittest

from backend.src.service.media_asset import (
  SECURE_OPEN_SUPPORTED,
  open_regular_file_within_root,
)


class OpenWithinRootTest(unittest.TestCase):
  def setUp(self):
    self.storage = tempfile.TemporaryDirectory()
    self.addCleanup(self.storage.cleanup)
    self.root = Path(self.storage.name)
    (self.root / "douyin" / "live").mkdir(parents=True)
    self.media = self.root / "douyin" / "live" / "live.mp4"
    self.media.write_bytes(b"recorded-media-bytes")

  def open(self, candidate):
    return open_regular_file_within_root(self.root, candidate)

  ##
  ## >>=============================== accepts ===============================>>
  ##
  def test_a_real_recording_inside_the_root_opens(self):
    opened = self.open("douyin/live/live.mp4")

    self.assertIsNotNone(opened)
    stream, info = opened
    try:
      self.assertEqual(len(b"recorded-media-bytes"), info.st_size)
    finally:
      stream.close()

  def test_an_absolute_path_inside_the_root_opens(self):
    ##
    ## The production spelling: the recorder builds its output path from the
    ## configured save path, so what a note carries is usually absolute.
    ##
    opened = self.open(str(self.media))

    self.assertIsNotNone(opened)
    opened[0].close()

  def test_the_file_is_not_read_or_changed(self):
    ##
    ## Validation, not verification of content. Hashing a recording would read
    ## gigabytes during startup for every note in the directory.
    ##
    before = self.media.read_bytes()
    stat_before = self.media.stat()

    opened = self.open("douyin/live/live.mp4")
    opened[0].close()

    self.assertEqual(before, self.media.read_bytes())
    self.assertEqual(stat_before.st_mtime_ns, self.media.stat().st_mtime_ns)

  ##
  ## >>=============================== refuses ===============================>>
  ##
  def test_a_missing_recording_is_refused(self):
    self.assertIsNone(self.open("douyin/live/gone.mp4"))

  def test_a_directory_is_refused(self):
    self.assertIsNone(self.open("douyin/live"))

  def test_the_root_itself_is_refused(self):
    self.assertIsNone(self.open(str(self.root)))

  def test_an_empty_or_absent_path_is_refused(self):
    for candidate in (None, "", "   "):
      self.assertIsNone(self.open(candidate))

  def test_a_path_outside_the_root_is_refused(self):
    with tempfile.TemporaryDirectory() as elsewhere:
      outside = Path(elsewhere) / "live.mp4"
      outside.write_bytes(b"not ours")

      self.assertIsNone(self.open(str(outside)))

  def test_a_sibling_directory_sharing_a_prefix_is_refused(self):
    ##
    ## Containment is a path-segment relationship, never a string prefix.
    ##
    sibling = Path(str(self.root) + "-evil")
    sibling.mkdir()
    self.addCleanup(sibling.rmdir)
    self.addCleanup(lambda: (sibling / "live.mp4").unlink(missing_ok=True))
    (sibling / "live.mp4").write_bytes(b"not ours")

    self.assertIsNone(self.open(str(sibling / "live.mp4")))

  def test_traversal_out_of_the_root_is_refused(self):
    self.assertIsNone(self.open("douyin/../../etc/passwd"))

  @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "requires O_NOFOLLOW")
  def test_a_symlinked_recording_is_refused_even_inside_the_root(self):
    ##
    ## The target is a perfectly good file in the root, so following the link
    ## would succeed and this test would pass for the wrong reason. It must
    ## fail on the link itself.
    ##
    ## Fail-closed on purpose: the recorder writes a regular file. A link where
    ## the recording should be means something other than this server chose
    ## what a replay is about to catalogue.
    ##
    link = self.root / "douyin" / "live" / "linked.mp4"
    link.symlink_to(self.media)

    self.assertIsNone(self.open("douyin/live/linked.mp4"))

  @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "requires O_NOFOLLOW")
  def test_an_intermediate_directory_symlink_is_refused(self):
    real = self.root / "real"
    real.mkdir()
    (real / "live.mp4").write_bytes(b"recorded-media-bytes")
    (self.root / "linkdir").symlink_to(real)

    self.assertIsNone(self.open("linkdir/live.mp4"))

  @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "requires O_NOFOLLOW")
  def test_a_symlink_escaping_the_root_is_refused(self):
    with tempfile.TemporaryDirectory() as elsewhere:
      outside = Path(elsewhere) / "live.mp4"
      outside.write_bytes(b"not ours")
      (self.root / "escape.mp4").symlink_to(outside)

      self.assertIsNone(self.open("escape.mp4"))

  @unittest.skipUnless(
    hasattr(os, "mkfifo"), "requires a platform with named pipes"
  )
  def test_a_fifo_is_refused(self):
    ##
    ## A named pipe is not a recording, and opening one where a file is
    ## expected is how a startup hangs waiting for a writer.
    ##
    os.mkfifo(str(self.root / "pipe.mp4"))

    self.assertIsNone(self.open("pipe.mp4"))


class SymlinkedRootIsStillTrustedTest(unittest.TestCase):
  """An operator may point the storage root at a symlink; a mount often is one."""

  @unittest.skipUnless(SECURE_OPEN_SUPPORTED, "requires the secure open path")
  def test_a_recording_reached_through_a_symlinked_root_opens(self):
    with tempfile.TemporaryDirectory() as base:
      real = Path(base) / "real-storage"
      (real / "douyin").mkdir(parents=True)
      (real / "douyin" / "live.mp4").write_bytes(b"recorded")
      linked = Path(base) / "storage"
      linked.symlink_to(real)

      opened = open_regular_file_within_root(linked, "douyin/live.mp4")

      self.assertIsNotNone(opened)
      opened[0].close()


if __name__ == "__main__":
  unittest.main()
