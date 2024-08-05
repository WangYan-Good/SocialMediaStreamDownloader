## <<Base>>
import os
from pathlib import Path
import sys

SRC_WORK_SPACE = os.path.dirname(sys.path[0])
sys.path.append(os.path.join(SRC_WORK_SPACE))
sys.path.append(os.getcwd())

## <<Extension>>
import yaml as yml

## <<Third-part>>
from src.base.config import BaseConfig, DEFAULT_BASE_CONFIG_PATH

DOUYIN_POST_CONFIG_PATH = "config/douyin/post.yml"

'''
DouyinPostConfig->BaseConfig:
  Attribute:
    share_url
    sec_user_id
    nickname
    device_platform
    aid
    channel
    pc_client_type
    version_code
    version_name
    cookie_enabled
    screen_width
    screen_height
    browser_language
    browser_platform
    browser_name
    browser_version
    browser_online
    engine_name
    engine_version
    os_name
    os_version
    cpu_core_num
    device_memory
    platform
    downlink
    effective_type
    round_trip_time
    max_cursor
    page_counts
    max_counts

  Operation:
    to_dict
    dump_config
'''

class DouyinPostConfig(BaseConfig):
  ##
  ## Declare and define default value
  ##
  device_platform    = "webapp"
  aid                = "6383"
  channel            = "channel_pc_web"
  pc_client_type     = 1
  version_code       = "190500"
  version_name       = "19.5.0"
  cookie_enabled     = "true"
  screen_width       = 1920
  screen_height      = 1080
  browser_language   = "zh-CN"
  browser_platform   = "Win32"
  browser_name       = "Edge"
  browser_version    = "122.0.0.0"
  browser_online     = "true"
  engine_name        = "Blink"
  engine_version     = "122.0.0.0"
  os_name            = "Windows"
  os_version         = "10"
  cpu_core_num       = 12
  device_memory      = 8
  platform           = "PC"
  downlink           = 10
  effective_type     = "4g"
  round_trip_time    = 100

  ##
  ## TODO
  ##
  max_cursor         = 0
  page_counts        = 20
  max_counts         = 0

  ##
  ## The part of extension
  ##
  __douyin_post_config_dict = dict()

  def __init__(self, path:Path = None) -> None:
    if path is None:
      print("WARNNING: Invalid input, will use default configuration!")
      path = DOUYIN_POST_CONFIG_PATH
    super().__init__(path=DEFAULT_BASE_CONFIG_PATH)
    self.__parse_config(Path(path))


  ##
  ## parse and genearte douyin post download config
  ##
  def __parse_config(self, path:Path = None)->dict:
    if path is None:
      print ("ERROR: invalide configuration path!")
    
    try:
      
      ##
      ## read config file
      ##
      self.__douyin_post_config_dict = yml.safe_load(path.read_text(encoding="utf-8"))

      ##
      ## Construct configuration
      ##
      self.device_platform = self.__douyin_post_config_dict.get("device_platform", "webapp")
      self.aid             = self.__douyin_post_config_dict.get("aid", "6383")
      self.channel         = self.__douyin_post_config_dict.get("channel", "channel_pc_web")
      self.pc_client_type  = self.__douyin_post_config_dict.get("pc_client_type", 1)
      self.version_code    = self.__douyin_post_config_dict.get("version_code", "190500")
      self.version_name    = self.__douyin_post_config_dict.get("version_name", "19.5.0")
      self.cookie_enabled  = self.__douyin_post_config_dict.get("cookie_enabled", "true")
      self.screen_width    = self.__douyin_post_config_dict.get("screen_width", 1920)
      self.screen_height   = self.__douyin_post_config_dict.get("screen_height", 1080)
      self.browser_language= self.__douyin_post_config_dict.get("browser_language", "zh-CN")
      self.browser_platform= self.__douyin_post_config_dict.get("browser_platform", "Win32")
      self.browser_name    = self.__douyin_post_config_dict.get("browser_name", "Edge")
      self.browser_version = self.__douyin_post_config_dict.get("browser_version", "122.0.0.0")
      self.browser_online  = self.__douyin_post_config_dict.get("browser_online", "true")
      self.engine_name     = self.__douyin_post_config_dict.get("engine_name", "Blink")
      self.engine_version  = self.__douyin_post_config_dict.get("engine_version", "122.0.0.0")
      self.os_name         = self.__douyin_post_config_dict.get("os_name", "Windows")
      self.os_version      = self.__douyin_post_config_dict.get("os_version", "10")
      self.cpu_core_num    = self.__douyin_post_config_dict.get("cpu_core_num", 12)
      self.device_memory   = self.__douyin_post_config_dict.get("device_memory", 8)
      self.platform        = self.__douyin_post_config_dict.get("platform", "PC")
      self.downlink        = self.__douyin_post_config_dict.get("downlink", 10)
      self.effective_type  = self.__douyin_post_config_dict.get("effective_type", "4g")
      self.round_trip_time = self.__douyin_post_config_dict.get("round_trip_time", 100)

      ##
      ## TODO
      ##
      self.max_cursor      = self.__douyin_post_config_dict.get("max_cursor", 0)
      self.page_counts     = self.__douyin_post_config_dict.get("page_counts", 20)
      self.max_counts      = self.__douyin_post_config_dict.get("max_counts", 0)
    except Exception as e:
      print("ERROR: parse configuration failed = {}".format(e))
    return self.__douyin_post_config_dict

  ##
  ## Transform config to dict
  ##
  def to_dict(self) -> dict:
    ##
    ## Loop super's content
    ##
    config_dict = dict
    super_dict = super().to_dict()
    for key, value in super_dict.items():
      config_dict[key] = value
    
    ##
    ## Loop sub-class' content
    ##
    for key, value in self.__douyin_post_config_dict:
      config_dict[key] = value
    
    return config_dict
    


  def dump_config(self, out_putlog_file:Path = False):
    super().dump_config(out_putlog_file)
    if out_putlog_file is True:
      pass

    print("Douyin POST configuration:")
    for key, value in self.__douyin_post_config_dict.items():
      print("\t{k}: {v}".format(k=key, v=value))
'''
    print("\tdevice platform: {}".format(self.device_platform))
    print("\taid: {}".format(self.aid))
    print("\tchannel: {}".format(self.channel))
    print("\tpc client type: {}".format(self.pc_client_type))
    print("\tversion code: {}".format(self.version_code))
    print("\tversion name: {}".format(self.version_name))
    print("\tcookie enabled: {}".format(self.cookie_enabled))
    print("\tscreen width: {}".format(self.screen_width))
    print("\tscreen height: {}".format(self.screen_height))
    print("\tbrowser language: {}".format(self.browser_language))
    print("\tbrowser platform: {}".format(self.browser_platform))
    print("\tbrowser name:{}".format(self.browser_name))
    print("\tbrowser version:{}".format(self.browser_version))
    print("\tbrowser online:{}".format(self.browser_online))
    print("\tengine name:{}".format(self.engine_name))
    print("\tengine version:{}".format(self.engine_version))
    print("\tos name:{}".format(self.os_name))
    print("\tos version:{}".format(self.os_version))
    print("\tcpu core num:{}".format(self.cpu_core_num))
    print("\tdevice memory:{}".format(self.device_memory))
    print("\tplatform:{}".format(self.platform))
    print("\tdownlink:{}".format(self.downlink))
    print("\teffective type:{}".format(self.effective_type))
    print("\tround trip time:{}".format(self.round_trip_time))
    print("\tmax cursor:{}".format(self.max_cursor))
    print("\tmax counts:{}".format(self.max_counts))
    print("\tpage counts:{}".format(self.page_counts))
'''    

if __name__ == "__main__":
  post_config = DouyinPostConfig()
  post_config.dump_config()
