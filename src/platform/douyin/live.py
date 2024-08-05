#>>test
#<<test

##<<Base>>
from requests import request
from random import randint
from time import sleep
from urllib.parse import urlparse
from urllib.parse import parse_qs
from re import compile
from pathlib import Path

##<<Extension>>
import yaml as yml

##<<Third-part>>
from src.base.header import Header
from platform.douyin.xbogus import XBogus as XB

MAX_TIMEOUT = 10
ROOM_ID_LIVE_PATH = compile(r"/douyin/webcast/reflow/\S+")
ROOM_ID = compile(r"/douyin/webcast/reflow/(\S+)")

DEFAULT_LIVE_CONFIG_NAME = "config/douyin/live.yml"

class Live():
  ##
  ## Declare and define default value
  ##
  timeout         = None
  live_link_share = ""
  header          = dict()
  rid             = bool()
  room_id         = ""
  web_rid         = ""
  x_bogus         = None

  def __init__(self) -> None:
    pass

  def construct_live_data(self, query_response:dict=None)->None:
    if query_response is None:
        return None
    ##
    ## Construct live data
    ## Make sure root_id/web_rid
    ## 
    if (u:=ROOM_ID_LIVE_PATH.findall(query_response["path"])) is not None:
      self.rid = True
      self.room_id = ROOM_ID.findall(query_response["path"])
      self.web_rid = None
    else:
      self.rid = False
      self.room_id = None
      self.web_rid = ROOM_ID.findall(query_response["path"])

  def query_share_url(self, url:str = "", timeout=MAX_TIMEOUT, header:Header = None):
    response_url = dict()
    ##
    ## Preparetion
    ##
    self.live_link_share = url
    self.timeout = timeout
    self.header["Referer"] = header.referer
    self.header["User-Agent"] = header.user_agent
    response = request("get", self.live_link_share, timeout=self.timeout, headers=self.header)
    self.x_bogus = XB(user_agent=self.header["User-Agent"]).getXBogus(response.url)

    # random delay
    sleep(randint(15, 45) * 0.1)

    url = urlparse(response.url)
    response_url["scheme"] = url.scheme
    response_url["netloc"] = url.netloc
    response_url["path"] = url.path
    response_url["params"] = url.params

    # url query
    url_query = str(parse_qs(url.query)).replace("\\", "")
    response_url["query"] = yml.safe_load(url_query)
    return response_url
  
  def save_config(self, path:Path = DEFAULT_LIVE_CONFIG_NAME):
    live = dict()
    live["rid"] = self.rid
    live["room_id"] = self.room_id
    live["web_rid"] = self.web_rid
    live["sec_user_id"] = self.timeout

    with open(path, 'w') as f:
      yml.safe_dump(live, f)
