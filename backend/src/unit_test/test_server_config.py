import importlib
import os
import signal
import unittest
from unittest.mock import patch

from backend.src.unit_test.config_fixture import unified_config
from backend.src.platform.douyin import douyin_live_downloader as live_module
import server


class ServerConfigTest(unittest.TestCase):
  def test_create_app_needs_no_legacy_dispatcher_or_template_tree(self):
    config = unified_config()

    with patch.object(
      server,
      "PlatformDispatcher",
      side_effect=AssertionError("retired dispatcher must not be constructed"),
      create=True,
    ):
      app = server.create_app(
        config=config,
        schema_guard_factory=lambda received: object(),
      )

    self.assertIsNone(app.static_folder)
    self.assertIsNone(app.template_folder)

  def test_cancel_live_downloads_does_not_construct_when_none_exists(self):
    cancel = getattr(live_module, "cancel_live_downloads", None)
    self.assertIsNotNone(cancel)

    with patch.object(live_module, "downloader", None), patch.object(
      live_module,
      "get_live_downloader",
      side_effect=AssertionError("cancellation must not construct downloader"),
    ) as get_downloader:
      cancel()

    get_downloader.assert_not_called()

  def test_cancel_live_downloads_cancels_existing_recorder_once(self):
    cancel = getattr(live_module, "cancel_live_downloads", None)
    self.assertIsNotNone(cancel)
    cancel_calls = []

    class Recorder:
      def cancel_all(self):
        cancel_calls.append("cancel")

    class Downloader:
      hls_recorder = Recorder()

    with patch.object(live_module, "downloader", Downloader()), patch.object(
      live_module,
      "get_live_downloader",
      side_effect=AssertionError("cancellation must use existing downloader"),
    ) as get_downloader:
      cancel()

    get_downloader.assert_not_called()
    self.assertEqual(["cancel"], cancel_calls)

  def test_create_app_initializes_the_schema_guard(self):
    config = unified_config()
    events = []

    guard = object()

    def guard_factory(received_config):
      self.assertIs(config, received_config)
      events.append("guard")
      return guard

    app = server.create_app(
      config=config,
      schema_guard_factory=guard_factory,
    )

    self.assertEqual(["guard"], events)
    self.assertIs(guard, app.extensions["smsd_schema_guard"])

  def test_create_app_gives_probing_and_downloading_the_one_task_service(self):
    ##
    ## Both businesses must report into the store the task API reads.  Two
    ## services would mean a task centre that can only ever show half of what
    ## this process is doing.
    ##
    captured = {}
    build_history = server.build_history_blueprint
    build_owner = server.build_owner_blueprint

    def capture_history(runtime=None, task_service=None):
      captured["history"] = task_service
      return build_history(runtime=runtime, task_service=task_service)

    def capture_owner(runtime=None, task_service=None):
      ##
      ## The owner blueprint is handed a runtime rather than a bare task
      ## service, because the unified task api has to be given the *same*
      ## runtime - two would mean two job stores and two payload caches.  The
      ## invariant under test is unchanged and is read one level in: whatever
      ## reports owner work must report into the store the task api reads.
      ##
      captured["owner"] = None if runtime is None else runtime.task_service
      return build_owner(runtime=runtime, task_service=task_service)

    with patch.object(server, "build_history_blueprint", capture_history):
      with patch.object(server, "build_owner_blueprint", capture_owner):
        app = server.create_app(
          config=unified_config(),
          schema_guard_factory=lambda unused: object(),
        )

    installed = app.extensions["smsd_task_service"]
    self.assertIsNotNone(installed)
    self.assertIs(installed, captured["history"])
    self.assertIs(installed, captured["owner"])

  def test_two_applications_get_their_own_modern_task_runners(self):
    first = server.create_app(
      config=unified_config(), schema_guard_factory=lambda unused: object()
    )
    second = server.create_app(
      config=unified_config(), schema_guard_factory=lambda unused: object()
    )

    first_creation = first.extensions["smsd_task_creation_service"]
    second_creation = second.extensions["smsd_task_creation_service"]
    for attribute in ("_direct_post_service", "_live_record_service"):
      first_runner = getattr(first_creation, attribute)
      second_runner = getattr(second_creation, attribute)
      self.assertIsNot(first_runner, second_runner)
      self.assertIs(first.extensions["smsd_task_service"], first_runner._task_service)
      self.assertIs(second.extensions["smsd_task_service"], second_runner._task_service)

  def test_wsgi_app_lazily_initializes_once_on_first_get(self):
    config = unified_config()

    with patch(
      "backend.src.library.configlib.load_config", return_value=config
    ) as load:
      wsgi_server = importlib.reload(server)

      first_response = wsgi_server.app.test_client().get("/")
      second_response = wsgi_server.app.test_client().get("/")

      self.assertEqual(first_response.status_code, 200)
      self.assertEqual(second_response.status_code, 200)
      self.assertEqual(load.call_count, 1)

    importlib.reload(server)

  def test_wsgi_get_fails_when_lazy_configuration_is_invalid(self):
    invalid_config = unified_config()
    invalid_config["server"]["port"] = "not-a-port"

    with patch(
      "backend.src.library.configlib.load_config", return_value=invalid_config
    ) as load:
      wsgi_server = importlib.reload(server)

      response = wsgi_server.app.test_client().get("/")

      self.assertEqual(response.status_code, 500)
      self.assertEqual(load.call_count, 1)

    importlib.reload(server)

  def test_run_server_ignores_configuration_environment_variables(self):
    config = unified_config()
    config["server"].update({
      "host": "127.0.0.7", "port": 5102, "debug_mode": False,
    })
    captured = []

    class App:
      def run(self, **options):
        captured.append(options)

    with patch.dict(os.environ, {
      "SERVER_HOST": "environment.invalid",
      "SERVER_PORT": "9999",
      "FLASK_DEBUG": "true",
    }), patch.object(
      server,
      "create_app",
      return_value=App(),
    ), patch.object(server, "cancel_live_downloads") as cancel:
      server.run_server(config)

    self.assertEqual(captured, [{
      "host": "127.0.0.7", "port": 5102, "debug": False,
    }])
    cancel.assert_called_once_with()

  def test_run_server_sigterm_cancels_once_and_restores_handlers(self):
    signal_module = getattr(server, "signal", None)
    self.assertIsNotNone(signal_module)
    self.assertTrue(hasattr(server, "cancel_live_downloads"))
    config = unified_config()
    events = []
    prior_handlers = {
      signal.SIGINT: object(),
      signal.SIGTERM: object(),
    }
    active_handlers = dict(prior_handlers)

    def install_handler(signum, handler):
      previous = active_handlers[signum]
      active_handlers[signum] = handler
      events.append(("handler", signum, handler))
      return previous

    class App:
      def run(self, **options):
        events.append(("run", options))
        active_handlers[signal.SIGTERM](signal.SIGTERM, None)

    def cancel():
      events.append(("cancel",))

    with patch.object(server, "create_app", return_value=App()), patch.object(
      signal_module,
      "signal",
      side_effect=install_handler,
    ), patch.object(server, "cancel_live_downloads", side_effect=cancel):
      with self.assertRaises(SystemExit) as raised:
        server.run_server(config)

    self.assertEqual(128 + signal.SIGTERM, raised.exception.code)
    self.assertEqual(1, events.count(("cancel",)))
    self.assertIs(prior_handlers[signal.SIGINT], active_handlers[signal.SIGINT])
    self.assertIs(
      prior_handlers[signal.SIGTERM],
      active_handlers[signal.SIGTERM],
    )
    cancel_index = events.index(("cancel",))
    restore_indices = [
      index
      for index, event in enumerate(events)
      if event[0] == "handler" and event[2] in prior_handlers.values()
    ]
    self.assertTrue(all(cancel_index < index for index in restore_indices))

  def test_run_server_normal_return_cancels_once_and_restores_handlers(self):
    signal_module = getattr(server, "signal", None)
    self.assertIsNotNone(signal_module)
    self.assertTrue(hasattr(server, "cancel_live_downloads"))
    config = unified_config()
    events = []
    prior_handlers = {
      signal.SIGINT: object(),
      signal.SIGTERM: object(),
    }
    active_handlers = dict(prior_handlers)

    def install_handler(signum, handler):
      previous = active_handlers[signum]
      active_handlers[signum] = handler
      events.append(("handler", signum, handler))
      return previous

    class App:
      def run(self, **options):
        events.append(("run", options))

    with patch.object(server, "create_app", return_value=App()), patch.object(
      signal_module,
      "signal",
      side_effect=install_handler,
    ), patch.object(
      server,
      "cancel_live_downloads",
      side_effect=lambda: events.append(("cancel",)),
    ):
      server.run_server(config)

    self.assertEqual(1, events.count(("cancel",)))
    self.assertIs(prior_handlers[signal.SIGINT], active_handlers[signal.SIGINT])
    self.assertIs(
      prior_handlers[signal.SIGTERM],
      active_handlers[signal.SIGTERM],
    )
    run_index = next(
      index for index, event in enumerate(events) if event[0] == "run"
    )
    cancel_index = events.index(("cancel",))
    self.assertLess(run_index, cancel_index)

  def test_run_server_sigterm_keeps_system_exit_when_cancellation_fails(self):
    config = unified_config()
    messages = []
    prior_handlers = {
      signal.SIGINT: object(),
      signal.SIGTERM: object(),
    }
    active_handlers = dict(prior_handlers)

    def install_handler(signum, handler):
      previous = active_handlers[signum]
      active_handlers[signum] = handler
      return previous

    class App:
      def run(self, **options):
        active_handlers[signal.SIGTERM](signal.SIGTERM, None)

    class Logger:
      def error(self, message):
        messages.append(str(message))

    def fail_cancellation():
      raise RuntimeError("cancel-sensitive-marker")

    caught = None
    with patch.object(server, "create_app", return_value=App()), patch.object(
      server.signal,
      "signal",
      side_effect=install_handler,
    ), patch.object(
      server,
      "cancel_live_downloads",
      side_effect=fail_cancellation,
    ), patch.object(server, "get_logger", return_value=Logger()):
      try:
        server.run_server(config)
      except BaseException as exc:
        caught = exc

    self.assertIsInstance(caught, SystemExit)
    self.assertEqual(128 + signal.SIGTERM, caught.code)
    self.assertIs(prior_handlers[signal.SIGINT], active_handlers[signal.SIGINT])
    self.assertIs(
      prior_handlers[signal.SIGTERM],
      active_handlers[signal.SIGTERM],
    )
    self.assertEqual(1, len(messages))
    self.assertIn("cancellation failed", messages[0])
    self.assertNotIn("cancel-sensitive-marker", messages[0])

  def test_run_server_keeps_app_error_when_cancellation_and_logging_fail(self):
    config = unified_config()
    expected_error = RuntimeError("app-sensitive-marker")
    cancellation_calls = []
    prior_handlers = {
      signal.SIGINT: object(),
      signal.SIGTERM: object(),
    }
    active_handlers = dict(prior_handlers)

    def install_handler(signum, handler):
      previous = active_handlers[signum]
      active_handlers[signum] = handler
      return previous

    class App:
      def run(self, **options):
        raise expected_error

    class FailingLogger:
      def error(self, message):
        raise RuntimeError("logger-sensitive-marker")

    def fail_cancellation():
      cancellation_calls.append("cancel")
      raise RuntimeError("cancel-sensitive-marker")

    caught = None
    with patch.object(server, "create_app", return_value=App()), patch.object(
      server.signal,
      "signal",
      side_effect=install_handler,
    ), patch.object(
      server,
      "cancel_live_downloads",
      side_effect=fail_cancellation,
    ), patch.object(server, "get_logger", return_value=FailingLogger()):
      try:
        server.run_server(config)
      except BaseException as exc:
        caught = exc

    self.assertIs(expected_error, caught)
    self.assertEqual(["cancel"], cancellation_calls)
    self.assertIs(prior_handlers[signal.SIGINT], active_handlers[signal.SIGINT])
    self.assertIs(
      prior_handlers[signal.SIGTERM],
      active_handlers[signal.SIGTERM],
    )
