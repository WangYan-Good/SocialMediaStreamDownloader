##<<Test
import os
import sys
sys.path.append(os.getcwd())
##>>Test
##<<Extension>>
import yaml as yml

##<<Third-part>>
from pathlib import Path
from backend.src.base.api import Api
from backend.src.library.baselib import get_dict_attr


DEFAULT_API_CONFIG_PATH = "./config/douyin/api.yml"

class DouyinApi(Api):
##
## >>============================= attribute =============================>>
##
  __api = dict()
##
## >>============================= private method =============================>>
##
  def __init__(self, path: Path | str = None) -> None:
    if path is None:
      print("WARNING: invalid api config path, will use default api config")
      path = DEFAULT_API_CONFIG_PATH
    super().__init__(path)

    ##
    ## parse api path
    ##
    self.__parse_api(path=Path(path))

    ##
    ## transform dict to attribute
    ##
    self.__dict__.update(self.__api)

  def __parse_api(self, path: Path = None):
    if path is None:
      print("ERROR: invalid api config path")
      raise FileNotFoundError
    self.__api = yml.safe_load(path.read_text(encoding="utf-8"))
##
## >>============================= abstract method =============================>>
##
  def dump_config(self):
    super().dump_config()
    print("douyin API configuration:")
    for k,v in self.__api.items():
      print("\t{}: {}".format(k,v))
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
      print("ERROR: get douyin live config attr({}) failed".format(attr))
      raise e
    return value
if __name__ == "__main__":
  douyin_api = DouyinApi(DEFAULT_API_CONFIG_PATH)
  douyin_api.dump_config()