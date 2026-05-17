##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Third-Part>>
from backend.src.database.social_media_stream_database                import SocialMediaStreamDataBase
from backend.src.database.table.social_media_stream_db_table          import SocialMediaStreamDataTable

##
## room_stream
##
## +-------------------------------------+-------------------+------+-----+---------+-------+----------------------------------------+---------------------+
## | Field                               | Type              | Null | Key | Default | Extra | Topology                               | Comment             |
## +-------------------------------------+-------------------+------+-----+---------+-------+----------------------------------------+---------------------+
## | platform                            | varchar(20)       | NO   | PRI |         |       | "$.platform"                           | 平台                |
## | start_time                          | datetime          | NO   | PRI |         |       | "$.data.start_time"                    | 直播开始时间         |
## | room_id                             | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                       | 直播间 ID           |
## | default_resolution                  | varchar(20)       | YES  |     | NULL    |       | "$.data.room.stream_url.default_resolution" | 默认分辨率      |
## | hls_pull_url                        | text              | YES  |     | NULL    |       | "$.data.room.stream_url.hls_pull_url"  | HLS 拉流 URL        |
## | rtmp_pull_url                       | text              | YES  |     | NULL    |       | "$.data.room.stream_url.rtmp_pull_url" | RTMP 拉流 URL       |
## | rtmp_pull_url_params                | text              | YES  |     | NULL    |       | "$.data.room.stream_url.rtmp_pull_url_params" | RTMP 拉流参数 |
## | rtmp_push_url                       | text              | YES  |     | NULL    |       | "$.data.room.stream_url.rtmp_push_url" | RTMP 推流 URL       |
## | rtmp_push_url_params                | text              | YES  |     | NULL    |       | "$.data.room.stream_url.rtmp_push_url_params" | RTMP 推流参数 |
## | stream_id                           | bigint            | YES  |     | NULL    |       | "$.data.room.stream_url.id"            | 流 ID               |
## | stream_id_str                       | varchar(200)      | YES  |     | NULL    |       | "$.data.room.stream_url.id_str"        | 流 ID 字符串         |
## | multi_stream_scene                  | tinyint           | YES  |     | 0       |       | "$.data.room.stream_url.multi_stream_scene" | 多流场景      |
## | provider                            | tinyint           | YES  |     | 0       |       | "$.data.room.stream_url.provider"      | 提供者              |
## | stream_control_type                 | tinyint           | YES  |     | 0       |       | "$.data.room.stream_url.stream_control_type" | 流控制类型  |
## | stream_orientation                  | tinyint           | YES  |     | 0       |       | "$.data.room.stream_url.stream_orientation" | 流方向      |
## | vr_type                             | tinyint           | YES  |     | 0       |       | "$.data.room.stream_url.vr_type"       | VR 类型             |
## | resolution_name_sd1                 | varchar(50)       | YES  |     | NULL    |       | "$.data.room.stream_url.resolution_name.SD1" | 标清分辨率名称 |
## | resolution_name_sd2                 | varchar(50)       | YES  |     | NULL    |       | "$.data.room.stream_url.resolution_name.SD2" | 高清分辨率名称 |
## | resolution_name_hd1                 | varchar(50)       | YES  |     | NULL    |       | "$.data.room.stream_url.resolution_name.HD1" | 超清分辨率名称 |
## | resolution_name_full_hd1            | varchar(50)       | YES  |     | NULL    |       | "$.data.room.stream_url.resolution_name.FULL_HD1" | 蓝光分辨率名称 |
## | flv_pull_url_sd1                    | text              | YES  |     | NULL    |       | "$.data.room.stream_url.flv_pull_url.SD1" | 标清 FLV 拉流 URL  |
## | flv_pull_url_sd2                    | text              | YES  |     | NULL    |       | "$.data.room.stream_url.flv_pull_url.SD2" | 高清 FLV 拉流 URL  |
## | flv_pull_url_hd1                    | text              | YES  |     | NULL    |       | "$.data.room.stream_url.flv_pull_url.HD1" | 超清 FLV 拉流 URL  |
## | flv_pull_url_full_hd1               | text              | YES  |     | NULL    |       | "$.data.room.stream_url.flv_pull_url.FULL_HD1" | 蓝光 FLV 拉流 URL |
## | hls_pull_url_sd1                    | text              | YES  |     | NULL    |       | "$.data.room.stream_url.hls_pull_url_map.SD1" | 标清 HLS 拉流 URL |
## | hls_pull_url_sd2                    | text              | YES  |     | NULL    |       | "$.data.room.stream_url.hls_pull_url_map.SD2" | 高清 HLS 拉流 URL |
## | hls_pull_url_hd1                    | text              | YES  |     | NULL    |       | "$.data.room.stream_url.hls_pull_url_map.HD1" | 超清 HLS 拉流 URL |
## | hls_pull_url_full_hd1               | text              | YES  |     | NULL    |       | "$.data.room.stream_url.hls_pull_url_map.FULL_HD1" | 蓝光 HLS 拉流 URL |
## | flv_params_sd1                      | text              | YES  |     | NULL    |       | "$.data.room.stream_url.flv_pull_url_params.SD1" | 标清 FLV 参数 |
## | flv_params_sd2                      | text              | YES  |     | NULL    |       | "$.data.room.stream_url.flv_pull_url_params.SD2" | 高清 FLV 参数 |
## | flv_params_hd1                      | text              | YES  |     | NULL    |       | "$.data.room.stream_url.flv_pull_url_params.HD1" | 超清 FLV 参数 |
## | flv_params_full_hd1                 | text              | YES  |     | NULL    |       | "$.data.room.stream_url.flv_pull_url_params.FULL_HD1" | 蓝光 FLV 参数 |
## | hls_params                          | text              | YES  |     | NULL    |       | "$.data.room.stream_url.hls_pull_url_params" | HLS 参数       |
## | extra_anchor_interact_profile       | tinyint           | YES  |     | 0       |       | "$.data.room.stream_url.extra.anchor_interact_profile" | 主播互动档案 |
## | extra_audience_interact_profile     | tinyint           | YES  |     | 0       |       | "$.data.room.stream_url.extra.audience_interact_profile" | 观众互动档案 |
## | extra_bframe_enable                 | bool              | YES  |     | FALSE   |       | "$.data.room.stream_url.extra.bframe_enable" | B 帧启用     |
## | extra_bitrate_adapt_strategy        | tinyint           | YES  |     | 0       |       | "$.data.room.stream_url.extra.bitrate_adapt_strategy" | 码率自适应策略 |
## | extra_business_name                 | varchar(100)      | YES  |     | NULL    |       | "$.data.room.stream_url.extra.business_name" | 业务名称   |
## | extra_bytevc1_enable                | bool              | YES  |     | FALSE   |       | "$.data.room.stream_url.extra.bytevc1_enable" | ByteVC1 启用 |
## | extra_default_bitrate               | int               | YES  |     | 0       |       | "$.data.room.stream_url.extra.default_bitrate" | 默认码率   |
## | extra_fps                           | tinyint           | YES  |     | 0       |       | "$.data.room.stream_url.extra.fps"     | 帧率                |
## | extra_gop_sec                       | tinyint           | YES  |     | 0       |       | "$.data.room.stream_url.extra.gop_sec" | GOP 秒数            |
## | extra_h265_enable                   | bool              | YES  |     | FALSE   |       | "$.data.room.stream_url.extra.h265_enable" | H265 启用    |
## | extra_hardware_encode               | bool              | YES  |     | FALSE   |       | "$.data.room.stream_url.extra.hardware_encode" | 硬件编码   |
## | extra_height                        | int               | YES  |     | 0       |       | "$.data.room.stream_url.extra.height"  | 高度                |
## | extra_width                         | int               | YES  |     | 0       |       | "$.data.room.stream_url.extra.width"   | 宽度                |
## | extra_max_bitrate                   | int               | YES  |     | 0       |       | "$.data.room.stream_url.extra.max_bitrate" | 最大码率   |
## | extra_min_bitrate                   | int               | YES  |     | 0       |       | "$.data.room.stream_url.extra.min_bitrate" | 最小码率   |
## | extra_roi                           | bool              | YES  |     | FALSE   |       | "$.data.room.stream_url.extra.roi"     | ROI                 |
## | extra_sw_roi                        | bool              | YES  |     | FALSE   |       | "$.data.room.stream_url.extra.sw_roi"  | 软件 ROI            |
## | extra_video_profile                 | tinyint           | YES  |     | 0       |       | "$.data.room.stream_url.extra.video_profile" | 视频档案   |
## +-------------------------------------+-------------------+------+-----+---------+-------+----------------------------------------+---------------------+
##
class RoomStreamTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_STREAM_TABLE_NAME: str = 'room_stream'
  __ROOM_STREAM_TABLE_HEADER: list[str] = [
    'platform', 'start_time', 'room_id',
    'default_resolution', 'hls_pull_url', 'rtmp_pull_url', 'rtmp_pull_url_params', 'rtmp_push_url', 'rtmp_push_url_params',
    'stream_id', 'stream_id_str', 'multi_stream_scene', 'provider', 'stream_control_type', 'stream_orientation', 'vr_type',
    'resolution_name_sd1', 'resolution_name_sd2', 'resolution_name_hd1', 'resolution_name_full_hd1',
    'flv_pull_url_sd1', 'flv_pull_url_sd2', 'flv_pull_url_hd1', 'flv_pull_url_full_hd1',
    'hls_pull_url_sd1', 'hls_pull_url_sd2', 'hls_pull_url_hd1', 'hls_pull_url_full_hd1',
    'flv_params_sd1', 'flv_params_sd2', 'flv_params_hd1', 'flv_params_full_hd1',
    'hls_params',
    'extra_anchor_interact_profile', 'extra_audience_interact_profile', 'extra_bframe_enable', 'extra_bitrate_adapt_strategy',
    'extra_business_name', 'extra_bytevc1_enable', 'extra_default_bitrate', 'extra_fps', 'extra_gop_sec', 'extra_h265_enable',
    'extra_hardware_encode', 'extra_height', 'extra_width', 'extra_max_bitrate', 'extra_min_bitrate', 'extra_roi',
    'extra_sw_roi', 'extra_video_profile'
  ]
  __ROOM_STREAM_TABLE_PRI_KEY: list[str] = ['platform', 'start_time', 'room_id']
  __TABLE_AUTO_INCREMENT: list[str] = []
  __ROOM_STREAM_TABLE_TUPLE: dict[str, None] = {item:None for item in __ROOM_STREAM_TABLE_HEADER}
  __SQL_CREATE_ROOM_STREAM_TABLE: str = '''
                                    CREATE TABLE IF NOT EXISTS {} (
                                      platform                         varchar(20)   NOT NULL,
                                      start_time                       datetime      NOT NULL,
                                      room_id                          varchar(200)  NOT NULL,
                                      default_resolution               varchar(20)   DEFAULT NULL,
                                      hls_pull_url                     text          DEFAULT NULL,
                                      rtmp_pull_url                    text          DEFAULT NULL,
                                      rtmp_pull_url_params             text          DEFAULT NULL,
                                      rtmp_push_url                    text          DEFAULT NULL,
                                      rtmp_push_url_params             text          DEFAULT NULL,
                                      stream_id                        bigint        DEFAULT NULL,
                                      stream_id_str                    varchar(200)  DEFAULT NULL,
                                      multi_stream_scene               tinyint       DEFAULT 0,
                                      provider                         tinyint       DEFAULT 0,
                                      stream_control_type              tinyint       DEFAULT 0,
                                      stream_orientation               tinyint       DEFAULT 0,
                                      vr_type                          tinyint       DEFAULT 0,
                                      resolution_name_sd1              varchar(50)   DEFAULT NULL,
                                      resolution_name_sd2              varchar(50)   DEFAULT NULL,
                                      resolution_name_hd1              varchar(50)   DEFAULT NULL,
                                      resolution_name_full_hd1         varchar(50)   DEFAULT NULL,
                                      flv_pull_url_sd1                 text          DEFAULT NULL,
                                      flv_pull_url_sd2                 text          DEFAULT NULL,
                                      flv_pull_url_hd1                 text          DEFAULT NULL,
                                      flv_pull_url_full_hd1            text          DEFAULT NULL,
                                      hls_pull_url_sd1                 text          DEFAULT NULL,
                                      hls_pull_url_sd2                 text          DEFAULT NULL,
                                      hls_pull_url_hd1                 text          DEFAULT NULL,
                                      hls_pull_url_full_hd1            text          DEFAULT NULL,
                                      flv_params_sd1                   text          DEFAULT NULL,
                                      flv_params_sd2                   text          DEFAULT NULL,
                                      flv_params_hd1                   text          DEFAULT NULL,
                                      flv_params_full_hd1              text          DEFAULT NULL,
                                      hls_params                       text          DEFAULT NULL,
                                      extra_anchor_interact_profile    tinyint       DEFAULT 0,
                                      extra_audience_interact_profile  tinyint       DEFAULT 0,
                                      extra_bframe_enable              bool          DEFAULT FALSE,
                                      extra_bitrate_adapt_strategy     tinyint       DEFAULT 0,
                                      extra_business_name              varchar(100)  DEFAULT NULL,
                                      extra_bytevc1_enable             bool          DEFAULT FALSE,
                                      extra_default_bitrate            int           DEFAULT 0,
                                      extra_fps                        tinyint       DEFAULT 0,
                                      extra_gop_sec                    tinyint       DEFAULT 0,
                                      extra_h265_enable                bool          DEFAULT FALSE,
                                      extra_hardware_encode            bool          DEFAULT FALSE,
                                      extra_height                     int           DEFAULT 0,
                                      extra_width                      int           DEFAULT 0,
                                      extra_max_bitrate                int           DEFAULT 0,
                                      extra_min_bitrate                int           DEFAULT 0,
                                      extra_roi                        bool          DEFAULT FALSE,
                                      extra_sw_roi                     bool          DEFAULT FALSE,
                                      extra_video_profile              tinyint       DEFAULT 0,
                                      PRIMARY KEY (platform, start_time, room_id)
                                    )
                                    '''.format(__ROOM_STREAM_TABLE_NAME)
  __SQL_DROP_ROOM_STREAM_TABLE: str = 'DROP TABLE IF EXISTS {};'.format(__ROOM_STREAM_TABLE_NAME)


##
## >>============================= private method =============================>>
##
  ##
  ## init method
  ##
  def __init__(self, db_instance:SocialMediaStreamDataBase) -> None:
    if hasattr(self, '_initialized') and self._initialized:
        return
    super().__init__(db_instance)
    self._initialized = True

##
## >>============================= abstract method =============================>>
##
  ##
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__ROOM_STREAM_TABLE_NAME

  ##
  ## get table header
  ##
  def get_header(self) -> list[str]:
    return self.__ROOM_STREAM_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict[str, None]:
    return self.__ROOM_STREAM_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list[str]:
    return self.__ROOM_STREAM_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list[str]:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_STREAM_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_STREAM_TABLE

  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()