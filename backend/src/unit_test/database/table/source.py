##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from datetime                                                         import datetime as dat

## <<Third-Part>>
from backend.src.database.social_media_stream_database                import SocialMediaStreamDataBase
from backend.src.database.table.source                                import BadgeImageTable
from backend.src.base.log                                             import get_logger

##
## >>================================ room owner table test method ===============================>>
##

def test_create_badge_image_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  badge_image = BadgeImageTable(db_instance=db)
  badge_image.create()
  return

##
## test: drop table
##
def test_drop_badge_image_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  badge_image = BadgeImageTable(db_instance=db)
  badge_image.drop()
  return

##
## test: check if table exists
##
def test_check_badge_image_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  badge_image = BadgeImageTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(badge_image.get_name()):
    get_logger().info("{} table exists!".format(badge_image.get_name()))
  else:
    get_logger().info("{} table not exists!".format(badge_image.get_name()))
  return

##
## test: insert record
##
def test_insert_badge_image_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  badge_image = BadgeImageTable(db_instance=db)
  
  ##
  ## insert a sample record
  ##
  sample_record = {
    'badge_image_index': 0,
    'version': '123456789',
    'uri': '1080x1080/aweme-avatar/tos-cn-avt-0015_073398e34f18e2e545861a83f392ad9f'
  }
  
  try:
    badge_image.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_badge_image_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  badge_image = BadgeImageTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'badge_image_index': 0
  }
  
  try:
    badge_image.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_badge_image_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  badge_image = BadgeImageTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'badge_image_index': 0,
    'version': '123',
    'uri': '720x720/aweme-avatar/tos-cn-avt-0015_073398e34f18e2e545861a83f392ad9f'
  }
  
  try:
    badge_image.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_badge_image_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  badge_image = BadgeImageTable(db)
  
  ##
  ## get a sample record
  ##
  sample_record = {
    'badge_image_index': 0
  }
  
  try:
    record = badge_image.get_record(sample_record)
    if record:
      get_logger().info("sample {} record retrieved successfully: \n\t{}".format(badge_image.get_name(), record))
    else:
      get_logger().warning("sample {} record not found".format(badge_image.get_name()))
  except Exception as e:
    get_logger().error("failed to retrieve sample {} record: {}".format(badge_image.get_name(), e))
    raise e

##
## >>================================ main method ===============================>>
##
if __name__ == "__main__":
  db = SocialMediaStreamDataBase(host='192.168.1.12', user='wangyan', passwd='wuyu1998', database='social_media_stream_downloader')
  """
  ##
  ## room owner table
  ##
  test_create_badge_image_table(db)
  test_check_badge_image_exists(db)
  test_insert_badge_image_record(db)
  test_get_badge_image_record(db)
  test_update_badge_image_record(db)
  test_get_badge_image_record(db)
  test_delete_badge_image_record(db)
  test_get_badge_image_record(db)
  test_drop_badge_image_table(db)
  test_check_badge_image_exists(db)
  """