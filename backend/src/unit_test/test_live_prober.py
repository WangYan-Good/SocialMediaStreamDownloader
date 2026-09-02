import contextlib
import io
import logging
import unittest
from unittest.mock import patch

from requests import exceptions

from backend.src.library.baselib import get_dict_attr
from backend.src.platform.douyin import douyin_live_prober as prober_module
from backend.src.platform.douyin import douyin_redirect_trust as redirect_module
from backend.src.platform.douyin.douyin_api import DouyinApi
from backend.src.platform.douyin.douyin_live_external_info import LiveExternal, observed_at
from backend.src.platform.douyin.douyin_live_prober import DouyinLiveProber
from backend.src.unit_test.config_fixture import unified_config


class FakeConfig:
  def __init__(self, source):
    self._source = source

  def get_config_dict_attr(self, path):
    return get_dict_attr(self._source, path)


class FakeResponse:
  def __init__(self, url="https://live.douyin.com/douyin/webcast/reflow/123?sec_user_id=user",
               status_code=200, payload=None, location=None):
    self.url = url
    self.status_code = status_code
    self._payload = payload
    self.headers = {}
    if location is not None:
      self.headers["Location"] = location

  def raise_for_status(self):
    return None

  def json(self):
    return self._payload


def living_payload(room_status=2):
  return {
    "status_code": 0,
    "extra": {"now": 1786000000000},
    "data": {
      "room": {
        "id": "room-1",
        "status": room_status,
        "title": "标题",
        "owner_user_id": 42,
        "owner": {"nickname": "主播", "sec_uid": "sec", "status": 1},
      }
    },
  }


class FakeContext:
  """Minimal collaborator exposing the primitives the prober calls back into."""

  def __init__(self, responses, params=None, raise_on_live=None, source=None):
    source = unified_config() if source is None else source
    self.config = FakeConfig(source)
    self.API = DouyinApi(get_dict_attr(source, "$.platform.douyin.api"))
    self.live_external_info = LiveExternal()
    self._responses = list(responses)
    self._params = params if params is not None else {"room_id": "123"}
    self._raise_on_live = raise_on_live
    self.pauses = 0
    self.requests = 0
    self.calls = []

  def query_url(
    self,
    method,
    url,
    params,
    timeout,
    headers,
    allow_redirects=True,
  ):
    self.requests += 1
    self.calls.append({
      "method": method,
      "url": url,
      "params": params,
      "timeout": timeout,
      "headers": headers,
      "allow_redirects": allow_redirects,
    })
    if self._raise_on_live is not None and self.requests == 3:
      raise self._raise_on_live
    outcome = self._responses.pop(0)
    if isinstance(outcome, Exception):
      raise outcome
    if (
      self.requests == 1
      and allow_redirects is False
      and not outcome.headers
      and outcome.url != url
    ):
      self._responses.insert(0, outcome)
      return FakeResponse(url=url, status_code=302, location=outcome.url)
    return outcome

  def pause(self):
    self.pauses += 1

  def construct_live_params_no_login(self, share_info, header):
    return self._params


class ObservedAtTest(unittest.TestCase):
  def test_the_payload_timestamp_is_used_when_present(self):
    self.assertEqual(1786000000.0, observed_at(living_payload()).timestamp())

  def test_a_missing_or_unusable_timestamp_falls_back_to_the_clock(self):
    self.assertIsNotNone(observed_at({}))
    self.assertIsNotNone(observed_at({"extra": {"now": "not-a-number"}}))


class LiveProberSuccessTest(unittest.TestCase):
  def test_an_unsafe_share_redirect_is_blocked_before_live_info(self):
    sentinel = "SECRET_LOCATION_17A"
    context = FakeContext([
      FakeResponse(
        url="https://v.douyin.com/example/",
        status_code=302,
        location="http://127.0.0.1/path?token=" + sentinel,
      )
    ])
    output = io.StringIO()
    logger = logging.Logger("phase17a-live-redirect")
    logger.propagate = False
    logger.addHandler(logging.StreamHandler(output))

    with patch.object(prober_module, "get_logger", return_value=logger), \
         patch.object(redirect_module, "get_logger", return_value=logger), \
         contextlib.redirect_stdout(io.StringIO()) as stdout, \
         contextlib.redirect_stderr(io.StringIO()) as stderr:
      result = DouyinLiveProber(context).probe(
        "https://v.douyin.com/example/"
      )

    self.assertFalse(result.ok)
    self.assertEqual(context.requests, 1)
    self.assertNotIn(sentinel, result.error)
    visible = output.getvalue() + stdout.getvalue() + stderr.getvalue()
    self.assertNotIn(sentinel, visible)

  def test_debug_diagnostics_are_positive_but_never_emit_transport_secrets(self):
    sentinels = (
      "SECRET_COOKIE_13A",
      "SECRET_AUTHORIZATION_13A",
      "SECRET_MSTOKEN_13A",
      "SECRET_X_BOGUS_13A",
      "SECRET_VERIFY_FP_13A",
      "SECRET_SIGN_13A",
      "SECRET_QUERY_TOKEN_13A",
      "SECRET_PROXY_PASSWORD_13A",
      "SECRET_SESSION_13A",
      "SECRET_CSRF_13A",
    )
    source = unified_config()
    source["server"]["debug_mode"] = True
    source["platform"]["douyin"]["headers"]["share_live_url_no_login"].update({
      "cookie": sentinels[0],
      "Authorization": sentinels[1],
      "X-Session": sentinels[8],
      "X-CSRF-Token": sentinels[9],
    })
    source["platform"]["douyin"]["api"]["LIVE_INFO_ROOM_ID"] = (
      "https://webcast.amemv.com/webcast/room/reflow/info/"
      "?sign=" + sentinels[5]
    )
    source["platform"]["douyin"]["login"]["proxies"] = {
      "https": "http://user:{}@proxy.example.test".format(sentinels[7])
    }
    params = {
      "room_id": "123",
      "msToken": sentinels[2],
      "X-Bogus": sentinels[3],
      "verifyFp": sentinels[4],
      "sign": sentinels[5],
      "token": sentinels[6],
    }
    context = FakeContext(
      [FakeResponse(), FakeResponse(payload=living_payload(2))],
      params=params,
      source=source,
    )
    login_source = unified_config()
    login_source["server"]["debug_mode"] = True
    login_source["download"]["user_login"] = True
    login_source["platform"]["douyin"]["headers"]["share_live_url"].update({
      "cookie": sentinels[0],
      "Authorization": sentinels[1],
      "X-Session": sentinels[8],
      "X-CSRF-Token": sentinels[9],
    })
    login_context = FakeContext(
      [FakeResponse(), FakeResponse(payload=living_payload(2))],
      source=login_source,
    )

    messages = []

    class Logger:
      def _record(self, message):
        messages.append(str(message))

      debug = _record
      info = _record
      warning = _record
      error = _record
      exception = _record

    stdout = io.StringIO()
    stderr = io.StringIO()
    with patch.object(prober_module, "get_logger", return_value=Logger()):
      with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        result = DouyinLiveProber(context).probe(
          "https://v.douyin.com/example/?token=" + sentinels[6]
        )
        login_result = DouyinLiveProber(login_context).probe(
          "https://v.douyin.com/login-example/?token=" + sentinels[6]
        )

    visible = stdout.getvalue() + stderr.getvalue() + "\n".join(messages)
    self.assertTrue(result.ok)
    self.assertTrue(login_result.ok)
    for sentinel in sentinels:
      with self.subTest(sentinel=sentinel):
        self.assertNotIn(sentinel, visible)
    self.assertIn("live diagnostic event=live_info_request", visible)
    self.assertIn("host=webcast.amemv.com", visible)

  def test_a_broadcasting_room_is_reported_with_its_details(self):
    context = FakeContext([FakeResponse(), FakeResponse(payload=living_payload(2))])

    result = DouyinLiveProber(context).probe("https://v.douyin.com/example/")

    self.assertTrue(result.ok)
    self.assertTrue(result.is_living)
    self.assertEqual(2, result.room_status)
    self.assertEqual("room-1", result.room_id)
    self.assertEqual("42", result.owner_user_id)
    self.assertEqual("主播", result.nickname)
    self.assertEqual("标题", result.title)
    self.assertIsNotNone(result.checked_at)
    self.assertIsNotNone(result.response)

  def test_a_finished_room_still_succeeds_but_is_not_living(self):
    context = FakeContext([FakeResponse(), FakeResponse(payload=living_payload(4))])

    result = DouyinLiveProber(context).probe("https://v.douyin.com/example/")

    self.assertTrue(result.ok)
    self.assertFalse(result.is_living)

  def test_both_platform_requests_are_spaced_by_a_pause(self):
    context = FakeContext([FakeResponse(), FakeResponse(payload=living_payload(2))])

    DouyinLiveProber(context).probe("https://v.douyin.com/example/")

    self.assertEqual(3, context.requests)
    self.assertEqual(3, context.pauses)
    self.assertTrue(
      all(call["allow_redirects"] is False for call in context.calls[:2])
    )


class LiveProberFailureTest(unittest.TestCase):
  def test_a_share_url_timeout_ends_the_probe_without_raising(self):
    context = FakeContext([exceptions.ReadTimeout()])

    result = DouyinLiveProber(context).probe("https://v.douyin.com/example/")

    self.assertFalse(result.ok)
    self.assertEqual("请求超时", result.error)

  def test_a_share_url_failure_is_reported_rather_than_raised(self):
    context = FakeContext([RuntimeError("network unavailable")])

    result = DouyinLiveProber(context).probe("https://v.douyin.com/example/")

    self.assertFalse(result.ok)
    self.assertEqual("分享链接请求失败", result.error)

  def test_a_non_200_live_response_is_reported(self):
    context = FakeContext([FakeResponse(), FakeResponse(status_code=403)])

    result = DouyinLiveProber(context).probe("https://v.douyin.com/example/")

    self.assertFalse(result.ok)
    self.assertEqual("直播信息请求失败", result.error)

  def test_an_unknown_rejection_code_is_surfaced_verbatim(self):
    payload = living_payload()
    payload["status_code"] = 4003
    context = FakeContext([FakeResponse(), FakeResponse(payload=payload)])

    result = DouyinLiveProber(context).probe("https://v.douyin.com/example/")

    self.assertFalse(result.ok)
    ##
    ## An unmapped code must still reach the operator rather than collapse into a
    ## generic message.
    ##
    self.assertIn("4003", result.error)

  def test_a_known_rejection_code_gets_its_own_wording(self):
    payload = living_payload()
    payload["status_code"] = 10033
    payload["data"] = {
      "message": "forbidden",
      "prompts": "Server upgrading. Please try again.",
    }
    context = FakeContext([FakeResponse(), FakeResponse(payload=payload)])

    result = DouyinLiveProber(context).probe("https://v.douyin.com/example/")

    self.assertFalse(result.ok)
    self.assertIn("10033", result.error)
    self.assertIn("稍后重试", result.error)

  def test_a_rejection_with_an_unreadable_body_still_reports_its_code(self):
    class UnreadableResponse(FakeResponse):
      def __init__(self):
        super().__init__(status_code=200)
        self._calls = 0

      def json(self):
        ##
        ## get_status reads the code first; the explanation lookup then fails.
        ##
        self._calls += 1
        if self._calls == 1:
          return {"status_code": 10033}
        raise ValueError("body is not decodable")

    context = FakeContext([FakeResponse(), UnreadableResponse()])

    result = DouyinLiveProber(context).probe("https://v.douyin.com/example/")

    self.assertFalse(result.ok)
    self.assertIn("10033", result.error)

  def test_an_unexpected_live_request_error_still_propagates(self):
    context = FakeContext([FakeResponse()], raise_on_live=MemoryError("boom"))

    with self.assertRaises(MemoryError):
      DouyinLiveProber(context).probe("https://v.douyin.com/example/")

  def test_a_missing_url_is_a_programming_error(self):
    with self.assertRaises(ValueError):
      DouyinLiveProber(FakeContext([])).probe(None)

  def test_a_missing_context_is_rejected(self):
    with self.assertRaises(ValueError):
      DouyinLiveProber(None)


if __name__ == "__main__":
  unittest.main()
