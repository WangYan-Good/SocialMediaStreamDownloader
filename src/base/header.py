##>> test
##<< test

##<<Base>>
from abc import ABC, abstractmethod
from pathlib import Path

##<<Extension>>
import yaml

##<<Third-part>>
from src.library.baselib import load_yml, set_dict_attr, output_dict, get_dict_attr
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
  def __init__(self, header_path:Path|str = None) -> None:
    if header_path is None:
      raise FileNotFoundError
    
    try:
      if isinstance(header_path, str) is True:
        header_path = Path(header_path)
      ##
      ## Load header configuration
      ##
      self._header = load_yml(header_path)   
    except Exception as e:
      print("ERROR: Header init failed: {}".format(e))
      raise e
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
    print("Header configuration:")
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
  def save_header(self, output:Path = None):
    pass

if __name__ == "__main__":
  Header(Path("config/douyin/headers.yml")).dump_header()