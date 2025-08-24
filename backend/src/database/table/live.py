##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from datetime import datetime as dat

## <<Third-Part>>
from backend.src.database.social_media_stream_database                import SocialMediaStreamDataBase
from backend.src.database.table.social_media_stream_db_table          import SocialMediaStreamDataTable


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
class LiveRecordTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
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

