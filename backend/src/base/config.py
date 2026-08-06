##>> test
import os
import sys
sys.path.append(os.getcwd())
##<< test

##<<Base>>
import os
import sys
import threading
from pathlib import Path

##<<Extension>>

##<<Third-part>>
from backend.src.library.baselib     import load_yml, set_dict_attr, has_dict_attr

##
## config file path
##
CONFIG_PATH = Path(__file__).resolve().parents[3] / "config" / "config.yml"

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
      self.__config = config
    except Exception as e:
      raise RuntimeError(f"Failed to load config file '{CONFIG_PATH}': {str(e)}") from e

  ##
  ## update config value by field path
  ##
  def update_config(self, field:str, value:any):
    pass

  ##
  ## get config dict
  ##
  def get_config(self):
    return self.__config
