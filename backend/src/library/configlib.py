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
    return BaseConfig().get_config()
  except Exception as e:
    ##
    ## Handle exceptions during configuration initialization
    ##
    get_logger().error(f"Failed to initialize configuration: {e}")
    raise e

def get_config(path: str):
  if not isinstance(path, str) or not path.startswith("$."):
    raise ValueError("config path must start with '$.'")
  config = load_config()
  if not has_dict_attr(config, path):
    raise KeyError(f"Configuration path not found: {path}")
  return get_dict_attr(config, path)
