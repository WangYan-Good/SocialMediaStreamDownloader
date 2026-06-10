##<<Test>>
import os
import sys
sys.path.append(os.getcwd())

##<<Third-part>>
from backend.src.library.loglib  import register_logger,            \
                                        set_logger_console_handler, \
                                        set_logger_file_handler,    \
                                        set_logger_console_handler, \
                                        register_logger,            \
                                        get_logger

DEFAULT_LOGGER_FORMATTER_STR = '[%(asctime)s]-[%(name)s]-[%(levelname)s]: %(message)s'

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

  test_logger = register_logger(name="test_logger", level="DEBUG")
  set_logger_console_handler(name="test_logger", format=DEFAULT_LOGGER_FORMATTER_STR, level="DEBUG")
  set_logger_file_handler(name="test_logger", file_path="test_log.log", format=DEFAULT_LOGGER_FORMATTER_STR, level="DEBUG")
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