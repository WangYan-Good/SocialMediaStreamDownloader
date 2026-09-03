##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

##<<Base>>
import re
import threading
from contextlib import contextmanager
from typing     import Iterator

## <<Extension>>
import pymysql
from pymysql.connections import Connection
from dbutils.pooled_db   import PooledDB

## <<Third-Part>>
from backend.src.library.baselib import output_dict
from backend.src.library.loglib  import get_logger
from backend.src.library.safe_diagnostics import persistence_diagnostic
from backend.src.library.baselib import set_dict_attr
from backend.src.database.schema_guard import (
  require_database_write_ready,
  require_runtime_schema_mutation_allowed,
)

##
## MySQL 标识符的安全字符集：字母、数字、下划线、美元符号。
## 受管表名全部落在此范围内，超出即视为调用方传错。
##
_SAFE_IDENTIFIER = re.compile(r"^[0-9a-zA-Z_$]+$")


def quote_identifier(identifier) -> str:
  """把表名或列名转成可安全拼接的反引号形式。

  标识符不能用 %s 占位符传递，只能拼接，所以在拼接前先限定字符集，
  再加倍内部的反引号并包裹。两道措施缺一不可：只加引号不校验，仍可
  被换行或控制字符干扰；只校验不加引号，则保留字会让语句解析失败。
  """
  if identifier is None:
    raise ValueError("identifier is required")
  text = str(identifier)
  if not _SAFE_IDENTIFIER.match(text):
    raise ValueError("unsafe SQL identifier: {!r}".format(text))
  return "`{}`".format(text.replace("`", "``"))


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
    'maxusage': 0,       # 单个连接最大使用次数 (0 or None represents unlimited)
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
    """
    each database instance is a singleton per connection config
    different args including host/user/passwd/database will create different database instance
    thread-safe map of instances keyed by connection parameters
    """
    try:
      if len(args) >= 4:
        host, user, passwd, database = args[0], args[1], args[2], args[3]
      else:
        host = kwargs.get('host') if 'host' in kwargs else (args[0] if len(args) > 0 else None)
        user = kwargs.get('user') if 'user' in kwargs else (kwargs.get('username') if 'username' in kwargs else (args[1] if len(args) > 1 else None))
        passwd = kwargs.get('passwd') if 'passwd' in kwargs else (kwargs.get('password') if 'password' in kwargs else (args[2] if len(args) > 2 else None))
        database = kwargs.get('database') if 'database' in kwargs else (args[3] if len(args) > 3 else None)

      ##
      ## Combine `user` and `passwd` into a single identifier per user request (format: "user|passwd").
      ## Normalize None to empty string so keys are stable.
      ##
      def _norm(x):
        return '' if x is None else str(x)

      user_pass_combined = _norm(user) + '|' + _norm(passwd)
      instance_key = (host, user_pass_combined, database)
    except Exception:
      instance_key = (args, frozenset(kwargs.items()))

    if not hasattr(cls, '_instances'):
      cls._instances = {}

    with cls._instance_lock:
      inst = cls._instances.get(instance_key)
      if inst is None:
        inst = super().__new__(cls)
        cls._instances[instance_key] = inst
    return inst

  ##
  ## init method
  ##
  def __init__(self, host:str, user:str, passwd:str, database:str) -> None:
    """
    Make __init__ idempotent: if the instance was already initialized for
    this connection config, skip re-initialization.
    """
    if getattr(self, '_initialized', False):
      return

    try:
      self.__host               = host
      self.__user               = user
      self.__passwd             = passwd
      self.__database           = database
      
      ##
      ## per-instance table registry
      ##
      self.__db_tables_instance = dict()
      
      ##
      ## initialize connection pool lazily (will no-op if already set)
      ##
      self.__initialize_pool()
      
      ##
      ## mark as initialized to avoid repeated init on same singleton
      ##
      self._initialized = True
    except Exception as e:
      get_logger().error(
        persistence_diagnostic("persistence_initialisation_failed", error=e)
      )
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
            ##
            ## The host and the schema name are configuration, not a
            ## diagnostic: an operator who needs them already has the file.
            ## Repeating them into every log stream only widens where the
            ## deployment topology is written down.
            ##
            get_logger().info(
              persistence_diagnostic("persistence_pool_ready")
            )
          except Exception as e:
            get_logger().error(
              persistence_diagnostic(
                "persistence_initialisation_failed", error=e
              )
            )
            raise e

##
## >>============================= abstract method =============================>>
##

##
## >>============================= sub class method =============================>>
##
  ##
  ## get database connection info
  ##
  def get_connection_info(self) -> dict:
    return {
      "host": self.__host,
      "user": self.__user,
      "database": self.__database
    }

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
      get_logger().info(
        persistence_diagnostic("persistence_registered", table=table_name)
      )
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
      get_logger().info(
        persistence_diagnostic("persistence_unregistered", table=table_name)
      )
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
      ##
      ## Every database operation in this process funnels through here, and
      ## a driver exception carries the failing statement together with the
      ## parameters bound into it. That is the row - a share url, a nickname,
      ## a recording path - so only the class of the failure is written down.
      ##
      get_logger().error(
        persistence_diagnostic("persistence_connection_failed", error=e)
      )
      conn.rollback()
      raise
    finally:
      try:
        conn.close()  # 归还到连接池，不是真正关闭
      except Exception as e:
        get_logger().warning(
          persistence_diagnostic(
            "persistence_connection_returned_failed", error=e
          )
        )

  ##
  ## drop database table
  ##
  def drop_db_table(self, table_name:str) -> None:
    require_runtime_schema_mutation_allowed()
    require_database_write_ready()
    ##
    ## 表名无法用占位符传递，只能拼接，因此先限定字符集再加反引号包裹。
    ## 这是一条 DROP TABLE，拼错的代价是删掉计划之外的对象。
    ##
    quoted_table_name = quote_identifier(table_name)
    try:
      sql = '''DROP TABLE IF EXISTS {};'''.format(quoted_table_name)
      with self.get_connection() as conn:
        with conn.cursor() as cursor:
          cursor.execute(sql)
          conn.commit()
    except Exception as e:
      get_logger().error(
        persistence_diagnostic(
          "persistence_table_dropped_failed",
          table=table_name,
          operation="drop",
          error=e,
        )
      )
      raise e

  def require_write_ready(self) -> None:
    require_database_write_ready()

  def require_schema_mutation_allowed(self) -> None:
    require_runtime_schema_mutation_allowed()

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
          get_logger().debug(
            persistence_diagnostic(
              "persistence_queried",
              table=table_name,
              operation="query",
            )
          )
          cursor.execute(sql, (self.__database, table_name))
          result = cursor.fetchone()
      if result and result.get('COUNT(*)') == 1:
        return True
      else:
        return False
    except Exception as e:
      get_logger().error(
        persistence_diagnostic(
          "persistence_schema_probe_failed",
          table=table_name,
          operation="query",
          error=e,
        )
      )
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
        get_logger().error(
          persistence_diagnostic(
            "persistence_connection_returned_failed", error=e
          )
        )
