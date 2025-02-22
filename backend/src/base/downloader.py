##>> test
##<< test

##<<Base>>
from abc import ABC, abstractmethod
from requests import request, exceptions
from pathlib import Path
from time import sleep
from random import randint
import urllib.request
import re

##<<Extension>>
import yaml as yml

##<<Third-part>>
from backend.src.base.config import BaseConfig, DEFAULT_BASE_CONFIG_PATH
from backend.src.base.header import Header
from backend.src.base.login  import Login

##
## Defination save file name
##
URL_RESPONSE_PATH = ""

class Downloader(ABC):
##
## >>============================= attribute =============================>>
##
  ##
  ## Downloader default configuration
  ##
  CONFIG_PATH                      = ""

  ##
  ## Config
  ##
  config                           = None

  ##
  ## Login
  ##
  login                            = None

  ##
  ## Header
  ##
  header                           = None

  ##
  ## API
  ##
  API                              = None

  ##
  ## Listener
  ##
  listener                        = None

##
## >>============================= private method =============================>>
##
  ##
  ## TODO: config path as input parameter
  ##
  def __init__(self, path:Path = None) -> None:
    if path is None:
      print("WARNING: invalid input, will use default configuration")
      path = DEFAULT_BASE_CONFIG_PATH
    self.CONFIG_PATH = path

##
## >>============================= abstract method =============================>>
##
  ##
  ## Generate download config based on base configuration
  ##
  @abstractmethod
  def construct_aggregation_class(self):
    ##
    ## construct user config
    ##
    self.config = BaseConfig(self.CONFIG_PATH)

    self.header = Header(Path(self.config.header_config_path))
    ##
    ## construct target config
    ##
    self.login = Login(self.login_config_path)

  ##
  ## Dump downloader configuration
  ##
  @abstractmethod
  def dump_config(self):

    ##
    ## Dump extension configuration
    ##
    self.config.dump_config()
    self.header.dump_header()
    self.login.dump_config()

  ##
  ## Common download interface
  ##
  @abstractmethod
  def run(self, params:None = ...)->None:
    pass
##
## >>============================= sub class method =============================>>
##

##
## parse str to dict
## {"k":"v","k":"", ... ,"k":"{"k":"v"}"}
##
def parse_str_to_dict(source:str=None)->dict:
  ##
  ## match "{", "}"
  ##
  start = int()
  end = int()
  for index in range(len(source)):
    
    ch = source[index]
    ##
    ## exit
    ##
    if ch == '}':
      end = index
      break

    ##
    ## start char
    ##
    if ch == '{':
      start = index
    else:
      pass
  '''
  if source[0] == "{":
    if source[-1] != "}":
      raise ValueError
    else:
      element_list = list()
      ##
      ## loop list
      ##
      for item in element_list:
        pass
  else:
    ##
    ## deal
    ##
    pass
  '''

# '''
if __name__ == "__main__":
  downloader = Downloader()
  for url in downloader.download_url_list:
    stream_url = downloader.get_douyin_live_download_stream(url)
    if stream_url is None:
      continue
    print(downloader.live_stream_name)

  print("all live download completed!")
# '''