##>> test
##<< test

##<<Base>>
from abc import ABC, abstractmethod
from pathlib import Path

##<<Extension>>
import yaml

##<<Third-part>>

DEFAULT_REFERER = "https://www.douyin.com/"
DEFAULT_USERR_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"

class Header(ABC):

  ##
  ## Defination and Initialize default
  ##
  __header_dict = dict()

  ##
  ## Initialize header and constrcut
  ##
  def __init__(self, header_path:Path|str = None) -> None:
    if header_path is None:
      print("WARNNING: Invalide input, will use default config")
    
    try:
      if isinstance(header_path, str) is True:
        header_path = Path(header_path)
      ##
      ## Load header configuration
      ##
      if header_path is not None:
        header_dict = self.parse_header(header_path)
        print("INFO: header initialized succeed!")
      else:
        header_dict.get("Referer", DEFAULT_REFERER)
        header_dict.get("User-Agent", DEFAULT_USERR_AGENT)
      
      self.__header_dict = header_dict.copy()

      ##
      ## Transform dict to attribute
      ##
      self.__dict__.update(self.__header_dict)
      # print(dir(self))
      
    except Exception as e:
      print("ERROR: Header init failed: {}".format(e))
    return None
    
  ##
  ## Parse header file
  ##
  def parse_header(self, header_path:Path = None)->dict:
    if header_path is None:
      print("ERROR: Invalid input")
      return None
    
    try:
      ##
      ## Load header load
      ##
      header_dict = yaml.safe_load(header_path.read_text(encoding="utf-8"))
    except Exception as e:
      print(e)
      return None
    
    return header_dict
  
  def to_dict(self):
    return self.__header_dict

  ##
  ## Dump header config
  ##
  def dump_header(self):
    print("Header configuration:")
    for key, value in self.__header_dict.items():
      print("\t{}: {}".format(key, value))

if __name__ == "__main__":
  Header(Path("config/douyin/headers.yml")).dump_header()