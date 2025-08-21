##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Third-Part>>
from backend.src.database.social_media_stream_database                import SocialMediaStreamDataBase
from backend.src.database.table.social_media_stream_db_table          import SocialMediaStreamDataTable

##
## data.room.owner.badge_image_list
## data.user.badge_image_list
##
## +-------------------+------------------+------+-----+---------+-------+--------------------------------------------+---------------------------+
## | Field             | Type             | Null | Key | Default | Extra | Topology                                   | Comment                   |
## +-------------------+------------------+------+-----+---------+-------+--------------------------------------------+---------------------------+
## | badge_image_index | unsigned int     | NO   | PRI |         |       |                                            | 勋章图片索引               |
## | version           | varchar(20)      |      |     | NULL    |       |                                            |                           |
## | uri               | text             |      |     | NULL    |       | "$.data.room.owner.badge_image_list.x.uri" | 统一资源识别符             |
## +-------------------+------------------+------+-----+---------+-------+--------------------------------------------+---------------------------+
##
class BadgeImageTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __BADGE_IMAGE_TABLE_NAME       = 'badge_image'
  __BADGE_IMAGE_TABLE_HEADER     = ['uri', 'version', 'badge_image_index']
  __BADGE_IMAGE_TABLE_PRI_KEY    = ['badge_image_index']
  __BADGE_IMAGE_TABLE_TUPLE      = {item:None for item in __BADGE_IMAGE_TABLE_HEADER}
  __SQL_CREATE_BADGE_IMAGE_TABLE = '''
                                   CREATE TABLE IF NOT EXISTS {} (
                                     badge_image_index  int          NOT NULL,
                                     version            varchar(20)  DEFAULT NULL,
                                     uri                text         DEFAULT NULL,
                                     PRIMARY KEY (badge_image_index)
                                   )
                                   '''.format(__BADGE_IMAGE_TABLE_NAME)
  __SQL_DROP_BADGE_IMAGE_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__BADGE_IMAGE_TABLE_NAME)

##
## >>============================= private method =============================>>
##
  ##
  ## singleton pattern
  ##
  def __new__(cls, *args, **kwargs):
    return super().__new__(cls, *args, **kwargs)

  ##
  ## init method
  ##
  def __init__(self, db_instance:SocialMediaStreamDataBase = None) -> None:
    super().__init__(db_instance)

##
## >>============================= abstract method =============================>>
##
  ##
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__BADGE_IMAGE_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__BADGE_IMAGE_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__BADGE_IMAGE_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__BADGE_IMAGE_TABLE_PRI_KEY

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_BADGE_IMAGE_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_BADGE_IMAGE_TABLE


class PayGradeIconTable(SocialMediaStreamDataTable):
  pass