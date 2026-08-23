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
from backend.src.library.config_contract import validate_config_contract

##
## config file path
##
CONFIG_PATH = Path(__file__).resolve().parents[3] / "config" / "config.yml"
CONFIG_EXAMPLE_PATH = Path(__file__).resolve().parents[3] / "docs" / "design" / "config.yml.example"

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
    Load the active config after checking it against the canonical example.
    '''
    try:
      ##
      ## load config from file
      ##
      config = load_yml(CONFIG_PATH)
      
      ##
      ## load template config file
      ##
      config_example = load_yml(CONFIG_EXAMPLE_PATH)
      
      ##
      ## compare config & template field
      ## if mismatch will raise exception
      ##
      validate_config_contract(config_example, config)
      self.__config = config
    except Exception as e:
      raise RuntimeError(f"Failed to load config file '{CONFIG_PATH}': {str(e)}") from e

  ##
  ## get config dict, read only
  ##
  def get_config(self):
    return deepcopy(self.__config)
