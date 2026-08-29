##<<Base>>
import errno
import os
import stat
import tempfile
import unittest
from pathlib import Path

##<<Third-part>>
from backend.src.service.media_asset import (
  MediaAssetResolver,
  OpenedMediaAsset,
  SECURE_OPEN_SUPPORTED,
  StorageState,
  asset_id_for,
)


class SecureOpenTestCase(unittest.TestCase):
  """A root, a file inside it, and a secret outside it."""

  def setUp(self):
    self._tmp = tempfile.TemporaryDirectory()
    self.base = Path(self._tmp.name)
    self.root = self.base / "downloads"
    self.root.mkdir()
    ##
    ## Outside the root, and the thing every escape test is trying to reach.
    ## Asserting its absence is what makes those tests able to fail.
    ##
    self.secret = self.base / "secret.txt"
    self.secret.write_bytes(b"SECRET-OUTSIDE-ROOT")
    self.resolver = MediaAssetResolver(lambda: str(self.root))
    self.addCleanup(self._tmp.cleanup)

  def post_dir(self, aweme_id="aw1", nickname="creator"):
    directory = self.root / nickname
    directory.mkdir(parents=True, exist_ok=True)
    return directory

  def write_post_video(self, aweme_id="aw1", body=b"POST-BYTES", nickname="creator"):
    directory = self.post_dir(aweme_id, nickname)
    name = "{}_video.mp4".format(aweme_id)
    (directory / name).write_bytes(body)
    return directory, name

  def discovered_id(self, directory, aweme_id="aw1"):
    discovery = self.resolver.post_assets(str(directory), "douyin", aweme_id)
    self.assertEqual(StorageState.AVAILABLE, discovery.storage_state)
    return discovery.assets[0].asset_id


class SecureOpenSupportTest(SecureOpenTestCase):
  def test_this_platform_is_declared_capable_or_it_is_not(self):
    ##
    ## Not a claim that the flag is True - a claim that the answer comes from
    ## probing the primitives rather than from assuming them.
    ##
    expected = (
      hasattr(os, "O_NOFOLLOW")
      and hasattr(os, "O_DIRECTORY")
      and os.open in os.supports_dir_fd
    )
    self.assertEqual(expected, SECURE_OPEN_SUPPORTED)


class PostSecureOpenTest(SecureOpenTestCase):
  def test_an_authorized_post_asset_opens_and_reads_back_its_bytes(self):
    directory, _ = self.write_post_video()
    asset_id = self.discovered_id(directory)

    opened = self.resolver.open_post_asset(
      str(directory), "douyin", "aw1", asset_id
    )

    self.assertIsInstance(opened, OpenedMediaAsset)
    try:
      self.assertEqual(b"POST-BYTES", opened.stream.read())
      self.assertEqual(len(b"POST-BYTES"), opened.size_bytes)
      self.assertEqual("aw1_video.mp4", opened.asset.name)
      self.assertEqual("video/mp4", opened.asset.media_type)
    finally:
      opened.close()

  def test_the_opened_result_can_never_be_serialized(self):
    ##
    ## It holds a descriptor and a resolved location. Nothing about it may
    ## reach a browser, so it must not carry the method that would let it.
    ##
    directory, _ = self.write_post_video()
    opened = self.resolver.open_post_asset(
      str(directory), "douyin", "aw1", self.discovered_id(directory)
    )
    self.addCleanup(opened.close)

    self.assertFalse(hasattr(opened, "as_dict"))
    for forbidden in ("path", "absolute_path", "save_dir", "root"):
      self.assertFalse(
        hasattr(opened, forbidden), "OpenedMediaAsset must not expose " + forbidden
      )

  def test_an_unknown_asset_id_opens_nothing(self):
    directory, _ = self.write_post_video()

    self.assertIsNone(
      self.resolver.open_post_asset(str(directory), "douyin", "aw1", "0" * 64)
    )

  def test_an_asset_id_from_another_post_opens_nothing(self):
    ##
    ## Same file name, different parent. The id is derived from the parent
    ## identity, so it must not match - this is what stops an id from being
    ## redeemable anywhere but where it was issued.
    ##
    directory, name = self.write_post_video(aweme_id="aw1")
    other = asset_id_for("post", ("douyin", "aw2"), name)

    self.assertIsNone(
      self.resolver.open_post_asset(str(directory), "douyin", "aw1", other)
    )

  def test_a_file_deleted_after_discovery_opens_nothing(self):
    directory, name = self.write_post_video()
    asset_id = self.discovered_id(directory)

    (directory / name).unlink()

    ##
    ## Not an exception, and certainly not a stale hit: the id was valid when
    ## it was issued and means nothing now.
    ##
    self.assertIsNone(
      self.resolver.open_post_asset(str(directory), "douyin", "aw1", asset_id)
    )

  def test_a_file_swapped_for_a_symlink_after_discovery_opens_nothing(self):
    """The race this whole boundary exists for.

    Discovery saw a regular file. Between then and the open, the name is made
    to point outside the root. Re-running discovery is not enough on its own -
    the open itself has to refuse to follow the link.
    """
    directory, name = self.write_post_video()
    asset_id = self.discovered_id(directory)

    (directory / name).unlink()
    (directory / name).symlink_to(self.secret)

    opened = self.resolver.open_post_asset(
      str(directory), "douyin", "aw1", asset_id
    )

    if opened is not None:
      self.addCleanup(opened.close)
      self.assertNotIn(b"SECRET", opened.stream.read())
      self.fail("a symlinked asset must not open at all")

  def test_an_intermediate_directory_swapped_for_a_symlink_opens_nothing(self):
    """O_NOFOLLOW on the final component alone is not enough.

    Every directory between the root and the file is an opportunity to
    redirect the walk, so each level is opened with O_NOFOLLOW too.
    """
    nested = self.root / "a" / "b"
    nested.mkdir(parents=True)
    (nested / "aw1_video.mp4").write_bytes(b"POST-BYTES")
    asset_id = self.discovered_id(nested)

    ##
    ## Somewhere outside the root that has the same interior shape, so the walk
    ## would succeed if it followed the link.
    ##
    elsewhere = self.base / "elsewhere" / "b"
    elsewhere.mkdir(parents=True)
    (elsewhere / "aw1_video.mp4").write_bytes(b"SECRET-OUTSIDE-ROOT")

    import shutil

    shutil.rmtree(self.root / "a")
    (self.root / "a").symlink_to(self.base / "elsewhere")

    opened = self.resolver.open_post_asset(
      str(nested), "douyin", "aw1", asset_id
    )

    if opened is not None:
      self.addCleanup(opened.close)
      self.assertNotIn(b"SECRET", opened.stream.read())
      self.fail("an intermediate symlink must not be followed")

  def test_a_directory_wearing_a_media_name_opens_nothing(self):
    directory = self.post_dir()
    (directory / "aw1_video.mp4").mkdir()

    self.assertIsNone(
      self.resolver.open_post_asset(
        str(directory),
        "douyin",
        "aw1",
        asset_id_for("post", ("douyin", "aw1"), "aw1_video.mp4"),
      )
    )

  @unittest.skipUnless(hasattr(os, "mkfifo"), "requires mkfifo")
  def test_a_fifo_wearing_a_media_name_opens_nothing(self):
    """And does not block trying.

    Opening a fifo for reading blocks until a writer appears, which would hold
    a worker forever. The open must be non-blocking, or the type must be
    refused before the blocking open is attempted.
    """
    directory = self.post_dir()
    os.mkfifo(str(directory / "aw1_video.mp4"))

    self.assertIsNone(
      self.resolver.open_post_asset(
        str(directory),
        "douyin",
        "aw1",
        asset_id_for("post", ("douyin", "aw1"), "aw1_video.mp4"),
      )
    )

  def test_a_directory_outside_the_root_opens_nothing(self):
    outside = self.base / "elsewhere"
    outside.mkdir()
    (outside / "aw1_video.mp4").write_bytes(b"SECRET-OUTSIDE-ROOT")

    self.assertIsNone(
      self.resolver.open_post_asset(
        str(outside),
        "douyin",
        "aw1",
        asset_id_for("post", ("douyin", "aw1"), "aw1_video.mp4"),
      )
    )

  def test_a_prefix_that_merely_looks_like_the_root_opens_nothing(self):
    ##
    ## `/tmp/x/downloads-evil` starts with `/tmp/x/downloads` as text and is a
    ## different directory.
    ##
    evil = Path(str(self.root) + "-evil")
    evil.mkdir()
    (evil / "aw1_video.mp4").write_bytes(b"SECRET-OUTSIDE-ROOT")

    self.assertIsNone(
      self.resolver.open_post_asset(
        str(evil),
        "douyin",
        "aw1",
        asset_id_for("post", ("douyin", "aw1"), "aw1_video.mp4"),
      )
    )


class RecordingSecureOpenTest(SecureOpenTestCase):
  def write_recording(self, name="live.flv", body=b"RECORDING-BYTES"):
    directory = self.root / "creator"
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / name
    target.write_bytes(body)
    return target

  def discovered_recording_id(self, target, recording_id=7):
    discovery = self.resolver.recording_asset(str(target), recording_id)
    self.assertEqual(StorageState.AVAILABLE, discovery.storage_state)
    return discovery.assets[0].asset_id

  def test_a_recording_opens_and_reads_back_its_bytes(self):
    target = self.write_recording()
    asset_id = self.discovered_recording_id(target)

    opened = self.resolver.open_recording_asset(str(target), 7, asset_id)
    self.addCleanup(opened.close)

    self.assertEqual(b"RECORDING-BYTES", opened.stream.read())
    self.assertEqual("live.flv", opened.asset.name)
    self.assertEqual("video/x-flv", opened.asset.media_type)

  def test_a_transport_stream_opens_with_its_own_media_type(self):
    target = self.write_recording(name="live.ts", body=b"TS-BYTES")
    asset_id = self.discovered_recording_id(target)

    opened = self.resolver.open_recording_asset(str(target), 7, asset_id)
    self.addCleanup(opened.close)

    self.assertEqual(b"TS-BYTES", opened.stream.read())
    self.assertEqual("video/mp2t", opened.asset.media_type)

  def test_an_identity_beyond_the_javascript_safe_range_opens_its_own_file(self):
    target = self.write_recording()
    big = 9007199254740993
    asset_id = self.discovered_recording_id(target, recording_id=big)

    opened = self.resolver.open_recording_asset(str(target), big, asset_id)
    self.addCleanup(opened.close)

    self.assertEqual(b"RECORDING-BYTES", opened.stream.read())
    ##
    ## And the neighbouring identity does not open it.
    ##
    self.assertIsNone(
      self.resolver.open_recording_asset(str(target), 9007199254740992, asset_id)
    )

  def test_a_recording_swapped_for_a_symlink_after_discovery_opens_nothing(self):
    target = self.write_recording()
    asset_id = self.discovered_recording_id(target)

    target.unlink()
    target.symlink_to(self.secret)

    opened = self.resolver.open_recording_asset(str(target), 7, asset_id)

    if opened is not None:
      self.addCleanup(opened.close)
      self.assertNotIn(b"SECRET", opened.stream.read())
      self.fail("a symlinked recording must not open at all")

  def test_a_recording_deleted_after_discovery_opens_nothing(self):
    target = self.write_recording()
    asset_id = self.discovered_recording_id(target)

    target.unlink()

    self.assertIsNone(self.resolver.open_recording_asset(str(target), 7, asset_id))

  def test_a_recorded_path_outside_the_root_opens_nothing(self):
    self.assertIsNone(
      self.resolver.open_recording_asset(
        str(self.secret),
        7,
        asset_id_for("recording", (7,), "secret.txt"),
      )
    )

  def test_a_traversal_in_the_recorded_path_opens_nothing(self):
    self.assertIsNone(
      self.resolver.open_recording_asset(
        str(self.root / ".." / "secret.txt"),
        7,
        asset_id_for("recording", (7,), "secret.txt"),
      )
    )


class DescriptorLifecycleTest(SecureOpenTestCase):
  """A long-running server must not accumulate descriptors."""

  def open_descriptor_count(self):
    return len(os.listdir("/proc/self/fd"))

  @unittest.skipUnless(os.path.isdir("/proc/self/fd"), "requires /proc")
  def test_a_successful_open_leaks_no_intermediate_directory_descriptor(self):
    nested = self.root / "a" / "b" / "c"
    nested.mkdir(parents=True)
    (nested / "aw1_video.mp4").write_bytes(b"POST-BYTES")
    asset_id = self.discovered_id(nested)

    before = self.open_descriptor_count()
    opened = self.resolver.open_post_asset(str(nested), "douyin", "aw1", asset_id)
    ##
    ## Exactly one descriptor is still held - the file being served. Every
    ## directory opened on the way down is closed.
    ##
    self.assertEqual(before + 1, self.open_descriptor_count())

    opened.close()
    self.assertEqual(before, self.open_descriptor_count())

  @unittest.skipUnless(os.path.isdir("/proc/self/fd"), "requires /proc")
  def test_a_refused_open_leaks_nothing(self):
    directory, name = self.write_post_video()
    asset_id = self.discovered_id(directory)
    (directory / name).unlink()
    (directory / name).symlink_to(self.secret)

    before = self.open_descriptor_count()
    for _ in range(25):
      self.assertIsNone(
        self.resolver.open_post_asset(str(directory), "douyin", "aw1", asset_id)
      )

    self.assertEqual(before, self.open_descriptor_count())

  @unittest.skipUnless(os.path.isdir("/proc/self/fd"), "requires /proc")
  def test_repeated_successful_opens_do_not_accumulate(self):
    directory, _ = self.write_post_video()
    asset_id = self.discovered_id(directory)

    before = self.open_descriptor_count()
    for _ in range(25):
      opened = self.resolver.open_post_asset(
        str(directory), "douyin", "aw1", asset_id
      )
      opened.close()

    self.assertEqual(before, self.open_descriptor_count())

  def test_closing_twice_is_harmless(self):
    directory, _ = self.write_post_video()
    opened = self.resolver.open_post_asset(
      str(directory), "douyin", "aw1", self.discovered_id(directory)
    )

    opened.close()
    opened.close()


##
## >>--------------------- the open primitive, isolated ---------------------<<
##
from backend.src.service.media_asset import _open_within_root  # noqa: E402


class OpenWithinRootTest(SecureOpenTestCase):
  """The walk itself, with rediscovery deliberately out of the way.

  The tests above swap the file before ``open_post_asset`` is called, so
  rediscovery refuses them and the walk is never reached. That is a real
  defence, but it is the *first* one; these prove the second exists, because
  in a genuine race the swap lands after discovery has already passed.
  """

  def walk(self, target):
    return _open_within_root(Path(os.path.realpath(str(self.root))), Path(target))

  def test_it_opens_a_regular_file_inside_the_root(self):
    directory, name = self.write_post_video()

    opened = self.walk(directory / name)

    self.assertIsNotNone(opened)
    ##
    ## The walk hands back the stat it took on the descriptor it proved, not
    ## just a size. Phase 10C needs the rest of it to tell one representation
    ## of a file from another, and re-taking the stat later would describe a
    ## different moment.
    ##
    stream, info = opened
    self.addCleanup(stream.close)
    self.assertEqual(b"POST-BYTES", stream.read())
    self.assertEqual(len(b"POST-BYTES"), info.st_size)
    self.assertEqual(os.fstat(stream.fileno()).st_ino, info.st_ino)

  def test_it_refuses_a_symlinked_final_component(self):
    directory = self.post_dir()
    link = directory / "aw1_video.mp4"
    link.symlink_to(self.secret)

    self.assertIsNone(self.walk(link))

  def test_it_refuses_a_symlinked_intermediate_directory(self):
    ##
    ## The file is real, is inside a real directory, and the only thing wrong
    ## is one component on the way down. Checking O_NOFOLLOW on the final name
    ## alone would open it.
    ##
    elsewhere = self.base / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / "aw1_video.mp4").write_bytes(b"SECRET-OUTSIDE-ROOT")
    (self.root / "a").symlink_to(elsewhere)

    self.assertIsNone(self.walk(self.root / "a" / "aw1_video.mp4"))

  def test_it_refuses_a_directory(self):
    directory = self.post_dir()
    (directory / "aw1_video.mp4").mkdir()

    self.assertIsNone(self.walk(directory / "aw1_video.mp4"))

  @unittest.skipUnless(hasattr(os, "mkfifo"), "requires mkfifo")
  def test_it_refuses_a_fifo_without_blocking_on_it(self):
    directory = self.post_dir()
    os.mkfifo(str(directory / "aw1_video.mp4"))

    ##
    ## If this hangs rather than returning, the open was not non-blocking and a
    ## worker would be held until somebody wrote to the pipe.
    ##
    self.assertIsNone(self.walk(directory / "aw1_video.mp4"))

  def test_it_refuses_a_target_outside_the_root(self):
    self.assertIsNone(self.walk(self.secret))

  def test_it_refuses_a_file_that_is_no_longer_there(self):
    directory, name = self.write_post_video()
    (directory / name).unlink()

    self.assertIsNone(self.walk(directory / name))


class InterleavedRaceTest(SecureOpenTestCase):
  """The real TOCTOU: the swap lands *after* discovery has already passed.

  Rediscovery cannot help here by construction - it ran, it saw a regular file,
  and it approved.

  These assert the *outcome* - no secret bytes - rather than which layer
  produced it. Two refuse independently: ``contained_path`` re-resolves inside
  ``_open_matching`` and rejects a link leading out of the root, and the walk
  refuses to follow one at all. Replacing the walk with a plain ``open()``
  leaves these passing, because the first layer still catches them; the tests
  that pin the walk itself are in ``OpenWithinRootTest``, three of which fail
  under exactly that substitution.

  Both layers are wanted. The first is a check and therefore has a window after
  it; the second is a property of the open and has none.
  """

  def race(self, sabotage):
    """Run a post open with ``sabotage`` fired between discovery and the walk."""
    directory, name = self.write_post_video()
    asset_id = self.discovered_id(directory)

    real_walk = MediaAssetResolver._open_matching

    def sabotaged(resolver, discovery, wanted, root, folder):
      ##
      ## Discovery has completed and approved a regular file. This is precisely
      ## the window an attacker races for.
      ##
      sabotage(directory, name)
      return real_walk(resolver, discovery, wanted, root, folder)

    MediaAssetResolver._open_matching = sabotaged
    try:
      return self.resolver.open_post_asset(
        str(directory), "douyin", "aw1", asset_id
      )
    finally:
      MediaAssetResolver._open_matching = real_walk

  def test_a_file_replaced_by_a_symlink_after_discovery_is_refused(self):
    def swap(directory, name):
      (directory / name).unlink()
      (directory / name).symlink_to(self.secret)

    opened = self.race(swap)

    if opened is not None:
      self.addCleanup(opened.close)
      body = opened.stream.read()
      self.assertNotIn(b"SECRET", body)
      self.fail("the open must refuse a component that became a symlink")

  def test_a_file_deleted_after_discovery_is_refused(self):
    opened = self.race(lambda directory, name: (directory / name).unlink())

    self.assertIsNone(opened)

  def test_a_file_replaced_by_a_directory_after_discovery_is_refused(self):
    def swap(directory, name):
      (directory / name).unlink()
      (directory / name).mkdir()

    self.assertIsNone(self.race(swap))

  def test_an_intermediate_directory_replaced_after_discovery_is_refused(self):
    ##
    ## Same window, one level up. The file discovery approved still exists at
    ## its own name; the route to it is what changed.
    ##
    import shutil

    nested = self.root / "a" / "b"
    nested.mkdir(parents=True)
    (nested / "aw1_video.mp4").write_bytes(b"POST-BYTES")
    asset_id = self.discovered_id(nested)

    elsewhere = self.base / "elsewhere" / "b"
    elsewhere.mkdir(parents=True)
    (elsewhere / "aw1_video.mp4").write_bytes(b"SECRET-OUTSIDE-ROOT")

    real_walk = MediaAssetResolver._open_matching

    def sabotaged(resolver, discovery, wanted, root, folder):
      shutil.rmtree(self.root / "a")
      (self.root / "a").symlink_to(self.base / "elsewhere")
      return real_walk(resolver, discovery, wanted, root, folder)

    MediaAssetResolver._open_matching = sabotaged
    try:
      opened = self.resolver.open_post_asset(
        str(nested), "douyin", "aw1", asset_id
      )
    finally:
      MediaAssetResolver._open_matching = real_walk

    if opened is not None:
      self.addCleanup(opened.close)
      self.assertNotIn(b"SECRET", opened.stream.read())
      self.fail("an intermediate component that became a symlink must be refused")
