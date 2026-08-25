import unittest

from flask import Flask
from backend.src.unit_test.auth_context import install_test_auth

from backend.src.service.job_store import (
  JOB_DONE,
  JOB_ERROR,
  STATE_DONE,
  STATE_ERROR,
  STATE_SKIPPED,
  JobStore,
)
from backend.src.service.owner_task_mirror import PLATFORM_DOUYIN
from backend.src.service.post_download_job import PayloadCache, PostDownloadJobService
from backend.src.task.model import (
  ITEM_STATE_FAILED,
  ITEM_STATE_PENDING,
  ITEM_STATE_RUNNING,
  ITEM_STATE_SKIPPED,
  ITEM_STATE_SUCCESS,
  TASK_STATE_FAILED,
  TASK_STATE_PARTIAL,
  TASK_STATE_RUNNING,
  TASK_STATE_SUCCESS,
  TASK_TYPE_OWNER_BATCH_DOWNLOAD,
)
from backend.src.task.service import TaskService
from backend.src.web.owner_routes import OwnerRuntime, build_owner_blueprint
from backend.src.web.task_routes import build_task_blueprint, install_task_service
from backend.src.unit_test.test_post_download_job import (
  SEC_UID,
  SWITCHES,
  OfflineTestCase,
  StubApi,
  StubDownloader,
  page,
  post_item,
)


def build_service(
  downloader=None,
  api=None,
  cache=None,
  store=None,
  task_service=None,
  post_pool=None,
  post_concurrency=1,
):
  """A service wired for dual write, with every outbound call stubbed."""
  return PostDownloadJobService(
    downloader=downloader if downloader is not None else StubDownloader(),
    api=api,
    store=store if store is not None else JobStore(),
    cache=cache if cache is not None else PayloadCache(),
    media_switches=SWITCHES,
    task_service=task_service if task_service is not None else TaskService(),
    post_pool=post_pool,
    post_concurrency=post_concurrency,
  )


def selected_job(service, ids):
  service.cache.remember([post_item(value) for value in ids])
  return service.start_selected(ids, share_url="https://share/")


def task_of(service, job_id):
  return service.task_service.get_task(service.task_id_for(job_id))


def internal_job_id_for_task(service, task_id):
  return service.task_service.get_task(task_id)["metadata"]["legacy_job_id"]


class SelectedTaskTest(OfflineTestCase):
  """The posts the user ticked, mirrored onto the unified task."""

  def test_a_selected_download_creates_an_owner_batch_task(self):
    service = build_service()

    job_id = selected_job(service, ["1", "2"])
    task = task_of(service, job_id)

    self.assertEqual(task["task_type"], TASK_TYPE_OWNER_BATCH_DOWNLOAD)
    self.assertEqual(task["metadata"]["platform"], PLATFORM_DOUYIN)
    self.assertEqual(task["metadata"]["legacy_job_id"], job_id)
    self.assertEqual(task["metadata"]["mode"], "selected")
    self.assertEqual(task["metadata"]["requested_count"], 2)

  def test_the_task_id_is_not_the_job_id(self):
    """Two independent identifiers, associated by record rather than by shape."""
    service = build_service()

    job_id = selected_job(service, ["1"])

    self.assertNotEqual(service.task_id_for(job_id), job_id)

  def test_an_unknown_job_has_no_task(self):
    service = build_service()

    self.assertIsNone(service.task_id_for("never-started"))

  def test_the_owner_nickname_is_used_when_it_is_already_known(self):
    """The payload is already in hand; no extra platform request is made."""
    service = build_service()
    api = service.api

    job_id = selected_job(service, ["1"])

    self.assertEqual(task_of(service, job_id)["title"], "下载主播的作品")
    self.assertIsNone(api)

  def test_every_selected_post_is_an_item(self):
    service = build_service()

    job_id = selected_job(service, ["1", "2", "3"])
    task = task_of(service, job_id)

    self.assertEqual([item["key"] for item in task["items"]], ["1", "2", "3"])
    self.assertEqual(task["progress"]["total"], 3)

  def test_a_selection_with_repeats_counts_each_post_once(self):
    """A total of 3 over 2 items would strand the bar at 2 / 3 for the whole run."""
    service = build_service()
    service.cache.remember([post_item("1"), post_item("2")])
    created = []
    original = service.task_service.create_task

    def record(*args, **kwargs):
      task = original(*args, **kwargs)
      created.append(task)
      return task

    service.task_service.create_task = record
    job_id = service.start_selected(["1", "2", "1"])

    self.assertEqual(created[0]["progress"], {"current": 0, "total": 2})
    self.assertEqual(created[0]["metadata"]["requested_count"], 2)
    self.assertEqual([item["key"] for item in created[0]["items"]], ["1", "2"])
    self.assertEqual(task_of(service, job_id)["progress"], {"current": 2, "total": 2})

  def test_a_selection_with_repeats_leaves_the_legacy_job_as_it_was(self):
    """Legacy counting is not this migration's business to change."""
    service = build_service()
    service.cache.remember([post_item("1"), post_item("2")])

    job_id = service.start_selected(["1", "2", "1"])

    self.assertEqual(service.store.snapshot(job_id)["total"], 3)
    self.assertEqual(service.store.snapshot(job_id)["state"], JOB_DONE)

  def test_progress_never_promises_more_than_there_is_to_do(self):
    service = build_service(downloader=StubDownloader(failures={"2": RuntimeError("x")}))
    service.cache.remember([post_item(value) for value in ("1", "2", "3")])

    job_id = service.start_selected(["1", "2", "3", "2"])
    progress = task_of(service, job_id)["progress"]

    self.assertEqual(progress["current"], progress["total"])
    self.assertEqual(progress["total"], 3)

  def test_a_downloaded_post_becomes_a_successful_item(self):
    service = build_service()

    job_id = selected_job(service, ["1"])
    item = task_of(service, job_id)["items"][0]

    self.assertEqual(item["state"], ITEM_STATE_SUCCESS)
    self.assertEqual(item["metadata"]["saved_count"], 3)
    self.assertEqual(item["metadata"]["media_count"], 3)
    self.assertEqual(item["metadata"]["save_dir"], "/tmp/1")

  def test_an_already_downloaded_post_becomes_a_skipped_item(self):
    service = build_service(downloader=StubDownloader(skips=["1"]))

    job_id = selected_job(service, ["1"])
    item = task_of(service, job_id)["items"][0]

    self.assertEqual(item["state"], ITEM_STATE_SKIPPED)
    self.assertEqual(item["message"], "already downloaded")

  def test_a_post_with_nothing_downloadable_becomes_a_skipped_item(self):
    service = build_service()
    service.cache.remember([post_item("1", with_media=False)])

    job_id = service.start_selected(["1"])
    item = task_of(service, job_id)["items"][0]

    self.assertEqual(item["state"], ITEM_STATE_SKIPPED)

  def test_a_failing_post_becomes_a_failed_item(self):
    downloader = StubDownloader(failures={"1": RuntimeError("下载超时")})
    service = build_service(downloader=downloader)

    job_id = selected_job(service, ["1", "2"])
    items = task_of(service, job_id)["items"]

    self.assertEqual(items[0]["state"], ITEM_STATE_FAILED)
    self.assertEqual(items[0]["message"], "下载超时")
    self.assertEqual(items[1]["state"], ITEM_STATE_SUCCESS)

  def test_progress_counts_every_finished_post(self):
    """42 / 42 means processed, not "all of them worked"."""
    downloader = StubDownloader(failures={"2": RuntimeError("下载超时")}, skips=["3"])
    service = build_service(downloader=downloader)

    job_id = selected_job(service, ["1", "2", "3"])

    self.assertEqual(task_of(service, job_id)["progress"], {"current": 3, "total": 3})

  def test_all_downloaded_ends_the_task_successfully(self):
    service = build_service()

    job_id = selected_job(service, ["1", "2"])

    self.assertEqual(task_of(service, job_id)["state"], TASK_STATE_SUCCESS)

  def test_downloaded_and_already_present_still_ends_successfully(self):
    service = build_service(downloader=StubDownloader(skips=["2"]))

    job_id = selected_job(service, ["1", "2"])

    self.assertEqual(task_of(service, job_id)["state"], TASK_STATE_SUCCESS)

  def test_some_failed_ends_the_task_partial(self):
    downloader = StubDownloader(failures={"2": RuntimeError("下载超时")})
    service = build_service(downloader=downloader)

    job_id = selected_job(service, ["1", "2"])

    self.assertEqual(task_of(service, job_id)["state"], TASK_STATE_PARTIAL)

  def test_all_failed_ends_the_task_failed(self):
    downloader = StubDownloader(
      failures={"1": RuntimeError("下载超时"), "2": RuntimeError("下载超时")}
    )
    service = build_service(downloader=downloader)

    job_id = selected_job(service, ["1", "2"])

    self.assertEqual(task_of(service, job_id)["state"], TASK_STATE_FAILED)


class DownloadEverythingTaskTest(OfflineTestCase):
  """The owner walk, whose size is unknown until it ends."""

  def test_a_walk_starts_without_a_known_total(self):
    """The profile's aweme_count is a statistic, not a promise about the pages."""
    api = StubApi(pages=[page(["1"], 100, 0)])
    service = build_service(api=api)
    created = []
    original = service.task_service.create_task

    def record(*args, **kwargs):
      task = original(*args, **kwargs)
      created.append(task)
      return task

    service.task_service.create_task = record
    job_id = service.start_all(SEC_UID)

    self.assertEqual(created[0]["progress"], {"current": 0, "total": None})
    self.assertEqual(created[0]["items"], [])
    self.assertEqual(created[0]["metadata"]["mode"], "all")
    self.assertEqual(created[0]["metadata"]["sec_user_id"], SEC_UID)
    self.assertEqual(task_of(service, job_id)["metadata"]["sec_user_id"], SEC_UID)

  def test_discovery_never_guesses_at_a_total(self):
    """Until the walk ends there is no honest number to divide by."""
    api = StubApi(pages=[page(["1", "2"], 100, 1), page(["3"], 200, 0)])
    service = build_service(api=api)
    totals = []
    original = service.task_service.add_item

    def record(task_id, key, **kwargs):
      task = original(task_id, key, **kwargs)
      totals.append(task["progress"]["total"])
      return task

    service.task_service.add_item = record
    service.start_all(SEC_UID)

    self.assertEqual(totals, [None, None, None])

  def test_progress_never_promises_more_than_was_discovered(self):
    api = StubApi(pages=[page(["1", "2"], 100, 1), page(["2", "3"], 200, 0)])
    service = build_service(api=api)

    job_id = service.start_all(SEC_UID)
    task = task_of(service, job_id)

    self.assertEqual(task["progress"]["current"], task["progress"]["total"])
    self.assertEqual(task["progress"]["total"], len(task["items"]))

  def test_discovered_posts_become_items_in_page_order(self):
    api = StubApi(pages=[page(["1", "2"], 100, 1), page(["3"], 200, 0)])
    service = build_service(api=api)

    job_id = service.start_all(SEC_UID)
    task = task_of(service, job_id)

    self.assertEqual([item["key"] for item in task["items"]], ["1", "2", "3"])

  def test_the_final_total_is_what_was_discovered(self):
    api = StubApi(pages=[page(["1", "2"], 100, 1), page(["3"], 200, 0)])
    service = build_service(api=api)

    job_id = service.start_all(SEC_UID)

    self.assertEqual(task_of(service, job_id)["progress"], {"current": 3, "total": 3})

  def test_a_post_seen_twice_is_one_item(self):
    """Overlapping pages must not double the total the user is shown."""
    api = StubApi(pages=[page(["1", "2"], 100, 1), page(["2", "3"], 200, 0)])
    service = build_service(api=api)

    job_id = service.start_all(SEC_UID)
    task = task_of(service, job_id)

    self.assertEqual([item["key"] for item in task["items"]], ["1", "2", "3"])
    self.assertEqual(task["progress"], {"current": 3, "total": 3})

  def test_an_owner_with_no_posts_succeeds_without_inventing_progress(self):
    api = StubApi(pages=[page([], 0, 0)])
    service = build_service(api=api)

    job_id = service.start_all(SEC_UID)
    task = task_of(service, job_id)

    self.assertEqual(task["state"], TASK_STATE_SUCCESS)
    self.assertEqual(task["progress"], {"current": 0, "total": 0})
    self.assertEqual(task["items"], [])
    self.assertIsNotNone(task["message"])

  def test_a_walk_stopped_part_way_keeps_what_it_downloaded(self):
    api = StubApi(pages=[page(["1", "2"], 100, 1)], error_after=1)
    service = build_service(api=api)

    job_id = service.start_all(SEC_UID)
    task = task_of(service, job_id)

    self.assertEqual(task["state"], TASK_STATE_PARTIAL)
    self.assertIn("停在第 3 个作品", task["message"])
    self.assertEqual(task["progress"]["current"], 2)

  def test_a_walk_that_fails_immediately_fails_the_task(self):
    api = StubApi(pages=[], error_after=0)
    service = build_service(api=api)

    job_id = service.start_all(SEC_UID)

    self.assertEqual(task_of(service, job_id)["state"], TASK_STATE_FAILED)


class DualWriteTest(OfflineTestCase):
  """Both records must tell the same story, and legacy must not depend on task."""

  def test_the_legacy_job_still_receives_every_update(self):
    downloader = StubDownloader(failures={"2": RuntimeError("下载超时")}, skips=["3"])
    service = build_service(downloader=downloader)

    job_id = selected_job(service, ["1", "2", "3"])
    snapshot = service.store.snapshot(job_id)

    self.assertEqual(snapshot["state"], JOB_DONE)
    self.assertEqual(snapshot["total"], 3)
    self.assertEqual(snapshot["finished"], 3)
    self.assertEqual(
      [item["state"] for item in snapshot["items"]],
      [STATE_DONE, STATE_ERROR, STATE_SKIPPED],
    )

  def test_the_legacy_walk_report_is_unchanged(self):
    api = StubApi(pages=[page(["1", "2"], 100, 1)], error_after=1)
    service = build_service(api=api)

    job_id = service.start_all(SEC_UID)
    snapshot = service.store.snapshot(job_id)

    self.assertEqual(snapshot["state"], JOB_ERROR)
    self.assertEqual(snapshot["total"], 2)
    self.assertIn("停在第 3 个作品", snapshot["message"])

  def test_both_records_agree_on_every_post(self):
    downloader = StubDownloader(failures={"2": RuntimeError("下载超时")}, skips=["3"])
    service = build_service(downloader=downloader)

    job_id = selected_job(service, ["1", "2", "3"])
    legacy = {
      item["key"]: item["state"] for item in service.store.snapshot(job_id)["items"]
    }
    unified = {item["key"]: item["state"] for item in task_of(service, job_id)["items"]}

    self.assertEqual(legacy, {"1": STATE_DONE, "2": STATE_ERROR, "3": STATE_SKIPPED})
    self.assertEqual(
      unified,
      {"1": ITEM_STATE_SUCCESS, "2": ITEM_STATE_FAILED, "3": ITEM_STATE_SKIPPED},
    )

  def test_a_broken_task_layer_does_not_disturb_the_download(self):
    """Task mirroring is telemetry; the work and the legacy job must survive it."""

    class BrokenTaskService(TaskService):
      def update_item(self, *args, **kwargs):
        raise RuntimeError("task layer unavailable")

    downloader = StubDownloader()
    service = build_service(downloader=downloader, task_service=BrokenTaskService())

    job_id = selected_job(service, ["1", "2"])
    snapshot = service.store.snapshot(job_id)

    self.assertEqual([call[0] for call in downloader.calls], ["1", "2"])
    self.assertEqual(snapshot["state"], JOB_DONE)
    self.assertEqual(
      [item["state"] for item in snapshot["items"]], [STATE_DONE, STATE_DONE]
    )

  def test_a_service_without_a_task_layer_behaves_exactly_as_before(self):
    downloader = StubDownloader()
    service = PostDownloadJobService(
      downloader=downloader,
      store=JobStore(),
      cache=PayloadCache(),
      media_switches=SWITCHES,
    )
    service.cache.remember([post_item("1")])

    job_id = service.start_selected(["1"])
    snapshot = service.store.snapshot(job_id)

    self.assertEqual(snapshot["state"], JOB_DONE)
    self.assertIsNone(service.task_id_for(job_id))


class ConcurrentTaskTest(OfflineTestCase):
  """Posts download in parallel; the task must survive that."""

  def build_pool(self, workers):
    from concurrent.futures import ThreadPoolExecutor

    pool = ThreadPoolExecutor(max_workers=workers)
    self.addCleanup(pool.shutdown)
    return pool

  def test_no_progress_update_is_lost_when_posts_finish_together(self):
    ids = [str(index) for index in range(40)]
    service = build_service(
      post_pool=self.build_pool(8), post_concurrency=8
    )

    job_id = selected_job(service, ids)
    task = task_of(service, job_id)

    self.assertEqual(task["progress"], {"current": 40, "total": 40})
    self.assertEqual(len(task["items"]), 40)
    self.assertEqual({item["state"] for item in task["items"]}, {ITEM_STATE_SUCCESS})

  def test_the_task_reaches_a_terminal_state_exactly_once(self):
    ids = [str(index) for index in range(20)]
    service = build_service(post_pool=self.build_pool(8), post_concurrency=8)

    job_id = selected_job(service, ids)
    task_id = service.task_id_for(job_id)

    self.assertEqual(service.task_service.get_task(task_id)["state"], TASK_STATE_SUCCESS)

  def test_a_late_second_finish_leaves_both_records_alone(self):
    service = build_service()
    service.cache.remember([post_item("1")])
    job_id = selected_job(service, ["1"])
    legacy_before = service.store.snapshot(job_id)

    service._tasks.finish(job_id, message="迟到的结束", stopped_early=True)

    self.assertEqual(service.store.snapshot(job_id), legacy_before)
    task = task_of(service, job_id)
    self.assertEqual(task["state"], TASK_STATE_SUCCESS)
    self.assertNotEqual(task["message"], "迟到的结束")

  def test_two_workers_finishing_at_once_do_not_break_the_download(self):
    import threading

    downloader = StubDownloader()
    service = build_service(downloader=downloader)
    service.cache.remember([post_item("1"), post_item("2")])
    job_id = selected_job(service, ["1", "2"])
    ready = threading.Barrier(2)
    escaped = []

    def run():
      ready.wait()
      try:
        service._tasks.finish(job_id)
      except Exception as e:
        escaped.append(e)

    threads = [threading.Thread(target=run) for _ in range(2)]
    for thread in threads:
      thread.start()
    for thread in threads:
      thread.join()

    self.assertEqual(escaped, [])
    self.assertEqual([call[0] for call in downloader.calls], ["1", "2"])
    self.assertEqual(service.store.snapshot(job_id)["state"], JOB_DONE)
    self.assertEqual(task_of(service, job_id)["state"], TASK_STATE_SUCCESS)

  def test_a_parallel_walk_registers_each_post_once(self):
    api = StubApi(pages=[page(["1", "2", "3"], 100, 1), page(["3", "4"], 200, 0)])
    service = build_service(
      api=api, post_pool=self.build_pool(4), post_concurrency=4
    )

    job_id = service.start_all(SEC_UID)
    task = task_of(service, job_id)

    self.assertEqual(len(task["items"]), 4)
    self.assertEqual(task["progress"], {"current": 4, "total": 4})


class DownloadRuntime(OwnerRuntime):
  """An owner runtime whose only real part is the download service."""

  def __init__(self, service):
    self._service = service
    self.task_service = service.task_service

  def service(self):
    return self._service


def build_client(service):
  app = Flask(__name__)
  install_test_auth(app)
  app.config["TESTING"] = True
  install_task_service(app, service.task_service)
  app.register_blueprint(build_owner_blueprint(DownloadRuntime(service)))
  app.register_blueprint(build_task_blueprint())
  return app.test_client()


class OwnerDownloadApiTest(OfflineTestCase):
  """The public API exposes unified tasks while internal jobs keep executing."""

  def test_starting_a_selected_download_returns_only_the_task_id(self):
    service = build_service()
    service.cache.remember([post_item("1"), post_item("2")])

    response = build_client(service).post(
      "/api/owner/download", json={"aweme_ids": ["1", "2"]}
    )
    data = response.get_json()["data"]

    self.assertEqual(response.status_code, 200)
    self.assertEqual({"task_id"}, set(data))
    self.assertIsNotNone(data["task_id"])

  def test_starting_a_full_download_returns_only_the_task_id(self):
    service = build_service(api=StubApi(pages=[page(["1"], 100, 0)]))

    response = build_client(service).post(
      "/api/owner/download", json={"all": True, "sec_user_id": SEC_UID}
    )
    data = response.get_json()["data"]

    self.assertEqual(response.status_code, 200)
    self.assertEqual({"task_id"}, set(data))
    self.assertIsNotNone(data["task_id"])

  def test_the_new_task_is_readable_through_the_task_api(self):
    """One batch download, observable from the unified endpoint."""
    service = build_service()
    service.cache.remember([post_item("1"), post_item("2")])
    client = build_client(service)

    data = client.post(
      "/api/owner/download", json={"aweme_ids": ["1", "2"]}
    ).get_json()["data"]
    task = client.get("/api/tasks/" + data["task_id"]).get_json()["data"]

    self.assertEqual(task["task_type"], "owner_batch_download")
    self.assertEqual(task["state"], "success")
    self.assertEqual(task["progress"], {"current": 2, "total": 2})
    self.assertEqual(task["metadata"]["platform"], PLATFORM_DOUYIN)
    self.assertIsInstance(task["metadata"]["legacy_job_id"], str)
    self.assertNotEqual(task["metadata"]["legacy_job_id"], data["task_id"])
    self.assertEqual(
      [item["key"] for item in task["items"]], ["1", "2"]
    )

  def test_the_batch_is_listed_among_the_tasks(self):
    service = build_service()
    service.cache.remember([post_item("1")])
    client = build_client(service)

    client.post("/api/owner/download", json={"aweme_ids": ["1"]})
    listed = client.get("/api/tasks?type=owner_batch_download").get_json()["data"]

    self.assertEqual(listed["total"], 1)

  def test_the_public_job_polling_route_is_not_registered(self):
    service = build_service()
    app = Flask(__name__)
    install_test_auth(app)
    app.register_blueprint(build_owner_blueprint(DownloadRuntime(service)))

    self.assertFalse(any(
      str(rule).startswith("/api/owner/download/") and "GET" in rule.methods
      for rule in app.url_map.iter_rules()
    ))

  def test_a_runtime_without_task_wiring_still_starts_downloads(self):
    """task_id is absent, not fatal, when nothing is mirroring."""
    service = PostDownloadJobService(
      downloader=StubDownloader(),
      store=JobStore(),
      cache=PayloadCache(),
      media_switches=SWITCHES,
    )
    service.cache.remember([post_item("1")])
    app = Flask(__name__)
    install_test_auth(app)
    app.config["TESTING"] = True
    app.register_blueprint(build_owner_blueprint(DownloadRuntime(service)))

    data = app.test_client().post(
      "/api/owner/download", json={"aweme_ids": ["1"]}
    ).get_json()["data"]

    self.assertEqual({"task_id": None}, data)


class MirrorLifetimeTest(OfflineTestCase):
  """The job-to-task map lives with the service, not with a request."""

  def test_a_task_id_is_still_resolvable_after_the_request_ends(self):
    service = build_service()
    service.cache.remember([post_item("1")])
    client = build_client(service)

    data = client.post(
      "/api/owner/download", json={"aweme_ids": ["1"]}
    ).get_json()["data"]

    ##
    ## Read outside any request context at all: nothing about the association
    ## may depend on Flask being mid-request.
    ##
    job_id = internal_job_id_for_task(service, data["task_id"])
    self.assertEqual(service.task_id_for(job_id), data["task_id"])

  def test_the_map_survives_across_several_requests(self):
    service = build_service()
    service.cache.remember([post_item(value) for value in ("1", "2", "3")])
    client = build_client(service)

    first = client.post(
      "/api/owner/download", json={"aweme_ids": ["1"]}
    ).get_json()["data"]
    second = client.post(
      "/api/owner/download", json={"aweme_ids": ["2"]}
    ).get_json()["data"]
    third = client.post(
      "/api/owner/download", json={"aweme_ids": ["3"]}
    ).get_json()["data"]

    for started in (first, second, third):
      job_id = internal_job_id_for_task(service, started["task_id"])
      self.assertEqual(service.task_id_for(job_id), started["task_id"])
    self.assertEqual(len({first["task_id"], second["task_id"], third["task_id"]}), 3)

  def test_an_earlier_task_is_still_readable_after_later_ones_start(self):
    service = build_service()
    service.cache.remember([post_item("1"), post_item("2")])
    client = build_client(service)

    first = client.post(
      "/api/owner/download", json={"aweme_ids": ["1"]}
    ).get_json()["data"]
    client.post("/api/owner/download", json={"aweme_ids": ["2"]})
    response = client.get("/api/tasks/" + first["task_id"])

    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.get_json()["data"]["task_id"], first["task_id"])

  def test_every_request_reports_into_the_one_store(self):
    service = build_service()
    service.cache.remember([post_item("1"), post_item("2")])
    client = build_client(service)

    client.post("/api/owner/download", json={"aweme_ids": ["1"]})
    client.post("/api/owner/download", json={"aweme_ids": ["2"]})
    listed = client.get("/api/tasks?type=owner_batch_download").get_json()["data"]

    self.assertEqual(listed["total"], 2)

  def test_the_download_service_is_not_rebuilt_per_request(self):
    """A service rebuilt per request would lose every association it made."""
    service = build_service()
    runtime = DownloadRuntime(service)

    self.assertIs(runtime.service(), runtime.service())
    self.assertIs(runtime.service()._tasks, service._tasks)


class RepeatedSelectionTest(OfflineTestCase):
  """["A", "B", "A"] - legacy downloads three times, the task counts two units."""

  def trace(self, ids):
    """Every task write during the run, as (key, state, task state, progress)."""
    service = build_service()
    service.cache.remember([post_item("A"), post_item("B")])
    seen = []
    original = service.task_service.update_item

    def record(task_id, key, **kwargs):
      task = original(task_id, key, **kwargs)
      seen.append(
        (key, kwargs.get("state"), task["state"], dict(task["progress"]))
      )
      return task

    service.task_service.update_item = record
    job_id = service.start_selected(list(ids))
    return service, job_id, seen

  def test_the_legacy_loop_still_processes_every_entry(self):
    service, job_id, seen = self.trace(["A", "B", "A"])

    self.assertEqual([call[0] for call in service.downloader.calls], ["A", "B", "A"])
    self.assertEqual(service.store.snapshot(job_id)["total"], 3)

  def test_a_repeated_post_is_never_reopened(self):
    service, job_id, seen = self.trace(["A", "B", "A"])

    running_reports = [row[0] for row in seen if row[1] == ITEM_STATE_RUNNING]
    self.assertEqual(running_reports, ["A", "B"])

  def test_progress_only_ever_moves_forward(self):
    service, job_id, seen = self.trace(["A", "B", "A"])

    current = [row[3]["current"] for row in seen]
    self.assertEqual(current, sorted(current))
    self.assertEqual(current[-1], 2)

  def test_the_task_stays_running_until_the_whole_loop_ends(self):
    """Progress may read 2 / 2 while the legacy list still has an entry left."""
    service, job_id, seen = self.trace(["A", "B", "A"])

    complete_but_unfinished = [
      row for row in seen if row[3]["current"] == row[3]["total"]
    ]
    self.assertTrue(complete_but_unfinished)
    for row in complete_but_unfinished:
      self.assertEqual(row[2], TASK_STATE_RUNNING)

  def test_the_task_ends_only_after_the_last_entry(self):
    service, job_id, seen = self.trace(["A", "B", "A"])
    task = task_of(service, job_id)

    self.assertEqual(task["state"], TASK_STATE_SUCCESS)
    self.assertEqual(task["progress"], {"current": 2, "total": 2})
    self.assertEqual([item["key"] for item in task["items"]], ["A", "B"])


class SkippedOutcomeTest(OfflineTestCase):
  """Already downloaded is a goal met, not a fault."""

  def run_selection(self, ids, skips=(), failures=None):
    service = build_service(
      downloader=StubDownloader(skips=skips, failures=failures or {})
    )
    service.cache.remember([post_item(value) for value in ids])
    job_id = service.start_selected(list(ids))
    return task_of(service, job_id)

  def test_everything_already_downloaded_is_a_success(self):
    task = self.run_selection(["1", "2"], skips=["1", "2"])

    self.assertEqual(task["state"], TASK_STATE_SUCCESS)
    self.assertEqual(task["progress"], {"current": 2, "total": 2})

  def test_downloaded_and_already_present_is_a_success(self):
    task = self.run_selection(["1", "2"], skips=["2"])

    self.assertEqual(task["state"], TASK_STATE_SUCCESS)

  def test_already_present_alongside_a_failure_is_partial(self):
    task = self.run_selection(
      ["1", "2"], skips=["1"], failures={"2": RuntimeError("下载超时")}
    )

    self.assertEqual(task["state"], TASK_STATE_PARTIAL)

  def test_downloaded_alongside_a_failure_is_partial(self):
    task = self.run_selection(["1", "2"], failures={"2": RuntimeError("下载超时")})

    self.assertEqual(task["state"], TASK_STATE_PARTIAL)

  def test_everything_failing_is_a_failure(self):
    task = self.run_selection(
      ["1", "2"],
      failures={"1": RuntimeError("下载超时"), "2": RuntimeError("下载超时")},
    )

    self.assertEqual(task["state"], TASK_STATE_FAILED)


class OwnerRuntimeWiringTest(unittest.TestCase):
  """The task service reaches the download service by injection, not by Flask."""

  def test_a_runtime_carries_the_task_service_it_was_given(self):
    task_service = TaskService()

    runtime = OwnerRuntime(task_service=task_service)

    self.assertIs(runtime.task_service, task_service)

  def test_a_blueprint_built_with_a_task_service_passes_it_on(self):
    task_service = TaskService()
    captured = {}

    class RecordingRuntime(OwnerRuntime):
      def __init__(self, **kwargs):
        captured.update(kwargs)
        super().__init__(**kwargs)

    import backend.src.web.owner_routes as module

    original = module.OwnerRuntime
    module.OwnerRuntime = RecordingRuntime
    self.addCleanup(lambda: setattr(module, "OwnerRuntime", original))

    build_owner_blueprint(task_service=task_service)

    self.assertIs(captured["task_service"], task_service)

  def test_the_download_service_is_never_built_from_flask(self):
    """Business services stay testable without an application context."""
    service = build_service()

    self.assertIsInstance(service.task_service, TaskService)


if __name__ == "__main__":
  unittest.main()
