#!/usr/bin/env python3
"""Production-image proof for bounded application logging."""

import logging
from pathlib import Path
import stat
import sys
import tempfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if not (PROJECT_ROOT / "backend").is_dir():
  PROJECT_ROOT = Path("/app")
sys.path.insert(0, str(PROJECT_ROOT))

from backend.src.base.log import (
  BoundedRotatingFileHandler,
  BoundedUtf8Formatter,
  LOG_BACKUP_COUNT,
  LOG_MAX_BYTES,
  LOG_MAX_RECORD_BYTES,
  LoggerManager,
  build_bounded_file_handler,
)


MARKER = "ok   runtime bounded persistent logging"


def _fail(message):
  raise SystemExit("FAIL: {}".format(message))


def _close_logger(logger):
  for handler in logger.handlers[:]:
    logger.removeHandler(handler)
    handler.close()


def _prove_production_defaults(directory):
  log_path = directory / "production" / "server.log"
  manager = LoggerManager({
    "log_enable": True,
    "log_level": "INFO",
    "log_save": True,
    "log_file_path": str(log_path),
  })
  logger = manager.get_logger()
  file_handlers = [
    one for one in logger.handlers
    if isinstance(one, BoundedRotatingFileHandler)
  ]
  console_handlers = [
    one for one in logger.handlers if type(one) is logging.StreamHandler
  ]
  try:
    if len(file_handlers) != 1 or len(console_handlers) != 1:
      _fail("production LoggerManager handler topology is not bounded file plus console")
    file_handler = file_handlers[0]
    if file_handler.maxBytes != LOG_MAX_BYTES or LOG_MAX_BYTES != 10 * 1024 * 1024:
      _fail("production file maxBytes changed")
    if file_handler.backupCount != LOG_BACKUP_COUNT or LOG_BACKUP_COUNT != 9:
      _fail("production file backupCount changed")
    for handler in (file_handler, console_handlers[0]):
      formatter = handler.formatter
      if not isinstance(formatter, BoundedUtf8Formatter):
        _fail("production output path is missing the bounded formatter")
      if formatter.max_record_bytes != LOG_MAX_RECORD_BYTES:
        _fail("production output paths disagree on the record limit")
    if LOG_MAX_RECORD_BYTES != 64 * 1024:
      _fail("production record byte limit changed")
  finally:
    _close_logger(logger)


def _prove_real_rollover(directory):
  log_path = directory / "tiny" / "server.log"
  log_path.parent.mkdir()
  handler = build_bounded_file_handler(
    log_path,
    level="INFO",
    formatter_format="%(message)s",
    max_bytes=512,
    backup_count=2,
    max_record_bytes=256,
  )
  logger = logging.Logger("runtime-log-retention", logging.INFO)
  logger.addHandler(handler)
  try:
    for index in range(24):
      logger.info("record-%02d-%s", index, "界" * 40)
    handler.flush()
    files = sorted(log_path.parent.glob("server.log*"))
    if len(files) < 2:
      _fail("tiny-limit proof did not roll over")
    if len(files) > 3:
      _fail("tiny-limit proof exceeded active plus backup count")
    for path in files:
      if stat.S_IMODE(path.stat().st_mode) != 0o600:
        _fail("logger-owned file mode is not 0600")

    logger.info("active-file-still-writable")
    handler.flush()
    if "active-file-still-writable" not in log_path.read_text(encoding="utf-8"):
      _fail("active file was not writable after rollover")

    record = logging.LogRecord(
      "runtime-log-retention",
      logging.ERROR,
      __file__,
      1,
      "界" * 512,
      (),
      None,
    )
    formatted = handler.format(record)
    if len(formatted.encode("utf-8")) > 256:
      _fail("oversized UTF-8 record exceeded the injected limit")
    if not formatted.endswith("[truncated]"):
      _fail("oversized UTF-8 record did not carry the truncation marker")

    try:
      raise RuntimeError("trace界" * 512)
    except RuntimeError:
      exception_info = sys.exc_info()
    traceback_record = logging.LogRecord(
      "runtime-log-retention",
      logging.ERROR,
      __file__,
      1,
      "failed",
      (),
      exception_info,
    )
    formatted_traceback = handler.format(traceback_record)
    if len(formatted_traceback.encode("utf-8")) > 256:
      _fail("traceback exceeded the injected record limit")
    if not formatted_traceback.endswith("[truncated]"):
      _fail("oversized traceback did not carry the truncation marker")
    if traceback_record.exc_text is not None:
      _fail("formatting mutated the original LogRecord")
  finally:
    logger.removeHandler(handler)
    handler.close()


def main():
  with tempfile.TemporaryDirectory(prefix="smsd-log-retention-") as temporary:
    directory = Path(temporary)
    _prove_production_defaults(directory)
    _prove_real_rollover(directory)
  print(MARKER)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
