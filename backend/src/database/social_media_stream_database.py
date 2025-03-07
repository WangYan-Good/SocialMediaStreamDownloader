##<<Base>>
from abc import ABC
from logging import error, info

## <<Extension>>
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
def test_search_sec_user_id(live_share_url:str):
  sql = '''
          SELECT sec_user_id
          FROM share_url
          WHERE live_share_url = "{}";
        '''.format(live_share_url)
  db = SocialMediaStreamDataBase(host='127.0.0.1', user='admin', passwd='admin', database='social_media_stream_downloader')
  cursor = db.get_db_connector().cursor()
  print(sql)
  cursor.execute(sql)
  result = cursor.fetchall()
  print(result)

##
## test: insert owner id into owner_liked table
##
def test_insert_owner_into_liked_table(owner_user_id:str, platform:str):
  try:
    sql = '''
            insert into owner_liked (owner_user_id, platform) values ("{}", "{}");
          '''.format(owner_user_id, platform)
    db = SocialMediaStreamDataBase(host='127.0.0.1', user='admin', passwd='admin', database='social_media_stream_downloader')
    connector = db.get_db_connector()
    cursor = connector.cursor()
    print(sql)
    cursor.execute(sql)
    connector.commit()
    info("insert {} into liked table succeed!")
  except Exception as e:
    error(e)

##
## test: search liked owner nickname
##    
def test_search_nickname_from_liked_table(owner_user_id:str):
  pass

if __name__ == "__main__":
  # test_search_sec_user_id("https://v.douyin.com/ikRBs7Sy/")
  test_insert_owner_into_liked_table("2661232450234647", "douyin")