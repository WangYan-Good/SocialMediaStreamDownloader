##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from typing import Dict, Any, cast

## <<Third-Part>>
from backend.src.database.table.share_url import DouyinShareUrlTable
from backend.src.library.loglib           import get_logger
from backend.src.unit_test.test_db_config import get_test_db_config


def _get_db() -> DouyinShareUrlTable:
  return DouyinShareUrlTable(**get_test_db_config())


def _sample_record() -> Dict[str, str]:
  return {
    "owner_user_id": "ut-owner-001",
    "sec_user_id": "ut-sec-001",
    "nickname": "ut_nickname",
    "post_share_url": "https://v.douyin.com/ut-post-001/",
    "live_share_url": "https://v.douyin.com/ut-live-001/",
    "directory_name": "ut_dir_001",
    "user_status": "normal",
  }


def test_create_share_url_table() -> None:
  db = _get_db()
  sql = '''
          CREATE TABLE IF NOT EXISTS share_url (
            owner_user_id     VARCHAR(200) NOT NULL,
            sec_user_id       VARCHAR(200) DEFAULT NULL,
            nickname          VARCHAR(50)  DEFAULT NULL,
            post_share_url    VARCHAR(100) DEFAULT NULL,
            live_share_url    VARCHAR(100) DEFAULT NULL,
            directory_name    VARCHAR(100) DEFAULT NULL,
            user_status       VARCHAR(100) DEFAULT NULL,
            actived_count     INT UNSIGNED NOT NULL DEFAULT 0,
            PRIMARY KEY (owner_user_id),
            INDEX idx_nickname (nickname)
          ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        '''
  with db.get_connection() as connector:
    with connector.cursor() as cursor:
      cursor.execute(sql)
      connector.commit()
  get_logger().info("test create share_url table success")


def test_insert_record() -> None:
  db = _get_db()
  record = _sample_record()
  sql = '''
          INSERT INTO share_url (
            owner_user_id,
            sec_user_id,
            nickname,
            post_share_url,
            live_share_url,
            directory_name,
            user_status
          ) VALUES (%s, %s, %s, %s, %s, %s, %s)
          ON DUPLICATE KEY UPDATE
            sec_user_id = VALUES(sec_user_id),
            nickname = VALUES(nickname),
            post_share_url = VALUES(post_share_url),
            live_share_url = VALUES(live_share_url),
            directory_name = VALUES(directory_name),
            user_status = VALUES(user_status)
        '''
  params = (
    record["owner_user_id"],
    record["sec_user_id"],
    record["nickname"],
    record["post_share_url"],
    record["live_share_url"],
    record["directory_name"],
    record["user_status"],
  )
  with db.get_connection() as connector:
    with connector.cursor() as cursor:
      cursor.execute(sql, params)
      connector.commit()
  get_logger().info("test insert share_url record success")


def test_search_record_from_table() -> None:
  db = _get_db()
  url = _sample_record()["live_share_url"]
  exists = db.is_live_share_url_record_exist(url)
  assert exists is True
  get_logger().info("test search share_url record success")


def test_increment_actived_count() -> None:
  db = _get_db()
  owner_user_id = _sample_record()["owner_user_id"]

  with db.get_connection() as connector:
    with connector.cursor() as cursor:
      cursor.execute("SELECT actived_count FROM share_url WHERE owner_user_id = %s", (owner_user_id,))
      before_row = cursor.fetchone()
      if isinstance(before_row, dict):
        before_dict = cast(dict[str, Any], before_row)
        before = int(before_dict.get("actived_count", 0))
      elif before_row is None:
        before = 0
      else:
        before = int(before_row[0])

  db.increment_live_actived_count(owner_user_id)

  with db.get_connection() as connector:
    with connector.cursor() as cursor:
      cursor.execute("SELECT actived_count FROM share_url WHERE owner_user_id = %s", (owner_user_id,))
      after_row = cursor.fetchone()
      if isinstance(after_row, dict):
        after_dict = cast(dict[str, Any], after_row)
        after = int(after_dict.get("actived_count", 0))
      elif after_row is None:
        after = 0
      else:
        after = int(after_row[0])

  assert after == before + 1
  get_logger().info("test increment actived_count success")


def test_drop_db_table() -> None:
  db = _get_db()
  with db.get_connection() as connector:
    with connector.cursor() as cursor:
      cursor.execute("DROP TABLE IF EXISTS share_url;")
      connector.commit()
  get_logger().info("test drop share_url table success")


if __name__ == "__main__":
  test_create_share_url_table()
  test_insert_record()
  test_search_record_from_table()
  test_increment_actived_count()
  test_drop_db_table()