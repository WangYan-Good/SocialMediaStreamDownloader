##<<Test>>
import os
import sys
sys.path.append(os.getcwd())

##<<Base>>
from logging import Logger, FileHandler, StreamHandler, Formatter
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
import re

##<<Existension>>
import yaml as yml

##<<Third-part>>
from backend.src.base.default import DEFAULT_BASE_CONFIG_PATH

##
## >>============================= public defination =============================>>
##
DEFAULT_LOGGER_FORMATTER_STR = '[%(asctime)s]-[%(name)s]-[%(levelname)s]: %(message)s'
class LoggerManager():

##
## >>============================= attribute =============================>>
##
  __default_logger          = None
  __default_console_handler = None
  __logger_queue            = dict()
  
  
  ##
  ## default logger attributes
  ##
  __DEFAULT_LOGGER_NAME          = "default"
  __DEFAULT_LOGGER_LEVEL         = "INFO"
  __DEFAULT_LOG_FILE_DIR         = str()
  __DEFAULT_LOGGER_FORMATTER_STR = DEFAULT_LOGGER_FORMATTER_STR

##
## >>============================= private method =============================>>
##
  ##
  ## singleton pattern
  ##
  def __new__(cls, *args, **kwargs):
    if not hasattr(cls, 'instance'):
      cls.instance = super().__new__(cls)
    return cls.instance

  ##
  ## init the logger manager
  ##
  def __init__(self) -> None:
    ##
    ## prevent re-initialization for singleton pattern
    ##
    if hasattr(self, '_initialized') and self._initialized:
      return

    try:
      ##
      ## initialize the log file directory
      ##
      self.__init_log_file_handle_dir()
      
      ##
      ## initialize the default logger
      ##
      self.__init_default_logger()

      ##
      ## mark as initialized
      ##
      self._initialized = True
    except Exception as e:
      raise e
    return

  ##
  ## initialize the log directory
  ##
  def __init_log_file_handle_dir(self) -> None:
    try:
      ##
      ## load default config from file
      ##
      with open(DEFAULT_BASE_CONFIG_PATH, 'r') as file:
        config = yml.safe_load(file)
        
        ##
        ## get the log path from the config file
        ##
        self.__DEFAULT_LOG_FILE_DIR =  config.get("log_path", None)
        if self.__DEFAULT_LOG_FILE_DIR is None:
          raise Exception("Log path is not defined in the base config file.")
        
        ##
        ## set create the log directory if it does not exist
        ##
        log_dir = Path(self.__DEFAULT_LOG_FILE_DIR)
        if not log_dir.exists():
          log_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
      raise Exception(f"Failed to initialize log file directory: {e}")

  ##
  ## initialize the default logger
  ##
  def __init_default_logger(self) -> None:
    self.__default_logger = Logger(name=self.__DEFAULT_LOGGER_NAME, level=self.__DEFAULT_LOGGER_LEVEL)

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
    file_handler = TimedRotatingFileHandler(
      filename=os.path.join(self.__DEFAULT_LOG_FILE_DIR, "social_media_stream_downloader"),
      when='midnight',
      interval=1,
      encoding="utf-8"
    )
    file_handler.suffix="-%Y-%m-%d.log"
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

##
## register a logger for module-level logging
##
def register_logger(name:str, level:str) -> Logger:
  return LoggerManager().register_logger(name, level)

##
## get logger by name
##
def get_logger(name:str="default") -> Logger:
  return LoggerManager().get_logger(name)
  
##
## set logger with file handler
##
def set_logger_file_handler(name:str, file_path:str, format:str=None, level:str="DEBUG") -> None:
  LoggerManager().set_logger_file_handler(name, file_path, format, level)

##
## set logger with console handler
##
def set_logger_console_handler(name:str, format:str=None, level:str="DEBUG") -> None:
  LoggerManager().set_logger_console_handler(name, format, level)

##
## >>================================ test method ===============================>>
##
def test_default_logger():
  """
  Test the default logger
  """
  logger = get_logger()
  logger.info("This is a test log message from the default logger.")
  logger.error("This is a test error message from the default logger.")
  logger.warning("This is a test warning message from the default logger.")
  logger.debug("This is a test debug message from the default logger.")
  logger.critical("This is a test critical message from the default logger.")
  
  # test_logger = register_logger(name="test_logger", level="DEBUG")
  # set_logger_console_handler(name="test_logger", format=DEFAULT_LOGGER_FORMATTER_STR, level="DEBUG")
  # set_logger_file_handler(name="test_logger", file_path="test_log.log", format=DEFAULT_LOGGER_FORMATTER_STR, level="DEBUG")
  # test_logger.info("This is a test log message from the test logger.")
  # test_logger.error("This is a test error message from the test logger.")
  # test_logger.warning("This is a test warning message from the test logger.")
  # test_logger.debug("This is a test debug message from the test logger.")
  # test_logger.critical("This is a test critical message from the test logger.")

##
## >>================================ main method ===============================>>
##
if __name__ == "__main__":
  test_default_logger()
  