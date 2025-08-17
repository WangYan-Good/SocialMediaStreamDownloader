##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from datetime import datetime as dat

## <<Third-Part>>
from backend.src.database.social_media_stream_database                import SocialMediaStreamDataBase
from backend.src.database.database_table.social_media_stream_db_table import SocialMediaStreamDataTable
from backend.src.base.log                                             import get_logger

class LiveRecordTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##

##
## live record table header
## +----------------------------------+-------------------+------+-----+---------+-------+----------------------------+----------------------+
## | Field                            | Type              | Null | Key | Default | Extra | Topology                   | Comment              | 
## +----------------------------------+-------------------+------+-----+---------+-------+----------------------------+----------------------+
## | now                              | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"              | 当前时间戳            |
## | platform                         | varchar(20)       | NO   | PRI |         |       |           -                | 平台                  | 
## | room_id                          | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"           | 直播间ID              | 
## | user_id                          | varchar(200)      |      |     | NULL    |       | "$.data.user.id"           | 当前观众ID            | 
## | start_time                       | timestamp         |      |     | NULL    |       | "$.data.room.start_time"   | 开始时间              | 
## | finish_time                      | timestamp         |      |     | NULL    |       | "$.data.room.finish_time"  | 结束时间              | 
## | status_code                      | unsigned tinyint  |      |     | NULL    |       | "$.status_code"            | 网络请求状态          | 
## +----------------------------------+-------------------+------+-----+---------+-------+----------------------------+----------------------+
##
  __LIVE_RECORD_TABLE_NAME       = 'live_record'
  __LIVE_RECORD_TABLE_HEADER     = ['now', 'platform', 'room_id', 'user_id', 'start_time', 'finish_time', 'status_code']
  __LIVE_RECORD_TABLE_PRI_KEY    = ['now', 'platform', 'room_id']
  __LIVE_RECORD_TABLE_TUPLE      = {item:None for item in __LIVE_RECORD_TABLE_HEADER}
  __SQL_CREATE_LIVE_RECORD_TABLE = '''
                                    CREATE TABLE IF NOT EXISTS {} (
                                      now          timestamp(3)      NOT NULL,
                                      platform     varchar(20)       NOT NULL,
                                      room_id      varchar(200)      NOT NULL,
                                      user_id      varchar(200)      DEFAULT NULL,
                                      start_time   timestamp         DEFAULT NULL,
                                      finish_time  timestamp         DEFAULT NULL,
                                      status_code  tinyint           DEFAULT NULL,
                                      PRIMARY KEY (now, platform, room_id)
                                    )
                                    '''.format(__LIVE_RECORD_TABLE_NAME)
  __SQL_DROP_LIVE_RECORD_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__LIVE_RECORD_TABLE_NAME)


##
## >>============================= private method =============================>>
##
  ##
  ## singleton mode
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
  ## get live record table name
  ##
  def get_name(self) -> str:
    return self.__LIVE_RECORD_TABLE_NAME
  
  ##
  ## get live record table header
  ##
  def get_header(self) -> list:
    return self.__LIVE_RECORD_TABLE_HEADER

  ##
  ## get live record table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__LIVE_RECORD_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__LIVE_RECORD_TABLE_PRI_KEY

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_LIVE_RECORD_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_LIVE_RECORD_TABLE

##
## >>============================= sub class method =============================>>
##

##
## >>================================ test method ===============================>>
##

##
## test: create live_record table
##
def test_create_live_record_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create live_record table
  ##
  live_record = LiveRecordTable(db_instance=db)
  live_record.create()
  return

##
## test: drop live_record table
##
def test_drop_live_record_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop live_record table
  ##
  live_record = LiveRecordTable(db_instance=db)
  live_record.drop()
  return

##
## test: check if live_record table exists
##
def test_check_live_record_table_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  live_record = LiveRecordTable(db)
  
  ##
  ## check if live_record table exists
  ##
  if db.is_table_exist(live_record.get_name()):
    get_logger().info("live_record table exists!")
  else:
    get_logger().info("live_record table not exists!")
  return

##
## test: insert live record
##
def test_insert_live_record(db:SocialMediaStreamDataBase = None):
  """
  Test inserting a live record into the live_record table.
  """
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create live_record table if not exists
  ##
  live_record = LiveRecordTable(db_instance=db)
  
  ##
  ## insert a sample live record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'user_id': '2700838411446480',
    'start_time': dat.fromtimestamp(1714227435),
    'finish_time': dat.fromtimestamp(1714232860),
    'status_code': 0
  }
  
  try:
    live_record.insert_record(sample_record)
    get_logger().info("sample live record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample live record: {}".format(e))
    raise e

##
## test: get live record
##
def test_get_live_record(db:SocialMediaStreamDataBase = None):
  """
  Test getting a live record from the live_record table.
  """
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create live_record table if not exists
  ##
  live_record = LiveRecordTable(db_instance=db)
  
  ##
  ## get a sample live record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    record = live_record.get_record(sample_record)
    if record:
      get_logger().info("sample live record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample live record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample live record: {}".format(e))
    raise e

##
## test: delete live record
##
def test_delete_live_record(db:SocialMediaStreamDataBase = None):
  """
  Test deleting a live record from the live_record table.
  """
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create live_record table if not exists
  ##
  live_record = LiveRecordTable(db_instance=db)
  
  ##
  ## delete a sample live record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    live_record.delete_record(sample_record)
    get_logger().info("sample live record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample live record: {}".format(e))
    raise e

##
## test: update live record
##
def test_update_live_record(db:SocialMediaStreamDataBase = None):
  """
  Test updating a live record in the live_record table.
  """
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create live_record table if not exists
  ##
  live_record = LiveRecordTable(db_instance=db)
  
  ##
  ## update a sample live record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'start_time': dat.fromtimestamp(1714227435),
    'finish_time': dat.fromtimestamp(1714232860),
    'status_code': 1
  }
  
  try:
    live_record.update_record(sample_record)
    get_logger().info("sample live record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample live record: {}".format(e))
    raise e

##
## >>================================ main method ===============================>>
##
if __name__ == "__main__":
  db = SocialMediaStreamDataBase(host='192.168.1.12', user='wangyan', passwd='wuyu1998', database='social_media_stream_downloader')
  test_check_live_record_table_exists(db)
  test_create_live_record_table(db)
  test_insert_live_record(db)
  test_check_live_record_table_exists(db)
  test_get_live_record(db)
  test_update_live_record(db)
  test_delete_live_record(db)
  test_drop_live_record_table(db)