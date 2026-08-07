##>> test
import os
import sys
sys.path.append(os.getcwd())
##<< test

##<<Base>>
import os
import sys
import threading
from copy import deepcopy
from pathlib import Path

##<<Extension>>

##<<Third-part>>
from backend.src.library.baselib     import load_yml

##
## config file path
##
CONFIG_PATH = Path(__file__).resolve().parents[3] / "config" / "config.yml"

REQUIRED_TOP_LEVEL_SECTIONS = (
  "database", "download", "log", "server", "migrate", "platform",
)
REQUIRED_DOUYIN_SECTIONS = (
  "download", "api", "headers", "login", "post", "live",
)


def _require_mapping(source: dict, key: str, path: str) -> dict:
  value = source.get(key)
  if not isinstance(value, dict):
    raise ValueError(f"{path} must be a mapping")
  return value

##
## Defination sbstract class
##
class BaseConfig():
##
## >>============================= attribute =============================>>
##
  ##
  ## configuration dict
  ##
  __config = dict()

  ##
  ## singleton lock
  ##
  __instance_lock = threading.Lock()

  ##
  ## identify whether the instance is initialized
  ##
  __initialized = False

##
## >>============================= private method =============================>>
##
  ##
  ## singleton pattern
  ##
  def __new__(cls, *args, **kwargs):
    with cls.__instance_lock:
      if not hasattr(cls, "_instance"):
        cls._instance = super().__new__(cls)
    return cls._instance
  
  ##
  ## initialize base config
  ##
  def __init__(self):
    '''
    Load the YAML configuration once for the process-wide singleton.
    '''
    if self.__initialized:
      return
    with self.__instance_lock:
      if self.__initialized:
        return
      try:

        ##
        ## load config from file
        ##
        self.__init_config()

        ##
        ## flag the instance is initialized
        ##
        self.__initialized = True
      except Exception as e:
        ##
        ## logger still cannot be used at this time.
        ##
        raise e

  def __init_config(self):
    '''
    Load the active config.
    '''
    try:
      config = load_yml(CONFIG_PATH)
      if not isinstance(config, dict):
        raise ValueError("Config root must be a mapping")
      self.__validate_config(config)
      self.__config = config
    except Exception as e:
      raise RuntimeError(f"Failed to load config file '{CONFIG_PATH}': {str(e)}") from e

  ##
  ## validate required configuration mappings
  ##
  def __validate_config(self, config: dict) -> None:
    for section in REQUIRED_TOP_LEVEL_SECTIONS:
      _require_mapping(config, section, f"$.{section}")
    platform = _require_mapping(config, "platform", "$.platform")
    douyin = _require_mapping(platform, "douyin", "$.platform.douyin")
    for section in REQUIRED_DOUYIN_SECTIONS:
      _require_mapping(douyin, section, f"$.platform.douyin.{section}")

  ##
  ## get config dict
  ##
  def get_config(self):
    return deepcopy(self.__config)
