##>>Test
import logging
import os
import sys
sys.path.append(os.getcwd())
##<<Test

##<<Third-part>>
from backend.src.base.log import (
  BoundedUtf8Formatter,
  DEFAULT_LOGGER_FORMATTER_STR,
  Logger,
  LoggerManager,
  build_bounded_file_handler,
)

##
## register a logger for module-level logging
##
def register_logger(name:str, level:str) -> Logger:
  return LoggerManager().register_logger(name, level)

##
## get logger by name
##
def get_logger(name:str="default") -> Logger:
  manager = getattr(LoggerManager, "_instance", None)
  if manager is None or not getattr(
    manager,
    "_LoggerManager__initialized",
    False,
  ):
    ##
    ## LoggerManager is not initialized
    ## return a simple logger that outputs to console with DEBUG level
    ##
    return logging.getLogger("bootstrap")
  return manager.get_logger(name)
  
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
## initialize a bootstrap logger for logging during the early initialization phase before the main configuration is loaded
## should no dependency on LoggerManager
##
def init_bootstrap_logger():
  ##
  ## create a simple logger that outputs to console with DEBUG level
  ##
  logger = logging.getLogger("bootstrap")
  logger.setLevel(logging.DEBUG)
  
  ##
  ## set console handler with formatter
  ##
  console_handler = logging.StreamHandler()
  console_handler.setLevel(logging.DEBUG)
  formatter = BoundedUtf8Formatter(DEFAULT_LOGGER_FORMATTER_STR)
  console_handler.setFormatter(formatter)
  logger.addHandler(console_handler)
  
  ##
  ## set file handler with formatter
  ##
  log_file_path = os.path.join(os.getcwd(), "bootstrap.log")
  file_handler = build_bounded_file_handler(
    log_file_path,
    level="DEBUG",
    formatter_format=DEFAULT_LOGGER_FORMATTER_STR,
  )
  logger.addHandler(file_handler)
