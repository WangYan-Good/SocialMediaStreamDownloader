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
BEYOND_SAFE = 9007199254740993
##
## Ten distinguishable bytes. Nothing here has to be a decodable JPEG or MP4 -
## these tests are about the HTTP boundary, not a browser's decoder.
##
BODY = b"0123456789"


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


class PreviewTestCase(unittest.TestCase):
  """One directory holding one file of each interesting media type."""

  def setUp(self):
    self._tmp = tempfile.TemporaryDirectory()
    self.base = Path(self._tmp.name)
    self.root = self.base / "downloads"
    self.creator = self.root / "creator"
    self.creator.mkdir(parents=True)
    self.addCleanup(self._tmp.cleanup)

    ##
    ## Named the way the downloader names them, so discovery recognises each.
    ##
    self.names = {
      "video": "20260824_{}.mp4".format(AWEME),
      "image": "20260824_{}_01.jpg".format(AWEME),
      "audio": "20260824_{}_music.mp3".format(AWEME),
    }
    for name in self.names.values():
      (self.creator / name).write_bytes(BODY)

    self.recording_name = "live.flv"
    self.recording_path = self.creator / self.recording_name
    self.recording_path.write_bytes(BODY)

    self.post_row = {
      "platform": "douyin",
      "aweme_id": AWEME,
      "save_dir": str(self.creator),
    }
    self.recording_row = {
      "recording_id": BEYOND_SAFE,
      "app_user_id": 3,
      "output_path": str(self.recording_path),
    }

    ##
    ## Aged past the validator-strength window, so a strong ETag is published
    ## and the If-Range parity tests below mean something.
    ##
    self.settle()

  def settle(self, *paths):
    old = time.time() - 3600
    for one in paths or (
      [self.creator / name for name in self.names.values()] + [self.recording_path]
    ):
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

  def refused_recording(self):
    """A recording of the one container still refused for rendering.

    Phase 10E admitted flv, so it is no longer an example of a refused type.
    MPEG-TS is - seeking within a static .ts file remains limited upstream - and
    these tests are about what happens to a refusal, not about which container
    it happens to be.
    """
    target = self.creator / "live.ts"
    target.write_bytes(BODY)
    self.settle(target)
    row = dict(self.recording_row, output_path=str(target))
    return row, asset_id_for("recording", (BEYOND_SAFE,), "live.ts")

  def refused_url(self, asset_id):
    return "/api/library/recordings/{}/assets/{}/preview".format(
      BEYOND_SAFE, asset_id
    )

  def post_id(self, name):
    return asset_id_for("post", ("douyin", AWEME), name)

  def url(self, name=None, asset_id=None, aweme_id=AWEME, action="preview"):
    chosen = asset_id or asset_id_for(
      "post", ("douyin", aweme_id), name or self.names["image"]
    )
    return "/api/library/posts/douyin/{}/assets/{}/{}".format(
      aweme_id, chosen, action
    )

  def owner_client(self):
    return self.build(FakeQuery(post=self.post_row), principal=self.user())[0]

  def get(self, name=None, headers=None, client=None, **kwargs):
    return (client or self.owner_client()).get(
      self.url(name=name, **kwargs), headers=headers or {}
    )


##
## >>================== authorization strictly before filesystem ==================<<
##
class PreviewAuthorizationTest(PreviewTestCase):
  """Inline delivery does not get an easier door onto the same bytes."""

  def test_an_anonymous_preview_is_refused_without_a_disk_read(self):
    client, resolver = self.build(FakeQuery(post=self.post_row))

    response = client.get(self.url())

    self.assertEqual(401, response.status_code)
    self.assertEqual([], resolver.calls)

  def test_an_anonymous_recording_preview_is_refused_without_a_disk_read(self):
    client, resolver = self.build(FakeQuery(recording=self.recording_row))

    response = client.get(
      "/api/library/recordings/{}/assets/{}/preview".format(
        BEYOND_SAFE, asset_id_for("recording", (BEYOND_SAFE,), self.recording_name)
      )
    )

    self.assertEqual(401, response.status_code)
    self.assertEqual([], resolver.calls)

  def test_a_cross_owner_preview_is_refused_without_a_disk_read(self):
    client, resolver = self.build(FakeQuery(post=None), principal=self.user(99))

    response = client.get(self.url())

    self.assertEqual(404, response.status_code)
    self.assertEqual([], resolver.calls)
    self.assertNotIn(BODY, response.get_data())

  def test_an_unavailable_backend_refuses_without_a_disk_read(self):
    client, resolver = self.build(
      FakeQuery(post=self.post_row),
      principal=self.user(),
      unavailable=LibraryUnavailable("数据库暂时不可用"),
    )

    response = client.get(self.url())

    self.assertEqual(503, response.status_code)
    self.assertEqual([], resolver.calls)

  def test_an_anonymous_ranged_preview_never_reaches_the_disk(self):
    ##
    ## A Range header does not change who may ask, on this route either.
    ##
    client, resolver = self.build(FakeQuery(post=self.post_row))

    response = client.get(self.url(), headers={"Range": "bytes=0-3"})

    self.assertEqual(401, response.status_code)
    self.assertEqual([], resolver.calls)

  def test_an_anonymous_head_preview_never_reaches_the_disk(self):
    client, resolver = self.build(FakeQuery(post=self.post_row))

    self.assertEqual(401, client.head(self.url()).status_code)
    self.assertEqual([], resolver.calls)

  def test_a_cross_owner_head_cannot_distinguish_a_real_post(self):
    client, resolver = self.build(FakeQuery(post=None), principal=self.user(99))

    real = client.head(self.url())
    invented = client.head(self.url(aweme_id="0000000000000000000"))

    self.assertEqual(404, real.status_code)
    self.assertEqual(invented.status_code, real.status_code)
    self.assertEqual([], resolver.calls)

  def test_an_admin_may_preview_a_resource_that_belongs_to_nobody(self):
    client, _ = self.build(
      FakeQuery(post=self.post_row), principal=self.user(1, ROLE_ADMIN)
    )

    response = client.get(self.url())

    self.assertEqual(200, response.status_code)
    self.assertEqual(BODY, response.get_data())

  def test_an_admin_may_preview_an_unowned_recording(self):
    unowned = dict(self.recording_row, app_user_id=None, output_path=str(
      self.creator / self.names["video"]
    ))
    client, _ = self.build(
      FakeQuery(recording=unowned), principal=self.user(1, ROLE_ADMIN)
    )

    response = client.get(
      "/api/library/recordings/{}/assets/{}/preview".format(
        BEYOND_SAFE,
        asset_id_for("recording", (BEYOND_SAFE,), self.names["video"]),
      )
    )

    self.assertEqual(200, response.status_code)
    self.assertEqual("video/mp4", response.headers["Content-Type"])


##
## >>========================= the closed MIME boundary =========================<<
##
class PreviewMediaTypeTest(PreviewTestCase):
  """Only three types are rendered. Everything else is a download."""

  def test_a_jpeg_is_served_for_rendering(self):
    response = self.get(self.names["image"])

    self.assertEqual(200, response.status_code)
    self.assertEqual("image/jpeg", response.headers["Content-Type"])
    self.assertEqual(BODY, response.get_data())

  def test_an_mp4_is_served_for_rendering(self):
    response = self.get(self.names["video"])

    self.assertEqual(200, response.status_code)
    self.assertEqual("video/mp4", response.headers["Content-Type"])
    self.assertEqual(BODY, response.get_data())

  def test_an_mp3_is_served_for_rendering(self):
    response = self.get(self.names["audio"])

    self.assertEqual(200, response.status_code)
    self.assertEqual("audio/mpeg", response.headers["Content-Type"])
    self.assertEqual(BODY, response.get_data())

  def test_a_transport_stream_recording_is_refused_rather_than_rendered(self):
    """Refusing is the honest answer where a preview could not work properly.

    Phase 10E gave flv a browser-side transmuxer. MPEG-TS did not follow: the
    same library demuxes it, but seeking within a static .ts file is limited
    upstream, so a preview would work until somebody scrubbed - a worse offer
    than none.
    """
    row, asset = self.refused_recording()
    client, _ = self.build(FakeQuery(recording=row), principal=self.user())

    response = client.get(self.refused_url(asset))

    self.assertEqual(415, response.status_code)
    self.assertNotIn(BODY, response.get_data())

  def test_a_transport_stream_is_refused(self):
    target = self.creator / "live.ts"
    target.write_bytes(BODY)
    row = dict(self.recording_row, output_path=str(target))
    client, _ = self.build(FakeQuery(recording=row), principal=self.user())

    response = client.get(
      "/api/library/recordings/{}/assets/{}/preview".format(
        BEYOND_SAFE, asset_id_for("recording", (BEYOND_SAFE,), "live.ts")
      )
    )

    self.assertEqual(415, response.status_code)

  def test_a_refusal_explains_nothing_about_the_filesystem(self):
    row, asset = self.refused_recording()
    client, _ = self.build(FakeQuery(recording=row), principal=self.user())

    response = client.get(self.refused_url(asset))

    body = response.get_data(as_text=True)
    self.assertIn("application/json", response.headers["Content-Type"])
    self.assertEqual("error", json.loads(body)["status"])
    for secret in (str(self.root), str(self.base), str(self.creator), ".ts"):
      self.assertNotIn(secret, body)

  def test_a_range_does_not_talk_the_server_into_rendering_a_refused_type(self):
    ##
    ## The type was refused; asking for part of it changes nothing. A 206 here
    ## would hand a browser bytes it had just been told it may not render.
    ##
    row, asset = self.refused_recording()
    client, _ = self.build(FakeQuery(recording=row), principal=self.user())

    response = client.get(
      self.refused_url(asset), headers={"Range": "bytes=0-3"}
    )

    self.assertEqual(415, response.status_code)
    self.assertNotIn(b"0123", response.get_data())

  def test_an_unrecognised_type_is_refused(self):
    ##
    ## Discovery only recognises files belonging to this post, so the fixture
    ## uses a name it accepts with an extension the media map does not know.
    ##
    unknown = "20260824_{}.mp4.part".format(AWEME)
    (self.creator / unknown).write_bytes(BODY)

    response = self.get(unknown)

    ##
    ## Not recognised as this post's media at all, so it is not an asset - 404
    ## rather than 415, because there is nothing to have an opinion about.
    ##
    self.assertEqual(404, response.status_code)

  def test_the_download_route_still_serves_what_preview_refuses(self):
    """Refusing to render is not refusing to deliver."""
    row, asset = self.refused_recording()
    client, _ = self.build(FakeQuery(recording=row), principal=self.user())

    response = client.get(
      "/api/library/recordings/{}/assets/{}/download".format(BEYOND_SAFE, asset)
    )

    self.assertEqual(200, response.status_code)
    self.assertEqual(BODY, response.get_data())
    self.assertTrue(
      response.headers["Content-Disposition"].startswith("attachment")
    )


##
## >>==================== an id is still not a capability ====================<<
##
class PreviewAssetIdentityTest(PreviewTestCase):
  def test_an_unknown_id_is_missing_rather_than_unsupported(self):
    ##
    ## 415 would confirm the id named a real file. The type question is only
    ## reached after the id has matched the current discovery.
    ##
    response = self.get(asset_id="0" * 64)

    self.assertEqual(404, response.status_code)

  def test_a_malformed_id_answers_exactly_like_an_unknown_one(self):
    unknown = self.get(asset_id="0" * 64)
    malformed = self.get(asset_id="not-an-id")

    self.assertEqual(404, unknown.status_code)
    self.assertEqual(unknown.status_code, malformed.status_code)
    self.assertEqual(
      json.loads(unknown.get_data(as_text=True))["message"],
      json.loads(malformed.get_data(as_text=True))["message"],
    )

  def test_an_id_issued_for_another_post_previews_nothing(self):
    other = asset_id_for("post", ("douyin", "1111111111111111111"), self.names["image"])

    self.assertEqual(404, self.get(asset_id=other).status_code)

  def test_a_recording_id_does_not_redeem_on_a_post_preview(self):
    other = asset_id_for("recording", (BEYOND_SAFE,), self.recording_name)

    self.assertEqual(404, self.get(asset_id=other).status_code)

  def test_a_file_deleted_after_it_was_listed_previews_nothing(self):
    client = self.owner_client()
    listed = client.get("/api/library/posts/douyin/{}/assets".format(AWEME))
    self.assertEqual(200, listed.status_code)

    (self.creator / self.names["image"]).unlink()

    self.assertEqual(404, self.get(self.names["image"], client=client).status_code)


##
## >>========================= how the bytes are presented =========================<<
##
class PreviewPresentationTest(PreviewTestCase):
  def test_a_preview_is_never_an_attachment(self):
    response = self.get(self.names["image"])

    disposition = response.headers.get("Content-Disposition")
    self.assertIsNone(disposition, disposition)

  def test_a_preview_cannot_be_reinterpreted_by_sniffing(self):
    """The header that matters most here.

    A .jpg holding something else must not be re-read by the browser as HTML
    and executed on this origin.
    """
    self.assertEqual(
      "nosniff", self.get(self.names["image"]).headers["X-Content-Type-Options"]
    )

  def test_a_preview_may_only_be_embedded_by_this_origin(self):
    ##
    ## Without this, another site could embed a logged-in user's video by url
    ## and learn about it from load timing and dimensions.
    ##
    self.assertEqual(
      "same-origin",
      self.get(self.names["image"]).headers["Cross-Origin-Resource-Policy"],
    )

  def test_a_preview_is_not_cacheable(self):
    cache = self.get(self.names["image"]).headers["Cache-Control"]

    self.assertIn("private", cache)
    self.assertIn("no-store", cache)
    self.assertNotIn("public", cache)

  def test_a_partial_preview_carries_the_same_protections(self):
    response = self.get(self.names["video"], headers={"Range": "bytes=2-5"})

    self.assertEqual(206, response.status_code)
    self.assertIsNone(response.headers.get("Content-Disposition"))
    self.assertEqual("nosniff", response.headers["X-Content-Type-Options"])
    self.assertEqual(
      "same-origin", response.headers["Cross-Origin-Resource-Policy"]
    )
    self.assertIn("no-store", response.headers["Cache-Control"])

  def test_the_download_route_is_untouched_by_any_of_this(self):
    ##
    ## The two differ in presentation and nothing else. A download must still
    ## be an attachment, and must not acquire a CORP header it never had.
    ##
    response = self.get(self.names["image"], action="download")

    self.assertTrue(
      response.headers["Content-Disposition"].startswith("attachment")
    )
    self.assertIsNone(response.headers.get("Cross-Origin-Resource-Policy"))

  def test_the_content_type_comes_from_the_server_not_the_request(self):
    ##
    ## There is no parameter to pass one, and an Accept header is not a
    ## proposal about what this file is.
    ##
    response = self.get(
      self.names["image"], headers={"Accept": "text/html", "Content-Type": "text/html"}
    )

    self.assertEqual("image/jpeg", response.headers["Content-Type"])


##
## >>=================== the same transport, not a second one ===================<<
##
class PreviewRangeParityTest(PreviewTestCase):
  """Preview reuses Phase 10C's delivery, so it inherits its guarantees.

  Not a re-derivation of the whole range contract - that is tested exhaustively
  against the download route. What these assert is that preview goes through
  the same code, so a fix or a regression there reaches both.
  """

  def video(self, headers=None):
    return self.get(self.names["video"], headers=headers)

  def test_a_full_preview_advertises_ranges_and_a_validator(self):
    response = self.video()

    self.assertEqual("bytes", response.headers["Accept-Ranges"])
    tag = response.headers.get("ETag")
    self.assertIsNotNone(tag)
    self.assertFalse(tag.startswith("W/"), tag)

  def test_a_closed_range_returns_exactly_that_window(self):
    response = self.video({"Range": "bytes=2-5"})

    self.assertEqual(206, response.status_code)
    self.assertEqual(b"2345", response.get_data())
    self.assertEqual("bytes 2-5/10", response.headers["Content-Range"])
    self.assertEqual("4", response.headers["Content-Length"])

  def test_an_open_ended_range_runs_to_the_end(self):
    response = self.video({"Range": "bytes=6-"})

    self.assertEqual(206, response.status_code)
    self.assertEqual(b"6789", response.get_data())

  def test_a_suffix_range_counts_back_from_the_end(self):
    response = self.video({"Range": "bytes=-3"})

    self.assertEqual(206, response.status_code)
    self.assertEqual(b"789", response.get_data())

  def test_the_rfc_suffix_normalization_applies_here_too(self):
    ##
    ## The two cases Phase 10C normalized after parsing. Sharing the transport
    ## means sharing these.
    ##
    longer = self.video({"Range": "bytes=-5000"})
    self.assertEqual(206, longer.status_code)
    self.assertEqual(BODY, longer.get_data())

    self.assertEqual(416, self.video({"Range": "bytes=-0"}).status_code)

  def test_an_unsatisfiable_range_reports_the_real_length(self):
    response = self.video({"Range": "bytes=200-300"})

    self.assertEqual(416, response.status_code)
    self.assertEqual("bytes */10", response.headers["Content-Range"])

  def test_a_matching_condition_resumes(self):
    client = self.owner_client()
    tag = client.get(self.url(self.names["video"])).headers["ETag"]

    response = client.get(
      self.url(self.names["video"]),
      headers={"Range": "bytes=6-", "If-Range": tag},
    )

    self.assertEqual(206, response.status_code)
    self.assertEqual(b"6789", response.get_data())

  def test_a_stale_condition_sends_the_whole_current_representation(self):
    response = self.video(
      {"Range": "bytes=6-", "If-Range": '"' + "0" * 64 + '"'}
    )

    self.assertEqual(200, response.status_code)
    self.assertEqual(BODY, response.get_data())

  def test_a_just_written_representation_publishes_no_validator(self):
    ##
    ## The strength window, inherited unchanged.
    ##
    with open(str(self.creator / self.names["video"]), "r+b") as handle:
      handle.seek(0)
      handle.write(b"ABCDEFGHIJ")

    response = self.video()

    self.assertEqual(200, response.status_code)
    self.assertIsNone(response.headers.get("ETag"))

  def test_head_describes_the_representation_and_ignores_range(self):
    client = self.owner_client()

    response = client.head(
      self.url(self.names["video"]), headers={"Range": "bytes=2-5"}
    )

    self.assertEqual(200, response.status_code)
    self.assertEqual("10", response.headers["Content-Length"])
    self.assertIsNone(response.headers.get("Content-Range"))
    self.assertEqual("bytes", response.headers["Accept-Ranges"])
    self.assertEqual(
      "same-origin", response.headers["Cross-Origin-Resource-Policy"]
    )
    self.assertEqual(b"", response.get_data())

  def test_an_empty_representation_ignores_range(self):
    (self.creator / self.names["video"]).write_bytes(b"")
    self.settle()

    response = self.video({"Range": "bytes=0-0"})

    self.assertEqual(200, response.status_code)
    self.assertEqual(b"", response.get_data())
    self.assertEqual("0", response.headers["Content-Length"])

  def test_a_partial_preview_sends_exactly_the_requested_bytes(self):
    big = bytes(one % 251 for one in range(100))
    (self.creator / self.names["video"]).write_bytes(big)
    self.settle()

    response = self.video({"Range": "bytes=10-19"})

    self.assertEqual(206, response.status_code)
    self.assertEqual(10, len(response.get_data()))
    self.assertEqual(big[10:20], response.get_data())


class PreviewDescriptorLifecycleTest(PreviewTestCase):
  def descriptor_count(self):
    return len(os.listdir("/proc/self/fd"))

  @unittest.skipUnless(os.path.isdir("/proc/self/fd"), "requires /proc")
  def test_no_preview_outcome_leaks_a_descriptor(self):
    client = self.owner_client()
    cases = {
      "full": (self.names["image"], {}),
      "partial": (self.names["video"], {"Range": "bytes=2-5"}),
      "unsatisfiable": (self.names["video"], {"Range": "bytes=200-300"}),
      "stale condition": (
        self.names["video"],
        {"Range": "bytes=2-5", "If-Range": '"' + "0" * 64 + '"'},
      ),
      "unknown id": (None, {}),
    }

    for name, (asset, headers) in cases.items():
      with self.subTest(case=name):
        before = self.descriptor_count()
        for _ in range(15):
          if asset is None:
            response = client.get(self.url(asset_id="0" * 64), headers=headers)
          else:
            response = client.get(self.url(asset), headers=headers)
          response.close()
        self.assertEqual(before, self.descriptor_count())

  @unittest.skipUnless(os.path.isdir("/proc/self/fd"), "requires /proc")
  def test_a_refused_media_type_leaks_nothing(self):
    """415 opens the file before it can know the type, so it must release it."""
    row, asset = self.refused_recording()
    client, _ = self.build(FakeQuery(recording=row), principal=self.user())
    url = self.refused_url(asset)

    before = self.descriptor_count()
    for _ in range(20):
      self.assertEqual(415, client.get(url).status_code)

    self.assertEqual(before, self.descriptor_count())

  @unittest.skipUnless(os.path.isdir("/proc/self/fd"), "requires /proc")
  def test_a_head_preview_leaks_nothing(self):
    client = self.owner_client()

    before = self.descriptor_count()
    for _ in range(15):
      client.head(self.url(self.names["image"])).close()

    self.assertEqual(before, self.descriptor_count())

  @unittest.skipUnless(os.path.isdir("/proc/self/fd"), "requires /proc")
  def test_an_abandoned_preview_stream_releases_the_file(self):
    (self.creator / self.names["video"]).write_bytes(b"x" * (4 * 1024 * 1024))
    self.settle()
    client = self.owner_client()

    before = self.descriptor_count()
    for _ in range(15):
      response = client.get(
        self.url(self.names["video"]), headers={"Range": "bytes=0-"}, buffered=False
      )
      next(response.response.__iter__(), None)
      response.close()

    self.assertEqual(before, self.descriptor_count())

  def test_a_refused_media_type_closes_the_file_before_answering(self):
    opened_streams = []

    class WatchingResolver(CountingResolver):
      def open_recording_asset(inner, output_path, recording_id, asset_id):
        opened = super().open_recording_asset(output_path, recording_id, asset_id)
        if opened is not None:
          opened_streams.append(opened.stream)
        return opened

    row, asset = self.refused_recording()
    resolver = WatchingResolver(lambda: str(self.root))
    runtime = FakeRuntime(query=FakeQuery(recording=row), resolver=resolver)
    app = Flask(__name__)
    install_test_auth(app, user=self.user())
    app.register_blueprint(build_library_blueprint(runtime=runtime))

    response = app.test_client().get(self.refused_url(asset))

    self.assertEqual(415, response.status_code)
    self.assertEqual(1, len(opened_streams))
    self.assertTrue(opened_streams[0].closed)


class PreviewMetadataTest(PreviewTestCase):
  """The listing tells a browser what may be previewed."""

  def test_every_listed_asset_declares_whether_it_can_be_previewed(self):
    client = self.owner_client()

    payload = client.get(
      "/api/library/posts/douyin/{}/assets".format(AWEME)
    ).get_json()["data"]

    by_name = {one["name"]: one for one in payload["assets"]}
    self.assertEqual("image", by_name[self.names["image"]]["preview_kind"])
    self.assertEqual("video", by_name[self.names["video"]]["preview_kind"])
    self.assertEqual("audio", by_name[self.names["audio"]]["preview_kind"])

  def test_a_transport_stream_recording_declares_itself_unpreviewable(self):
    row, _ = self.refused_recording()
    client, _ = self.build(FakeQuery(recording=row), principal=self.user())

    payload = client.get(
      "/api/library/recordings/{}/assets".format(BEYOND_SAFE)
    ).get_json()["data"]

    self.assertIsNone(payload["assets"][0]["preview_kind"])

  def test_an_flv_recording_declares_which_renderer_it_needs(self):
    ##
    ## Not "video" - that would send it to a native <video src>, which cannot
    ## decode it.
    ##
    client, _ = self.build(
      FakeQuery(recording=self.recording_row), principal=self.user()
    )

    payload = client.get(
      "/api/library/recordings/{}/assets".format(BEYOND_SAFE)
    ).get_json()["data"]

    self.assertEqual("flv", payload["assets"][0]["preview_kind"])

  def test_the_listing_still_hands_out_no_location_and_no_url(self):
    client = self.owner_client()

    payload = client.get(
      "/api/library/posts/douyin/{}/assets".format(AWEME)
    ).get_json()["data"]

    for asset in payload["assets"]:
      for forbidden in ("path", "save_dir", "preview_url", "download_url", "href"):
        self.assertNotIn(forbidden, asset)


##
## >>========================= flv recordings, in place =========================<<
##
class FlvPreviewTest(PreviewTestCase):
  """The recording container that is actually on disk.

  The live downloader tries FLV first and only falls back to HLS, so most
  recordings are flv files. Until now every one of them could be downloaded and
  none could be watched.

  Nothing about the transport changes to allow this - the bytes travel exactly
  as an mp4's would. What changed is that the media type is admitted, and the
  browser is handed a transmuxer for it.
  """

  def flv_client(self):
    return self.build(
      FakeQuery(recording=self.recording_row), principal=self.user()
    )

  def flv_url(self, action="preview"):
    return "/api/library/recordings/{}/assets/{}/{}".format(
      BEYOND_SAFE,
      asset_id_for("recording", (BEYOND_SAFE,), self.recording_name),
      action,
    )

  def test_an_authorized_flv_recording_is_served_for_rendering(self):
    client, _ = self.flv_client()

    response = client.get(self.flv_url())

    self.assertEqual(200, response.status_code)
    self.assertEqual(BODY, response.get_data())
    self.assertEqual("video/x-flv", response.headers["Content-Type"])

  def test_it_is_not_an_attachment(self):
    client, _ = self.flv_client()

    self.assertIsNone(
      client.get(self.flv_url()).headers.get("Content-Disposition")
    )

  def test_it_carries_the_same_protections_as_every_other_preview(self):
    client, _ = self.flv_client()

    response = client.get(self.flv_url())

    self.assertEqual("nosniff", response.headers["X-Content-Type-Options"])
    self.assertEqual(
      "same-origin", response.headers["Cross-Origin-Resource-Policy"]
    )
    self.assertIn("no-store", response.headers["Cache-Control"])
    self.assertIn("private", response.headers["Cache-Control"])
    self.assertEqual("bytes", response.headers["Accept-Ranges"])

  def test_no_cross_origin_permission_was_granted_to_make_this_work(self):
    ##
    ## The transmuxer fetches same-origin, so none of this is needed. Adding it
    ## would widen who can read a logged-in user's recording.
    ##
    client, _ = self.flv_client()

    headers = client.get(self.flv_url()).headers

    for granted in (
      "Access-Control-Allow-Origin",
      "Access-Control-Allow-Credentials",
      "Access-Control-Expose-Headers",
    ):
      self.assertIsNone(headers.get(granted), granted)

  def test_a_range_of_an_flv_uses_the_existing_transport(self):
    """The seek path. No new range implementation exists for this."""
    client, _ = self.flv_client()

    response = client.get(self.flv_url(), headers={"Range": "bytes=2-5"})

    self.assertEqual(206, response.status_code)
    self.assertEqual(b"2345", response.get_data())
    self.assertEqual("bytes 2-5/10", response.headers["Content-Range"])
    self.assertEqual("4", response.headers["Content-Length"])
    self.assertEqual("video/x-flv", response.headers["Content-Type"])
    self.assertEqual(
      "same-origin", response.headers["Cross-Origin-Resource-Policy"]
    )

  def test_an_open_ended_range_of_an_flv_runs_to_the_end(self):
    client, _ = self.flv_client()

    response = client.get(self.flv_url(), headers={"Range": "bytes=6-"})

    self.assertEqual(206, response.status_code)
    self.assertEqual(b"6789", response.get_data())

  def test_an_unsatisfiable_flv_range_reports_the_real_length(self):
    client, _ = self.flv_client()

    response = client.get(self.flv_url(), headers={"Range": "bytes=200-300"})

    self.assertEqual(416, response.status_code)
    self.assertEqual("bytes */10", response.headers["Content-Range"])

  def test_head_describes_the_flv_without_a_body(self):
    client, _ = self.flv_client()

    response = client.head(self.flv_url())

    self.assertEqual(200, response.status_code)
    self.assertEqual("10", response.headers["Content-Length"])
    self.assertEqual("video/x-flv", response.headers["Content-Type"])
    self.assertEqual("bytes", response.headers["Accept-Ranges"])
    self.assertEqual(
      "same-origin", response.headers["Cross-Origin-Resource-Policy"]
    )
    self.assertEqual("nosniff", response.headers["X-Content-Type-Options"])
    self.assertIsNotNone(response.headers.get("ETag"))
    self.assertEqual(b"", response.get_data())

  def test_a_matching_condition_resumes_an_flv(self):
    ##
    ## Proved once here rather than re-deriving Phase 10C's whole suite: the
    ## point is that flv goes through the same code, not that the code works.
    ##
    client, _ = self.flv_client()
    tag = client.get(self.flv_url()).headers["ETag"]

    response = client.get(
      self.flv_url(), headers={"Range": "bytes=6-", "If-Range": tag}
    )

    self.assertEqual(206, response.status_code)
    self.assertEqual(b"6789", response.get_data())

  def test_a_stale_condition_sends_the_whole_flv(self):
    client, _ = self.flv_client()

    response = client.get(
      self.flv_url(),
      headers={"Range": "bytes=6-", "If-Range": '"' + "0" * 64 + '"'},
    )

    self.assertEqual(200, response.status_code)
    self.assertEqual(BODY, response.get_data())

  def test_the_flv_download_route_is_unchanged(self):
    client, _ = self.flv_client()

    response = client.get(self.flv_url(action="download"))

    self.assertEqual(200, response.status_code)
    self.assertTrue(
      response.headers["Content-Disposition"].startswith("attachment")
    )
    self.assertIsNone(response.headers.get("Cross-Origin-Resource-Policy"))

  ##
  ## >>------------------- authorization, again and unchanged -------------------<<
  ##
  def test_an_anonymous_flv_preview_never_reaches_the_disk(self):
    client, resolver = self.build(FakeQuery(recording=self.recording_row))

    response = client.get(self.flv_url())

    self.assertEqual(401, response.status_code)
    self.assertEqual([], resolver.calls)

  def test_an_anonymous_ranged_flv_preview_never_reaches_the_disk(self):
    ##
    ## The shape the transmuxer actually sends when it seeks.
    ##
    client, resolver = self.build(FakeQuery(recording=self.recording_row))

    response = client.get(self.flv_url(), headers={"Range": "bytes=0-3"})

    self.assertEqual(401, response.status_code)
    self.assertEqual([], resolver.calls)

  def test_a_cross_owner_flv_preview_never_reaches_the_disk(self):
    client, resolver = self.build(FakeQuery(recording=None), principal=self.user(99))

    response = client.get(self.flv_url())

    self.assertEqual(404, response.status_code)
    self.assertEqual([], resolver.calls)
    self.assertNotIn(BODY, response.get_data())

  def test_an_unavailable_backend_refuses_an_flv_preview_without_the_disk(self):
    client, resolver = self.build(
      FakeQuery(recording=self.recording_row),
      principal=self.user(),
      unavailable=LibraryUnavailable("数据库暂时不可用"),
    )

    response = client.get(self.flv_url())

    self.assertEqual(503, response.status_code)
    self.assertEqual([], resolver.calls)

  def test_an_unknown_flv_asset_id_is_missing_rather_than_unsupported(self):
    client, _ = self.flv_client()

    response = client.get(
      "/api/library/recordings/{}/assets/{}/preview".format(
        BEYOND_SAFE, "0" * 64
      )
    )

    self.assertEqual(404, response.status_code)

  def test_an_flv_asset_id_from_another_recording_previews_nothing(self):
    client, _ = self.flv_client()

    response = client.get(
      "/api/library/recordings/{}/assets/{}/preview".format(
        BEYOND_SAFE, asset_id_for("recording", (7,), self.recording_name)
      )
    )

    self.assertEqual(404, response.status_code)

  def test_the_metadata_declares_the_flv_renderable(self):
    client, _ = self.flv_client()

    payload = client.get(
      "/api/library/recordings/{}/assets".format(BEYOND_SAFE)
    ).get_json()["data"]

    self.assertEqual("flv", payload["assets"][0]["preview_kind"])


class TransportStreamStillDownloadOnlyTest(PreviewTestCase):
  """FLV moved. TS deliberately did not."""

  def ts_setup(self):
    target = self.creator / "live.ts"
    target.write_bytes(BODY)
    row = dict(self.recording_row, output_path=str(target))
    client, _ = self.build(FakeQuery(recording=row), principal=self.user())
    return client, asset_id_for("recording", (BEYOND_SAFE,), "live.ts")

  def test_a_transport_stream_preview_is_still_refused(self):
    client, asset = self.ts_setup()

    response = client.get(
      "/api/library/recordings/{}/assets/{}/preview".format(BEYOND_SAFE, asset)
    )

    self.assertEqual(415, response.status_code)
    self.assertNotIn(BODY, response.get_data())

  def test_a_ranged_transport_stream_preview_is_still_refused(self):
    client, asset = self.ts_setup()

    response = client.get(
      "/api/library/recordings/{}/assets/{}/preview".format(BEYOND_SAFE, asset),
      headers={"Range": "bytes=0-3"},
    )

    self.assertEqual(415, response.status_code)

  def test_a_transport_stream_still_downloads(self):
    client, asset = self.ts_setup()

    response = client.get(
      "/api/library/recordings/{}/assets/{}/download".format(BEYOND_SAFE, asset)
    )

    self.assertEqual(200, response.status_code)
    self.assertEqual(BODY, response.get_data())
    self.assertTrue(
      response.headers["Content-Disposition"].startswith("attachment")
    )

  def test_the_metadata_still_declares_it_unrenderable(self):
    client, _ = self.ts_setup()

    payload = client.get(
      "/api/library/recordings/{}/assets".format(BEYOND_SAFE)
    ).get_json()["data"]

    self.assertIsNone(payload["assets"][0]["preview_kind"])
