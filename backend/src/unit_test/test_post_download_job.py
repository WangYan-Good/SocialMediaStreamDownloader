import tempfile
import unittest
from pathlib import Path

from backend.src.service import post_download_job as job_module
from backend.src.platform.douyin.douyin_aweme_downloader import (
  AwemeDownloadResult,
)
from backend.src.service.job_store import (
  JOB_DONE,
  JOB_ERROR,
  STATE_DONE,
  STATE_ERROR,
  STATE_SKIPPED,
  JobStore,
)
from backend.src.service.post_download_job import (
  MissingPayloads,
  PayloadCache,
  PostDownloadJobService,
)
from backend.src.platform.douyin.douyin_session import SessionExpired


SEC_UID = "MS4wLjABAAAAGZkW5n1EHZD_TFyQ-QiaISBPemtKFxVVdhLSeoXhh-U"
SWITCHES = {"video": True, "images": True, "music": True, "cover": True}


def post_item(aweme_id, with_media=True):
  payload = {
    "aweme_id": aweme_id,
    "desc": "作品 " + aweme_id,
    "create_time": 1712484087,
    "author": {"uid": "58859666123", "sec_uid": SEC_UID, "nickname": "主播"},
  }
  if with_media:
    payload["video"] = {
      "play_addr": {"url_list": ["https://v.example.test/" + aweme_id + ".mp4"]},
      "cover": {"url_list": ["https://p.example.test/" + aweme_id + ".jpg"]},
    }
    payload["music"] = {
      "play_url": {"url_list": ["https://m.example.test/s.mp3"]}
    }
  return payload


class FakeClock:
  def __init__(self, now=0.0):
    self.now = now

  def __call__(self):
    return self.now

  def advance(self, seconds):
    self.now += seconds


class StubDownloader:
  class Config:
    owner_max_pages = 0
    max_timeout = 10

    def __init__(self, switches):
      self.media_switches = switches

  def __init__(self, switches=None, failures=None, skips=(), owner_dir="/tmp/owner",
               ownership_failures=()):
    self.config = self.Config(switches or SWITCHES)
    self.calls = []
    self.owner_links = []
    self.failures = failures or {}
    self.skips = set(skips)
    self.owner_dir = owner_dir
    self.links = []
    self.ownership_failures = set(ownership_failures)

  def build_owner_dir(self, detail):
    return self.owner_dir

  def media_headers(self):
    return {}

  def media_proxies(self):
    return {"http": None, "https": None}

  def download_detail(self, detail, share_url, owner_share_url=None):
    self.calls.append((detail.aweme_id, share_url))
    self.owner_links.append(owner_share_url)
    if detail.aweme_id in self.failures:
      raise self.failures[detail.aweme_id]
    return AwemeDownloadResult(
      ok=True,
      aweme_id=detail.aweme_id,
      save_dir="/tmp/" + detail.aweme_id,
      media_count=detail.media_count,
      saved_count=detail.media_count,
      skipped=detail.aweme_id in self.skips,
      reason="already downloaded" if detail.aweme_id in self.skips else None,
    )

  def link_post(self, app_user_id, aweme_id):
    self.links.append((app_user_id, aweme_id))
    if aweme_id in self.ownership_failures:
      raise RuntimeError("foreign key failed")


OWNER_PAYLOAD = {
  "status_code": 0,
  "user": {
    "sec_uid": SEC_UID,
    "uid": "58859666123",
    "nickname": "主播",
    "unique_id": "zhubo",
    "signature": "签名",
    "avatar_larger": {"url_list": ["https://p.example.test/avatar.jpeg"]},
    "follower_count": 100,
    "following_count": 10,
    "aweme_count": 238,
    "total_favorited": 999,
  },
}


class StubApi:
  """Serves owner pages and the owner profile, told apart by endpoint.

  The two are separate calls in production, so a stub that answered both from one
  queue would let a profile request eat a page.
  """

  class Config:
    owner_page_size = 18

  def __init__(self, pages, error_after=None, owner_error=None):
    self.config = self.Config()
    self.pages = list(pages)
    self.error_after = error_after
    self.owner_error = owner_error
    self.calls = 0
    self.owner_calls = 0

  def get(self, api_attr, extra_params=None):
    if api_attr == "$.USER_DETAIL":
      self.owner_calls += 1
      if self.owner_error is not None:
        raise self.owner_error
      return OWNER_PAYLOAD
    self.calls += 1
    if self.error_after is not None and self.calls > self.error_after:
      raise SessionExpired("the platform returned an empty body")
    if not self.pages:
      return {"aweme_list": [], "has_more": 0, "max_cursor": 0}
    return self.pages.pop(0)


def page(ids, cursor, has_more):
  return {
    "aweme_list": [post_item(i) for i in ids],
    "max_cursor": cursor,
    "has_more": has_more,
  }


class OfflineTestCase(unittest.TestCase):
  """No test in this file may touch the network.

  _write_owner_card fetches an avatar, so the transport is replaced for every
  test rather than left to resolve example.test.
  """

  def setUp(self):
    self.fetched = []
    original = job_module.fetch_file

    def fake_fetch(url, save_path, file_name, **kwargs):
      self.fetched.append({"url": url, "save_path": str(save_path),
                           "file_name": file_name, "kwargs": kwargs})
      target = Path(save_path) / file_name
      target.parent.mkdir(parents=True, exist_ok=True)
      target.write_bytes(b"avatar")
      return target

    job_module.fetch_file = fake_fetch
    self.addCleanup(lambda: setattr(job_module, "fetch_file", original))


def build_service(
  downloader=None,
  api=None,
  cache=None,
  store=None,
  post_pool=None,
  post_concurrency=1,
):
  return PostDownloadJobService(
    downloader=downloader if downloader is not None else StubDownloader(),
    api=api,
    store=store if store is not None else JobStore(),
    cache=cache if cache is not None else PayloadCache(),
    media_switches=SWITCHES,
    post_pool=post_pool,
    post_concurrency=post_concurrency,
  )


class PayloadCacheTest(OfflineTestCase):
  """Payloads stay server-side; the browser only ever sends ids.

  A post object is kilobytes and a page carries nineteen, so round-tripping them
  through the client would move megabytes and let the client pick what downloads.
  """

  def test_payloads_are_recalled_by_id_in_the_requested_order(self):
    cache = PayloadCache()
    cache.remember([post_item("1"), post_item("2"), post_item("3")])

    payloads, missing = cache.take(["3", "1"])

    self.assertEqual([p["aweme_id"] for p in payloads], ["3", "1"])
    self.assertEqual(missing, [])

  def test_unknown_ids_are_reported_as_missing(self):
    cache = PayloadCache()
    cache.remember([post_item("1")])

    payloads, missing = cache.take(["1", "nope"])

    self.assertEqual(len(payloads), 1)
    self.assertEqual(missing, ["nope"])

  def test_payloads_without_an_id_are_not_kept(self):
    cache = PayloadCache()
    broken = post_item("1")
    broken.pop("aweme_id")

    self.assertEqual(cache.remember([broken]), 0)

  def test_entries_expire(self):
    clock = FakeClock()
    cache = PayloadCache(retention_seconds=100.0, clock=clock)
    cache.remember([post_item("1")])

    clock.advance(101)
    payloads, missing = cache.take(["1"])

    self.assertEqual(payloads, [])
    self.assertEqual(missing, ["1"])

  def test_reading_an_entry_keeps_it_alive(self):
    clock = FakeClock()
    cache = PayloadCache(retention_seconds=100.0, clock=clock)
    cache.remember([post_item("1")])

    clock.advance(90)
    cache.take(["1"])
    clock.advance(90)

    payloads, missing = cache.take(["1"])

    self.assertEqual(len(payloads), 1)
    self.assertEqual(missing, [])


class SelectedDownloadTest(OfflineTestCase):
  def test_every_selected_post_is_downloaded(self):
    downloader = StubDownloader()
    cache = PayloadCache()
    cache.remember([post_item("1"), post_item("2"), post_item("3")])
    service = build_service(downloader=downloader, cache=cache)

    job_id = service.start_selected(["1", "3"], share_url="https://share/")

    self.assertEqual(
      [call[0] for call in downloader.calls],
      ["1", "3"],
    )
    snapshot = service.store.snapshot(job_id)
    self.assertEqual(snapshot["state"], JOB_DONE)
    self.assertEqual(snapshot["total"], 2)
    self.assertEqual(snapshot["finished"], 2)

  def test_the_share_url_is_handed_to_the_downloader(self):
    downloader = StubDownloader()
    cache = PayloadCache()
    cache.remember([post_item("1")])
    service = build_service(downloader=downloader, cache=cache)

    service.start_selected(["1"], share_url="https://v.douyin.com/abc/")

    self.assertEqual(downloader.calls[0][1], "https://v.douyin.com/abc/")

  def test_the_share_url_is_declared_to_be_an_owners(self):
    """This path only ever holds a profile link, and only it can say so.

    A short link gives nothing away - an owner's and a post's look the same -
    so unless this caller declares it, the link cannot be recorded at all.
    """
    downloader = StubDownloader()
    cache = PayloadCache()
    cache.remember([post_item("1")])
    service = build_service(downloader=downloader, cache=cache)

    service.start_selected(["1"], share_url="https://v.douyin.com/abc/")

    self.assertEqual(downloader.owner_links[0], "https://v.douyin.com/abc/")

  def test_no_share_url_declares_nothing(self):
    downloader = StubDownloader()
    cache = PayloadCache()
    cache.remember([post_item("1")])
    service = build_service(downloader=downloader, cache=cache)

    service.start_selected(["1"])

    self.assertIsNone(downloader.owner_links[0])

  def test_saved_and_planned_counts_are_recorded(self):
    cache = PayloadCache()
    cache.remember([post_item("1")])
    service = build_service(cache=cache)

    job_id = service.start_selected(["1"])
    item = service.store.snapshot(job_id)["items"][0]

    self.assertEqual(item["state"], STATE_DONE)
    self.assertEqual(item["saved"], 3)
    self.assertEqual(item["planned"], 3)

  def test_an_already_downloaded_post_is_marked_skipped(self):
    downloader = StubDownloader(skips=["1"])
    cache = PayloadCache()
    cache.remember([post_item("1")])
    service = build_service(downloader=downloader, cache=cache)

    job_id = service.start_selected(["1"])

    self.assertEqual(
      service.store.snapshot(job_id)["items"][0]["state"],
      STATE_SKIPPED,
    )

  def test_one_failing_post_does_not_stop_the_others(self):
    downloader = StubDownloader(failures={"1": OSError("connection reset")})
    cache = PayloadCache()
    cache.remember([post_item("1"), post_item("2")])
    service = build_service(downloader=downloader, cache=cache)

    job_id = service.start_selected(["1", "2"])
    snapshot = service.store.snapshot(job_id)

    self.assertEqual(snapshot["state"], JOB_DONE)
    self.assertEqual(snapshot["items"][0]["state"], STATE_ERROR)
    self.assertEqual(snapshot["items"][1]["state"], STATE_DONE)

  def test_a_post_with_nothing_downloadable_is_skipped(self):
    cache = PayloadCache()
    cache.remember([post_item("1", with_media=False)])
    service = build_service(cache=cache)

    job_id = service.start_selected(["1"])
    item = service.store.snapshot(job_id)["items"][0]

    self.assertEqual(item["state"], STATE_SKIPPED)
    self.assertIn("no downloadable media", item["message"])

  def test_expired_payloads_are_refused_rather_than_guessed_at(self):
    cache = PayloadCache()
    service = build_service(cache=cache)

    with self.assertRaises(MissingPayloads) as caught:
      service.start_selected(["1", "2"])

    self.assertEqual(caught.exception.missing, ["1", "2"])

  def test_an_empty_selection_is_a_client_error(self):
    service = build_service()

    for value in ([], ["", "  "], None or []):
      with self.subTest(value=value):
        with self.assertRaises(ValueError):
          service.start_selected(value)


class DownloadEverythingTest(OfflineTestCase):
  def test_every_page_is_walked_and_downloaded(self):
    downloader = StubDownloader()
    api = StubApi(pages=[
      page(["1", "2"], 100, 1),
      page(["3"], 200, 0),
    ])
    service = build_service(downloader=downloader, api=api)

    job_id = service.start_all(SEC_UID, share_url="https://share/")

    self.assertEqual([call[0] for call in downloader.calls], ["1", "2", "3"])
    snapshot = service.store.snapshot(job_id)
    self.assertEqual(snapshot["state"], JOB_DONE)
    self.assertEqual(snapshot["total"], 3)

  def test_walked_posts_are_cached_so_a_retry_can_reference_them(self):
    api = StubApi(pages=[page(["1", "2"], 100, 0)])
    service = build_service(api=api)

    service.start_all(SEC_UID)

    payloads, missing = service.cache.take(["1", "2"])
    self.assertEqual(len(payloads), 2)
    self.assertEqual(missing, [])

  def test_a_mid_walk_session_failure_keeps_what_was_downloaded(self):
    """An expired cookie part way through must not discard the finished work."""
    downloader = StubDownloader()
    api = StubApi(pages=[page(["1", "2"], 100, 1)], error_after=1)
    service = build_service(downloader=downloader, api=api)

    job_id = service.start_all(SEC_UID)
    snapshot = service.store.snapshot(job_id)

    self.assertEqual([call[0] for call in downloader.calls], ["1", "2"])
    self.assertEqual(snapshot["state"], JOB_ERROR)
    self.assertEqual(snapshot["total"], 2)
    self.assertIn("停在第 3 个作品", snapshot["message"])

  def test_a_blank_owner_is_a_client_error(self):
    service = build_service(api=StubApi(pages=[]))

    for value in (None, "", "   "):
      with self.subTest(value=value):
        with self.assertRaises(ValueError):
          service.start_all(value)

  def test_walking_without_an_api_is_a_programming_error(self):
    service = build_service(api=None)

    with self.assertRaises(ValueError):
      service.start_all(SEC_UID)

  def test_an_owner_with_no_posts_finishes_cleanly(self):
    api = StubApi(pages=[page([], 0, 0)])
    service = build_service(api=api)

    job_id = service.start_all(SEC_UID)
    snapshot = service.store.snapshot(job_id)

    self.assertEqual(snapshot["state"], JOB_DONE)
    self.assertEqual(snapshot["total"], 0)


class OwnerCardTest(OfflineTestCase):
  """The owner's card sits one level above their posts.

  A folder named 20260701081200_7657271784144009946 tells a person nothing, and
  neither does a folder of such folders, so the owner is described in text beside
  them.
  """

  def test_the_card_and_avatar_land_in_the_owner_folder(self):
    with tempfile.TemporaryDirectory() as directory:
      downloader = StubDownloader(owner_dir=directory)
      api = StubApi(pages=[page(["1"], 0, 0)])
      service = build_service(downloader=downloader, api=api)

      service.start_all(SEC_UID)

      note = Path(directory) / "owner.txt"
      self.assertTrue(note.is_file())
      body = note.read_text(encoding="utf-8")
      self.assertIn("主播", body)
      self.assertIn("@zhubo", body)
      self.assertIn("238", body)
      self.assertEqual([f["file_name"] for f in self.fetched], ["avatar.jpg"])

  def test_the_card_is_written_once_per_job_not_once_per_post(self):
    """One platform request per job; the posts themselves cost none."""
    with tempfile.TemporaryDirectory() as directory:
      api = StubApi(pages=[page(["1", "2", "3"], 0, 0)])
      service = build_service(
        downloader=StubDownloader(owner_dir=directory), api=api
      )

      service.start_all(SEC_UID)

      self.assertEqual(api.owner_calls, 1)

  def test_the_avatar_is_refreshed_rather_than_skipped(self):
    with tempfile.TemporaryDirectory() as directory:
      api = StubApi(pages=[page(["1"], 0, 0)])
      service = build_service(
        downloader=StubDownloader(owner_dir=directory), api=api
      )

      service.start_all(SEC_UID)

      self.assertEqual(self.fetched[0]["kwargs"]["on_exists"], "overwrite")

  def test_selected_downloads_write_the_card_too(self):
    with tempfile.TemporaryDirectory() as directory:
      cache = PayloadCache()
      cache.remember([post_item("1")])
      api = StubApi(pages=[])
      service = build_service(
        downloader=StubDownloader(owner_dir=directory), api=api, cache=cache
      )

      service.start_selected(["1"])

      self.assertTrue((Path(directory) / "owner.txt").is_file())

  def test_an_unreadable_profile_does_not_stop_the_download(self):
    """The card is a convenience beside the media, never the product."""
    with tempfile.TemporaryDirectory() as directory:
      downloader = StubDownloader(owner_dir=directory)
      api = StubApi(pages=[page(["1"], 0, 0)],
                    owner_error=SessionExpired("empty body"))
      service = build_service(downloader=downloader, api=api)

      job_id = service.start_all(SEC_UID)

      self.assertEqual(service.store.snapshot(job_id)["state"], JOB_DONE)
      self.assertEqual([c[0] for c in downloader.calls], ["1"])
      self.assertFalse((Path(directory) / "owner.txt").is_file())

  def test_no_api_means_no_card_and_no_crash(self):
    cache = PayloadCache()
    cache.remember([post_item("1")])
    service = build_service(api=None, cache=cache)

    job_id = service.start_selected(["1"])

    self.assertEqual(service.store.snapshot(job_id)["state"], JOB_DONE)
    self.assertEqual(self.fetched, [])


if __name__ == "__main__":
  unittest.main()


class ParallelDownloadTest(OfflineTestCase):
  """Posts may run in parallel, bounded by the configured count.

  The bound is global rather than per job: 429 from the image CDN is a
  cumulative quota, so a peak that multiplies with the number of jobs would
  burn it faster and fail every job at once.
  """

  def build_counting_downloader(self):
    from threading import Lock

    class CountingDownloader(StubDownloader):
      def __init__(self):
        super().__init__()
        self._guard = Lock()
        self.running = 0
        self.peak = 0

      def download_detail(self, detail, share_url, owner_share_url=None):
        with self._guard:
          self.running += 1
          self.peak = max(self.peak, self.running)
        try:
          return super().download_detail(detail, share_url, owner_share_url)
        finally:
          with self._guard:
            self.running -= 1

    return CountingDownloader()

  def test_the_default_stays_serial(self):
    downloader = self.build_counting_downloader()
    cache = PayloadCache()
    cache.remember([post_item(str(index)) for index in range(6)])
    service = build_service(downloader=downloader, cache=cache)

    service.start_selected([str(index) for index in range(6)])

    self.assertEqual(downloader.peak, 1)
    self.assertEqual(len(downloader.calls), 6)

  def test_posts_run_in_parallel_up_to_the_configured_count(self):
    from concurrent.futures import ThreadPoolExecutor

    downloader = self.build_counting_downloader()
    cache = PayloadCache()
    cache.remember([post_item(str(index)) for index in range(12)])
    pool = ThreadPoolExecutor(max_workers=4)
    try:
      service = build_service(
        downloader=downloader,
        cache=cache,
        post_pool=pool,
        post_concurrency=3,
      )

      service.start_selected([str(index) for index in range(12)])
    finally:
      pool.shutdown(wait=True)

    self.assertLessEqual(downloader.peak, 3)
    self.assertEqual(len(downloader.calls), 12)

  def test_every_selected_post_is_downloaded_exactly_once(self):
    from concurrent.futures import ThreadPoolExecutor

    downloader = self.build_counting_downloader()
    cache = PayloadCache()
    cache.remember([post_item(str(index)) for index in range(10)])
    pool = ThreadPoolExecutor(max_workers=4)
    try:
      service = build_service(
        downloader=downloader,
        cache=cache,
        post_pool=pool,
        post_concurrency=4,
      )

      service.start_selected([str(index) for index in range(10)])
    finally:
      pool.shutdown(wait=True)

    downloaded = sorted(int(call[0]) for call in downloader.calls)
    self.assertEqual(downloaded, list(range(10)))

  def test_the_job_is_only_done_once_every_post_finished(self):
    from concurrent.futures import ThreadPoolExecutor

    downloader = self.build_counting_downloader()
    cache = PayloadCache()
    cache.remember([post_item(str(index)) for index in range(8)])
    store = JobStore()
    pool = ThreadPoolExecutor(max_workers=4)
    try:
      service = build_service(
        downloader=downloader,
        cache=cache,
        store=store,
        post_pool=pool,
        post_concurrency=3,
      )

      job_id = service.start_selected([str(index) for index in range(8)])
    finally:
      pool.shutdown(wait=True)

    snapshot = store.snapshot(job_id)
    self.assertEqual(snapshot["state"], JOB_DONE)
    self.assertEqual(downloader.running, 0)
    self.assertEqual(len(downloader.calls), 8)

  def test_one_failing_post_does_not_stop_the_others(self):
    from concurrent.futures import ThreadPoolExecutor

    downloader = self.build_counting_downloader()
    downloader.failures = {"3": RuntimeError("boom")}
    cache = PayloadCache()
    cache.remember([post_item(str(index)) for index in range(6)])
    pool = ThreadPoolExecutor(max_workers=4)
    try:
      service = build_service(
        downloader=downloader,
        cache=cache,
        post_pool=pool,
        post_concurrency=3,
      )

      service.start_selected([str(index) for index in range(6)])
    finally:
      pool.shutdown(wait=True)

    self.assertEqual(len(downloader.calls), 6)
