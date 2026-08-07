# Unified Log Config Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `LoggerManager` consume the unified YAML `log` section and remove its runtime dependency on `config/base_config.yml`.

**Architecture:** `LoggerManager` accepts an optional log-section mapping for injection; otherwise it reads `BaseConfig().get_config()["log"]`. It validates the four logging fields once, creates console/file handlers from that immutable initialization state, and preserves the existing singleton and public `loglib` APIs.

**Tech Stack:** Python 3.13, standard-library `logging`, `pathlib`, `threading`, and `unittest`.

## Global Constraints

- Only migrate the logging configuration chain.
- Do not modify `DouyinConfig`, `DouyinPostConfig`, or `DouyinPostDownloader`.
- Do not delete `config/base_config.yml` or `backend/src/base/default.py` in this batch.
- Preserve `register_logger()`, `get_logger()`, `set_logger_file_handler()`, and `set_logger_console_handler()` call signatures.
- `log_file_path` is the complete default log filename, not a directory.
- Use `/home/wangyan/miniconda3/envs/smsd/bin/python` for tests.

---

### Task 1: Load and apply the unified log section

**Files:**
- Create: `backend/src/unit_test/test_log_config.py`
- Modify: `backend/src/base/log.py:6-141`

**Interfaces:**
- Consumes: `BaseConfig().get_config() -> dict` and optional `LoggerManager(config: dict)` log-section injection.
- Produces: one initialized default `logging.Logger` returned by `LoggerManager.get_logger("default")`.

- [ ] **Step 1: Write failing tests for enabled file logging and disabled file logging**

Create a `unittest.TestCase` with a test-only reset helper that closes handlers, deletes `LoggerManager._instance`, and resets the mangled class initialization fields. Use literal injected configurations:

```python
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
```

- [ ] **Step 2: Run the new tests and verify RED**

Run:

```bash
/home/wangyan/miniconda3/envs/smsd/bin/python -m unittest \
  backend.src.unit_test.test_log_config -v
```

Expected: ERROR because the existing `LoggerManager.__init__()` does not accept an injected configuration.

- [ ] **Step 3: Implement unified configuration loading and handler construction**

In `backend/src/base/log.py`:

```python
from backend.src.base.config import BaseConfig

VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

def __init__(self, config: dict = None) -> None:
  if self.__initialized:
    return
  with self.__instance_Lock:
    if self.__initialized:
      return
    log_config = self.__load_log_config(config)
    self.__configure(log_config)
    self.__logger_queue = {}
    self.__init_default_logger()
    self.__initialized = True

def __load_log_config(self, config):
  if config is None:
    config = BaseConfig().get_config().get("log")
  if not isinstance(config, dict):
    raise ValueError("Unified log config must be a mapping")
  return config
```

Implement validation and derived paths without mutating the supplied mapping:

```python
def __configure(self, config: dict) -> None:
  log_enable = config.get("log_enable")
  log_level = config.get("log_level")
  log_save = config.get("log_save")
  log_file_path = config.get("log_file_path")

  if type(log_enable) is not bool:
    raise ValueError("log_enable must be a boolean")
  if not isinstance(log_level, str) or log_level not in VALID_LOG_LEVELS:
    raise ValueError("log_level must be a standard logging level")
  if type(log_save) is not bool:
    raise ValueError("log_save must be a boolean")
  if log_save and (
    not isinstance(log_file_path, str) or not log_file_path.strip()
  ):
    raise ValueError("log_file_path must be a non-empty string")

  self.__log_enable = log_enable
  self.__log_save = log_save
  self.__DEFAULT_LOGGER_LEVEL = log_level
  self.__DEFAULT_LOG_FILE_PATH = (
    Path(log_file_path) if isinstance(log_file_path, str) and log_file_path.strip()
    else None
  )
  self.__DEFAULT_LOG_FILE_DIR = (
    self.__DEFAULT_LOG_FILE_PATH.parent
    if self.__DEFAULT_LOG_FILE_PATH is not None
    else Path(".")
  )
  if self.__log_save:
    self.__DEFAULT_LOG_FILE_DIR.mkdir(parents=True, exist_ok=True)
```

Build the default console handler at `self.__DEFAULT_LOGGER_LEVEL`. Add this exact default file handler only when `self.__log_save` is true:

```python
file_handler = TimedRotatingFileHandler(
  filename=str(self.__DEFAULT_LOG_FILE_PATH),
  when="midnight",
  interval=1,
  encoding="utf-8",
)
```

- [ ] **Step 4: Run target tests and verify GREEN**

Run the command from Step 2. Expected: both tests PASS and no files are created for `log_save=false`.

- [ ] **Step 5: Commit Task 1**

```bash
git add backend/src/base/log.py backend/src/unit_test/test_log_config.py
git commit -m "feat: load logger settings from unified config"
```

---

### Task 2: Preserve singleton and public logging API behavior

**Files:**
- Modify: `backend/src/unit_test/test_log_config.py`
- Modify: `backend/src/base/log.py:48-81,150-230`
- Modify: `backend/src/library/loglib.py:14-40`

**Interfaces:**
- Consumes: initialized `LoggerManager` singleton from Task 1.
- Produces: public `loglib.get_logger()` returning the configured default logger and registered loggers respecting `log_enable`.

- [ ] **Step 1: Write failing lifecycle and public API tests**

Add tests that assert observable identity and state:

```python
def test_repeated_construction_does_not_replace_default_logger(self):
  first_manager = LoggerManager(make_log_config(self.log_path))
  first_logger = first_manager.get_logger()
  second_manager = LoggerManager(
    make_log_config(self.other_log_path, log_level="ERROR")
  )
  self.assertIs(second_manager, first_manager)
  self.assertIs(second_manager.get_logger(), first_logger)

def test_public_get_logger_returns_initialized_default_logger(self):
  configured_logger = LoggerManager(
    make_log_config(self.log_path, log_save=False)
  ).get_logger()
  self.assertIs(loglib.get_logger(), configured_logger)

def test_log_enable_false_disables_default_and_registered_loggers(self):
  manager = LoggerManager(
    make_log_config(self.log_path, log_enable=False, log_save=False)
  )
  self.assertTrue(manager.get_logger().disabled)
  self.assertTrue(manager.register_logger("worker", "INFO").disabled)
```

- [ ] **Step 2: Run the lifecycle tests and verify RED**

Run:

```bash
/home/wangyan/miniconda3/envs/smsd/bin/python -m unittest \
  backend.src.unit_test.test_log_config -v
```

Expected: at least the public getter test FAILS because `loglib.get_logger()` checks the nonexistent `_instances` attribute and returns the bootstrap logger.

- [ ] **Step 3: Fix singleton initialization and public getter detection**

Use the mangled boolean directly in `LoggerManager.__init__`, reset instance queues only during first successful initialization, and set `logger.disabled = not self.__log_enable` for default and registered loggers.

In `backend/src/library/loglib.py` replace `_instances` detection with:

```python
def get_logger(name: str = "default") -> Logger:
  manager = getattr(LoggerManager, "_instance", None)
  if manager is None or not getattr(
    manager,
    "_LoggerManager__initialized",
    False,
  ):
    return logging.getLogger("bootstrap")
  return manager.get_logger(name)
```

- [ ] **Step 4: Run all logging tests and verify GREEN**

Run the command from Step 2. Expected: all lifecycle and configuration tests PASS.

- [ ] **Step 5: Commit Task 2**

```bash
git add backend/src/base/log.py backend/src/library/loglib.py \
  backend/src/unit_test/test_log_config.py
git commit -m "fix: preserve configured logger singleton"
```

---

### Task 3: Validate configuration errors and remove the legacy log dependency

**Files:**
- Modify: `backend/src/unit_test/test_log_config.py`
- Modify: `backend/src/base/log.py:6-18`

**Interfaces:**
- Consumes: Task 1 configuration validator.
- Produces: retryable initialization failures and a logging module with no `DEFAULT_BASE_CONFIG_PATH` dependency.

- [ ] **Step 1: Write failing validation and default-source tests**

Add table-driven invalid configuration cases with literal expected field names:

```python
def test_invalid_log_config_is_rejected_and_initialization_can_retry(self):
  invalid_configs = [
    ([], "mapping"),
    ({"log_enable": "yes", "log_level": "INFO", "log_save": False}, "log_enable"),
    ({"log_enable": True, "log_level": "TRACE", "log_save": False}, "log_level"),
    ({"log_enable": True, "log_level": "INFO", "log_save": "yes"}, "log_save"),
    ({"log_enable": True, "log_level": "INFO", "log_save": True, "log_file_path": ""}, "log_file_path"),
  ]
  for invalid_config, expected_text in invalid_configs:
    self.reset_logger_manager()
    with self.subTest(config=invalid_config):
      with self.assertRaisesRegex(ValueError, expected_text):
        LoggerManager(invalid_config)

  self.reset_logger_manager()
  manager = LoggerManager(make_log_config(self.log_path, log_save=False))
  self.assertEqual(manager.get_logger().level, logging.DEBUG)
```

Patch `backend.src.base.log.BaseConfig` with a small fake returning `{"log": make_log_config(...)}` and construct `LoggerManager()` without arguments. Assert the configured file path and level, proving the default path consumes the unified mapping rather than a legacy file.

- [ ] **Step 2: Run target tests and verify RED**

Run:

```bash
/home/wangyan/miniconda3/envs/smsd/bin/python -m unittest \
  backend.src.unit_test.test_log_config -v
```

Expected: invalid inputs expose missing validation or leave singleton state that prevents retry.

- [ ] **Step 3: Complete retry-safe validation and legacy import removal**

Ensure `LoggerManager.__init__` sets `__initialized = True` only after handler construction succeeds and leaves it false on any exception. Remove these imports from `backend/src/base/log.py`:

```python
import yaml as yml
from backend.src.base.default import DEFAULT_BASE_CONFIG_PATH
```

The no-argument construction test must remain the proof that the logging chain reads `BaseConfig().get_config()["log"]`; do not add a source-text or AST assertion for removed imports.

- [ ] **Step 4: Run logging and import-policy tests**

Run:

```bash
/home/wangyan/miniconda3/envs/smsd/bin/python -m unittest \
  backend.src.unit_test.test_log_config \
  backend.src.unit_test.test_default_config_imports -v
```

Expected: all tests PASS.

- [ ] **Step 5: Run focused regression and static checks**

Run:

```bash
/home/wangyan/miniconda3/envs/smsd/bin/python -m unittest \
  backend.src.unit_test.test_config_loading \
  backend.src.unit_test.test_default_config_imports \
  backend.src.unit_test.test_unified_config_schema \
  backend.src.unit_test.test_live_downloader_construction \
  backend.src.unit_test.test_live_downloader_pipeline \
  backend.src.unit_test.test_log_config -v
git diff --check
/home/wangyan/miniconda3/envs/smsd/bin/python -m py_compile \
  backend/src/base/log.py backend/src/library/loglib.py \
  backend/src/unit_test/test_log_config.py
```

Expected: zero test failures, zero syntax errors, and no diff whitespace errors.

- [ ] **Step 6: Commit Task 3**

```bash
git add backend/src/base/log.py backend/src/library/loglib.py \
  backend/src/unit_test/test_log_config.py
git commit -m "test: verify unified logger configuration"
```

---

### Task 4: Review the completed migration

**Files:**
- Review: `backend/src/base/log.py`
- Review: `backend/src/library/loglib.py`
- Review: `backend/src/unit_test/test_log_config.py`
- Review: `backend/src/unit_test/test_default_config_imports.py`

**Interfaces:**
- Consumes: Tasks 1-3 committed implementation.
- Produces: review verdict against `docs/superpowers/specs/2026-08-07-unified-log-config-design.md`.

- [ ] **Step 1: Request a read-only code review**

Ask the reviewer to verify unified config loading, singleton safety, handler lifecycle, error recovery, public API compatibility, and absence of `base_config.yml` reads from the logging chain.

- [ ] **Step 2: Address all Critical and Important findings**

For each finding, reproduce it with a failing test, implement the minimal correction, and rerun the focused regression command from Task 3.

- [ ] **Step 3: Record final evidence**

Run `git status --short`, `git log -4 --oneline`, and the complete focused regression command from Task 3. Report exact test count and commit hashes; do not push.
