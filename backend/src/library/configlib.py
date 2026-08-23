##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

##<<Third-Part>>
from backend.src.library.loglib   import get_logger
from backend.src.base.config      import BaseConfig
from backend.src.library.baselib import get_dict_attr, has_dict_attr

# ============================================
# initialize system base configuration
# ============================================
def load_config():
  try:
    ##
    ## base config as singlton and save system configuration
    ##
    return BaseConfig().get_config()
  except Exception as e:
    ##
    ## Handle exceptions during configuration initialization
    ##
    get_logger().error(f"Failed to initialize configuration: {e}")
    raise e

# ==================================================
# config path "$." is prefix for configuration path
#
# for example, "$.database.host" refers to the 
# "host" attribute under the "database" section 
# in the configuration.
# ==================================================
def get_config(path: str):
  ##
  ## check prefix
  ##
  if not isinstance(path, str) or not path.startswith("$."):
    raise ValueError("config path must start with '$.'")
  
  ##
  ## load configuration
  ##
  config = load_config()
  
  ##
  ## check if it exist of the specific field
  ##
  if not has_dict_attr(config, path):
    raise KeyError(f"Configuration path not found: {path}")
  
  ##
  ## execute action
  ##
  return get_dict_attr(config, path)
