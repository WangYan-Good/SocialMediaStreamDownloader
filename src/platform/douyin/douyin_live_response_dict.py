##>> test
import os
import sys
WORK_SPACE = os.path.dirname(sys.path[0])
sys.path.append(os.path.join(WORK_SPACE))
import json
##<< test

# base
from pathlib import Path
import yaml
from requests import request
from time import sleep
from random import randint
from urllib.parse import urlparse
from urllib.parse import parse_qs
from re import compile

# F2
from f2.utils.xbogus import XBogus as XB

LIVE_CONFIG_PATH = "config/douyin/live.yml"
MAX_TIMEOUT = 10

room_id_live_path = compile(r"/douyin/webcast/reflow/\S+")
room_id = compile(r"/douyin/webcast/reflow/(\S+)")

class Live():
  
  def __init__(self, url:str) -> None:
    # check url
    if url is None:
      print("Have no detect live url")

    # load default config formal
    self.live_config = yaml.safe_load(Path(LIVE_CONFIG_PATH).read_text(encoding="utf-8"))
    
    # initialize live link share
    self.live_config["live"]["live_link_share"] = url
    
    # request response url
    self.live_config["live"]["response_url"] = self.__get_response_url(url)    

    # initialize X-Bogus
    self.live_config["live"]["X-Bogus"] = self.live_config["live"]["response_url"]["X-Bogus"]

    # make sure root_id/web_rid
    if (u:=room_id_live_path.findall(self.live_config["live"]["response_url"]["path"])) is not None:
      self.live_config["live"]["rid"] = True
      self.live_config["live"]["room_id"] = room_id.findall(self.live_config["live"]["response_url"]["path"])
      self.live_config["live"]["web_rid"] = None
    else:
      self.live_config["live"]["rid"] = False
      self.live_config["live"]["room_id"] = None
      self.live_config["live"]["web_rid"] = room_id.findall(self.live_config["live"]["response_url"]["path"])

    # self.update_config()
  
  def update_config(self):
    # save yaml config
    with open(LIVE_CONFIG_PATH, 'w') as f:
      yaml.safe_dump(self.live_config, f)
  
  def __get_response_url(self, share_url:str) -> dict:
    response_url = dict()
    # request url
    response = request("get", share_url, timeout=MAX_TIMEOUT, headers=self.live_config["live"]["headers"])
    
    # random delay
    sleep(randint(15, 45) * 0.1)
    
    # initialize X-Bogus
    response_url["X-Bogus"] = XB(user_agent=self.live_config["live"]["headers"].get("User-Agent", "")).getXBogus(response.url)

    # response url
    url = urlparse(response.url)
    response_url["scheme"] = url.scheme
    response_url["netloc"] = url.netloc
    response_url["path"] = url.path
    response_url["params"] = url.params

    # url query
    url_query = str(parse_qs(url.query)).replace("\\", "")
    response_url["query"] = yaml.safe_load(url_query)
    return response_url

if __name__ == "__main__":
  live_config = Live("https://v.douyin.com/iFemNNTW/")
  print(live_config.live_config)
