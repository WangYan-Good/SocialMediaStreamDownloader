##<<Base>>
from abc import abstractmethod
from logging import Logger, FileHandler, StreamHandler

##<<Existension>>

##<<Third-part>>

class LoggerManager():

##
## >>============================= attribute =============================>>
##
  __enable = False
  __default_logger = None
  __logger_queue = set()

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

      ##
      ## initialize the logger queue
      ##
      self.__init_logger_queue()
      
      ##
      ## start the logger manager
      ##
      self.__enable_logger_manager()
    except Exception as e:
      raise e
    
  ##
  ## enable the logger manager
  ##
  def __enable_logger_manager(self) -> None:
    self.__enable = True

  ##
  ## initialize the default logger
  ##
  def __init_default_logger(self) -> None:
    self.__default_logger = Logger(name="default", level="DEBUG")
    
    ##
    ## set console handler for the default logger
    ##
    self.__default_logger.addHandler(StreamHandler())

  ##
  ##  initialize the logger queue
  ##
  def __init_logger_queue(self) -> None:
    ##
    ## initialize the default logger
    ##
    if self.__default_logger is None:
      self.__default_logger = self.register_logger("default")
      self.__logger_queue.add(self.__default_logger)
  
##
## >>============================= abstract method =============================>>
##

##
## >>============================= sub class method =============================>>
##

  ##
  ## disable the logger manager
  ##
  def disable_logger_manager(self):
    self.__enable = False

  ##
  ## register a logger for module-level logging
  ##
  def register_logger(self, name:str):
    pass
  
  ##
  ## destroy the logger queue
  ##
  def destroy_logger_queue(self):
    pass
  
  ##
  ## set the path for the file handler
  ##
  def set_file_handler_path(self, name:str, path:str) -> None:
    ##
    ## check if the parameters are valid
    ## when path is None, it will output to the console
    ##
    if name is None:
      raise Exception("Logger name cannot be None.")
    
    ##
    ## check if the logger manager is enabled
    ##
    if not self.__enable:
      raise Exception("Logger manager is not enabled.")
    
    ##
    ## check if the default logger is initialized
    ##
    if self.__default_logger is None:
      raise Exception("Default logger is not initialized.")
    
    ##
    ## find the logger in the logger queue
    ##
    for logger in self.__logger_queue:
      if logger.name == name:
        ##
        ## set the file handler for the logger
        ##
        file_handler = FileHandler(path)
        logger.addHandler(file_handler)
        return
    
    raise Exception(f"Logger {name} not found in the logger queue.")

##
## >>================================ test method ===============================>>
##

##
## >>================================ main method ===============================>>
##