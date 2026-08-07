# Complete Unified Config Enablement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `config/config.yml` the only persistent runtime configuration source for Server, logging, database, Live, Post, and their shared Douyin components, then remove every legacy YAML configuration dependency.

**Architecture:** `BaseConfig` remains the only filesystem loader and `configlib` exposes full-config and strict JSON-style path reads. Runtime assemblers receive the full mapping and inject copied domain sections into API, Header, Login, Downloader, Live, and Post objects; no consumer accepts a configuration file path or falls back to legacy files.

**Tech Stack:** Python 3.12, standard-library `copy`, `pathlib`, `threading`, `unittest`, Flask, and PyYAML.

## Global Constraints

- `config/config.yml` is the only persistent runtime configuration source.
- Do not introduce environment-variable overrides, legacy YAML fallbacks, YAML write-back, hot reload, or database-backed configuration.
- Production URLs come from the existing frontend `POST /` JSON `urls` array.
- Keep `config/douyin/conf.ini` only as a test fixture; production modules must not read or reference it.
- Do not add Post URL classification or new Web routing in this plan.
- Runtime tokens and response data stay in object-local memory and must not mutate the `BaseConfig` mapping.
- Do not redesign Live networking, HLS/FLV extraction, or the download algorithms.
- Do not migrate the vendored `f2` project's configuration system.
- `config/config.yml` is ignored because it contains local credentials: update it locally when present, never stage it, and never print its values.
- Use `/home/wangyan/miniconda3/envs/smsd/bin/python` for all Python tests and checks.

---

### Task 1: Make the unified configuration contract strict and read-only

**Files:**
- Create: `backend/src/unit_test/config_fixture.py`
- Modify: `backend/src/base/config.py:16-108`
- Modify: `backend/src/library/configlib.py:8-59`
- Modify: `backend/src/unit_test/test_config_loading.py:1-96`

**Interfaces:**
- Consumes: project `config/config.yml` or a test replacement at `backend.src.base.config.CONFIG_PATH`.
- Produces: `load_config() -> dict` and `get_config(path: str) -> Any`, where paths use `$.server.port` syntax and missing paths raise.

- [ ] **Step 1: Add a shared, side-effect-free unified test fixture**

Create `backend/src/unit_test/config_fixture.py`:

```python
from copy import deepcopy
from pathlib import Path

from backend.src.library.baselib import load_yml


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_EXAMPLE_PATH = PROJECT_ROOT / "docs" / "design" / "config.yml.example"


def unified_config() -> dict:
  config = deepcopy(load_yml(CONFIG_EXAMPLE_PATH))
  config["database"]["enable"] = False
  config["download"]["test_mode"] = True
  config["download"]["save_response"] = False
  config["download"]["save_error_response"] = False
  config["log"]["log_save"] = False
  config["server"]["debug_mode"] = False
  return config
```

- [ ] **Step 2: Write failing strict-access and schema tests**

Extend `test_config_loading.py` with YAML files produced from the shared fixture:

```python
import yaml

from backend.src.library.configlib import get_config
from backend.src.unit_test.config_fixture import unified_config


def write_config(self, path, config):
  path.write_text(
    yaml.safe_dump(config, sort_keys=False, allow_unicode=True),
    encoding="utf-8",
  )


def test_get_config_reads_a_strict_nested_path(self):
  config = unified_config()
  config["server"]["port"] = 5101
  self.write_config(self.config_path, config)
  config_module.CONFIG_PATH = self.config_path

  self.assertEqual(get_config("$.server.port"), 5101)


def test_get_config_rejects_missing_and_invalid_paths(self):
  self.write_config(self.config_path, unified_config())
  config_module.CONFIG_PATH = self.config_path

  with self.assertRaisesRegex(KeyError, r"\$\.server\.missing"):
    get_config("$.server.missing")
  with self.assertRaisesRegex(ValueError, "path"):
    get_config("server.port")


def test_load_config_rejects_a_missing_required_section(self):
  config = unified_config()
  del config["platform"]["douyin"]["post"]
  self.write_config(self.config_path, config)
  config_module.CONFIG_PATH = self.config_path

  with self.assertRaisesRegex(RuntimeError, r"\$\.platform\.douyin\.post"):
    load_config()
```

Update the existing successful temporary YAML test to use `unified_config()` so the stricter root contract does not make it an invalid fixture.

- [ ] **Step 3: Run the tests and verify RED**

Run:

```bash
/home/wangyan/miniconda3/envs/smsd/bin/python -m unittest \
  backend.src.unit_test.test_config_loading -v
```

Expected: the nested read returns `None`, missing paths do not raise, and a missing Douyin section is accepted.

- [ ] **Step 4: Implement root validation and strict reads**

In `backend/src/base/config.py`, remove the empty `update_config()` method and validate required mappings after YAML parsing:

```python
REQUIRED_TOP_LEVEL_SECTIONS = (
  "database", "download", "log", "server", "migrate", "platform",
)
REQUIRED_DOUYIN_SECTIONS = (
  "download", "api", "headers", "login", "post", "live",
)


def _require_mapping(source: dict, key: str, path: str) -> dict:
  value = source.get(key)
  if not isinstance(value, dict):
    raise ValueError(f"{path} must be a mapping")
  return value


def __validate_config(self, config: dict) -> None:
  for section in REQUIRED_TOP_LEVEL_SECTIONS:
    _require_mapping(config, section, f"$.{section}")
  platform = _require_mapping(config, "platform", "$.platform")
  douyin = _require_mapping(platform, "douyin", "$.platform.douyin")
  for section in REQUIRED_DOUYIN_SECTIONS:
    _require_mapping(douyin, section, f"$.platform.douyin.{section}")
```

Call `self.__validate_config(config)` before assigning `self.__config`.

In `backend/src/library/configlib.py`, remove unused database environment constants and delete `set_config()`. Replace `get_config()` with:

```python
from backend.src.library.baselib import get_dict_attr, has_dict_attr


def get_config(path: str):
  if not isinstance(path, str) or not path.startswith("$."):
    raise ValueError("config path must start with '$.'")
  config = load_config()
  if not has_dict_attr(config, path):
    raise KeyError(f"Configuration path not found: {path}")
  return get_dict_attr(config, path)
```

Do not catch these caller errors and turn them into `None`.

- [ ] **Step 5: Run Task 1 tests and focused regressions**

Run:

```bash
/home/wangyan/miniconda3/envs/smsd/bin/python -m unittest \
  backend.src.unit_test.test_config_loading \
  backend.src.unit_test.test_unified_config_schema \
  backend.src.unit_test.test_log_config \
  backend.src.unit_test.test_live_downloader_construction -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit Task 1**

```bash
git add backend/src/base/config.py backend/src/library/configlib.py \
  backend/src/unit_test/config_fixture.py \
  backend/src/unit_test/test_config_loading.py
git commit -m "feat: add strict unified config access"
```

---

### Task 2: Start the Web server from the unified server section

**Files:**
- Create: `backend/src/unit_test/test_server_config.py`
- Modify: `server.py:1-166`

**Interfaces:**
- Consumes: full unified mapping through `create_app(config: dict = None, dispatcher = None)` and `run_server(config: dict = None)`.
- Produces: an import-safe Flask `app` whose host, port, debug mode, logger, and error response behavior use the same mapping.

- [ ] **Step 1: Write failing server configuration tests**

Create `test_server_config.py`:

```python
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


class ServerConfigTest(unittest.TestCase):
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
```

- [ ] **Step 2: Run the server tests and verify RED**

Run:

```bash
/home/wangyan/miniconda3/envs/smsd/bin/python -m unittest \
  backend.src.unit_test.test_server_config -v
```

Expected: importing `server` fails because `app` is referenced before construction, or the new factory functions are absent.

- [ ] **Step 3: Add import-safe configuration and startup boundaries**

In `server.py`, construct the Flask object before route decorators and keep runtime dependencies explicitly initialized:

```python
from backend.src.base.log import LoggerManager


app = Flask(
  __name__,
  static_folder="./frontend/src/static",
  template_folder="./frontend/src/templates",
)
platform_dispatcher = None
logger = logging.getLogger("bootstrap")


def _server_options(config: dict) -> dict:
  server = config.get("server")
  if not isinstance(server, dict):
    raise ValueError("$.server must be a mapping")
  host = server.get("host")
  port = server.get("port")
  debug_mode = server.get("debug_mode")
  if not isinstance(host, str) or not host.strip():
    raise ValueError("$.server.host must be a non-empty string")
  if type(port) is not int or not 1 <= port <= 65535:
    raise ValueError("$.server.port must be an integer from 1 to 65535")
  if type(debug_mode) is not bool:
    raise ValueError("$.server.debug_mode must be a boolean")
  return {"host": host, "port": port, "debug": debug_mode}


def create_app(config: dict = None, dispatcher=None):
  global platform_dispatcher, logger
  source = load_config() if config is None else config
  options = _server_options(source)
  LoggerManager(source["log"])
  logger = get_logger()
  platform_dispatcher = dispatcher or PlatformDispatcher()
  platform_dispatcher.register()
  app.debug = options["debug"]
  return app


def run_server(config: dict = None):
  source = load_config() if config is None else config
  options = _server_options(source)
  configured_app = create_app(source)
  configured_app.run(**options)
```

In the request error handler use `app.debug`, not `os.getenv()`. Replace the `__main__` block with `run_server()` and remove `dotenv` plus Server configuration environment reads.

- [ ] **Step 4: Run server and configuration regressions**

Run:

```bash
/home/wangyan/miniconda3/envs/smsd/bin/python -m unittest \
  backend.src.unit_test.test_server_config \
  backend.src.unit_test.test_config_loading \
  backend.src.unit_test.test_log_config -v
```

Expected: all tests pass without starting a real Flask server.

- [ ] **Step 5: Commit Task 2**

```bash
git add server.py backend/src/unit_test/test_server_config.py
git commit -m "feat: start server from unified config"
```

---

### Task 3: Restrict shared consumers to injected configuration mappings

**Files:**
- Create: `backend/src/unit_test/test_config_consumers.py`
- Modify: `backend/src/base/api.py:1-13`
- Modify: `backend/src/base/header.py:1-93`
- Modify: `backend/src/base/login.py:1-127`
- Modify: `backend/src/base/downloader.py:1-105`
- Modify: `backend/src/platform/douyin/douyin_api.py:1-74`
- Modify: `backend/src/platform/douyin/douyin_header.py:1-334`
- Modify: `backend/src/platform/douyin/douyin_login.py:1-80`
- Modify: `backend/src/unit_test/test_live_downloader_pipeline.py:129-225`

**Interfaces:**
- Consumes: `dict` sections for Header, Login, API, and Download.
- Produces: copied, mutation-isolated domain objects; `DouyinApi()` remains a unified-config no-argument convenience.

- [ ] **Step 1: Write failing mapping-only consumer tests**

Create `test_config_consumers.py`:

```python
from pathlib import Path
import unittest

from backend.src.platform.douyin.douyin_api import DouyinApi
from backend.src.platform.douyin.douyin_header import (
  DouyinLiveInfoHeader, DouyinPostInfoHeader, DouyinShareHeader,
)
from backend.src.platform.douyin.douyin_login import DouyinLogin
from backend.src.unit_test.config_fixture import unified_config


class ConfigConsumerTest(unittest.TestCase):
  def setUp(self):
    self.config = unified_config()
    self.douyin = self.config["platform"]["douyin"]

  def test_consumers_accept_copied_unified_sections(self):
    api_source = self.douyin["api"]
    header_source = self.douyin["headers"]
    login_source = self.douyin["login"]
    api = DouyinApi(api_source)
    share = DouyinShareHeader(header_source)
    live = DouyinLiveInfoHeader(header_source)
    post = DouyinPostInfoHeader(header_source)
    login = DouyinLogin(login_source)

    api_source["LIVE_DOMAIN"] = "mutated.invalid"
    header_source["share_live_url"]["accept"] = "mutated"
    login_source["msToken"] = "mutated"

    self.assertNotEqual(api.LIVE_DOMAIN, "mutated.invalid")
    share.init_share_live_header(True)
    self.assertNotEqual(share.to_dict()["accept"], "mutated")
    self.assertNotEqual(login.to_dict()["msToken"], "mutated")
    live.init_header(False)
    post.init_header(False)

  def test_consumers_reject_legacy_paths(self):
    legacy = Path("config/douyin/headers.yml")
    for consumer in (DouyinShareHeader, DouyinLiveInfoHeader,
                     DouyinPostInfoHeader, DouyinLogin, DouyinApi):
      with self.subTest(consumer=consumer.__name__):
        with self.assertRaisesRegex(ValueError, "mapping"):
          consumer(legacy)
```

- [ ] **Step 2: Run the consumer tests and verify RED**

Run:

```bash
/home/wangyan/miniconda3/envs/smsd/bin/python -m unittest \
  backend.src.unit_test.test_config_consumers -v
```

Expected: legacy paths are accepted, Header/Login still read files, and the Post Header annotation/constructor does not consistently accept mappings.

- [ ] **Step 3: Make base consumers mapping-only**

Use the same validation pattern in `Header` and `Login`:

```python
def __init__(self, config: dict) -> None:
  if not isinstance(config, dict):
    raise ValueError("configuration must be a mapping")
  self._header = deepcopy(config)  # Header
```

```python
def __init__(self, config: dict) -> None:
  if not isinstance(config, dict):
    raise ValueError("login configuration must be a mapping")
  self.__login = deepcopy(config)
  self.__dict__.update(self.__login)
```

Remove `Path`, PyYAML, `load_yml`, and default path imports from these base modules. Do not swallow initialization exceptions.

Make the base API contract mapping-based:

```python
class Api(ABC):
  def __init__(self, config: dict) -> None:
    if not isinstance(config, dict):
      raise ValueError("API configuration must be a mapping")
    super().__init__()
```

Make `Downloader.__init__(download_config: dict)` validate and deep-copy only the download section:

```python
def __init__(self, download_config: dict) -> None:
  if not isinstance(download_config, dict):
    raise ValueError("$.download must be a mapping")
  self.download_config = deepcopy(download_config)
```

Remove its `BaseConfig`, `DEFAULT_BASE_CONFIG_PATH`, Header, and Login construction. Its abstract `construct_aggregation_class()` becomes a pure subclass responsibility:

```python
@abstractmethod
def construct_aggregation_class(self, config: dict):
  raise NotImplementedError
```

- [ ] **Step 4: Remove Douyin path compatibility without changing domain behavior**

For `DouyinApi`, retain its no-argument unified load but reject every explicit non-mapping input:

```python
def __init__(self, config: dict = None) -> None:
  source = get_config("$.platform.douyin.api") if config is None else config
  if not isinstance(source, dict):
    raise ValueError("$.platform.douyin.api must be a mapping")
  self.__api = deepcopy(source)
  self.__dict__.update(self.__api)
```

Delete the YAML parser and `DEFAULT_API_CONFIG_PATH`.

Make every Douyin Header constructor accept `config: dict` and remove
`DEFAULT_HEADER_PATH`. Make `DouyinPostInfoHeader` accept `dict` like the other Header types. `DouyinLogin` requires its injected mapping.

Remove `DOUYIN_MSTOKEN` and `DOUYIN_DISABLE_F2_TOKEN_MANAGER` branches from `create_douyin_msToken()`. Runtime generation may call `f2` and retain the existing empty-token fallback; tests explicitly replace the generator method.

- [ ] **Step 5: Replace the Live environment-token test hook**

In `test_live_downloader_pipeline.py`, remove all mutation of
`DOUYIN_DISABLE_F2_TOKEN_MANAGER` and set the object boundary directly before the tested run:

```python
downloader.header.create_douyin_msToken = lambda: ""
try:
  downloader.run({"url": "https://v.douyin.com/example/"})
finally:
  live_module.request = original_request
  live_module.sleep = original_sleep
```

- [ ] **Step 6: Run shared-consumer and Live regressions**

Run:

```bash
/home/wangyan/miniconda3/envs/smsd/bin/python -m unittest \
  backend.src.unit_test.test_config_consumers \
  backend.src.unit_test.test_live_downloader_construction \
  backend.src.unit_test.test_live_downloader_pipeline -v
```

Expected: all tests pass without reading a configuration path or configuration environment variable.

- [ ] **Step 7: Commit Task 3**

```bash
git add backend/src/base/api.py backend/src/base/header.py \
  backend/src/base/login.py backend/src/base/downloader.py \
  backend/src/platform/douyin/douyin_api.py \
  backend/src/platform/douyin/douyin_header.py \
  backend/src/platform/douyin/douyin_login.py \
  backend/src/unit_test/test_config_consumers.py \
  backend/src/unit_test/test_live_downloader_pipeline.py
git commit -m "refactor: inject config mappings into shared consumers"
```

---

### Task 4: Load the Post construction chain from the unified mapping

**Files:**
- Create: `backend/src/unit_test/test_post_downloader_config.py`
- Modify: `backend/src/platform/douyin/douyin_post_config.py:1-190`
- Modify: `backend/src/platform/douyin/douyin_post_downloader.py:1-576`

**Interfaces:**
- Consumes: `DouyinPostConfig(config: dict = None)` and `DouyinPostDownloader(config: dict = None)`.
- Produces: a Post downloader assembled from `download`, `server`, and `platform.douyin.{download,post,headers,login,api}` plus `run(token: dict)` with a side-effect-free test-mode path.

- [ ] **Step 1: Write failing Post construction and token tests**

Create `test_post_downloader_config.py`:

```python
import unittest

from backend.src.platform.douyin import douyin_post_downloader as post_module
from backend.src.platform.douyin.douyin_api import DouyinApi
from backend.src.platform.douyin.douyin_header import DouyinPostInfoHeader
from backend.src.platform.douyin.douyin_login import DouyinLogin
from backend.src.unit_test.config_fixture import unified_config


class PostDownloaderConfigTest(unittest.TestCase):
  def post_config(self):
    config = unified_config()
    config["platform"]["douyin"]["download"]["type"] = "post"
    return config

  def test_constructs_every_member_from_the_unified_mapping(self):
    config = self.post_config()
    downloader = post_module.DouyinPostDownloader(config)

    self.assertIsInstance(downloader.header, DouyinPostInfoHeader)
    self.assertIsInstance(downloader.login, DouyinLogin)
    self.assertIsInstance(downloader.API, DouyinApi)
    self.assertEqual(downloader.config.max_threads,
                     config["download"]["max_threads"])
    self.assertEqual(downloader.config.type, "post")

  def test_runtime_updates_do_not_mutate_the_base_mapping(self):
    config = self.post_config()
    downloader = post_module.DouyinPostDownloader(config)
    downloader.config.update_post_share_url({"share_url": "https://example.test"})

    self.assertNotIn("share_url", config["platform"]["douyin"]["post"])

  def test_run_accepts_a_web_token_without_network_in_test_mode(self):
    config = self.post_config()
    downloader = post_module.DouyinPostDownloader(config)
    original_request = post_module.request
    calls = []
    post_module.request = lambda *args, **kwargs: calls.append((args, kwargs))
    try:
      result = downloader.run({
        "url": "https://www.douyin.com/user/test-sec-user",
      })
    finally:
      post_module.request = original_request

    self.assertIsNone(result)
    self.assertEqual(calls, [])
    self.assertEqual(downloader.config.share_url,
                     "https://www.douyin.com/user/test-sec-user")
```

- [ ] **Step 2: Run Post tests and verify RED**

Run:

```bash
/home/wangyan/miniconda3/envs/smsd/bin/python -m unittest \
  backend.src.unit_test.test_post_downloader_config -v
```

Expected: constructors treat the mapping as a filesystem path or call the legacy multi-file `DouyinConfig` chain.

- [ ] **Step 3: Replace `DouyinPostConfig` with a unified, object-local view**

Implement a standalone class that does not inherit `DouyinConfig`:

```python
from copy import deepcopy
from pathlib import Path

from backend.src.library.baselib import get_dict_attr
from backend.src.library.configlib import load_config


PROJECT_ROOT = Path(__file__).resolve().parents[4]


class DouyinPostConfig:
  def __init__(self, config: dict = None) -> None:
    source = load_config() if config is None else config
    if not isinstance(source, dict):
      raise ValueError("Unified configuration must be a mapping")
    self.__config = deepcopy(source)
    download = self.__require("$.download")
    server = self.__require("$.server")
    douyin_download = self.__require("$.platform.douyin.download")
    post = self.__require("$.platform.douyin.post")
    self.__dict__.update(download)
    self.__dict__.update(douyin_download)
    self.__dict__.update(post)
    self.login = download["user_login"]
    self.debug = server["debug_mode"]
    self.stream_platform = "douyin"
    self.build_path = str(PROJECT_ROOT / "config" / "build")
    self.share_url = ""
    self.nickname = ""

  def __require(self, path: str) -> dict:
    value = get_dict_attr(self.__config, path)
    if not isinstance(value, dict):
      raise ValueError(f"{path} must be a mapping")
    return value

  def to_dict(self) -> dict:
    return deepcopy(self.__config)
```

Keep the existing runtime update methods (`update_verifyFp`, `update_fp`, `update_a_bogus`, `update_count`, and `update_post_share_url`) but make them update only object-local attributes/config. Remove YAML parsing, path derivation, saving, and legacy imports.

- [ ] **Step 4: Assemble the Post downloader from sections**

Change construction to:

```python
def __init__(self, config: dict = None) -> None:
  source = load_config() if config is None else config
  self._source_config = deepcopy(source)
  super().__init__(self._source_config["download"])
  self.construct_aggregation_class(self._source_config)


def construct_aggregation_class(self, config: dict):
  douyin = config["platform"]["douyin"]
  self.config = DouyinPostConfig(config)
  self.header = DouyinPostInfoHeader(douyin["headers"])
  self.header.init_header(self.config.login)
  self.login = DouyinLogin(douyin["login"])
  self.API = DouyinApi(douyin["api"])
```

Remove `DEFAULT_BASE_CONFIG_PATH`, `DouyinHeader`, `UrlListConfig`, and all configuration-path fields. Retain PyYAML only where this downloader parses or saves response payloads, not for configuration.

Implement the existing `run()` boundary without adding new URL routing:

```python
def run(self, token: dict) -> None:
  if not isinstance(token, dict) or not isinstance(token.get("url"), str):
    raise ValueError("Post token must contain a URL")
  self.set_share_url(token["url"])
  if self.config.test_mode:
    return None
  if self.config.login:
    self.query_user_post()
  else:
    self.query_user_post_without_login()
```

- [ ] **Step 5: Run Post, shared-consumer, and Live regressions**

Run:

```bash
/home/wangyan/miniconda3/envs/smsd/bin/python -m unittest \
  backend.src.unit_test.test_post_downloader_config \
  backend.src.unit_test.test_config_consumers \
  backend.src.unit_test.test_live_downloader_construction \
  backend.src.unit_test.test_live_downloader_pipeline -v
```

Expected: all tests pass and test-mode Post construction performs no network or filesystem writes.

- [ ] **Step 6: Commit Task 4**

```bash
git add backend/src/platform/douyin/douyin_post_config.py \
  backend/src/platform/douyin/douyin_post_downloader.py \
  backend/src/unit_test/test_post_downloader_config.py
git commit -m "feat: load post downloader from unified config"
```

---

### Task 5: Remove production file-based URL input

**Files:**
- Modify: `docs/design/config.yml.example`
- Modify locally only when present: `config/config.yml` (ignored; never stage)
- Modify: `backend/src/platform/douyin/douyin_live_downloader.py:141-190,824-930`
- Delete: `backend/src/platform/douyin/douyin_url_list_config.py`
- Modify: `backend/src/unit_test/test_live_downloader_construction.py`
- Modify: `backend/src/unit_test/test_live_downloader_pipeline.py`
- Modify: `backend/src/unit_test/test_server_config.py`
- Modify: `backend/src/unit_test/test_unified_config_schema.py`

**Interfaces:**
- Consumes: frontend Web JSON `{"urls": [...]}` and explicit test tokens.
- Produces: Live/Post construction with no `UrlListConfig` member and no production reference to `conf.ini`.

- [ ] **Step 1: Write failing URL-source and schema tests**

Add assertions:

```python
def test_share_url_file_is_not_persistent_configuration(self):
  config = load_yml(CONFIG_EXAMPLE_PATH)
  self.assertNotIn(
    "share_url_file",
    config["platform"]["douyin"]["download"],
  )


def test_live_construction_has_no_file_url_list(self):
  downloader = DouyinLiveDownloader(unified_config())
  self.assertFalse(hasattr(downloader, "url_list"))
```

In `test_server_config.py`, retain the successful Web dispatch assertion from Task 2 as the production URL-source proof.

Add a test-only parser for `config/douyin/conf.ini` inside a unit-test module and assert it returns URLs. Do not import a production `UrlListConfig` class:

```python
def test_conf_ini_remains_available_as_test_input(self):
  parser = configparser.ConfigParser()
  parser.read(PROJECT_ROOT / "config" / "douyin" / "conf.ini")
  urls = [value for _key, value in parser.items("live")]
  self.assertTrue(urls)
```

- [ ] **Step 2: Run the URL-source tests and verify RED**

Run:

```bash
/home/wangyan/miniconda3/envs/smsd/bin/python -m unittest \
  backend.src.unit_test.test_server_config \
  backend.src.unit_test.test_live_downloader_construction \
  backend.src.unit_test.test_unified_config_schema -v
```

Expected: the example still contains `share_url_file` and Live still creates `UrlListConfig`.

- [ ] **Step 3: Remove URL-file configuration and runtime construction**

Delete `share_url_file` from `docs/design/config.yml.example` and, if it exists in the primary checkout, from the ignored local `config/config.yml`. Never stage the local file.

In `douyin_live_downloader.py`, remove the `UrlListConfig` import, `url_list` attribute, and constructor assignment. Change file-driven helper functions to explicit input:

```python
def download_multiple_live_with_patrolman(urls: list[str]):
  downloader = get_live_downloader()
  for url in urls:
    item = ListenerItem(func=downloader.run, args=({"url": url},))
    downloader.live_douyin_listener.add_sub_task(item)
  if urls and not downloader.live_douyin_listener.is_patrolman_actived():
    downloader.live_douyin_listener.start()


def download_live_test(urls: list[str]):
  downloader = get_live_downloader()
  for url in urls:
    downloader.run({"url": url})
```

Delete `douyin_url_list_config.py`; tests read `conf.ini` directly as a fixture.

- [ ] **Step 4: Run URL-source and pipeline regressions**

Run:

```bash
/home/wangyan/miniconda3/envs/smsd/bin/python -m unittest \
  backend.src.unit_test.test_server_config \
  backend.src.unit_test.test_live_downloader_construction \
  backend.src.unit_test.test_live_downloader_pipeline \
  backend.src.unit_test.test_post_downloader_config \
  backend.src.unit_test.test_unified_config_schema -v
```

Expected: all tests pass; the Web test supplies production URLs and only test code opens `conf.ini`.

- [ ] **Step 5: Commit tracked Task 5 changes**

Confirm `config/config.yml` is not staged, then commit:

```bash
git add docs/design/config.yml.example \
  backend/src/platform/douyin/douyin_live_downloader.py \
  backend/src/platform/douyin/douyin_url_list_config.py \
  backend/src/unit_test/test_live_downloader_construction.py \
  backend/src/unit_test/test_live_downloader_pipeline.py \
  backend/src/unit_test/test_server_config.py \
  backend/src/unit_test/test_unified_config_schema.py
git commit -m "refactor: use web urls as runtime input"
```

---

### Task 6: Delete legacy configuration and prove completion

**Files:**
- Delete: `config/base_config.yml`
- Delete: `config/douyin/api.yml`
- Delete: `config/douyin/download.yml`
- Delete: `config/douyin/headers.yml`
- Delete: `config/douyin/login.yml`
- Delete: `config/douyin/post.yml`
- Delete: `backend/src/base/default.py`
- Delete: `backend/src/platform/douyin/douyin_config.py`
- Modify: `backend/src/unit_test/test_default_config_imports.py`
- Modify: `backend/src/unit_test/test_unified_config_schema.py`

**Interfaces:**
- Consumes: Tasks 1-5 with zero runtime legacy dependency.
- Produces: a repository whose only project runtime YAML source is the ignored local `config/config.yml`, with `docs/design/config.yml.example` as its tracked redacted schema.

- [ ] **Step 1: Replace transitional import tests with final-state tests**

In `test_default_config_imports.py`, replace the old rule that some consumers must import `DEFAULT_BASE_CONFIG_PATH` with a runtime-source scan:

```python
RUNTIME_PATHS = [PROJECT_ROOT / "server.py", PROJECT_ROOT / "backend" / "src"]
FORBIDDEN_TEXT = (
  "DEFAULT_BASE_CONFIG_PATH",
  "base_config.yml",
  "config/douyin/api.yml",
  "config/douyin/download.yml",
  "config/douyin/headers.yml",
  "config/douyin/login.yml",
  "config/douyin/post.yml",
  "SERVER_HOST",
  "SERVER_PORT",
  "FLASK_DEBUG",
  "DOUYIN_MSTOKEN",
  "DOUYIN_DISABLE_F2_TOKEN_MANAGER",
)


def test_runtime_sources_have_no_legacy_configuration_dependency(self):
  sources = [PROJECT_ROOT / "server.py"]
  sources.extend(
    path for path in (PROJECT_ROOT / "backend" / "src").rglob("*.py")
    if "unit_test" not in path.parts
  )
  violations = {
    str(path.relative_to(PROJECT_ROOT)): marker
    for path in sources
    for marker in FORBIDDEN_TEXT
    if marker in path.read_text(encoding="utf-8")
  }
  self.assertEqual(violations, {})


def test_conf_ini_is_referenced_only_by_tests(self):
  production_sources = [
    path for path in (PROJECT_ROOT / "backend" / "src").rglob("*.py")
    if "unit_test" not in path.parts
  ]
  self.assertEqual([
    str(path.relative_to(PROJECT_ROOT))
    for path in production_sources
    if "conf.ini" in path.read_text(encoding="utf-8")
  ], [])
```

In `test_unified_config_schema.py`, replace reads of files scheduled for deletion with:

```python
def test_all_legacy_configuration_files_are_removed(self):
  legacy_paths = [
    PROJECT_ROOT / "config" / "base_config.yml",
    PROJECT_ROOT / "config" / "douyin" / "api.yml",
    PROJECT_ROOT / "config" / "douyin" / "download.yml",
    PROJECT_ROOT / "config" / "douyin" / "headers.yml",
    PROJECT_ROOT / "config" / "douyin" / "login.yml",
    PROJECT_ROOT / "config" / "douyin" / "post.yml",
    PROJECT_ROOT / "backend" / "src" / "base" / "default.py",
    PROJECT_ROOT / "backend" / "src" / "platform" / "douyin" / "douyin_config.py",
  ]
  self.assertEqual([path for path in legacy_paths if path.exists()], [])
  self.assertTrue((PROJECT_ROOT / "config" / "douyin" / "conf.ini").is_file())
```

- [ ] **Step 2: Run the final-state tests and verify RED**

Run:

```bash
/home/wangyan/miniconda3/envs/smsd/bin/python -m unittest \
  backend.src.unit_test.test_default_config_imports \
  backend.src.unit_test.test_unified_config_schema -v
```

Expected: legacy files and any remaining forbidden runtime reference cause failures.

- [ ] **Step 3: Remove remaining runtime references, then delete exact legacy files**

Resolve every reported production reference without adding compatibility aliases. Delete only the exact files listed in this task. Preserve `config/douyin/conf.ini`.

- [ ] **Step 4: Run the complete unit-test suite**

Run:

```bash
/home/wangyan/miniconda3/envs/smsd/bin/python -m unittest discover \
  -s backend/src/unit_test -p 'test_*.py' -v
```

Expected: zero failures and zero errors.

- [ ] **Step 5: Run static, syntax, and dependency gates**

Run:

```bash
/home/wangyan/miniconda3/envs/smsd/bin/python -m compileall -q \
  server.py backend/src
git diff --check
rg -n 'DEFAULT_BASE_CONFIG_PATH|base_config\.yml|config/douyin/(api|download|headers|login|post)\.yml|SERVER_HOST|SERVER_PORT|FLASK_DEBUG|DOUYIN_MSTOKEN|DOUYIN_DISABLE_F2_TOKEN_MANAGER' \
  server.py backend/src --glob '*.py' --glob '!backend/src/unit_test/**'
rg -n 'conf\.ini|UrlListConfig' \
  server.py backend/src --glob '*.py' --glob '!backend/src/unit_test/**'
```

Expected: compile and diff checks exit zero; both `rg` commands return no matches. Treat `rg` exit code 1 with empty output as success for the absence checks.

- [ ] **Step 6: Validate the ignored local configuration without exposing values**

In the primary checkout, if `config/config.yml` exists, load it and assert only structure/field absence; do not print the mapping:

```bash
/home/wangyan/miniconda3/envs/smsd/bin/python -c 'from pathlib import Path; import yaml; p=Path("config/config.yml"); c=yaml.safe_load(p.read_text(encoding="utf-8")); assert isinstance(c, dict); assert "share_url_file" not in c["platform"]["douyin"]["download"]'
```

Expected: exit zero. If an isolated worktree lacks this ignored local file, record the check as pending primary-checkout finalization; do not create a credential-bearing replacement.

- [ ] **Step 7: Commit Task 6**

```bash
git add config/base_config.yml config/douyin/api.yml \
  config/douyin/download.yml config/douyin/headers.yml \
  config/douyin/login.yml config/douyin/post.yml \
  backend/src/base/default.py \
  backend/src/platform/douyin/douyin_config.py \
  backend/src/unit_test/test_default_config_imports.py \
  backend/src/unit_test/test_unified_config_schema.py
git commit -m "chore: remove legacy configuration files"
```

- [ ] **Step 8: Request final read-only review**

Review the complete feature range against
`docs/superpowers/specs/2026-08-07-complete-unified-config-enablement-design.md`.
The reviewer must verify all nine acceptance criteria, constructor/API compatibility, no credential exposure, no production `conf.ini` reads, and no scope expansion into Post routing or Live networking.
