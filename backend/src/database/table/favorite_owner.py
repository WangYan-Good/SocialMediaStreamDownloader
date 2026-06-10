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

class FavoriteOwnerTable(SocialMediaStreamDataBase):
##
## >>============================= attribute =============================>>
##
  __FAVORITE_OWNER_TABLE_NAME     = 'favorite_owner'
  __FAVORITE_OWNER_TABLE_HEADER   = ['owner_user_id', 'platform', 'score']
  __FAVORITE_OWNER_TABLE_PRI_KEY  = ['owner_user_id', 'platform']
  __TABLE_AUTO_INCREMENT          = []
  __FAVORITE_OWNER_TABLE_TUPLE    = {item:None for item in __FAVORITE_OWNER_TABLE_HEADER}
  __SQL_CREATE_FAVORITE_OWNER_TABLE = '''
                                       CREATE TABLE IF NOT EXISTS {} (
                                         owner_user_id  VARCHAR(200)     NOT NULL,
                                         platform       VARCHAR(20)      NOT NULL,
                                         score          TINYINT UNSIGNED NOT NULL DEFAULT 0,
                                         PRIMARY KEY (owner_user_id, platform)
                                       ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                                     '''.format(__FAVORITE_OWNER_TABLE_NAME)
  __SQL_DROP_FAVORITE_OWNER_TABLE = '''
                                     DROP TABLE IF EXISTS {};
                                   '''.format(__FAVORITE_OWNER_TABLE_NAME)
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
  ##
  ## get favorite owner table name
  ##
  def get_favorite_owner_table_name(self) -> str:
    return self.__FAVORITE_OWNER_TABLE_NAME

  ##
  ## get favorite owner table header
  ##
  def get_favorite_owner_table_header(self) -> list:
    return self.__FAVORITE_OWNER_TABLE_HEADER

  ##
  ## get favorite owner table tuple
  ##
  def get_favorite_owner_table_tuple(self) -> dict:
    return self.__FAVORITE_OWNER_TABLE_TUPLE

  ##
  ## create favorite owner table
  ##
  def create_favorite_owner_table(self) -> None:
    with self.get_connection() as connector:
      with connector.cursor() as cursor:
        cursor.execute(self.__SQL_CREATE_FAVORITE_OWNER_TABLE)
        connector.commit()

  ##
  ## drop favorite owner table
  ##
  def drop_favorite_owner_table(self) -> None:
    with self.get_connection() as connector:
      with connector.cursor() as cursor:
        cursor.execute(self.__SQL_DROP_FAVORITE_OWNER_TABLE)
        connector.commit()
