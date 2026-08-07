##<<Base>>
from dataclasses import dataclass
from pathlib import PurePosixPath
import re
from typing import Literal
from urllib.parse import urlparse

##<<Extension>>

##<<Third-part>>
from backend.src.base.json import JSON
from backend.src.library.baselib import get_dict_attr

##
## Live stream file name
##
@dataclass(frozen=True)
class LiveStreamSource:
  url: str
  file_name: str
  protocol: Literal["flv", "hls"]


class _NoUsableStreamError(ValueError):
  pass


class LiveExternal(JSON):
  CLARITY_NAMES = {
    1: "FULL_HD1",
    2: "HD1",
    3: "SD1",
    4: "SD2",
  }

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

  def _clarity_order(self, clarity, protocol):
    configured_clarity = self.CLARITY_NAMES.get(clarity)
    if configured_clarity is None:
      raise ValueError("Unsupported {} clarity: {}".format(protocol, clarity))
    return (
      configured_clarity,
      *(name for name in self.CLARITY_NAMES.values() if name != configured_clarity),
    )

  def _quality_urls(self, urls, clarity, protocol):
    source = urls if isinstance(urls, dict) else {}
    for name in self._clarity_order(clarity, protocol):
      candidate = source.get(name)
      if isinstance(candidate, str) and candidate.strip():
        yield candidate.strip()

  @staticmethod
  def _parse_http_url(candidate):
    try:
      parsed = urlparse(candidate)
    except ValueError:
      return None
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
      return None
    return parsed

  def get_flv_pull_url(self, response, flv_clarity, hls_clarity=None):
    stream_url = response.json()["data"]["room"]["stream_url"]
    for live_stream_url in self._quality_urls(
        stream_url.get("flv_pull_url"), flv_clarity, "FLV"):
      parsed = self._parse_http_url(live_stream_url)
      if parsed is None:
        continue
      path = PurePosixPath(parsed.path)
      if path.suffix.lower() == ".flv":
        return live_stream_url, path.name
    raise _NoUsableStreamError("No usable FLV live stream URL found")

  def get_hls_pull_url(self, response, hls_clarity):
    stream_url = response.json()["data"]["room"]["stream_url"]
    for live_stream_url in self._quality_urls(
        stream_url.get("hls_pull_url_map"), hls_clarity, "HLS"):
      parsed = self._parse_http_url(live_stream_url)
      if parsed is None:
        continue
      path = PurePosixPath(parsed.path)
      candidate = path.stem
      if candidate.lower() == "index":
        candidate = path.parent.name
      safe_name = re.sub(
        r"[^\u4e00-\u9fa5a-zA-Z0-9#_-]",
        "_",
        candidate,
      ).strip("._")
      return live_stream_url, (safe_name or "live") + ".ts"
    raise _NoUsableStreamError("No usable HLS live stream URL found")

  def get_live_stream_source(self, response, flv_clarity, hls_clarity):
    try:
      url, file_name = self.get_flv_pull_url(response, flv_clarity)
      return LiveStreamSource(url, file_name, "flv")
    except _NoUsableStreamError:
      pass

    try:
      url, file_name = self.get_hls_pull_url(response, hls_clarity)
      return LiveStreamSource(url, file_name, "hls")
    except _NoUsableStreamError as hls_error:
      raise ValueError("No usable FLV or HLS live stream URL found") from hls_error
  
  def get_room_status (self, response):
    build_dict = response.json()
    return build_dict["data"]["room"]["status"]
  
  def get_status (self, response):
    build_dict = response.json()
    return build_dict["status_code"]
