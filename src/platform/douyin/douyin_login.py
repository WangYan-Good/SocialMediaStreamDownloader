## <<Base>>
import os
import sys
sys.path.append(os.getcwd())
from pathlib import Path


## <<Extension>>

## <<Third-part>>
from src.base.login import Login, Proxies

## TODO
import f2
from f2.apps.douyin.utils import TokenManager as TM

class DouyinLogin(Login):

  __login_status = False
  
  ##
  ## Initialize Attribute & super
  ##
  def __init__(self, path: Path = None):
    ##
    ## Initialize attribute
    ##
    super().__init__(path)

    ##
    ## Initialize member
    ##
    self.construct_aggregation_class()

  ##
  ## switch login account
  ##
  def switch_login_account(self):
    pass

  ##
  ## login
  ##
  def login(self):
    self.__login_status = True
    
    ##
    ## TODO
    ##

  ##
  ## get cookie
  ##
  def get_douyin_cookie(self):
    pass

  ##
  ## update cookie
  ##
  def update_douyin_cookie(self):
    pass

  ##
  ## get maToken
  ##
  def get_douyin_msToken(self):
    pass

  ##
  ## Update msToken
  ##
  def update_douyin_msToken(self):
    ##
    ## Update attribute
    ##
    if self.__login_status is True:
      pass
    else:
      self.msToken = TM.gen_real_msToken()

      ##
      ## update dict
      ##
      self.to_dict()["msToken"] = self.msToken

  def to_dict(self) -> dict:
    return super().to_dict()
  
  def construct_aggregation_class(self) -> None:
    super().construct_aggregation_class()
  
  def dump_config(self):
    super().dump_config()

if __name__ == "__main__":
  dylogin = DouyinLogin()
  dylogin.dump_config()