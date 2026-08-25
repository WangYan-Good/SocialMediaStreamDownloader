import unittest
from datetime import datetime

from flask import Flask
from backend.src.unit_test.auth_context import install_test_auth

from backend.src.database.query.owner_history import OwnerHistoryPage
from backend.src.database.schema_guard import DatabaseWriteBlocked
from backend.src.service.live_probe import ProbeBatchError
from backend.src.service.owner_preference import (
  OwnerNotFound,
  OwnerPreferenceResult,
  OwnerPreferenceValidationError,
)
from backend.src.web.history_routes import (
  HistoryRuntime,
  HistoryUnavailable,
  build_history_blueprint,
)


class FakeQuery:
  def __init__(self, page=None, sessions=(), error=None):
    self._page = page
    self._sessions = sessions
    self._error = error
    self.filters = []

  def search(self, owner_filter):
    if self._error is not None:
      raise self._error
    self.filters.append(owner_filter)
    return self._page

  def sessions(self, owner_user_id, platform, limit):
    if self._error is not None:
      raise self._error
    self.calls = (owner_user_id, platform, limit)
    return self._sessions


class FakeProbeService:
  def __init__(self, batch=None, error=None, task_id="task-1"):
    self._batch = batch
    self._error = error
    self._task_id = task_id
    self.submitted = None

  def submit(self, owner_user_ids):
    if self._error is not None:
      raise self._error
    self.submitted = owner_user_ids
    return "batch-1"

  def snapshot(self, batch_id):
    if self._batch is None or batch_id != "batch-1":
      return None
    return self._batch

  def task_id_for(self, batch_id):
    return self._task_id if batch_id == "batch-1" else None


class FakePreferenceService:
  def __init__(self, result=None, error=None):
    self.result = result
    self.error = error
    self.calls = []

  def update(self, owner_user_id, payload):
    self.calls.append((owner_user_id, payload))
    if self.error is not None:
      raise self.error
    return self.result


class FakeRuntime:
  def __init__(
    self,
    query=None,
    probe_service=None,
    preference_service=None,
    unavailable=None,
  ):
    self._query = query
    self._probe_service = probe_service
    self._preference_service = preference_service
    self._unavailable = unavailable

  def page_size_limit(self):
    return 10

  def query(self):
    if self._unavailable is not None:
      raise self._unavailable
    return self._query

  def probe_service(self):
    if self._unavailable is not None:
      raise self._unavailable
    return self._probe_service

  def preference_service(self):
    if self._unavailable is not None:
      raise self._unavailable
    return self._preference_service


def build_client(runtime):
  app = Flask(__name__)
  install_test_auth(app)
  app.register_blueprint(build_history_blueprint(runtime))
  return app.test_client()


class HistoryListingApiTest(unittest.TestCase):
  def test_owner_rows_are_serialised_with_iso_timestamps(self):
    page = OwnerHistoryPage(
      total=1,
      page=1,
      page_size=10,
      items=(
        {
          "owner_user_id": "1",
          "nickname": "Host",
          "actived_count": 3,
          "score": 60,
          "last_live_status": 2,
          "last_checked_at": datetime(2026, 8, 10, 12, 0, 0),
          "last_room_id": "room-1",
        },
      ),
    )
    client = build_client(FakeRuntime(query=FakeQuery(page=page)))

    response = client.get("/api/history/owners")
    body = response.get_json()

    self.assertEqual(200, response.status_code)
    self.assertEqual(1, body["data"]["total"])
    item = body["data"]["items"][0]
    self.assertEqual("2026-08-10T12:00:00.000", item["last_checked_at"])
    self.assertTrue(item["favorite"])

  def test_an_owner_without_a_score_is_not_marked_favorite(self):
    page = OwnerHistoryPage(
      total=1, page=1, page_size=10, items=({"owner_user_id": "1", "score": None},)
    )
    client = build_client(FakeRuntime(query=FakeQuery(page=page)))

    body = client.get("/api/history/owners").get_json()

    self.assertFalse(body["data"]["items"][0]["favorite"])

  def test_an_invalid_filter_is_a_client_error(self):
    client = build_client(FakeRuntime(query=FakeQuery()))

    response = client.get("/api/history/owners?sort=nonsense")

    self.assertEqual(400, response.status_code)
    self.assertEqual("error", response.get_json()["status"])

  def test_a_disabled_database_degrades_to_service_unavailable(self):
    client = build_client(
      FakeRuntime(unavailable=HistoryUnavailable("历史功能需要启用数据库"))
    )

    response = client.get("/api/history/owners")

    self.assertEqual(503, response.status_code)
    self.assertEqual("历史功能需要启用数据库", response.get_json()["message"])

  def test_an_unexpected_failure_does_not_leak_details(self):
    client = build_client(
      FakeRuntime(query=FakeQuery(error=RuntimeError("connection string leaked")))
    )

    response = client.get("/api/history/owners")

    self.assertEqual(500, response.status_code)
    self.assertNotIn("leaked", response.get_json()["message"])


class HistorySessionsApiTest(unittest.TestCase):
  def test_sessions_are_serialised_and_the_limit_is_capped(self):
    query = FakeQuery(
      sessions=(
        {
          "observed_at": datetime(2026, 8, 9, 12, 0, 0),
          "room_id": "room-1",
          "title": "T",
          "room_status": 2,
        },
      )
    )
    client = build_client(FakeRuntime(query=query))

    response = client.get("/api/history/owners/1/sessions?limit=500")
    body = response.get_json()

    self.assertEqual(200, response.status_code)
    self.assertEqual(100, query.calls[2])
    self.assertEqual("2026-08-09T12:00:00.000", body["data"]["items"][0]["observed_at"])

  def test_a_non_positive_limit_is_rejected(self):
    client = build_client(FakeRuntime(query=FakeQuery()))

    self.assertEqual(400, client.get("/api/history/owners/1/sessions?limit=0").status_code)
    self.assertEqual(400, client.get("/api/history/owners/1/sessions?limit=x").status_code)


class OwnerPreferenceApiTest(unittest.TestCase):
  def build_preference_client(self, result=None, error=None):
    service = FakePreferenceService(result=result, error=error)
    return build_client(FakeRuntime(preference_service=service)), service

  def test_score_zero_is_returned_as_a_favorite(self):
    client, service = self.build_preference_client(
      OwnerPreferenceResult("owner-1", True, 0)
    )

    response = client.patch(
      "/api/history/owners/owner-1/preference",
      json={"favorite": True, "score": 0},
    )

    self.assertEqual(200, response.status_code)
    self.assertEqual(
      {"owner_user_id": "owner-1", "favorite": True, "score": 0},
      response.get_json()["data"],
    )
    self.assertEqual(
      [("owner-1", {"favorite": True, "score": 0})], service.calls
    )

  def test_removal_returns_a_null_score(self):
    client, unused = self.build_preference_client(
      OwnerPreferenceResult("owner-1", False, None)
    )

    body = client.patch(
      "/api/history/owners/owner-1/preference", json={"favorite": False}
    ).get_json()

    self.assertFalse(body["data"]["favorite"])
    self.assertIsNone(body["data"]["score"])

  def test_non_json_and_non_mapping_bodies_are_rejected(self):
    client, unused = self.build_preference_client()

    self.assertEqual(
      400,
      client.patch(
        "/api/history/owners/owner-1/preference",
        data="x",
        content_type="text/plain",
      ).status_code,
    )
    self.assertEqual(
      400,
      client.patch(
        "/api/history/owners/owner-1/preference", json=["not", "a", "mapping"]
      ).status_code,
    )

  def test_validation_and_unknown_owner_are_mapped_to_400_and_404(self):
    invalid, unused = self.build_preference_client(
      error=OwnerPreferenceValidationError("favorite 必须是 boolean")
    )
    missing, unused = self.build_preference_client(
      error=OwnerNotFound("主播账号不存在或尚未进入历史记录")
    )

    self.assertEqual(
      400,
      invalid.patch(
        "/api/history/owners/owner-1/preference", json={"favorite": "false"}
      ).status_code,
    )
    self.assertEqual(
      404,
      missing.patch(
        "/api/history/owners/missing/preference", json={"favorite": False}
      ).status_code,
    )

  def test_schema_and_database_unavailability_are_service_unavailable(self):
    blocked, unused = self.build_preference_client(
      error=DatabaseWriteBlocked("schema state is behind")
    )
    unavailable = build_client(
      FakeRuntime(unavailable=HistoryUnavailable("数据库暂时不可用"))
    )

    self.assertEqual(
      503,
      blocked.patch(
        "/api/history/owners/owner-1/preference", json={"favorite": False}
      ).status_code,
    )
    self.assertEqual(
      503,
      unavailable.patch(
        "/api/history/owners/owner-1/preference", json={"favorite": False}
      ).status_code,
    )

  def test_unexpected_failure_is_generic_and_methods_are_patch_only(self):
    client, unused = self.build_preference_client(
      error=RuntimeError("database password leaked")
    )

    response = client.patch(
      "/api/history/owners/owner-1/preference", json={"favorite": False}
    )

    self.assertEqual(500, response.status_code)
    self.assertNotIn("password", response.get_json()["message"])
    for method in (client.get, client.post, client.delete):
      with self.subTest(method=method.__name__):
        self.assertEqual(
          405, method("/api/history/owners/owner-1/preference").status_code
        )


class LiveProbeApiTest(unittest.TestCase):
  def setUp(self):
    self.batch = {
      "batch_id": "batch-1",
      "done": False,
      "items": [
        {
          "owner_user_id": "1",
          "state": "living",
          "checked_at": datetime(2026, 8, 10, 12, 0, 0),
        }
      ],
    }

  def test_a_submitted_batch_is_accepted_with_its_first_snapshot(self):
    service = FakeProbeService(batch=self.batch)
    client = build_client(FakeRuntime(probe_service=service))

    response = client.post("/api/live/probe", json={"owner_user_ids": ["1"]})
    body = response.get_json()

    self.assertEqual(202, response.status_code)
    self.assertEqual("batch-1", body["data"]["batch_id"])
    self.assertEqual("2026-08-10T12:00:00.000", body["data"]["items"][0]["checked_at"])
    self.assertEqual(["1"], service.submitted)

  def test_an_accepted_batch_names_the_task_mirroring_it(self):
    client = build_client(
      FakeRuntime(probe_service=FakeProbeService(batch=self.batch, task_id="task-7"))
    )

    body = client.post("/api/live/probe", json={"owner_user_ids": ["1"]}).get_json()

    self.assertEqual("task-7", body["data"]["task_id"])

  def test_a_batch_nothing_is_mirroring_reports_a_null_task(self):
    client = build_client(
      FakeRuntime(probe_service=FakeProbeService(batch=self.batch, task_id=None))
    )

    response = client.post("/api/live/probe", json={"owner_user_ids": ["1"]})
    body = response.get_json()

    ##
    ## The field is present and null rather than absent: the response shape must
    ## not depend on whether mirroring happens to be wired up.
    ##
    self.assertEqual(202, response.status_code)
    self.assertIn("task_id", body["data"])
    self.assertIsNone(body["data"]["task_id"])
    self.assertEqual("batch-1", body["data"]["batch_id"])

  def test_the_accepted_response_keeps_exactly_its_legacy_fields(self):
    client = build_client(FakeRuntime(probe_service=FakeProbeService(batch=self.batch)))

    body = client.post("/api/live/probe", json={"owner_user_ids": ["1"]}).get_json()

    self.assertEqual({"batch_id", "task_id", "done", "items"}, set(body["data"]))
    self.assertIs(False, body["data"]["done"])
    self.assertEqual("living", body["data"]["items"][0]["state"])

  def test_a_non_json_or_malformed_body_is_rejected(self):
    client = build_client(FakeRuntime(probe_service=FakeProbeService()))

    self.assertEqual(400, client.post("/api/live/probe", data="x").status_code)
    self.assertEqual(400, client.post("/api/live/probe", json={}).status_code)
    self.assertEqual(
      400, client.post("/api/live/probe", json={"owner_user_ids": "1"}).status_code
    )

  def test_a_rejected_batch_size_is_reported_to_the_caller(self):
    client = build_client(
      FakeRuntime(probe_service=FakeProbeService(error=ProbeBatchError("too many")))
    )

    response = client.post("/api/live/probe", json={"owner_user_ids": ["1"]})

    self.assertEqual(400, response.status_code)
    self.assertEqual("too many", response.get_json()["message"])

  def test_reading_a_known_batch_returns_its_snapshot(self):
    client = build_client(FakeRuntime(probe_service=FakeProbeService(batch=self.batch)))

    response = client.get("/api/live/probe/batch-1")

    self.assertEqual(200, response.status_code)
    self.assertEqual("batch-1", response.get_json()["data"]["batch_id"])

  def test_an_expired_or_unknown_batch_is_not_found(self):
    client = build_client(FakeRuntime(probe_service=FakeProbeService()))

    self.assertEqual(404, client.get("/api/live/probe/missing").status_code)

  def test_polling_a_batch_is_untouched_by_the_task_migration(self):
    client = build_client(FakeRuntime(probe_service=FakeProbeService(batch=self.batch)))

    response = client.get("/api/live/probe/batch-1")
    body = response.get_json()

    ##
    ## The polling contract the current page depends on, asserted whole.  No
    ## task field appears here: this endpoint answers about the legacy batch and
    ## a browser wanting the task reads /api/tasks/<task_id> instead.
    ##
    self.assertEqual(200, response.status_code)
    self.assertEqual("success", body["status"])
    self.assertEqual({"batch_id", "done", "items"}, set(body["data"]))
    self.assertEqual("batch-1", body["data"]["batch_id"])
    self.assertIs(False, body["data"]["done"])
    self.assertEqual(
      {"owner_user_id": "1", "state": "living", "checked_at": "2026-08-10T12:00:00.000"},
      body["data"]["items"][0],
    )


class HistoryRuntimeTest(unittest.TestCase):
  def test_a_disabled_database_is_reported_as_unavailable(self):
    runtime = HistoryRuntime(config_loader=lambda: {"database": {"enable": False}})

    with self.assertRaises(HistoryUnavailable):
      runtime.query()

  def test_the_page_size_limit_comes_from_configuration(self):
    runtime = HistoryRuntime(config_loader=lambda: {"history": {"page_size_limit": 4}})

    self.assertEqual(4, runtime.page_size_limit())

  def test_a_missing_page_size_limit_falls_back_to_ten(self):
    runtime = HistoryRuntime(config_loader=lambda: {})

    self.assertEqual(10, runtime.page_size_limit())


class FakeDownloader:
  def __init__(self):
    self.prober = object()

  def _database_if_ready(self):
    return None


class HistoryRuntimeProbeWiringTest(unittest.TestCase):
  """The probe service must be given the app's task service, not find its own."""

  def build_runtime(self, task_service=None):
    settings = {
      "database": {"enable": True},
      "platform": {
        "douyin": {
          "live": {
            "probe": {
              "max_batch_size": 5,
              "concurrency": 2,
              "cache_ttl_seconds": 60,
              "batch_retention_seconds": 600,
            }
          }
        }
      },
    }
    runtime = HistoryRuntime(
      config_loader=lambda: settings,
      downloader_factory=FakeDownloader,
      task_service=task_service,
    )
    ##
    ## The query side would open a real database handle, which probing does not
    ## need for this wiring question.
    ##
    runtime.query = lambda: FakeQuery()
    return runtime

  def test_the_probe_service_reports_into_the_injected_task_service(self):
    tasks = object()
    runtime = self.build_runtime(task_service=tasks)

    self.assertIs(tasks, runtime.probe_service().task_service)

  def test_a_runtime_without_a_task_service_still_builds_a_prober(self):
    runtime = self.build_runtime()

    self.assertIsNone(runtime.probe_service().task_service)

  def test_the_probe_service_is_built_once_and_kept(self):
    runtime = self.build_runtime(task_service=object())

    ##
    ## Rebuilding per request would hand every probe a fresh batch store, so a
    ## browser polling the batch it just started would be told it never existed.
    ##
    self.assertIs(runtime.probe_service(), runtime.probe_service())


if __name__ == "__main__":
  unittest.main()
