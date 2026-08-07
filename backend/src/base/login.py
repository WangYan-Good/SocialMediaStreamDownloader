##>> test
##<< test

##<<Base>>
import os
import sys
from abc import ABC, abstractmethod
from copy import deepcopy
from pathlib import Path

##<<Extension>>
import yaml as yml

##<<Third-part>>
from backend.src.library.loglib import get_logger
DEFAULT_BASE_CONFIG_PATH = "config/douyin/login.yml"

class Proxies(ABC):

  __proxies = None

  ##
  ## Set proxies
  ##
  def set_proxies(self, proxies:dict = None):
    if proxies is None:
      get_logger().error("Invalid proxies!")
      return
    
    try:
      self.__proxies = proxies.copy()
      self.__dict__.update(proxies)
    except Exception as e:
      get_logger().error("Set proxies failed {}".format(e))

  ##
  ## get proxies in dict
  ##
  def get_proxies_dict(self)->dict:
    return self.__proxies

  ##
  ## Dump configuration
  ##
  def dump_config(self):
    get_logger().info("Proxies configuration:")
    for key, value in self.__proxies.items():
      get_logger().info("\t{}: {}".format(key, value))

class Login(ABC):

  ##
  ## Attribute
  ##
  proxies = None

  ##
  ## raw dict data
  ##
  __login      = None

  ##
  ## Initialize and construc class
  ##
  def __init__(self, path: Path|str|dict = None):
    if path is None:
      get_logger().warning("invalid input path, will use default path")
      path = DEFAULT_BASE_CONFIG_PATH
    
    ##
    ## Parse configuration file
    ##
    if isinstance(path, str) is True:
      path = Path(path)
    try:
      if isinstance(path, dict):
        self.__login = deepcopy(path)
      else:
        self.__login = self.parse_config(path)
      self.__dict__.update(self.__login)
    except Exception as e:
      get_logger().error("Login init failed: {}".format(e))
  ##
  ## Parse and genearte download config
  ##
  def parse_config(self, path:Path = None)->dict:
    if path is None:
      get_logger().error("Invalid configuration path!")
      return
    
    try:
      
      ##
      ## read config file
      ##
      base_config = yml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as e:
      get_logger().error("Parse configuration failed: {}".format(e))
    return base_config

  ##
  ## Return dict raw data
  ##
  @abstractmethod
  def to_dict(self)->dict:
    return self.__login

  ##
  ## Construct aggregation member
  ##
  @abstractmethod
  def construct_aggregation_class(self)->None:
    try:
      self.proxies = Proxies()
      self.proxies.set_proxies(self.__login.get("proxies", None))
    except Exception as e:
      get_logger().error("Construct aggregation class failed {}".format(e))

  ##
  ## Dump configuration
  ##
  @abstractmethod
  def dump_config(self):
    get_logger().info("Login configuration:")
    for key, value in self.__login.items():
      get_logger().info("\t{}: {}".format(key, value))
    self.proxies.dump_config()
