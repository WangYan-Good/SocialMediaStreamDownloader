##>> test
##<< test

##<<Base>>
from abc import ABC, abstractmethod
from copy import deepcopy

##<<Extension>>

##<<Third-part>>

##
## Defination save file name
##
URL_RESPONSE_PATH = ""

class Downloader(ABC):
##
## >>============================= attribute =============================>>
##
  ##
  ## Downloader default configuration
  ##
  CONFIG_PATH                      = ""

  ##
  ## Config
  ##
  config                           = None

  ##
  ## Login
  ##
  login                            = None

  ##
  ## Header
  ##
  header                           = None

  ##
  ## API
  ##
  API                              = None

  ##
  ## Listener
  ##
  listener                        = None

##
## >>============================= private method =============================>>
##
  ##
  ## TODO: config path as input parameter
  ##
  def __init__(self, download_config: dict) -> None:
    if not isinstance(download_config, dict):
      raise ValueError("$.download must be a mapping")
    self.download_config = deepcopy(download_config)

##
## >>============================= abstract method =============================>>
##
  ##
  ## Generate download config based on base configuration
  ##
  @abstractmethod
  def construct_aggregation_class(self, config: dict):
    raise NotImplementedError

  ##
  ## Dump downloader configuration
  ##
  @abstractmethod
  def dump_config(self):

    ##
    ## Dump extension configuration
    ##
    pass

  ##
  ## Common download interface
  ##
  @abstractmethod
  def run(self, params:None = ...)->None:
    pass
##
## >>============================= sub class method =============================>>
##

##
## parse str to dict
## {"k":"v","k":"", ... ,"k":"{"k":"v"}"}
##
def parse_str_to_dict(source:str=None)->dict:
  ##
  ## match "{", "}"
  ##
  start = int()
  end = int()
  for index in range(len(source)):
    
    ch = source[index]
    ##
    ## exit
    ##
    if ch == '}':
      end = index
      break

    ##
    ## start char
    ##
    if ch == '{':
      start = index
    else:
      pass
  '''
  if source[0] == "{":
    if source[-1] != "}":
      raise ValueError
    else:
      element_list = list()
      ##
      ## loop list
      ##
      for item in element_list:
        pass
  else:
    ##
    ## deal
    ##
    pass
  '''
