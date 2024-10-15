## <<Base>>
import os
from pathlib import Path
import sys
sys.path.append(os.getcwd())

## <<Extension>>
import yaml as yml

## <<Third-part>>
from src.library.baselib import output_dict, save_dict_as_file, set_dict_attr, get_dict_attr, load_yml
from src.base.config import DEFAULT_BASE_CONFIG_PATH
from src.platform.douyin.douyin_config import DouyinConfig

##TODO remove
from verify_fp_manager import VerifyFpManager as VFM

class DouyinLiveConfig(DouyinConfig):
##
## >>============================= attribute =============================>>
##
  _douyin_live_config_save_path = None
  ##
  ## The part of extension
  ##
  __config                 = dict()

##
## >>============================= private method =============================>>
##
  ##
  ## Initialize douyin live config
  ##
  def __init__(self, path: Path = None):
    if path is None:
      print("WARNING: invalid input, will use default config path")
      path = DEFAULT_BASE_CONFIG_PATH
    super().__init__(path)

    ##
    ## Parse live config
    ##
    self.__config = super().to_dict()
    self.__config.update(load_yml(Path(self.live_config_path)))
    
    ##
    ## Transform dict to attribute
    ##
    self.__dict__.update(self.__config)

    ##
    ## constructure douyin live config
    ##
    self._douyin_live_config_save_path = self.build_path + "/" + self.stream_platform + "/" + "douyin_live_config.yml"
    self.set_config_dict_attr("$.douyin_live_config_save_path", self._douyin_live_config_save_path)

##
## >>============================= abstract method =============================>>
##
  ##
  ## Transform config to dict
  ##
  def to_dict(self) -> dict:
    return self.__config
  
  ##
  ##  Dump config
  ##
  def dump_config(self):
    # super().dump_config()

    print("Douyin live config:")
    output_dict(self.__config)

  ##
  ## get config dict attr
  ##
  def get_config_dict_attr(self, attr: str = None):
    value = None
    try:
      value = get_dict_attr(self.__config, attr)
    except KeyError:
      value = super().get_config_dict_attr(attr)
    except Exception as e:
      print("ERROR: get douyin live config attr({}) failed".format(attr))
      raise e
    return value


  ##
  ## set config dict
  ##
  def set_config_dict_attr(self, attr: str = None, value: any = None):
    set_dict_attr(self.__config, attr, value)

##
## >>============================= sub class method =============================>>
##
  ##
  ## Update verify Fp Manager
  ##
  def update_verifyFp(self):
    ##
    ## update attribute
    ##
    if self.get_config_dict_attr("$.login") is True:
      pass
    else:
      self.verifyFp = VFM.gen_verify_fp()
    
      ##
      ## update dict
      ##
      self.set_config_dict_attr("$.params_no_login.verifyFp", self.verifyFp)
      return self.verifyFp
##
## >>============================= override super method =============================>>
##
  ##
  ## Save config
  ##
  def save_config(self, output: Path = None):
    ##
    ## save super config
    ##
    super().save_config(output)
    
    ##
    ## save sub class config
    ##
    if output is None:
      print("WARNING: save douyin live config in default path")
      output = self._douyin_live_config_save_path
    save_dict_as_file(self.__config, output)

if __name__ == "__main__":
  live_config = DouyinLiveConfig()
  live_config.save_config()
  live_config.dump_config()