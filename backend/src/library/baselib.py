##>>Test
import os
import sys
sys.path.append(os.getcwd())
##<<Test

##<<Base>>
import os
import re
from pathlib import Path

##<<Extension>>
import yaml as yml

##<<Third-part>>
from backend.src.library.loglib import get_logger

try:
  from dotenv import load_dotenv
except ImportError:
  load_dotenv = None

_DOTENV_LOADED = False
_ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-(.*?))?\}")

def load_env_file() -> None:
  global _DOTENV_LOADED
  if _DOTENV_LOADED:
    return
  if load_dotenv is not None:
    load_dotenv()
  _DOTENV_LOADED = True

def _coerce_env_value(value: str):
  lowered = value.lower()
  if lowered == "true":
    return True
  if lowered == "false":
    return False
  if lowered in ("none", "null"):
    return None
  try:
    return int(value)
  except ValueError:
    return value

def replace_env_variables(source):
  if isinstance(source, dict):
    return {key: replace_env_variables(value) for key, value in source.items()}

  if isinstance(source, list):
    return [replace_env_variables(item) for item in source]

  if not isinstance(source, str):
    return source

  full_match = _ENV_PATTERN.fullmatch(source)
  if full_match:
    env_name, default_value = full_match.groups()
    value = os.getenv(env_name, default_value)
    if value is None:
      return source
    return _coerce_env_value(value)

  def _replace(match):
    env_name, default_value = match.groups()
    value = os.getenv(env_name, default_value)
    return match.group(0) if value is None else value

  return _ENV_PATTERN.sub(_replace, source)

##
## get dict attribute
##
def get_dict_attr(source:dict=None, attr:str=None)->any:
  if attr is None:
    raise ValueError
  if source is None:
    return None
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
    if isinstance(target, dict) is False:
      return None
    target = target.get(item)
    if target is None:
      return None
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
##
def output_dict(source:dict=None, tab:int=1):
  """Print data using YAML-like indentation.

  - Uses two spaces per `tab` level.
  - Prints scalars inline (`key: value`), nested dicts/lists as blocks.
  """
  indent = "  " * tab
  if isinstance(source, dict):
    for k, v in source.items():
      if isinstance(v, (dict, list, tuple)):
        print(f"{indent}{k}:")
        output_dict(v, tab+1)
      else:
        if v is None:
          val = "null"
        elif isinstance(v, bool):
          val = "true" if v else "false"
        else:
          val = v
        print(f"{indent}{k}: {val}")
  elif isinstance(source, (list, tuple)):
    for item in source:
      if isinstance(item, (dict, list, tuple)):
        print(f"{indent}-")
        output_dict(item, tab+1)
      else:
        if item is None:
          val = "null"
        elif isinstance(item, bool):
          val = "true" if item else "false"
        else:
          val = item
        print(f"{indent}- {val}")
  else:
    if source is None:
      val = "null"
    elif isinstance(source, bool):
      val = "true" if source else "false"
    else:
      val = source
    print(f"{indent}{val}")

##
## save dict as file
##
def save_dict_as_file(source:dict=None, save_path:Path = None, allow_unicode:bool = True):
    if source is None or save_path is None:
      get_logger().error("Invalid base config input")
      if save_path is not None:
        get_logger().error("{} save failed".format(save_path))
      raise ValueError

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'w', encoding="utf-8") as f:
      yml.safe_dump(source, f, sort_keys=False, allow_unicode=allow_unicode)

##
## load yml file
##
def load_yml(path:Path=None)->dict:
  if path is None:
    get_logger().error("invalid yaml path!")
    raise ValueError
  if isinstance(path, str):
    path = Path(path)
  
  try:      
    load_env_file()
    ##
    ## Read config file
    ##
    config = yml.safe_load(path.read_text(encoding="utf-8"))
    config = replace_env_variables(config)
  except Exception as e:
    get_logger().error("load yaml file failed: {}".format(e))
    raise e
  return config
