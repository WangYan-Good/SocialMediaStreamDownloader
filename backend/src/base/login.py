##>> test
##<< test

##<<Base>>
from abc import ABC, abstractmethod
from copy import deepcopy

##<<Third-part>>
from backend.src.library.loglib import get_logger
from backend.src.library.safe_diagnostics import config_diagnostic

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
      ##
      ## A proxy mapping holds the url - credentials included, when one is
      ## configured that way - and a failure message quotes it back.
      ##
      get_logger().error(
        config_diagnostic(
          "config_apply_failed", section="proxies", error=e, state=False
        )
      )

  ##
  ## get proxies in dict
  ##
  def get_proxies_dict(self)->dict:
    return self.__proxies

  ##
  ## Dump configuration
  ##
  ##
  ## Counted, never listed: a proxy url can carry a user and a password.
  ##
  def dump_config(self):
    get_logger().info(
      config_diagnostic(
        "config_dumped",
        section="proxies",
        total=len(self.__proxies) if isinstance(self.__proxies, dict) else 0,
      )
    )

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
      get_logger().error(
        config_diagnostic(
          "config_apply_failed", section="login", error=e, state=False
        )
      )

  ##
  ## Dump configuration
  ##
  ##
  ## Deliberately dumps nothing.
  ##
  ## The login section holds ``msToken`` and the signing material beside it.
  ## What a diagnostic can honestly say is that a dump was asked for and how
  ## many entries the section had.
  ##
  @abstractmethod
  def dump_config(self):
    get_logger().info(
      config_diagnostic(
        "config_dumped",
        section="login",
        total=len(self.__login) if isinstance(self.__login, dict) else 0,
      )
    )
    self.proxies.dump_config()
