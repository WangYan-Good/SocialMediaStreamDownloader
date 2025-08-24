##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Third-Part>>
from backend.src.database.social_media_stream_database                import SocialMediaStreamDataBase
from backend.src.database.table.social_media_stream_db_table          import SocialMediaStreamDataTable

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
class LiveStreamTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
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

"""
##
## $.data.room.stream_url
##
## +---------------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------------------+
## | Field                     | Type              | Null | Key | Default | Extra | Topology                                                 | Comment                          | 
## +---------------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------------------+
## | default_resolution        | varchar(20)       |      |     | NULL    |       | "$.data.room.stream_url.default_resolution"              | 默认分辨率                        |
## | anchor_interact_profile   | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stream_url.extra.anchor_interact_profile"   | 主播互动配置文件                  |
## | audience_interact_profile | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stream_url.extra.audience_interact_profile" | 观众互动配置文件                  |
## | bframe_enable             | bool              |      |     | NULL    |       | "$.data.room.stream_url.extra.bframe_enable"             | B帧启用                          |
## | bitrate_adapt_strategy    | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stream_url.extra.bitrate_adapt_strategy"    | 比特率自适应策略                  |
## | bytevc1_enable            | bool              |      |     | NULL    |       | "$.data.room.stream_url.extra.bytevc1_enable"            | 比特率自适应策略                  |
## | default_bitrate           | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stream_url.extra.default_bitrate"           | 默认比特率                        |
## | fps                       | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stream_url.extra.fps"                       | 帧率                              |
## | gop_sec                   | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stream_url.extra.gop_sec"                   | GOP秒数                          |
## | h265_enable               | bool              |      |     | NULL    |       | "$.data.room.stream_url.extra.h265_enable"               | H.265启用                        |
## | hardware_encode           | bool              |      |     | NULL    |       | "$.data.room.stream_url.extra.hardware_encode"           | 硬件编码                          |
## | height                    | unsigned smallint |      |     | NULL    |       | "$.data.room.stream_url.extra.height"                    | 高度                             |
## | max_bitrate               | unsigned int      |      |     | NULL    |       | "$.data.room.stream_url.extra.max_bitrate"               | 最大比特率                        |
## | min_bitrate               | unsigned int      |      |     | NULL    |       | "$.data.room.stream_url.extra.min_bitrate"               | 最小比特率                        |
## | roi                       | bool              |      |     | NULL    |       | "$.data.room.stream_url.extra.roi"                       | 是否启用ROI（Region of Interest） |
## | sw_roi                    | bool              |      |     | NULL    |       | "$.data.room.stream_url.extra.sw_roi"                    | 是否启用软件ROI                   |
## | video_profile             | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stream_url.extra.video_profile"             | 视频配置文件                      |
## | width                     | unsigned smallint |      |     | NULL    |       | "$.data.room.stream_url.extra.width"                     | 宽度                             |
## | resolution_name           | json              |      |     | NULL    |       | "$.data.room.stream_url.resolution_name"                 | 分辨率名称                        |
## | flv_pull_url              | json              |      |     | NULL    |       | "$.data.room.stream_url.flv_pull_url"                    | 直播间FLV拉流地址                 |
## | flv_pull_url_params       | json              |      |     | NULL    |       | "$.data.room.stream_url.flv_pull_url_params"             | FLV拉流地址参数                   |
## | hls_pull_url              | text              |      |     | NULL    |       | "$.data.room.stream_url.hls_pull_url"                    | 直播间HLS拉流地址                 |
## | hls_pull_url_map          | json              |      |     | NULL    |       | "$.data.room.stream_url.hls_pull_url_map"                | 直播间HLS拉流地址映射              |
## | hls_pull_url_params       | json              |      |     | NULL    |       | "$.data.room.stream_url.hls_pull_url_params"             | HLS拉流地址参数                   |
## | id                        | varchar(200)      | NO   | PRI |         |       | "$.data.room.stream_url.id"                              | 直播间流ID                        |
## | provider                  | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stream_url.provider"                        | 直播间推流服务商                  |
## | pull_datas                | json              |      |     | NULL    |       | "$.data.room.stream_url.pull_datas"                      | 拉流数据                          |
## | push_datas                | json              |      |     | NULL    |       | "$.data.room.stream_url.push_datas"                      | 推流数据                          |
## | push_stream_type          | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stream_url.push_stream_type"                | 推流类型                          |
## | rtmp_pull_url             | text              |      |     | NULL    |       | "$.data.room.stream_url.rtmp_pull_url"                   | 直播间RTMP拉流地址                |
## | rtmp_pull_url_params      | json              |      |     | NULL    |       | "$.data.room.stream_url.rtmp_pull_url_params"            | RTMP拉流地址参数                  |
## | rtmp_push_url             | text              |      |     | NULL    |       | "$.data.room.stream_url.rtmp_push_url"                   | 直播间RTMP推流地址                |
## | rtmp_push_url_params      | text              |      |     | NULL    |       | "$.data.room.stream_url.rtmp_push_url_params"            | RTMP推流地址参数                  |
## | stream_control_type       | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stream_url.stream_control_type"             | 直播间流控制类型                  |
## | stream_orientation        | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stream_url.stream_orientation"              | 直播间流方向：1-竖屏 2-横屏        |
## | vr_type                   | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stream_url.vr_type"                         | VR类型                           |
## +---------------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------------------+
##
class LiveStreamTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __LIVE_STREAM_TABLE_NAME       = "live_stream"
  __LIVE_STREAM_TABLE_HEADER     = ['default_resolution',   'anchor_interact_profile', 'audience_interact_profile', 'bframe_enable',       'bitrate_adapt_strategy',
                                    'bytevc1_enable',       'default_bitrate',         'fps',                       'gop_sec',             'h265_enable',
                                    'hardware_encode',      'height',                  'max_bitrate',               'min_bitrate',         'roi',
                                    'sw_roi',               'video_profile',           'width',                     'resolution_name',     'flv_pull_url',
                                    'flv_pull_url_params',  'hls_pull_url',            'hls_pull_url_map',          'hls_pull_url_params', 'id',
                                    'provider',             'pull_datas',              'push_datas',                'push_stream_type',    'rtmp_pull_url',
                                    'rtmp_pull_url_params', 'rtmp_push_url',           'rtmp_push_url_params',      'stream_control_type', 'stream_orientation',
                                    'vr_type',
                                    ]
  __LIVE_STREAM_TABLE_PRI_KEY    = ['id']
  __LIVE_STREAM_TABLE_TUPLE      = {item:None for item in __LIVE_STREAM_TABLE_HEADER}
  __SQL_CREATE_LIVE_STREAM_TABLE = '''
                                   CREATE TABLE IF NOT EXISTS {} (
                                     default_resolution         varchar(20)       DEFAULT NULL,
                                     anchor_interact_profile    tinyint           DEFAULT NULL,
                                     audience_interact_profile  tinyint           DEFAULT NULL,
                                     bframe_enable              bool              DEFAULT NULL,
                                     bitrate_adapt_strategy     tinyint           DEFAULT NULL,
                                     bytevc1_enable             bool              DEFAULT NULL,
                                     default_bitrate            tinyint           DEFAULT NULL,
                                     fps                        tinyint           DEFAULT NULL,
                                     gop_sec                    tinyint           DEFAULT NULL,
                                     h265_enable                bool              DEFAULT NULL,
                                     hardware_encode            bool              DEFAULT NULL,
                                     height                     smallint          DEFAULT NULL,
                                     max_bitrate                int               DEFAULT NULL,
                                     min_bitrate                int               DEFAULT NULL,
                                     roi                        bool              DEFAULT NULL,
                                     sw_roi                     bool              DEFAULT NULL,
                                     video_profile              tinyint           DEFAULT NULL,
                                     width                      smallint          DEFAULT NULL,
                                     resolution_name            json              DEFAULT NULL,
                                     flv_pull_url               json              DEFAULT NULL,
                                     flv_pull_url_params        json              DEFAULT NULL,
                                     hls_pull_url               text              DEFAULT NULL,
                                     hls_pull_url_map           json              DEFAULT NULL,
                                     hls_pull_url_params        json              DEFAULT NULL,
                                     id                         varchar(200)      NOT NULL,
                                     provider                   tinyint           DEFAULT NULL,
                                     pull_datas                 json              DEFAULT NULL,
                                     push_datas                 json              DEFAULT NULL,
                                     push_stream_type           tinyint           DEFAULT NULL,
                                     rtmp_pull_url              text              DEFAULT NULL,
                                     rtmp_pull_url_params       json              DEFAULT NULL,
                                     rtmp_push_url              text              DEFAULT NULL,
                                     rtmp_push_url_params       text              DEFAULT NULL,
                                     stream_control_type        tinyint           DEFAULT NULL,
                                     stream_orientation         tinyint           DEFAULT NULL,
                                     vr_type                    tinyint           DEFAULT NULL,
                                     PRIMARY KEY (id)
                                   )
                                   '''.format(__LIVE_STREAM_TABLE_NAME)
  __SQL_DROP_LIVE_STREAM_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__LIVE_STREAM_TABLE_NAME)

##
## >>============================= private method =============================>>
##
  ##
  ## singleton mode
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
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__LIVE_STREAM_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__LIVE_STREAM_TABLE_HEADER

  ##
  ## get table tuple
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
"""
##
## data.room.stream_url.candidate_resolution
##
## +----------------------+-------------------+------+-----+---------+-------+-----------------------------------------------+---------------------+
## | Field                | Type              | Null | Key | Default | Extra | Topology                                      | Comment             |
## +----------------------+-------------------+------+-----+---------+-------+-----------------------------------------------+---------------------+
## | now                  | timestamp(3)      | NO   | PRI |         |       | "$.data.room.create_time"                     | 当前时间戳           | 
## | platform             | varchar(20)       | NO   | PRI |         |       |           -                                   | 平台                 | 
## | room_id              | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                              | 直播间ID             | 
## | stream_id            | varchar(200)      | NO   | PRI |         |       | "$.data.room.stream_id"                       | 直播间流ID           |
## | resolution_index     | unsigned tinyint  | NO   | PRI |         |       |           -                                   | 分辨率索引           | 
## | candidate_resolution | varchar(20)       |      |     | NULL    |       | "$.data.room.stream_url.candidate_resolution" | 候选分辨率           | 
## +----------------------+-------------------+------+-----+---------+-------+-----------------------------------------------+---------------------+
##
class StreamCandidateResolutionTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __STREAM_CANDIDATE_RESOLUTION_TABLE_NAME       = "stream_candidate_resolution"
  __STREAM_CANDIDATE_RESOLUTION_TABLE_HEADER     = ['now', 'platform', 'room_id', 'stream_id', 'resolution_index', 'candidate_resolution']
  __STREAM_CANDIDATE_RESOLUTION_TABLE_PRI_KEY    = ['now', 'platform', 'room_id', 'stream_id', 'resolution_index']
  __STREAM_CANDIDATE_RESOLUTION_TABLE_TUPLE      = {item:None for item in __STREAM_CANDIDATE_RESOLUTION_TABLE_HEADER}
  __SQL_CREATE_STREAM_CANDIDATE_RESOLUTION_TABLE = '''
                                                   CREATE TABLE IF NOT EXISTS {} (
                                                     now                    timestamp(3) NOT NULL,
                                                     platform               varchar(20)  NOT NULL,
                                                     room_id                varchar(200) NOT NULL,
                                                     stream_id              varchar(200) NOT NULL,
                                                     resolution_index       tinyint      NOT NULL,
                                                     candidate_resolution   varchar(20)  DEFAULT NULL,
                                                     PRIMARY KEY (now, platform, room_id, stream_id, resolution_index)
                                                   )
                                                   '''.format(__STREAM_CANDIDATE_RESOLUTION_TABLE_NAME)
  __SQL_DROP_STREAM_CANDIDATE_RESOLUTION_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__STREAM_CANDIDATE_RESOLUTION_TABLE_NAME)

##
## >>============================= private method =============================>>
##
  ##
  ## singleton mode
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
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__STREAM_CANDIDATE_RESOLUTION_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__STREAM_CANDIDATE_RESOLUTION_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__STREAM_CANDIDATE_RESOLUTION_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__STREAM_CANDIDATE_RESOLUTION_TABLE_PRI_KEY

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_STREAM_CANDIDATE_RESOLUTION_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_STREAM_CANDIDATE_RESOLUTION_TABLE

##
## data.room.stream_url.complete_push_urls
##
## +-------------------------+-------------------+------+-----+---------+-------+---------------------------------------------+---------------------+
## | Field                   | Type              | Null | Key | Default | Extra | Topology                                    | Comment             |
## +-------------------------+-------------------+------+-----+---------+-------+---------------------------------------------+---------------------+
## | now                     | timestamp(3)      | NO   | PRI |         |       | "$.data.room.create_time"                   | 当前时间戳           | 
## | platform                | varchar(20)       | NO   | PRI |         |       |           -                                 | 平台                 | 
## | room_id                 | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                            | 直播间ID             |
## | stream_id               | varchar(200)      | NO   | PRI |         |       | "$.data.room.stream_id"                     | 直播间流ID           |
## | complete_push_url_index | unsigned tinyint  | NO   | PRI |         |       |           -                                 | 完整推流地址序号     | 
## | complete_push_url       | text              |      |     | NULL    |       | "$.data.room.stream_url.complete_push_urls" | 完整推流地址         |
## +-------------------------+-------------------+------+-----+---------+-------+---------------------------------------------+---------------------+
##
class StreamCompletePushUrlTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __STREAM_COMPLETE_PUSH_URL_TABLE_NAME       = "stream_complete_push_url"
  __STREAM_COMPLETE_PUSH_URL_TABLE_HEADER     = ['now', 'platform', 'room_id', 'stream_id', 'complete_push_url_index', 'complete_push_url']
  __STREAM_COMPLETE_PUSH_URL_TABLE_PRI_KEY    = ['now', 'platform', 'room_id', 'stream_id', 'complete_push_url_index']
  __STREAM_COMPLETE_PUSH_URL_TABLE_TUPLE      = {item:None for item in __STREAM_COMPLETE_PUSH_URL_TABLE_HEADER}
  __SQL_CREATE_STREAM_COMPLETE_PUSH_URL_TABLE = '''
                                                   CREATE TABLE IF NOT EXISTS {} (
                                                     now                     timestamp(3) NOT NULL,
                                                     platform                varchar(20)  NOT NULL,
                                                     room_id                 varchar(200) NOT NULL,
                                                     stream_id               varchar(200) NOT NULL,
                                                     complete_push_url_index tinyint      NOT NULL,
                                                     complete_push_url       varchar(20)  DEFAULT NULL,
                                                     PRIMARY KEY (now, platform, room_id, stream_id, complete_push_url_index)
                                                   )
                                                   '''.format(__STREAM_COMPLETE_PUSH_URL_TABLE_NAME)
  __SQL_DROP_STREAM_COMPLETE_PUSH_URL_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__STREAM_COMPLETE_PUSH_URL_TABLE_NAME)

##
## >>============================= private method =============================>>
##
  ##
  ## singleton mode
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
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__STREAM_COMPLETE_PUSH_URL_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__STREAM_COMPLETE_PUSH_URL_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__STREAM_COMPLETE_PUSH_URL_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__STREAM_COMPLETE_PUSH_URL_TABLE_PRI_KEY

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_STREAM_COMPLETE_PUSH_URL_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_STREAM_COMPLETE_PUSH_URL_TABLE

##
## data.room.stream_url.live_core_sdk_data
##
## +----------+--------------+------+-----+---------+-------+--------------------------------------------------+---------------------+
## | Field    | Type         | Null | Key | Default | Extra | Topology                                         | Comment             |
## +----------+--------------+------+-----+---------+-------+--------------------------------------------------+---------------------+
## | now      | timestamp(3) | NO   | PRI |         |       | "$.data.room.create_time"                        | 当前时间戳           | 
## | platform | varchar(20)  | NO   | PRI |         |       |           -                                      | 平台                 | 
## | room_id  | varchar(200) | NO   | PRI |         |       | "$.data.room.id"                                 | 直播间ID             |
## | size     | varchar(100) |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.size" | 流大小              |
## +----------+--------------+------+-----+---------+-------+--------------------------------------------------+---------------------+
##
class LiveCoreSdkDataTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __LIVE_CORE_SDK_DATA_TABLE_NAME       = "live_core_sdk_data"
  __LIVE_CORE_SDK_DATA_TABLE_HEADER     = ['now', 'platform', 'room_id', 'size']
  __LIVE_CORE_SDK_DATA_TABLE_PRI_KEY    = ['now', 'platform', 'room_id']
  __LIVE_CORE_SDK_DATA_TABLE_TUPLE      = {item:None for item in __LIVE_CORE_SDK_DATA_TABLE_HEADER}
  __SQL_CREATE_LIVE_CORE_SDK_DATA_TABLE = '''
                                          CREATE TABLE IF NOT EXISTS {} (
                                            now                     timestamp(3) NOT NULL,
                                            platform                varchar(20)  NOT NULL,
                                            room_id                 varchar(200) NOT NULL,
                                            size                    varchar(100) DEFAULT NULL,
                                            PRIMARY KEY (now, platform, room_id)
                                          )
                                          '''.format(__LIVE_CORE_SDK_DATA_TABLE_NAME)
  __SQL_DROP_LIVE_CORE_SDK_DATA_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__LIVE_CORE_SDK_DATA_TABLE_NAME)

##
## >>============================= private method =============================>>
##
  ##
  ## singleton mode
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
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__LIVE_CORE_SDK_DATA_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__LIVE_CORE_SDK_DATA_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__LIVE_CORE_SDK_DATA_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__LIVE_CORE_SDK_DATA_TABLE_PRI_KEY

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_LIVE_CORE_SDK_DATA_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_LIVE_CORE_SDK_DATA_TABLE

##
## data.room.stream_url.live_core_sdk_data.pull_data
##
## +----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------------------------+---------------------+
## | Field                | Type              | Null | Key | Default | Extra | Topology                                                                   | Comment             |
## +----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------------------------+---------------------+
## | now                  | timestamp(3)      | NO   | PRI |         |       | "$.data.room.create_time"                                                  | 当前时间戳           | 
## | platform             | varchar(20)       | NO   | PRI |         |       |           -                                                                | 平台                 | 
## | room_id              | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                                                           | 直播间ID             |
## | codec                | varchar(100)      |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.codec"                | 编解码器             |
## | compensatory_data    | text              |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.compensatory_data"    | 补偿数据             |
## | hls_data_unencrypted | json              |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.hls_data_unencrypted" | HLS未加密数据        |
## | kind                 | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.kind"                 | 类型                |
## | stream_data          | text              |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.stream_data"          | 流数据内容           |
## | version              | varchar(20)       |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.version"              | 版本                |
## +----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------------------------+---------------------+
##
class LiveCoreSdkPullDataTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __LIVE_CORE_SDK_PULL_DATA_TABLE_NAME       = "live_core_sdk_pull_data"
  __LIVE_CORE_SDK_PULL_DATA_TABLE_HEADER     = ['now', 'platform', 'room_id', 'codec', 'compensatory_data', 'hls_data_unencrypted', 'kind', 'stream_data', 'version']
  __LIVE_CORE_SDK_PULL_DATA_TABLE_PRI_KEY    = ['now', 'platform', 'room_id']
  __LIVE_CORE_SDK_PULL_DATA_TABLE_TUPLE      = {item:None for item in __LIVE_CORE_SDK_PULL_DATA_TABLE_HEADER}
  __SQL_CREATE_LIVE_CORE_SDK_PULL_DATA_TABLE = '''
                                               CREATE TABLE IF NOT EXISTS {} (
                                                 now                     timestamp(3) NOT NULL,
                                                 platform                varchar(20)  NOT NULL,
                                                 room_id                 varchar(200) NOT NULL,
                                                 codec                   varchar(100) DEFAULT NULL,
                                                 compensatory_data       text         DEFAULT NULL,
                                                 hls_data_unencrypted    json         DEFAULT NULL,
                                                 kind                    tinyint      DEFAULT NULL,
                                                 stream_data             text         DEFAULT NULL,
                                                 version                 varchar(20)  DEFAULT NULL,
                                                 PRIMARY KEY (now, platform, room_id)
                                               )
                                               '''.format(__LIVE_CORE_SDK_PULL_DATA_TABLE_NAME)
  __SQL_DROP_LIVE_CORE_SDK_PULL_DATA_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__LIVE_CORE_SDK_PULL_DATA_TABLE_NAME)

##
## >>============================= private method =============================>>
##
  ##
  ## singleton mode
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
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__LIVE_CORE_SDK_PULL_DATA_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__LIVE_CORE_SDK_PULL_DATA_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__LIVE_CORE_SDK_PULL_DATA_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__LIVE_CORE_SDK_PULL_DATA_TABLE_PRI_KEY

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_LIVE_CORE_SDK_PULL_DATA_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_LIVE_CORE_SDK_PULL_DATA_TABLE


##
## data.room.stream_url.live_core_sdk_data.pull_data.Flv
##
## +-----------+------------------+------+-----+---------+-------+-----------------------------------------------------------+---------------------+
## | Field     | Type             | Null | Key | Default | Extra | Topology                                                  | Comment             |
## +-----------+------------------+------+-----+---------+-------+-----------------------------------------------------------+---------------------+
## | now       | timestamp(3)     | NO   | PRI |         |       | "$.data.room.create_time"                                 | 当前时间戳           | 
## | platform  | varchar(20)      | NO   | PRI |         |       |           -                                               | 平台                 | 
## | room_id   | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                                          | 直播间ID             |
## | Flv_index | unsigned tinyint | NO   | PRI |         |       |           -                                               | Flv序号              | 
## | Flv       | text             |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.Flv" | Flv数据             |
## +-----------+------------------+------+-----+---------+-------+-----------------------------------------------------------+---------------------+
##
class LiveCoreSdkPullFlvDataTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __LIVE_CORE_SDK_PULL_FLV_DATA_TABLE_NAME       = "live_core_sdk_pull_flv_data"
  __LIVE_CORE_SDK_PULL_FLV_DATA_TABLE_HEADER     = ['now', 'platform', 'room_id', 'Flv_index', 'Flv']
  __LIVE_CORE_SDK_PULL_FLV_DATA_TABLE_PRI_KEY    = ['now', 'platform', 'room_id', 'Flv_index']
  __LIVE_CORE_SDK_PULL_FLV_DATA_TABLE_TUPLE      = {item:None for item in __LIVE_CORE_SDK_PULL_FLV_DATA_TABLE_HEADER}
  __SQL_CREATE_LIVE_CORE_SDK_PULL_FLV_DATA_TABLE = '''
                                                   CREATE TABLE IF NOT EXISTS {} (
                                                     now                     timestamp(3) NOT NULL,
                                                     platform                varchar(20)  NOT NULL,
                                                     room_id                 varchar(200) NOT NULL,
                                                     Flv_index               tinyint      NOT NULL,
                                                     Flv                     text         DEFAULT NULL,
                                                     PRIMARY KEY (now, platform, room_id, Flv_index)
                                                   )
                                                   '''.format(__LIVE_CORE_SDK_PULL_FLV_DATA_TABLE_NAME)
  __SQL_DROP_LIVE_CORE_SDK_PULL_FLV_DATA_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__LIVE_CORE_SDK_PULL_FLV_DATA_TABLE_NAME)

##
## >>============================= private method =============================>>
##
  ##
  ## singleton mode
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
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__LIVE_CORE_SDK_PULL_FLV_DATA_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__LIVE_CORE_SDK_PULL_FLV_DATA_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__LIVE_CORE_SDK_PULL_FLV_DATA_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__LIVE_CORE_SDK_PULL_FLV_DATA_TABLE_PRI_KEY

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_LIVE_CORE_SDK_PULL_FLV_DATA_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_LIVE_CORE_SDK_PULL_FLV_DATA_TABLE

##
## data.room.stream_url.live_core_sdk_data.pull_data.Hls
##
## +-----------+------------------+------+-----+---------+-------+-----------------------------------------------------------+---------------------+
## | Field     | Type             | Null | Key | Default | Extra | Topology                                                  | Comment             |
## +-----------+------------------+------+-----+---------+-------+-----------------------------------------------------------+---------------------+
## | now       | timestamp(3)     | NO   | PRI |         |       | "$.data.room.create_time"                                 | 当前时间戳           | 
## | platform  | varchar(20)      | NO   | PRI |         |       |           -                                               | 平台                 | 
## | room_id   | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                                          | 直播间ID             |
## | Hls_index | unsigned tinyint | NO   | PRI |         |       |           -                                               | Hls序号              | 
## | Hls       | text             |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.Hls" | Hls数据             |
## +-----------+------------------+------+-----+---------+-------+-----------------------------------------------------------+---------------------+
##
class LiveCoreSdkPullHlsDataTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __LIVE_CORE_SDK_PULL_HLS_DATA_TABLE_NAME       = "live_core_sdk_pull_hls_data"
  __LIVE_CORE_SDK_PULL_HLS_DATA_TABLE_HEADER     = ['now', 'platform', 'room_id', 'Hls_index', 'Hls']
  __LIVE_CORE_SDK_PULL_HLS_DATA_TABLE_PRI_KEY    = ['now', 'platform', 'room_id', 'Hls_index']
  __LIVE_CORE_SDK_PULL_HLS_DATA_TABLE_TUPLE      = {item:None for item in __LIVE_CORE_SDK_PULL_HLS_DATA_TABLE_HEADER}
  __SQL_CREATE_LIVE_CORE_SDK_PULL_HLS_DATA_TABLE = '''
                                                   CREATE TABLE IF NOT EXISTS {} (
                                                     now                     timestamp(3) NOT NULL,
                                                     platform                varchar(20)  NOT NULL,
                                                     room_id                 varchar(200) NOT NULL,
                                                     Hls_index               tinyint      NOT NULL,
                                                     Hls                     text         DEFAULT NULL,
                                                     PRIMARY KEY (now, platform, room_id, Hls_index)
                                                   )
                                                   '''.format(__LIVE_CORE_SDK_PULL_HLS_DATA_TABLE_NAME)
  __SQL_DROP_LIVE_CORE_SDK_PULL_HLS_DATA_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__LIVE_CORE_SDK_PULL_HLS_DATA_TABLE_NAME)

##
## >>============================= private method =============================>>
##
  ##
  ## singleton mode
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
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__LIVE_CORE_SDK_PULL_HLS_DATA_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__LIVE_CORE_SDK_PULL_HLS_DATA_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__LIVE_CORE_SDK_PULL_HLS_DATA_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__LIVE_CORE_SDK_PULL_HLS_DATA_TABLE_PRI_KEY

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_LIVE_CORE_SDK_PULL_HLS_DATA_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_LIVE_CORE_SDK_PULL_HLS_DATA_TABLE

##
## data.room.stream_url.live_core_sdk_data.pull_data.options
##
## +---------------+--------------+------+-----+---------+-------+----------------------------------------------------------------------------+---------------------+
## | Field         | Type         | Null | Key | Default | Extra | Topology                                                                   | Comment             |
## +---------------+--------------+------+-----+---------+-------+----------------------------------------------------------------------------+---------------------+
## | now           | timestamp(3) | NO   | PRI |         |       | "$.data.room.create_time"                                                  | 当前时间戳           | 
## | platform      | varchar(20)  | NO   | PRI |         |       |           -                                                                | 平台                 | 
## | room_id       | varchar(200) | NO   | PRI |         |       | "$.data.room.id"                                                           | 直播间ID             |
## | vpass_default | bool         |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.vpass_default"| 视频默认通过         |
## +---------------+--------------+------+-----+---------+-------+----------------------------------------------------------------------------+---------------------+
##
class LiveCoreSdkPullDataOptionTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __LIVE_CORE_SDK_PULL_DATA_OPTION_TABLE_NAME       = "live_core_sdk_pull_data_option"
  __LIVE_CORE_SDK_PULL_DATA_OPTION_TABLE_HEADER     = ['now', 'platform', 'room_id', 'vpass_default']
  __LIVE_CORE_SDK_PULL_DATA_OPTION_TABLE_PRI_KEY    = ['now', 'platform', 'room_id']
  __LIVE_CORE_SDK_PULL_DATA_OPTION_TABLE_TUPLE      = {item:None for item in __LIVE_CORE_SDK_PULL_DATA_OPTION_TABLE_HEADER}
  __SQL_CREATE_LIVE_CORE_SDK_PULL_DATA_OPTION_TABLE = '''
                                                      CREATE TABLE IF NOT EXISTS {} (
                                                        now                     timestamp(3) NOT NULL,
                                                        platform                varchar(20)  NOT NULL,
                                                        room_id                 varchar(200) NOT NULL,
                                                        vpass_default           bool         DEFAULT NULL,
                                                        PRIMARY KEY (now, platform, room_id)
                                                      )
                                                      '''.format(__LIVE_CORE_SDK_PULL_DATA_OPTION_TABLE_NAME)
  __SQL_DROP_LIVE_CORE_SDK_PULL_DATA_OPTION_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__LIVE_CORE_SDK_PULL_DATA_OPTION_TABLE_NAME)

##
## >>============================= private method =============================>>
##
  ##
  ## singleton mode
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
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__LIVE_CORE_SDK_PULL_DATA_OPTION_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__LIVE_CORE_SDK_PULL_DATA_OPTION_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__LIVE_CORE_SDK_PULL_DATA_OPTION_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__LIVE_CORE_SDK_PULL_DATA_OPTION_TABLE_PRI_KEY

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_LIVE_CORE_SDK_PULL_DATA_OPTION_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_LIVE_CORE_SDK_PULL_DATA_OPTION_TABLE

##
## data.room.stream_url.live_core_sdk_data.pull_data.options.qualities
##
## +--------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------------------------------+---------------------+
## | Field              | Type              | Null | Key | Default | Extra | Topology                                                                                   | Comment             |
## +--------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------------------------------+---------------------+
## | now                | timestamp(3)      | NO   | PRI |         |       | "$.data.room.create_time"                                                                  | 当前时间戳           | 
## | platform           | varchar(20)       | NO   | PRI |         |       |           -                                                                                | 平台                 | 
## | room_id            | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                                                                           | 直播间ID             |
## | quality_index      | unsigned tinyint  | NO   | PRI |         |       |           -                                                                                | 视频流质量序号        |
## | additional_content | text              |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities.additional_content" | 附加内容             |
## | disable            | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities.disable"            | 默认质量禁用标志     |
## | fps                | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities.fps"                | 帧率                |
## | level              | unsigned smallint |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities.level"              | 级别                |
## | name               | varchar(50)       |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities.name"               | 名称                |
## | resolution         | varchao(50)       |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities.resolution"         | 分辨率              |
## | sdk_key            | varchar(100)      |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities.sdk_key"            | SDK密钥             |
## | v_bit_rate         | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities.v_bit_rate"         | 视频比特率           |
## | v_codec            | varchar(100)      |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities.v_codec"            | 视频编解码器         |
## +--------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------------------------------+---------------------+
##
class LiveCoreSdkPullQualityDataTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __LIVE_CORE_SDK_PULL_QUALITY_DATA_TABLE_NAME       = "live_core_sdk_pull_quality_data"
  __LIVE_CORE_SDK_PULL_QUALITY_DATA_TABLE_HEADER     = ['now', 'platform', 'room_id', 'quality_index', 'disable', 'fps', 'level', 'name', 'resolution', 'sdk_key', 'v_bit_rate', 'v_codec']
  __LIVE_CORE_SDK_PULL_QUALITY_DATA_TABLE_PRI_KEY    = ['now', 'platform', 'room_id', 'quality_index']
  __LIVE_CORE_SDK_PULL_QUALITY_DATA_TABLE_TUPLE      = {item:None for item in __LIVE_CORE_SDK_PULL_QUALITY_DATA_TABLE_HEADER}
  __SQL_CREATE_LIVE_CORE_SDK_PULL_QUALITY_DATA_TABLE = '''
                                                       CREATE TABLE IF NOT EXISTS {} (
                                                         now                     timestamp(3) NOT NULL,
                                                         platform                varchar(20)  NOT NULL,
                                                         room_id                 varchar(200) NOT NULL,
                                                         quality_index           tinyint      NOT NULL,
                                                         disable                 tinyint      DEFAULT NULL,
                                                         fps                     tinyint      DEFAULT NULL,
                                                         level                   smallint     DEFAULT NULL,
                                                         name                    varchar(50)  DEFAULT NULL,
                                                         resolution              varchar(50)  DEFAULT NULL,
                                                         sdk_key                 varchar(100) DEFAULT NULL,
                                                         v_bit_rate              tinyint      DEFAULT NULL,
                                                         v_codec                 varchar(100) DEFAULT NULL,
                                                         PRIMARY KEY (now, platform, room_id, quality_index)
                                                       )
                                                       '''.format(__LIVE_CORE_SDK_PULL_QUALITY_DATA_TABLE_NAME)
  __SQL_DROP_LIVE_CORE_SDK_PULL_QUALITY_DATA_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__LIVE_CORE_SDK_PULL_QUALITY_DATA_TABLE_NAME)

##
## >>============================= private method =============================>>
##
  ##
  ## singleton mode
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
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__LIVE_CORE_SDK_PULL_QUALITY_DATA_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__LIVE_CORE_SDK_PULL_QUALITY_DATA_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__LIVE_CORE_SDK_PULL_QUALITY_DATA_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__LIVE_CORE_SDK_PULL_QUALITY_DATA_TABLE_PRI_KEY

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_LIVE_CORE_SDK_PULL_QUALITY_DATA_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_LIVE_CORE_SDK_PULL_QUALITY_DATA_TABLE

##
## data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality
##
## +--------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------------------------------------+---------------------+
## | Field              | Type              | Null | Key | Default | Extra | Topology                                                                                         | Comment             |
## +--------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------------------------------------+---------------------+
## | now                | timestamp(3)      | NO   | PRI |         |       | "$.data.room.create_time"                                                                        | 当前时间戳           | 
## | platform           | varchar(20)       | NO   | PRI |         |       |           -                                                                                      | 平台                 | 
## | room_id            | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                                                                                 | 直播间ID             |
## | additional_content | text              |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.additional_content" | 附加内容            |
## | disable            | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.disable"            | 默认质量禁用标志     |
## | fps                | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.fps"                | 帧率                |
## | level              | unsigned smallint |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.level"              | 级别                |
## | name               | varchar(50)       |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.name"               | 名称                |
## | resolution         | varchao(50)       |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.resolution"         | 分辨率              |
## | sdk_key            | varchar(100)      |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.sdk_key"            | SDK密钥             |
## | v_bit_rate         | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.v_bit_rate"         | 视频比特率           |
## | v_codec            | varchar(100)      |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.v_codec"            | 视频编解码器         |
## +--------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------------------------------------+---------------------+
##
class LiveCoreSdkPullDefaultQualityDataTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __LIVE_CORE_SDK_PULL_DEFAULT_QUALITY_DATA_TABLE_NAME       = "live_core_sdk_pull_default_quality_data"
  __LIVE_CORE_SDK_PULL_DEFAULT_QUALITY_DATA_TABLE_HEADER     = ['now', 'platform', 'room_id', 'additional_content', 'disable', 'fps', 'level', 'name', 'resolution', 'sdk_key', 'v_bit_rate', 'v_codec']
  __LIVE_CORE_SDK_PULL_DEFAULT_QUALITY_DATA_TABLE_PRI_KEY    = ['now', 'platform', 'room_id']
  __LIVE_CORE_SDK_PULL_DEFAULT_QUALITY_DATA_TABLE_TUPLE      = {item:None for item in __LIVE_CORE_SDK_PULL_DEFAULT_QUALITY_DATA_TABLE_HEADER}
  __SQL_CREATE_LIVE_CORE_SDK_PULL_DEFAULT_QUALITY_DATA_TABLE = '''
                                                               CREATE TABLE IF NOT EXISTS {} (
                                                                 now                     timestamp(3) NOT NULL,
                                                                 platform                varchar(20)  NOT NULL,
                                                                 room_id                 varchar(200) NOT NULL,
                                                                 additional_content      text         DEFAULT NULL,
                                                                 disable                 tinyint      DEFAULT NULL,
                                                                 fps                     tinyint      DEFAULT NULL,
                                                                 level                   smallint     DEFAULT NULL,
                                                                 name                    varchar(50)  DEFAULT NULL,
                                                                 resolution              varchar(50)  DEFAULT NULL,
                                                                 sdk_key                 varchar(100) DEFAULT NULL,
                                                                 v_bit_rate              tinyint      DEFAULT NULL,
                                                                 v_codec                 varchar(100) DEFAULT NULL,
                                                                 PRIMARY KEY (now, platform, room_id, quality_index)
                                                               )
                                                               '''.format(__LIVE_CORE_SDK_PULL_DEFAULT_QUALITY_DATA_TABLE_NAME)
  __SQL_DROP_LIVE_CORE_SDK_PULL_DEFAULT_QUALITY_DATA_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__LIVE_CORE_SDK_PULL_DEFAULT_QUALITY_DATA_TABLE_NAME)

##
## >>============================= private method =============================>>
##
  ##
  ## singleton mode
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
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__LIVE_CORE_SDK_PULL_DEFAULT_QUALITY_DATA_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__LIVE_CORE_SDK_PULL_DEFAULT_QUALITY_DATA_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__LIVE_CORE_SDK_PULL_DEFAULT_QUALITY_DATA_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__LIVE_CORE_SDK_PULL_DEFAULT_QUALITY_DATA_TABLE_PRI_KEY

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_LIVE_CORE_SDK_PULL_DEFAULT_QUALITY_DATA_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_LIVE_CORE_SDK_PULL_DEFAULT_QUALITY_DATA_TABLE

##
## data.room.stream_url.push_urls
##
## +----------------+------------------+------+-----+---------+-------+------------------------------------+---------------------+
## | Field          | Type             | Null | Key | Default | Extra | Topology                           | Comment             |
## +----------------+------------------+------+-----+---------+-------+------------------------------------+---------------------+
## | now            | timestamp(3)     | NO   | PRI |         |       | "$.data.room.create_time"          | 当前时间戳           | 
## | platform       | varchar(20)      | NO   | PRI |         |       |           -                        | 平台                 | 
## | room_id        | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                   | 直播间ID             |
## | stream_id      | varchar(200)     | NO   | PRI |         |       | "$.data.room.stream_url.id"        | 直播流ID             |
## | push_url_index | unsigned tinyint | NO   | PRI |         |       |           -                        | 推流地址序号         | 
## | push_url       | text             |      |     | NULL    |       | "$.data.room.stream_url.push_urls" | 推流地址             |
## +----------------+------------------+------+-----+---------+-------+------------------------------------+---------------------+
##
class StreamPushUrlTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __STREAM_PUSH_URL_TABLE_NAME       = "stream_push_url"
  __STREAM_PUSH_URL_TABLE_HEADER     = ['now', 'platform', 'room_id', 'stream_id', 'push_url_index', 'push_url']
  __STREAM_PUSH_URL_TABLE_PRI_KEY    = ['now', 'platform', 'room_id', 'stream_id', 'push_url_index']
  __STREAM_PUSH_URL_TABLE_TUPLE      = {item:None for item in __STREAM_PUSH_URL_TABLE_HEADER}
  __SQL_CREATE_STREAM_PUSH_URL_TABLE = '''
                                       CREATE TABLE IF NOT EXISTS {} (
                                         now                     timestamp(3) NOT NULL,
                                         platform                varchar(20)  NOT NULL,
                                         room_id                 varchar(200) NOT NULL,
                                         stream_id               varchar(200) NOT NULL,
                                         push_url_index          tinyint      NOT NULL,
                                         push_url                text         DEFAULT NULL,
                                         PRIMARY KEY (now, platform, room_id, quality_index)
                                       )
                                       '''.format(__STREAM_PUSH_URL_TABLE_NAME)
  __SQL_DROP_STREAM_PUSH_URL_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__STREAM_PUSH_URL_TABLE_NAME)

##
## >>============================= private method =============================>>
##
  ##
  ## singleton mode
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
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__STREAM_PUSH_URL_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__STREAM_PUSH_URL_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__STREAM_PUSH_URL_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__STREAM_PUSH_URL_TABLE_PRI_KEY

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_STREAM_PUSH_URL_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_STREAM_PUSH_URL_TABLE
