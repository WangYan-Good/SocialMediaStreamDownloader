##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

##<<Base>>
import threading
from contextlib import contextmanager
from typing     import Iterator

## <<Extension>>
import pymysql
from pymysql.connections import Connection
from dbutils.pooled_db   import PooledDB

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
  ## 连接池配置
  ##
  __connection_pool      = None
  __pool_lock            = threading.Lock()
  __pool_config          = {
    'mincached': 2,      # 初始化时创建的空闲连接数
    'maxcached': 10,     # 连接池最大空闲连接数
    'maxshared': 20,     # 连接池最大共享连接数
    'maxconnections': 30,# 连接池最大连接数
    'blocking': True,    # 达到最大连接时是否阻塞等待
    'maxusage': 1000,    # 单个连接最大使用次数
    'ping': 1,           # 连接失效时自动重连 (pymysql.ping()=1)
  }

  ##
  ## table instance
  ##
  __db_tables_instance   = None

##
## >>============================= private method =============================>>
##
  ##
  ## singleton mode (thread-safe)
  ##
  _instance_lock = threading.Lock()
  def __new__(cls, *args, **kwargs):
    if not hasattr(cls, '_instance'):
      with cls._instance_lock:
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
      self.__initialize_pool()
    except Exception as e:
      get_logger().error("数据库初始化失败: {}".format(e))
      raise e

  ##
  ## 初始化连接池
  ##
  def __initialize_pool(self) -> None:
    if self.__connection_pool is None:
      with self.__pool_lock:
        if self.__connection_pool is None:
          try:
            self.__connection_pool = PooledDB(
              creator=pymysql,
              host=self.__host,
              user=self.__user,
              passwd=self.__passwd,
              database=self.__database,
              charset='utf8mb4',
              cursorclass=pymysql.cursors.DictCursor,
              **self.__pool_config
            )
            get_logger().info("数据库连接池初始化成功 - 主机: {}, 数据库: {}".format(
              self.__host, self.__database))
          except Exception as e:
            get_logger().error("数据库连接池初始化失败: {}".format(e))
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
  ## Obtain a database connection from the connection pool (context manager)
  ##
  @contextmanager
  def get_connection(self) -> Iterator[Connection]:
    """
    Context Manager for Obtaining Database Connections from a Connection Pool

    Usage:
    with db.get_connection() as conn:
    with conn.cursor() as cursor:
    cursor.execute(sql, params)

    Advantages:
    1. Automatically obtains connections from the connection pool
    2. Automatically returns connections after use, no manual closing required
    3. Returns connections even in case of exceptions, preventing connection leaks
    """
    if self.__connection_pool is None:
      get_logger().error("Connection pool not initialized")
      raise RuntimeError("Database connection pool not initialized")

    conn = self.__connection_pool.connection()
    try:
      yield conn
    except Exception as e:
      get_logger().error("Database operation exception: {}".format(e))
      conn.rollback()
      raise
    finally:
      try:
        conn.close()  # 归还到连接池，不是真正关闭
      except Exception as e:
        get_logger().warning("Fail to return the connection pool: {}".format(e))

  ##
  ## drop database table
  ##
  def drop_db_table(self, table_name:str) -> None:
    try:
      sql = '''DROP TABLE IF EXISTS {};'''.format(table_name)
      with self.get_connection() as conn:
        with conn.cursor() as cursor:
          cursor.execute(sql)
          conn.commit()
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
              WHERE TABLE_SCHEMA = %s
              AND TABLE_NAME = %s;
            '''
      with self.get_connection() as conn:
        with conn.cursor() as cursor:
          get_logger().debug(sql)
          cursor.execute(sql, (self.__database, table_name))
          result = cursor.fetchone()
      if result and result.get('COUNT(*)') == 1:
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
  ## 获取连接池状态
  ##
  def get_pool_status(self) -> dict:
    """
    获取连接池当前状态（用于监控和调试）
    """
    if self.__connection_pool is None:
      return {"status": "Non-initialized"}

    return {
      "status": "运行中",
      "mincached": self.__pool_config['mincached'],
      "maxcached": self.__pool_config['maxcached'],
      "maxshared": self.__pool_config['maxshared'],
      "maxconnections": self.__pool_config['maxconnections'],
      # 注：DBUtils 不直接暴露当前使用数，需通过内部API
    }

  ##
  ## 关闭连接池（应用退出时调用）
  ##
  def close_pool(self) -> None:
    """
    关闭连接池，释放所有连接

    应在应用退出时调用
    """
    if self.__connection_pool is not None:
      try:
        self.__connection_pool.close()
        self.__connection_pool = None
        get_logger().info("DB connect pool has been closed")
      except Exception as e:
        get_logger().error("Fail to close DB connect pool: {}".format(e))