import unittest

from flask import Flask

from backend.src.platform.douyin.douyin_owner_detail import OwnerDetail
from backend.src.platform.douyin.douyin_session import (
  SessionExpired,
  UpstreamRejected,
)
from backend.src.service.job_store import JobStore
from backend.src.service.post_download_job import MissingPayloads, PayloadCache
from backend.src.web.owner_routes import (
  SESSION_MESSAGE,
  OwnerRuntime,
  build_owner_blueprint,
)


SEC_UID = "MS4wLjABAAAAGZkW5n1EHZD_TFyQ-QiaISBPemtKFxVVdhLSeoXhh-U"
OWNER_URL = "https://www.douyin.com/user/" + SEC_UID


def post_item(aweme_id, images=None):
  payload = {
    "aweme_id": aweme_id,
    "desc": "作品 " + aweme_id,
    "create_time": 1712484087,
    "author": {"uid": "58859666123", "sec_uid": SEC_UID, "nickname": "主播"},
    "statistics": {"digg_count": 12, "comment_count": 3},
  }
  if images:
    payload["images"] = [
      {"url_list": ["https://p.example.test/{}-{}.webp".format(aweme_id, i)]}
      for i in range(images)
    ]
  else:
    payload["video"] = {
      "duration": 15000,
      "play_addr": {"url_list": ["https://v.example.test/" + aweme_id + ".mp4"]},
      "cover": {"url_list": ["https://p.example.test/" + aweme_id + ".jpg"]},
    }
  return payload


OWNER_DETAIL = OwnerDetail(
  sec_user_id=SEC_UID,
  uid="58859666123",
  nickname="✨米开朗绿萝✨",
  unique_id="mollymollyding",
  signature="不出闲置",
  avatar_url="https://p.example.test/avatar.jpeg",
  follower_count=858776,
  following_count=120,
  aweme_count=238,
  total_favorited=5451610,
)


class StubService:
  def __init__(self, cache=None, store=None):
    self.cache = cache if cache is not None else PayloadCache()
    self.store = store if store is not None else JobStore()
    self.selected = []
    self.all_calls = []
    self.selected_error = None
    self.downloader = None

  def start_selected(self, aweme_ids, share_url=""):
    if self.selected_error is not None:
      raise self.selected_error
    self.selected.append((list(aweme_ids), share_url))
    return self.store.create(aweme_ids)

  def start_all(self, sec_user_id, share_url=""):
    self.all_calls.append((sec_user_id, share_url))
    return self.store.create([])


class StubRuntime(OwnerRuntime):
  """Replaces every outbound call so the routes are tested on their own."""

  def __init__(self, pages=None, detail=OWNER_DETAIL, resolve_to=SEC_UID,
               page_error=None, detail_error=None, records=None,
               resolve_error=None, service=None):
    self._pages = list(pages or [])
    self._detail = detail
    self._resolve_to = resolve_to
    self._page_error = page_error
    self._detail_error = detail_error
    self._records = records or {}
    self._resolve_error = resolve_error
    self._service = service if service is not None else StubService()
    self.days_left = 59

  def settings(self):
    return {}

  def api(self):
    return self

  def credential_days_left(self):
    return self.days_left

  def proxies(self):
    return {"http": None, "https": None}

  def service(self):
    return self._service

  def resolve_owner(self, url):
    if self._resolve_error is not None:
      raise self._resolve_error
    return self._resolve_to

  def records_for(self, aweme_ids):
    return self._records


def build_client(runtime):
  app = Flask(__name__)
  app.register_blueprint(build_owner_blueprint(runtime))
  app.config["TESTING"] = True
  return app.test_client()


def patch_fetchers(test, runtime):
  """Point the module's fetchers at the stub runtime's prepared answers."""
  from backend.src.web import owner_routes

  def fake_detail(api, sec_user_id):
    if runtime._detail_error is not None:
      raise runtime._detail_error
    return runtime._detail

  def fake_page(api, sec_user_id, cursor=0, count=None):
    if runtime._page_error is not None:
      raise runtime._page_error
    from backend.src.platform.douyin.douyin_owner_posts import OwnerPostPage
    payloads = runtime._pages.pop(0) if runtime._pages else []
    return OwnerPostPage(
      payloads=tuple(payloads),
      next_cursor=1765077600000,
      has_more=bool(runtime._pages),
    )

  original_detail = owner_routes.fetch_owner_detail
  original_page = owner_routes.fetch_post_page
  owner_routes.fetch_owner_detail = fake_detail
  owner_routes.fetch_post_page = fake_page

  def restore():
    owner_routes.fetch_owner_detail = original_detail
    owner_routes.fetch_post_page = original_page

  test.addCleanup(restore)


class ReadOwnerTest(unittest.TestCase):
  def test_the_profile_and_the_first_page_come_back_together(self):
    runtime = StubRuntime(pages=[[post_item("1"), post_item("2")]])
    patch_fetchers(self, runtime)

    response = build_client(runtime).get("/api/owner?url=" + OWNER_URL)
    body = response.get_json()

    self.assertEqual(response.status_code, 200)
    self.assertEqual(body["data"]["sec_user_id"], SEC_UID)
    self.assertEqual(body["data"]["owner"]["nickname"], "✨米开朗绿萝✨")
    self.assertEqual(body["data"]["owner"]["aweme_count"], 238)
    self.assertEqual(len(body["data"]["posts"]), 2)

  def test_the_credential_expiry_is_reported(self):
    """Surfaced so an expiry is noticed before it becomes an empty list."""
    runtime = StubRuntime(pages=[[post_item("1")]])
    patch_fetchers(self, runtime)

    body = build_client(runtime).get("/api/owner?url=" + OWNER_URL).get_json()

    self.assertEqual(body["data"]["credential"]["expires_in_days"], 59)

  def test_a_missing_url_is_a_client_error(self):
    runtime = StubRuntime()
    patch_fetchers(self, runtime)

    response = build_client(runtime).get("/api/owner")

    self.assertEqual(response.status_code, 400)
    self.assertIn("url", response.get_json()["message"])

  def test_a_link_that_is_not_a_profile_is_a_client_error(self):
    runtime = StubRuntime(resolve_to=None)
    patch_fetchers(self, runtime)

    response = build_client(runtime).get("/api/owner?url=https://example.test/x")

    self.assertEqual(response.status_code, 400)
    self.assertIn("主播主页", response.get_json()["message"])

  def test_a_dead_session_says_so_instead_of_showing_nothing(self):
    """The failure mode this whole feature had to be protected from."""
    runtime = StubRuntime(
      pages=[[post_item("1")]],
      detail_error=SessionExpired("the platform returned an empty body"),
    )
    patch_fetchers(self, runtime)

    response = build_client(runtime).get("/api/owner?url=" + OWNER_URL)

    self.assertEqual(response.status_code, 502)
    self.assertEqual(response.get_json()["message"], SESSION_MESSAGE)

  def test_a_dead_session_on_the_post_page_also_says_so(self):
    runtime = StubRuntime(
      page_error=SessionExpired("the platform returned an empty body"),
    )
    patch_fetchers(self, runtime)

    response = build_client(runtime).get("/api/owner?url=" + OWNER_URL)

    self.assertEqual(response.status_code, 502)
    self.assertEqual(response.get_json()["message"], SESSION_MESSAGE)

  def test_an_unreadable_profile_does_not_hide_the_post_list(self):
    """The two requests are independent on purpose."""
    from backend.src.platform.douyin.douyin_owner_detail import OwnerUnavailable

    runtime = StubRuntime(
      pages=[[post_item("1")]],
      detail_error=OwnerUnavailable("owner payload carries no user"),
    )
    patch_fetchers(self, runtime)

    body = build_client(runtime).get("/api/owner?url=" + OWNER_URL).get_json()

    self.assertIsNone(body["data"]["owner"])
    self.assertIn("详情不可用", body["data"]["owner_message"])
    self.assertEqual(len(body["data"]["posts"]), 1)

  def test_an_upstream_refusal_is_reported_separately_from_a_session_failure(self):
    runtime = StubRuntime(
      page_error=UpstreamRejected("the platform returned a non-JSON body"),
    )
    patch_fetchers(self, runtime)

    response = build_client(runtime).get("/api/owner?url=" + OWNER_URL)
    body = response.get_json()

    self.assertEqual(response.status_code, 502)
    self.assertNotEqual(body["message"], SESSION_MESSAGE)
    self.assertIn("拒绝", body["message"])

  def test_a_link_resolution_failure_is_reported(self):
    runtime = StubRuntime(resolve_error=OSError("connection reset"))
    patch_fetchers(self, runtime)

    response = build_client(runtime).get("/api/owner?url=" + OWNER_URL)

    self.assertEqual(response.status_code, 502)


class SerializedPostTest(unittest.TestCase):
  def test_only_display_fields_are_sent_not_the_whole_payload(self):
    runtime = StubRuntime(pages=[[post_item("1")]])
    patch_fetchers(self, runtime)

    body = build_client(runtime).get("/api/owner?url=" + OWNER_URL).get_json()
    post = body["data"]["posts"][0]

    self.assertEqual(
      sorted(post.keys()),
      sorted([
        "aweme_id", "desc", "create_time", "cover_url", "duration",
        "aweme_type", "digg_count", "comment_count", "downloaded",
        "saved_count", "media_count",
      ]),
    )
    self.assertNotIn("video", post)
    self.assertNotIn("author", post)

  def test_a_video_post_reports_its_cover_and_type(self):
    runtime = StubRuntime(pages=[[post_item("1")]])
    patch_fetchers(self, runtime)

    post = build_client(runtime).get(
      "/api/owner?url=" + OWNER_URL
    ).get_json()["data"]["posts"][0]

    self.assertEqual(post["aweme_type"], "video")
    self.assertEqual(post["cover_url"], "https://p.example.test/1.jpg")
    self.assertEqual(post["duration"], 15000)

  def test_an_image_post_uses_its_first_image_as_the_cover(self):
    runtime = StubRuntime(pages=[[post_item("1", images=3)]])
    patch_fetchers(self, runtime)

    post = build_client(runtime).get(
      "/api/owner?url=" + OWNER_URL
    ).get_json()["data"]["posts"][0]

    self.assertEqual(post["aweme_type"], "image")
    self.assertEqual(post["cover_url"], "https://p.example.test/1-0.webp")

  def test_an_already_downloaded_post_is_marked(self):
    runtime = StubRuntime(
      pages=[[post_item("1"), post_item("2")]],
      records={"1": {"saved_count": 3, "media_count": 3}},
    )
    patch_fetchers(self, runtime)

    posts = build_client(runtime).get(
      "/api/owner?url=" + OWNER_URL
    ).get_json()["data"]["posts"]

    self.assertTrue(posts[0]["downloaded"])
    self.assertEqual(posts[0]["saved_count"], 3)
    self.assertFalse(posts[1]["downloaded"])
    self.assertIsNone(posts[1]["saved_count"])


class ReadOwnerPostsTest(unittest.TestCase):
  def test_a_later_page_is_served(self):
    runtime = StubRuntime(pages=[[post_item("3")]])
    patch_fetchers(self, runtime)

    response = build_client(runtime).get(
      "/api/owner/posts?sec_user_id={}&cursor=100".format(SEC_UID)
    )
    body = response.get_json()

    self.assertEqual(response.status_code, 200)
    self.assertEqual(body["data"]["posts"][0]["aweme_id"], "3")
    self.assertIn("next_cursor", body["data"])

  def test_a_missing_owner_is_a_client_error(self):
    runtime = StubRuntime()
    patch_fetchers(self, runtime)

    response = build_client(runtime).get("/api/owner/posts")

    self.assertEqual(response.status_code, 400)

  def test_a_non_integer_cursor_is_a_client_error(self):
    runtime = StubRuntime()
    patch_fetchers(self, runtime)

    response = build_client(runtime).get(
      "/api/owner/posts?sec_user_id={}&cursor=abc".format(SEC_UID)
    )

    self.assertEqual(response.status_code, 400)
    self.assertIn("cursor", response.get_json()["message"])

  def test_a_dead_session_says_so(self):
    runtime = StubRuntime(page_error=SessionExpired("empty body"))
    patch_fetchers(self, runtime)

    response = build_client(runtime).get(
      "/api/owner/posts?sec_user_id=" + SEC_UID
    )

    self.assertEqual(response.status_code, 502)
    self.assertEqual(response.get_json()["message"], SESSION_MESSAGE)


class StartDownloadTest(unittest.TestCase):
  def test_selected_posts_are_submitted(self):
    service = StubService()
    runtime = StubRuntime(service=service)
    patch_fetchers(self, runtime)

    response = build_client(runtime).post(
      "/api/owner/download",
      json={"aweme_ids": ["1", "2"], "share_url": "https://share/"},
    )

    self.assertEqual(response.status_code, 200)
    self.assertIn("job_id", response.get_json()["data"])
    self.assertEqual(service.selected, [(["1", "2"], "https://share/")])

  def test_download_everything_is_submitted(self):
    service = StubService()
    runtime = StubRuntime(service=service)
    patch_fetchers(self, runtime)

    response = build_client(runtime).post(
      "/api/owner/download",
      json={"all": True, "sec_user_id": SEC_UID},
    )

    self.assertEqual(response.status_code, 200)
    self.assertEqual(service.all_calls, [(SEC_UID, "")])

  def test_download_everything_needs_an_owner(self):
    runtime = StubRuntime()
    patch_fetchers(self, runtime)

    response = build_client(runtime).post(
      "/api/owner/download", json={"all": True}
    )

    self.assertEqual(response.status_code, 400)

  def test_an_empty_selection_is_a_client_error(self):
    runtime = StubRuntime()
    patch_fetchers(self, runtime)

    for payload in ({}, {"aweme_ids": []}, {"aweme_ids": "1"}):
      with self.subTest(payload=payload):
        response = build_client(runtime).post(
          "/api/owner/download", json=payload
        )
        self.assertEqual(response.status_code, 400)

  def test_expired_payloads_ask_for_a_reload_rather_than_guessing(self):
    service = StubService()
    service.selected_error = MissingPayloads(["1", "2"])
    runtime = StubRuntime(service=service)
    patch_fetchers(self, runtime)

    response = build_client(runtime).post(
      "/api/owner/download", json={"aweme_ids": ["1", "2"]}
    )

    self.assertEqual(response.status_code, 404)
    self.assertIn("重新读取", response.get_json()["message"])

  def test_a_non_json_body_is_a_client_error(self):
    runtime = StubRuntime()
    patch_fetchers(self, runtime)

    response = build_client(runtime).post(
      "/api/owner/download", data="not json",
      content_type="text/plain",
    )

    self.assertEqual(response.status_code, 400)


class ReadDownloadProgressTest(unittest.TestCase):
  def test_progress_is_served(self):
    service = StubService()
    job_id = service.store.create(["1", "2"])
    runtime = StubRuntime(service=service)
    patch_fetchers(self, runtime)

    response = build_client(runtime).get("/api/owner/download/" + job_id)
    body = response.get_json()

    self.assertEqual(response.status_code, 200)
    self.assertEqual(body["data"]["total"], 2)
    self.assertEqual(body["data"]["finished"], 0)

  def test_an_unknown_job_is_a_not_found(self):
    runtime = StubRuntime()
    patch_fetchers(self, runtime)

    response = build_client(runtime).get("/api/owner/download/nope")

    self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
  unittest.main()
