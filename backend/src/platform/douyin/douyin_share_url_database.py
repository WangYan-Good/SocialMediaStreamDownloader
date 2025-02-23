##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Extension>>
import pymysql.err

## <<Third-Part>>
from backend.src.database.social_media_stream_database import SocialMediaStreamDataBase

class DouyinShareUrlDatabase(SocialMediaStreamDataBase):
##
## >>============================= attribute =============================>>
##

##
## douyin share url table header
## +---------------+-------------+-----------+----------------+----------------+----------------+-------------+
## | owner_user_id | sec_user_id | nickname  | post_share_url | live_share_url | directory_name | user_status |
## +---------------+-------------+-----------+----------------+----------------+----------------+-------------+
##
  __DOUYIN_SHARE_URL_TABLE_NAME   = 'share_url'
  __DOUYIN_SHARE_URL_TABLE_HEADER = ['owner_user_id', 'sec_user_id', 'nickname', 'post_share_url', 'live_share_url', 'directory_name', 'user_status']
  __DOUYIN_SHARE_URL_TABLE_TUPLE  = {item:None for item in __DOUYIN_SHARE_URL_TABLE_HEADER}
  __SQL_DROP_SHARE_URL_TABLE      = '''
                                    DROP TABLE share_url;
                                  '''
  __SQL_CREATE_SHARE_URL_TABLE    = '''
                                    CREATE TABLE share_url (
                                      sec_user_id       CHAR(200) NOT NULL PRIMARY KEY,
                                      nickname          CHAR(20),
                                      post_share_url    CHAR(100),
                                      live_share_url    CHAR(100),
                                      directory_name    CHAR(100),
                                      user_status       CHAR(100)
                                    )
                                  '''
##
## >>============================= private method =============================>>
##
  def __init__(self, host:str, user:str, passwd:str, database:str):
    super().__init__(host, user, passwd, database)

##
## >>============================= abstract method =============================>>
##
  # def insert_db_record(self, cursor, table, record):
  #   return super().insert_db_record(cursor, table, record)
  
  # def create_db_table(self):
  #   return super().create_db_table()

##
## >>============================= sub class method =============================>>
##
  ##
  ## get share url table name
  ##
  def get_share_url_table_name(self) -> str:
    return self.__DOUYIN_SHARE_URL_TABLE_NAME
  
  ##
  ## get share url table header
  ##
  def get_share_url_table_header(self) -> list:
    return self.__DOUYIN_SHARE_URL_TABLE_HEADER
  
  ##
  ## get share url table tuple
  ##
  def get_share_url_table_tuple(self) -> dict:
    return self.__DOUYIN_SHARE_URL_TABLE_TUPLE
  
  ##
  ## create a share url record
  ##
  def insert_live_share_url_record(self, record:dict):
    try:        
      ##
      ## check if the primary key is exist
      ##
      if record.get("owner_user_id") is None:
        raise KeyError
      
      ##
      ## check if the record is exist in database
      ##
      sql = '''SELECT owner_user_id, live_share_url
              FROM   share_url
              WHERE  owner_user_id = "{}";
            '''.format(record.get("owner_user_id"))
      connector = self.get_db_connector()
      cursor = connector.cursor()
      cursor.execute(sql)
      result = cursor.fetchall()
      if len(result) != 0:
        ##
        ## the record is exist in database
        ## next: insert it if live share url is None
        ##
        for db_record in result:
          ##
          ## update the record when the record is None
          ##
          if db_record[1] is None:
            update_sql = '''
                          UPDATE share_url
                          SET live_share_url = "{}"
                          WHERE owner_user_id = "{}";
                          '''.format(record.get("live_share_url"), db_record[0])
            cursor.execute(update_sql)
            connector.commit()
            connector.close()
            print("INFO: update owner_user_id:{} live_share_url:{} success".format(db_record[0], record["live_share_url"]))
          else:
            pass
      else:
        ##
        ## the record is not exist in database
        ## next: insert it into database
        ##
        insert_sql = '''
                      INSERT INTO share_url (owner_user_id, sec_user_id, nickname, post_share_url, live_share_url, directory_name, user_status) VALUES (
                        "{}",
                        "{}", 
                        "{}", 
                        '{}',
                        "{}", 
                        "{}", 
                        "{}"
                      );
                     '''.format(record.get("owner_user_id"), record.get("sec_user_id"), record.get("nickname"), record.get("post_share_url"), record.get("live_share_url"), record.get("directory_name"), record.get("user_status"))
        cursor.execute(insert_sql)
        connector.commit()
        connector.close()
        print("INFO: insert record {} success".format([item for item in record.values()]))
    except Exception as e:
      print("ERROR: insert live share url {} failed {}".format(record["live_share_url"], e))
      raise e

  ##
  ## check if the douyin user is recorded
  ##
  def is_live_share_url_record_exist (self, live_share_url:str) -> bool:
    try:
      sql = '''
              SELECT live_share_url 
              FROM share_url
              WHERE live_share_url = "{}";
            '''.format(live_share_url)
      cursor = self.get_db_connector().cursor()
      cursor.execute(sql)
      result = cursor.fetchall()
      if len(result) != 0:
        return True
      else:
        return False
    except Exception as e:
      print("ERROR: search live share url {} failed {}".format(live_share_url, e))
      raise e

##
## >>================================ test method ===============================>>
##

##
## test：create a database table
##
def test_create_db_table():
  ##
  ## test for connect to database
  ##
  try:
    db = DouyinShareUrlDatabase(host='127.0.0.1', user='admin', passwd='admin', database='social_media_stream_downloader')
    connector = db.get_db_connector()
    cursor = connector.cursor()
    sql = '''
            CREATE TABLE share_url (
              owner_user_id     CHAR(200) NOT NULL PRIMARY KEY,
              sec_user_id       CHAR(200),
              nickname          CHAR(20),
              post_share_url    CHAR(100),
              live_share_url    CHAR(100),
              directory_name    CHAR(100),
              user_status       CHAR(100)
            )
          '''
    cursor.execute(sql)
    print("INFO: test create database table success")
    connector.close()
  except Exception as e:
    print("ERROR: test create database table failed {}".format(e))


##
## test：drop a database table
##
def test_drop_db_table():  
  ##
  ## test for connect to database
  ##
  try:
    db = DouyinShareUrlDatabase(host='127.0.0.1', user='admin', passwd='admin', database='social_media_stream_downloader')
    connector = db.get_db_connector()
    cursor = connector.cursor()
    sql = '''
            DROP TABLE share_url;
          '''
    cursor.execute(sql)
    print("INFO: test drop database table success")
    connector.close()
  except Exception as e:
    print("ERROR: test drop database table failed {}".format(e))

##
## test：insert a record to database table
##
def test_insert_record():
  record = dict()
  record["owner_user_id"]  = "58859666123"
  record["sec_user_id"]    = "MS4wLjABAAAAGZkW5n1EHZD_TFyQ-QiaISBPemtKFxVVdhLSeoXhh-U"
  record["nickname"]       = "\u2728\u7C73\u5F00\u6717\u7EFF\u841D\u2728"
  record["post_share_url"] = "https://v.douyin.com/iYkvSmAw/"
  record["live_share_url"] = "https://v.douyin.com/iFemNNTW/"
  record["directory_name"] = "_\u7C73\u5F00\u6717\u7EFF\u841D_"
  record["user_status"]    = "正常"

  try:
    db = DouyinShareUrlDatabase(host='127.0.0.1', user='admin', passwd='admin', database='social_media_stream_downloader')
    db.insert_live_share_url_record(record)
  except Exception as e:
    print("ERROR: insert a record failed {}".format(e))

##
## test: search recode from table
##
def test_search_record_from_table():
  try:
    db = DouyinShareUrlDatabase(host='127.0.0.1', user='admin', passwd='admin', database='social_media_stream_downloader')
    url = "https://v.douyin.com/ikRBs7Sy/"
    if db.is_live_share_url_record_exist(url) is True:
      print("INFO: live share url {} is exist".format(url))
    db.close()
  except Exception as e:
    print("ERROR: search records from table failed {}".format(e))
    raise e

if __name__ == "__main__":
  ##
  ## test for connect to database
  ##
  # test_create_db_table()
  # test_drop_db_table()
  # test_insert_record()
  # test_search_record_from_table()
  pass