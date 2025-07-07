# 数据库设计

[TOC]

## 概述

用户表
- 用户ID
- 用户名
- 用户密码
- 用户联系方式

## 数据类型存储原则
- 状态：unsigned tinyint, 占 1 个字节 0~255
- ID: varchar(200)
- 姓名昵称: varchar(50)
- 城市: varchar(100)
- 类型: unsigned tinyint, 占 1 个字节 0~255
- 模式: unsigned tinyint, 占 1 个字节 0~255
- 时间：timestamp
- URL: text，最大 64KB
- 星座: varchar(20)
- 等级: unsigned smallint, 占 2 个字节 0-65535
- 性别：unsigned tinyint, 占 1 个字节 0-255
- 签名：text, 最大 64KB
- 号码：varchar(20)
- 配置：text, 最大 64KB
- 参数：text, 最大 64KB
- 标题：tinytext, 最大 256 字节
- 标签：tinytext, 最大 256 字节
- 版本：varchar(20)

## 抖音
### 二次数据
作者信息表 - share_url
```shell
+----------------+--------------+------+-----+---------+-------+-----------------+------------------------------+
| Field          | Type         | Null | Key | Default | Extra | Comment         | Topology                     |
+----------------+--------------+------+-----+---------+-------+-----------------+------------------------------+
| owner_user_id  | varchar(200) | NO   | PRI | NULL    |       |                 | "$.data.room.owner_user_id"  |
| sec_user_id    | varchar(200) | YES  |     | NULL    |       |                 |                              |
| nickname       | varchar(50)  | YES  |     | NULL    |       |                 | "$.data.room.owner.nickname" |
| post_share_url | varchar(100) | YES  |     | NULL    |       |                 |
| live_share_url | varchar(100) | YES  |     | NULL    |       |                 |
| directory_name | varchar(100) | YES  |     | NULL    |       |                 |
| user_status    | varchar(100) | YES  |     | NULL    |       |                 |
| actived_count  | unsinged int | NO   |     | 0       |       |                 |
+----------------+--------------+------+-----+---------+-------+-----------------+-----------------------------+
```

喜爱的作者表 - favorite_owner
```shell
+---------------+------------------+------+-----+---------+-------+-----------------+-----------------------------+
| Field         | Type             | Null | Key | Default | Extra | Comment         | Topology                    |
+---------------+------------------+------+-----+---------+-------+-----------------+-----------------------------+
| owner_user_id | varchar(200)     | NO   | PRI | NULL    |       |                 | "$.data.room.owner_user_id" |
| platform      | varchar(20)      | YES  |     | NULL    |       |                 |                             |
| score         | unsigned tinyint | NO   |     | 0       |       |     0-100       |                             |
+---------------+------------------+------+-----+---------+-------+-----------------+-----------------------------+
```

直播记录表 - live_record
```shell
+----------------------------+------------------+------+-----+---------+-------+-----------------+---------------------------+
| Field                      | Type             | Null | Key | Default | Extra | Comment         | Topology                  |
+----------------------------+------------------+------+-----+---------+-------+-----------------+---------------------------+
| now                        | timestamp        | YES  |     |         |       | 当前时间戳       | "$.extra.now"             |
| platform                   | varchar(20)      |      |     | NULL    |       | 平台             |                          |
| room_id                    | varchar(200)     |      |     |         |       | 直播间ID         | "$.data.room.id"          |
| user_id                    | varchar(200)     |      |     | NULL    |       | 当前观众ID       | "$.data.user.id"          |
| start_time                 | timestamp        |      |     | 0       |       | 开始时间         | "$.data.room.start_time"  |
| finish_time                | timestamp        |      |     | 0       |       | 结束时间         | "$.data.room.finish_time" |
| status_code                | unsigned tinyint |      |     | 0       |       | 网络请求状态     | "$.status_code"           |
| status                     | unsigned tinyint |      |     | 0       |       | 直播状态         | "$.data.room.status"      |
+----------------------------+------------------+------+-----+---------+-------+-----------------+---------------------------+
```

直播间表 - live_room
```shell
+----------------------------+------------------+------+-----+---------+-------+-----------------+---------------------------+
| Field                      | Type             | Null | Key | Default | Extra | Comment         | Topology                  |
+----------------------------+------------------+------+-----+---------+-------+-----------------+---------------------------+
| now                        | timestamp        | YES  |     |         |       | 当前时间戳       | "$.extra.now"             |
| id                         | varchar(200)     |      |     |         |       | 直播间ID         | "$.data.room.id"          |
| create_time                | timestamp        |      |     |         |       | 直播间创建时间   | "$.data.room.create_time" | 
+----------------------------+------------------+------+-----+---------+-------+-----------------+---------------------------+
```

直播间 owner 表 - live_room_owner
```shell
+----------------------------+------------------+------+-----+---------+-------+-----------------+-----------------------------+
| Field                      | Type             | Null | Key | Default | Extra | Comment         | Topology                    |
+----------------------------+------------------+------+-----+---------+-------+-----------------+-----------------------------+
| now                        | timestamp        | YES  |     |         |       | 当前时间戳       | "$.extra.now"               |
| room_id                    | varchar(200)     |      |     |         |       | 直播间ID         | "$.data.room.id"            |
| owner_user_id              | varchar(200)     |      |     |         |       | 直播间主播ID     | "$.data.room.owner_user_id" |
+----------------------------+------------------+------+-----+---------+-------+-----------------+-----------------------------+
```

用户表 - user
```shell
+----------------------------+------------------+------+-----+---------+-------+-----------------+-----------------------------+
| Field                      | Type             | Null | Key | Default | Extra | Comment         | Topology                    |
+----------------------------+------------------+------+-----+---------+-------+-----------------+-----------------------------+
| id                         | varchar(200)     |      |     |         |       | 直播间ID         |  "$.data.user.id"           |
+----------------------------+------------------+------+-----+---------+-------+-----------------+-----------------------------+
```

===

短接触区域配置 - short_touch_area_config
```shell
+--------------------------------+------------------------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                                     | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------------------------------+------+-----+---------+-------+-----------------+
| elements                       | table - short_touch_area_config_elements | NULL |     |         |       |                 |
| forbidden_types_map            | json                                     | NULL |     |         |       |                 |
| strategy_feat_whitelist        | table - strategy_feat_whitelist          | NULL |     |         |       |                 |
| temp_state_condition_map       | table - temp_state_condition_map         | NULL |     |         |       |                 |
| temp_state_global_condition    | table - temp_state_global_condition      | NULL |     |         |       |                 |
| temp_state_strategy            | table - temp_state_strategy              | NULL |     |         |       |                 |
+--------------------------------+------------------------------------------+------+-----+---------+-------+-----------------+
```

直播间用户 ID 记录表 - live_room_user_id
```shell
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| Field                          | Type             | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| room_id                        | varchar(200)     |      |     |         |       |                 |
| start_time                     | timestamp        |      |     |         |       |                 |
| owner                          | bool             |      |     |         |       |                 |
| room_admin                     | bool             |      |     |         |       |                 |
| fans_group_admin               | bool             |      |     |         |       |                 |
| user_id                        | varchar(200)     |      |     |         |       |                 |
| user_open_id                   | varchar(200)     |      |     |         |       |                 |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
```

直播流质量表 live_stream
```shell
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| Field                          | Type             | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| quality                        | varchar(10)      |      |     |         |       |                 |
| url                            | text             |      |     |         |       |                 |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
```

直播间过滤词 - live_room_filter_word
```shell
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                 | Null | Key | Default | Extra | Comment         |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| filter_word                    | varchar(20)          |      |     |         |       |                 |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
```

分享音乐ID - live_room_sharing_music_id
```shell
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                 | Null | Key | Default | Extra | Comment         |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| sharing_music_id               | varchar(200)         |      |     |         |       | 分享音乐ID       |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
```

直播间标签 - live_room_tag
```shell
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                               | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| tag                            | tinytext                           |      |     |         |       |                 |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
```

策略壮举白名单 - strategy_feat_whitelist

```shell
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                               | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| strategy_feat_whiteitem        | tinytext                           |      |     |         |       |                 |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
```


临时状态全局条件 - temp_state_global_condition
```shell
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                               | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| allow_count                    | unsigned tinyint                   |      |     |         |       |                 |
| duration_gap                   | unsigned tinyint                   |      |     |         |       |                 |
| ignore_strategy_types          | unsigned tinyint                   |      |     |         |       |                 |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
```
### 原始数据

直播信息
```shell
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                               | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| data                           | table - data                       |      |     |         |       |                 |
| extra                          | table - extra                      |      |     |         |       |                 |
| status_code                    | tinyint                            |      |     |         |       |                 |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
```
===
数据 - data
```shell
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                               | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| room                           | table - room                       |      |     |         |       |                 |
| user                           | table - user                       |      |     |         |       |                 |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
```

额外数据表 - extra
```shell
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type              | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| now                                      | timestamp         |      |     |         |       |                    |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
```
===
直播间 room
```shell
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                               | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| AnchorABMap                    | json                               | YES  |     | NULL    |       |                 |
| acquaintance_status            | unsigned tinyint                   |      |     | 0       |       | 熟人状态         |
| admin_user_ids                 | table - live_room_user_id          |      |     |         |       | 管理员ID列表     |
| admin_user_open_ids            | table - live_room_user_id          |      |     |         |       | 管理员公开ID列表 |
| anchor_scheduled_time_text     | tinytext                           |      |     |         |       | 锚定时间文本     |
| anchor_share_text              | tinytext                           |      |     |         |       | 锚定分享文本     |
| anchor_tab_type                | unsigned tinyint                   |      |     |         |       | 锚定标签类型     |
| app_id                         | varchar(200)                       |      |     |         |       |                 |
| assist_label_list              | varchar(200)                       |      |     |         |       |                 |
| auth_city                      | varchar(100)                       |      |     |         |       | 认证城市         |
| auto_cover                     | unsigned tinyint                   |      |     |         |       | 自动封面         |
| base_category                  | unsigned tinyint                   |      |     |         |       | 基本类别         |
| book_end_time                  | timestamp                          |      |     |         |       | 预定结束时间     |
| book_time                      | timestamp                          |      |     |         |       |                 |
| business_live                  | unsigned tinyint                   |      |     |         |       | 商业直播         |
| category                       | unsigned tinyint                   |      |     |         |       | 类别            |
| cell_style                     | unsigned tinyint                   |      |     |         |       |                 |
| challenge_info                 | tinytext                           |      |     |         |       |                 |
| city_top_distance              | tinytext                           |      |     |         |       |                 |
| client_version                 | varchar(20)                        |      |     |         |       | 客户端版本号     |
| comment_box                    | table - room_comment_box           |      |     |         |       |                 |
| comment_name_mode              | unsigned tinyint                   |      |     |         |       |                 |
| common_label_list              | tinytext                           |      |     |         |       |                 |
| content_tag                    | tinytext                           |      |     |         |       |                 |
| cover                          | table - live_room_pic              |      |     |         |       | 封面-图片信息表  |
| create_time                    | timestamp                          |      |     |         |       | 创建时间         |
| danmaku_detail                 | unsigned int                       |      |     |         |       | 弹幕详情         |
| deco_list                      | table - deco_list                  |      |     |         |       | 装饰清单         |
| distance                       | varchar(100)                       |      |     |         |       | 距离            |
| distance_city                  | varchar(100)                       |      |     |         |       | 城市距离        |
| distance_km                    | varchar(100)                       |      |     |         |       | 公里距离        |
| dynamic_cover_dict             | json                               |      |     |         |       |                 |
| dynamic_cover_uri              | text                               |      |     |         |       |                 |
| enable_room_perspective        | bool                               |      |     |         |       |                 |
| extra                          | table - live_room_extra            |      |     |         |       | 额外直播信息表   |
| fans_group_admin_user_ids      | table - live_room_user_id          |      |     |         |       | 直播间用户ID表   |
| fans_group_admin_user_open_ids | table - live_room_user_id          |      |     |         |       | 直播间用户ID表   |
| fansclub_msg_style             | unsigned tinyint                   |      |     |         |       |                 |
| fcdn_appid                     | varchar(200)                       |      |     |         |       |                 |
| feed_room_label                | table - live_room_pic              |      |     |         |       | -> 图片信息表    |
| filter_words                   | table - live_room_filter_word      |      |     |         |       |                 |
| finish_reason                  | unsigned tinyint                   |      |     |         |       |                 |
| finish_time                    | timestamp                          |      |     |         |       |                 |
| finish_url                     | text                               |      |     |         |       |                 |
| follow_msg_style               | unsigned tinyint                   |      |     |         |       |                 |
| forum_extra_data               | tinytext                           |      |     |         |       |                 |
| game_room_type                 | unsigned tinyint                   |      |     |         |       | 游戏房间类型     |
| gift_msg_style                 | unsigned tinyint                   |      |     |         |       | 礼物消息风格     |
| group_id                       | varchar(200)                       |      |     |         |       |                 |
| group_source                   | unsigned tinyint                   |      |     |         |       |                 |
| guide_button                   | table - live_room_pic              |      |     |         |       | -> 图片信息表    |
| has_commerce_goods             | bool                               |      |     |         |       |                 |
| has_promotion_games            | unsigned tinyint                   |      |     |         |       |                 |
| highlight                      | bool                               |      |     |         |       |                 |
| hot_sentence_info              | text                               |      |     |         |       |                 |
| id                             | varchar(200)                       |      |     |         |       |                 |
| id_str                         | varchar(200)                       |      |     |         |       |                 |
| introduction                   | text                               |      |     |         |       |                 |
| is_need_check_list             | bool                               |      |     |         |       |                 |
| is_official_channel_room       | bool                               |      |     |         |       |                 |
| is_replay                      | bool                               |      |     |         |       |                 |
| is_show_inquiry_ball           | bool                               |      |     |         |       |                 |
| is_show_user_card_switch       | bool                               |      |     |         |       |                 |
| item_explicit_info             | text                               |      |     |         |       |                 |
| last_ping_time                 | timestamp                          |      |     |         |       |                 |
| layout                         | unsigned tinyint                   |      |     |         |       |                 |
| like_count                     | unsigned int                       |      |     |         |       |                 |
| linker_map                     | json                               |      |     |         |       |                 |
| linkmic_display_type           | unsigned tinyint                   |      |     |         |       |                 |
| linkmic_layout                 | unsigned tinyint                   |      |     |         |       |                 |
| live_distribution              |                                    |      |     |         |       |                 |
| live_id                        | varchar(200)                       |      |     |         |       |                 |
| live_platform_source           | tinytext                           |      |     |         |       |                 |
| live_room_mode                 | unsigned tinyint                   |      |     |         |       |                 |
| live_type_audio                | bool                               |      |     |         |       |                 |
| live_type_linkmic              | bool                               |      |     |         |       |                 |
| live_type_normal               | bool                               |      |     |         |       |                 |
| live_type_official             | bool                               |      |     |         |       |                 |
| live_type_sandbox              | bool                               |      |     |         |       |                 |
| live_type_screenshot           | bool                               |      |     |         |       |                 |
| live_type_third_party          | bool                               |      |     |         |       |                 |
| live_type_vs_live              | bool                               |      |     |         |       |                 |
| live_type_vs_premiere          | bool                               |      |     |         |       |                 |
| living_room_attrs              | table - live_room_attribute        |      |     |         |       | 直播间属性表     |
| location                       | varchar(100)                       |      |     |         |       |                 |
| lottery_finish_time            | timestamp                          |      |     |         |       |                 |
| luckymoney_num                 | unsigned int                       |      |     |         |       |                 |
| mosaic_status                  | unsigned tinyint                   |      |     |         |       |                 |
| mosaic_tip                     | tinytext                           |      |     |         |       |                 |
| official_channel_open_id       | varchar(200)                       |      |     |         |       |                 |
| official_channel_uid           | varchar(200)                       |      |     |         |       |                 |
| orientation                    | unsigned tinyint                   |      |     |         |       |                 |
| os_type                        | unsigned tinyint                   |      |     |         |       |                 |
| owner                          | table - live_owner                 |      |     |         |       | 主播信息表       |
| owner_device_id                | unsigned tinyint                   |      |     |         |       |                 |
| owner_open_id                  | varchar(200)                       |      |     |         |       |                 |
| owner_user_id                  | varchar(200)                       |      |     |         |       |                 |
| pack_meta                      | json                               |      |     |         |       |                 |
| paid_live_data                 | json                               |      |     |         |       |                 |
| popularity                     | unsigned int                       |      |     |         |       | 人气            |
| popularity_str                 | varchar(200)                       |      |     |         |       |                 |
| pre_enter_time                 | timestamp                          |      |     |         |       | 预入时间         |
| preview_copy                   | tinytext                           |      |     |         |       |                 |
| preview_flow_tag               | unsigned tinyint                   |      |     |         |       |                 |
| private_info                   | text                               |      |     |         |       |                 |
| ranklist_audience_type         | unsigned tinyint                   |      |     |         |       | 排名列表受众类型  |
| real_distance                  | varchar(100)                       |      |     |         |       | 实时距离         |
| redpacket_audience_auth        | unsigned tinyint                   |      |     |         |       |                 |
| relation_tag                   | tinytext                           |      |     |         |       |                 |
| replay                         | bool                               |      |     |         |       | 重播            |
| replay_location                | unsigned tinyint                   |      |     |         |       | 重播位置         |
| room_audit_status              | unsigned tinyint                   |      |     |         |       | 房间审核状态     |
| room_auth                      | json                               |      |     |         |       |                 |
| room_create_ab_param           | text                               |      |     |         |       |                 |
| room_layout                    | unsigned tinyint                   |      |     |         |       |                 |
| room_tabs                      | text                               |      |     |         |       |                 |
| room_tag                       | unsigned tinyint                   |      |     |         |       |                 |
| room_view_stats                | json                               |      |     |         |       |                 |
| screen_capture_sharing_title   | tinytext                           |      |     |         |       | 屏幕截图共享标题  |
| scroll_config                  | text                               |      |     |         |       |                 |
| search_id                      | varchar(200)                       |      |     |         |       |                 |
| sell_goods                     | bool                               |      |     |         |       | 卖货            |
| share_msg_style                | unsigned tinyint                   |      |     |         |       |                 |
| share_url                      | text                               |      |     |         |       |                 |
| sharing_music_id_list          | table - live_room_sharing_music_id |      |     |         |       |                 |
| short_title                    | tinytext                           |      |     |         |       |                 |
| short_touch_area_config        | table - short_touch_area_config    |      |     |         |       |                 |
| sofa_layout                    | unsigned tinyint                   |      |     |         |       |                 |
| stamps                         | tinytext                           |      |     |         |       |                 |
| start_time                     | timestamp                          |      |     |         |       |                 |
| stats                          | table - live_room_stats            |      |     |         |       |                 |
| status                         | unsigned tinyint                   |      |     |         |       |                 |
| stream_close_time              | timestamp                          |      |     |         |       |                 |
| stream_id                      | varchar(200)                       |      |     |         |       |                 |
| stream_id_str                  | varchar(200)                       |      |     |         |       |                 |
| stream_provider                | unsigned tinyint                   |      |     |         |       |                 |
| stream_url                     | table - stream_url                 |      |     |         |       |                 |
| sun_daily_icon_content         | tinytext                           |      |     |         |       |                 |
| tags                           | table - live_room_tag              |      |     |         |       |                 |
| title                          | tinytext                           |      |     |         |       |                 |
| title_recommend                | bool                               |      |     |         |       |                 |
| top_fans                       |                                    |      |     |         |       |                 |
| toutiao_cover_recommend_level  | unsigned smallint                  |      |     |         |       |                 |
| toutiao_title_recommend_level  | unsigned smallint                  |      |     |         |       |                 |
| upper_right_widget_data_list   |                                    |      |     |         |       | 右上角小部件数据列表 |
| use_filter                     | bool                               |      |     |         |       |                 |
| user_count                     | unsigned int                       |      |     |         |       | 观众数量         |
| user_share_text                | text                               |      |     |         |       |                 |
| vertical_cover_uri             | text                               |      |     |         |       |                 |
| vid                            | varchar(200)                       |      |     |         |       |                 |
| video_feed_tag                 | tinytext                           |      |     |         |       |                 |
| visibility_range               | unsigned smallint                  |      |     |         |       |                 |
| vs_main_replay_id              | varchar(200)                       |      |     |         |       |                 |
| vs_roles                       |                                    |      |     |         |       |                 |
| wait_copy                      | tinytext                           |      |     |         |       |                 |
| web_count                      | unsigned smallint                  |      |     |         |       |                 |
| webcast_comment_tcs            | unsigned int                       |      |     |         |       |                 |
| webcast_sdk_version            | varchar(20)                        |      |     |         |       |                 |
| with_aggregate_column          | bool                               |      |     |         |       |                 |
| with_draw_something            | bool                               |      |     |         |       |                 |
| with_ktv                       | bool                               |      |     |         |       |                 |
| with_linkmic                   | bool                               |      |     |         |       |                 |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
```

用户表 user
```shell
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type              | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| adversary_authorization_info             | unsigned tinyint  |      |     |         |       |                    |
| adversary_user_status                    | unsigned tinyint  |      |     |         |       |                    |
| age_range                                | unsigned tinyint  |      |     |         |       | 年纪范围            |
| allow_be_located                         | bool              |      |     |         |       | 允许被定位          |
| allow_find_by_contacts                   | bool              |      |     |         |       | 允许通过通讯录被发现 |
| allow_others_download_video              | bool              |      |     |         |       | 允许其它人下载作品   |
| allow_others_download_when_sharing_video | bool              |      |     |         |       | 允许被分享人下载作品 |
| allow_share_show_profile                 | bool              |      |     |         |       | 允许分享显示个人资料 |
| allow_show_in_gossip                     | bool              |      |     |         |       | 允许在八卦中显示     |
| allow_show_my_action                     | bool              |      |     |         |       | 允许显示我的行为     |
| allow_strange_comment                    | bool              |      |     |         |       |                    |
| allow_unfollower_comment                 | bool              |      |     |         |       |                    |
| allow_use_linkmic                        | bool              |      |     |         |       |                    |
| authorization_info                       | unsigned tinyint  |      |     |         |       |                    |
| badge_image_list                         |                   |      |     |         |       | 头像，查看图片信息表 |
| badge_image_list_v2                      |                   |      |     |         |       | 头像，查看图片信息表 |
| bg_img_url                               | text              |      |     |         |       |                    |
| birthday                                 | timestamp         |      |     |         |       |                    |
| birthday_description                     | text              |      |     |         |       |                    |
| birthday_valid                           | bool              |      |     |         |       |                    |
| block_status                             | unsigned tinyint  |      |     |         |       |                    |
| city                                     | varchar(100)      |      |     |         |       | 城市               |
| comment_restrict                         | unsigned tinyint  |      |     |         |       | 限制评论            |
| commerce_webcast_config_ids              |                   |      |     |         |       |                    |
| constellation                            | varchar(20)       |      |     |         |       | 星座               |
| consume_diamond_level                    | unsigned smallint |      |     |         |       | 消费钻石等级        |
| create_time                              | timestamp         |      |     |         |       | 创建时间            |
| desensitized_nickname                    | varchar(50)       |      |     |         |       | 去敏感化的昵称      |
| disable_ichat                            | unsigned tinyint  |      |     |         |       | 禁止聊天            |
| display_id                               | varchar(200)      |      |     |         |       | 显示ID             |
| enable_ichat_img                         | unsigned tinyint  |      |     |         |       |                    |
| exp                                      | unsigned int      |      |     |         |       |                    |
| experience                               | unsigned int      |      |     |         |       |                    |
| fan_ticket_count                         | unsigned int      |      |     |         |       | 粉丝票数量          |
| fold_stranger_chat                       | bool              |      |     |         |       | 折叠陌生人聊天      |
| follow_status                            | unsigned tinyint  |      |     |         |       | 关注状态           |
| gender                                   | unsigned tinyint  |      |     |         |       | 性别               |
| hotsoon_verified                         | bool              |      |     |         |       |                    |
| hotsoon_verified_reason                  | text              |      |     |         |       |                    |
| ichat_restrict_type                      | unsigned tinyint  |      |     |         |       |                    |
| id                                       | varchar(200)      |      |     |         |       |                    |
| id_str                                   | varchar(200)      |      |     |         |       |                    |
| income_share_percent                     | unsigned tinyint  |      |     |         |       |                    |
| is_anonymous                             | bool              |      |     |         |       |                    |
| is_follower                              | bool              |      |     |         |       |                    |
| is_following                             | bool              |      |     |         |       |                    |
| level                                    | unsigned smallint |      |     |         |       | 等级               |
| link_mic_stats                           | unsigned smallint |      |     |         |       | 连麦统计           |
| location_city                            | varchar(100)      |      |     |         |       | 定位城市           |
| media_badge_image_list                   |                   |      |     |         |       |                   |
| modify_time                              | timestamp         |      |     |         |       |                   |
| mystery_man                              | unsigned tinyint  |      |     |         |       | 神秘人             |
| need_profile_guide                       | bool              |      |     |         |       |                   |
| new_real_time_icons                      | list              |      |     |         |       |                   |
| nickname                                 | varchar(50)       |      |     |         |       | 昵称              |
| pay_score                                | unsigned int      |      |     |         |       |                   |
| pay_scores                               | unsigned int      |      |     |         |       |                   |
| public_area_oper_freq                    | unsigned smallint |      |     |         |       |                   |
| push_comment_status                      | bool              |      |     |         |       |                   |
| push_digg                                | bool              |      |     |         |       |                   |
| push_follow                              | bool              |      |     |         |       |                   |
| push_friend_action                       | bool              |      |     |         |       |                   |
| push_ichat                               | bool              |      |     |         |       |                   |
| push_status                              | bool              |      |     |         |       |                   |
| push_video_post                          | bool              |      |     |         |       |                   |
| push_video_recommend                     | bool              |      |     |         |       |                   |
| real_time_icons                          |                   |      |     |         |       |                   |
| remark_name                              | varchar(50)       |      |     |         |       |                   |
| sec_uid                                  | varchar(200)      |      |     |         |       |                   |
| secret                                   | unsigned tinyint  |      |     |         |       |                   |
| share_qrcode_uri                         | text              |      |     |         |       |                   |
| short_id                                 | varchar(200)      |      |     |         |       |                   |
| signature                                | text              |      |     |         |       |                   |
| special_id                               | varchar(200)      |      |     |         |       |                   |
| status                                   | unsigned tinyint  |      |     |         |       | 主播状态         |
| telephone                                | varchar(20)       |      |     |         |       | 手机号码         |
| ticket_count                             | unsigned int      |      |     |         |       |                 |
| top_fans                                 |                   |      |     |         |       |                 |
| top_vip_no                               | unsigned int      |      |     |         |       |                 |
| total_recharge_diamond_count             | unsigned int      |      |     |         |       | 钻石充值总数     |
| user_canceled                            | bool              |      |     |         |       | 用户已取消       |
| user_open_id                             | varchar(200)      |      |     |         |       |                 |
| user_role                                | unsigned tinyint  |      |     |         |       |                 |
| verified                                 | bool              |      |     |         |       |                 |
| verified_content                         | tinytext          |      |     |         |       |                 |
| verified_mobile                          | bool              |      |     |         |       |                 |
| verified_reason                          | tinytext          |      |     |         |       |                 |
| watch_duration_month                     | unsigned smallint |      |     |         |       |                 |
| web_rid                                  | varchar(200)      |      |     |         |       |                 |
| webcast_uid                              | varchar(200)      |      |     |         |       |                 |
| with_car_management_permission           | bool              |      |     |         |       |                 |
| with_commerce_permission                 | bool              |      |     |         |       |                 |
| with_fusion_shop_entry                   | bool              |      |     |         |       |                 |
+------------------------------------------+-------------------+------+-----+---------+-------+-----------------+
```
===

直播间评论区 - room_comment_box
```shell
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type              | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| placeholder                              | tinytext          |      |     |         |       |                    |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
```

图片信息表 live_room_pic
```shell
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                 | Null | Key | Default | Extra | Comment         |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| avg_color                      | varchar(7)           |      |     |         |       | 平均颜色         | 
| content                        | json                 |      |     |         |       |                 |
| flex_setting_list              |                      |      |     |         |       | 灵活设置列表     |
| height                         | unsigned int         |      |     |         |       | 高度             |
| image_type                     | unsigned tinyint     |      |     |         |       | 图片类型         |
| is_animated                    | bool                 |      |     |         |       |                 |
| open_web_url                   | text                 |      |     |         |       |                 |
| text_setting_list              |                      |      |     |         |       | 文本设置列表     |
| uri                            | text                 |      |     |         |       |                 |
| url_list                       | table - live_pic_url |      |     |         |       | 直播图片资源表    |
| width                          | unsigned int         |      |     |         |       | 宽度             |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
```

直播间封面 - cover
```shell
参考 - live_room_pic
```

装饰清单 - deco_list
```shell
+--------------------------------+--------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                     | Null | Key | Default | Extra | Comment         |
+--------------------------------+--------------------------+------+-----+---------+-------+-----------------+
|                                | table - audit_text_color |      |     |         |       |                 |
+--------------------------------+--------------------------+------+-----+---------+-------+-----------------+
```

额外直播信息表 - room_extra
```shell
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                 | Null | Key | Default | Extra | Comment         |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| create_scene                   | tinytext             |      |     |         |       | 创建场景         |
| facial_unrecognised            | unsigned tinyint     |      |     |         |       | 面部无法识别     |
| geo_block                      | unsigned tinyint     |      |     |         |       | 地理封锁         |
| is_sandbox                     | bool                 |      |     |         |       |                 |
| is_virtual_anchor              | bool                 |      |     |         |       |                 |
| limit_appid                    | varchar(200)         |      |     |         |       |                 |
| limit_strategy                 | unsigned tinyint     |      |     |         |       |                 |
| realtime_playback_qualities    | table - live_quality |      |     |         |       | 直播质量表       |
| realtime_playback_shift        | unsigned tinyint     |      |     |         |       |                 |
| realtime_playback_start_shift  | unsigned tinyint     |      |     |         |       |                 |
| realtime_replay_enabled        | bool                 |      |     |         |       |                 |
| vr_type                        | unsigned tinyint     |      |     |         |       |                 |
| vs_type                        | unsigned tinyint     |      |     |         |       |                 |
| xigua_uid                      | varchar(200)         |      |     |         |       |                 |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
```

打赏直播间标签 - feed_room_label
```shell
参考 - live_room_pic
```

指引按钮 - guide_button
```shell
参考 - live_room_pic
```

直播间属性表 live_room_attrs
```shell
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                 | Null | Key | Default | Extra | Comment         |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| admin_flag                     | unsigned tinyint     |      |     |         |       | 管理员标识       |
| rank                           | unsigned smallint    |      |     |         |       | 排名            |
| room_id                        | varchar(200)         | PRI  |     |         |       |                 |
| room_id_str                    | varchar(200)         |      |     |         |       |                 |
| silence_flag                   | unsigned tinyint     |      |     |         |       | 沉默标识         |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
```

直播主播表 room_owner
```shell
+------------------------------------------+-------------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                    | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-------------------------+------+-----+---------+-------+--------------------+
| adversary_authorization_info             | unsigned tinyint        |      |     |         |       |                    |
| adversary_user_status                    | unsigned tinyint        |      |     |         |       |                    |
| age_range                                | unsigned tinyint        |      |     |         |       | 年纪范围            |
| allow_be_located                         | bool                    |      |     |         |       | 允许被定位          |
| allow_find_by_contacts                   | bool                    |      |     |         |       | 允许通过通讯录被发现 |
| allow_others_download_video              | bool                    |      |     |         |       | 允许其它人下载作品   |
| allow_others_download_when_sharing_video | bool                    |      |     |         |       | 允许被分享人下载作品 |
| allow_share_show_profile                 | bool                    |      |     |         |       | 允许分享显示个人资料 |
| allow_show_in_gossip                     | bool                    |      |     |         |       | 允许在八卦中显示    |
| allow_show_my_action                     | bool                    |      |     |         |       | 允许显示我的行为    |
| allow_strange_comment                    | bool                    |      |     |         |       |                    |
| allow_unfollower_comment                 | bool                    |      |     |         |       |                    |
| allow_use_linkmic                        | bool                    |      |     |         |       |                    |
| authorization_info                       | unsigned tinyint        |      |     |         |       |                    |
| avatar_large                             |                         |      |     |         |       | 头像，查看图片信息表 |
| avatar_medium                            |                         |      |     |         |       | 头像，查看图片信息表 |
| avatar_thumb                             |                         |      |     |         |       | 头像，查看图片信息表 |
| badge_image_list                         |                         |      |     |         |       | 头像，查看图片信息表 |
| badge_image_list_v2                      |                         |      |     |         |       | 头像，查看图片信息表 |
| bg_img_url                               | text                    |      |     |         |       |                    |
| birthday                                 | timestamp               |      |     |         |       |                    |
| birthday_description                     | text                    |      |     |         |       |                    |
| birthday_valid                           | bool                    |      |     |         |       |                    |
| block_status                             | unsigned tinyint        |      |     |         |       |                    |
| city                                     | varchar(100)            |      |     |         |       | 城市               |
| comment_restrict                         | unsigned tinyint        |      |     |         |       | 限制评论           |
| commerce_webcast_config_ids              |                         |      |     |         |       |                    |
| constellation                            | varchar(20)             |      |     |         |       | 星座               |
| consume_diamond_level                    | unsigned smallint       |      |     |         |       | 消费钻石等级        |
| create_time                              | timestamp               |      |     |         |       | 创建时间            |
| desensitized_nickname                    | varchar(50)             |      |     |         |       | 去敏感化的昵称      |
| disable_ichat                            | unsigned tinyint        |      |     |         |       | 禁止聊天            |
| display_id                               | varchar(200)            |      |     |         |       | 显示ID             |
| enable_ichat_img                         | unsigned tinyint        |      |     |         |       |                    |
| exp                                      | unsigned int            |      |     |         |       |                    |
| experience                               | unsigned int            |      |     |         |       |                    |
| fan_ticket_count                         | unsigned int            |      |     |         |       | 粉丝票数量          |
| fans_club                                |                         |      |     |         |       | 粉丝俱乐部          |
| fans_group_info                          | json                    |      |     |         |       | 粉丝群信息          |
| fold_stranger_chat                       | bool                    |      |     |         |       | 折叠陌生人聊天      |
| follow_info                              |                         |      |     |         |       | 关注信息            |
| follow_status                            | unsigned tinyint        |      |     |         |       | 关注状态            |
| gender                                   | unsigned tinyint        |      |     |         |       | 性别               |
| hotsoon_verified                         | bool                    |      |     |         |       |                 |
| hotsoon_verified_reason                  | text                    |      |     |         |       |                 |
| ichat_restrict_type                      | unsigned tinyint        |      |     |         |       |                 |
| id                                       | varchar(200)            |      |     |         |       |                 |
| id_str                                   | varchar(200)            |      |     |         |       |                 |
| income_share_percent                     | unsigned tinyint        |      |     |         |       |                 |
| is_anonymous                             | bool                    |      |     |         |       |                 |
| is_follower                              | bool                    |      |     |         |       |                 |
| is_following                             | bool                    |      |     |         |       |                 |
| j_accredit_info                          | json                    |      |     |         |       | 认证信息         |
| level                                    | unsigned smallint       |      |     |         |       | 等级            |
| link_mic_stats                           | unsigned smallint       |      |     |         |       | 连麦统计         |
| location_city                            | varchar(100)            |      |     |         |       | 定位城市         |
| media_badge_image_list                   |                         |      |     |         |       |                 |
| modify_time                              | timestamp               |      |     |         |       |                 |
| mystery_man                              | unsigned tinyint        |      |     |         |       | 神秘人           |
| need_profile_guide                       | bool                    |      |     |         |       |                 |
| new_real_time_icons                      | list                    |      |     |         |       |                 |
| nickname                                 | varchar(50)             |      |     |         |       | 昵称            |
| own_room                                 |                         |      |     |         |       |                 |
| pay_grade                                |                         |      |     |         |       |                 |
| pay_score                                | unsigned int            |      |     |         |       |                 |
| pay_scores                               | unsigned int            |      |     |         |       |                 |
| public_area_oper_freq                    | unsigned smallint       |      |     |         |       |                 |
| push_comment_status                      | bool                    |      |     |         |       |                 |
| push_digg                                | bool                    |      |     |         |       |                 |
| push_follow                              | bool                    |      |     |         |       |                 |
| push_friend_action                       | bool                    |      |     |         |       |                 |
| push_ichat                               | bool                    |      |     |         |       |                 |
| push_status                              | bool                    |      |     |         |       |                 |
| push_video_post                          | bool                    |      |     |         |       |                 |
| push_video_recommend                     | bool                    |      |     |         |       |                 |
| real_time_icons                          |                         |      |     |         |       |                 |
| remark_name                              | varchar(50)             |      |     |         |       |                 |
| sec_uid                                  | varchar(200)            |      |     |         |       |                 |
| secret                                   | unsigned tinyint        |      |     |         |       |                 |
| share_qrcode_uri                         | text                    |      |     |         |       |                 |
| short_id                                 | varchar(200)            |      |     |         |       |                 |
| signature                                | text                    |      |     |         |       |                 |
| special_id                               | varchar(200)            |      |     |         |       |                 |
| status                                   | unsigned tinyint        |      |     |         |       | 主播状态         |
| subscribe                                |                         |      |     |         |       | 订阅            |
| telephone                                | varchar(20)             |      |     |         |       | 手机号码         |
| ticket_count                             | unsigned int            |      |     |         |       |                 |
| top_fans                                 |                         |      |     |         |       |                 |
| top_vip_no                               | unsigned int            |      |     |         |       |                 |
| total_recharge_diamond_count             | unsigned int            |      |     |         |       | 钻石充值总数     |
| user_attr                                | table - user_attr       |      |     |         |       |                 |
| user_canceled                            | bool                    |      |     |         |       | 用户已取消       |
| user_dress_info                          | table - user_dress_info |      |     |         |       |                 |
| user_open_id                             | varchar(200)            |      |     |         |       |                 |
| user_role                                | unsigned tinyint        |      |     |         |       |                 |
| verified                                 | bool                    |      |     |         |       |                 |
| verified_content                         | tinytext                |      |     |         |       |                 |
| verified_mobile                          | bool                    |      |     |         |       |                 |
| verified_reason                          | tinytext                |      |     |         |       |                 |
| watch_duration_month                     | unsigned smallint       |      |     |         |       |                 |
| web_rid                                  | varchar(200)            |      |     |         |       |                 |
| webcast_uid                              | varchar(200)            |      |     |         |       |                 |
| with_car_management_permission           | bool                    |      |     |         |       |                 |
| with_commerce_permission                 | bool                    |      |     |         |       |                 |
| with_fusion_shop_entry                   | bool                    |      |     |         |       |                 |
+------------------------------------------+-------------------------+------+-----+---------+-------+-----------------+
```

打包元数据 - pack_meta
```shell
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                 | Null | Key | Default | Extra | Comment         |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| cluster                        | varchar(20)          |      |     |         |       |                 |
| dc                             | varchar(20)          |      |     |         |       |                 |
| env                            | varchar(20)          |      |     |         |       |                 |
| extras                         | json                 |      |     |         |       |                 |
| scene                          | tinytedt             |      |     |         |       |                 |
| trace_id                       | varchar(200)         |      |     |         |       |                 |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
```

支付直播数据 - paid_live_data
```shell
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                 | Null | Key | Default | Extra | Comment         |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| anchor_right                   | unsigned tinyint     |      |     |         |       | 锚定右侧         |
| delivery                       | unsigned tinyint     |      |     |         |       | 快递             |
| duration                       | timestamp            |      |     |         |       | 持续时间         |
| max_preview_duration           | timestamp            |      |     |         |       | 最大预览持续时间  |
| need_delivery_notice           | bool                 |      |     |         |       | 需要送货通知     |
| paid_type                      | unsigned tinyint     |      |     |         |       | 付费类型         |
| pay_ab_type                    | unsigned tinyint     |      |     |         |       |                 |
| privilege_info                 | json                 |      |     |         |       | 特权信息         |
| privilege_info_map             | json                 |      |     |         |       | 特权信息图       |
| view_right                     | unsigned tinyint     |      |     |         |       | 向右查看         |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
```

room_auth
```shell
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                 | Null | Key | Default | Extra | Comment         |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| AIClone                        |                      |      |     |         |       |                 |
| AdminCommentWall               |                      |      |     |         |       |                 |
| AnchorAudioChat                |                      |      |     |         |       |                 |
| AnchorColdMessageTiled         |                      |      |     |         |       |                 |
| AnchorHotMessageAggregated     |                      |      |     |         |       |                 |
| AnchorMission                  |                      |      |     |         |       |                 |
| AudioChat                      |                      |      |     |         |       |                 |
| AudioChatTotext                |                      |      |     |         |       |                 |
| Banner                         |                      |      |     |         |       |                 |
| BulletStyle                    |                      |      |     |         |       |                 |
| CanSellTicket                  |                      |      |     |         |       |                 |
| CastScreen                     |                      |      |     |         |       |                 |
| CastScreenExplicit             |                      |      |     |         |       |                 |
| Chat                           |                      |      |     |         |       |                 |
| ChatDispatch                   |                      |      |     |         |       |                 |
| ChatDynamicSlideSpeed          |                      |      |     |         |       |                 |
| ChatDynamicSlideSpeedAnchor    |                      |      |     |         |       |                 |
| ChatGuideEmoji                 |                      |      |     |         |       |                 |
| ChatGuideImage                 |                      |      |     |         |       |                 |
| ChatIdentity                   |                      |      |     |         |       |                 |
| ChatMention                    |                      |      |     |         |       |                 |
| ChatMentionV2                  |                      |      |     |         |       |                 |
| ChatOperate                    |                      |      |     |         |       |                 |
| ChatReply                      |                      |      |     |         |       |                 |
| ClearEntranceOption            |                      |      |     |         |       |                 |
| Collect                        |                      |      |     |         |       |                 |
| CommentWall                    |                      |      |     |         |       |                 |
| CommerceCard                   |                      |      |     |         |       |                 |
| CommerceComponent              |                      |      |     |         |       |                 |
| CommonCard                     |                      |      |     |         |       |                 |
| CountType                      |                      |      |     |         |       |                 |
| Danmaku                        |                      |      |     |         |       |                 |
| DanmakuDefault                 |                      |      |     |         |       |                 |
| Denounce                       |                      |      |     |         |       |                 |
| Digg                           |                      |      |     |         |       |                 |
| Dislike                        |                      |      |     |         |       |                 |
| DonationSticker                |                      |      |     |         |       |                 |
| DouPlus                        |                      |      |     |         |       |                 |
| DouPlusPopularityGem           |                      |      |     |         |       |                 |
| DownloadVideo                  |                      |      |     |         |       |                 |
| EcomFansClub                   |                      |      |     |         |       |                 |
| EmojiOutside                   |                      |      |     |         |       |                 |
| EnhancedTouch                  |                      |      |     |         |       |                 |
| EnterEffects                   |                      |      |     |         |       |                 |
| ExpandScreen                   |                      |      |     |         |       |                 |
| FansClub                       |                      |      |     |         |       |                 |
| FansClubBlessing               |                      |      |     |         |       |                 |
| FansClubDeclaration            |                      |      |     |         |       |                 |
| FansClubLetter                 |                      |      |     |         |       |                 |
| FansClubNotice                 |                      |      |     |         |       |                 |
| FansGroup                      |                      |      |     |         |       |                 |
| FeaturedPublicScreen           |                      |      |     |         |       |                 |
| FirstFeedHistChat              |                      |      |     |         |       |                 |
| FixedChat                      |                      |      |     |         |       |                 |
| FrequentlyChat                 |                      |      |     |         |       |                 |
| FusionEmoji                    |                      |      |     |         |       |                 |
| GamePointsPlaying              |                      |      |     |         |       |                 |
| Gift                           |                      |      |     |         |       |                 |
| GiftAnchorMt                   |                      |      |     |         |       |                 |
| GiftVote                       |                      |      |     |         |       |                 |
| Highlights                     |                      |      |     |         |       |                 |
| HostTeam                       |                      |      |     |         |       |                 |
| HostTeamChannel                |                      |      |     |         |       |                 |
| HotChatTray                    |                      |      |     |         |       |                 |
| HourRank                       |                      |      |     |         |       |                 |
| ImHeatValue                    |                      |      |     |         |       |                 |
| IndustryService                |                      |      |     |         |       |                 |
| InteractionGift                |                      |      |     |         |       |                 |
| InteractiveComponent           |                      |      |     |         |       |                 |
| ItemShare                      |                      |      |     |         |       |                 |
| KtvOrderSong                   |                      |      |     |         |       |                 |
| Landscape                      |                      |      |     |         |       |                 |
| LandscapeChat                  |                      |      |     |         |       |                 |
| LandscapeChatDynamicSlideSpeed |                      |      |     |         |       |                 |
| LandscapeGift                  |                      |      |     |         |       |                 |
| LandscapeScreenCapture         |                      |      |     |         |       |                 |
| LandscapeScreenRecording       |                      |      |     |         |       |                 |
| LandscapeScreenShare           |                      |      |     |         |       |                 |
| Like                           |                      |      |     |         |       |                 |
| LinkmicGuestLike               |                      |      |     |         |       |                 |
| LongPressOption                |                      |      |     |         |       |                 |
| LongTouch                      |                      |      |     |         |       |                 |
| LuckMoney                      |                      |      |     |         |       |                 |
| MarkUser                       |                      |      |     |         |       |                 |
| MediaHistoryMessage            |                      |      |     |         |       |                 |
| MediaLinkmic                   |                      |      |     |         |       |                 |
| MessageDispatch                |                      |      |     |         |       |                 |
| MessageGift                    |                      |      |     |         |       |                 |
| MissionCenter                  |                      |      |     |         |       |                 |
| MoreAnchor                     |                      |      |     |         |       |                 |
| MoreHistChat                   |                      |      |     |         |       |                 |
| MultiplierPlayback             |                      |      |     |         |       |                 |
| MyLiveEntrance                 |                      |      |     |         |       |                 |
| OnlyTa                         |                      |      |     |         |       |                 |
| PCPlay                         |                      |      |     |         |       |                 |
| POI                            |                      |      |     |         |       |                 |
| PadPlay                        |                      |      |     |         |       |                 |
| PanelECService                 |                      |      |     |         |       |                 |
| PlayerRankList                 |                      |      |     |         |       |                 |
| Poster                         |                      |      |     |         |       |                 |
| PosterCache                    |                      |      |     |         |       |                 |
| PreviewChatExpose              |                      |      |     |         |       |                 |
| PreviewHotCommentSwitch        |                      |      |     |         |       |                 |
| ProjectionBtn                  |                      |      |     |         |       |                 |
| Props                          |                      |      |     |         |       |                 |
| PublicScreen                   |                      |      |     |         |       |                 |
| QuizGamePointsPlaying          |                      |      |     |         |       |                 |
| RecordScreen                   |                      |      |     |         |       |                 |
| RoomChannel                    |                      |      |     |         |       |                 |
| RoomChatLikeDisplay            |                      |      |     |         |       |                 |
| RoomChatOperatePanel           |                      |      |     |         |       |                 |
| RoomContributor                |                      |      |     |         |       |                 |
| RoomWidget                     |                      |      |     |         |       |                 |
| ScreenBottomInfo               |                      |      |     |         |       |                 |
| ScreenProjectionBarrage        |                      |      |     |         |       |                 |
| Seek                           |                      |      |     |         |       |                 |
| Selection                      |                      |      |     |         |       |                 |
| SelectionAlbum                 |                      |      |     |         |       |                 |
| Share                          |                      |      |     |         |       |                 |
| ShortTouch                     |                      |      |     |         |       |                 |
| ShortTouchTempState            |                      |      |     |         |       |                 |
| ShowGamePlugin                 |                      |      |     |         |       |                 |
| ShowQualification              |                      |      |     |         |       |                 |
| SmallWindowDisplay             |                      |      |     |         |       |                 |
| SmallWindowPlayer              |                      |      |     |         |       |                 |
| StickyMessage                  |                      |      |     |         |       |                 |
| StreamAdaptation               |                      |      |     |         |       |                 |
| StrokeUpDownGuide              |                      |      |     |         |       |                 |
| SubscribeCardPackage           |                      |      |     |         |       |                 |
| Teleprompter                   |                      |      |     |         |       |                 |
| TextGift                       |                      |      |     |         |       |                 |
| TimedShutdown                  |                      |      |     |         |       |                 |
| ToolbarBubble                  |                      |      |     |         |       |                 |
| Topic                          |                      |      |     |         |       |                 |
| TypingCommentState             |                      |      |     |         |       |                 |
| UgcVSReplayDelete              |                      |      |     |         |       |                 |
| UgcVsReplayVisibility          |                      |      |     |         |       |                 |
| UpRightStatsFloatingLayer      |                      |      |     |         |       |                 |
| UseHostInfo                    |                      |      |     |         |       |                 |
| UserCard                       |                      |      |     |         |       |                 |
| UserCorner                     |                      |      |     |         |       |                 |
| VSGift                         |                      |      |     |         |       |                 |
| VSRank                         |                      |      |     |         |       |                 |
| VSTopic                        |                      |      |     |         |       |                 |
| VerticalRank                   |                      |      |     |         |       |                 |
| VerticalScreenShare            |                      |      |     |         |       |                 |
| VideoAmplificationType         |                      |      |     |         |       |                 |
| VideoShare                     |                      |      |     |         |       |                 |
| VsCommentBar                   |                      |      |     |         |       |                 |
| VsDouPlus                      |                      |      |     |         |       |                 |
| VsExtensionEnableFollow        |                      |      |     |         |       |                 |
| VsFansClub                     |                      |      |     |         |       |                 |
| VsWelcomeDanmaku               |                      |      |     |         |       |                 |
| WordAssociation                |                      |      |     |         |       |                 |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
```

room_view_stats
```shell
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                 | Null | Key | Default | Extra | Comment         |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| display_long                   | tinytext             |      |     |         |       |                 |
| display_long_anchor            | tinytext             |      |     |         |       |                 |
| display_middle                 | tinytext             |      |     |         |       |                 |
| display_middle_anchor          | tinytext             |      |     |         |       |                 |
| display_short                  | tinytext             |      |     |         |       |                 |
| display_short_anchor           | tinytext             |      |     |         |       |                 |
| display_type                   | unsigned tinyint     |      |     |         |       |                 |
| display_value                  | unsigned int         |      |     |         |       |                 |
| display_version                | varchar(20)          |      |     |         |       |                 |
| incremental                    | bool                 |      |     |         |       |                 |
| is_hidden                      | bool                 |      |     |         |       |                 |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
```

short_touch_area_config
```shell
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                 | Null | Key | Default | Extra | Comment         |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| elements                       |                      |      |     |         |       |                 |
| forbidden_types_map            |                      |      |     |         |       |                 |
| strategy_feat_whitelist        |                      |      |     |         |       |                 |
| temp_state_condition_map       |                      |      |     |         |       |                 |
| temp_state_global_condition    |                      |      |     |         |       |                 |
| temp_state_strategy            |                      |      |     |         |       |                 |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
```

直播间状态 - room_stats
```shell
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                               | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| comment_count                  | unsigned bigint                    |      |     |         |       | 评论数量         |
| digg_count                     |                                    |      |     |         |       |                 |
| dou_plus_promotion             |                                    |      |     |         |       | 抖+促销          |
| enter_count                    | unsigned int                       |      |     |         |       | 进入数量         |
| fan_ticket                     | unsigned bigint                    |      |     |         |       | 粉丝票           |
| follow_count                   | unsigned int                       |      |     |         |       | 关注数量         |
| gift_uv_count                  | unsigned int                       |      |     |         |       | 关注数量         |
| id                             | varchar(200)                       |      |     |         |       | 直播间ID         |
| id_str                         | varchar(200)                       |      |     |         |       | 直播间ID         |
| like_count                     | unsigned int                       |      |     |         |       | 点赞数量         |
| money                          | unsigned int                       |      |     |         |       | 金钱             |
| total_user                     | unsigned int                       |      |     |         |       | 用户数量         |
| total_user_desp                |
| total_user_str                 | varchar(100)                       |      |     |         |       | 用户数量         |
| up_right_stats_str             |                                                                   | 右上角状态条     |
| up_right_stats_str_complete    |                                                                   | 右上角状态条完成  |
| user_count_composition         |                                                                   | 用户数量组成     |
| user_count_str                 | varchar(100)                       |      |     |         |       | 用户数量         |
| watermelon                     | 
| welfare_donation_amount        | unsigned int                       |      |     |         |       | 福利捐赠金额     |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
```

直播流信息表 - stream_url
```shell
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type              | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| candidate_resolution                     |                   |      |     |         |       | 候选分辨率          |
| complete_push_urls                       |                   |      |     |         |       |                    |
| default_resolution                       | varchar(20)       |      |     |         |       | 默认分辨率          |
| extra                                    | json              |      |     |         |       |                    |
| flv_pull_url                             |                   |      |     |         |       |                    |
| flv_pull_url_params                      |                   |      |     |         |       |                    |
| hls_pull_url                             | text              |      |     |         |       |                    |
| hls_pull_url_map                         |                   |      |     |         |       |                    |
| hls_pull_url_params                      | text              |      |     |         |       |                    |
| id                                       | varchar(200)      |      |     |         |       |                    |
| id_str                                   | varchar(200)      |      |     |         |       |                    |
| live_core_sdk_data                       |                   |      |     |         |       |                    |
| provider                                 | unsigned tinyint  |      |     |         |       |                    |
| pull_datas                               | json              |      |     |         |       |                    |
| push_datas                               | json              |      |     |         |       |                    |
| push_stream_type                         | unsigned tinyint  |      |     |         |       | 推流类型            |
| push_urls                                |                   |      |     |         |       |                    |
| resolution_name                          |                   |      |     |         |       | 分辨率名称          |
| rtmp_pull_url                            | text              |      |     |         |       |                    |
| rtmp_pull_url_params                     | text              |      |     |         |       |                    |
| rtmp_push_url                            | text              |      |     |         |       |                    |
| rtmp_push_url_params                     | text              |      |     |         |       |                    |
| stream_control_type                      | unsigned tinyint  |      |     |         |       |                    |
| stream_orientation                       | unsigned tinyint  |      |     |         |       |                    |
| vr_type                                  | unsigned tinyint  |      |     |         |       |                    |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
```
===
审核文本颜色 - audit_text_color
```shell
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type              | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| content
| h
| id
| image
| input_rect
| kind
| max_length
| nine_patch_image
| reservation
| status
| sub_type
| text_color
| text_image_adjustable_end_position
| text_image_adjustable_start_position
| text_size
| text_special_effects
| type
| w
| x
| y
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
```

直播间打赏标签内容 - content
```shell
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type              | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| alternative_text
| font_color
| level
| name
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
```

badge_image_list
```shell
+------------------------------------------+-----------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                  | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-----------------------+------+-----+---------+-------+--------------------+
|                                          | table - live_room_pic |      |     |         |       |                    |
+------------------------------------------+-----------------------+------+-----+---------+-------+--------------------+
+-----
```

badge_image_list_v2
```shell
+------------------------------------------+-----------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                  | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-----------------------+------+-----+---------+-------+--------------------+
|                                          | table - live_room_pic |      |     |         |       |                    |
+------------------------------------------+-----------------------+------+-----+---------+-------+--------------------+
```

粉丝俱乐部 - fans_club
```shell
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                   | Null | Key | Default | Extra | Comment            |
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| data                                     | table - fans_club_data |      |     |         |       |                    |
| prefer_data                              | json                   |      |     |         |       |                    |
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
```

粉丝群信息 - fans_group_info
```shell
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                   | Null | Key | Default | Extra | Comment            |
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| list_fans_group_url                      | text                   |      |     |         |       |                    |
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
```

关注信息 - follow_info
```shell
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                   | Null | Key | Default | Extra | Comment            |
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| follow_status                            | tinyint                |      |     |         |       |                    |
| follower_count
| follower_count_str
| following_count
| following_count_str
| invalid_follow_status
| push_status
| remark_name
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
```

j_accredit_info
```shell
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                   | Null | Key | Default | Extra | Comment            |
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| JAccreditAdvance
| JAccreditBasic
| JAccreditContent
| JAccreditLive
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
```
own_room
```shell
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                   | Null | Key | Default | Extra | Comment            |
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| room_ids
| room_ids_display
| room_ids_str
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
```

支付等级 - pay_grade
```shell
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                   | Null | Key | Default | Extra | Comment            |
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| grade_banner
| grade_describe
| grade_describe_shining
| grade_icon_list
| level
| name
| new_im_icon_with_level
| new_live_icon
| next_diamond
| next_name
| next_privileges
| now_diamond
| pay_diamond_bak
| score
| screen_chat_type
| this_grade_max_diamond
| this_grade_min_diamond
| total_diamond_count
| upgrade_need_consume
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
```

订阅 - subscribe
```shell
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                   | Null | Key | Default | Extra | Comment            |
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| buy_type
| identity_type
| is_member
| level
| open
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
```

user_attr
```shell
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                   | Null | Key | Default | Extra | Comment            |
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| admin_privileges
| is_admin
| is_muted
| is_super_admin
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
```

user_dress_info
```shell
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                   | Null | Key | Default | Extra | Comment            |
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| dress_own_ids
| dress_wear_ids
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
```

elements
```shell
+------------------------------------------+------------------------------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                                     | Null | Key | Default | Extra | Comment            |
+------------------------------------------+------------------------------------------+------+-----+---------+-------+--------------------+
| '1'                                      | table - short_touch_area_config_elements |      |     |         |       |                    |
| ...                                      | table - short_touch_area_config_elements |      |     |         |       |                    |
+------------------------------------------+------------------------------------------+------+-----+---------+-------+--------------------+
```

临时状态条件图 - temp_state_condition_map
```shell
+------------------------------------------+------------------------------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                                     | Null | Key | Default | Extra | Comment            |
+------------------------------------------+------------------------------------------+------+-----+---------+-------+--------------------+
| '1'                                      | table - temp_state_condition             |      |     |         |       |                    |
| ...                                      | table - temp_state_condition             |      |     |         |       |                    |
+------------------------------------------+------------------------------------------+------+-----+---------+-------+--------------------+
```

temp_state_global_condition
```shell
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                               | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| allow_count
| duration_gap
| ignore_strategy_types
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
```

临时状态策略 - temp_state_strategy
```shell
+------------------------------------------+------------------------------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                                     | Null | Key | Default | Extra | Comment            |
+------------------------------------------+------------------------------------------+------+-----+---------+-------+--------------------+
| '1'                                      | table - temp_state_condition             |      |     |         |       |                    |
| ...                                      | table - temp_state_condition             |      |     |         |       |                    |
+------------------------------------------+------------------------------------------+------+-----+---------+-------+--------------------+
```

user_count_composition
```shell
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                               | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| city                           | unsigned tinyint                   |      |     |         |       |                 |
| my_follow                      | unsigned tinyint                   |      |     |         |       |                 |
| other                          | unsigned tinyint                   |      |     |         |       |                 |
| video_detail                   | unsigned tinyint                   |      |     |         |       |                 |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
```

直播流额外信息表 - stream_url_extra
```shell
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type              | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| anchor_interact_profile                  |                   |      |     |         |       |                    |
| audience_interact_profile                |                   |      |     |         |       |                    |
| bframe_enable                            |                   |      |     |         |       |                    |
| bitrate_adapt_strategy                   |                   |      |     |         |       |                    |
| bytevc1_enable                           |                   |      |     |         |       |                    |
| default_bitrate                          |                   |      |     |         |       |                    |
| fps                                      |                   |      |     |         |       |                    |
| gop_sec                                  |                   |      |     |         |       |                    |
| h265_enable                              | bool              |      |     |         |       |                    |
| hardware_encode                          | bool              |      |     |         |       |                    |
| height                                   | unsigned smallint |      |     |         |       |                    |
| max_bitrate                              |                   |      |     |         |       |                    |
| min_bitrate                              |                   |      |     |         |       |                    |
| roi                                      | bool              |      |     |         |       |                    |
| sw_roi                                   | bool              |      |     |         |       |                    |
| video_profile                            |                   |      |     |         |       |                    |
| width                                    | unsigned smallint |      |     |         |       |                    |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
```

flv_pull_url
```shell
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type              | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| FULL_HD1
| HD1
| SD1
| SD2
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
```

flv_pull_url_params
```shell
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type              | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| HD1
| SD1
| SD2
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
```

hls_pull_url_map
```shell
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type              | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| FULL_HD1
| HD1
| SD1
| SD2
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
```

live_core_sdk_data
```shell
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type              | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| pull_data
| size
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
```

resolution_name
```shell
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type              | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| FULL_HD1
| HD1
| ORIGIN
| SD1
| SD2
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
```
===

预定 - reservation
```shell
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| Field                          | Type             | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| anchor_id
| anchor_open_id
| appointment_id
| btn_color
| btn_rect
| end_time
| is_reserved
| room_id
| start_time
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
```

粉丝俱乐部数据 - fans_club_data

```shell
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| Field                          | Type             | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| anchor_id
| anchor_open_id
| available_gift_ids
| badge
| badge_type
| club_name
| guard_expired_time
| level
| user_fans_club_status
| user_guard_status
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
```

短接触区域配置元素 - short_touch_area_config_elements
```shell
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                               | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| priority                       | unsigned tinyint                   |      |     |         |       |                 |
| type                           | unsigned tinyint                   |      |     |         |       |                 |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
```

temp_state_condition
```shell
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                               | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| minimum_gap                    |                                    |      |     |         |       |                 |
| type                           | table                              |      |     |         |       |                 |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
```

temp_state_strategy_item
```shell
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                               | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| short_touch_type               | unsigned tinyint                   |      |     |         |       |                 |
| strategy_map                   |                                    |      |     |         |       |                 |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
```

pull_data
```shell
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| Field                          | Type             | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| Flv
| Hls
| codec
| compensatory_data
| hls_data_unencrypted
| kind
| options
| stream_data
| version
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
```

live_core_sdk_pull_data_options
```shell
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| Field                          | Type             | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| default_quality
| qualities
| vpass_default
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
```
===
fans_club_badge
```shell
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| Field                          | Type             | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| icons                          |                  |      |     |         |       |                 |
| title                          |                  |      |     |         |       |                 |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
```

temp_state_condition_map_type
```shell
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| Field                          | Type             | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| priority                       |                  |      |     |         |       |                 |
| strategy_type                  |                  |      |     |         |       |                 |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
```

strategy_map
```shell
+--------------------------------+---------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                      | Null | Key | Default | Extra | Comment         |
+--------------------------------+---------------------------+------+-----+---------+-------+-----------------+
| '1'                            | table - strategy_map_item |      |     |         |       |                 |
| ...                            | table - strategy_map_item |      |     |         |       |                 |
+--------------------------------+---------------------------+------+-----+---------+-------+-----------------+
```

strategy_map_item
```shell
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| Field                          | Type             | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| duration                       |                  |      |     |         |       |                 |
| strategy_method                |
| strategy_map                   |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
```

default_quality
```shell
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| Field                          | Type             | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| additional_content             |                  |      |     |         |       |                 |
| disable                        |
| fps                            |
| level
| name
| resolution
| sdk_key
| v_bit_rate
| v_codec
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
```

additional_content
```shell
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| Field                          | Type             | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| disable                        |
| fps                            |
| level
| name
| resolution
| sdk_key
| v_bit_rate
| v_codec
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
```
