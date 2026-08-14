import unittest
from concurrent.futures import ThreadPoolExecutor

from backend.src.platform.resource_resolution import (
  RESOURCE_TYPE_LIVE,
  RESOURCE_TYPE_OWNER,
  RESOURCE_TYPE_POST,
  InputMissing,
  MultipleUrls,
  NoUrlFound,
  ResourceResolution,
  ResourceResolveError,
  UnsupportedPlatform,
  UnsupportedResource,
  extract_urls,
)
from backend.src.platform.douyin.douyin_owner_url import extract_url
from backend.src.service.resource_resolve import (
  ResolveStore,
  ResourceResolveService,
)


##
## The ids from the real share links used during design verification.
##
SEC_UID = "MS4wLjABAAAAGZkW5n1EHZD_TFyQ-QiaISBPemtKFxVVdhLSeoXhh-U"
AWEME_ID = "7657271784144009946"


class ExtractUrlsTest(unittest.TestCase):
  """Pulling links out of whatever the user pasted.

  ``/api/resolve`` answers about exactly one resource, so unlike the existing
  ``extract_url`` this has to be able to say "there were three".
  """

  def test_a_bare_url_is_the_only_url(self):
    url = "https://v.douyin.com/M-kmspLye0o/"

    self.assertEqual(extract_urls(url), [url])

  def test_a_share_sentence_yields_its_one_link(self):
    text = ("4.33 复制打开抖音，看看【✨米开朗绿萝✨的作品】小鸟都粘我 "
            "https://v.douyin.com/MqjfOkWSeG8/ :0pm g@B.GI 12/06 sRK:/")

    self.assertEqual(extract_urls(text), ["https://v.douyin.com/MqjfOkWSeG8/"])

  def test_trailing_chinese_punctuation_is_trimmed(self):
    url = "https://www.douyin.com/user/" + SEC_UID

    self.assertEqual(extract_urls("看这个主播 " + url + "。"), [url])

  def test_every_trailing_noise_character_the_share_text_uses(self):
    url = "https://v.douyin.com/M-kmspLye0o/"
    for suffix in ("，", "）", "】", ")", ",", ".", "！", "?", "；", "》"):
      with self.subTest(suffix=suffix):
        self.assertEqual(extract_urls("分享 " + url + suffix), [url])

  def test_several_links_are_all_reported(self):
    """The count is the point: one link is a resolve, two is a bad request."""
    first = "https://v.douyin.com/AAAAAAA/"
    second = "https://v.douyin.com/BBBBBBB/"

    self.assertEqual(extract_urls("看看 " + first + " 还有 " + second),
                     [first, second])

  def test_the_same_link_pasted_twice_is_one_resource(self):
    """A doubled paste names one thing, so it must not read as ambiguous.

    The rule is distinct links, not link occurrences: the api's constraint is
    one *resource* per resolve, and how many times a clipboard repeated it is
    not something the user should have to tidy up first.
    """
    url = "https://v.douyin.com/AAAAAAA/"

    self.assertEqual(extract_urls(url + " " + url), [url])

  def test_the_same_link_repeated_across_lines_is_one_resource(self):
    url = "https://v.douyin.com/AAAAAAA/"

    self.assertEqual(extract_urls(url + "\n一些文字\n" + url), [url])

  def test_two_spellings_of_one_link_are_two_candidates(self):
    """``/abc/`` and ``/abc`` may be one resource - only the platform knows.

    Treating them as equal here would mean resolving a url nobody pasted, so
    they stay two and the request is refused as ambiguous.
    """
    url = "https://v.douyin.com/AAAAAAA/"

    self.assertEqual(len(extract_urls(url + " " + url.rstrip("/"))), 2)

  def test_prose_without_a_link_yields_nothing(self):
    for text in ("这段文字里没有链接", "douyin.com/user/abc", "", "   ", None, 42):
      with self.subTest(text=text):
        self.assertEqual(extract_urls(text), [])

  def test_a_non_http_scheme_is_not_a_url(self):
    """``ftp://`` and ``file://`` are not links this api can follow."""
    for text in ("ftp://example.test/x", "file:///etc/passwd",
                 "javascript:alert(1)"):
      with self.subTest(text=text):
        self.assertEqual(extract_urls(text), [])


class ExtractUrlsAgreesWithExtractUrlTest(unittest.TestCase):
  """The two must never disagree about where a url ends.

  ``extract_url`` keeps its contract - first url or empty string - and this
  pins that the new parser is the same rules, not a second opinion.
  """

  CASES = (
    "https://v.douyin.com/M-kmspLye0o/",
    "0- 长按复制此条消息，打开抖音搜索，查看TA的更多作品。 "
    "https://v.douyin.com/M-kmspLye0o/ 4@1.com :0pm",
    "看这个主播 https://www.douyin.com/user/" + SEC_UID + "。",
    "看看 https://v.douyin.com/AAAAAAA/ 还有 https://v.douyin.com/BBBBBBB/",
    "这段文字里没有链接",
    "",
  )

  def test_the_first_url_is_the_same_url(self):
    for text in self.CASES:
      with self.subTest(text=text):
        found = extract_urls(text)
        self.assertEqual(extract_url(text), found[0] if found else "")


class ResourceResolutionTest(unittest.TestCase):
  """What one answered resolve is, as a value."""

  def test_it_carries_the_platform_the_resource_type_and_both_urls(self):
    resolution = ResourceResolution(
      platform="douyin",
      resource_type=RESOURCE_TYPE_POST,
      source_url="https://v.douyin.com/abc/",
      resolved_url="https://www.douyin.com/video/" + AWEME_ID,
      identity={"aweme_id": AWEME_ID},
    )

    self.assertEqual(resolution.platform, "douyin")
    self.assertEqual(resolution.resource_type, "post")
    self.assertEqual(resolution.source_url, "https://v.douyin.com/abc/")
    self.assertEqual(
      resolution.resolved_url, "https://www.douyin.com/video/" + AWEME_ID
    )
    self.assertEqual(resolution.identity, {"aweme_id": AWEME_ID})

  def test_the_wire_resource_types_are_platform_neutral(self):
    """``post``, not ``douyin_post`` - the platform is its own field."""
    self.assertEqual(RESOURCE_TYPE_POST, "post")
    self.assertEqual(RESOURCE_TYPE_OWNER, "owner")
    self.assertEqual(RESOURCE_TYPE_LIVE, "live")

  def test_identity_defaults_to_empty(self):
    """A live room has no identity that can be read from its url alone."""
    resolution = ResourceResolution(
      platform="douyin",
      resource_type=RESOURCE_TYPE_LIVE,
      source_url="https://live.douyin.com/123456",
      resolved_url="https://live.douyin.com/123456",
    )

    self.assertEqual(resolution.identity, {})

  def test_the_identity_handed_in_is_copied(self):
    """A caller that keeps and edits its dict must not reach into the value."""
    identity = {"aweme_id": AWEME_ID}
    resolution = ResourceResolution(
      platform="douyin",
      resource_type=RESOURCE_TYPE_POST,
      source_url="https://www.douyin.com/video/" + AWEME_ID,
      resolved_url="https://www.douyin.com/video/" + AWEME_ID,
      identity=identity,
    )

    identity["aweme_id"] = "tampered"

    self.assertEqual(resolution.identity, {"aweme_id": AWEME_ID})

  def test_a_resolution_cannot_be_reassigned(self):
    resolution = ResourceResolution(
      platform="douyin",
      resource_type=RESOURCE_TYPE_POST,
      source_url="https://www.douyin.com/video/" + AWEME_ID,
      resolved_url="https://www.douyin.com/video/" + AWEME_ID,
    )

    with self.assertRaises(Exception):
      resolution.resource_type = RESOURCE_TYPE_OWNER

  def test_an_unknown_resource_type_is_refused(self):
    """The wire vocabulary is closed; a typo must not reach the browser."""
    with self.assertRaises(ValueError):
      ResourceResolution(
        platform="douyin",
        resource_type="douyin_post",
        source_url="https://www.douyin.com/video/" + AWEME_ID,
        resolved_url="https://www.douyin.com/video/" + AWEME_ID,
      )


class ResolveErrorTest(unittest.TestCase):
  """Every failure is one of a known set, each with the status it answers."""

  def test_a_missing_link_is_a_bad_request(self):
    error = NoUrlFound("没有找到链接")

    self.assertIsInstance(error, ResourceResolveError)
    self.assertEqual(error.status_code, 400)

  def test_several_links_are_a_bad_request(self):
    error = MultipleUrls("一次只能解析一个链接")

    self.assertIsInstance(error, ResourceResolveError)
    self.assertEqual(error.status_code, 400)

  def test_every_failure_names_its_kind_for_the_log(self):
    """Logs record the category, never the pasted text."""
    self.assertEqual(NoUrlFound("x").kind, "no_url")
    self.assertEqual(MultipleUrls("x").kind, "multiple_urls")


class FakeClock:
  def __init__(self):
    self.mono = 0.0

  def monotonic(self):
    return self.mono

  def advance(self, seconds):
    self.mono += seconds


def post_resolution(aweme_id=AWEME_ID, source_url=None):
  url = "https://www.douyin.com/video/" + aweme_id
  return ResourceResolution(
    platform="douyin",
    resource_type=RESOURCE_TYPE_POST,
    source_url=source_url or url,
    resolved_url=url,
    identity={"aweme_id": aweme_id},
  )


class ResolveStoreTest(unittest.TestCase):
  """What the server remembers between the resolve and whatever acts on it."""

  def test_a_stored_resolution_reads_back(self):
    store = ResolveStore()
    resolution = post_resolution()

    resolve_id = store.put(resolution)

    self.assertEqual(store.get(resolve_id), resolution)

  def test_an_unknown_id_is_simply_missing(self):
    """A browser may hold an id the store has since dropped; that is expected."""
    self.assertIsNone(ResolveStore().get("nope"))

  def test_reading_does_not_consume(self):
    """A retried click, or a second download of the same post, must both work.

    Whether repeating an action is allowed is a question for whatever creates
    the task; the store has no business deciding it by forgetting.
    """
    store = ResolveStore()
    resolve_id = store.put(post_resolution())

    first = store.get(resolve_id)
    second = store.get(resolve_id)

    self.assertEqual(first, second)
    self.assertIsNotNone(second)

  def test_each_put_gets_its_own_id(self):
    store = ResolveStore()

    first = store.put(post_resolution())
    second = store.put(post_resolution())

    self.assertNotEqual(first, second)

  def test_the_id_reveals_nothing_about_the_resource(self):
    """An id that could be derived would let a caller mint one it never resolved.

    The whole point of handing back an opaque id is that presenting it later is
    evidence *this server* resolved the resource - not evidence the caller can
    spell an aweme id.
    """
    store = ResolveStore()
    resolution = post_resolution()

    resolve_id = store.put(resolution)

    self.assertNotIn(AWEME_ID, resolve_id)
    self.assertNotIn(resolution.resolved_url, resolve_id)
    self.assertNotEqual(resolve_id, AWEME_ID)

  def test_a_resolution_expires(self):
    clock = FakeClock()
    store = ResolveStore(retention_seconds=600.0, clock=clock.monotonic)
    resolve_id = store.put(post_resolution())

    clock.advance(599)
    self.assertIsNotNone(store.get(resolve_id))

    clock.advance(2)
    self.assertIsNone(store.get(resolve_id))

  def test_expired_resolutions_do_not_accumulate(self):
    """A long-running server must not keep one entry per link ever pasted."""
    clock = FakeClock()
    store = ResolveStore(retention_seconds=600.0, clock=clock.monotonic)
    for _ in range(50):
      store.put(post_resolution())

    clock.advance(601)
    store.put(post_resolution())

    self.assertEqual(store.tracked(), 1)

  def test_what_comes_back_is_detached_from_the_store(self):
    """A caller editing the identity it was handed must not edit the record."""
    store = ResolveStore()
    resolve_id = store.put(post_resolution())

    store.get(resolve_id).identity["aweme_id"] = "tampered"

    self.assertEqual(store.get(resolve_id).identity, {"aweme_id": AWEME_ID})

  def test_two_readers_do_not_share_one_identity_dict(self):
    store = ResolveStore()
    resolve_id = store.put(post_resolution())

    first = store.get(resolve_id)
    second = store.get(resolve_id)
    first.identity["aweme_id"] = "tampered"

    self.assertEqual(second.identity, {"aweme_id": AWEME_ID})

  def test_editing_what_was_stored_does_not_edit_the_store(self):
    store = ResolveStore()
    resolution = post_resolution()
    resolve_id = store.put(resolution)

    resolution.identity["aweme_id"] = "tampered"

    self.assertEqual(store.get(resolve_id).identity, {"aweme_id": AWEME_ID})

  def test_concurrent_writers_get_distinct_ids_and_their_own_resolution(self):
    store = ResolveStore()
    aweme_ids = [str(7657271784144000000 + index) for index in range(60)]

    with ThreadPoolExecutor(max_workers=12) as pool:
      resolve_ids = list(
        pool.map(lambda one: store.put(post_resolution(one)), aweme_ids)
      )

    self.assertEqual(len(set(resolve_ids)), len(aweme_ids))
    for aweme_id, resolve_id in zip(aweme_ids, resolve_ids):
      with self.subTest(aweme_id=aweme_id):
        self.assertEqual(store.get(resolve_id).identity["aweme_id"], aweme_id)


class RecordingResolver:
  """A platform resolver that answers from a table and records what it was asked."""

  platform = "douyin"

  def __init__(self, answers=None, error=None, claimed=None):
    self.answers = dict(answers or {})
    self.error = error
    self.claimed = claimed
    self.resolved = []

  def claims(self, url):
    if self.claimed is not None:
      return self.claimed
    return "douyin.com" in (url or "")

  def resolve(self, url):
    self.resolved.append(url)
    if self.error is not None:
      raise self.error
    answer = self.answers.get(url)
    if answer is None:
      raise UnsupportedResource("无法识别该链接指向的资源")
    return answer


SHORT_LINK = "https://v.douyin.com/M-kmspLye0o/"


def build_service(resolver=None, store=None, retention_seconds=600.0):
  resolver = resolver if resolver is not None else RecordingResolver(
    {SHORT_LINK: post_resolution(source_url=SHORT_LINK)}
  )
  service = ResourceResolveService(
    resolvers=(resolver,), store=store, retention_seconds=retention_seconds
  )
  return service, resolver


class ResolveServiceInputTest(unittest.TestCase):
  """Turning whatever was pasted into exactly one resource, or one refusal."""

  def test_a_bare_link_resolves(self):
    service, resolver = build_service()

    record = service.resolve(SHORT_LINK)

    self.assertEqual(record.resolution.resource_type, RESOURCE_TYPE_POST)
    self.assertEqual(resolver.resolved, [SHORT_LINK])

  def test_a_share_sentence_resolves_the_link_inside_it(self):
    service, resolver = build_service()
    text = "4.33 复制打开抖音，看看【xxx的作品】小鸟都粘我 " + SHORT_LINK + " :0pm"

    record = service.resolve(text)

    self.assertEqual(record.resolution.resource_type, RESOURCE_TYPE_POST)
    self.assertEqual(
      resolver.resolved,
      [SHORT_LINK],
      "the platform resolver sees the link, never the pasted sentence",
    )

  def test_an_empty_input_is_refused(self):
    service, resolver = build_service()

    for value in ("", "   ", None):
      with self.subTest(value=value):
        with self.assertRaises(InputMissing):
          service.resolve(value)
    self.assertEqual(resolver.resolved, [])

  def test_prose_without_a_link_is_refused(self):
    service, resolver = build_service()

    with self.assertRaises(NoUrlFound):
      service.resolve("这段文字里没有链接")

    self.assertEqual(resolver.resolved, [])

  def test_two_links_are_refused_rather_than_silently_narrowed(self):
    """Taking the first would make the server's verdict disagree with the user."""
    service, resolver = build_service()

    with self.assertRaises(MultipleUrls):
      service.resolve(SHORT_LINK + " 还有 https://v.douyin.com/BBBBBBB/")

    self.assertEqual(resolver.resolved, [])

  def test_the_same_link_twice_is_one_resource(self):
    service, _ = build_service()

    record = service.resolve(SHORT_LINK + " " + SHORT_LINK)

    self.assertEqual(record.resolution.resource_type, RESOURCE_TYPE_POST)

  def test_a_non_http_scheme_is_a_bad_request(self):
    service, resolver = build_service()

    for value in ("file:///etc/passwd", "ftp://example.test/x"):
      with self.subTest(value=value):
        with self.assertRaises(ResourceResolveError) as caught:
          service.resolve(value)
        self.assertEqual(caught.exception.status_code, 400)
    self.assertEqual(resolver.resolved, [])

  def test_a_platform_nobody_claims_is_refused_without_being_fetched(self):
    service, resolver = build_service()

    with self.assertRaises(UnsupportedPlatform):
      service.resolve("https://www.bilibili.com/video/BV1")

    self.assertEqual(resolver.resolved, [])

  def test_a_platform_failure_is_passed_through_unchanged(self):
    """The service adds no opinion to why a link could not be named."""
    resolver = RecordingResolver(error=UnsupportedResource("无法识别"))
    service, _ = build_service(resolver)

    with self.assertRaises(UnsupportedResource):
      service.resolve(SHORT_LINK)


class ResolveServiceStorageTest(unittest.TestCase):
  """The resolution is kept server-side, and the caller gets only a receipt."""

  def test_resolving_hands_back_an_id_that_reads_the_resolution_back(self):
    service, _ = build_service()

    record = service.resolve(SHORT_LINK)

    self.assertEqual(service.get(record.resolve_id), record.resolution)

  def test_an_unknown_receipt_is_missing(self):
    service, _ = build_service()

    self.assertIsNone(service.get("nope"))

  def test_the_receipt_is_opaque(self):
    service, _ = build_service()

    record = service.resolve(SHORT_LINK)

    self.assertNotIn(AWEME_ID, record.resolve_id)
    self.assertNotIn("douyin", record.resolve_id)

  def test_only_the_urls_are_kept_never_the_pasted_text(self):
    """A share sentence carries nothing later stages need, and can carry a lot."""
    service, _ = build_service()
    secret = "私人备注 联系方式13800000000"
    text = "4.33 " + secret + " " + SHORT_LINK

    record = service.resolve(text)
    stored = service.get(record.resolve_id)

    self.assertEqual(stored.source_url, SHORT_LINK)
    self.assertNotIn(secret, stored.source_url)
    self.assertNotIn(secret, stored.resolved_url)
    self.assertNotIn(secret, repr(stored))

  def test_a_resolution_expires_with_the_service_retention(self):
    clock = FakeClock()
    store = ResolveStore(retention_seconds=5.0, clock=clock.monotonic)
    service, _ = build_service(store=store, retention_seconds=5.0)
    record = service.resolve(SHORT_LINK)

    clock.advance(6)

    self.assertIsNone(service.get(record.resolve_id))

  def test_the_service_states_how_long_a_receipt_lives(self):
    """The browser has to know when to stop offering the confirm button."""
    service, _ = build_service(retention_seconds=600.0)

    self.assertEqual(service.retention_seconds, 600.0)

  def test_concurrent_resolves_do_not_cross(self):
    answers = {}
    for index in range(40):
      aweme_id = str(7657271784144000000 + index)
      answers["https://www.douyin.com/video/" + aweme_id] = post_resolution(aweme_id)
    service, _ = build_service(RecordingResolver(answers))

    with ThreadPoolExecutor(max_workers=8) as pool:
      records = list(pool.map(service.resolve, answers.keys()))

    self.assertEqual(len({record.resolve_id for record in records}), len(answers))
    for url, record in zip(answers.keys(), records):
      with self.subTest(url=url):
        self.assertEqual(service.get(record.resolve_id).resolved_url, url)


if __name__ == "__main__":
  unittest.main()
