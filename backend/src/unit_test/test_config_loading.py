from pathlib import Path
import tempfile
import threading
import unittest

import yaml

from backend.src.base import config as config_module
from backend.src.base.config import BaseConfig
from backend.src.library.configlib import get_config, load_config
from backend.src.unit_test.config_fixture import unified_config


class ConfigLoadingTest(unittest.TestCase):
  def setUp(self):
    self.original_config_path = config_module.CONFIG_PATH
    self.reset_base_config()

  @staticmethod
  def write_config(path, config):
    path.write_text(
      yaml.safe_dump(config, sort_keys=False, allow_unicode=True),
      encoding="utf-8",
    )

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
      expected_config = unified_config()
      expected_config["server"]["host"] = "127.0.0.1"
      expected_config["server"]["port"] = 5000
      expected_config["download"]["max_threads"] = 3
      self.write_config(config_path, expected_config)
      config_module.CONFIG_PATH = config_path

      config = load_config()

    self.assertEqual(config, expected_config)

  def test_base_config_get_config_isolates_nested_mutations(self):
    with tempfile.TemporaryDirectory() as temp_directory:
      config_path = Path(temp_directory) / "config.yml"
      config = unified_config()
      config["platform"]["douyin"]["post"]["count"] = 18
      self.write_config(config_path, config)
      config_module.CONFIG_PATH = config_path

      first_read = BaseConfig().get_config()
      first_read["platform"]["douyin"]["post"]["count"] = 999

      self.assertEqual(
        BaseConfig().get_config()["platform"]["douyin"]["post"]["count"],
        18,
      )

  def test_load_config_isolates_nested_mutations(self):
    with tempfile.TemporaryDirectory() as temp_directory:
      config_path = Path(temp_directory) / "config.yml"
      config = unified_config()
      config["server"]["port"] = 5000
      self.write_config(config_path, config)
      config_module.CONFIG_PATH = config_path

      first_read = load_config()
      first_read["server"]["port"] = 9999

      self.assertEqual(load_config()["server"]["port"], 5000)

  def test_get_config_isolates_nested_mapping_mutations(self):
    with tempfile.TemporaryDirectory() as temp_directory:
      config_path = Path(temp_directory) / "config.yml"
      config = unified_config()
      config["platform"]["douyin"]["post"]["count"] = 18
      self.write_config(config_path, config)
      config_module.CONFIG_PATH = config_path

      first_read = get_config("$.platform.douyin.post")
      first_read["count"] = 999

      self.assertEqual(
        get_config("$.platform.douyin.post")["count"],
        18,
      )

  def test_get_config_reads_a_strict_nested_path(self):
    with tempfile.TemporaryDirectory() as temp_directory:
      config_path = Path(temp_directory) / "config.yml"
      config = unified_config()
      config["server"]["port"] = 5101
      self.write_config(config_path, config)
      config_module.CONFIG_PATH = config_path

      self.assertEqual(get_config("$.server.port"), 5101)

  def test_get_config_rejects_missing_and_invalid_paths(self):
    with tempfile.TemporaryDirectory() as temp_directory:
      config_path = Path(temp_directory) / "config.yml"
      self.write_config(config_path, unified_config())
      config_module.CONFIG_PATH = config_path

      with self.assertRaisesRegex(KeyError, r"\$\.server\.missing"):
        get_config("$.server.missing")
      with self.assertRaisesRegex(ValueError, "path"):
        get_config("server.port")

  def test_load_config_rejects_a_missing_required_section(self):
    with tempfile.TemporaryDirectory() as temp_directory:
      config_path = Path(temp_directory) / "config.yml"
      config = unified_config()
      del config["platform"]["douyin"]["post"]
      self.write_config(config_path, config)
      config_module.CONFIG_PATH = config_path

      with self.assertRaisesRegex(RuntimeError, r"\$\.platform\.douyin\.post"):
        load_config()

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
      return unified_config()

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
