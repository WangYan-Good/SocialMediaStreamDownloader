##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Third-Part>>
from backend.src.database.social_media_stream_database                import SocialMediaStreamDataBase
from backend.src.database.database_table.social_media_stream_db_table import SocialMediaStreamDataTable
from backend.src.base.log                                             import get_logger

class LiveStreamTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##

##
## live stream table header
## +------------------------------------------+-------------------+------+-----+---------+-------+------------------------------------------------------------+----------------------------------+
## | Field                                    | Type              | Null | Key | Default | Extra | Topology                                                   | Comment                          | 
## +------------------------------------------+-------------------+------+-----+---------+-------+------------------------------------------------------------+----------------------------------+
## | default_resolution                       | varchar(20)       | YES  |     | NULL    |       | "$.data.room.stream_url.default_resolution"                | 默认分辨率                        |
## | anchor_interact_profile                  | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.stream_url.extra.anchor_interact_profile"     | 主播互动配置文件                  |
## | audience_interact_profile                | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.stream_url.extra.audience_interact_profile"   | 观众互动配置文件                  |
## | bframe_enable                            | bool              | YES  |     | NULL    |       | "$.data.room.stream_url.extra.bframe_enable"               | B帧启用                          |
## | bitrate_adapt_strategy                   | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.stream_url.extra.bitrate_adapt_strategy"      | 比特率自适应策略                  |
## | bytevc1_enable                           | bool              | YES  |     | NULL    |       | "$.data.room.stream_url.extra.bytevc1_enable"              | 比特率自适应策略                  |
## | default_bitrate                          | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.stream_url.extra.default_bitrate"             | 默认比特率                        |
## | fps                                      | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.stream_url.extra.fps"                         | 帧率                              |
## | gop_sec                                  | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.stream_url.extra.gop_sec"                     | GOP秒数                          |
## | h265_enable                              | bool              | YES  |     | NULL    |       | "$.data.room.stream_url.extra.h265_enable"                 | H.265启用                        |
## | hardware_encode                          | bool              | YES  |     | NULL    |       | "$.data.room.stream_url.extra.hardware_encode"             | 硬件编码                          |
## | height                                   | unsigned smallint | YES  |     | NULL    |       | "$.data.room.stream_url.extra.height"                      | 高度                             |
## | max_bitrate                              | unsigned int      | YES  |     | NULL    |       | "$.data.room.stream_url.extra.max_bitrate"                 | 最大比特率                        |
## | min_bitrate                              | unsigned int      | YES  |     | NULL    |       | "$.data.room.stream_url.extra.min_bitrate"                 | 最小比特率                        |
## | roi                                      | bool              | YES  |     | NULL    |       | "$.data.room.stream_url.extra.roi"                         | 是否启用ROI（Region of Interest） |
## | sw_roi                                   | bool              | YES  |     | NULL    |       | "$.data.room.stream_url.extra.sw_roi"                      | 是否启用软件ROI                   |
## | video_profile                            | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.stream_url.extra.video_profile"               | 视频配置文件                      |
## | width                                    | unsigned smallint | YES  |     | NULL    |       | "$.data.room.stream_url.extra.width"                       | 宽度                             |
## | resolution_name                          | json              | YES  |     | NULL    |       | "$.data.room.stream_url.resolution_name"                   | 分辨率名称                        |
## | flv_pull_url                             | json              | YES  |     | NULL    |       | "$.data.room.stream_url.flv_pull_url"                      | 直播间FLV拉流地址                 |
## | flv_pull_url_params                      | json              | YES  |     | NULL    |       | "$.data.room.stream_url.flv_pull_url_params"               | FLV拉流地址参数                   |
## | hls_pull_url                             | text              | YES  |     | NULL    |       | "$.data.room.stream_url.hls_pull_url"                      | 直播间HLS拉流地址                 |
## | hls_pull_url_map                         | json              | YES  |     | NULL    |       | "$.data.room.stream_url.hls_pull_url_map"                  | 直播间HLS拉流地址映射              |
## | hls_pull_url_params                      | json              | YES  |     | NULL    |       | "$.data.room.stream_url.hls_pull_url_params"               | HLS拉流地址参数                   |
## | id                                       | varchar(200)      | NO   | PRI |         |       | "$.data.room.stream_url.id"                                | 直播间流ID                        |
## | provider                                 | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.stream_url.provider"                          | 直播间推流服务商                  |
## | pull_datas                               | json              | YES  |     | NULL    |       | "$.data.room.stream_url.pull_datas"                        | 拉流数据                          |
## | push_datas                               | json              | YES  |     | NULL    |       | "$.data.room.stream_url.push_datas"                        | 推流数据                          |
## | push_stream_type                         | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.stream_url.push_stream_type"                  | 推流类型                          |
## | rtmp_pull_url                            | text              | YES  |     | NULL    |       | "$.data.room.stream_url.rtmp_pull_url"                     | 直播间RTMP拉流地址                |
## | rtmp_pull_url_params                     | json              | YES  |     | NULL    |       | "$.data.room.stream_url.rtmp_pull_url_params"              | RTMP拉流地址参数                  |
## | rtmp_push_url                            | text              | YES  |     | NULL    |       | "$.data.room.stream_url.rtmp_push_url"                     | 直播间RTMP推流地址                |
## | rtmp_push_url_params                     | text              | YES  |     | NULL    |       | "$.data.room.stream_url.rtmp_push_url_params"              | RTMP推流地址参数                  |
## | stream_control_type                      | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.stream_url.stream_control_type"               | 直播间流控制类型                  |
## | stream_orientation                       | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.stream_url.stream_orientation"                | 直播间流方向：1-竖屏 2-横屏        |
## | vr_type                                  | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.stream_url.vr_type"                           | VR类型                           |
## +------------------------------------------+-------------------+------+-----+---------+-------+------------------------------------------------------------+----------------------------------+
## 
  __LIVE_STREAM_TABLE_NAME        = "live_stream"
  __LIVE_STREAM_TABLE_HEADER      = ['default_resolution',   'anchor_interact_profile', 'audience_interact_profile ',
                                     'bframe_enable',        'bitrate_adapt_strategy',  'bytevc1_enable',
                                     'default_bitrate',      'fps',                     'gop_sec',
                                     'h265_enable',          'hardware_encode',         'height',
                                     'max_bitrate',          'min_bitrate',             'roi',
                                     'sw_roi',               'video_profile',           'width',
                                     'resolution_name',      'flv_pull_url',            'flv_pull_url_params',
                                     'hls_pull_url',         'hls_pull_url_map',        'hls_pull_url_params',
                                     'id',                   'provider',                'pull_datas', 
                                     'push_datas',           'push_stream_type',        'rtmp_pull_url', 
                                     'rtmp_pull_url_params', 'rtmp_push_url',           'rtmp_push_url_params', 
                                     'stream_control_type',  'stream_orientation',      'vr_type'
                                     ]
  __LIVE_STREAM_TABLE_PRI_KEY     = ['id']
  __LIVE_STREAM_TABLE_TUPLE       = {item:None for item in __LIVE_STREAM_TABLE_HEADER}
  __SQL_CREATE_LIVE_STREAM_TABLE  = '''
                                    CREATE TABLE IF NOT EXISTS {} (
                                      default_resolution         varchar(20)  DEFAULT NULL,
                                      anchor_interact_profile    tinyint      DEFAULT NULL,
                                      audience_interact_profile  tinyint      DEFAULT NULL,
                                      bframe_enable              bool         DEFAULT NULL,
                                      bitrate_adapt_strategy     tinyint      DEFAULT NULL,
                                      bytevc1_enable             bool         DEFAULT NULL,
                                      default_bitrate            tinyint      DEFAULT NULL,
                                      fps                        tinyint      DEFAULT NULL,
                                      gop_sec                    tinyint      DEFAULT NULL,
                                      h265_enable                bool         DEFAULT NULL,
                                      hardware_encode            bool         DEFAULT NULL,
                                      height                     smallint     DEFAULT NULL,
                                      max_bitrate                int          DEFAULT NULL,
                                      min_bitrate                int          DEFAULT NULL,
                                      roi                        bool         DEFAULT NULL,
                                      sw_roi                     bool         DEFAULT NULL,
                                      video_profile              tinyint      DEFAULT NULL,
                                      width                      smallint     DEFAULT NULL,
                                      resolution_name            json         DEFAULT NULL,
                                      flv_pull_url               json         DEFAULT NULL,
                                      flv_pull_url_params        json         DEFAULT NULL,
                                      hls_pull_url               text         DEFAULT NULL,
                                      hls_pull_url_map           json         DEFAULT NULL,
                                      hls_pull_url_params        json         DEFAULT NULL,
                                      id                         varchar(200) NOT     NULL,
                                      provider                   tinyint      DEFAULT NULL,
                                      pull_datas                 json         DEFAULT NULL,
                                      push_datas                 json         DEFAULT NULL,
                                      push_stream_type           tinyint      DEFAULT NULL,
                                      rtmp_pull_url              text         DEFAULT NULL,
                                      rtmp_pull_url_params       json         DEFAULT NULL,
                                      rtmp_push_url              text         DEFAULT NULL,
                                      rtmp_push_url_params       text         DEFAULT NULL,
                                      stream_control_type        tinyint      DEFAULT NULL,
                                      stream_orientation         tinyint      DEFAULT NULL,
                                      vr_type                    tinyint      DEFAULT NULL,
                                      PRIMARY KEY (id)
                                    )
                                    '''.format(__LIVE_STREAM_TABLE_NAME)
  __SQL_DROP_LIVE_STREAM_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__LIVE_STREAM_TABLE_NAME)

##
## >>============================= private method =============================>>
##
  ##
  ## singleton pattern
  ##
  def __new__(cls, *args, **kwargs):
    return super().__new__(cls, *args, **kwargs)
  
  ##
  ## init method
  ##
  def __init__(self, db_instance:SocialMediaStreamDataBase = None) -> None:
    super().__init__(db_instance)

##
## >>============================= abstract method =============================>>
##
  ##
  ## get live stream table name
  ##
  def get_name(self) -> str:
    return self.__LIVE_STREAM_TABLE_NAME
  
  ##
  ## get live stream table header
  ##
  def get_header(self) -> list:
    return self.__LIVE_STREAM_TABLE_HEADER

  ##
  ## get live stream table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__LIVE_STREAM_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__LIVE_STREAM_TABLE_PRI_KEY

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_LIVE_STREAM_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_LIVE_STREAM_TABLE

##
## >>============================= sub class method =============================>>
##

##
## >>================================ test method ===============================>>
##

##
## test: create live_stream table
##
def test_create_live_stream_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create live_stream table
  ##
  live_stream = LiveStreamTable(db_instance=db)
  live_stream.create()
  return

##
## test: drop live_stream table
##
def test_drop_live_stream_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database is valid
  ##
  if db is None:
    get_logger().error("db_instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop live_stream table
  ##
  live_stream = LiveStreamTable(db)
  live_stream.drop()
  return

##
## test: check if live_stream table exists
##
def test_check_live_stream_table_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid {} instance".format(type(db)))
    raise ValueError
  
  ##
  ## check if live stream table exists
  ##
  live_stream = LiveStreamTable(db)
  if db.is_table_exist(live_stream.get_name()):
    get_logger().info("{} table exists!".format(live_stream.get_name()))
  else:
    get_logger().info("{} table not exists!".format(live_stream.get_name()))
  return

##
## test: insert live stream record
##
def test_insert_live_stream_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid {} instance".format(type(db)))
    raise ValueError
  
  ##
  ## create live_stream table if not exists
  ##
  live_stream = LiveStreamTable(db)
  sample_record = {
    "id": "691500607505433258",
  }
  
  ##
  ## insert a sample live stream record
  ##
  try:
    live_stream.insert_record(sample_record)
    get_logger().info("sample live stream record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample {} record: {}".format(live_stream.get_name(), e))
    raise e

##
## test: delete live stream record
##
def test_delete_live_stream_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create live_stream table if not exist
  ##
  live_stream = LiveStreamTable(db)
  
  ##
  ## delete a sample live stream record
  ##
  sample_record = {
    'id':'691500607505433258'
  }
  
  try:
    live_stream.delete_record(sample_record)
    get_logger().info("sample live stream record delete successfully")
  except Exception as e:
    get_logger().error("failed to delete sample live stream record: {}".format(e))
    raise e

##
## test: update live stream record
##
def test_update_live_stream_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## create live_stream table if not exist
  ##
  live_stream = LiveStreamTable(db)

  ##
  ## update a sample live stream record
  ##
  sample_record = {
    "id": "691500607505433258",
    "default_resolution":"FULL_HD1"
  }

  try:
    live_stream.update_record(sample_record)
    get_logger().info("sample live stream record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample live stream: {}".format(e))
    raise e

##
## test: get live stream record
##
def test_get_live_stream_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create live_stream table if not exist
  ##
  live_stream = LiveStreamTable(db)
  
  ##
  ## get a sample live stream record
  ##
  sample_record = {
    'id':'691500607505433258'
  }
  
  try:
    record = live_stream.get_record(sample_record)
    if record:
      get_logger().info("sample live stream record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample live record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample live stream record: {}".format(e))
    raise e

##
## >>================================ main method ===============================>>
##

if __name__ == "__main__":
  db = SocialMediaStreamDataBase(host='192.168.1.12', user='wangyan', passwd='wuyu1998', database='social_media_stream_downloader')
  test_create_live_stream_table(db)
  test_insert_live_stream_record(db)
  test_update_live_stream_record(db)
  test_get_live_stream_record(db)
  test_delete_live_stream_record(db)
  test_check_live_stream_table_exists(db)
  test_drop_live_stream_table(db)
  test_check_live_stream_table_exists(db)