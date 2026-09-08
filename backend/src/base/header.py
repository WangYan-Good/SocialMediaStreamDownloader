##>> test
##<< test

##<<Base>>
from abc import ABC, abstractmethod
from copy import deepcopy

##<<Extension>>

##<<Third-part>>
from backend.src.library.baselib import set_dict_attr, get_dict_attr
from backend.src.library.loglib import get_logger
from backend.src.library.safe_diagnostics import config_diagnostic
DEFAULT_REFERER = "https://www.douyin.com/"
DEFAULT_USERR_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"

class Header(ABC):
##
## >>============================= attribute =============================>>
##
  ##
  ## Defination and Initialize default
  ##
  _header = dict()

##
## >>============================= private method =============================>>
##
  ##
  ## Initialize header and constrcut
  ##
  def __init__(self, config: dict) -> None:
    if not isinstance(config, dict):
      raise ValueError("configuration must be a mapping")
    self._header = deepcopy(config)
    return None
##
## >>============================= abstract method =============================>>
##
  ##
  ## conversion header to dict
  ##
  @abstractmethod
  def to_dict(self)->dict:
    return self._header


  ##
  ## Dump header config
  ##
  ##
  ## Deliberately dumps nothing.
  ##
  ## A header *is* the credential: on a logged-in deployment it carries the
  ## request ``Cookie`` and, where one is configured, ``Authorization``.
  ## ``output_dict`` ``print``s, so this went to stdout with no log level in
  ## front of it - a deployment could not have turned it down if it wanted to.
  ##
  @abstractmethod
  def dump_header(self):
    get_logger().info(
      config_diagnostic(
        "config_dumped",
        section="header",
        total=len(self._header) if isinstance(self._header, dict) else 0,
      )
    )

  ##
  ## get header dict attr
  ##
  @abstractmethod
  def get_header_dict_attr(self, attr:str=None):
    return get_dict_attr(self._header, attr)

  ##
  ## set header dict attr
  ##
  @abstractmethod
  def set_header_dict_attr(self, attr:str=None, value:any=None):
    set_dict_attr(self._header, attr, value)

##
## >>============================= sub class method =============================>>
##
  ##
  ## save header
  ##
  def save_header(self, output = None):
    pass
