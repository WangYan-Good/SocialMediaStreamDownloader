##>> test
##<< test

##<<Base>>
import os
import sys
from pathlib import Path
from abc import ABC, abstractmethod

##<<Extension>>
import yaml as yml

##<<Third-part>>

##
## Define
##
DEFAULT_BASE_CONFIG_PATH = "config/base_config.yml"

##
## Defination sbstract class
##
class BaseConfig(ABC):
  '''
  save_path: /mnt/nvme2/vedio
  max_thread: 0
  folderize: True
  config_directory: config
  stream_platform: douyin
  build_directory: build
  login: True
  save_response: True
  headers_file: headers.yml
  download_file: download.yml
  base_config_directory: /mnt/nvme/CodeSpace/OpenSource/TikTokDownload/config
  platform_config_path: /mnt/nvme/CodeSpace/OpenSource/TikTokDownload/config/douyin
  header_config_path: /mnt/nvme/CodeSpace/OpenSource/TikTokDownload/config/douyin/headers.yml
  download_config_path: /mnt/nvme/CodeSpace/OpenSource/TikTokDownload/config/douyin/download.yml
  build_path: /mnt/nvme/CodeSpace/OpenSource/TikTokDownload/config/build
  '''
  ##
  ## Declare and define default value
  ##
  WORK_SPACE_PATH          = os.getcwd()
  BASE_CONFIG_FILE         = None
  base_config_directory    = None
  platform_config_path     = None
  header_config_path       = None
  download_config_path     = None
  build_path               = None

  ##
  ## The part of extension
  ##
  __config                 = dict()

  ##
  ## Initialize base config
  ##
  def __init__(self, path:Path|str = None):
    if path is None:
      print("WARNNING: Invalide input, will use default base configuration!")
      path = DEFAULT_BASE_CONFIG_PATH

    ##
    ## Initialize base config
    ##
    if isinstance(path, str) is True:
      path = Path(path)
    self.BASE_CONFIG_FILE = path
    try:

      ##
      ## Parse configuration file
      ##
      self.__config = self.parse_config(Path(self.BASE_CONFIG_FILE))
    except Exception as e:
      print("ERROR: Parse base configuration failed! {}".format(e))
      return None

    try:
      ##
      ## Construct configuration
      ##
      self.__dict__.update(self.__config)

      ##
      ## Construct extension config path
      ##
      self.base_config_directory     = self.WORK_SPACE_PATH + "/" + self.config_directory
      self.platform_config_path      = self.WORK_SPACE_PATH + "/" + self.config_directory + "/" + self.stream_platform
      self.header_config_path        = self.platform_config_path + "/" + self.headers_file
      self.download_config_path      = self.platform_config_path + "/" + self.download_file
      self.build_path                = self.WORK_SPACE_PATH + "/" + self.config_directory + "/" + self.build_directory

      ##
      ## Construct config dict
      ##
      self.__config["base_config_directory"]     = self.base_config_directory
      self.__config["platform_config_path"]      = self.platform_config_path
      self.__config["header_config_path"]        = self.header_config_path
      self.__config["download_config_path"]      = self.download_config_path
      self.__config["build_path"]                = self.build_path
    except Exception as e:
      print("ERROR: Base config init failed! {}".format(e))

  ##
  ## parse and genearte download config
  ##
  def parse_config(self, path:Path = None)->dict:
    if path is None:
      print ("ERROR: Invalide configuration path!")
      return
    
    try:      
      ##
      ## Read config file
      ##
      config = yml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as e:
      print("ERROR: Parse configuration failed: {}".format(e))
    return config
  

  ##
  ## Transform config to dict
  ##
  @abstractmethod
  def to_dict(self)->dict:
    return self.__config

  ##
  ## Dump config
  ##
  @abstractmethod
  def dump_config(self):
    print("Base configuration:")
    for key, value in self.__config.items():
      print("\t{k}: {v}".format(k=key, v=value))
  
  ##
  ## Save config
  ##
  def save_config(self, output:Path = None):
    if output is None:
      print("ERROR: Invalid input")
      return

    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, 'w', encoding="utf-8") as f:
        yml.safe_dump(self.__config, f)
        f.close()
        print("INFO: Save file {} success!".format(output))
  
  ##
  ## regural out put
  ##
  def dict_regular_output(self, config:dict, level:int = 1):
    for k,v in config.items():
      if isinstance(v, dict):
        print("\t"*level+"{}:".format(k))
        self.dict_regular_output(config=v, level=(level+1))
      else:
        print("\t"*level+"{k}:{v}".format(k=k, v=v))
    return None