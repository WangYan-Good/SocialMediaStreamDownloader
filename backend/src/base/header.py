##>> test
##<< test

##<<Base>>
from abc import ABC, abstractmethod
from copy import deepcopy

##<<Extension>>

##<<Third-part>>
from backend.src.library.baselib import set_dict_attr, output_dict, get_dict_attr
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
  @abstractmethod
  def dump_header(self):
    get_logger().info("Header configuration:")
    output_dict(self._header)

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
