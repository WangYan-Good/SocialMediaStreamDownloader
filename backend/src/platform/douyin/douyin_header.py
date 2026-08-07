##<<Test
import os
import sys
sys.path.append(os.getcwd())
##>>Test

##<<Third-part>>
from backend.src.base.header     import Header
from backend.src.library.baselib import output_dict, get_dict_attr, set_dict_attr
from backend.src.library.loglib  import get_logger

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
  def __init__(self, config: dict) -> None:
    super().__init__(config)
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
    try:
      from f2.apps.douyin.utils import TokenManager as TM
      return TM.gen_real_msToken()
    except Exception as e:
      get_logger().warning("f2 TokenManager unavailable, use empty msToken: {}".format(e))
      return ""

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
  def __init__(self, config: dict) -> None:
    super().__init__(config)

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
    get_logger().info("Douyin share url header configuration:")
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
      get_logger().error("Douyin share live header does not found!")
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
      get_logger().error("Douyin share post header does not found!")
      raise ValueError
    get_logger().info("Douyin share post header initialize complete")
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
  def __init__(self, config: dict) -> None:
    super().__init__(config)

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
    get_logger().info("Douyin live info header configuration:")
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
      get_logger().error("Douyin live info header does not found!")
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
  def __init__(self, config: dict) -> None:
    super().__init__(config)
  
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
    get_logger().info("Douyin live info header configuration:")
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
      get_logger().error("Douyin post info header does not found!")
      raise ModuleNotFoundError
    get_logger().info("Douyin post info header initialize complete")
