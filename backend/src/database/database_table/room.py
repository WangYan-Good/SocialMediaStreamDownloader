##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from threading import Lock
from datetime  import datetime as dat

## <<Third-Part>>
from backend.src.database.social_media_stream_database                import SocialMediaStreamDataBase
from backend.src.database.database_table.social_media_stream_db_table import SocialMediaStreamDataTable
from backend.src.base.log                                             import get_logger

class RoomAttributeTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##

##
##
## room attribute table header
## +----------------------------------+-------------------+------+-----+---------+-------+-------------------------------------------------------+---------------------------------+
## | Field                            | Type              | Null | Key | Default | Extra |Topology                                               | Comment                         |
## +----------------------------------+-------------------+------+-----+---------+-------+-------------------------------------------------------+---------------------------------+
## | AnchorABMap                      | json              | YES  |     | NULL    |       | "$.data.room.living_room_attrs.rank"                  | 主播AB映射                       | 
## | acquaintance_status              | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.acquaintance_status"                     | 直播间熟人状态                    |
## | anchor_scheduled_time_text       | text              | YES  |     | NULL    |       | "$.data.room.anchor_scheduled_time_text"              | 直播间布局                       |
## | anchor_share_text                | text              | YES  |     | NULL    |       | "$.data.room.anchor_share_text"                       | 主播分享文本                     |
## | anchor_tab_type                  | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.anchor_tab_type"                         | 主播标签类型                     |
## | app_id                           | varchar(200)      | YES  |     | NULL    |       | "$.data.room.app_id"                                  | 应用ID                          |
## | auth_city                        | varchar(100)      | YES  |     | NULL    |       | "$.data.room.auth_city"                               | 直播间认证城市                   |
## | auto_cover                       | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.auto_cover"                              | 自动封面                         |
## | base_category                    | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.base_category"                           | 基础分类                         |
## | book_end_time                    | timestamp         | YES  |     | NULL    |       | "$.data.room.book_end_time"                           | 直播间预约结束时间                |
## | book_time                        | timestamp         | YES  |     | NULL    |       | "$.data.room.book_time"                               | 直播间预约开始时间                |
## | business_live                    | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.business_live"                           | 商业直播                         |
## | category                         | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.category"                                | 分类                            |
## | cell_style                       | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.cell_style"                              | 直播间单元样式                   |
## | city_top_distance                | tinytext          | YES  |     | NULL    |       | "$.data.room.city_top_distance"                       | 城市顶部距离                     |
## | client_version                   | varchar(20)       | YES  |     | NULL    |       | "$.data.room.client_version"                          | 客户端版本                       |
## | placeholder                      | tinytext          | YES  |     | NULL    |       | "$.data.room.comment_box.placeholder"                 | 评论框占位符                     |
## | comment_name_mode                | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.comment_name_mode"                       | 评论名称模式                     |
## | common_label_list                | tinytext          | YES  |     | NULL    |       | "$.data.room.common_label_list"                       | 常用标签列表                     |
## | content_tag                      | tinytext          | YES  |     | NULL    |       | "$.data.room.content_tag"                             | 内容标签                         |
## | create_time                      | timestamp         | YES  |     | NULL    |       | "$.data.room.create_time"                             | 直播间创建时间                    | 
## | distance                         | varchar(100)      | YES  |     | NULL    |       | "$.data.room.distance"                                | 距离                             |
## | distance_city                    | varchar(100)      | YES  |     | NULL    |       | "$.data.room.distance_city"                           | 城市距离                         |
## | distance_km                      | varchar(100)      | YES  |     | NULL    |       | "$.data.room.distance_km"                             | 公里距离                         |
## | dynamic_cover_dict               | json              | YES  |     | NULL    |       | "$.data.room.dynamic_cover_dict"                      | 动态封面字典                     |
## | dynamic_cover_uri                | text              | YES  |     | NULL    |       | "$.data.room.dynamic_cover_uri"                       | 动态封面URI                      |
## | enable_room_perspective          | bool              | YES  |     | NULL    |       | "$.data.room.enable_room_perspective"                 | 是否启用直播间透视                |
## | create_scene                     | tinytext          | YES  |     | NULL    |       | "$.data.room.extra.create_scene"                      | 创建场景                         |
## | facial_unrecognised              | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.extra.facial_unrecognised"               | 面部未识别                       |
## | geo_block                        | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.extra.geo_block"                         | 地理封锁                         |
## | is_sandbox                       | bool              | YES  |     | NULL    |       | "$.data.room.extra.is_sandbox"                        | 是否为沙盒                       |
## | is_virtual_anchor                | bool              | YES  |     | NULL    |       | "$.data.room.extra.is_virtual_anchor"                 | 是否为虚拟主播                   |
## | limit_appid                      | varchar(200)      | YES  |     | NULL    |       | "$.data.room.extra.limit_appid"                       | 限制应用ID                      |
## | limit_strategy                   | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.extra.limit_strategy"                    | 地理封锁                        |
## | realtime_playback_shift          | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.extra.realtime_playback_shift"           | 实时回放偏移                    |
## | realtime_playback_start_shift    | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.extra.realtime_playback_start_shift"     | 实时回放开始偏移                 |
## | realtime_replay_enabled          | bool              | YES  |     | NULL    |       | "$.data.room.extra.realtime_replay_enabled"           | 是否启用实时回放                 |
## | vr_type                          | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.extra.vr_type"                           | VR类型                          |
## | vs_type                          | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.extra.vs_type"                           | VS类型                          |
## | xigua_uid                        | varchar(200)      | YES  |     | NULL    |       | "$.data.room.extra.xigua_uid"                         | 西瓜用户ID                       |
## | fansclub_msg_style               | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.fansclub_msg_style"                      | 粉丝俱乐部消息样式                |
## | fcdn_appid                       | varchar(200)      | YES  |     | NULL    |       | "$.data.room.fcdn_appid"                              | FCDN应用ID                       |
## | finish_reason                    | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.finish_reason"                           | 直播结束原因                     |
## | finish_time                      | timestamp         | YES  |     | NULL    |       | "$.data.room.finish_time"                             | 直播结束时间                     |
## | finish_url                       | text              | YES  |     | NULL    |       | "$.data.room.finish_url"                              | 直播结束URL                      |
## | follow_msg_style                 | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.follow_msg_style"                        | 关注消息样式                     |
## | forum_extra_data                 | text              | YES  |     | NULL    |       | "$.data.room.forum_extra_data"                        | 论坛额外数据                     |
## | game_room_type                   | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.game_room_type"                          | 游戏直播间类型                   |
## | gift_msg_style                   | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.gift_msg_style"                          | 礼物消息样式                     |
## | group_id                         | varchar(200)      | YES  |     | NULL    |       | "$.data.room.group_id"                                | 直播间组ID                       |
## | group_source                     | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.group_source"                            | 直播间组来源                     |
## | has_commerce_goods               | bool              | YES  |     | NULL    |       | "$.data.room.has_commerce_goods"                      | 是否有商品                       |
## | has_promotion_games              | bool              | YES  |     | NULL    |       | "$.data.room.has_promotion_games"                     | 是否有推广游戏                   |
## | highlight                        | bool              | YES  |     | NULL    |       | "$.data.room.highlight"                               | 是否高亮                         |
## | id                               | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                                      | 直播间 ID                       |
## | introduction                     | text              | YES  |     | NULL    |       | "$.data.room.introduction"                            | 直播间介绍                       |
## | is_need_check_list               | bool              | YES  |     | NULL    |       | "$.data.room.is_need_check_list"                      | 是否需要检查列表                 |
## | is_official_channel_room         | bool              | YES  |     | NULL    |       | "$.data.room.is_official_channel_room"                | 是否为官方频道直播间              |
## | is_replay                        | bool              | YES  |     | NULL    |       | "$.data.room.is_replay"                               | 是否为回放                       |
## | is_show_inquiry_ball             | bool              | YES  |     | NULL    |       | "$.data.room.is_show_inquiry_ball"                    | 是否显示询问球                   |
## | is_show_user_card_switch         | bool              | YES  |     | NULL    |       | "$.data.room.is_show_user_card_switch"                | 是否显示用户卡片开关              |
## | item_explicit_info               | text              | YES  |     | NULL    |       | "$.data.room.item_explicit_info"                      | 物品显式信息                     |
## | layout                           | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.layout"                                  | 直播间布局                       |
## | linkmic_display_type             | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.linkmic_display_type"                    | 连麦显示类型                     |
## | linkmic_layout                   | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.linkmic_layout"                          | 连麦布局                         |
## | live_id                          | varchar(200)      | YES  |     | NULL    |       | "$.data.room.live_id"                                 | 直播ID                          |
## | live_platform_source             | tinytext          | YES  |     | NULL    |       | "$.data.room.live_platform_source"                    | 直播平台来源                     |
## | live_room_mode                   | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.live_room_mode"                          | 直播间模式                       |
## | live_type_audio                  | bool              | YES  |     | NULL    |       | "$.data.room.live_type_audio"                         | 是否为音频直播                   |
## | live_type_linkmic                | bool              | YES  |     | NULL    |       | "$.data.room.live_type_linkmic"                       | 是否为连麦直播                   |
## | live_type_normal                 | bool              | YES  |     | NULL    |       | "$.data.room.live_type_normal"                        | 是否为普通直播                   |
## | live_type_official               | bool              | YES  |     | NULL    |       | "$.data.room.live_type_official"                      | 是否为官方直播                   |
## | live_type_sandbox                | bool              | YES  |     | NULL    |       | "$.data.room.live_type_sandbox"                       | 是否为沙盒直播                   |
## | live_type_screenshot             | bool              | YES  |     | NULL    |       | "$.data.room.live_type_screenshot"                    | 是否为截图直播                   |
## | live_type_third_party            | bool              | YES  |     | NULL    |       | "$.data.room.live_type_third_party"                   | 是否为第三方直播                 |
## | live_type_vs_live                | bool              | YES  |     | NULL    |       | "$.data.room.live_type_vs_live"                       | 是否为VS直播                     |
## | live_type_vs_premiere            | bool              | YES  |     | NULL    |       | "$.data.room.live_type_vs_premiere"                   | 是否为VS首播                     |
## | admin_flag                       | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.living_room_attrs.admin_flag"            | 直播间管理员标志                  |
## | location                         | varchar(100)      | YES  |     | NULL    |       | "$.data.room.location"                                | 直播间位置                        |
## | official_channel_open_id         | varchar(200)      | YES  |     | NULL    |       | "$.data.room.official_channel_open_id"                | 官方频道OpenID                   |
## | official_channel_uid             | varchar(200)      | YES  |     | NULL    |       | "$.data.room.official_channel_uid"                    | 官方频道用户ID                   |
## | orientation                      | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.orientation"                             | 直播间方向                       |
## | os_type                          | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.os_type"                                 | 操作系统类型                     |
## | owner_device_id                  | varchar(200)      | YES  |     | NULL    |       | "$.data.room.owner.owner_device_id"                   | 主播设备ID                      |
## | owner_open_id                    | varchar(200)      | YES  |     | NULL    |       | "$.data.room.owner.owner_open_id"                     | 主播OpenID                      | 
## | owner_user_id                    | varchar(200)      | YES  |     | NULL    |       | "$.data.room.owner_user_id"                           | 账号作者ID                      |
## | start_time                       | timestamp         | YES  |     | NULL    |       | "$.data.room.start_time"                              | 开始时间                         | 
## | room_layout                      | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.room_layout"                             | 直播间布局                        |
## | room_tag                         | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.room_tag"                                | 直播间标签                        |
## | scroll_config                    | text              | YES  |     | NULL    |       | "$.data.room.scroll_config"                           | 滚动配置                          |
## | search_id                        | varchar(200)      | YES  |     | NULL    |       | "$.data.room.search_id"                               | 直播间搜索ID                     |
## | sell_goods                       | bool              | YES  |     | NULL    |       | "$.data.room.sell_goods"                              | 卖货                             |
## | share_msg_style                  | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.share_msg_style"                         | 分享消息样式                      |
## | share_url                        | text              | YES  |     | NULL    |       | "$.data.room.share_url"                               | 直播间分享链接                    |
## | title                            | tinytext          | YES  |     | NULL    |       | "$.data.room.title"                                   | 直播间标题                       |
## | title_recommend                  | bool              | YES  |     | NULL    |       | "$.data.room.title_recommend"                         | 是否推荐标题                     |
## | toutiao_cover_recommend_level    | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.toutiao_cover_recommend_level"           | 头条封面推荐等级                 |
## | toutiao_title_recommend_level    | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.toutiao_title_recommend_level"           | 头条标题推荐等级                 |
## | use_filter                       | bool              | YES  |     | NULL    |       | "$.data.room.use_filter"                              | 是否使用滤镜                     |
## | user_count                       | unsigned int      | YES  |     | NULL    |       | "$.data.room.user_count"                              | 用户数量                         |
## | vertical_cover_uri               | text              | YES  |     | NULL    |       | "$.data.room.vertical_cover_uri"                      | 竖屏封面URI                      |
## | vid                              | varchar(200)      | YES  |     | NULL    |       | "$.data.room.vid"                                     | 视频ID                          |
## | video_feed_tag                   | tinytext          | YES  |     | NULL    |       | "$.data.room.video_feed_tag"                          | 视频Feed标签                     |
## | visibility_range                 | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.visibility_range"                        | 可见范围：X-公开 X-私密 X-好友可见 |
## | vs_main_replay_id                | varchar(200)      | YES  |     | NULL    |       | "$.data.room.vs_main_replay_id"                       | VS主回放ID                       |
## | wait_copy                        | tinytext          | YES  |     | NULL    |       | "$.data.room.wait_copy"                               | 等待复制                         |
## | webcast_sdk_version              | varchar(20)       | YES  |     | NULL    |       | "$.data.room.webcast_sdk_version"                     | 直播间SDK版本                     |
## +----------------------------------+-------------------+------+-----+---------+-------+-------------------------------------------------------+----------------------------------+YES
##
  __ROOM_ATTRIBUTE_TABLE_NAME   = 'room_attribute'
  __ROOM_ATTRIBUTE_TABLE_HEADER = ['AnchorABMap',                   'acquaintance_status',           'anchor_scheduled_time_text',    'anchor_share_text',    'anchor_tab_type', 
                                   'app_id',                        'auth_city',                     'auto_cover',                    'base_category',        'book_end_time', 
                                   'book_time',                     'business_live',                 'category',                      'cell_style',           'city_top_distance', 
                                   'client_version',                'placeholder',                   'comment_name_mode',             'common_label_list',    'content_tag', 
                                   'create_time',                   'distance',                      'distance_city',                 'distance_km',          'dynamic_cover_dict',
                                   'dynamic_cover_uri',             'enable_room_perspective',       'create_scene',                  'facial_unrecognised',  'geo_block', 
                                   'is_sandbox',                    'is_virtual_anchor',             'limit_appid',                   'limit_strategy',       'realtime_playback_shift',
                                   'realtime_playback_start_shift', 'realtime_replay_enabled',       'vr_type',                       'vs_type',              'xigua_uid',
                                   'fansclub_msg_style',            'fcdn_appid',                    'finish_reason',                 'finish_time',          'finish_url', 
                                   'follow_msg_style',              'forum_extra_data',              'game_room_type',                'gift_msg_style',       'group_id',
                                   'group_source',                  'has_commerce_goods',            'has_promotion_games',           'highlight',            'id', 
                                   'introduction',                  'is_need_check_list',            'is_official_channel_room',      'is_replay',            'is_show_inquiry_ball', 
                                   'is_show_user_card_switch',      'item_explicit_info',            'layout',                        'linkmic_display_type', 'linkmic_layout',
                                   'live_id',                       'live_platform_source',          'live_room_mode',                'live_type_audio',      'live_type_linkmic', 
                                   'live_type_normal',              'live_type_official',            'live_type_sandbox',             'live_type_screenshot', 'live_type_third_party',
                                   'live_type_vs_live',             'live_type_vs_premiere',         'admin_flag',                    'location',             'official_channel_open_id', 
                                   'official_channel_uid',          'orientation',                   'os_type',                       'owner_device_id',      'owner_open_id',
                                   'owner_user_id',                 'start_time',                    'room_layout',                   'room_tag',             'scroll_config',
                                   'search_id',                     'sell_goods',                    'share_msg_style',               'share_url',            'title',
                                   'title_recommend',               'toutiao_cover_recommend_level', 'toutiao_title_recommend_level', 'use_filter',           'user_count',
                                   'vertical_cover_uri',            'vid',                           'video_feed_tag',                'visibility_range',     'vs_main_replay_id', 
                                   'wait_copy',                     'webcast_sdk_version'
                                   ]
  __ROOM_ATTRIBUTE_TABLE_PRI_KEY = ['id']
  __ROOM_ATTRIBUTE_TABLE_TUPLE   = {item:None for item in __ROOM_ATTRIBUTE_TABLE_HEADER}
  __SQL_CREATE_ROOM_ATTRIBUTE_TABLE = '''
                                      CREATE TABLE IF NOT EXISTS {} (
                                        AnchorABMap                      JSON           DEFAULT NULL,
                                        acquaintance_status              tinyint        DEFAULT NULL,
                                        anchor_scheduled_time_text       text           DEFAULT NULL,
                                        anchor_share_text                text           DEFAULT NULL,
                                        anchor_tab_type                  tinyint        DEFAULT NULL,
                                        app_id                           varchar(200)   DEFAULT NULL,
                                        auth_city                        varchar(100)   DEFAULT NULL,
                                        auto_cover                       tinyint        DEFAULT NULL,
                                        base_category                    tinyint        DEFAULT NULL,
                                        book_end_time                    timestamp      DEFAULT NULL,
                                        book_time                        timestamp      DEFAULT NULL,
                                        business_live                    tinyint        DEFAULT NULL,
                                        category                         tinyint        DEFAULT NULL,
                                        cell_style                       tinyint        DEFAULT NULL,
                                        city_top_distance                tinytext       DEFAULT NULL,
                                        client_version                   varchar(20)    DEFAULT NULL,
                                        placeholder                      tinytext       DEFAULT NULL,
                                        comment_name_mode                tinyint        DEFAULT NULL,
                                        common_label_list                tinytext       DEFAULT NULL,
                                        content_tag                      tinytext       DEFAULT NULL,
                                        create_time                      timestamp      DEFAULT NULL,
                                        distance                         varchar(100)   DEFAULT NULL,
                                        distance_city                    varchar(100)   DEFAULT NULL,
                                        distance_km                      varchar(100)   DEFAULT NULL,
                                        dynamic_cover_dict               JSON           DEFAULT NULL,
                                        dynamic_cover_uri                text           DEFAULT NULL,
                                        enable_room_perspective          bool           DEFAULT NULL,
                                        create_scene                     tinytext       DEFAULT NULL,
                                        facial_unrecognised              tinyint        DEFAULT NULL,
                                        geo_block                        tinyint        DEFAULT NULL,
                                        is_sandbox                       bool           DEFAULT NULL,
                                        is_virtual_anchor                bool           DEFAULT NULL,
                                        limit_appid                      varchar(200)   DEFAULT NULL,
                                        limit_strategy                   tinyint        DEFAULT NULL,
                                        realtime_playback_shift          tinyint        DEFAULT NULL,
                                        realtime_playback_start_shift    tinytext       DEFAULT NULL,
                                        realtime_replay_enabled          bool           DEFAULT NULL,
                                        vr_type                          tinyint        DEFAULT NULL,
                                        vs_type                          tinyint        DEFAULT NULL,
                                        xigua_uid                        varchar(200)   DEFAULT NULL,
                                        fansclub_msg_style               tinyint        DEFAULT NULL,
                                        fcdn_appid                       varchar(200)   DEFAULT NULL,
                                        finish_reason                    tinyint        DEFAULT NULL,
                                        finish_time                      timestamp      DEFAULT NULL,
                                        finish_url                       text           DEFAULT NULL,
                                        follow_msg_style                 tinyint        DEFAULT NULL,
                                        forum_extra_data                 text           DEFAULT NULL,
                                        game_room_type                   tinyint        DEFAULT NULL,
                                        gift_msg_style                   tinyint        DEFAULT NULL,
                                        group_id                         varchar(200)   DEFAULT NULL,
                                        group_source                     tinyint        DEFAULT NULL,
                                        has_commerce_goods               bool           DEFAULT NULL,
                                        has_promotion_games              bool           DEFAULT NULL,
                                        highlight                        bool           DEFAULT NULL,
                                        id                               varchar(200)   NOT     NULL,
                                        introduction                     text           DEFAULT NULL,
                                        is_need_check_list               bool           DEFAULT NULL,
                                        is_official_channel_room         bool           DEFAULT NULL,
                                        is_replay                        bool           DEFAULT NULL,
                                        is_show_inquiry_ball             bool           DEFAULT NULL,
                                        is_show_user_card_switch         bool           DEFAULT NULL,
                                        item_explicit_info               text           DEFAULT NULL,
                                        layout                           tinyint        DEFAULT NULL,
                                        linkmic_display_type             tinyint        DEFAULT NULL,
                                        linkmic_layout                   tinyint        DEFAULT NULL,
                                        live_id                          varchar(200)   DEFAULT NULL,
                                        live_platform_source             tinytext       DEFAULT NULL,
                                        live_room_mode                   tinyint        DEFAULT NULL,
                                        live_type_audio                  bool           DEFAULT NULL,
                                        live_type_linkmic                bool           DEFAULT NULL,
                                        live_type_normal                 bool           DEFAULT NULL,
                                        live_type_official               bool           DEFAULT NULL,
                                        live_type_sandbox                bool           DEFAULT NULL,
                                        live_type_screenshot             bool           DEFAULT NULL,
                                        live_type_third_party            bool           DEFAULT NULL,
                                        live_type_vs_live                bool           DEFAULT NULL,
                                        live_type_vs_premiere            bool           DEFAULT NULL,
                                        admin_flag                       tinyint        DEFAULT NULL,
                                        location                         varchar(100)   DEFAULT NULL,
                                        official_channel_open_id         varchar(200)   DEFAULT NULL,
                                        official_channel_uid             varchar(200)   DEFAULT NULL,
                                        orientation                      tinyint        DEFAULT NULL,
                                        os_type                          tinyint        DEFAULT NULL,
                                        owner_device_id                  varchar(200)   DEFAULT NULL,
                                        owner_open_id                    varchar(200)   DEFAULT NULL,
                                        owner_user_id                    varchar(200)   DEFAULT NULL,
                                        start_time                       timestamp      DEFAULT NULL,
                                        room_layout                      tinyint        DEFAULT NULL,
                                        room_tag                         tinyint        DEFAULT NULL,
                                        scroll_config                    text           DEFAULT NULL,
                                        search_id                        varchar(200)   DEFAULT NULL,
                                        sell_goods                       bool           DEFAULT NULL,
                                        share_msg_style                  tinyint        DEFAULT NULL,
                                        share_url                        text           DEFAULT NULL,
                                        title                            tinytext       DEFAULT NULL,
                                        title_recommend                  bool           DEFAULT NULL,
                                        toutiao_cover_recommend_level    tinyint        DEFAULT NULL,
                                        toutiao_title_recommend_level    tinyint        DEFAULT NULL,
                                        use_filter                       bool           DEFAULT NULL,
                                        user_count                       int            DEFAULT NULL,
                                        vertical_cover_uri               text           DEFAULT NULL,
                                        vid                              varchar(200)   DEFAULT NULL,
                                        video_feed_tag                   tinytext       DEFAULT NULL,
                                        visibility_range                 tinyint        DEFAULT NULL,
                                        vs_main_replay_id                varchar(200)   DEFAULT NULL,
                                        wait_copy                        tinytext       DEFAULT NULL,
                                        webcast_sdk_version              varchar(20)    DEFAULT NULL,
                                        PRIMARY KEY (id)
                                      )
                                      '''.format(__ROOM_ATTRIBUTE_TABLE_NAME)
  __SQL_DROP_ROOM_ATTRIBUTE_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_ATTRIBUTE_TABLE_NAME)

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
  ## get room attribute table name
  ##
  def get_name(self) -> str:
    return self.__ROOM_ATTRIBUTE_TABLE_NAME
  
  ##
  ## get room attribute table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_ATTRIBUTE_TABLE_HEADER

  ##
  ## get room attribute table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_ATTRIBUTE_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_ATTRIBUTE_TABLE_PRI_KEY

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_ATTRIBUTE_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_ATTRIBUTE_TABLE

##
## >>============================= sub class method =============================>>
##

##
## >>================================ test method ===============================>>
##

##
## test: create room_attribute table
##
def test_create_room_attribute_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create room_attribute table
  ##
  room_attribute = RoomAttributeTable(db_instance=db)
  room_attribute.create()
  return

##
## test: drop room_attribute table
##
def test_drop_room_attribute_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database is valid
  ##
  if db is None:
    get_logger().error("db_instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop room_attribute table
  ##
  room_attribute = RoomAttributeTable(db)
  room_attribute.drop()
  return

##
## test: check if room_attribute table exists
##
def test_check_room_attribute_table_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid {} instance".format(type(db)))
    raise ValueError
  
  ##
  ## check if room attribute table exists
  ##
  room_attribute = RoomAttributeTable(db)
  if db.is_table_exist(room_attribute.get_name()):
    get_logger().info("{} table exists!".format(room_attribute.get_name()))
  else:
    get_logger().info("{} table not exists!".format(room_attribute.get_name()))
  return

##
## test: insert room attribute record
##
def test_insert_room_attribute(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid {} instance".format(type(db)))
    raise ValueError
  
  ##
  ## create room_attribute table if not exists
  ##
  room_attribute = RoomAttributeTable(db)
  
  sample_record = {
    "id": "7411524533301119798"
  }
  
  ##
  ## insert a sample room attribute record
  ##
  try:
    room_attribute.insert_record(sample_record)
    get_logger().info("sample room attribute record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample {} record: {}".format(room_attribute.get_name(), e))
    raise e

##
## test: delete room attribute record
##
def test_delete_room_attribute_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create room_attribute table if not exist
  ##
  room_attribute = RoomAttributeTable(db)
  
  ##
  ## delete a sample room attribute record
  ##
  sample_record = {
    'id':'7411524533301119798'
  }
  
  try:
    room_attribute.delete_record(sample_record)
    get_logger().info("sample room attribute record delete successfully")
  except Exception as e:
    get_logger().error("failed to delete sample room attribute record: {}".format(e))
    raise e    

##
## test: update room attribute record
##
def test_update_room_attribute_record(db:SocialMediaStreamDataBase) -> None:
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## create room_attribute table if not exist
  ##
  room_attribute = RoomAttributeTable(db)
  sample_record = {
    'id':'7411524533301119798',
    'app_id':'1223456789'
  }
  
  ##
  ## update a sample room attribute record
  ##  
  try:
    room_attribute.update_record(sample_record)
    get_logger().info("sample room attribute record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample room attribute: {}".format(e))
    raise e
 
##
## test: get room attribute record
## 
def test_get_room_attribute_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create room_attribute table if not exist
  ##
  room_attribute = RoomAttributeTable(db)
  
  ##
  ## get a sample room attribute record
  ##
  sample_record = {
    'id':'7411524533301119798'
  }
  
  try:
    record = room_attribute.get_record(sample_record)
    if record:
      get_logger().info("sample room attribute record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample live record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample room attribute record: {}".format(e))
    raise e
 
class RoomPackMetaTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##

##
## room pack meta table
## +----------------------------------+-------------------+------+-----+---------+-------+------------------------------------------------------+---------------------+
## | Field                            | Type              | Null | Key | Default | Extra | Topology                                             | Comment             |
## +----------------------------------+-------------------+------+-----+---------+-------+------------------------------------------------------+---------------------+
## | now                              | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"                                        | 当前时间戳           | 
## | platform                         | varchar(20)       | NO   | PRI |         |       |           -                                          | 平台                 | 
## | room_id                          | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                                     | 直播间ID             | 
## | cluster                          | varchar(50)       | YES  |     | NULL    |       | "$.data.room.pack_meta.cluster"                      | 集群                |
## | dc                               | varchar(50)       | YES  |     | NULL    |       | "$.data.room.pack_meta.dc"                           | 数据中心             |
## | env                              | varchar(50)       | YES  |     | NULL    |       | "$.data.room.pack_meta.env"                          | 环境                |
## | extras                           | json              | YES  |     | NULL    |       | "$.data.room.pack_meta.extras"                       | 附加信息             |
## | scene                            | text              | YES  |     | NULL    |       | "$.data.room.pack_meta.scene"                        | 场景                |
## | trace_id                         | varchar(200)      | YES  |     | NULL    |       | "$.data.room.pack_meta.trace_id"                     | 跟踪ID              |
## +----------------------------------+-------------------+------+-----+---------+-------+------------------------------------------------------+---------------------+
##

  __ROOM_PACK_META_TABLE_NAME       = "room_pack_meta"
  __ROOM_PACK_META_TABLE_HEADER     = ['now',       'platform', 'room_id',
                                       'cluster ',  'dc',       'env',
                                       'extras',    'scene',    'trace_id'
                                       ]
  __ROOM_PACK_META_TABLE_PRI_KEY    = ['now','platform','room_id']
  __ROOM_PACK_META_TABLE_TUPLE      = {item:None for item in __ROOM_PACK_META_TABLE_HEADER}
  __SQL_CREATE_ROOM_PACK_META_TABLE = '''
                                      CREATE TABLE IF NOT EXISTS {} (
                                        now        timestamp(3) NOT NULL,
                                        platform   varchar(20)  NOT NULL,
                                        room_id    varchar(200) NOT NULL,
                                        cluster    varchar(50)  DEFAULT NULL,
                                        dc         varchar(50)  DEFAULT NULL,
                                        env        varchar(50)  DEFAULT NULL,
                                        extras     json         DEFAULT NULL,
                                        scene      text         DEFAULT NULL,
                                        trace_id   varchar(200) DEFAULT NULL,
                                        PRIMARY KEY (now, platform, room_id)
                                      )
                                      '''.format(__ROOM_PACK_META_TABLE_NAME)
  __SQL_DROP_ROOM_PACK_META_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_PACK_META_TABLE_NAME)

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
    return self.__ROOM_PACK_META_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_PACK_META_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_PACK_META_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_PACK_META_TABLE_PRI_KEY

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_PACK_META_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_PACK_META_TABLE

##
## >>================================ test method ===============================>>
##

##
## test: create table
##
def test_create_room_pack_meta_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create room pack meta table
  ##
  room_pack_meta = RoomPackMetaTable(db_instance=db)
  room_pack_meta.create()
  return

##
## test: drop table
##
def test_drop_room_pack_meta_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop room pack meta table
  ##
  room_pack_meta = RoomPackMetaTable(db_instance=db)
  room_pack_meta.drop()
  return

##
## test: check if table exists
##
def test_check_room_pack_meta_table_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  room_pack_meta = RoomPackMetaTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(room_pack_meta.get_name()):
    get_logger().info("{} table exists!".format(room_pack_meta.get_name()))
  else:
    get_logger().info("{} table not exists!".format(room_pack_meta.get_name()))
  return

##
## test: insert record
##
def test_insert_room_pack_meta_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_pack_meta = RoomPackMetaTable(db_instance=db)
  
  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'cluster':'default',
    'dc':'lf',
    'env':'prod',
    'scene':'reflow_room_info(prod_single_dc/rpc/topo)'
  }
  
  try:
    room_pack_meta.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_room_pack_meta_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create room_pack_meta table if not exists
  ##
  room_pack_meta = RoomPackMetaTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  now = dat.fromtimestamp(1740301577026/1000.0)
  print(now)
  sample_record = {
    'now':now,
    'platform':'douyin',
    'room_id':'7411524533301119798'
  }
  
  try:
    room_pack_meta.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_room_pack_meta_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create room_pack_meta table if not exists
  ##
  room_pack_meta = RoomPackMetaTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'cluster':'default',
    'dc':'lf',
    'env':'test',
    'scene':'reflow_room_info(prod_single_dc/rpc/topo)'
  }
  
  try:
    room_pack_meta.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_room_pack_meta_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  room_pack_meta = RoomPackMetaTable(db)
  
  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    record = room_pack_meta.get_record(sample_record)
    if record:
      get_logger().info("sample room pack meta record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample room pack meta record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample room pack meta record: {}".format(e))
    raise e
 

class RoomPaidLiveDataTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##

##
## room paid live data header
## +----------------------------------+-------------------+------+-----+---------+-------+------------------------------------------------------+---------------------+
## | Field                            | Type              | Null | Key | Default | Extra | Topology                                             | Comment             |
## +----------------------------------+-------------------+------+-----+---------+-------+------------------------------------------------------+---------------------+
## | now                              | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"                                        | 当前时间戳           | 
## | platform                         | varchar(20)       | NO   | PRI |         |       |           -                                          | 平台                 | 
## | room_id                          | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                                     | 直播间ID             | 
## | anchor_right                     | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.paid_live_data.anchor_right"            | 主播权限             |
## | delivery                         | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.paid_live_data.delivery"                | 交付状态             |
## | duration                         | unsigned int      | YES  |     | NULL    |       | "$.data.room.paid_live_data.duration"                | 直播时长             |
## | max_preview_duration             | unsigned int      | YES  |     | NULL    |       | "$.data.room.paid_live_data.max_preview_duration"    | 最大预览时长          |
## | need_delivery_notice             | bool              | YES  |     | NULL    |       | "$.data.room.paid_live_data.need_delivery_notice"    | 是否需要交付通知      |
## | paid_type                        | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.paid_live_data.paid_type"               | 付费类型             |
## | pay_ab_type                      | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.paid_live_data.pay_ab_type"             | 付费AB类型           |
## | privilege_info                   | json              | YES  |     | NULL    |       | "$.data.room.paid_live_data.privilege_info"          | 特权信息             |
## | privilege_info_map               | json              | YES  |     | NULL    |       | "$.data.room.paid_live_data.privilege_info_map"      | 特权信息映射         |
## | view_right                       | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.paid_live_data.view_right"              | 观看权限             |
## +----------------------------------+-------------------+------+-----+---------+-------+------------------------------------------------------+---------------------+
##

  __ROOM_PAID_LIVE_DATA_TABLE_NAME        = "room_paid_live_data"
  __ROOM_PAID_LIVE_DATA_TABLE_HEADER      = ['now',                  'platform',              'room_id',
                                             'anchor_right',         'delivery',              'duration',
                                             'max_preview_duration', 'need_delivery_notice',  'paid_type',
                                             'pay_ab_type',          'privilege_info',        'privilege_info_map',
                                             'view_right'
                                             ]
  __ROOM_PAID_LIVE_DATA_TABLE_PRI_KEY    = ['now','platform','room_id']
  __ROOM_PAID_LIVE_DATA_TABLE_TUPLE      = {item:None for item in __ROOM_PAID_LIVE_DATA_TABLE_HEADER}
  __SQL_CREATE_ROOM_PAID_LIVE_DATA_TABLE = '''
                                           CREATE TABLE IF NOT EXISTS {} (
                                             now                  timestamp(3)     NOT NULL,
                                             platform             varchar(20)      NOT NULL,
                                             room_id              varchar(200)     NOT NULL,
                                             anchor_right         tinyint          DEFAULT NULL,
                                             delivery             tinyint          DEFAULT NULL,
                                             duration             int              DEFAULT NULL,
                                             max_preview_duration int              DEFAULT NULL,
                                             need_delivery_notice bool             DEFAULT NULL,
                                             paid_type            tinyint          DEFAULT NULL,
                                             pay_ab_type          tinyint          DEFAULT NULL,
                                             privilege_info       json             DEFAULT NULL,
                                             privilege_info_map   json             DEFAULT NULL,
                                             view_right           tinyint          DEFAULT NULL,
                                             PRIMARY KEY (now, platform, room_id)
                                           )
                                           '''.format(__ROOM_PAID_LIVE_DATA_TABLE_NAME)
  __SQL_DROP_ROOM_PAID_LIVE_DATA_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_PAID_LIVE_DATA_TABLE_NAME)
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
    return self.__ROOM_PAID_LIVE_DATA_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_PAID_LIVE_DATA_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_PAID_LIVE_DATA_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_PAID_LIVE_DATA_TABLE_PRI_KEY

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_PAID_LIVE_DATA_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_PAID_LIVE_DATA_TABLE

##
## >>================================ test method ===============================>>
##

##
## test: create table
##
def test_create_room_room_paid_live_data_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create room pack meta table
  ##
  room_room_paid_live_data = RoomPaidLiveDataTable(db_instance=db)
  room_room_paid_live_data.create()
  return

##
## test: drop table
##
def test_drop_room_room_paid_live_data(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop room pack meta table
  ##
  room_room_paid_live_data = RoomPaidLiveDataTable(db_instance=db)
  room_room_paid_live_data.drop()
  return

##
## test: check if table exists
##
def test_check_room_room_paid_live_data_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  room_room_paid_live_data = RoomPaidLiveDataTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(room_room_paid_live_data.get_name()):
    get_logger().info("{} table exists!".format(room_room_paid_live_data.get_name()))
  else:
    get_logger().info("{} table not exists!".format(room_room_paid_live_data.get_name()))
  return

##
## test: insert record
##
def test_insert_room_paid_live_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_room_paid_live_data = RoomPaidLiveDataTable(db_instance=db)
  
  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    room_room_paid_live_data.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_room_room_paid_live_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_room_paid_live_data = RoomPaidLiveDataTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'now':dat.fromtimestamp(1740301577026/1000.0),
    'platform':'douyin',
    'room_id':'7411524533301119798'
  }
  
  try:
    room_room_paid_live_data.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_room_paid_live_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_paid_live_data = RoomPaidLiveDataTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'anchor_right':0,
    'need_delivery_notice':False,
    'view_right':0
  }
  
  try:
    room_paid_live_data.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_room_paid_live_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  room_paid_live_data = RoomPaidLiveDataTable(db)
  
  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    record = room_paid_live_data.get_record(sample_record)
    if record:
      get_logger().info("sample room paid live data record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample room paid live data record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample room paid live data record: {}".format(e))
    raise e

##
## >>================================ main method ===============================>>
##
if __name__ == "__main__":
  db = SocialMediaStreamDataBase(host='192.168.1.12', user='wangyan', passwd='wuyu1998', database='social_media_stream_downloader')
  
  ##
  ## room attribute table
  ##
  # test_create_room_attribute_table(db)
  # test_check_room_attribute_table_exists(db)
  # test_insert_room_attribute(db)
  # test_update_room_attribute_record(db)
  # test_get_room_attribute_record(db)
  # test_delete_room_attribute_record(db)
  # test_drop_room_attribute_table(db)
  # test_check_room_attribute_table_exists(db)
  
  ##
  ## room pack meta table
  ##
  # test_create_room_pack_meta_table(db)
  # test_check_room_pack_meta_table_exists(db)
  # test_insert_room_pack_meta_record(db)
  # test_update_room_pack_meta_record(db)
  # test_get_room_pack_meta_record(db)
  # test_delete_room_pack_meta_record(db)
  # test_drop_room_pack_meta_table(db)
  # test_check_room_pack_meta_table_exists(db)
  
  ##
  ## room paid live data table
  ##
  # test_create_room_room_paid_live_data_table(db)
  # test_check_room_room_paid_live_data_exists(db)
  # test_insert_room_paid_live_data_record(db)
  # test_update_room_paid_live_data_record(db)
  # test_get_room_paid_live_data_record(db)
  # test_delete_room_room_paid_live_data_record(db)
  # test_drop_room_room_paid_live_data(db)
  # test_check_room_room_paid_live_data_exists(db)