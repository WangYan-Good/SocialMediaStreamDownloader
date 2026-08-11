import unittest

from backend.src.platform.douyin.douyin_owner_detail import (
  OwnerUnavailable,
  build_owner_detail,
  fetch_owner_detail,
)


SEC_UID = "MS4wLjABAAAAGZkW5n1EHZD_TFyQ-QiaISBPemtKFxVVdhLSeoXhh-U"


def user_payload(**overrides):
  ##
  ## Shaped after the real USER_DETAIL response captured during design
  ## verification: nickname ✨米开朗绿萝✨, aweme_count 238, follower 858825.
  ##
  user = {
    "sec_uid": SEC_UID,
    "uid": "58859666123",
    "nickname": "✨米开朗绿萝✨",
    "unique_id": "lvluo2024",
    "signature": "分享生活",
    "avatar_larger": {"url_list": ["https://p.example.test/large.jpeg"]},
    "avatar_thumb": {"url_list": ["https://p.example.test/thumb.jpeg"]},
    "follower_count": 858825,
    "following_count": 42,
    "aweme_count": 238,
    "total_favorited": 12345678,
  }
  user.update(overrides)
  return {"status_code": 0, "user": user}


class StubApi:
  def __init__(self, payload=None, error=None):
    self.payload = payload
    self.error = error
    self.calls = []

  def get(self, api_attr, extra_params=None):
    self.calls.append((api_attr, extra_params))
    if self.error is not None:
      raise self.error
    return self.payload


class OwnerDetailParsingTest(unittest.TestCase):
  def test_every_displayed_field_is_carried_through(self):
    detail = build_owner_detail(user_payload())

    self.assertEqual(detail.sec_user_id, SEC_UID)
    self.assertEqual(detail.uid, "58859666123")
    self.assertEqual(detail.nickname, "✨米开朗绿萝✨")
    self.assertEqual(detail.unique_id, "lvluo2024")
    self.assertEqual(detail.signature, "分享生活")
    self.assertEqual(detail.follower_count, 858825)
    self.assertEqual(detail.following_count, 42)
    self.assertEqual(detail.aweme_count, 238)
    self.assertEqual(detail.total_favorited, 12345678)

  def test_the_largest_available_avatar_is_preferred(self):
    detail = build_owner_detail(user_payload())

    self.assertEqual(detail.avatar_url, "https://p.example.test/large.jpeg")

  def test_a_smaller_avatar_is_used_when_the_larger_is_missing(self):
    payload = user_payload()
    payload["user"].pop("avatar_larger")

    detail = build_owner_detail(payload)

    self.assertEqual(detail.avatar_url, "https://p.example.test/thumb.jpeg")

  def test_no_avatar_yields_an_empty_string_rather_than_none(self):
    payload = user_payload()
    payload["user"].pop("avatar_larger")
    payload["user"].pop("avatar_thumb")

    self.assertEqual(build_owner_detail(payload).avatar_url, "")

  def test_a_non_http_avatar_entry_is_skipped(self):
    payload = user_payload(avatar_larger={"url_list": ["", "not-a-url"]})

    self.assertEqual(
      build_owner_detail(payload).avatar_url,
      "https://p.example.test/thumb.jpeg",
    )

  def test_a_numeric_uid_is_normalised_to_text(self):
    detail = build_owner_detail(user_payload(uid=58859666123))

    self.assertEqual(detail.uid, "58859666123")

  def test_short_id_stands_in_for_a_missing_unique_id(self):
    payload = user_payload(short_id="99887766")
    payload["user"].pop("unique_id")

    self.assertEqual(build_owner_detail(payload).unique_id, "99887766")

  def test_missing_counts_read_as_zero(self):
    payload = user_payload()
    for key in ("follower_count", "following_count", "aweme_count",
                "total_favorited"):
      payload["user"].pop(key)

    detail = build_owner_detail(payload)

    self.assertEqual(detail.follower_count, 0)
    self.assertEqual(detail.aweme_count, 0)

  def test_a_negative_count_reads_as_zero(self):
    self.assertEqual(
      build_owner_detail(user_payload(follower_count=-1)).follower_count,
      0,
    )

  def test_a_non_integer_count_reads_as_zero(self):
    for value in ("858825", None, True, 1.5):
      with self.subTest(value=value):
        self.assertEqual(
          build_owner_detail(user_payload(follower_count=value)).follower_count,
          0,
        )

  def test_missing_text_fields_read_as_empty_strings(self):
    payload = user_payload()
    for key in ("nickname", "unique_id", "signature"):
      payload["user"].pop(key)

    detail = build_owner_detail(payload)

    self.assertEqual(detail.nickname, "")
    self.assertEqual(detail.unique_id, "")
    self.assertEqual(detail.signature, "")

  def test_the_requested_id_stands_in_when_the_payload_omits_it(self):
    payload = user_payload()
    payload["user"].pop("sec_uid")

    detail = build_owner_detail(payload, sec_user_id=SEC_UID)

    self.assertEqual(detail.sec_user_id, SEC_UID)

  def test_the_detail_is_immutable(self):
    detail = build_owner_detail(user_payload())

    with self.assertRaises(Exception):
      detail.nickname = "other"


class OwnerUnavailableTest(unittest.TestCase):
  """An empty user here means the account is gone, not that we are logged out.

  The logged-out form - {"status_msg": "blocked", "user": {}} - is caught earlier
  by douyin_session.read_payload and raised as SessionExpired, so it never
  reaches this function.
  """

  def test_an_empty_user_object(self):
    with self.assertRaises(OwnerUnavailable):
      build_owner_detail({"status_code": 0, "user": {}})

  def test_a_missing_user_key(self):
    with self.assertRaises(OwnerUnavailable):
      build_owner_detail({"status_code": 0})

  def test_a_non_object_payload(self):
    for value in (None, [], "x", 42):
      with self.subTest(value=value):
        with self.assertRaises(OwnerUnavailable):
          build_owner_detail(value)

  def test_a_user_without_any_identity(self):
    with self.assertRaises(OwnerUnavailable):
      build_owner_detail({"user": {"nickname": "无身份"}})

  def test_a_user_with_only_a_uid_is_accepted(self):
    detail = build_owner_detail({"user": {"uid": "1", "nickname": "n"}})

    self.assertEqual(detail.uid, "1")


class FetchOwnerDetailTest(unittest.TestCase):
  def test_the_request_carries_the_sec_user_id(self):
    api = StubApi(payload=user_payload())

    detail = fetch_owner_detail(api, SEC_UID)

    self.assertEqual(api.calls, [
      ("$.USER_DETAIL", {
        "sec_user_id": SEC_UID,
        "publish_video_strategy_type": 2,
      }),
    ])
    self.assertEqual(detail.nickname, "✨米开朗绿萝✨")

  def test_a_blank_sec_user_id_is_a_programming_error(self):
    api = StubApi(payload=user_payload())

    for value in (None, "", "   ", 42):
      with self.subTest(value=value):
        with self.assertRaises(ValueError):
          fetch_owner_detail(api, value)

  def test_a_session_failure_propagates(self):
    """The caller must tell the user to refresh the cookie, not show a blank card."""
    from backend.src.platform.douyin.douyin_session import SessionExpired

    api = StubApi(error=SessionExpired("the platform returned an empty body"))

    with self.assertRaises(SessionExpired):
      fetch_owner_detail(api, SEC_UID)


if __name__ == "__main__":
  unittest.main()
