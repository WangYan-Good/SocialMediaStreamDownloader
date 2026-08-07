import logging
import os
import sys
import tempfile
import unittest
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from unittest.mock import patch

sys.path.append(os.getcwd())

from backend.src.base.log import LoggerManager
from backend.src.library import loglib


def reset_logger_manager():
  manager = getattr(LoggerManager, "_instance", None)
  if manager is not None:
    logger_queue = getattr(
      manager,
      "_LoggerManager__logger_queue",
      {},
    )
    for logger in logger_queue.values():
      for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()
  if hasattr(LoggerManager, "_instance"):
    delattr(LoggerManager, "_instance")
  LoggerManager._LoggerManager__initialized = False
  LoggerManager._LoggerManager__logger_queue = {}


def make_log_config(log_file_path, **overrides):
  config = {
    "log_enable": True,
    "log_level": "DEBUG",
    "log_save": True,
    "log_file_path": str(log_file_path),
  }
  config.update(overrides)
  return config


class TestLogConfig(unittest.TestCase):
  def setUp(self):
    reset_logger_manager()
    self.temporary_directory = tempfile.TemporaryDirectory()

  def tearDown(self):
    reset_logger_manager()
    self.temporary_directory.cleanup()

  def test_file_logging_uses_unified_path_and_level(self):
    log_path = Path(self.temporary_directory.name) / "nested" / "server.log"
    manager = LoggerManager(make_log_config(log_path))
    logger = manager.get_logger()
    rotating_handlers = [
      handler for handler in logger.handlers
      if isinstance(handler, TimedRotatingFileHandler)
    ]
    self.assertEqual(logger.level, logging.DEBUG)
    self.assertEqual(len(rotating_handlers), 1)
    self.assertEqual(Path(rotating_handlers[0].baseFilename), log_path)
    self.assertTrue(log_path.parent.is_dir())

  def test_enabled_logging_applies_configured_level_to_both_handlers(self):
    log_path = Path(self.temporary_directory.name) / "server.log"
    logger = LoggerManager(
      make_log_config(log_path, log_level="ERROR")
    ).get_logger()
    console_handlers = [
      handler for handler in logger.handlers
      if type(handler) is logging.StreamHandler
    ]
    rotating_handlers = [
      handler for handler in logger.handlers
      if isinstance(handler, TimedRotatingFileHandler)
    ]
    self.assertEqual([handler.level for handler in console_handlers], [logging.ERROR])
    self.assertEqual([handler.level for handler in rotating_handlers], [logging.ERROR])

  def test_log_save_false_does_not_create_directory_or_file_handler(self):
    log_path = Path(self.temporary_directory.name) / "disabled" / "server.log"
    logger = LoggerManager(
      make_log_config(log_path, log_save=False)
    ).get_logger()
    self.assertFalse(log_path.parent.exists())
    self.assertFalse(any(
      isinstance(handler, TimedRotatingFileHandler)
      for handler in logger.handlers
    ))

  def test_repeated_construction_does_not_replace_default_logger(self):
    log_path = Path(self.temporary_directory.name) / "first.log"
    other_log_path = Path(self.temporary_directory.name) / "second.log"
    first_manager = LoggerManager(make_log_config(log_path))
    first_logger = first_manager.get_logger()
    second_manager = LoggerManager(
      make_log_config(other_log_path, log_level="ERROR")
    )
    self.assertIs(second_manager, first_manager)
    self.assertIs(second_manager.get_logger(), first_logger)

  def test_get_instance_returns_configured_manager_without_reconfiguration(self):
    log_path = Path(self.temporary_directory.name) / "first.log"
    manager = LoggerManager(make_log_config(log_path, log_level="ERROR"))
    default_logger = manager.get_logger()

    retrieved_manager = LoggerManager.get_instance()

    self.assertIs(retrieved_manager, manager)
    self.assertIs(retrieved_manager.get_logger(), default_logger)
    self.assertEqual(default_logger.level, logging.ERROR)

  def test_get_instance_cold_start_uses_unified_configuration(self):
    log_path = Path(self.temporary_directory.name) / "cold-start.log"

    class FakeBaseConfig:
      def get_config(self):
        return {"log": make_log_config(log_path, log_level="WARNING")}

    with patch("backend.src.base.config.BaseConfig", FakeBaseConfig):
      manager = LoggerManager.get_instance()

    self.assertEqual(manager.get_logger().level, logging.WARNING)

  def test_public_get_logger_returns_initialized_default_logger(self):
    log_path = Path(self.temporary_directory.name) / "server.log"
    configured_logger = LoggerManager(
      make_log_config(log_path, log_save=False)
    ).get_logger()
    self.assertIs(loglib.get_logger(), configured_logger)

  def test_log_enable_false_disables_default_and_registered_loggers(self):
    log_path = Path(self.temporary_directory.name) / "server.log"
    manager = LoggerManager(
      make_log_config(log_path, log_enable=False, log_save=False)
    )
    self.assertTrue(manager.get_logger().disabled)
    self.assertTrue(manager.register_logger("worker", "INFO").disabled)

  def test_invalid_log_config_is_rejected_and_initialization_can_retry(self):
    invalid_configs = [
      ([], "mapping"),
      ({"log_enable": "yes", "log_level": "INFO", "log_save": False}, "log_enable"),
      ({"log_enable": True, "log_level": "TRACE", "log_save": False}, "log_level"),
      ({"log_enable": True, "log_level": "INFO", "log_save": "yes"}, "log_save"),
      ({"log_enable": True, "log_level": "INFO", "log_save": True, "log_file_path": ""}, "log_file_path"),
    ]
    for invalid_config, expected_text in invalid_configs:
      reset_logger_manager()
      with self.subTest(config=invalid_config):
        with self.assertRaisesRegex(ValueError, expected_text):
          LoggerManager(invalid_config)

    reset_logger_manager()
    log_path = Path(self.temporary_directory.name) / "retry.log"
    manager = LoggerManager(make_log_config(log_path, log_save=False))
    self.assertEqual(manager.get_logger().level, logging.DEBUG)

  def test_directory_log_file_paths_are_rejected_before_handler_setup(self):
    existing_directory = Path(self.temporary_directory.name) / "existing"
    existing_directory.mkdir()
    invalid_paths = [
      "logs/", "logs\\", ".", "..", "/", str(existing_directory),
      "logs/.", "logs/..", "logs\\.", "logs\\..",
    ]
    for index, invalid_path in enumerate(invalid_paths):
      case_directory = Path(self.temporary_directory.name) / str(index)
      case_directory.mkdir()
      previous_directory = os.getcwd()
      os.chdir(case_directory)
      try:
        with self.subTest(log_file_path=invalid_path):
          reset_logger_manager()
          with self.assertRaisesRegex(ValueError, "log_file_path"):
            LoggerManager(make_log_config(invalid_path))
          self.assertFalse(Path("logs").exists())
      finally:
        os.chdir(previous_directory)

  def test_relative_log_file_names_remain_valid(self):
    previous_directory = os.getcwd()
    os.chdir(self.temporary_directory.name)
    try:
      for log_file_path in ["logs", ".server.log"]:
        with self.subTest(log_file_path=log_file_path):
          reset_logger_manager()
          logger = LoggerManager(make_log_config(log_file_path)).get_logger()
          self.assertTrue(logger.handlers)
    finally:
      os.chdir(previous_directory)

  def test_failed_validation_keeps_singleton_for_a_successful_retry(self):
    with self.assertRaisesRegex(ValueError, "log_file_path"):
      LoggerManager(make_log_config("logs/"))
    failed_manager = LoggerManager._instance

    retried_manager = LoggerManager(
      make_log_config(".server.log", log_save=False)
    )

    self.assertIs(retried_manager, failed_manager)
    self.assertEqual(retried_manager.get_logger().level, logging.DEBUG)

  def test_default_configuration_uses_unified_log_mapping(self):
    log_path = Path(self.temporary_directory.name) / "configured" / "server.log"

    class FakeBaseConfig:
      def get_config(self):
        return {"log": make_log_config(log_path, log_level="ERROR")}

    with patch("backend.src.base.config.BaseConfig", FakeBaseConfig):
      logger = LoggerManager().get_logger()

    rotating_handlers = [
      handler for handler in logger.handlers
      if isinstance(handler, TimedRotatingFileHandler)
    ]
    self.assertEqual(logger.level, logging.ERROR)
    self.assertEqual(Path(rotating_handlers[0].baseFilename), log_path)

  def test_handler_setup_failure_closes_partial_handlers_and_can_retry(self):
    log_path = Path(self.temporary_directory.name) / "failed" / "server.log"
    closed_handlers = []

    class TrackingStreamHandler(logging.StreamHandler):
      def close(self):
        closed_handlers.append(self)
        super().close()

    with patch(
      "backend.src.base.log.StreamHandler", TrackingStreamHandler
    ), patch(
      "backend.src.base.log.TimedRotatingFileHandler",
      side_effect=OSError("cannot create log file"),
    ):
      with self.assertRaisesRegex(OSError, "cannot create log file"):
        LoggerManager(make_log_config(log_path))

    self.assertEqual(len(closed_handlers), 1)
    self.assertFalse(
      getattr(LoggerManager, "_LoggerManager__initialized", False)
    )
    logger = LoggerManager(make_log_config(log_path, log_save=False)).get_logger()
    self.assertEqual(logger.level, logging.DEBUG)
