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

##TODO remove
import f2
from f2.apps.douyin.utils import TokenManager as TM

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
## >>============================= sub class method =============================>>
##
  ##
  ## Update msToken
  ##
  def create_douyin_msToken(self):
    ##
    ## update attribute
    ##
    return TM.gen_real_msToken()

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
  def init_share_live_header(self, login: bool = False):
    if login is True:
      self._header = super().get_header_dict_attr("$.share_live_url")
    else:
      self._header = super().get_header_dict_attr("$.share_live_url_no_login")
    if self._header is None:
      print("ERROR: Douyin share live header does not found!")
      raise ModuleNotFoundError
  
  ##
  ## initialize header
  ##
  def init_share_post_header(self, login:bool = False):
    if login is True:
      pass
    else:
      pass
    if self._header is None:
      print("ERROR: Douyin share post header does not found!")
      raise ValueError
    print("INFO: Douyin share post header initialize complete")
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
  def set_header_dict_attr(self, attr: str = None, value: any = None):
    set_dict_attr(self._header, attr, value)

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

  ##
  ## update header
  ##
  def update_header(self, login: bool = False, header:dict = None)->dict:
    if login is True:
      set_dict_attr(header, "$.User-Agent", self.get_header_dict_attr("$.user-agent"))
    else:
      # set_dict_attr(header, "$.Referer", self.get_header_dict_attr("$.referer"))
      # set_dict_attr(header, "$.Accept", self.get_header_dict_attr("$.accept"))
      # set_dict_attr(header, "$.Accept-Encoding", self.get_header_dict_attr("$.accept-encoding"))
      # set_dict_attr(header, "$.Accept-Language", self.get_header_dict_attr("$.accept-language"))
      # set_dict_attr(header, "$.Cookie", self.get_header_dict_attr("$.cookie"))
      # set_dict_attr(header, "$.Priority", self.get_header_dict_attr("$.priority"))
      # set_dict_attr(header, "$.Sec-Ch-Ua", self.get_header_dict_attr("$.sec-ch-ua"))
      # set_dict_attr(header, "$.Sec-Ch-Ua-Mobile", self.get_header_dict_attr("$.sec-ch-ua-mobile"))
      # set_dict_attr(header, "$.Sec-Ch-Ua-Platform", self.get_header_dict_attr("$.sec-ch-ua-platform"))
      # set_dict_attr(header, "$.Sec-Fetch-Dest", self.get_header_dict_attr("$.sec-fetch-dest"))
      # set_dict_attr(header, "$.Sec-Fetch-Mode", self.get_header_dict_attr("$.sec-fetch-mode"))
      # set_dict_attr(header, "$.Sec-Fetch-Site", self.get_header_dict_attr("$.sec-fetch-site"))
      set_dict_attr(header, "$.User-Agent", self.get_header_dict_attr("$.user-agent"))
      # set_dict_attr(header, "$.Content-Type", self.get_header_dict_attr("$.content-type"))
    return header
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
