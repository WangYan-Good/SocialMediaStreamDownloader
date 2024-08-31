##<<Base>>
import re

##<<Extension>>

##<<Third-part>>
from src.base.json import JSON
from src.library.baselib import get_dict_attr

##
## Live stream file name
##
LIVE_STREAM_FILE_NAME_RE = r"stream-(\d+)_(\w+)\.(?:flv|m3u8)"

class LiveExternal(JSON):
  def __init__(self) -> None:
    super().__init__()

  def get_flv_url(self, response)->str:
    pass

  def _replaceT(self, obj, replace:str=None):
      """
      替换文案非法字符 (Replace illegal characters in the text)

      Args:
          obj (str): 传入对象 (Input object)

      Returns:
          new: 处理后的内容 (Processed content)
      """
      if replace is None:
        replace = "_"
      reSub = r"[^\u4e00-\u9fa5a-zA-Z0-9#]"

      if isinstance(obj, list):
          return [re.sub(reSub, replace, i) for i in obj]

      if isinstance(obj, str):
          return re.sub(reSub, replace, obj)

      return obj
      # raise TypeError("输入应为字符串或字符串列表")

  def get_nickname(self, response):
    nickname = str()
    build_dict = response.json()
    nickname = get_dict_attr(build_dict, "$.data.room.owner.nickname")
    if nickname is None:
      raise ValueError
    return self._replaceT(nickname)
  
  def get_raw_nickname(self, response):
    nickname = str()
    build_dict = response.json()
    nickname = get_dict_attr(build_dict, "$.data.room.owner.nickname")
    if nickname is None:
      raise ValueError
    return nickname

  def get_flv_pull_url(self, response, flv_clarity):
    ##
    ## catch live status success
    ## return live stream
    ##
    try:
      build_dict = response.json()
      ##
      ## FULL_HD1
      ##
      if flv_clarity == 1 and build_dict["data"]["room"]["stream_url"]["flv_pull_url"]["FULL_HD1"] is not None:
        self.live_stream_url = build_dict["data"]["room"]["stream_url"]["flv_pull_url"]["FULL_HD1"]
      elif self.hls_clarity == 1 and build_dict["data"]["room"]["stream_url"]["hls_pull_url_map"]["FULL_HD1"] is not None:
        self.live_stream_url = build_dict["data"]["room"]["stream_url"]["hls_pull_url_map"]["FULL_HD1"]
      ##
      ## HD1
      ##
      elif flv_clarity == 2 and build_dict["data"]["room"]["stream_url"]["flv_pull_url"]["HD1"] is not None:
        self.live_stream_url = build_dict["data"]["room"]["stream_url"]["flv_pull_url"]["HD1"]
      elif self.hls_clarity == 2 and build_dict["data"]["room"]["stream_url"]["hls_pull_url_map"]["HD1"] is not None:
        self.live_stream_url = build_dict["data"]["room"]["stream_url"]["hls_pull_url_map"]["HD1"]
      ##
      ## SD1
      ##
      elif flv_clarity == 3 and build_dict["data"]["room"]["stream_url"]["flv_pull_url"]["SD1"] is not None:
        self.live_stream_url = build_dict["data"]["room"]["stream_url"]["flv_pull_url"]["SD1"]
      elif self.hls_clarity == 3 and build_dict["data"]["room"]["stream_url"]["hls_pull_url_map"]["SD1"] is not None:
        self.live_stream_url = build_dict["data"]["room"]["stream_url"]["hls_pull_url_map"]["SD1"]
      ##
      ## SD2
      ##
      elif flv_clarity == 4 and build_dict["data"]["room"]["stream_url"]["flv_pull_url"]["SD2"] is not None:
        self.live_stream_url = build_dict["data"]["room"]["stream_url"]["flv_pull_url"]["SD2"]
      elif self.hls_clarity == 4 and build_dict["data"]["room"]["stream_url"]["hls_pull_url_map"]["SD2"] is not None:
        self.live_stream_url = build_dict["data"]["room"]["stream_url"]["hls_pull_url_map"]["SD2"]
      
      live_stream_name = re.search(LIVE_STREAM_FILE_NAME_RE, self.live_stream_url).group()
    except Exception as e:
       print(e)
       return None
    return self.live_stream_url, live_stream_name

  def get_hls_pull_url(self, response):
     pass
  
  def get_room_status (self, response):
    build_dict = response.json()
    return build_dict["data"]["room"]["status"]
  
  def get_status (self, response):
    build_dict = response.json()
    return build_dict["status_code"]