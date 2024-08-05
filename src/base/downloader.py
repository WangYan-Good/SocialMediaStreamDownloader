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
from src.base.config import BaseConfig, DEFAULT_BASE_CONFIG_PATH
from src.base.header import Header
from src.base.login  import Login

##
## Defination save file name
##
URL_RESPONSE_PATH = ""

class Downloader(ABC):

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
  ## Listener
  ##
  listener                        = None

  ##
  ## TODO: config path as input parameter
  ##
  def __init__(self, path:Path = None) -> None:
    if path is None:
      print("WARNNING: Invalid input, will use default configuration.")
      path = DEFAULT_BASE_CONFIG_PATH
    self.CONFIG_PATH = path

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