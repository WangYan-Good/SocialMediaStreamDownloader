##<<Base>>
import os
import tempfile
import unittest
from pathlib import Path

##<<Third-part>>
from backend.src.service.media_asset import (
  MAX_POST_ASSET_SCAN_ENTRIES,
  MediaAssetResolver,
  StorageState,
)


AWEME = "7657271784144009946"


def write(path: Path, size: int = 8) -> Path:
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_bytes(b"x" * size)
  return path


class ResolverCase(unittest.TestCase):
  def setUp(self):
    self._temporary = tempfile.TemporaryDirectory()
    self.base = Path(os.path.realpath(self._temporary.name))
    self.root = self.base / "downloads"
    self.root.mkdir()
    self.resolver = MediaAssetResolver(lambda: str(self.root))

  def tearDown(self):
    self._temporary.cleanup()

  def post_dir(self, name="creator") -> Path:
    directory = self.root / name
    directory.mkdir(parents=True, exist_ok=True)
    return directory


class TestPostDiscovery(ResolverCase):
  def test_a_video_post_reports_its_three_files(self):
    directory = self.post_dir()
    write(directory / "20260824_{}.mp4".format(AWEME), 100)
    write(directory / "20260824_{}_music.mp3".format(AWEME), 50)
    write(directory / "20260824_{}_cover.jpg".format(AWEME), 20)

    found = self.resolver.post_assets(str(directory), "douyin", AWEME)

    self.assertEqual(StorageState.AVAILABLE, found.storage_state)
    self.assertEqual(["video", "music", "cover"], [one.kind for one in found.assets])
    self.assertEqual([100, 50, 20], [one.size_bytes for one in found.assets])
    self.assertEqual("video/mp4", found.assets[0].media_type)
    self.assertEqual("audio/mpeg", found.assets[1].media_type)
    self.assertEqual("image/jpeg", found.assets[2].media_type)
    for one in found.assets:
      self.assertTrue(one.asset_id)

  def test_an_image_post_orders_its_pictures_by_position(self):
    directory = self.post_dir()
    ##
    ## Written out of order on purpose: the answer must not depend on what the
    ## filesystem hands back first.
    ##
    write(directory / "20260824_{}_02.jpg".format(AWEME))
    write(directory / "20260824_{}_01.jpg".format(AWEME))
    write(directory / "20260824_{}_music.mp3".format(AWEME))
    write(directory / "20260824_{}_cover.jpg".format(AWEME))

    found = self.resolver.post_assets(str(directory), "douyin", AWEME)

    self.assertEqual(
      ["image", "image", "music", "cover"], [one.kind for one in found.assets]
    )
    self.assertEqual([1, 2], [one.image_index for one in found.assets[:2]])
    ##
    ## The cover is a jpg carrying the id too, and must not be counted as a
    ## third picture.
    ##
    self.assertEqual(2, len([one for one in found.assets if one.kind == "image"]))

  def test_the_order_is_the_same_on_every_request(self):
    directory = self.post_dir()
    for name in ("_03.jpg", "_01.jpg", "_02.jpg"):
      write(directory / "20260824_{}{}".format(AWEME, name))

    first = self.resolver.post_assets(str(directory), "douyin", AWEME)
    second = self.resolver.post_assets(str(directory), "douyin", AWEME)

    self.assertEqual(
      [one.asset_id for one in first.assets], [one.asset_id for one in second.assets]
    )

  def test_nothing_but_this_posts_media_is_reported(self):
    directory = self.post_dir()
    write(directory / "20260824_{}.mp4".format(AWEME))
    ##
    ## Everything a real post directory also contains.
    ##
    write(directory / "info.txt")
    write(directory / "notes.json")
    write(directory / "unrelated.jpg")
    write(directory / "20260824_7000000000000000001.mp4")
    write(directory / "nested" / "20260824_{}.mp4".format(AWEME))

    found = self.resolver.post_assets(str(directory), "douyin", AWEME)

    self.assertEqual(1, len(found.assets))
    self.assertEqual("video", found.assets[0].kind)

  def test_a_nested_directory_is_not_descended_into(self):
    ##
    ## One post's media lives in one directory. Recursing would widen the read
    ## surface for nothing and make a deep tree somebody planted expensive.
    ##
    directory = self.post_dir()
    write(directory / "deep" / "deeper" / "20260824_{}.mp4".format(AWEME))

    found = self.resolver.post_assets(str(directory), "douyin", AWEME)

    self.assertEqual(StorageState.EMPTY, found.storage_state)
    self.assertEqual((), found.assets)

  def test_a_legacy_caption_name_is_still_found(self):
    directory = self.post_dir()
    write(directory / "20240101_一个很长的作品文案_{}_01.jpg".format(AWEME))

    found = self.resolver.post_assets(str(directory), "douyin", AWEME)

    self.assertEqual(StorageState.AVAILABLE, found.storage_state)
    self.assertEqual("image", found.assets[0].kind)


class TestPostStorageStates(ResolverCase):
  def test_a_directory_that_is_gone_is_missing(self):
    found = self.resolver.post_assets(
      str(self.root / "never-existed"), "douyin", AWEME
    )

    self.assertEqual(StorageState.MISSING, found.storage_state)
    self.assertEqual((), found.assets)

  def test_a_directory_holding_no_media_is_empty(self):
    directory = self.post_dir()
    write(directory / "info.txt")

    found = self.resolver.post_assets(str(directory), "douyin", AWEME)

    self.assertEqual(StorageState.EMPTY, found.storage_state)

  def test_a_recorded_path_that_is_a_file_is_unavailable(self):
    ##
    ## save_dir naming a regular file is a record this program cannot make
    ## sense of, and listing it is not possible.
    ##
    target = write(self.root / "a-file.mp4")

    found = self.resolver.post_assets(str(target), "douyin", AWEME)

    self.assertEqual(StorageState.UNAVAILABLE, found.storage_state)

  def test_an_empty_recorded_path_is_unavailable(self):
    for empty in (None, "", "   "):
      found = self.resolver.post_assets(empty, "douyin", AWEME)
      self.assertEqual(StorageState.UNAVAILABLE, found.storage_state)


class TestPostRootEscape(ResolverCase):
  def assert_refused(self, recorded):
    found = self.resolver.post_assets(str(recorded), "douyin", AWEME)

    self.assertEqual(StorageState.UNAVAILABLE, found.storage_state, recorded)
    self.assertEqual((), found.assets)

  def test_a_traversal_out_of_the_root_is_refused(self):
    secret = self.base / "secret"
    write(secret / "20260824_{}.mp4".format(AWEME))

    self.assert_refused("../secret")

  def test_an_absolute_path_outside_the_root_is_refused(self):
    secret = self.base / "secret"
    write(secret / "20260824_{}.mp4".format(AWEME))

    self.assert_refused(secret)

  def test_a_sibling_sharing_the_roots_prefix_is_refused(self):
    ##
    ## /…/downloads-evil is not inside /…/downloads, however the two strings
    ## compare.
    ##
    evil = self.base / "downloads-evil"
    write(evil / "20260824_{}.mp4".format(AWEME))

    self.assert_refused(evil)

  def test_a_directory_symlinked_out_of_the_root_is_refused(self):
    secret = self.base / "secret"
    write(secret / "20260824_{}.mp4".format(AWEME))
    link = self.root / "escape"
    os.symlink(secret, link)

    self.assert_refused(link)


class TestPostSymlinkedFiles(ResolverCase):
  def test_a_symlinked_media_file_is_never_an_asset(self):
    ##
    ## The directory is legitimately inside the root; one entry in it points
    ## somewhere else entirely. The real file is reported, the link is not.
    ##
    directory = self.post_dir()
    write(directory / "20260824_{}.mp4".format(AWEME), 30)
    secret = write(self.base / "secret" / "leak.mp4", 900)
    os.symlink(secret, directory / "20260824_{}_01.jpg".format(AWEME))

    found = self.resolver.post_assets(str(directory), "douyin", AWEME)

    self.assertEqual(1, len(found.assets))
    self.assertEqual("video", found.assets[0].kind)
    self.assertEqual(30, found.assets[0].size_bytes)

  def test_a_symlink_pointing_inside_the_root_is_still_not_an_asset(self):
    ##
    ## Refused for being a link at all rather than for where it leads. A link
    ## is a second name for a file, and following one would let a post claim
    ## another post's media as its own.
    ##
    directory = self.post_dir()
    real = write(self.root / "other" / "real.mp4")
    os.symlink(real, directory / "20260824_{}.mp4".format(AWEME))

    found = self.resolver.post_assets(str(directory), "douyin", AWEME)

    self.assertEqual(StorageState.EMPTY, found.storage_state)


class TestScanBound(ResolverCase):
  def test_a_directory_beyond_the_cap_stops_rather_than_counting(self):
    directory = self.post_dir()
    for index in range(MAX_POST_ASSET_SCAN_ENTRIES + 5):
      write(directory / "filler_{}.bin".format(index), 1)

    found = self.resolver.post_assets(str(directory), "douyin", AWEME)

    self.assertEqual(StorageState.UNAVAILABLE, found.storage_state)
    self.assertEqual((), found.assets)


class TestRecordingDiscovery(ResolverCase):
  def test_a_recorded_flv_is_one_asset(self):
    target = write(self.root / "creator" / "live.flv", 4096)

    found = self.resolver.recording_asset(str(target), 7)

    self.assertEqual(StorageState.AVAILABLE, found.storage_state)
    self.assertEqual(1, len(found.assets))
    self.assertEqual("recording", found.assets[0].kind)
    self.assertEqual("live.flv", found.assets[0].name)
    self.assertEqual(4096, found.assets[0].size_bytes)
    self.assertEqual("video/x-flv", found.assets[0].media_type)

  def test_a_recorded_ts_is_one_asset(self):
    target = write(self.root / "creator" / "live.ts")

    found = self.resolver.recording_asset(str(target), 7)

    self.assertEqual("video/mp2t", found.assets[0].media_type)

  def test_an_mp4_recording_is_named_from_the_file_on_disk(self):
    ##
    ## The extension that is actually there, never one inferred from the
    ## protocol column: the disk is the current fact.
    ##
    target = write(self.root / "creator" / "live.mp4")

    found = self.resolver.recording_asset(str(target), 7)

    self.assertEqual("video/mp4", found.assets[0].media_type)

  def test_an_unknown_extension_falls_back_to_octet_stream(self):
    target = write(self.root / "creator" / "live.weird")

    found = self.resolver.recording_asset(str(target), 7)

    self.assertEqual("application/octet-stream", found.assets[0].media_type)

  def test_the_parent_directory_is_never_listed(self):
    ##
    ## A recording knows exactly which file it wrote. Everything beside it
    ## belongs to other recordings, and listing them would report one user's
    ## recording under another's resource.
    ##
    directory = self.root / "creator"
    target = write(directory / "live.flv")
    write(directory / "someone-elses.flv")
    write(directory / "another.ts")

    found = self.resolver.recording_asset(str(target), 7)

    self.assertEqual(1, len(found.assets))
    self.assertEqual("live.flv", found.assets[0].name)

  def test_a_recording_that_is_gone_is_missing(self):
    found = self.resolver.recording_asset(str(self.root / "gone.flv"), 7)

    self.assertEqual(StorageState.MISSING, found.storage_state)
    self.assertEqual((), found.assets)

  def test_a_recording_outside_the_root_is_unavailable(self):
    outside = write(self.base / "secret" / "live.flv")

    found = self.resolver.recording_asset(str(outside), 7)

    self.assertEqual(StorageState.UNAVAILABLE, found.storage_state)
    self.assertEqual((), found.assets)

  def test_a_symlinked_recording_is_unavailable(self):
    real = write(self.base / "secret" / "live.flv")
    link = self.root / "creator" / "live.flv"
    link.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(real, link)

    found = self.resolver.recording_asset(str(link), 7)

    self.assertEqual(StorageState.UNAVAILABLE, found.storage_state)

  def test_a_directory_recorded_as_an_output_path_is_unavailable(self):
    directory = self.root / "creator"
    directory.mkdir(parents=True, exist_ok=True)

    found = self.resolver.recording_asset(str(directory), 7)

    self.assertEqual(StorageState.UNAVAILABLE, found.storage_state)

  def test_an_empty_recorded_path_is_unavailable(self):
    for empty in (None, "", "   "):
      found = self.resolver.recording_asset(empty, 7)
      self.assertEqual(StorageState.UNAVAILABLE, found.storage_state)


class TestNothingLeaksAPath(ResolverCase):
  def test_an_asset_carries_a_name_but_never_a_location(self):
    directory = self.post_dir()
    write(directory / "20260824_{}.mp4".format(AWEME))

    found = self.resolver.post_assets(str(directory), "douyin", AWEME)
    asset = found.assets[0]

    rendered = repr(asset.as_dict())
    self.assertNotIn(str(self.root), rendered)
    self.assertNotIn(str(directory), rendered)
    self.assertEqual(
      {"asset_id", "kind", "name", "size_bytes", "media_type", "image_index"},
      set(asset.as_dict().keys()),
    )


if __name__ == "__main__":
  unittest.main()
