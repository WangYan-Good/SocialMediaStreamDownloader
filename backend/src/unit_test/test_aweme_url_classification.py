import unittest

from backend.src.platform.douyin.douyin_aweme_url import (
  classify_aweme_url,
  is_aweme_url,
  needs_resolution,
)


AWEME_ID = "7123456789012345678"


class AwemeUrlRecognisedFormsTest(unittest.TestCase):
  """Every form a resolved single-post link lands on yields the same id."""

  def test_pc_video_page(self):
    self.assertEqual(
      classify_aweme_url("https://www.douyin.com/video/" + AWEME_ID),
      AWEME_ID,
    )

  def test_pc_note_page(self):
    self.assertEqual(
      classify_aweme_url("https://www.douyin.com/note/" + AWEME_ID),
      AWEME_ID,
    )

  def test_mobile_share_video_page(self):
    self.assertEqual(
      classify_aweme_url(
        "https://www.iesdouyin.com/share/video/{}/?region=CN&mid=123".format(
          AWEME_ID
        )
      ),
      AWEME_ID,
    )

  def test_mobile_share_note_page(self):
    self.assertEqual(
      classify_aweme_url(
        "https://www.iesdouyin.com/share/note/{}/?from=web".format(AWEME_ID)
      ),
      AWEME_ID,
    )

  def test_feed_modal(self):
    self.assertEqual(
      classify_aweme_url(
        "https://www.douyin.com/discover?modal_id=" + AWEME_ID
      ),
      AWEME_ID,
    )

  def test_feed_modal_with_trailing_slash_and_extra_query(self):
    self.assertEqual(
      classify_aweme_url(
        "https://www.douyin.com/discover/?vid=9&modal_id={}&x=1".format(
          AWEME_ID
        )
      ),
      AWEME_ID,
    )

  def test_search_page_modal(self):
    self.assertEqual(
      classify_aweme_url(
        "https://www.douyin.com/search?modal_id=" + AWEME_ID
      ),
      AWEME_ID,
    )

  def test_trailing_path_after_the_id_is_tolerated(self):
    self.assertEqual(
      classify_aweme_url(
        "https://www.douyin.com/video/{}/extra".format(AWEME_ID)
      ),
      AWEME_ID,
    )

  def test_surrounding_whitespace_is_tolerated(self):
    self.assertEqual(
      classify_aweme_url("  https://www.douyin.com/video/" + AWEME_ID + "  "),
      AWEME_ID,
    )

  def test_is_aweme_url_agrees_with_classify(self):
    self.assertTrue(is_aweme_url("https://www.douyin.com/video/" + AWEME_ID))


class AwemeUrlRejectedFormsTest(unittest.TestCase):
  """Anything that is not a single post must not be claimed."""

  def test_live_room_is_not_a_post(self):
    self.assertIsNone(classify_aweme_url("https://live.douyin.com/123456789"))

  def test_live_reflow_host_is_not_a_post(self):
    self.assertIsNone(
      classify_aweme_url(
        "https://webcast.amemv.com/douyin/webcast/reflow/7123456789012345678"
      )
    )

  def test_live_host_is_rejected_even_with_a_post_shaped_path(self):
    """A live host wins over the path shape.

    The live path owns these urls; claiming one here would send a live room
    into the post pipeline.
    """
    self.assertIsNone(
      classify_aweme_url("https://live.douyin.com/video/" + AWEME_ID)
    )

  def test_user_home_page_is_not_a_post(self):
    self.assertIsNone(
      classify_aweme_url(
        "https://www.douyin.com/user/MS4wLjABAAAAqGTeSZHx2YaoWi6GWYNgnh79g6Jp"
      )
    )

  def test_unresolved_short_share_link_is_not_a_post(self):
    """The short link must be followed first; it carries no id of its own."""
    self.assertIsNone(classify_aweme_url("https://v.douyin.com/i2DeLnxH/"))

  def test_non_numeric_id_is_rejected(self):
    self.assertIsNone(
      classify_aweme_url("https://www.douyin.com/video/not-an-id")
    )

  def test_non_numeric_modal_id_is_rejected(self):
    self.assertIsNone(
      classify_aweme_url("https://www.douyin.com/discover?modal_id=abc")
    )

  def test_modal_id_on_an_unrelated_path_is_rejected(self):
    self.assertIsNone(
      classify_aweme_url(
        "https://www.douyin.com/user/MS4w?modal_id=" + AWEME_ID
      )
    )

  def test_unrelated_domain_shape_is_rejected(self):
    self.assertIsNone(classify_aweme_url("https://example.test/video/123"))

  def test_lookalike_host_is_rejected(self):
    """A post-shaped path on a host that merely contains "douyin" is not ours.

    The dispatcher routes on ``'douyin' in netloc``, so these do reach this
    module.  Matching on the path alone would feed them to the post pipeline.
    """
    for host in (
      "douyin.com.example.test",
      "notdouyin.com",
      "iesdouyin.com.attacker.test",
      "fake-douyin.com",
    ):
      with self.subTest(host=host):
        self.assertIsNone(
          classify_aweme_url("https://{}/video/{}".format(host, AWEME_ID))
        )

  def test_subdomains_of_the_post_domains_are_accepted(self):
    for host in ("www.douyin.com", "m.douyin.com", "douyin.com",
                 "www.iesdouyin.com", "iesdouyin.com"):
      with self.subTest(host=host):
        self.assertEqual(
          classify_aweme_url("https://{}/video/{}".format(host, AWEME_ID)),
          AWEME_ID,
        )

  def test_port_and_credentials_do_not_confuse_the_host_check(self):
    self.assertEqual(
      classify_aweme_url(
        "https://www.douyin.com:443/video/" + AWEME_ID
      ),
      AWEME_ID,
    )
    self.assertIsNone(
      classify_aweme_url(
        "https://www.douyin.com@evil.test/video/" + AWEME_ID
      )
    )

  def test_empty_and_missing_input(self):
    self.assertIsNone(classify_aweme_url(""))
    self.assertIsNone(classify_aweme_url("   "))
    self.assertIsNone(classify_aweme_url(None))
    self.assertIsNone(classify_aweme_url(12345))

  def test_is_aweme_url_is_false_for_a_live_room(self):
    self.assertFalse(is_aweme_url("https://live.douyin.com/123456789"))


class NeedsResolutionTest(unittest.TestCase):
  """Only the short share form is worth spending a request to follow."""

  def test_a_short_share_link_needs_following(self):
    """It is a douyin.com subdomain like any other but carries no id.

    Treating it as "already a known host" would skip the redirect and leave the
    link unclassifiable.
    """
    self.assertTrue(needs_resolution("https://v.douyin.com/MqjfOkWSeG8/"))

  def test_an_already_classified_post_needs_nothing(self):
    self.assertFalse(
      needs_resolution("https://www.douyin.com/video/" + AWEME_ID)
    )

  def test_a_live_room_needs_nothing(self):
    self.assertFalse(needs_resolution("https://live.douyin.com/123456"))

  def test_a_user_home_page_needs_nothing(self):
    """Following it lands on the same page, so the request buys nothing."""
    self.assertFalse(
      needs_resolution("https://www.douyin.com/user/MS4wLjABAAAAqGTe")
    )

  def test_an_unrelated_host_needs_nothing(self):
    self.assertFalse(needs_resolution("https://example.test/whatever"))

  def test_a_lookalike_short_host_needs_nothing(self):
    self.assertFalse(needs_resolution("https://v.douyin.com.evil.test/abc/"))

  def test_empty_input_needs_nothing(self):
    self.assertFalse(needs_resolution(""))
    self.assertFalse(needs_resolution(None))


if __name__ == "__main__":
  unittest.main()
