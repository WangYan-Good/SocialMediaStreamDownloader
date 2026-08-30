##
## The dependencies the *application* actually assembles.
##
## Phase 11B built the journal protocol and proved it against
## hand-constructed ``LiveRecordingTaskService`` instances.  Every one of those
## tests passed while ``server.py`` was still constructing the live service
## without a journal at all, so production entered the persistence path with
## ``recovery_journal=None`` and failed in region 1 on every real recording:
## owned recordings became partial and nothing reached the catalogue.
##
## A protocol test cannot catch that, because it builds the object itself.
## These tests call the real application factory and inspect what it wired.
##
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from backend.src.unit_test.config_fixture import unified_config
import server


class _Captured:
  """Records the constructor arguments the application actually passed."""

  def __init__(self):
    self.resources = []
    self.journals = []
    self.live_services = []


def build_application(config=None, capture=None):
  """Construct a real application, recording what it wires together."""
  capture = capture if capture is not None else _Captured()
  config = config if config is not None else unified_config()

  real_resource = server.RecordingResourceService
  real_journal = server.RecordingRecoveryJournal
  real_live = server.LiveRecordingTaskService

  def resource_factory(*args, **kwargs):
    instance = real_resource(*args, **kwargs)
    capture.resources.append((instance, kwargs))
    return instance

  def journal_factory(*args, **kwargs):
    instance = real_journal(*args, **kwargs)
    capture.journals.append((instance, kwargs))
    return instance

  def live_factory(*args, **kwargs):
    instance = real_live(*args, **kwargs)
    capture.live_services.append((instance, kwargs))
    return instance

  with patch.object(server, "RecordingResourceService", resource_factory), \
       patch.object(server, "RecordingRecoveryJournal", journal_factory), \
       patch.object(server, "LiveRecordingTaskService", live_factory):
    app = server.create_app(
      config=config,
      schema_guard_factory=lambda received: object(),
    )
  return app, capture


class ServerRecordingRecoveryWiringTest(unittest.TestCase):
  """The regression #156 shipped: production had no journal."""

  def test_server_wires_the_recording_recovery_journal_into_live_recording_service(self):
    ##
    ## The assertion that would have failed before this fix. Without it the
    ## live service holds ``recovery_journal=None`` and every real recording
    ## dies in region 1 with "recording recovery journal is unavailable".
    ##
    app, capture = build_application()

    self.assertEqual(1, len(capture.live_services))
    _, live_kwargs = capture.live_services[0]
    self.assertIn("recovery_journal", live_kwargs)
    self.assertIsNotNone(live_kwargs["recovery_journal"])

  def test_the_live_service_receives_the_application_journal_instance(self):
    ##
    ## Identity, not merely "a journal": two instances would mean the
    ## recording path and any future reader disagree about which notes exist.
    ##
    app, capture = build_application()

    self.assertEqual(1, len(capture.journals))
    constructed_journal, _ = capture.journals[0]
    _, live_kwargs = capture.live_services[0]

    self.assertIs(constructed_journal, live_kwargs["recovery_journal"])

  def test_the_live_service_receives_the_application_resource_service(self):
    app, capture = build_application()

    self.assertEqual(1, len(capture.resources))
    constructed_resource, _ = capture.resources[0]
    _, live_kwargs = capture.live_services[0]

    self.assertIs(constructed_resource, live_kwargs["recording_service"])

  def test_each_dependency_is_constructed_exactly_once(self):
    ##
    ## Application-scoped, not per-recording. A journal rebuilt on every
    ## persistence attempt would re-read configuration underneath itself.
    ##
    app, capture = build_application()

    self.assertEqual(1, len(capture.resources))
    self.assertEqual(1, len(capture.journals))
    self.assertEqual(1, len(capture.live_services))

  def test_two_applications_get_their_own_journals(self):
    ##
    ## Not a module global. Two apps in one interpreter - the lazy wsgi app and
    ## a test's app - must not share recovery state, exactly as they must not
    ## share a task store.
    ##
    first_app, first = build_application()
    second_app, second = build_application()

    first_journal, _ = first.journals[0]
    second_journal, _ = second.journals[0]
    self.assertIsNot(first_journal, second_journal)


class SharedConfigSnapshotTest(unittest.TestCase):
  """Both services must read the same validated configuration."""

  def test_the_journal_and_the_resource_service_share_one_config_loader(self):
    ##
    ## They both need ``$.download.save_path``, and a journal that read it from
    ## a different snapshot than the service could write notes beside media the
    ## rest of the application does not believe in.
    ##
    app, capture = build_application()

    _, resource_kwargs = capture.resources[0]
    _, journal_kwargs = capture.journals[0]

    self.assertIn("config_loader", resource_kwargs)
    self.assertIn("config_loader", journal_kwargs)
    self.assertIs(
      resource_kwargs["config_loader"],
      journal_kwargs["config_loader"],
    )

  def test_the_shared_loader_is_the_applications_own_snapshot(self):
    ##
    ## Not the global ``load_config``: that would read the file again rather
    ## than the snapshot this application's schema guard validated.
    ##
    from backend.src.library.configlib import load_config

    app, capture = build_application()
    _, journal_kwargs = capture.journals[0]
    loader = journal_kwargs["config_loader"]

    self.assertIsNot(loader, load_config)
    self.assertEqual("recording_config", getattr(loader, "__name__", None))


class StartupHasNoJournalSideEffectTest(unittest.TestCase):
  """Wiring a journal is not the same as using one."""

  def test_building_an_application_does_not_create_the_journal_directory(self):
    ##
    ## The journal is lazy on purpose: a server that never records, or one
    ## started against read-only storage, must still start.
    ##
    from backend.src.service.recording_recovery_journal import (
      JOURNAL_DIRECTORY_NAME,
    )

    with tempfile.TemporaryDirectory() as storage:
      config = unified_config()
      config["download"]["save_path"] = storage

      build_application(config=config)

      self.assertFalse((Path(storage) / JOURNAL_DIRECTORY_NAME).exists())
      self.assertEqual([], sorted(p.name for p in Path(storage).iterdir()))

  def test_building_an_application_never_touches_the_journal(self):
    ##
    ## Phase 11C has not started. Startup must not publish, read or retire a
    ## note - and this is the test that will notice the day somebody wires a
    ## replay in without saying so.
    ##
    calls = []

    class RefusingJournal:
      def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

      def publish(self, *args, **kwargs):
        calls.append("publish")
        raise AssertionError("startup must not publish a recovery note")

      def load(self, *args, **kwargs):
        calls.append("load")
        raise AssertionError("startup must not read a recovery note")

      def acknowledge(self, *args, **kwargs):
        calls.append("acknowledge")
        raise AssertionError("startup must not retire a recovery note")

      def ensure_root(self, *args, **kwargs):
        calls.append("ensure_root")
        raise AssertionError("startup must not create the journal directory")

    with patch.object(server, "RecordingRecoveryJournal", RefusingJournal):
      server.create_app(
        config=unified_config(),
        schema_guard_factory=lambda received: object(),
      )

    self.assertEqual([], calls)

  def test_constructing_the_journal_does_not_read_configuration(self):
    ##
    ## The lazy wsgi app is imported before any configuration exists, so
    ## construction may only store the loader.
    ##
    from backend.src.service.recording_recovery_journal import (
      RecordingRecoveryJournal,
    )

    def refuse():
      raise AssertionError("journal construction must not read configuration")

    RecordingRecoveryJournal(config_loader=refuse)


class DatabaseDisabledStillWiresJournalTest(unittest.TestCase):
  def test_a_database_disabled_application_still_gets_a_journal(self):
    ##
    ## Phase 11B's contract is that a note can be durable while the database is
    ## not reachable - that is precisely the state a later replay exists for.
    ## Tying journal wiring to ``database.enable`` would throw away the
    ## recovery input in exactly the case it matters most.
    ##
    config = unified_config()
    config["database"]["enable"] = False

    app, capture = build_application(config=config)

    self.assertEqual(1, len(capture.journals))
    constructed_journal, _ = capture.journals[0]
    _, live_kwargs = capture.live_services[0]
    self.assertIs(constructed_journal, live_kwargs["recovery_journal"])


if __name__ == "__main__":
  unittest.main()
