##>> test
##<< test

##<<Base>>
from abc import ABC, abstractmethod
from copy import deepcopy

##<<Third-part>>
from backend.src.library.loglib import get_logger

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
  proxies      = None

  ##
  ## raw dict data
  ##
  __login      = None

  ##
  ## Initialize and construc class
  ##
  def __init__(self, config: dict):
    if not isinstance(config, dict):
      raise ValueError("login configuration must be a mapping")
    self.__login = deepcopy(config)
    self.__dict__.update(self.__login)

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
