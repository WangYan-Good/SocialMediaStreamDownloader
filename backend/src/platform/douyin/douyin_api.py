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
  def dump_config(self):
    super().dump_config()
    get_logger().info("Douyin API configuration:")
    for k,v in self.__api.items():
      get_logger().info("\t{}: {}".format(k,v))
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
      get_logger().error("Douyin API get config attr failed: {}".format(e))
      raise e
    return value
