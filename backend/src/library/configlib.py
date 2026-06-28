##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

##<<Third-Part>>
from backend.src.library.baselib  import get_dict_attr, set_dict_attr
from backend.src.library.loglib   import get_logger
from backend.src.base.config      import BaseConfig

ENV_SMSD_DB_HOST     = "SMSD_DB_HOST"
ENV_SMSD_DB_PORT     = "SMSD_DB_PORT"
ENV_SMSD_DB_USER     = "SMSD_DB_USER"
ENV_SMSD_DB_PASSWORD = "SMSD_DB_PASSWORD"
ENV_SMSD_DB_NAME     = "SMSD_DB_NAME"

# ============================================
# initialize system base configuration
# ============================================
def init_base_config():
  '''  
  BaseConfig: singleton class, responsible for loading and managing base configuration
              base configuration includes:
              - DB configuration, it only configured through by environment variables
                else system could not connect to the database, so it is critical for the system to work
              - Server configuration
              - Logging configuration
              - Other global configuration
  '''
  try:
    BaseConfig()
  except Exception as e:
    ##
    ## Handle exceptions during configuration initialization
    ##
    get_logger().error(f"Error initializing configuration: {e}")
    raise e

def get_base_config(config_name:str=None):
  '''
  Get the configuration value by name
  '''
  try:
    config = BaseConfig()
    if config_name:
      return get_dict_attr(config.__config, config_name)
    else:
      raise ValueError("config_name cannot be None")
  except Exception as e:
    ##
    ## Handle exceptions during getting configuration
    ##
    get_logger().error(f"Error getting configuration: {e}")
    return None

def set_base_config(config_name:str, config_value):
  '''
  Set the configuration value by name
  '''
  try:
    config = BaseConfig()
    set_dict_attr(config.__config, config_name, config_value)
  except Exception as e:
    ##
    ## Handle exceptions during setting configuration
    ##
    get_logger().error(f"Error setting configuration: {e}")
    raise e

def dump_base_config():
  '''
  Dump the current configuration to console
  '''
  try:
    config = BaseConfig()
    config.dump_config()
  except Exception as e:
    ##
    ## Handle exceptions during dumping configuration
    ##
    get_logger().error(f"Error dumping configuration: {e}")
    raise e