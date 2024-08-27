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
from src.library.baselib import get_dict_attr, set_dict_attr, save_dict_as_file, output_dict, load_yml

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
## >>============================= attribute =============================>>
##
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
  _base_config_save_path   = None

  ##
  ## The part of extension
  ##
  __config                 = dict()
##
## >>============================= private method =============================>>
##
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
      self.__config = load_yml(Path(self.BASE_CONFIG_FILE))
    except Exception as e:
      print("ERROR: Parse base configuration failed! {}".format(e))
      return None

    try:
      ##
      ## Construct extension config path
      ##
      self.base_config_directory     = self.WORK_SPACE_PATH + "/" + get_dict_attr(self.__config,"$.config_directory")
      self.platform_config_path      = self.WORK_SPACE_PATH + "/" + get_dict_attr(self.__config,"$.config_directory") + "/" + get_dict_attr(self.__config,"$.stream_platform")
      self.header_config_path        = self.platform_config_path + "/" + get_dict_attr(self.__config,"$.headers_file")
      self.download_config_path      = self.platform_config_path + "/" + get_dict_attr(self.__config,"$.download_file")
      self.build_path                = self.WORK_SPACE_PATH + "/" + get_dict_attr(self.__config,"$.config_directory") + "/" + get_dict_attr(self.__config,"$.build_directory")
      self._base_config_save_path    = self.build_path + "/" + "base_config.yml"

      ##
      ## Construct config dict
      ##
      set_dict_attr(self.__config, "$.base_config_directory", self.base_config_directory)
      set_dict_attr(self.__config, "$.platform_config_path",  self.platform_config_path)
      set_dict_attr(self.__config, "$.header_config_path",    self.header_config_path)
      set_dict_attr(self.__config, "$.download_config_path",  self.download_config_path)
      set_dict_attr(self.__config, "$.build_path",            self.build_path)
      set_dict_attr(self.__config, "$.base_config_save_path", self._base_config_save_path)

      ##
      ## Construct configuration
      ##
      self.__dict__.update(self.__config)
    except Exception as e:
      print("ERROR: Base config init failed! {}".format(e))
      raise e
    print("INFO: base config initialize complete!")

##
## >>============================= abstract method =============================>>
##
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
    output_dict(self.to_dict())

  ##
  ## get config dict attr
  ##
  @abstractmethod
  def get_config_dict_attr(self, attr:str=None):
    try:
      get_dict_attr(self.to_dict(), attr)
    except Exception as e:
      print("ERROR: get base config attr({}) failed".format(attr))
      raise e

  ##
  ## set config dict
  ##
  @abstractmethod
  def set_config_dict_attr(self, attr:str=None, value:any=None):
    set_dict_attr(self.to_dict(), attr, value)

##
## >>============================= sub class method =============================>>
##
  ##
  ## Save config
  ##
  def save_config(self, output:Path = None):
    if output is None:
      output = self._base_config_save_path
      print("WARNNING: save base config in default path")
    save_dict_as_file(self.to_dict(), output)