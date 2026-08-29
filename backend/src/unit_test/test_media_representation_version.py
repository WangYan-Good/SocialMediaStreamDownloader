##<<Base>>
import os
import tempfile
import time
import unittest
from pathlib import Path

##<<Third-part>>
from backend.src.service.media_asset import (
  WEAK_VALIDATOR_WINDOW_NS,
  MediaAssetResolver,
  OpenedFileVersion,
  asset_id_for,
)


class RepresentationVersionTest(unittest.TestCase):
  """What makes one opening of a file different from another.

  Phase 10B could answer "which file" with an asset id.  Resuming needs a
  harder question answered: "is this still the same *bytes* I started
  downloading".  An asset id cannot answer it - it is derived from the parent
  identity and the file name, so replacing a file with entirely different
  content leaves it identical.  Resuming against that would splice two files
  together and produce a corrupt download that nothing reported.
  """

  def setUp(self):
    self._tmp = tempfile.TemporaryDirectory()
    self.base = Path(self._tmp.name)
    self.root = self.base / "downloads"
    self.creator = self.root / "creator"
    self.creator.mkdir(parents=True)
    self.resolver = MediaAssetResolver(lambda: str(self.root))
    self.addCleanup(self._tmp.cleanup)

    self.aweme = "7657271784144009946"
    self.name = "20260824_{}.mp4".format(self.aweme)
    self.target = self.creator / self.name
    self.target.write_bytes(b"0123456789")

  def open_it(self):
    return self.resolver.open_post_asset(
      str(self.creator),
      "douyin",
      self.aweme,
      asset_id_for("post", ("douyin", self.aweme), self.name),
    )

  def test_an_opened_asset_carries_a_version_taken_from_its_descriptor(self):
    opened = self.open_it()
    self.addCleanup(opened.close)

    self.assertIsInstance(opened.version, OpenedFileVersion)
    ##
    ## Every field comes from fstat on the descriptor that was actually opened,
    ## never from a path stat that could describe a different file by now.
    ##
    info = os.fstat(opened.stream.fileno())
    self.assertEqual(info.st_dev, opened.version.st_dev)
    self.assertEqual(info.st_ino, opened.version.st_ino)
    self.assertEqual(info.st_size, opened.version.st_size)
    self.assertEqual(info.st_mtime_ns, opened.version.st_mtime_ns)
    self.assertEqual(info.st_ctime_ns, opened.version.st_ctime_ns)

  def test_the_version_never_learns_how_to_describe_itself(self):
    ##
    ## It carries an inode and a device number. Those describe this host's
    ## filesystem, so the object must not acquire a way into a response.
    ##
    opened = self.open_it()
    self.addCleanup(opened.close)

    self.assertFalse(hasattr(opened.version, "as_dict"))
    for forbidden in ("path", "name", "root", "save_dir"):
      self.assertFalse(hasattr(opened.version, forbidden))

  def test_the_same_unchanged_file_validates_identically(self):
    first = self.open_it()
    self.addCleanup(first.close)
    second = self.open_it()
    self.addCleanup(second.close)

    self.assertEqual(first.version.entity_tag, second.version.entity_tag)

  def test_a_replaced_file_validates_differently_though_its_id_is_unchanged(self):
    """The test this whole mechanism exists for.

    ``os.replace`` swaps the content behind the same name - which is what a
    re-download, a re-encode or a repair does. The asset id is derived from the
    name and cannot notice. The validator must.
    """
    first = self.open_it()
    first_tag = first.version.entity_tag
    first_id = first.asset.asset_id
    first.close()

    replacement = self.creator / "replacement.tmp"
    replacement.write_bytes(b"ABCDEFGHIJ")
    os.replace(str(replacement), str(self.target))

    second = self.open_it()
    self.addCleanup(second.close)

    ##
    ## Same name, same parent, therefore the same asset id...
    ##
    self.assertEqual(first_id, second.asset.asset_id)
    ##
    ## ...and a different representation, which is the whole point.
    ##
    self.assertNotEqual(first_tag, second.version.entity_tag)

  def test_a_file_that_only_grew_validates_differently(self):
    first = self.open_it()
    first_tag = first.version.entity_tag
    first.close()

    with open(str(self.target), "ab") as handle:
      handle.write(b"MORE")

    second = self.open_it()
    self.addCleanup(second.close)

    self.assertNotEqual(first_tag, second.version.entity_tag)

  def test_the_tag_is_not_the_asset_id(self):
    ##
    ## They answer different questions and must never be confused: one names a
    ## file, the other names the bytes currently in it.
    ##
    opened = self.open_it()
    self.addCleanup(opened.close)

    self.assertNotEqual(opened.asset.asset_id, opened.version.entity_tag)

  def test_the_tag_is_opaque_hex_and_reveals_nothing_it_was_built_from(self):
    opened = self.open_it()
    self.addCleanup(opened.close)

    tag = opened.version.entity_tag

    self.assertEqual(64, len(tag))
    self.assertTrue(all(one in "0123456789abcdef" for one in tag))
    ##
    ## An inode or a device number appearing verbatim would describe the host's
    ## filesystem to anyone who received the header.
    ##
    for revealing in (
      str(opened.version.st_ino),
      str(opened.version.st_dev),
      str(opened.version.st_mtime_ns),
    ):
      self.assertNotIn(revealing, tag)

  def test_the_tag_is_deterministic_rather_than_per_process(self):
    """Two workers must agree, so a resume can land on either.

    ``hash()`` is randomised per process and would make a validator issued by
    one worker meaningless to the next.
    """
    import hashlib

    opened = self.open_it()
    self.addCleanup(opened.close)
    version = opened.version

    expected = hashlib.sha256(
      "\0".join(
        str(one)
        for one in (
          version.st_dev,
          version.st_ino,
          version.st_size,
          version.st_mtime_ns,
          version.st_ctime_ns,
        )
      ).encode("utf-8")
    ).hexdigest()

    self.assertEqual(expected, version.entity_tag)

  def test_building_the_tag_does_not_read_the_media(self):
    """A validator is metadata, never a digest of the content.

    Hashing the bytes would mean reading a file that may be tens of gigabytes,
    once per request, to answer a question stat already answers.
    """
    opened = self.open_it()
    self.addCleanup(opened.close)

    ##
    ## Nothing has been consumed from the descriptor: the file is still at its
    ## start, so the tag cannot have come from its contents.
    ##
    self.assertEqual(0, opened.stream.tell())

    ##
    ## And two files with identical content but different identities do not
    ## share a tag - which they would if the tag were a content digest.
    ##
    twin = self.creator / "20260824_{}_twin.mp4".format(self.aweme)
    twin.write_bytes(b"0123456789")
    other = self.resolver.open_post_asset(
      str(self.creator),
      "douyin",
      self.aweme,
      asset_id_for("post", ("douyin", self.aweme), twin.name),
    )
    self.addCleanup(other.close)

    self.assertNotEqual(opened.version.entity_tag, other.version.entity_tag)


class StrongValidatorTest(RepresentationVersionTest):
  """Does the validator meet RFC 9110's definition of *strong*?

  §8.8.1: a strong validator must change whenever the representation data
  changes in any way observable to a GET.  Replacing the file through
  ``os.replace`` is the easy case - a new inode makes the tuple differ almost
  by accident.

  The hard case is a rewrite in place: same inode, same size, different bytes.
  If the validator cannot see that, it is not strong, and using it for
  ``If-Range`` would let a resume splice two different files together while
  believing it had checked.
  """

  def rewrite_in_place(self, payload):
    """Change the content without changing the inode or the length."""
    with open(str(self.target), "r+b") as handle:
      handle.seek(0)
      handle.write(payload)
      handle.flush()
      os.fsync(handle.fileno())

  def test_the_same_inode_rewritten_with_different_bytes_validates_differently(self):
    before_stat = os.stat(str(self.target))
    first = self.open_it()
    first_tag = first.version.entity_tag
    first.close()

    ##
    ## Past the filesystem's timestamp resolution, so the two writes cannot
    ## share a tick. Inside one tick they are genuinely indistinguishable
    ## afterwards - see the companion tests, where that case is handled by
    ## refusing to call the validator strong rather than by pretending.
    ##
    time.sleep(0.05)
    self.rewrite_in_place(b"ABCDEFGHIJ")

    second = self.open_it()
    self.addCleanup(second.close)
    after_stat = os.stat(str(self.target))

    ##
    ## The conditions that make this the hard case, asserted rather than
    ## assumed - if the inode or the size changed, this test proved the easy
    ## case again and would pass without meaning anything.
    ##
    self.assertEqual(before_stat.st_ino, after_stat.st_ino)
    self.assertEqual(before_stat.st_size, after_stat.st_size)
    self.assertEqual(b"ABCDEFGHIJ", self.target.read_bytes())

    self.assertNotEqual(
      first_tag,
      second.version.entity_tag,
      "an in-place rewrite must change the validator, or it is not strong",
    )

  def test_a_rewrite_that_changes_one_byte_is_noticed_once_the_clock_moves(self):
    first = self.open_it()
    first_tag = first.version.entity_tag
    first.close()

    ##
    ## Past the filesystem's timestamp resolution. Without this the two writes
    ## can land in one tick and be genuinely indistinguishable afterwards -
    ## which is a real property of the filesystem, not a flaw in the test, and
    ## is what ``is_strong_at`` exists to handle.
    ##
    time.sleep(0.05)
    with open(str(self.target), "r+b") as handle:
      handle.seek(5)
      handle.write(b"X")
      handle.flush()
      os.fsync(handle.fileno())

    second = self.open_it()
    self.addCleanup(second.close)

    self.assertEqual(10, second.version.st_size)
    self.assertNotEqual(first_tag, second.version.entity_tag)

  def test_a_validator_is_not_called_strong_while_the_clock_cannot_prove_it(self):
    """The honest limit of a timestamp-derived validator.

    A file written within the filesystem's timestamp resolution could change
    again without the tuple moving. For that window the validator cannot claim
    to have noticed anything, and says so - which is what stops ``If-Range``
    from honouring a resume it has not actually checked.
    """
    self.rewrite_in_place(b"ABCDEFGHIJ")
    opened = self.open_it()
    self.addCleanup(opened.close)

    self.assertFalse(opened.version.is_strong_at(time.time_ns()))

  def test_a_settled_file_does_have_a_strong_validator(self):
    ##
    ## The ordinary case: a file written some time ago cannot have changed
    ## inside the current tick, so its tag is trustworthy and a resume works.
    ##
    opened = self.open_it()
    self.addCleanup(opened.close)

    settled = opened.version.st_mtime_ns + WEAK_VALIDATOR_WINDOW_NS + 1

    self.assertTrue(opened.version.is_strong_at(settled))

  def test_rapid_rewrites_are_either_distinguished_or_declared_not_strong(self):
    """Whichever way the clock falls, a resume is never wrongly honoured.

    Two writes inside one tick may share a tag - that is the filesystem's
    resolution, not something this code can fix. What it can guarantee is that
    such a representation is never reported as strong, so the ambiguity turns
    into a re-sent file rather than a corrupt one.
    """
    seen = []
    for payload in (b"AAAAAAAAAA", b"BBBBBBBBBB", b"CCCCCCCCCC", b"DDDDDDDDDD"):
      self.rewrite_in_place(payload)
      opened = self.open_it()
      seen.append((opened.version.entity_tag, opened.version.is_strong_at(time.time_ns())))
      opened.close()

    for tag, strong in seen:
      self.assertFalse(strong, "a just-written file must not be called strong")

    ##
    ## And once things settle, the distinct contents are distinguishable.
    ##
    tags = []
    for payload in (b"EEEEEEEEEE", b"FFFFFFFFFF", b"GGGGGGGGGG"):
      time.sleep(0.05)
      self.rewrite_in_place(payload)
      opened = self.open_it()
      tags.append(opened.version.entity_tag)
      opened.close()

    self.assertEqual(len(tags), len(set(tags)))

  def test_an_untouched_file_keeps_its_validator_across_reopens(self):
    ##
    ## The other half of strength: it must not change when nothing did, or no
    ## resume could ever succeed.
    ##
    tags = set()
    for _ in range(5):
      opened = self.open_it()
      tags.add(opened.version.entity_tag)
      opened.close()

    self.assertEqual(1, len(tags))
