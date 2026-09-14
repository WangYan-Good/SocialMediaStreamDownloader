##
## Capturing two terabytes of media without copying two terabytes.
##
## The Compose backup tars its download volume. Production's media root holds
## 2.0 TB on a filesystem with 1.8 TB free, so there is no destination for a
## copy - not on that disk, and not on the other one either. A release that
## demanded one would simply never run.
##
## What does work is reflink: the media filesystem is XFS with ``reflink=1``, so
## a copy-on-write clone is a metadata operation that shares extents with the
## original and costs almost nothing until something diverges. That is a real
## snapshot of the tree as it was at that instant.
##
## Two things follow, and both are load-bearing.
##
## First, reflink is a property of the filesystem, not an assumption. If the
## destination cannot do it the answer is to stop, not to fall back to a copy
## that cannot fit - a fallback would turn "no rollback authority" into "a
## release that hangs overnight and then fails".
##
## Second, the snapshot lives on the same filesystem as the media, by
## construction. It is authority against logical loss - a bad migration, an
## application bug, a wrong delete - and it is not authority against the device
## failing. That boundary is documented rather than blurred.
##
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SNAPSHOT_SCRIPT = PROJECT_ROOT / "scripts" / "release_media_snapshot.py"
##
## The interpreter running these tests, not a checked-in virtualenv path.
## A hard-coded ``venv/bin/python`` exists on a developer machine and on no
## CI runner, where it fails as "the configuration file must be a 0600
## regular file" - the inner check never ran, and the script reported the
## refusal it falls back to.
##
PYTHON_BIN = sys.executable


def reflink_supported(directory: Path) -> bool:
  source = directory / ".reflink-probe-src"
  target = directory / ".reflink-probe-dst"
  try:
    source.write_bytes(b"probe")
    completed = subprocess.run(
      ["cp", "--reflink=always", str(source), str(target)],
      capture_output=True,
    )
    return completed.returncode == 0
  finally:
    for path in (source, target):
      try:
        path.unlink()
      except FileNotFoundError:
        pass


class MediaSnapshotTestCase(unittest.TestCase):
  ##
  ## Where a file's first extent physically lives. Two files reporting the same
  ## one are sharing it, which is the whole claim reflink makes.
  ##
  def first_physical_extent(self, path: Path) -> str:
    completed = subprocess.run(
      ["filefrag", "-v", str(path)], capture_output=True, text=True
    )
    if completed.returncode != 0:
      self.skipTest("filefrag is unavailable")
    for line in completed.stdout.splitlines():
      stripped = line.strip()
      if stripped.startswith("0:"):
        return stripped.split()[3]
    self.fail("filefrag reported no extents for {}".format(path.name))

  def run_snapshot(self, *arguments):
    return subprocess.run(
      [str(PYTHON_BIN), str(SNAPSHOT_SCRIPT), *[str(a) for a in arguments]],
      capture_output=True,
      text=True,
    )

  def populate(self, media: Path):
    ##
    ## An ordinary recording, and the hidden state P18 put beside it. Both have
    ## to travel, because a library restored without its recovery journal and
    ## its quarantine is a library whose bookkeeping belongs to another moment.
    ##
    (media / "douyin" / "live" / "broadcaster").mkdir(parents=True)
    (media / "douyin" / "live" / "broadcaster" / "a.flv").write_bytes(b"recording")
    (media / ".smsd-recording-recovery").mkdir()
    (media / ".smsd-recording-recovery" / "k.json").write_text(
      '{"key": "k"}', encoding="utf-8"
    )
    (media / ".smsd-recording-orphan-quarantine").mkdir(mode=0o700)
    (media / ".smsd-recording-orphan-quarantine" / "q.flv").write_bytes(b"set aside")


class MediaSnapshotCreateTest(MediaSnapshotTestCase):
  def test_it_records_every_file_including_the_hidden_state(self):
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      media = root / "media"
      media.mkdir()
      self.populate(media)
      document_path = root / "media-snapshot.json"

      completed = self.run_snapshot(
        "create",
        "--media-root", media,
        "--snapshot-root", root / "snapshots",
        "--output", document_path,
      )

      if not reflink_supported(root):
        ##
        ## The scratch filesystem cannot clone, which is exactly the condition
        ## the script must refuse rather than work around.
        ##
        self.assertNotEqual(0, completed.returncode)
        self.assertIn("reflink", completed.stderr.lower())
        return

      self.assertEqual(0, completed.returncode, completed.stderr)
      document = json.loads(document_path.read_text(encoding="utf-8"))
      paths = {entry["relative_path"] for entry in document["entries"]}

      self.assertIn("douyin/live/broadcaster/a.flv", paths)
      self.assertIn(".smsd-recording-recovery/k.json", paths)
      self.assertIn(".smsd-recording-orphan-quarantine/q.flv", paths)
      self.assertEqual(len(document["entries"]), document["entry_count"])

  def test_every_entry_carries_the_identity_a_restore_is_judged_against(self):
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      media = root / "media"
      media.mkdir()
      self.populate(media)
      document_path = root / "media-snapshot.json"

      completed = self.run_snapshot(
        "create",
        "--media-root", media,
        "--snapshot-root", root / "snapshots",
        "--output", document_path,
      )
      if not reflink_supported(root):
        self.skipTest("the scratch filesystem cannot reflink")

      self.assertEqual(0, completed.returncode, completed.stderr)
      document = json.loads(document_path.read_text(encoding="utf-8"))
      for entry in document["entries"]:
        for field in ("relative_path", "size", "mtime_ns", "device", "inode"):
          self.assertIn(field, entry)

  ##
  ## The snapshot shares extents rather than duplicating them. Proven by
  ## measuring, because "it should be cheap" is what a full copy also claims
  ## right up until the disk fills.
  ##
  def test_the_snapshot_shares_extents_with_the_media(self):
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      if not reflink_supported(root):
        self.skipTest("the scratch filesystem cannot reflink")
      media = root / "media"
      media.mkdir()
      self.populate(media)
      payload = media / "large.flv"
      payload.write_bytes(b"x" * (4 * 1024 * 1024))

      completed = self.run_snapshot(
        "create",
        "--media-root", media,
        "--snapshot-root", root / "snapshots",
        "--output", root / "media-snapshot.json",
      )

      self.assertEqual(0, completed.returncode, completed.stderr)
      snapshot = sorted((root / "snapshots").iterdir())[0]
      clone = snapshot / "large.flv"
      self.assertTrue(clone.is_file())
      ##
      ## Same bytes, different inode, and the blocks charged once rather than
      ## twice.
      ##
      self.assertEqual(payload.read_bytes(), clone.read_bytes())
      self.assertNotEqual(os.stat(payload).st_ino, os.stat(clone).st_ino)
      ##
      ## Sharing is proven by where the blocks are, not by how many each file
      ## reports: XFS charges a shared extent to every file that maps it, so
      ## ``st_blocks`` looks identical whether or not the data was copied. The
      ## physical extent is the thing that differs.
      ##
      self.assertEqual(
        self.first_physical_extent(payload),
        self.first_physical_extent(clone),
        "the snapshot does not share extents with the media",
      )

  def test_a_destination_that_cannot_reflink_is_refused_not_copied(self):
    ##
    ## ``/dev/shm`` is tmpfs, which has no reflink. A fallback copy is exactly
    ## what must not happen here.
    ##
    shared = Path("/dev/shm")
    if not shared.is_dir() or not os.access(shared, os.W_OK):
      self.skipTest("no tmpfs available to prove the refusal")
    with tempfile.TemporaryDirectory(dir=shared) as directory:
      root = Path(directory)
      media = root / "media"
      media.mkdir()
      self.populate(media)

      completed = self.run_snapshot(
        "create",
        "--media-root", media,
        "--snapshot-root", root / "snapshots",
        "--output", root / "media-snapshot.json",
      )

      self.assertNotEqual(0, completed.returncode)
      ##
      ## The *probe's* refusal, named specifically. A generic "reflink" match
      ## would also be satisfied by the clone failing later, which is a weaker
      ## guarantee: it would mean the destination was never checked and the
      ## refusal came from cp giving up partway through a tree.
      ##
      self.assertIn("does not support reflink", completed.stderr)
      self.assertFalse(
        (root / "media-snapshot.json").exists(),
        "a document was written for a snapshot that was refused",
      )
      ##
      ## And nothing half-made was left behind for a later release to mistake
      ## for a complete capture.
      ##
      snapshots = root / "snapshots"
      if snapshots.exists():
        self.assertEqual(
          [], sorted(p.name for p in snapshots.iterdir()),
          "a partial snapshot survived a refused clone",
        )

  def test_the_filesystem_root_is_never_snapshotted(self):
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      completed = self.run_snapshot(
        "create",
        "--media-root", "/",
        "--snapshot-root", root / "snapshots",
        "--output", root / "media-snapshot.json",
      )

      self.assertNotEqual(0, completed.returncode)

  ##
  ## >>============ where a snapshot is allowed to live ============>>
  ##
  ## Reflink only works within one filesystem, and the media root *is* the
  ## mount point of its filesystem. So the snapshot store has to sit inside the
  ## media root - there is nowhere else on that disk - and everything below is
  ## about making that safe rather than pretending it can be avoided.
  ##

  def test_a_hidden_snapshot_root_inside_the_media_root_is_allowed(self):
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      if not reflink_supported(root):
        self.skipTest("the scratch filesystem cannot reflink")
      media = root / "media"
      media.mkdir()
      self.populate(media)

      completed = self.run_snapshot(
        "create",
        "--media-root", media,
        "--snapshot-root", media / ".smsd-release-snapshot",
        "--output", root / "media-snapshot.json",
      )

      self.assertEqual(0, completed.returncode, completed.stderr)

  def test_a_visible_snapshot_root_inside_the_media_root_is_refused(self):
    ##
    ## The application's orphan scan descends into any directory whose name is
    ## not hidden. A visible snapshot store would be walked as if it were media,
    ## and every cloned recording would be offered as an orphan candidate.
    ##
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      media = root / "media"
      media.mkdir()
      self.populate(media)

      completed = self.run_snapshot(
        "create",
        "--media-root", media,
        "--snapshot-root", media / "snapshots",
        "--output", root / "media-snapshot.json",
      )

      self.assertNotEqual(0, completed.returncode)
      self.assertIn("hidden", completed.stderr.lower())

  def test_the_application_scan_really_excludes_a_hidden_snapshot_root(self):
    ##
    ## Pinned against the production rule rather than restated, so the two
    ## cannot drift into disagreeing about what is scanned.
    ##
    from backend.src.service.recording_orphan import (
      _is_scannable_directory_name,
    )

    self.assertFalse(_is_scannable_directory_name(".smsd-release-snapshot"))
    self.assertTrue(_is_scannable_directory_name("snapshots"))

  def test_a_snapshot_root_on_another_filesystem_is_refused(self):
    ##
    ## Reflink cannot cross a filesystem, so this would either fail obscurely or
    ## silently become the byte copy that must never happen.
    ##
    shared = Path("/dev/shm")
    if not shared.is_dir() or not os.access(shared, os.W_OK):
      self.skipTest("no second filesystem available")
    with tempfile.TemporaryDirectory() as directory, \
         tempfile.TemporaryDirectory(dir=shared) as elsewhere:
      root = Path(directory)
      media = root / "media"
      media.mkdir()
      self.populate(media)

      completed = self.run_snapshot(
        "create",
        "--media-root", media,
        "--snapshot-root", Path(elsewhere) / ".snapshots",
        "--output", root / "media-snapshot.json",
      )

      self.assertNotEqual(0, completed.returncode)
      self.assertIn("filesystem", completed.stderr.lower())

  def test_the_snapshot_store_is_never_cloned_into_itself(self):
    ##
    ## The store lives inside the tree being cloned, so without an explicit
    ## exclusion every release would nest the release before it until the media
    ## root was mostly its own history.
    ##
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      if not reflink_supported(root):
        self.skipTest("the scratch filesystem cannot reflink")
      media = root / "media"
      media.mkdir()
      self.populate(media)
      store = media / ".smsd-release-snapshot"

      first = self.run_snapshot(
        "create", "--media-root", media, "--snapshot-root", store,
        "--output", root / "first.json",
      )
      self.assertEqual(0, first.returncode, first.stderr)
      second = self.run_snapshot(
        "create", "--media-root", media, "--snapshot-root", store,
        "--output", root / "second.json",
      )
      self.assertEqual(0, second.returncode, second.stderr)

      document = json.loads((root / "second.json").read_text(encoding="utf-8"))
      paths = [entry["relative_path"] for entry in document["entries"]]
      for path in paths:
        self.assertFalse(
          path.startswith(".smsd-release-snapshot"),
          "the snapshot store was cloned into the snapshot: {}".format(path),
        )


  ##
  ## A clone that fails partway must leave nothing. A half-made snapshot that
  ## looks like a whole one is the failure the whole helper exists to prevent:
  ## the next release would find a plausible directory and describe it.
  ##
  def test_a_clone_that_fails_partway_leaves_no_snapshot_behind(self):
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      if not reflink_supported(root):
        self.skipTest("the scratch filesystem cannot reflink")
      media = root / "media"
      media.mkdir()
      self.populate(media)
      ##
      ## An entry cp cannot read. The clone of the tree fails after some of it
      ## has already been written.
      ##
      unreadable = media / "unreadable"
      unreadable.mkdir()
      (unreadable / "a.flv").write_bytes(b"x")
      unreadable.chmod(0o000)

      completed = self.run_snapshot(
        "create",
        "--media-root", media,
        "--snapshot-root", root / "snapshots",
        "--output", root / "media-snapshot.json",
      )

      ##
      ## Restored before anything else looks at the tree, so the temporary
      ## directory can still be cleaned up afterwards.
      ##
      unreadable.chmod(0o700)

      self.assertNotEqual(0, completed.returncode)
      snapshots = root / "snapshots"
      if snapshots.exists():
        self.assertEqual(
          [], sorted(item.name for item in snapshots.iterdir()),
          "a partial snapshot survived a failed clone",
        )
      self.assertFalse((root / "media-snapshot.json").exists())


class MediaSnapshotVerifyTest(MediaSnapshotTestCase):
  def create(self, root: Path):
    media = root / "media"
    media.mkdir()
    self.populate(media)
    document = root / "media-snapshot.json"
    completed = self.run_snapshot(
      "create",
      "--media-root", media,
      "--snapshot-root", root / "snapshots",
      "--output", document,
    )
    self.assertEqual(0, completed.returncode, completed.stderr)
    snapshot = sorted((root / "snapshots").iterdir())[0]
    return document, snapshot

  def test_an_untouched_snapshot_verifies(self):
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      if not reflink_supported(root):
        self.skipTest("the scratch filesystem cannot reflink")
      document, snapshot = self.create(root)

      completed = self.run_snapshot(
        "verify", "--snapshot-path", snapshot, "--document", document
      )

      self.assertEqual(0, completed.returncode, completed.stderr)

  def test_a_file_removed_from_the_snapshot_is_caught(self):
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      if not reflink_supported(root):
        self.skipTest("the scratch filesystem cannot reflink")
      document, snapshot = self.create(root)
      (snapshot / "douyin" / "live" / "broadcaster" / "a.flv").unlink()

      completed = self.run_snapshot(
        "verify", "--snapshot-path", snapshot, "--document", document
      )

      self.assertNotEqual(0, completed.returncode)

  def test_a_file_substituted_in_the_snapshot_is_caught(self):
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      if not reflink_supported(root):
        self.skipTest("the scratch filesystem cannot reflink")
      document, snapshot = self.create(root)
      target = snapshot / "douyin" / "live" / "broadcaster" / "a.flv"
      identity = os.stat(target)
      ##
      ## Same size and same modification time, different inode - the exact
      ## substitution the identity fields exist to refuse.
      ##
      replacement = snapshot / "replacement.bin"
      replacement.write_bytes(b"x" * identity.st_size)
      os.utime(replacement, ns=(identity.st_mtime_ns, identity.st_mtime_ns))
      target.unlink()
      os.link(replacement, target)
      replacement.unlink()

      completed = self.run_snapshot(
        "verify", "--snapshot-path", snapshot, "--document", document
      )

      self.assertNotEqual(0, completed.returncode)


if __name__ == "__main__":
  unittest.main()
