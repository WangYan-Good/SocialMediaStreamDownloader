##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Third-Part>>
from backend.src.database.social_media_stream_database                import SocialMediaStreamDataBase
from backend.src.database.table.social_media_stream_db_table          import SocialMediaStreamDataTable

##
## room attribute table
##
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
class RoomAttributeTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
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
## room admin user id
##
##+---------------------+-------------------+------+-----+---------+-------+------------------------------+---------------------+
##| Field               | Type              | Null | Key | Default | Extra | Topology                     | Comment             |
##+---------------------+-------------------+------+-----+---------+-------+------------------------------+---------------------+
##| now                 | timestamp(3)      | NO   | PRI |         |       | "$.data.room.create_time"    | 当前时间戳           |
##| platform            | varchar(20)       | NO   | PRI |         |       |           -                  | 平台                 |
##| room_id             | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"             | 直播间ID             |
##| admin_user_id_index | unsigned tinyint  | NO   | PRI |         |       |           -                  | 直播间管理员ID序号    |
##| admin_user_id       | varchar(200)      |      |     | NULL    |       | "$.data.room.admin_user_ids" | 直播间管理员用户ID    | 
##+---------------------+-------------------+------+-----+---------+-------+------------------------------+---------------------+
##
class RoomAdminUserIdTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_ADMIN_USER_ID_TABLE_NAME       = 'room_admin_user_id'
  __ROOM_ADMIN_USER_ID_TABLE_HEADER     = ['now',                 'platform',     'room_id',
                                           'admin_user_id_index', 'admin_user_id'
                                           ]
  __ROOM_ADMIN_USER_ID_TABLE_PRI_KEY    = ['now', 'platform', 'room_id', 'admin_user_id_index']
  __ROOM_ADMIN_USER_ID_TABLE_TUPLE      = {item:None for item in __ROOM_ADMIN_USER_ID_TABLE_HEADER}
  __SQL_CREATE_ROOM_ADMIN_USER_ID_TABLE = '''
                                          CREATE TABLE IF NOT EXISTS {} (
                                            now                    timestamp(3) NOT NULL,
                                            platform               varchar(20)  NOT NULL,
                                            room_id                varchar(200) NOT NULL,
                                            admin_user_id_index    tinyint      NOT NULL,
                                            admin_user_id          varchar(200) DEFAULT NULL,
                                            PRIMARY KEY (now, platform, room_id, admin_user_id_index)
                                          )
                                          '''.format(__ROOM_ADMIN_USER_ID_TABLE_NAME)
  __SQL_DROP_ROOM_ADMIN_USER_ID_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_ADMIN_USER_ID_TABLE_NAME)


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
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__ROOM_ADMIN_USER_ID_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_ADMIN_USER_ID_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_ADMIN_USER_ID_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_ADMIN_USER_ID_TABLE_PRI_KEY

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_ADMIN_USER_ID_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_ADMIN_USER_ID_TABLE

##
## room admin user open id table
##
## +-----------------------+-------------------+------+-----+---------+-------+-----------------------------------+---------------------+
## | Field                 | Type              | Null | Key | Default | Extra | Topology                          | Comment             |
## +-----------------------+-------------------+------+-----+---------+-------+-----------------------------------+---------------------+
## | now                   | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"                     | 当前时间戳           | 
## | platform              | varchar(20)       | NO   | PRI |         |       |           -                       | 平台                 | 
## | room_id               | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                  | 直播间ID             |
## | admin_user_open_index | unsigned tinyint  | NO   | PRI |         |       |           -                       | 直播间管理员用户ID序号|
## | admin_user_open_id    | varchar(200)      |      |     | NULL    |       | "$.data.room.admin_user_open_ids" | 直播间管理员用户ID    | 
## +-----------------------+-------------------+------+-----+---------+-------+-----------------------------------+---------------------+
##
class RoomAdminUserOpenIdTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_ADMIN_USER_OPEN_ID_TABLE_NAME       = 'room_admin_user_open_id'
  __ROOM_ADMIN_USER_OPEN_ID_TABLE_HEADER     = ['now',                   'platform',          'room_id',
                                                'admin_user_open_index', 'admin_user_open_id'
                                                ]
  __ROOM_ADMIN_USER_OPEN_ID_TABLE_PRI_KEY    = ['now', 'platform', 'room_id', 'admin_user_open_index']
  __ROOM_ADMIN_USER_OPEN_ID_TABLE_TUPLE      = {item:None for item in __ROOM_ADMIN_USER_OPEN_ID_TABLE_HEADER}
  __SQL_CREATE_ROOM_ADMIN_USER_OPEN_ID_TABLE = '''
                                               CREATE TABLE IF NOT EXISTS {} (
                                                 now                      timestamp(3) NOT NULL,
                                                 platform                 varchar(20)  NOT NULL,
                                                 room_id                  varchar(200) NOT NULL,
                                                 admin_user_open_index    tinyint      NOT NULL,
                                                 admin_user_open_id       varchar(200) DEFAULT NULL,
                                                 PRIMARY KEY (now, platform, room_id, admin_user_open_index)
                                               )
                                               '''.format(__ROOM_ADMIN_USER_OPEN_ID_TABLE_NAME)
  __SQL_DROP_ROOM_ADMIN_USER_OPEN_ID_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_ADMIN_USER_OPEN_ID_TABLE_NAME)


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
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__ROOM_ADMIN_USER_OPEN_ID_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_ADMIN_USER_OPEN_ID_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_ADMIN_USER_OPEN_ID_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_ADMIN_USER_OPEN_ID_TABLE_PRI_KEY

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_ADMIN_USER_OPEN_ID_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_ADMIN_USER_OPEN_ID_TABLE

'''
  TBD: no related data type of room_assist_label
'''
class RoomAssistLabelTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##

##
## data.room.assist_label_list
##
## +--------------------+-------------------+------+-----+---------+-------+---------------------------------+---------------------+
## | Field              | Type              | Null | Key | Default | Extra | Topology                        | Comment             |
## +--------------------+-------------------+------+-----+---------+-------+---------------------------------+---------------------+
## | now                | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"                   | 当前时间戳           | 
## | platform           | varchar(20)       | NO   | PRI |         |       |           -                     | 平台                 | 
## | room_id            | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                | 直播间ID             | 
## | assist_label_index | unsigned tinyint  |      |     | NULL    |       |           -                     | 直播间辅助标签序号   |
## | assist_label       | TBD               |      |     | NULL    |       | "$.data.room.assist_label_list" | 直播间辅助标签       | 
## +--------------------+-------------------+------+-----+---------+-------+---------------------------------+---------------------+
##

  __ROOM_ASSIST_LABEL_TABLE_NAME       = 'room_assist_label'
  __ROOM_ASSIST_LABEL_TABLE_HEADER     = ['now',                'platform',    'room_id',
                                               'assist_label_index', 'assist_label'
                                               ]
  __ROOM_ASSIST_LABEL_TABLE_PRI_KEY    = ['now', 'platform', 'room_id']
  __ROOM_ASSIST_LABEL_TABLE_TUPLE      = {item:None for item in __ROOM_ASSIST_LABEL_TABLE_HEADER}
  __SQL_CREATE_ROOM_ASSIST_LABEL_TABLE = '''
                                              CREATE TABLE IF NOT EXISTS {} (
                                                now                   timestamp(3) NOT NULL,
                                                platform              varchar(20)  NOT NULL,
                                                room_id               varchar(200) NOT NULL,
                                                assist_label_index    tinyint      DEFAULT NULL,
                                                assist_label          TBD          DEFAULT NULL,
                                                PRIMARY KEY (now, platform, room_id)
                                              )
                                              '''.format(__ROOM_ASSIST_LABEL_TABLE_NAME)
  __SQL_DROP_ROOM_ASSIST_LABEL_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_ASSIST_LABEL_TABLE_NAME)


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
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__ROOM_ASSIST_LABEL_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_ASSIST_LABEL_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_ASSIST_LABEL_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_ASSIST_LABEL_TABLE_PRI_KEY

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_ASSIST_LABEL_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_ASSIST_LABEL_TABLE


'''
  TBD: no related data type of room_deco
'''
class RoomDecoTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##

##
## $.data.room.deco_list
##
## +------------+-------------------+------+-----+---------+-------+-------------------------+---------------------+
## | Field      | Type              | Null | Key | Default | Extra | Topology                | Comment             |
## +------------+-------------------+------+-----+---------+-------+-------------------------+---------------------+
## | now        | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"           | 当前时间戳           | 
## | platform   | varchar(20)       | NO   | PRI |         |       |           -             | 平台                 | 
## | room_id    | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"        | 直播间ID             |
## | deco_index | unsigned tinyint  |      |     | NULL    |       |           -             | 装饰索引号            |  
## | deco       | TBD               |      |     | NULL    |       | "$.data.room.deco_list" | 装饰                 | 
## +------------+-------------------+------+-----+---------+-------+-------------------------+----------------------+
##

  __ROOM_DECO_TABLE_NAME       = 'room_deco'
  __ROOM_DECO_TABLE_HEADER     = ['now',        'platform',    'room_id',
                                  'deco_index', 'deco'
                                  ]
  __ROOM_DECO_TABLE_PRI_KEY    = ['now', 'platform', 'room_id']
  __ROOM_DECO_TABLE_TUPLE      = {item:None for item in __ROOM_DECO_TABLE_HEADER}
  __SQL_CREATE_ROOM_DECO_TABLE = '''
                                 CREATE TABLE IF NOT EXISTS {} (
                                   now           timestamp(3) NOT NULL,
                                   platform      varchar(20)  NOT NULL,
                                   room_id       varchar(200) NOT NULL,
                                   deco_index    tinyint      DEFAULT NULL,
                                   deco          TBD          DEFAULT NULL,
                                   PRIMARY KEY (now, platform, room_id)
                                 )
                                 '''.format(__ROOM_DECO_TABLE_NAME)
  __SQL_DROP_ROOM_DECO_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_DECO_TABLE_NAME)


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
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__ROOM_DECO_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_DECO_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_DECO_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_DECO_TABLE_PRI_KEY

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_DECO_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_DECO_TABLE

'''
  TBD: no related data type of room_realtime_playback_quality
'''
class RoomRealtimePlaybackQualityTable(SocialMediaStreamDataTable):
  pass

##
## fans group admin user id
##
## +--------------------------------+-------------------+------+-----+---------+-------+-----------------------------------------+---------------------+
## | Field                          | Type              | Null | Key | Default | Extra | Topology                                | Comment             |
## +--------------------------------+-------------------+------+-----+---------+-------+-----------------------------------------+---------------------+
## | now                            | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"                           | 当前时间戳           | 
## | platform                       | varchar(20)       | NO   | PRI |         |       |           -                             | 平台                 |
## | room_id                        | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                        | 直播间ID             | 
## | fans_group_admin_user_id_index | unsigned tinyint  | NO   | PRI |         |       |           -                             | 粉丝群管理员ID序号   |
## | fans_group_admin_user_id       | varchar(200)      |      |     | NULL    |       | "$.data.room.fans_group_admin_user_ids" | 粉丝群管理员用户ID   |
## +--------------------------------+-------------------+------+-----+---------+-------+-----------------------------------------+---------------------+
##
class FansGroupAdminUserIdTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __FANS_GROUP_ADMIN_USER_ID_TABLE_NAME       = 'fans_group_admin_user_id'
  __FANS_GROUP_ADMIN_USER_ID_TABLE_HEADER     = ['now',                            'platform',                'room_id',
                                                 'fans_group_admin_user_id_index', 'fans_group_admin_user_id'
                                                 ]
  __FANS_GROUP_ADMIN_USER_ID_TABLE_PRI_KEY    = ['now', 'platform', 'room_id', 'fans_group_admin_user_id_index']
  __FANS_GROUP_ADMIN_USER_ID_TABLE_TUPLE      = {item:None for item in __FANS_GROUP_ADMIN_USER_ID_TABLE_HEADER}
  __SQL_CREATE_FANS_GROUP_ADMIN_USER_ID_TABLE = '''
                                                CREATE TABLE IF NOT EXISTS {} (
                                                  now                               timestamp(3) NOT NULL,
                                                  platform                          varchar(20)  NOT NULL,
                                                  room_id                           varchar(200) NOT NULL,
                                                  fans_group_admin_user_id_index    tinyint      NOT NULL,
                                                  fans_group_admin_user_id          varchar(200) DEFAULT NULL,
                                                  PRIMARY KEY (now, platform, room_id, fans_group_admin_user_id_index)
                                                )
                                                '''.format(__FANS_GROUP_ADMIN_USER_ID_TABLE_NAME)
  __SQL_DROP_FANS_GROUP_ADMIN_USER_ID_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__FANS_GROUP_ADMIN_USER_ID_TABLE_NAME)


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
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__FANS_GROUP_ADMIN_USER_ID_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__FANS_GROUP_ADMIN_USER_ID_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__FANS_GROUP_ADMIN_USER_ID_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__FANS_GROUP_ADMIN_USER_ID_TABLE_PRI_KEY

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_FANS_GROUP_ADMIN_USER_ID_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_FANS_GROUP_ADMIN_USER_ID_TABLE

##
## data.room.fans_group_admin_user_open_ids
##
## +-------------------------------------+-------------------+------+-----+---------+-------+----------------------------------------------+----------------------+
## | Field                               | Type              | Null | Key | Default | Extra | Topology                                     | Comment              |
## +-------------------------------------+-------------------+------+-----+---------+-------+----------------------------------------------+----------------------+
## | now                                 | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"                                | 当前时间戳            | 
## | platform                            | varchar(20)       | NO   | PRI |         |       |           -                                  | 平台                  |
## | room_id                             | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                             | 直播间ID              | 
## | fans_group_admin_user_open_id_index | unsigned tinyint  | NO   | PRI |         |       |           -                                  | 粉丝群管理员OpenID序号 |
## | fans_group_admin_user_open_id       | varchar(200)      |      |     | NULL    |       | "$.data.room.fans_group_admin_user_open_ids" | 粉丝群管理员OpenID列表 |
## +-------------------------------------+-------------------+------+-----+---------+-------+----------------------------------------------+-----------------------+
##
class FansGroupAdminUserOpenIdTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE_NAME       = 'fans_group_admin_user_open_id'
  __FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE_HEADER     = ['now',                                 'platform',                     'room_id',
                                                      'fans_group_admin_user_open_id_index', 'fans_group_admin_user_open_id'
                                                      ]
  __FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE_PRI_KEY    = ['now', 'platform', 'room_id', 'fans_group_admin_user_open_id_index']
  __FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE_TUPLE      = {item:None for item in __FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE_HEADER}
  __SQL_CREATE_FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE = '''
                                                     CREATE TABLE IF NOT EXISTS {} (
                                                       now                                    timestamp(3) NOT NULL,
                                                       platform                               varchar(20)  NOT NULL,
                                                       room_id                                varchar(200) NOT NULL,
                                                       fans_group_admin_user_open_id_index    tinyint      NOT NULL,
                                                       fans_group_admin_user_open_id          varchar(200) DEFAULT NULL,
                                                       PRIMARY KEY (now, platform, room_id, fans_group_admin_user_open_id_index)
                                                     )
                                                     '''.format(__FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE_NAME)
  __SQL_DROP_FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE_NAME)

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
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE_PRI_KEY

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE

'''
  TBD: no related data type of room_filter_word
'''
class RoomFilterWordTable(SocialMediaStreamDataTable):
  pass

'''
  TBD: no related data type of room_live_distribution
'''
class RoomLiveDistributionTable(SocialMediaStreamDataTable):
  pass

'''
  TBD: no related data type of commerce_webcast_config_id
'''
class CommerceWebcastConfigIdTable(SocialMediaStreamDataTable):
  pass

'''
  TBD: no related data type of media_badge_image
'''
class MediaBadgeImageTable(SocialMediaStreamDataTable):
  pass

'''
  TBD: no related data type of new_real_time_icon
'''
class NewRealTimeIconTable(SocialMediaStreamDataTable):
  pass

'''
  TBD: no related data type of room_owner_real_time_icon
'''
class RoomOwnerRealTimeIconTable(SocialMediaStreamDataTable):
  pass

##
## data.room.owner.subscribe
##
## +---------------+-------------------+------+-----+---------+-------+---------------------------------------------+---------------------+
## | Field         | Type              | Null | Key | Default | Extra | Topology                                    | Comment             |
## +---------------+-------------------+------+-----+---------+-------+---------------------------------------------+---------------------+
## | now           | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"                               | 当前时间戳           | 
## | platform      | varchar(20)       | NO   | PRI |         |       |           -                                 | 平台                 | 
## | room_id       | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                            | 直播间ID             | 
## | owner_user_id | varchar(200)      | NO   | PRI |         |       | "$.data.room.owner_user_id"                 | 直播间主播ID         |
## | buy_type      | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.subscribe.buy_type"      | 购买类型             |
## | identity_type | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.subscribe.identity_type" | 身份类型             |
## | is_member     | bool              |      |     | NULL    |       | "$.data.room.owner.subscribe.is_member"     | 是否为会员           |
## | level         | unsigned smallint |      |     | NULL    |       | "$.data.room.owner.subscribe.level"         | 订阅等级             |
## | open          | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.subscribe.open"          | 是否开放             |
## +---------------+-------------------+------+-----+---------+-------+---------------------------------------------+---------------------+
##
class RoomSubscribeTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_SUBSCRIBE_TABLE_TABLE_NAME       = 'room_subscribe'
  __ROOM_SUBSCRIBE_TABLE_TABLE_HEADER     = ['now', 'platform', 'room_id', 'owner_user_id', 'buy_type', 'identity_type', 'is_member', 'level', 'open']
  __ROOM_SUBSCRIBE_TABLE_TABLE_PRI_KEY    = ['now', 'platform', 'room_id']
  __ROOM_SUBSCRIBE_TABLE_TABLE_TUPLE      = {item:None for item in __ROOM_SUBSCRIBE_TABLE_TABLE_HEADER}
  __SQL_CREATE_ROOM_SUBSCRIBE_TABLE_TABLE = '''
                                            CREATE TABLE IF NOT EXISTS {} (
                                              now           timestamp(3)      NOT NULL,
                                              platform      varchar(20)       NOT NULL,
                                              room_id       varchar(200)      NOT NULL,
                                              owner_user_id varchar(200)      NOT NULL,
                                              buy_type      tinyint           DEFAULT NULL,
                                              identity_type tinyint           DEFAULT NULL,
                                              is_member     bool              DEFAULT NULL,
                                              level         smallint          DEFAULT NULL,
                                              open          tinyint           DEFAULT NULL,
                                              PRIMARY KEY (now, platform, room_id, owner_user_id)
                                            )
                                            '''.format(__ROOM_SUBSCRIBE_TABLE_TABLE_NAME)
  __SQL_DROP_ROOM_SUBSCRIBE_TABLE_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_SUBSCRIBE_TABLE_TABLE_NAME)


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
  ## get live record table name
  ##
  def get_name(self) -> str:
    return self.__ROOM_SUBSCRIBE_TABLE_TABLE_NAME
  
  ##
  ## get live record table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_SUBSCRIBE_TABLE_TABLE_HEADER

  ##
  ## get live record table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_SUBSCRIBE_TABLE_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_SUBSCRIBE_TABLE_TABLE_PRI_KEY

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_SUBSCRIBE_TABLE_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_SUBSCRIBE_TABLE_TABLE


'''
  TBD: no related data type of room_owner_top_fans
'''
class RoomOwnerTopFansTable(SocialMediaStreamDataTable):
  pass

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
class RoomPackMetaTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_PACK_META_TABLE_NAME       = "room_pack_meta"
  __ROOM_PACK_META_TABLE_HEADER     = ['now',       'platform', 'room_id',
                                       'cluster',   'dc',       'env',
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
class RoomPaidLiveDataTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
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
## data.room.room_auth
##
## +----------------------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------+
## | Field                            | Type              | Null | Key | Default | Extra | Topology                                                 | Comment              |
## +----------------------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------+
## | now                              | timestamp         | YES  | PRI |         |       | "$.extra.now"                                            | 当前时间戳            | 
## | platform                         | varchar(20)       |      | PRI | NULL    |       |           -                                              | 平台                  |
## | room_id                          | varchar(200)      |      |     |         |       | "$.data.room.id"                                         | 直播间ID              | 
## | AIClone                          | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.AIClone"                          | AI克隆                | 
## | AdminCommentWall                 | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.AdminCommentWall"                 | 管理员评论墙          | 
## | AnchorAudioChat                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.AnchorAudioChat"                  | 主播音频聊天          | 
## | AnchorColdMessageTiled           | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.AnchorColdMessageTiled"           | 主播冷消息平铺        | 
## | AnchorHotMessageAggregated       | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.AnchorHotMessageAggregated"       | 主播热消息聚合        | 
## | AnchorMission                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.AnchorMission"                    | 主播任务             | 
## | AudioChat                        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.AudioChat"                        | 音频聊天             | 
## | AudioChatTotext                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.AudioChatTotext"                  | 音频聊天转文本        | 
## | Banner                           | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Banner"                           | 横幅                 | 
## | BulletStyle                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.BulletStyle"                      | 弹幕样式              | 
## | CanSellTicket                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.CanSellTicket"                    | 是否可以售票          | 
## | CastScreen                       | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.CastScreen"                       | 屏幕投射             | 
## | CastScreenExplicit               | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.CastScreenExplicit"               | 屏幕投射显式          | 
## | Chat                             | bool              |      |     |         |       | "$.data.room.room_auth.Chat"                             | 聊天                 | 
## | ChatDispatch                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatDispatch"                     | 聊天分发             | 
## | ChatDynamicSlideSpeed            | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatDynamicSlideSpeed"            | 聊天动态滑动速度      | 
## | ChatDynamicSlideSpeedAnchor      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatDynamicSlideSpeedAnchor"      | 主播聊天动态滑动速度   | 
## | ChatGuideEmoji                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatGuideEmoji"                   | 聊天引导表情          |
## | ChatGuideImage                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatGuideImage"                   | 聊天引导图片          |
## | ChatIdentity                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatIdentity"                     | 聊天身份              |
## | ChatMention                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatMention"                      | 聊天提及             |
## | ChatMentionV2                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatMentionV2"                    | 聊天提及V2            |
## | ChatOperate                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatOperate"                      | 聊天操作             |
## | ChatReply                        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatReply"                        | 聊天回复              |
## | ClearEntranceOption              | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ClearEntranceOption"              | 清除入口选项          |
## | Collect                          | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Collect"                          | 收藏                 |
## | CommentWall                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.CommentWall"                      | 评论墙               |
## | CommerceCard                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.CommerceCard"                     | 商业卡片             |
## | CommerceComponent                | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.CommerceComponent"                | 商业组件             |
## | CommonCard                       | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.CommonCard"                       | 通用卡片             |
## | CountType                        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.CountType"                        | 计数类型             | 
## | Danmaku                          | bool              |      |     |         |       | "$.data.room.room_auth.Danmaku"                          | 弹幕                 | 
## | DanmakuDefault                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.DanmakuDefault"                   | 弹幕默认             | 
## | Denounce                         | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Denounce"                         | 举报                 | 
## | Digg                             | bool              |      |     |         |       | "$.data.room.room_auth.Digg"                             | 点赞                 | 
## | Dislike                          | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Dislike"                          | 不喜欢               | 
## | DonationSticker                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.DonationSticker"                  | 捐赠贴纸             | 
## | DouPlus                          | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.DouPlus"                          | DouPlus             | 
## | DouPlusPopularityGem             | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.DouPlusPopularityGem"             | DouPlus人气宝石      | 
## | DownloadVideo                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.DownloadVideo"                    | 下载视频             | 
## | EcomFansClub                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.EcomFansClub"                     | 电商粉丝俱乐部        | 
## | EmojiOutside                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.EmojiOutside"                     | 外部表情             | 
## | EnhancedTouch                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.EnhancedTouch"                    | 增强触摸             | 
## | EnterEffects                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.EnterEffects"                     | 进入效果             | 
## | ExpandScreen                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ExpandScreen"                     | 扩展屏幕             | 
## | FansClub                         | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FansClub"                         | 粉丝俱乐部           | 
## | FansClubBlessing                 | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FansClubBlessing"                 | 粉丝俱乐部祝福        | 
## | FansClubDeclaration              | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FansClubDeclaration"              | 粉丝俱乐部宣言        | 
## | FansClubLetter                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FansClubLetter"                   | 粉丝俱乐部信件        | 
## | FansClubNotice                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FansClubNotice"                   | 粉丝俱乐部通知        | 
## | FansGroup                        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FansGroup"                        | 粉丝群               | 
## | FeaturedPublicScreen             | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FeaturedPublicScreen"             | 精选公共屏幕          | 
## | FirstFeedHistChat                | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FirstFeedHistChat"                | 首次Feed历史聊天      | 
## | FixedChat                        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FixedChat"                        | 固定聊天             | 
## | FrequentlyChat                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FrequentlyChat"                   | 常用聊天             | 
## | FusionEmoji                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FusionEmoji"                      | 融合表情             | 
## | GamePointsPlaying                | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.GamePointsPlaying"                | 游戏积分玩法          | 
## | Gift                             | bool              |      |     |         |       | "$.data.room.room_auth.Gift"                             | 礼物                 | 
## | GiftAnchorMt                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.GiftAnchorMt"                     | 主播礼物MT           | 
## | GiftVote                         | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.GiftVote"                         | 礼物投票             | 
## | Highlights                       | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Highlights"                       | 精彩片段             | 
## | HostTeam                         | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.HostTeam"                         | 主播团队             | 
## | HostTeamChannel                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.HostTeamChannel"                  | 主播团队频道          | 
## | HotChatTray                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.HotChatTray"                      | 热聊天托盘            | 
## | HourRank                         | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.HourRank"                         | 小时排行榜            | 
## | ImHeatValue                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ImHeatValue"                      | IM热值               | 
## | IndustryService                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.IndustryService"                  | 行业服务             | 
## | InteractionGift                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.InteractionGift"                  | 互动礼物             | 
## | InteractiveComponent             | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.InteractiveComponent"             | 互动组件             | 
## | ItemShare                        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ItemShare"                        | 物品分享             | 
## | KtvOrderSong                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.KtvOrderSong"                     | KTV点歌              | 
## | Landscape                        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Landscape"                        | 横屏                 | 
## | LandscapeChat                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.LandscapeChat"                    | 横屏聊天             | 
## | LandscapeChatDynamicSlideSpeed   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.LandscapeChatDynamicSlideSpeed"   | 横屏聊天动态滑动速度   | 
## | LandscapeGift                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.LandscapeGift"                    | 横屏礼物             | 
## | LandscapeScreenCapture           | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.LandscapeScreenCapture"           | 横屏屏幕截图          | 
## | LandscapeScreenRecording         | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.LandscapeScreenRecording"         | 横屏屏幕录制          | 
## | LandscapeScreenShare             | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.LandscapeScreenShare"             | 横屏屏幕分享          | 
## | Like                             | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Like"                             | 点赞                 | 
## | LinkmicGuestLike                 | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.LinkmicGuestLike"                 | 连麦嘉宾点赞          | 
## | LongPressOption                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.LongPressOption"                  | 长按选项              | 
## | LongTouch                        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.LongTouch"                        | 长按触摸              | 
## | LuckMoney                        | bool              |      |     |         |       | "$.data.room.room_auth.LuckMoney"                        | 红包                 | 
## | MarkUser                         | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MarkUser"                         | 标记用户             | 
## | MediaHistoryMessage              | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MediaHistoryMessage"              | 媒体历史消息          | 
## | MediaLinkmic                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MediaLinkmic"                     | 媒体连麦             | 
## | MessageDispatch                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MessageDispatch"                  | 消息分发             | 
## | MessageGift                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MessageGift"                      | 消息礼物             | 
## | MissionCenter                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MissionCenter"                    | 任务中心             | 
## | MoreAnchor                       | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MoreAnchor"                       | 更多主播             | 
## | MoreHistChat                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MoreHistChat"                     | 更多历史聊天          | 
## | MultiplierPlayback               | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MultiplierPlayback"               | 倍速播放             | 
## | MyLiveEntrance                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MyLiveEntrance"                   | 我的直播入口          | 
## | OnlyTa                           | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.OnlyTa"                           | 仅限TA               | 
## | PCPlay                           | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.PCPlay"                           | PC播放               | 
## | POI                              | bool              |      |     |         |       | "$.data.room.room_auth.POI"                              | POI                  | 
## | PadPlay                          | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.PadPlay"                          | 平板播放             | 
## | PanelECService                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.PanelECService"                   | 面板EC服务           | 
## | PlayerRankList                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.PlayerRankList"                   | 播放器排行榜列表      | 
## | Poster                           | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Poster"                           | 海报                 | 
## | PosterCache                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.PosterCache"                      | 海报缓存             | 
## | PreviewChatExpose                | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.PreviewChatExpose"                | 预览聊天曝光          | 
## | PreviewHotCommentSwitch          | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.PreviewHotCommentSwitch"          | 预览热评论开关        | 
## | ProjectionBtn                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ProjectionBtn"                    | 投影按钮             | 
## | Props                            | bool              |      |     |         |       | "$.data.room.room_auth.Props"                            | 道具                 | 
## | PublicScreen                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.PublicScreen"                     | 公共屏幕             | 
## | QuizGamePointsPlaying            | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.QuizGamePointsPlaying"            | 测验游戏积分玩法      | 
## | RecordScreen                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.RecordScreen"                     | 录制屏幕             | 
## | RoomChannel                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.RoomChannel"                      | 直播间频道            | 
## | RoomChatLikeDisplay              | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.RoomChatLikeDisplay"              | 直播间聊天点赞显示    | 
## | RoomChatOperatePanel             | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.RoomChatOperatePanel"             | 直播间聊天操作面板    | 
## | RoomContributor                  | bool              |      |     |         |       | "$.data.room.room_auth.RoomContributor"                  | 直播间贡献者          | 
## | RoomWidget                       | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.RoomWidget"                       | 直播间小部件          | 
## | ScreenBottomInfo                 | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ScreenBottomInfo"                 | 屏幕底部信息          | 
## | ScreenProjectionBarrage          | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ScreenProjectionBarrage"          | 屏幕投影弹幕          | 
## | Seek                             | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Seek"                             | 寻找                 | 
## | Selection                        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Selection"                        | 选择                 | 
## | SelectionAlbum                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.SelectionAlbum"                   | 选择相册             | 
## | Share                            | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Share"                            | 分享                 | 
## | ShortTouch                       | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ShortTouch"                       | 短触摸               | 
## | ShortTouchTempState              | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ShortTouchTempState"              | 短触摸临时状态        | 
## | ShowGamePlugin                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ShowGamePlugin"                   | 显示游戏插件          | 
## | ShowQualification                | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ShowQualification"                | 显示资格             | 
## | SmallWindowDisplay               | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.SmallWindowDisplay"               | 小窗口显示            | 
## | SmallWindowPlayer                | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.SmallWindowPlayer"                | 小窗口播放器          | 
## | StickyMessage                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.StickyMessage"                    | 固定消息             | 
## | StreamAdaptation                 | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.StreamAdaptation"                 | 流适应               | 
## | StrokeUpDownGuide                | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.StrokeUpDownGuide"                | 上下滑动引导          | 
## | SubscribeCardPackage             | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.SubscribeCardPackage"             | 订阅卡包             | 
## | Teleprompter                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Teleprompter"                     | 提词器               | 
## | TextGift                         | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.TextGift"                         | 文本礼物             | 
## | TimedShutdown                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.TimedShutdown"                    | 定时关机             | 
## | ToolbarBubble                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ToolbarBubble"                    | 工具栏气泡            | 
## | Topic                            | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Topic"                            | 话题                 | 
## | TypingCommentState               | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.TypingCommentState"               | 输入评论状态          | 
## | UgcVSReplayDelete                | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.UgcVSReplayDelete"                | Ugc VS回放删除        | 
## | UgcVsReplayVisibility            | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.UgcVsReplayVisibility"            | Ugc VS回放可见性      | 
## | UpRightStatsFloatingLayer        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.UpRightStatsFloatingLayer"        | 右上角统计浮动层      | 
## | UseHostInfo                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.UseHostInfo"                      | 使用主机信息          | 
## | UserCard                         | bool              |      |     |         |       | "$.data.room.room_auth.UserCard"                         | 用户卡片              | 
## | UserCorner                       | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.UserCorner"                       | 用户角落              | 
## | VSGift                           | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VSGift"                           | VS礼物               | 
## | VSRank                           | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VSRank"                           | VS排行榜             | 
## | VSTopic                          | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VSTopic"                          | VS话题               | 
## | VerticalRank                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VerticalRank"                     | 垂直排行榜            | 
## | VerticalScreenShare              | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VerticalScreenShare"              | 垂直屏幕分享          | 
## | VideoAmplificationType           | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VideoAmplificationType"           | 视频放大类型          | 
## | VideoShare                       | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VideoShare"                       | 视频分享             | 
## | VsCommentBar                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VsCommentBar"                     | VS评论栏             | 
## | VsDouPlus                        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VsDouPlus"                        | VS DouPlus           | 
## | VsExtensionEnableFollow          | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VsExtensionEnableFollow"          | VS扩展启用关注        | 
## | VsFansClub                       | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VsFansClub"                       | VS粉丝俱乐部          | 
## | VsWelcomeDanmaku                 | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VsWelcomeDanmaku"                 | VS欢迎弹幕            | 
## | WordAssociation                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.WordAssociation"                  | 词关联                | 
## +----------------------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------+
##
class RoomAuthTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_AUTH_TABLE_NAME        = "room_auth"
  __ROOM_AUTH_TABLE_HEADER      = ['now',                           'platform',                       'room_id',                      'AIClone',                 'AdminCommentWall',
                                   'AnchorAudioChat',               'AnchorColdMessageTiled',         'AnchorHotMessageAggregated',   'AnchorMission',           'AudioChat',
                                   'AudioChatTotext',               'Banner',                         'BulletStyle',                  'CanSellTicket',           'CastScreen',
                                   'CastScreenExplicit',            'Chat',                           'ChatDispatch',                 'ChatDynamicSlideSpeed',   'ChatDynamicSlideSpeedAnchor',
                                   'ChatGuideEmoji',                'ChatGuideImage',                 'ChatIdentity',                 'ChatMention',             'ChatMentionV2',
                                   'ChatOperate',                   'ChatReply',                      'ClearEntranceOption',          'Collect',                 'CommentWall',
                                   'CommerceCard',                  'CommerceComponent',              'CommonCard',                   'CountType',               'Danmaku',
                                   'DanmakuDefault',                'Denounce',                       'Digg',                         'Dislike',                 'DonationSticker',
                                   'DouPlus',                       'DouPlusPopularityGem',           'DownloadVideo',                'EcomFansClub',            'EmojiOutside',
                                   'EnhancedTouch',                 'EnterEffects',                   'ExpandScreen',                 'FansClub',                'FansClubBlessing',
                                   'FansClubDeclaration',           'FansClubLetter',                 'FansClubNotice',               'FansGroup',               'FeaturedPublicScreen',
                                   'FirstFeedHistChat',             'FixedChat',                      'FrequentlyChat',               'FusionEmoji',             'GamePointsPlaying',
                                   'Gift',                          'GiftAnchorMt',                   'GiftVote',                     'Highlights',              'HostTeam',
                                   'HostTeamChannel',               'HotChatTray',                    'HourRank',                     'ImHeatValue',             'IndustryService',
                                   'InteractionGift',               'InteractiveComponent',           'ItemShare',                    'KtvOrderSong',            'Landscape',
                                   'LandscapeChat',                 'LandscapeChatDynamicSlideSpeed', 'LandscapeGift',                'LandscapeScreenCapture',  'LandscapeScreenRecording',
                                   'LandscapeScreenShare',          '`Like`',                         'LinkmicGuestLike',             'LongPressOption',         'LongTouch',
                                   'LuckMoney',                     'MarkUser',                       'MediaHistoryMessage',          'MediaLinkmic',            'MessageDispatch',
                                   'MessageGift',                   'MissionCenter',                  'MoreAnchor',                   'MoreHistChat',            'MultiplierPlayback',
                                   'MyLiveEntrance',                'OnlyTa',                         'PCPlay',                       'POI',                     'PadPlay',
                                   'PanelECService',                'PlayerRankList',                 'Poster',                       'PosterCache',             'PreviewChatExpose',
                                   'PreviewHotCommentSwitch',       'ProjectionBtn',                  'Props',                        'PublicScreen',            'QuizGamePointsPlaying',
                                   'RecordScreen',                  'RoomChannel',                    'RoomChatLikeDisplay',          'RoomChatOperatePanel',    'RoomContributor',
                                   'RoomWidget',                    'ScreenBottomInfo',               'ScreenProjectionBarrage',      'Seek',                    'Selection',
                                   'SelectionAlbum',                'Share',                          'ShortTouch',                   'ShortTouchTempState',     'ShowGamePlugin',
                                   'ShowQualification',             'SmallWindowDisplay',             'SmallWindowPlayer',            'StickyMessage',           'StreamAdaptation',
                                   'StrokeUpDownGuide',             'SubscribeCardPackage',           'Teleprompter',                 'TextGift',                'TimedShutdown',
                                   'ToolbarBubble',                 'Topic',                          'TypingCommentState',           'UgcVSReplayDelete',       'UgcVsReplayVisibility',
                                   'UpRightStatsFloatingLayer',     'UseHostInfo',                    'UserCard',                     'UserCorner',              'VSGift',
                                   'VSRank',                        'VSTopic',                        'VerticalRank',                 'VerticalScreenShare',     'VideoAmplificationType',
                                   'VideoShare',                    'VsCommentBar',                   'VsDouPlus',                    'VsExtensionEnableFollow', 'VsFansClub',
                                   'VsWelcomeDanmaku',              'WordAssociation'
                                   ]
  __ROOM_AUTH_TABLE_PRI_KEY    = ['now','platform','room_id']
  __ROOM_AUTH_TABLE_TUPLE      = {item:None for item in __ROOM_AUTH_TABLE_HEADER}
  __SQL_CREATE_ROOM_AUTH_TABLE = '''
                                 CREATE TABLE IF NOT EXISTS {} (
                                   now                             timestamp(3)     NOT NULL, 
                                   platform                        varchar(20)      NOT NULL,
                                   room_id                         varchar(200)     NOT NULL,
                                   AIClone                         tinyint          DEFAULT NULL,
                                   AdminCommentWall                tinyint          DEFAULT NULL,
                                   AnchorAudioChat                 tinyint          DEFAULT NULL,
                                   AnchorColdMessageTiled          tinyint          DEFAULT NULL,
                                   AnchorHotMessageAggregated      tinyint          DEFAULT NULL,
                                   AnchorMission                   tinyint          DEFAULT NULL,
                                   AudioChat                       tinyint          DEFAULT NULL,
                                   AudioChatTotext                 tinyint          DEFAULT NULL,
                                   Banner                          tinyint          DEFAULT NULL,
                                   BulletStyle                     tinyint          DEFAULT NULL,
                                   CanSellTicket                   tinyint          DEFAULT NULL,
                                   CastScreen                      tinyint          DEFAULT NULL,
                                   CastScreenExplicit              tinyint          DEFAULT NULL,
                                   Chat                            bool             DEFAULT NULL,
                                   ChatDispatch                    tinyint          DEFAULT NULL,
                                   ChatDynamicSlideSpeed           tinyint          DEFAULT NULL,
                                   ChatDynamicSlideSpeedAnchor     tinyint          DEFAULT NULL,
                                   ChatGuideEmoji                  tinyint          DEFAULT NULL,
                                   ChatGuideImage                  tinyint          DEFAULT NULL,
                                   ChatIdentity                    tinyint          DEFAULT NULL,
                                   ChatMention                     tinyint          DEFAULT NULL,
                                   ChatMentionV2                   tinyint          DEFAULT NULL,
                                   ChatOperate                     tinyint          DEFAULT NULL,
                                   ChatReply                       tinyint          DEFAULT NULL,
                                   ClearEntranceOption             tinyint          DEFAULT NULL,
                                   Collect                         tinyint          DEFAULT NULL,
                                   CommentWall                     tinyint          DEFAULT NULL,
                                   CommerceCard                    tinyint          DEFAULT NULL,
                                   CommerceComponent               tinyint          DEFAULT NULL,
                                   CommonCard                      tinyint          DEFAULT NULL,
                                   CountType                       tinyint          DEFAULT NULL,
                                   Danmaku                         bool             DEFAULT NULL,
                                   DanmakuDefault                  tinyint          DEFAULT NULL,
                                   Denounce                        tinyint          DEFAULT NULL,
                                   Digg                            bool             DEFAULT NULL,
                                   Dislike                         tinyint          DEFAULT NULL,
                                   DonationSticker                 tinyint          DEFAULT NULL,
                                   DouPlus                         tinyint          DEFAULT NULL,
                                   DouPlusPopularityGem            tinyint          DEFAULT NULL,
                                   DownloadVideo                   tinyint          DEFAULT NULL,
                                   EcomFansClub                    tinyint          DEFAULT NULL,
                                   EmojiOutside                    tinyint          DEFAULT NULL,
                                   EnhancedTouch                   tinyint          DEFAULT NULL,
                                   EnterEffects                    tinyint          DEFAULT NULL,
                                   ExpandScreen                    tinyint          DEFAULT NULL,
                                   FansClub                        tinyint          DEFAULT NULL,
                                   FansClubBlessing                tinyint          DEFAULT NULL,
                                   FansClubDeclaration             tinyint          DEFAULT NULL,
                                   FansClubLetter                  tinyint          DEFAULT NULL,
                                   FansClubNotice                  tinyint          DEFAULT NULL,
                                   FansGroup                       tinyint          DEFAULT NULL,
                                   FeaturedPublicScreen            tinyint          DEFAULT NULL,
                                   FirstFeedHistChat               tinyint          DEFAULT NULL,
                                   FixedChat                       tinyint          DEFAULT NULL,
                                   FrequentlyChat                  tinyint          DEFAULT NULL,
                                   FusionEmoji                     tinyint          DEFAULT NULL,
                                   GamePointsPlaying               tinyint          DEFAULT NULL,
                                   Gift                            bool             DEFAULT NULL,
                                   GiftAnchorMt                    tinyint          DEFAULT NULL,
                                   GiftVote                        tinyint          DEFAULT NULL,
                                   Highlights                      tinyint          DEFAULT NULL,
                                   HostTeam                        tinyint          DEFAULT NULL,
                                   HostTeamChannel                 tinyint          DEFAULT NULL,
                                   HotChatTray                     tinyint          DEFAULT NULL,
                                   HourRank                        tinyint          DEFAULT NULL,
                                   ImHeatValue                     tinyint          DEFAULT NULL,
                                   IndustryService                 tinyint          DEFAULT NULL,
                                   InteractionGift                 tinyint          DEFAULT NULL,
                                   InteractiveComponent            tinyint          DEFAULT NULL,
                                   ItemShare                       tinyint          DEFAULT NULL,
                                   KtvOrderSong                    tinyint          DEFAULT NULL,
                                   Landscape                       tinyint          DEFAULT NULL,
                                   LandscapeChat                   tinyint          DEFAULT NULL,
                                   LandscapeChatDynamicSlideSpeed  tinyint          DEFAULT NULL,
                                   LandscapeGift                   tinyint          DEFAULT NULL,
                                   LandscapeScreenCapture          tinyint          DEFAULT NULL,
                                   LandscapeScreenRecording        tinyint          DEFAULT NULL,
                                   LandscapeScreenShare            tinyint          DEFAULT NULL,
                                   `Like`                          tinyint          DEFAULT NULL,
                                   LinkmicGuestLike                tinyint          DEFAULT NULL,
                                   LongPressOption                 tinyint          DEFAULT NULL,
                                   LongTouch                       tinyint          DEFAULT NULL,
                                   LuckMoney                       bool             DEFAULT NULL,
                                   MarkUser                        tinyint          DEFAULT NULL,
                                   MediaHistoryMessage             tinyint          DEFAULT NULL,
                                   MediaLinkmic                    tinyint          DEFAULT NULL,
                                   MessageDispatch                 tinyint          DEFAULT NULL,
                                   MessageGift                     tinyint          DEFAULT NULL,
                                   MissionCenter                   tinyint          DEFAULT NULL,
                                   MoreAnchor                      tinyint          DEFAULT NULL,
                                   MoreHistChat                    tinyint          DEFAULT NULL,
                                   MultiplierPlayback              tinyint          DEFAULT NULL,
                                   MyLiveEntrance                  tinyint          DEFAULT NULL,
                                   OnlyTa                          tinyint          DEFAULT NULL,
                                   PCPlay                          tinyint          DEFAULT NULL,
                                   POI                             bool             DEFAULT NULL,
                                   PadPlay                         tinyint          DEFAULT NULL,
                                   PanelECService                  tinyint          DEFAULT NULL,
                                   PlayerRankList                  tinyint          DEFAULT NULL,
                                   Poster                          tinyint          DEFAULT NULL,
                                   PosterCache                     tinyint          DEFAULT NULL,
                                   PreviewChatExpose               tinyint          DEFAULT NULL,
                                   PreviewHotCommentSwitch         tinyint          DEFAULT NULL,
                                   ProjectionBtn                   tinyint          DEFAULT NULL,
                                   Props                           bool             DEFAULT NULL,
                                   PublicScreen                    tinyint          DEFAULT NULL,
                                   QuizGamePointsPlaying           tinyint          DEFAULT NULL,
                                   RecordScreen                    tinyint          DEFAULT NULL,
                                   RoomChannel                     tinyint          DEFAULT NULL,
                                   RoomChatLikeDisplay             tinyint          DEFAULT NULL,
                                   RoomChatOperatePanel            tinyint          DEFAULT NULL,
                                   RoomContributor                 bool             DEFAULT NULL,
                                   RoomWidget                      tinyint          DEFAULT NULL,
                                   ScreenBottomInfo                tinyint          DEFAULT NULL,
                                   ScreenProjectionBarrage         tinyint          DEFAULT NULL,
                                   Seek                            tinyint          DEFAULT NULL,
                                   Selection                       tinyint          DEFAULT NULL,
                                   SelectionAlbum                  tinyint          DEFAULT NULL,
                                   Share                           tinyint          DEFAULT NULL,
                                   ShortTouch                      tinyint          DEFAULT NULL,
                                   ShortTouchTempState             tinyint          DEFAULT NULL,
                                   ShowGamePlugin                  tinyint          DEFAULT NULL,
                                   ShowQualification               tinyint          DEFAULT NULL,
                                   SmallWindowDisplay              tinyint          DEFAULT NULL,
                                   SmallWindowPlayer               tinyint          DEFAULT NULL,
                                   StickyMessage                   tinyint          DEFAULT NULL,
                                   StreamAdaptation                tinyint          DEFAULT NULL,
                                   StrokeUpDownGuide               tinyint          DEFAULT NULL,
                                   SubscribeCardPackage            tinyint          DEFAULT NULL,
                                   Teleprompter                    tinyint          DEFAULT NULL,
                                   TextGift                        tinyint          DEFAULT NULL,
                                   TimedShutdown                   tinyint          DEFAULT NULL,
                                   ToolbarBubble                   tinyint          DEFAULT NULL,
                                   Topic                           tinyint          DEFAULT NULL,
                                   TypingCommentState              tinyint          DEFAULT NULL,
                                   UgcVSReplayDelete               tinyint          DEFAULT NULL,
                                   UgcVsReplayVisibility           tinyint          DEFAULT NULL,
                                   UpRightStatsFloatingLayer       tinyint          DEFAULT NULL,
                                   UseHostInfo                     tinyint          DEFAULT NULL,
                                   UserCard                        bool             DEFAULT NULL,
                                   UserCorner                      tinyint          DEFAULT NULL,
                                   VSGift                          tinyint          DEFAULT NULL,
                                   VSRank                          tinyint          DEFAULT NULL,
                                   VSTopic                         tinyint          DEFAULT NULL,
                                   VerticalRank                    tinyint          DEFAULT NULL,
                                   VerticalScreenShare             tinyint          DEFAULT NULL,
                                   VideoAmplificationType          tinyint          DEFAULT NULL,
                                   VideoShare                      tinyint          DEFAULT NULL,
                                   VsCommentBar                    tinyint          DEFAULT NULL,
                                   VsDouPlus                       tinyint          DEFAULT NULL,
                                   VsExtensionEnableFollow         tinyint          DEFAULT NULL,
                                   VsFansClub                      tinyint          DEFAULT NULL,
                                   VsWelcomeDanmaku                tinyint          DEFAULT NULL,
                                   WordAssociation                 tinyint          DEFAULT NULL,
                                   PRIMARY KEY (now, platform, room_id)
                                  )
                                  '''.format(__ROOM_AUTH_TABLE_NAME)
  __SQL_DROP_ROOM_AUTH_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_AUTH_TABLE_NAME)
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
    return self.__ROOM_AUTH_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_AUTH_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_AUTH_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_AUTH_TABLE_PRI_KEY

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_AUTH_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_AUTH_TABLE

'''
  TBD: no related data type of room_tab
'''
class RoomTabTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##

##
## data.room.room_tabs
## +-----------+-------------------+------+-----+---------+-------+-------------------------+----------------------+
## | Field     | Type              | Null | Key | Default | Extra | Topology                | Comment              |
## +-----------+-------------------+------+-----+---------+-------+-------------------------+----------------------+
## | now       | timestamp         | NO   | PRI |         |       | "$.extra.now"           | 当前时间戳            | 
## | platform  | varchar(20)       | NO   | PRI |         |       |           -             | 平台                  |
## | room_id   | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"        | 直播间ID              | 
## | tab_index | unsigned tinyint  |      |     | NULL    |       |           -             | tab序号               |
## | room_tab  | TBD               |      |     | NULL    |       | "$.data.room.room_tabs" | 直播间标签列表         |
## +-----------+-------------------+------+-----+---------+-------+-------------------------+----------------------+
##

  __ROOM_TAB_TABLE_NAME        = "room_tab"
  __ROOM_TAB_TABLE_HEADER      = ['now',                  'platform',              'room_id',
                                             'tab_index',            'room_tab'
                                             ]
  __ROOM_TAB_TABLE_PRI_KEY    = ['now','platform','room_id']
  __ROOM_TAB_TABLE_TUPLE      = {item:None for item in __ROOM_TAB_TABLE_HEADER}
  __SQL_CREATE_ROOM_TAB_TABLE = '''
                                           CREATE TABLE IF NOT EXISTS {} (
                                             now                  timestamp(3)     NOT NULL,
                                             platform             varchar(20)      NOT NULL,
                                             room_id              varchar(200)     NOT NULL,
                                             tab_index            tinyint          DEFAULT NULL,
                                             room_tab             TBD              DEFAULT NULL
                                             PRIMARY KEY (now, platform, room_id)
                                           )
                                           '''.format(__ROOM_TAB_TABLE_NAME)
  __SQL_DROP_ROOM_TAB_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_TAB_TABLE_NAME)
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
    return self.__ROOM_TAB_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_TAB_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_TAB_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_TAB_TABLE_PRI_KEY

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_TAB_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_TAB_TABLE

##
## data.room.short_touch_area_config
##
## +---------------------+--------------+------+-----+---------+-------+-----------------------------------------------------------+-----------------------+
## | Field               | Type         | Null | Key | Default | Extra | Topology                                                  | Comment               |
## +---------------------+--------------+------+-----+---------+-------+-----------------------------------------------------------+-----------------------+
## | now                 | timestamp(3) | NO   | PRI |         |       | "$.extra.now"                                             | 当前时间戳             |
## | platform            | varchar(20)  | NO   | PRI |         |       |           -                                               | 平台                  | 
## | room_id             | varchar(200) | NO   | PRI |         |       | "$.data.room.id"                                          | 直播间ID              | 
## | forbidden_types_map | json         |      |     | NULL    |       | "$.data.room.short_touch_area_config.forbidden_types_map" | 禁止类型映射表         |
## +---------------------+--------------+------+-----+---------+-------+-----------------------------------------------------------+-----------------------+
##
class RoomShortTouchAreaConfigTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_SHORT_TOUCH_AREA_CONFIG_TABLE_NAME       = "room_short_touch_area_config"
  __ROOM_SHORT_TOUCH_AREA_CONFIG_TABLE_HEADER     = ['now',       'platform', 'room_id', 'forbidden_types_map']
  __ROOM_SHORT_TOUCH_AREA_CONFIG_TABLE_PRI_KEY    = ['now','platform','room_id']
  __ROOM_SHORT_TOUCH_AREA_CONFIG_TABLE_TUPLE      = {item:None for item in __ROOM_SHORT_TOUCH_AREA_CONFIG_TABLE_HEADER}
  __SQL_CREATE_ROOM_SHORT_TOUCH_AREA_CONFIG_TABLE = '''
                                                    CREATE TABLE IF NOT EXISTS {} (
                                                      now                    timestamp(3) NOT NULL,
                                                      platform               varchar(20)  NOT NULL,
                                                      room_id                varchar(200) NOT NULL,
                                                      forbidden_types_map    json         DEFAULT NULL,
                                                      PRIMARY KEY (now, platform, room_id)
                                                    )
                                                    '''.format(__ROOM_SHORT_TOUCH_AREA_CONFIG_TABLE_NAME)
  __SQL_DROP_ROOM_SHORT_TOUCH_AREA_CONFIG_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_SHORT_TOUCH_AREA_CONFIG_TABLE_NAME)

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
    return self.__ROOM_SHORT_TOUCH_AREA_CONFIG_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_SHORT_TOUCH_AREA_CONFIG_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_SHORT_TOUCH_AREA_CONFIG_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_SHORT_TOUCH_AREA_CONFIG_TABLE_PRI_KEY

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_SHORT_TOUCH_AREA_CONFIG_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_SHORT_TOUCH_AREA_CONFIG_TABLE

##
## data.room.short_touch_area_config.elements
##
## +---------------+------------------+------+-----+---------+-------+-------------------------------------------------------------+-----------------------+
## | Field         | Type             | Null | Key | Default | Extra | Topology                                                    | Comment               |
## +---------------+------------------+------+-----+---------+-------+-------------------------------------------------------------+-----------------------+
## | now           | timestamp(3)     | NO   | PRI |         |       | "$.extra.now"                                               | 当前时间戳             |
## | platform      | varchar(20)      | NO   | PRI |         |       |           -                                                 | 平台                  | 
## | room_id       | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                                            | 直播间ID              | 
## | element_index | unsigned tinyint | NO   | PRI |         |       |           -                                                 | 短触摸区域配置元素     |
## | priority      | unsigned tinyint |      |     | NULL    |       | "$.data.room.short_touch_area_config.elements.'x'.priority" | 优先级                |
## | type          | unsigned tinyint |      |     | NULL    |       | "$.data.room.short_touch_area_config.elements.'x'.type"     | 类型                  |
## +---------------+------------------+------+-----+---------+-------+-------------------------------------------------------------+-----------------------+
##
class RoomShortTouchAreaConfigElementTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_SHORT_TOUCH_AREA_CONFIG_ELEMENT_TABLE_NAME       = "room_short_touch_area_config_element"
  __ROOM_SHORT_TOUCH_AREA_CONFIG_ELEMENT_TABLE_HEADER     = ['now', 'platform', 'room_id', 'element_index', 'priority', 'type']
  __ROOM_SHORT_TOUCH_AREA_CONFIG_ELEMENT_TABLE_PRI_KEY    = ['now', 'platform', 'room_id', 'element_index']
  __ROOM_SHORT_TOUCH_AREA_CONFIG_ELEMENT_TABLE_TUPLE      = {item:None for item in __ROOM_SHORT_TOUCH_AREA_CONFIG_ELEMENT_TABLE_HEADER}
  __SQL_CREATE_ROOM_SHORT_TOUCH_AREA_CONFIG_ELEMENT_TABLE = '''
                                                            CREATE TABLE IF NOT EXISTS {} (
                                                              now                    timestamp(3) NOT NULL,
                                                              platform               varchar(20)  NOT NULL,
                                                              room_id                varchar(200) NOT NULL,
                                                              element_index          tinyint      NOT NULL,
                                                              priority               tinyint      DEFAULT NULL,
                                                              type                   tinyint      DEFAULT NULL,
                                                              PRIMARY KEY (now, platform, room_id, element_index)
                                                            )
                                                            '''.format(__ROOM_SHORT_TOUCH_AREA_CONFIG_ELEMENT_TABLE_NAME)
  __SQL_DROP_ROOM_SHORT_TOUCH_AREA_CONFIG_ELEMENT_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_SHORT_TOUCH_AREA_CONFIG_ELEMENT_TABLE_NAME)

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
    return self.__ROOM_SHORT_TOUCH_AREA_CONFIG_ELEMENT_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_SHORT_TOUCH_AREA_CONFIG_ELEMENT_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_SHORT_TOUCH_AREA_CONFIG_ELEMENT_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_SHORT_TOUCH_AREA_CONFIG_ELEMENT_TABLE_PRI_KEY

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_SHORT_TOUCH_AREA_CONFIG_ELEMENT_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_SHORT_TOUCH_AREA_CONFIG_ELEMENT_TABLE

##
## data.room.short_touch_area_config.strategy_feat_whitelist
##
## +-----------------+------------------+------+-----+---------+-------+------------------+-----------------------+
## | Field           | Type             | Null | Key | Default | Extra | Topology         | Comment               |
## +-----------------+------------------+------+-----+---------+-------+------------------+-----------------------+
## | now             | timestamp(3)     | NO   | PRI |         |       | "$.extra.now"    | 当前时间戳             |
## | platform        | varchar(20)      | NO   | PRI |         |       |           -      | 平台                  | 
## | room_id         | varchar(200)     | NO   | PRI |         |       | "$.data.room.id" | 直播间ID              | 
## | whitelist_index | unsigned tinyint | NO   | PRI |         |       |           -      | 白名单索引             | 
## | whitelist_tag   | tinytext         |      |     | NULL    |       |           -      | 白名单标签             | 
## +-----------------+------------------+------+-----+---------+-------+------------------+-----------------------+
##
class RoomShortTouchAreaConfigStrategyFeatWhitelistTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_SHORT_TOUCH_AREA_CONFIG_STRATEGY_FEAT_WHITELIST_TABLE_NAME       = "room_short_touch_area_config_strategy_feat_whitelist"
  __ROOM_SHORT_TOUCH_AREA_CONFIG_STRATEGY_FEAT_WHITELIST_TABLE_HEADER     = ['now', 'platform', 'room_id', 'whitelist_index', 'whitelist_tag']
  __ROOM_SHORT_TOUCH_AREA_CONFIG_STRATEGY_FEAT_WHITELIST_TABLE_PRI_KEY    = ['now', 'platform', 'room_id', 'whitelist_index']
  __ROOM_SHORT_TOUCH_AREA_CONFIG_STRATEGY_FEAT_WHITELIST_TABLE_TUPLE      = {item:None for item in __ROOM_SHORT_TOUCH_AREA_CONFIG_STRATEGY_FEAT_WHITELIST_TABLE_HEADER}
  __SQL_CREATE_ROOM_SHORT_TOUCH_AREA_CONFIG_STRATEGY_FEAT_WHITELIST_TABLE = '''
                                                                            CREATE TABLE IF NOT EXISTS {} (
                                                                              now                    timestamp(3) NOT NULL,
                                                                              platform               varchar(20)  NOT NULL,
                                                                              room_id                varchar(200) NOT NULL,
                                                                              whitelist_index        tinyint      NOT NULL,
                                                                              whitelist_tag          tinytext     DEFAULT NULL,
                                                                              PRIMARY KEY (now, platform, room_id, whitelist_index)
                                                                            )
                                                                            '''.format(__ROOM_SHORT_TOUCH_AREA_CONFIG_STRATEGY_FEAT_WHITELIST_TABLE_NAME)
  __SQL_DROP_ROOM_SHORT_TOUCH_AREA_CONFIG_STRATEGY_FEAT_WHITELIST_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_SHORT_TOUCH_AREA_CONFIG_STRATEGY_FEAT_WHITELIST_TABLE_NAME)

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
    return self.__ROOM_SHORT_TOUCH_AREA_CONFIG_STRATEGY_FEAT_WHITELIST_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_SHORT_TOUCH_AREA_CONFIG_STRATEGY_FEAT_WHITELIST_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_SHORT_TOUCH_AREA_CONFIG_STRATEGY_FEAT_WHITELIST_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_SHORT_TOUCH_AREA_CONFIG_STRATEGY_FEAT_WHITELIST_TABLE_PRI_KEY

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_SHORT_TOUCH_AREA_CONFIG_STRATEGY_FEAT_WHITELIST_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_SHORT_TOUCH_AREA_CONFIG_STRATEGY_FEAT_WHITELIST_TABLE


class RoomTempStateConditionMapTable(SocialMediaStreamDataTable):
  pass

class RoomTempStateGlobalConditionIgnoreStrategyTypeTable(SocialMediaStreamDataTable):
  pass

class RoomTempStateGlobalConditionTable(SocialMediaStreamDataTable):
  pass

class RoomRecordTable(SocialMediaStreamDataTable):
  pass

class LiveStreamTable(SocialMediaStreamDataTable):
  pass

class StreamCandidateResolutionTable(SocialMediaStreamDataTable):
  pass

class StreamCompletePushUrlTable(SocialMediaStreamDataTable):
  pass

class LiveCoreSdkDataTable(SocialMediaStreamDataTable):
  pass

class LiveCoreSdkPullDataTable(SocialMediaStreamDataTable):
  pass

class LiveCoreSdkPullFlvDataTable(SocialMediaStreamDataTable):
  pass

class LiveCoreSdkPullHlsDataTable(SocialMediaStreamDataTable):
  pass

class LiveCoreSdkPullDataOptionTable(SocialMediaStreamDataTable):
  pass

class LiveCoreSdkPullQualityDataTable(SocialMediaStreamDataTable):
  pass

class LiveCoreSdkPullDefaultQualityDataTable(SocialMediaStreamDataTable):
  pass

class StreamPushUrlTable(SocialMediaStreamDataTable):
  pass

class RoomTagTable(SocialMediaStreamDataTable):
  pass

class RoomTopFansTable(SocialMediaStreamDataTable):
  pass

class RoomUpperRightWidgetDataTable(SocialMediaStreamDataTable):
  pass

class RoomVsRoleTable(SocialMediaStreamDataTable):
  pass

class PictureTable(SocialMediaStreamDataTable):
  pass

class PictureFlexSettingTable(SocialMediaStreamDataTable):
  pass

class PictureTextSettingTable(SocialMediaStreamDataTable):
  pass

class PictureUrlTable(SocialMediaStreamDataTable):
  pass

class PictureContentTable(SocialMediaStreamDataTable):
  pass

class UserTable(SocialMediaStreamDataTable):
  pass