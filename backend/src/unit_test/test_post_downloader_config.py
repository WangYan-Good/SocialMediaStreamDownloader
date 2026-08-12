import unittest
from unittest.mock import patch

from backend.src.platform.douyin import douyin_post_downloader as post_module
from backend.src.platform.douyin.douyin_api import DouyinApi
from backend.src.platform.douyin.douyin_aweme_config import DouyinAwemeConfig
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

  def test_rejects_a_non_mapping_unified_config_with_a_path_aware_error(self):
    with self.assertRaises(Exception) as raised:
      post_module.DouyinPostDownloader([])
    self.assertIsInstance(raised.exception, ValueError)
    self.assertRegex(str(raised.exception), r"Unified configuration.*mapping")

  def test_rejects_a_missing_required_post_leaf_with_its_full_path(self):
    config = self.post_config()
    del config["download"]["user_login"]

    with self.assertRaises(Exception) as raised:
      post_module.DouyinPostDownloader(config)
    self.assertIsInstance(raised.exception, ValueError)
    self.assertRegex(str(raised.exception), r"\$\.download\.user_login")

  def test_rejects_an_invalid_required_post_leaf_with_its_full_path(self):
    config = self.post_config()
    config["server"]["debug_mode"] = "false"

    with self.assertRaises(Exception) as raised:
      post_module.DouyinPostDownloader(config)
    self.assertIsInstance(raised.exception, ValueError)
    self.assertRegex(
      str(raised.exception), r"\$\.server\.debug_mode.*boolean"
    )

  def test_rejects_a_missing_selected_post_header_with_its_full_path(self):
    config = self.post_config()
    del config["platform"]["douyin"]["headers"]["post_info_no_login"]

    with self.assertRaises(Exception) as raised:
      post_module.DouyinPostDownloader(config)
    self.assertIsInstance(raised.exception, ValueError)
    self.assertRegex(
      str(raised.exception),
      r"\$\.platform\.douyin\.headers\.post_info_no_login",
    )

  def test_rejects_missing_post_dependency_sections_with_full_paths(self):
    for section in ("headers", "login", "api"):
      with self.subTest(section=section):
        config = self.post_config()
        del config["platform"]["douyin"][section]

        with self.assertRaises(Exception) as raised:
          post_module.DouyinPostDownloader(config)
        self.assertIsInstance(raised.exception, ValueError)
        self.assertIn(
          f"$.platform.douyin.{section}",
          str(raised.exception),
        )

  def test_runtime_updates_do_not_mutate_the_base_mapping(self):
    config = self.post_config()
    downloader = post_module.DouyinPostDownloader(config)
    downloader.config.update_post_share_url({"share_url": "https://example.test"})

    self.assertNotIn("share_url", config["platform"]["douyin"]["post"])
    self.assertEqual(
        downloader.config.to_dict()["platform"]["douyin"]["post"]["share_url"],
        "https://example.test")

  def test_run_accepts_a_web_token_without_network_in_test_mode(self):
    config = self.post_config()
    downloader = post_module.DouyinPostDownloader(config)
    original_request = post_module.request
    original_get = post_module.get

    def fail_network(*args, **kwargs):
      self.fail("test-mode Post run attempted a network request")

    post_module.request = fail_network
    post_module.get = fail_network
    try:
      result = downloader.run({
        "url": "https://www.douyin.com/user/test-sec-user",
      })
    finally:
      post_module.request = original_request
      post_module.get = original_get

    self.assertIsNone(result)
    self.assertEqual(downloader.config.share_url,
                     "https://www.douyin.com/user/test-sec-user")

  def test_short_link_test_mode_does_not_access_network_or_filesystem(self):
    config = self.post_config()
    config["download"]["save_response"] = True
    downloader = post_module.DouyinPostDownloader(config)
    share_url = "https://v.douyin.com/test-short-link/"

    def fail_external_access(*args, **kwargs):
      self.fail("test-mode Post run attempted network or filesystem access")

    with patch.object(post_module, "request", side_effect=fail_external_access), \
         patch.object(post_module, "get", side_effect=fail_external_access), \
         patch.object(post_module.os, "makedirs",
                      side_effect=fail_external_access), \
         patch("builtins.open", side_effect=fail_external_access):
      result = downloader.run({"url": share_url})

    self.assertIsNone(result)
    self.assertEqual(downloader.config.share_url, share_url)
    self.assertNotIn("share_url", config["platform"]["douyin"]["post"])


class OwnerDownloadConcurrencyTest(unittest.TestCase):
  """并行数必须落在 [1, page_size]，任何脏值都退回串行。

  串行是这个配置项要改变的行为，不是它应当引入的风险：读不懂的值宁可慢，
  也不要让一个手滑的配置把并发放大到不可控。
  """

  def concurrency_for(self, **owner_overrides):
    config = unified_config()
    config["platform"]["douyin"]["owner"].update(owner_overrides)
    return DouyinAwemeConfig(config).owner_download_concurrency

  def test_the_default_is_serial(self):
    config = unified_config()
    config["platform"]["douyin"]["owner"].pop("download_concurrency", None)

    self.assertEqual(DouyinAwemeConfig(config).owner_download_concurrency, 1)

  def test_a_configured_value_is_used(self):
    self.assertEqual(self.concurrency_for(download_concurrency=6), 6)

  def test_it_never_exceeds_one_page(self):
    ##
    ## 一次只翻一页，超出一页的并行没有作品可跑
    ##
    self.assertEqual(
      self.concurrency_for(page_size=18, download_concurrency=999), 18
    )

  def test_zero_and_negative_fall_back_to_serial(self):
    self.assertEqual(self.concurrency_for(download_concurrency=0), 1)
    self.assertEqual(self.concurrency_for(download_concurrency=-4), 1)

  def test_a_non_integer_falls_back_to_serial(self):
    self.assertEqual(self.concurrency_for(download_concurrency="8"), 1)
    self.assertEqual(self.concurrency_for(download_concurrency=2.5), 1)

  def test_a_boolean_is_not_an_integer_here(self):
    ##
    ## bool 是 int 的子类，不挡住会让 True 读成并行 1、False 读成 0
    ##
    self.assertEqual(self.concurrency_for(download_concurrency=True), 1)

  def test_an_unusable_page_size_forces_serial(self):
    self.assertEqual(
      self.concurrency_for(page_size=0, download_concurrency=8), 1
    )
