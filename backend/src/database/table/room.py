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
## | AnchorABMap                      | json              | YES  |     | NULL    |       | "$.data.room.AnchorABMap"                             | 主播AB映射                       | 
## | acquaintance_status              | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.acquaintance_status"                     | 直播间熟人状态                    |
## | anchor_scheduled_time_text       | text              | YES  |     | NULL    |       | "$.data.room.anchor_scheduled_time_text"              | 直播间布局                       |
## | anchor_share_text                | text              | YES  |     | NULL    |       | "$.data.room.anchor_share_text"                       | 主播分享文本                     |
## | anchor_tab_type                  | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.anchor_tab_type"                         | 主播标签类型                     |
## | app_id                           | varchar(200)      | YES  |     | NULL    |       | "$.data.room.app_id"                                  | 应用ID                          |
## | auth_city                        | varchar(100)      | YES  |     | NULL    |       | "$.data.room.auth_city"                               | 直播间认证城市                   |
## | auto_cover                       | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.auto_cover"                              | 自动封面                         |
## | base_category                    | unsigned int      | YES  |     | NULL    |       | "$.data.room.base_category"                           | 基础分类                         |
## | book_end_time                    | timestamp         | YES  |     | NULL    |       | "$.data.room.book_end_time"                           | 直播间预约结束时间                |
## | book_time                        | timestamp         | YES  |     | NULL    |       | "$.data.room.book_time"                               | 直播间预约开始时间                |
## | business_live                    | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.business_live"                           | 商业直播                         |
## | category                         | unsigned int      | YES  |     | NULL    |       | "$.data.room.category"                                | 分类                            |
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
## | finish_reason                    | unsigned int      | YES  |     | NULL    |       | "$.data.room.finish_reason"                           | 直播结束原因                     |
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
  __TABLE_AUTO_INCREMENT         = []
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
                                        base_category                    int            DEFAULT NULL,
                                        book_end_time                    timestamp      DEFAULT NULL,
                                        book_time                        timestamp      DEFAULT NULL,
                                        business_live                    tinyint        DEFAULT NULL,
                                        category                         int            DEFAULT NULL,
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
                                        realtime_playback_start_shift    tinyint        DEFAULT NULL,
                                        realtime_replay_enabled          bool           DEFAULT NULL,
                                        vr_type                          tinyint        DEFAULT NULL,
                                        vs_type                          tinyint        DEFAULT NULL,
                                        xigua_uid                        varchar(200)   DEFAULT NULL,
                                        fansclub_msg_style               tinyint        DEFAULT NULL,
                                        fcdn_appid                       varchar(200)   DEFAULT NULL,
                                        finish_reason                    int            DEFAULT NULL,
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
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

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
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## room admin user id
##
##+---------------------+-------------------+------+-----+---------+-------+------------------------------+---------------------+
##| Field               | Type              | Null | Key | Default | Extra | Topology                     | Comment             |
##+---------------------+-------------------+------+-----+---------+-------+------------------------------+---------------------+
##| start_time          | timestamp         | NO   | PRI |         |       | "$.data.room.start_time"     | 当前时间戳           |
##| platform            | varchar(20)       | NO   | PRI |         |       |           -                  | 平台                 |
##| room_id             | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"             | 直播间ID             |
##| admin_user_id_index | unsigned bigint   | NO   | PRI |         |       |           -                  | 直播间管理员ID序号    |
##| admin_user_id       | varchar(200)      |      |     | NULL    |       | "$.data.room.admin_user_ids" | 直播间管理员用户ID    | 
##+---------------------+-------------------+------+-----+---------+-------+------------------------------+---------------------+
##
class RoomAdminUserIdTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_ADMIN_USER_ID_TABLE_NAME       = 'room_admin_user_id'
  __ROOM_ADMIN_USER_ID_TABLE_HEADER     = ['start_time',                 'platform',     'room_id',
                                           'admin_user_id_index', 'admin_user_id'
                                           ]
  __ROOM_ADMIN_USER_ID_TABLE_PRI_KEY    = ['start_time', 'platform', 'room_id', 'admin_user_id_index']
  __TABLE_AUTO_INCREMENT                = []
  __ROOM_ADMIN_USER_ID_TABLE_TUPLE      = {item:None for item in __ROOM_ADMIN_USER_ID_TABLE_HEADER}
  __SQL_CREATE_ROOM_ADMIN_USER_ID_TABLE = '''
                                          CREATE TABLE IF NOT EXISTS {} (
                                            start_time             timestamp    NOT NULL,
                                            platform               varchar(20)  NOT NULL,
                                            room_id                varchar(200) NOT NULL,
                                            admin_user_id_index    bigint       NOT NULL,
                                            admin_user_id          varchar(200) DEFAULT NULL,
                                            PRIMARY KEY (start_time, platform, room_id, admin_user_id_index)
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
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

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
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## room admin user open id table
##
## +--------------------------+-------------------+------+-----+---------+-------+-----------------------------------+---------------------+
## | Field                    | Type              | Null | Key | Default | Extra | Topology                          | Comment             |
## +--------------------------+-------------------+------+-----+---------+-------+-----------------------------------+---------------------+
## | now                      | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"                     | 当前时间戳           | 
## | platform                 | varchar(20)       | NO   | PRI |         |       |           -                       | 平台                 | 
## | room_id                  | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                  | 直播间ID             |
## | admin_user_open_id_index | unsigned bigint   | NO   | PRI |         |       |           -                       | 直播间管理员用户ID序号|
## | admin_user_open_id       | varchar(200)      |      |     | NULL    |       | "$.data.room.admin_user_open_ids" | 直播间管理员用户ID    | 
## +--------------------------+-------------------+------+-----+---------+-------+-----------------------------------+---------------------+
##
class RoomAdminUserOpenIdTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_ADMIN_USER_OPEN_ID_TABLE_NAME       = 'room_admin_user_open_id'
  __ROOM_ADMIN_USER_OPEN_ID_TABLE_HEADER     = ['now',                      'platform',          'room_id',
                                                'admin_user_open_id_index', 'admin_user_open_id'
                                                ]
  __ROOM_ADMIN_USER_OPEN_ID_TABLE_PRI_KEY    = ['admin_user_open_id_index']
  __TABLE_AUTO_INCREMENT                     = ['admin_user_open_id_index']
  __ROOM_ADMIN_USER_OPEN_ID_TABLE_TUPLE      = {item:None for item in __ROOM_ADMIN_USER_OPEN_ID_TABLE_HEADER}
  __SQL_CREATE_ROOM_ADMIN_USER_OPEN_ID_TABLE = '''
                                               CREATE TABLE IF NOT EXISTS {} (
                                                 now                         timestamp(3) NOT NULL,
                                                 platform                    varchar(20)  NOT NULL,
                                                 room_id                     varchar(200) NOT NULL,
                                                 admin_user_open_id_index    bigint       NOT NULL AUTO_INCREMENT,
                                                 admin_user_open_id          varchar(200) DEFAULT NULL,
                                                 PRIMARY KEY (admin_user_open_id_index),
                                                 UNIQUE KEY unique_record (now, platform, room_id, admin_user_open_id)
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
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

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
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

'''
  TBD: no related data type of room_assist_label
'''
##
## data.room.assist_label_list
##
## +--------------------+-------------------+------+-----+---------+-------+---------------------------------+---------------------+
## | Field              | Type              | Null | Key | Default | Extra | Topology                        | Comment             |
## +--------------------+-------------------+------+-----+---------+-------+---------------------------------+---------------------+
## | now                | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"                   | 当前时间戳           | 
## | platform           | varchar(20)       | NO   | PRI |         |       |           -                     | 平台                 | 
## | room_id            | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                | 直播间ID             | 
## | assist_label_index | unsigned bigint   |      |     | NULL    |       |           -                     | 直播间辅助标签序号   |
## | assist_label       | TBD               |      |     | NULL    |       | "$.data.room.assist_label_list" | 直播间辅助标签       | 
## +--------------------+-------------------+------+-----+---------+-------+---------------------------------+---------------------+
##
class RoomAssistLabelTable(SocialMediaStreamDataTable):
  pass
  """
##
## >>=============================== attribute ===============================>>
##
  __ROOM_ASSIST_LABEL_TABLE_NAME       = 'room_assist_label'
  __ROOM_ASSIST_LABEL_TABLE_HEADER     = ['now',                'platform',    'room_id',
                                          'assist_label_index', 'assist_label'
                                          ]
  __ROOM_ASSIST_LABEL_TABLE_PRI_KEY    = ['now', 'platform', 'room_id']
  __TABLE_AUTO_INCREMENT               = ['assist_label_index']
  __ROOM_ASSIST_LABEL_TABLE_TUPLE      = {item:None for item in __ROOM_ASSIST_LABEL_TABLE_HEADER}
  __SQL_CREATE_ROOM_ASSIST_LABEL_TABLE = '''
                                          CREATE TABLE IF NOT EXISTS {} (
                                            now                   timestamp(3) NOT NULL,
                                            platform              varchar(20)  NOT NULL,
                                            room_id               varchar(200) NOT NULL,
                                            assist_label_index    bigint       DEFAULT NULL AUTO_INCREMENT,
                                            assist_label          TBD          DEFAULT NULL,
                                            PRIMARY KEY (assist_label_index),
                                            UNIQUE KEY unique_record (now, platform, room_id, assist_label_index)
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
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

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
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()
  """
'''
  TBD: no related data type of room_deco
'''
##
## $.data.room.deco_list
##
## +------------+-------------------+------+-----+---------+-------+-------------------------+---------------------+
## | Field      | Type              | Null | Key | Default | Extra | Topology                | Comment             |
## +------------+-------------------+------+-----+---------+-------+-------------------------+---------------------+
## | now        | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"           | 当前时间戳           | 
## | platform   | varchar(20)       | NO   | PRI |         |       |           -             | 平台                 | 
## | room_id    | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"        | 直播间ID             |
## | deco_index | unsigned bigint   |      |     | NULL    |       |           -             | 装饰索引号            |  
## | deco       | TBD               |      |     | NULL    |       | "$.data.room.deco_list" | 装饰                 | 
## +------------+-------------------+------+-----+---------+-------+-------------------------+----------------------+
##
"""
deco_list:
- audit_text_color: ''
  content: "\u793C\u82B1\u7B52\uFF0C\u70B9\u6B4C"
  h: 1920
  id: 1184
  image:
    avg_color: '#E6FADC'
    flex_setting_list: []
    height: 0
    image_type: 0
    is_animated: false
    open_web_url: ''
    text_setting_list: []
    uri: webcast/decoration_8e605288f9089f4ede4a93336586b22c.png
    url_list:
    - https://p3-webcast.douyinpic.com/img/webcast/decoration_8e605288f9089f4ede4a93336586b22c.png~tplv-resize:0:0.image
    - https://p11-webcast.douyinpic.com/img/webcast/decoration_8e605288f9089f4ede4a93336586b22c.png~tplv-resize:0:0.image
    width: 0
  input_rect:
  - 63
  - 43
  - 195
  - 34
  kind: 0
  max_length: 8
  nine_patch_image:
    avg_color: '#CCB1A3'
    flex_setting_list: []
    height: 0
    image_type: 0
    is_animated: false
    open_web_url: ''
    text_setting_list: []
    uri: webcast/decoration_6825f92fe146f5938028eb2f3f192a99.png
    url_list:
    - https://p3-webcast.douyinpic.com/img/webcast/decoration_6825f92fe146f5938028eb2f3f192a99.png~tplv-obj.image
    - https://p11-webcast.douyinpic.com/img/webcast/decoration_6825f92fe146f5938028eb2f3f192a99.png~tplv-obj.image
    width: 0
  reservation:
    anchor_id: 0
    anchor_open_id: ''
    appointment_id: 0
    btn_color: ''
    btn_rect: []
    end_time: 0
    is_reserved: false
    room_id: 0
    start_time: 0
  status: 1
  sub_type: 0
  text_color: '#000000'
  text_image_adjustable_end_position: 212
  text_image_adjustable_start_position: 132
  text_size: 24
  text_special_effects: []
  type: 1
  w: 1080
  x: 849
  y: 453
"""
##
## $.data.room.deco_list
##
## +--------------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------+---------------------+
## | Field                                | Type              | Null | Key | Default | Extra | Topology                                                           | Comment             |
## +--------------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------+---------------------+
## | start_time                           | timestamp         | YES  |     |         |       | "$.extra.now"                                                      | 当前时间戳           | 
## | platform                             | varchar(20)       |      |     | NULL    |       |           -                                                        | 平台                 | 
## | room_id                              | varchar(200)      |      |     |         |       | "$.data.room.id"                                                   | 直播间ID             |
## | deco_index                           | unsigned bigint   |      |     |         |       |           -                                                        | 装饰索引号            |  
## | audit_text_color                     | varchar(7)        |      |     |         |       | "$.data.room.deco_list.[x].audit_text_color"                       | 审核文本颜色          | 
## | content                              | tinytext          |      |     |         |       | "$.data.room.deco_list.[x].content"                                | 内容                 | 
## | h                                    | unsigned int      |      |     |         |       | "$.data.room.deco_list.[x].h"                                      | 高度                 | 
## | id                                   | unsigned int      |      |     |         |       | "$.data.room.deco_list.[x].id"                                     | ID                   | 
## | kind                                 | unsigned tinyint  |      |     |         |       | "$.data.room.deco_list.[x].kind"                                   | 种类                 | 
## | max_length                           | unsigned tinyint  |      |     |         |       | "$.data.room.deco_list.[x].max_length"                             | 最大长度             | 
## | status                               | unsigned tinyint  |      |     |         |       | "$.data.room.deco_list.[x].status"                                 | 状态                 |
## | sub_type                             | unsigned tinyint  |      |     |         |       | "$.data.room.deco_list.[x].sub_type"                               | 子类型               |
## | text_color                           | varchar(7)        |      |     |         |       | "$.data.room.deco_list.[x].text_color"                             | 文本颜色             |
## | text_image_adjustable_end_position   | unsigned int      |      |     |         |       | "$.data.room.deco_list.[x].text_image_adjustable_end_position"     | 可调整文本图片结束位置 |
## | text_image_adjustable_start_position | unsigned int      |      |     |         |       | "$.data.room.deco_list.[x].text_image_adjustable_start_position"   | 可调整文本图片开始位置 |
## | text_size                            | unsigned int      |      |     |         |       | "$.data.room.deco_list.[x].text_size"                              | 文本大小              |
## | type                                 | unsigned tinyint  |      |     |         |       | "$.data.room.deco_list.[x].type"                                   | 类型                 |
## | w                                    | unsigned int      |      |     |         |       | "$.data.room.deco_list.[x].w"                                      |                      |
## | x                                    | unsigned int      |      |     |         |       | "$.data.room.deco_list.[x].x"                                      |                      |
## | y                                    | unsigned int      |      |     |         |       | "$.data.room.deco_list.[x].y"                                      |                      |
## +--------------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------+----------------------+
##
class RoomDecoTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_DECO_TABLE_NAME       = 'room_deco'
  __ROOM_DECO_TABLE_HEADER     = ['start_time',       'platform',                           'room_id',                              'deco_index', 
                                  'audit_text_color', 'content',                            'h',                                    'id',
                                  'kind',             'max_length',                         'status',                               'sub_type',
                                  'text_color',       'text_image_adjustable_end_position', 'text_image_adjustable_start_position', 'text_size',
                                  'type',             'w',                                  'x',                                    'y'
                                  ]
  __ROOM_DECO_TABLE_PRI_KEY    = ['start_time', 'platform', 'room_id', 'deco_index']
  __TABLE_AUTO_INCREMENT       = []
  __ROOM_DECO_TABLE_TUPLE      = {item:None for item in __ROOM_DECO_TABLE_HEADER}
  __SQL_CREATE_ROOM_DECO_TABLE = '''
                                 CREATE TABLE IF NOT EXISTS {} (
                                   start_time                           timestamp         NOT NULL,
                                   platform                             varchar(20)       NOT NULL,
                                   room_id                              varchar(200)      NOT NULL,
                                   deco_index                           bigint            NOT NULL,
                                   audit_text_color                     varchar(7)        DEFAULT NULL,
                                   content                              tinytext          DEFAULT NULL,
                                   h                                    int               DEFAULT NULL,
                                   id                                   int               DEFAULT NULL,
                                   kind                                 tinyint           DEFAULT NULL,
                                   max_length                           tinyint           DEFAULT NULL,
                                   status                               tinyint           DEFAULT NULL,
                                   sub_type                             tinyint           DEFAULT NULL,
                                   text_color                           varchar(7)        DEFAULT NULL, 
                                   text_image_adjustable_end_position   int               DEFAULT NULL,
                                   text_image_adjustable_start_position int               DEFAULT NULL,
                                   text_size                            int               DEFAULT NULL,
                                   type                                 tinyint           DEFAULT NULL,
                                   w                                    int               DEFAULT NULL,
                                   x                                    int               DEFAULT NULL,
                                   y                                    int               DEFAULT NULL,
                                   PRIMARY KEY (start_time, platform, room_id, deco_index)
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
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

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
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## $.data.room.deco_list.[x].input_rect
##
## +------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------+---------------------+
## | Field            | Type              | Null | Key | Default | Extra | Topology                                                           | Comment             |
## +------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------+---------------------+
## | start_time       | timestamp         |  NO  |     |         |       | "$.extra.now"                                                      | 当前时间戳           | 
## | platform         | varchar(20)       |  NO  |     |         |       |           -                                                        | 平台                 | 
## | room_id          | varchar(200)      |  NO  |     |         |       | "$.data.room.id"                                                   | 直播间ID             |
## | deco_index       | unsigned bigint   |      |     |         |       |           -                                                        | 装饰索引号            |  
## | input_rect_index | unsigned bigint   |  NO  | PRI |         |       | -                                                                  | 索引                 |
## | input_rect       | unsigned int      |      |     | NULL    |       | "$.data.room.deco_list.[x].reservation.input_rect"                 |                      |
## +------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------+----------------------+
##
class RoomDecoInputRectTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_DECO_INPUT_RECT_TABLE_NAME       = 'room_deco_input_rect'
  __ROOM_DECO_INPUT_RECT_TABLE_HEADER     = ['start_time',       'platform',                           'room_id',                              'deco_index', 
                                             'input_rect_index', 'input_rect'
                                             ]
  __ROOM_DECO_INPUT_RECT_TABLE_PRI_KEY    = ['start_time', 'platform', 'room_id', 'deco_index', 'input_rect_index']
  __TABLE_AUTO_INCREMENT                  = []
  __ROOM_DECO_INPUT_RECT_TABLE_TUPLE      = {item:None for item in __ROOM_DECO_INPUT_RECT_TABLE_HEADER}
  __SQL_CREATE_ROOM_DECO_INPUT_RECT_TABLE = '''
                                            CREATE TABLE IF NOT EXISTS {} (
                                              start_time       timestamp         NOT NULL,
                                              platform         varchar(20)       NOT NULL,
                                              room_id          varchar(200)      NOT NULL,
                                              deco_index       bigint            NOT NULL,
                                              input_rect_index bigint            NOT NULL,
                                              input_rect       int               DEFAULT NULL,
                                              PRIMARY KEY (start_time, platform, room_id, deco_index, input_rect_index)
                                            )
                                            '''.format(__ROOM_DECO_INPUT_RECT_TABLE_NAME)
  __SQL_DROP_ROOM_DECO_INPUT_RECT_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_DECO_INPUT_RECT_TABLE_NAME)


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
    return self.__ROOM_DECO_INPUT_RECT_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_DECO_INPUT_RECT_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_DECO_INPUT_RECT_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_DECO_INPUT_RECT_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_DECO_INPUT_RECT_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_DECO_INPUT_RECT_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## $.data.room.deco_list.[x].reservation
##
## +------------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+---------------+
## | Field                  | Type              | Null | Key | Default | Extra | Topology                                                 | Comment       |
## +------------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+---------------+
## | start_time             | timestamp         |  NO  |     |         |       | "$.extra.now"                                            | 当前时间戳     | 
## | platform               | varchar(20)       |  NO  |     | NULL    |       |           -                                              | 平台           | 
## | room_id                | varchar(200)      |  NO  |     |         |       | "$.data.room.id"                                         | 直播间ID       |
## | deco_index             | unsigned bigint   |      |     |         |       |           -                                              | 装饰索引号      |
## | anchor_id              | varchar(200)      |      |     |         |       | "$.data.room.deco_list.[x].reservation.anchor_id"        | 主播ID         | 
## | anchor_open_id         | varchar(200)      |      |     |         |       | "$.data.room.deco_list.[x].reservation.anchor_open_id"   | 主播开放ID     | 
## | appointment_id         | varchar(200)      |      |     |         |       | "$.data.room.deco_list.[x].reservation.appointment_id"   | 预约ID         | 
## | btn_color              | varchar(7)        |      |     |         |       | "$.data.room.deco_list.[x].reservation.btn_color"        | 按钮颜色       | 
## | reservation_end_time   | timestamp         |      |     |         |       | "$.data.room.deco_list.[x].reservation.end_time"         | 结束时间       | 
## | is_reserved            | bool              |      |     |         |       | "$.data.room.deco_list.[x].reservation.is_reserved"      | 是否保留       | 
## | reservation_room_id    | varchar(200)      |      |     |         |       | "$.data.room.deco_list.[x].reservation.room_id"          | 直播间ID       |
## | reservation_start_time | timestamp         |      |     |         |       | "$.data.room.deco_list.[x].reservation.start_time"       | 开始时间       |
## +------------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+---------------+
##
class RoomDecoReservationTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_DECO_RESERVATION_TABLE_NAME       = 'room_deco_reservation'
  __ROOM_DECO_RESERVATION_TABLE_HEADER     = ['start_time',           'platform',       'room_id',             'deco_index', 
                                             'anchor_id',            'anchor_open_id', 'appointment_id',      'btn_color',
                                             'reservation_end_time', 'is_reserved',    'reservation_room_id', 'reservation_start_time'
                                             ]
  __ROOM_DECO_RESERVATION_TABLE_PRI_KEY    = ['start_time', 'platform', 'room_id', 'deco_index']
  __TABLE_AUTO_INCREMENT                   = []
  __ROOM_DECO_RESERVATION_TABLE_TUPLE      = {item:None for item in __ROOM_DECO_RESERVATION_TABLE_HEADER}
  __SQL_CREATE_ROOM_DECO_RESERVATION_TABLE = '''
                                               CREATE TABLE IF NOT EXISTS {} (
                                                 start_time             timestamp       NOT NULL,
                                                 platform               varchar(20)     NOT NULL,
                                                 room_id                varchar(200)    NOT NULL,
                                                 deco_index             bigint          NOT NULL,
                                                 anchor_id              varchar(200)    DEFAULT NULL,
                                                 anchor_open_id         varchar(200)    DEFAULT NULL,
                                                 appointment_id         varchar(200)    DEFAULT NULL,
                                                 btn_color              varchar(7)      DEFAULT NULL,
                                                 reservation_end_time   timestamp       DEFAULT NULL,
                                                 is_reserved            bool            DEFAULT NULL,
                                                 reservation_room_id    varchar(200)    DEFAULT NULL,
                                                 reservation_start_time timestamp       DEFAULT NULL,
                                                 PRIMARY KEY (start_time, platform, room_id, deco_index)
                                               )
                                             '''.format(__ROOM_DECO_RESERVATION_TABLE_NAME)
  __SQL_DROP_ROOM_DECO_RESERVATION_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_DECO_RESERVATION_TABLE_NAME)


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
    return self.__ROOM_DECO_RESERVATION_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_DECO_RESERVATION_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_DECO_RESERVATION_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_DECO_RESERVATION_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_DECO_RESERVATION_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_DECO_RESERVATION_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## TODO
## $.data.room.deco_list.[x].reservation.btn_rect
##
## +----------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------+---------------------+
## | Field          | Type              | Null | Key | Default | Extra | Topology                                                           | Comment             |
## +----------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------+---------------------+
## | start_time     | timestamp         |  NO  |     |         |       | "$.extra.now"                                                      | 当前时间戳           | 
## | platform       | varchar(20)       |  NO  |     | NULL    |       |           -                                                        | 平台                 | 
## | room_id        | varchar(200)      |  NO  |     |         |       | "$.data.room.id"                                                   | 直播间ID             |
## | deco_index     | unsigned bigint   |      |     |         |       |           -                                                        | 装饰索引号            |
## | btn_rect_index | unsigned bigint   |      |     |         |       | -                                                                  | 索引                 |
## | btn_rect       | TBD               |      |     |         |       | "$.data.room.deco_list.[x].reservation.btn_rect"                   |                      |
## +----------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------+----------------------+
##
class RoomDecoReservationBtnRectTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_DECO_RESERVATION_BTN_RECT_TABLE_NAME       = 'room_deco_reservation_btn_rect'
  __ROOM_DECO_RESERVATION_BTN_RECT_TABLE_HEADER     = ['start_time',           'platform',       'room_id',             'deco_index', 
                                                       'btn_rect_index',       'btn_rect'
                                                       ]
  __ROOM_DECO_RESERVATION_BTN_RECT_TABLE_PRI_KEY    = ['start_time', 'platform', 'room_id', 'deco_index', 'btn_rect_index']
  __TABLE_AUTO_INCREMENT                            = []
  __ROOM_DECO_RESERVATION_BTN_RECT_TABLE_TUPLE      = {item:None for item in __ROOM_DECO_RESERVATION_BTN_RECT_TABLE_HEADER}
  __SQL_CREATE_ROOM_DECO_RESERVATION_BTN_RECT_TABLE = '''
                                                        CREATE TABLE IF NOT EXISTS {} (
                                                          start_time             timestamp       NOT NULL,
                                                          platform               varchar(20)     NOT NULL,
                                                          room_id                varchar(200)    NOT NULL,
                                                          deco_index             bigint          NOT NULL,
                                                          btn_rect_index         varchar(200)    DEFAULT NULL,
                                                          btn_rect               TBD             DEFAULT NULL,
                                                          PRIMARY KEY (start_time, platform, room_id, deco_index, btn_rect_index)
                                                        )
                                                      '''.format(__ROOM_DECO_RESERVATION_BTN_RECT_TABLE_NAME)
  __SQL_DROP_ROOM_DECO_RESERVATION_BTN_RECT_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_DECO_RESERVATION_BTN_RECT_TABLE_NAME)


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
    return self.__ROOM_DECO_RESERVATION_BTN_RECT_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_DECO_RESERVATION_BTN_RECT_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_DECO_RESERVATION_BTN_RECT_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_DECO_RESERVATION_BTN_RECT_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_DECO_RESERVATION_BTN_RECT_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_DECO_RESERVATION_BTN_RECT_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
##
## TODO
## $.data.room.deco_list.[x].text_special_effects
##
## +---------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------+---------------------+
## | Field                     | Type              | Null | Key | Default | Extra | Topology                                                           | Comment             |
## +---------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------+---------------------+
## | start_time                | timestamp         |  NO  |     |         |       | "$.extra.now"                                                      | 当前时间戳           | 
## | platform                  | varchar(20)       |  NO  |     | NULL    |       |           -                                                        | 平台                 | 
## | room_id                   | varchar(200)      |  NO  |     |         |       | "$.data.room.id"                                                   | 直播间ID             |
## | deco_index                | unsigned bigint   |      |     |         |       |           -                                                        | 装饰索引号            |
## | text_special_effect_index | unsigned bigint   |      |     |         |       | -                                                                  | 索引                 |
## | text_special_effect       | TBD               |      |     |         |       | "$.data.room.deco_list.[x].text_special_effects"                   |                      |
## +---------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------+----------------------+
##
##
class RoomDecoTextSpecialEffectsTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_DECO_TEXT_SPECIAL_EFFECT_TABLE_NAME       = 'room_deco_text_special_effect'
  __ROOM_DECO_TEXT_SPECIAL_EFFECT_TABLE_HEADER     = ['start_time',                'platform',       'room_id',             'deco_index', 
                                                       'text_special_effect_index', 'text_special_effect'
                                                       ]
  __ROOM_DECO_TEXT_SPECIAL_EFFECT_TABLE_PRI_KEY    = ['start_time', 'platform', 'room_id', 'deco_index', 'text_special_effect_index']
  __TABLE_AUTO_INCREMENT                            = []
  __ROOM_DECO_TEXT_SPECIAL_EFFECT_TABLE_TUPLE      = {item:None for item in __ROOM_DECO_TEXT_SPECIAL_EFFECT_TABLE_HEADER}
  __SQL_CREATE_ROOM_DECO_TEXT_SPECIAL_EFFECT_TABLE = '''
                                                        CREATE TABLE IF NOT EXISTS {} (
                                                          start_time                        timestamp       NOT NULL,
                                                          platform                          varchar(20)     NOT NULL,
                                                          room_id                           varchar(200)    NOT NULL,
                                                          deco_index                        bigint          NOT NULL,
                                                          text_special_effect_index         varchar(200)    DEFAULT NULL,
                                                          text_special_effect               TBD             DEFAULT NULL,
                                                          PRIMARY KEY (start_time, platform, room_id, deco_index, text_special_effect_index)
                                                        )
                                                      '''.format(__ROOM_DECO_TEXT_SPECIAL_EFFECT_TABLE_NAME)
  __SQL_DROP_ROOM_DECO_TEXT_SPECIAL_EFFECT_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_DECO_TEXT_SPECIAL_EFFECT_TABLE_NAME)


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
    return self.__ROOM_DECO_TEXT_SPECIAL_EFFECT_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_DECO_TEXT_SPECIAL_EFFECT_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_DECO_TEXT_SPECIAL_EFFECT_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_DECO_TEXT_SPECIAL_EFFECT_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_DECO_TEXT_SPECIAL_EFFECT_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_DECO_TEXT_SPECIAL_EFFECT_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

'''
  TBD: no related data type of room_realtime_playback_quality
'''
##
## $.data.room.extra.realtime_playback_qualities
##
## +---------------------------------+-------------------+------+-----+---------+-------+-------------------------------------------------+---------------------+
## | Field                           | Type              | Null | Key | Default | Extra | Topology                                        | Comment             |
## +---------------------------------+-------------------+------+-----+---------+-------+-------------------------------------------------+---------------------+
## | now                             | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"                                   | 当前时间戳           | 
## | platform                        | varchar(20)       | NO   | PRI |         |       |           -                                     | 平台                 | 
## | room_id                         | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                                | 直播间ID             |
## | realtime_playback_quality_index | unsigned bigint   |      |     | NULL    |       |           -                                     | 装饰索引号            |  
## | realtime_playback_quality       | TBD               |      |     | NULL    |       | "$.data.room.extra.realtime_playback_qualities" | 装饰                 | 
## +---------------------------------+-------------------+------+-----+---------+-------+-------------------------------------------------+----------------------+
##
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
## | fans_group_admin_user_id_index | unsigned bigint   | NO   | PRI |         |       |           -                             | 粉丝群管理员ID序号   |
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
  __FANS_GROUP_ADMIN_USER_ID_TABLE_PRI_KEY    = ['fans_group_admin_user_id_index']
  __TABLE_AUTO_INCREMENT                      = ['fans_group_admin_user_id_index']
  __FANS_GROUP_ADMIN_USER_ID_TABLE_TUPLE      = {item:None for item in __FANS_GROUP_ADMIN_USER_ID_TABLE_HEADER}
  __SQL_CREATE_FANS_GROUP_ADMIN_USER_ID_TABLE = '''
                                                CREATE TABLE IF NOT EXISTS {} (
                                                  now                               timestamp(3) NOT NULL,
                                                  platform                          varchar(20)  NOT NULL,
                                                  room_id                           varchar(200) NOT NULL,
                                                  fans_group_admin_user_id_index    bigint       NOT NULL AUTO_INCREMENT,
                                                  fans_group_admin_user_id          varchar(200) DEFAULT NULL,
                                                  PRIMARY KEY (fans_group_admin_user_id_index),
                                                  UNIQUE KEY unique_record (now, platform, room_id, fans_group_admin_user_id)
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
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

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
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## data.room.fans_group_admin_user_open_ids
##
## +-------------------------------------+-------------------+------+-----+---------+-------+----------------------------------------------+----------------------+
## | Field                               | Type              | Null | Key | Default | Extra | Topology                                     | Comment              |
## +-------------------------------------+-------------------+------+-----+---------+-------+----------------------------------------------+----------------------+
## | now                                 | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"                                | 当前时间戳            | 
## | platform                            | varchar(20)       | NO   | PRI |         |       |           -                                  | 平台                  |
## | room_id                             | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                             | 直播间ID              | 
## | fans_group_admin_user_open_id_index | unsigned bigint   | NO   | PRI |         |       |           -                                  | 粉丝群管理员OpenID序号 |
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
  __FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE_PRI_KEY    = ['fans_group_admin_user_open_id_index']
  __TABLE_AUTO_INCREMENT                           = ['fans_group_admin_user_open_id_index']
  __FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE_TUPLE      = {item:None for item in __FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE_HEADER}
  __SQL_CREATE_FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE = '''
                                                     CREATE TABLE IF NOT EXISTS {} (
                                                       now                                    timestamp(3) NOT NULL,
                                                       platform                               varchar(20)  NOT NULL,
                                                       room_id                                varchar(200) NOT NULL,
                                                       fans_group_admin_user_open_id_index    bigint       NOT NULL AUTO_INCREMENT,
                                                       fans_group_admin_user_open_id          varchar(200) DEFAULT NULL,
                                                       PRIMARY KEY (fans_group_admin_user_open_id_index),
                                                       UNIQUE KEY unique_record (now, platform, room_id, fans_group_admin_user_open_id)
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
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

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
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

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
  __TABLE_AUTO_INCREMENT                  = []
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
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

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
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()


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
  __TABLE_AUTO_INCREMENT            = []
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
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

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
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

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
  __TABLE_AUTO_INCREMENT                 = []
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
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

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
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

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
## | `Like`                           | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Like"                             | 点赞                 | 
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
  __TABLE_AUTO_INCREMENT       = []
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
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

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
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

'''
  TBD: no related data type of room_tab
'''
##
## data.room.room_tabs
## +-----------+-------------------+------+-----+---------+-------+-------------------------+----------------------+
## | Field     | Type              | Null | Key | Default | Extra | Topology                | Comment              |
## +-----------+-------------------+------+-----+---------+-------+-------------------------+----------------------+
## | now       | timestamp         | NO   | PRI |         |       | "$.extra.now"           | 当前时间戳            | 
## | platform  | varchar(20)       | NO   | PRI |         |       |           -             | 平台                  |
## | room_id   | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"        | 直播间ID              | 
## | tab_index | unsigned bigint   |      |     | NULL    |       |           -             | tab序号               |
## | room_tab  | TBD               |      |     | NULL    |       | "$.data.room.room_tabs" | 直播间标签列表         |
## +-----------+-------------------+------+-----+---------+-------+-------------------------+----------------------+
##
class RoomTabTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_TAB_TABLE_NAME        = "room_tab"
  __ROOM_TAB_TABLE_HEADER      = ['now',                  'platform',              'room_id',
                                  'tab_index',            'room_tab'
                                  ]
  __ROOM_TAB_TABLE_PRI_KEY    = ['now','platform','room_id']
  __TABLE_AUTO_INCREMENT      = ['tab_index']
  __ROOM_TAB_TABLE_TUPLE      = {item:None for item in __ROOM_TAB_TABLE_HEADER}
  __SQL_CREATE_ROOM_TAB_TABLE = '''
                                CREATE TABLE IF NOT EXISTS {} (
                                  now                  timestamp(3)     NOT NULL,
                                  platform             varchar(20)      NOT NULL,
                                  room_id              varchar(200)     NOT NULL,
                                  tab_index            bigint           NOT NULL AUTO_INCREMENT,
                                  room_tab             TBD              DEFAULT NULL
                                  PRIMARY KEY (tab_index),
                                  UNIQUE KEY unique_record (now, platform, room_id, tab_index)
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
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

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
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

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
  __TABLE_AUTO_INCREMENT                          = []
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
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

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
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## data.room.short_touch_area_config.elements
##
## +---------------+------------------+------+-----+---------+-------+-------------------------------------------------------------+-----------------------+
## | Field         | Type             | Null | Key | Default | Extra | Topology                                                    | Comment               |
## +---------------+------------------+------+-----+---------+-------+-------------------------------------------------------------+-----------------------+
## | now           | timestamp(3)     | NO   | PRI |         |       | "$.extra.now"                                               | 当前时间戳             |
## | platform      | varchar(20)      | NO   | PRI |         |       |           -                                                 | 平台                  | 
## | room_id       | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                                            | 直播间ID              | 
## | element_index | unsigned bigint  | NO   | PRI |         |       |           -                                                 | 短触摸区域配置元素     |
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
  __ROOM_SHORT_TOUCH_AREA_CONFIG_ELEMENT_TABLE_PRI_KEY    = ['element_index']
  __TABLE_AUTO_INCREMENT                                  = ['element_index']
  __ROOM_SHORT_TOUCH_AREA_CONFIG_ELEMENT_TABLE_TUPLE      = {item:None for item in __ROOM_SHORT_TOUCH_AREA_CONFIG_ELEMENT_TABLE_HEADER}
  __SQL_CREATE_ROOM_SHORT_TOUCH_AREA_CONFIG_ELEMENT_TABLE = '''
                                                            CREATE TABLE IF NOT EXISTS {} (
                                                              now                    timestamp(3) NOT NULL,
                                                              platform               varchar(20)  NOT NULL,
                                                              room_id                varchar(200) NOT NULL,
                                                              element_index          bigint       NOT NULL AUTO_INCREMENT,
                                                              priority               tinyint      DEFAULT NULL,
                                                              type                   tinyint      DEFAULT NULL,
                                                              PRIMARY KEY (element_index)
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
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

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
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## data.room.short_touch_area_config.strategy_feat_whitelist
##
## +---------------------+------------------+------+-----+---------+-------+---------------------------------------------------------------+-----------------------+
## | Field               | Type             | Null | Key | Default | Extra | Topology                                                      | Comment               |
## +---------------------+------------------+------+-----+---------+-------+---------------------------------------------------------------+-----------------------+
## | start_time          | timestamp        | NO   | PRI |         |       | "$.extra.now"                                                 | 当前时间戳             |
## | platform            | varchar(20)      | NO   | PRI |         |       |           -                                                   | 平台                  | 
## | room_id             | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                                              | 直播间ID              | 
## | whitelist_tag_index | unsigned bigint  | NO   | PRI |         |       |           -                                                   | 白名单索引             | 
## | whitelist_tag       | tinytext         |      |     | NULL    |       | "$.data.room.short_touch_area_config.strategy_feat_whitelist" | 白名单标签             | 
## +---------------------+------------------+------+-----+---------+-------+---------------------------------------------------------------+-----------------------+
##
class RoomShortTouchAreaConfigStrategyFeatWhitelistTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_SHORT_TOUCH_AREA_CONFIG_STRATEGY_FEAT_WHITELIST_TABLE_NAME       = "room_short_touch_area_config_strategy_feat_whitelist"
  __ROOM_SHORT_TOUCH_AREA_CONFIG_STRATEGY_FEAT_WHITELIST_TABLE_HEADER     = ['start_time', 'platform', 'room_id', 'whitelist_tag_index', 'whitelist_tag']
  __ROOM_SHORT_TOUCH_AREA_CONFIG_STRATEGY_FEAT_WHITELIST_TABLE_PRI_KEY    = ['start_time', 'platform', 'room_id', 'whitelist_tag_index']
  __TABLE_AUTO_INCREMENT                                                  = []
  __ROOM_SHORT_TOUCH_AREA_CONFIG_STRATEGY_FEAT_WHITELIST_TABLE_TUPLE      = {item:None for item in __ROOM_SHORT_TOUCH_AREA_CONFIG_STRATEGY_FEAT_WHITELIST_TABLE_HEADER}
  __SQL_CREATE_ROOM_SHORT_TOUCH_AREA_CONFIG_STRATEGY_FEAT_WHITELIST_TABLE = '''
                                                                            CREATE TABLE IF NOT EXISTS {} (
                                                                              start_time             timestamp    NOT NULL,
                                                                              platform               varchar(20)  NOT NULL,
                                                                              room_id                varchar(200) NOT NULL,
                                                                              whitelist_tag_index    bigint       NOT NULL,
                                                                              whitelist_tag          tinytext     DEFAULT NULL,
                                                                              PRIMARY KEY (start_time, platform, room_id, whitelist_tag_index)
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
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

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
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## data.room.short_touch_area_config.temp_state_condition_map
##
## +---------------+------------------+------+-----+---------+-------+---------------------------------------------------------------------------------------+------------+
## | Field         | Type             | Null | Key | Default | Extra | Topology                                                                              | Comment    |
## +---------------+------------------+------+-----+---------+-------+---------------------------------------------------------------------------------------+------------+
## | now           | timestamp(3)     | NO   | PRI |         |       | "$.extra.now"                                                                         | 当前时间戳  |
## | platform      | varchar(20)      | NO   | PRI |         |       |           -                                                                           | 平台       | 
## | room_id       | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                                                                      | 直播间ID   |
## | map_index     | unsigned bigint  | NO   | PRI |         |       |           -                                                                           | 映射索引   |
## | minimum_gap   | unsigned int     |      |     | NULL    |       | "$.data.room.short_touch_area_config.temp_state_condition_map.'x'.minimum_gap"        | 最小间隔   |
## | priority      | unsigned tinyint |      |     | NULL    |       | "$.data.room.short_touch_area_config.temp_state_condition_map.'x'.type.priority"      | 优先级     |
## | strategy_type | unsigned tinyint |      |     | NULL    |       | "$.data.room.short_touch_area_config.temp_state_condition_map.'x'.type.strategy_type" | 策略类型   |
## +---------------+------------------+------+-----+---------+-------+---------------------------------------------------------------------------------------+------------+
##
class RoomTempStateConditionMapTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_TEMP_STATE_CONDITION_MAP_TABLE_NAME       = "room_temp_state_condition_map"
  __ROOM_TEMP_STATE_CONDITION_MAP_TABLE_HEADER     = ['now', 'platform', 'room_id', 'map_index', 'minimum_gap', 'priority', 'strategy_type']
  __ROOM_TEMP_STATE_CONDITION_MAP_TABLE_PRI_KEY    = ['map_index']
  __TABLE_AUTO_INCREMENT                           = ['map_index']
  __ROOM_TEMP_STATE_CONDITION_MAP_TABLE_TUPLE      = {item:None for item in __ROOM_TEMP_STATE_CONDITION_MAP_TABLE_HEADER}
  __SQL_CREATE_ROOM_TEMP_STATE_CONDITION_MAP_TABLE = '''
                                                     CREATE TABLE IF NOT EXISTS {} (
                                                       now                    timestamp(3) NOT NULL,
                                                       platform               varchar(20)  NOT NULL,
                                                       room_id                varchar(200) NOT NULL,
                                                       map_index              bigint       NOT NULL AUTO_INCREMENT,
                                                       minimum_gap            int          DEFAULT NULL,
                                                       priority               tinyint      DEFAULT NULL,
                                                       strategy_type          tinyint      DEFAULT NULL,
                                                       PRIMARY KEY (map_index),
                                                       UNIQUE KEY unique_record (now, platform, room_id, strategy_type)
                                                     )
                                                     '''.format(__ROOM_TEMP_STATE_CONDITION_MAP_TABLE_NAME)
  __SQL_DROP_ROOM_TEMP_STATE_CONDITION_MAP_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_TEMP_STATE_CONDITION_MAP_TABLE_NAME)

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
    return self.__ROOM_TEMP_STATE_CONDITION_MAP_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_TEMP_STATE_CONDITION_MAP_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_TEMP_STATE_CONDITION_MAP_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_TEMP_STATE_CONDITION_MAP_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_TEMP_STATE_CONDITION_MAP_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_TEMP_STATE_CONDITION_MAP_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## data.room.short_touch_area_config.temp_state_global_condition.ignore_strategy_types
##
## +-----------------------------+------------------+------+-----+---------+-------+-----------------------------------------------------------------------------------------+----------------+
## | Field                       | Type             | Null | Key | Default | Extra | Topology                                                                                | Comment        |
## +-----------------------------+------------------+------+-----+---------+-------+-----------------------------------------------------------------------------------------+----------------+
## | now                         | timestamp(3)     | NO   | PRI |         |       | "$.extra.now"                                                                           | 当前时间戳      |
## | platform                    | varchar(20)      | NO   | PRI |         |       |           -                                                                             | 平台            | 
## | room_id                     | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                                                                        | 直播间ID        |
## | ignore_strategy_type_index  | unsigned bigint  |      |     | NULL    |       |                                  -                                                      | 忽略策略类型索引 |
## | ignore_strategy_type        | unsigned tinyint |      |     | NULL    |       | "$.data.room.short_touch_area_config.temp_state_global_condition.ignore_strategy_types" | 忽略策略类型     |
## +-----------------------------+------------------+------+-----+---------+-------+-----------------------------------------------------------------------------------------+-----------------+
##
class RoomTempStateGlobalConditionIgnoreStrategyTypeTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_TEMP_STATE_GLOBAL_CONDITION_IGNORE_STRATEGY_TYPE_TABLE_NAME       = "room_temp_state_global_condition_ignore_strategy_type"
  __ROOM_TEMP_STATE_GLOBAL_CONDITION_IGNORE_STRATEGY_TYPE_TABLE_HEADER     = ['now', 'platform', 'room_id', 'ignore_strategy_type_index', 'ignore_strategy_type']
  __ROOM_TEMP_STATE_GLOBAL_CONDITION_IGNORE_STRATEGY_TYPE_TABLE_PRI_KEY    = ['ignore_strategy_type_index']
  __TABLE_AUTO_INCREMENT                                                   = ['ignore_strategy_type_index']
  __ROOM_TEMP_STATE_GLOBAL_CONDITION_IGNORE_STRATEGY_TYPE_TABLE_TUPLE      = {item:None for item in __ROOM_TEMP_STATE_GLOBAL_CONDITION_IGNORE_STRATEGY_TYPE_TABLE_HEADER}
  __SQL_CREATE_ROOM_TEMP_STATE_GLOBAL_CONDITION_IGNORE_STRATEGY_TYPE_TABLE = '''
                                                                             CREATE TABLE IF NOT EXISTS {} (
                                                                               now                         timestamp(3) NOT NULL,
                                                                               platform                    varchar(20)  NOT NULL,
                                                                               room_id                     varchar(200) NOT NULL,
                                                                               ignore_strategy_type_index  bigint       NOT NULL AUTO_INCREMENT,
                                                                               ignore_strategy_type        tinyint      DEFAULT NULL,
                                                                               PRIMARY KEY (ignore_strategy_type_index),
                                                                               UNIQUE KEY unqiue_record (now, platform, room_id, ignore_strategy_type)
                                                                             )
                                                                             '''.format(__ROOM_TEMP_STATE_GLOBAL_CONDITION_IGNORE_STRATEGY_TYPE_TABLE_NAME)
  __SQL_DROP_ROOM_TEMP_STATE_GLOBAL_CONDITION_IGNORE_STRATEGY_TYPE_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_TEMP_STATE_GLOBAL_CONDITION_IGNORE_STRATEGY_TYPE_TABLE_NAME)

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
    return self.__ROOM_TEMP_STATE_GLOBAL_CONDITION_IGNORE_STRATEGY_TYPE_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_TEMP_STATE_GLOBAL_CONDITION_IGNORE_STRATEGY_TYPE_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_TEMP_STATE_GLOBAL_CONDITION_IGNORE_STRATEGY_TYPE_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_TEMP_STATE_GLOBAL_CONDITION_IGNORE_STRATEGY_TYPE_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_TEMP_STATE_GLOBAL_CONDITION_IGNORE_STRATEGY_TYPE_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_TEMP_STATE_GLOBAL_CONDITION_IGNORE_STRATEGY_TYPE_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## data.room.short_touch_area_config.temp_state_global_condition
##
## +--------------+------------------+------+-----+---------+-------+--------------------------------------------------------------------------------+------------+
## | Field        | Type             | Null | Key | Default | Extra | Topology                                                                       | Comment    |
## +--------------+------------------+------+-----+---------+-------+--------------------------------------------------------------------------------+------------+
## | now          | timestamp        | NO   | PRI |         |       | "$.extra.now"                                                                  | 当前时间戳 |
## | platform     | varchar(20)      | NO   | PRI |         |       |           -                                                                    | 平台       | 
## | room_id      | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                                                               | 直播间ID   |
## | allow_count  | unsigned tinyint |      |     | NULL    |       | "$.data.room.short_touch_area_config.temp_state_global_condition.allow_count"  | 允许总数   |
## | duration_gap | unsigned int     |      |     | NULL    |       | "$.data.room.short_touch_area_config.temp_state_global_condition.duration_gap" | 持续间隔   |
## +--------------+------------------+------+-----+---------+-------+--------------------------------------------------------------------------------+------------+
##
class RoomTempStateGlobalConditionTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_TEMP_STATE_GLOBAL_CONDITION_TABLE_NAME       = "room_temp_state_global_condition"
  __ROOM_TEMP_STATE_GLOBAL_CONDITION_TABLE_HEADER     = ['now', 'platform', 'room_id', 'allow_count', 'duration_gap']
  __ROOM_TEMP_STATE_GLOBAL_CONDITION_TABLE_PRI_KEY    = ['now', 'platform', 'room_id']
  __TABLE_AUTO_INCREMENT                              = []
  __ROOM_TEMP_STATE_GLOBAL_CONDITION_TABLE_TUPLE      = {item:None for item in __ROOM_TEMP_STATE_GLOBAL_CONDITION_TABLE_HEADER}
  __SQL_CREATE_ROOM_TEMP_STATE_GLOBAL_CONDITION_TABLE = '''
                                                        CREATE TABLE IF NOT EXISTS {} (
                                                          now                    timestamp(3) NOT NULL,
                                                          platform               varchar(20)  NOT NULL,
                                                          room_id                varchar(200) NOT NULL,
                                                          allow_count            tinyint      DEFAULT NULL,
                                                          duration_gap           int          DEFAULT NULL,
                                                          PRIMARY KEY (now, platform, room_id)
                                                        )
                                                        '''.format(__ROOM_TEMP_STATE_GLOBAL_CONDITION_TABLE_NAME)
  __SQL_DROP_ROOM_TEMP_STATE_GLOBAL_CONDITION_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_TEMP_STATE_GLOBAL_CONDITION_TABLE_NAME)

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
    return self.__ROOM_TEMP_STATE_GLOBAL_CONDITION_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_TEMP_STATE_GLOBAL_CONDITION_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_TEMP_STATE_GLOBAL_CONDITION_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_TEMP_STATE_GLOBAL_CONDITION_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_TEMP_STATE_GLOBAL_CONDITION_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_TEMP_STATE_GLOBAL_CONDITION_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## data.room.short_touch_area_config.temp_state_strategy
## +------------------------+------------------+------+-----+---------+-------+-------------------------------------------------------------------------------------+------------+
## | Field                  | Type             | Null | Key | Default | Extra | Topology                                                                            | Comment    |
## +------------------------+------------------+------+-----+---------+-------+-------------------------------------------------------------------------------------+------------+
## | now                    | timestamp        | NO   |     |         |       | "$.extra.now"                                                                       | 当前时间戳 |
## | platform               | varchar(20)      | NO   |     |         |       |           -                                                                         | 平台       | 
## | room_id                | varchar(200)     | NO   |     |         |       | "$.data.room.id"                                                                    | 直播间ID   |
## | short_touch_type       | unsigned int     |      |     | NULL    |       | "$.data.room.short_touch_area_config.temp_state_global_condition.short_touch_type"  | 允许总数   |
## | short_touch_type_index | bigint           | NO   | PRI |         |       |           -                                                                         |            | 
## +------------------------+------------------+------+-----+---------+-------+-------------------------------------------------------------------------------------+------------+
##
class RoomTempStateStrategyTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_TEMP_STATE_STRATEGY_TABLE_NAME       = "room_temp_state_strategy"
  __ROOM_TEMP_STATE_STRATEGY_TABLE_HEADER     = ['now', 'platform', 'room_id', 'short_touch_type', 'short_touch_type_index']
  __ROOM_TEMP_STATE_STRATEGY_TABLE_PRI_KEY    = ['short_touch_type_index']
  __TABLE_AUTO_INCREMENT                      = ['short_touch_type_index']
  __ROOM_TEMP_STATE_STRATEGY_TABLE_TUPLE      = {item:None for item in __ROOM_TEMP_STATE_STRATEGY_TABLE_HEADER}
  __SQL_CREATE_ROOM_TEMP_STATE_STRATEGY_TABLE = '''
                                                  CREATE TABLE IF NOT EXISTS {} (
                                                    now                       timestamp(3) NOT NULL,
                                                    platform                  varchar(20)  NOT NULL,
                                                    room_id                   varchar(200) NOT NULL,
                                                    short_touch_type          int          NOT NULL,
                                                    short_touch_type_index    bigint       NOT NULL AUTO_INCREMENT,
                                                    PRIMARY KEY (short_touch_type_index),
                                                    UNIQUE KEY unique_record (now, platform, room_id, short_touch_type)
                                                  )
                                                  '''.format(__ROOM_TEMP_STATE_STRATEGY_TABLE_NAME)
  __SQL_DROP_ROOM_TEMP_STATE_STRATEGY_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_TEMP_STATE_STRATEGY_TABLE_NAME)

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
    return self.__ROOM_TEMP_STATE_STRATEGY_TABLE_NAME

  ##
  ## table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_TEMP_STATE_STRATEGY_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_TEMP_STATE_STRATEGY_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_TEMP_STATE_STRATEGY_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_TEMP_STATE_STRATEGY_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_TEMP_STATE_STRATEGY_TABLE

  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## data.room.short_touch_area_config.temp_state_strategy.strategy_map
##
## +-------------------+------------------+------+-----+---------+-------+--------------------------------------------------------------------------------------------+------------+
## | Field             | Type             | Null | Key | Default | Extra | Topology                                                                                   | Comment    |
## +-------------------+------------------+------+-----+---------+-------+--------------------------------------------------------------------------------------------+------------+
## | now               | timestamp        | NO   | PRI |         |       | "$.extra.now"                                                                              | 当前时间戳 |
## | platform          | varchar(20)      | NO   | PRI |         |       |           -                                                                                | 平台       | 
## | room_id           | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                                                                           | 直播间ID   |
## | short_touch_type  | unsigned int     | NO   | PRI | NULL    |       | "$.data.room.short_touch_area_config.temp_state_strategy.'x'.short_touch_type"             | 允许总数   |
## | duration          | unsigned int     |      |     | NULL    |       | "$.data.room.short_touch_area_config.temp_state_strategy.strategy_map.'x'.duration"        | 持续时间   |
## | strategy_method   | varchar(100)     |      |     | NULL    |       | "$.data.room.short_touch_area_config.temp_state_strategy.strategy_map.'x'.strategy_method" | 策略方法   |
## | priority          | unsigned tinyint |      |     | NULL    |       | "$.data.room.short_touch_area_config.temp_state_strategy.strategy_map.'x'.priority"        | 优先级     |
## | strategy_type     | unsigned tinyint | NO   | PRI | NULL    |       | "$.data.room.short_touch_area_config.temp_state_strategy.strategy_map.'x'.strategy_type"   | 策略类型   |
## +-------------------+------------------+------+-----+---------+-------+--------------------------------------------------------------------------------------------+------------+
##
class RoomTempStateStrategyMapTable(SocialMediaStreamDataTable):
  ##
  ## >>=============================== attribute ===============================>>
  ##
  __ROOM_TEMP_STATE_STRATEGY_MAP_TABLE_NAME = "room_temp_state_strategy_map"
  __ROOM_TEMP_STATE_STRATEGY_MAP_TABLE_HEADER = ['now', 'platform', 'room_id', 'short_touch_type', 'duration', 'strategy_method', 'priority', 'strategy_type']
  __ROOM_TEMP_STATE_STRATEGY_MAP_TABLE_PRI_KEY = ['now', 'platform', 'room_id', 'short_touch_type', 'strategy_type']
  __TABLE_AUTO_INCREMENT = []
  __ROOM_TEMP_STATE_STRATEGY_MAP_TABLE_TUPLE = {item:None for item in __ROOM_TEMP_STATE_STRATEGY_MAP_TABLE_HEADER}
  __SQL_CREATE_ROOM_TEMP_STATE_STRATEGY_MAP_TABLE = '''
                                                  CREATE TABLE IF NOT EXISTS {} (
                                                    now                    timestamp(3)  NOT NULL,
                                                    platform               varchar(20)   NOT NULL,
                                                    room_id                varchar(200)  NOT NULL,
                                                    short_touch_type       int           NOT NULL,
                                                    duration               int           DEFAULT NULL,
                                                    strategy_method        varchar(100)  DEFAULT NULL,
                                                    priority               tinyint       DEFAULT NULL,
                                                    strategy_type          tinyint       NOT NULL,
                                                    PRIMARY KEY (now, platform, room_id, short_touch_type, strategy_type)
                                                  )
                                                  '''.format(__ROOM_TEMP_STATE_STRATEGY_MAP_TABLE_NAME)
  __SQL_DROP_ROOM_TEMP_STATE_STRATEGY_MAP_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_TEMP_STATE_STRATEGY_MAP_TABLE_NAME)
  
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
    return self.__ROOM_TEMP_STATE_STRATEGY_MAP_TABLE_NAME

  ##
  ## table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_TEMP_STATE_STRATEGY_MAP_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_TEMP_STATE_STRATEGY_MAP_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_TEMP_STATE_STRATEGY_MAP_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_TEMP_STATE_STRATEGY_MAP_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_TEMP_STATE_STRATEGY_MAP_TABLE

  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## room
##
## +-------------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------+---------------------+
## | Field                               | Type              | Null | Key | Default | Extra | Topology                                               | Comment             |
## +-------------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------+---------------------+
## | now                                 | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"                                          | 当前时间戳           | 
## | platform                            | varchar(20)       | NO   | PRI |         |       |           -                                            | 平台                 | 
## | id                                  | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                                       | 直播间ID             | 
## | `rank`                              | unsigned smallint |      |     | NULL    |       | "$.data.room.living_room_attrs.rank"                   | 排名/等级            |
## | silence_flag                        | unsigned tinyint  |      |     | NULL    |       | "$.data.room.living_room_attrs.silence_flag"           | 直播间静音状态       | 
## | view_stats_display_long             | tinytext          |      |     | NULL    |       | "$.data.room.room_view_stats.display_long"             | 直播间观看人数       | 
## | view_stats_display_long_anchor      | tinytext          |      |     | NULL    |       | "$.data.room.room_view_stats.display_long_anchor"      | 主播观看人数         | 
## | view_stats_display_middle           | tinytext          |      |     | NULL    |       | "$.data.room.room_view_stats.display_middle"           | 直播间观看人数（中）  |
## | view_stats_display_middle_anchor    | tinytext          |      |     | NULL    |       | "$.data.room.room_view_stats.display_middle_anchor"    | 主播观看人数（中）    |
## | view_stats_display_short            | tinytext          |      |     | NULL    |       | "$.data.room.room_view_stats.display_short"            | 直播间观看人数（短）  |
## | view_stats_display_short_anchor     | tinytext          |      |     | NULL    |       | "$.data.room.room_view_stats.display_short_anchor"     | 主播观看人数（短）    |
## | view_stats_display_type             | unsigned tinyint  |      |     | NULL    |       | "$.data.room.room_view_stats.display_type"             | 直播间观看人数显示类型 |
## | view_stats_display_value            | unsigned int      |      |     | NULL    |       | "$.data.room.room_view_stats.display_value"            | 直播间观看人数        |
## | view_stats_display_version          | varchar(20)       |      |     | NULL    |       | "$.data.room.room_view_stats.display_version"          | 直播间观看人数显示版本 |
## | view_stats_incremental              | bool              |      |     | NULL    |       | "$.data.room.room_view_stats.incremental"              | 是否增量更新          |
## | view_stats_is_hidden                | bool              |      |     | NULL    |       | "$.data.room.room_view_stats.is_hidden"                | 是否隐藏状态          |
## | user_share_text                     | text              |      |     | NULL    |       | "$.data.room.user_share_text"                          | 用户分享文本          |
## | screen_capture_sharing_title        | tinytext          |      |     | NULL    |       | "$.data.room.screen_capture_sharing_title"             | 屏幕截图分享标题       |
## | short_title                         | tinytext          |      |     | NULL    |       | "$.data.room.short_title"                              | 屏幕直播间短          |
## | lottery_finish_time                 | timestamp         |      |     | NULL    |       | "$.data.room.lottery_finish_time"                      | 抽奖结束时间          |
## | luckymoney_num                      | unsigned int      |      |     | NULL    |       | "$.data.room.luckymoney_num"                           | 幸运红包数量          |
## | mosaic_status                       | unsigned int      |      |     | NULL    |       | "$.data.room.mosaic_status"                            | 马赛克状态            |
## | mosaic_tip                          | tinytext          |      |     | NULL    |       | "$.data.room.mosaic_tip"                               | 马赛克提示            |
## | popularity                          | unsigned bigint   |      |     | NULL    |       | "$.data.room.popularity"                               | 人气                 |
## | popularity_str                      | varchar(20)       |      |     | NULL    |       | "$.data.room.popularity_str"                           | 人气字符串            |
## | pre_enter_time                      | timestamp         |      |     | NULL    |       | "$.data.room.pre_enter_time"                           | 预进入时间            |
## | preview_copy                        | tinytext          |      |     | NULL    |       | "$.data.room.preview_copy"                             | 预览复制文本          |
## | preview_flow_tag                    | unsigned tinyint  |      |     | NULL    |       | "$.data.room.preview_flow_tag"                         | 预览流量标签          |
## | private_info                        | text              |      |     | NULL    |       | "$.data.room.private_info"                             | 私有信息              |
## | ranklist_audience_type              | unsigned tinyint  |      |     | NULL    |       | "$.data.room.ranklist_audience_type"                   | 排行榜观众类型        |
## | real_distance                       | varchar(100)      |      |     | NULL    |       | "$.data.room.real_distance"                            | 实际距离              |
## | redpacket_audience_auth             | unsigned tinyint  |      |     | NULL    |       | "$.data.room.redpacket_audience_auth"                  | 红包观众认证          |
## | relation_tag                        | tinytext          |      |     | NULL    |       | "$.data.room.relation_tag"                             | 关系标签              |
## | replay                              | bool              |      |     | NULL    |       | "$.data.room.replay"                                   | 是否为回放            |
## | replay_location                     | unsigned tinyint  |      |     | NULL    |       | "$.data.room.replay_location"                          | 回放位置              |
## | room_audit_status                   | unsigned tinyint  |      |     | NULL    |       | "$.data.room.room_audit_status"                        | 直播间审核状态        |
## | room_create_ab_param                | text              |      |     | NULL    |       | "$.data.room.room_create_ab_param"                     | 直播间创建AB参数      |
## | sofa_layout                         | unsigned tinyint  |      |     | NULL    |       | "$.data.room.sofa_layout"                              | 沙发布局              |
## | stamps                              | text              |      |     | NULL    |       | "$.data.room.stamps"                                   | 印章                 |
## | comment_count                       | unsigned bigint   |      |     | NULL    |       | "$.data.room.stats.comment_count"                      | 评论数量              |
## | digg_count                          | unsigned bigint   |      |     | NULL    |       | "$.data.room.stats.digg_count"                         | 点赞数量              |
## | dou_plus_promotion                  | tinytext          |      |     | NULL    |       | "$.data.room.stats.dou_plus_promotion"                 | DouPlus推广          |
## | enter_count                         | unsigned bigint   |      |     | NULL    |       | "$.data.room.stats.enter_count"                        | 进入数量              |
## | fan_ticket                          | unsigned bigint   |      |     | NULL    |       | "$.data.room.stats.fan_ticket"                         | 粉丝票数量            |
## | follow_count                        | unsigned bigint   |      |     | NULL    |       | "$.data.room.stats.follow_count"                       | 关注数量              |
## | gift_uv_count                       | unsigned int      |      |     | NULL    |       | "$.data.room.stats.gift_uv_count"                      | 礼物UV数量            |
## | like_count                          | unsigned int      |      |     | NULL    |       | "$.data.room.stats.like_count"                         | 喜欢数量              |
## | money                               | unsigned int      |      |     | NULL    |       | "$.data.room.stats.money"                              | 金额                  |
## | total_user                          | unsigned int      |      |     | NULL    |       | "$.data.room.stats.total_user"                         | 用户数量              |
## | total_user_desp                     | text              |      |     | NULL    |       | "$.data.room.stats.total_user_desp"                    | 总用户描述            |
## | total_user_str                      | varchar(100)      |      |     | NULL    |       | "$.data.room.stats.total_user_str"                     | 总用户描述            |
## | up_right_stats_str                  | varchar(100)      |      |     | NULL    |       | "$.data.room.stats.up_right_stats_str"                 | 右上角统计字符串      |
## | up_right_stats_str_complete         | tinytext          |      |     | NULL    |       | "$.data.room.stats.up_right_stats_str_complete"        | 完整的右上角统计字符串 |
## | user_count_composition_city         | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stats.user_count_composition.city"        | 城市                 |
## | user_count_composition_my_follow    | unsigned bigint   |      |     | NULL    |       | "$.data.room.stats.user_count_composition.my_follow"   | 我的关注              |
## | user_count_composition_other        | unsigned bigint   |      |     | NULL    |       | "$.data.room.stats.user_count_composition.other"       | 其他                 |
## | user_count_composition_video_detail | unsigned bigint   |      |     | NULL    |       | "$.data.room.stats.user_count_composition.video_detail"| 视频详情              |
## | user_count_str                      | unsigned bigint   |      |     | NULL    |       | "$.data.room.stats.user_count_str"                     | 用户数量字符串        |
## | watermelon                          | unsigned bigint   |      |     | NULL    |       | "$.data.room.stats.watermelon"                         | 西瓜                 |
## | welfare_donation_amount             | unsigned bigint   |      |     | NULL    |       | "$.data.room.stats.welfare_donation_amount"            | 福利捐赠金额          |
## | status                              | unsigned tinyint  |      |     | NULL    |       | "$.data.room.status"                                   | 直播状态             | 
## | stream_close_time                   | timestamp         |      |     | NULL    |       | "$.data.room.stream_close_time"                        | 直播间流关闭时间戳     |
## | stream_id                           | varchar(200)      |      |     | NULL    |       | "$.data.room.stream_id"                                | 直播间流ID            |
## | stream_provider                     | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stream_provider"                          | 直播间流提供者         |
## | sun_daily_icon_content              | text              |      |     | NULL    |       | "$.data.room.sun_daily_icon_content"                   | 日常图标内容          |
## | challenge_info                      | tinytext          |      |     | NULL    |       | "$.data.room.challenge_info"                           | 挑战信息              |
## | danmaku_detail                      | unsigned int      |      |     | NULL    |       | "$.data.room.danmaku_detail"                           | 弹幕详情              |
## | hot_sentence_info                   | text              |      |     | NULL    |       | "$.data.room.hot_sentence_info"                        | 热门语句信息          |
## | last_ping_time                      | timestamp         |      |     | NULL    |       | "$.data.room.last_ping_time"                           | 最后ping时间          |
## | room_like_count                     | unsigned bigint   |      |     | NULL    |       | "$.data.room.like_count"                               | 点赞数量              |
## | linker_map                          | json              |      |     | NULL    |       | "$.data.room.linker_map"                               | 点连接器映射          |
## | web_count                           | unsigned bigint   |      |     | NULL    |       | "$.data.room.web_count"                                | 网页观看人数          |
## | webcast_comment_tcs                 | unsigned int      |      |     | NULL    |       | "$.data.room.webcast_comment_tcs"                      | 直播间评论TCs         |
## | with_aggregate_column               | bool              |      |     | NULL    |       | "$.data.room.with_aggregate_column"                    | 是否有聚合栏目        |
## | with_draw_something                 | bool              |      |     | NULL    |       | "$.data.room.with_draw_something"                      | 是否有抽奖            |
## | with_ktv                            | bool              |      |     | NULL    |       | "$.data.room.with_ktv"                                 | 是否有KTV             |
## | with_linkmic                        | bool              |      |     | NULL    |       | "$.data.room.with_linkmic"                             | 是否有连麦            |
## +-------------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------+----------------------+
##
class RoomRecordTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_RECORD_TABLE_NAME       = "room_record"
  __ROOM_RECORD_TABLE_HEADER     = ['now',                              'platform',                            'id',                           '`rank`',                           'silence_flag',
                                    'view_stats_display_long',          'view_stats_display_long_anchor',      'view_stats_display_middle',    'view_stats_display_middle_anchor', 'view_stats_display_short', 
                                    'view_stats_display_short_anchor',  'view_stats_display_type',             'view_stats_display_value',     'view_stats_display_version',       'view_stats_incremental',
                                    'view_stats_is_hidden',             'user_share_text',                     'screen_capture_sharing_title', 'short_title',                      'lottery_finish_time',
                                    'luckymoney_num',                   'mosaic_status',                       'mosaic_tip',                   'popularity',                       'popularity_str',
                                    'pre_enter_time',                   'preview_copy',                        'preview_flow_tag',             'private_info',                     'ranklist_audience_type',
                                    'real_distance',                    'redpacket_audience_auth',             'relation_tag',                 'replay',                           'replay_location',
                                    'room_audit_status',                'room_create_ab_param',                'sofa_layout',                  'stamps',                           'comment_count',
                                    'digg_count',                       'dou_plus_promotion',                  'enter_count',                  'fan_ticket',                       'follow_count',
                                    'gift_uv_count',                    'like_count',                          'money',                        'total_user',                       'total_user_desp',
                                    'total_user_str',                   'up_right_stats_str',                  'up_right_stats_str_complete',  'user_count_composition_city',      'user_count_composition_my_follow',
                                    'user_count_composition_other',     'user_count_composition_video_detail', 'user_count_str',               'watermelon',                       'welfare_donation_amount',
                                    'status',                           'stream_close_time',                   'stream_id',                    'stream_provider',                  'sun_daily_icon_content',
                                    'challenge_info',                   'danmaku_detail',                      'hot_sentence_info',            'last_ping_time',                   'room_like_count',
                                    'linker_map',                       'web_count',                           'webcast_comment_tcs',          'with_aggregate_column',            'with_draw_something',
                                    'with_ktv',                         'with_linkmic'
                                    ]
  __ROOM_RECORD_TABLE_PRI_KEY    = ['now', 'platform', 'id']
  __TABLE_AUTO_INCREMENT         = []
  __ROOM_RECORD_TABLE_TUPLE      = {item:None for item in __ROOM_RECORD_TABLE_HEADER}
  __SQL_CREATE_ROOM_RECORD_TABLE = '''
                                   CREATE TABLE IF NOT EXISTS {} (
                                     now                                  timestamp(3)         NOT NULL,
                                     platform                             varchar(20)          NOT NULL,
                                     id                                   varchar(200)         NOT NULL,
                                     `rank`                               smallint             DEFAULT NULL,
                                     silence_flag                         tinyint              DEFAULT NULL,
                                     view_stats_display_long              tinytext             DEFAULT NULL,
                                     view_stats_display_long_anchor       tinytext             DEFAULT NULL,
                                     view_stats_display_middle            tinytext             DEFAULT NULL,
                                     view_stats_display_middle_anchor     tinytext             DEFAULT NULL,
                                     view_stats_display_short             tinytext             DEFAULT NULL,
                                     view_stats_display_short_anchor      tinytext             DEFAULT NULL,
                                     view_stats_display_type              tinyint              DEFAULT NULL,
                                     view_stats_display_value             int                  DEFAULT NULL,
                                     view_stats_display_version           varchar(20)          DEFAULT NULL,
                                     view_stats_incremental               bool                 DEFAULT NULL,
                                     view_stats_is_hidden                 bool                 DEFAULT NULL,
                                     user_share_text                      text                 DEFAULT NULL,
                                     screen_capture_sharing_title         tinytext             DEFAULT NULL,
                                     short_title                          tinytext             DEFAULT NULL,
                                     lottery_finish_time                  timestamp            DEFAULT NULL,
                                     luckymoney_num                       int                  DEFAULT NULL,
                                     mosaic_status                        int                  DEFAULT NULL,
                                     mosaic_tip                           tinytext             DEFAULT NULL,
                                     popularity                           bigint               DEFAULT NULL,
                                     popularity_str                       varchar(20)          DEFAULT NULL,
                                     pre_enter_time                       timestamp            DEFAULT NULL,
                                     preview_copy                         tinytext             DEFAULT NULL,
                                     preview_flow_tag                     tinyint              DEFAULT NULL,
                                     private_info                         text                 DEFAULT NULL,
                                     ranklist_audience_type               tinyint              DEFAULT NULL,
                                     real_distance                        varchar(100)         DEFAULT NULL,
                                     redpacket_audience_auth              tinyint              DEFAULT NULL,
                                     relation_tag                         tinytext             DEFAULT NULL,
                                     replay                               bool                 DEFAULT NULL,
                                     replay_location                      tinyint              DEFAULT NULL,
                                     room_audit_status                    tinyint              DEFAULT NULL,
                                     room_create_ab_param                 text                 DEFAULT NULL,
                                     sofa_layout                          tinyint              DEFAULT NULL,
                                     stamps                               text                 DEFAULT NULL,
                                     comment_count                        bigint               DEFAULT NULL,
                                     digg_count                           bigint               DEFAULT NULL,
                                     dou_plus_promotion                   tinytext             DEFAULT NULL,
                                     enter_count                          bigint               DEFAULT NULL,
                                     fan_ticket                           bigint               DEFAULT NULL,
                                     follow_count                         bigint               DEFAULT NULL,
                                     gift_uv_count                        int                  DEFAULT NULL,
                                     like_count                           int                  DEFAULT NULL,
                                     money                                int                  DEFAULT NULL,
                                     total_user                           int                  DEFAULT NULL,
                                     total_user_desp                      text                 DEFAULT NULL,
                                     total_user_str                       varchar(100)         DEFAULT NULL,
                                     up_right_stats_str                   varchar(100)         DEFAULT NULL,
                                     up_right_stats_str_complete          tinytext             DEFAULT NULL,
                                     user_count_composition_city          tinyint              DEFAULT NULL,
                                     user_count_composition_my_follow     bigint               DEFAULT NULL,
                                     user_count_composition_other         bigint               DEFAULT NULL,
                                     user_count_composition_video_detail  bigint               DEFAULT NULL,
                                     user_count_str                       bigint               DEFAULT NULL,
                                     watermelon                           bigint               DEFAULT NULL,
                                     welfare_donation_amount              bigint               DEFAULT NULL,
                                     status                               tinyint              DEFAULT NULL,
                                     stream_close_time                    timestamp            DEFAULT NULL,
                                     stream_id                            varchar(200)         DEFAULT NULL,
                                     stream_provider                      tinyint              DEFAULT NULL,
                                     sun_daily_icon_content               text                 DEFAULT NULL,
                                     challenge_info                       tinytext             DEFAULT NULL,
                                     danmaku_detail                       int                  DEFAULT NULL,
                                     hot_sentence_info                    text                 DEFAULT NULL,
                                     last_ping_time                       timestamp            DEFAULT NULL,
                                     room_like_count                      bigint               DEFAULT NULL,
                                     linker_map                           json                 DEFAULT NULL,
                                     web_count                            bigint               DEFAULT NULL,
                                     webcast_comment_tcs                  int                  DEFAULT NULL,
                                     with_aggregate_column                bool                 DEFAULT NULL,
                                     with_draw_something                  bool                 DEFAULT NULL,
                                     with_ktv                             bool                 DEFAULT NULL,
                                     with_linkmic                         bool                 DEFAULT NULL,
                                     PRIMARY KEY (now, platform, id)
                                    )
                                    '''.format(__ROOM_RECORD_TABLE_NAME)
  __SQL_DROP_ROOM_RECORD_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_RECORD_TABLE_NAME)
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
    return self.__ROOM_RECORD_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_RECORD_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_RECORD_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_RECORD_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_RECORD_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_RECORD_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## data.room.tags
##
## +-----------+------------------+------+-----+---------+-------+---------------------------+---------------------+
## | Field     | Type             | Null | Key | Default | Extra | Topology                  | Comment             |
## +-----------+------------------+------+-----+---------+-------+---------------------------+---------------------+
## | now       | timestamp(3)     | NO   | PRI |         |       | "$.data.room.create_time" | 当前时间戳           | 
## | platform  | varchar(20)      | NO   | PRI |         |       |           -               | 平台                 | 
## | room_id   | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"          | 直播间ID             |
## | tag_index | unsigned bigint  | NO   | PRI |         |       |           -               | 标签序号             | 
## | tag       | tinytext         |      |     | NULL    |       | "$.data.room.tags"        | 标签列表             |
## +-----------+------------------+------+-----+---------+-------+---------------------------+---------------------+
##
class RoomTagTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_TAG_TABLE_NAME       = "room_tag"
  __ROOM_TAG_TABLE_HEADER     = ['now', 'platform', 'room_id', 'tag_index', 'tag']
  __ROOM_TAG_TABLE_PRI_KEY    = ['tag_index']
  __TABLE_AUTO_INCREMENT      = ['tag_index']
  __ROOM_TAG_TABLE_TUPLE      = {item:None for item in __ROOM_TAG_TABLE_HEADER}
  __SQL_CREATE_ROOM_TAG_TABLE = '''
                                CREATE TABLE IF NOT EXISTS {} (
                                  now                     timestamp(3) NOT NULL,
                                  platform                varchar(20)  NOT NULL,
                                  room_id                 varchar(200) NOT NULL,
                                  tag_index               bigint       NOT NULL AUTO_INCREMENT,
                                  tag                     tinytext     DEFAULT NULL,
                                  PRIMARY KEY (tag_index)
                                )
                                '''.format(__ROOM_TAG_TABLE_NAME)
  __SQL_DROP_ROOM_TAG_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_TAG_TABLE_NAME)

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
    return self.__ROOM_TAG_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_TAG_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_TAG_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_TAG_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_TAG_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_TAG_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

'''
  TBD: no related data type of room_tab
'''
##
## data.room.top_fans
##
## +------------+-------------------+------+-----+---------+-------+---------------------------+---------------------+
## | Field      | Type              | Null | Key | Default | Extra | Topology                  | Comment             |
## +------------+-------------------+------+-----+---------+-------+---------------------------+---------------------+
## | now        | timestamp(3)      | NO   | PRI |         |       | "$.data.room.create_time" | 当前时间戳           | 
## | platform   | varchar(20)       | NO   | PRI |         |       |           -               | 平台                 | 
## | room_id    | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"          | 直播间ID             |
## | fans_index | unsigned bigint   | NO   | PRI |         |       |           -               | 粉丝序号             | 
## | top_fans   | TBD               |      |     | NULL    |       | "$.data.room.top_fans"    | 顶级粉丝             |
## +------------+-------------------+------+-----+---------+-------+---------------------------+---------------------+
##
class RoomTopFansTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_TOP_FANS_TABLE_NAME       = "room_top_fans"
  __ROOM_TOP_FANS_TABLE_HEADER     = ['now', 'platform', 'room_id', 'fans_index', 'top_fans']
  __ROOM_TOP_FANS_TABLE_PRI_KEY    = ['fans_index']
  __TABLE_AUTO_INCREMENT           = ['fans_index']
  __ROOM_TOP_FANS_TABLE_TUPLE      = {item:None for item in __ROOM_TOP_FANS_TABLE_HEADER}
  __SQL_CREATE_ROOM_TOP_FANS_TABLE = '''
                                     CREATE TABLE IF NOT EXISTS {} (
                                       now                     timestamp(3) NOT NULL,
                                       platform                varchar(20)  NOT NULL,
                                       room_id                 varchar(200) NOT NULL,
                                       fans_index              bigint       NOT NULL AUTO_INCREMENT,
                                       top_fans                TBD          DEFAULT NULL,
                                       PRIMARY KEY (fans_index),
                                       UNIQUE KEY unique_record (now, platform, room_id, top_fans)
                                     )
                                     '''.format(__ROOM_TOP_FANS_TABLE_NAME)
  __SQL_DROP_ROOM_TOP_FANS_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_TOP_FANS_TABLE_NAME)

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
    return self.__ROOM_TOP_FANS_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_TOP_FANS_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_TOP_FANS_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_TOP_FANS_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_TOP_FANS_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_TOP_FANS_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

'''
  TBD: no related data type of room_tab
'''
##
## data.room.upper_right_widget_data_list
##
## +-------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------+---------------------+
## | Field                         | Type              | Null | Key | Default | Extra | Topology                                   | Comment             |
## +-------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------+---------------------+
## | now                           | timestamp(3)      | NO   | PRI |         |       | "$.data.room.create_time"                  | 当前时间戳           | 
## | platform                      | varchar(20)       | NO   | PRI |         |       |           -                                | 平台                 | 
## | room_id                       | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                           | 直播间ID             |
## | upper_right_widget_data_index | unsigned bigint   | NO   | PRI |         |       |           -                                | 右上角小组件数据序号  | 
## | upper_right_widget_data       | TBD               |      |     | NULL    |       | "$.data.room.upper_right_widget_data_list" | 右上角小组件数据     |
## +-------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------+---------------------+
##
class RoomUpperRightWidgetDataTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_UPPER_RIGHT_WIDGET_DATA_TABLE_NAME       = "room_upper_right_widget_data"
  __ROOM_UPPER_RIGHT_WIDGET_DATA_TABLE_HEADER     = ['now', 'platform', 'room_id', 'upper_right_widget_data_index', 'upper_right_widget_data']
  __ROOM_UPPER_RIGHT_WIDGET_DATA_TABLE_PRI_KEY    = ['upper_right_widget_data_index']
  __TABLE_AUTO_INCREMENT                          = ['upper_right_widget_data_index']
  __ROOM_UPPER_RIGHT_WIDGET_DATA_TABLE_TUPLE      = {item:None for item in __ROOM_UPPER_RIGHT_WIDGET_DATA_TABLE_HEADER}
  __SQL_CREATE_ROOM_UPPER_RIGHT_WIDGET_DATA_TABLE = '''
                                                    CREATE TABLE IF NOT EXISTS {} (
                                                      now                            timestamp(3) NOT NULL,
                                                      platform                       varchar(20)  NOT NULL,
                                                      room_id                        varchar(200) NOT NULL,
                                                      upper_right_widget_data_index  bigint       NOT NULL AUTO_INCREMENT,
                                                      upper_right_widget_data        TBD          DEFAULT NULL,
                                                      PRIMARY KEY (upper_right_widget_data_index),
                                                      UNIQUE KEY unique_record (now, platform, room_id, upper_right_widget_data)
                                                    )
                                                    '''.format(__ROOM_UPPER_RIGHT_WIDGET_DATA_TABLE_NAME)
  __SQL_DROP_ROOM_UPPER_RIGHT_WIDGET_DATA_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_UPPER_RIGHT_WIDGET_DATA_TABLE_NAME)

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
    return self.__ROOM_UPPER_RIGHT_WIDGET_DATA_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_UPPER_RIGHT_WIDGET_DATA_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_UPPER_RIGHT_WIDGET_DATA_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_UPPER_RIGHT_WIDGET_DATA_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_UPPER_RIGHT_WIDGET_DATA_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_UPPER_RIGHT_WIDGET_DATA_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

'''
  TBD: no related data type of room_tab
'''
##
## data.room.vs_roles
##
## +---------------+------------------+------+-----+---------+-------+---------------------------+---------------------+
## | Field         | Type             | Null | Key | Default | Extra | Topology                  | Comment             |
## +---------------+------------------+------+-----+---------+-------+---------------------------+---------------------+
## | now           | timestamp(3)     | NO   | PRI |         |       | "$.data.room.create_time" | 当前时间戳           | 
## | platform      | varchar(20)      | NO   | PRI |         |       |           -               | 平台                 | 
## | room_id       | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"          | 直播间ID             |
## | vs_role_index | unsigned bigint  | NO   | PRI |         |       |           -               | VS角色序号          | 
## | vs_role       | TBD              |      |     | NULL    |       | "$.data.room.vs_roles"    | VS角色              |
## +---------------+------------------+------+-----+---------+-------+---------------------------+---------------------+
##
class RoomVsRoleTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_VS_ROLE_TABLE_NAME       = "room_vs_role"
  __ROOM_VS_ROLE_TABLE_HEADER     = ['now', 'platform', 'room_id', 'vs_role_index', 'vs_role']
  __ROOM_VS_ROLE_TABLE_PRI_KEY    = ['vs_role_index']
  __TABLE_AUTO_INCREMENT          = ['vs_role_index']
  __ROOM_VS_ROLE_TABLE_TUPLE      = {item:None for item in __ROOM_VS_ROLE_TABLE_HEADER}
  __SQL_CREATE_ROOM_VS_ROLE_TABLE = '''
                                    CREATE TABLE IF NOT EXISTS {} (
                                      now                            timestamp(3) NOT NULL,
                                      platform                       varchar(20)  NOT NULL,
                                      room_id                        varchar(200) NOT NULL,
                                      vs_role_index                  bigint       NOT NULL AUTO_INCREMENT,
                                      vs_role                        TBD          DEFAULT NULL,
                                      PRIMARY KEY (vs_role_index),
                                      UNIQUE KEY unique_record (now, platform, room_id, vs_role)
                                    )
                                    '''.format(__ROOM_VS_ROLE_TABLE_NAME)
  __SQL_DROP_ROOM_VS_ROLE_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_VS_ROLE_TABLE_NAME)

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
    return self.__ROOM_VS_ROLE_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_VS_ROLE_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_VS_ROLE_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_VS_ROLE_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_VS_ROLE_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_VS_ROLE_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

