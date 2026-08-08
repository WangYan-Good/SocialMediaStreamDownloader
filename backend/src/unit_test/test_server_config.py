import importlib
import os
import signal
import unittest
from unittest.mock import patch

from backend.src.unit_test.config_fixture import unified_config
from backend.src.platform.douyin import douyin_live_downloader as live_module
import server


class FakeDispatcher:
  def __init__(self, failure=None):
    self.failure = failure
    self.received = []
    self.register_calls = 0

  def register(self):
    self.register_calls += 1

  def dispatch(self, payload):
    self.received.append(payload)
    if self.failure is not None:
      raise self.failure


class FalseyDispatcher(FakeDispatcher):
  def __bool__(self):
    return False


class ServerConfigTest(unittest.TestCase):
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

  def test_create_app_initializes_schema_guard_before_dispatcher(self):
    config = unified_config()
    events = []

    class OrderedDispatcher(FakeDispatcher):
      def register(self):
        events.append("dispatcher")
        super().register()

    guard = object()

    def guard_factory(received_config):
      self.assertIs(config, received_config)
      events.append("guard")
      return guard

    app = server.create_app(
      config,
      OrderedDispatcher(),
      schema_guard_factory=guard_factory,
    )

    self.assertEqual(["guard", "dispatcher"], events)
    self.assertIs(guard, app.extensions["smsd_schema_guard"])

  def test_lazy_app_guard_failure_state_does_not_block_dispatch(self):
    config = unified_config()
    dispatcher = FakeDispatcher()
    guard = object()
    app = server._new_flask_app(
      lazy_config=True,
      schema_guard_factory=lambda unused: guard,
    )

    with patch.object(server, "load_config", return_value=config), patch.object(
      server, "PlatformDispatcher", return_value=dispatcher
    ):
      response = app.test_client().post(
        "/", json={"urls": ["https://v.douyin.com/guard/"]}
      )

    self.assertEqual(200, response.status_code)
    self.assertEqual(1, dispatcher.register_calls)
    self.assertIs(guard, app.extensions["smsd_schema_guard"])

  def test_wsgi_app_lazily_initializes_once_on_first_get(self):
    config = unified_config()
    dispatcher = FakeDispatcher()

    with patch(
      "backend.src.library.configlib.load_config", return_value=config
    ) as load, patch(
      "backend.src.platform.platform_dispatcher.PlatformDispatcher",
      return_value=dispatcher,
    ) as dispatcher_type:
      wsgi_server = importlib.reload(server)

      first_response = wsgi_server.app.test_client().get("/")
      second_response = wsgi_server.app.test_client().get("/")

      self.assertEqual(first_response.status_code, 200)
      self.assertEqual(second_response.status_code, 200)
      self.assertEqual(load.call_count, 1)
      self.assertEqual(dispatcher_type.call_count, 1)
      self.assertEqual(dispatcher.register_calls, 1)

    importlib.reload(server)

  def test_wsgi_get_fails_when_lazy_configuration_is_invalid(self):
    invalid_config = unified_config()
    invalid_config["server"]["port"] = "not-a-port"

    with patch(
      "backend.src.library.configlib.load_config", return_value=invalid_config
    ) as load, patch(
      "backend.src.platform.platform_dispatcher.PlatformDispatcher"
    ) as dispatcher_type:
      wsgi_server = importlib.reload(server)

      response = wsgi_server.app.test_client().get("/")

      self.assertEqual(response.status_code, 500)
      self.assertEqual(load.call_count, 1)
      self.assertEqual(dispatcher_type.call_count, 0)

    importlib.reload(server)

  def test_wsgi_app_lazily_initializes_on_first_valid_post(self):
    config = unified_config()
    config["server"]["debug_mode"] = True
    dispatcher = FakeDispatcher()

    with patch(
      "backend.src.library.configlib.load_config", return_value=config
    ) as load, patch(
      "backend.src.platform.platform_dispatcher.PlatformDispatcher",
      return_value=dispatcher,
    ) as dispatcher_type:
      wsgi_server = importlib.reload(server)
      self.assertEqual(load.call_count, 0)
      self.assertEqual(dispatcher_type.call_count, 0)

      response = wsgi_server.app.test_client().post(
        "/", json={"urls": ["https://v.douyin.com/wsgi/"]}
      )

      self.assertEqual(response.status_code, 200)
      self.assertTrue(wsgi_server.app.debug)
      self.assertEqual(load.call_count, 1)
      self.assertEqual(dispatcher_type.call_count, 1)
      self.assertEqual(dispatcher.register_calls, 1)
      self.assertEqual(dispatcher.received, [{
        "urls": ["https://v.douyin.com/wsgi/"],
      }])

    importlib.reload(server)

  def test_create_app_keeps_dispatcher_and_debug_state_isolated(self):
    production_config = unified_config()
    production_config["server"]["debug_mode"] = False
    production_dispatcher = FakeDispatcher(RuntimeError("production boom"))
    production_app = server.create_app(production_config, production_dispatcher)

    debug_config = unified_config()
    debug_config["server"]["debug_mode"] = True
    debug_dispatcher = FakeDispatcher(RuntimeError("debug boom"))
    debug_app = server.create_app(debug_config, debug_dispatcher)

    production_response = production_app.test_client().post(
      "/", json={"urls": ["https://live.douyin.com/production"]}
    )
    debug_response = debug_app.test_client().post(
      "/", json={"urls": ["https://live.douyin.com/debug"]}
    )

    self.assertIsNot(production_app, debug_app)
    self.assertNotIn("traceback", production_response.get_json())
    self.assertIn("traceback", debug_response.get_json())
    self.assertEqual(production_dispatcher.received, [{
      "urls": ["https://live.douyin.com/production"],
    }])
    self.assertEqual(debug_dispatcher.received, [{
      "urls": ["https://live.douyin.com/debug"],
    }])

  def test_create_app_honors_a_falsey_dispatcher(self):
    config = unified_config()
    dispatcher = FalseyDispatcher()
    app = server.create_app(config, dispatcher)

    response = app.test_client().post(
      "/", json={"urls": ["https://example.com/"]}
    )

    self.assertEqual(response.status_code, 200)
    self.assertEqual(dispatcher.register_calls, 1)
    self.assertEqual(dispatcher.received, [{
      "urls": ["https://example.com/"],
    }])

  def test_create_app_uses_yaml_debug_for_error_responses(self):
    config = unified_config()
    config["server"]["debug_mode"] = True
    app = server.create_app(config, FakeDispatcher(RuntimeError("boom")))

    response = app.test_client().post(
      "/", json={"urls": ["https://live.douyin.com/1"]}
    )

    self.assertEqual(response.status_code, 500)
    self.assertIn("traceback", response.get_json())

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

  def test_successful_web_request_dispatches_the_frontend_urls(self):
    config = unified_config()
    dispatcher = FakeDispatcher()
    app = server.create_app(config, dispatcher)

    response = app.test_client().post(
      "/", json={"urls": ["https://v.douyin.com/example/"]}
    )

    self.assertEqual(response.status_code, 200)
    self.assertEqual(dispatcher.received, [{
      "urls": ["https://v.douyin.com/example/"],
    }])
