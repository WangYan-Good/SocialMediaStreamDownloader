## <<Base>>
import os
from pathlib import Path
import sys
sys.path.append(os.getcwd())

## <<Extension>>
import yaml as yml

## <<Third-part>>
from src.base.config import DEFAULT_BASE_CONFIG_PATH
from src.platform.douyin.douyin_config import DouyinConfig

##TODO remove
from verify_fp_manager import VerifyFpManager as VFM

class DouyinLiveConfig(DouyinConfig):

  ##
  ## The part of extension
  ##
  __config                 = dict()

  ##
  ## Initialize douyin live config
  ##
  def __init__(self, path: Path = None):
    if path is None:
      print("WARNNING: Invalid input, will use default config path")
      path = DEFAULT_BASE_CONFIG_PATH
    super().__init__(path)

    ##
    ## Parse live config
    ##
    self.__config = self.parse_config(Path(self.live_config_path))

    ##
    ## Transform dict to attribute
    ##
    self.__dict__.update(self.__config)

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
  ## Transform config to dict
  ##
  def to_dict(self) -> dict:
    return super().to_dict()
  
  ##
  ##  Dump config
  ##
  def dump_config(self):
    super().dump_config()

    print("Douyin live config:")
    for k,v in self.__config.items():
      print("\t{}: {}".format(k,v))

  ##
  ## Save config
  ##
  def save_config(self, data:dict = None, output:Path = None):
    if data is None:
      print("WARNNING: Invalid data, default save all config data")
      data = self.__dict__
    if output is None:
      print("WARNNING: Invalid input, will use default path")
      return

    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, 'w', encoding="utf-8") as f:
        yml.safe_dump(data, f)
        f.close()

if __name__ == "__main__":
  post_config = DouyinLiveConfig()
  post_config.dump_config()