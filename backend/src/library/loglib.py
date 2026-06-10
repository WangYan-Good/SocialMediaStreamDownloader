##>>Test
import os
import sys
sys.path.append(os.getcwd())
##<<Test

##<<Third-part>>
from backend.src.base.log import Logger, LoggerManager

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