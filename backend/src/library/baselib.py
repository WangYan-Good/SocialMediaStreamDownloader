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
    target = target.get(item)
  return target

##
## set config dict
##
def set_dict_attr(source: dict = None, attr: str = None, value: any = None, force: bool = False):
    if source is None or attr is None:
        get_logger().error("Invalid source or attribute")
        raise ValueError
    path = attr.split(".")
    if path[0] != "$":
        get_logger().error("Attribute path must start with '$'")
        raise ValueError

    target = source
    for key in path[1:-1]:
        if key not in target or not isinstance(target[key], dict):
            if force:
                target[key] = {}
            else:
                get_logger().error(f"Missing intermediate key '{key}' in path and force=False")
                raise KeyError(f"Missing intermediate key '{key}' in path")
        target = target[key]
    # target[path[-1]] = value
    target.update({path[-1]:value})

##
## format output dict
## TBD
##
def output_dict(source:dict=None, tab:int=1):
  if isinstance(source, dict):
    if len(source) > 1: print()
    for k,v in source.items():
      # get_logger().info("{}{}:".format("\t"*tab,k))
      print("{}{}:".format("\t"*tab,k))
      output_dict(v, tab+1)
  elif isinstance(source, list) or isinstance(source, tuple):
    for item in source:
      output_dict(item, tab+1)
  else:
    # get_logger().info("{}".format(source))
    print(f"{"\t"*tab}{source}")

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