##<<Test
import os
import sys
sys.path.append(os.getcwd())
##>>Test
##<<Base>>
from abc import abstractmethod

##<<Extension>>

##<<Third-part>>
from pathlib import Path
from src.base.header import Header
from src.library.baselib import output_dict, get_dict_attr, set_dict_attr

DEFAULT_HEADER_PATH = "config/douyin/headers.yml"

class DouyinHeader(Header):
##
## >>============================= attribute =============================>>
##
  ##
  ## attribute
  ##
  _header = dict()

##
## >>============================= private method =============================>>
##
  ##
  ## init
  ##
  def __init__(self, header_path: Path | str = None) -> None:
    if header_path is None:
      print("WARNNING: Invalid config, use default douyin header config")
      header_path = DEFAULT_HEADER_PATH
    
    ##
    ## initialize header
    ##
    super().__init__(header_path)
    self._header = super().to_dict()
##
## >>============================= abstract method =============================>>
##
  ##
  ## conversion header to dict
  ##
  def to_dict(self) -> dict:
    return self._header

  ##
  ## Dump header config
  ##
  def dump_header(self):
    output_dict(self._header)

  ##
  ## get header dict attr
  ##
  def get_header_dict_attr(self, attr: str = None):
    return get_dict_attr(self._header, attr)
  
  ##
  ## set header dict attr
  ##
  def set_header_dict_attr(self, attr: str = None, value: any = None):
    set_dict_attr(self._header, attr, value)

  ##
  ## initialize header
  ##
  @abstractmethod
  def init_header(self, login: bool = False):
    pass
##
## >>============================= sub class method =============================>>
##
  ##
  ## set header sttribute 
  ## example: "$.a.b.c"
  ##
  def set_header_attribute(self, attr:str=None, value:any=None):
    pass

##
## header for query share url
##
class DouyinShareHeader(DouyinHeader):
##
## >>============================= attribute =============================>>
##
  ##
  ## attribute
  ##
  _header = dict()

##
## >>============================= private method =============================>>
##
  ##
  ## Initialize header and constrcut
  ##
  def __init__(self, header_path: Path | str = None) -> None:
    super().__init__(header_path)

##
## >>============================= abstract method =============================>>
##  
  ##
  ## conversion header to dict
  ##
  def to_dict(self)->dict:
    return self._header

  ##
  ## Dump header config
  ##
  def dump_header(self):
    print("Douyin share url header configuration:")
    output_dict(self._header)

  ##
  ## get header dict attr
  ##
  def get_header_dict_attr(self, attr: str = None):
    return get_dict_attr(self._header, attr)

  ##
  ## set header dict attr
  ##
  def set_header_attribute(self, attr:str=None, value:any=None):
    set_dict_attr(self._header, attr, value)

  ##
  ## initialize header
  ##
  def init_header(self, login: bool = False):
    if login is True:
      self._header = super().get_header_dict_attr("$.share_live_url")
    else:
      self._header = super().get_header_dict_attr("$.share_live_url_no_login")
    if self._header is None:
      print("ERROR: Douyin share header does not found!")
      raise ModuleNotFoundError
    print("INFO: Douyin share header initialize complete")
##
## >>============================= sub class method =============================>>
##

class DouyinLiveInfoHeader(DouyinHeader):
##
## >>============================= attribute =============================>>
##
  ##
  ## attribute
  ##
  _header = dict()

##
## >>============================= private method =============================>>
##
  ##
  ## init
  ##
  def __init__(self, header_path: Path | str = None) -> None:
    super().__init__(header_path)

##
## >>============================= abstract method =============================>>
##
  ##
  ## conversion header to dict
  ##
  def to_dict(self)->dict:
    return self._header

  ##
  ## Dump header config
  ##  
  def dump_header(self):
    print("Douyin live info header configuration:")
    output_dict(self._header)

  ##
  ## get header dict attr
  ##
  def get_header_dict_attr(self, attr: str = None):
    return get_dict_attr(self._header, attr)

  ##
  ## set header dict attr
  ##
  def set_header_attribute(self, attr):
    set_dict_attr(self._header, attr)

##
## >>============================= sub class method =============================>>
##
  ##
  ## init header by login status
  ##
  def init_header(self, login: bool = False):
    if login is True:
      self._header = super().get_header_dict_attr("$.live_room_info")
    else:
      self._header = super().get_header_dict_attr("$.live_room_info_no_login")
    if self._header is None:
      print("ERROR: Douyin live info header does not found!")
      raise ModuleNotFoundError
    print("INFO: Douyin live info header initialize complete")

class DouyinPostInfoHeader(DouyinHeader):
##
## >>============================= attribute =============================>>
##
  ##
  ## attribute
  ##
  _header = dict()

##
## >>============================= private method =============================>>
##
  ##
  ## init
  ##
  def __init__(self, header_path: Path | str = None) -> None:
    super().__init__(header_path)
  
##
## >>============================= abstract method =============================>>
##
  ##
  ## conversion header to dict
  ##
  def to_dict(self)->dict:
    return self._header

  ##
  ## Dump header config
  ##  
  def dump_header(self):
    print("Douyin live info header configuration:")
    output_dict(self._header)

  ##
  ## get header dict attr
  ##
  def get_header_dict_attr(self, attr: str = None):
    return get_dict_attr(self._header, attr)

  ##
  ## set header dict attr
  ##
  def set_header_attribute(self, attr):
    set_dict_attr(self._header, attr)

##
## >>============================= sub class method =============================>>
##
  ##
  ## init header by login status
  ##
  def init_header(self, login: bool = False):
    if login is True:
      self._header = super().get_header_dict_attr("$.post_info")
    else:
      self._header = super().get_header_dict_attr("$.post_info_no_login")
    if self._header is None:
      print("ERROR: Douyin post info header does not found!")
      raise ModuleNotFoundError
    print("INFO: Douyin post info header initialize complete")

if __name__ == "__main__":
  # '''
  dyheader = DouyinShareHeader(DEFAULT_HEADER_PATH)
  dyheader.init_header(False)
  dyheader.dump_header()
  # '''

  # '''
  dyheader = DouyinLiveInfoHeader(DEFAULT_HEADER_PATH)
  dyheader.init_header(False)
  dyheader.dump_header()
  # '''

  # '''
  dyheader = DouyinPostInfoHeader(DEFAULT_HEADER_PATH)
  dyheader.init_header(False)
  dyheader.dump_header()
  # '''
