##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

##<<Third-Part>>
from backend.src.base.config import BaseConfig

def init_config():
  BaseConfig()