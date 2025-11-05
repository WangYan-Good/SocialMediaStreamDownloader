##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Third-Part>>
from backend.src.database.social_media_stream_database       import SocialMediaStreamDataBase
from backend.src.database.table.social_media_stream_db_table import SocialMediaStreamDataTable
from backend.src.base.log                                    import get_logger

def create_table(db:SocialMediaStreamDataBase, table:str):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## create table instance
  ##
  SocialMediaStreamDataTable.get_subclass_by_table_name(table=table)(db_instance=db).create()
  return

def is_table_exist(db:SocialMediaStreamDataBase, table:str) -> bool:
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## check table instance
  ##
  return db.is_table_exist(table_name=table)

def drop_table(db:SocialMediaStreamDataBase, table:str):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## drop table instance
  ##
  SocialMediaStreamDataTable.get_subclass_by_table_name(table=table)(db_instance=db).drop(confirm=True)
  return

def insert_record(db:SocialMediaStreamDataBase, table:str, record:dict):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## insert record into table
  ##
  SocialMediaStreamDataTable.get_subclass_by_table_name(table=table)(db_instance=db).insert_record(record=record)
  return

def delete_record(db:SocialMediaStreamDataBase, table:str, condition:dict):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## delete record from table
  ##
  SocialMediaStreamDataTable.get_subclass_by_table_name(table=table)(db_instance=db).delete_record(condition=condition)
  return

def update_record(db:SocialMediaStreamDataBase, table:str, new_value:dict):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## update record in table
  ##
  SocialMediaStreamDataTable.get_subclass_by_table_name(table=table)(db_instance=db).update_record(new_value)
  return

def get_record(db:SocialMediaStreamDataBase, table:str, condition:dict, force:bool = False) -> list:
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## get record from table
  ##
  return SocialMediaStreamDataTable.get_subclass_by_table_name(table=table)(db_instance=db).get_record(record=condition, force=force)