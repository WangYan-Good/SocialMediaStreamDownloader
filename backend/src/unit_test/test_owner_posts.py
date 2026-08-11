import unittest

from backend.src.platform.douyin.douyin_owner_posts import (
  FIRST_CURSOR,
  build_post_page,
  fetch_post_page,
  iter_all_posts,
)
from backend.src.platform.douyin.douyin_session import SessionExpired


SEC_UID = "MS4wLjABAAAAGZkW5n1EHZD_TFyQ-QiaISBPemtKFxVVdhLSeoXhh-U"


def post_item(aweme_id):
  ##
  ## Shaped after a real USER_POST list item: same shape as POST_DETAIL's
  ## aweme_detail, which is why these can be downloaded without a second request.
  ##
  return {
    "aweme_id": aweme_id,
    "desc": "作品 " + aweme_id,
    "create_time": 1712484087,
    "author": {"uid": "58859666123", "sec_uid": SEC_UID, "nickname": "主播"},
    "video": {
      "play_addr": {"url_list": ["https://v.example.test/" + aweme_id + ".mp4"]},
      "cover": {"url_list": ["https://p.example.test/" + aweme_id + ".jpg"]},
    },
    "music": {"play_url": {"url_list": ["https://m.example.test/s.mp3"]}},
    "statistics": {"digg_count": 12, "comment_count": 3},
  }


def page_payload(ids, next_cursor=1765077600000, has_more=1):
  return {
    "status_code": 0,
    "aweme_list": [post_item(i) for i in ids],
    "max_cursor": next_cursor,
    "has_more": has_more,
  }


class StubApi:
  """Serves prepared pages and records the cursors it was asked for."""

  class Config:
    owner_page_size = 18
    owner_max_pages = 0

  def __init__(self, pages=None, error=None):
    self.config = self.Config()
    self.pages = list(pages or [])
    self.error = error
    self.requests = []

  def get(self, api_attr, extra_params=None):
    self.requests.append(extra_params or {})
    if self.error is not None:
      raise self.error
    if not self.pages:
      raise AssertionError("unexpected extra request")
    return self.pages.pop(0)


class PostPageParsingTest(unittest.TestCase):
  def test_items_cursor_and_has_more_are_carried_through(self):
    page = build_post_page(page_payload(["1", "2", "3"]))

    self.assertEqual(page.count, 3)
    self.assertEqual(page.next_cursor, 1765077600000)
    self.assertTrue(page.has_more)

  def test_the_payloads_are_handed_over_untouched(self):
    """They feed build_aweme_detail directly, so nothing may be stripped."""
    payload = page_payload(["1"])
    page = build_post_page(payload)

    self.assertEqual(page.payloads[0], payload["aweme_list"][0])
    self.assertTrue(page.payloads[0]["video"]["play_addr"]["url_list"])

  def test_has_more_accepts_the_platforms_integer_form(self):
    self.assertTrue(build_post_page(page_payload(["1"], has_more=1)).has_more)
    self.assertFalse(build_post_page(page_payload(["1"], has_more=0)).has_more)

  def test_has_more_accepts_booleans_and_strings(self):
    for value, expected in ((True, True), (False, False), ("1", True),
                            ("0", False), ("true", True), (None, False)):
      with self.subTest(value=value):
        self.assertIs(
          build_post_page(page_payload(["1"], has_more=value)).has_more,
          expected,
        )

  def test_an_empty_list_is_a_valid_answer(self):
    """An owner can genuinely have no posts.

    The refusals that look like emptiness are caught upstream in douyin_session,
    so an empty list here means what it says.
    """
    page = build_post_page(page_payload([], has_more=0))

    self.assertEqual(page.count, 0)
    self.assertFalse(page.has_more)

  def test_items_without_an_id_are_dropped(self):
    payload = page_payload(["1", "2"])
    payload["aweme_list"][0].pop("aweme_id")

    page = build_post_page(payload)

    self.assertEqual(page.count, 1)
    self.assertEqual(page.payloads[0]["aweme_id"], "2")

  def test_non_object_items_are_dropped(self):
    payload = page_payload(["1"])
    payload["aweme_list"].extend([None, "x", 42])

    self.assertEqual(build_post_page(payload).count, 1)

  def test_a_missing_list_yields_an_empty_page(self):
    page = build_post_page({"status_code": 0, "has_more": 0})

    self.assertEqual(page.count, 0)
    self.assertEqual(page.next_cursor, FIRST_CURSOR)

  def test_a_non_object_payload_yields_an_empty_page(self):
    for value in (None, [], "x", 42):
      with self.subTest(value=value):
        self.assertEqual(build_post_page(value).count, 0)

  def test_a_malformed_cursor_falls_back_to_the_first_cursor(self):
    for value in ("abc", None, True, {}):
      with self.subTest(value=value):
        page = build_post_page(page_payload(["1"], next_cursor=value))
        self.assertEqual(page.next_cursor, FIRST_CURSOR)


class FetchPostPageTest(unittest.TestCase):
  def test_the_request_carries_the_owner_cursor_and_page_size(self):
    api = StubApi(pages=[page_payload(["1"])])

    fetch_post_page(api, SEC_UID, cursor=42)

    self.assertEqual(api.requests, [{
      "sec_user_id": SEC_UID,
      "max_cursor": 42,
      "count": 18,
      "publish_video_strategy_type": 2,
    }])

  def test_an_explicit_count_overrides_the_configured_page_size(self):
    api = StubApi(pages=[page_payload(["1"])])

    fetch_post_page(api, SEC_UID, count=5)

    self.assertEqual(api.requests[0]["count"], 5)

  def test_a_blank_owner_is_a_programming_error(self):
    api = StubApi(pages=[page_payload(["1"])])

    for value in (None, "", "   ", 42):
      with self.subTest(value=value):
        with self.assertRaises(ValueError):
          fetch_post_page(api, value)

  def test_a_session_failure_propagates(self):
    """Must not degrade into "this owner has no posts"."""
    api = StubApi(error=SessionExpired("the platform returned an empty body"))

    with self.assertRaises(SessionExpired):
      fetch_post_page(api, SEC_UID)


class IterAllPostsTest(unittest.TestCase):
  def test_every_page_is_walked_until_has_more_clears(self):
    api = StubApi(pages=[
      page_payload(["1", "2"], next_cursor=100, has_more=1),
      page_payload(["3", "4"], next_cursor=200, has_more=1),
      page_payload(["5"], next_cursor=300, has_more=0),
    ])

    ids = [item["aweme_id"] for item in iter_all_posts(api, SEC_UID)]

    self.assertEqual(ids, ["1", "2", "3", "4", "5"])
    self.assertEqual(
      [r["max_cursor"] for r in api.requests],
      [FIRST_CURSOR, 100, 200],
    )

  def test_duplicate_ids_across_pages_are_yielded_once(self):
    api = StubApi(pages=[
      page_payload(["1", "2"], next_cursor=100, has_more=1),
      page_payload(["2", "3"], next_cursor=200, has_more=0),
    ])

    ids = [item["aweme_id"] for item in iter_all_posts(api, SEC_UID)]

    self.assertEqual(ids, ["1", "2", "3"])

  def test_a_repeating_cursor_stops_the_walk(self):
    """A cursor that never advances would otherwise loop forever."""
    api = StubApi(pages=[
      page_payload(["1"], next_cursor=100, has_more=1),
      page_payload(["2"], next_cursor=100, has_more=1),
    ])

    ids = [item["aweme_id"] for item in iter_all_posts(api, SEC_UID)]

    self.assertEqual(ids, ["1", "2"])
    self.assertEqual(len(api.requests), 2)

  def test_a_cursor_repeating_the_first_one_stops_the_walk(self):
    api = StubApi(pages=[
      page_payload(["1"], next_cursor=FIRST_CURSOR, has_more=1),
    ])

    ids = [item["aweme_id"] for item in iter_all_posts(api, SEC_UID)]

    self.assertEqual(ids, ["1"])
    self.assertEqual(len(api.requests), 1)

  def test_an_empty_page_stops_the_walk_even_with_has_more_set(self):
    api = StubApi(pages=[
      page_payload(["1"], next_cursor=100, has_more=1),
      page_payload([], next_cursor=200, has_more=1),
    ])

    ids = [item["aweme_id"] for item in iter_all_posts(api, SEC_UID)]

    self.assertEqual(ids, ["1"])

  def test_the_page_cap_stops_the_walk(self):
    api = StubApi(pages=[
      page_payload(["1"], next_cursor=100, has_more=1),
      page_payload(["2"], next_cursor=200, has_more=1),
      page_payload(["3"], next_cursor=300, has_more=1),
    ])

    ids = [item["aweme_id"] for item in iter_all_posts(api, SEC_UID, max_pages=2)]

    self.assertEqual(ids, ["1", "2"])
    self.assertEqual(len(api.requests), 2)

  def test_a_cap_of_zero_means_no_cap(self):
    api = StubApi(pages=[
      page_payload(["1"], next_cursor=100, has_more=1),
      page_payload(["2"], next_cursor=200, has_more=0),
    ])

    ids = [item["aweme_id"] for item in iter_all_posts(api, SEC_UID, max_pages=0)]

    self.assertEqual(ids, ["1", "2"])

  def test_a_session_failure_mid_walk_propagates_after_earlier_pages(self):
    """Items already yielded stay yielded; the caller decides what partial means."""
    api = StubApi(pages=[page_payload(["1"], next_cursor=100, has_more=1)])
    walked = []

    with self.assertRaises(AssertionError):
      ##
      ## the stub raises when asked for a page it does not have, standing in for
      ## any mid-walk failure
      ##
      for item in iter_all_posts(api, SEC_UID):
        walked.append(item["aweme_id"])

    self.assertEqual(walked, ["1"])


if __name__ == "__main__":
  unittest.main()
