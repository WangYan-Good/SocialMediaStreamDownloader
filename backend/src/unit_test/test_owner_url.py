import unittest

from backend.src.platform.douyin.douyin_owner_url import (
  classify_owner_url,
  extract_url,
  is_owner_url,
  needs_resolution,
)


##
## The id from the real share link used during design verification.
##
SEC_UID = "MS4wLjABAAAAGZkW5n1EHZD_TFyQ-QiaISBPemtKFxVVdhLSeoXhh-U"
AWEME_ID = "7657271784144009946"


class OwnerUrlRecognisedFormsTest(unittest.TestCase):
  """Every form a resolved profile link lands on yields the same id."""

  def test_pc_profile_page(self):
    self.assertEqual(
      classify_owner_url("https://www.douyin.com/user/" + SEC_UID),
      SEC_UID,
    )

  def test_pc_profile_page_with_query(self):
    self.assertEqual(
      classify_owner_url(
        "https://www.douyin.com/user/{}?previous_page=app_code_link".format(SEC_UID)
      ),
      SEC_UID,
    )

  def test_mobile_share_page(self):
    """The form a real "查看TA的更多作品" link resolves to."""
    self.assertEqual(
      classify_owner_url(
        "https://www.iesdouyin.com/share/user/{}?from_ssr=1&sec_uid={}"
        "&u_code=ki64k3a1&from_aid=1128".format(SEC_UID, SEC_UID)
      ),
      SEC_UID,
    )

  def test_id_taken_from_the_query_when_the_path_has_none(self):
    self.assertEqual(
      classify_owner_url(
        "https://www.douyin.com/follow?sec_uid=" + SEC_UID
      ),
      SEC_UID,
    )

  def test_sec_user_id_query_key_is_also_accepted(self):
    self.assertEqual(
      classify_owner_url(
        "https://www.douyin.com/follow?sec_user_id=" + SEC_UID
      ),
      SEC_UID,
    )

  def test_trailing_path_after_the_id_is_tolerated(self):
    self.assertEqual(
      classify_owner_url(
        "https://www.douyin.com/user/{}/post".format(SEC_UID)
      ),
      SEC_UID,
    )

  def test_surrounding_whitespace_is_tolerated(self):
    self.assertEqual(
      classify_owner_url("  https://www.douyin.com/user/" + SEC_UID + "  "),
      SEC_UID,
    )

  def test_subdomains_of_the_content_domains_are_accepted(self):
    for host in ("www.douyin.com", "m.douyin.com", "douyin.com",
                 "www.iesdouyin.com", "iesdouyin.com"):
      with self.subTest(host=host):
        self.assertEqual(
          classify_owner_url("https://{}/user/{}".format(host, SEC_UID)),
          SEC_UID,
        )

  def test_is_owner_url_agrees_with_classify(self):
    self.assertTrue(is_owner_url("https://www.douyin.com/user/" + SEC_UID))


class OwnerUrlRejectedFormsTest(unittest.TestCase):
  """Anything that is not a profile must not be claimed."""

  def test_a_single_post_is_not_a_profile(self):
    for path in ("/video/", "/note/", "/share/video/"):
      with self.subTest(path=path):
        self.assertIsNone(
          classify_owner_url("https://www.douyin.com" + path + AWEME_ID)
        )

  def test_a_live_room_is_not_a_profile(self):
    self.assertIsNone(classify_owner_url("https://live.douyin.com/123456789"))

  def test_a_live_host_is_rejected_even_with_a_profile_shaped_path(self):
    """A live host wins over the path shape.

    The live path owns these urls; claiming one here would send a live room into
    the owner pipeline.
    """
    self.assertIsNone(
      classify_owner_url("https://live.douyin.com/user/" + SEC_UID)
    )

  def test_an_unresolved_short_link_is_not_a_profile(self):
    """The short link must be followed first; it carries no id of its own."""
    self.assertIsNone(classify_owner_url("https://v.douyin.com/M-kmspLye0o/"))

  def test_a_lookalike_host_is_rejected(self):
    """The dispatcher routes on ``'douyin' in netloc``, so these do arrive here."""
    for host in ("douyin.com.example.test", "notdouyin.com",
                 "iesdouyin.com.attacker.test", "fake-douyin.com"):
      with self.subTest(host=host):
        self.assertIsNone(
          classify_owner_url("https://{}/user/{}".format(host, SEC_UID))
        )

  def test_credentials_in_the_netloc_do_not_confuse_the_host_check(self):
    self.assertIsNone(
      classify_owner_url("https://www.douyin.com@evil.test/user/" + SEC_UID)
    )

  def test_a_port_does_not_confuse_the_host_check(self):
    self.assertEqual(
      classify_owner_url("https://www.douyin.com:443/user/" + SEC_UID),
      SEC_UID,
    )

  def test_a_non_owner_path_segment_is_rejected(self):
    """Without the id marker, /user/settings would read as an owner."""
    for segment in ("settings", "self", "me", "12345"):
      with self.subTest(segment=segment):
        self.assertIsNone(
          classify_owner_url("https://www.douyin.com/user/" + segment)
        )

  def test_an_id_without_the_owner_marker_is_rejected(self):
    self.assertIsNone(
      classify_owner_url(
        "https://www.douyin.com/user/AAAAAAAAAAAAAAAAAAAAAAAAAAAA"
      )
    )

  def test_a_too_short_id_is_rejected(self):
    self.assertIsNone(
      classify_owner_url("https://www.douyin.com/user/MS4wLjABAAAA")
    )

  def test_an_id_with_illegal_characters_is_rejected(self):
    self.assertIsNone(
      classify_owner_url(
        "https://www.douyin.com/user/MS4wLjABAAAA!!!!!!!!!!!!"
      )
    )

  def test_empty_and_missing_input(self):
    for value in ("", "   ", None, 12345):
      with self.subTest(value=value):
        self.assertIsNone(classify_owner_url(value))

  def test_unrelated_domain_is_rejected(self):
    self.assertIsNone(
      classify_owner_url("https://example.test/user/" + SEC_UID)
    )


class NeedsResolutionTest(unittest.TestCase):
  """Only the short share form is worth spending a request to follow."""

  def test_a_short_share_link_needs_following(self):
    self.assertTrue(needs_resolution("https://v.douyin.com/M-kmspLye0o/"))

  def test_an_already_classified_profile_needs_nothing(self):
    self.assertFalse(
      needs_resolution("https://www.douyin.com/user/" + SEC_UID)
    )

  def test_a_live_room_needs_nothing(self):
    self.assertFalse(needs_resolution("https://live.douyin.com/123456"))

  def test_a_post_page_needs_nothing(self):
    """Following it lands on the same post, so the request buys nothing."""
    self.assertFalse(
      needs_resolution("https://www.douyin.com/video/" + AWEME_ID)
    )

  def test_a_lookalike_short_host_needs_nothing(self):
    self.assertFalse(needs_resolution("https://v.douyin.com.evil.test/abc/"))

  def test_empty_input_needs_nothing(self):
    self.assertFalse(needs_resolution(""))
    self.assertFalse(needs_resolution(None))


class ExtractUrlTest(unittest.TestCase):
  """Sharing from the app copies a sentence, not a bare link."""

  def test_a_profile_share_message(self):
    text = ("0- 长按复制此条消息，打开抖音搜索，查看TA的更多作品。 "
            "https://v.douyin.com/M-kmspLye0o/ 4@1.com :0pm")

    self.assertEqual(extract_url(text), "https://v.douyin.com/M-kmspLye0o/")

  def test_a_post_share_message(self):
    text = ("4.33 复制打开抖音，看看【✨米开朗绿萝✨的作品】小鸟都粘我 "
            "https://v.douyin.com/MqjfOkWSeG8/ :0pm g@B.GI 12/06 sRK:/")

    self.assertEqual(extract_url(text), "https://v.douyin.com/MqjfOkWSeG8/")

  def test_a_bare_url_is_returned_unchanged(self):
    url = "https://www.douyin.com/user/" + SEC_UID

    self.assertEqual(extract_url(url), url)

  def test_a_trailing_chinese_full_stop_is_trimmed(self):
    """A url ending a Chinese sentence sits flush against the punctuation."""
    url = "https://www.douyin.com/user/" + SEC_UID

    self.assertEqual(extract_url("看这个主播 " + url + "。"), url)

  def test_other_trailing_punctuation_is_trimmed(self):
    url = "https://v.douyin.com/M-kmspLye0o/"
    for suffix in ("，", "）", "】", ")", ",", ".", "！", "?"):
      with self.subTest(suffix=suffix):
        self.assertEqual(extract_url("分享 " + url + suffix), url)

  def test_the_first_url_wins_when_several_are_present(self):
    first = "https://v.douyin.com/AAAAAAA/"
    text = "看看 " + first + " 还有 https://v.douyin.com/BBBBBBB/"

    self.assertEqual(extract_url(text), first)

  def test_text_without_a_url_yields_nothing(self):
    """Never invents a url out of prose."""
    for text in ("这段文字里没有链接", "douyin.com/user/abc", "", "   ", None, 42):
      with self.subTest(text=text):
        self.assertEqual(extract_url(text), "")

  def test_extraction_feeds_classification(self):
    text = "看这个主播 https://www.douyin.com/user/" + SEC_UID + " 挺好"

    self.assertEqual(classify_owner_url(extract_url(text)), SEC_UID)


if __name__ == "__main__":
  unittest.main()
