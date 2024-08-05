##>> test
##<< test

##<<Base>>
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path

##<<Extension>>
import yaml as yml

##<<Third-part>>
DEFAULT_BASE_CONFIG_PATH = "config/douyin/login.yml"

class Proxies(ABC):

  __proxies = None

  ##
  ## Set proxies
  ##
  def set_proxies(self, proxies:dict = None):
    if proxies is None:
      print("ERROR: Invalid proxies!")
      return
    
    try:
      self.__proxies = proxies.copy()
      self.__dict__.update(proxies)
    except Exception as e:
      print("ERROR: Set proxies failed {}".format(e))

  ##
  ## get proxies in dict
  ##
  def get_proxies_dict(self)->dict:
    return self.__proxies

  ##
  ## Dump configuration
  ##
  def dump_config(self):
    print("Proxies configuration:")
    for key, value in self.__proxies.items():
      print("\t{}: {}".format(key, value))

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
  def __init__(self, path: Path|str = None):
    if path is None:
      print("WRANNING: Invalid input path, will use default path!")
      path = DEFAULT_BASE_CONFIG_PATH
    
    ##
    ## Parse configuration file
    ##
    if isinstance(path, str) is True:
      path = Path(path)
    try:
      self.__login = self.parse_config(path)
      self.__dict__.update(self.__login)
    except Exception as e:
      print("ERROR: Login init failed {}".format(e))
  ##
  ## Parse and genearte download config
  ##
  def parse_config(self, path:Path = None)->dict:
    if path is None:
      print ("ERROR: Invalid configuration path!")
      return
    
    try:
      
      ##
      ## read config file
      ##
      base_config = yml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as e:
      print("ERROR: Parse configuration failed: {}".format(e))
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
      print("ERROR: Construct aggregation class failed {}".format(e))

  ##
  ## Dump configuration
  ##
  @abstractmethod
  def dump_config(self):
    print("Login configuration:")
    for key, value in self.__login.items():
      print("\t{}: {}".format(key, value))
    self.proxies.dump_config()