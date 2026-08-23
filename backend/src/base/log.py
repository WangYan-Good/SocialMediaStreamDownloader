##<<Test>>
import os
import sys
sys.path.append(os.getcwd())

##<<Base>>
from logging import Logger, FileHandler, StreamHandler, Formatter
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
import re
import threading

##
## >>============================= public defination =============================>>
##
DEFAULT_LOGGER_FORMATTER_STR = '[%(asctime)s]-[%(name)s]-[%(levelname)s]: %(message)s'
VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
class LoggerManager():
##
## >>============================= attribute =============================>>
##
  __default_logger          = None
  __default_console_handler = None
  __logger_queue            = dict()
  __instance_Lock           = threading.Lock()
  
  
  ##
  ## default logger attributes
  ##
  __DEFAULT_LOGGER_NAME          = "default"
  __DEFAULT_LOGGER_LEVEL         = "INFO"
  __DEFAULT_LOG_FILE_DIR         = Path(".")
  __DEFAULT_LOG_FILE_PATH        = None
  __DEFAULT_LOGGER_FORMATTER_STR = DEFAULT_LOGGER_FORMATTER_STR

##
## >>============================= private method =============================>>
##
  ##
  ## singleton pattern
  ##
  def __new__(cls, *args, **kwargs):
    with cls.__instance_Lock:
      if not hasattr(cls, '_instance'):
        cls._instance = super().__new__(cls)
    return cls._instance

  @classmethod
  def get_instance(cls):
    ##
    ## return singleton instance
    ##
    instance = getattr(cls, "_instance", None)
    if instance is not None and getattr(instance, "_LoggerManager__initialized", False):
      return instance
    ##
    ## create one if not exist instance
    ##
    return cls()

  ##
  ## initialize the logger manager
  ##
  def __init__(self, config: dict = None) -> None:
    ##
    ## check if the instance is initialize
    ## _LoggerManager__initialized default as false when created
    ## it will be set true once initialized
    ##
    if self._LoggerManager__initialized:
      return
    with self.__instance_Lock:
      ##
      ## in case the instance has been initialized
      ## if exist an other thread and completed initialization process
      ##
      if self._LoggerManager__initialized:
        return
      
      ##
      ## load logger config
      ##
      log_config = self.__load_log_config(config)
      
      ##
      ## configure logger with log_config
      ##
      self.__configure(log_config)
      self.__logger_queue = {}

      try:
        ##
        ## make default logger work
        ##
        self.__init_default_logger()
      except Exception:
        ##
        ## clean once initialize failed
        ##
        self.__cleanup_failed_initialization()
        raise
      self._LoggerManager__initialized = True

  def __cleanup_failed_initialization(self) -> None:
    if self.__default_logger is not None:
      for handler in self.__default_logger.handlers[:]:
        ##
        ## remove and close logger handler
        ##
        self.__default_logger.removeHandler(handler)
        handler.close()
    self.__default_logger            = None
    self.__default_console_handler   = None
    self.__logger_queue              = {}
    self._LoggerManager__initialized = False

  ##
  ## load config
  ## TODO: handle config source
  ##
  def __load_log_config(self, config):
    if config is None:
      from backend.src.base.config import BaseConfig
      config = BaseConfig().get_config().get("log")
    if not isinstance(config, dict):
      raise ValueError("Unified log config must be a mapping")
    return config

  def __configure(self, config: dict) -> None:
    ##
    ## logger field
    ##
    log_enable    = config.get("log_enable")
    log_level     = config.get("log_level")
    log_save      = config.get("log_save")
    log_file_path = config.get("log_file_path")

    ##
    ## check and verify if is valid
    ##
    if type(log_enable) is not bool:
      raise ValueError("log_enable must be a boolean")
    if not isinstance(log_level, str) or log_level not in VALID_LOG_LEVELS:
      raise ValueError("log_level must be a standard logging level")
    if type(log_save) is not bool:
      raise ValueError("log_save must be a boolean")
    if log_save:
      if not isinstance(log_file_path, str) or not log_file_path.strip():
        raise ValueError("log_file_path must be a non-empty string")
      normalized_path = log_file_path.strip()
      file_name = re.split(r"[\\/]", normalized_path)[-1]
      if (
        not file_name
        or file_name in (".", "..")
        or Path(normalized_path).is_dir()
      ):
        raise ValueError("log_file_path must include a file name")

    ##
    ## set valid value from config
    ##
    self.__log_enable            = log_enable
    self.__log_save              = log_save
    self.__DEFAULT_LOGGER_LEVEL  = log_level
    self.__DEFAULT_LOG_FILE_PATH = (
      Path(log_file_path) if isinstance(log_file_path, str) and log_file_path.strip()
      else None
    )
    self.__DEFAULT_LOG_FILE_DIR  = (
      self.__DEFAULT_LOG_FILE_PATH.parent
      if self.__DEFAULT_LOG_FILE_PATH is not None
      else Path(".")
    )

    if self.__log_save:
      ##
      ## create folder path
      ##
      self.__DEFAULT_LOG_FILE_DIR.mkdir(parents=True, exist_ok=True)

  ##
  ## initialize the default logger
  ##
  def __init_default_logger(self) -> None:
    self.__default_logger = Logger(name=self.__DEFAULT_LOGGER_NAME, level=self.__DEFAULT_LOGGER_LEVEL)
    self.__default_logger.disabled = not self.__log_enable

    ##
    ## set console handler for the default logger
    ##
    self.__default_console_handler = StreamHandler()
    self.__default_console_handler.setLevel(self.__DEFAULT_LOGGER_LEVEL)
    self.__default_console_handler.setFormatter(Formatter(self.__DEFAULT_LOGGER_FORMATTER_STR))
    self.__default_logger.addHandler(self.__default_console_handler)
    
    ##
    ## initialize the default logger with file handler
    ##
    if self.__log_save:
      file_handler = TimedRotatingFileHandler(
        filename=str(self.__DEFAULT_LOG_FILE_PATH),
        when="midnight",
        interval=1,
        encoding="utf-8",
      )
      file_handler.setLevel(self.__DEFAULT_LOGGER_LEVEL)
      file_handler.setFormatter(Formatter(self.__DEFAULT_LOGGER_FORMATTER_STR))
      self.__default_logger.addHandler(file_handler)
    
    ##
    ## add the default logger to the logger queue
    ##
    self.__logger_queue[self.__DEFAULT_LOGGER_NAME] = self.__default_logger

##
## >>============================= abstract method =============================>>
##

##
## >>============================= sub class method =============================>>
##
  ##
  ## get logger by name
  ##
  def get_logger(self, name:str="default") -> Logger:
    if name is None:
      raise Exception("Logger name cannot be None.")
    
    ##
    ## check if the logger is registered
    ##
    if self.__logger_queue.get(name) is not None:
      return self.__logger_queue[name]
    else:
      ##
      ## if the logger is not registered, raise an exception
      ##
      raise Exception(f"Logger with name {name} is not registered. Please register the logger first.")

  ##
  ## register a logger for module-level logging
  ##
  def register_logger(self, name:str, level:str) -> Logger:
    ##
    ## check if the parameters are valid
    ##
    if name is None:
      raise Exception("Logger name cannot be None.")
    
    ##
    ## register a new logger
    ##
    if self.__logger_queue.get(name) is None:
      ##
      ## check if the level is valid
      ##
      if level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        raise Exception(f"Invalid logger level: {level}. Valid levels are: DEBUG, INFO, WARNING, ERROR, CRITICAL.")
      
      ##
      ## create a new logger and add it to the logger queue
      ##
      self.__logger_queue[name] = Logger(name=name, level=level)
      self.__logger_queue[name].disabled = not self.__log_enable

      ##
      ## return the logger
      ##
      return self.__logger_queue[name]
    else:
      ##
      ## the logger should not be registered again
      ##
      raise Exception(f"Logger with name {name} is already registered.")

  ##
  ## set logger with file handler
  ##
  def set_logger_file_handler(self, name:str, file:str, format:str=None, level:str="DEBUG") -> None:
    try:
      logger = self.get_logger(name)
      file_name = re.search(r"[^\\/]+$", file)
      file_handler = FileHandler(f"{self.__DEFAULT_LOG_FILE_DIR}/{file_name[0]}")
      file_handler.setLevel(level)
      if format is not None:
        file_handler.setFormatter(Formatter(format))
      logger.addHandler(file_handler)
    except Exception as e:
      raise Exception(f"Failed to set file handler for logger {name}: {e}")

  ##
  ## set logger with console handler
  ##
  def set_logger_console_handler(self, name:str, format:str=None, level:str="DEBUG") -> None:
    try:
      logger = self.get_logger(name)
      console_handler = StreamHandler()
      console_handler.setLevel(level)
      if format is not None:
        console_handler.setFormatter(Formatter(format))        
      logger.addHandler(console_handler)
    except Exception as e:
      raise Exception(f"Failed to set console handler for logger {name}: {e}")

##
## >>================================ public method ===============================>>
##
