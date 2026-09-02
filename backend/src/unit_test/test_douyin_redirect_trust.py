import contextlib
import io
import unittest
from unittest.mock import patch

from backend.src.platform.douyin.douyin_redirect_trust import (
  DouyinRedirectTrust,
)
from backend.src.platform.resource_resolution import (
  RedirectLoop,
  ResourceResolveError,
  ShortLinkUnavailable,
  TooManyRedirects,
  UntrustedRedirect,
)


SHORT_URL = "https://v.douyin.com/phase17a/"
POST_URL = "https://www.douyin.com/video/7123456789012345678"


class FakeResponse:
  def __init__(self, status_code=200, location=None, text=""):
    self.status_code = status_code
    self.headers = {}
    if location is not None:
      self.headers["Location"] = location
    self.text = text
    self.encoding = None


class RecordingTransport:
  def __init__(self, responses=None, error=None):
    self.responses = dict(responses or {})
    self.error = error
    self.calls = []

  def __call__(self, method="GET", url=None, **options):
    recorded = {"method": method, "url": url, **options}
    if options.get("headers") is not None:
      recorded["headers"] = dict(options["headers"])
    self.calls.append(recorded)
    if self.error is not None:
      raise self.error
    if url not in self.responses:
      raise AssertionError("unexpected request")
    return self.responses[url]

  @property
  def urls(self):
    return [call["url"] for call in self.calls]


class RecordingLogger:
  def __init__(self):
    self.messages = []

  def warning(self, message):
    self.messages.append(str(message))


def build_trust(responses=None, error=None, max_redirects=5):
  transport = RecordingTransport(responses=responses, error=error)
  return (
    DouyinRedirectTrust(
      request_function=transport,
      max_redirects=max_redirects,
    ),
    transport,
  )


class InitialTrustTest(unittest.TestCase):
  def test_untrusted_initial_urls_are_refused_without_a_request(self):
    candidates = (
      "https://example.test/share",
      "https://www.douyin.com.evil.test/video/1",
      "http://127.0.0.1:8080/",
      "http://[::1]/",
      "http://169.254.169.254/latest/meta-data/",
      "https://www.douyin.com@evil.test/video/1",
      "file:///etc/passwd",
      "ftp://v.douyin.com/file",
      "javascript:alert(1)",
      "https:///missing-host",
    )
    for candidate in candidates:
      with self.subTest(candidate=candidate):
        trust, transport = build_trust()
        with self.assertRaises(ResourceResolveError):
          trust.resolve_identity(candidate)
        self.assertEqual(transport.calls, [])

  def test_userinfo_is_refused_even_when_the_real_host_is_douyin(self):
    trust, transport = build_trust()

    with self.assertRaises(ResourceResolveError):
      trust.resolve_identity("https://attacker@www.douyin.com/video/1")

    self.assertEqual(transport.calls, [])


class IdentityRedirectTest(unittest.TestCase):
  def test_identity_stops_at_a_classifiable_target_without_fetching_it(self):
    trust, transport = build_trust({
      SHORT_URL: FakeResponse(302, POST_URL),
    })

    result = trust.resolve_identity(SHORT_URL)

    self.assertEqual(result, POST_URL)
    self.assertEqual(transport.urls, [SHORT_URL])

  def test_relative_and_multi_hop_redirects_are_walked_safely(self):
    middle = "https://v.douyin.com/phase17a/middle"
    trust, transport = build_trust({
      SHORT_URL: FakeResponse(302, "/phase17a/middle"),
      middle: FakeResponse(302, POST_URL),
    })

    self.assertEqual(trust.resolve_identity(SHORT_URL), POST_URL)
    self.assertEqual(transport.urls, [SHORT_URL, middle])
    self.assertTrue(
      all(call["allow_redirects"] is False for call in transport.calls)
    )

  def test_each_unsafe_second_hop_is_refused_before_it_is_requested(self):
    targets = (
      "http://127.0.0.1:3306/SECRET_REDIRECT_QUERY_17A",
      "http://169.254.169.254/latest/meta-data/",
      "https://outside.example/SECRET_LOCATION_17A",
      "https://www.douyin.com.evil.test/video/1",
      "https://www.douyin.com@evil.test/video/1",
      "file:///etc/passwd",
      "ftp://v.douyin.com/file",
      "https:///missing-host",
      "http://[::1",
    )
    for target in targets:
      with self.subTest(target=target):
        trust, transport = build_trust({
          SHORT_URL: FakeResponse(302, target),
        })
        with self.assertRaises(UntrustedRedirect):
          trust.resolve_identity(SHORT_URL)
        self.assertEqual(transport.urls, [SHORT_URL])

  def test_redirect_loop_is_bounded(self):
    middle = "https://v.douyin.com/phase17a/middle"
    trust, transport = build_trust({
      SHORT_URL: FakeResponse(302, middle),
      middle: FakeResponse(302, SHORT_URL),
    })

    with self.assertRaises(RedirectLoop):
      trust.resolve_identity(SHORT_URL)

    self.assertEqual(transport.urls, [SHORT_URL, middle])

  def test_hop_cap_never_requests_max_plus_one(self):
    responses = {}
    current = SHORT_URL
    for index in range(8):
      target = "https://v.douyin.com/phase17a/hop-{}".format(index)
      responses[current] = FakeResponse(302, target)
      current = target
    trust, transport = build_trust(responses, max_redirects=5)

    with self.assertRaises(TooManyRedirects):
      trust.resolve_identity(SHORT_URL)

    self.assertEqual(len(transport.calls), 5)


class DocumentRedirectTest(unittest.TestCase):
  def test_a_classifiable_initial_url_is_still_fetched(self):
    trust, transport = build_trust({
      POST_URL: FakeResponse(200, text="document body"),
    })

    document = trust.fetch_document(POST_URL)

    self.assertEqual(document.url, POST_URL)
    self.assertEqual(document.response.text, "document body")
    self.assertEqual(transport.urls, [POST_URL])

  def test_relative_multi_hop_document_returns_the_final_body(self):
    middle = "https://www.douyin.com/phase17a/middle"
    final = "https://www.iesdouyin.com/share/video/7123456789012345678"
    trust, transport = build_trust({
      POST_URL: FakeResponse(302, "/phase17a/middle"),
      middle: FakeResponse(302, final),
      final: FakeResponse(200, text="final body"),
    })

    document = trust.fetch_document(POST_URL)

    self.assertEqual(document.url, final)
    self.assertEqual(document.response.text, "final body")
    self.assertEqual(transport.urls, [POST_URL, middle, final])
    self.assertTrue(
      all(call["allow_redirects"] is False for call in transport.calls)
    )

  def test_document_redirect_off_platform_is_never_requested(self):
    middle = "https://www.douyin.com/phase17a/middle"
    unsafe = "http://127.0.0.1/SECRET_LOCATION_17A"
    trust, transport = build_trust({
      POST_URL: FakeResponse(302, middle),
      middle: FakeResponse(302, unsafe),
    })

    with self.assertRaises(UntrustedRedirect):
      trust.fetch_document(POST_URL)

    self.assertEqual(transport.urls, [POST_URL, middle])

  def test_document_hop_cap_never_requests_max_plus_one(self):
    responses = {}
    current = POST_URL
    for index in range(8):
      target = "https://www.douyin.com/phase17a/doc-{}".format(index)
      responses[current] = FakeResponse(302, target)
      current = target
    trust, transport = build_trust(responses, max_redirects=5)

    with self.assertRaises(TooManyRedirects):
      trust.fetch_document(POST_URL)

    self.assertEqual(len(transport.calls), 5)


class RedirectHeaderTest(unittest.TestCase):
  def test_cookie_is_initial_only_and_the_caller_headers_are_immutable(self):
    middle = "https://v.douyin.com/phase17a/middle"
    headers = {
      "Cookie": "session=SECRET_COOKIE_17A",
      "Authorization": "Bearer SECRET_AUTHORIZATION_17A",
      "User-Agent": "phase17a-test",
    }
    original = dict(headers)
    trust, transport = build_trust({
      SHORT_URL: FakeResponse(302, middle),
      middle: FakeResponse(200),
    })

    trust.resolve_identity(
      SHORT_URL,
      is_terminal=lambda unused: False,
      headers=headers,
    )

    self.assertEqual(transport.calls[0]["headers"], original)
    self.assertNotIn("Cookie", transport.calls[1]["headers"])
    self.assertEqual(
      transport.calls[1]["headers"]["Authorization"],
      original["Authorization"],
    )
    self.assertEqual(headers, original)

  def test_authorization_is_removed_when_the_redirect_origin_changes(self):
    cases = (
      "https://www.douyin.com/phase17a/cross-host",
      "http://v.douyin.com/phase17a/cross-scheme",
      "https://v.douyin.com:444/phase17a/cross-port",
    )
    for target in cases:
      with self.subTest(target=target):
        headers = {
          "authorization": "Bearer SECRET_AUTHORIZATION_17A",
          "X-Safe": "preserved",
        }
        trust, transport = build_trust({
          SHORT_URL: FakeResponse(302, target),
          target: FakeResponse(200),
        })

        trust.resolve_identity(
          SHORT_URL,
          is_terminal=lambda unused: False,
          headers=headers,
        )

        self.assertEqual(len(transport.calls), 2)
        self.assertNotIn("authorization", transport.calls[1]["headers"])
        self.assertEqual(transport.calls[1]["headers"]["X-Safe"], "preserved")
        self.assertIn("authorization", headers)

  def test_unsafe_target_has_no_second_hop_or_sensitive_header_record(self):
    headers = {
      "Cookie": "session=SECRET_COOKIE_17A",
      "Authorization": "Bearer SECRET_AUTHORIZATION_17A",
    }
    trust, transport = build_trust({
      SHORT_URL: FakeResponse(302, "http://169.254.169.254/latest/meta-data/"),
    })

    with self.assertRaises(UntrustedRedirect):
      trust.resolve_identity(SHORT_URL, headers=headers)

    self.assertEqual(len(transport.calls), 1)
    self.assertEqual(transport.calls[0]["url"], SHORT_URL)
    self.assertEqual(transport.calls[0]["headers"], headers)


class DiagnosticBoundaryTest(unittest.TestCase):
  def test_location_query_and_transport_exception_are_not_visible(self):
    logger = RecordingLogger()
    stdout = io.StringIO()
    stderr = io.StringIO()
    trust, _ = build_trust({
      SHORT_URL: FakeResponse(
        302,
        "https://outside.example/path?token=SECRET_LOCATION_17A",
      ),
    })
    with patch(
      "backend.src.platform.douyin.douyin_redirect_trust.get_logger",
      return_value=logger,
    ), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
      with self.assertRaises(UntrustedRedirect) as caught:
        trust.resolve_identity(SHORT_URL)

    visible = "\n".join(
      logger.messages + [stdout.getvalue(), stderr.getvalue(), str(caught.exception)]
    )
    self.assertNotIn("SECRET_LOCATION_17A", visible)
    self.assertNotIn("token=", visible)
    self.assertIn("outside.example", visible)

    logger = RecordingLogger()
    trust, _ = build_trust(error=OSError("SECRET_EXCEPTION_17A"))
    with patch(
      "backend.src.platform.douyin.douyin_redirect_trust.get_logger",
      return_value=logger,
    ):
      with self.assertRaises(ShortLinkUnavailable) as caught:
        trust.resolve_identity(
          SHORT_URL + "?token=SECRET_REDIRECT_QUERY_17A"
        )
    visible = "\n".join(logger.messages + [str(caught.exception)])
    self.assertNotIn("SECRET_EXCEPTION_17A", visible)
    self.assertNotIn("SECRET_REDIRECT_QUERY_17A", visible)
    self.assertIn("OSError", visible)


if __name__ == "__main__":
  unittest.main()
