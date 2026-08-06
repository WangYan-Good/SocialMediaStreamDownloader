from pathlib import Path
import tempfile
import threading
import unittest

from backend.src.base import config as config_module
from backend.src.base.config import BaseConfig
from backend.src.library.configlib import load_config


class ConfigLoadingTest(unittest.TestCase):
  def setUp(self):
    self.original_config_path = config_module.CONFIG_PATH
    self.reset_base_config()

  def tearDown(self):
    config_module.CONFIG_PATH = self.original_config_path
    self.reset_base_config()

  @staticmethod
  def reset_base_config():
    if hasattr(BaseConfig, "_instance"):
      delattr(BaseConfig, "_instance")
    BaseConfig._BaseConfig__initialized = False
    BaseConfig._BaseConfig__config = {}

  def test_default_config_path_points_to_project_config(self):
    expected_path = Path(__file__).resolve().parents[3] / "config" / "config.yml"

    self.assertEqual(config_module.CONFIG_PATH, expected_path)

  def test_load_config_returns_nested_yaml_mapping(self):
    with tempfile.TemporaryDirectory() as temp_directory:
      config_path = Path(temp_directory) / "config.yml"
      config_path.write_text(
        "server:\n"
        "  host: 127.0.0.1\n"
        "  port: 5000\n"
        "download:\n"
        "  max_threads: 3\n",
        encoding="utf-8"
      )
      config_module.CONFIG_PATH = config_path

      config = load_config()

    self.assertEqual(config, {
      "server": {
        "host": "127.0.0.1",
        "port": 5000
      },
      "download": {
        "max_threads": 3
      }
    })

  def test_load_config_rejects_non_mapping_yaml(self):
    with tempfile.TemporaryDirectory() as temp_directory:
      config_path = Path(temp_directory) / "config.yml"
      config_path.write_text("- server\n- download\n", encoding="utf-8")
      config_module.CONFIG_PATH = config_path

      with self.assertRaisesRegex(RuntimeError, str(config_path)):
        load_config()

  def test_concurrent_first_load_reads_config_once(self):
    load_barrier = threading.Barrier(2)
    load_calls = []
    load_calls_lock = threading.Lock()

    def controlled_load(_path):
      with load_calls_lock:
        load_calls.append(_path)
      try:
        load_barrier.wait(timeout=0.2)
      except threading.BrokenBarrierError:
        pass
      return {"environment": "test"}

    original_load_yml = config_module.load_yml
    config_module.load_yml = controlled_load
    try:
      threads = [threading.Thread(target=load_config) for _ in range(2)]
      for thread in threads:
        thread.start()
      for thread in threads:
        thread.join(timeout=1)
    finally:
      config_module.load_yml = original_load_yml

    self.assertTrue(all(not thread.is_alive() for thread in threads))
    self.assertEqual(len(load_calls), 1)


if __name__ == "__main__":
  unittest.main()
