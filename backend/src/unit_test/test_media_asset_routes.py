##<<Base>>
import json
import unittest

##<<Extension>>
from flask import Flask

##<<Third-part>>
from backend.src.auth.context import RequestAuthContext
from backend.src.auth.roles import ROLE_ADMIN, ROLE_USER
from backend.src.auth.service import AuthenticatedUser
from backend.src.service.media_asset import AssetDiscovery, MediaAsset, StorageState
from backend.src.unit_test.auth_context import install_test_auth
from backend.src.web.library_routes import LibraryUnavailable, build_library_blueprint


AWEME = "7657271784144009946"

POST_ROW = {
  "platform": "douyin",
  "aweme_id": AWEME,
  "save_dir": "/downloads/creator",
  "media_count": 1,
  "saved_count": 1,
}

RECORDING_ROW = {
  "recording_id": 7,
  "app_user_id": 3,
  "output_path": "/downloads/creator/live.flv",
}


class RecordingResolver:
  """Records whether it was consulted, and what with."""

  def __init__(self, discovery=None):
    self.calls = []
    self._discovery = discovery or AssetDiscovery(
      storage_state=StorageState.AVAILABLE,
      assets=(
        MediaAsset(
          asset_id="a" * 64,
          kind="video",
          name="20260824_{}.mp4".format(AWEME),
          size_bytes=100,
          media_type="video/mp4",
        ),
      ),
    )

  def post_assets(self, save_dir, platform, aweme_id):
    self.calls.append(("post", save_dir, platform, aweme_id))
    return self._discovery

  def recording_asset(self, output_path, recording_id):
    self.calls.append(("recording", output_path, recording_id))
    return self._discovery


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


def auth_context_for(user_id, role):
  return AuthenticatedUser(user_id, "u{}".format(user_id), role)


def install_anonymous(app):
  """No principal at all - what an unauthenticated browser looks like."""
  from flask import g

  @app.before_request
  def anonymous_request():
    g.auth_context = RequestAuthContext.anonymous()


def build(query=None, resolver=None, unavailable=None, principal=None):
  resolver = resolver if resolver is not None else RecordingResolver()
  runtime = FakeRuntime(query=query, resolver=resolver, unavailable=unavailable)
  app = Flask(__name__)
  if principal is None:
    install_anonymous(app)
  else:
    install_test_auth(app, user=principal)
  app.register_blueprint(build_library_blueprint(runtime=runtime))
  return app.test_client(), resolver


def body_of(response):
  return json.loads(response.get_data(as_text=True))


def post_url(platform="douyin", aweme_id=AWEME):
  return "/api/library/posts/{}/{}/assets".format(platform, aweme_id)


RECORDING_URL = "/api/library/recordings/7/assets"


class TestPostAssetScope(unittest.TestCase):
  def test_an_owner_sees_their_own_posts_assets(self):
    query = FakeQuery(post=POST_ROW)
    client, resolver = build(query, principal=auth_context_for(3, ROLE_USER))

    response = client.get(post_url())

    self.assertEqual(200, response.status_code)
    payload = body_of(response)["data"]
    self.assertEqual("available", payload["storage_state"])
    self.assertEqual(1, len(payload["assets"]))
    self.assertEqual(("post_for_user", 3, "douyin", AWEME), query.calls[0])

  def test_another_user_is_told_it_does_not_exist(self):
    ##
    ## Scoped lookup finds nothing, so the answer is the same one an unknown
    ## post gets. Anything else would confirm the post exists.
    ##
    query = FakeQuery(post=None)
    client, _ = build(query, principal=auth_context_for(4, ROLE_USER))

    self.assertEqual(404, client.get(post_url()).status_code)

  def test_the_filesystem_is_never_reached_for_somebody_elses_post(self):
    ##
    ## The invariant this whole route ordering exists for. A refused request
    ## must not probe the disk at all - not to check existence, not to count
    ## entries, not to stat anything.
    ##
    query = FakeQuery(post=None)
    client, resolver = build(query, principal=auth_context_for(4, ROLE_USER))

    client.get(post_url())

    self.assertEqual([], resolver.calls)

  def test_an_admin_sees_any_post(self):
    query = FakeQuery(post=POST_ROW)
    client, _ = build(query, principal=auth_context_for(9, ROLE_ADMIN))

    response = client.get(post_url())

    self.assertEqual(200, response.status_code)
    self.assertEqual(("post", "douyin", AWEME), query.calls[0])

  def test_a_user_never_reaches_a_post_owned_by_nobody(self):
    ##
    ## Historical rows predate ownership. The scoped statement's join simply
    ## does not match them.
    ##
    query = FakeQuery(post=None)
    client, _ = build(query, principal=auth_context_for(3, ROLE_USER))

    self.assertEqual(404, client.get(post_url()).status_code)

  def test_an_admin_does_reach_a_post_owned_by_nobody(self):
    query = FakeQuery(post=POST_ROW)
    client, _ = build(query, principal=auth_context_for(9, ROLE_ADMIN))

    self.assertEqual(200, client.get(post_url()).status_code)


class TestRecordingAssetScope(unittest.TestCase):
  def test_an_owner_sees_their_own_recordings_asset(self):
    query = FakeQuery(recording=RECORDING_ROW)
    client, _ = build(query, principal=auth_context_for(3, ROLE_USER))

    response = client.get(RECORDING_URL)

    self.assertEqual(200, response.status_code)
    self.assertEqual(("recording_for_user", 3, 7), query.calls[0])

  def test_another_user_is_told_it_does_not_exist(self):
    query = FakeQuery(recording=None)
    client, _ = build(query, principal=auth_context_for(4, ROLE_USER))

    self.assertEqual(404, client.get(RECORDING_URL).status_code)

  def test_the_filesystem_is_never_reached_for_somebody_elses_recording(self):
    query = FakeQuery(recording=None)
    client, resolver = build(query, principal=auth_context_for(4, ROLE_USER))

    client.get(RECORDING_URL)

    self.assertEqual([], resolver.calls)

  def test_an_admin_sees_any_recording(self):
    query = FakeQuery(recording=RECORDING_ROW)
    client, _ = build(query, principal=auth_context_for(9, ROLE_ADMIN))

    response = client.get(RECORDING_URL)

    self.assertEqual(200, response.status_code)
    self.assertEqual(("recording", 7), query.calls[0])


class TestStorageStatesAreNotNotFound(unittest.TestCase):
  def state_for(self, state):
    query = FakeQuery(post=POST_ROW)
    resolver = RecordingResolver(AssetDiscovery.nothing(state))
    client, _ = build(query, resolver=resolver, principal=auth_context_for(3, ROLE_USER))
    return client.get(post_url())

  def test_files_gone_is_still_a_two_hundred(self):
    ##
    ## "There is no such library resource" and "the resource is here but its
    ## files are not" are different facts, and only the first is a 404.
    ##
    response = self.state_for(StorageState.MISSING)

    self.assertEqual(200, response.status_code)
    self.assertEqual("missing", body_of(response)["data"]["storage_state"])

  def test_an_empty_directory_is_still_a_two_hundred(self):
    response = self.state_for(StorageState.EMPTY)

    self.assertEqual(200, response.status_code)
    self.assertEqual("empty", body_of(response)["data"]["storage_state"])

  def test_an_unsafe_path_is_still_a_two_hundred(self):
    response = self.state_for(StorageState.UNAVAILABLE)

    self.assertEqual(200, response.status_code)
    self.assertEqual("unavailable", body_of(response)["data"]["storage_state"])


class TestResponsePrivacy(unittest.TestCase):
  def assert_no_paths(self, response):
    rendered = response.get_data(as_text=True)

    for leaked in (
      "/downloads",
      "/app/downloads",
      "/tmp/",
      "save_dir",
      "output_path",
      "absolute_path",
      "relative_path",
      "filesystem_root",
    ):
      self.assertNotIn(leaked, rendered, leaked)

  def test_a_post_response_carries_no_path(self):
    query = FakeQuery(post=POST_ROW)
    client, _ = build(query, principal=auth_context_for(3, ROLE_USER))

    self.assert_no_paths(client.get(post_url()))

  def test_a_recording_response_carries_no_path(self):
    query = FakeQuery(recording=RECORDING_ROW)
    client, _ = build(query, principal=auth_context_for(3, ROLE_USER))

    self.assert_no_paths(client.get(RECORDING_URL))

  def test_an_admin_response_carries_no_path_either(self):
    ##
    ## Admin is a wider data scope, not a licence to learn the filesystem
    ## layout of the host.
    ##
    query = FakeQuery(post=POST_ROW, recording=RECORDING_ROW)
    client, _ = build(query, principal=auth_context_for(9, ROLE_ADMIN))

    self.assert_no_paths(client.get(post_url()))
    self.assert_no_paths(client.get(RECORDING_URL))

  def test_the_resource_block_names_the_resource_and_nothing_else(self):
    query = FakeQuery(post=POST_ROW)
    client, _ = build(query, principal=auth_context_for(3, ROLE_USER))

    resource = body_of(client.get(post_url()))["data"]["resource"]

    self.assertEqual({"kind": "post", "platform": "douyin", "aweme_id": AWEME}, resource)


class TestRouteSecurity(unittest.TestCase):
  def test_an_anonymous_request_is_refused(self):
    query = FakeQuery(post=POST_ROW)
    client, resolver = build(query, principal=None)

    self.assertEqual(401, client.get(post_url()).status_code)
    self.assertEqual(401, client.get(RECORDING_URL).status_code)
    ##
    ## And never touched the disk on the way to being refused.
    ##
    self.assertEqual([], resolver.calls)

  def test_a_database_that_cannot_answer_is_a_five_oh_three(self):
    client, resolver = build(
      unavailable=LibraryUnavailable("数据库暂时不可用"),
      principal=auth_context_for(3, ROLE_USER),
    )

    self.assertEqual(503, client.get(post_url()).status_code)
    self.assertEqual([], resolver.calls)

  def test_an_identity_query_parameter_cannot_widen_the_scope(self):
    ##
    ## The scope comes from the session, never from the url.
    ##
    query = FakeQuery(post=None)
    client, _ = build(query, principal=auth_context_for(4, ROLE_USER))

    response = client.get(post_url() + "?app_user_id=3&user_id=3&role=admin")

    self.assertEqual(404, response.status_code)
    self.assertEqual(("post_for_user", 4, "douyin", AWEME), query.calls[0])

  def test_a_non_numeric_recording_id_is_not_a_route(self):
    query = FakeQuery(recording=RECORDING_ROW)
    client, _ = build(query, principal=auth_context_for(3, ROLE_USER))

    response = client.get("/api/library/recordings/not-a-number/assets")

    self.assertEqual(404, response.status_code)


if __name__ == "__main__":
  unittest.main()
