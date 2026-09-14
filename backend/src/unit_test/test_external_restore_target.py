##
## The guard that keeps a restore drill away from production.
##
## The Compose restore has one of these already: a restore project must match
## ``smsd-restore-test-*`` and must differ from the source, so the drill cannot
## be pointed at the live stack even by a typo. That guard works because in
## Compose a project name *is* the destination - the database and the volume
## both hang off it.
##
## Externally there is no project. The destination is a database name on a host
## and a directory on a filesystem, and both of them can be the live ones. A
## drill run with the production database name would import a backup over
## production; one run with ``/mnt/video`` would unpack a snapshot over two
## terabytes of media. Neither is recoverable, and neither is a typo away from
## impossible - they are a typo away from happening.
##
## So the same idea, restated for two destinations instead of one: an explicit
## disposable name, never the source, and a media root that is not the live one
## and not inside it.
##
import importlib.util
from pathlib import Path
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BUNDLE_HELPER = PROJECT_ROOT / "scripts" / "release_bundle.py"


def bundle_module():
  specification = importlib.util.spec_from_file_location(
    "release_bundle_restore_target", BUNDLE_HELPER
  )
  module = importlib.util.module_from_spec(specification)
  specification.loader.exec_module(module)
  return module


class ExternalRestoreTargetTest(unittest.TestCase):
  def setUp(self):
    self.module = bundle_module()
    self.source_database = "social_media_stream_downloader_v2"
    self.source_media = "/mnt/video"

  def validate(self, database, media_root):
    return self.module.validate_external_restore_target(
      database=database,
      media_root=media_root,
      source_database=self.source_database,
      source_media_root=self.source_media,
    )

  def test_an_explicit_disposable_target_is_accepted(self):
    self.validate("smsd_restore_test_drill01", "/srv/restore-drill/media")

  ##
  ## >>==================== the database destination ====================>>
  ##

  def test_the_live_database_name_is_refused(self):
    with self.assertRaises(ValueError):
      self.validate(self.source_database, "/srv/restore-drill/media")

  def test_a_name_that_is_not_explicitly_disposable_is_refused(self):
    for name in ("", "smsd", "production", "social_media_stream_downloader_v3",
                 "restore_test", "smsd_restore_test_"):
      with self.subTest(database=name):
        with self.assertRaises(ValueError):
          self.validate(name, "/srv/restore-drill/media")

  ##
  ## >>====================== the media destination ======================>>
  ##

  def test_the_live_media_root_is_refused(self):
    with self.assertRaises(ValueError):
      self.validate("smsd_restore_test_drill01", self.source_media)

  def test_a_destination_inside_the_live_media_root_is_refused(self):
    ##
    ## Restoring into a subdirectory of the library would interleave a
    ## snapshot's files with the live ones, and the orphan scan would then be
    ## asked to decide which of two identical trees is real.
    ##
    for path in ("/mnt/video/restore", "/mnt/video/douyin/live/restore"):
      with self.subTest(media_root=path):
        with self.assertRaises(ValueError):
          self.validate("smsd_restore_test_drill01", path)

  def test_the_live_media_root_is_refused_through_a_relative_spelling(self):
    ##
    ## The same directory reached by a different sentence. Compared after
    ## normalisation, or the guard only refuses the spellings somebody thought
    ## of.
    ##
    for path in ("/mnt/video/", "/mnt/video/.", "/mnt/./video", "/mnt/video/x/.."):
      with self.subTest(media_root=path):
        with self.assertRaises(ValueError):
          self.validate("smsd_restore_test_drill01", path)

  def test_a_relative_media_root_is_refused(self):
    with self.assertRaises(ValueError):
      self.validate("smsd_restore_test_drill01", "restore/media")

  def test_the_filesystem_root_is_refused(self):
    with self.assertRaises(ValueError):
      self.validate("smsd_restore_test_drill01", "/")

  ##
  ## >>================ and the destination must be empty ================>>
  ##
  ## A guard on the *name* says the operator meant a drill. It says nothing
  ## about whether something is already there, and restoring on top of an
  ## existing tree is how a drill quietly becomes a merge.
  ##

  def test_an_existing_populated_destination_is_refused(self):
    with tempfile.TemporaryDirectory() as directory:
      occupied = Path(directory) / "media"
      occupied.mkdir()
      (occupied / "something.flv").write_bytes(b"already here")

      with self.assertRaises(ValueError):
        self.module.require_empty_restore_destination(occupied)

  def test_an_absent_destination_is_accepted(self):
    with tempfile.TemporaryDirectory() as directory:
      self.module.require_empty_restore_destination(
        Path(directory) / "not-yet-there"
      )

  def test_an_existing_empty_destination_is_accepted(self):
    with tempfile.TemporaryDirectory() as directory:
      empty = Path(directory) / "media"
      empty.mkdir()

      self.module.require_empty_restore_destination(empty)


if __name__ == "__main__":
  unittest.main()
