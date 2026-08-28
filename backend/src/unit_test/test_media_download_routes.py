##<<Base>>
import json
import os
import tempfile
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
POST_BYTES = b"POST-BYTES"
RECORDING_BYTES = b"RECORDING-BYTES"

##
## The identity a JavaScript number cannot hold. Used to prove the url survives
## a recording id that a double would round.
##
BEYOND_SAFE = 9007199254740993


class CountingResolver:
  """A real resolver that records whether the filesystem was reached.

  Wrapping rather than faking: the security claim is that an unauthorized
  request never touches the disk, and only a resolver that would actually touch
  it can witness that.
  """

  def __init__(self, root_provider):
    self._inner = MediaAssetResolver(root_provider)
    self.calls = []

  def post_assets(self, save_dir, platform, aweme_id):
    self.calls.append(("post_assets", save_dir, platform, aweme_id))
    return self._inner.post_assets(save_dir, platform, aweme_id)

  def recording_asset(self, output_path, recording_id):
    self.calls.append(("recording_asset", output_path, recording_id))
    return self._inner.recording_asset(output_path, recording_id)

  def open_post_asset(self, save_dir, platform, aweme_id, asset_id):
    self.calls.append(("open_post", save_dir, platform, aweme_id, asset_id))
    return self._inner.open_post_asset(save_dir, platform, aweme_id, asset_id)

  def open_recording_asset(self, output_path, recording_id, asset_id):
    self.calls.append(("open_recording", output_path, recording_id, asset_id))
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
    self.calls.append(("post", platform, aweme_id))
    self._maybe_fail()
    return self._post

  def post_for_user(self, app_user_id, platform, aweme_id):
    self.calls.append(("post_for_user", app_user_id, platform, aweme_id))
    self._maybe_fail()
    return self._post

  def recording(self, recording_id):
    self.calls.append(("recording", recording_id))
    self._maybe_fail()
    return self._recording

  def recording_for_user(self, app_user_id, recording_id):
    self.calls.append(("recording_for_user", app_user_id, recording_id))
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


class DownloadTestCase(unittest.TestCase):
  """A real download root with one post file and one recording in it."""

  def setUp(self):
    self._tmp = tempfile.TemporaryDirectory()
    self.base = Path(self._tmp.name)
    self.root = self.base / "downloads"
    self.creator = self.root / "creator"
    self.creator.mkdir(parents=True)
    self.addCleanup(self._tmp.cleanup)

    self.secret = self.base / "secret.txt"
    self.secret.write_bytes(b"SECRET-OUTSIDE-ROOT")

    self.post_name = "20260824_{}.mp4".format(AWEME)
    (self.creator / self.post_name).write_bytes(POST_BYTES)

    self.recording_name = "live.flv"
    self.recording_path = self.creator / self.recording_name
    self.recording_path.write_bytes(RECORDING_BYTES)

    self.post_row = {
      "platform": "douyin",
      "aweme_id": AWEME,
      "save_dir": str(self.creator),
    }
    self.recording_row = {
      "recording_id": 7,
      "app_user_id": 3,
      "output_path": str(self.recording_path),
    }

  ##
  ## >>------------------------- harness -------------------------<<
  ##
  def build(self, query=None, principal=None, unavailable=None, resolver=None):
    resolver = resolver or CountingResolver(lambda: str(self.root))
    runtime = FakeRuntime(query=query, resolver=resolver, unavailable=unavailable)
    app = Flask(__name__)
    if principal is None:
      install_anonymous(app)
    else:
      install_test_auth(app, user=principal)
    app.register_blueprint(build_library_blueprint(runtime=runtime))
    return app.test_client(), resolver

  def post_asset_id(self, aweme_id=AWEME, name=None):
    return asset_id_for("post", ("douyin", aweme_id), name or self.post_name)

  def recording_asset_id(self, recording_id=7, name=None):
    return asset_id_for(
      "recording", (recording_id,), name or self.recording_name
    )

  def post_url(self, asset_id=None, platform="douyin", aweme_id=AWEME):
    return "/api/library/posts/{}/{}/assets/{}/download".format(
      platform, aweme_id, asset_id or self.post_asset_id()
    )

  def recording_url(self, asset_id=None, recording_id=7):
    return "/api/library/recordings/{}/assets/{}/download".format(
      recording_id, asset_id or self.recording_asset_id()
    )

  def user(self, user_id=3, role=ROLE_USER):
    return AuthenticatedUser(user_id, "u{}".format(user_id), role)


##
## >>================= authorization strictly before filesystem =================<<
##
class AuthorizationBeforeFilesystemTest(DownloadTestCase):
  """The first invariant: a refused request never reaches the disk.

  Not merely "is refused" - never touches it. A download route that authorized
  after looking could be timed to learn which files exist on the host, which is
  the probe the whole ordering exists to prevent.
  """

  def test_an_anonymous_post_download_is_refused_without_a_disk_read(self):
    query = FakeQuery(post=self.post_row)
    client, resolver = self.build(query)

    response = client.get(self.post_url())

    self.assertEqual(401, response.status_code)
    self.assertEqual([], resolver.calls)
    ##
    ## And the database was not consulted either.
    ##
    self.assertEqual([], query.calls)

  def test_an_anonymous_recording_download_is_refused_without_a_disk_read(self):
    query = FakeQuery(recording=self.recording_row)
    client, resolver = self.build(query)

    response = client.get(self.recording_url())

    self.assertEqual(401, response.status_code)
    self.assertEqual([], resolver.calls)

  def test_a_cross_owner_post_download_is_refused_without_a_disk_read(self):
    ##
    ## Bob holds an asset id for Alice's post - it was in a listing, or he
    ## computed it, since the algorithm is public and deterministic. It buys
    ## him nothing, and does not even cause the file to be looked at.
    ##
    query = FakeQuery(post=None)
    client, resolver = self.build(query, principal=self.user(99))

    response = client.get(self.post_url())

    self.assertEqual(404, response.status_code)
    self.assertEqual([], resolver.calls)
    self.assertEqual(("post_for_user", 99, "douyin", AWEME), query.calls[0])

  def test_a_cross_owner_recording_download_is_refused_without_a_disk_read(self):
    query = FakeQuery(recording=None)
    client, resolver = self.build(query, principal=self.user(99))

    response = client.get(self.recording_url())

    self.assertEqual(404, response.status_code)
    self.assertEqual([], resolver.calls)
    self.assertEqual(("recording_for_user", 99, 7), query.calls[0])

  def test_an_unavailable_auth_backend_refuses_without_a_disk_read(self):
    client, resolver = self.build(
      FakeQuery(post=self.post_row),
      principal=self.user(3),
      unavailable=LibraryUnavailable("数据库暂时不可用"),
    )

    response = client.get(self.post_url())

    self.assertEqual(503, response.status_code)
    self.assertEqual([], resolver.calls)

  def test_a_legacy_unowned_post_is_invisible_to_a_user_and_open_to_an_admin(self):
    ##
    ## The user's scoped lookup finds nothing and stops there.
    ##
    client, resolver = self.build(FakeQuery(post=None), principal=self.user(3))
    self.assertEqual(404, client.get(self.post_url()).status_code)
    self.assertEqual([], resolver.calls)

    ##
    ## The admin's global lookup finds it, and the download proceeds.
    ##
    client, resolver = self.build(
      FakeQuery(post=self.post_row), principal=self.user(1, ROLE_ADMIN)
    )
    response = client.get(self.post_url())
    self.assertEqual(200, response.status_code)
    self.assertEqual(POST_BYTES, response.get_data())

  def test_a_legacy_unowned_recording_is_invisible_to_a_user_and_open_to_an_admin(self):
    unowned = dict(self.recording_row, app_user_id=None)

    client, resolver = self.build(FakeQuery(recording=None), principal=self.user(3))
    self.assertEqual(404, client.get(self.recording_url()).status_code)
    self.assertEqual([], resolver.calls)

    client, _ = self.build(
      FakeQuery(recording=unowned), principal=self.user(1, ROLE_ADMIN)
    )
    response = client.get(self.recording_url())
    self.assertEqual(200, response.status_code)
    self.assertEqual(RECORDING_BYTES, response.get_data())


##
## >>=========================== HEAD is not a side door ===========================<<
##
class HeadRequestTest(DownloadTestCase):
  """Flask answers HEAD on every GET route, so it must be checked.

  A HEAD that skipped authorization would be an existence oracle: no body, but
  a 200 or a 404 is the whole answer somebody probing for another user's files
  is after.
  """

  def test_an_anonymous_head_is_refused_like_a_get(self):
    client, resolver = self.build(FakeQuery(post=self.post_row))

    response = client.head(self.post_url())

    self.assertEqual(401, response.status_code)
    self.assertEqual([], resolver.calls)

  def test_a_cross_owner_head_cannot_distinguish_a_real_post(self):
    ##
    ## The same 404 a nonexistent post gives, and no disk read either way.
    ##
    client, resolver = self.build(FakeQuery(post=None), principal=self.user(99))

    real = client.head(self.post_url())
    invented = client.head(self.post_url(aweme_id="0000000000000000000"))

    self.assertEqual(404, real.status_code)
    self.assertEqual(invented.status_code, real.status_code)
    self.assertEqual([], resolver.calls)

  def test_an_authorized_head_reports_the_same_headers_with_no_body(self):
    client, _ = self.build(FakeQuery(post=self.post_row), principal=self.user(3))

    response = client.head(self.post_url())

    self.assertEqual(200, response.status_code)
    self.assertEqual("video/mp4", response.headers["Content-Type"])
    self.assertEqual(b"", response.get_data())

  def test_an_anonymous_recording_head_is_refused(self):
    client, resolver = self.build(FakeQuery(recording=self.recording_row))

    self.assertEqual(401, client.head(self.recording_url()).status_code)
    self.assertEqual([], resolver.calls)


##
## >>============================ delivering the bytes ============================<<
##
class SuccessfulDeliveryTest(DownloadTestCase):
  def test_an_owned_post_asset_downloads_its_exact_bytes(self):
    client, _ = self.build(FakeQuery(post=self.post_row), principal=self.user(3))

    response = client.get(self.post_url())

    self.assertEqual(200, response.status_code)
    self.assertEqual(POST_BYTES, response.get_data())
    self.assertEqual("video/mp4", response.headers["Content-Type"])

  def test_an_owned_recording_downloads_its_exact_bytes(self):
    client, _ = self.build(
      FakeQuery(recording=self.recording_row), principal=self.user(3)
    )

    response = client.get(self.recording_url())

    self.assertEqual(200, response.status_code)
    self.assertEqual(RECORDING_BYTES, response.get_data())
    self.assertEqual("video/x-flv", response.headers["Content-Type"])

  def test_a_transport_stream_recording_downloads_with_its_own_type(self):
    target = self.creator / "live.ts"
    target.write_bytes(b"TS-BYTES")
    row = dict(self.recording_row, output_path=str(target))
    client, _ = self.build(FakeQuery(recording=row), principal=self.user(3))

    response = client.get(
      self.recording_url(asset_id=self.recording_asset_id(name="live.ts"))
    )

    self.assertEqual(200, response.status_code)
    self.assertEqual(b"TS-BYTES", response.get_data())
    self.assertEqual("video/mp2t", response.headers["Content-Type"])

  def test_the_response_is_always_an_attachment(self):
    ##
    ## Images included. Nothing stored here is rendered in the browser in this
    ## phase, so no stored file can become something the page displays or runs.
    ##
    ##
    ## The two-digit tail the downloader actually writes - `_\d{2}\.jpg` is
    ## what marks a file as one of a post's images.
    ##
    image = self.creator / "20260824_{}_01.jpg".format(AWEME)
    image.write_bytes(b"JPEG-BYTES")
    client, _ = self.build(FakeQuery(post=self.post_row), principal=self.user(3))

    response = client.get(
      self.post_url(asset_id=self.post_asset_id(name=image.name))
    )

    self.assertEqual(200, response.status_code)
    self.assertEqual("image/jpeg", response.headers["Content-Type"])
    self.assertTrue(
      response.headers["Content-Disposition"].startswith("attachment")
    )
    self.assertNotIn("inline", response.headers["Content-Disposition"])

  def test_a_chinese_file_name_survives_the_header(self):
    name = "{}_我的视频.mp4".format(AWEME)
    (self.creator / name).write_bytes(b"CN-BYTES")
    client, _ = self.build(FakeQuery(post=self.post_row), principal=self.user(3))

    response = client.get(self.post_url(asset_id=self.post_asset_id(name=name)))

    self.assertEqual(200, response.status_code)
    disposition = response.headers["Content-Disposition"]
    ##
    ## Werkzeug emits the RFC 5987 form for a name that is not latin-1. The
    ## point is not the exact spelling but that the name arrives intact and the
    ## header is well formed.
    ##
    self.assertIn("filename*=UTF-8''", disposition)
    self.assertIn("%E6%88%91", disposition)
    self.assertNotIn("\n", disposition)
    self.assertNotIn("\r", disposition)

  def test_a_name_carrying_quotes_cannot_break_the_header(self):
    ##
    ## The framework builds this header. A hand-formatted one is where a name
    ## containing a quote or a newline becomes header injection.
    ##
    name = '{}_a"b.mp4'.format(AWEME)
    try:
      (self.creator / name).write_bytes(b"Q-BYTES")
    except OSError:
      self.skipTest("filesystem refuses this name")
    client, _ = self.build(FakeQuery(post=self.post_row), principal=self.user(3))

    response = client.get(self.post_url(asset_id=self.post_asset_id(name=name)))

    self.assertEqual(200, response.status_code)
    disposition = response.headers["Content-Disposition"]
    self.assertNotIn("\r", disposition)
    self.assertNotIn("\n", disposition)
    ##
    ## One header, not two.
    ##
    self.assertEqual(1, len(response.headers.getlist("Content-Disposition")))

  def test_the_length_comes_from_the_opened_file_not_the_earlier_listing(self):
    """A file that grew between discovery and delivery is sent whole.

    Content-Length has to describe the bytes actually being written. Reusing a
    size remembered from a metadata call would truncate the response or leave
    the client waiting for bytes that never come.
    """
    client, _ = self.build(FakeQuery(post=self.post_row), principal=self.user(3))
    grown = POST_BYTES + b"-MORE-BYTES-ADDED-LATER"
    (self.creator / self.post_name).write_bytes(grown)

    response = client.get(self.post_url())

    self.assertEqual(200, response.status_code)
    self.assertEqual(str(len(grown)), response.headers["Content-Length"])
    self.assertEqual(grown, response.get_data())

  def test_private_media_is_not_cacheable_and_not_sniffable(self):
    client, _ = self.build(FakeQuery(post=self.post_row), principal=self.user(3))

    response = client.get(self.post_url())

    cache = response.headers["Cache-Control"]
    self.assertIn("private", cache)
    self.assertIn("no-store", cache)
    self.assertEqual("nosniff", response.headers["X-Content-Type-Options"])

  def test_no_entity_tag_and_no_range_advertisement(self):
    ##
    ## An ETag would mean hashing the file, and the asset id is a name rather
    ## than a content digest. Range support is a later phase with its own
    ## design; advertising it now would invite requests this cannot answer.
    ##
    client, _ = self.build(FakeQuery(post=self.post_row), principal=self.user(3))

    response = client.get(self.post_url())

    self.assertIsNone(response.headers.get("ETag"))
    self.assertNotEqual("bytes", response.headers.get("Accept-Ranges"))

  def test_a_recording_identity_beyond_the_safe_range_downloads_its_own_file(self):
    row = dict(self.recording_row, recording_id=BEYOND_SAFE)
    query = FakeQuery(recording=row)
    client, _ = self.build(query, principal=self.user(3))

    response = client.get(
      self.recording_url(
        asset_id=self.recording_asset_id(recording_id=BEYOND_SAFE),
        recording_id=BEYOND_SAFE,
      )
    )

    self.assertEqual(200, response.status_code)
    self.assertEqual(RECORDING_BYTES, response.get_data())
    ##
    ## The url carried the identity exactly, and Flask handed the query layer a
    ## Python int of the same value - no double in between.
    ##
    self.assertEqual(("recording_for_user", 3, BEYOND_SAFE), query.calls[0])
    self.assertIs(int, type(query.calls[0][2]))

  def test_the_neighbouring_rounded_identity_is_a_different_recording(self):
    ##
    ## 9007199254740992 is what 9007199254740993 becomes if it is ever parsed
    ## as a double. It must not open the same file.
    ##
    query = FakeQuery(recording=None)
    client, resolver = self.build(query, principal=self.user(3))

    response = client.get(
      self.recording_url(
        asset_id=self.recording_asset_id(recording_id=BEYOND_SAFE),
        recording_id=9007199254740992,
      )
    )

    self.assertEqual(404, response.status_code)
    self.assertEqual([], resolver.calls)


##
## >>========================= the id is not a capability =========================<<
##
class AssetIdIsNotACapabilityTest(DownloadTestCase):
  def test_an_invented_asset_id_downloads_nothing(self):
    client, _ = self.build(FakeQuery(post=self.post_row), principal=self.user(3))

    response = client.get(self.post_url(asset_id="0" * 64))

    self.assertEqual(404, response.status_code)

  def test_a_malformed_asset_id_answers_exactly_like_an_unknown_one(self):
    ##
    ## Telling the two apart would confirm the id format, and confirm that a
    ## well-formed id had been checked against something.
    ##
    client, _ = self.build(FakeQuery(post=self.post_row), principal=self.user(3))

    unknown = client.get(self.post_url(asset_id="0" * 64))
    malformed = client.get(self.post_url(asset_id="not-an-id"))

    self.assertEqual(404, unknown.status_code)
    self.assertEqual(unknown.status_code, malformed.status_code)
    self.assertEqual(
      json.loads(unknown.get_data(as_text=True))["message"],
      json.loads(malformed.get_data(as_text=True))["message"],
    )

  def test_an_asset_id_issued_for_another_post_downloads_nothing(self):
    """Same file, same name, different parent - and it must not redeem.

    This is the property that stops an id from being a bearer token: it is
    matched against the discovery of the resource named in the url, so it only
    means anything in the one place it was issued.
    """
    other_aweme = "1111111111111111111"
    client, _ = self.build(FakeQuery(post=self.post_row), principal=self.user(3))

    response = client.get(
      self.post_url(asset_id=asset_id_for("post", ("douyin", other_aweme), self.post_name))
    )

    self.assertEqual(404, response.status_code)

  def test_a_recording_asset_id_does_not_redeem_on_a_post_route(self):
    client, _ = self.build(FakeQuery(post=self.post_row), principal=self.user(3))

    response = client.get(self.post_url(asset_id=self.recording_asset_id()))

    self.assertEqual(404, response.status_code)

  def test_an_id_from_another_recording_downloads_nothing(self):
    client, _ = self.build(
      FakeQuery(recording=self.recording_row), principal=self.user(3)
    )

    response = client.get(
      self.recording_url(asset_id=self.recording_asset_id(recording_id=999))
    )

    self.assertEqual(404, response.status_code)

  def test_an_id_listed_before_the_file_was_deleted_downloads_nothing(self):
    """The proof that nothing is cached between the two calls.

    The metadata endpoint issued this id and it was valid. The only thing that
    changed is the disk, and that is enough.
    """
    client, _ = self.build(FakeQuery(post=self.post_row), principal=self.user(3))

    listed = client.get(
      "/api/library/posts/douyin/{}/assets".format(AWEME)
    )
    self.assertEqual(200, listed.status_code)
    asset_id = json.loads(listed.get_data(as_text=True))["data"]["assets"][0]["asset_id"]

    (self.creator / self.post_name).unlink()

    response = client.get(self.post_url(asset_id=asset_id))

    self.assertEqual(404, response.status_code)


##
## >>========================= what must never be revealed =========================<<
##
class ResponsePrivacyTest(DownloadTestCase):
  def assert_says_nothing_about_the_filesystem(self, response):
    """No part of this response may describe where files live."""
    haystack = "\n".join(
      [
        response.get_data(as_text=True)[:4096],
        "\n".join("{}: {}".format(k, v) for k, v in response.headers.items()),
      ]
    )
    for secret in (str(self.root), str(self.base), str(self.creator), "secret.txt"):
      self.assertNotIn(secret, haystack)
    for leak in ("Errno", "errno", "Traceback", "symlink", "save_dir", "output_path"):
      self.assertNotIn(leak, haystack)

  def test_a_successful_download_reveals_no_path(self):
    client, _ = self.build(FakeQuery(post=self.post_row), principal=self.user(3))

    response = client.get(self.post_url())

    self.assertEqual(200, response.status_code)
    self.assert_says_nothing_about_the_filesystem(response)

  def test_a_refusal_reveals_no_path(self):
    client, _ = self.build(FakeQuery(post=self.post_row), principal=self.user(3))

    self.assert_says_nothing_about_the_filesystem(
      client.get(self.post_url(asset_id="0" * 64))
    )

  def test_an_admin_download_reveals_no_path_either(self):
    ##
    ## Being an admin is permission to reach every resource, not permission to
    ## learn the host's directory layout through an api that never offered it.
    ##
    client, _ = self.build(
      FakeQuery(post=self.post_row), principal=self.user(1, ROLE_ADMIN)
    )

    self.assert_says_nothing_about_the_filesystem(client.get(self.post_url()))

  def test_an_escape_attempt_reveals_neither_bytes_nor_reason(self):
    row = dict(self.post_row, save_dir=str(self.base / "elsewhere"))
    outside = self.base / "elsewhere"
    outside.mkdir()
    (outside / self.post_name).write_bytes(b"SECRET-OUTSIDE-ROOT")
    client, _ = self.build(FakeQuery(post=row), principal=self.user(3))

    response = client.get(self.post_url())

    self.assertEqual(404, response.status_code)
    self.assertNotIn(b"SECRET", response.get_data())
    self.assert_says_nothing_about_the_filesystem(response)

  def test_a_symlinked_asset_delivers_no_target_bytes(self):
    link_name = "{}_link.mp4".format(AWEME)
    (self.creator / link_name).symlink_to(self.secret)
    client, _ = self.build(FakeQuery(post=self.post_row), principal=self.user(3))

    response = client.get(
      self.post_url(asset_id=self.post_asset_id(name=link_name))
    )

    self.assertEqual(404, response.status_code)
    self.assertNotIn(b"SECRET", response.get_data())

  def test_every_failure_is_json_not_an_html_error_page(self):
    client, _ = self.build(FakeQuery(post=None), principal=self.user(3))

    response = client.get(self.post_url())

    self.assertIn("application/json", response.headers["Content-Type"])
    body = json.loads(response.get_data(as_text=True))
    self.assertEqual("error", body["status"])
    self.assertNotIn("<html", response.get_data(as_text=True).lower())


##
## >>===================== streaming, and letting go of the file =====================<<
##
class StreamingTest(DownloadTestCase):
  """A recording can be tens of gigabytes. It is never a bytes object."""

  def raw_response(self, query=None, principal=None):
    """The Response the view returned, before any client wrapped it.

    The test client re-wraps a streamed body in a ``ClosingIterator`` and
    clears ``direct_passthrough``, so the property has to be read where it is
    actually set - on the application's own response object.
    """
    resolver = CountingResolver(lambda: str(self.root))
    runtime = FakeRuntime(query=query, resolver=resolver)
    app = Flask(__name__)
    install_test_auth(app, user=principal)
    app.register_blueprint(build_library_blueprint(runtime=runtime))

    with app.test_request_context(self.post_url()):
      return app.full_dispatch_request()

  def test_the_response_hands_the_file_to_the_server_rather_than_buffering_it(self):
    ##
    ## ``direct_passthrough`` is Werkzeug undertaking not to materialise the
    ## body: the WSGI server pulls chunks from the file itself. Without it a
    ## multi-gigabyte recording would be assembled in this process first.
    ##
    response = self.raw_response(
      query=FakeQuery(post=self.post_row), principal=self.user(3)
    )
    self.addCleanup(response.close)

    self.assertEqual(200, response.status_code)
    self.assertTrue(response.direct_passthrough)
    self.assertFalse(isinstance(response.response, (bytes, bytearray, str)))
    self.assertTrue(hasattr(response.response, "__iter__"))

  def test_the_body_is_never_read_whole_before_being_sent(self):
    """The file handed to the response is still at its start.

    A file that had been read to the end - the ``data = f.read()`` this phase
    forbids - would have a position at its size.
    """
    response = self.raw_response(
      query=FakeQuery(post=self.post_row), principal=self.user(3)
    )
    self.addCleanup(response.close)

    underlying = getattr(response.response, "file", None)
    if underlying is None:
      self.skipTest("response wrapper does not expose the file object")
    self.assertEqual(0, underlying.tell())

  def test_the_streamed_body_is_a_lazy_iterator_through_the_client_too(self):
    ##
    ## What a caller can still observe after the test client has wrapped it:
    ## the body is something to be iterated, not a bytes object already built.
    ##
    client, _ = self.build(FakeQuery(post=self.post_row), principal=self.user(3))

    response = client.get(self.post_url(), buffered=False)
    self.addCleanup(response.close)

    self.assertFalse(isinstance(response.response, (bytes, bytearray, str)))
    self.assertTrue(hasattr(response.response, "__iter__"))

  def test_a_large_file_streams_without_being_held_in_memory(self):
    ##
    ## Eight megabytes: far more than one chunk, small enough to write in a
    ## test. The point is that it arrives correctly through the wrapper.
    ##
    big = b"0123456789abcdef" * 512 * 1024
    (self.creator / self.post_name).write_bytes(big)
    client, _ = self.build(FakeQuery(post=self.post_row), principal=self.user(3))

    response = client.get(self.post_url())

    self.assertEqual(200, response.status_code)
    self.assertEqual(len(big), int(response.headers["Content-Length"]))
    self.assertEqual(big, response.get_data())


class DescriptorLifecycleTest(DownloadTestCase):
  """A server that runs for weeks cannot leak a descriptor per download."""

  def descriptor_count(self):
    return len(os.listdir("/proc/self/fd"))

  @unittest.skipUnless(os.path.isdir("/proc/self/fd"), "requires /proc")
  def test_a_completed_download_releases_the_file(self):
    client, _ = self.build(FakeQuery(post=self.post_row), principal=self.user(3))

    before = self.descriptor_count()
    for _ in range(20):
      response = client.get(self.post_url())
      self.assertEqual(200, response.status_code)
      response.close()

    self.assertEqual(before, self.descriptor_count())

  @unittest.skipUnless(os.path.isdir("/proc/self/fd"), "requires /proc")
  def test_a_client_that_hangs_up_early_still_releases_the_file(self):
    ##
    ## The common case in production: somebody starts a large download and
    ## cancels it. The descriptor must go with the response, not with the
    ## bytes that were never read.
    ##
    big = b"x" * (4 * 1024 * 1024)
    (self.creator / self.post_name).write_bytes(big)
    client, _ = self.build(FakeQuery(post=self.post_row), principal=self.user(3))

    before = self.descriptor_count()
    for _ in range(20):
      response = client.get(self.post_url(), buffered=False)
      ##
      ## One chunk read, then abandoned.
      ##
      next(response.response.__iter__(), None)
      response.close()

    self.assertEqual(before, self.descriptor_count())

  @unittest.skipUnless(os.path.isdir("/proc/self/fd"), "requires /proc")
  def test_a_refused_download_releases_nothing_because_it_opened_nothing(self):
    client, _ = self.build(FakeQuery(post=self.post_row), principal=self.user(3))

    before = self.descriptor_count()
    for _ in range(20):
      self.assertEqual(404, client.get(self.post_url(asset_id="0" * 64)).status_code)

    self.assertEqual(before, self.descriptor_count())

  def test_the_opened_file_is_closed_when_the_response_closes(self):
    """Asserted on the object itself, not inferred from a descriptor count."""
    opened_files = []

    class WatchingResolver(CountingResolver):
      def open_post_asset(inner, save_dir, platform, aweme_id, asset_id):
        opened = super().open_post_asset(save_dir, platform, aweme_id, asset_id)
        if opened is not None:
          opened_files.append(opened.stream)
        return opened

    client, _ = self.build(
      FakeQuery(post=self.post_row),
      principal=self.user(3),
      resolver=WatchingResolver(lambda: str(self.root)),
    )

    response = client.get(self.post_url())
    self.assertEqual(200, response.status_code)
    response.close()

    self.assertEqual(1, len(opened_files))
    self.assertTrue(opened_files[0].closed)
