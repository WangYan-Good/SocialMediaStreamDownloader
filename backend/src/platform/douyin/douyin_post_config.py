from copy import deepcopy
from pathlib import Path

from backend.src.library.baselib import get_dict_attr, has_dict_attr
from backend.src.library.configlib import load_config
from backend.src.library.loglib import get_logger
from backend.src.library.safe_diagnostics import config_diagnostic
from backend.src.platform.douyin.a_bogus import ABogus as AB
from backend.src.platform.douyin.verify_fp_manager import VerifyFpManager as VFM


PROJECT_ROOT = Path(__file__).resolve().parents[4]


class DouyinPostConfig:
  def __init__(self, config: dict = None) -> None:
    source = load_config() if config is None else config
    if not isinstance(source, dict):
      raise ValueError("Unified configuration must be a mapping")
    self.__config = deepcopy(source)
    download = self.__require("$.download")
    self.__require("$.server")
    self.__require("$.platform")
    self.__require("$.platform.douyin")
    douyin_download = self.__require("$.platform.douyin.download")
    post = self.__require("$.platform.douyin.post")
    self.__require("$.platform.douyin.headers")
    self.__require("$.platform.douyin.login")
    self.__require("$.platform.douyin.api")
    self.login = self.__require_boolean("$.download.user_login")
    self.debug = self.__require_boolean("$.server.debug_mode")
    selected_header = "post_info" if self.login else "post_info_no_login"
    self.__require(f"$.platform.douyin.headers.{selected_header}")
    self.__dict__.update(download)
    self.__dict__.update(douyin_download)
    self.__dict__.update(post)
    self.stream_platform = "douyin"
    self.build_path = str(PROJECT_ROOT / "config" / "build")
    self.share_url = ""
    self.nickname = ""

  def __require(self, path: str) -> dict:
    value = get_dict_attr(self.__config, path)
    if not isinstance(value, dict):
      raise ValueError(f"{path} must be a mapping")
    return value

  def __require_boolean(self, path: str) -> bool:
    if not has_dict_attr(self.__config, path):
      raise ValueError(f"{path} is required")
    value = get_dict_attr(self.__config, path)
    if type(value) is not bool:
      raise ValueError(f"{path} must be a boolean")
    return value

  def __post_config(self) -> dict:
    return get_dict_attr(self.__config, "$.platform.douyin.post")

  def update_verifyFp(self):
    if self.login is not True:
      self.verifyFp = VFM.gen_verify_fp()
      self.__post_config()["verifyFp"] = self.verifyFp

  def update_fp(self):
    if self.login is not True:
      self.fp = self.verifyFp
      self.__post_config()["fp"] = self.fp

  def update_a_bogus(self, params: dict = None):
    if self.login is not True:
      self.a_bogus = AB().get_value(params, "GET")
      self.__post_config()["a_bogus"] = self.a_bogus

  def update_count(self, count: int = 0):
    if count == 0:
      raise ValueError
    self.count = count
    self.__post_config()["count"] = self.count

  def update_post_share_url(self, param: dict = None):
    if param is None:
      get_logger().error("invalid parameter!")
      raise ValueError
    self.share_url = param.get("share_url", "")
    self.__post_config()["share_url"] = self.share_url

  def to_dict(self) -> dict:
    return deepcopy(self.__config)

  ##
  ## Deliberately dumps nothing.
  ##
  ## This section holds ``verifyFp``, ``fp``, ``msToken`` and ``a_bogus`` - the
  ## values that make a signed request accepted - beside the account's
  ## ``sec_user_id`` and the share url it was reached by.  There is no safe
  ## rendering of that, so there is no rendering of it.
  ##
  def dump_config(self):
    section = self.__post_config()
    get_logger().info(
      config_diagnostic(
        "config_dumped",
        section="post",
        total=len(section) if isinstance(section, dict) else 0,
      )
    )
