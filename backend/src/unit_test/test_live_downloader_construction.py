import configparser
import importlib
from pathlib import Path
import tempfile
from threading import Barrier, Lock, Thread
from time import sleep
import unittest

from backend.src.library.baselib import load_yml
from backend.src.unit_test.config_fixture import unified_config


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_EXAMPLE_PATH = PROJECT_ROOT / "docs" / "design" / "config.yml.example"


class LiveDownloaderConstructionTest(unittest.TestCase):
  def test_import_does_not_construct_downloader(self):
    module = importlib.import_module(
      "backend.src.platform.douyin.douyin_live_downloader"
    )

    self.assertIsNone(module.downloader)

  def test_test_mode_initializes_database_like_normal_mode(self):
    module = importlib.import_module(
      "backend.src.platform.douyin.douyin_live_downloader"
    )
    config = load_yml(CONFIG_EXAMPLE_PATH)
    config["database"]["enable"] = True
    config["download"]["test_mode"] = True

    original_database = module.DouyinShareUrlTable
    database_connections = []

    class RecordingDatabase:
      def __init__(self, **kwargs):
        database_connections.append(kwargs)

    module.DouyinShareUrlTable = RecordingDatabase
    try:
      with tempfile.TemporaryDirectory() as temporary_directory:
        save_path = Path(temporary_directory) / "downloads"
        config["download"]["save_path"] = str(save_path)

        downloader = module.DouyinLiveDownloader(config)

        self.assertIsInstance(downloader.database, RecordingDatabase)
        self.assertEqual(database_connections, [{
          "host": config["database"]["host"],
          "user": config["database"]["username"],
          "passwd": config["database"]["password"],
          "database": config["database"]["name"],
        }])
        self.assertEqual(
          downloader.API.get_config_dict_attr("$.LIVE_INFO_ROOM_ID"),
          config["platform"]["douyin"]["api"]["LIVE_INFO_ROOM_ID"],
        )
        self.assertEqual(
          downloader.header.to_dict(),
          config["platform"]["douyin"]["headers"],
        )
        self.assertEqual(
          downloader.login.to_dict(),
          config["platform"]["douyin"]["login"],
        )
        self.assertFalse(save_path.exists())
    finally:
      module.DouyinShareUrlTable = original_database

  def test_live_construction_has_no_file_url_list(self):
    module = importlib.import_module(
      "backend.src.platform.douyin.douyin_live_downloader"
    )

    downloader = module.DouyinLiveDownloader(unified_config())

    self.assertFalse(hasattr(downloader, "url_list"))

  def test_conf_ini_remains_available_as_test_input(self):
    parser = configparser.ConfigParser()
    parser.read(PROJECT_ROOT / "config" / "douyin" / "conf.ini")
    urls = [value for _key, value in parser.items("live")]

    self.assertTrue(urls)

  def test_lazy_downloader_is_constructed_once_for_concurrent_callers(self):
    module = importlib.import_module(
      "backend.src.platform.douyin.douyin_live_downloader"
    )
    original_downloader_class = module.DouyinLiveDownloader
    original_downloader = module.downloader
    caller_count = 8
    start = Barrier(caller_count)
    count_lock = Lock()
    construction_count = 0
    instances = []

    class SlowDownloader:
      def __init__(self):
        nonlocal construction_count
        with count_lock:
          construction_count += 1
        sleep(0.05)

    def get_downloader():
      start.wait()
      instances.append(module.get_live_downloader())

    module.DouyinLiveDownloader = SlowDownloader
    module.downloader = None
    try:
      callers = [Thread(target=get_downloader) for _ in range(caller_count)]
      for caller in callers:
        caller.start()
      for caller in callers:
        caller.join(timeout=1)

      self.assertTrue(all(not caller.is_alive() for caller in callers))
      self.assertEqual(construction_count, 1)
      self.assertEqual(len({id(instance) for instance in instances}), 1)
    finally:
      module.DouyinLiveDownloader = original_downloader_class
      module.downloader = original_downloader

  def test_database_failure_does_not_block_live_downloader_construction(self):
    module = importlib.import_module(
      "backend.src.platform.douyin.douyin_live_downloader"
    )
    config = load_yml(CONFIG_EXAMPLE_PATH)
    config["database"]["enable"] = True
    config["download"]["test_mode"] = False
    original_database = module.DouyinShareUrlTable

    def fail_database(*args, **kwargs):
      raise RuntimeError("database unavailable")

    module.DouyinShareUrlTable = fail_database
    try:
      downloader = module.DouyinLiveDownloader(config)
    finally:
      module.DouyinShareUrlTable = original_database

    self.assertIsNone(downloader.database)


if __name__ == "__main__":
  unittest.main()
