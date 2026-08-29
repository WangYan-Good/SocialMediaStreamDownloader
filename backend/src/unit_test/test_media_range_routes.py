##<<Base>>
import json
import os
import tempfile
import time
import unittest
from pathlib import Path

##<<Extension>>
from flask import Flask

##<<Third-part>>
from backend.src.auth.context import RequestAuthContext
from backend.src.auth.roles import ROLE_ADMIN, ROLE_USER
from backend.src.auth.service import AuthenticatedUser
from backend.src.service.media_asset import MediaAssetResolver, asset_id_for
from backend.src.unit_test.auth_context import install_test_auth
from backend.src.web.library_routes import LibraryUnavailable, build_library_blueprint


AWEME = "7657271784144009946"
##
## Ten bytes whose every position is distinguishable, so an off-by-one in a
## window is visible in the assertion rather than hidden by repetition.
##
BODY = b"0123456789"
BEYOND_SAFE = 9007199254740993


class CountingResolver:
  """A real resolver that records whether the filesystem was reached."""

  def __init__(self, root_provider):
    self._inner = MediaAssetResolver(root_provider)
    self.calls = []

  def post_assets(self, save_dir, platform, aweme_id):
    self.calls.append("post_assets")
    return self._inner.post_assets(save_dir, platform, aweme_id)

  def recording_asset(self, output_path, recording_id):
    self.calls.append("recording_asset")
    return self._inner.recording_asset(output_path, recording_id)

  def open_post_asset(self, save_dir, platform, aweme_id, asset_id):
    self.calls.append("open_post")
    return self._inner.open_post_asset(save_dir, platform, aweme_id, asset_id)

  def open_recording_asset(self, output_path, recording_id, asset_id):
    self.calls.append("open_recording")
    return self._inner.open_recording_asset(output_path, recording_id, asset_id)


class FakeQuery:
  def __init__(self, post=None, recording=None, failure=None):
    self._post = post
    self._recording = recording
    self._failure = failure
    self.calls = []

  def _maybe_fail(self):
    if self._failure is not None:
      raise self._failure

  def post(self, platform, aweme_id):
    self.calls.append("post")
    self._maybe_fail()
    return self._post

  def post_for_user(self, app_user_id, platform, aweme_id):
    self.calls.append("post_for_user")
    self._maybe_fail()
    return self._post

  def recording(self, recording_id):
    self.calls.append("recording")
    self._maybe_fail()
    return self._recording

  def recording_for_user(self, app_user_id, recording_id):
    self.calls.append("recording_for_user")
    self._maybe_fail()
    return self._recording


class FakeRuntime:
  def __init__(self, query=None, resolver=None, unavailable=None):
    self._query = query
    self._resolver = resolver
    self._unavailable = unavailable

  def page_size_limit(self):
    return 100

  def query(self):
    if self._unavailable is not None:
      raise self._unavailable
    return self._query

  def asset_resolver(self):
    return self._resolver


def install_anonymous(app):
  from flask import g

  @app.before_request
  def anonymous_request():
    g.auth_context = RequestAuthContext.anonymous()


class RangeTestCase(unittest.TestCase):
  def setUp(self):
    self._tmp = tempfile.TemporaryDirectory()
    self.base = Path(self._tmp.name)
    self.root = self.base / "downloads"
    self.creator = self.root / "creator"
    self.creator.mkdir(parents=True)
    self.addCleanup(self._tmp.cleanup)

    self.name = "20260824_{}.mp4".format(AWEME)
    self.target = self.creator / self.name
    self.target.write_bytes(BODY)

    self.post_row = {
      "platform": "douyin",
      "aweme_id": AWEME,
      "save_dir": str(self.creator),
    }
    self.recording_name = "live.flv"
    self.recording_path = self.creator / self.recording_name
    self.recording_path.write_bytes(b"RECORDING-BYTES")
    self.recording_row = {
      "recording_id": BEYOND_SAFE,
      "app_user_id": 3,
      "output_path": str(self.recording_path),
    }

    ##
    ## Aged past the validator-strength window, because that is what a file
    ## somebody downloads normally is: written some time ago and settled. A
    ## file written microseconds before the request is a different situation -
    ## no strong validator can be claimed for it - and has its own tests in
    ## ``ValidatorStrengthTest``.
    ##
    self.settle()

  def settle(self, *paths):
    """Age files past the window in which no strong validator is published."""
    old = time.time() - 3600
    for one in paths or (self.target, self.recording_path):
      os.utime(str(one), (old, old))

  def build(self, query=None, principal=None, unavailable=None):
    resolver = CountingResolver(lambda: str(self.root))
    runtime = FakeRuntime(query=query, resolver=resolver, unavailable=unavailable)
    app = Flask(__name__)
    if principal is None:
      install_anonymous(app)
    else:
      install_test_auth(app, user=principal)
    app.register_blueprint(build_library_blueprint(runtime=runtime))
    return app.test_client(), resolver

  def user(self, user_id=3, role=ROLE_USER):
    return AuthenticatedUser(user_id, "u{}".format(user_id), role)

  def url(self, asset_id=None, aweme_id=AWEME):
    return "/api/library/posts/douyin/{}/assets/{}/download".format(
      aweme_id, asset_id or asset_id_for("post", ("douyin", aweme_id), self.name)
    )

  def owner_client(self):
    return self.build(FakeQuery(post=self.post_row), principal=self.user())[0]

  def get(self, headers=None, client=None):
    return (client or self.owner_client()).get(self.url(), headers=headers or {})


##
## >>=========================== the full representation ===========================<<
##
class FullResponseTest(RangeTestCase):
  def test_a_plain_get_still_returns_the_whole_file(self):
    response = self.get()

    self.assertEqual(200, response.status_code)
    self.assertEqual(BODY, response.get_data())
    self.assertEqual("10", response.headers["Content-Length"])

  def test_it_now_advertises_that_ranges_are_understood(self):
    ##
    ## Without this a browser has no reason to attempt a resume at all - it is
    ## the server saying the offer is real.
    ##
    self.assertEqual("bytes", self.get().headers["Accept-Ranges"])

  def test_it_carries_a_validator_a_later_resume_can_quote(self):
    response = self.get()

    tag = response.headers.get("ETag")
    self.assertIsNotNone(tag)
    ##
    ## Quoted by the framework's own header handling rather than by hand.
    ##
    self.assertTrue(tag.startswith('"') and tag.endswith('"'), tag)

  def test_the_existing_download_contract_is_untouched(self):
    response = self.get()

    self.assertTrue(
      response.headers["Content-Disposition"].startswith("attachment")
    )
    self.assertEqual("video/mp4", response.headers["Content-Type"])
    self.assertIn("no-store", response.headers["Cache-Control"])
    self.assertIn("private", response.headers["Cache-Control"])
    self.assertEqual("nosniff", response.headers["X-Content-Type-Options"])

  def test_adding_a_validator_did_not_make_the_media_cacheable(self):
    ##
    ## An entity tag is a resume validator here, not an invitation for a shared
    ## proxy to keep a copy of somebody's private video.
    ##
    cache = self.get().headers["Cache-Control"]

    self.assertIn("no-store", cache)
    self.assertNotIn("public", cache)
    self.assertNotIn("max-age", cache)


##
## >>============================== one byte range ==============================<<
##
class SingleRangeTest(RangeTestCase):
  def test_a_closed_range_returns_exactly_those_bytes(self):
    response = self.get({"Range": "bytes=2-5"})

    self.assertEqual(206, response.status_code)
    self.assertEqual(b"2345", response.get_data())
    self.assertEqual("4", response.headers["Content-Length"])
    self.assertEqual("bytes 2-5/10", response.headers["Content-Range"])

  def test_an_open_ended_range_runs_to_the_end(self):
    ##
    ## The shape a resuming download actually sends: "I have the first six
    ## bytes, continue from there."
    ##
    response = self.get({"Range": "bytes=6-"})

    self.assertEqual(206, response.status_code)
    self.assertEqual(b"6789", response.get_data())
    self.assertEqual("bytes 6-9/10", response.headers["Content-Range"])

  def test_a_suffix_range_counts_back_from_the_end(self):
    response = self.get({"Range": "bytes=-3"})

    self.assertEqual(206, response.status_code)
    self.assertEqual(b"789", response.get_data())
    self.assertEqual("bytes 7-9/10", response.headers["Content-Range"])

  def test_a_single_byte_is_a_legitimate_range(self):
    response = self.get({"Range": "bytes=0-0"})

    self.assertEqual(206, response.status_code)
    self.assertEqual(b"0", response.get_data())
    self.assertEqual("bytes 0-0/10", response.headers["Content-Range"])

  def test_the_final_byte_is_reachable(self):
    response = self.get({"Range": "bytes=9-9"})

    self.assertEqual(206, response.status_code)
    self.assertEqual(b"9", response.get_data())
    self.assertEqual("bytes 9-9/10", response.headers["Content-Range"])

  def test_a_range_covering_everything_is_still_a_partial_response(self):
    ##
    ## The client asked with a Range header, so it gets 206 and a Content-Range
    ## even though the window happens to be the whole file.
    ##
    response = self.get({"Range": "bytes=0-9"})

    self.assertEqual(206, response.status_code)
    self.assertEqual(BODY, response.get_data())
    self.assertEqual("bytes 0-9/10", response.headers["Content-Range"])

  def test_a_partial_response_keeps_every_delivery_header(self):
    response = self.get({"Range": "bytes=2-5"})

    self.assertTrue(
      response.headers["Content-Disposition"].startswith("attachment")
    )
    self.assertEqual("video/mp4", response.headers["Content-Type"])
    self.assertEqual("bytes", response.headers["Accept-Ranges"])
    self.assertEqual("nosniff", response.headers["X-Content-Type-Options"])
    self.assertIn("no-store", response.headers["Cache-Control"])
    self.assertIsNotNone(response.headers.get("ETag"))

  def test_the_partial_response_carries_the_same_validator_as_the_full_one(self):
    ##
    ## A resume compares the two. If they disagreed for an unchanged file, no
    ## client could ever continue a download.
    ##
    self.assertEqual(
      self.get().headers["ETag"],
      self.get({"Range": "bytes=2-5"}).headers["ETag"],
    )


##
## >>=========================== ranges that cannot be met ===========================<<
##
class UnsatisfiableRangeTest(RangeTestCase):
  def test_a_range_past_the_end_is_refused_with_the_real_length(self):
    response = self.get({"Range": "bytes=20-30"})

    self.assertEqual(416, response.status_code)
    ##
    ## The one useful thing a 416 can say: how long the file actually is, so
    ## the next attempt can be correct.
    ##
    self.assertEqual("bytes */10", response.headers["Content-Range"])
    self.assertEqual("bytes", response.headers["Accept-Ranges"])

  def test_a_refusal_still_carries_the_current_validator(self):
    ##
    ## No existence is leaked by this: the request has already authenticated,
    ## authorized its parent resource and opened the file.
    ##
    self.assertIsNotNone(self.get({"Range": "bytes=20-30"}).headers.get("ETag"))

  def test_a_refusal_says_nothing_about_the_filesystem(self):
    response = self.get({"Range": "bytes=20-30"})

    body = response.get_data(as_text=True)
    self.assertIn("application/json", response.headers["Content-Type"])
    for secret in (str(self.root), str(self.base), str(self.creator)):
      self.assertNotIn(secret, body)
    for leak in ("Errno", "Traceback", "save_dir"):
      self.assertNotIn(leak, body)

  def test_an_absurdly_large_start_is_refused_rather_than_crashing(self):
    ##
    ## HTTP puts no bound on the digits. Python integers do not overflow, but
    ## the arithmetic still has to reach a decision rather than an exception.
    ##
    response = self.get({"Range": "bytes=999999999999999999999999-"})

    self.assertEqual(416, response.status_code)
    self.assertEqual("bytes */10", response.headers["Content-Range"])

  def test_a_start_exactly_at_the_end_is_refused(self):
    ##
    ## Byte 10 of a ten byte file does not exist; the last one is byte 9.
    ##
    self.assertEqual(416, self.get({"Range": "bytes=10-"}).status_code)


class ZeroLengthFileTest(RangeTestCase):
  """A file with nothing in it must not produce arithmetic nobody checked."""

  def setUp(self):
    super().setUp()
    self.target.write_bytes(b"")
    self.settle()

  def test_the_whole_of_an_empty_file_is_a_valid_download(self):
    response = self.get()

    self.assertEqual(200, response.status_code)
    self.assertEqual(b"", response.get_data())
    self.assertEqual("0", response.headers["Content-Length"])
    self.assertEqual("bytes", response.headers["Accept-Ranges"])

  def test_a_range_of_an_empty_file_is_ignored_rather_than_refused(self):
    """RFC 9110 §14.2 permits ignoring Range when there is no content.

    Taken deliberately over 416: a partial response would need a Content-Range
    describing a window of an empty representation, and there is no such window
    to describe. Answering the whole of nothing is both valid and simpler.
    """
    for header in ("bytes=0-0", "bytes=0-", "bytes=-1", "bytes=-0", "bytes=5-9"):
      with self.subTest(header=header):
        response = self.get({"Range": header})

        self.assertEqual(200, response.status_code)
        self.assertEqual(b"", response.get_data())
        self.assertEqual("0", response.headers["Content-Length"])
        self.assertIsNone(response.headers.get("Content-Range"))
        ##
        ## Still advertised - ranges are supported, this representation simply
        ## has no bytes to take one of.
        ##
        self.assertEqual("bytes", response.headers["Accept-Ranges"])


##
## >>======================= headers this phase deliberately ignores =======================<<
##
class IgnoredRangeFormsTest(RangeTestCase):
  """Every one of these answers with the whole file rather than an error.

  A GET may always be answered in full. Refusing would turn a header this
  phase chose not to implement into a broken download.
  """

  def assert_full(self, header):
    response = self.get({"Range": header})

    self.assertEqual(200, response.status_code, header)
    self.assertEqual(BODY, response.get_data())
    self.assertIsNone(response.headers.get("Content-Range"))
    ##
    ## Still advertised, because ranges *are* supported - just not this one.
    ##
    self.assertEqual("bytes", response.headers["Accept-Ranges"])

  def test_several_ranges_are_answered_in_full_rather_than_as_multipart(self):
    ##
    ## multipart/byteranges is a second body format to implement and get right,
    ## for a case no download client sends. Not partially implemented.
    ##
    self.assert_full("bytes=0-1,5-6")

  def test_an_unsupported_unit_is_ignored(self):
    self.assert_full("items=0-1")

  def test_a_malformed_header_is_ignored_rather_than_failing(self):
    for header in ("garbage", "bytes=", "bytes=abc-def", "bytes=--5", "="):
      with self.subTest(header=header):
        response = self.get({"Range": header})
        self.assertEqual(200, response.status_code, header)
        self.assertEqual(BODY, response.get_data())

  def test_a_closed_range_wider_than_the_file_is_clamped(self):
    ##
    ## Unchanged, and correct: a last-byte-pos past the end is clamped to the
    ## end rather than refused.
    ##
    response = self.get({"Range": "bytes=0-100"})

    self.assertEqual(206, response.status_code)
    self.assertEqual(BODY, response.get_data())
    self.assertEqual("bytes 0-9/10", response.headers["Content-Range"])


##
## >>============================== resume safety ==============================<<
##
class IfRangeTest(RangeTestCase):
  """The reason this phase exists.

  A resumed download appends what it receives to bytes it already has. If the
  file changed in between, a 206 would splice two different files together and
  produce a corrupt result that nothing detected - not the client, not the
  server, not the user until they tried to play it.
  """

  def replace_file(self, payload=b"ABCDEFGHIJ"):
    ##
    ## os.replace is what a re-download, a re-encode or a repair does: same
    ## name, different content, atomically.
    ##
    replacement = self.creator / "replacement.tmp"
    replacement.write_bytes(payload)
    os.replace(str(replacement), str(self.target))
    self.settle()

  def test_a_resume_quoting_the_current_version_is_honoured(self):
    client = self.owner_client()
    tag = client.get(self.url()).headers["ETag"]

    response = client.get(self.url(), headers={"Range": "bytes=6-", "If-Range": tag})

    self.assertEqual(206, response.status_code)
    self.assertEqual(b"6789", response.get_data())
    self.assertEqual("bytes 6-9/10", response.headers["Content-Range"])

  def test_a_resume_quoting_a_version_that_is_gone_gets_the_whole_new_file(self):
    """The corruption this prevents, stated as a test.

    Without it the client would receive bytes 6-9 of the *new* file and append
    them to bytes 0-5 of the old one.
    """
    client = self.owner_client()
    original = client.get(self.url()).headers["ETag"]

    self.replace_file(b"ABCDEFGHIJ")

    response = client.get(
      self.url(), headers={"Range": "bytes=6-", "If-Range": original}
    )

    self.assertEqual(200, response.status_code)
    self.assertEqual(b"ABCDEFGHIJ", response.get_data())
    ##
    ## Not a partial answer of any kind.
    ##
    self.assertIsNone(response.headers.get("Content-Range"))
    self.assertNotEqual(original, response.headers["ETag"])

  def test_the_validator_changes_when_the_file_does_though_the_id_does_not(self):
    client = self.owner_client()
    before = client.get(self.url()).headers["ETag"]

    self.replace_file()

    after = client.get(self.url()).headers["ETag"]

    self.assertNotEqual(before, after)
    ##
    ## The url - and so the asset id in it - is byte for byte the same request.
    ## Only the validator noticed.
    ##
    self.assertEqual(200, client.get(self.url()).status_code)

  def test_an_unrelated_validator_is_not_honoured(self):
    response = self.get(
      {"Range": "bytes=6-", "If-Range": '"' + "0" * 64 + '"'}
    )

    self.assertEqual(200, response.status_code)
    self.assertEqual(BODY, response.get_data())

  def test_a_date_condition_falls_back_to_the_whole_file(self):
    """Deliberate: modification time is too coarse to resume against.

    Its one-second resolution cannot distinguish a file replaced moments after
    it was read, which is exactly the case that corrupts a resume. Rather than
    pretend, the whole representation is sent.
    """
    response = self.get(
      {"Range": "bytes=6-", "If-Range": "Wed, 21 Oct 2026 07:28:00 GMT"}
    )

    self.assertEqual(200, response.status_code)
    self.assertEqual(BODY, response.get_data())

  def test_a_condition_without_a_range_changes_nothing(self):
    client = self.owner_client()
    tag = client.get(self.url()).headers["ETag"]

    response = client.get(self.url(), headers={"If-Range": tag})

    self.assertEqual(200, response.status_code)
    self.assertEqual(BODY, response.get_data())

  def test_a_range_without_a_condition_is_still_honoured(self):
    ##
    ## If-Range is the client's option, not a requirement. Ordinary Range
    ## behaviour has to keep working for anything that does not send one.
    ##
    response = self.get({"Range": "bytes=5-"})

    self.assertEqual(206, response.status_code)
    self.assertEqual(b"56789", response.get_data())

  def test_a_grown_file_invalidates_a_resume(self):
    ##
    ## Appending is the common case for a recording still being written. The
    ## offsets a client holds are still valid, but this phase does not try to
    ## prove that - it sends the current representation whole.
    ##
    client = self.owner_client()
    original = client.get(self.url()).headers["ETag"]

    with open(str(self.target), "ab") as handle:
      handle.write(b"AB")
    ##
    ## Settled, so the refusal below is caused by the validator differing -
    ## not by the file being too recently written to judge.
    ##
    self.settle()

    response = client.get(
      self.url(), headers={"Range": "bytes=6-", "If-Range": original}
    )

    self.assertEqual(200, response.status_code)
    self.assertEqual(b"0123456789AB", response.get_data())


##
## >>================== the window is a cap, not a suggestion ==================<<
##
class ExactByteCapTest(RangeTestCase):
  """Proof that nothing downstream can send past the window.

  A file object handed to a WSGI server may be copied to the socket with
  ``sendfile``, which ignores anything expressed in Python. The count is the
  only assertion that would notice.
  """

  def setUp(self):
    super().setUp()
    ##
    ## A hundred distinguishable bytes, so a window of ten cannot pass by
    ## coincidence.
    ##
    self.big = bytes(one % 251 for one in range(100))
    self.target.write_bytes(self.big)
    self.settle()

  def test_a_ten_byte_window_of_a_hundred_byte_file_sends_ten_bytes(self):
    response = self.get({"Range": "bytes=10-19"})

    self.assertEqual(206, response.status_code)
    body = response.get_data()
    self.assertEqual(10, len(body))
    self.assertEqual(self.big[10:20], body)
    self.assertEqual("10", response.headers["Content-Length"])

  def test_the_declared_length_matches_the_bytes_actually_sent(self):
    for header, expected in (
      ("bytes=0-9", 10),
      ("bytes=50-", 50),
      ("bytes=-25", 25),
      ("bytes=99-99", 1),
    ):
      with self.subTest(header=header):
        response = self.get({"Range": header})
        body = response.get_data()
        self.assertEqual(expected, len(body))
        self.assertEqual(expected, int(response.headers["Content-Length"]))

  def test_the_partial_body_is_streamed_rather_than_assembled(self):
    ##
    ## The body is something to iterate, not a bytes object already built. A
    ## range can be most of a very large file.
    ##
    response = self.get({"Range": "bytes=10-19"})
    self.addCleanup(response.close)

    self.assertFalse(isinstance(response.response, (bytes, bytearray, str)))
    self.assertTrue(hasattr(response.response, "__iter__"))

  def test_the_streamed_body_offers_no_descriptor_to_optimise_past(self):
    client, _ = self.build(FakeQuery(post=self.post_row), principal=self.user())

    response = client.get(self.url(), headers={"Range": "bytes=10-19"}, buffered=False)
    self.addCleanup(response.close)

    ##
    ## Whatever wrapping the client applied, nothing in the chain offers a
    ## ``fileno`` - which is what a sendfile path would look for.
    ##
    self.assertFalse(hasattr(response.response, "fileno"))


##
## >>================================ HEAD ================================<<
##
class HeadTest(RangeTestCase):
  """HEAD answers what a GET would, without the body - and authorizes the same.

  Flask registers HEAD on every GET route, so it exists whether or not anyone
  designed it. A HEAD that skipped authorization would be an existence oracle:
  no bytes, but a 200 against a 404 is the entire answer somebody probing for
  another user's files wants.
  """

  def head(self, headers=None, client=None):
    return (client or self.owner_client()).head(self.url(), headers=headers or {})

  def test_it_reports_the_full_length_and_no_body(self):
    response = self.head()

    self.assertEqual(200, response.status_code)
    self.assertEqual("10", response.headers["Content-Length"])
    self.assertEqual(b"", response.get_data())

  def test_it_advertises_ranges_and_carries_a_validator(self):
    ##
    ## This is how a client learns a resume is possible before committing to
    ## downloading anything.
    ##
    response = self.head()

    self.assertEqual("bytes", response.headers["Accept-Ranges"])
    self.assertIsNotNone(response.headers.get("ETag"))

  def test_its_validator_is_the_one_a_get_would_give(self):
    client = self.owner_client()

    self.assertEqual(
      client.get(self.url()).headers["ETag"],
      client.head(self.url()).headers["ETag"],
    )

  def test_it_describes_the_same_attachment(self):
    response = self.head()

    self.assertTrue(
      response.headers["Content-Disposition"].startswith("attachment")
    )
    self.assertEqual("video/mp4", response.headers["Content-Type"])
    self.assertIn("no-store", response.headers["Cache-Control"])
    self.assertEqual("nosniff", response.headers["X-Content-Type-Options"])

  def test_a_range_on_a_head_is_ignored(self):
    """Deliberate: HEAD describes the representation, not a slice of it.

    Range semantics are defined for GET. Answering 206 to a HEAD would report a
    Content-Length for a body that is never sent, which is a worse answer than
    describing the whole thing.
    """
    response = self.head({"Range": "bytes=2-5"})

    self.assertEqual(200, response.status_code)
    self.assertEqual("10", response.headers["Content-Length"])
    self.assertIsNone(response.headers.get("Content-Range"))

  def test_an_anonymous_head_is_refused_without_touching_the_disk(self):
    client, resolver = self.build(FakeQuery(post=self.post_row))

    response = client.head(self.url())

    self.assertEqual(401, response.status_code)
    self.assertEqual([], resolver.calls)

  def test_a_cross_owner_head_cannot_tell_a_real_post_from_an_invented_one(self):
    client, resolver = self.build(FakeQuery(post=None), principal=self.user(99))

    real = client.head(self.url())
    invented = client.head(self.url(aweme_id="0000000000000000000"))

    self.assertEqual(404, real.status_code)
    self.assertEqual(invented.status_code, real.status_code)
    self.assertEqual([], resolver.calls)


##
## >>=================== a range never widens authorization ===================<<
##
class AuthorizationWithRangeTest(RangeTestCase):
  """A Range header changes which bytes are sent. Nothing else."""

  def test_an_anonymous_range_request_never_reaches_the_disk(self):
    client, resolver = self.build(FakeQuery(post=self.post_row))

    response = client.get(self.url(), headers={"Range": "bytes=0-3"})

    self.assertEqual(401, response.status_code)
    self.assertEqual([], resolver.calls)

  def test_a_cross_owner_range_request_never_reaches_the_disk(self):
    client, resolver = self.build(FakeQuery(post=None), principal=self.user(99))

    response = client.get(self.url(), headers={"Range": "bytes=0-3"})

    self.assertEqual(404, response.status_code)
    self.assertEqual([], resolver.calls)
    self.assertNotIn(b"0123", response.get_data())

  def test_an_unavailable_backend_refuses_a_range_request_without_the_disk(self):
    client, resolver = self.build(
      FakeQuery(post=self.post_row),
      principal=self.user(),
      unavailable=LibraryUnavailable("数据库暂时不可用"),
    )

    response = client.get(self.url(), headers={"Range": "bytes=0-3"})

    self.assertEqual(503, response.status_code)
    self.assertEqual([], resolver.calls)

  def test_a_condition_header_cannot_widen_scope(self):
    ##
    ## None of these are inputs to authorization, and a request carrying all of
    ## them is refused exactly as one carrying none would be.
    ##
    client, resolver = self.build(FakeQuery(post=None), principal=self.user(99))

    response = client.get(
      self.url(),
      headers={
        "Range": "bytes=0-3",
        "If-Range": '"' + "0" * 64 + '"',
        "If-None-Match": "*",
        "If-Match": "*",
      },
    )

    self.assertEqual(404, response.status_code)
    self.assertEqual([], resolver.calls)

  def test_an_id_from_another_post_is_not_redeemable_with_a_range(self):
    ##
    ## The asset id is still not a capability. A Range header does not make it
    ## one.
    ##
    response = self.get(
      {"Range": "bytes=0-3"},
      client=self.build(FakeQuery(post=self.post_row), principal=self.user())[0],
    )
    self.assertEqual(206, response.status_code)

    other = asset_id_for("post", ("douyin", "1111111111111111111"), self.name)
    client, _ = self.build(FakeQuery(post=self.post_row), principal=self.user())

    refused = client.get(self.url(asset_id=other), headers={"Range": "bytes=0-3"})

    self.assertEqual(404, refused.status_code)

  def test_a_recording_identity_beyond_the_safe_range_serves_a_window(self):
    client, _ = self.build(
      FakeQuery(recording=self.recording_row), principal=self.user()
    )
    url = "/api/library/recordings/{}/assets/{}/download".format(
      BEYOND_SAFE,
      asset_id_for("recording", (BEYOND_SAFE,), self.recording_name),
    )

    response = client.get(url, headers={"Range": "bytes=0-8"})

    self.assertEqual(206, response.status_code)
    self.assertEqual(b"RECORDING", response.get_data())
    self.assertEqual("bytes 0-8/15", response.headers["Content-Range"])


##
## >>=========================== descriptor lifecycle ===========================<<
##
class RangeDescriptorLifecycleTest(RangeTestCase):
  def descriptor_count(self):
    return len(os.listdir("/proc/self/fd"))

  @unittest.skipUnless(os.path.isdir("/proc/self/fd"), "requires /proc")
  def test_no_kind_of_response_leaks_a_descriptor(self):
    client = self.owner_client()
    cases = {
      "full": {},
      "partial": {"Range": "bytes=2-5"},
      "unsatisfiable": {"Range": "bytes=200-300"},
      "if-range mismatch": {"Range": "bytes=2-5", "If-Range": '"' + "0" * 64 + '"'},
      "ignored multi-range": {"Range": "bytes=0-1,5-6"},
      "malformed": {"Range": "garbage"},
    }

    for name, headers in cases.items():
      with self.subTest(case=name):
        before = self.descriptor_count()
        for _ in range(15):
          response = client.get(self.url(), headers=headers)
          response.close()
        self.assertEqual(before, self.descriptor_count())

  @unittest.skipUnless(os.path.isdir("/proc/self/fd"), "requires /proc")
  def test_a_head_leaks_nothing(self):
    client = self.owner_client()

    before = self.descriptor_count()
    for _ in range(15):
      client.head(self.url()).close()

    self.assertEqual(before, self.descriptor_count())

  @unittest.skipUnless(os.path.isdir("/proc/self/fd"), "requires /proc")
  def test_a_partial_download_abandoned_part_way_releases_the_file(self):
    ##
    ## The common case in production: a resume that is cancelled again.
    ##
    self.target.write_bytes(bytes(one % 251 for one in range(4 * 1024 * 1024)))
    client = self.owner_client()

    before = self.descriptor_count()
    for _ in range(15):
      response = client.get(
        self.url(), headers={"Range": "bytes=0-"}, buffered=False
      )
      next(response.response.__iter__(), None)
      response.close()

    self.assertEqual(before, self.descriptor_count())

  def test_an_unsatisfiable_range_releases_the_file_immediately(self):
    """Nothing is going to be sent, so nothing should still be held open."""
    opened_streams = []

    class WatchingResolver(CountingResolver):
      def open_post_asset(inner, save_dir, platform, aweme_id, asset_id):
        opened = super().open_post_asset(save_dir, platform, aweme_id, asset_id)
        if opened is not None:
          opened_streams.append(opened.stream)
        return opened

    resolver = WatchingResolver(lambda: str(self.root))
    runtime = FakeRuntime(query=FakeQuery(post=self.post_row), resolver=resolver)
    app = Flask(__name__)
    install_test_auth(app, user=self.user())
    app.register_blueprint(build_library_blueprint(runtime=runtime))

    response = app.test_client().get(self.url(), headers={"Range": "bytes=99-200"})

    self.assertEqual(416, response.status_code)
    self.assertEqual(1, len(opened_streams))
    ##
    ## Closed before the response was even returned, not on response teardown.
    ##
    self.assertTrue(opened_streams[0].closed)

  def test_a_completed_partial_response_closes_its_file(self):
    opened_streams = []

    class WatchingResolver(CountingResolver):
      def open_post_asset(inner, save_dir, platform, aweme_id, asset_id):
        opened = super().open_post_asset(save_dir, platform, aweme_id, asset_id)
        if opened is not None:
          opened_streams.append(opened.stream)
        return opened

    resolver = WatchingResolver(lambda: str(self.root))
    runtime = FakeRuntime(query=FakeQuery(post=self.post_row), resolver=resolver)
    app = Flask(__name__)
    install_test_auth(app, user=self.user())
    app.register_blueprint(build_library_blueprint(runtime=runtime))

    response = app.test_client().get(self.url(), headers={"Range": "bytes=2-5"})
    self.assertEqual(b"2345", response.get_data())
    response.close()

    self.assertEqual(1, len(opened_streams))
    self.assertTrue(opened_streams[0].closed)


##
## >>=========================== memory, not just bytes ===========================<<
##
class StreamingMemoryTest(RangeTestCase):
  """A window may be most of a very large file. It is never assembled."""

  def test_a_large_window_is_read_in_bounded_pieces(self):
    from backend.src.service import media_range

    ##
    ## Several chunks worth, without writing anything large to disk.
    ##
    payload = bytes(one % 251 for one in range(media_range.RANGE_CHUNK_SIZE * 3))
    self.target.write_bytes(payload)

    observed = []
    real_reader = media_range.BoundedRangeReader

    class SpyingReader(real_reader):
      def __init__(inner, stream, start, length):
        observed.append(("window", start, length))
        super().__init__(_RecordingStream(stream, observed), start, length)

    import backend.src.web.library_routes as routes

    routes.BoundedRangeReader = SpyingReader
    try:
      response = self.get({"Range": "bytes=0-"})
      body = response.get_data()
    finally:
      routes.BoundedRangeReader = real_reader

    self.assertEqual(len(payload), len(body))

    reads = [one for one in observed if one[0] == "read"]
    self.assertTrue(reads)
    ##
    ## No single read asked for the whole window - which is what
    ## ``stream.read(length)`` would have done.
    ##
    for _, size in reads:
      self.assertLessEqual(size, media_range.RANGE_CHUNK_SIZE)
    self.assertGreater(len(reads), 1)


class _RecordingStream:
  """Passes everything through, and writes down every read size."""

  def __init__(self, inner, log):
    self._inner = inner
    self._log = log

  def seek(self, *args, **kwargs):
    return self._inner.seek(*args, **kwargs)

  def read(self, size=-1):
    self._log.append(("read", size))
    return self._inner.read(size)

  def close(self):
    return self._inner.close()

  @property
  def closed(self):
    return self._inner.closed


##
## >>=================== RFC 9110 suffix-range semantics ===================<<
##
class SuffixRangeRfcTest(RangeTestCase):
  """§14.1.2, stated case by case.

  Werkzeug's ``range_for_length`` disagrees with the RFC in two places - it
  refuses a suffix longer than the representation, and accepts a zero-length
  one. It is a helper, not this server's contract, so both are normalized after
  parsing rather than passed through.

  The rest of the parse is still entirely Werkzeug's.
  """

  def test_a_suffix_shorter_than_the_file_takes_that_much_of_the_tail(self):
    response = self.get({"Range": "bytes=-3"})

    self.assertEqual(206, response.status_code)
    self.assertEqual(b"789", response.get_data())
    self.assertEqual("bytes 7-9/10", response.headers["Content-Range"])
    self.assertEqual("3", response.headers["Content-Length"])

  def test_a_suffix_the_length_of_the_file_is_the_whole_file(self):
    response = self.get({"Range": "bytes=-10"})

    self.assertEqual(206, response.status_code)
    self.assertEqual(BODY, response.get_data())
    self.assertEqual("bytes 0-9/10", response.headers["Content-Range"])

  def test_a_suffix_longer_than_the_file_is_the_whole_file(self):
    """§14.1.2: "if the selected representation is shorter than the specified
    suffix-length, the entire representation is used."

    Not 416. A client asking for the last 5000 bytes of a 10-byte file is
    asking for all of it, and that request is satisfiable.
    """
    response = self.get({"Range": "bytes=-5000"})

    self.assertEqual(206, response.status_code)
    self.assertEqual(BODY, response.get_data())
    self.assertEqual("bytes 0-9/10", response.headers["Content-Range"])
    self.assertEqual("10", response.headers["Content-Length"])

  def test_a_zero_length_suffix_cannot_be_satisfied(self):
    """§14.1.2 makes a suffix satisfiable only for a non-zero suffix-length.

    "The last zero bytes" names no window at all.
    """
    response = self.get({"Range": "bytes=-0"})

    self.assertEqual(416, response.status_code)
    self.assertEqual("bytes */10", response.headers["Content-Range"])
    self.assertEqual("bytes", response.headers["Accept-Ranges"])

  def test_a_zero_suffix_is_not_confused_with_a_range_from_the_first_byte(self):
    """The distinction the parse cannot make on its own.

    ``bytes=-0`` and ``bytes=0-`` both parse to ``(0, None)`` - the sign is
    lost on an integer zero - and they mean opposite things. If this ever
    regresses, one of these two assertions fails.
    """
    self.assertEqual(416, self.get({"Range": "bytes=-0"}).status_code)

    from_first = self.get({"Range": "bytes=0-"})
    self.assertEqual(206, from_first.status_code)
    self.assertEqual(BODY, from_first.get_data())
    self.assertEqual("bytes 0-9/10", from_first.headers["Content-Range"])

  def test_whitespace_does_not_change_which_form_a_range_is(self):
    ##
    ## The header may carry optional whitespace after the unit. It must not
    ## turn a suffix into something else.
    ##
    self.assertEqual(416, self.get({"Range": "bytes= -0"}).status_code)

    padded = self.get({"Range": "bytes= -3"})
    self.assertEqual(206, padded.status_code)
    self.assertEqual(b"789", padded.get_data())

  def test_the_reviewed_matrix_in_full(self):
    """Every case from the review, asserted together.

    Kept as one table so the whole contract can be read at once rather than
    reassembled from separate tests.
    """
    expected = [
      ("bytes=-3", 206, "bytes 7-9/10", b"789"),
      ("bytes=-5000", 206, "bytes 0-9/10", BODY),
      ("bytes=-0", 416, "bytes */10", None),
      ("bytes=0-100", 206, "bytes 0-9/10", BODY),
    ]

    for header, status, content_range, body in expected:
      with self.subTest(header=header):
        response = self.get({"Range": header})
        self.assertEqual(status, response.status_code)
        self.assertEqual(content_range, response.headers["Content-Range"])
        if body is not None:
          self.assertEqual(body, response.get_data())
          self.assertEqual(str(len(body)), response.headers["Content-Length"])


##
## >>=============== the limit of a timestamp-derived validator ===============<<
##
class ValidatorStrengthTest(RangeTestCase):
  """What happens when the tag cannot prove what it appears to prove.

  A filesystem records modification times at finite resolution. Two writes
  inside one tick carry the same timestamp, so a file rewritten immediately
  after being read can present an identical tag over different bytes.

  Honouring ``If-Range`` there would append new content to old and call it a
  download - through the very mechanism meant to prevent that. So a
  representation written within the window is not treated as strong, and the
  resume becomes a full send.
  """

  def rewrite_in_place(self, payload):
    with open(str(self.target), "r+b") as handle:
      handle.seek(0)
      handle.write(payload)
      handle.flush()
      os.fsync(handle.fileno())

  def test_a_resume_against_a_just_written_file_is_not_honoured(self):
    client = self.owner_client()
    tag = client.get(self.url()).headers["ETag"]

    ##
    ## Same length, same inode, different bytes, immediately. The tag may well
    ## be unchanged - that is the filesystem's resolution, not a bug - and it
    ## must not be trusted.
    ##
    self.rewrite_in_place(b"ABCDEFGHIJ")

    response = client.get(
      self.url(), headers={"Range": "bytes=6-", "If-Range": tag}
    )

    self.assertEqual(200, response.status_code)
    self.assertEqual(b"ABCDEFGHIJ", response.get_data())
    self.assertIsNone(response.headers.get("Content-Range"))

  def test_a_resume_against_a_settled_file_is_honoured(self):
    ##
    ## The ordinary case, and the one that has to keep working: a file written
    ## long enough ago that its timestamp is decisive.
    ##
    old = time.time() - 3600
    os.utime(str(self.target), (old, old))

    client = self.owner_client()
    tag = client.get(self.url()).headers["ETag"]

    response = client.get(
      self.url(), headers={"Range": "bytes=6-", "If-Range": tag}
    )

    self.assertEqual(206, response.status_code)
    self.assertEqual(b"6789", response.get_data())

  def test_an_ordinary_range_is_unaffected_by_validator_strength(self):
    """Only If-Range consults it.

    A client that asked for a window without claiming to know which version it
    is resuming gets that window, freshly read, as it always did.
    """
    self.rewrite_in_place(b"ABCDEFGHIJ")

    response = self.get({"Range": "bytes=6-"})

    self.assertEqual(206, response.status_code)
    self.assertEqual(b"GHIJ", response.get_data())

  def test_no_entity_tag_is_published_for_a_just_written_file(self):
    """An unprefixed ETag *is* a strong validator, as far as HTTP is concerned.

    RFC 9110 §8.8.1 requires a server whose generation mechanism cannot meet
    that standard to say so. Sending an unmarked tag here would be the header
    claiming a guarantee the mechanism behind it does not provide - and a
    client is entitled to build an ``If-Range`` out of whatever it is given.

    Withheld rather than marked ``W/``: a weak tag could not satisfy
    ``If-Range`` either, since §13.1.3 requires a strong comparison, so it
    would be a second kind of state carried for no gain. These responses are
    already ``no-store``, so no cache wants one.
    """
    self.rewrite_in_place(b"ABCDEFGHIJ")

    response = self.get()

    self.assertEqual(200, response.status_code)
    self.assertIsNone(response.headers.get("ETag"))

  def test_a_settled_file_publishes_a_strong_tag_with_no_weak_prefix(self):
    response = self.get()

    tag = response.headers.get("ETag")
    self.assertIsNotNone(tag)
    self.assertFalse(tag.startswith("W/"), tag)
    self.assertTrue(tag.startswith('"') and tag.endswith('"'), tag)

  def test_a_fabricated_condition_cannot_resume_a_just_written_file(self):
    ##
    ## Nothing was published, so nothing can match - whatever the client
    ## quotes, including a tag it held from before the rewrite.
    ##
    self.rewrite_in_place(b"ABCDEFGHIJ")

    response = self.get(
      {"Range": "bytes=6-", "If-Range": '"' + "0" * 64 + '"'}
    )

    self.assertEqual(200, response.status_code)
    self.assertEqual(b"ABCDEFGHIJ", response.get_data())

  def test_a_just_written_file_still_serves_an_unconditional_range(self):
    ##
    ## Only ``If-Range`` depends on a validator. A client asking for a window
    ## without claiming to know which version it has gets that window.
    ##
    self.rewrite_in_place(b"ABCDEFGHIJ")

    response = self.get({"Range": "bytes=6-"})

    self.assertEqual(206, response.status_code)
    self.assertEqual(b"GHIJ", response.get_data())
    self.assertIsNone(response.headers.get("ETag"))

  def test_a_new_strong_tag_appears_once_the_representation_settles(self):
    """The full arc: settled, rewritten, unpublished, then settled again."""
    before = self.get().headers["ETag"]

    self.rewrite_in_place(b"ABCDEFGHIJ")
    self.assertIsNone(self.get().headers.get("ETag"))

    ##
    ## The same bytes, once the clock can vouch for them.
    ##
    self.settle()
    after = self.get().headers.get("ETag")

    self.assertIsNotNone(after)
    self.assertFalse(after.startswith("W/"), after)
    self.assertNotEqual(before, after)
