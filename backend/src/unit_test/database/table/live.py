##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from datetime                                                         import datetime as dat

## <<Third-Part>>
from backend.src.database.social_media_stream_database                import SocialMediaStreamDataBase
from backend.src.database.table.live                                  import LiveRecordTable
from backend.src.base.log                                             import get_logger
from backend.src.unit_test.test_db_config                             import get_test_db_config

##
## >>================================ live record table test method ===============================>>
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
  live_record.drop(confirm=True)
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
    'owner_user_id': '2700838411446480',
    'user_id': '0',
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
    'owner_user_id':'2700838411446480',
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
  db = SocialMediaStreamDataBase(**get_test_db_config())

  ##
  ## live record table
  ##
  test_check_live_record_table_exists(db)
  test_create_live_record_table(db)
  test_insert_live_record(db)
  test_check_live_record_table_exists(db)
  test_get_live_record(db)
  test_update_live_record(db)
  test_delete_live_record(db)
  test_drop_live_record_table(db)