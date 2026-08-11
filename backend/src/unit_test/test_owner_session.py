import unittest
from datetime import datetime, timedelta

from backend.src.platform.douyin.douyin_session import (
  SessionExpired,
  UpstreamRejected,
  credential_days_left,
  credential_expiry,
  read_payload,
)


class FakeResponse:
  def __init__(self, text="", status_code=200):
    self.text = text
    self.status_code = status_code

  def json(self):
    import json
    return json.loads(self.text)


class SessionRefusalTest(unittest.TestCase):
  """The four ways douyin says "your session is dead" without saying it.

  Every one of these arrives as something that reads like "no data".  During
  design verification an expired cookie produced the empty-body form and it was
  mistaken for a platform-level block on the endpoint for over an hour.
  """

  def test_an_empty_body_is_a_session_failure(self):
    """The one that reads as "this owner has no posts"."""
    with self.assertRaises(SessionExpired) as caught:
      read_payload(FakeResponse(text=""), endpoint="USER_POST")

    self.assertIn("empty body", str(caught.exception))
    self.assertIn("USER_POST", str(caught.exception))

  def test_a_whitespace_only_body_is_a_session_failure(self):
    with self.assertRaises(SessionExpired):
      read_payload(FakeResponse(text="   \n  "))

  def test_a_blocked_status_message_is_a_session_failure(self):
    body = '{"status_code":0,"status_msg":"blocked","user":{}}'
    with self.assertRaises(SessionExpired) as caught:
      read_payload(FakeResponse(text=body))

    self.assertIn("blocked", str(caught.exception))

  def test_a_blocked_status_message_is_matched_case_insensitively(self):
    body = '{"status_code":0,"status_msg":"BLOCKED"}'
    with self.assertRaises(SessionExpired):
      read_payload(FakeResponse(text=body))

  def test_an_argus_403_is_a_session_failure(self):
    with self.assertRaises(SessionExpired) as caught:
      read_payload(
        FakeResponse(
          text="Blocked by ArgusSecurityPlugin Validate Error",
          status_code=403,
        )
      )

    self.assertIn("signature validation", str(caught.exception))

  def test_a_verification_bundle_is_a_session_failure(self):
    for marker in ("verifycenter", "rmc-nocaptcha", "captcha", "secsdk"):
      with self.subTest(marker=marker):
        body = "<html><script src='https://x/{}/index.js'></script></html>".format(
          marker
        )
        with self.assertRaises(SessionExpired) as caught:
          read_payload(FakeResponse(text=body))
        self.assertIn("human verification", str(caught.exception))


class UpstreamRefusalTest(unittest.TestCase):
  """Refusals a fresh cookie would not fix are reported differently."""

  def test_a_non_json_body_without_verification_markers(self):
    with self.assertRaises(UpstreamRejected) as caught:
      read_payload(FakeResponse(text="<html>maintenance</html>"))

    self.assertIn("non-JSON", str(caught.exception))

  def test_a_non_object_payload(self):
    with self.assertRaises(UpstreamRejected):
      read_payload(FakeResponse(text="[1, 2, 3]"))

  def test_a_non_200_status_with_a_valid_body(self):
    with self.assertRaises(UpstreamRejected) as caught:
      read_payload(FakeResponse(text='{"status_code":0}', status_code=503))

    self.assertIn("503", str(caught.exception))


class SuccessfulPayloadTest(unittest.TestCase):
  def test_a_good_payload_is_returned(self):
    payload = read_payload(
      FakeResponse(text='{"status_code":0,"aweme_list":[],"has_more":0}')
    )

    self.assertEqual(payload["status_code"], 0)
    self.assertEqual(payload["aweme_list"], [])

  def test_an_empty_list_is_not_treated_as_a_failure(self):
    """A genuinely empty list is a valid answer once the session is good."""
    payload = read_payload(FakeResponse(text='{"aweme_list":[],"has_more":0}'))

    self.assertEqual(payload["aweme_list"], [])


class CredentialExpiryTest(unittest.TestCase):
  """sid_guard states its own lifetime, so expiry is knowable before any request.

  Surfaced in the UI so an expiry is noticed as an expiry, not as an empty list.
  """

  def _cookie(self, issued: datetime, lifetime_days: int) -> str:
    return "ttwid=1; sid_guard=tok%7C{}%7C{}%7CThu%2C+01-Jan-2026+00%3A00%3A00+GMT; other=x".format(
      int(issued.timestamp()),
      lifetime_days * 86400,
    )

  def test_a_fresh_cookie_reports_days_remaining(self):
    ##
    ## issued a day ago with a 60 day lifetime leaves 59
    ##
    now = datetime(2026, 8, 11, 12, 0, 0)
    cookie = self._cookie(now - timedelta(days=1), 60)

    self.assertEqual(credential_days_left(cookie, now=now), 59)

  def test_an_expired_cookie_reports_a_negative_number(self):
    now = datetime(2026, 8, 11, 12, 0, 0)
    cookie = self._cookie(now - timedelta(days=100), 59)

    self.assertLess(credential_days_left(cookie, now=now), 0)

  def test_the_expiry_datetime_is_issued_plus_lifetime(self):
    issued = datetime(2026, 8, 1, 0, 0, 0)
    cookie = self._cookie(issued, 10)

    self.assertEqual(
      credential_expiry(cookie),
      datetime(2026, 8, 11, 0, 0, 0),
    )

  def test_a_cookie_without_sid_guard_is_unknown(self):
    self.assertIsNone(credential_days_left("ttwid=1; other=x"))
    self.assertIsNone(credential_expiry("ttwid=1; other=x"))

  def test_a_malformed_sid_guard_is_unknown(self):
    for value in ("tok", "tok%7Cabc%7Cdef", "tok%7C0%7C0", "tok%7C-1%7C-1"):
      with self.subTest(value=value):
        self.assertIsNone(credential_days_left("sid_guard=" + value))

  def test_missing_and_empty_input_is_unknown(self):
    for value in (None, "", "   ", 42):
      with self.subTest(value=value):
        self.assertIsNone(credential_days_left(value))

  def test_sid_guard_is_not_matched_inside_another_cookie_name(self):
    """``not_sid_guard=`` must not be read as ``sid_guard=``."""
    self.assertIsNone(credential_days_left("not_sid_guard=tok%7C100%7C100"))


if __name__ == "__main__":
  unittest.main()
