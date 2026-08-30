##
## What the recovery machinery must never let out.
##
## A recovery key is a persistence identity, not a capability: knowing one
## grants nothing, and every media access still has to authenticate, authorise
## the parent recording, and rediscover the file.  But it has no business value
## either, and a field that appears in a response is a field that has to stay
## correct forever - so the right number of places it appears in is none.
##
## The journal is the other half.  It is written from a
## ``RecordingPersistenceIntent``, which has no field for a stream url, a
## cookie or a proxy password.  These tests plant unmistakable sentinels around
## everything the recording pipeline touches and then read the actual bytes,
## because "the schema has no such field" is an argument about the schema and
## this is a question about the file.
##
from datetime import datetime
from pathlib import Path
import json
import tempfile
import unittest

from flask import Flask

from backend.src.auth.roles import ROLE_ADMIN
from backend.src.auth.service import AuthenticatedUser
from backend.src.database.query.library import LibraryPage
from backend.src.platform.douyin.douyin_live_downloader import LiveDownloadResult
from backend.src.service.recording_recovery_journal import (
  JOURNAL_DIRECTORY_NAME,
  RecordingRecoveryJournal,
)
from backend.src.service.recording_resource import RecordingResourceService
from backend.src.unit_test.auth_context import install_test_auth
from backend.src.web.library_routes import build_library_blueprint

KEY = "0123456789abcdef0123456789abcdef"

##
## Values that exist nowhere else in the codebase, so finding one in a response
## body or a journal file can only mean it travelled there.
##
SECRET_STREAM_TOKEN = "SECRET_STREAM_TOKEN_11B"
SECRET_COOKIE = "SECRET_COOKIE_11B"
SECRET_AUTH = "SECRET_AUTH_11B"
SECRET_PROXY_PASSWORD = "SECRET_PROXY_PASSWORD_11B"
SECRET_CSRF = "SECRET_CSRF_11B"
SECRET_SESSION = "SECRET_SESSION_11B"

ALL_SECRETS = (
  SECRET_STREAM_TOKEN,
  SECRET_COOKIE,
  SECRET_AUTH,
  SECRET_PROXY_PASSWORD,
  SECRET_CSRF,
  SECRET_SESSION,
)

##
## Exactly what a note says. An allowlist rather than a blocklist: a blocklist
## only catches the leaks somebody already thought of, and the realistic
## accident here is somebody merging a whole task or result dict into the
## payload, which no list of forbidden words would notice.
##
ALLOWED_JOURNAL_FIELDS = frozenset({
  "schema_version",
  "recovery_key",
  "app_user_id",
  "platform",
  "room_id",
  "owner_user_id",
  "title",
  "protocol",
  "output_path",
  "started_at",
  "finished_at",
  "source",
})


def contaminated_result():
  """A finished recording surrounded by transport material.

  The extra attributes are not fields of ``LiveDownloadResult`` - they are
  planted directly on the instance, which is the closest thing to "somebody
  passed the whole thing through" that can be arranged.
  """
  result = LiveDownloadResult(
    ok=True,
    recorded=True,
    room_status=2,
    room_id="998877",
    owner_user_id="owner-1",
    nickname="Test Host",
    title="Launch title",
    protocol="hls",
    ##
    ## Root-relative: a note may only describe media inside the configured
    ## storage root, and this fixture runs against a temporary one.
    ##
    output_path="douyin/live/A/live.mp4",
    started_at=datetime(2026, 8, 30, 9, 0, 0),
    finished_at=datetime(2026, 8, 30, 10, 0, 0),
  )
  object.__setattr__(
    result, "stream_url",
    "https://stream.example.test/index.m3u8?sign={}&token={}".format(
      SECRET_STREAM_TOKEN, SECRET_STREAM_TOKEN
    ),
  )
  object.__setattr__(result, "resolved_url", "https://live.douyin.com/123456")
  object.__setattr__(result, "source_url", "https://v.douyin.com/abc/")
  object.__setattr__(result, "headers", {"Cookie": SECRET_COOKIE,
                                         "Authorization": SECRET_AUTH})
  object.__setattr__(result, "proxies", {"https": "http://u:{}@p".format(
    SECRET_PROXY_PASSWORD
  )})
  object.__setattr__(result, "csrf_token", SECRET_CSRF)
  object.__setattr__(result, "session_token", SECRET_SESSION)
  return result


def journal_for(root):
  return RecordingRecoveryJournal(
    config_loader=lambda: {"download": {"save_path": str(root)}}
  )


def intent_for(result, **overrides):
  arguments = {"app_user_id": 41, "platform": "douyin", "source": "task_api"}
  arguments.update(overrides)
  return RecordingResourceService(
    repository_provider=lambda: None
  ).prepare(result, **arguments)


class JournalBytesTest(unittest.TestCase):
  """Read the file, not the schema."""

  def published_bytes(self, root, result=None):
    service = journal_for(root)
    published = service.publish(
      intent_for(result if result is not None else contaminated_result()), KEY
    )
    return published.read_bytes()

  def test_no_transport_secret_reaches_the_journal_file(self):
    with tempfile.TemporaryDirectory() as root:
      raw = self.published_bytes(root).decode("utf-8")

      for secret in ALL_SECRETS:
        with self.subTest(secret=secret):
          self.assertNotIn(secret, raw)

  def test_no_stream_or_source_url_reaches_the_journal_file(self):
    with tempfile.TemporaryDirectory() as root:
      raw = self.published_bytes(root).decode("utf-8")

      for fragment in (
        "stream.example.test",
        "live.douyin.com",
        "v.douyin.com",
        "m3u8",
        "sign=",
        "token=",
      ):
        with self.subTest(fragment=fragment):
          self.assertNotIn(fragment, raw)

  def test_the_journal_carries_exactly_the_allowed_fields(self):
    ##
    ## The guard that catches the accident a blocklist cannot: somebody merging
    ## a whole result or task dict into the payload fails here immediately,
    ## whatever the new keys happen to be called.
    ##
    with tempfile.TemporaryDirectory() as root:
      payload = json.loads(self.published_bytes(root).decode("utf-8"))

      self.assertEqual(ALLOWED_JOURNAL_FIELDS, set(payload))

  def test_the_journal_still_carries_the_recording_facts(self):
    ##
    ## The negative tests above would also pass on an empty file, so the note
    ## has to be shown to still say what it is for.
    ##
    with tempfile.TemporaryDirectory() as root:
      payload = json.loads(self.published_bytes(root).decode("utf-8"))

      self.assertEqual(41, payload["app_user_id"])
      self.assertEqual("douyin", payload["platform"])
      self.assertEqual("douyin/live/A/live.mp4", payload["output_path"])
      self.assertEqual("998877", payload["room_id"])

  def test_a_contaminated_result_still_round_trips(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal_for(root)
      original = intent_for(contaminated_result())
      service.publish(original, KEY)

      self.assertEqual(original, service.load(KEY))


class JournalDirectoryIsNotMediaTest(unittest.TestCase):
  def test_the_journal_directory_is_hidden_and_named_for_this_service(self):
    ##
    ## Media discovery walks the download root. A hidden, service-specific name
    ## keeps notes from ever looking like content.
    ##
    self.assertTrue(JOURNAL_DIRECTORY_NAME.startswith("."))
    self.assertNotIn("/", JOURNAL_DIRECTORY_NAME)

  def test_media_discovery_does_not_treat_journal_notes_as_assets(self):
    from backend.src.service.media_asset import media_type_for, preview_kind_for

    media_type = media_type_for("{}.json".format(KEY))
    self.assertEqual("application/octet-stream", media_type)
    self.assertIsNone(preview_kind_for(media_type))


class SourceBoundaryTest(unittest.TestCase):
  """No layer that answers a browser knows this vocabulary."""

  def modules_under(self, *relative):
    root = Path(__file__).resolve().parents[1]
    for part in relative:
      target = root / part
      if target.is_dir():
        yield from sorted(target.glob("*.py"))
      else:
        yield target

  def test_no_web_route_mentions_the_recovery_vocabulary(self):
    for module in self.modules_under("web"):
      text = module.read_text(encoding="utf-8")
      for term in ("recovery_key", "recovery_journal", JOURNAL_DIRECTORY_NAME):
        with self.subTest(module=module.name, term=term):
          self.assertNotIn(term, text)

  def test_the_library_query_layer_does_not_select_it(self):
    text = (
      Path(__file__).resolve().parents[1]
      / "database" / "query" / "library.py"
    ).read_text(encoding="utf-8")

    self.assertNotIn("recovery_key", text)

  def test_the_media_layers_do_not_know_about_it(self):
    for module in ("media_asset.py", "media_range.py"):
      text = (
        Path(__file__).resolve().parents[1] / "service" / module
      ).read_text(encoding="utf-8")
      with self.subTest(module=module):
        self.assertNotIn("recovery_key", text)
        self.assertNotIn(JOURNAL_DIRECTORY_NAME, text)

  def test_the_task_result_metadata_does_not_carry_it(self):
    text = (
      Path(__file__).resolve().parents[1]
      / "service" / "live_recording_task.py"
    ).read_text(encoding="utf-8")
    metadata = text[text.index("def _result_metadata"):]
    metadata = metadata[:metadata.index("\n  def ")]

    self.assertNotIn("recovery", metadata)
    self.assertNotIn("journal", metadata)


class LibraryResponseTest(unittest.TestCase):
  """A real recording response body, read as bytes."""

  def client(self, rows):
    class FakeQuery:
      def recordings(self, recording_filter):
        return LibraryPage(len(rows), 1, 25, tuple(rows))

      def recordings_for_user(self, app_user_id, recording_filter):
        return LibraryPage(len(rows), 1, 25, tuple(rows))

    class FakeRuntime:
      def page_size_limit(self):
        return 100

      def query(self):
        return FakeQuery()

    app = Flask(__name__)
    install_test_auth(
      app, user=AuthenticatedUser(9001, "test-admin", ROLE_ADMIN)
    )
    app.register_blueprint(build_library_blueprint(runtime=FakeRuntime()))
    return app.test_client()

  def recording_row(self):
    ##
    ## The row shape the query layer produces, with a recovery key planted as
    ## if a future column had leaked into the select.
    ##
    return {
      "recording_id": 73,
      "app_user_id": 41,
      "platform": "douyin",
      "room_id": "998877",
      "owner_user_id": "owner-1",
      "title": "Launch title",
      "protocol": "hls",
      "output_path": "douyin/live/A/live.mp4",
      "started_at": datetime(2026, 8, 30, 9, 0, 0),
      "finished_at": datetime(2026, 8, 30, 10, 0, 0),
      "source": "task_api",
      "created_at": datetime(2026, 8, 30, 10, 0, 1),
      "nickname": "Test Host",
      "directory_name": "Test_Host",
      "person_id": None,
      "person_display_name": None,
      "recovery_key": KEY,
    }

  def test_a_recording_response_never_carries_the_recovery_key(self):
    ##
    ## Even when the row handed to serialisation has one. The response is built
    ## from a known set of fields rather than by copying the row, and this is
    ## what proves it.
    ##
    response = self.client([self.recording_row()]).get("/api/library/recordings")

    self.assertEqual(200, response.status_code)
    raw = response.data.decode("utf-8")
    self.assertNotIn("recovery_key", raw)
    self.assertNotIn(KEY, raw)

  def test_the_recording_response_still_carries_its_own_facts(self):
    response = self.client([self.recording_row()]).get("/api/library/recordings")

    body = json.loads(response.data.decode("utf-8"))
    self.assertEqual("success", body["status"])
    item = body["data"]["items"][0]
    ##
    ## Still the Phase 10B-0 wire contract: a canonical decimal string, not a
    ## number a browser would round.
    ##
    self.assertEqual("73", item["recording_id"])
    self.assertEqual("douyin", item["platform"])
    self.assertEqual("998877", item["room_id"])

  def test_the_recording_serializer_is_a_closed_allowlist(self):
    ##
    ## This is what actually keeps the recovery key out, and it is stronger
    ## than the key's absence alone: the response is built from a fixed set of
    ## fields rather than by copying the row, so no future column - recovery
    ## key, filesystem path or anything else - reaches a browser by being
    ## added to a SELECT.
    ##
    ## ``output_path`` is absent for the same reason, and has always been: the
    ## server's own filesystem layout is not the browser's business.
    ##
    response = self.client([self.recording_row()]).get("/api/library/recordings")

    item = json.loads(response.data.decode("utf-8"))["data"]["items"][0]
    self.assertEqual(
      {
        "recording_id", "platform", "room_id", "title",
        "started_at", "finished_at", "created_at", "nickname",
      },
      set(item),
    )
    self.assertNotIn("output_path", item)
    self.assertNotIn("app_user_id", item)

  def test_no_journal_path_appears_in_a_recording_response(self):
    response = self.client([self.recording_row()]).get("/api/library/recordings")

    raw = response.data.decode("utf-8")
    self.assertNotIn(JOURNAL_DIRECTORY_NAME, raw)
    self.assertNotIn(".json", raw)


if __name__ == "__main__":
  unittest.main()
