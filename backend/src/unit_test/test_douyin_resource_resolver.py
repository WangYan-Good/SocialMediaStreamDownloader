import unittest

from backend.src.platform.douyin.douyin_resource_resolver import (
  PLATFORM_DOUYIN,
  DouyinResourceResolver,
)
from backend.src.platform.resource_resolution import (
  RESOURCE_TYPE_LIVE,
  RESOURCE_TYPE_OWNER,
  RESOURCE_TYPE_POST,
  RedirectLoop,
  ShortLinkUnavailable,
  TooManyRedirects,
  UnsupportedPlatform,
  UnsupportedResource,
  UnsupportedScheme,
  UntrustedRedirect,
)


##
## The ids from the real share links used during design verification.
##
SEC_UID = "MS4wLjABAAAAGZkW5n1EHZD_TFyQ-QiaISBPemtKFxVVdhLSeoXhh-U"
AWEME_ID = "7657271784144009946"


class FakeResponse:
  """Just the two things a redirect hop is read from."""

  def __init__(self, status_code=302, location=None, headers=None):
    self.status_code = status_code
    self.headers = dict(headers or {})
    if location is not None:
      self.headers["Location"] = location


class RecordingHttp:
  """A stand-in for ``requests.request`` that never touches the network.

  Every call is recorded, so a test can assert not only what was answered but
  that nothing was fetched to answer it - which is the whole point for a url
  that is already a verdict, and the safety property for one that is not ours.
  """

  def __init__(self, responses=None, error=None):
    self.responses = dict(responses or {})
    self.error = error
    self.calls = []

  def __call__(self, method="GET", url=None, **options):
    self.calls.append({"method": method, "url": url, **options})
    if self.error is not None:
      raise self.error
    response = self.responses.get(url)
    if response is None:
      raise AssertionError("unexpected request to {!r}".format(url))
    return response

  @property
  def requested_urls(self):
    return [call["url"] for call in self.calls]


def build_resolver(http=None):
  http = http if http is not None else RecordingHttp()
  return DouyinResourceResolver(request_function=http), http


class ClaimsTest(unittest.TestCase):
  """Which hosts this resolver is willing to speak for at all."""

  def test_it_claims_the_douyin_content_hosts(self):
    resolver, _ = build_resolver()
    for url in ("https://www.douyin.com/video/1",
                "https://douyin.com/user/x",
                "https://www.iesdouyin.com/share/video/1"):
      with self.subTest(url=url):
        self.assertTrue(resolver.claims(url))

  def test_it_claims_the_live_and_short_link_hosts(self):
    resolver, _ = build_resolver()
    for url in ("https://live.douyin.com/123456",
                "https://webcast.amemv.com/webcast/reflow/123",
                "https://v.douyin.com/M-kmspLye0o/"):
      with self.subTest(url=url):
        self.assertTrue(resolver.claims(url))

  def test_it_claims_nothing_else(self):
    resolver, _ = build_resolver()
    for url in ("https://www.bilibili.com/video/BV1",
                "https://example.test/",
                "https://douyin.com.evil.test/video/1"):
      with self.subTest(url=url):
        self.assertFalse(resolver.claims(url))

  def test_the_platform_is_named_once(self):
    resolver, _ = build_resolver()

    self.assertEqual(PLATFORM_DOUYIN, "douyin")
    self.assertEqual(resolver.platform, "douyin")


class PostUrlTest(unittest.TestCase):
  """Every long post form, answered without asking the platform anything."""

  def assertPost(self, url, aweme_id=AWEME_ID):
    resolver, http = build_resolver()

    resolution = resolver.resolve(url)

    self.assertEqual(resolution.platform, PLATFORM_DOUYIN)
    self.assertEqual(resolution.resource_type, RESOURCE_TYPE_POST)
    self.assertEqual(resolution.identity, {"aweme_id": aweme_id})
    self.assertEqual(resolution.source_url, url)
    self.assertEqual(resolution.resolved_url, url)
    self.assertEqual(http.calls, [])
    return resolution

  def test_a_pc_video_page(self):
    self.assertPost("https://www.douyin.com/video/" + AWEME_ID)

  def test_a_pc_image_note_page(self):
    self.assertPost("https://www.douyin.com/note/" + AWEME_ID)

  def test_a_mobile_share_video_page(self):
    self.assertPost("https://www.iesdouyin.com/share/video/" + AWEME_ID)

  def test_a_mobile_share_note_page(self):
    self.assertPost("https://www.iesdouyin.com/share/note/" + AWEME_ID)

  def test_the_discover_feed_modal(self):
    self.assertPost("https://www.douyin.com/discover?modal_id=" + AWEME_ID)

  def test_the_search_modal(self):
    self.assertPost("https://www.douyin.com/search?modal_id=" + AWEME_ID)

  def test_the_root_search_modal(self):
    self.assertPost("https://www.douyin.com/root/search?modal_id=" + AWEME_ID)

  def test_a_query_string_is_kept_on_the_resolved_url(self):
    """The modal id lives in the query, so dropping it would drop the verdict."""
    url = "https://www.douyin.com/video/{}?region=CN&mid=7".format(AWEME_ID)

    resolution = self.assertPost(url)

    self.assertEqual(resolution.resolved_url, url)

  def test_surrounding_whitespace_is_trimmed(self):
    resolver, http = build_resolver()
    url = "https://www.douyin.com/video/" + AWEME_ID

    resolution = resolver.resolve("  " + url + "  ")

    self.assertEqual(resolution.source_url, url)
    self.assertEqual(resolution.resolved_url, url)
    self.assertEqual(http.calls, [])


class OwnerUrlTest(unittest.TestCase):
  """Every profile form, answered without reading the profile."""

  def assertOwner(self, url):
    resolver, http = build_resolver()

    resolution = resolver.resolve(url)

    self.assertEqual(resolution.platform, PLATFORM_DOUYIN)
    self.assertEqual(resolution.resource_type, RESOURCE_TYPE_OWNER)
    self.assertEqual(resolution.identity, {"sec_user_id": SEC_UID})
    self.assertEqual(resolution.resolved_url, url)
    self.assertEqual(http.calls, [])

  def test_a_pc_profile_page(self):
    self.assertOwner("https://www.douyin.com/user/" + SEC_UID)

  def test_a_mobile_share_profile_page(self):
    self.assertOwner("https://www.iesdouyin.com/share/user/" + SEC_UID)

  def test_the_sec_uid_query_form(self):
    self.assertOwner("https://www.iesdouyin.com/share/user/?sec_uid=" + SEC_UID)

  def test_the_sec_user_id_query_form(self):
    self.assertOwner(
      "https://www.douyin.com/share/?sec_user_id=" + SEC_UID
    )


class LiveUrlTest(unittest.TestCase):
  """A live room is named, and nothing is asked about whether it is on air."""

  def assertLive(self, url):
    resolver, http = build_resolver()

    resolution = resolver.resolve(url)

    self.assertEqual(resolution.platform, PLATFORM_DOUYIN)
    self.assertEqual(resolution.resource_type, RESOURCE_TYPE_LIVE)
    self.assertEqual(resolution.resolved_url, url)
    self.assertEqual(http.calls, [])
    return resolution

  def test_a_live_douyin_room(self):
    self.assertLive("https://live.douyin.com/123456")

  def test_a_webcast_reflow_room(self):
    self.assertLive("https://webcast.amemv.com/webcast/reflow/7123456789")

  def test_a_live_room_carries_no_guessed_identity(self):
    """The number in the path is a web id, not the room id the payload uses.

    Filling ``room_id`` from it would mint an identifier that looks server-
    verified and is not, and reading the real one costs a live probe - a
    request that answers a different question and whose answer expires.
    """
    resolution = self.assertLive("https://live.douyin.com/123456")

    self.assertEqual(resolution.identity, {})


class ExactlyOneVerdictTest(unittest.TestCase):
  """A url means one thing.  These are the confusions that would matter."""

  def test_a_live_room_is_not_read_as_a_post_or_an_owner(self):
    resolver, _ = build_resolver()

    resolution = resolver.resolve("https://live.douyin.com/" + AWEME_ID)

    self.assertEqual(resolution.resource_type, RESOURCE_TYPE_LIVE)

  def test_a_post_is_not_read_as_an_owner(self):
    """A post url carrying a sec_uid query still names the post."""
    resolver, _ = build_resolver()
    url = "https://www.douyin.com/video/{}?sec_uid={}".format(AWEME_ID, SEC_UID)

    resolution = resolver.resolve(url)

    self.assertEqual(resolution.resource_type, RESOURCE_TYPE_POST)
    self.assertEqual(resolution.identity, {"aweme_id": AWEME_ID})

  def test_an_owner_is_not_read_as_a_post(self):
    resolver, _ = build_resolver()

    resolution = resolver.resolve("https://www.douyin.com/user/" + SEC_UID)

    self.assertEqual(resolution.resource_type, RESOURCE_TYPE_OWNER)
    self.assertNotIn("aweme_id", resolution.identity)


class UnsupportedResourceTest(unittest.TestCase):
  """A host we know, pointing at something we cannot name."""

  def assertUnsupported(self, url):
    resolver, http = build_resolver()

    with self.assertRaises(UnsupportedResource):
      resolver.resolve(url)

    self.assertEqual(http.calls, [])

  def test_the_douyin_home_page(self):
    self.assertUnsupported("https://www.douyin.com/")

  def test_a_settings_page_is_not_an_owner(self):
    """``/user/settings`` has an owner-shaped path and no owner id in it."""
    self.assertUnsupported("https://www.douyin.com/user/settings")

  def test_a_non_numeric_video_path_is_not_a_post(self):
    self.assertUnsupported("https://www.douyin.com/video/not-an-id")

  def test_the_failure_names_its_kind(self):
    resolver, _ = build_resolver()

    with self.assertRaises(UnsupportedResource) as caught:
      resolver.resolve("https://www.douyin.com/")

    self.assertEqual(caught.exception.kind, "unsupported_resource")
    self.assertEqual(caught.exception.status_code, 400)


class HostSpoofingTest(unittest.TestCase):
  """A lookalike host is refused, and refused without being contacted.

  ``/api/resolve`` takes whatever a browser sends, so a url that merely reads
  like ours must never become a request this server makes on its behalf.
  """

  def assertRefusedUnvisited(self, url):
    resolver, http = build_resolver()

    with self.assertRaises(UnsupportedPlatform):
      resolver.resolve(url)

    self.assertEqual(http.calls, [], "no request may be made to {}".format(url))

  def test_a_domain_with_ours_as_a_prefix(self):
    self.assertRefusedUnvisited("https://douyin.com.example.test/video/123")

  def test_credentials_that_look_like_our_host(self):
    """``https://www.douyin.com@evil.test/`` really points at evil.test."""
    self.assertRefusedUnvisited("https://www.douyin.com@evil.test/video/123")

  def test_a_short_link_lookalike(self):
    self.assertRefusedUnvisited("https://v.douyin.com.evil.test/abc")

  def test_a_bare_lookalike_word(self):
    self.assertRefusedUnvisited("https://fake-douyin.com/video/123")

  def test_another_platform_is_simply_not_supported_yet(self):
    resolver, http = build_resolver()

    with self.assertRaises(UnsupportedPlatform) as caught:
      resolver.resolve("https://www.bilibili.com/video/BV1")

    self.assertEqual(caught.exception.kind, "unsupported_platform")
    self.assertEqual(http.calls, [])


class SsrfTest(unittest.TestCase):
  """``/api/resolve`` must not become a way to make this server fetch anything.

  These are the addresses that make an open fetcher dangerous: the loopback
  interface, and the cloud metadata endpoint that hands out credentials.
  """

  def assertNeverFetched(self, url):
    resolver, http = build_resolver()

    with self.assertRaises(UnsupportedPlatform):
      resolver.resolve(url)

    self.assertEqual(http.calls, [], "must not fetch {}".format(url))

  def test_loopback_by_address(self):
    self.assertNeverFetched("http://127.0.0.1/")

  def test_loopback_by_name(self):
    self.assertNeverFetched("http://localhost/")

  def test_a_database_port_on_loopback(self):
    self.assertNeverFetched("http://127.0.0.1:3306/")

  def test_the_cloud_metadata_endpoint(self):
    self.assertNeverFetched("http://169.254.169.254/latest/meta-data/")

  def test_a_private_network_address(self):
    self.assertNeverFetched("http://192.168.1.1/admin")


class SchemeTest(unittest.TestCase):
  """Only http and https are followable; nothing else is even a candidate."""

  def assertRefusedScheme(self, url):
    resolver, http = build_resolver()

    with self.assertRaises(UnsupportedScheme):
      resolver.resolve(url)

    self.assertEqual(http.calls, [])

  def test_a_file_url(self):
    self.assertRefusedScheme("file:///etc/passwd")

  def test_an_ftp_url(self):
    self.assertRefusedScheme("ftp://www.douyin.com/video/123")

  def test_a_javascript_url(self):
    self.assertRefusedScheme("javascript:alert(1)")

  def test_an_empty_url(self):
    for value in ("", "   ", None):
      with self.subTest(value=value):
        self.assertRefusedScheme(value)


SHORT_LINK = "https://v.douyin.com/M-kmspLye0o/"
POST_URL = "https://www.douyin.com/video/" + AWEME_ID


class ShortLinkTest(unittest.TestCase):
  """A short link carries no id, so it is the one form worth a request."""

  def test_it_is_followed_to_the_post_it_names(self):
    http = RecordingHttp({SHORT_LINK: FakeResponse(302, POST_URL)})
    resolver, _ = build_resolver(http)

    resolution = resolver.resolve(SHORT_LINK)

    self.assertEqual(resolution.resource_type, RESOURCE_TYPE_POST)
    self.assertEqual(resolution.identity, {"aweme_id": AWEME_ID})
    self.assertEqual(resolution.source_url, SHORT_LINK)
    self.assertEqual(resolution.resolved_url, POST_URL)

  def test_it_is_followed_to_the_owner_it_names(self):
    owner_url = "https://www.douyin.com/user/" + SEC_UID
    http = RecordingHttp({SHORT_LINK: FakeResponse(302, owner_url)})
    resolver, _ = build_resolver(http)

    resolution = resolver.resolve(SHORT_LINK)

    self.assertEqual(resolution.resource_type, RESOURCE_TYPE_OWNER)
    self.assertEqual(resolution.identity, {"sec_user_id": SEC_UID})
    self.assertEqual(resolution.resolved_url, owner_url)

  def test_it_is_followed_to_the_live_room_it_names(self):
    live_url = "https://live.douyin.com/123456"
    http = RecordingHttp({SHORT_LINK: FakeResponse(302, live_url)})
    resolver, _ = build_resolver(http)

    resolution = resolver.resolve(SHORT_LINK)

    self.assertEqual(resolution.resource_type, RESOURCE_TYPE_LIVE)
    self.assertEqual(resolution.identity, {})

  def test_following_stops_at_the_first_url_that_can_be_named(self):
    """One share link, one resolution - not one per interested reader.

    Before this resolver existed the owner path, the post resolver and the live
    prober each followed the same short link in turn.  The test states the fix:
    once a hop lands somewhere classifiable, nothing further is fetched.
    """
    http = RecordingHttp({SHORT_LINK: FakeResponse(302, POST_URL)})
    resolver, _ = build_resolver(http)

    resolver.resolve(SHORT_LINK)

    self.assertEqual(http.requested_urls, [SHORT_LINK])

  def test_redirects_are_never_delegated_to_the_http_library(self):
    """Each hop has to be inspected, so the library must not follow any of them."""
    http = RecordingHttp({SHORT_LINK: FakeResponse(302, POST_URL)})
    resolver, _ = build_resolver(http)

    resolver.resolve(SHORT_LINK)

    self.assertIs(http.calls[0]["allow_redirects"], False)

  def test_a_chain_of_douyin_hops_is_walked(self):
    middle = "https://www.douyin.com/redirect/2"
    http = RecordingHttp({
      SHORT_LINK: FakeResponse(302, middle),
      middle: FakeResponse(302, POST_URL),
    })
    resolver, _ = build_resolver(http)

    resolution = resolver.resolve(SHORT_LINK)

    self.assertEqual(resolution.resolved_url, POST_URL)
    self.assertEqual(http.requested_urls, [SHORT_LINK, middle])

  def test_a_relative_location_is_resolved_against_the_hop_it_came_from(self):
    """``Location: /x`` is legal and means the same host, not a bare path."""
    middle = "https://v.douyin.com/redirect/2"
    http = RecordingHttp({
      SHORT_LINK: FakeResponse(302, "/redirect/2"),
      middle: FakeResponse(302, POST_URL),
    })
    resolver, _ = build_resolver(http)

    resolution = resolver.resolve(SHORT_LINK)

    self.assertEqual(resolution.resolved_url, POST_URL)
    self.assertEqual(http.requested_urls, [SHORT_LINK, middle])

  def test_a_lowercase_location_header_is_read(self):
    """Header names are case-insensitive; a fake dict must not be the reason it works."""
    http = RecordingHttp({
      SHORT_LINK: FakeResponse(302, headers={"location": POST_URL})
    })
    resolver, _ = build_resolver(http)

    self.assertEqual(resolver.resolve(SHORT_LINK).resolved_url, POST_URL)

  def test_a_long_url_is_never_followed(self):
    """Already a verdict.  Following it could only rediscover what it says."""
    http = RecordingHttp()
    resolver, _ = build_resolver(http)

    for url in (POST_URL,
                "https://www.douyin.com/user/" + SEC_UID,
                "https://live.douyin.com/123456"):
      with self.subTest(url=url):
        resolver.resolve(url)

    self.assertEqual(http.calls, [])


class RedirectStatusTest(unittest.TestCase):
  """The status of a hop is not what decides whether the link resolved."""

  def test_a_444_carrying_a_valid_location_still_resolves(self):
    """Douyin answers a share link opened outside the app with 444.

    What matters is where the chain landed, not what the last hop said about
    it.  A ``status_code != 200`` gate here turned "pasted a link" into
    "nothing happened" for every post shared that way.
    """
    http = RecordingHttp({SHORT_LINK: FakeResponse(444, POST_URL)})
    resolver, _ = build_resolver(http)

    resolution = resolver.resolve(SHORT_LINK)

    self.assertEqual(resolution.resource_type, RESOURCE_TYPE_POST)
    self.assertEqual(resolution.resolved_url, POST_URL)

  def test_a_200_carrying_a_valid_location_still_resolves(self):
    http = RecordingHttp({SHORT_LINK: FakeResponse(200, POST_URL)})
    resolver, _ = build_resolver(http)

    self.assertEqual(resolver.resolve(SHORT_LINK).resolved_url, POST_URL)

  def test_a_short_link_that_leads_nowhere_cannot_be_named(self):
    """No Location at all: the chain ended on the short link itself."""
    http = RecordingHttp({SHORT_LINK: FakeResponse(200)})
    resolver, _ = build_resolver(http)

    with self.assertRaises(UnsupportedResource):
      resolver.resolve(SHORT_LINK)


class RedirectSafetyTest(unittest.TestCase):
  """Every hop is validated before it is taken, never after."""

  def test_a_redirect_off_the_platform_is_refused_before_it_is_taken(self):
    http = RecordingHttp({SHORT_LINK: FakeResponse(302, "https://evil.example/")})
    resolver, _ = build_resolver(http)

    with self.assertRaises(UntrustedRedirect):
      resolver.resolve(SHORT_LINK)

    self.assertEqual(
      http.requested_urls,
      [SHORT_LINK],
      "the untrusted target must never be contacted",
    )

  def test_a_redirect_to_a_lookalike_host_is_refused(self):
    http = RecordingHttp({
      SHORT_LINK: FakeResponse(302, "https://www.douyin.com.evil.test/video/1")
    })
    resolver, _ = build_resolver(http)

    with self.assertRaises(UntrustedRedirect):
      resolver.resolve(SHORT_LINK)

    self.assertEqual(http.requested_urls, [SHORT_LINK])

  def test_a_redirect_to_loopback_is_refused(self):
    """The classic pivot: a trusted host handing back an internal address."""
    http = RecordingHttp({
      SHORT_LINK: FakeResponse(302, "http://127.0.0.1:3306/")
    })
    resolver, _ = build_resolver(http)

    with self.assertRaises(UntrustedRedirect):
      resolver.resolve(SHORT_LINK)

    self.assertEqual(http.requested_urls, [SHORT_LINK])

  def test_a_redirect_to_a_non_http_scheme_is_refused(self):
    http = RecordingHttp({SHORT_LINK: FakeResponse(302, "file:///etc/passwd")})
    resolver, _ = build_resolver(http)

    with self.assertRaises(UntrustedRedirect):
      resolver.resolve(SHORT_LINK)

    self.assertEqual(http.requested_urls, [SHORT_LINK])

  def test_credentials_in_a_redirect_target_do_not_launder_the_host(self):
    http = RecordingHttp({
      SHORT_LINK: FakeResponse(302, "https://www.douyin.com@evil.test/video/1")
    })
    resolver, _ = build_resolver(http)

    with self.assertRaises(UntrustedRedirect):
      resolver.resolve(SHORT_LINK)

    self.assertEqual(http.requested_urls, [SHORT_LINK])

  def test_an_untrusted_redirect_is_a_bad_request_not_a_gateway_error(self):
    """Nothing upstream malfunctioned - the link just does not lead where ours do."""
    http = RecordingHttp({SHORT_LINK: FakeResponse(302, "https://evil.example/")})
    resolver, _ = build_resolver(http)

    with self.assertRaises(UntrustedRedirect) as caught:
      resolver.resolve(SHORT_LINK)

    self.assertEqual(caught.exception.status_code, 400)
    self.assertEqual(caught.exception.kind, "untrusted_redirect")


class RedirectTerminationTest(unittest.TestCase):
  """A chain has to end, whatever the other side does."""

  def test_a_loop_fails_instead_of_spinning(self):
    second = "https://www.douyin.com/redirect/2"
    http = RecordingHttp({
      SHORT_LINK: FakeResponse(302, second),
      second: FakeResponse(302, SHORT_LINK),
    })
    resolver, _ = build_resolver(http)

    with self.assertRaises(RedirectLoop):
      resolver.resolve(SHORT_LINK)

    self.assertEqual(http.requested_urls, [SHORT_LINK, second])

  def test_a_self_referential_hop_fails(self):
    http = RecordingHttp({SHORT_LINK: FakeResponse(302, SHORT_LINK)})
    resolver, _ = build_resolver(http)

    with self.assertRaises(RedirectLoop):
      resolver.resolve(SHORT_LINK)

  def test_a_chain_longer_than_the_hop_limit_fails(self):
    responses = {SHORT_LINK: FakeResponse(302, "https://v.douyin.com/hop/0")}
    for index in range(10):
      responses["https://v.douyin.com/hop/{}".format(index)] = FakeResponse(
        302, "https://v.douyin.com/hop/{}".format(index + 1)
      )
    resolver = DouyinResourceResolver(
      request_function=RecordingHttp(responses), max_redirects=5
    )

    with self.assertRaises(TooManyRedirects):
      resolver.resolve(SHORT_LINK)

  def test_the_hop_limit_bounds_how_many_requests_are_made(self):
    responses = {SHORT_LINK: FakeResponse(302, "https://v.douyin.com/hop/0")}
    for index in range(10):
      responses["https://v.douyin.com/hop/{}".format(index)] = FakeResponse(
        302, "https://v.douyin.com/hop/{}".format(index + 1)
      )
    http = RecordingHttp(responses)
    resolver = DouyinResourceResolver(request_function=http, max_redirects=5)

    with self.assertRaises(TooManyRedirects):
      resolver.resolve(SHORT_LINK)

    self.assertEqual(len(http.calls), 5)

  def test_running_out_of_hops_is_a_short_link_failure(self):
    """Callers that only care "the short link did not resolve" catch one type."""
    self.assertTrue(issubclass(TooManyRedirects, ShortLinkUnavailable))
    self.assertTrue(issubclass(RedirectLoop, ShortLinkUnavailable))
    self.assertEqual(TooManyRedirects("x").status_code, 502)
    self.assertEqual(RedirectLoop("x").status_code, 502)


class ShortLinkNetworkFailureTest(unittest.TestCase):
  """The network failing is upstream's problem, and says so."""

  def test_a_connection_error_becomes_a_gateway_failure(self):
    http = RecordingHttp(error=OSError("connection refused"))
    resolver, _ = build_resolver(http)

    with self.assertRaises(ShortLinkUnavailable) as caught:
      resolver.resolve(SHORT_LINK)

    self.assertEqual(caught.exception.status_code, 502)
    self.assertEqual(caught.exception.kind, "short_link_unavailable")

  def test_a_timeout_becomes_a_gateway_failure(self):
    http = RecordingHttp(error=TimeoutError("timed out"))
    resolver, _ = build_resolver(http)

    with self.assertRaises(ShortLinkUnavailable):
      resolver.resolve(SHORT_LINK)

  def test_the_failure_message_does_not_carry_the_underlying_exception(self):
    """Error text reaches the browser; a stack detail must not travel with it."""
    http = RecordingHttp(error=OSError("connect to 10.0.0.5:8080 refused"))
    resolver, _ = build_resolver(http)

    with self.assertRaises(ShortLinkUnavailable) as caught:
      resolver.resolve(SHORT_LINK)

    self.assertNotIn("10.0.0.5", str(caught.exception))


if __name__ == "__main__":
  unittest.main()
