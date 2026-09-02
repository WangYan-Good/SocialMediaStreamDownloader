##<<Test>>
import os
import sys
sys.path.append(os.getcwd())

##<<Base>>
from logging import Logger, StreamHandler, Formatter
from logging.handlers import RotatingFileHandler
from pathlib import Path
import copy
import re
import threading

##
## >>============================= public defination =============================>>
##
DEFAULT_LOGGER_FORMATTER_STR = '[%(asctime)s]-[%(name)s]-[%(levelname)s]: %(message)s'
VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
LOG_MAX_BYTES = 10 * 1024 * 1024
LOG_BACKUP_COUNT = 9
LOG_MAX_RECORD_BYTES = 64 * 1024
LOG_TRUNCATION_MARKER = "[truncated]"


class BoundedUtf8Formatter(Formatter):
  """Bound one independently formatted record by its final UTF-8 byte size."""

  def __init__(
    self,
    fmt=None,
    datefmt=None,
    style="%",
    validate=True,
    defaults=None,
    max_record_bytes=LOG_MAX_RECORD_BYTES,
  ):
    if type(max_record_bytes) is not int or max_record_bytes <= 0:
      raise ValueError("max_record_bytes must be a positive integer")
    marker_size = len(LOG_TRUNCATION_MARKER.encode("utf-8"))
    if max_record_bytes < marker_size:
      raise ValueError("max_record_bytes must fit the truncation marker")
    super().__init__(fmt, datefmt, style, validate, defaults=defaults)
    self.max_record_bytes = max_record_bytes

  def format(self, record):
    ## ``Formatter.format`` caches traceback text on the LogRecord. Copy first
    ## so one handler cannot change what the next handler observes.
    formatted = super().format(copy.copy(record))
    encoded = formatted.encode("utf-8", errors="replace")
    if len(encoded) <= self.max_record_bytes:
      return encoded.decode("utf-8")

    marker = LOG_TRUNCATION_MARKER.encode("utf-8")
    prefix = encoded[:self.max_record_bytes - len(marker)]
    ## Dropping only an incomplete final code point keeps the retained prefix
    ## valid UTF-8 without walking or rewriting the rest of the record.
    safe_prefix = prefix.decode("utf-8", errors="ignore")
    return safe_prefix + LOG_TRUNCATION_MARKER


class BoundedRotatingFileHandler(RotatingFileHandler):
  """Size-rotating UTF-8 file handler with descriptor-level mode control."""

  def __init__(
    self,
    filename,
    mode="a",
    maxBytes=LOG_MAX_BYTES,
    backupCount=LOG_BACKUP_COUNT,
    encoding="utf-8",
    delay=False,
    errors=None,
  ):
    if type(maxBytes) is not int or maxBytes <= 0:
      raise ValueError("maxBytes must be a positive integer")
    if type(backupCount) is not int or backupCount <= 0:
      raise ValueError("backupCount must be a positive integer")
    super().__init__(
      filename,
      mode=mode,
      maxBytes=maxBytes,
      backupCount=backupCount,
      encoding=encoding,
      delay=delay,
      errors=errors,
    )

  def _open(self):
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
    flags |= getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(self.baseFilename, flags, 0o600)
    try:
      os.fchmod(descriptor, 0o600)
      stream = os.fdopen(
        descriptor,
        self.mode,
        encoding=self.encoding,
        errors=self.errors,
      )
      descriptor = -1
      return stream
    finally:
      if descriptor >= 0:
        os.close(descriptor)

  def shouldRollover(self, record):
    if self.stream is None:
      self.stream = self._open()
    if self.maxBytes <= 0:
      return False
    current_size = os.fstat(self.stream.fileno()).st_size
    formatted = self.format(record) + self.terminator
    record_size = len(formatted.encode(self.encoding or "utf-8"))
    return current_size > 0 and current_size + record_size >= self.maxBytes


def build_bounded_file_handler(
  filename,
  *,
  level="DEBUG",
  formatter_format=DEFAULT_LOGGER_FORMATTER_STR,
  max_bytes=LOG_MAX_BYTES,
  backup_count=LOG_BACKUP_COUNT,
  max_record_bytes=LOG_MAX_RECORD_BYTES,
):
  handler = BoundedRotatingFileHandler(
    filename=str(filename),
    maxBytes=max_bytes,
    backupCount=backup_count,
    encoding="utf-8",
  )
  handler.setLevel(level)
  handler.setFormatter(BoundedUtf8Formatter(
    formatter_format,
    max_record_bytes=max_record_bytes,
  ))
  return handler


class LoggerManager():
##
## >>============================= attribute =============================>>
##
  __default_logger          = None
  __default_console_handler = None
  __logger_queue            = dict()
  __initialized             = False
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
    instance = getattr(cls, "_instance", None)
    if instance is not None and getattr(
      instance, "_LoggerManager__initialized", False
    ):
      return instance
    return cls()

  ##
  ## init the logger manager
  ##
  def __init__(self, config: dict = None) -> None:
    if self._LoggerManager__initialized:
      return
    with self.__instance_Lock:
      if self._LoggerManager__initialized:
        return
      log_config = self.__load_log_config(config)
      self.__configure(log_config)
      self.__logger_queue = {}
      try:
        self.__init_default_logger()
      except Exception:
        self.__cleanup_failed_initialization()
        raise
      self._LoggerManager__initialized = True

  def __cleanup_failed_initialization(self) -> None:
    if self.__default_logger is not None:
      for handler in self.__default_logger.handlers[:]:
        self.__default_logger.removeHandler(handler)
        handler.close()
    self.__default_logger = None
    self.__default_console_handler = None
    self.__logger_queue = {}
    self._LoggerManager__initialized = False

  def __load_log_config(self, config):
    if config is None:
      from backend.src.base.config import BaseConfig
      config = BaseConfig().get_config().get("log")
    if not isinstance(config, dict):
      raise ValueError("Unified log config must be a mapping")
    return config

  def __configure(self, config: dict) -> None:
    log_enable = config.get("log_enable")
    log_level = config.get("log_level")
    log_save = config.get("log_save")
    log_file_path = config.get("log_file_path")

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

    self.__log_enable = log_enable
    self.__log_save = log_save
    self.__DEFAULT_LOGGER_LEVEL = log_level
    self.__DEFAULT_LOG_FILE_PATH = (
      Path(log_file_path) if isinstance(log_file_path, str) and log_file_path.strip()
      else None
    )
    self.__DEFAULT_LOG_FILE_DIR = (
      self.__DEFAULT_LOG_FILE_PATH.parent
      if self.__DEFAULT_LOG_FILE_PATH is not None
      else Path(".")
    )
    if self.__log_save:
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
    self.__default_console_handler.setFormatter(BoundedUtf8Formatter(
      self.__DEFAULT_LOGGER_FORMATTER_STR
    ))
    self.__default_logger.addHandler(self.__default_console_handler)
    
    ##
    ## initialize the default logger with file handler
    ##
    if self.__log_save:
      file_handler = build_bounded_file_handler(
        self.__DEFAULT_LOG_FILE_PATH,
        level=self.__DEFAULT_LOGGER_LEVEL,
        formatter_format=self.__DEFAULT_LOGGER_FORMATTER_STR,
      )
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
      file_handler = build_bounded_file_handler(
        self.__DEFAULT_LOG_FILE_DIR / file_name[0],
        level=level,
        formatter_format=(
          format if format is not None else self.__DEFAULT_LOGGER_FORMATTER_STR
        ),
      )
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
      console_handler.setFormatter(BoundedUtf8Formatter(format))
      logger.addHandler(console_handler)
    except Exception as e:
      raise Exception(f"Failed to set console handler for logger {name}: {e}")

##
## >>================================ public method ===============================>>
##
