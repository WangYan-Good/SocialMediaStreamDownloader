##<<Base>>
from abc import ABC, abstractmethod
from typing import Any
import pymysql

class SocialMediaStreamDataBase(ABC):
##
## >>============================= attribute =============================>>
##
  __host:str     = None
  __user:str     = None
  __passwd:str   = None
  __database:str = None
  __connector    = None

##
## >>============================= private method =============================>>
##
  def __init__(self, host:str, user:str, passwd:str, database:str) -> None:
    try:
      self.__host     = host
      self.__user     = user
      self.__passwd   = passwd
      self.__database = database
    except Exception as e:
      raise e
##
## >>============================= abstract method =============================>>
##

##
## >>============================= sub class method =============================>>
##

  ##
  ## get database connector
  ##
  def get_db_connector(self):
    try:
      ##
      ## connect database
      ##
      self.__connector = pymysql.connect(host=self.__host, user=self.__user, passwd=self.__passwd, db=self.__database)
    except Exception as e:
      print ("ERROR: connect database {} fail".format(self.__database))
      
    return self.__connector

  ##
  ## drop database table
  ##
  def drop_db_table(self, table_name:str) -> None:
    try:
      sql = '''DROP TABLE {};'''.format(table_name)
      self.get_db_connector().cursor().execute(sql)
    except Exception as e:
      print("ERROR: drop databse table {} is failed! reason: {}".format(table_name, e))
      raise e
    
##
## >>============================= override super method =============================>>
##

##
## >>================================ test method ===============================>>
##

##
## test: execute search sql
##
  def test_search_sec_user_id(self, live_share_url:str):
    sql = '''
            SELECT sec_user_id
            FROM share_url
            WHERE live_share_url = "{}";
          '''.format(live_share_url)
    cursor = self.get_db_connector().cursor()
    print(sql)
    cursor.execute(sql)
    result = cursor.fetchall()
    print(result)
    
if __name__ == "__main__":
  db = SocialMediaStreamDataBase(host='127.0.0.1', user='admin', passwd='admin', database='social_media_stream_downloader')
  db.test_search_sec_user_id("https://v.douyin.com/ikRBs7Sy/")  