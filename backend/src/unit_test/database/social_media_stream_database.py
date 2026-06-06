##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from typing import Any, cast

## <<Third-Part>>
from backend.src.database.social_media_stream_database import SocialMediaStreamDataBase
from backend.src.base.log                              import get_logger
from backend.src.unit_test.test_db_config              import get_test_db_config

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
  db = SocialMediaStreamDataBase(**get_test_db_config())
  with db.get_connection() as connector:
    connector = cast(Any, connector)
    with connector.cursor() as cursor:
      get_logger().debug(sql)
      cursor.execute(sql)
      result = cursor.fetchall()
      get_logger().debug(result)

##
## test: insert owner id into owner_liked table
##
def test_insert_owner_into_liked_table(owner_user_id:str, platform:str):
  try:
    sql = '''
            insert into favorite_owner (owner_user_id, platform) values ("{}", "{}");
          '''.format(owner_user_id, platform)
    db = SocialMediaStreamDataBase(**get_test_db_config())
    with db.get_connection() as connector:
      connector = cast(Any, connector)
      with connector.cursor() as cursor:
        cursor.execute(sql)
        connector.commit()
    get_logger().info("insert {} into liked table succeed!".format(owner_user_id))
  except Exception as e:
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
  db = SocialMediaStreamDataBase(**get_test_db_config())
  if db.is_table_exist("live_record"):
    get_logger().info("live_record table exists!")
  else:
    get_logger().info("live_record table not exists!")
  return

if __name__ == "__main__":
  # test_search_sec_user_id("https://v.douyin.com/ikRBs7Sy/")
  # test_insert_owner_into_liked_table("3171420333409886", "douyin")
  test_check_live_record_table_exists()