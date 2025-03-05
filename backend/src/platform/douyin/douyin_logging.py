##<<Base>>
from pathlib import Path

##<<Extension>>

##<<Third-part>>
from backend.src.base.logging import BaseLogging

class DouyinLogger(BaseLogging):
##
## >>============================= attribute =============================>>
##

##
## >>============================= private method =============================>>
##
  def __init__(self) -> None:
    ##
    ## enable log
    ##
    self.enable()

##
## >>============================= abstract method =============================>>
##
  
##
## >>============================= sub class method =============================>>
##

  def set_log_save_path(self, path:Path):
    pass
  
  def set_log_format(self):
    pass

##
## >>================================ test method ===============================>>
##

##
## >>================================ main method ===============================>>
##