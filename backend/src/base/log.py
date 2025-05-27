##<<Base>>
from abc import abstractmethod
from logging import Logger, FileHandler, StreamHandler, Formatter

##<<Existension>>

##<<Third-part>>

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
  