##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from threading import Lock
from abc       import ABC, abstractmethod
from typing    import ClassVar, Dict, Type

## <<Third-Part>>
from backend.src.database.social_media_stream_database       import SocialMediaStreamDataBase
from backend.src.base.log                                    import get_logger

class SocialMediaStreamDataTable(ABC):
##
## >>=============================== attribute ===============================>>
##
  __db_lock  = Lock()
  __database = None
  
  __TABLE_NAME           = str()
  __TABLE_HEADER         = list()
  __TABLE_PRI_KEY        = list()
  __TABLE_AUTO_INCREMENT = list()
  __TABLE_TUPLE          = {item:None for item in __TABLE_HEADER}
  
  __SQL_CMD_CREATE_TABLE = str()
  __SQL_CMD_DROP_TABLE   = str()

  ##
  ## registry for subclasses
  ##
  __REGISTRY: ClassVar[Dict[str, Type['SocialMediaStreamDataTable']]] = {}

##
## >>============================= private method =============================>>
##
  ##
  ## singleton pattern
  ##
  def __new__(cls, *args, **kwargs):
    if not hasattr(cls, 'instance'):
      cls.instance = super().__new__(cls)
    return cls.instance

  ##
  ## init method
  ##
  def __init__(self, db_instance:SocialMediaStreamDataBase = None) -> None:
    ##
    ## prevent re-initialization for singleton pattern
    ##
    if hasattr(self, '_initialized') and self._initialized:
      return

    ##
    ## check if db_instance is provided
    ##
    if db_instance is None:
      get_logger().error("db_instance is None, please provide a valid database instance")
      raise ValueError

    ##
    ## initialize the database instance
    ##
    self.__database = db_instance

    ##
    ## register the table when room_attribute table is exist but not registered
    ##
    if self.__database.is_table_exist(self.get_name()) and self.__database.is_table_registered(self.get_name()) is False:
      try:
        self.__database.register_table(self.get_name(), self)
        get_logger().info("{} table registered successfully".format(self.get_name()))
      except Exception as e:
        get_logger().error("failed to register {} table: {}".format(self.get_name(), e))
        raise e
    else:
      get_logger().info("{} table is already registered or does not exist".format(self.get_name()))

    ##
    ## mark as initialized
    ##
    self._initialized = True
    return
  
  def __init_subclass__(cls, **kwargs):
    """
    subclass registration hook
    """
    super().__init_subclass__(**kwargs)
    
    ##
    ## register subclass
    ##
    cls.__REGISTRY[cls.get_name(cls)] = cls

  ##
  ## quote SQL identifier safely
  ##
  @staticmethod
  def _quote_identifier(identifier: str) -> str:
    if not isinstance(identifier, str):
      raise ValueError("SQL identifier must be a string")
    if len(identifier.strip()) == 0:
      raise ValueError("SQL identifier must not be empty")
    return "`{}`".format(identifier.replace("`", "``"))

  ##
  ## validate keys belong to current table header
  ##
  def _validate_record_keys(self, keys: list) -> None:
    header_set = set(self.get_header())
    invalid_keys = [key for key in keys if key not in header_set]
    if len(invalid_keys) != 0:
      raise ValueError("Invalid columns for {}: {}".format(self.get_name(), invalid_keys))

##
## >>============================= abstract method =============================>>
##
  ##
  ## abstract method to get table name
  ##
  @abstractmethod
  def get_name(self) -> str:
    return self.__TABLE_NAME
  
  ##
  ## abstract method to get table header
  ##
  @abstractmethod
  def get_header(self) -> list:
    return self.__TABLE_HEADER
  
  ##
  ## abstract method to get table tuple
  ##
  @abstractmethod
  def get_tuple(self) -> dict:
    return self.__TABLE_TUPLE

  ##
  ## abstract method to get table primary key
  ##
  @abstractmethod
  def get_pri_key(self) -> list:
    return self.__TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  @abstractmethod
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT
    
  ##
  ## abstract method to get SQL command of create table
  ##
  @abstractmethod
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CMD_CREATE_TABLE

  ##
  ## abstract method to get SQL command of drop table
  ##
  @abstractmethod
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_CMD_DROP_TABLE  

  ##
  ## verify table schema
  ##
  @abstractmethod
  def verify_table_schema(self) -> bool:
    return True

##
## >>============================= sub class method =============================>>
##
  ##
  ## get subclass by table name
  ##
  @classmethod
  def get_subclass_by_table_name(cls, table:str) -> Type['SocialMediaStreamDataTable']:
    if table in cls.__REGISTRY:
      return cls.__REGISTRY[table]
    else:
      get_logger().error("No subclass found for table name: {}".format(table))
      raise ValueError("No subclass found for table name: {}".format(table))

  ##
  ## create table
  ##
  def create(self, verify_schema: bool = True) -> bool:
    """
    安全创建数据库表
    
    Args:
      verify_schema: 是否在创建后验证表结构
      
    Returns:
      bool: 表是否成功创建并验证
    """
    table_name = self.get_name()
    
    ##
    ## check if the table already exists
    ##
    if self.__database.is_table_exist(table_name):
      get_logger().warning("{} table already exists".format(table_name))
      ##
      ## 如果表已存在，可选进行结构验证
      ##
      if verify_schema:
        return self.verify_table_schema()
      return False
    
    ##
    ## create new table
    ##
    try:
      with self.__database.get_connection() as connector:
        with connector.cursor() as cursor:
          ##
          ## 使用锁保护表创建过程
          ##
          with self.__db_lock:
            cursor.execute(self.get_create_sql_cmd())
            connector.commit()
            pass
          
          get_logger().info("{} table created successfully".format(table_name))
          
          ##
          ## 验证表结构（如果启用）
          ##
          if verify_schema:
            schema_valid = self.verify_table_schema()
            if not schema_valid:
              get_logger().warning("table {} created but schema verification failed".format(table_name))
              return False
          
          return True
          
    except Exception as e:
      get_logger().error("failed to create {} table: {}".format(table_name, e))
      return False
    
    ##
    ## register table after successful creation
    ##
    finally:
      try:
        self.__database.register_table(table_name, self)
        get_logger().info("{} table registered successfully".format(table_name))
      except Exception as e:
        get_logger().error("failed to register {} table: {}".format(table_name, e))
  
  ##
  ## drop table
  ##
  def drop(self, confirm: bool = False) -> bool:
    """
    安全删除数据库表
    
    Args:
      confirm: 是否需要确认操作，为True时才会实际执行删除
      
    Returns:
      bool: 表是否成功删除
    """
    table_name = self.get_name()
    
    ##
    ## check if the table exist
    ##
    if not self.__database.is_table_exist(table_name):
      get_logger().warning("{} table does not exist".format(table_name))
      return False
    
    ##
    ## 需要确认操作
    ##
    if not confirm:
      get_logger().warning("drop operation requires confirmation for table {}".format(table_name))
      return False
    
    ##
    ## 记录删除操作前的表信息
    ##
    try:
      with self.__database.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute("SELECT COUNT(*) AS row_count FROM {}".format(self._quote_identifier(table_name)))
          result = cursor.fetchone()
          if isinstance(result, dict):
            row_count = result.get('row_count', 0)
          elif result is None:
            row_count = 0
          else:
            row_count = result[0]
          get_logger().info("table {} has {} rows before drop".format(table_name, row_count))
    except Exception as e:
      get_logger().warning("failed to get row count before drop: {}".format(e))
    
    ##
    ## 执行删除操作
    ##
    try:
      with self.__database.get_connection() as connector:
        with connector.cursor() as cursor:
          ##
          ## 使用锁保护删除操作
          ##
          with self.__db_lock:
            cursor.execute(self.get_drop_sql_cmd())
            connector.commit()
          
          get_logger().info("{} table dropped successfully".format(table_name))
          
          ##
          ## 确认表确实已被删除
          ##
          if self.__database.is_table_exist(table_name):
            get_logger().error("table {} still exists after drop operation".format(table_name))
            return False
          
          return True
          
    except Exception as e:
      get_logger().error("failed to drop {} table: {}".format(table_name, e))
      return False

  ##
  ## insert record
  ##
  def insert_record(self, record: dict, on_duplicate: str = 'error') -> int:
    """
    向数据库中插入记录
    
    Args:
      record: 要插入的记录字典
      on_duplicate: 重复记录处理策略 ('error', 'ignore', 'update')
      
    Returns:
      int: 插入记录的主键值
      
    Raises:
      ValueError: 参数错误或重复记录策略不支持
    """
    ##
    ## check if the record is valid
    ##
    if not isinstance(record, dict):
      get_logger().error("record must be a dictionary")
      raise ValueError("record must be a dictionary")
    
    if not record:
      get_logger().warning("empty record provided for insertion")
      raise ValueError("empty record provided")
    
    if on_duplicate not in ['error', 'ignore', 'update']:
      raise ValueError("on_duplicate must be one of: 'error', 'ignore', 'update'")

    self._validate_record_keys(list(record.keys()))
    
    ##
    ## insert the record into the database
    ##
    try:
      ##
      ## filter out auto-increment primary key field
      ##
      filtered_keys = []
      filtered_values = []
      
      for key, value in record.items():
        ##
        ## skip auto-increment primary key field
        ##
        if key in self.get_auto_increment_field():
          get_logger().debug("skipping auto-increment field: {}".format(key))
          continue
        filtered_keys.append(key)
        filtered_values.append(value)

      if len(filtered_keys) == 0:
        raise ValueError("no insertable fields after filtering auto-increment fields")
      
      ##
      ## build INSERT SQL statement
      ##
      quoted_columns = [self._quote_identifier(key) for key in filtered_keys]
      columns_str = ', '.join(quoted_columns)
      placeholders_str = ', '.join(['%s' for _ in filtered_keys])
      
      sql = '''
        INSERT INTO {} ({})
        VALUES ({})
      '''.format(self._quote_identifier(self.get_name()), columns_str, placeholders_str)
      
      ##
      ## handle duplicate record strategy
      ##
      if on_duplicate == 'ignore':
        quoted_key = self._quote_identifier(filtered_keys[0])
        sql += " ON DUPLICATE KEY UPDATE {0} = {0}".format(quoted_key)
      elif on_duplicate == 'update':
        update_clause = ', '.join(["{0} = VALUES({0})".format(self._quote_identifier(key)) for key in filtered_keys])
        sql += " ON DUPLICATE KEY UPDATE " + update_clause
      
      ##
      ## prepare parameters
      ##
      params = tuple(filtered_values)
      get_logger().debug("executing SQL: {}".format(sql))
      get_logger().debug("with parameters: {}".format(params))
      with self.__database.get_connection() as connector:
        with connector.cursor() as cursor:       
          ##
          ## execute INSERT statement with database lock
          ##
          with self.__db_lock:
            cursor.execute(sql, params)
            connector.commit()
            
            ##
            ## handle insertion result
            ##
            if on_duplicate == 'ignore' and cursor.rowcount == 0:
              get_logger().warning("duplicate record ignored")
              return -1
            
            inserted_id = cursor.lastrowid
            if inserted_id and inserted_id != 0:
              get_logger().info("inserted record successfully with ID: {}".format(inserted_id))
            else:
              get_logger().info("inserted record successfully")
            return inserted_id or 0
    except Exception as e:
      get_logger().error("failed to insert record into {}: {}".format(self.get_name(), e))
      get_logger().error("record data: {}".format(record))
      raise e

  ##
  ## delete record
  ##
  def delete_record(self, conditions: dict, soft_delete: bool = False) -> int:
    """
    根据条件删除记录，支持软删除
    
    Args:
      conditions: 删除条件字典
      soft_delete: 是否使用软删除
      
    Returns:
      删除的记录数量
    """
    if not isinstance(conditions, dict) or not conditions:
      raise ValueError("Conditions must be a non-empty dictionary")

    self._validate_record_keys(list(conditions.keys()))
    
    try:
      with self.__database.get_connection() as connector:
        with connector.cursor() as cursor:
          where_parts = []
          params = []
          
          for key, value in conditions.items():
            where_parts.append("{} = %s".format(self._quote_identifier(key)))
            params.append(value)
          
          where_clause = ' AND '.join(where_parts)
          
          if soft_delete:
            ##
            ## 软删除：更新标记字段
            ##
            sql = f"""
              UPDATE {self._quote_identifier(self.get_name())}
              SET `is_deleted` = 1, `delete_time` = NOW()
              WHERE {where_clause}
            """
          else:
            ##
            ## 物理删除
            ##
            sql = "DELETE FROM {} WHERE {}".format(self._quote_identifier(self.get_name()), where_clause)
          
          ##
          ## 使用锁
          ##
          with self.__db_lock:
            cursor.execute(sql, params)
            affected_rows = cursor.rowcount
            connector.commit()
          
          action = "Soft deleted" if soft_delete else "Deleted"
          get_logger().info(f"{action} {affected_rows} record(s) with conditions: {conditions}")
          
          return affected_rows
          
    except Exception as e:
      get_logger().error(f"Failed to delete records with conditions {conditions}: {str(e)}")
      raise

  ##
  ## update record
  ##
  def update_record(self, record: dict) -> int:
    """
    更新数据库中的记录
    
    Args:
      record: 包含更新字段和主键值的字典
        
    Returns:
      更新的记录数量
    """
    ##
    ## 参数验证
    ##
    if not isinstance(record, dict):
      get_logger().error("Record must be a dictionary")
      raise ValueError("Record must be a dictionary")
    
    if not record:
      get_logger().warning("Empty update record provided")
      return 0

    self._validate_record_keys(list(record.keys()))
    
    ##
    ## 获取主键字段
    ##
    primary_keys = self.get_pri_key()
    
    ##
    ## 检查是否包含所有主键字段
    ##
    missing_primary_keys = [pk for pk in primary_keys if pk not in record]
    if missing_primary_keys:
      get_logger().error("Missing primary key fields: {}".format(missing_primary_keys))
      raise ValueError(f"Missing primary key fields: {missing_primary_keys}")
    
    try:
      with self.__database.get_connection() as connector:
        with connector.cursor() as cursor:
          ##
          ## 分离更新字段和主键字段
          ##
          update_fields = [key for key in record.keys() if key not in primary_keys]
          
          if not update_fields:
            get_logger().warning("No fields to update")
            return 0
          
          ##
          ## 安全构建SQL语句
          ##
          set_clause = ', '.join(["{} = %s".format(self._quote_identifier(field)) for field in update_fields])
          where_clause = ' AND '.join(["{} = %s".format(self._quote_identifier(pk)) for pk in primary_keys])
          
          sql = f"""
            UPDATE {self._quote_identifier(self.get_name())}
            SET {set_clause}
            WHERE {where_clause}
          """
          
          ##
          ## 准备参数：更新值 + 主键值
          ##
          update_values = [record[field] for field in update_fields]
          primary_values = [record[pk] for pk in primary_keys]
          params = update_values + primary_values
          
          get_logger().debug(f"Update SQL: {sql}")
          get_logger().debug(f"Update params: {params}")
          
          ##
          ## 使用锁
          ##
          lock_acquired = self.__db_lock.acquire(timeout=10)
          if not lock_acquired:
            raise TimeoutError("Failed to acquire database lock")
          
          try:
            ##
            ## 执行更新
            ##
            cursor.execute(sql, params)
            affected_rows = cursor.rowcount
            
            if affected_rows == 0:
              get_logger().warning(
                "No record found to update with primary keys: {}".format(
                  {pk: record[pk] for pk in primary_keys}
                )
              )
            else:
              get_logger().info(
                "Updated {} record(s) in {}".format(
                  affected_rows, self.get_name()
                )
              )
            
            connector.commit()
            return affected_rows
            
          finally:
            self.__db_lock.release()
            
    except Exception as e:
      get_logger().error("Failed to update {} record: {}".format(self.get_name(), str(e)))
      get_logger().error("Update data: {}".format(record))
      raise e

  ##
  ## get record
  ##
  def get_record(self, record: dict, fetchall: bool = False) -> list:
    """
    根据条件从数据库获取记录
    
    Args:
      record: 查询条件字典，如 {'platform': 'douyin', 'room_id': '123'}
        
    Returns:
      匹配的记录字典列表，如果未找到返回None
    """
    if not isinstance(record, dict) or not record:
      raise ValueError("record must be a non-empty dictionary")

    self._validate_record_keys(list(record.keys()))

    try:
      with self.__database.get_connection() as connector:
        with connector.cursor() as cursor:
          ##
          ## 安全地构建SQL查询
          ##
          where_conditions = []
          params = []
          
          for key, value in record.items():
            if value is not None:  ## 只处理非None的条件
              where_conditions.append("{} = %s".format(self._quote_identifier(key)))
              params.append(value)
          
          if not where_conditions:
            get_logger().warning("No valid conditions provided for query")
            return None
          
          header_sql = ', '.join([self._quote_identifier(key) for key in self.get_header()])
          sql = '''
            SELECT {} 
            FROM {}
            WHERE {}
            '''.format(
            header_sql,
            self._quote_identifier(self.get_name()),
            ' AND '.join(where_conditions)
          )
          
          get_logger().debug(f"Executing SQL: {sql}")
          get_logger().debug(f"With params: {params}")
          
          ##
          ## 获取数据库锁（带超时和重试机制）
          ##
          lock_acquired = self.__db_lock.acquire(timeout=10)  ## 10秒超时
          if not lock_acquired:
            get_logger().error("Failed to acquire database lock within timeout")
            raise TimeoutError("Database lock acquisition timeout")
          
          try:
            record_list = list()
            cursor.execute(sql, params)
            if fetchall:
              result = cursor.fetchall()
              
              ##
              ## check if the result is None
              ##
              if result is None:
                return None

              for row in result:
                if isinstance(row, dict):
                  record_dict = dict(row)
                else:
                  record_dict = dict(zip(self.get_header(), row))
                record_list.append(record_dict)
            else:
              result = cursor.fetchone()
              
              ##
              ## check if the result if None
              ##
              if result is None:
                return list()
              if isinstance(result, dict):
                record_list.append(dict(result))
              else:
                record_list.append(dict(zip(self.get_header(), result)))
            if result is None:
              get_logger().debug("{} record not found with conditions: {}".format(
                self.get_name(), record))
              return list()
            get_logger().debug("Record found: {}".format(record_list))
            return record_list            
          finally:
            self.__db_lock.release()
            
    except Exception as e:
      get_logger().error("Failed to get {} record: {}".format(self.get_name(), str(e)))
      get_logger().error("Query conditions: {}".format(record))
      raise e