import unittest
from datetime import datetime

from flask import Flask

from backend.src.database.query.owner_history import OwnerHistoryPage
from backend.src.service.live_probe import ProbeBatchError
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
  def __init__(self, batch=None, error=None):
    self._batch = batch
    self._error = error
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


class FakeRuntime:
  def __init__(self, query=None, probe_service=None, unavailable=None):
    self._query = query
    self._probe_service = probe_service
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


def build_client(runtime):
  app = Flask(__name__)
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


if __name__ == "__main__":
  unittest.main()
