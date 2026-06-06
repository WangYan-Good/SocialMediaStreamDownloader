##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Third-Part>>
from dotenv import load_dotenv
from typing import TypedDict


load_dotenv()


class TestDBConfig(TypedDict):
  host: str
  user: str
  passwd: str
  database: str


def get_test_db_config() -> TestDBConfig:
  return {
    'host': os.getenv('MYSQL_HOST', os.getenv('DB_HOST', '127.0.0.1')),
    'user': os.getenv('MYSQL_USER', os.getenv('DB_USER', 'admin')),
    'passwd': os.getenv('MYSQL_PASSWORD', os.getenv('DB_PASSWORD', os.getenv('DB_PASS', 'admin'))),
    'database': os.getenv('MYSQL_DB_NAME', os.getenv('DB_NAME', 'test_social_media_stream_downloader')),
  }
