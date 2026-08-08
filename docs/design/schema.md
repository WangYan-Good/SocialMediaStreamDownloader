# 数据库 Schema

> 当前生产受管 schema 以 `backend/src/database/orm/models/` 和
> `backend/src/database/migration/versions/` 为准。本文后续的大字段设计说明保留作结构背景，
> 不再作为运行时自动建表来源。

当前 Alembic 基线 `0001_initial_schema` 管理 12 张表：

- 基础表：`share_url`、`favorite_owner`、`live_record`
- 主实体表：`room_base`、`room_owner_v2`、`user`
- 扩展表：`room_stats`、`room_admin_user_id`、`room_admin_user_open_id`、
  `room_deco`、`fans_group_admin_user_id`、`fans_group_admin_user_open_id`

字段、类型、unsigned、默认值、主键顺序、索引、约束、引擎、字符集和排序规则均由 ORM
元数据严格校验。未受管表只产生警告，不会被自动删除。生产运行时不自动建表或迁移。

## 一、历史结构分析

### 1.1 数据结构概览

```
external_info.data.room
├── 简单字段 (标量)：约 95 个
├── 对象字段 (嵌套)：约 25 个
└── 数组字段 (列表)：约 44 个
```

**字段总数：** 164 个第一层字段

### 1.2 当前问题

| 问题 | 描述 | 影响 |
|------|------|------|
| 表数量过多 | 120+ 张表 | 维护成本高，DBA 管理困难 |
| 查询复杂 | 完整查询需 JOIN 20+ 表 | 查询性能差，响应时间长 |
| 写入性能差 | 插入需写入 30+ 表 | 事务复杂，容易失败 |
| 空值率高 | room_auth 表 100+ 字段，实际使用约 20 个 | 存储空间浪费 |
| 嵌套层级深 | 最深达 5 层 (owner.fans_club.data.badge.icons) | 查询复杂度高 |

### 1.3 字段使用频率分析

| 频率 | 字段示例 | 占比 | 建议存储方式 |
|------|---------|------|-------------|
| 高频 | id, status, owner_user_id, title | 20% | 独立列 |
| 中频 | cover, stats, stream_url | 30% | JSON 或独立表 |
| 低频 | deco_list, filter_words, tags | 50% | JSON 数组 |

---

## 二、优化方案设计

### 2.1 设计原则

```
┌─────────────────────────────────────────────────────────────┐
│                    优化原则                                  │
├─────────────────────────────────────────────────────────────┤
│ 1. 高频查询字段 → 独立列存储                                 │
│ 2. 低频查询对象 → JSON 存储                                  │
│ 3. 需关联查询数组 → 独立表                                   │
│ 4. 布尔标志位 → 位图存储                                     │
│ 5. 时间戳 → 统一 BIGINT (毫秒)                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 表结构规划

```
┌─────────────────────────────────────────────────────────────┐
│                    核心表 (2 张)                             │
├─────────────────────────────────────────────────────────────┤
│ 1. room_base          - 直播间基础信息 (70 字段 + 35 JSON)   │
│ 2. room_owner_v2      - 主播信息 (80 字段 + 18 JSON)         │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                    扩展表 (16 张)                                    │
├──────────────────────────────────────────────────────────────────────┤
│ 3. room_admin_user                      - 管理员表                   │
│ 3-1. room_admin_user_open_id            - 管理员开放 ID 表           │
│ 4. room_deco                            - 装饰表                     │
│ 4-1. room_fans_group_admin_user_id      - 粉丝群管理员 ID 表         │
│ 4-2. room_fans_group_admin_user_open_id - 粉丝群管理员开放 ID 表     │
│ 5. room_stats                           - 统计数据表                 │
│ 6. room_stream                          - 流信息表                   │
└──────────────────────────────────────────────────────────────────────┘

**当前 Alembic 受管总计：12 张表。** 下方 21 张表是早期规划数字，不代表当前迁移边界。

**表分类统计：**
- 基础表：3 张 (share_url, favorite_owner, live_record)
- 核心表：2 张 (room_base, room_owner_v2)
- 扩展表：16 张
```

### 2.3 字段映射规则

| YAML 字段类型 | 优化后存储方式 | 示例 |
|-------------|--------------|------|
| 标量 (数字/字符串/布尔) | 独立列 | id, status, title |
| 嵌套对象 (不常查询) | JSON 列 | cover_data, extra_data |
| 嵌套对象 (常查询) | 独立表 + 外键 | room_owner_v2 |
| 数组 (需关联查询) | 独立表 | admin_user_ids, deco_list |
| 数组 (仅展示) | JSON 数组 | filter_words, tags |

**JSON 字段统计：**
- `room_base`: 20 JSON 对象字段 + 15 JSON 数组字段 = **35 JSON 字段**
- `room_owner_v2`: **18 JSON 字段**

---

## 三、详细表结构 Schema

### 3.1 基础表

#### 1. 分享链接表 - share_url

```sql
CREATE TABLE IF NOT EXISTS `share_url` (
    `owner_user_id`  VARCHAR(200) NOT NULL COMMENT '账号作者 ID',
    `sec_user_id`    VARCHAR(200) DEFAULT NULL COMMENT '安全用户 ID',
    `nickname`       VARCHAR(50)  DEFAULT NULL COMMENT '昵称',
    `post_share_url` VARCHAR(100) DEFAULT NULL COMMENT '主页分享链接',
    `live_share_url` VARCHAR(100) DEFAULT NULL COMMENT '直播分享链接',
    `directory_name` VARCHAR(100) DEFAULT NULL COMMENT '文件夹名称',
    `user_status`    VARCHAR(100) DEFAULT NULL COMMENT '用户状态',
    `actived_count`  UNSIGNED INT NOT NULL DEFAULT 0 COMMENT '访问次数',
    PRIMARY KEY (`owner_user_id`),
    INDEX `idx_nickname` (`nickname`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分享链接表';
```

```shell
+----------------+--------------+------+-----+---------+-------+------------------------------+--------------+
| Field          | Type         | Null | Key | Default | Extra | Topology                     | Comment      |
+----------------+--------------+------+-----+---------+-------+------------------------------+--------------+
| owner_user_id  | varchar(200) | NO   | PRI | NULL    |       | "$.data.room.owner_user_id"  | 账号作者 ID   |
| sec_user_id    | varchar(200) | YES  |     | NULL    |       |                              | 安全用户 ID   |
| nickname       | varchar(50)  | YES  |     | NULL    |       | "$.data.room.owner.nickname" | 昵称         |
| post_share_url | varchar(100) | YES  |     | NULL    |       |             -                | 主页分享链接 |
| live_share_url | varchar(100) | YES  |     | NULL    |       |             -                | 直播分享链接 |
| directory_name | varchar(100) | YES  |     | NULL    |       |             -                | 文件夹名称   |
| user_status    | varchar(100) | YES  |     | NULL    |       |             -                | 用户状态     |
| actived_count  | unsinged int | NO   |     | 0       |       |             -                | 访问次数     |
+----------------+--------------+------+-----+---------+-------+------------------------------+--------------+
```

#### 2. 喜爱的作者表 - favorite_owner

```sql
CREATE TABLE IF NOT EXISTS `favorite_owner` (
    `owner_user_id` VARCHAR(200)     NOT NULL COMMENT '账号作者 ID',
    `platform`      VARCHAR(20)      NOT NULL COMMENT '平台',
    `score`         UNSIGNED TINYINT NOT NULL DEFAULT 0 COMMENT '评分 0-100',
    PRIMARY KEY (`owner_user_id`, `platform`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='喜爱的作者表';
```

```shell
+---------------+------------------+------+-----+---------+-------+-----------------------------+------------+
| Field         | Type             | Null | Key | Default | Extra | Topology                    | Comment    |
+---------------+------------------+------+-----+---------+-------+-----------------------------+------------+
| owner_user_id | varchar(200)     | NO   | PRI | NULL    |       | "$.data.room.owner_user_id" | 账号作者 ID |
| platform      | varchar(20)      | NO   |     | NULL    |       |             -               | 平台       |
| score         | unsigned tinyint | NO   |     | 0       |       |             -               | 评分 0-100 |
+---------------+------------------+------+-----+---------+-------+-----------------------------+------------+
```

#### 3. 直播记录表 - live_record

```sql
CREATE TABLE IF NOT EXISTS `live_record` (
    `now`         TIMESTAMP(3)      NOT NULL COMMENT '当前时间戳',
    `platform`    VARCHAR(20)       NOT NULL COMMENT '平台',
    `room_id`     VARCHAR(200)      NOT NULL COMMENT '直播间 ID',
    `owner_user_id` VARCHAR(200)    NOT NULL COMMENT '当前主播 ID',
    `user_id`     VARCHAR(200)      DEFAULT NULL COMMENT '当前观众 ID',
    `start_time`  TIMESTAMP         DEFAULT NULL COMMENT '开始时间',
    `finish_time` TIMESTAMP         DEFAULT NULL COMMENT '结束时间',
    `status_code` TINYINT           DEFAULT NULL COMMENT '网络请求状态',
    PRIMARY KEY (`now`, `platform`, `owner_user_id`, `room_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='直播记录表';
```

```shell
+-------------+-------------------+------+-----+---------+-------+---------------------------+--------------+
| Field       | Type              | Null | Key | Default | Extra | Topology                  | Comment      |
+-------------+-------------------+------+-----+---------+-------+---------------------------+--------------+
| now         | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"             | 当前时间戳   |
| platform    | varchar(20)       | NO   | PRI |         |       |           -               | 平台         |
| room_id     | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"          | 直播间 ID    |
| owner_user_id | varchar(200)    | NO   | PRI |         |       | "$.data.room.owner_user_id" | 当前主播 ID |
| user_id     | varchar(200)      |      |     | NULL    |       | "$.data.user.id"          | 当前观众 ID  |
| start_time  | timestamp         |      |     | NULL    |       | "$.data.room.start_time"  | 开始时间     |
| finish_time | timestamp         |      |     | NULL    |       | "$.data.room.finish_time" | 结束时间     |
| status_code | tinyint           |      |     | NULL    |       | "$.status_code"           | 网络请求状态 |
+-------------+-------------------+------+-----+---------+-------+---------------------------+--------------+
```

### 3.2 核心表

#### 4. 直播间基础表 - room_base

```sql
CREATE TABLE IF NOT EXISTS `room_base` (
    `now`                              TIMESTAMP(3)      NOT NULL,
    `id`                               VARCHAR(200)      NOT NULL,
    `id_str`                           VARCHAR(200)      DEFAULT NULL,

    `title`                            TINYTEXT          DEFAULT NULL,
    `introduction`                     TEXT              DEFAULT NULL,
    `share_url`                        TEXT              DEFAULT NULL,
    `user_share_text`                  TEXT              DEFAULT NULL,
    `anchor_share_text`                TEXT              DEFAULT NULL,

    `create_time`                      BIGINT            DEFAULT NULL,
    `start_time`                       BIGINT            DEFAULT NULL,
    `finish_time`                      BIGINT            DEFAULT NULL,
    `stream_close_time`                BIGINT            DEFAULT NULL,

    `status`                           TINYINT  UNSIGNED DEFAULT 0,
    `finish_reason`                    SMALLINT UNSIGNED DEFAULT NULL,
    `acquaintance_status`              TINYINT  UNSIGNED DEFAULT 0,

    `owner_user_id`                    BIGINT            DEFAULT NULL,

    `app_id`                           BIGINT            DEFAULT NULL,
    `base_category`                    BIGINT            DEFAULT 0,
    `category`                         BIGINT            DEFAULT 0,
    `client_version`                   BIGINT            DEFAULT NULL,
    `orientation`                      TINYINT UNSIGNED DEFAULT 0,
    `layout`                           TINYINT UNSIGNED DEFAULT 0,
    `room_layout`                      TINYINT UNSIGNED DEFAULT 0,
    `room_tag`                         TINYINT UNSIGNED DEFAULT 0,
    `live_room_mode`                   TINYINT UNSIGNED DEFAULT 0,
    `live_platform_source`             TINYTEXT          DEFAULT NULL,
    `cell_style`                       TINYINT UNSIGNED DEFAULT 0,
    `os_type`                          TINYINT UNSIGNED DEFAULT 0,
    `owner_device_id`                  BIGINT            DEFAULT NULL,
    `owner_open_id`                    VARCHAR(200)      DEFAULT NULL,
    `visibility_range`                 TINYINT UNSIGNED DEFAULT 0,
    `webcast_sdk_version`              VARCHAR(20)       DEFAULT NULL,

    `stream_id`                        BIGINT            DEFAULT NULL,
    `stream_id_str`                    VARCHAR(200)      DEFAULT NULL,
    `live_id`                          BIGINT            DEFAULT NULL,
    `stream_provider`                  TINYINT UNSIGNED DEFAULT 0,

    `like_count`                       BIGINT            DEFAULT 0,
    `user_count`                       INT UNSIGNED      DEFAULT 0,
    `popularity`                       INT UNSIGNED      DEFAULT 0,
    `danmaku_detail`                   INT UNSIGNED      DEFAULT 0,
    `web_count`                        BIGINT            DEFAULT 0,
    `webcast_comment_tcs`              INT UNSIGNED      DEFAULT 0,
    `gift_msg_style`                   TINYINT UNSIGNED DEFAULT 0,
    `share_msg_style`                  TINYINT UNSIGNED DEFAULT 0,
    `follow_msg_style`                 TINYINT UNSIGNED DEFAULT 0,
    `fansclub_msg_style`               TINYINT UNSIGNED DEFAULT 0,

    `sell_goods`                       BOOL              DEFAULT FALSE,
    `has_commerce_goods`               BOOL              DEFAULT FALSE,
    `is_replay`                        BOOL              DEFAULT FALSE,
    `replay`                           BOOL              DEFAULT FALSE,
    `highlight`                        BOOL              DEFAULT FALSE,
    `use_filter`                       BOOL              DEFAULT FALSE,
    `title_recommend`                  BOOL              DEFAULT FALSE,
    `enable_room_perspective`          BOOL              DEFAULT FALSE,
    `with_aggregate_column`            BOOL              DEFAULT FALSE,
    `with_draw_something`              BOOL              DEFAULT FALSE,
    `with_ktv`                         BOOL              DEFAULT FALSE,
    `with_linkmic`                     BOOL              DEFAULT FALSE,

    `live_type_normal`                 BOOL              DEFAULT FALSE,
    `live_type_audio`                  BOOL              DEFAULT FALSE,
    `live_type_linkmic`                BOOL              DEFAULT FALSE,
    `live_type_official`               BOOL              DEFAULT FALSE,
    `live_type_sandbox`                BOOL              DEFAULT FALSE,
    `live_type_screenshot`             BOOL              DEFAULT FALSE,
    `live_type_third_party`            BOOL              DEFAULT FALSE,
    `live_type_vs_live`                BOOL              DEFAULT FALSE,
    `live_type_vs_premiere`            BOOL              DEFAULT FALSE,

    `linkmic_layout`                   TINYINT UNSIGNED DEFAULT 0,

    `auth_city`                        VARCHAR(100)      DEFAULT NULL,
    `location`                         VARCHAR(100)      DEFAULT NULL,
    `distance`                         VARCHAR(100)      DEFAULT NULL,
    `distance_city`                    VARCHAR(100)      DEFAULT NULL,
    `distance_km`                      VARCHAR(100)      DEFAULT NULL,
    `real_distance`                    VARCHAR(100)      DEFAULT NULL,
    `dynamic_cover_uri`                TEXT              DEFAULT NULL,
    `vertical_cover_uri`               TEXT              DEFAULT NULL,
    `finish_url`                       TEXT              DEFAULT NULL,
    `forum_extra_data`                 TEXT              DEFAULT NULL,
    `private_info`                     TEXT              DEFAULT NULL,
    `item_explicit_info`               TEXT              DEFAULT NULL,
    `hot_sentence_info`                TEXT              DEFAULT NULL,
    `relation_tag`                     TINYTEXT          DEFAULT NULL,
    `stamps`                           TINYTEXT          DEFAULT NULL,
    `room_create_ab_param`             TEXT              DEFAULT NULL,
    `scroll_config`                    TEXT              DEFAULT NULL,
    `mosaic_tip`                       TINYTEXT          DEFAULT NULL,
    `popularity_str`                   VARCHAR(50)       DEFAULT NULL,
    `preview_copy`                     TINYTEXT          DEFAULT NULL,
    `wait_copy`                        TINYTEXT          DEFAULT NULL,
    `short_title`                      TINYTEXT          DEFAULT NULL,
    `video_feed_tag`                   TINYTEXT          DEFAULT NULL,
    `screen_capture_sharing_title`     TINYTEXT          DEFAULT NULL,
    `common_label_list`                TINYTEXT          DEFAULT NULL,
    `content_tag`                      TINYTEXT          DEFAULT NULL,
    `challenge_info`                   TINYTEXT          DEFAULT NULL,
    `anchor_scheduled_time_text`       TEXT              DEFAULT NULL,
    `anchor_tab_type`                  TINYINT UNSIGNED DEFAULT 0,
    `comment_name_mode`                TINYINT UNSIGNED DEFAULT 0,
    `fcdn_appid`                       BIGINT            DEFAULT NULL,
    `game_room_type`                   TINYINT UNSIGNED DEFAULT 0,
    `official_channel_open_id`         VARCHAR(200)      DEFAULT NULL,
    `official_channel_uid`             BIGINT            DEFAULT NULL,
    `search_id`                        BIGINT            DEFAULT NULL,
    `group_id`                         BIGINT            DEFAULT NULL,
    `group_source`                     TINYINT UNSIGNED DEFAULT 0,
    `sofa_layout`                      TINYINT UNSIGNED DEFAULT 0,
    `sun_daily_icon_content`           TINYTEXT          DEFAULT NULL,
    `ranklist_audience_type`           TINYINT UNSIGNED DEFAULT 0,
    `redpacket_audience_auth`          TINYINT UNSIGNED DEFAULT 0,
    `toutiao_cover_recommend_level`    TINYINT UNSIGNED DEFAULT 0,
    `toutiao_title_recommend_level`    TINYINT UNSIGNED DEFAULT 0,
    `preview_flow_tag`                 TINYINT UNSIGNED DEFAULT 0,
    `replay_location`                  TINYINT UNSIGNED DEFAULT 0,
    `room_audit_status`                TINYINT UNSIGNED DEFAULT 0,
    `mosaic_status`                    TINYINT UNSIGNED DEFAULT 0,
    `lottery_finish_time`              BIGINT            DEFAULT NULL,
    `luckymoney_num`                   INT UNSIGNED      DEFAULT 0,
    `has_promotion_games`              TINYINT UNSIGNED DEFAULT 0,
    `is_need_check_list`               BOOL              DEFAULT FALSE,
    `is_official_channel_room`         BOOL              DEFAULT FALSE,
    `is_show_inquiry_ball`             BOOL              DEFAULT FALSE,
    `is_show_user_card_switch`         BOOL              DEFAULT FALSE,
    `auto_cover`                       TINYINT UNSIGNED DEFAULT 0,
    `business_live`                    TINYINT UNSIGNED DEFAULT 0,
    `book_time`                        BIGINT            DEFAULT NULL,
    `book_end_time`                    BIGINT            DEFAULT NULL,
    `linkmic_display_type`             TINYINT UNSIGNED DEFAULT 0,
    `vid`                              VARCHAR(200)      DEFAULT NULL,
    `vs_main_replay_id`                VARCHAR(200)      DEFAULT NULL,
    `last_ping_time`                   BIGINT            DEFAULT NULL,
    `pre_enter_time`                   BIGINT            DEFAULT NULL,
    `city_top_distance`                TINYTEXT          DEFAULT NULL,

    `cover`                            JSON              DEFAULT NULL,
    `content_label`                    JSON              DEFAULT NULL,
    `feed_room_label`                  JSON              DEFAULT NULL,
    `guide_button`                     JSON              DEFAULT NULL,
    `comment_box`                      JSON              DEFAULT NULL,
    `link_mic`                         JSON              DEFAULT NULL,
    `living_room_attrs`                JSON              DEFAULT NULL,
    `pack_meta`                        JSON              DEFAULT NULL,
    `paid_live_data`                   JSON              DEFAULT NULL,
    `room_view_stats`                  JSON              DEFAULT NULL,
    `extra`                            JSON              DEFAULT NULL,
    `room_auth`                        JSON              DEFAULT NULL,
    `short_touch_area_config`          JSON              DEFAULT NULL,
    `stream_url`                       JSON              DEFAULT NULL,
    `stats`                            JSON              DEFAULT NULL,
    `owner`                            JSON              DEFAULT NULL,
    `official_channel`                 JSON              DEFAULT NULL,

    `admin_user_ids`                   JSON              DEFAULT NULL,
    `admin_user_open_ids`              JSON              DEFAULT NULL,
    `deco_list`                        JSON              DEFAULT NULL,
    `fans_group_admin_user_ids`        JSON              DEFAULT NULL,
    `fans_group_admin_user_open_ids`   JSON              DEFAULT NULL,
    `filter_words`                     JSON              DEFAULT NULL,
    `live_distribution`                JSON              DEFAULT NULL,
    `sharing_music_id_list`            JSON              DEFAULT NULL,
    `tags`                             JSON              DEFAULT NULL,
    `top_fans`                         JSON              DEFAULT NULL,
    `upper_right_widget_data_list`     JSON              DEFAULT NULL,
    `vs_roles`                         JSON              DEFAULT NULL,
    `room_tabs`                        JSON              DEFAULT NULL,
    `assist_label_list`                JSON              DEFAULT NULL,
    `AnchorABMap`                      JSON              DEFAULT NULL,
    `linker_map`                       JSON              DEFAULT NULL,
    `dynamic_cover_dict`               JSON              DEFAULT NULL,

    `created_at`                       TIMESTAMP         DEFAULT CURRENT_TIMESTAMP,
    `updated_at`                       TIMESTAMP         DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY `idx_room_base_id_start_time` (`id`, `start_time`),
    PRIMARY KEY (`now`, `id`, `start_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='直播间基础表';
```

```shell

##
## room_base
##
+-------------------------------------+------------------------+------+-----+-------------------------+-------+--------------------------------------------------+-------------------------------+
| Field                               | Type                   | Null | Key | Default                 | Extra | Topology                                         | Comment                       |
+-------------------------------------+------------------------+------+-----+-------------------------+-------+--------------------------------------------------+-------------------------------+
| now                                 | timestamp(3)           | NO   | PRI |                         |       | "$.extra.now"                                    | 当前时间戳                    |
| id                                  | varchar(200)           | NO   | PRI |                         |       | "$.data.room.id"                                 | 直播间 ID                     |
| id_str                              | varchar(200)           | YES  |     | NULL                    |       | "$.data.room.id_str"                             | 直播间 ID 字符串              |
| title                               | tinytext               | YES  |     | NULL                    |       | "$.data.room.title"                              | 直播间标题                    |
| introduction                        | text                   | YES  |     | NULL                    |       | "$.data.room.introduction"                       | 直播间简介                    |
| share_url                           | text                   | YES  |     | NULL                    |       | "$.data.room.share_url"                          | 分享 URL                      |
| user_share_text                     | text                   | YES  |     | NULL                    |       | "$.data.room.user_share_text"                    | 用户分享文案                  |
| anchor_share_text                   | text                   | YES  |     | NULL                    |       | "$.data.room.anchor_share_text"                  | 主播分享文案                  |
| create_time                         | bigint                 | YES  |     | NULL                    |       | "$.data.room.create_time"                        | 创建时间 (毫秒时间戳)         |
| start_time                          | bigint                 | NO   | PRI |                         |       | "$.data.room.start_time"                         | 开始时间 (毫秒时间戳)         |
| finish_time                         | bigint                 | YES  |     | NULL                    |       | "$.data.room.finish_time"                        | 结束时间 (毫秒时间戳)         |
| stream_close_time                   | bigint                 | YES  |     | NULL                    |       | "$.data.room.stream_close_time"                  | 流关闭时间 (毫秒时间戳)       |
| status                              | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.status"                             | 直播状态 (2=直播中)           |
| finish_reason                       | smallint unsigned      | YES  |     | NULL                    |       | "$.data.room.finish_reason"                      | 结束原因                      |
| acquaintance_status                 | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.acquaintance_status"                | 熟人状态                      |
| owner_user_id                       | bigint                 | YES  |     | NULL                    |       | "$.data.room.owner_user_id"                      | 主播用户 ID                   |
| app_id                              | bigint                 | YES  |     | NULL                    |       | "$.data.room.app_id"                             | 应用 ID                       |
| base_category                       | bigint                 | YES  |     | 0                       |       | "$.data.room.base_category"                      | 基础分类                      |
| category                            | bigint                 | YES  |     | 0                       |       | "$.data.room.category"                           | 分类                          |
| client_version                      | bigint                 | YES  |     | NULL                    |       | "$.data.room.client_version"                     | 客户端版本                    |
| orientation                         | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.orientation"                        | 横竖屏方向                    |
| layout                              | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.layout"                             | 布局                          |
| room_layout                         | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.room_layout"                        | 房间布局                      |
| room_tag                            | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.room_tag"                           | 房间标签                      |
| live_room_mode                      | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.live_room_mode"                     | 直播模式                      |
| live_platform_source                | tinytext               | YES  |     | NULL                    |       | "$.data.room.live_platform_source"               | 直播平台来源                  |
| cell_style                          | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.cell_style"                         | 单元格样式                    |
| os_type                             | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.os_type"                            | 操作系统类型                  |
| owner_device_id                     | bigint                 | YES  |     | NULL                    |       | "$.data.room.owner_device_id"                    | 主播设备 ID                   |
| owner_open_id                       | varchar(200)           | YES  |     | NULL                    |       | "$.data.room.owner_open_id"                      | 主播 OpenID                   |
| visibility_range                    | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.visibility_range"                   | 可见范围                      |
| webcast_sdk_version                 | varchar(20)            | YES  |     | NULL                    |       | "$.data.room.webcast_sdk_version"                | Webcast SDK 版本              |
| stream_id                           | bigint                 | YES  |     | NULL                    |       | "$.data.room.stream_id"                          | 流 ID                         |
| stream_id_str                       | varchar(200)           | YES  |     | NULL                    |       | "$.data.room.stream_id_str"                      | 流 ID 字符串                  |
| live_id                             | bigint                 | YES  |     | NULL                    |       | "$.data.room.live_id"                            | 直播 ID                       |
| stream_provider                     | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.stream_provider"                    | 流提供商                      |
| like_count                          | bigint                 | YES  |     | 0                       |       | "$.data.room.like_count"                         | 点赞数                        |
| user_count                          | int unsigned           | YES  |     | 0                       |       | "$.data.room.user_count"                         | 用户数                        |
| popularity                          | int unsigned           | YES  |     | 0                       |       | "$.data.room.popularity"                         | 人气值                        |
| danmaku_detail                      | int unsigned           | YES  |     | 0                       |       | "$.data.room.danmaku_detail"                     | 弹幕详情                      |
| web_count                           | bigint                 | YES  |     | 0                       |       | "$.data.room.web_count"                          | 网页端人数                    |
| webcast_comment_tcs                 | int unsigned           | YES  |     | 0                       |       | "$.data.room.webcast_comment_tcs"                | Webcast 评论 TCS              |
| gift_msg_style                      | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.gift_msg_style"                     | 礼物消息样式                  |
| share_msg_style                     | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.share_msg_style"                    | 分享消息样式                  |
| follow_msg_style                    | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.follow_msg_style"                   | 关注消息样式                  |
| fansclub_msg_style                  | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.fansclub_msg_style"                 | 粉丝牌消息样式                |
| sell_goods                          | bool                   | YES  |     | FALSE                   |       | "$.data.room.sell_goods"                         | 是否售卖商品                  |
| has_commerce_goods                  | bool                   | YES  |     | FALSE                   |       | "$.data.room.has_commerce_goods"                 | 是否有电商商品                |
| is_replay                           | bool                   | YES  |     | FALSE                   |       | "$.data.room.is_replay"                          | 是否回放                      |
| replay                              | bool                   | YES  |     | FALSE                   |       | "$.data.room.replay"                             | 是否重播                      |
| highlight                           | bool                   | YES  |     | FALSE                   |       | "$.data.room.highlight"                          | 是否高亮                      |
| use_filter                          | bool                   | YES  |     | FALSE                   |       | "$.data.room.use_filter"                         | 是否使用滤镜                  |
| title_recommend                     | bool                   | YES  |     | FALSE                   |       | "$.data.room.title_recommend"                    | 是否标题推荐                  |
| enable_room_perspective             | bool                   | YES  |     | FALSE                   |       | "$.data.room.enable_room_perspective"            | 是否启用房间透视              |
| with_aggregate_column               | bool                   | YES  |     | FALSE                   |       | "$.data.room.with_aggregate_column"              | 聚合列标志                    |
| with_draw_something                 | bool                   | YES  |     | FALSE                   |       | "$.data.room.with_draw_something"                | 绘制标志                      |
| with_ktv                            | bool                   | YES  |     | FALSE                   |       | "$.data.room.with_ktv"                           | KTV 标志                      |
| with_linkmic                        | bool                   | YES  |     | FALSE                   |       | "$.data.room.with_linkmic"                       | 连麦标志                      |
| live_type_normal                    | bool                   | YES  |     | FALSE                   |       | "$.data.room.live_type_normal"                   | 普通直播                      |
| live_type_audio                     | bool                   | YES  |     | FALSE                   |       | "$.data.room.live_type_audio"                    | 音频直播                      |
| live_type_linkmic                   | bool                   | YES  |     | FALSE                   |       | "$.data.room.live_type_linkmic"                  | 连麦直播                      |
| live_type_official                  | bool                   | YES  |     | FALSE                   |       | "$.data.room.live_type_official"                 | 官方直播                      |
| live_type_sandbox                   | bool                   | YES  |     | FALSE                   |       | "$.data.room.live_type_sandbox"                  | 沙盒直播                      |
| live_type_screenshot                | bool                   | YES  |     | FALSE                   |       | "$.data.room.live_type_screenshot"               | 截图直播                      |
| live_type_third_party               | bool                   | YES  |     | FALSE                   |       | "$.data.room.live_type_third_party"              | 第三方直播                    |
| live_type_vs_live                   | bool                   | YES  |     | FALSE                   |       | "$.data.room.live_type_vs_live"                  | VS 直播                       |
| live_type_vs_premiere               | bool                   | YES  |     | FALSE                   |       | "$.data.room.live_type_vs_premiere"              | VS 首映                       |
| linkmic_layout                      | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.linkmic_layout"                     | 连麦布局                      |
| auth_city                           | varchar(100)           | YES  |     | NULL                    |       | "$.data.room.auth_city"                          | 授权城市                      |
| location                            | varchar(100)           | YES  |     | NULL                    |       | "$.data.room.location"                           | 位置                          |
| distance                            | varchar(100)           | YES  |     | NULL                    |       | "$.data.room.distance"                           | 距离                          |
| distance_city                       | varchar(100)           | YES  |     | NULL                    |       | "$.data.room.distance_city"                      | 距离城市                      |
| distance_km                         | varchar(100)           | YES  |     | NULL                    |       | "$.data.room.distance_km"                        | 距离公里                      |
| real_distance                       | varchar(100)           | YES  |     | NULL                    |       | "$.data.room.real_distance"                      | 真实距离                      |
| dynamic_cover_uri                   | text                   | YES  |     | NULL                    |       | "$.data.room.dynamic_cover_uri"                  | 动态封面 URI                  |
| vertical_cover_uri                  | text                   | YES  |     | NULL                    |       | "$.data.room.vertical_cover_uri"                 | 竖版封面 URI                  |
| finish_url                          | text                   | YES  |     | NULL                    |       | "$.data.room.finish_url"                         | 结束 URL                      |
| forum_extra_data                    | text                   | YES  |     | NULL                    |       | "$.data.room.forum_extra_data"                   | 论坛额外数据                  |
| private_info                        | text                   | YES  |     | NULL                    |       | "$.data.room.private_info"                       | 隐私信息                      |
| item_explicit_info                  | text                   | YES  |     | NULL                    |       | "$.data.room.item_explicit_info"                 | 显式内容信息                  |
| hot_sentence_info                   | text                   | YES  |     | NULL                    |       | "$.data.room.hot_sentence_info"                  | 热句信息                      |
| relation_tag                        | tinytext               | YES  |     | NULL                    |       | "$.data.room.relation_tag"                       | 关系标签                      |
| stamps                              | text                   | YES  |     | NULL                    |       | "$.data.room.stamps"                             | 印章列表 (JSON 字符串)        |
| room_create_ab_param                | text                   | YES  |     | NULL                    |       | "$.data.room.room_create_ab_param"               | 房间创建 AB 实验参数          |
| scroll_config                       | text                   | YES  |     | NULL                    |       | "$.data.room.scroll_config"                      | 滚动配置                      |
| mosaic_tip                          | tinytext               | YES  |     | NULL                    |       | "$.data.room.mosaic_tip"                         | 马赛克提示文案                |
| popularity_str                      | varchar(50)            | YES  |     | NULL                    |       | "$.data.room.popularity_str"                     | 人气值字符串                  |
| preview_copy                        | tinytext               | YES  |     | NULL                    |       | "$.data.room.preview_copy"                       | 预览文案                      |
| wait_copy                           | tinytext               | YES  |     | NULL                    |       | "$.data.room.wait_copy"                          | 等待文案                      |
| short_title                         | tinytext               | YES  |     | NULL                    |       | "$.data.room.short_title"                        | 短标题                        |
| video_feed_tag                      | tinytext               | YES  |     | NULL                    |       | "$.data.room.video_feed_tag"                     | 视频流标签                    |
| screen_capture_sharing_title        | tinytext               | YES  |     | NULL                    |       | "$.data.room.screen_capture_sharing_title"       | 截屏分享标题                  |
| common_label_list                   | tinytext               | YES  |     | NULL                    |       | "$.data.room.common_label_list"                  | 通用标签列表                  |
| content_tag                         | tinytext               | YES  |     | NULL                    |       | "$.data.room.content_tag"                        | 内容标签                      |
| challenge_info                      | tinytext               | YES  |     | NULL                    |       | "$.data.room.challenge_info"                     | 挑战信息                      |
| anchor_scheduled_time_text          | text                   | YES  |     | NULL                    |       | "$.data.room.anchor_scheduled_time_text"         | 主播预定时间文案              |
| anchor_tab_type                     | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.anchor_tab_type"                    | 主播 Tab 类型                 |
| comment_name_mode                   | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.comment_name_mode"                  | 评论名称模式                  |
| fcdn_appid                          | bigint                 | YES  |     | NULL                    |       | "$.data.room.fcdn_appid"                         | FCDN 应用 ID                  |
| game_room_type                      | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.game_room_type"                     | 游戏房间类型                  |
| official_channel_open_id            | varchar(200)           | YES  |     | NULL                    |       | "$.data.room.official_channel_open_id"           | 官方频道 OpenID               |
| official_channel_uid                | bigint                 | YES  |     | NULL                    |       | "$.data.room.official_channel_uid"               | 官方频道 UID                  |
| search_id                           | bigint                 | YES  |     | NULL                    |       | "$.data.room.search_id"                          | 搜索 ID                       |
| group_id                            | bigint                 | YES  |     | NULL                    |       | "$.data.room.group_id"                           | 分组 ID                       |
| group_source                        | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.group_source"                       | 分组来源                      |
| sofa_layout                         | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.sofa_layout"                        | 沙发布局                      |
| sun_daily_icon_content              | tinytext               | YES  |     | NULL                    |       | "$.data.room.sun_daily_icon_content"             | 每日太阳图标内容              |
| ranklist_audience_type              | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.ranklist_audience_type"             | 榜单观众类型                  |
| redpacket_audience_auth             | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.redpacket_audience_auth"            | 红包观众认证                  |
| toutiao_cover_recommend_level       | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.toutiao_cover_recommend_level"      | 头条封面推荐等级              |
| toutiao_title_recommend_level       | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.toutiao_title_recommend_level"      | 头条标题推荐等级              |
| preview_flow_tag                    | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.preview_flow_tag"                   | 预览流标签                    |
| replay_location                     | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.replay_location"                    | 回放位置                      |
| room_audit_status                   | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.room_audit_status"                  | 房间审核状态                  |
| mosaic_status                       | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.mosaic_status"                      | 马赛克状态                    |
| lottery_finish_time                 | bigint                 | YES  |     | NULL                    |       | "$.data.room.lottery_finish_time"                | 抽奖结束时间 (毫秒时间戳)     |
| luckymoney_num                      | int unsigned           | YES  |     | 0                       |       | "$.data.room.luckymoney_num"                     | 红包数量                      |
| has_promotion_games                 | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.has_promotion_games"                | 是否有推广游戏                |
| is_need_check_list                  | bool                   | YES  |     | FALSE                   |       | "$.data.room.is_need_check_list"                 | 是否需要清单审核              |
| is_official_channel_room            | bool                   | YES  |     | FALSE                   |       | "$.data.room.is_official_channel_room"           | 是否官方频道房间              |
| is_show_inquiry_ball                | bool                   | YES  |     | FALSE                   |       | "$.data.room.is_show_inquiry_ball"               | 是否显示咨询气泡              |
| is_show_user_card_switch            | bool                   | YES  |     | FALSE                   |       | "$.data.room.is_show_user_card_switch"           | 是否显示用户名片开关          |
| auto_cover                          | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.auto_cover"                         | 自动封面                      |
| business_live                       | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.business_live"                      | 商业直播                      |
| book_time                           | bigint                 | YES  |     | NULL                    |       | "$.data.room.book_time"                          | 预约时间 (毫秒时间戳)         |
| book_end_time                       | bigint                 | YES  |     | NULL                    |       | "$.data.room.book_end_time"                      | 预约结束时间 (毫秒时间戳)     |
| linkmic_display_type                | tinyint unsigned       | YES  |     | 0                       |       | "$.data.room.linkmic_display_type"               | 连麦展示类型                  |
| vid                                 | varchar(200)           | YES  |     | NULL                    |       | "$.data.room.vid"                                | 视频 ID                       |
| vs_main_replay_id                   | varchar(200)           | YES  |     | NULL                    |       | "$.data.room.vs_main_replay_id"                  | VS 主回放 ID                  |
| last_ping_time                      | bigint                 | YES  |     | NULL                    |       | "$.data.room.last_ping_time"                     | 最后心跳时间 (毫秒时间戳)     |
| pre_enter_time                      | bigint                 | YES  |     | NULL                    |       | "$.data.room.pre_enter_time"                     | 预进入时间 (毫秒时间戳)       |
| city_top_distance                   | tinytext               | YES  |     | NULL                    |       | "$.data.room.city_top_distance"                  | 城市顶部距离                  |
| cover                               | JSON                   | YES  |     | NULL                    |       | "$.data.room.cover"                              | 封面数据 (JSON)               |
| content_label                       | JSON                   | YES  |     | NULL                    |       | "$.data.room.content_label"                      | 内容标签 (JSON)               |
| feed_room_label                     | JSON                   | YES  |     | NULL                    |       | "$.data.room.feed_room_label"                    | 推荐流房间标签 (JSON)         |
| guide_button                        | JSON                   | YES  |     | NULL                    |       | "$.data.room.guide_button"                       | 引导按钮 (JSON)               |
| comment_box                         | JSON                   | YES  |     | NULL                    |       | "$.data.room.comment_box"                        | 评论框 (JSON)                 |
| link_mic                            | JSON                   | YES  |     | NULL                    |       | "$.data.room.link_mic"                           | 连麦信息 (JSON)               |
| living_room_attrs                   | JSON                   | YES  |     | NULL                    |       | "$.data.room.living_room_attrs"                  | 直播间属性 (JSON)             |
| pack_meta                           | JSON                   | YES  |     | NULL                    |       | "$.data.room.pack_meta"                          | 包元数据 (JSON)               |
| paid_live_data                      | JSON                   | YES  |     | NULL                    |       | "$.data.room.paid_live_data"                     | 付费直播数据 (JSON)           |
| room_view_stats                     | JSON                   | YES  |     | NULL                    |       | "$.data.room.room_view_stats"                    | 房间浏览统计 (JSON)           |
| extra                               | JSON                   | YES  |     | NULL                    |       | "$.data.room.extra"                              | 扩展数据 (JSON)               |
| room_auth                           | JSON                   | YES  |     | NULL                    |       | "$.data.room.room_auth"                          | 房间权限 (JSON)               |
| short_touch_area_config             | JSON                   | YES  |     | NULL                    |       | "$.data.room.short_touch_area_config"            | 短触区域配置 (JSON)           |
| stream_url                          | JSON                   | YES  |     | NULL                    |       | "$.data.room.stream_url"                         | 流地址数据 (JSON)             |
| stats                               | JSON                   | YES  |     | NULL                    |       | "$.data.room.stats"                              | 统计数据 (JSON)               |
| owner                               | JSON                   | YES  |     | NULL                    |       | "$.data.room.owner"                              | 主播信息 (JSON)               |
| official_channel                    | JSON                   | YES  |     | NULL                    |       | "$.data.room.official_channel"                   | 官方频道 (JSON)               |
| admin_user_ids                      | JSON                   | YES  |     | NULL                    |       | "$.data.room.admin_user_ids"                     | 管理员用户 ID 列表 (JSON)     |
| admin_user_open_ids                 | JSON                   | YES  |     | NULL                    |       | "$.data.room.admin_user_open_ids"                | 管理员 OpenID 列表 (JSON)     |
| deco_list                           | JSON                   | YES  |     | NULL                    |       | "$.data.room.deco_list"                          | 装饰列表 (JSON)               |
| fans_group_admin_user_ids           | JSON                   | YES  |     | NULL                    |       | "$.data.room.fans_group_admin_user_ids"          | 粉丝群管理员 ID 列表 (JSON)   |
| fans_group_admin_user_open_ids      | JSON                   | YES  |     | NULL                    |       | "$.data.room.fans_group_admin_user_open_ids"     | 粉丝群管理员 OpenID 列表 (JSON) |
| filter_words                        | JSON                   | YES  |     | NULL                    |       | "$.data.room.filter_words"                       | 过滤词列表 (JSON)             |
| live_distribution                   | JSON                   | YES  |     | NULL                    |       | "$.data.room.live_distribution"                  | 直播分发信息 (JSON)           |
| sharing_music_id_list               | JSON                   | YES  |     | NULL                    |       | "$.data.room.sharing_music_id_list"              | 分享音乐 ID 列表 (JSON)       |
| tags                                | JSON                   | YES  |     | NULL                    |       | "$.data.room.tags"                               | 标签列表 (JSON)               |
| top_fans                            | JSON                   | YES  |     | NULL                    |       | "$.data.room.top_fans"                           | 头部粉丝列表 (JSON)           |
| upper_right_widget_data_list        | JSON                   | YES  |     | NULL                    |       | "$.data.room.upper_right_widget_data_list"       | 右上角组件列表 (JSON)         |
| vs_roles                            | JSON                   | YES  |     | NULL                    |       | "$.data.room.vs_roles"                           | VS 角色列表 (JSON)            |
| room_tabs                           | JSON                   | YES  |     | NULL                    |       | "$.data.room.room_tabs"                          | 房间 Tab 列表 (JSON)          |
| assist_label_list                   | JSON                   | YES  |     | NULL                    |       | "$.data.room.assist_label_list"                  | 辅助标签列表 (JSON)           |
| AnchorABMap                         | JSON                   | YES  |     | NULL                    |       | "$.data.room.AnchorABMap"                        | 主播 AB 实验映射 (JSON)       |
| linker_map                          | JSON                   | YES  |     | NULL                    |       | "$.data.room.linker_map"                         | 连麦映射 (JSON)               |
| dynamic_cover_dict                  | JSON                   | YES  |     | NULL                    |       | "$.data.room.dynamic_cover_dict"                 | 动态封面字典 (JSON)           |
| created_at                          | timestamp              | YES  |     | CURRENT_TIMESTAMP       |       | -                                                | 创建时间                      |
| updated_at                          | timestamp              | YES  |     | CURRENT_TIMESTAMP       | on update CURRENT_TIMESTAMP | -                                | 更新时间                      |
+-------------------------------------+------------------------+------+-----+-------------------------+-------+--------------------------------------------------+-------------------------------+

#### 5-1. 直播间统计数据表 - room_stats

```sql
CREATE TABLE IF NOT EXISTS `room_stats` (
    `now`                 TIMESTAMP(3)      NOT NULL COMMENT '当前时间戳',
    `platform`            VARCHAR(20)       NOT NULL COMMENT '平台',
    `room_id`             VARCHAR(200)      NOT NULL COMMENT '直播间 ID',
    `comment_count`       BIGINT            DEFAULT 0 COMMENT '评论数',
    `digg_count`          BIGINT            DEFAULT 0 COMMENT '点赞数',
    `dou_plus_promotion`  TINYTEXT          DEFAULT NULL COMMENT 'Dou+ 推广',
    `enter_count`         BIGINT            DEFAULT 0 COMMENT '进入数',
    `fan_ticket`          BIGINT            DEFAULT 0 COMMENT '粉丝票数量',
    `follow_count`        BIGINT            DEFAULT 0 COMMENT '关注数',
    `gift_uv_count`       INT               DEFAULT 0 COMMENT '礼物 UV 数',
    `like_count`          BIGINT            DEFAULT 0 COMMENT '喜欢数',
    `money`               BIGINT            DEFAULT 0 COMMENT '金额',
    `total_user`          INT               DEFAULT 0 COMMENT '总用户数',
    `total_user_desp`     TEXT              DEFAULT NULL COMMENT '总用户描述',
    `total_user_str`      VARCHAR(100)      DEFAULT NULL COMMENT '总用户字符串',
    `up_right_stats_str`  VARCHAR(100)      DEFAULT NULL COMMENT '右上角统计字符串',
    `up_right_stats_str_complete` TINYTEXT  DEFAULT NULL COMMENT '右上角统计完整字符串',
    `user_count_str`      VARCHAR(100)      DEFAULT NULL COMMENT '用户数量字符串',
    `watermelon`          BIGINT            DEFAULT 0 COMMENT '西瓜',
    `welfare_donation_amount` BIGINT        DEFAULT 0 COMMENT '福利捐赠金额',
    `user_count_composition_city`       INT DEFAULT 0 COMMENT '城市用户数',
    `user_count_composition_my_follow`  BIGINT DEFAULT 0 COMMENT '我的关注用户数',
    `user_count_composition_other`      BIGINT DEFAULT 0 COMMENT '其他用户数',
    `user_count_composition_video_detail` BIGINT DEFAULT 0 COMMENT '视频详情用户数',
    PRIMARY KEY (`now`, `platform`, `room_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='直播间统计数据表';
```

```shell
##
## room_stats
##
+-------------------------------------+-------------------+------+-----+---------+-------+----------------------------------------+---------------------+
| Field                               | Type              | Null | Key | Default | Extra | Topology                               | Comment             |
+-------------------------------------+-------------------+------+-----+---------+-------+----------------------------------------+---------------------+
| now                                 | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"                          | 当前时间戳          |
| platform                            | varchar(20)       | NO   | PRI |         |       |           -                              | 平台                |
| room_id                             | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                       | 直播间 ID           |
| comment_count                       | bigint            | YES  |     | 0       |       | "$.data.room.stats.comment_count"      | 评论数              |
| digg_count                          | bigint            | YES  |     | 0       |       | "$.data.room.stats.digg_count"         | 点赞数              |
| dou_plus_promotion                  | tinytext          | YES  |     | NULL    |       | "$.data.room.stats.dou_plus_promotion" | Dou+ 推广           |
| enter_count                         | bigint            | YES  |     | 0       |       | "$.data.room.stats.enter_count"        | 进入数              |
| fan_ticket                          | bigint            | YES  |     | 0       |       | "$.data.room.stats.fan_ticket"         | 粉丝票数量          |
| follow_count                        | bigint            | YES  |     | 0       |       | "$.data.room.stats.follow_count"       | 关注数              |
| gift_uv_count                       | int               | YES  |     | 0       |       | "$.data.room.stats.gift_uv_count"      | 礼物 UV 数          |
| like_count                          | bigint            | YES  |     | 0       |       | "$.data.room.stats.like_count"         | 喜欢数              |
| money                               | bigint            | YES  |     | 0       |       | "$.data.room.stats.money"              | 金额                |
| total_user                          | int               | YES  |     | 0       |       | "$.data.room.stats.total_user"         | 总用户数            |
| total_user_desp                     | text              | YES  |     | NULL    |       | "$.data.room.stats.total_user_desp"    | 总用户描述          |
| total_user_str                      | varchar(100)      | YES  |     | NULL    |       | "$.data.room.stats.total_user_str"     | 总用户字符串        |
| up_right_stats_str                  | varchar(100)      | YES  |     | NULL    |       | "$.data.room.stats.up_right_stats_str" | 右上角统计字符串    |
| up_right_stats_str_complete         | tinytext          | YES  |     | NULL    |       | "$.data.room.stats.up_right_stats_str_complete" | 右上角统计完整字符串 |
| user_count_str                      | varchar(100)      | YES  |     | NULL    |       | "$.data.room.stats.user_count_str"     | 用户数量字符串      |
| watermelon                          | bigint            | YES  |     | 0       |       | "$.data.room.stats.watermelon"         | 西瓜                |
| welfare_donation_amount             | bigint            | YES  |     | 0       |       | "$.data.room.stats.welfare_donation_amount" | 福利捐赠金额    |
| user_count_composition_city         | int               | YES  |     | 0       |       | "$.data.room.stats.user_count_composition.city" | 城市用户数    |
| user_count_composition_my_follow    | bigint            | YES  |     | 0       |       | "$.data.room.stats.user_count_composition.my_follow" | 我的关注用户数 |
| user_count_composition_other        | bigint            | YES  |     | 0       |       | "$.data.room.stats.user_count_composition.other" | 其他用户数    |
| user_count_composition_video_detail | bigint            | YES  |     | 0       |       | "$.data.room.stats.user_count_composition.video_detail" | 视频详情用户数 |
+-------------------------------------+-------------------+------+-----+---------+-------+----------------------------------------+---------------------+
```

#### 5-2. 直播间流信息表 - room_stream

```sql
CREATE TABLE IF NOT EXISTS `room_stream` (
    `platform`            VARCHAR(20)       NOT NULL COMMENT '平台',
    `start_time`          DATETIME          NOT NULL COMMENT '直播开始时间',
    `room_id`             VARCHAR(200)      NOT NULL COMMENT '直播间 ID',
    `default_resolution`  VARCHAR(20)       DEFAULT NULL COMMENT '默认分辨率',
    `hls_pull_url`        TEXT              DEFAULT NULL COMMENT 'HLS 拉流 URL',
    `rtmp_pull_url`       TEXT              DEFAULT NULL COMMENT 'RTMP 拉流 URL',
    `rtmp_pull_url_params` TEXT             DEFAULT NULL COMMENT 'RTMP 拉流 URL 参数',
    `rtmp_push_url`       TEXT              DEFAULT NULL COMMENT 'RTMP 推流 URL',
    `rtmp_push_url_params` TEXT             DEFAULT NULL COMMENT 'RTMP 推流 URL 参数',
    `stream_id`           BIGINT            DEFAULT NULL COMMENT '流 ID',
    `stream_id_str`       VARCHAR(200)      DEFAULT NULL COMMENT '流 ID 字符串',
    `multi_stream_scene`  TINYINT           DEFAULT 0 COMMENT '多流场景',
    `provider`            TINYINT           DEFAULT 0 COMMENT '提供者',
    `stream_control_type` TINYINT           DEFAULT 0 COMMENT '流控制类型',
    `stream_orientation`  TINYINT           DEFAULT 0 COMMENT '流方向',
    `vr_type`             TINYINT           DEFAULT 0 COMMENT 'VR 类型',
    `resolution_name_sd1` VARCHAR(50)       DEFAULT NULL COMMENT '标清分辨率名称',
    `resolution_name_sd2` VARCHAR(50)       DEFAULT NULL COMMENT '高清分辨率名称',
    `resolution_name_hd1` VARCHAR(50)       DEFAULT NULL COMMENT '超清分辨率名称',
    `resolution_name_full_hd1` VARCHAR(50)  DEFAULT NULL COMMENT '蓝光分辨率名称',
    `flv_pull_url_sd1`    TEXT              DEFAULT NULL COMMENT '标清 FLV 拉流 URL',
    `flv_pull_url_sd2`    TEXT              DEFAULT NULL COMMENT '高清 FLV 拉流 URL',
    `flv_pull_url_hd1`    TEXT              DEFAULT NULL COMMENT '超清 FLV 拉流 URL',
    `flv_pull_url_full_hd1` TEXT            DEFAULT NULL COMMENT '蓝光 FLV 拉流 URL',
    `hls_pull_url_sd1`    TEXT              DEFAULT NULL COMMENT '标清 HLS 拉流 URL',
    `hls_pull_url_sd2`    TEXT              DEFAULT NULL COMMENT '高清 HLS 拉流 URL',
    `hls_pull_url_hd1`    TEXT              DEFAULT NULL COMMENT '超清 HLS 拉流 URL',
    `hls_pull_url_full_hd1` TEXT            DEFAULT NULL COMMENT '蓝光 HLS 拉流 URL',
    `flv_params_sd1`      TEXT              DEFAULT NULL COMMENT '标清 FLV 参数',
    `flv_params_sd2`      TEXT              DEFAULT NULL COMMENT '高清 FLV 参数',
    `flv_params_hd1`      TEXT              DEFAULT NULL COMMENT '超清 FLV 参数',
    `flv_params_full_hd1` TEXT              DEFAULT NULL COMMENT '蓝光 FLV 参数',
    `hls_params`          TEXT              DEFAULT NULL COMMENT 'HLS 参数',
    `extra_anchor_interact_profile` TINYINT DEFAULT 0 COMMENT '主播互动档案',
    `extra_audience_interact_profile` TINYINT DEFAULT 0 COMMENT '观众互动档案',
    `extra_bframe_enable` BOOL              DEFAULT FALSE COMMENT 'B 帧启用',
    `extra_bitrate_adapt_strategy` TINYINT  DEFAULT 0 COMMENT '码率自适应策略',
    `extra_business_name` VARCHAR(100)      DEFAULT NULL COMMENT '业务名称',
    `extra_bytevc1_enable` BOOL             DEFAULT FALSE COMMENT 'ByteVC1 启用',
    `extra_default_bitrate` INT             DEFAULT 0 COMMENT '默认码率',
    `extra_fps`           TINYINT           DEFAULT 0 COMMENT '帧率',
    `extra_gop_sec`       TINYINT           DEFAULT 0 COMMENT 'GOP 秒数',
    `extra_h265_enable`   BOOL              DEFAULT FALSE COMMENT 'H265 启用',
    `extra_hardware_encode` BOOL             DEFAULT FALSE COMMENT '硬件编码',
    `extra_height`        INT               DEFAULT 0 COMMENT '高度',
    `extra_width`         INT               DEFAULT 0 COMMENT '宽度',
    `extra_max_bitrate`   INT               DEFAULT 0 COMMENT '最大码率',
    `extra_min_bitrate`   INT               DEFAULT 0 COMMENT '最小码率',
    `extra_roi`           BOOL              DEFAULT FALSE COMMENT 'ROI',
    `extra_sw_roi`        BOOL              DEFAULT FALSE COMMENT '软件 ROI',
    `extra_video_profile` TINYINT           DEFAULT 0 COMMENT '视频档案',
    PRIMARY KEY (`platform`, `start_time`, `room_id`)
);
```

```shell
##
## room_stream
##
+-------------------------------------+-------------------+------+-----+---------+-------+----------------------------------------+---------------------+
| Field                               | Type              | Null | Key | Default | Extra | Topology                               | Comment             |
+-------------------------------------+-------------------+------+-----+---------+-------+----------------------------------------+---------------------+
| platform                            | varchar(20)       | NO   | PRI |         |       | "$.platform"                           | 平台                |
| start_time                          | datetime          | NO   | PRI |         |       | "$.data.start_time"                    | 直播开始时间         |
| room_id                             | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                       | 直播间 ID           |
| default_resolution                  | varchar(20)       | YES  |     | NULL    |       | "$.data.room.stream_url.default_resolution" | 默认分辨率      |
| hls_pull_url                        | text              | YES  |     | NULL    |       | "$.data.room.stream_url.hls_pull_url"  | HLS 拉流 URL        |
| rtmp_pull_url                       | text              | YES  |     | NULL    |       | "$.data.room.stream_url.rtmp_pull_url" | RTMP 拉流 URL       |
| rtmp_pull_url_params                | text              | YES  |     | NULL    |       | "$.data.room.stream_url.rtmp_pull_url_params" | RTMP 拉流参数 |
| rtmp_push_url                       | text              | YES  |     | NULL    |       | "$.data.room.stream_url.rtmp_push_url" | RTMP 推流 URL       |
| rtmp_push_url_params                | text              | YES  |     | NULL    |       | "$.data.room.stream_url.rtmp_push_url_params" | RTMP 推流参数 |
| stream_id                           | bigint            | YES  |     | NULL    |       | "$.data.room.stream_url.id"            | 流 ID               |
| stream_id_str                       | varchar(200)      | YES  |     | NULL    |       | "$.data.room.stream_url.id_str"        | 流 ID 字符串         |
| multi_stream_scene                  | tinyint           | YES  |     | 0       |       | "$.data.room.stream_url.multi_stream_scene" | 多流场景      |
| provider                            | tinyint           | YES  |     | 0       |       | "$.data.room.stream_url.provider"      | 提供者              |
| stream_control_type                 | tinyint           | YES  |     | 0       |       | "$.data.room.stream_url.stream_control_type" | 流控制类型  |
| stream_orientation                  | tinyint           | YES  |     | 0       |       | "$.data.room.stream_url.stream_orientation" | 流方向      |
| vr_type                             | tinyint           | YES  |     | 0       |       | "$.data.room.stream_url.vr_type"       | VR 类型             |
| resolution_name_sd1                 | varchar(50)       | YES  |     | NULL    |       | "$.data.room.stream_url.resolution_name.SD1" | 标清分辨率名称 |
| resolution_name_sd2                 | varchar(50)       | YES  |     | NULL    |       | "$.data.room.stream_url.resolution_name.SD2" | 高清分辨率名称 |
| resolution_name_hd1                 | varchar(50)       | YES  |     | NULL    |       | "$.data.room.stream_url.resolution_name.HD1" | 超清分辨率名称 |
| resolution_name_full_hd1            | varchar(50)       | YES  |     | NULL    |       | "$.data.room.stream_url.resolution_name.FULL_HD1" | 蓝光分辨率名称 |
| flv_pull_url_sd1                    | text              | YES  |     | NULL    |       | "$.data.room.stream_url.flv_pull_url.SD1" | 标清 FLV 拉流 URL  |
| flv_pull_url_sd2                    | text              | YES  |     | NULL    |       | "$.data.room.stream_url.flv_pull_url.SD2" | 高清 FLV 拉流 URL  |
| flv_pull_url_hd1                    | text              | YES  |     | NULL    |       | "$.data.room.stream_url.flv_pull_url.HD1" | 超清 FLV 拉流 URL  |
| flv_pull_url_full_hd1               | text              | YES  |     | NULL    |       | "$.data.room.stream_url.flv_pull_url.FULL_HD1" | 蓝光 FLV 拉流 URL |
| hls_pull_url_sd1                    | text              | YES  |     | NULL    |       | "$.data.room.stream_url.hls_pull_url_map.SD1" | 标清 HLS 拉流 URL |
| hls_pull_url_sd2                    | text              | YES  |     | NULL    |       | "$.data.room.stream_url.hls_pull_url_map.SD2" | 高清 HLS 拉流 URL |
| hls_pull_url_hd1                    | text              | YES  |     | NULL    |       | "$.data.room.stream_url.hls_pull_url_map.HD1" | 超清 HLS 拉流 URL |
| hls_pull_url_full_hd1               | text              | YES  |     | NULL    |       | "$.data.room.stream_url.hls_pull_url_map.FULL_HD1" | 蓝光 HLS 拉流 URL |
| flv_params_sd1                      | text              | YES  |     | NULL    |       | "$.data.room.stream_url.flv_pull_url_params.SD1" | 标清 FLV 参数 |
| flv_params_sd2                      | text              | YES  |     | NULL    |       | "$.data.room.stream_url.flv_pull_url_params.SD2" | 高清 FLV 参数 |
| flv_params_hd1                      | text              | YES  |     | NULL    |       | "$.data.room.stream_url.flv_pull_url_params.HD1" | 超清 FLV 参数 |
| flv_params_full_hd1                 | text              | YES  |     | NULL    |       | "$.data.room.stream_url.flv_pull_url_params.FULL_HD1" | 蓝光 FLV 参数 |
| hls_params                          | text              | YES  |     | NULL    |       | "$.data.room.stream_url.hls_pull_url_params" | HLS 参数       |
| extra_anchor_interact_profile       | tinyint           | YES  |     | 0       |       | "$.data.room.stream_url.extra.anchor_interact_profile" | 主播互动档案 |
| extra_audience_interact_profile     | tinyint           | YES  |     | 0       |       | "$.data.room.stream_url.extra.audience_interact_profile" | 观众互动档案 |
| extra_bframe_enable                 | bool              | YES  |     | FALSE   |       | "$.data.room.stream_url.extra.bframe_enable" | B 帧启用     |
| extra_bitrate_adapt_strategy        | tinyint           | YES  |     | 0       |       | "$.data.room.stream_url.extra.bitrate_adapt_strategy" | 码率自适应策略 |
| extra_business_name                 | varchar(100)      | YES  |     | NULL    |       | "$.data.room.stream_url.extra.business_name" | 业务名称   |
| extra_bytevc1_enable                | bool              | YES  |     | FALSE   |       | "$.data.room.stream_url.extra.bytevc1_enable" | ByteVC1 启用 |
| extra_default_bitrate               | int               | YES  |     | 0       |       | "$.data.room.stream_url.extra.default_bitrate" | 默认码率   |
| extra_fps                           | tinyint           | YES  |     | 0       |       | "$.data.room.stream_url.extra.fps"     | 帧率                |
| extra_gop_sec                       | tinyint           | YES  |     | 0       |       | "$.data.room.stream_url.extra.gop_sec" | GOP 秒数            |
| extra_h265_enable                   | bool              | YES  |     | FALSE   |       | "$.data.room.stream_url.extra.h265_enable" | H265 启用    |
| extra_hardware_encode               | bool              | YES  |     | FALSE   |       | "$.data.room.stream_url.extra.hardware_encode" | 硬件编码   |
| extra_height                        | int               | YES  |     | 0       |       | "$.data.room.stream_url.extra.height"  | 高度                |
| extra_width                         | int               | YES  |     | 0       |       | "$.data.room.stream_url.extra.width"   | 宽度                |
| extra_max_bitrate                   | int               | YES  |     | 0       |       | "$.data.room.stream_url.extra.max_bitrate" | 最大码率   |
| extra_min_bitrate                   | int               | YES  |     | 0       |       | "$.data.room.stream_url.extra.min_bitrate" | 最小码率   |
| extra_roi                           | bool              | YES  |     | FALSE   |       | "$.data.room.stream_url.extra.roi"     | ROI                 |
| extra_sw_roi                        | bool              | YES  |     | FALSE   |       | "$.data.room.stream_url.extra.sw_roi"  | 软件 ROI            |
| extra_video_profile                 | tinyint           | YES  |     | 0       |       | "$.data.room.stream_url.extra.video_profile" | 视频档案   |
+-------------------------------------+-------------------+------+-----+---------+-------+----------------------------------------+---------------------+
```

#### 5-3. 主播信息表 - room_owner_v2

```sql
CREATE TABLE IF NOT EXISTS `room_owner_v2` (
    `room_id`             VARCHAR(200)      NOT NULL COMMENT '直播间 ID',
    
    -- 基本信息
    `user_id`             VARCHAR(200)      DEFAULT NULL COMMENT '用户 ID',
    `owner_open_id`       VARCHAR(200)      DEFAULT NULL COMMENT '主播 OpenID',
    `owner_device_id`     BIGINT            DEFAULT NULL COMMENT '主播设备 ID',
    `sec_uid`             TEXT              DEFAULT NULL COMMENT '安全用户 UID',
    `user_open_id`        VARCHAR(200)      DEFAULT NULL COMMENT '用户开放 ID',
    `short_id`            VARCHAR(50)       DEFAULT NULL COMMENT '短 ID',
    `display_id`          VARCHAR(50)       DEFAULT NULL COMMENT '显示 ID',
    `nickname`            VARCHAR(50)       DEFAULT NULL COMMENT '昵称',
    `signature`           TEXT              DEFAULT NULL COMMENT '签名',
    `share_qrcode_uri`    TEXT              DEFAULT NULL COMMENT '分享二维码 URI',
    `special_id`          VARCHAR(100)      DEFAULT NULL COMMENT '特殊 ID',
    `status`              UNSIGNED TINYINT  DEFAULT 0 COMMENT '用户状态',
    `bg_img_url`          TEXT              DEFAULT NULL COMMENT '背景图片 URL',

    -- 个人信息
    `gender`              UNSIGNED TINYINT  DEFAULT NULL COMMENT '性别',
    `city`                VARCHAR(100)      DEFAULT NULL COMMENT '城市',
    `constellation`       VARCHAR(20)       DEFAULT NULL COMMENT '星座',
    `age_range`           UNSIGNED TINYINT  DEFAULT 0 COMMENT '年龄范围',
    `birthday`            BIGINT            DEFAULT 0 COMMENT '生日时间戳',
    `birthday_description` VARCHAR(100)     DEFAULT NULL COMMENT '生日描述',
    `birthday_valid`      BOOL              DEFAULT FALSE COMMENT '生日是否有效',
    `location_city`       VARCHAR(100)      DEFAULT NULL COMMENT '位置城市',
    `foreign_user`        UNSIGNED TINYINT  DEFAULT 0 COMMENT '是否海外用户',
    `mystery_man`         UNSIGNED TINYINT  DEFAULT 0 COMMENT '神秘人标识',
    
    -- 等级
    `level`               UNSIGNED SMALLINT DEFAULT NULL COMMENT '等级',
    `exp`                 BIGINT            DEFAULT 0 COMMENT '经验值',
    `experience`          BIGINT            DEFAULT 0 COMMENT '经验',
    `fan_ticket_count`    BIGINT            DEFAULT NULL COMMENT '粉丝票数量',
    `consume_diamond_level` UNSIGNED TINYINT DEFAULT 0 COMMENT '消费钻石等级',
    `income_share_percent` UNSIGNED TINYINT DEFAULT 0 COMMENT '收入分成比例',
    `link_mic_stats`      UNSIGNED TINYINT  DEFAULT 0 COMMENT '连麦统计',
    `media_badge_image_list` JSON           DEFAULT NULL COMMENT '媒体勋章图片列表 (JSON)',
    `modify_time`         BIGINT            DEFAULT 0 COMMENT '修改时间戳',
    `pay_score`           BIGINT            DEFAULT 0 COMMENT '支付分数',
    `pay_scores`          BIGINT            DEFAULT 0 COMMENT '支付分数 (复数)',
    `need_profile_guide`  BOOL              DEFAULT FALSE COMMENT '需要资料引导',
    `new_real_time_icons` JSON              DEFAULT NULL COMMENT '新实时图标列表 (JSON)',
    `real_time_icons`     JSON              DEFAULT NULL COMMENT '实时图标列表 (JSON)',
    
    -- 关注
    `follow_status`       UNSIGNED TINYINT  DEFAULT 0 COMMENT '关注状态',
    `is_follower`         BOOL              DEFAULT FALSE COMMENT '是否粉丝',
    `is_following`        BOOL              DEFAULT FALSE COMMENT '是否关注',
    `follow_info`         JSON              DEFAULT NULL COMMENT '关注信息 (JSON)',
    `is_anonymous`        BOOL              DEFAULT FALSE COMMENT '是否匿名',
    `hotsoon_verified`    BOOL              DEFAULT FALSE COMMENT '是否快手认证',
    `hotsoon_verified_reason` VARCHAR(255)  DEFAULT NULL COMMENT '快手认证原因',
    `ichat_restrict_type` UNSIGNED TINYINT  DEFAULT 0 COMMENT '聊天限制类型',
    `disable_ichat`       UNSIGNED TINYINT  DEFAULT 0 COMMENT '禁用聊天',
    `enable_ichat_img`    UNSIGNED TINYINT  DEFAULT 0 COMMENT '启用聊天图片',
    `fold_stranger_chat`  BOOL              DEFAULT FALSE COMMENT '折叠陌生人聊天',
    `desensitized_nickname` VARCHAR(50)     DEFAULT NULL COMMENT '脱敏昵称',
    
    -- 认证
    `verified`            BOOL              DEFAULT FALSE COMMENT '是否认证',
    `verified_reason`     VARCHAR(255)      DEFAULT NULL COMMENT '认证原因',
    `verified_content`    TEXT              DEFAULT NULL COMMENT '认证内容',
    `verified_mobile`     BOOL              DEFAULT FALSE COMMENT '是否手机认证',
    `enterprise_verify_reason` VARCHAR(255) DEFAULT NULL COMMENT '企业认证原因',
    `custom_verify`       VARCHAR(100)      DEFAULT NULL COMMENT '自定义认证',
    `block_status`        UNSIGNED TINYINT  DEFAULT 0 COMMENT '屏蔽状态',
    `comment_restrict`    UNSIGNED TINYINT  DEFAULT 0 COMMENT '评论限制',
    `public_area_oper_freq` UNSIGNED TINYINT DEFAULT 0 COMMENT '公共区域操作频率',
    `push_comment_status` BOOL              DEFAULT FALSE COMMENT '推送评论状态',
    `push_digg`           BOOL              DEFAULT FALSE COMMENT '推送点赞',
    `push_follow`         BOOL              DEFAULT FALSE COMMENT '推送关注',
    `push_friend_action`  BOOL              DEFAULT FALSE COMMENT '推送好友动态',
    `push_ichat`          BOOL              DEFAULT FALSE COMMENT '推送聊天',
    `push_status`         BOOL              DEFAULT FALSE COMMENT '推送状态',
    `push_video_post`     BOOL              DEFAULT FALSE COMMENT '推送视频发布',
    `push_video_recommend` BOOL             DEFAULT FALSE COMMENT '推送视频推荐',
    `remark_name`         VARCHAR(50)       DEFAULT NULL COMMENT '备注名',
    `secret`              UNSIGNED TINYINT  DEFAULT 0 COMMENT '隐私设置',
    `user_role`           UNSIGNED TINYINT  DEFAULT 0 COMMENT '用户角色',
    `webcast_private`     UNSIGNED TINYINT  DEFAULT 0 COMMENT '直播隐私设置',
    `can_view_webcast_private` UNSIGNED TINYINT DEFAULT 0 COMMENT '是否可观看直播隐私',
    `user_canceled`       BOOL              DEFAULT FALSE COMMENT '用户是否已注销',
    `telephone`           VARCHAR(20)       DEFAULT NULL COMMENT '电话号码',

    -- 权限
    `with_commerce_permission` BOOL         DEFAULT FALSE COMMENT '商务权限',
    `with_fusion_shop_entry`   BOOL         DEFAULT FALSE COMMENT '融合店铺入口',
    `with_car_management_permission` BOOL   DEFAULT FALSE COMMENT '汽车管理权限',
    `adversary_authorization_info` UNSIGNED TINYINT DEFAULT 0 COMMENT '对手授权信息',
    `adversary_user_status`    UNSIGNED TINYINT DEFAULT 0 COMMENT '对手用户状态',
    `authorization_info`       UNSIGNED TINYINT DEFAULT 0 COMMENT '授权信息',
    `allow_be_located`         BOOL          DEFAULT FALSE COMMENT '允许被定位',
    `allow_find_by_contacts`   BOOL          DEFAULT FALSE COMMENT '允许通过联系人找到',
    `allow_others_download_video` BOOL       DEFAULT FALSE COMMENT '允许他人下载视频',
    `allow_others_download_when_sharing_video` BOOL DEFAULT FALSE COMMENT '分享视频时允许他人下载',
    `allow_share_show_profile` BOOL          DEFAULT FALSE COMMENT '允许分享显示资料',
    `allow_show_in_gossip`     BOOL          DEFAULT FALSE COMMENT '允许在闲聊中显示',
    `allow_show_my_action`     BOOL          DEFAULT FALSE COMMENT '允许显示我的动态',
    `allow_strange_comment`    BOOL          DEFAULT FALSE COMMENT '允许陌生人评论',
    `allow_unfollower_comment` BOOL          DEFAULT FALSE COMMENT '允许未关注者评论',
    `allow_use_linkmic`        BOOL          DEFAULT FALSE COMMENT '允许使用连麦',
    
    -- JSON 扩展字段
    `avatar_large`            JSON    DEFAULT NULL COMMENT '大头像数据 (JSON)',
    `avatar_medium`           JSON    DEFAULT NULL COMMENT '中等头像数据 (JSON)',
    `avatar_thumb`            JSON    DEFAULT NULL COMMENT '缩略头像数据 (JSON)',
    `badge_image_list`        JSON    DEFAULT NULL COMMENT '勋章图片列表 (JSON)',
    `badge_image_list_v2`     JSON    DEFAULT NULL COMMENT '勋章图片列表 V2 (JSON)',
    `commerce_webcast_config_ids` JSON DEFAULT NULL COMMENT '商业直播配置 ID 列表 (JSON)',
    `authentication_info`     JSON    DEFAULT NULL COMMENT '认证信息数据 (JSON)',
    `border_data`             JSON    DEFAULT NULL COMMENT '边框数据',
    `pay_grade_data`          JSON    DEFAULT NULL COMMENT '付费等级数据',
    `fans_club_data`          JSON    DEFAULT NULL COMMENT '粉丝俱乐部完整数据 (JSON，包含 data 和 prefer_data)',
    `fans_group_info`         JSON    DEFAULT NULL COMMENT '粉丝群信息 (JSON)',
    `subscribe_data`          JSON    DEFAULT NULL COMMENT '订阅信息',
    `user_attr_data`          JSON    DEFAULT NULL COMMENT '用户属性',
    `user_dress_info_data`    JSON    DEFAULT NULL COMMENT '用户装扮信息',
    `biz_relation_data`       JSON    DEFAULT NULL COMMENT '业务关系',
    `j_accredit_info_data`    JSON    DEFAULT NULL COMMENT 'J 认证信息',
    `own_room_data`           JSON    DEFAULT NULL COMMENT '自己的房间列表',
    `total_recharge_diamond_count` BIGINT     DEFAULT 0 COMMENT '总充值钻石数',
    `watch_duration_month`    UNSIGNED INT      DEFAULT 0 COMMENT '观看时长 (月)',
    `web_rid`                 VARCHAR(100)      DEFAULT NULL COMMENT '网页 RID',
    `webcast_nick`            VARCHAR(50)       DEFAULT NULL COMMENT 'Webcast 昵称',
    `webcast_uid`             TEXT              DEFAULT NULL COMMENT 'Webcast UID',

    `created_at`  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at`  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (`room_id`),
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_nickname` (`nickname`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='主播信息表';
```

```shell
##
## room_owner
##
+---------------------------+-------------------+------+-----+---------+-------+---------------------------------------------+---------------------------------+
| Field                     | Type              | Null | Key | Default | Extra | Topology                                    | Comment                         |
+---------------------------+-------------------+------+-----+---------+-------+---------------------------------------------+---------------------------------+
| room_id                   | varchar(200)      | NO   | PRI | NULL    |       | "$.data.room.id"                            | 直播间 ID                       |
| user_id                   | varchar(200)      | YES  |     | NULL    |       | "$.data.room.owner.id"                      | 用户 ID                         |
| owner_open_id             | varchar(200)      | YES  |     | NULL    |       | "$.data.room.owner.owner_open_id"           | 主播 OpenID                     |
| owner_device_id           | bigint            | YES  |     | NULL    |       | "$.data.room.owner.owner_device_id"         | 主播设备 ID                     |
| sec_uid                   | text              | YES  |     | NULL    |       | "$.data.room.owner.sec_uid"                 | 安全用户 UID                    |
| user_open_id              | varchar(200)      | YES  |     | NULL    |       | "$.data.room.owner.user_open_id"            | 用户开放 ID                     |
| short_id                  | varchar(50)       | YES  |     | NULL    |       | "$.data.room.owner.short_id"                | 短 ID                           |
| display_id                | varchar(50)       | YES  |     | NULL    |       | "$.data.room.owner.display_id"              | 显示 ID                         |
| nickname                  | varchar(50)       | YES  |     | NULL    |       | "$.data.room.owner.nickname"                | 昵称                            |
| signature                 | text              | YES  |     | NULL    |       | "$.data.room.owner.signature"               | 签名                            |
| share_qrcode_uri          | text              | YES  |     | NULL    |       | "$.data.room.owner.share_qrcode_uri"        | 分享二维码 URI                  |
| special_id                | varchar(100)      | YES  |     | NULL    |       | "$.data.room.owner.special_id"              | 特殊 ID                         |
| status                    | unsigned tinyint  | YES  |     | 0       |       | "$.data.room.owner.status"                  | 用户状态                        |
| bg_img_url                | text              | YES  |     | NULL    |       | "$.data.room.owner.bg_img_url"              | 背景图片 URL                    |
| gender                    | unsigned tinyint  | YES  |     | 0       |       | "$.data.room.owner.gender"                  | 性别                            |
| city                      | varchar(100)      | YES  |     | NULL    |       | "$.data.room.owner.city"                    | 城市                            |
| constellation             | varchar(20)       | YES  |     | NULL    |       | "$.data.room.owner.constellation"           | 星座                            |
| age_range                 | unsigned tinyint  | YES  |     | 0       |       | "$.data.room.owner.age_range"               | 年龄范围                        |
| birthday                  | bigint            | YES  |     | 0       |       | "$.data.room.owner.birthday"                | 生日时间戳                      |
| birthday_description      | varchar(100)      | YES  |     | NULL    |       | "$.data.room.owner.birthday_description"    | 生日描述                        |
| birthday_valid            | bool              | YES  |     | FALSE   |       | "$.data.room.owner.birthday_valid"          | 生日是否有效                    |
| location_city             | varchar(100)      | YES  |     | NULL    |       | "$.data.room.owner.location_city"           | 位置城市                        |
| foreign_user              | unsigned tinyint  | YES  |     | 0       |       | "$.data.room.owner.foreign_user"            | 是否海外用户                    |
| mystery_man               | unsigned tinyint  | YES  |     | 0       |       | "$.data.room.owner.mystery_man"             | 神秘人标识                      |
| level                     | unsigned smallint | YES  |     | 0       |       | "$.data.room.owner.level"                   | 等级                            |
| exp                       | bigint            | YES  |     | 0       |       | "$.data.room.owner.exp"                     | 经验值                          |
| experience                | bigint            | YES  |     | 0       |       | "$.data.room.owner.experience"              | 经验                            |
| fan_ticket_count          | bigint            | YES  |     | 0       |       | "$.data.room.owner.fan_ticket_count"        | 粉丝票数量                      |
| consume_diamond_level     | unsigned tinyint  | YES  |     | 0       |       | "$.data.room.owner.consume_diamond_level"   | 消费钻石等级                    |
| income_share_percent      | unsigned tinyint  | YES  |     | 0       |       | "$.data.room.owner.income_share_percent"    | 收入分成比例                    |
| link_mic_stats            | unsigned tinyint  | YES  |     | 0       |       | "$.data.room.owner.link_mic_stats"          | 连麦统计                        |
| media_badge_image_list    | json              | YES  |     | NULL    |       | "$.data.room.owner.media_badge_image_list"  | 媒体勋章图片列表 (JSON)          |
| modify_time               | bigint            | YES  |     | 0       |       | "$.data.room.owner.modify_time"             | 修改时间戳                      |
| pay_score                 | bigint            | YES  |     | 0       |       | "$.data.room.owner.pay_score"               | 支付分数                        |
| pay_scores                | bigint            | YES  |     | 0       |       | "$.data.room.owner.pay_scores"              | 支付分数 (复数)                 |
| need_profile_guide        | bool              | YES  |     | FALSE   |       | "$.data.room.owner.need_profile_guide"      | 需要资料引导                    |
| new_real_time_icons       | json              | YES  |     | NULL    |       | "$.data.room.owner.new_real_time_icons"     | 新实时图标列表 (JSON)            |
| real_time_icons           | json              | YES  |     | NULL    |       | "$.data.room.owner.real_time_icons"         | 实时图标列表 (JSON)              |
| follow_status             | unsigned tinyint  | YES  |     | 0       |       | "$.data.room.owner.follow_status"           | 关注状态                        |
| is_follower               | bool              | YES  |     | FALSE   |       | "$.data.room.owner.is_follower"             | 是否粉丝                        |
| is_following              | bool              | YES  |     | FALSE   |       | "$.data.room.owner.is_following"            | 是否关注                        |
| follow_info               | json              | YES  |     | NULL    |       | "$.data.room.owner.follow_info"             | 关注信息 (JSON)                  |
| is_anonymous              | bool              | YES  |     | FALSE   |       | "$.data.room.owner.is_anonymous"            | 是否匿名                        |
| hotsoon_verified          | bool              | YES  |     | FALSE   |       | "$.data.room.owner.hotsoon_verified"        | 是否快手认证                    |
| hotsoon_verified_reason   | varchar(255)      | YES  |     | NULL    |       | "$.data.room.owner.hotsoon_verified_reason" | 快手认证原因                    |
| ichat_restrict_type       | unsigned tinyint  | YES  |     | 0       |       | "$.data.room.owner.ichat_restrict_type"     | 聊天限制类型                    |
| disable_ichat             | unsigned tinyint  | YES  |     | 0       |       | "$.data.room.owner.disable_ichat"           | 禁用聊天                        |
| enable_ichat_img          | unsigned tinyint  | YES  |     | 0       |       | "$.data.room.owner.enable_ichat_img"        | 启用聊天图片                    |
| fold_stranger_chat        | bool              | YES  |     | FALSE   |       | "$.data.room.owner.fold_stranger_chat"      | 折叠陌生人聊天                  |
| desensitized_nickname     | varchar(50)       | YES  |     | NULL    |       | "$.data.room.owner.desensitized_nickname"   | 脱敏昵称                        |
| verified                  | bool              | YES  |     | 0       |       | "$.data.room.owner.verified"                | 是否认证                        |
| verified_reason           | varchar(255)      | YES  |     | NULL    |       | "$.data.room.owner.verified_reason"         | 认证原因                        |
| verified_content          | text              | YES  |     | NULL    |       | "$.data.room.owner.verified_content"        | 认证内容                        |
| verified_mobile           | bool              | YES  |     | FALSE   |       | "$.data.room.owner.verified_mobile"         | 是否手机认证                    |
| enterprise_verify_reason  | varchar(255)      | YES  |     | NULL    |       | "$.data.room.owner.authentication_info.enterprise_verify_reason" | 企业认证原因     |
| custom_verify             | varchar(100)      | YES  |     | NULL    |       | "$.data.room.owner.authentication_info.custom_verify" | 自定义认证     |
| block_status              | unsigned tinyint  | YES  |     | 0       |       | "$.data.room.owner.block_status"            | 屏蔽状态                        |
| comment_restrict          | unsigned tinyint  | YES  |     | 0       |       | "$.data.room.owner.comment_restrict"        | 评论限制                        |
| public_area_oper_freq     | unsigned tinyint  | YES  |     | 0       |       | "$.data.room.owner.public_area_oper_freq"   | 公共区域操作频率                |
| push_comment_status       | bool              | YES  |     | FALSE   |       | "$.data.room.owner.push_comment_status"     | 推送评论状态                    |
| push_digg                 | bool              | YES  |     | FALSE   |       | "$.data.room.owner.push_digg"               | 推送点赞                        |
| push_follow               | bool              | YES  |     | FALSE   |       | "$.data.room.owner.push_follow"             | 推送关注                        |
| push_friend_action        | bool              | YES  |     | FALSE   |       | "$.data.room.owner.push_friend_action"      | 推送好友动态                    |
| push_ichat                | bool              | YES  |     | FALSE   |       | "$.data.room.owner.push_ichat"              | 推送聊天                        |
| push_status               | bool              | YES  |     | FALSE   |       | "$.data.room.owner.push_status"             | 推送状态                        |
| push_video_post           | bool              | YES  |     | FALSE   |       | "$.data.room.owner.push_video_post"         | 推送视频发布                    |
| push_video_recommend      | bool              | YES  |     | FALSE   |       | "$.data.room.owner.push_video_recommend"    | 推送视频推荐                    |
| remark_name               | varchar(50)       | YES  |     | NULL    |       | "$.data.room.owner.remark_name"             | 备注名                          |
| secret                    | unsigned tinyint  | YES  |     | 0       |       | "$.data.room.owner.secret"                  | 隐私设置                        |
| user_role                 | unsigned tinyint  | YES  |     | 0       |       | "$.data.room.owner.user_role"               | 用户角色                        |
| webcast_private           | unsigned tinyint  | YES  |     | 0       |       | "$.data.room.owner.webcast_private"         | 直播隐私设置                    |
| can_view_webcast_private  | unsigned tinyint  | YES  |     | 0       |       | "$.data.room.owner.can_view_webcast_private"| 是否可观看直播隐私              |
| user_canceled             | bool              | YES  |     | FALSE   |       | "$.data.room.owner.user_canceled"           | 用户是否已注销                  |
| telephone                 | varchar(20)       | YES  |     | NULL    |       | "$.data.room.owner.telephone"               | 电话号码                        |
| with_commerce_permission  | bool              | YES  |     | 0       |       | "$.data.room.owner.with_commerce_permission"| 商务权限                        |
| with_fusion_shop_entry    | bool              | YES  |     | 0       |       | "$.data.room.owner.with_fusion_shop_entry"  | 融合店铺入口                    |
| with_car_management_permission | bool         | YES  |     | 0       |       | "$.data.room.owner.with_car_management_permission" | 汽车管理权限         |
| adversary_authorization_info | unsigned tinyint | YES | | 0 | | "$.data.room.owner.adversary_authorization_info" | 对手授权信息     |
| adversary_user_status     | unsigned tinyint  | YES  |     | 0       |       | "$.data.room.owner.adversary_user_status"   | 对手用户状态                    |
| authorization_info        | unsigned tinyint  | YES  |     | 0       |       | "$.data.room.owner.authorization_info"      | 授权信息                        |
| allow_be_located          | bool              | YES  |     | 0       |       | "$.data.room.owner.allow_be_located"        | 允许被定位                      |
| allow_find_by_contacts    | bool              | YES  |     | 0       |       | "$.data.room.owner.allow_find_by_contacts"  | 允许通过联系人找到              |
| allow_others_download_video | bool            | YES  |     | 0       |       | "$.data.room.owner.allow_others_download_video" | 允许他人下载视频            |
| allow_others_download_when_sharing_video | bool | YES | | 0 | | "$.data.room.owner.allow_others_download_when_sharing_video" | 分享视频时允许他人下载 |
| allow_share_show_profile  | bool              | YES  |     | 0       |       | "$.data.room.owner.allow_share_show_profile"| 允许分享显示资料                |
| allow_show_in_gossip      | bool              | YES  |     | 0       |       | "$.data.room.owner.allow_show_in_gossip"    | 允许在闲聊中显示                |
| allow_show_my_action      | bool              | YES  |     | 0       |       | "$.data.room.owner.allow_show_my_action"    | 允许显示我的动态                |
| allow_strange_comment     | bool              | YES  |     | 0       |       | "$.data.room.owner.allow_strange_comment"   | 允许陌生人评论                  |
| allow_unfollower_comment  | bool              | YES  |     | 0       |       | "$.data.room.owner.allow_unfollower_comment"| 允许未关注者评论                |
| allow_use_linkmic         | bool              | YES  |     | 0       |       | "$.data.room.owner.allow_use_linkmic"       | 允许使用连麦                    |
| avatar_large              | json              | YES  |     | NULL    |       | "$.data.room.owner.avatar_large"            | 大头像数据 (JSON)                |
| avatar_medium             | json              | YES  |     | NULL    |       | "$.data.room.owner.avatar_medium"           | 中等头像数据 (JSON)              |
| avatar_thumb              | json              | YES  |     | NULL    |       | "$.data.room.owner.avatar_thumb"            | 缩略头像数据 (JSON)              |
| badge_image_list          | json              | YES  |     | NULL    |       | "$.data.room.owner.badge_image_list"        | 勋章图片列表 (JSON)              |
| badge_image_list_v2       | json              | YES  |     | NULL    |       | "$.data.room.owner.badge_image_list_v2"     | 勋章图片列表 V2 (JSON)           |
| commerce_webcast_config_ids | json            | YES  |     | NULL    |       | "$.data.room.owner.commerce_webcast_config_ids" | 商业直播配置 ID 列表 (JSON)    |
| authentication_info       | json              | YES  |     | NULL    |       | "$.data.room.owner.authentication_info"     | 认证信息数据 (JSON) |
| border_data               | json              | YES  |     | NULL    |       | "$.data.room.owner.border"                  | 边框数据 (JSON)                  |
| pay_grade_data            | json              | YES  |     | NULL    |       | "$.data.room.owner.pay_grade"               | 付费等级数据 (JSON)              |
| fans_club_data            | json              | YES  |     | NULL    |       | "$.data.room.owner.fans_club"               | 粉丝俱乐部完整数据 (JSON，包含 data 和 prefer_data) |
| fans_group_info           | json              | YES  |     | NULL    |       | "$.data.room.owner.fans_group_info"         | 粉丝群信息 (JSON)                |
| subscribe_data            | json              | YES  |     | NULL    |       | "$.data.room.owner.subscribe"               | 订阅信息 (JSON)                  |
| user_attr_data            | json              | YES  |     | NULL    |       | "$.data.room.owner.user_attr"               | 用户属性数据 (JSON)              |
| user_dress_info_data      | json              | YES  |     | NULL    |       | "$.data.room.owner.user_dress_info"         | 用户装扮数据 (JSON)              |
| biz_relation_data         | json              | YES  |     | NULL    |       | "$.data.room.owner.biz_relation"            | 业务关系数据 (JSON)              |
| j_accredit_info_data      | json              | YES  |     | NULL    |       | "$.data.room.owner.j_accredit_info"         | J 认证信息 (JSON)                 |
| own_room_data             | json              | YES  |     | NULL    |       | "$.data.room.owner.own_room"                | 自己的房间数据 (JSON)            |
| total_recharge_diamond_count | bigint         | YES  |     | 0       |       | "$.data.room.owner.total_recharge_diamond_count" | 总充值钻石数    |
| watch_duration_month      | unsigned int      | YES  |     | 0       |       | "$.data.room.owner.watch_duration_month"    | 观看时长 (月)                    |
| web_rid                   | varchar(100)      | YES  |     | NULL    |       | "$.data.room.owner.web_rid"                 | 网页 RID                        |
| webcast_nick              | varchar(50)       | YES  |     | NULL    |       | "$.data.room.owner.webcast_nick"            | Webcast 昵称                    |
| webcast_uid               | text              | YES  |     | NULL    |       | "$.data.room.owner.webcast_uid"             | Webcast UID                     |
| created_at                | timestamp         | YES  |     | NOW   |       | -                                           | 创建时间                        |
| updated_at                | timestamp         | YES  |     | NOW   |       | -                                           | 更新时间                        |
+---------------------------+-------------------+------+-----+---------+-------+---------------------------------------------+---------------------------------+
```

#### 5-4. 用户信息表 - user

```sql
CREATE TABLE IF NOT EXISTS `user` (
    `id`                                       VARCHAR(200)      NOT NULL,
    `adversary_authorization_info`             UNSIGNED TINYINT  DEFAULT 0,
    `adversary_user_status`                    UNSIGNED TINYINT  DEFAULT 0,
    `age_range`                                UNSIGNED TINYINT  DEFAULT 0,
    `allow_be_located`                         BOOL              DEFAULT FALSE,
    `allow_find_by_contacts`                   BOOL              DEFAULT FALSE,
    `allow_others_download_video`              BOOL              DEFAULT FALSE,
    `allow_others_download_when_sharing_video` BOOL              DEFAULT FALSE,
    `allow_share_show_profile`                 BOOL              DEFAULT FALSE,
    `allow_show_in_gossip`                     BOOL              DEFAULT FALSE,
    `allow_show_my_action`                     BOOL              DEFAULT FALSE,
    `allow_strange_comment`                    BOOL              DEFAULT FALSE,
    `allow_unfollower_comment`                 BOOL              DEFAULT FALSE,
    `allow_use_linkmic`                        BOOL              DEFAULT FALSE,
    `authorization_info`                       UNSIGNED TINYINT  DEFAULT 0,
    `badge_image_list`                         JSON              DEFAULT NULL,
    `badge_image_list_v2`                      JSON              DEFAULT NULL,
    `bg_img_url`                               TEXT              DEFAULT NULL,
    `birthday`                                 BIGINT            DEFAULT 0,
    `birthday_description`                     VARCHAR(100)      DEFAULT NULL,
    `birthday_valid`                           BOOL              DEFAULT FALSE,
    `block_status`                             UNSIGNED TINYINT  DEFAULT 0,
    `city`                                     VARCHAR(100)      DEFAULT NULL,
    `comment_restrict`                         UNSIGNED TINYINT  DEFAULT 0,
    `commerce_webcast_config_ids`              JSON              DEFAULT NULL,
    `constellation`                            VARCHAR(20)       DEFAULT NULL,
    `consume_diamond_level`                    UNSIGNED TINYINT  DEFAULT 0,
    `create_time`                              BIGINT            DEFAULT 0,
    `desensitized_nickname`                    VARCHAR(50)       DEFAULT NULL,
    `disable_ichat`                            UNSIGNED TINYINT  DEFAULT 0,
    `display_id`                               VARCHAR(50)       DEFAULT NULL,
    `enable_ichat_img`                         UNSIGNED TINYINT  DEFAULT 0,
    `exp`                                      BIGINT            DEFAULT 0,
    `experience`                               BIGINT            DEFAULT 0,
    `fan_ticket_count`                         BIGINT            DEFAULT 0,
    `fold_stranger_chat`                       BOOL              DEFAULT FALSE,
    `follow_status`                            UNSIGNED TINYINT  DEFAULT 0,
    `foreign_user`                             UNSIGNED TINYINT  DEFAULT 0,
    `gender`                                   UNSIGNED TINYINT  DEFAULT 0,
    `hotsoon_verified`                         BOOL              DEFAULT FALSE,
    `hotsoon_verified_reason`                  VARCHAR(255)      DEFAULT NULL,
    `ichat_restrict_type`                      UNSIGNED TINYINT  DEFAULT 0,
    `income_share_percent`                     UNSIGNED TINYINT  DEFAULT 0,
    `is_anonymous`                             BOOL              DEFAULT FALSE,
    `is_follower`                              BOOL              DEFAULT FALSE,
    `is_following`                             BOOL              DEFAULT FALSE,
    `level`                                    UNSIGNED SMALLINT DEFAULT 0,
    `link_mic_stats`                           UNSIGNED TINYINT  DEFAULT 0,
    `location_city`                            VARCHAR(100)      DEFAULT NULL,
    `media_badge_image_list`                   JSON              DEFAULT NULL,
    `modify_time`                              BIGINT            DEFAULT 0,
    `mystery_man`                              UNSIGNED TINYINT  DEFAULT 0,
    `need_profile_guide`                       BOOL              DEFAULT FALSE,
    `new_real_time_icons`                      JSON              DEFAULT NULL,
    `nickname`                                 VARCHAR(50)       DEFAULT NULL,
    `pay_score`                                BIGINT            DEFAULT 0,
    `pay_scores`                               BIGINT            DEFAULT 0,
    `public_area_oper_freq`                    UNSIGNED TINYINT  DEFAULT 0,
    `push_comment_status`                      BOOL              DEFAULT FALSE,
    `push_digg`                                BOOL              DEFAULT FALSE,
    `push_follow`                              BOOL              DEFAULT FALSE,
    `push_friend_action`                       BOOL              DEFAULT FALSE,
    `push_ichat`                               BOOL              DEFAULT FALSE,
    `push_status`                              BOOL              DEFAULT FALSE,
    `push_video_post`                          BOOL              DEFAULT FALSE,
    `push_video_recommend`                     BOOL              DEFAULT FALSE,
    `real_time_icons`                          JSON              DEFAULT NULL,
    `remark_name`                              VARCHAR(50)       DEFAULT NULL,
    `sec_uid`                                  TEXT              DEFAULT NULL,
    `secret`                                   UNSIGNED TINYINT  DEFAULT 0,
    `share_qrcode_uri`                         TEXT              DEFAULT NULL,
    `short_id`                                 VARCHAR(50)       DEFAULT NULL,
    `signature`                                TEXT              DEFAULT NULL,
    `special_id`                               VARCHAR(100)      DEFAULT NULL,
    `status`                                   UNSIGNED TINYINT  DEFAULT 0,
    `telephone`                                VARCHAR(20)       DEFAULT NULL,
    `ticket_count`                             BIGINT            DEFAULT 0,
    `top_fans`                                 JSON              DEFAULT NULL,
    `top_vip_no`                               UNSIGNED INT      DEFAULT 0,
    `total_recharge_diamond_count`             BIGINT            DEFAULT 0,
    `user_canceled`                            BOOL              DEFAULT FALSE,
    `user_open_id`                             VARCHAR(200)      DEFAULT NULL,
    `user_role`                                UNSIGNED TINYINT  DEFAULT 0,
    `verified`                                 BOOL              DEFAULT FALSE,
    `verified_content`                         TEXT              DEFAULT NULL,
    `verified_mobile`                          BOOL              DEFAULT FALSE,
    `verified_reason`                          VARCHAR(255)      DEFAULT NULL,
    `watch_duration_month`                     UNSIGNED INT      DEFAULT 0,
    `web_rid`                                  VARCHAR(100)      DEFAULT NULL,
    `webcast_uid`                              TEXT              DEFAULT NULL,
    `with_car_management_permission`           BOOL              DEFAULT FALSE,
    `with_commerce_permission`                 BOOL              DEFAULT FALSE,
    `with_fusion_shop_entry`                   BOOL              DEFAULT FALSE,
    `can_view_webcast_private`                 UNSIGNED TINYINT  DEFAULT 0,
    `webcast_nick`                             VARCHAR(50)       DEFAULT NULL,
    `webcast_private`                          UNSIGNED TINYINT  DEFAULT 0,
    `hide_by_room`                             UNSIGNED TINYINT  DEFAULT 0,
    `link_mask`                                UNSIGNED TINYINT  DEFAULT 0,
    `created_at`                               TIMESTAMP         DEFAULT CURRENT_TIMESTAMP,
    `updated_at`                               TIMESTAMP         DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户信息表';
```

```shell
##
## user
##
+--------------------------------------+-------------------+------+-----+---------------------+-------+---------------------------------------------+----------------------+
| Field                                | Type              | Null | Key | Default             | Extra | Topology                                    | Comment              |
+--------------------------------------+-------------------+------+-----+---------------------+-------+---------------------------------------------+----------------------+
| id                                   | varchar(200)      | NO   | PRI |                     |       | "$.data.user.id"                            | 用户 ID              |
| adversary_authorization_info         | unsigned tinyint  | YES  |     | 0                   |       | "$.data.user.adversary_authorization_info"  | 对手授权信息         |
| adversary_user_status                | unsigned tinyint  | YES  |     | 0                   |       | "$.data.user.adversary_user_status"         | 对手用户状态         |
| age_range                            | unsigned tinyint  | YES  |     | 0                   |       | "$.data.user.age_range"                     | 年龄范围             |
| allow_be_located                     | bool              | YES  |     | FALSE               |       | "$.data.user.allow_be_located"              | 允许被定位           |
| allow_find_by_contacts               | bool              | YES  |     | FALSE               |       | "$.data.user.allow_find_by_contacts"        | 允许通过联系人找到   |
| allow_others_download_video          | bool              | YES  |     | FALSE               |       | "$.data.user.allow_others_download_video"   | 允许他人下载视频     |
| allow_others_download_when_sharing_video | bool         | YES  |     | FALSE               |       | "$.data.user.allow_others_download_when_sharing_video" | 分享视频时允许下载 |
| allow_share_show_profile             | bool              | YES  |     | FALSE               |       | "$.data.user.allow_share_show_profile"      | 允许分享展示资料     |
| allow_show_in_gossip                 | bool              | YES  |     | FALSE               |       | "$.data.user.allow_show_in_gossip"          | 允许在闲聊中展示     |
| allow_show_my_action                 | bool              | YES  |     | FALSE               |       | "$.data.user.allow_show_my_action"          | 允许展示我的动态     |
| allow_strange_comment                | bool              | YES  |     | FALSE               |       | "$.data.user.allow_strange_comment"         | 允许陌生人评论       |
| allow_unfollower_comment             | bool              | YES  |     | FALSE               |       | "$.data.user.allow_unfollower_comment"      | 允许未关注者评论     |
| allow_use_linkmic                    | bool              | YES  |     | FALSE               |       | "$.data.user.allow_use_linkmic"             | 允许使用连麦         |
| authorization_info                   | unsigned tinyint  | YES  |     | 0                   |       | "$.data.user.authorization_info"            | 授权信息             |
| badge_image_list                     | json              | YES  |     | NULL                |       | "$.data.user.badge_image_list"              | 徽章列表             |
| badge_image_list_v2                  | json              | YES  |     | NULL                |       | "$.data.user.badge_image_list_v2"           | 徽章列表 V2          |
| bg_img_url                           | text              | YES  |     | NULL                |       | "$.data.user.bg_img_url"                    | 背景图 URL           |
| birthday                             | bigint            | YES  |     | 0                   |       | "$.data.user.birthday"                      | 生日时间戳           |
| birthday_description                 | varchar(100)      | YES  |     | NULL                |       | "$.data.user.birthday_description"          | 生日描述             |
| birthday_valid                       | bool              | YES  |     | FALSE               |       | "$.data.user.birthday_valid"                | 生日是否有效         |
| block_status                         | unsigned tinyint  | YES  |     | 0                   |       | "$.data.user.block_status"                  | 屏蔽状态             |
| city                                 | varchar(100)      | YES  |     | NULL                |       | "$.data.user.city"                          | 城市                 |
| comment_restrict                     | unsigned tinyint  | YES  |     | 0                   |       | "$.data.user.comment_restrict"              | 评论限制             |
| commerce_webcast_config_ids          | json              | YES  |     | NULL                |       | "$.data.user.commerce_webcast_config_ids"   | 电商直播配置 IDs     |
| constellation                        | varchar(20)       | YES  |     | NULL                |       | "$.data.user.constellation"                 | 星座                 |
| consume_diamond_level                | unsigned tinyint  | YES  |     | 0                   |       | "$.data.user.consume_diamond_level"         | 消费钻石等级         |
| create_time                          | bigint            | YES  |     | 0                   |       | "$.data.user.create_time"                   | 创建时间             |
| desensitized_nickname                | varchar(50)       | YES  |     | NULL                |       | "$.data.user.desensitized_nickname"         | 脱敏昵称             |
| disable_ichat                        | unsigned tinyint  | YES  |     | 0                   |       | "$.data.user.disable_ichat"                 | 禁用聊天             |
| display_id                           | varchar(50)       | YES  |     | NULL                |       | "$.data.user.display_id"                    | 展示 ID              |
| enable_ichat_img                     | unsigned tinyint  | YES  |     | 0                   |       | "$.data.user.enable_ichat_img"              | 启用聊天图片         |
| exp                                  | bigint            | YES  |     | 0                   |       | "$.data.user.exp"                           | 经验值               |
| experience                           | bigint            | YES  |     | 0                   |       | "$.data.user.experience"                    | 经验                 |
| fan_ticket_count                     | bigint            | YES  |     | 0                   |       | "$.data.user.fan_ticket_count"              | 粉丝票数             |
| fold_stranger_chat                   | bool              | YES  |     | FALSE               |       | "$.data.user.fold_stranger_chat"            | 折叠陌生人聊天       |
| follow_status                        | unsigned tinyint  | YES  |     | 0                   |       | "$.data.user.follow_status"                 | 关注状态             |
| foreign_user                         | unsigned tinyint  | YES  |     | 0                   |       | "$.data.user.foreign_user"                  | 是否海外用户         |
| gender                               | unsigned tinyint  | YES  |     | 0                   |       | "$.data.user.gender"                        | 性别                 |
| hotsoon_verified                     | bool              | YES  |     | FALSE               |       | "$.data.user.hotsoon_verified"              | 快手认证             |
| hotsoon_verified_reason              | varchar(255)      | YES  |     | NULL                |       | "$.data.user.hotsoon_verified_reason"       | 快手认证原因         |
| ichat_restrict_type                  | unsigned tinyint  | YES  |     | 0                   |       | "$.data.user.ichat_restrict_type"           | 聊天限制类型         |
| income_share_percent                 | unsigned tinyint  | YES  |     | 0                   |       | "$.data.user.income_share_percent"          | 收入分成比例         |
| is_anonymous                         | bool              | YES  |     | FALSE               |       | "$.data.user.is_anonymous"                  | 是否匿名             |
| is_follower                          | bool              | YES  |     | FALSE               |       | "$.data.user.is_follower"                   | 是否粉丝             |
| is_following                         | bool              | YES  |     | FALSE               |       | "$.data.user.is_following"                  | 是否关注             |
| level                                | unsigned smallint | YES  |     | 0                   |       | "$.data.user.level"                         | 等级                 |
| link_mic_stats                       | unsigned tinyint  | YES  |     | 0                   |       | "$.data.user.link_mic_stats"                | 连麦统计             |
| location_city                        | varchar(100)      | YES  |     | NULL                |       | "$.data.user.location_city"                 | 定位城市             |
| media_badge_image_list               | json              | YES  |     | NULL                |       | "$.data.user.media_badge_image_list"        | 媒体徽章列表         |
| modify_time                          | bigint            | YES  |     | 0                   |       | "$.data.user.modify_time"                   | 修改时间             |
| mystery_man                          | unsigned tinyint  | YES  |     | 0                   |       | "$.data.user.mystery_man"                   | 神秘人标识           |
| need_profile_guide                   | bool              | YES  |     | FALSE               |       | "$.data.user.need_profile_guide"            | 需要资料引导         |
| new_real_time_icons                  | json              | YES  |     | NULL                |       | "$.data.user.new_real_time_icons"           | 新实时图标           |
| nickname                             | varchar(50)       | YES  |     | NULL                |       | "$.data.user.nickname"                      | 昵称                 |
| pay_score                            | bigint            | YES  |     | 0                   |       | "$.data.user.pay_score"                     | 支付分数             |
| pay_scores                           | bigint            | YES  |     | 0                   |       | "$.data.user.pay_scores"                    | 支付分数（复数）     |
| public_area_oper_freq                | unsigned tinyint  | YES  |     | 0                   |       | "$.data.user.public_area_oper_freq"         | 公共区域操作频率     |
| push_comment_status                  | bool              | YES  |     | FALSE               |       | "$.data.user.push_comment_status"           | 推送评论状态         |
| push_digg                            | bool              | YES  |     | FALSE               |       | "$.data.user.push_digg"                     | 推送点赞             |
| push_follow                          | bool              | YES  |     | FALSE               |       | "$.data.user.push_follow"                   | 推送关注             |
| push_friend_action                   | bool              | YES  |     | FALSE               |       | "$.data.user.push_friend_action"            | 推送好友动态         |
| push_ichat                           | bool              | YES  |     | FALSE               |       | "$.data.user.push_ichat"                    | 推送聊天             |
| push_status                          | bool              | YES  |     | FALSE               |       | "$.data.user.push_status"                   | 推送状态             |
| push_video_post                      | bool              | YES  |     | FALSE               |       | "$.data.user.push_video_post"               | 推送视频发布         |
| push_video_recommend                 | bool              | YES  |     | FALSE               |       | "$.data.user.push_video_recommend"          | 推送视频推荐         |
| real_time_icons                      | json              | YES  |     | NULL                |       | "$.data.user.real_time_icons"               | 实时图标             |
| remark_name                          | varchar(50)       | YES  |     | NULL                |       | "$.data.user.remark_name"                   | 备注名               |
| sec_uid                              | text              | YES  |     | NULL                |       | "$.data.user.sec_uid"                       | 安全 UID             |
| secret                               | unsigned tinyint  | YES  |     | 0                   |       | "$.data.user.secret"                        | 隐私设置             |
| share_qrcode_uri                     | text              | YES  |     | NULL                |       | "$.data.user.share_qrcode_uri"              | 分享二维码 URI       |
| short_id                             | varchar(50)       | YES  |     | NULL                |       | "$.data.user.short_id"                      | 短 ID                |
| signature                            | text              | YES  |     | NULL                |       | "$.data.user.signature"                     | 签名                 |
| special_id                           | varchar(100)      | YES  |     | NULL                |       | "$.data.user.special_id"                    | 特殊 ID              |
| status                               | unsigned tinyint  | YES  |     | 0                   |       | "$.data.user.status"                        | 状态                 |
| telephone                            | varchar(20)       | YES  |     | NULL                |       | "$.data.user.telephone"                     | 电话                 |
| ticket_count                         | bigint            | YES  |     | 0                   |       | "$.data.user.ticket_count"                  | 门票数               |
| top_fans                             | json              | YES  |     | NULL                |       | "$.data.user.top_fans"                      | 头部粉丝列表         |
| top_vip_no                           | unsigned int      | YES  |     | 0                   |       | "$.data.user.top_vip_no"                    | VIP 排名             |
| total_recharge_diamond_count         | bigint            | YES  |     | 0                   |       | "$.data.user.total_recharge_diamond_count"  | 总充值钻石           |
| user_canceled                        | bool              | YES  |     | FALSE               |       | "$.data.user.user_canceled"                 | 用户是否注销         |
| user_open_id                         | varchar(200)      | YES  |     | NULL                |       | "$.data.user.user_open_id"                  | 用户开放 ID          |
| user_role                            | unsigned tinyint  | YES  |     | 0                   |       | "$.data.user.user_role"                     | 用户角色             |
| verified                             | bool              | YES  |     | FALSE               |       | "$.data.user.verified"                      | 是否认证             |
| verified_content                     | text              | YES  |     | NULL                |       | "$.data.user.verified_content"              | 认证内容             |
| verified_mobile                      | bool              | YES  |     | FALSE               |       | "$.data.user.verified_mobile"               | 是否手机认证         |
| verified_reason                      | varchar(255)      | YES  |     | NULL                |       | "$.data.user.verified_reason"               | 认证原因             |
| watch_duration_month                 | unsigned int      | YES  |     | 0                   |       | "$.data.user.watch_duration_month"          | 月观看时长           |
| web_rid                              | varchar(100)      | YES  |     | NULL                |       | "$.data.user.web_rid"                       | 网页 RID             |
| webcast_uid                          | text              | YES  |     | NULL                |       | "$.data.user.webcast_uid"                   | Webcast UID          |
| with_car_management_permission       | bool              | YES  |     | FALSE               |       | "$.data.user.with_car_management_permission"| 座驾管理权限         |
| with_commerce_permission             | bool              | YES  |     | FALSE               |       | "$.data.user.with_commerce_permission"      | 电商权限             |
| with_fusion_shop_entry               | bool              | YES  |     | FALSE               |       | "$.data.user.with_fusion_shop_entry"        | 融合店铺入口         |
| can_view_webcast_private             | unsigned tinyint  | YES  |     | 0                   |       | "$.data.user.can_view_webcast_private"      | 可见私密直播         |
| webcast_nick                         | varchar(50)       | YES  |     | NULL                |       | "$.data.user.webcast_nick"                  | Webcast 昵称         |
| webcast_private                      | unsigned tinyint  | YES  |     | 0                   |       | "$.data.user.webcast_private"               | 私密直播状态         |
| hide_by_room                         | unsigned tinyint  | YES  |     | 0                   |       | "$.data.user.hide_by_room"                  | 房间隐藏标记         |
| link_mask                            | unsigned tinyint  | YES  |     | 0                   |       | "$.data.user.link_mask"                     | 连麦掩码             |
| created_at                           | timestamp         | YES  |     | CURRENT_TIMESTAMP   |       | -                                           | 创建时间             |
| updated_at                           | timestamp         | YES  |     | CURRENT_TIMESTAMP   |       | -                                           | 更新时间             |
+--------------------------------------+-------------------+------+-----+---------------------+-------+---------------------------------------------+----------------------+
```

### 3.3 扩展表

#### 6. 直播间管理员表 - room_admin_user_id

```sql
CREATE TABLE IF NOT EXISTS `room_admin_user_id` (
    `platform`        VARCHAR(20)       NOT NULL COMMENT '平台',
    `room_id`         VARCHAR(200)      NOT NULL COMMENT '直播间ID',
    `index`           BIGINT            NOT NULL AUTO_INCREMENT COMMENT '直播间管理员ID序号',
    `admin_user_id`   VARCHAR(200)      DEFAULT NULL COMMENT '直播间管理员用户ID',
    PRIMARY KEY (`index`, `platform`, `room_id`),
    UNIQUE KEY `unique_record` (`platform`, `room_id`, `admin_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='直播间管理员表';
```

```shell
##
## $.data.room.admin_user_ids
##
+-------------------+--------------+------+-----+---------+-------+------------------------------+---------------------+
| Field             | Type         | Null | Key | Default | Extra | Topology                     | Comment             |
+-------------------+--------------+------+-----+---------+-------+------------------------------+---------------------+
| platform          | varchar(20)  | NO   | PRI |         |       |           -                  | 平台                 |
| room_id           | varchar(200) | NO   | PRI |         |       | "$.data.room.id"             | 直播间ID             |
| index             | bigint       | NO   | PRI |         | auto_increment |           -      | 直播间管理员ID序号    |
| admin_user_id     | varchar(200) | YES  |     | NULL    |       | "$.data.room.admin_user_ids" | 直播间管理员用户ID    |
+-------------------+--------------+------+-----+---------+-------+------------------------------+---------------------+
```

#### 6-1. 直播间管理员用户开放 ID 表 - room_admin_user_open_id

```sql
CREATE TABLE IF NOT EXISTS `room_admin_user_open_id` (
    `platform`              VARCHAR(20)       NOT NULL COMMENT '平台',
    `room_id`               VARCHAR(200)      NOT NULL COMMENT '直播间ID',
    `index`                 BIGINT            NOT NULL AUTO_INCREMENT COMMENT '直播间管理员用户ID序号',
    `admin_user_open_id`    VARCHAR(200)      DEFAULT NULL COMMENT '直播间管理员用户ID',
    PRIMARY KEY (`index`, `platform`, `room_id`),
    UNIQUE KEY `unique_record` (`platform`, `room_id`, `admin_user_open_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='直播间管理员用户开放 ID 表';
```

```shell
##
## $.data.room.admin_user_open_ids
##
+--------------------------+-------------------+------+-----+---------+----------------+-----------------------------------+---------------------+
| Field                    | Type              | Null | Key | Default | Extra          | Topology                          | Comment             |
+--------------------------+-------------------+------+-----+---------+----------------+-----------------------------------+---------------------+
| platform                 | varchar(20)       | NO   | PRI |         |                | -                                 | 平台                |
| room_id                  | varchar(200)      | NO   | PRI |         |                | "$.data.room.id"                  | 直播间ID            |
| index                    | bigint            | NO   | PRI |         | auto_increment | -                                 | 直播间管理员用户ID序号|
| admin_user_open_id       | varchar(200)      | YES  |     | NULL    |                | "$.data.room.admin_user_open_ids" | 直播间管理员用户ID   |
+--------------------------+-------------------+------+-----+---------+----------------+-----------------------------------+---------------------+
```

#### 7. 直播间装饰表 - room_deco

```sql
CREATE TABLE IF NOT EXISTS `room_deco` (
    `platform`        VARCHAR(20)       NOT NULL COMMENT '平台',
    `room_id`         VARCHAR(200)      NOT NULL COMMENT '直播间 ID',
    `deco_index`      UNSIGNED TINYINT  NOT NULL AUTO_INCREMENT COMMENT '装饰索引',
    `deco_id`         UNSIGNED INT      DEFAULT NULL COMMENT '装饰 ID',
    `deco_type`       UNSIGNED TINYINT  DEFAULT NULL COMMENT '装饰类型',
    `kind`            UNSIGNED TINYINT  DEFAULT NULL COMMENT '种类',
    `audit_text_color` VARCHAR(7)       DEFAULT NULL COMMENT '审核文本颜色',
    `content`         TINYTEXT          DEFAULT NULL COMMENT '装饰内容',
    `status`          UNSIGNED TINYINT  DEFAULT NULL COMMENT '状态',
    `text_color`      VARCHAR(7)        DEFAULT NULL COMMENT '文本颜色',
    `text_size`       UNSIGNED INT      DEFAULT NULL COMMENT '文本大小',
    `position_x`      UNSIGNED INT      DEFAULT NULL COMMENT 'X 坐标',
    `position_y`      UNSIGNED INT      DEFAULT NULL COMMENT 'Y 坐标',
    `width`           UNSIGNED INT      DEFAULT NULL COMMENT '宽度',
    `height`          UNSIGNED INT      DEFAULT NULL COMMENT '高度',
    `max_length`      UNSIGNED TINYINT  DEFAULT NULL COMMENT '最大长度',
    `sub_type`        UNSIGNED TINYINT  DEFAULT NULL COMMENT '子类型',
    `text_image_adjustable_start_position` UNSIGNED INT DEFAULT NULL COMMENT '文本图片可调整开始位置',
    `text_image_adjustable_end_position`   UNSIGNED INT DEFAULT NULL COMMENT '文本图片可调整结束位置',
    `input_rect`      JSON              DEFAULT NULL COMMENT '输入框矩形 (JSON)',
    `nine_patch_image` JSON             DEFAULT NULL COMMENT '九宫格图片 (JSON)',
    `reservation`     JSON              DEFAULT NULL COMMENT '预约信息 (JSON)',
    `text_font_config` JSON             DEFAULT NULL COMMENT '文本字体配置 (JSON)',
    `text_special_effects` JSON         DEFAULT NULL COMMENT '文本特效 (JSON)',
    `image_data`      JSON              DEFAULT NULL COMMENT '图片数据 (JSON)',
    PRIMARY KEY (`deco_index`, `platform`, `room_id`),
    INDEX `idx_deco_type` (`deco_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='直播间装饰表';
```

```shell
##
## $.data.room.deco_list
##
+-------------------+--------------+------+-----+---------+-------+--------------------------------+---------------------+
| Field             | Type         | Null | Key | Default | Extra | Topology                       | Comment             |
+-------------------+--------------+------+-----+---------+-------+--------------------------------+---------------------+
| platform          | varchar(20)  | NO   | PRI |         |       | -                              | 平台                |
| room_id           | varchar(200) | NO   | PRI |         |       | "$.data.room.id"               | 直播间 ID           |
| deco_index        | unsigned tinyint | NO | PRI |         | auto_increment | -                   | 装饰索引            |
| deco_id           | unsigned int | YES  |     | NULL    |       | "$.data.room.deco_list[x].id"  | 装饰 ID             |
| deco_type         | unsigned tinyint | YES |  | NULL    |       | "$.data.room.deco_list[x].type"| 装饰类型            |
| kind              | unsigned tinyint | YES | | NULL    |       | "$.data.room.deco_list[x].kind"| 种类                |
| audit_text_color  | varchar(7)   | YES  |     | NULL    |       | "$.data.room.deco_list[x].audit_text_color" | 审核文本颜色 |
| content           | tinytext     | YES  |     | NULL    |       | "$.data.room.deco_list[x].content" | 装饰内容         |
| status            | unsigned tinyint | YES |  | 0       |       | "$.data.room.deco_list[x].status" | 状态             |
| text_color        | varchar(7)   | YES  |     | NULL    |       | "$.data.room.deco_list[x].text_color" | 文本颜色       |
| text_size         | unsigned int | YES  |     | NULL    |       | "$.data.room.deco_list[x].text_size" | 文本大小        |
| position_x        | unsigned int | YES  |     | NULL    |       | "$.data.room.deco_list[x].x"   | X 坐标               |
| position_y        | unsigned int | YES  |     | NULL    |       | "$.data.room.deco_list[x].y"   | Y 坐标               |
| width             | unsigned int | YES  |     | NULL    |       | "$.data.room.deco_list[x].w"   | 宽度                |
| height            | unsigned int | YES  |     | NULL    |       | "$.data.room.deco_list[x].h"   | 高度                |
| max_length        | unsigned tinyint | YES | | NULL | | "$.data.room.deco_list[x].max_length" | 最大长度        |
| sub_type          | unsigned tinyint | YES | | NULL | | "$.data.room.deco_list[x].sub_type" | 子类型          |
| text_image_adjustable_start_position | unsigned int | YES | | NULL | | "$.data.room.deco_list[x].text_image_adjustable_start_position" | 文本图片可调整开始位置 |
| text_image_adjustable_end_position | unsigned int | YES | | NULL | | "$.data.room.deco_list[x].text_image_adjustable_end_position" | 文本图片可调整结束位置 |
| input_rect        | json         | YES  |     | NULL    |       | "$.data.room.deco_list[x].input_rect" | 输入框矩形 (JSON) |
| nine_patch_image  | json         | YES  |     | NULL    |       | "$.data.room.deco_list[x].nine_patch_image" | 九宫格图片 (JSON) |
| reservation       | json         | YES  |     | NULL    |       | "$.data.room.deco_list[x].reservation" | 预约信息 (JSON)   |
| text_font_config  | json         | YES  |     | NULL    |       | "$.data.room.deco_list[x].text_font_config" | 文本字体配置 (JSON) |
| text_special_effects | json      | YES  |     | NULL    |       | "$.data.room.deco_list[x].text_special_effects" | 文本特效 (JSON) |
| image_data        | json         | YES  |     | NULL    |       | "$.data.room.deco_list[x].image" | 图片数据 (JSON)   |
+-------------------+--------------+------+-----+---------+-------+--------------------------------+---------------------+
```

#### 7-1. 直播间粉丝群管理员用户 ID 表 - fans_group_admin_user_id

```sql
CREATE TABLE IF NOT EXISTS `fans_group_admin_user_id` (
    `platform`                    VARCHAR(20)       NOT NULL COMMENT '平台',
    `room_id`                     VARCHAR(200)      NOT NULL COMMENT '直播间ID',
    `index`                       BIGINT            NOT NULL AUTO_INCREMENT COMMENT '粉丝群管理员ID序号',
    `fans_group_admin_user_id`    VARCHAR(200)      DEFAULT NULL COMMENT '粉丝群管理员用户ID',
    PRIMARY KEY (`index`, `platform`, `room_id`),
    UNIQUE KEY `unique_record` (`platform`, `room_id`, `fans_group_admin_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='直播间粉丝群管理员用户 ID 表';
```

```shell
##
## $.data.room.fans_group_admin_user_ids
##
+--------------------------------+------------------+------+-----+---------+----------------+-----------------------------------------+---------------------+
| Field                          | Type             | Null | Key | Default | Extra          | Topology                                | Comment             |
+--------------------------------+------------------+------+-----+---------+----------------+-----------------------------------------+---------------------+
| platform                       | varchar(20)      | NO   | PRI |         |                | -                                       | 平台                |
| room_id                        | varchar(200)     | NO   | PRI |         |                | "$.data.room.id"                        | 直播间ID             |
| index                          | bigint           | NO   | PRI |         | auto_increment | -                                       | 粉丝群管理员ID序号   |
| fans_group_admin_user_id       | varchar(200)     | YES  |     | NULL    |                | "$.data.room.fans_group_admin_user_ids" | 粉丝群管理员用户ID   |
+--------------------------------+------------------+------+-----+---------+----------------+-----------------------------------------+---------------------+
```

#### 7-2. 直播间粉丝群管理员用户开放 ID 表 - fans_group_admin_user_open_id

```sql
CREATE TABLE IF NOT EXISTS `fans_group_admin_user_open_id` (
    `platform`                         VARCHAR(20)       NOT NULL COMMENT '平台',
    `room_id`                          VARCHAR(200)      NOT NULL COMMENT '直播间ID',
    `index`                            BIGINT            NOT NULL AUTO_INCREMENT COMMENT '粉丝群管理员OpenID序号',
    `fans_group_admin_user_open_id`    VARCHAR(200)      DEFAULT NULL COMMENT '粉丝群管理员OpenID列表',
    PRIMARY KEY (`index`, `platform`, `room_id`),
    UNIQUE KEY `unique_record` (`platform`, `room_id`, `fans_group_admin_user_open_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='直播间粉丝群管理员用户开放 ID 表';
```

```shell
##
## $.data.room.fans_group_admin_user_open_ids
##
+-------------------------------------+------------------+------+-----+---------+-------+----------------------------------------------+----------------------+
| Field                               | Type             | Null | Key | Default | Extra | Topology                                     | Comment              |
+-------------------------------------+------------------+------+-----+---------+-------+----------------------------------------------+----------------------+
| platform                            | varchar(20)      | NO   | PRI |         |       | -                                            | 平台                 |
| room_id                             | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                             | 直播间ID              |
| index                               | bigint           | NO   | PRI |         | auto_increment | -                                  | 粉丝群管理员OpenID序号 |
| fans_group_admin_user_open_id       | varchar(200)     | YES  |     | NULL    |       | "$.data.room.fans_group_admin_user_open_ids" | 粉丝群管理员OpenID列表 |
+-------------------------------------+------------------+------+-----+---------+-------+----------------------------------------------+----------------------+
```

---

---

## 五、实施建议

### 5.1 分阶段实施

**第一阶段：核心表迁移 (1-2 周)**
1. 创建 room_base 表
2. 创建 room_owner_v2 表
3. 迁移直播间基础数据
4. 验证数据完整性

**第二阶段：JSON 字段迁移 (1-2 周)**
1. 将嵌套对象转为 JSON 存储
2. 更新应用层读取逻辑
3. 性能测试

**第三阶段：扩展表优化 (1-2 周)**
1. 创建必要的扩展表
2. 迁移数组数据
3. 删除旧表
