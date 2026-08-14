import unittest

from backend.src.platform.douyin import douyin_handler as handler_module


AWEME_ID = "7123456789012345678"


class FakeResponse:
  def __init__(self, url, status_code=200):
    self.url = url
    self.status_code = status_code


class RoutingTestCase(unittest.TestCase):
  """The handler follows the share link once, then sorts the resolved url."""

  def setUp(self):
    self.live_batches = []
    self.aweme_batches = []
    self.warnings = []
    self.errors = []
    self.requested = []

    self._original_request = handler_module.request
    self._original_live = handler_module.download_multiple_live
    self._original_aweme = handler_module.download_multiple_aweme
    self._original_logger = handler_module.get_logger

    handler_module.download_multiple_live = self.live_batches.append
    handler_module.download_multiple_aweme = self.aweme_batches.append
    handler_module.get_logger = lambda: self

    self.addCleanup(self._restore)

  def _restore(self):
    handler_module.request = self._original_request
    handler_module.download_multiple_live = self._original_live
    handler_module.download_multiple_aweme = self._original_aweme
    handler_module.get_logger = self._original_logger

  ##
  ## logger stand-in
  ##
  def warning(self, message):
    self.warnings.append(message)

  def info(self, message):
    return None

  def error(self, message):
    self.errors.append(message)

  def resolve_to(self, resolved_url, status_code=200):
    def fake_request(method, url, *args, **kwargs):
      self.requested.append((method, url))
      return FakeResponse(resolved_url, status_code)

    handler_module.request = fake_request


class LiveRoutingTest(RoutingTestCase):
  def test_a_live_room_goes_to_the_live_path(self):
    self.resolve_to("https://live.douyin.com/123456")

    handler_module.douyin_handler({"url": "https://v.douyin.com/abc/"})

    self.assertEqual(len(self.live_batches), 1)
    self.assertEqual(self.aweme_batches, [])

  def test_the_share_link_is_followed_exactly_once(self):
    """Classification must not cost a second request."""
    self.resolve_to("https://live.douyin.com/123456")

    handler_module.douyin_handler({"url": "https://v.douyin.com/abc/"})

    self.assertEqual(len(self.requested), 1)


class RefusedFinalPageTest(RoutingTestCase):
  """The status of the final page does not decide whether the link is usable.

  Only ``response.url`` is read here; the body is never touched.  Douyin answers
  a share link opened outside the app with 444 after redirecting correctly, so
  a real image-post link resolved to ``/note/<id>`` and was then thrown away by
  a ``!= 200`` check:

    https://v.douyin.com/Gv2snnrMBCs/
      -> 302 -> 302 -> https://www.douyin.com/note/7672710351788455034  (444)
  """

  def test_a_post_is_downloaded_even_when_the_final_page_is_refused(self):
    self.resolve_to("https://www.douyin.com/note/" + AWEME_ID, status_code=444)

    handler_module.douyin_handler({"url": "https://v.douyin.com/abc/"})

    self.assertEqual(len(self.aweme_batches), 1)
    self.assertEqual(self.aweme_batches[0][0]["aweme_id"], AWEME_ID)

  def test_a_live_room_survives_a_refused_final_page_too(self):
    self.resolve_to("https://live.douyin.com/123456", status_code=444)

    handler_module.douyin_handler({"url": "https://v.douyin.com/abc/"})

    self.assertEqual(len(self.live_batches), 1)

  def test_an_unresolvable_link_is_reported_with_its_status(self):
    """When the url really is unusable, the status is the evidence to keep."""
    self.resolve_to("https://v.douyin.com/abc/", status_code=444)

    handler_module.douyin_handler({"url": "https://v.douyin.com/abc/"})

    self.assertEqual(self.aweme_batches, [])
    self.assertEqual(len(self.warnings), 1)
    self.assertIn("444", self.warnings[0])
    self.assertIn("https://v.douyin.com/abc/", self.warnings[0])


class AwemeRoutingTest(RoutingTestCase):
  def test_a_video_page_goes_to_the_post_path(self):
    self.resolve_to("https://www.douyin.com/video/" + AWEME_ID)

    handler_module.douyin_handler({"url": "https://v.douyin.com/abc/"})

    self.assertEqual(len(self.aweme_batches), 1)
    self.assertEqual(self.live_batches, [])

  def test_a_note_page_goes_to_the_post_path(self):
    self.resolve_to("https://www.douyin.com/note/" + AWEME_ID)

    handler_module.douyin_handler({"url": "https://v.douyin.com/abc/"})

    self.assertEqual(len(self.aweme_batches), 1)

  def test_the_users_score_and_favorite_survive_the_handoff(self):
    self.resolve_to("https://www.douyin.com/video/" + AWEME_ID)
    token = {"url": "https://v.douyin.com/abc/", "score": 80, "favorite": True}

    handler_module.douyin_handler(token)

    forwarded = self.aweme_batches[0][0]
    self.assertEqual(forwarded["url"], "https://v.douyin.com/abc/")
    self.assertEqual(forwarded["score"], 80)
    self.assertIs(forwarded["favorite"], True)

  def test_what_the_handler_resolved_is_passed_down(self):
    """The share link was already followed here.

    Handing the result down keeps the post path from spending a second request
    to rediscover it - a short link carries no id of its own.
    """
    self.resolve_to("https://www.douyin.com/video/" + AWEME_ID)

    handler_module.douyin_handler({"url": "https://v.douyin.com/abc/"})

    forwarded = self.aweme_batches[0][0]
    self.assertEqual(
      forwarded["resolved_url"],
      "https://www.douyin.com/video/" + AWEME_ID,
    )
    self.assertEqual(forwarded["aweme_id"], AWEME_ID)

  def test_the_callers_token_is_not_mutated(self):
    self.resolve_to("https://www.douyin.com/video/" + AWEME_ID)
    token = {"url": "https://v.douyin.com/abc/"}

    handler_module.douyin_handler(token)

    self.assertEqual(token, {"url": "https://v.douyin.com/abc/"})

  def test_only_one_request_is_spent_on_a_post(self):
    self.resolve_to("https://www.douyin.com/video/" + AWEME_ID)

    handler_module.douyin_handler({"url": "https://v.douyin.com/abc/"})

    self.assertEqual(len(self.requested), 1)


class UnhandledUrlTest(RoutingTestCase):
  def test_a_user_home_page_is_dropped_with_a_warning(self):
    """It used to be dropped silently, leaving nothing to diagnose."""
    self.resolve_to("https://www.douyin.com/user/MS4wLjABAAAAqGTe")

    handler_module.douyin_handler({"url": "https://v.douyin.com/abc/"})

    self.assertEqual(self.live_batches, [])
    self.assertEqual(self.aweme_batches, [])
    self.assertEqual(len(self.warnings), 1)
    self.assertIn("no douyin handler", self.warnings[0])

  def test_the_warning_names_both_the_original_and_resolved_url(self):
    self.resolve_to("https://www.douyin.com/user/MS4wLjABAAAAqGTe")

    handler_module.douyin_handler({"url": "https://v.douyin.com/short/"})

    self.assertIn("MS4wLjABAAAAqGTe", self.warnings[0])
    self.assertIn("https://v.douyin.com/short/", self.warnings[0])

  def test_a_failed_request_that_resolved_nowhere_stops(self):
    """A bad status only stops the link when the url is unusable as well.

    This used to assert that any non-200 stops, which is what dropped image
    posts: douyin answers their resolved page with 444 while the redirect chain
    identified the post correctly.  See ``RefusedFinalPageTest``.
    """
    self.resolve_to("https://www.douyin.com/user/MS4wLjABAAAAqGTe", 503)

    handler_module.douyin_handler({"url": "https://v.douyin.com/abc/"})

    self.assertEqual(self.live_batches, [])
    self.assertEqual(self.aweme_batches, [])
    self.assertIn("503", self.warnings[0])

  def test_a_token_without_a_url_is_dropped(self):
    self.resolve_to("https://www.douyin.com/video/" + AWEME_ID)

    handler_module.douyin_handler({"score": 1})

    self.assertEqual(self.requested, [])
    self.assertEqual(self.aweme_batches, [])

  def test_a_missing_token_is_a_programming_error(self):
    with self.assertRaises(ValueError):
      handler_module.douyin_handler(None)


class BatchIsolationTest(RoutingTestCase):
  def test_the_two_paths_never_receive_the_same_token(self):
    """A resolved url is one thing or the other, never both."""
    for resolved, expect_live in (
      ("https://live.douyin.com/9", True),
      ("https://www.douyin.com/video/" + AWEME_ID, False),
    ):
      with self.subTest(resolved=resolved):
        self.live_batches.clear()
        self.aweme_batches.clear()
        self.resolve_to(resolved)

        handler_module.douyin_handler({"url": "https://v.douyin.com/abc/"})

        self.assertEqual(len(self.live_batches), 1 if expect_live else 0)
        self.assertEqual(len(self.aweme_batches), 0 if expect_live else 1)


class FakeDirectPostService:
  """Stands in for the task-aware post runner handed down by a dispatch."""

  def __init__(self):
    self.submitted = []

  def submit(self, token):
    self.submitted.append(token)
    return None


class DispatchContextTest(RoutingTestCase):
  """A dispatch may carry dependencies; the handler routes work through them.

  The context is execution machinery, not user data.  It travels beside the
  token rather than inside it, so nothing that reaches a log, a database or an
  API can ever contain a service object.
  """

  def test_a_post_goes_to_the_runner_the_dispatch_supplied(self):
    self.resolve_to("https://www.douyin.com/video/" + AWEME_ID)
    runner = FakeDirectPostService()

    handler_module.douyin_handler(
      {"url": "https://v.douyin.com/abc/"},
      context={"direct_post_service": runner},
    )

    self.assertEqual(1, len(runner.submitted))
    ##
    ## The legacy batch call is bypassed rather than run as well: submitting to
    ## both would download the post twice.
    ##
    self.assertEqual([], self.aweme_batches)

  def test_the_runner_is_given_what_the_handler_resolved(self):
    self.resolve_to("https://www.douyin.com/video/" + AWEME_ID)
    runner = FakeDirectPostService()

    handler_module.douyin_handler(
      {"url": "https://v.douyin.com/abc/", "score": 80},
      context={"direct_post_service": runner},
    )

    forwarded = runner.submitted[0]
    self.assertEqual("https://v.douyin.com/abc/", forwarded["url"])
    self.assertEqual("https://www.douyin.com/video/" + AWEME_ID, forwarded["resolved_url"])
    self.assertEqual(AWEME_ID, forwarded["aweme_id"])
    self.assertEqual(80, forwarded["score"])

  def test_the_context_never_leaks_into_the_token(self):
    self.resolve_to("https://www.douyin.com/video/" + AWEME_ID)
    runner = FakeDirectPostService()

    handler_module.douyin_handler(
      {"url": "https://v.douyin.com/abc/"},
      context={"direct_post_service": runner},
    )

    forwarded = runner.submitted[0]
    self.assertNotIn("direct_post_service", forwarded)
    self.assertNotIn("context", forwarded)
    self.assertNotIn("task_service", forwarded)

  def test_a_live_room_is_untouched_by_the_context(self):
    self.resolve_to("https://live.douyin.com/123456")
    runner = FakeDirectPostService()

    handler_module.douyin_handler(
      {"url": "https://v.douyin.com/abc/"},
      context={"direct_post_service": runner},
    )

    ##
    ## Live recording is not this stage's to migrate: it goes where it always
    ## went, and no post task is invented for it.
    ##
    self.assertEqual(1, len(self.live_batches))
    self.assertEqual([], runner.submitted)

  def test_an_unrecognised_url_creates_no_post_work(self):
    self.resolve_to("https://www.douyin.com/user/MS4wLjABAAAA")
    runner = FakeDirectPostService()

    handler_module.douyin_handler(
      {"url": "https://v.douyin.com/abc/"},
      context={"direct_post_service": runner},
    )

    ##
    ## It was never confirmed to be a post, so it must not become a failed post
    ## task.  Saying so is the resolve stage's job, later.
    ##
    self.assertEqual([], runner.submitted)
    self.assertEqual([], self.aweme_batches)
    self.assertEqual(1, len(self.warnings))

  def test_each_post_is_submitted_on_its_own(self):
    self.resolve_to("https://www.douyin.com/video/" + AWEME_ID)
    runner = FakeDirectPostService()

    for unused in range(3):
      handler_module.douyin_handler(
        {"url": "https://v.douyin.com/abc/"},
        context={"direct_post_service": runner},
      )

    self.assertEqual(3, len(runner.submitted))

  def test_a_dispatch_without_a_runner_uses_the_legacy_path(self):
    self.resolve_to("https://www.douyin.com/video/" + AWEME_ID)

    handler_module.douyin_handler(
      {"url": "https://v.douyin.com/abc/"}, context={}
    )

    self.assertEqual(1, len(self.aweme_batches))

  def test_no_context_at_all_uses_the_legacy_path(self):
    self.resolve_to("https://www.douyin.com/video/" + AWEME_ID)

    handler_module.douyin_handler({"url": "https://v.douyin.com/abc/"})

    self.assertEqual(1, len(self.aweme_batches))

  def test_a_runner_that_throws_does_not_escape_the_handler(self):
    class ExplodingRunner:
      def submit(self, token):
        raise RuntimeError("scheduling exploded")

    self.resolve_to("https://www.douyin.com/video/" + AWEME_ID)

    handler_module.douyin_handler(
      {"url": "https://v.douyin.com/abc/"},
      context={"direct_post_service": ExplodingRunner()},
    )

    ##
    ## Handled the same way the legacy batch call already is: reported, not
    ## propagated into the dispatcher's worker thread.
    ##
    self.assertEqual(1, len(self.errors))


class FakeLiveRecordService:
  """Stands in for the task-aware recorder handed down by a dispatch."""

  def __init__(self):
    self.submitted = []

  def submit(self, token):
    self.submitted.append(token)
    return None


class LiveDispatchContextTest(RoutingTestCase):
  def test_a_live_room_goes_to_the_recorder_the_dispatch_supplied(self):
    self.resolve_to("https://live.douyin.com/123456")
    recorder = FakeLiveRecordService()

    handler_module.douyin_handler(
      {"url": "https://v.douyin.com/abc/"},
      context={"live_record_service": recorder},
    )

    self.assertEqual(1, len(recorder.submitted))
    ##
    ## The legacy batch call is bypassed rather than run as well: both would
    ## record the same room twice.
    ##
    self.assertEqual([], self.live_batches)

  def test_the_recorder_is_given_what_the_handler_resolved(self):
    self.resolve_to("https://live.douyin.com/123456")
    recorder = FakeLiveRecordService()

    handler_module.douyin_handler(
      {"url": "https://v.douyin.com/abc/", "score": 80},
      context={"live_record_service": recorder},
    )

    forwarded = recorder.submitted[0]
    self.assertEqual("https://v.douyin.com/abc/", forwarded["url"])
    self.assertEqual("https://live.douyin.com/123456", forwarded["resolved_url"])
    self.assertEqual(80, forwarded["score"])

  def test_the_callers_token_is_not_mutated_by_the_live_branch(self):
    self.resolve_to("https://live.douyin.com/123456")
    token = {"url": "https://v.douyin.com/abc/"}

    handler_module.douyin_handler(
      token, context={"live_record_service": FakeLiveRecordService()}
    )

    self.assertEqual({"url": "https://v.douyin.com/abc/"}, token)

  def test_the_context_never_leaks_into_the_live_token(self):
    self.resolve_to("https://live.douyin.com/123456")
    recorder = FakeLiveRecordService()

    handler_module.douyin_handler(
      {"url": "https://v.douyin.com/abc/"},
      context={"live_record_service": recorder},
    )

    forwarded = recorder.submitted[0]
    self.assertNotIn("live_record_service", forwarded)
    self.assertNotIn("direct_post_service", forwarded)

  def test_a_post_is_untouched_by_the_live_runner(self):
    self.resolve_to("https://www.douyin.com/video/" + AWEME_ID)
    recorder = FakeLiveRecordService()
    poster = FakeDirectPostService()

    handler_module.douyin_handler(
      {"url": "https://v.douyin.com/abc/"},
      context={"live_record_service": recorder, "direct_post_service": poster},
    )

    ##
    ## The two branches stay strictly separate: a post must never produce a
    ## recording task, and vice versa.
    ##
    self.assertEqual([], recorder.submitted)
    self.assertEqual(1, len(poster.submitted))

  def test_a_live_room_never_reaches_the_post_runner(self):
    self.resolve_to("https://live.douyin.com/123456")
    recorder = FakeLiveRecordService()
    poster = FakeDirectPostService()

    handler_module.douyin_handler(
      {"url": "https://v.douyin.com/abc/"},
      context={"live_record_service": recorder, "direct_post_service": poster},
    )

    self.assertEqual(1, len(recorder.submitted))
    self.assertEqual([], poster.submitted)

  def test_an_unrecognised_url_creates_no_recording(self):
    self.resolve_to("https://www.douyin.com/user/MS4wLjABAAAA")
    recorder = FakeLiveRecordService()

    handler_module.douyin_handler(
      {"url": "https://v.douyin.com/abc/"},
      context={"live_record_service": recorder},
    )

    self.assertEqual([], recorder.submitted)
    self.assertEqual([], self.live_batches)
    self.assertEqual(1, len(self.warnings))

  def test_a_dispatch_without_a_recorder_uses_the_legacy_path(self):
    self.resolve_to("https://live.douyin.com/123456")

    handler_module.douyin_handler({"url": "https://v.douyin.com/abc/"}, context={})

    self.assertEqual(1, len(self.live_batches))

  def test_no_context_at_all_uses_the_legacy_path(self):
    self.resolve_to("https://live.douyin.com/123456")

    handler_module.douyin_handler({"url": "https://v.douyin.com/abc/"})

    self.assertEqual(1, len(self.live_batches))

  def test_the_legacy_live_path_still_receives_the_resolved_url(self):
    self.resolve_to("https://live.douyin.com/123456")

    handler_module.douyin_handler({"url": "https://v.douyin.com/abc/"})

    forwarded = self.live_batches[0][0]
    self.assertEqual("https://v.douyin.com/abc/", forwarded["url"])
    self.assertEqual("https://live.douyin.com/123456", forwarded["resolved_url"])

  def test_a_recorder_that_throws_does_not_escape_the_handler(self):
    class ExplodingRecorder:
      def submit(self, token):
        raise RuntimeError("thread exploded")

    self.resolve_to("https://live.douyin.com/123456")

    handler_module.douyin_handler(
      {"url": "https://v.douyin.com/abc/"},
      context={"live_record_service": ExplodingRecorder()},
    )

    self.assertEqual(1, len(self.errors))


if __name__ == "__main__":
  unittest.main()
