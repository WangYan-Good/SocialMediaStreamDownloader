##<<Base>>
import json
import unittest

##<<Extension>>
from flask import Flask

##<<Third-part>>
from backend.src.auth.roles import ROLE_ADMIN, ROLE_USER
from backend.src.auth.service import AuthenticatedUser
from backend.src.database.query.library import LibraryPage
from backend.src.service.media_asset import AssetDiscovery, MediaAsset, StorageState
from backend.src.unit_test.auth_context import install_test_auth
from backend.src.web.library_routes import build_library_blueprint
from backend.src.web.wire import recording_id_to_wire


##
## Two identities a JavaScript number cannot hold.
##
## The first is the smallest integer above ``Number.MAX_SAFE_INTEGER``; parsed
## as a double it becomes 9007199254740992, so a browser that received it as a
## JSON number would ask for a recording that is not the one it was listed.
##
BEYOND_SAFE = 9007199254740993

##
## And the top of the column's own domain.  ``BIGINT UNSIGNED`` can hold this,
## which is the whole reason the wire cannot be a JSON number - not the size of
## the ids that happen to exist today.
##
BIGINT_MAX = 18446744073709551615


class RecordingIdWireHelperTest(unittest.TestCase):
  """The one place an internal identity becomes wire text."""

  def test_a_positive_identity_becomes_its_decimal_string(self):
    self.assertEqual("1", recording_id_to_wire(1))
    self.assertEqual("42", recording_id_to_wire(42))

  def test_an_identity_beyond_the_javascript_safe_range_survives_exactly(self):
    self.assertEqual("9007199254740993", recording_id_to_wire(BEYOND_SAFE))

  def test_the_top_of_the_bigint_domain_survives_exactly(self):
    ##
    ## No table is expected to reach this.  The serializer is being asked
    ## whether it *could* carry it, because that is what the column promises.
    ##
    self.assertEqual("18446744073709551615", recording_id_to_wire(BIGINT_MAX))

  def test_the_wire_form_is_canonical(self):
    ##
    ## No sign, no padding, no decimal point, no surrounding space: one identity
    ## has exactly one spelling, so two clients cannot disagree about whether
    ## they hold the same recording.
    ##
    for value in (1, 42, BEYOND_SAFE, BIGINT_MAX):
      text = recording_id_to_wire(value)
      self.assertEqual(text, text.strip())
      self.assertTrue(text.isdigit())
      self.assertNotIn(".", text)
      self.assertNotIn("e", text.lower())
      self.assertFalse(text.startswith("0"))

  def test_nothing_is_not_quietly_spelled_out(self):
    ##
    ## ``str(None)`` is "None", which would reach a browser as a plausible
    ## looking identity and come back as a url segment.  A missing identity is a
    ## fault here, not a value.
    ##
    with self.assertRaises(ValueError):
      recording_id_to_wire(None)

  def test_a_value_that_is_not_an_identity_is_refused(self):
    for value in ("7", 7.0, b"7", [7], {"recording_id": 7}, object()):
      with self.assertRaises(ValueError):
        recording_id_to_wire(value)

  def test_a_boolean_is_not_an_identity(self):
    ##
    ## ``True`` is an ``int`` in Python and would serialize as "1" - the same
    ## text as a real recording.  Matches ``_require_identifier`` in the query
    ## layer, which refuses booleans for the same reason.
    ##
    for value in (True, False):
      with self.assertRaises(ValueError):
        recording_id_to_wire(value)

  def test_an_identity_below_one_is_refused(self):
    for value in (0, -1):
      with self.assertRaises(ValueError):
        recording_id_to_wire(value)


##
## >>------------------------- library list wire -------------------------<<
##
class FakeQuery:
  def __init__(self, recordings=None, recording=None):
    self.recordings_page = (
      recordings if recordings is not None else LibraryPage(0, 1, 25, tuple())
    )
    self._recording = recording
    self.recording_calls = []

  def recordings(self, recording_filter):
    return self.recordings_page

  def recordings_for_user(self, app_user_id, recording_filter):
    return self.recordings_page

  def recording(self, recording_id):
    self.recording_calls.append(recording_id)
    return self._recording

  def recording_for_user(self, app_user_id, recording_id):
    self.recording_calls.append(recording_id)
    return self._recording


class FakeResolver:
  """Reports one file, and remembers the identity it was asked about."""

  def __init__(self):
    self.calls = []

  def recording_asset(self, output_path, recording_id):
    self.calls.append((output_path, recording_id))
    return AssetDiscovery(
      storage_state=StorageState.AVAILABLE,
      assets=(
        MediaAsset(
          asset_id="a" * 64,
          kind="recording",
          name="live.flv",
          size_bytes=100,
          media_type="video/x-flv",
        ),
      ),
    )


class FakeRuntime:
  def __init__(self, query, resolver=None):
    self._query = query
    self._resolver = resolver if resolver is not None else FakeResolver()

  def page_size_limit(self):
    return 100

  def query(self):
    return self._query

  def asset_resolver(self):
    return self._resolver


def client_for(runtime, user=None):
  app = Flask(__name__)
  install_test_auth(
    app,
    user=user or AuthenticatedUser(9001, "test-admin", ROLE_ADMIN),
  )
  app.register_blueprint(build_library_blueprint(runtime=runtime))
  return app.test_client()


def recording_row(recording_id):
  return {
    "recording_id": recording_id,
    "app_user_id": 71,
    "platform": "douyin",
    "room_id": "room",
    "title": "晚间直播",
    "nickname": "主播",
    "output_path": "/downloads/creator/live.flv",
    "started_at": None,
    "finished_at": None,
    "created_at": None,
    "source": "task_api",
  }


class LibraryRecordingListWireTest(unittest.TestCase):
  def _item(self, recording_id):
    page = LibraryPage(1, 1, 25, (recording_row(recording_id),))
    response = client_for(FakeRuntime(FakeQuery(recordings=page))).get(
      "/api/library/recordings"
    )
    self.assertEqual(200, response.status_code)
    return response

  def test_a_listed_recording_names_itself_with_a_string(self):
    item = self._item(1).get_json()["data"]["items"][0]

    self.assertEqual("1", item["recording_id"])
    self.assertIsInstance(item["recording_id"], str)

  def test_an_identity_beyond_the_safe_range_is_listed_without_loss(self):
    ##
    ## Read out of the raw body rather than the parsed one: this asserts what
    ## crossed the wire, which is the only place the loss could occur.
    ##
    response = self._item(BEYOND_SAFE)
    raw = response.get_data(as_text=True)

    self.assertIn('"recording_id":"9007199254740993"', raw.replace('": "', '":"'))
    self.assertNotIn("9007199254740992", raw)
    self.assertEqual(
      "9007199254740993",
      response.get_json()["data"]["items"][0]["recording_id"],
    )

  def test_the_top_of_the_bigint_domain_is_listed_without_loss(self):
    item = self._item(BIGINT_MAX).get_json()["data"]["items"][0]

    self.assertEqual("18446744073709551615", item["recording_id"])

  def test_a_row_without_a_usable_identity_is_refused_not_invented(self):
    ##
    ## The row cannot be addressed, so it must not be listed as though it could.
    ## The existing listing boundary answers, rather than the exception escaping
    ## as a bare stack trace.
    ##
    page = LibraryPage(1, 1, 25, (recording_row(None),))
    response = client_for(FakeRuntime(FakeQuery(recordings=page))).get(
      "/api/library/recordings"
    )

    self.assertEqual(500, response.status_code)
    self.assertNotIn("None", json.loads(response.get_data(as_text=True))["message"])


class RecordingAssetResourceWireTest(unittest.TestCase):
  def _resource(self, recording_id, user=None):
    query = FakeQuery(recording=recording_row(recording_id))
    resolver = FakeResolver()
    response = client_for(FakeRuntime(query, resolver), user=user).get(
      "/api/library/recordings/{}/assets".format(recording_id)
    )
    self.assertEqual(200, response.status_code)
    return response, query, resolver

  def test_the_named_resource_uses_the_same_string_form_as_the_list(self):
    response, _, _ = self._resource(1)
    resource = response.get_json()["data"]["resource"]

    self.assertEqual({"kind": "recording", "recording_id": "1"}, resource)
    self.assertIsInstance(resource["recording_id"], str)

  def test_an_identity_beyond_the_safe_range_is_echoed_without_loss(self):
    response, _, _ = self._resource(BEYOND_SAFE)
    raw = response.get_data(as_text=True)

    self.assertIn('"recording_id":"9007199254740993"', raw.replace('": "', '":"'))
    self.assertNotIn("9007199254740992", raw)

  def test_the_route_still_hands_the_lookup_an_integer(self):
    ##
    ## The wire is text; everything behind the route is not.  A string reaching
    ## the query layer would turn an indexed BIGINT comparison into a string
    ## comparison, and ``_require_identifier`` refuses it outright.
    ##
    _, query, resolver = self._resource(BEYOND_SAFE, user=AuthenticatedUser(71, "alice", ROLE_USER))

    self.assertEqual([BEYOND_SAFE], query.recording_calls)
    self.assertIs(int, type(query.recording_calls[0]))
    self.assertIs(int, type(resolver.calls[0][1]))


##
## >>-------------------------- task result wire --------------------------<<
##
from backend.src.task.model import TASK_TYPE_LIVE_RECORD  # noqa: E402
from backend.src.task.service import TaskService  # noqa: E402
from backend.src.web.task_routes import (  # noqa: E402
  build_task_blueprint,
  install_task_service,
)


def task_client(service, user):
  app = Flask(__name__)
  app.config["TESTING"] = True
  install_test_auth(app, user=user)
  install_task_service(app, service)
  app.register_blueprint(build_task_blueprint())
  return app.test_client()


def recorded_task(service, recording_id, app_user_id=71):
  task = service.create_task(
    TASK_TYPE_LIVE_RECORD,
    title="录制抖音直播",
    app_user_id=app_user_id,
  )
  service.update_metadata(
    task["task_id"],
    {
      "result": {
        "ok": True,
        "recorded": True,
        "saved_count": 1,
        "recording_id": recording_id,
      }
    },
  )
  return task


class TaskRecordingIdWireTest(unittest.TestCase):
  """A third spelling would be a third contract for the same identity."""

  def setUp(self):
    self.service = TaskService()
    self.alice = AuthenticatedUser(71, "alice", ROLE_USER)
    self.admin = AuthenticatedUser(72, "operator", ROLE_ADMIN)

  def _user_result(self, recording_id):
    task = recorded_task(self.service, recording_id)
    response = task_client(self.service, self.alice).get(
      "/api/tasks/" + task["task_id"]
    )
    self.assertEqual(200, response.status_code)
    return response

  def _admin_result(self, recording_id):
    task = recorded_task(self.service, recording_id)
    response = task_client(self.service, self.admin).get(
      "/api/tasks/" + task["task_id"]
    )
    self.assertEqual(200, response.status_code)
    return response

  def test_the_user_wire_spells_the_identity_as_a_string(self):
    result = self._user_result(1).get_json()["data"]["metadata"]["result"]

    self.assertEqual("1", result["recording_id"])
    self.assertIsInstance(result["recording_id"], str)

  def test_the_user_wire_keeps_counts_as_numbers(self):
    ##
    ## ``recording_id`` left the count allowlist because it is an identity, not
    ## a quantity.  The quantities must not have followed it.
    ##
    result = self._user_result(1).get_json()["data"]["metadata"]["result"]

    self.assertEqual(1, result["saved_count"])
    self.assertIsInstance(result["saved_count"], int)
    self.assertNotIsInstance(result["saved_count"], str)

  def test_the_user_wire_survives_an_identity_beyond_the_safe_range(self):
    raw = self._user_result(BEYOND_SAFE).get_data(as_text=True)

    self.assertIn('"recording_id":"9007199254740993"', raw.replace('": "', '":"'))
    self.assertNotIn("9007199254740992", raw)

  def test_the_admin_wire_spells_the_identity_as_a_string(self):
    result = self._admin_result(1).get_json()["data"]["metadata"]["result"]

    self.assertEqual("1", result["recording_id"])

  def test_the_admin_wire_survives_an_identity_beyond_the_safe_range(self):
    raw = self._admin_result(BEYOND_SAFE).get_data(as_text=True)

    self.assertIn('"recording_id":"9007199254740993"', raw.replace('": "', '":"'))
    self.assertNotIn("9007199254740992", raw)

  def test_a_listed_task_spells_it_the_same_way_a_read_one_does(self):
    recorded_task(self.service, BEYOND_SAFE)

    for user in (self.alice, self.admin):
      items = task_client(self.service, user).get("/api/tasks").get_json()
      result = items["data"]["items"][0]["metadata"]["result"]
      self.assertEqual("9007199254740993", result["recording_id"])

  def test_the_stored_task_still_holds_an_integer(self):
    ##
    ## The conversion belongs to the response copy.  Mutating the process's own
    ## memory of the task would rewrite what the runner recorded, and every
    ## later reader would inherit the wire's spelling.
    ##
    task = recorded_task(self.service, BEYOND_SAFE)
    task_client(self.service, self.admin).get("/api/tasks/" + task["task_id"])

    stored = self.service.get_task(task["task_id"])
    self.assertIs(int, type(stored["metadata"]["result"]["recording_id"]))
    self.assertEqual(BEYOND_SAFE, stored["metadata"]["result"]["recording_id"])

  def test_a_task_that_recorded_nothing_says_nothing(self):
    task = self.service.create_task(
      TASK_TYPE_LIVE_RECORD, app_user_id=self.alice.user_id
    )
    self.service.update_metadata(task["task_id"], {"result": {"ok": False}})

    for user in (self.alice, self.admin):
      data = task_client(self.service, user).get(
        "/api/tasks/" + task["task_id"]
      ).get_json()["data"]
      self.assertNotIn("recording_id", data["metadata"].get("result", {}))

  def test_an_unusable_identity_is_dropped_rather_than_spelled_out(self):
    ##
    ## Task metadata is a loose bag written by runners, so unlike a database row
    ## a bad value here is possible without the store being broken.  It must not
    ## reach a browser looking like an identity - and it must not take the rest
    ## of the task report down with it either.
    ##
    for bad in (0, -1, "7", 7.5, None, True):
      task = recorded_task(self.service, bad)
      for user in (self.alice, self.admin):
        data = task_client(self.service, user).get(
          "/api/tasks/" + task["task_id"]
        ).get_json()["data"]
        result = data["metadata"].get("result", {})
        self.assertNotIn("recording_id", result)
        ##
        ## And the rest of the report is still there: one unusable field must
        ## not cost the browser everything else the task said.
        ##
        self.assertEqual(1, result["saved_count"])


##
## >>------------------------ asset id compatibility ------------------------<<
##
from backend.src.service.media_asset import asset_id_for  # noqa: E402


class AssetIdCompatibilityTest(unittest.TestCase):
  """Phase 10A ids were published.  Restating the wire must not restate them.

  The identity that reaches the digest is the text ``str(...)`` makes of it, and
  the wire form of a recording id is that same text.  So the two spellings were
  never distinguishable to the digest - which is why this change can be made at
  all, and why it has to stay true.
  """

  ##
  ## Written down rather than recomputed.  An expectation derived from the code
  ## under test would agree with any change to that code, including a changed
  ## separator or an added version prefix - which is exactly what this is here
  ## to catch.  Both were taken from the algorithm as Phase 10A shipped it.
  ##
  RECORDING_123_X_FLV = (
    "896d4d038da75e9ffa875111a10234cf700f9c7ce25d807ca02c1790e66e2963"
  )
  RECORDING_BEYOND_SAFE_LIVE_FLV = (
    "c54f62ec2ee408115ac5f9736937e15c3c31130c5c3e45dca63811ea412ab648"
  )

  def test_a_published_recording_asset_id_is_unchanged(self):
    self.assertEqual(
      self.RECORDING_123_X_FLV, asset_id_for("recording", (123,), "x.flv")
    )
    self.assertEqual(
      self.RECORDING_BEYOND_SAFE_LIVE_FLV,
      asset_id_for("recording", (BEYOND_SAFE,), "live.flv"),
    )

  def test_the_material_is_still_kind_identity_and_file_name_nul_joined(self):
    import hashlib

    expected = hashlib.sha256(
      "recording\x00123\x00x.flv".encode("utf-8")
    ).hexdigest()

    self.assertEqual(expected, asset_id_for("recording", (123,), "x.flv"))

  def test_an_integer_and_its_wire_spelling_digest_identically(self):
    ##
    ## The compatibility guarantee itself.  Whichever side of the boundary the
    ## identity is taken from, the id a browser was handed in Phase 10A is the
    ## id it will be handed now.
    ##
    self.assertEqual(
      asset_id_for("recording", (123,), "x.flv"),
      asset_id_for("recording", (recording_id_to_wire(123),), "x.flv"),
    )
    self.assertEqual(
      asset_id_for("recording", (BEYOND_SAFE,), "live.flv"),
      asset_id_for("recording", (recording_id_to_wire(BEYOND_SAFE),), "live.flv"),
    )

  def test_the_id_carries_no_path_no_quotes_and_no_version(self):
    import hashlib

    produced = asset_id_for("recording", (123,), "x.flv")

    self.assertEqual(64, len(produced))
    for wrong in (
      "recording\x00\"123\"\x00x.flv",
      '["recording", "123", "x.flv"]',
      "v1\x00recording\x00123\x00x.flv",
      "recording:123:x.flv",
      "recording\x00123\x00/downloads/x.flv",
    ):
      self.assertNotEqual(
        hashlib.sha256(wrong.encode("utf-8")).hexdigest(), produced
      )


##
## >>------------------------- query internal type -------------------------<<
##
from backend.src.database.query.library import LibraryQuery  # noqa: E402


class RecordingCursor:
  """Remembers the statement and the parameters it was bound with."""

  def __init__(self, row=None):
    self.row = row
    self.executed = []

  def execute(self, statement, params=None):
    self.executed.append((statement, params))

  def fetchone(self):
    return self.row

  def __enter__(self):
    return self

  def __exit__(self, *exception):
    return False


class RecordingConnection:
  def __init__(self, cursor):
    self._cursor = cursor

  def cursor(self):
    return self._cursor

  def __enter__(self):
    return self

  def __exit__(self, *exception):
    return False


class RecordingDatabase:
  def __init__(self, cursor):
    self._cursor = cursor

  def get_connection(self):
    return RecordingConnection(self._cursor)


class LibraryQueryInternalIdentityTest(unittest.TestCase):
  """Behind the route, an identity is an integer and stays one."""

  def _query(self, row=None):
    cursor = RecordingCursor(row=row)
    return LibraryQuery(RecordingDatabase(cursor)), cursor

  def test_a_recording_lookup_binds_the_integer_as_a_parameter(self):
    query, cursor = self._query(row={"recording_id": BEYOND_SAFE})

    query.recording(BEYOND_SAFE)

    statement, params = cursor.executed[0]
    self.assertEqual((BEYOND_SAFE,), params)
    self.assertIs(int, type(params[0]))
    ##
    ## Bound, never interpolated: the identity must not appear in the statement
    ## text at all.
    ##
    self.assertIn("rr.recording_id = %s", statement)
    self.assertNotIn(str(BEYOND_SAFE), statement)

  def test_an_owned_recording_lookup_binds_both_identities_as_integers(self):
    query, cursor = self._query(row={"recording_id": 7})

    query.recording_for_user(71, 7)

    statement, params = cursor.executed[0]
    self.assertEqual((7, 71), params)
    for one in params:
      self.assertIs(int, type(one))
    self.assertIn("rr.app_user_id = %s", statement)

  def test_the_wire_spelling_is_refused_by_the_query_layer(self):
    ##
    ## The point of keeping the boundary at the route: a string arriving here
    ## would turn an indexed BIGINT comparison into a string comparison.  It is
    ## refused rather than coerced.
    ##
    query, _ = self._query()

    for spelling in ("7", recording_id_to_wire(7)):
      with self.assertRaises(ValueError):
        query.recording(spelling)
      with self.assertRaises(ValueError):
        query.recording_for_user(71, spelling)
