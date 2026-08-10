import json
import unittest

from backend.src.platform.douyin import douyin_aweme_resolver as resolver_module
from backend.src.platform.douyin.douyin_aweme_external_info import (
  MEDIA_VIDEO,
  SOURCE_API,
  SOURCE_HTML,
)
from backend.src.platform.douyin.douyin_aweme_resolver import (
  DouyinAwemeResolver,
  extract_embedded_payloads,
  find_aweme_payload,
)
from backend.src.unit_test.config_fixture import unified_config


AWEME_ID = "7123456789012345678"
POST_URL = "https://www.douyin.com/video/" + AWEME_ID


def aweme_payload(aweme_id=AWEME_ID, **overrides):
  payload = {
    "aweme_id": aweme_id,
    "desc": "测试作品",
    "create_time": 1712484087,
    "author": {
      "uid": "999",
      "sec_uid": "MS4wLjABAAAAsec",
      "nickname": "作者",
    },
    "video": {
      "play_addr": {"url_list": ["https://v.example.test/play.mp4"]},
      "cover": {"url_list": ["https://p.example.test/cover.jpeg"]},
    },
    "music": {"play_url": {"url_list": ["https://m.example.test/song.mp3"]}},
  }
  payload.update(overrides)
  return payload


def aweme_config(**overrides):
  config = unified_config()
  config["download"]["user_login"] = False
  aweme = config["platform"]["douyin"]["aweme"]
  aweme.update(overrides)
  return config


class FakeResponse:
  def __init__(self, status_code=200, payload=None, text="", url=None):
    self.status_code = status_code
    self._payload = payload
    self.text = text
    self.encoding = None
    ##
    ## where a followed share link landed
    ##
    self.url = url

  def json(self):
    if self._payload is None:
      raise ValueError("no json payload")
    return self._payload


class RecordingTransport:
  """Answers each request from a queue and records what was asked."""

  def __init__(self, responses):
    self._responses = list(responses)
    self.calls = []

  def __call__(self, **kwargs):
    self.calls.append(kwargs)
    if not self._responses:
      raise AssertionError("unexpected extra request: {}".format(kwargs))
    outcome = self._responses.pop(0)
    if isinstance(outcome, Exception):
      raise outcome
    return outcome


class ResolverTestCase(unittest.TestCase):
  def build(self, config=None, responses=()):
    transport = RecordingTransport(responses)
    self._original_request = resolver_module.request
    resolver_module.request = transport
    self.addCleanup(self._restore)
    resolver = DouyinAwemeResolver(
      config if config is not None else aweme_config(),
      sleeper=lambda: None,
    )
    return resolver, transport

  def _restore(self):
    resolver_module.request = self._original_request


class ApiRouteTest(ResolverTestCase):
  def test_api_success_produces_a_detail_marked_api(self):
    resolver, transport = self.build(
      responses=[
        FakeResponse(payload={"status_code": 0, "aweme_detail": aweme_payload()})
      ]
    )

    result = resolver.resolve(POST_URL)

    self.assertTrue(result.ok)
    self.assertEqual(result.aweme_id, AWEME_ID)
    self.assertEqual(result.source, SOURCE_API)
    self.assertEqual(result.detail.media[0].kind, MEDIA_VIDEO)
    self.assertEqual(len(transport.calls), 1)

  def test_api_request_carries_the_aweme_id_and_a_signature(self):
    resolver, transport = self.build(
      responses=[
        FakeResponse(payload={"status_code": 0, "aweme_detail": aweme_payload()})
      ]
    )

    resolver.resolve(POST_URL)
    params = transport.calls[0]["params"]

    self.assertEqual(params["aweme_id"], AWEME_ID)
    self.assertIn("a_bogus", params)
    self.assertIn("verifyFp", params)
    self.assertEqual(params["verifyFp"], params["fp"])
    self.assertEqual(transport.calls[0]["method"], "GET")

  def test_api_request_headers_are_flat_strings(self):
    """requests rejects a nested mapping, so the header must be flattened."""
    resolver, transport = self.build(
      responses=[
        FakeResponse(payload={"status_code": 0, "aweme_detail": aweme_payload()})
      ]
    )

    resolver.resolve(POST_URL)
    headers = transport.calls[0]["headers"]

    self.assertTrue(headers)
    for key, value in headers.items():
      self.assertIsInstance(key, str)
      self.assertIsInstance(value, str)


class HtmlFallbackTest(ResolverTestCase):
  def _share_page(self, payload):
    document = {
      "loaderData": {
        "video_(id)/page": {"videoInfoRes": {"item_list": [payload]}}
      }
    }
    return (
      "<html><body><script>window._ROUTER_DATA = "
      + json.dumps(document)
      + ";</script></body></html>"
    )

  def test_html_is_used_when_the_api_request_raises(self):
    resolver, transport = self.build(
      responses=[
        TimeoutError("detail api timed out"),
        FakeResponse(text=self._share_page(aweme_payload())),
      ]
    )

    result = resolver.resolve(POST_URL)

    self.assertTrue(result.ok)
    self.assertEqual(result.source, SOURCE_HTML)
    self.assertIn("TimeoutError", result.api_error)
    self.assertEqual(len(transport.calls), 2)

  def test_html_is_used_when_the_api_reports_a_status_code(self):
    resolver, _ = self.build(
      responses=[
        FakeResponse(payload={"status_code": 2145, "aweme_detail": None}),
        FakeResponse(text=self._share_page(aweme_payload())),
      ]
    )

    result = resolver.resolve(POST_URL)

    self.assertTrue(result.ok)
    self.assertEqual(result.source, SOURCE_HTML)
    self.assertIn("2145", result.api_error)

  def test_html_is_used_when_the_api_returns_a_non_200(self):
    resolver, _ = self.build(
      responses=[
        FakeResponse(status_code=444),
        FakeResponse(text=self._share_page(aweme_payload())),
      ]
    )

    result = resolver.resolve(POST_URL)

    self.assertTrue(result.ok)
    self.assertEqual(result.source, SOURCE_HTML)

  def test_html_is_used_when_the_api_omits_the_detail(self):
    resolver, _ = self.build(
      responses=[
        FakeResponse(payload={"status_code": 0}),
        FakeResponse(text=self._share_page(aweme_payload())),
      ]
    )

    result = resolver.resolve(POST_URL)

    self.assertTrue(result.ok)
    self.assertEqual(result.source, SOURCE_HTML)

  def test_fallback_is_skipped_when_disabled(self):
    resolver, transport = self.build(
      config=aweme_config(html_fallback=False),
      responses=[TimeoutError("detail api timed out")],
    )

    result = resolver.resolve(POST_URL)

    self.assertFalse(result.ok)
    self.assertIn("html fallback is disabled", result.reason)
    self.assertEqual(len(transport.calls), 1)

  def test_both_routes_failing_reports_both_reasons(self):
    resolver, _ = self.build(
      responses=[
        TimeoutError("detail api timed out"),
        FakeResponse(status_code=503),
      ]
    )

    result = resolver.resolve(POST_URL)

    self.assertFalse(result.ok)
    self.assertIn("TimeoutError", result.api_error)
    self.assertIn("503", result.html_error)
    self.assertIsNone(result.detail)

  def test_share_page_without_an_embedded_payload_fails_cleanly(self):
    resolver, _ = self.build(
      responses=[
        TimeoutError("detail api timed out"),
        FakeResponse(text="<html><body>nothing here</body></html>"),
      ]
    )

    result = resolver.resolve(POST_URL)

    self.assertFalse(result.ok)
    self.assertIn("embedded payload", result.html_error)


class UnavailablePostTest(ResolverTestCase):
  def test_api_saying_there_is_nothing_to_download_skips_the_fallback(self):
    """A deleted post is an answer, not a transport failure.

    Trying the second route cannot change the answer, so it must not spend
    another request on it.
    """
    resolver, transport = self.build(
      responses=[
        FakeResponse(
          payload={
            "status_code": 0,
            "aweme_detail": {"aweme_id": AWEME_ID, "desc": "gone"},
          }
        )
      ]
    )

    result = resolver.resolve(POST_URL)

    self.assertFalse(result.ok)
    self.assertIn("no downloadable media", result.reason)
    self.assertEqual(len(transport.calls), 1)

  def test_unrecognised_url_is_refused_without_any_request(self):
    resolver, transport = self.build(responses=[])

    result = resolver.resolve("https://live.douyin.com/123456")

    self.assertFalse(result.ok)
    self.assertIn("does not point at a single post", result.reason)
    self.assertEqual(len(transport.calls), 0)

  def test_a_short_share_link_is_followed_before_classifying(self):
    """A v.douyin.com link carries no id, so it has to be followed first.

    The handler normally does this and hands the result down; this covers a
    standalone call.
    """
    resolver, transport = self.build(
      responses=[
        FakeResponse(text=""),
        FakeResponse(payload={"status_code": 0, "aweme_detail": aweme_payload()}),
      ]
    )
    transport._responses[0].url = POST_URL

    result = resolver.resolve("https://v.douyin.com/MqjfOkWSeG8/")

    self.assertTrue(result.ok)
    self.assertEqual(result.aweme_id, AWEME_ID)
    self.assertEqual(len(transport.calls), 2)

  def test_a_live_room_is_refused_without_following_it(self):
    """A live room is already a definite "not a post"; following it learns
    nothing and costs a request."""
    resolver, transport = self.build(responses=[])

    result = resolver.resolve("https://live.douyin.com/123456")

    self.assertFalse(result.ok)
    self.assertEqual(len(transport.calls), 0)

  def test_a_user_home_page_is_refused_without_following_it(self):
    resolver, transport = self.build(responses=[])

    result = resolver.resolve("https://www.douyin.com/user/MS4wLjABAAAAqGTe")

    self.assertFalse(result.ok)
    self.assertEqual(len(transport.calls), 0)

  def test_a_short_link_that_leads_nowhere_useful_is_reported(self):
    resolver, transport = self.build(responses=[FakeResponse(text="")])
    transport._responses[0].url = "https://www.douyin.com/user/MS4w"

    result = resolver.resolve("https://v.douyin.com/MqjfOkWSeG8/")

    self.assertFalse(result.ok)
    self.assertIn("does not point at a single post", result.reason)

  def test_a_failing_share_link_is_reported(self):
    resolver, _ = self.build(
      responses=[TimeoutError("share link timed out")]
    )

    result = resolver.resolve("https://v.douyin.com/MqjfOkWSeG8/")

    self.assertFalse(result.ok)
    self.assertIn("could not follow the share link", result.reason)

  def test_explicit_aweme_id_bypasses_url_classification(self):
    resolver, _ = self.build(
      responses=[
        FakeResponse(payload={"status_code": 0, "aweme_detail": aweme_payload()})
      ]
    )

    result = resolver.resolve("https://v.douyin.com/short/", aweme_id=AWEME_ID)

    self.assertTrue(result.ok)
    self.assertEqual(result.aweme_id, AWEME_ID)


class EmbeddedPayloadExtractionTest(unittest.TestCase):
  def test_router_data_is_extracted(self):
    html = (
      '<script>window._ROUTER_DATA = {"a": 1};</script>'
    )
    self.assertEqual(extract_embedded_payloads(html), [{"a": 1}])

  def test_render_data_is_extracted(self):
    html = '<script id="RENDER_DATA" type="application/json">{"a": 2}</script>'
    self.assertEqual(extract_embedded_payloads(html), [{"a": 2}])

  def test_uri_encoded_render_data_is_decoded(self):
    html = (
      '<script id="RENDER_DATA" type="application/json">'
      '%7B%22a%22%3A%203%7D</script>'
    )
    self.assertEqual(extract_embedded_payloads(html), [{"a": 3}])

  def test_undecodable_blob_is_ignored(self):
    html = '<script>window._ROUTER_DATA = {not json};</script>'
    self.assertEqual(extract_embedded_payloads(html), [])

  def test_no_script_yields_nothing(self):
    self.assertEqual(extract_embedded_payloads("<html></html>"), [])
    self.assertEqual(extract_embedded_payloads(""), [])
    self.assertEqual(extract_embedded_payloads(None), [])


class AwemePayloadSearchTest(unittest.TestCase):
  def test_post_is_found_at_any_depth(self):
    payload = aweme_payload()
    nested = {"a": {"b": [{"c": {"d": [payload]}}]}}

    self.assertIs(find_aweme_payload(nested, AWEME_ID), payload)

  def test_the_requested_post_wins_over_a_neighbour(self):
    """A share page can embed related posts next to the one asked for."""
    wanted = aweme_payload(AWEME_ID)
    other = aweme_payload("7000000000000000000")
    document = {"list": [other, wanted]}

    self.assertIs(find_aweme_payload(document, AWEME_ID), wanted)

  def test_a_different_id_is_not_accepted_when_one_was_requested(self):
    other = aweme_payload("7000000000000000000")

    self.assertIsNone(find_aweme_payload({"list": [other]}, AWEME_ID))

  def test_any_post_matches_when_no_id_is_requested(self):
    other = aweme_payload("7000000000000000000")

    self.assertIs(find_aweme_payload({"list": [other]}, None), other)

  def test_an_object_without_media_keys_is_not_a_post(self):
    self.assertIsNone(
      find_aweme_payload({"aweme_id": AWEME_ID, "desc": "only text"}, AWEME_ID)
    )

  def test_an_object_without_an_id_is_not_a_post(self):
    self.assertIsNone(find_aweme_payload({"video": {}, "music": {}}))

  def test_search_stops_at_the_depth_limit(self):
    payload = aweme_payload()
    nested = payload
    for _ in range(60):
      nested = {"deeper": nested}

    self.assertIsNone(find_aweme_payload(nested, AWEME_ID))


if __name__ == "__main__":
  unittest.main()
