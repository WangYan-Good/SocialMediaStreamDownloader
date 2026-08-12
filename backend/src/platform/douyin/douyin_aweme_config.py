from copy import deepcopy

from backend.src.library.baselib import get_dict_attr, output_dict, set_dict_attr
from backend.src.library.configlib import load_config
from backend.src.platform.douyin.a_bogus import ABogus as AB
from backend.src.platform.douyin.verify_fp_manager import VerifyFpManager as VFM


##
## Browser-fingerprint parameters the web endpoints expect.  They live under
## $.platform.douyin.post because that is where the existing post settings are;
## the single-post request needs the same set.
##
_POST_PARAM_KEYS = (
  "device_platform",
  "aid",
  "channel",
  "pc_client_type",
  "version_code",
  "version_name",
  "update_version_code",
  "cookie_enabled",
  "screen_width",
  "screen_height",
  "browser_language",
  "browser_platform",
  "browser_name",
  "browser_version",
  "browser_online",
  "engine_name",
  "engine_version",
  "os_name",
  "os_version",
  "cpu_core_num",
  "device_memory",
  "platform",
  "downlink",
  "effective_type",
  "round_trip_time",
)


class DouyinAwemeConfig:
  """Single-post view of the process-wide unified configuration."""

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
    self._require_mapping("$.platform.douyin.post")
    self._require_mapping("$.platform.douyin.aweme")
    self._require_mapping("$.platform.douyin.aweme.media")
    self._require_mapping("$.platform.douyin.owner")

  def _require_mapping(self, attr: str) -> dict:
    value = get_dict_attr(self.__config, attr)
    if not isinstance(value, dict):
      raise ValueError(
        "Unified config section '{}' must be a mapping".format(attr)
      )
    return value

  def to_dict(self) -> dict:
    return self.__config

  def dump_config(self):
    output_dict(get_dict_attr(self.__config, "$.platform.douyin.aweme"))

  def get_config_dict_attr(self, attr: str = None):
    return get_dict_attr(self.__config, attr)

  def set_config_dict_attr(self, attr: str = None, value: any = None):
    set_dict_attr(self.__config, attr, value)

##
## >>============================= aweme settings =============================>>
##
  @property
  def login(self) -> bool:
    return self.get_config_dict_attr("$.download.user_login") is True

  @property
  def debug(self) -> bool:
    return self.get_config_dict_attr("$.server.debug_mode") is True

  @property
  def test_mode(self) -> bool:
    return self.get_config_dict_attr("$.download.test_mode") is True

  @property
  def max_timeout(self):
    return self.get_config_dict_attr("$.platform.douyin.aweme.max_timeout")

  @property
  def concurrency(self) -> int:
    return self.get_config_dict_attr("$.platform.douyin.aweme.concurrency")

  @property
  def html_fallback(self) -> bool:
    return self.get_config_dict_attr(
      "$.platform.douyin.aweme.html_fallback"
    ) is True

  @property
  def skip_downloaded(self) -> bool:
    return self.get_config_dict_attr(
      "$.platform.douyin.aweme.skip_downloaded"
    ) is True

  @property
  def video_quality(self) -> str:
    """Which encoding of a video to save; see the config comment."""
    value = self.get_config_dict_attr("$.platform.douyin.aweme.video_quality")
    return value if isinstance(value, str) and value.strip() else "highest"

  @property
  def media_switches(self) -> dict:
    return deepcopy(
      self.get_config_dict_attr("$.platform.douyin.aweme.media")
    )

##
## >>============================= owner settings =============================>>
##
  @property
  def owner_max_timeout(self):
    return self.get_config_dict_attr("$.platform.douyin.owner.max_timeout")

  @property
  def owner_page_size(self) -> int:
    return self.get_config_dict_attr("$.platform.douyin.owner.page_size")

  @property
  def owner_download_concurrency(self) -> int:
    """How many posts a batch download may fetch at once, process-wide.

    Clamped into ``[1, page_size]``.  Beyond one page's worth there is nothing
    to run - the walk yields posts a page at a time - and anything unusable
    means serial, which is the behaviour this setting was added to change
    rather than the one it risks.
    """
    cap = self._positive_int("$.platform.douyin.owner.page_size")
    if cap is None:
      return 1
    value = self._positive_int("$.platform.douyin.owner.download_concurrency")
    if value is None:
      return 1
    return min(value, cap)

  def _positive_int(self, attr: str):
    """Return the value at ``attr`` when it is a usable count, else ``None``.

    ``bool`` is rejected explicitly: it is a subclass of ``int``, so ``True``
    would otherwise read as the count 1 and ``False`` as 0.
    """
    value = self.get_config_dict_attr(attr)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
      return None
    return value

  @property
  def owner_max_pages(self) -> int:
    return self.get_config_dict_attr("$.platform.douyin.owner.max_pages")

  @property
  def payload_retention_seconds(self):
    return self.get_config_dict_attr(
      "$.platform.douyin.owner.payload_retention_seconds"
    )

  @property
  def job_retention_seconds(self):
    return self.get_config_dict_attr(
      "$.platform.douyin.owner.job_retention_seconds"
    )

  @property
  def save_path(self):
    return self.get_config_dict_attr("$.download.save_path")

  @property
  def folderize(self) -> bool:
    return self.get_config_dict_attr("$.download.folderize") is True

  @property
  def max_retry(self):
    return self.get_config_dict_attr("$.download.max_retry")

##
## >>============================= request params =============================>>
##
  def post_params(self) -> dict:
    """Return the browser-fingerprint parameters, without any signing."""
    post = self.get_config_dict_attr("$.platform.douyin.post") or {}
    return {
      key: post[key] for key in _POST_PARAM_KEYS if key in post
    }

  def update_verifyFp(self):
    """Refresh verifyFp/fp.  Only meaningful without a login cookie."""
    if self.login:
      return self.get_config_dict_attr("$.platform.douyin.post.verifyFp")
    verify_fp = VFM.gen_verify_fp()
    self.set_config_dict_attr("$.platform.douyin.post.verifyFp", verify_fp)
    self.set_config_dict_attr("$.platform.douyin.post.fp", verify_fp)
    return verify_fp

  def update_a_bogus(self, params: dict = None):
    """Sign ``params``.  Only meaningful without a login cookie."""
    if self.login:
      return self.get_config_dict_attr("$.platform.douyin.post.a_bogus")
    a_bogus = AB().get_value(params, "GET")
    self.set_config_dict_attr("$.platform.douyin.post.a_bogus", a_bogus)
    return a_bogus


if __name__ == "__main__":
  DouyinAwemeConfig().dump_config()
