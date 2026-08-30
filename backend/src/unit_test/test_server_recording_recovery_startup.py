##
## Reconciliation as the *application* actually runs it.
##
## Phase 11B built a journal protocol and proved it against hand-constructed
## services.  Every one of those tests passed while ``server.py`` was wiring the
## live service with no journal at all, and production failed on every real
## recording - the regression #157 had to repair.
##
## The same trap is open here, and wider: a reconciler that is never called at
## startup is indistinguishable, from a unit test's point of view, from one that
## is.  Testing ``reconcile_once()`` directly proves the algorithm and nothing
## about whether anything runs it.  So these tests call the real application
## factory, against a real temporary storage root, and look at what actually
## happened to the notes on disk.
##
## Both entry points are covered, because they initialise differently:
##
##   create_app(config)          - eager. Configuration and schema guard are
##                                 known before the application is built.
##   _new_flask_app(lazy=True)   - the wsgi app. Imported before any
##                                 configuration exists; the first request
##                                 initialises the runtime.
##
## And one rule underpins all of it: whatever reconciliation does, the server
## comes up. A recovery failure must never cost the SPA or an unrelated API.
##
from datetime import datetime
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from backend.src.service.recording_recovery_journal import (
  JOURNAL_DIRECTORY_NAME,
  RecordingRecoveryJournal,
)
from backend.src.service.recording_resource import (
  RecordingPersistenceIntent,
  RecordingPersistenceUnavailable,
  RecordingResourceService,
)
from backend.src.unit_test.config_fixture import unified_config
import server

KEY = "0123456789abcdef0123456789abcdef"


class FakeRecordingTable:
  """The repository, isolated from any real database."""

  def __init__(self):
    self.rows = []

  def create_recording(self, record, recovery_key=None):
    self.rows.append((record, recovery_key))
    return 500 + len(self.rows)


class Harness:
  """A real application, over a real temporary storage root."""

  def __init__(self, storage, repository=None, unavailable=False):
    self.storage = Path(storage)
    self.repository = repository if repository is not None else FakeRecordingTable()
    self.unavailable = unavailable
    self.config = unified_config()
    self.config["download"]["save_path"] = str(self.storage)
    self.reconcilers = []
    self.runs = []
    self.config_reads = 0

  ##
  ## >>------------------------- fixtures on disk -------------------------<<
  ##
  def media(self, relative="douyin/live/live.mp4", content=b"recorded-bytes"):
    target = self.storage / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return target

  def intent(self, output_path="douyin/live/live.mp4", app_user_id=41):
    return RecordingPersistenceIntent(
      app_user_id=app_user_id,
      platform="douyin",
      room_id="998877",
      owner_user_id="owner-1",
      title="Launch title",
      protocol="hls",
      output_path=output_path,
      started_at=datetime(2026, 8, 30, 9, 0, 0, 123000),
      finished_at=datetime(2026, 8, 30, 10, 0, 0, 456000),
      source="task_api",
    )

  def publish(self, key=KEY, **overrides):
    journal = RecordingRecoveryJournal(
      config_loader=lambda: {"download": {"save_path": str(self.storage)}}
    )
    intent = self.intent(**overrides)
    journal.publish(intent, key)
    return intent

  def notes(self):
    directory = self.storage / JOURNAL_DIRECTORY_NAME
    if not directory.exists():
      return []
    return sorted(p.name for p in directory.iterdir())

  ##
  ## >>--------------------------- the patches ---------------------------<<
  ##
  def resource_factory(self, *args, **kwargs):
    ##
    ## The real service, holding a repository that is not a database. The
    ## application still wires *this* instance everywhere, which is the point:
    ## the reconciler must reach the same repository the recording path does.
    ##
    provider = (lambda: None) if self.unavailable else (lambda: self.repository)
    service = RecordingResourceService(
      repository_provider=provider, config_loader=kwargs.get("config_loader")
    )
    self.resource = service
    return service

  def reconciler_factory(self, **kwargs):
    real = server.RECONCILER_CLASS(**kwargs)
    self.reconcilers.append((real, kwargs))
    original = real.reconcile_once

    def counted():
      self.runs.append(True)
      return original()

    real.reconcile_once = counted
    return real

  def patches(self):
    return (
      patch.object(server, "RecordingResourceService", self.resource_factory),
      patch.object(
        server, "RecordingRecoveryReconciler", self.reconciler_factory
      ),
    )

  def create_app(self):
    first, second = self.patches()
    with first, second:
      return server.create_app(
        config=self.config, schema_guard_factory=lambda source: object()
      )

  def lazy_app(self):
    def counting_load():
      self.config_reads += 1
      return self.config

    first, second = self.patches()
    self.lazy_patches = (
      first, second, patch.object(server, "load_config", counting_load)
    )
    for one in self.lazy_patches:
      one.start()
    return server._new_flask_app(
      lazy_config=True, schema_guard_factory=lambda source: object()
    )

  def stop_lazy(self):
    for one in reversed(self.lazy_patches):
      one.stop()


class EagerStartupTest(unittest.TestCase):
  """``create_app`` reconciles once, for real."""

  def test_a_pending_note_is_recovered_when_the_application_is_built(self):
    with tempfile.TemporaryDirectory() as storage:
      harness = Harness(storage)
      harness.media()
      harness.publish()

      harness.create_app()

      ##
      ## The three things that together mean "recovered": something ran, the
      ## repository was told, and the note is gone.
      ##
      self.assertEqual(1, len(harness.runs))
      self.assertEqual(1, len(harness.repository.rows))
      self.assertEqual([], harness.notes())

  def test_the_recovered_row_carries_the_journalled_key_and_path(self):
    with tempfile.TemporaryDirectory() as storage:
      harness = Harness(storage)
      harness.media()
      harness.publish()

      harness.create_app()

      record, recovery_key = harness.repository.rows[0]
      self.assertEqual(KEY, recovery_key)
      self.assertEqual("douyin/live/live.mp4", record["output_path"])
      self.assertEqual(41, record["app_user_id"])

  def test_several_pending_notes_are_all_recovered(self):
    with tempfile.TemporaryDirectory() as storage:
      harness = Harness(storage)
      for value in range(3):
        harness.media("douyin/live/{}.mp4".format(value))
        harness.publish(
          key="{:032x}".format(value),
          output_path="douyin/live/{}.mp4".format(value),
        )

      harness.create_app()

      self.assertEqual(3, len(harness.repository.rows))
      self.assertEqual([], harness.notes())


class ReconcilerWiringTest(unittest.TestCase):
  """The reconciler is handed the application's own collaborators."""

  def build(self, storage):
    harness = Harness(storage)
    app = harness.create_app()
    return harness, app

  def test_the_application_builds_exactly_one_reconciler(self):
    with tempfile.TemporaryDirectory() as storage:
      harness, _ = self.build(storage)

      self.assertEqual(1, len(harness.reconcilers))

  def test_the_reconciler_receives_the_application_journal_instance(self):
    ##
    ## Identity, not "a journal". A reconciler holding its own would enumerate
    ## a directory the recording path is not writing into, and acknowledge
    ## notes the rest of the application does not believe in.
    ##
    with tempfile.TemporaryDirectory() as storage:
      harness, app = self.build(storage)
      _, kwargs = harness.reconcilers[0]

      self.assertIs(
        server.application_runtime(app)["recording_recovery_journal"],
        kwargs["journal"],
      )

  def test_the_reconciler_receives_the_application_recording_service(self):
    with tempfile.TemporaryDirectory() as storage:
      harness, app = self.build(storage)
      _, kwargs = harness.reconcilers[0]

      self.assertIs(
        server.application_runtime(app)["recording_service"],
        kwargs["recording_service"],
      )

  def test_the_reconciler_shares_the_one_configuration_snapshot(self):
    ##
    ## The same closure the journal and the resource service read. A reconciler
    ## on a different snapshot would judge a note's media against a different
    ## storage root than the one the note was written under.
    ##
    with tempfile.TemporaryDirectory() as storage:
      harness, app = self.build(storage)
      _, kwargs = harness.reconcilers[0]
      journal = server.application_runtime(app)["recording_recovery_journal"]

      self.assertIs(journal._config_loader, kwargs["config_loader"])
      self.assertEqual(
        "recording_config", getattr(kwargs["config_loader"], "__name__", None)
      )

  def test_the_reconciler_is_installed_on_the_application_runtime(self):
    with tempfile.TemporaryDirectory() as storage:
      harness, app = self.build(storage)
      built, _ = harness.reconcilers[0]

      self.assertIs(
        built, server.application_runtime(app)["recording_reconciler"]
      )

  def test_two_applications_get_their_own_reconcilers(self):
    with tempfile.TemporaryDirectory() as first_storage:
      with tempfile.TemporaryDirectory() as second_storage:
        first, _ = self.build(first_storage)
        second, _ = self.build(second_storage)

        self.assertIsNot(first.reconcilers[0][0], second.reconcilers[0][0])
        self.assertEqual(1, len(first.runs))
        self.assertEqual(1, len(second.runs))


class LazyStartupTest(unittest.TestCase):
  """The wsgi application reconciles on its first runtime initialisation."""

  def test_constructing_the_lazy_application_reads_nothing(self):
    ##
    ## It is built at import, before any configuration exists. Reading one -
    ## or reconciling - here would make importing this module a filesystem
    ## operation.
    ##
    with tempfile.TemporaryDirectory() as storage:
      harness = Harness(storage)
      harness.media()
      harness.publish()
      try:
        harness.lazy_app()

        self.assertEqual(0, harness.config_reads)
        self.assertEqual(0, len(harness.runs))
        self.assertEqual(["{}.json".format(KEY)], harness.notes())
      finally:
        harness.stop_lazy()

  def test_the_first_request_reconciles(self):
    with tempfile.TemporaryDirectory() as storage:
      harness = Harness(storage)
      harness.media()
      harness.publish()
      try:
        app = harness.lazy_app()
        app.test_client().get("/api/system/status")

        self.assertEqual(1, len(harness.runs))
        self.assertEqual(1, len(harness.repository.rows))
        self.assertEqual([], harness.notes())
      finally:
        harness.stop_lazy()

  def test_a_second_request_does_not_reconcile_again(self):
    ##
    ## "Once per application", not "once per request". A scan on every request
    ## would open the journal directory on the hot path forever.
    ##
    with tempfile.TemporaryDirectory() as storage:
      harness = Harness(storage)
      harness.media()
      harness.publish()
      try:
        app = harness.lazy_app()
        client = app.test_client()
        client.get("/api/system/status")
        client.get("/api/system/status")
        client.get("/api/system/status")

        self.assertEqual(1, len(harness.runs))
      finally:
        harness.stop_lazy()

  def test_concurrent_first_requests_reconcile_once(self):
    with tempfile.TemporaryDirectory() as storage:
      harness = Harness(storage)
      harness.media()
      harness.publish()
      try:
        app = harness.lazy_app()
        start = threading.Barrier(4)

        def hit():
          start.wait()
          app.test_client().get("/api/system/status")

        threads = [threading.Thread(target=hit) for _ in range(4)]
        for thread in threads:
          thread.start()
        for thread in threads:
          thread.join()

        self.assertEqual(1, len(harness.runs))
        self.assertEqual(1, len(harness.repository.rows))
      finally:
        harness.stop_lazy()


class StartupIsolationTest(unittest.TestCase):
  """Recovery may fail; the server may not."""

  def test_an_unavailable_repository_does_not_stop_the_application(self):
    with tempfile.TemporaryDirectory() as storage:
      harness = Harness(storage, unavailable=True)
      harness.media()
      harness.publish()

      app = harness.create_app()

      self.assertIsNotNone(app)
      self.assertEqual(["{}.json".format(KEY)], harness.notes())

  def test_an_unavailable_repository_still_serves_unrelated_routes(self):
    with tempfile.TemporaryDirectory() as storage:
      harness = Harness(storage, unavailable=True)
      harness.media()
      harness.publish()

      app = harness.create_app()

      ##
      ## 401, not 200: every API route refuses an anonymous caller, and that
      ## refusal is the point - the request was routed and answered by the
      ## authentication layer, which a startup broken by recovery could not do.
      ##
      self.assertEqual(
        401, app.test_client().get("/api/system/status").status_code
      )

  def test_a_reconciler_that_explodes_does_not_stop_the_application(self):
    ##
    ## Not a failure this code produces - a bug, an import error, anything
    ## unforeseen. The application still has to come up.
    ##
    with tempfile.TemporaryDirectory() as storage:
      harness = Harness(storage)

      def exploding(**kwargs):
        class Exploding:
          def reconcile_once(self):
            raise RuntimeError("reconciliation is broken")

        return Exploding()

      with patch.object(server, "RecordingResourceService", harness.resource_factory), \
           patch.object(server, "RecordingRecoveryReconciler", exploding):
        app = server.create_app(
          config=harness.config, schema_guard_factory=lambda source: object()
        )

      ##
      ## Answered by the authentication layer, which means the application was
      ## built and is routing - the only claim this test makes.
      ##
      self.assertEqual(
        401, app.test_client().get("/api/system/status").status_code
      )

  def test_a_recovery_failure_is_still_one_attempt(self):
    ##
    ## "Once" means one attempt per application, not one success. Retrying on
    ## every request would rescan the journal directory forever against a
    ## database that is down.
    ##
    with tempfile.TemporaryDirectory() as storage:
      harness = Harness(storage, unavailable=True)
      harness.media()
      harness.publish()
      try:
        app = harness.lazy_app()
        client = app.test_client()
        client.get("/api/system/status")
        client.get("/api/system/status")

        self.assertEqual(1, len(harness.runs))
        self.assertEqual(["{}.json".format(KEY)], harness.notes())
      finally:
        harness.stop_lazy()


class ExactlyOncePerApplicationTest(unittest.TestCase):
  """At most one reconciliation attempt per application, whoever asks."""

  def test_asking_again_does_not_reconcile_again(self):
    ##
    ## The latch, exercised directly. Both startup paths happen to call it
    ## once, so without this the guard could be removed entirely and every
    ## other test would still pass.
    ##
    with tempfile.TemporaryDirectory() as storage:
      harness = Harness(storage)
      harness.media()
      harness.publish()

      app = harness.create_app()
      runtime = server.application_runtime(app)
      runtime["reconcile_recoveries_once"]()
      runtime["reconcile_recoveries_once"]()

      self.assertEqual(1, len(harness.runs))
      self.assertEqual(1, len(harness.repository.rows))

  def test_a_failed_attempt_still_counts_as_the_attempt(self):
    ##
    ## "Once" means one attempt, not one success. A database that is down must
    ## not be rescanned by everything that asks afterwards; the notes wait for
    ## the next process start instead.
    ##
    with tempfile.TemporaryDirectory() as storage:
      harness = Harness(storage, unavailable=True)
      harness.media()
      harness.publish()

      app = harness.create_app()
      runtime = server.application_runtime(app)
      runtime["reconcile_recoveries_once"]()

      self.assertEqual(1, len(harness.runs))
      self.assertEqual(["{}.json".format(KEY)], harness.notes())

  def test_two_applications_each_get_their_own_attempt(self):
    ##
    ## Application-local, not a module global: the first application's startup
    ## must not silently cancel the second's.
    ##
    with tempfile.TemporaryDirectory() as first_storage:
      with tempfile.TemporaryDirectory() as second_storage:
        first = Harness(first_storage)
        first.media()
        first.publish()
        second = Harness(second_storage)
        second.media()
        second.publish()

        first.create_app()
        second.create_app()

        self.assertEqual(1, len(first.runs))
        self.assertEqual(1, len(second.runs))
        self.assertEqual([], first.notes())
        self.assertEqual([], second.notes())


class AbsentJournalDirectoryTest(unittest.TestCase):
  """A server that has never recorded leaves no trace of having looked."""

  def test_startup_does_not_create_the_journal_directory(self):
    with tempfile.TemporaryDirectory() as storage:
      harness = Harness(storage)

      harness.create_app()

      self.assertFalse((Path(storage) / JOURNAL_DIRECTORY_NAME).exists())
      self.assertEqual([], sorted(p.name for p in Path(storage).iterdir()))

  def test_startup_leaves_an_untouched_storage_root_untouched(self):
    with tempfile.TemporaryDirectory() as storage:
      harness = Harness(storage)
      harness.media()
      before = sorted(str(p) for p in Path(storage).rglob("*"))

      harness.create_app()

      self.assertEqual(before, sorted(str(p) for p in Path(storage).rglob("*")))


if __name__ == "__main__":
  unittest.main()
