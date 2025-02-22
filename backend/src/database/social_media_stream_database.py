##<<Base>>
from abc import ABC, abstractmethod
from typing import Any
import pymysql

class SocialMediaStreamDataBase(ABC):
##
## >>============================= attribute =============================>>
##
  __connector = None

##
## >>============================= private method =============================>>
##
  def __init__(self, host:str, user:str, passwd:str, database:str) -> None:
    try:
      ##
      ## connect database
      ##
      self.__connector = pymysql.connect(host=host, user=user, passwd=passwd, db=database)
      print ("INFO: connect database {} success".format(database))
    except Exception as e:
      print ("ERROR: connect database {} fail".format(database))
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
    return self.__connector

  ##
  ## database commit
  ##
  def database_commit(self):
    try:
      self.__connector.commit()
      print("INFO: database commit success!")
    except Exception as e:
      print("ERROR: database commit failed {} !".format(e))
      raise e
    return

  ##
  ## close database connector
  ##
  def close(self):
    try:
      self.__connector.close()
      print ("INFO: close database success")
    except Exception as e:
      print ("ERROR: database instance connect is not created")
      raise e

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