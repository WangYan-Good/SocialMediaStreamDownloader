## <<Base>>
import os
from pathlib import Path
import sys

# SRC_WORK_SPACE = os.path.dirname(sys.path[0])
# sys.path.append(os.path.join(SRC_WORK_SPACE))
sys.path.append(os.getcwd())

## <<Extension>>
import yaml as yml

## <<Third-part>>
from backend.src.platform.douyin.douyin_config import DouyinConfig, DEFAULT_BASE_CONFIG_PATH

## TODO remove
from verify_fp_manager import VerifyFpManager as VFM
from a_bogus import ABogus as AB

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

class DouyinPostConfig(DouyinConfig):

  ##
  ## The part of extension
  ##
  __config = dict()

  def __init__(self, path:Path = None) -> None:
    if path is None:
      print("WARNING: invalid input, will use default configuration")
      path = DEFAULT_BASE_CONFIG_PATH
    super().__init__(path=Path(path))
    self.__parse_config(Path(self.post_config_path))

  ##
  ## Update verify Fp Manager
  ##
  def update_verifyFp(self):
    ##
    ## update attribute
    ##
    if self.login is True:
      pass
    else:
      self.verifyFp = VFM.gen_verify_fp()
    
      ##
      ## update dict
      ##
      self.__config["verifyFp"] = self.verifyFp

  ##
  ## Update verify Fp Manager
  ##
  def update_fp(self):
    ##
    ## update attribute
    ##
    if self.login is True:
      pass
    else:
      self.fp = self.verifyFp
    
      ##
      ## update dict
      ##
      self.__config["fp"] = self.__config["verifyFp"]
  
  ##
  ## update a-bogus
  ##
  def update_a_bogus(self, params:dict=None):
    ## update attribute
    if self.login is True:
      pass
    else:
      self.a_bogus = AB().get_value(params, "GET")
      self.__config["a_bogus"] = self.a_bogus

  ##
  ## update count
  ##
  def update_count(self, count:int=0):
    if count == 0:
      raise ValueError
    self.count = count

  ##
  ## parse and genearte douyin post download config
  ##
  def __parse_config(self, path:Path = None)->dict:
    if path is None:
      print ("ERROR: invalid post configuration path!")
      raise FileNotFoundError
    
    try:
      
      ##
      ## read config file
      ##
      self.__config = yml.safe_load(path.read_text(encoding="utf-8"))

      ##
      ## construct configuration
      ##
      self.__dict__.update(self.__config)
    except Exception as e:
      print("ERROR: parse configuration failed = {}".format(e))
      raise e
    return self.__config

  ##
  ## update douyin post share url
  ##
  def update_post_share_url(self, param:dict = None):
    if param is None:
      print("ERROR: invalid parameter!")
      raise ValueError
    
    try:
      ##
      ## update post config
      ##
      self.share_url   = param.get("share_url", "")
      # self.sec_user_id = param.get("sec_user_id", "")
    except Exception as e:
      print("ERROR: update douyin post config failed!\n{}".format(e))
      raise e

  ##
  ## Transform config to dict
  ##
  def to_dict(self) -> dict:
    return self.__config
    
  def dump_config(self):
    ##
    ## dump super config
    ##
    super().dump_config()

    ##
    ## dump config
    ##
    print("Douyin POST configuration:")
    for key, value in self.__config.items():
      print("\t{k}: {v}".format(k=key, v=value))

if __name__ == "__main__":
  post_config = DouyinPostConfig()
  post_config.dump_config()
