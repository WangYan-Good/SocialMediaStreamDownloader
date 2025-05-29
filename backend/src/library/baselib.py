##>>Test
import os
import sys
sys.path.append(os.getcwd())
##<<Test

##<<Base>>
import os
from pathlib import Path

##<<Extension>>
import yaml as yml

##<<Third-part>>
from backend.src.base.log import get_logger

##
## get dict attribute
##
def get_dict_attr(source:dict=None, attr:str=None)->any:
  if attr is None or attr is None:
    raise ValueError
  path = attr.split(sep=".")

  ##
  ## Check "$"
  ##
  if path[0] != "$":
    raise ValueError

  ##
  ## locate the attribute
  ##
  target = source
  for item in path[1:]:
    target = target[item]
  return target

##
## set config dict
##
def set_dict_attr(source:dict=None, attr:str=None, value:any=None):
  if attr is None or value is None:
    get_logger().error("Invalid header attribute or value")
    raise ValueError
  path = attr.split(sep=".")

  ##
  ## Check "$"
  ##
  if path[0] != "$":
    raise ValueError
  
  
  target = source
  ##
  ## locate the attribute
  ##
  for item in path[1:-1]:
    target = target[item] # target = self._header[a][b][c]
    if target is None:
      get_logger().error("Invalid header attribute: {}".format(attr))
      raise ValueError
  
  ##
  ## set attribute
  ##
  target[path[-1]] = value
  return

##
## format output dict
##
def output_dict(source:dict=None, tab:int=1):
  if isinstance(source, dict):
    if len(source) > 1: print()
    for k,v in source.items():
      get_logger().info("{}{}:".format("\t"*tab,k), end="")
      output_dict(v, tab+1)
  elif isinstance(source, list) or isinstance(source, tuple):
    for item in source:
      output_dict(item, tab+1)
  else:
    get_logger().info("{}".format(source))

##
## save dict as file
##
def save_dict_as_file(source:dict=None, save_path:Path = None):
    if source is None or save_path is None:
      get_logger().error("Invalid base config input")
      if save_path is not None:
        get_logger().error("{} save failed".format(save_path))
      raise ValueError

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'w', encoding="utf-8") as f:
        yml.safe_dump(source, f)
        f.close()
        get_logger().info("Save file {} success!".format(save_path))

##
## load yml file
##
def load_yml(path:Path=None)->dict:
  if path is None:
    get_logger().error("invalid yaml path!")
    raise ValueError
  
  try:      
    ##
    ## Read config file
    ##
    config = yml.safe_load(path.read_text(encoding="utf-8"))
  except Exception as e:
    get_logger().error("load yaml file failed: {}".format(e))
    raise e
  return config