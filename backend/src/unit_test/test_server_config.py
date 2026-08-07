import importlib
import os
import unittest
from unittest.mock import patch

from backend.src.unit_test.config_fixture import unified_config
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
    }), patch.object(server, "create_app", return_value=App()):
      server.run_server(config)

    self.assertEqual(captured, [{
      "host": "127.0.0.7", "port": 5102, "debug": False,
    }])

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
