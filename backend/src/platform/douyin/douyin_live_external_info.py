##<<Base>>
import re

##<<Extension>>

##<<Third-part>>
from backend.src.base.json import JSON
from backend.src.library.baselib import get_dict_attr

##
## Live stream file name
##
# LIVE_STREAM_FILE_NAME_RE = r"stream-(\d+)_(\w+)\.(?:flv|m3u8)"
LIVE_STREAM_FILE_NAME_RE = r'/([^/?]+\.(?:flv|m3u8))'

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
    return self._replaceT(nickname, replace=None)
  
  def get_raw_nickname(self, response):
    nickname = str()
    build_dict = response.json()
    nickname = get_dict_attr(build_dict, "$.data.room.owner.nickname")
    if nickname is None:
      raise ValueError
    return nickname

  def get_flv_pull_url(self, response, flv_clarity, hls_clarity=None):
    clarity_names = {
      1: "FULL_HD1",
      2: "HD1",
      3: "SD1",
      4: "SD2",
    }
    stream_url = response.json()["data"]["room"]["stream_url"]
    configured_clarity = clarity_names.get(flv_clarity)
    if configured_clarity is None:
      raise ValueError("Unsupported FLV clarity: {}".format(flv_clarity))

    flv_urls = stream_url.get("flv_pull_url", {})
    fallback_order = [
      configured_clarity,
      *[
        clarity
        for clarity in clarity_names.values()
        if clarity != configured_clarity
      ],
    ]
    live_stream_url = next(
      (flv_urls.get(clarity) for clarity in fallback_order if flv_urls.get(clarity)),
      None,
    )
    if not live_stream_url:
      raise ValueError("No usable FLV live stream URL found")

    match = re.search(LIVE_STREAM_FILE_NAME_RE, live_stream_url)
    if match is None:
      raise ValueError("Live stream URL does not contain a media file name")
    return live_stream_url, match.group(1)

  def get_hls_pull_url(self, response):
     pass
  
  def get_room_status (self, response):
    build_dict = response.json()
    return build_dict["data"]["room"]["status"]
  
  def get_status (self, response):
    build_dict = response.json()
    return build_dict["status_code"]
