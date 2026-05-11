##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from logging import debug, info, warning, error

## <<Extension>>

## <<Third-Part>>
from backend.src.database.social_media_stream_database import SocialMediaStreamDataBase
from backend.src.base.log                              import get_logger

class FavoriteOwnerTable(SocialMediaStreamDataBase):
##
## >>============================= attribute =============================>>
##
  __FAVORITE_OWNER_TABLE_NAME  = 'favorite_owner'
  __FAVORITE_OWNER_TABLE_TITLE = ['owner_user_id', 'platform']
  __FAVORITE_OWNER_TABLE_TUPLE = {item:None for item in __FAVORITE_OWNER_TABLE_TITLE}
##
## favorite owner table header
## +---------------+----------+-------+
## | owner_user_id | platform | score |
## +---------------+----------+-------+
##

##
## >>============================= private method =============================>>
##
  def __init__(self, host:str, user:str, passwd:str, database:str):
    if hasattr(self, '_initialized') and self._initialized:
        return
    super().__init__(host, user, passwd, database)
    self._initialized = True

##
## >>============================= abstract method =============================>>
##

##
## >>============================= sub class method =============================>>
##