##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

##<<Third-Part>>
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
def load_config():
  try:
    return BaseConfig().get_config()
  except Exception as e:
    ##
    ## Handle exceptions during configuration initialization
    ##
    get_logger().error(f"Failed to initialize configuration: {e}")
    raise e

def get_config(config_name:str=None):
  '''
  Get the configuration value by name
  '''
  try:
    config = BaseConfig()
    if config_name:
      return getattr(config.get_config(), config_name, None)
    else:
      raise ValueError("config_name cannot be None")
  except Exception as e:
    ##
    ## Handle exceptions during getting configuration
    ##
    get_logger().error(f"Error getting configuration: {e}")
    return None

def set_config(config_name:str, config_value):
  '''
  Set the configuration value by name
  '''
  try:
    config = BaseConfig()
    config.update_config(f"$.{config_name}", config_value)
  except Exception as e:
    ##
    ## Handle exceptions during setting configuration
    ##
    get_logger().error(f"Error setting configuration: {e}")
    raise e
