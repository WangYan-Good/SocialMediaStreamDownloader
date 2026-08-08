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

  def test_default_config_paths_point_to_canonical_project_files(self):
    project_root = Path(__file__).resolve().parents[3]
    expected_path = project_root / "config" / "config.yml"
    expected_example_path = project_root / "docs" / "design" / "config.yml.example"

    self.assertEqual(config_module.CONFIG_PATH, expected_path)
    self.assertEqual(
      getattr(config_module, "CONFIG_EXAMPLE_PATH", None),
      expected_example_path,
    )

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

  def test_load_config_reports_missing_contract_paths_without_actual_values(self):
    with tempfile.TemporaryDirectory() as temp_directory:
      config_path = Path(temp_directory) / "config.yml"
      config = unified_config()
      del config["database"]["host"]
      del config["platform"]["douyin"]["live"]["hls_stall_timeout"]
      config["actual_only_secret"] = "do-not-expose-this-value"
      self.write_config(config_path, config)
      config_module.CONFIG_PATH = config_path

      with self.assertRaises(RuntimeError) as error:
        load_config()

    message = str(error.exception)
    database_path = "$.database.host"
    live_path = "$.platform.douyin.live.hls_stall_timeout"
    self.assertIn(database_path, message)
    self.assertIn(live_path, message)
    self.assertLess(message.index(database_path), message.index(live_path))
    self.assertNotIn("do-not-expose-this-value", message)

  def test_load_config_retains_actual_only_top_level_and_nested_keys(self):
    with tempfile.TemporaryDirectory() as temp_directory:
      config_path = Path(temp_directory) / "config.yml"
      config = unified_config()
      config["actual_only"] = {"feature_enabled": False}
      config["platform"]["douyin"]["live"]["actual_only_timeout"] = 0
      self.write_config(config_path, config)
      config_module.CONFIG_PATH = config_path

      loaded_config = load_config()

    self.assertEqual(
      loaded_config["actual_only"],
      {"feature_enabled": False},
    )
    self.assertEqual(
      loaded_config["platform"]["douyin"]["live"]["actual_only_timeout"],
      0,
    )

  def test_load_config_accepts_existing_null_leaves(self):
    with tempfile.TemporaryDirectory() as temp_directory:
      config_path = Path(temp_directory) / "config.yml"
      config = unified_config()
      self.assertIsNone(config["platform"]["douyin"]["login"]["msToken"])
      self.assertIsNone(config["platform"]["douyin"]["live"]["params"]["room_id"])
      self.write_config(config_path, config)
      config_module.CONFIG_PATH = config_path

      loaded_config = load_config()

    self.assertIsNone(loaded_config["platform"]["douyin"]["login"]["msToken"])
    self.assertIsNone(
      loaded_config["platform"]["douyin"]["live"]["params"]["room_id"]
    )

  def test_load_config_rejects_scalar_in_place_of_required_mapping(self):
    with tempfile.TemporaryDirectory() as temp_directory:
      config_path = Path(temp_directory) / "config.yml"
      config = unified_config()
      config["platform"]["douyin"]["live"] = "not-a-mapping"
      self.write_config(config_path, config)
      config_module.CONFIG_PATH = config_path

      with self.assertRaisesRegex(RuntimeError, r"\$\.platform\.douyin\.live"):
        load_config()

  def test_failed_first_load_can_retry_after_actual_file_is_corrected(self):
    with tempfile.TemporaryDirectory() as temp_directory:
      config_path = Path(temp_directory) / "config.yml"
      incomplete_config = unified_config()
      del incomplete_config["database"]["host"]
      self.write_config(config_path, incomplete_config)
      config_module.CONFIG_PATH = config_path

      with self.assertRaisesRegex(RuntimeError, r"\$\.database\.host"):
        load_config()

      complete_config = unified_config()
      complete_config["server"]["port"] = 5102
      self.write_config(config_path, complete_config)

      loaded_config = load_config()

    self.assertEqual(loaded_config["server"]["port"], 5102)

  def test_load_config_rejects_non_mapping_yaml(self):
    with tempfile.TemporaryDirectory() as temp_directory:
      config_path = Path(temp_directory) / "config.yml"
      config_path.write_text("- server\n- download\n", encoding="utf-8")
      config_module.CONFIG_PATH = config_path

      with self.assertRaisesRegex(RuntimeError, str(config_path)):
        load_config()

  def test_concurrent_first_load_reads_actual_and_example_once_each(self):
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
    self.assertEqual(
      load_calls,
      [
        config_module.CONFIG_PATH,
        Path(__file__).resolve().parents[3] / "docs" / "design" / "config.yml.example",
      ],
    )


if __name__ == "__main__":
  unittest.main()
