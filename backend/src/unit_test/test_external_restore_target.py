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

  def test_a_disposable_name_that_is_still_the_source_is_refused(self):
    ##
    ## Isolates the "differs from the source" rule from the name pattern.
    ##
    ## A source that already looks disposable is not hypothetical: it is what a
    ## second drill run against the output of the first one looks like. With
    ## only the pattern check, restoring a drill's own bundle back over itself
    ## would be permitted, and the rule that the destination must be a
    ## *different* place would never be exercised by any test.
    ##
    with self.assertRaises(ValueError):
      self.module.validate_external_restore_target(
        database="smsd_restore_test_drill01",
        media_root="/srv/restore-drill/second",
        source_database="smsd_restore_test_drill01",
        source_media_root="/srv/restore-drill/first",
      )

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


##
## >>=============== identity, not spelling ===============>>
##
## The guards used to compare normalised text. ``normpath`` is pure string work
## - it collapses ``.`` and ``..`` and knows nothing about links - so a
## destination that was a symbolic link into the live library passed every check
## and would have written the restore into the one tree it was forbidden to
## touch. These are real links on a real filesystem, because a mocked one would
## only prove that the mock behaves the way the code assumes.
##
class ExternalRestoreTargetIdentityTest(unittest.TestCase):
  def setUp(self):
    self.module = bundle_module()
    self.root = Path(tempfile.mkdtemp())
    self.addCleanup(__import__("shutil").rmtree, self.root, True)
    self.live = self.root / "live-media"
    (self.live / "douyin").mkdir(parents=True)
    ##
    ## An *empty* subdirectory of the library, which is the case a
    ## non-emptiness check alone would happily accept.
    ##
    self.empty_live_subdirectory = self.live / "empty"
    self.empty_live_subdirectory.mkdir()

  def validate(self, media_root):
    self.module.validate_external_restore_target(
      database="smsd_restore_test_drill",
      media_root=str(media_root),
      source_database="smsd",
      source_media_root=str(self.live),
    )

  def test_a_symlink_into_the_live_media_root_is_refused(self):
    link = self.root / "restore"
    link.symlink_to(self.empty_live_subdirectory)

    with self.assertRaises(ValueError):
      self.validate(link)

  def test_a_symlinked_ancestor_resolving_into_the_live_media_is_refused(self):
    ##
    ## The destination itself is an ordinary name. Its parent is the link, so
    ## the path the kernel would write to is inside the library and the spelling
    ## gives no sign of it.
    ##
    link = self.root / "staging"
    link.symlink_to(self.live)

    with self.assertRaises(ValueError):
      self.validate(link / "restored")

  def test_a_symlink_to_the_live_media_root_itself_is_refused(self):
    link = self.root / "restore-root"
    link.symlink_to(self.live)

    with self.assertRaises(ValueError):
      self.validate(link)

  ##
  ## The symlink rule, isolated.
  ##
  ## This link points somewhere harmless - not into the library, not near it -
  ## so every path comparison is satisfied and only "the destination must not be
  ## a symbolic link" objects. Without this case, deleting that rule changed
  ## nothing: the other symlink tests were all caught by the resolved-path
  ## comparison instead.
  ##
  ## Refusing it is the point rather than an accident. A link can be repointed
  ## between the check and the write, and a destination whose spelling is not
  ## the directory written to is one an operator cannot reason about.
  ##
  def test_a_symlink_is_refused_even_when_it_points_somewhere_harmless(self):
    elsewhere = self.root / "somewhere-else"
    elsewhere.mkdir()
    link = self.root / "restore-link"
    link.symlink_to(elsewhere)

    with self.assertRaises(ValueError):
      self.validate(link)

    ##
    ## And the same destination, named directly, is fine - so the refusal is
    ## about the link and not about the place it leads.
    ##
    self.validate(elsewhere)

  ##
  ## The resolved-against-resolved comparison, isolated.
  ##
  ## Both roots are reached through different links to the same real directory.
  ## Comparing the two spellings finds nothing; comparing either spelling
  ## against the other's resolved form finds nothing; only resolving both ends
  ## shows that the destination is inside the library.
  ##
  def test_two_different_links_to_one_directory_are_still_one_directory(self):
    real_live = self.root / "real-live"
    (real_live / "inside").mkdir(parents=True)
    source_link = self.root / "source-link"
    source_link.symlink_to(real_live)
    target_link = self.root / "target-link"
    target_link.symlink_to(real_live)

    with self.assertRaises(ValueError):
      self.module.validate_external_restore_target(
        database="smsd_restore_test_drill",
        media_root=str(target_link / "inside"),
        source_database="smsd",
        source_media_root=str(source_link),
      )

  ##
  ## Any symlink, not only one that points somewhere dangerous.
  ##
  ## A destination that resolves elsewhere is a destination whose emptiness and
  ## filesystem were checked against a different directory than the one that
  ## will be written. Refusing only the links that happen to reach the live
  ## library leaves the rest of that reasoning resting on where the link points
  ## today.
  ##
  def test_a_symlink_to_a_harmless_directory_is_still_refused(self):
    elsewhere = self.root / "somewhere-else"
    elsewhere.mkdir()
    link = self.root / "restore"
    link.symlink_to(elsewhere)

    with self.assertRaises(ValueError):
      self.validate(link)

  ##
  ## The case that only resolving *both* ends can catch.
  ##
  ## The library is named through a symlink to it, and the destination sits
  ## under a symlinked ancestor. The literal pair shares no prefix, and each
  ## crossed pair still has one unresolved half, so none of those three match.
  ## Only resolving both ends shows the restore would land inside the library.
  ##
  def test_a_destination_and_a_source_both_spelled_through_links_are_refused(self):
    staging = self.root / "staging"
    staging.symlink_to(self.live)
    source_link = self.root / "live-link"
    source_link.symlink_to(self.live)

    with self.assertRaises(ValueError):
      self.module.validate_external_restore_target(
        database="smsd_restore_test_drill",
        media_root=str(staging / "restored"),
        source_database="smsd",
        source_media_root=str(source_link),
      )

  def test_a_destination_containing_the_live_media_root_is_refused(self):
    with self.assertRaises(ValueError):
      self.validate(self.root)

  def test_a_genuinely_separate_destination_is_accepted(self):
    self.validate(self.root / "restore-here")

  ##
  ## And the same substitution against the emptiness check, which follows links
  ## and would otherwise answer for whatever is on the other end.
  ##
  def test_an_empty_destination_that_is_a_symlink_is_refused(self):
    link = self.root / "empty-link"
    link.symlink_to(self.empty_live_subdirectory)

    with self.assertRaises(ValueError):
      self.module.require_empty_restore_destination(link)

  def test_a_destination_that_does_not_exist_yet_is_accepted(self):
    self.module.require_empty_restore_destination(self.root / "absent")


if __name__ == "__main__":
  unittest.main()
