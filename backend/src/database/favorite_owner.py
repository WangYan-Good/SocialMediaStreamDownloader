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
    super().__init__(host, user, passwd, database)

##
## >>============================= abstract method =============================>>
##

##
## >>============================= sub class method =============================>>
##

##
## >>================================ test method ===============================>>
##

##
## test: create a database favorite owner table
##
def test_create_favorite_owner_table():
  ##
  ## test for create a table
  ##
  try:
    db = FavoriteOwnerTable(host='192.168.1.9', user='wangyan', passwd='wuyu1998', database='social_media_stream_downloader')
    connector = db.get_db_connector()
    cursor = connector.cursor()
    sql = '''
            CREATE TABLE favorite_owner (
              owner_user_id     CHAR(200) NOT NULL PRIMARY KEY,
              platform          CHAR(20)
            )
          '''
    cursor.execute(sql)
    get_logger().info("test create database table success")
    connector.close()
  except Exception as e:
    get_logger().error("test create database table failed {}".format(e))