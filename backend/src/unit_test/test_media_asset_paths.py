##<<Base>>
import os
import unittest

##<<Third-part>>
from backend.src.service.media_asset import (
  MAX_POST_ASSET_SCAN_ENTRIES,
  StorageState,
  asset_id_for,
  contained_path,
  recognise_post_file,
)


##
## >>============================= the trust boundary =============================>>
##
##
## Everything below the database is untrusted here.
##
## ``save_dir`` and ``output_path`` are strings a downloader wrote months ago.
## They are not attacker-supplied in any ordinary sense - no client can send one
## - but they are the only thing standing between a request and the filesystem,
## and this phase is where that boundary is drawn. A recorded path that escapes
## the configured download root has to be refused, whether it escapes by
## ``..``, by being absolute, by sharing a prefix with the root, or by a symlink
## somewhere along the way.
##
## Phase 10B will serve bytes through this same boundary, so it is worth being
## exact now rather than later.
##


class TestContainment(unittest.TestCase):
  """Whether one path is genuinely inside the configured root."""

  def setUp(self):
    import tempfile

    self._temporary = tempfile.TemporaryDirectory()
    self.root = os.path.realpath(self._temporary.name)
    os.makedirs(os.path.join(self.root, "downloads"), exist_ok=True)
    self.download_root = os.path.join(self.root, "downloads")

  def tearDown(self):
    self._temporary.cleanup()

  def test_a_child_of_the_root_is_contained(self):
    inside = os.path.join(self.download_root, "creator", "file.mp4")

    self.assertIsNotNone(contained_path(self.download_root, inside))

  def test_the_root_itself_is_contained(self):
    self.assertIsNotNone(contained_path(self.download_root, self.download_root))

  def test_a_relative_recorded_path_is_resolved_against_the_root(self):
    ##
    ## Historical rows hold relative paths, because the configured save_path
    ## was itself relative. They are still legitimate.
    ##
    self.assertIsNotNone(contained_path(self.download_root, "creator/file.mp4"))

  def test_a_parent_traversal_is_refused(self):
    for escape in ("../secret", "../../etc/passwd", "creator/../../../etc"):
      self.assertIsNone(contained_path(self.download_root, escape), escape)

  def test_an_absolute_path_outside_the_root_is_refused(self):
    self.assertIsNone(contained_path(self.download_root, "/etc/passwd"))

  def test_a_sibling_sharing_the_roots_prefix_is_refused(self):
    ##
    ## The trap a string comparison falls into:
    ##
    ##     root      = /tmp/x/downloads
    ##     candidate = /tmp/x/downloads-evil/a.mp4
    ##
    ## `str(candidate).startswith(str(root))` says yes. It is a different
    ## directory.
    ##
    evil = os.path.join(self.root, "downloads-evil")
    os.makedirs(evil, exist_ok=True)

    self.assertIsNone(contained_path(self.download_root, os.path.join(evil, "a.mp4")))

  def test_a_symlink_pointing_outside_the_root_is_refused(self):
    outside = os.path.join(self.root, "secret")
    os.makedirs(outside, exist_ok=True)
    link = os.path.join(self.download_root, "escape")
    os.symlink(outside, link)

    self.assertIsNone(contained_path(self.download_root, link))

  def test_a_symlink_in_the_middle_of_the_path_cannot_escape(self):
    ##
    ## The one a naive check misses: the final component is innocent, and the
    ## directory above it is the door out.
    ##
    outside = os.path.join(self.root, "secret")
    os.makedirs(outside, exist_ok=True)
    with open(os.path.join(outside, "a.mp4"), "wb") as handle:
      handle.write(b"x")
    os.symlink(outside, os.path.join(self.download_root, "hop"))

    self.assertIsNone(
      contained_path(self.download_root, os.path.join(self.download_root, "hop", "a.mp4"))
    )

  def test_an_empty_or_missing_recorded_path_is_refused(self):
    for empty in (None, "", "   "):
      self.assertIsNone(contained_path(self.download_root, empty))


class TestPostFileRecognition(unittest.TestCase):
  """Which files in a post's directory belong to that post."""

  AWEME = "7657271784144009946"

  def test_the_current_naming_scheme_is_recognised(self):
    self.assertEqual(
      "video", recognise_post_file("20260824_{}.mp4".format(self.AWEME), self.AWEME)
    )
    self.assertEqual(
      "music",
      recognise_post_file("20260824_{}_music.mp3".format(self.AWEME), self.AWEME),
    )
    self.assertEqual(
      "cover",
      recognise_post_file("20260824_{}_cover.jpg".format(self.AWEME), self.AWEME),
    )
    self.assertEqual(
      "image",
      recognise_post_file("20260824_{}_01.jpg".format(self.AWEME), self.AWEME),
    )

  def test_a_cover_is_not_mistaken_for_an_image(self):
    ##
    ## Both are .jpg and both carry the id. Only the tail tells them apart, so
    ## the cover has to be decided before any generic image rule.
    ##
    self.assertEqual(
      "cover",
      recognise_post_file("20260824_{}_cover.jpg".format(self.AWEME), self.AWEME),
    )

  def test_a_legacy_name_carrying_a_caption_is_still_recognised(self):
    ##
    ## Older versions put the post's caption in the file name. Those files are
    ## on real disks today, and the downloader still recognises them by id plus
    ## stable tail - so discovery has to as well, or the interface will report
    ## "no media" for a directory that is full of it.
    ##
    legacy = "20240101_一个很长的作品文案_{}_01.jpg".format(self.AWEME)

    self.assertEqual("image", recognise_post_file(legacy, self.AWEME))

  def test_an_id_that_merely_appears_inside_another_id_is_not_recognised(self):
    ##
    ## The substring bug the downloader's own comment calls out: this id sits
    ## inside a longer one, and a plain `in` test would claim the file.
    ##
    longer = "9957657271784144009946"
    self.assertNotEqual(longer, self.AWEME)

    self.assertIsNone(recognise_post_file("20260824_{}.mp4".format(longer), self.AWEME))

  def test_a_file_for_a_different_post_is_not_recognised(self):
    self.assertIsNone(recognise_post_file("20260824_7000000000000000001.mp4", self.AWEME))

  def test_the_notes_file_is_never_media(self):
    ##
    ## info.txt sits beside the media in every post directory this program has
    ## ever written.
    ##
    self.assertIsNone(recognise_post_file("info.txt", self.AWEME))
    self.assertIsNone(
      recognise_post_file("{}_info.txt".format(self.AWEME), self.AWEME)
    )

  def test_unknown_kinds_are_not_media(self):
    for name in (
      "notes.json",
      "{}.txt".format(self.AWEME),
      "{}.partial".format(self.AWEME),
      ".hidden",
      "{}_01.jpg.tmp".format(self.AWEME),
      "{}.mp4.part".format(self.AWEME),
    ):
      self.assertIsNone(recognise_post_file(name, self.AWEME), name)

  def test_an_image_marker_must_be_numeric(self):
    ##
    ## `_music.mp3` and `_cover.jpg` are named kinds; `_NN.jpg` is a position.
    ## A word where the number should be is not an image.
    ##
    self.assertIsNone(
      recognise_post_file("20260824_{}_thumb.jpg".format(self.AWEME), self.AWEME)
    )


class TestAssetIdentity(unittest.TestCase):
  """A name for a file that does not disclose where the file is."""

  def test_it_is_stable_for_the_same_resource_and_file(self):
    first = asset_id_for("post", ("douyin", "123"), "a.mp4")
    second = asset_id_for("post", ("douyin", "123"), "a.mp4")

    self.assertEqual(first, second)

  def test_it_differs_between_resources_holding_the_same_file_name(self):
    ##
    ## Two posts can both contain `video.mp4`. Their assets must not share an
    ## id, or Phase 10B's lookup would be ambiguous.
    ##
    self.assertNotEqual(
      asset_id_for("post", ("douyin", "123"), "video.mp4"),
      asset_id_for("post", ("douyin", "456"), "video.mp4"),
    )

  def test_it_differs_between_files_in_the_same_resource(self):
    self.assertNotEqual(
      asset_id_for("post", ("douyin", "123"), "a.mp4"),
      asset_id_for("post", ("douyin", "123"), "b.mp4"),
    )

  def test_a_post_and_a_recording_never_collide(self):
    self.assertNotEqual(
      asset_id_for("post", ("douyin", "123"), "a.flv"),
      asset_id_for("recording", ("123",), "a.flv"),
    )

  def test_it_is_a_full_hex_digest(self):
    ##
    ## Not Python's hash(): that is randomised per process, so an id issued by
    ## one worker would not be recognised by another.
    ##
    value = asset_id_for("post", ("douyin", "123"), "a.mp4")

    self.assertEqual(64, len(value))
    self.assertTrue(all(character in "0123456789abcdef" for character in value))

  def test_it_carries_no_path(self):
    value = asset_id_for("post", ("douyin", "123"), "a.mp4")

    for leaked in ("/", "\\", "a.mp4", "douyin"):
      self.assertNotIn(leaked, value)


class TestVocabulary(unittest.TestCase):
  def test_the_four_storage_states_are_the_whole_vocabulary(self):
    self.assertEqual(
      {"available", "missing", "empty", "unavailable"},
      {state.value for state in StorageState},
    )

  def test_the_scan_cap_is_finite_and_generous(self):
    ##
    ## Above any real image post by a wide margin, and finite so a directory
    ## somebody filled with a million entries cannot hold a request open.
    ##
    self.assertGreater(MAX_POST_ASSET_SCAN_ENTRIES, 100)
    self.assertLess(MAX_POST_ASSET_SCAN_ENTRIES, 100000)


if __name__ == "__main__":
  unittest.main()
