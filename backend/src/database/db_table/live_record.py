##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from threading import Lock
from datetime import datetime as dat

## <<Extension>>

## <<Third-Part>>
from backend.src.database.social_media_stream_database       import SocialMediaStreamDataBase
from backend.src.base.log                                    import get_logger

class LiveRecordTable():
##
## >>=============================== attribute ===============================>>
##
  __db_lock  = Lock()
  __database = None

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
  __LIVE_RECOED_TABLE_PRI_KEY    = ['now', 'platform', 'room_id']
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
    if not hasattr(cls, '_instance'):
      cls._instance = super().__new__(cls)
    return cls._instance

  ##
  ## init method
  ##
  def __init__(self, db_instance:SocialMediaStreamDataBase = None) -> None:
    ##
    ## check if db_instance is valid
    ##
    if db_instance is None:
      get_logger().error("db_instance is None, please provide a valid SocialMediaStreamDataBase instance")
      raise ValueError
    
    ##
    ## initialize the database instance
    ##
    self.__database = db_instance
    
    ##
    ## register the live record table when live_record table exists but not registered
    ##
    if self.__database.is_table_exist(self.__LIVE_RECORD_TABLE_NAME) and self.__database.is_table_registered(self.__LIVE_RECORD_TABLE_NAME) is False:
      try:
        self.__database.register_table(self.__LIVE_RECORD_TABLE_NAME, self)
        get_logger().info("live_record table registered successfully")
      except Exception as e:
        get_logger().error("failed to register live_record table: {}".format(e))
        raise e
    else:
      get_logger().warning("skipped to register live_record table because it does not exist")
      return
  
##
## >>============================= abstract method =============================>>
##

##
## >>============================= sub class method =============================>>
##
  ##
  ## get live record table name
  ##
  def get_live_record_table_name(self) -> str:
    return self.__LIVE_RECORD_TABLE_NAME
  
  ##
  ## get live record table header
  ##
  def get_live_record_table_header(self) -> list:
    return self.__LIVE_RECORD_TABLE_HEADER
  
  ##
  ## get live record table tuple
  ##
  def get_live_record_table_tuple(self) -> dict:
    return self.__LIVE_RECORD_TABLE_TUPLE
  
  ##
  ## create live record table
  ##
  def create_live_record_table(self):
    ##
    ## check if the live record table already exists
    ##
    if self.__database.is_table_exist(self.__LIVE_RECORD_TABLE_NAME):
      get_logger().warning("live_record table already exists, skipping creation")
      return
    
    ##
    ## create the live record table
    ##
    try:
      ##
      ## connector will be automatically closed after the with block
      ##
      with self.__database.get_db_connector() as connector:
        ##
        ## cursor will be automatically closed after the with block
        ##
        with connector.cursor() as cursor:
          cursor = connector.cursor()
          cursor.execute(self.__SQL_CREATE_LIVE_RECORD_TABLE)
          connector.commit()
          get_logger().info("live_record table created successfully")
    except Exception as e:
      get_logger().error("failed to create live_record table: {}".format(e))
      raise e
  
    ##
    ## register the live record table
    ##
    try:
      self.__database.register_table(self.__LIVE_RECORD_TABLE_NAME, self)
      get_logger().info("live_record table registered successfully")
    except Exception as e:
      get_logger().error("failed to register live_record table: {}".format(e))
      raise e
  
  ##
  ## drop live record table
  ##
  def drop_live_record_table(self):
    ##
    ## check if the live record table exists
    ##
    if not self.__database.is_table_exist(self.__LIVE_RECORD_TABLE_NAME):
      get_logger().warning("live_record table does not exist, skipping drop")
      return
    
    ##
    ## unregister the live record table
    ##
    try:
      self.__database.unregister_table(self.__LIVE_RECORD_TABLE_NAME)
      get_logger().info("live_record table unregistered successfully")
    except Exception as e:
      get_logger().error("failed to unregister live_record table: {}".format(e))
      raise e
    
    ##
    ## drop the live record table
    ##
    try:
      with self.__database.get_db_connector() as connector:
        with connector.cursor() as cursor:
          cursor.execute(self.__SQL_DROP_LIVE_RECORD_TABLE)
          connector.commit()
          get_logger().info("live_record table dropped successfully")
    except Exception as e:
      get_logger().error("failed to drop live_record table: {}".format(e))
      raise e

  ##
  ## insert live record
  ##
  def insert_live_record(self, record:dict) -> None:
    """
    Insert a live record into the live_record table.
    
    :param record: A dictionary containing the live record data.
    """
    ##
    ## check if the record is valid
    ##
    if not isinstance(record, dict):
      get_logger().error("record must be a dictionary")
      raise ValueError("record must be a dictionary")
    
    ##
    ## check if the primary key fields are present in the record
    ##
    for field in self.__LIVE_RECOED_TABLE_PRI_KEY:
      if field not in record:
        get_logger().error("record must contain the primary key field: {}".format(field))
        raise ValueError
    
    ##
    ## insert the live record into the database
    ##
    try:
      with self.__database.get_db_connector() as connector:
        with connector.cursor() as cursor:          
          ##
          ## insert the live record into the live_record table
          ##
          sql = '''
                INSERT INTO {} ({})
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                '''.format(self.__LIVE_RECORD_TABLE_NAME, ', '.join(self.__LIVE_RECORD_TABLE_HEADER))
          with self.__db_lock:
            cursor.execute(sql, tuple(record.get(field) for field in self.__LIVE_RECORD_TABLE_HEADER))
            connector.commit()
          get_logger().info("inserted live record successfully")
    except Exception as e:
      get_logger().error("failed to insert live record: {}".format(e))
      raise e

  ##
  ## delete live record
  ##
  def delete_live_record(self, record:dict) -> None:
    """
    Delete a live record from the live_record table.
    
    :param record: A dictionary containing the primary key fields of the live record.
    """
    ##
    ## check if the primary key fields are present in the record
    ##
    for field in self.__LIVE_RECOED_TABLE_PRI_KEY:
      if field not in record:
        get_logger().error("record must contain the primary key field: {}".format(field))
        raise ValueError
    
    ##
    ## delete the live record from the database
    ##
    try:
      with self.__database.get_db_connector() as connector:
        with connector.cursor() as cursor:
          sql = '''
                DELETE FROM {}
                WHERE {} = %s AND {} = %s AND {} = %s
                '''.format(self.__LIVE_RECORD_TABLE_NAME, *self.__LIVE_RECOED_TABLE_PRI_KEY)
          with self.__db_lock:
            cursor.execute(sql, tuple(record.get(field) for field in self.__LIVE_RECOED_TABLE_PRI_KEY))
            connector.commit()
          get_logger().info("deleted live record successfully")
    except Exception as e:
      get_logger().error("failed to delete live record: {}".format(e))
      raise e
  
  ##
  ## update live record
  ##
  def update_live_record(self, record:dict) -> None:
    """
    Update a live record in the live_record table.
    
    :param record: A dictionary containing the live record data.
    """
    ##
    ## check if the record is valid
    ##
    if not isinstance(record, dict):
      get_logger().error("record must be a dictionary")
      raise ValueError
    
    ##
    ## check if the primary key fields are present in the record
    ##
    for field in self.__LIVE_RECOED_TABLE_PRI_KEY:
      if field not in record:
        get_logger().error("record must contain the primary key field: {}".format(field))
        raise ValueError
    
    ##
    ## update the live record in the database
    ##
    try:
      with self.__database.get_db_connector() as connector:
        with connector.cursor() as cursor:
          sql = '''
                UPDATE {}
                SET start_time = %s, finish_time = %s, status_code = %s
                WHERE {} = %s AND {} = %s AND {} = %s
                '''.format(self.__LIVE_RECORD_TABLE_NAME, *self.__LIVE_RECOED_TABLE_PRI_KEY)
          with self.__db_lock:
            cursor.execute(sql, tuple(record.get(field) for field in ['start_time', 'finish_time', 'status_code'] + self.__LIVE_RECOED_TABLE_PRI_KEY))
            connector.commit()
          get_logger().info("updated live record successfully")
    except Exception as e:
      get_logger().error("failed to update live record: {}".format(e))
      raise e
  
  ##
  ## get live record
  ##
  def get_live_record(self, record:dict) -> dict:
    """
    Get a live record from the live_record table.
    
    :param record: A dictionary containing the primary key fields of the live record.
    :return: A dictionary containing the live record data.
    """
    ##
    ## check if the primary key fields are present in the record
    ##
    for field in self.__LIVE_RECOED_TABLE_PRI_KEY:
      if field not in record:
        get_logger().error("record must contain the primary key field: {}".format(field))
        raise ValueError
    
    ##
    ## get the live record from the database
    ##
    try:
      with self.__database.get_db_connector() as connector:
        with connector.cursor() as cursor:
          sql = '''
                SELECT * FROM {}
                WHERE {} = %s AND {} = %s AND {} = %s
                '''.format(self.__LIVE_RECORD_TABLE_NAME, *self.__LIVE_RECOED_TABLE_PRI_KEY)
          
          ##
          ## check if the lock is acquired
          ##
          self.__db_lock.acquire(False)
          cursor.execute(sql, tuple(record.get(field) for field in self.__LIVE_RECOED_TABLE_PRI_KEY))
          result = cursor.fetchone()
          self.__db_lock.release()
          if result is None:
            get_logger().warning("live record not found")
            return None
          return dict(zip(self.__LIVE_RECORD_TABLE_HEADER, result))
    except Exception as e:
      get_logger().error("failed to get live record: {}".format(e))
      raise e

##
## >>================================ test method ===============================>>
##

##
## test: create live_record table
##
def test_create_live_record_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db_instance is valid
  ##
  if db is None:
    get_logger().error("db_instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create live_record table
  ##
  live_record = LiveRecordTable(db_instance=db)
  live_record.create_live_record_table()
  return

##
## test: drop live_record table
##
def test_drop_live_record_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db_instance is valid
  ##
  if db is None:
    get_logger().error("db_instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop live_record table
  ##
  live_record = LiveRecordTable(db_instance=db)
  live_record.drop_live_record_table()
  return

##
## test: check if live_record table exists
##
def test_check_live_record_table_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db_instance is valid
  ##
  if db is None:
    get_logger().error("db_instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## check if live_record table exists
  ##
  live_record = LiveRecordTable(db_instance=db)
  db.register_table('live_record', live_record)
  if db.is_table_exist("live_record"):
    get_logger().info("live_record table exists!")
  else:
    get_logger().info("live_record table not exists!")
  db.dump_db_tables()
  return

##
## test: insert live record
##
def test_insert_live_record(db:SocialMediaStreamDataBase = None):
  """
  Test inserting a live record into the live_record table.
  """
  ##
  ## check if db_instance is valid
  ##
  if db is None:
    get_logger().error("db_instance is None, please provide a valid SocialMediaStreamDataBase instance")
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
    live_record.insert_live_record(sample_record)
    get_logger().info("sample live record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample live record: {}".format(e))

##
## test: get live record
##
def test_get_live_record(db:SocialMediaStreamDataBase = None):
  """
  Test getting a live record from the live_record table.
  """
  ##
  ## check if db_instance is valid
  ##
  if db is None:
    get_logger().error("db_instance is None, please provide a valid SocialMediaStreamDataBase instance")
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
    record = live_record.get_live_record(sample_record)
    if record:
      get_logger().info("sample live record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample live record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample live record: {}".format(e))

##
## test: delete live record
##
def test_delete_live_record(db:SocialMediaStreamDataBase = None):
  """
  Test deleting a live record from the live_record table.
  """
  ##
  ## check if db_instance is valid
  ##
  if db is None:
    get_logger().error("db_instance is None, please provide a valid SocialMediaStreamDataBase instance")
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
    live_record.delete_live_record(sample_record)
    get_logger().info("sample live record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample live record: {}".format(e))

##
## test: update live record
##
def test_update_live_record(db:SocialMediaStreamDataBase = None):
  """
  Test updating a live record in the live_record table.
  """
  ##
  ## check if db_instance is valid
  ##
  if db is None:
    get_logger().error("db_instance is None, please provide a valid SocialMediaStreamDataBase instance")
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
    live_record.update_live_record(sample_record)
    get_logger().info("sample live record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample live record: {}".format(e))

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