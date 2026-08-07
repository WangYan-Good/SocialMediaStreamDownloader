from copy import deepcopy
from pathlib import Path

from backend.src.library.baselib import load_yml


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_EXAMPLE_PATH = PROJECT_ROOT / "docs" / "design" / "config.yml.example"


def unified_config() -> dict:
  config = deepcopy(load_yml(CONFIG_EXAMPLE_PATH))
  config["database"]["enable"] = False
  config["download"]["test_mode"] = True
  config["download"]["save_response"] = False
  config["download"]["save_error_response"] = False
  config["log"]["log_save"] = False
  config["server"]["debug_mode"] = False
  return config
