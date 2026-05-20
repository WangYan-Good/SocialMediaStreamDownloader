##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Third-Part>>
from backend.src.database.social_media_stream_database                import SocialMediaStreamDataBase
from backend.src.database.table.social_media_stream_db_table          import SocialMediaStreamDataTable

##
## room_base table - 直播间基础信息表
##
## 优化后的核心表，包含直播间基础信息和 JSON 扩展字段
## 字段数：70 独立字段 + 35 JSON 字段 = 105 字段
##
class RoomBaseTable(SocialMediaStreamDataTable):
##
## >>=============================== room_base ===============================>>
##
  __ROOM_BASE_TABLE_NAME   = 'room_base'
  __ROOM_BASE_TABLE_HEADER = [
    # 主键
    'now',
    'id',                             'id_str',
    # 基础信息
    'title',                          'introduction',               'share_url',                  'user_share_text',
    'anchor_share_text',
    # 时间字段 (毫秒时间戳)
    'create_time',                    'start_time',                 'finish_time',                'stream_close_time',
    # 状态字段
    'status',                         'finish_reason',              'acquaintance_status',
    # 主播相关
    'owner_user_id',
    # 房间配置
    'app_id',                         'base_category',              'category',                   'client_version',
    'orientation',                    'layout',                     'room_layout',                'room_tag',
    'live_room_mode',                 'live_platform_source',       'cell_style',                 'os_type',
    'owner_device_id',                'owner_open_id',              'visibility_range',           'webcast_sdk_version',
    # 流相关
    'stream_id',                      'stream_id_str',              'live_id',                    'stream_provider',
    # 统计数值
    'like_count',                     'user_count',                 'popularity',
    'danmaku_detail',                 'web_count',                  'webcast_comment_tcs',        'gift_msg_style',
    'share_msg_style',                'follow_msg_style',           'fansclub_msg_style',
    # 布尔标志
    'sell_goods',                     'has_commerce_goods',         'is_replay',                  'replay',
    'highlight',
    'use_filter',                     'title_recommend',            'enable_room_perspective',    'with_aggregate_column',
    'with_draw_something',            'with_ktv',                   'with_linkmic',
    # 直播类型
    'live_type_normal',               'live_type_audio',                'live_type_linkmic',          'live_type_official',
    'live_type_sandbox',              'live_type_screenshot',           'live_type_third_party',      'live_type_vs_live',
    'live_type_vs_premiere',
    # 连麦信息
    'linkmic_layout',
    # 文本和其他配置字段
    'auth_city',                      'location',                       'distance',                   'distance_city',
    'distance_km',                    'real_distance',                  'dynamic_cover_uri',          'vertical_cover_uri',
    'finish_url',                     'forum_extra_data',               'private_info',               'item_explicit_info',
    'hot_sentence_info',
    'relation_tag',                   'stamps',                         'room_create_ab_param',       'scroll_config',
    'mosaic_tip',                     'popularity_str',                 'preview_copy',               'wait_copy',
    'short_title',                    'video_feed_tag',                 'screen_capture_sharing_title', 'common_label_list',
    'content_tag',                    'challenge_info',                 'anchor_scheduled_time_text', 'anchor_tab_type',
    'comment_name_mode',              'fcdn_appid',                     'game_room_type',             'official_channel_open_id',
    'official_channel_uid',           'search_id',                      'group_id',                   'group_source',
    'sofa_layout',                    'sun_daily_icon_content',         'ranklist_audience_type',     'redpacket_audience_auth',
    'toutiao_cover_recommend_level',
    'toutiao_title_recommend_level',  'preview_flow_tag',               'replay_location',            'room_audit_status',
    'mosaic_status',                  'lottery_finish_time',            'luckymoney_num',             'has_promotion_games',
    'is_need_check_list',             'is_official_channel_room',       'is_show_inquiry_ball',       'is_show_user_card_switch',
    'auto_cover',                     'business_live',                  'book_time',                  'book_end_time',
    'linkmic_display_type',           'vid',                            'vs_main_replay_id',          'last_ping_time',
    'pre_enter_time',                 'city_top_distance',
    # JSON 扩展字段 (不常查询的嵌套对象)
    'AnchorABMap',                    'comment_box',                    'cover',                      'dynamic_cover_dict',
    'extra',                          'feed_room_label',                'guide_button',               'linker_map',
    'living_room_attrs',     
    'owner',                          'pack_meta',                      'paid_live_data',             'room_auth',
    'room_view_stats',                'short_touch_area_config',        'stats',                      'stream_url',
    'content_label',                  'link_mic',                       'official_channel',
    # JSON 数组字段 (不常单独查询的列表)
    'admin_user_ids',                 'admin_user_open_ids',            'assist_label_list',          'deco_list',
    'fans_group_admin_user_ids',      'fans_group_admin_user_open_ids', 'filter_words',               'live_distribution',
    'room_tabs',                      'sharing_music_id_list',          'tags',                       'top_fans',
    'upper_right_widget_data_list',   'vs_roles',
    # 时间戳
    'created_at',                     'updated_at'
  ]
  __ROOM_BASE_TABLE_PRI_KEY = ['now', 'id', 'start_time']
  __TABLE_AUTO_INCREMENT    = []
  __ROOM_BASE_TABLE_TUPLE   = {item:None for item in __ROOM_BASE_TABLE_HEADER}
  __SQL_CREATE_ROOM_BASE_TABLE = '''
                                      CREATE TABLE IF NOT EXISTS {} (
                                        now                              timestamp(3)   NOT NULL,
                                        id                               varchar(200)   NOT NULL,
                                        id_str                           varchar(200)   DEFAULT NULL,

                                        title                            tinytext       DEFAULT NULL,
                                        introduction                     text           DEFAULT NULL,
                                        share_url                        text           DEFAULT NULL,
                                        user_share_text                  text           DEFAULT NULL,
                                        anchor_share_text                text           DEFAULT NULL,

                                        create_time                      bigint         DEFAULT NULL,
                                        start_time                       bigint         NOT NULL,
                                        finish_time                      bigint         DEFAULT NULL,
                                        stream_close_time                bigint         DEFAULT NULL,

                                        status                           tinyint  unsigned DEFAULT 0,
                                        finish_reason                    smallint unsigned DEFAULT NULL,
                                        acquaintance_status              tinyint  unsigned DEFAULT 0,

                                        owner_user_id                    bigint         DEFAULT NULL,

                                        app_id                           bigint         DEFAULT NULL,
                                        base_category                    bigint         DEFAULT 0,
                                        category                         bigint         DEFAULT 0,
                                        client_version                   bigint         DEFAULT NULL,
                                        orientation                      tinyint unsigned DEFAULT 0,
                                        layout                           tinyint unsigned DEFAULT 0,
                                        room_layout                      tinyint unsigned DEFAULT 0,
                                        room_tag                         tinyint unsigned DEFAULT 0,
                                        live_room_mode                   tinyint unsigned DEFAULT 0,
                                        live_platform_source             tinytext       DEFAULT NULL,
                                        cell_style                       tinyint unsigned DEFAULT 0,
                                        os_type                          tinyint unsigned DEFAULT 0,
                                        owner_device_id                  bigint         DEFAULT NULL,
                                        owner_open_id                    varchar(200)   DEFAULT NULL,
                                        visibility_range                 tinyint unsigned DEFAULT 0,
                                        webcast_sdk_version              varchar(20)    DEFAULT NULL,

                                        stream_id                        bigint         DEFAULT NULL,
                                        stream_id_str                    varchar(200)   DEFAULT NULL,
                                        live_id                          bigint         DEFAULT NULL,
                                        stream_provider                  tinyint unsigned DEFAULT 0,

                                        like_count                       bigint         DEFAULT 0,
                                        user_count                       int unsigned   DEFAULT 0,
                                        popularity                       int unsigned   DEFAULT 0,
                                        danmaku_detail                   int unsigned   DEFAULT 0,
                                        web_count                        bigint         DEFAULT 0,
                                        webcast_comment_tcs              int unsigned   DEFAULT 0,
                                        gift_msg_style                   tinyint unsigned DEFAULT 0,
                                        share_msg_style                  tinyint unsigned DEFAULT 0,
                                        follow_msg_style                 tinyint unsigned DEFAULT 0,
                                        fansclub_msg_style               tinyint unsigned DEFAULT 0,

                                        sell_goods                       bool           DEFAULT FALSE,
                                        has_commerce_goods               bool           DEFAULT FALSE,
                                        is_replay                        bool           DEFAULT FALSE,
                                        replay                           bool           DEFAULT FALSE,
                                        highlight                        bool           DEFAULT FALSE,
                                        use_filter                       bool           DEFAULT FALSE,
                                        title_recommend                  bool           DEFAULT FALSE,
                                        enable_room_perspective          bool           DEFAULT FALSE,
                                        with_aggregate_column            bool           DEFAULT FALSE,
                                        with_draw_something              bool           DEFAULT FALSE,
                                        with_ktv                         bool           DEFAULT FALSE,
                                        with_linkmic                     bool           DEFAULT FALSE,

                                        live_type_normal                 bool           DEFAULT FALSE,
                                        live_type_audio                  bool           DEFAULT FALSE,
                                        live_type_linkmic                bool           DEFAULT FALSE,
                                        live_type_official               bool           DEFAULT FALSE,
                                        live_type_sandbox                bool           DEFAULT FALSE,
                                        live_type_screenshot             bool           DEFAULT FALSE,
                                        live_type_third_party            bool           DEFAULT FALSE,
                                        live_type_vs_live                bool           DEFAULT FALSE,
                                        live_type_vs_premiere            bool           DEFAULT FALSE,

                                        linkmic_layout                   tinyint unsigned DEFAULT 0,

                                        auth_city                        varchar(100)   DEFAULT NULL,
                                        location                         varchar(100)   DEFAULT NULL,
                                        distance                         varchar(100)   DEFAULT NULL,
                                        distance_city                    varchar(100)   DEFAULT NULL,
                                        distance_km                      varchar(100)   DEFAULT NULL,
                                        real_distance                    varchar(100)   DEFAULT NULL,
                                        dynamic_cover_uri                text           DEFAULT NULL,
                                        vertical_cover_uri               text           DEFAULT NULL,
                                        finish_url                       text           DEFAULT NULL,
                                        forum_extra_data                 text           DEFAULT NULL,
                                        private_info                     text           DEFAULT NULL,
                                        item_explicit_info               text           DEFAULT NULL,
                                        hot_sentence_info                text           DEFAULT NULL,
                                        relation_tag                     tinytext       DEFAULT NULL,
                                        stamps                           text           DEFAULT NULL,
                                        room_create_ab_param             text           DEFAULT NULL,
                                        scroll_config                    text           DEFAULT NULL,
                                        mosaic_tip                       tinytext       DEFAULT NULL,
                                        popularity_str                   varchar(50)    DEFAULT NULL,
                                        preview_copy                     tinytext       DEFAULT NULL,
                                        wait_copy                        tinytext       DEFAULT NULL,
                                        short_title                      tinytext       DEFAULT NULL,
                                        video_feed_tag                   tinytext       DEFAULT NULL,
                                        screen_capture_sharing_title     tinytext       DEFAULT NULL,
                                        common_label_list                tinytext       DEFAULT NULL,
                                        content_tag                      tinytext       DEFAULT NULL,
                                        challenge_info                   tinytext       DEFAULT NULL,
                                        anchor_scheduled_time_text       text           DEFAULT NULL,
                                        anchor_tab_type                  tinyint unsigned DEFAULT 0,
                                        comment_name_mode                tinyint unsigned DEFAULT 0,
                                        fcdn_appid                       bigint         DEFAULT NULL,
                                        game_room_type                   tinyint unsigned DEFAULT 0,
                                        official_channel_open_id         varchar(200)   DEFAULT NULL,
                                        official_channel_uid             bigint         DEFAULT NULL,
                                        search_id                        bigint         DEFAULT NULL,
                                        group_id                         bigint         DEFAULT NULL,
                                        group_source                     tinyint unsigned DEFAULT 0,
                                        sofa_layout                      tinyint unsigned DEFAULT 0,
                                        sun_daily_icon_content           tinytext       DEFAULT NULL,
                                        ranklist_audience_type           tinyint unsigned DEFAULT 0,
                                        redpacket_audience_auth          tinyint unsigned DEFAULT 0,
                                        toutiao_cover_recommend_level    tinyint unsigned DEFAULT 0,
                                        toutiao_title_recommend_level    tinyint unsigned DEFAULT 0,
                                        preview_flow_tag                 tinyint unsigned DEFAULT 0,
                                        replay_location                  tinyint unsigned DEFAULT 0,
                                        room_audit_status                tinyint unsigned DEFAULT 0,
                                        mosaic_status                    tinyint unsigned DEFAULT 0,
                                        lottery_finish_time              bigint         DEFAULT NULL,
                                        luckymoney_num                   int unsigned   DEFAULT 0,
                                        has_promotion_games              tinyint unsigned DEFAULT 0,
                                        is_need_check_list               bool           DEFAULT FALSE,
                                        is_official_channel_room         bool           DEFAULT FALSE,
                                        is_show_inquiry_ball             bool           DEFAULT FALSE,
                                        is_show_user_card_switch         bool           DEFAULT FALSE,
                                        auto_cover                       tinyint unsigned DEFAULT 0,
                                        business_live                    tinyint unsigned DEFAULT 0,
                                        book_time                        bigint         DEFAULT NULL,
                                        book_end_time                    bigint         DEFAULT NULL,
                                        linkmic_display_type             tinyint unsigned DEFAULT 0,
                                        vid                              varchar(200)   DEFAULT NULL,
                                        vs_main_replay_id                varchar(200)   DEFAULT NULL,
                                        last_ping_time                   bigint         DEFAULT NULL,
                                        pre_enter_time                   bigint         DEFAULT NULL,
                                        city_top_distance                tinytext       DEFAULT NULL,

                                        cover                            JSON           DEFAULT NULL,
                                        content_label                    JSON           DEFAULT NULL,
                                        feed_room_label                  JSON           DEFAULT NULL,
                                        guide_button                     JSON           DEFAULT NULL,
                                        comment_box                      JSON           DEFAULT NULL,
                                        link_mic                         JSON           DEFAULT NULL,
                                        living_room_attrs                JSON           DEFAULT NULL,
                                        pack_meta                        JSON           DEFAULT NULL,
                                        paid_live_data                   JSON           DEFAULT NULL,
                                        room_view_stats                  JSON           DEFAULT NULL,
                                        extra                            JSON           DEFAULT NULL,
                                        room_auth                        JSON           DEFAULT NULL,
                                        short_touch_area_config          JSON           DEFAULT NULL,
                                        stream_url                       JSON           DEFAULT NULL,
                                        stats                            JSON           DEFAULT NULL,
                                        owner                            JSON           DEFAULT NULL,
                                        official_channel                 JSON           DEFAULT NULL,

                                        admin_user_ids                   JSON           DEFAULT NULL,
                                        admin_user_open_ids              JSON           DEFAULT NULL,
                                        deco_list                        JSON           DEFAULT NULL,
                                        fans_group_admin_user_ids        JSON           DEFAULT NULL,
                                        fans_group_admin_user_open_ids   JSON           DEFAULT NULL,
                                        filter_words                     JSON           DEFAULT NULL,
                                        live_distribution                JSON           DEFAULT NULL,
                                        sharing_music_id_list            JSON           DEFAULT NULL,
                                        tags                             JSON           DEFAULT NULL,
                                        top_fans                         JSON           DEFAULT NULL,
                                        upper_right_widget_data_list     JSON           DEFAULT NULL,
                                        vs_roles                         JSON           DEFAULT NULL,
                                        room_tabs                        JSON           DEFAULT NULL,
                                        assist_label_list                JSON           DEFAULT NULL,
                                        AnchorABMap                      JSON           DEFAULT NULL,
                                        linker_map                       JSON           DEFAULT NULL,
                                        dynamic_cover_dict               JSON           DEFAULT NULL,

                                        created_at                       timestamp      DEFAULT CURRENT_TIMESTAMP,
                                        updated_at                       timestamp      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                                        KEY idx_room_base_id_start_time (id, start_time),
                                        PRIMARY KEY (now, id, start_time)
                                      ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                                      '''.format(__ROOM_BASE_TABLE_NAME)
  __SQL_DROP_ROOM_BASE_TABLE = '''
                              DROP TABLE IF EXISTS {};
                            '''.format(__ROOM_BASE_TABLE_NAME)

##
## <<=============================== attribute ==============================<<
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
    if hasattr(self, '_initialized') and self._initialized:
        return
    super().__init__(db_instance)
    self._initialized = True

##
## >>============================= abstract method =============================>>
##
  def get_name(self) -> str:
    return self.__ROOM_BASE_TABLE_NAME

  def get_header(self) -> list:
    return self.__ROOM_BASE_TABLE_HEADER

  def get_tuple(self) -> dict:
    return self.__ROOM_BASE_TABLE_TUPLE

  def get_pri_key(self) -> list:
    return self.__ROOM_BASE_TABLE_PRI_KEY

  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_BASE_TABLE

  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_BASE_TABLE

  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()
