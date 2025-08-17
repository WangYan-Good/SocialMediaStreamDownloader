##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

##<<Base>>

## <<Extension>>
import pymysql
from pymysql.connections import Connection

## <<Third-Part>>
from backend.src.library.baselib import output_dict
from backend.src.base.log        import get_logger
from backend.src.library.baselib import set_dict_attr

class SocialMediaStreamDataBase():
##
## >>============================= attribute =============================>>
##
  __host:str             = None
  __user:str             = None
  __passwd:str           = None
  __database:str         = None
  ##
  ## TODO: use connection pool to manage database connections
  ##
  __connector_pool       = None
  __default_connector    = None
  
  ##
  ## table instance
  ##
  __db_tables_instance   = None

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
  def __init__(self, host:str, user:str, passwd:str, database:str) -> None:
    try:
      self.__host               = host
      self.__user               = user
      self.__passwd             = passwd
      self.__database           = database
      self.__db_tables_instance = dict()
    except Exception as e:
      raise e
##
## >>============================= abstract method =============================>>
##

##
## >>============================= sub class method =============================>>
##
  ##
  ## register database table instance
  ##
  def register_table(self, table_name:str, table_instance) -> None:
    ##
    ## check input
    ##
    if table_name is None or table_instance is None:
      get_logger().warning("database table name or instance is None!")
      raise ValueError

    ##
    ## check if table instance is already exists
    ##
    if self.__db_tables_instance is None or len(self.__db_tables_instance) == 0:
      set_dict_attr(self.__db_tables_instance, "$." + table_name, table_instance)
      get_logger().info("database table {} instance is added!".format(table_name))
    else:
      get_logger().warning("database table {} instance is already exists!".format(table_name))
    return
  
  ##
  ## check if database table instance is registered
  ##
  def is_table_registered(self, table_name:str) -> bool:
    if self.__db_tables_instance is None or len(self.__db_tables_instance) == 0:
      get_logger().warning("No database table instance registered")
      return False
    
    if table_name in self.__db_tables_instance:
      return True
    else:
      get_logger().warning("database table {} instance is not registered".format(table_name))
      return False

  ##
  ## unregister database table instance
  ##
  def unregister_table(self, table_name:str) -> None:
    if self.__db_tables_instance is None or len(self.__db_tables_instance) == 0:
      get_logger().warning("No database table instance registered")
      return
    
    if table_name in self.__db_tables_instance:
      del self.__db_tables_instance[table_name]
      get_logger().info("database table {} instance is removed".format(table_name))
    else:
      get_logger().warning("database table {} instance is not registered".format(table_name))
    return

  ##
  ## get database connector
  ## TODO: use connection pool to manage database connections
  ##
  def get_db_connector(self):
    try:
      ##
      ## connect database
      ##
      self.__connector = pymysql.connect(host=self.__host, user=self.__user, passwd=self.__passwd, db=self.__database)
      self.__default_connector = self.__connector
      get_logger().info("connect database {} successfully!".format(self.__database))
    except Exception as e:
      get_logger().error("connect database {} fail, reason: {}".format(self.__database, e))
    return self.__default_connector

  ##
  ## close database connector
  ##
  def close_db_connector(self, connector:Connection=None) -> None:
    if connector is not None:
      ##
      ## check if connector is valid
      ## close the specified connector
      ##
      try:
        connector.close()
        get_logger().info("database connector closed successfully!")
      except Exception as e:
        get_logger().error("close database connector failed! reason: {}".format(e))
    else:
      ##
      ## check if default connector is None
      ## close the default connector
      ##
      if self.__default_connector is not None:
        try:
          self.__default_connector.close()
          get_logger().info("default database connector closed successfully!")
        except Exception as e:
          get_logger().error("close default database connector failed! reason: {}".format(e))
      else:
        get_logger().warning("database connector is None, no need to close!")
        raise ValueError

  ##
  ## drop database table
  ##
  def drop_db_table(self, table_name:str) -> None:
    try:
      sql = '''DROP TABLE IF EXISTS {};'''.format(table_name)
      with self.get_db_connector() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql)
    except Exception as e:
      get_logger().error("ERROR: drop database table {} is failed! reason: {}".format(table_name, e))
      raise e
  
  ##
  ## check if table exists
  ##
  def is_table_exist(self, table_name:str) -> bool:
    try:
      sql = '''
              SELECT COUNT(*)
              FROM information_schema.TABLES
              WHERE TABLE_SCHEMA = "{}"
              AND TABLE_NAME = "{}";
            '''.format(self.__database, table_name)
      with self.get_db_connector() as connector:
        with connector.cursor() as cursor:
          get_logger().debug(sql)
          cursor.execute(sql)
          result = cursor.fetchall()
      if result[0][0] == 1:
        return True
      else:
        return False
    except Exception as e:
      get_logger().error("ERROR: check if table {} exists is failed! reason: {}".format(table_name, e))
      raise e
  
  ##
  ## dump database tables
  ##
  def dump_db_tables(self) -> None:
    get_logger().info("database tables:")
    if self.__db_tables_instance is None or len(self.__db_tables_instance) == 0:
      get_logger().warning("No database table instance registered")
      return
    output_dict(self.__db_tables_instance, tab=1)
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
  get_logger().debug(sql)
  cursor.execute(sql)
  result = cursor.fetchall()
  get_logger().debug(result)
  db.close_db_connector()

##
## test: insert owner id into owner_liked table
##
def test_insert_owner_into_liked_table(owner_user_id:str, platform:str):
  try:
    sql = '''
            insert into favorite_owner (owner_user_id, platform) values ("{}", "{}");
          '''.format(owner_user_id, platform)
    db = SocialMediaStreamDataBase(host='192.168.1.9', user='wangyan', passwd='wuyu1998', database='social_media_stream_downloader')
    connector = db.get_db_connector()
    cursor = connector.cursor()
    cursor.execute(sql)
    connector.commit()
    db.close_db_connector()
    get_logger().info("insert {} into liked table succeed!".format(owner_user_id))
  except Exception as e:
    db.close_db_connector()
    get_logger().error("insert {} into liked table failed {}".format(owner_user_id, e))

##
## test: search liked owner nickname
##    
def test_search_nickname_from_liked_table(owner_user_id:str):
  pass

##
## test: check if live_record table exists
##
def test_check_live_record_table_exists():
  db = SocialMediaStreamDataBase(host='192.168.1.12', user='wangyan', passwd='wuyu1998', database='social_media_stream_downloader')
  if db.is_table_exist("live_record"):
    get_logger().info("live_record table exists!")
  else:
    get_logger().info("live_record table not exists!")
  return

if __name__ == "__main__":
  # test_search_sec_user_id("https://v.douyin.com/ikRBs7Sy/")
  # test_insert_owner_into_liked_table("3171420333409886", "douyin")
  test_check_live_record_table_exists()