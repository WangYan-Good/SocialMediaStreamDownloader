from copy import deepcopy

from backend.src.library.baselib import get_dict_attr, output_dict, set_dict_attr
from backend.src.library.configlib import load_config
from backend.src.platform.douyin.verify_fp_manager import VerifyFpManager as VFM


class DouyinLiveConfig:
  """Live-domain view of the process-wide unified configuration."""

  def __init__(self, config: dict = None):
    source = load_config() if config is None else config
    if not isinstance(source, dict):
      raise ValueError("Unified config root must be a mapping")

    self.__config = deepcopy(source)
    self._require_mapping("$.database")
    self._require_mapping("$.download")
    self._require_mapping("$.server")
    self._require_mapping("$.platform.douyin")
    self._require_mapping("$.platform.douyin.api")
    self._require_mapping("$.platform.douyin.headers")
    self._require_mapping("$.platform.douyin.login")
    self._require_mapping("$.platform.douyin.live")

  def _require_mapping(self, attr: str) -> dict:
    value = get_dict_attr(self.__config, attr)
    if not isinstance(value, dict):
      raise ValueError("Unified config section '{}' must be a mapping".format(attr))
    return value

  def to_dict(self) -> dict:
    return self.__config

  def dump_config(self):
    output_dict(self.__config)

  def get_config_dict_attr(self, attr: str = None):
    return get_dict_attr(self.__config, attr)

  def set_config_dict_attr(self, attr: str = None, value: any = None):
    set_dict_attr(self.__config, attr, value)

  def update_verifyFp(self):
    if self.get_config_dict_attr("$.download.user_login") is True:
      return self.get_config_dict_attr(
        "$.platform.douyin.live.params_no_login.verifyFp"
      )

    verify_fp = VFM.gen_verify_fp()
    self.set_config_dict_attr(
      "$.platform.douyin.live.params_no_login.verifyFp",
      verify_fp,
    )
    return verify_fp


if __name__ == "__main__":
  DouyinLiveConfig().dump_config()
