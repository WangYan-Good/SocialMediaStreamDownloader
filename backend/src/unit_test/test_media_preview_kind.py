##<<Base>>
import unittest

##<<Third-part>>
from backend.src.service.media_asset import (
  PREVIEWABLE_MEDIA_TYPES,
  MediaAsset,
  media_type_for,
  preview_kind_for,
)


class PreviewKindTest(unittest.TestCase):
  """Which media types this server is willing to send inline.

  A closed list, not a rule.  Anything a browser renders in place is something
  it may also interpret, and the set of types worth that risk is small enough
  to write down - so it is written down, and everything absent from it is
  refused rather than reasoned about.
  """

  def test_the_three_types_a_browser_renders_natively(self):
    self.assertEqual("image", preview_kind_for("image/jpeg"))
    self.assertEqual("video", preview_kind_for("video/mp4"))
    self.assertEqual("audio", preview_kind_for("audio/mpeg"))

  def test_the_recording_container_formats_are_not_previewable(self):
    ##
    ## No browser plays either without a JavaScript demuxer. Offering a preview
    ## that cannot work is worse than not offering one.
    ##
    self.assertIsNone(preview_kind_for("video/x-flv"))
    self.assertIsNone(preview_kind_for("video/mp2t"))

  def test_an_unrecognised_type_is_not_previewable(self):
    ##
    ## The fallback for a file whose extension this program does not know. It
    ## must never be rendered - the point of the fallback is that the content
    ## is unidentified.
    ##
    self.assertIsNone(preview_kind_for("application/octet-stream"))

  def test_nothing_that_a_browser_could_execute_is_previewable(self):
    """The reason this is a list rather than a prefix match.

    ``image/svg+xml`` starts with ``image/`` and is a document that can carry
    script. ``text/html`` is the same problem stated plainly. A rule shaped
    like "images are safe" admits both.
    """
    for active in (
      "image/svg+xml",
      "text/html",
      "application/xhtml+xml",
      "text/xml",
      "application/xml",
      "application/pdf",
      "application/javascript",
      "text/javascript",
    ):
      with self.subTest(media_type=active):
        self.assertIsNone(preview_kind_for(active))

  def test_no_type_outside_the_written_list_is_previewable(self):
    ##
    ## Asserted against the list itself, so a type added to the mapping later
    ## cannot become previewable without somebody editing the list on purpose.
    ##
    self.assertEqual(
      {"image/jpeg", "video/mp4", "audio/mpeg"},
      set(PREVIEWABLE_MEDIA_TYPES),
    )

  def test_nothing_missing_or_malformed_is_previewable(self):
    for value in (None, "", "   ", "video", "video/", "/mp4", 7, object()):
      with self.subTest(value=value):
        self.assertIsNone(preview_kind_for(value))

  def test_a_type_carrying_parameters_is_not_guessed_at(self):
    ##
    ## Nothing in this program produces one. If something ever did, matching it
    ## loosely would be inventing a policy for a value nobody designed.
    ##
    self.assertIsNone(preview_kind_for("image/jpeg; charset=binary"))

  def test_every_extension_this_program_writes_has_a_settled_answer(self):
    ##
    ## Ties the allowlist to the extensions actually produced, so a new one
    ## cannot be added without a decision being made about previewing it.
    ##
    expected = {
      "x.mp4": "video",
      "x.jpg": "image",
      "x.jpeg": "image",
      "x.mp3": "audio",
      "x.flv": None,
      "x.ts": None,
      "x.unknown": None,
    }

    for name, kind in expected.items():
      with self.subTest(name=name):
        self.assertEqual(kind, preview_kind_for(media_type_for(name)))


class MediaAssetPreviewFieldTest(unittest.TestCase):
  """The asset tells a browser whether previewing it is on offer."""

  def asset(self, name, media_type):
    return MediaAsset(
      asset_id="a" * 64,
      kind="video",
      name=name,
      size_bytes=10,
      media_type=media_type,
    )

  def test_a_previewable_asset_says_which_element_would_render_it(self):
    self.assertEqual(
      "video", self.asset("x.mp4", "video/mp4").as_dict()["preview_kind"]
    )
    self.assertEqual(
      "image", self.asset("x.jpg", "image/jpeg").as_dict()["preview_kind"]
    )
    self.assertEqual(
      "audio", self.asset("x.mp3", "audio/mpeg").as_dict()["preview_kind"]
    )

  def test_an_unpreviewable_asset_says_so_rather_than_omitting_the_field(self):
    ##
    ## Present and null, so a browser reads one contract rather than two - a
    ## missing key would have to be interpreted.
    ##
    payload = self.asset("x.flv", "video/x-flv").as_dict()

    self.assertIn("preview_kind", payload)
    self.assertIsNone(payload["preview_kind"])

  def test_the_field_is_derived_rather_than_stored(self):
    ##
    ## One authority. A second copy of this decision - in a column, in a
    ## serializer, in the route - is a second copy that can disagree.
    ##
    asset = self.asset("x.mp4", "video/mp4")

    self.assertEqual(preview_kind_for(asset.media_type), asset.preview_kind)

  def test_the_asset_still_reveals_no_location(self):
    payload = self.asset("x.mp4", "video/mp4").as_dict()

    self.assertEqual(
      {
        "asset_id",
        "kind",
        "name",
        "size_bytes",
        "media_type",
        "image_index",
        "preview_kind",
      },
      set(payload),
    )
    for forbidden in ("path", "save_dir", "output_path", "preview_url", "download_url"):
      self.assertNotIn(forbidden, payload)
