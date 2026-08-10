import importlib
import os
import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]

##
## unittest 会导入 unit_test 目录下每一个 test_*.py。任何在导入期写入
## os.environ 的模块，都会把自己的配置泄漏给同一次运行中的其它测试。
## 这里锁住该不变量：曾经有人在 test_db_config 里调用 load_dotenv()，
## .env 中的 FLASK_DEBUG=True 因此进入环境，Flask 建 app 时打开 debug，
## PROPAGATE_EXCEPTIONS 随之生效，一个断言 500 响应的测试改为看到异常穿透。
##
DISCOVERED_MODULES = sorted(
  path.stem for path in (PROJECT_ROOT / "backend/src/unit_test").glob("test_*.py")
)


class FixtureIsolationTest(unittest.TestCase):
  def test_no_test_module_writes_to_the_environment_on_import(self):
    ##
    ## 在子进程里逐个导入并比对环境快照，避免污染本进程。
    ##
    script = (
      "import json, os, importlib, sys\n"
      "sys.path.insert(0, {root!r})\n"
      "before = dict(os.environ)\n"
      "leaked = {{}}\n"
      "for name in {modules!r}:\n"
      "    try:\n"
      "        importlib.import_module('backend.src.unit_test.' + name)\n"
      "    except Exception:\n"
      "        continue\n"
      "    added = {{k: v for k, v in os.environ.items() if k not in before}}\n"
      "    if added:\n"
      "        leaked[name] = sorted(added)\n"
      "        before = dict(os.environ)\n"
      "print(json.dumps(leaked))\n"
    ).format(root=str(PROJECT_ROOT), modules=DISCOVERED_MODULES)

    completed = subprocess.run(
      [sys.executable, "-c", script],
      capture_output=True,
      text=True,
      cwd=str(PROJECT_ROOT),
      timeout=120,
    )
    self.assertEqual(0, completed.returncode, completed.stderr[-500:])

    import json

    leaked = json.loads(completed.stdout.strip().splitlines()[-1])
    self.assertEqual(
      {},
      leaked,
      "导入这些测试模块时写入了环境变量，会污染同一次运行的其它测试: {}".format(leaked),
    )

  def test_the_database_fixture_reads_dotenv_without_loading_it(self):
    module = importlib.import_module("backend.src.unit_test.test_db_config")

    self.assertFalse(
      hasattr(module, "load_dotenv"),
      "改回 load_dotenv 会把 .env 写进整个进程的环境",
    )
    marker = "SMSD_FIXTURE_ISOLATION_PROBE"
    self.assertNotIn(marker, os.environ)
    module.get_test_db_config()
    self.assertNotIn(marker, os.environ)

  def test_the_database_fixture_lets_the_real_environment_win(self):
    module = importlib.import_module("backend.src.unit_test.test_db_config")

    original = os.environ.get("MYSQL_HOST")
    os.environ["MYSQL_HOST"] = "environment-wins.example"
    try:
      self.assertEqual("environment-wins.example", module.get_test_db_config()["host"])
    finally:
      if original is None:
        del os.environ["MYSQL_HOST"]
      else:
        os.environ["MYSQL_HOST"] = original


if __name__ == "__main__":
  unittest.main()
