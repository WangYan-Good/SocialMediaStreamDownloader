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
