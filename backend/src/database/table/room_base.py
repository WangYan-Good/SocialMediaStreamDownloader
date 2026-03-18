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
    'id',                         'id_str',
    # 基础信息
    'title',                      'introduction',               'share_url',                  'user_share_text',
    'anchor_share_text',
    # 时间字段 (毫秒时间戳)
    'create_time',                'start_time',                 'finish_time',                'stream_close_time',
    # 状态字段
    'status',                     'finish_reason',              'acquaintance_status',
    # 主播相关
    'owner_user_id',
    # 房间配置
    'app_id',                     'base_category',              'category',                   'client_version',
    'orientation',                'layout',                     'room_layout',                'room_tag',
    'live_room_mode',             'live_platform_source',       'cell_style',                 'os_type',
    'visibility_range',           'webcast_sdk_version',
    # 流相关
    'stream_id',                  'stream_id_str',              'live_id',                    'stream_provider',
    # 统计数值
    'danmaku_detail',             'web_count',                  'webcast_comment_tcs',        'gift_msg_style',
    'share_msg_style',            'follow_msg_style',           'fansclub_msg_style',
    # 布尔标志
    'sell_goods',                 'has_commerce_goods',         'is_replay',                  'highlight',
    'use_filter',                 'title_recommend',            'enable_room_perspective',    'with_aggregate_column',
    'with_draw_something',        'with_ktv',                   'with_linkmic',
    # 直播类型
    'live_type_normal',           'live_type_audio',            'live_type_linkmic',          'live_type_official',
    'live_type_sandbox',          'live_type_screenshot',       'live_type_third_party',      'live_type_vs_live',
    'live_type_vs_premiere',
    # 连麦信息
    'linkmic_layout',             'rival_anchor_id',
    # 文本和其他配置字段
    'auth_city',                  'location',                   'distance',                   'distance_city',
    'distance_km',                'real_distance',              'dynamic_cover_uri',          'vertical_cover_uri',
    'finish_url',                 'forum_extra_data',           'item_explicit_info',         'hot_sentence_info',
    'relation_tag',               'stamps',                     'room_create_ab_param',       'scroll_config',
    'mosaic_tip',                 'popularity_str',             'preview_copy',               'wait_copy',
    'short_title',                'video_feed_tag',             'screen_capture_sharing_title', 'common_label_list',
    'content_tag',                'challenge_info',             'anchor_scheduled_time_text', 'anchor_tab_type',
    'comment_name_mode',          'fcdn_appid',                 'game_room_type',             'official_channel_open_id',
    'official_channel_uid',       'search_id',                  'group_id',                   'group_source',
    'sofa_layout',                'ranklist_audience_type',     'redpacket_audience_auth',    'toutiao_cover_recommend_level',
    'toutiao_title_recommend_level', 'preview_flow_tag',        'replay_location',            'room_audit_status',
    'mosaic_status',              'lottery_finish_time',        'luckymoney_num',             'has_promotion_games',
    'is_need_check_list',         'is_official_channel_room',   'is_show_inquiry_ball',       'is_show_user_card_switch',
    'auto_cover',                 'business_live',              'book_time',                  'book_end_time',
    'linkmic_display_type',       'vid',                        'vs_main_replay_id',          'last_ping_time',
    'pre_enter_time',             'city_top_distance',
    # JSON 扩展字段 (不常查询的嵌套对象)
    'cover_data',                 'content_label_data',         'feed_room_label_data',       'guide_button_data',
    'comment_box_data',           'link_mic_data',              'living_room_attrs_data',     'pack_meta_data',
    'paid_live_data',             'view_stats_data',            'extra_data',                 'room_auth_data',
    'short_touch_config_data',    'stream_url_data',            'stream_extra_data',          'stats_data',
    # JSON 数组字段 (不常单独查询的列表)
    'admin_user_ids',             'admin_user_open_ids',        'fans_group_admin_user_ids',  'fans_group_admin_user_open_ids',
    'filter_words',               'live_distribution',          'sharing_music_ids',          'tags',
    'top_fans',                   'ticket_count',               'top_vip_no',                 'upper_right_widget_data_list',
    'vs_roles',                   'room_tabs',                  'assist_labels',              'anchor_ab_map',
    'linker_map',                 'dynamic_cover_dict',
    # 时间戳
    'created_at',                 'updated_at'
  ]
  __ROOM_BASE_TABLE_PRI_KEY = ['id']
  __TABLE_AUTO_INCREMENT         = []
  __ROOM_BASE_TABLE_TUPLE   = {item:None for item in __ROOM_BASE_TABLE_HEADER}
  __SQL_CREATE_ROOM_BASE_TABLE = '''
                                      CREATE TABLE IF NOT EXISTS {} (
                                        id                               varchar(200)   NOT NULL,
                                        id_str                           varchar(200)   DEFAULT NULL,

                                        title                            tinytext       DEFAULT NULL,
                                        introduction                     text           DEFAULT NULL,
                                        share_url                        text           DEFAULT NULL,
                                        user_share_text                  text           DEFAULT NULL,
                                        anchor_share_text                text           DEFAULT NULL,

                                        create_time                      bigint         DEFAULT NULL,
                                        start_time                       bigint         DEFAULT NULL,
                                        finish_time                      bigint         DEFAULT NULL,
                                        stream_close_time                bigint         DEFAULT NULL,

                                        status                           tinyint        DEFAULT 0,
                                        finish_reason                    tinyint        DEFAULT NULL,
                                        acquaintance_status              tinyint        DEFAULT 0,

                                        owner_user_id                    bigint         DEFAULT NULL,

                                        app_id                           bigint         DEFAULT NULL,
                                        base_category                    tinyint        DEFAULT 0,
                                        category                         tinyint        DEFAULT 0,
                                        client_version                   bigint         DEFAULT NULL,
                                        orientation                      tinyint        DEFAULT 0,
                                        layout                           tinyint        DEFAULT 0,
                                        room_layout                      tinyint        DEFAULT 0,
                                        room_tag                         tinyint        DEFAULT 0,
                                        live_room_mode                   tinyint        DEFAULT 0,
                                        live_platform_source             tinytext       DEFAULT NULL,
                                        cell_style                       tinyint        DEFAULT 0,
                                        os_type                          tinyint        DEFAULT 0,
                                        visibility_range                 tinyint        DEFAULT 0,
                                        webcast_sdk_version              varchar(20)    DEFAULT NULL,

                                        stream_id                        bigint         DEFAULT NULL,
                                        stream_id_str                    varchar(200)   DEFAULT NULL,
                                        live_id                          bigint         DEFAULT NULL,
                                        stream_provider                  tinyint        DEFAULT 0,

                                        danmaku_detail                   int            DEFAULT 0,
                                        web_count                        bigint         DEFAULT 0,
                                        webcast_comment_tcs              int            DEFAULT 0,
                                        gift_msg_style                   tinyint        DEFAULT 0,
                                        share_msg_style                  tinyint        DEFAULT 0,
                                        follow_msg_style                 tinyint        DEFAULT 0,
                                        fansclub_msg_style               tinyint        DEFAULT 0,

                                        sell_goods                       bool           DEFAULT FALSE,
                                        has_commerce_goods               bool           DEFAULT FALSE,
                                        is_replay                        bool           DEFAULT FALSE,
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

                                        linkmic_layout                   tinyint        DEFAULT 0,
                                        rival_anchor_id                  bigint         DEFAULT NULL,

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
                                        item_explicit_info               text           DEFAULT NULL,
                                        hot_sentence_info                text           DEFAULT NULL,
                                        relation_tag                     tinytext       DEFAULT NULL,
                                        stamps                           tinytext       DEFAULT NULL,
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
                                        anchor_tab_type                  tinyint        DEFAULT 0,
                                        comment_name_mode                tinyint        DEFAULT 0,
                                        fcdn_appid                       bigint         DEFAULT NULL,
                                        game_room_type                   tinyint        DEFAULT 0,
                                        official_channel_open_id         varchar(200)   DEFAULT NULL,
                                        official_channel_uid             bigint         DEFAULT NULL,
                                        search_id                        bigint         DEFAULT NULL,
                                        group_id                         bigint         DEFAULT NULL,
                                        group_source                     tinyint        DEFAULT 0,
                                        sofa_layout                      tinyint        DEFAULT 0,
                                        ranklist_audience_type           tinyint        DEFAULT 0,
                                        redpacket_audience_auth          tinyint        DEFAULT 0,
                                        toutiao_cover_recommend_level    tinyint        DEFAULT 0,
                                        toutiao_title_recommend_level    tinyint        DEFAULT 0,
                                        preview_flow_tag                 tinyint        DEFAULT 0,
                                        replay_location                  tinyint        DEFAULT 0,
                                        room_audit_status                tinyint        DEFAULT 0,
                                        mosaic_status                    tinyint        DEFAULT 0,
                                        lottery_finish_time              bigint         DEFAULT NULL,
                                        luckymoney_num                   int            DEFAULT 0,
                                        has_promotion_games              tinyint        DEFAULT 0,
                                        is_need_check_list               bool           DEFAULT FALSE,
                                        is_official_channel_room         bool           DEFAULT FALSE,
                                        is_show_inquiry_ball             bool           DEFAULT FALSE,
                                        is_show_user_card_switch         bool           DEFAULT FALSE,
                                        auto_cover                       tinyint        DEFAULT 0,
                                        business_live                    tinyint        DEFAULT 0,
                                        book_time                        bigint         DEFAULT NULL,
                                        book_end_time                    bigint         DEFAULT NULL,
                                        linkmic_display_type             tinyint        DEFAULT 0,
                                        vid                              varchar(200)   DEFAULT NULL,
                                        vs_main_replay_id                varchar(200)   DEFAULT NULL,
                                        last_ping_time                   bigint         DEFAULT NULL,
                                        pre_enter_time                   bigint         DEFAULT NULL,
                                        city_top_distance                tinytext       DEFAULT NULL,

                                        cover_data                       JSON           DEFAULT NULL,
                                        content_label_data               JSON           DEFAULT NULL,
                                        feed_room_label_data             JSON           DEFAULT NULL,
                                        guide_button_data                JSON           DEFAULT NULL,
                                        comment_box_data                 JSON           DEFAULT NULL,
                                        link_mic_data                    JSON           DEFAULT NULL,
                                        living_room_attrs_data           JSON           DEFAULT NULL,
                                        pack_meta_data                   JSON           DEFAULT NULL,
                                        paid_live_data                   JSON           DEFAULT NULL,
                                        view_stats_data                  JSON           DEFAULT NULL,
                                        extra_data                       JSON           DEFAULT NULL,
                                        room_auth_data                   JSON           DEFAULT NULL,
                                        short_touch_config_data          JSON           DEFAULT NULL,
                                        stream_url_data                  JSON           DEFAULT NULL,
                                        stream_extra_data                JSON           DEFAULT NULL,
                                        stats_data                       JSON           DEFAULT NULL,

                                        admin_user_ids                   JSON           DEFAULT NULL,
                                        admin_user_open_ids              JSON           DEFAULT NULL,
                                        fans_group_admin_user_ids        JSON           DEFAULT NULL,
                                        fans_group_admin_user_open_ids   JSON           DEFAULT NULL,
                                        filter_words                     JSON           DEFAULT NULL,
                                        live_distribution                JSON           DEFAULT NULL,
                                        sharing_music_ids                JSON           DEFAULT NULL,
                                        tags                           JSON           DEFAULT NULL,
                                        top_fans                         JSON           DEFAULT NULL,
                                        ticket_count                     int            DEFAULT 0,
                                        top_vip_no                       int            DEFAULT 0,
                                        upper_right_widget_data_list     JSON           DEFAULT NULL,
                                        vs_roles                         JSON           DEFAULT NULL,
                                        room_tabs                        JSON           DEFAULT NULL,
                                        assist_labels                    JSON           DEFAULT NULL,
                                        anchor_ab_map                    JSON           DEFAULT NULL,
                                        linker_map                       JSON           DEFAULT NULL,
                                        dynamic_cover_dict               JSON           DEFAULT NULL,

                                        created_at                       timestamp      DEFAULT CURRENT_TIMESTAMP,
                                        updated_at                       timestamp      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                                        PRIMARY KEY (id),
                                        INDEX idx_owner_user_id (owner_user_id),
                                        INDEX idx_status (status),
                                        INDEX idx_start_time (start_time),
                                        INDEX idx_create_time (create_time),
                                        INDEX idx_owner_status (owner_user_id, status)
                                      ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
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
    return 'DROP TABLE IF EXISTS {};'.format(self.__ROOM_BASE_TABLE_NAME)

  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()
