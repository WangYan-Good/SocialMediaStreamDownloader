import unittest
from datetime import datetime, timedelta

from flask import Flask

from backend.src.task.model import (
  ITEM_STATE_FAILED,
  ITEM_STATE_RUNNING,
  TASK_TYPE_LIVE_PROBE,
  TASK_TYPE_LIVE_RECORD,
  TASK_TYPE_OWNER_BATCH_DOWNLOAD,
  TASK_TYPE_POST_DOWNLOAD,
)
from backend.src.task.service import TaskService
from backend.src.task.store import TaskStore
from backend.src.web.task_routes import (
  TASK_SERVICE_KEY,
  build_task_blueprint,
  install_task_service,
)


class FakeClock:
  def __init__(self, start=datetime(2026, 8, 13, 9, 30, 15, 250000)):
    self.wall = start
    self.mono = 0.0

  def now(self):
    return self.wall

  def monotonic(self):
    return self.mono

  def advance(self, seconds):
    self.wall = self.wall + timedelta(seconds=seconds)
    self.mono += seconds


def build_app(service=None, clock=None):
  """A bare app carrying only the task blueprint, as the routes see it."""
  if service is None:
    clock = clock if clock is not None else FakeClock()
    service = TaskService(
      store=TaskStore(clock=clock.now, monotonic_clock=clock.monotonic)
    )
  app = Flask(__name__)
  app.config["TESTING"] = True
  install_task_service(app, service)
  app.register_blueprint(build_task_blueprint())
  return app, service


class TaskListEndpointTest(unittest.TestCase):
  def test_an_empty_task_centre_answers_with_an_empty_page(self):
    app, service = build_app()

    response = app.test_client().get("/api/tasks")

    self.assertEqual(response.status_code, 200)
    self.assertEqual(
      response.get_json(),
      {"status": "success", "code": 200, "data": {"items": [], "total": 0}},
    )

  def test_tasks_are_listed_newest_first(self):
    app, service = build_app()
    first = service.create_task(TASK_TYPE_LIVE_PROBE, title="探测")
    second = service.create_task(TASK_TYPE_POST_DOWNLOAD, title="下载")

    body = app.test_client().get("/api/tasks").get_json()

    self.assertEqual(body["data"]["total"], 2)
    self.assertEqual(
      [item["task_id"] for item in body["data"]["items"]],
      [second["task_id"], first["task_id"]],
    )

  def test_the_running_filter_narrows_the_page(self):
    app, service = build_app()
    service.create_task(TASK_TYPE_LIVE_PROBE)
    running = service.create_task(TASK_TYPE_POST_DOWNLOAD)
    service.start_task(running["task_id"])

    body = app.test_client().get("/api/tasks?state=running").get_json()

    self.assertEqual(body["data"]["total"], 1)
    self.assertEqual(body["data"]["items"][0]["task_id"], running["task_id"])

  def test_the_type_filter_narrows_the_page(self):
    app, service = build_app()
    probe = service.create_task(TASK_TYPE_LIVE_PROBE)
    service.create_task(TASK_TYPE_POST_DOWNLOAD)

    body = app.test_client().get("/api/tasks?type=live_probe").get_json()

    self.assertEqual(body["data"]["total"], 1)
    self.assertEqual(body["data"]["items"][0]["task_id"], probe["task_id"])

  def test_both_filters_apply_together(self):
    app, service = build_app()
    service.create_task(TASK_TYPE_LIVE_PROBE)

    body = app.test_client().get(
      "/api/tasks?state=running&type=live_probe"
    ).get_json()

    self.assertEqual(body["data"], {"items": [], "total": 0})

  def test_a_limit_shortens_the_page_without_hiding_the_count(self):
    """The UI needs to say "showing 1 of 3", so total ignores the limit."""
    app, service = build_app()
    for _ in range(3):
      service.create_task(TASK_TYPE_LIVE_PROBE)

    body = app.test_client().get("/api/tasks?limit=1").get_json()

    self.assertEqual(body["data"]["total"], 3)
    self.assertEqual(len(body["data"]["items"]), 1)

  def test_an_unknown_state_filter_is_a_bad_request(self):
    app, service = build_app()

    response = app.test_client().get("/api/tasks?state=done")

    self.assertEqual(response.status_code, 400)
    self.assertEqual(response.get_json()["status"], "error")

  def test_an_unknown_type_filter_is_a_bad_request(self):
    app, service = build_app()

    response = app.test_client().get("/api/tasks?type=post_dowload")

    self.assertEqual(response.status_code, 400)

  def test_a_limit_that_is_not_a_number_is_a_bad_request(self):
    app, service = build_app()

    response = app.test_client().get("/api/tasks?limit=abc")

    self.assertEqual(response.status_code, 400)

  def test_a_limit_below_one_is_a_bad_request(self):
    app, service = build_app()

    response = app.test_client().get("/api/tasks?limit=0")

    self.assertEqual(response.status_code, 400)

  def test_an_empty_filter_is_treated_as_no_filter(self):
    """A UI that always sends its filter fields must not be punished for it."""
    app, service = build_app()
    service.create_task(TASK_TYPE_LIVE_PROBE)

    body = app.test_client().get("/api/tasks?state=&type=").get_json()

    self.assertEqual(body["data"]["total"], 1)


class TaskDetailEndpointTest(unittest.TestCase):
  def test_an_unknown_task_is_not_found(self):
    app, service = build_app()

    response = app.test_client().get("/api/tasks/nope")

    self.assertEqual(response.status_code, 404)
    body = response.get_json()
    self.assertEqual(body["status"], "error")
    self.assertEqual(body["code"], 404)

  def test_a_task_serializes_every_documented_field(self):
    clock = FakeClock()
    app, service = build_app(clock=clock)
    task = service.create_task(
      TASK_TYPE_OWNER_BATCH_DOWNLOAD,
      title="批量下载",
      metadata={"sec_user_id": "MS4w"},
      items=["7657271784144009946", "7657271784144009947"],
    )
    clock.advance(1)
    service.start_task(task["task_id"])
    service.update_item(
      task["task_id"],
      "7657271784144009946",
      state=ITEM_STATE_RUNNING,
      advance_progress=False,
    )

    body = app.test_client().get("/api/tasks/" + task["task_id"]).get_json()
    data = body["data"]

    self.assertEqual(body["status"], "success")
    self.assertEqual(body["code"], 200)
    self.assertEqual(data["task_id"], task["task_id"])
    self.assertEqual(data["task_type"], "owner_batch_download")
    self.assertEqual(data["state"], "running")
    self.assertEqual(data["title"], "批量下载")
    self.assertIsNone(data["message"])
    self.assertEqual(data["created_at"], "2026-08-13T09:30:15.250")
    self.assertEqual(data["started_at"], "2026-08-13T09:30:16.250")
    self.assertIsNone(data["finished_at"])
    self.assertEqual(data["progress"], {"current": 0, "total": 2})
    self.assertEqual(data["metadata"], {"sec_user_id": "MS4w"})
    self.assertEqual(
      data["items"],
      [
        {
          "key": "7657271784144009946",
          "state": "running",
          "message": None,
          "metadata": {},
        },
        {
          "key": "7657271784144009947",
          "state": "pending",
          "message": None,
          "metadata": {},
        },
      ],
    )

  def test_a_finished_task_reports_when_it_ended(self):
    clock = FakeClock()
    app, service = build_app(clock=clock)
    task = service.create_task(TASK_TYPE_POST_DOWNLOAD)
    service.start_task(task["task_id"])
    clock.advance(30)
    service.finish_partial(task["task_id"], message="2 个中有 1 个失败")

    data = app.test_client().get("/api/tasks/" + task["task_id"]).get_json()["data"]

    self.assertEqual(data["state"], "partial")
    self.assertEqual(data["message"], "2 个中有 1 个失败")
    self.assertEqual(data["finished_at"], "2026-08-13T09:30:45.250")

  def test_a_continuous_task_reports_an_unknown_total(self):
    """A recording has no final count; the frontend must not divide by it."""
    app, service = build_app()
    task = service.create_task(TASK_TYPE_LIVE_RECORD, title="录制")
    service.start_task(task["task_id"])
    service.update_progress(task["task_id"], current=97)

    data = app.test_client().get("/api/tasks/" + task["task_id"]).get_json()["data"]

    self.assertEqual(data["progress"], {"current": 97, "total": None})

  def test_the_platform_reaches_the_browser_through_metadata(self):
    """A second platform must be readable without minting a new task type."""
    app, service = build_app()
    task = service.create_task(
      TASK_TYPE_POST_DOWNLOAD,
      title="下载作品",
      metadata={"platform": "douyin", "aweme_id": "7657271784144009946"},
    )

    data = app.test_client().get("/api/tasks/" + task["task_id"]).get_json()["data"]

    self.assertEqual(data["task_type"], "post_download")
    self.assertEqual(data["metadata"]["platform"], "douyin")

  def test_nested_metadata_reaches_the_browser_intact(self):
    app, service = build_app()
    task = service.create_task(
      TASK_TYPE_OWNER_BATCH_DOWNLOAD,
      metadata={"filters": {"types": ["video", "image"]}},
    )

    data = app.test_client().get("/api/tasks/" + task["task_id"]).get_json()["data"]

    self.assertEqual(data["metadata"], {"filters": {"types": ["video", "image"]}})

  def test_a_narrated_task_reports_its_current_stage(self):
    app, service = build_app()
    task = service.create_task(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=["a", "b"])
    service.start_task(task["task_id"])
    service.update_message(task["task_id"], "正在读取第 3 页")

    data = app.test_client().get("/api/tasks/" + task["task_id"]).get_json()["data"]

    self.assertEqual(data["state"], "running")
    self.assertEqual(data["message"], "正在读取第 3 页")

  def test_an_item_message_reaches_the_browser(self):
    app, service = build_app()
    task = service.create_task(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=["a"])
    service.update_item(
      task["task_id"], "a", state=ITEM_STATE_FAILED, message="下载超时"
    )

    data = app.test_client().get("/api/tasks/" + task["task_id"]).get_json()["data"]

    self.assertEqual(data["items"][0]["message"], "下载超时")
    self.assertEqual(data["items"][0]["state"], "failed")


class TaskServiceWiringTest(unittest.TestCase):
  """One store per process: what a worker writes, the next request must read."""

  def test_the_service_is_reachable_through_the_app_extensions(self):
    app, service = build_app()

    self.assertIs(app.extensions[TASK_SERVICE_KEY], service)

  def test_installing_without_a_service_still_provides_one(self):
    app = Flask(__name__)

    service = install_task_service(app)

    self.assertIsInstance(service, TaskService)
    self.assertIs(app.extensions[TASK_SERVICE_KEY], service)

  def test_every_request_sees_the_same_store(self):
    app, service = build_app()
    client = app.test_client()

    task = service.create_task(TASK_TYPE_POST_DOWNLOAD)
    first = client.get("/api/tasks").get_json()
    service.start_task(task["task_id"])
    second = client.get("/api/tasks").get_json()

    self.assertEqual(first["data"]["items"][0]["state"], "pending")
    self.assertEqual(second["data"]["items"][0]["state"], "running")

  def test_a_missing_service_is_reported_not_crashed(self):
    """Registering the blueprint without wiring is a deployment bug, not a 500 page."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(build_task_blueprint())

    response = app.test_client().get("/api/tasks")

    self.assertEqual(response.status_code, 503)
    self.assertEqual(response.get_json()["status"], "error")


class ApplicationFactoryTest(unittest.TestCase):
  """The task centre must be wired by the factory, not by each caller."""

  def build_app(self):
    import server
    from backend.src.unit_test.config_fixture import unified_config

    return server.create_app(
      config=unified_config(),
      schema_guard_factory=lambda config: object(),
    )

  def test_a_configured_app_carries_one_task_service(self):
    app = self.build_app()

    self.assertIsInstance(app.extensions[TASK_SERVICE_KEY], TaskService)

  def test_a_configured_app_serves_the_task_endpoints(self):
    app = self.build_app()

    listing = app.test_client().get("/api/tasks")
    missing = app.test_client().get("/api/tasks/nope")

    self.assertEqual(listing.status_code, 200)
    self.assertEqual(listing.get_json()["data"], {"items": [], "total": 0})
    self.assertEqual(missing.status_code, 404)

  def test_two_apps_do_not_share_their_tasks(self):
    """Each application owns its own store, as every other extension does."""
    first = self.build_app()
    second = self.build_app()

    first.extensions[TASK_SERVICE_KEY].create_task(TASK_TYPE_LIVE_PROBE)

    self.assertEqual(len(second.extensions[TASK_SERVICE_KEY].list_tasks()), 0)


if __name__ == "__main__":
  unittest.main()
