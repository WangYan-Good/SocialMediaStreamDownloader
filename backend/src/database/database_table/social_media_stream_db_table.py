##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from threading import Lock
from abc       import ABC, abstractmethod

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
  __TABLE_TUPLE          = {item:None for item in __TABLE_HEADER}
  
  __SQL_CMD_CREATE_TABLE = str()
  __SQL_CMD_DROP_TABLE   = str()
  

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
    ## register the room attribute table when room_attribute table is exist but not registered
    ##
    if self.__database.is_table_exist(self.get_name()) and self.__database.is_table_registered(self.get_name()) is False:
      try:
        self.__database.register_table(self.get_name(), self)
        get_logger().info("room attribute table registered successfully")
      except Exception as e:
        get_logger().error("failed to register room attribute table: {}".format(e))
        raise e
    else:
      get_logger().info("room_attribute table is already registered or does not exist")
    return

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
## >>============================= sub class method =============================>>
##
  ##
  ## create table
  ##
  def create(self) -> None:
    ##
    ## check if the table already exists
    ##
    try:
        if self.__database.is_table_exist(self.get_name()):
          get_logger().warning("room attribute table already exists, skipping creation")
          return
    except Exception as e:
      get_logger().error("failed to create room attribute table: {}".format(e))
      raise e
    
    ##
    ## create the room attribute table
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
          cursor.execute(self.get_create_sql_cmd())
          connector.commit()
          get_logger().info("room attribute table created successfully")
    except Exception as e:
      get_logger().error("failed to create room attribute table: {}".format(e))
      raise e
    
    ##
    ## register the room attribute table
    ##
    try:
      self.__database.register_table(self.get_name(), self)
      get_logger().info("room_attribute table registered successfully")
    except Exception as e:
      get_logger().error("failed to register room_attribute table: {}".format(e))
      raise e
  
  ##
  ## drop table
  ##
  def drop(self) -> None:
    ##
    ## check if the room attribute table exist
    ##
    if not self.__database.is_table_exist(self.get_name()):
      get_logger().warning("{} table does note exist, skipping drop".format(self.get_name()))
      return
    
    ##
    ## unregister the room attribute table
    ##
    try:
      self.__database.unregister_table(self.get_name())
      get_logger().info("{} table unregistered successfully".format(self.get_name()))
    except Exception as e:
      get_logger().error("failed to unregister {} table: {}".format(self.get_name(), e))
      raise e
    
    ##
    ## drop the room attribute table
    ##
    try:
      with self.__database.get_db_connector() as connector:
        with connector.cursor() as cursor:
          with self.__db_lock:
            cursor.execute(self.get_drop_sql_cmd())
            connector.commit()
          get_logger().info("{} table dropped successfully".format(self.get_name()))
    except Exception as e:
      get_logger().error("failed to drop {} table: {}".format(self.get_name(), e))
      raise e

  ##
  ## insert record
  ##
  def insert_record(self, record: dict) -> None:
    ##
    ## check if the record is valid
    ##
    if not isinstance(record, dict):
      get_logger().error("record must be a dictionary")
      raise ValueError
    
    ##
    ## check if the primary key fields are present in the record
    ##
    for field in self.get_pri_key():
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
          ## insert the room attribute record into room_attribute table
          ##
          sql = '''
                INSERT INTO {} ({})
                VALUES ({})
                '''.format(self.get_name(), ', '.join([item for item in record.keys()]), ', '.join(['%s' for item in [item for item in record.keys()]]))
          with self.__db_lock:
            cursor.execute(sql, tuple(value for value in record.values()))
            connector.commit()
          get_logger().info("inserted room attribute record successfully")
    except Exception as e:
      get_logger().error("failed to insert room attribute record: {}".format(e))
      raise e

  ##
  ## delete record
  ##
  def delete_record(self, record: dict) -> None:
    ##
    ## check if the primary key fields are present in the record
    ##
    for field in self.get_pri_key():
      if field not in record:
        get_logger().error("record must contain the primary key field: {}".format(field))
        raise ValueError
    
    ##
    ## delete the room attribute record from the database
    ##
    try:
      with self.__database.get_db_connector() as connector:
        with connector.cursor() as cursor:
          sql = '''
                DELETE FROM {}
                WHERE {}
                '''.format(self.get_name(), ' AND '.join(item + ' = %s' for item in self.get_pri_key()))
          with self.__db_lock:
            cursor.execute(sql, tuple(record.get(field) for field in self.get_pri_key()))
            connector.commit()
    except Exception as e:
      get_logger().error("failed to delete room attribute record: {}".format(e))
      raise e

  ##
  ## update record
  ##
  def update_record(self, record: dict) -> None:
    ##
    ## check if the record is valid
    ##
    if not isinstance(record, dict):
      get_logger().error("record must be a dictionary")
      raise ValueError
    
    ##
    ## check if the primary key fields are present in the record
    ##
    for field in self.get_pri_key():
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
                SET {}
                WHERE {}
                '''.format(self.get_name(), ', '.join([item + ' = %s' for item in record.keys()]), ' AND '.join(item + ' = %s' for item in self.get_pri_key()))
          with self.__db_lock:
            cursor.execute(sql, tuple(record.get(field) for field in [item for item in record.keys()] + self.get_pri_key()))
            connector.commit()
          get_logger().info("update room attribute record successfully")
    except Exception as e:
      get_logger().error("failed to update room attribute record: {}".format(e))
      raise e
  
  ##
  ## get record
  ##
  def get_record(self, record: dict) -> dict:
    ##
    ## check if the primary key fields are present in the record
    ##
    for field in self.get_pri_key():
      if field not in record:
        get_logger().error("record must contain the primary key field: {}".format(field))
        raise ValueError
    
    ##
    ## get the room attribute record from the database
    ##
    try:
      with self.__database.get_db_connector() as connector:
        with connector.cursor() as cursor:
          sql = '''
                SELECT {} 
                FROM {}
                WHERE {}
                '''.format(', '.join(self.get_header()), self.get_name(), ' AND '.join([item + ' = %s' for item in self.get_pri_key()]))
          
          ##
          ## check if the lock is acquired
          ##
          self.__db_lock.acquire(False)
          cursor.execute(sql, tuple(record.get(field) for field in self.get_pri_key()))
          result = cursor.fetchone()
          self.__db_lock.release()
          if result is None:
            get_logger().warning("room attribute record not found")
            return None
      return dict(zip(self.get_header(), result))
    except Exception as e:
      get_logger().error("failed to get room attribute record: {}".format(e))
      raise e