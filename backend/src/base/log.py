##<<Base>>
import os
import sys
sys.path.append(os.getcwd())
from logging import Logger, FileHandler, StreamHandler, Formatter
from pathlib import Path
import time

##<<Existension>>
import yaml as yml

##<<Third-part>>
from backend.src.base.config import DEFAULT_BASE_CONFIG_PATH
from backend.src.library.baselib import get_dict_attr

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
  __DEFAULT_LOGGER_LEVEL         = "DEBUG"
  __DEFAULT_LOGGER_FORMATTER_STR = '[%(asctime)s]-[%(name)s]-[%(levelname)s]: %(message)s'
  __DEFAULT_LOG_FILE_NAME        = None

##
## >>============================= private method =============================>>
##
  ##
  ## init the logger manager
  ##
  def __init__(self) -> None:
    
    try:
      ##
      ## initialize the default logger
      ##
      self.__init_default_logger()
    except Exception as e:
      raise e

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
    self.__init_default_logger_file_handler()
    
    ##
    ## add the default logger to the logger queue
    ##
    self.__logger_queue[self.__DEFAULT_LOGGER_NAME] = self.__default_logger

  ##
  ## initialize the default logger with file handler
  ##
  def __init_default_logger_file_handler(self) -> None:
    logger = self.__default_logger
    
    ##
    ## load default config from file
    ##
    try:
      with open(DEFAULT_BASE_CONFIG_PATH, 'r') as file:
        ##
        ## load the default config file
        ##
        config = yml.safe_load(file)
        
        ##
        ## get the log path from the config file
        ##
        file_path = get_dict_attr(config, "$.log_path")
        if file_path is None:
          raise Exception("Log path is not defined in the base config file.")
        
        ##
        ## set create the log directory if it does not exist
        ##
        log_dir = Path(file_path)
        if not log_dir.exists():
          log_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
      raise Exception(f"Failed to load default logger configuration: {e}")
    
    ##
    ## set the file handler for the default logger
    ##
    file_handler = FileHandler(time.strftime(f"{file_path}/%Y-%m-%d.log"))
    file_handler.setLevel(self.__DEFAULT_LOGGER_LEVEL)
    file_handler.setFormatter(Formatter(self.__DEFAULT_LOGGER_FORMATTER_STR))
    logger.addHandler(file_handler)

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
  def set_logger_file_handler(self, name:str, file_path:str, level:str="DEBUG") -> None:
    logger = self.get_logger(name)
    file_handler = FileHandler(file_path)
    file_handler.setLevel(level)
    logger.addHandler(file_handler)

  ##
  ## set logger with console handler
  ##
  def set_logger_console_handler(self, name:str, level:str="DEBUG") -> None:
    logger = self.get_logger(name)
    console_handler = StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(Formatter(self.__DEFAULT_LOGGER_FORMATTER_STR))
    logger.addHandler(console_handler)

##
## >>================================ public method ===============================>>
##

##
## singleton pattern for LoggerManager
##
logger_manager_instance = LoggerManager()

##
## register a logger for module-level logging
##
def register_logger(name:str, level:str) -> Logger:
  return logger_manager_instance.register_logger(name, level)

##
## get logger by name
##
def get_logger(name:str="default") -> Logger:
  return logger_manager_instance.get_logger(name)
  
##
## set logger with file handler
##
def set_logger_file_handler(name:str, file_path:str, level:str="DEBUG") -> None:
  logger_manager_instance.set_logger_file_handler(name, file_path, level)

##
## set logger with console handler
##
def set_logger_console_handler(name:str, level:str="DEBUG") -> None:
  logger_manager_instance.set_logger_console_handler(name, level)

##
## >>================================ test method ===============================>>
##
def test_default_logger():
  """
  Test the default logger
  """
  Lm = LoggerManager()
  logger = Lm.get_logger()
  logger.info("This is a test log message from the default logger.")
  logger.error("This is a test error message from the default logger.")
  logger.warning("This is a test warning message from the default logger.")
  logger.debug("This is a test debug message from the default logger.")
  logger.critical("This is a test critical message from the default logger.")
  
  test_logger = Lm.register_logger(name="test_logger", level="INFO")
  test_logger_console_handler = StreamHandler()
  test_logger_console_handler.setFormatter(Formatter('[%(asctime)s]-[%(name)s]-[%(levelname)s]: %(message)s'))
  test_logger.addHandler(test_logger_console_handler)
  test_logger.info("This is a test log message from the test logger.")
  test_logger.error("This is a test error message from the test logger.")
  test_logger.warning("This is a test warning message from the test logger.")
  test_logger.debug("This is a test debug message from the test logger.")
  test_logger.critical("This is a test critical message from the test logger.")

##
## >>================================ main method ===============================>>
##
if __name__ == "__main__":
  test_default_logger()
  