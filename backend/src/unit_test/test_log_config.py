import logging
import os
import io
import sys
import subprocess
import tempfile
import unittest
from logging.handlers import RotatingFileHandler
from pathlib import Path
from unittest.mock import patch

sys.path.append(os.getcwd())

from backend.src.base.log import LoggerManager
import backend.src.base.log as log_module
from backend.src.library import loglib


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_LOG_PROBE = PROJECT_ROOT / "scripts" / "runtime_log_retention_probe.py"


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


def reset_bootstrap_logger():
  logger = logging.getLogger("bootstrap")
  for handler in logger.handlers[:]:
    logger.removeHandler(handler)
    handler.close()


def bounded_logging_api():
  required = (
    "BoundedRotatingFileHandler",
    "BoundedUtf8Formatter",
    "LOG_BACKUP_COUNT",
    "LOG_MAX_BYTES",
    "LOG_MAX_RECORD_BYTES",
    "build_bounded_file_handler",
  )
  missing = [name for name in required if not hasattr(log_module, name)]
  if missing:
    raise AssertionError(
      "bounded logging API is missing: {}".format(", ".join(missing))
    )
  return tuple(getattr(log_module, name) for name in required)


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
    reset_bootstrap_logger()
    self.temporary_directory = tempfile.TemporaryDirectory()

  def tearDown(self):
    reset_logger_manager()
    reset_bootstrap_logger()
    self.temporary_directory.cleanup()

  def test_file_logging_uses_unified_path_and_level(self):
    log_path = Path(self.temporary_directory.name) / "nested" / "server.log"
    manager = LoggerManager(make_log_config(log_path))
    logger = manager.get_logger()
    rotating_handlers = [
      handler for handler in logger.handlers
      if isinstance(handler, RotatingFileHandler)
    ]
    self.assertEqual(logger.level, logging.DEBUG)
    self.assertEqual(len(rotating_handlers), 1)
    self.assertEqual(Path(rotating_handlers[0].baseFilename), log_path)
    self.assertEqual(rotating_handlers[0].maxBytes, 10 * 1024 * 1024)
    self.assertEqual(rotating_handlers[0].backupCount, 9)
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
      if isinstance(handler, RotatingFileHandler)
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
      isinstance(handler, logging.FileHandler)
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
      if isinstance(handler, RotatingFileHandler)
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
      "backend.src.base.log.build_bounded_file_handler",
      side_effect=OSError("cannot create log file"),
      create=True,
    ):
      with self.assertRaisesRegex(OSError, "cannot create log file"):
        LoggerManager(make_log_config(log_path))

    self.assertEqual(len(closed_handlers), 1)
    self.assertFalse(
      getattr(LoggerManager, "_LoggerManager__initialized", False)
    )
    logger = LoggerManager(make_log_config(log_path, log_save=False)).get_logger()
    self.assertEqual(logger.level, logging.DEBUG)

  def test_bounded_formatter_limits_final_utf8_bytes_without_mutating_record(self):
    (
      _, BoundedUtf8Formatter, _, _, max_record_bytes, _,
    ) = bounded_logging_api()
    formatter = BoundedUtf8Formatter(
      log_module.DEFAULT_LOGGER_FORMATTER_STR,
      max_record_bytes=max_record_bytes,
    )
    original_message = "界" * max_record_bytes
    record = logging.LogRecord(
      "utf8", logging.ERROR, __file__, 1, original_message, (), None
    )
    original_fields = dict(record.__dict__)

    formatted = formatter.format(record)

    self.assertLessEqual(len(formatted.encode("utf-8")), 64 * 1024)
    self.assertTrue(formatted.endswith("[truncated]"))
    self.assertEqual(formatted.encode("utf-8").decode("utf-8"), formatted)
    self.assertEqual(record.__dict__, original_fields)

  def test_bounded_formatter_preserves_normal_record(self):
    _, BoundedUtf8Formatter, _, _, _, _ = bounded_logging_api()
    formatter = BoundedUtf8Formatter("%(message)s", max_record_bytes=64)
    record = logging.LogRecord(
      "normal", logging.INFO, __file__, 1, "ordinary log", (), None
    )

    self.assertEqual(formatter.format(record), "ordinary log")

  def test_bounded_formatter_limits_traceback_as_part_of_final_record(self):
    _, BoundedUtf8Formatter, _, _, _, _ = bounded_logging_api()
    formatter = BoundedUtf8Formatter(
      "%(levelname)s: %(message)s", max_record_bytes=1024
    )
    try:
      raise RuntimeError("trace界" * 2048)
    except RuntimeError:
      exception_info = sys.exc_info()
    record = logging.LogRecord(
      "trace", logging.ERROR, __file__, 1, "failed", (), exception_info
    )

    formatted = formatter.format(record)

    self.assertLessEqual(len(formatted.encode("utf-8")), 1024)
    self.assertTrue(formatted.endswith("[truncated]"))
    self.assertIsNone(record.exc_text)

  def test_default_console_and_file_share_the_same_record_bound(self):
    _, _, _, _, max_record_bytes, _ = bounded_logging_api()
    log_path = Path(self.temporary_directory.name) / "server.log"
    logger = LoggerManager(make_log_config(log_path)).get_logger()
    console = next(
      handler for handler in logger.handlers
      if type(handler) is logging.StreamHandler
    )
    console_output = io.StringIO()
    console.setStream(console_output)

    logger.error("界" * max_record_bytes)
    for handler in logger.handlers:
      handler.flush()

    console_record = console_output.getvalue().removesuffix("\n")
    file_record = log_path.read_text(encoding="utf-8").removesuffix("\n")
    self.assertEqual(console_record, file_record)
    self.assertLessEqual(len(console_record.encode("utf-8")), 64 * 1024)
    self.assertTrue(console_record.endswith("[truncated]"))

  def test_tiny_limits_really_roll_and_keep_secure_writable_files(self):
    (
      BoundedRotatingFileHandler, _, _, _, _, build_handler,
    ) = bounded_logging_api()
    log_path = Path(self.temporary_directory.name) / "roll" / "server.log"
    log_path.parent.mkdir()
    handler = build_handler(
      log_path,
      level="INFO",
      formatter_format="%(message)s",
      max_bytes=512,
      backup_count=2,
      max_record_bytes=256,
    )
    logger = logging.Logger("tiny", logging.INFO)
    logger.addHandler(handler)
    try:
      for index in range(20):
        logger.info("record-%02d-%s", index, "x" * 120)
      handler.flush()
      files = sorted(log_path.parent.glob("server.log*"))
      self.assertIsInstance(handler, BoundedRotatingFileHandler)
      self.assertGreaterEqual(len(files), 2)
      self.assertLessEqual(len(files), 3)
      self.assertTrue(all((path.stat().st_mode & 0o777) == 0o600 for path in files))

      logger.info("active-file-still-writable")
      handler.flush()
      self.assertIn(
        "active-file-still-writable",
        log_path.read_text(encoding="utf-8"),
      )
    finally:
      logger.removeHandler(handler)
      handler.close()

  def test_named_logger_file_helper_uses_bounded_handler(self):
    BoundedRotatingFileHandler, _, backup_count, max_bytes, _, _ = (
      bounded_logging_api()
    )
    log_path = Path(self.temporary_directory.name) / "server.log"
    manager = LoggerManager(make_log_config(log_path, log_save=False))
    logger = manager.register_logger("worker", "INFO")

    manager.set_logger_file_handler("worker", "worker.log", level="INFO")

    handler = next(
      one for one in logger.handlers
      if isinstance(one, BoundedRotatingFileHandler)
    )
    self.assertEqual(handler.maxBytes, max_bytes)
    self.assertEqual(handler.backupCount, backup_count)

  def test_bootstrap_file_helper_uses_bounded_handler(self):
    BoundedRotatingFileHandler, _, backup_count, max_bytes, _, _ = (
      bounded_logging_api()
    )
    previous_directory = os.getcwd()
    os.chdir(self.temporary_directory.name)
    try:
      loglib.init_bootstrap_logger()
      logger = logging.getLogger("bootstrap")
      handler = next(
        one for one in logger.handlers
        if isinstance(one, BoundedRotatingFileHandler)
      )
      self.assertEqual(handler.maxBytes, max_bytes)
      self.assertEqual(handler.backupCount, backup_count)
    finally:
      os.chdir(previous_directory)

  def test_named_logger_console_helper_uses_bounded_formatter(self):
    _, _, _, _, max_record_bytes, _ = bounded_logging_api()
    log_path = Path(self.temporary_directory.name) / "server.log"
    manager = LoggerManager(make_log_config(log_path, log_save=False))
    logger = manager.register_logger("console-worker", "INFO")
    manager.set_logger_console_handler(
      "console-worker", format="%(message)s", level="INFO"
    )
    handler = next(
      one for one in logger.handlers if type(one) is logging.StreamHandler
    )
    output = io.StringIO()
    handler.setStream(output)

    logger.info("界" * max_record_bytes)

    formatted = output.getvalue().removesuffix("\n")
    self.assertLessEqual(len(formatted.encode("utf-8")), 64 * 1024)
    self.assertTrue(formatted.endswith("[truncated]"))

  def test_repeated_manager_construction_keeps_one_file_and_console_handler(self):
    log_path = Path(self.temporary_directory.name) / "server.log"
    first = LoggerManager(make_log_config(log_path))
    second = LoggerManager(make_log_config(log_path))

    self.assertIs(first, second)
    handlers = first.get_logger().handlers
    self.assertEqual(
      len([one for one in handlers if isinstance(one, RotatingFileHandler)]),
      1,
    )
    self.assertEqual(
      len([one for one in handlers if type(one) is logging.StreamHandler]),
      1,
    )

  def test_tracked_runtime_probe_exercises_real_rollover_and_prints_exact_marker(self):
    self.assertTrue(RUNTIME_LOG_PROBE.is_file())

    completed = subprocess.run(
      [sys.executable, str(RUNTIME_LOG_PROBE)],
      cwd=PROJECT_ROOT,
      check=False,
      capture_output=True,
      text=True,
    )

    self.assertEqual(completed.returncode, 0, completed.stderr)
    self.assertEqual(
      completed.stdout.splitlines(),
      ["ok   runtime bounded persistent logging"],
    )
