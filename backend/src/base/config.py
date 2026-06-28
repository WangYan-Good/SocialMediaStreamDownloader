##>> test
import os
import sys
sys.path.append(os.getcwd())
##<< test

##<<Base>>
import os
import sys
import threading

##<<Extension>>

##<<Third-part>>
from backend.src.library.baselib     import set_dict_attr, has_dict_attr

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
  __default_config = dict()
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
    Initialize base configuration, the config will be loaded in the following order:
    load config from database, if failed, load config from default config.
    '''
    if self.__initialized:
      return
    try:      
      ##
      ## load default config
      ##
      self.__init_default_config()
      
      ##
      ## load config from database, if failed, load config from default config
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

  def __init_default_config(self):
    '''
    Default config is the bootstrap config for the process.
    It is NOT the final source of truth. 
    The final config should be loaded from the database for non-first startup.
    For those cases the default config will be used as a fallback:
      1. first startup
      2. database connection failure
    '''
    self.__default_config = {
      "ENVIRONMENT": os.getenv("ENVIRONMENT"),

      ##
      ## Database bootstrap config. These values let the app connect to the
      ## config database and load the main config on non-first startup.
      ##
      "SMSD_DB_ENABLE": os.getenv("SMSD_DB_ENABLE", None),
      "SMSD_DB_HOST": os.getenv("SMSD_DB_HOST", None),
      "SMSD_DB_PORT": int(os.getenv("SMSD_DB_PORT", None)),
      "SMSD_DB_NAME": os.getenv("SMSD_DB_NAME", None),
      "SMSD_DB_USER": os.getenv("SMSD_DB_USER", None),
      "SMSD_DB_PASSWORD": os.getenv("SMSD_DB_PASSWORD", None),

      ##
      ## Download defaults. These are fallback values only; user/main config in
      ## the database should override them after initialization.
      ## TODO: move these to user config after the migration is done, 
      ##       since they are user-level preferences rather than system-level defaults.
      ##
      "DOWNLOAD_SAVE_PATH": os.getenv("DOWNLOAD_SAVE_PATH"),
      "DOWNLOAD_MAX_THREADS": os.getenv("DOWNLOAD_MAX_THREADS"),

      ##
      ## Server and logger bootstrap config. These keep the service operable
      ## before the database-backed main config is available.
      ##
      "SERVER_HOST": os.getenv("SERVER_HOST"),
      "SERVER_PORT": os.getenv("SERVER_PORT"),
      
      ##
      ## Logger debug config
      ##
      "FLASK_DEBUG": os.getenv("FLASK_DEBUG"),
      "LOG_LEVEL": os.getenv("LOG_LEVEL"),
      "LOG_FILE_PATH": os.getenv("LOG_FILE_PATH")
    }

    ##
    ## Default config is also the active config until a later database-backed
    ## load succeeds. Expose every config key as an instance attribute to keep
    ## compatibility with the older BaseConfig access pattern.
    ##
    self.__config = self.__default_config.copy()
    self.__dict__.update(self.__config)

  def __init_config(self):
    '''
    Initialize main config from database,
    if failed, it will use default config.
    '''
    ##
    ## check database config from default config
    ##
    smsd_db_host = self.__default_config.get("SMSD_DB_HOST")
    smsd_db_port = self.__default_config.get("SMSD_DB_PORT")
    smsd_db_name = self.__default_config.get("SMSD_DB_NAME")
    smsd_db_user = self.__default_config.get("SMSD_DB_USER")
    smsd_db_password = self.__default_config.get("SMSD_DB_PASSWORD")
    
    self.__config = __get_base_config_from_db(smsd_db_host, smsd_db_port, smsd_db_name, smsd_db_user, smsd_db_password)
    
    ##
    ## Internal function to fetch base config from database
    ##
    def __get_base_config_from_db(host:str=None, port:int=None, name:str=None, user:str=None, password:str=None):
      try:
        if host is None or port is None or name is None or user is None or password is None:
          raise ValueError("Database configuration is incomplete")
        ##
        ## Fetch the base config from the database using the provided credentials
        ##
        pass
      except Exception as e:
        raise e

  def update_config(self, field:str, value:any):
    '''
    Update the active config with new values, typically loaded from the database.
    This will override the default/bootstrap config values with the new ones.
    '''
    if has_dict_attr(self.__config, field) is False:
      raise ValueError("field cannot be None")
    set_dict_attr(self.__config, field, value)
    self.__dict__.update(self.__config)
    
    ##
    ## TODO
    ## write back updated config to database
    ##
