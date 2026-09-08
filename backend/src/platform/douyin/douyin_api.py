##<<Test
import os
import sys
sys.path.append(os.getcwd())
##>>Test
##<<Extension>>
from copy import deepcopy

##<<Third-part>>
from backend.src.base.api        import Api
from backend.src.library.baselib import get_dict_attr
from backend.src.library.configlib import get_config
from backend.src.library.loglib  import get_logger
from backend.src.library.safe_diagnostics import config_diagnostic


class DouyinApi(Api):
##
## >>============================= attribute =============================>>
##
  __api = dict()
##
## >>============================= private method =============================>>
##
  def __init__(self, config: dict = None) -> None:
    source = get_config("$.platform.douyin.api") if config is None else config
    if not isinstance(source, dict):
      raise ValueError("$.platform.douyin.api must be a mapping")
    super().__init__(source)
    self.__api = deepcopy(source)

    ##
    ## transform dict to attribute
    ##
    self.__dict__.update(self.__api)

##
## >>============================= abstract method =============================>>
##
  ##
  ## The endpoint table, counted rather than listed.
  ##
  ## Every value here is a url this deployment will sign a request against, and
  ## a listing of them in a shipped log is a map of what this build talks to.
  ##
  def dump_config(self):
    super().dump_config()
    get_logger().info(
      config_diagnostic("config_dumped", section="api", total=len(self.__api))
    )
##
## >>============================= sub class method =============================>>
##
  ##
  ## get config dict attr
  ##
  def get_config_dict_attr(self, attr: str = None):
    value = None
    try:
      value = get_dict_attr(self.__api, attr)
    except Exception as e:
      ##
      ## The message of a lookup failure quotes the path that was asked for and
      ## frequently the mapping it was asked of.
      ##
      get_logger().error(
        config_diagnostic(
          "config_lookup_failed", section="api", error=e, state=False
        )
      )
      raise e
    return value
