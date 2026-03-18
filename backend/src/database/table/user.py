##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Third-Part>>
from backend.src.database.social_media_stream_database                import SocialMediaStreamDataBase
from backend.src.database.table.social_media_stream_db_table          import SocialMediaStreamDataTable

##
## room owner table
##
## +------------------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------+----------------------------+
## | Field                                    | Type              | Null | Key | Default | Extra |Topology                                                      | Comment                    |
## +------------------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------+----------------------------+
## | now                                      | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"                                                | 当前时间戳                  |
## | platform                                 | varchar(20)       | NO   | PRI |         |       |           -                                                  | 平台                        |
## | room_id                                  | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                                             | 直播间ID                    |
## | owner_user_id                            | varchar(200)      | NO   | PRI |         |       | "$.data.room.owner_user_id"                                  | 直播间主播ID                |
## | adversary_authorization_info             | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.adversary_authorization_info"             | 对手授权信息                 |
## | adversary_user_status                    | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.adversary_user_status"                    | 对手用户状态                 |
## | age_range                                | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.age_range"                                | 年龄范围                     |
## | allow_be_located                         | bool              |      |     | NULL    |       | "$.data.room.owner.allow_be_located"                         | 是否允许被定位               |
## | allow_find_by_contacts                   | bool              |      |     | NULL    |       | "$.data.room.owner.allow_find_by_contacts"                   | 是否允许通过联系人查找       |
## | allow_others_download_video              | bool              |      |     | NULL    |       | "$.data.room.owner.allow_others_download_video"              | 是否允许其他人下载视频       |
## | allow_others_download_when_sharing_video | bool              |      |     | NULL    |       | "$.data.room.owner.allow_others_download_when_sharing_video" | 是否允许其他人下载分享的视频  |
## | allow_share_show_profile                 | bool              |      |     | NULL    |       | "$.data.room.owner.allow_share_show_profile"                 | 是否允许分享展示个人资料      |
## | allow_show_in_gossip                     | bool              |      |     | NULL    |       | "$.data.room.owner.allow_show_in_gossip"                     | 是否允许在八卦中展示          |
## | allow_show_my_action                     | bool              |      |     | NULL    |       | "$.data.room.owner.allow_show_my_action"                     | 是否允许展示我的动态          |
## | allow_strange_comment                    | bool              |      |     | NULL    |       | "$.data.room.owner..allow_strange_comment"                   | 是否允许陌生人评论            |
## | allow_unfollower_comment                 | bool              |      |     | NULL    |       | "$.data.room.owner..allow_unfollower_comment"                | 是否允许非关注者评论          |
## | allow_use_linkmic                        | bool              |      |     | NULL    |       | "$.data.room.owner..allow_use_linkmic"                       | 是否允许使用连麦              |
## | authorization_info                       | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner..authorization_info"                      | 授权信息                     |
## | bg_img_url                               | text              |      |     | NULL    |       | "$.data.room.owner.bg_img_url"                               | 背景图片URL                 |
## | birthday                                 | timestamp         |      |     | NULL    |       | "$.data.room.owner.birthday"                                 | 生日时间戳                  |
## | birthday_description                     | tinytext          |      |     | NULL    |       | "$.data.room.owner.birthday_description"                     | 生日描述                   |
## | birthday_valid                           | bool              |      |     | NULL    |       | "$.data.room.owner.birthday_valid"                           | 生日是否有效                |
## | block_status                             | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.block_status"                             | 屏蔽状态：0-未屏蔽 1-已屏蔽  |
## | city                                     | varchar(100)      |      |     | NULL    |       | "$.data.room.owner.city"                                     | 城市                       |
## | comment_restrict                         | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.comment_restrict"                         | 评论限制                    |
## | constellation                            | varchar(20)       |      |     | NULL    |       | "$.data.room.owner.constellation"                            | 星座                       |
## | consume_diamond_level                    | unsigned smallint |      |     | NULL    |       | "$.data.room.owner.consume_diamond_level"                    | 消费钻石等级                |
## | create_time                              | timestamp         |      |     | NULL    |       | "$.data.room.owner.create_time"                              | 账号创建时间戳              |
## | desensitized_nickname                    | varchar(50)       |      |     | NULL    |       | "$.data.room.owner.desensitized_nickname"                    | 脱敏昵称                   |
## | disable_ichat                            | bool              |      |     | NULL    |       | "$.data.room.owner.disable_ichat"                            | 是否禁用iChat               |
## | display_id                               | varchar(200)      |      |     | NULL    |       | "$.data.room.owner.display_id"                               | 显示ID                     |
## | enable_ichat_img                         | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.enable_ichat_img"                         | 是否启用iChat图片           |
## | exp                                      | unsigned int      |      |     | NULL    |       | "$.data.room.owner.exp"                                      | 经验值                      |
## | experience                               | unsigned int      |      |     | NULL    |       | "$.data.room.owner.experience"                               | 经验值                      |
## | fan_ticket_count                         | unsigned bigint   |      |     | NULL    |       | "$.data.room.owner.fan_ticket_count"                         | 粉丝票数量                  |
## | list_fans_group_url                      | text              |      |     | NULL    |       | "$.data.room.owner.fans_group_info.list_fans_group_url"      | 粉丝群列表URL               |
## | fold_stranger_chat                       | bool              |      |     | NULL    |       | "$.data.room.owner.fold_stranger_chat"                       | 是否折叠陌生人聊天           |
## | follow_info_follow_status                | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.follow_info.follow_status"                | 关注状态                    |
## | follower_count                           | unsigned bigint   |      |     | NULL    |       | "$.data.room.owner.follow_info.follower_count"               | 粉丝数量                    |
## | follower_count_str                       | varchar(20)       |      |     | NULL    |       | "$.data.room.owner.follow_info.follower_count_str"           | 粉丝数量字符串              |
## | following_count                          | unsigned int      |      |     | NULL    |       | "$.data.room.owner.follow_info.following_count"              | 关注数量                    |
## | following_count_str                      | varchar(20)       |      |     | NULL    |       | "$.data.room.owner.follow_info.following_count_str"          | 关注数量字符串               |
## | invalid_follow_status                    | bool              |      |     | NULL    |       | "$.data.room.owner.follow_info.invalid_follow_status"        | 是否为无效关注状态           |
## | follow_info_push_status                  | bool              |      |     | NULL    |       | "$.data.room.owner.follow_info.push_status"                  | 是否推送状态                |
## | follow_info_remark_name                  | varchar(50)       |      |     | NULL    |       | "$.data.room.owner.follow_info.remark_name"                  | 备注名                     |
## | follow_status                            | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.follow_status"                            | 关注状态                    |
## | gender                                   | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.follow_info.following_count_str"          | 性别（0-未知，1-男，2-女）   |
## | hotsoon_verified                         | bool              |      |     | NULL    |       | "$.data.room.owner.hotsoon_verified"                         | 是否Hotsoon认证             |
## | hotsoon_verified_reason                  | tinytext          |      |     | NULL    |       | "$.data.room.owner.hotsoon_verified_reason"                  | Hotsoon认证原因             |
## | ichat_restrict_type                      | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.ichat_restrict_type"                      | iChat限制类型               |
## | id                                       | varchar(200)      |      |     | NULL    |       | "$.data.room.owner.id"                                       | 直播间 owner ID             |
## | income_share_percent                     | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.income_share_percent"                     | 收入分成百分比               |
## | is_anonymous                             | bool              |      |     | NULL    |       | "$.data.room.owner.is_anonymous"                             | 是否匿名                    |
## | is_follower                              | bool              |      |     | NULL    |       | "$.data.room.owner.is_follower"                              | 是否是粉丝                  |
## | is_following                             | bool              |      |     | NULL    |       | "$.data.room.owner.is_following"                             | 是否正在关注                |
## | JAccreditAdvance                         | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.j_accredit_info.JAccreditAdvance"         | 主播认证高级                |
## | JAccreditBasic                           | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.j_accredit_info.JAccreditBasic"           | 主播认证基础                |
## | JAccreditContent                         | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.j_accredit_info.JAccreditContent"         | 主播认证内容                | 
## | JAccreditLive                            | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.j_accredit_info.JAccreditLive"            | 主播认证直播                |
## | level                                    | unsigned smallint |      |     | NULL    |       | "$.data.room.owner.level"                                    | 用户等级                    |
## | link_mic_stats                           | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.link_mic_stats"                           | 连麦状态                    |
## | location_city                            | varchar(100)      |      |     | NULL    |       | "$.data.room.owner.location_city"                            | 定位城市                    |
## | modify_time                              | timestamp         |      |     | NULL    |       | "$.data.room.owner.modify_time"                              | 修改时间戳                  |
## | mystery_man                              | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.mystery_man"                              | 是否神秘人                  |
## | need_profile_guide                       | bool              |      |     | NULL    |       | "$.data.room.owner.need_profile_guide"                       | 是否需要个人资料引导         |
## | nickname                                 | varchar(50)       |      |     | NULL    |       | "$.data.room.owner.nickname"                                 | 昵称                       |
## | pay_grade_banner                         | tinytext          |      |     | NULL    |       | "$.data.room.owner.pay_grade.grade_banner"                   | 付费等级横幅                |
## | pay_grade_describe                       | tinytext          |      |     | NULL    |       | "$.data.room.owner.pay_grade.grade_describe"                 | 付费等级描述                |
## | pay_grade_describe_shining               | bool              |      |     | NULL    |       | "$.data.room.owner.pay_grade.grade_describe_shining"         | 付费等级描述闪烁             | 
## | pay_grade_level                          | unsigned smallint |      |     | NULL    |       | "$.data.room.owner.pay_grade.level"                          | 付费等级                    |
## | pay_grade_name                           | varchar(50)       |      |     | NULL    |       | "$.data.room.owner.pay_grade.name"                           | 付费等级名称                 |
## | pay_grade_next_diamond                   | unsigned bigint   |      |     | NULL    |       | "$.data.room.owner.pay_grade.next_diamond"                   | 下一级所需钻石               |
## | pay_grade_next_name                      | varchar(50)       |      |     | NULL    |       | "$.data.room.owner.pay_grade.next_name"                      | 下一级名称                   |
## | pay_grade_next_privileges                | tinytext          |      |     | NULL    |       | "$.data.room.owner.pay_grade.next_privileges"                | 下一级特权                   |
## | pay_grade_now_diamond                    | unsigned bigint   |      |     | NULL    |       | "$.data.room.owner.pay_grade.now_diamond"                    | 当前钻石                     |
## | pay_diamond_bak                          | unsigned bigint   |      |     | NULL    |       | "$.data.room.owner.pay_grade.pay_diamond_bak"                | 付费钻石备份                 |
## | pay_grade_score                          | unsigned int      |      |     | NULL    |       | "$.data.room.owner.pay_grade.score"                          | 分数                        |
## | screen_chat_type                         | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.pay_grade.screen_chat_type"               | 屏幕聊天类型                 |
## | this_grade_max_diamond                   | unsigned bigint   |      |     | NULL    |       | "$.data.room.owner.pay_grade.this_grade_max_diamond"         | 当前等级最大钻石             |
## | this_grade_min_diamond                   | unsigned bigint   |      |     | NULL    |       | "$.data.room.owner.pay_grade.this_grade_min_diamond"         | 当前等级最小钻石             |
## | total_diamond_count                      | unsigned bigint   |      |     | NULL    |       | "$.data.room.owner.pay_grade.total_diamond_count"            | 总钻石数量                   |
## | upgrade_need_consume                     | unsigned bigint   |      |     | NULL    |       | "$.data.room.owner.pay_grade.upgrade_need_consume"           | 升级所需消费                 |
## | pay_score                                | unsigned int      |      |     | NULL    |       | "$.data.room.owner.pay_score"                                | 支付分                     |
## | pay_scores                               | unsigned int      |      |     | NULL    |       | "$.data.room.owner.pay_scores"                               | 支付分                     |
## | public_area_oper_freq                    | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.public_area_oper_freq"                    | 公共区域操作频率             |
## | push_comment_status                      | bool              |      |     | NULL    |       | "$.data.room.owner.push_comment_status"                      | 是否推送评论状态             |
## | push_digg                                | bool              |      |     | NULL    |       | "$.data.room.owner.push_digg"                                | 是否推送点赞                |
## | push_follow                              | bool              |      |     | NULL    |       | "$.data.room.owner.push_follow"                              | 是否推送关注                |
## | push_friend_action                       | bool              |      |     | NULL    |       | "$.data.room.owner.push_friend_action"                       | 是否推送好友操作            |
## | push_ichat                               | bool              |      |     | NULL    |       | "$.data.room.owner.push_ichat"                               | 是否推送iChat               |
## | push_status                              | bool              |      |     | NULL    |       | "$.data.room.owner.push_status"                              | 推送状态                   |
## | push_video_post                          | bool              |      |     | NULL    |       | "$.data.room.owner.push_video_post"                          | 是否推送视频发布            |
## | push_video_recommend                     | bool              |      |     | NULL    |       | "$.data.room.owner.push_video_recommend"                     | 是否推送视频推荐            |
## | remark_name                              | varchar(50)       |      |     | NULL    |       | "$.data.room.owner.remark_name"                              | 备注名称                   |
## | sec_uid                                  | varchar(200)      |      |     | NULL    |       | "$.data.room.owner.sec_uid"                                  | 安全用户ID                 |
## | secret                                   | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.secret"                                   | 是否私密                    |
## | share_qrcode_uri                         | text              |      |     | NULL    |       | "$.data.room.owner.share_qrcode_uri"                         | 分享二维码URI               |
## | short_id                                 | varchar(200)      |      |     | NULL    |       | "$.data.room.owner.short_id"                                 | 短ID                       |
## | signature                                | text              |      |     | NULL    |       | "$.data.room.owner.signature"                                | 个性签名                    |
## | special_id                               | varchar(200)      |      |     | NULL    |       | "$.data.room.owner.special_id"                               | 特殊ID                     |
## | status                                   | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.status"                                   | 用户状态：0-注销 1-正常     |
## | telephone                                | varchar(20)       |      |     | NULL    |       | "$.data.room.owner.telephone"                                | 电话号码                    |
## | ticket_count                             | unsigned bigint   |      |     | NULL    |       | "$.data.room.owner.ticket_count"                             | 票数                        |
## | top_vip_no                               | unsigned smallint |      |     | NULL    |       | "$.data.room.owner.top_vip_no"                               | 顶级VIP编号                 |
## | total_recharge_diamond_count             | unsigned bigint   |      |     | NULL    |       | "$.data.room.owner.total_recharge_diamond_count"             | 总充值钻石数量               |
## | user_canceled                            | bool              |      |     | NULL    |       | "$.data.room.owner.user_canceled"                            | 用户是否已取消               |
## | user_open_id                             | varchar(200)      |      |     | NULL    |       | "$.data.room.owner.user_open_id"                             | 用户OpenID                  |
## | user_role                                | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.user_role"                                | 用户角色                    |
## | verified                                 | bool              |      |     | NULL    |       | "$.data.room.owner.verified"                                 | 是否认证                     |
## | verified_content                         | tinytext          |      |     | NULL    |       | "$.data.room.owner.verified_content"                         | 认证内容                     |
## | verified_mobile                          | bool              |      |     | NULL    |       | "$.data.room.owner.verified_mobile"                          | 是否为认证手机号              |
## | verified_reason                          | tinytext          |      |     | NULL    |       | "$.data.room.owner.verified_reason"                          | 认证原因                      |
## | watch_duration_month                     | unsigned smallint |      |     | NULL    |       | "$.data.room.owner.watch_duration_month"                     | 观看时长（月）                |
## | web_rid                                  | varchar(200)      |      |     | NULL    |       | "$.data.room.owner.web_rid"                                  | Web RID                      |
## | webcast_uid                              | varchar(200)      |      |     | NULL    |       | "$.data.room.owner.webcast_uid"                              | 主播Webcast UID              |
## | with_car_management_permission           | bool              |      |     | NULL    |       | "$.data.room.owner.with_car_management_permission"           | 是否具有车辆管理权限          |
## | with_commerce_permission                 | bool              |      |     | NULL    |       | "$.data.room.owner.with_commerce_permission"                 | 是否具有商业权限              |
## | with_fusion_shop_entry                   | bool              |      |     | NULL    |       | "$.data.room.owner.with_fusion_shop_entry"                   | 是否具有融合店铺入口          |
## +------------------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------+-----------------------------+
class RoomOwnerTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_OWNER_TABLE_NAME       = "room_owner"
  __ROOM_OWNER_TABLE_HEADER     = ['now',                                      'platform',                 'room_id',                    'owner_user_id',                'adversary_authorization_info',
                                   'adversary_user_status',                    'age_range',                'allow_be_located',           'allow_find_by_contacts',       'allow_others_download_video',
                                   'allow_others_download_when_sharing_video', 'allow_share_show_profile', 'allow_show_in_gossip',       'allow_show_my_action',         'allow_strange_comment',
                                   'allow_unfollower_comment',                 'allow_use_linkmic',        'authorization_info',         'bg_img_url',                   'birthday',
                                   'birthday_description',                     'birthday_valid',           'block_status',               'city',                         'comment_restrict',
                                   'constellation',                            'consume_diamond_level',    'create_time',                'desensitized_nickname',        'disable_ichat',
                                   'display_id',                               'enable_ichat_img',         'exp',                        'experience',                   'fan_ticket_count',
                                   'list_fans_group_url',                      'fold_stranger_chat',       'follow_info_follow_status',  'follower_count',               'follower_count_str',
                                   'following_count',                          'following_count_str',      'invalid_follow_status',      'follow_info_push_status',      'follow_info_remark_name',
                                   'follow_status',                            'gender',                   'hotsoon_verified',           'hotsoon_verified_reason',      'ichat_restrict_type',
                                   'id',
                                   'income_share_percent',                     'is_anonymous',             'is_follower',                'is_following',                 'JAccreditAdvance',
                                   'JAccreditBasic',                           'JAccreditContent',         'JAccreditLive',              'level',                        'link_mic_stats',
                                   'location_city',                            'modify_time',              'mystery_man',                'need_profile_guide',           'nickname',
                                   'pay_grade_banner',                         'pay_grade_describe',       'pay_grade_describe_shining', 'pay_grade_level',              'pay_grade_name',
                                   'pay_grade_next_diamond',                   'pay_grade_next_name',      'pay_grade_next_privileges',  'pay_grade_now_diamond',        'pay_diamond_bak',
                                   'pay_grade_score',                          'screen_chat_type',         'this_grade_max_diamond',     'this_grade_min_diamond',       'total_diamond_count',
                                   'upgrade_need_consume',                     'pay_score',                'pay_scores',                 'public_area_oper_freq',        'push_comment_status',
                                   'push_digg',                                'push_follow',              'push_friend_action',         'push_ichat',                   'push_status',
                                   'push_video_post',                          'push_video_recommend',     'remark_name',                'sec_uid',                      'secret',
                                   'share_qrcode_uri',                         'short_id',                 'signature',                  'special_id',                   'status',
                                   'telephone',                                'ticket_count',             'top_vip_no',                 'total_recharge_diamond_count', 'user_canceled',
                                   'user_open_id',                             'user_role',                'verified',                   'verified_content',             'verified_mobile',
                                   'verified_reason',                          'watch_duration_month',     'web_rid',                    'webcast_uid',                  'with_car_management_permission',
                                   'with_commerce_permission',                 'with_fusion_shop_entry'
                                   ]
  __ROOM_OWNER_TABLE_PRI_KEY    = ['now','platform','room_id', 'owner_user_id']
  __TABLE_AUTO_INCREMENT        = []
  __ROOM_OWNER_TABLE_TUPLE      = {item:None for item in __ROOM_OWNER_TABLE_HEADER}
  __SQL_CREATE_ROOM_OWNER_TABLE = '''
                                  CREATE TABLE IF NOT EXISTS {} (
                                    now                                      timestamp(3)      NOT NULL,
                                    platform                                 varchar(20)       NOT NULL,
                                    room_id                                  varchar(200)      NOT NULL,
                                    owner_user_id                            varchar(200)      NOT NULL,
                                    adversary_authorization_info             tinyint           DEFAULT NULL,
                                    adversary_user_status                    tinyint           DEFAULT NULL,
                                    age_range                                tinyint           DEFAULT NULL,
                                    allow_be_located                         bool              DEFAULT NULL,
                                    allow_find_by_contacts                   bool              DEFAULT NULL,
                                    allow_others_download_video              bool              DEFAULT NULL,
                                    allow_others_download_when_sharing_video bool              DEFAULT NULL,
                                    allow_share_show_profile                 bool              DEFAULT NULL,
                                    allow_show_in_gossip                     bool              DEFAULT NULL,
                                    allow_show_my_action                     bool              DEFAULT NULL,
                                    allow_strange_comment                    bool              DEFAULT NULL,
                                    allow_unfollower_comment                 bool              DEFAULT NULL,
                                    allow_use_linkmic                        bool              DEFAULT NULL,
                                    authorization_info                       tinyint           DEFAULT NULL,
                                    bg_img_url                               text              DEFAULT NULL,
                                    birthday                                 timestamp         DEFAULT NULL,
                                    birthday_description                     tinytext          DEFAULT NULL,
                                    birthday_valid                           bool              DEFAULT NULL,
                                    block_status                             tinyint           DEFAULT NULL,
                                    city                                     varchar(100)      DEFAULT NULL,
                                    comment_restrict                         tinyint           DEFAULT NULL,
                                    constellation                            varchar(20)       DEFAULT NULL,
                                    consume_diamond_level                    smallint          DEFAULT NULL,
                                    create_time                              timestamp         DEFAULT NULL,
                                    desensitized_nickname                    varchar(50)       DEFAULT NULL,
                                    disable_ichat                            bool              DEFAULT NULL,
                                    display_id                               varchar(200)      DEFAULT NULL,
                                    enable_ichat_img                         tinyint           DEFAULT NULL,
                                    exp                                      int               DEFAULT NULL,
                                    experience                               int               DEFAULT NULL,
                                    fan_ticket_count                         bigint            DEFAULT NULL,
                                    list_fans_group_url                      text              DEFAULT NULL,
                                    fold_stranger_chat                       bool              DEFAULT NULL,
                                    follow_info_follow_status                tinyint           DEFAULT NULL,
                                    follower_count                           bigint            DEFAULT NULL,
                                    follower_count_str                       varchar(20)       DEFAULT NULL,
                                    following_count                          int               DEFAULT NULL,
                                    following_count_str                      varchar(20)       DEFAULT NULL,
                                    invalid_follow_status                    bool              DEFAULT NULL,
                                    follow_info_push_status                  bool              DEFAULT NULL,
                                    follow_info_remark_name                  varchar(50)       DEFAULT NULL,
                                    follow_status                            tinyint           DEFAULT NULL,
                                    gender                                   tinyint           DEFAULT NULL,
                                    hotsoon_verified                         bool              DEFAULT NULL,
                                    hotsoon_verified_reason                  tinytext          DEFAULT NULL,
                                    ichat_restrict_type                      tinyint           DEFAULT NULL,
                                    id                                       varchar(200)      DEFAULT NULL,
                                    income_share_percent                     tinyint           DEFAULT NULL,
                                    is_anonymous                             bool              DEFAULT NULL,
                                    is_follower                              bool              DEFAULT NULL,
                                    is_following                             bool              DEFAULT NULL,
                                    JAccreditAdvance                         tinyint           DEFAULT NULL,
                                    JAccreditBasic                           tinyint           DEFAULT NULL,
                                    JAccreditContent                         tinyint           DEFAULT NULL,
                                    JAccreditLive                            tinyint           DEFAULT NULL,
                                    level                                    smallint          DEFAULT NULL,
                                    link_mic_stats                           tinyint           DEFAULT NULL,
                                    location_city                            varchar(100)      DEFAULT NULL,
                                    modify_time                              timestamp         DEFAULT NULL,
                                    mystery_man                              tinyint           DEFAULT NULL,
                                    need_profile_guide                       bool              DEFAULT NULL,
                                    nickname                                 varchar(50)       DEFAULT NULL,
                                    pay_grade_banner                         tinytext          DEFAULT NULL,
                                    pay_grade_describe                       tinytext          DEFAULT NULL,
                                    pay_grade_describe_shining               bool              DEFAULT NULL,
                                    pay_grade_level                          smallint          DEFAULT NULL,
                                    pay_grade_name                           varchar(50)       DEFAULT NULL,
                                    pay_grade_next_diamond                   bigint            DEFAULT NULL,
                                    pay_grade_next_name                      varchar(50)       DEFAULT NULL,
                                    pay_grade_next_privileges                tinytext          DEFAULT NULL,
                                    pay_grade_now_diamond                    bigint            DEFAULT NULL,
                                    pay_diamond_bak                          bigint            DEFAULT NULL,
                                    pay_grade_score                          int               DEFAULT NULL,
                                    screen_chat_type                         tinyint           DEFAULT NULL,
                                    this_grade_max_diamond                   bigint            DEFAULT NULL,
                                    this_grade_min_diamond                   bigint            DEFAULT NULL,
                                    total_diamond_count                      bigint            DEFAULT NULL,
                                    upgrade_need_consume                     bigint            DEFAULT NULL,
                                    pay_score                                int               DEFAULT NULL,
                                    pay_scores                               int               DEFAULT NULL,
                                    public_area_oper_freq                    tinyint           DEFAULT NULL,
                                    push_comment_status                      bool              DEFAULT NULL,
                                    push_digg                                bool              DEFAULT NULL,
                                    push_follow                              bool              DEFAULT NULL,
                                    push_friend_action                       bool              DEFAULT NULL,
                                    push_ichat                               bool              DEFAULT NULL,
                                    push_status                              bool              DEFAULT NULL,
                                    push_video_post                          bool              DEFAULT NULL,
                                    push_video_recommend                     bool              DEFAULT NULL,
                                    remark_name                              varchar(50)       DEFAULT NULL,
                                    sec_uid                                  varchar(200)      DEFAULT NULL,
                                    secret                                   tinyint           DEFAULT NULL,
                                    share_qrcode_uri                         text              DEFAULT NULL,
                                    short_id                                 varchar(200)      DEFAULT NULL,
                                    signature                                text              DEFAULT NULL,
                                    special_id                               varchar(200)      DEFAULT NULL,
                                    status                                   tinyint           DEFAULT NULL,
                                    telephone                                varchar(20)       DEFAULT NULL,
                                    ticket_count                             bigint            DEFAULT NULL,
                                    top_vip_no                               smallint          DEFAULT NULL,
                                    total_recharge_diamond_count             bigint            DEFAULT NULL,
                                    user_canceled                            bool              DEFAULT NULL,
                                    user_open_id                             varchar(200)      DEFAULT NULL,
                                    user_role                                tinyint           DEFAULT NULL,
                                    verified                                 bool              DEFAULT NULL,
                                    verified_content                         tinytext          DEFAULT NULL,
                                    verified_mobile                          bool              DEFAULT NULL,
                                    verified_reason                          tinytext          DEFAULT NULL,
                                    watch_duration_month                     smallint          DEFAULT NULL,
                                    web_rid                                  varchar(200)      DEFAULT NULL,
                                    webcast_uid                              varchar(200)      DEFAULT NULL,
                                    with_car_management_permission           bool              DEFAULT NULL,
                                    with_commerce_permission                 bool              DEFAULT NULL,
                                    with_fusion_shop_entry                   bool              DEFAULT NULL,
                                    PRIMARY KEY (now, platform, room_id, owner_user_id)
                                  )
                                  '''.format(__ROOM_OWNER_TABLE_NAME)
  __SQL_DROP_ROOM_OWNER_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_OWNER_TABLE_NAME)

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
    return self.__ROOM_OWNER_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_OWNER_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_OWNER_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_OWNER_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_OWNER_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_OWNER_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

"""
  data.room.owner.own_room
  data.room.owner.own_room.room_ids
  data.room.owner.own_room.room_ids_display
  data.room.owner.own_room.room_ids_str
'''
own_room:
  room_ids:
  - 7474152752591997707
  room_ids_display: []
  room_ids_str:
  - '7474152752591997707'
'''
"""
##
## data.room.owner.own_room.room_ids
## +-----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------+
## | Field                 | Type              | Null | Key | Default | Extra | Topology                                                 | Comment              |
## +-----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------+
## | start_time            | timestamp         | NO   | PRI |         |       | "$.data.room.start_time"                                 | 开始时间              | 
## | platform              | varchar(20)       | NO   | PRI |         |       |           -                                              | 平台                  |
## | owner_user_id         | varchar(200)      | NO   | PRI |         |       | "$.data.room.owner_user_id"                              | 账号作者ID            |
## | exist_flag_index      | unsigned bigint   |      |     | NULL    |       | -                                                        | 存在标志索引          | 
## | exist_flag            | bool              |      |     | False   |       | -                                                        | 存在标志              | 
## +-----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------+
##
class OwnRoomFlagTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __OWN_ROOM_FLAG_TABLE_NAME       = 'own_room_flag'
  __OWN_ROOM_FLAG_TABLE_HEADER     = ['start_time', 'platform', 'owner_user_id', 'exist_flag_index', 'exist_flag']
  __OWN_ROOM_FLAG_TABLE_PRI_KEY    = ['exist_flag_index']
  __TABLE_AUTO_INCREMENT           = ['exist_flag_index']
  __OWN_ROOM_FLAG_TABLE_TUPLE      = {item:None for item in __OWN_ROOM_FLAG_TABLE_HEADER}
  __SQL_CREATE_OWN_ROOM_FLAG_TABLE = '''
                                       CREATE TABLE IF NOT EXISTS {} (
                                         start_time            timestamp     NOT NULL,
                                         platform              varchar(20)   NOT NULL,
                                         owner_user_id         varchar(200)  NOT NULL,
                                         exist_flag_index      bigint        NOT NULL AUTO_INCREMENT,
                                         exist_flag            bool          DEFAULT NULL,
                                         PRIMARY KEY (exist_flag_index),
                                         UNIQUE KEY unique_record (start_time, platform, owner_user_id, exist_flag)
                                         )
                                     '''.format(__OWN_ROOM_FLAG_TABLE_NAME)
  __SQL_DROP_OWN_ROOM_FLAG_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__OWN_ROOM_FLAG_TABLE_NAME)

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
    return self.__OWN_ROOM_FLAG_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__OWN_ROOM_FLAG_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__OWN_ROOM_FLAG_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__OWN_ROOM_FLAG_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_OWN_ROOM_FLAG_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_OWN_ROOM_FLAG_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## data.room.owner.own_room.room_ids
## +-----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------+
## | Field                 | Type              | Null | Key | Default | Extra | Topology                                                 | Comment              |
## +-----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------+
## | start_time            | timestamp         | NO   | PRI |         |       | "$.data.room.start_time"                                 | 开始时间              | 
## | platform              | varchar(20)       | NO   | PRI |         |       |           -                                              | 平台                  |
## | owner_user_id         | varchar(200)      | NO   | PRI |         |       | "$.data.room.owner_user_id"                              | 账号作者ID            |
## | room_id_index         | unsigned bigint   |      |     | NULL    |       | -                                                        | 直播间ID索引          | 
## | room_id               | varchar(200)      |      |     | NULL    |       | "$.data.room.owner.own_room.room_ids"                    | 直播间ID              | 
## +-----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------+
##
class OwnRoomIdTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __OWN_ROOM_ID_TABLE_NAME       = 'own_room_id'
  __OWN_ROOM_ID_TABLE_HEADER     = ['start_time', 'platform', 'owner_user_id', 'room_id_index', 'room_id']
  __OWN_ROOM_ID_TABLE_PRI_KEY    = ['start_time', 'platform', 'owner_user_id', 'room_id_index']
  __TABLE_AUTO_INCREMENT         = []
  __OWN_ROOM_ID_TABLE_TUPLE      = {item:None for item in __OWN_ROOM_ID_TABLE_HEADER}
  __SQL_CREATE_OWN_ROOM_ID_TABLE = '''
                                 CREATE TABLE IF NOT EXISTS {} (
                                   start_time            timestamp     NOT NULL,
                                   platform              varchar(20)   NOT NULL,
                                   owner_user_id         varchar(200)  NOT NULL,
                                   room_id_index         bigint        NOT NULL,
                                   room_id               varchar(200)  DEFAULT NULL,
                                   UNIQUE KEY unique_record (start_time, platform, owner_user_id, room_id_index)
                                   )
                                   '''.format(__OWN_ROOM_ID_TABLE_NAME)
  __SQL_DROP_OWN_ROOM_ID_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__OWN_ROOM_ID_TABLE_NAME)

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
    return self.__OWN_ROOM_ID_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__OWN_ROOM_ID_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__OWN_ROOM_ID_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__OWN_ROOM_ID_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_OWN_ROOM_ID_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_OWN_ROOM_ID_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## TODO
## data.room.owner.own_room.room_ids_display
## +-----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------+
## | Field                 | Type              | Null | Key | Default | Extra | Topology                                                 | Comment              |
## +-----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------+
## | start_time            | timestamp         | NO   | PRI |         |       | "$.data.room.start_time"                                 | 开始时间              | 
## | platform              | varchar(20)       | NO   | PRI |         |       |           -                                              | 平台                  |
## | owner_user_id         | varchar(200)      | NO   | PRI |         |       | "$.data.room.owner_user_id"                              | 账号作者ID            |
## | room_id_display_index | unsigned bigint   |      |     | NULL    |       | -                                                        | 直播间ID索引          | 
## | room_id_display       | TBD               |      |     | NULL    |       | "$.data.room.owner.own_room.room_ids_display             | 直播间ID显示          | 
## +-----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------+
##
class OwnRoomIdDisplayTable():
##
## >>=============================== attribute ===============================>>
##
  __OWN_ROOM_ID_DISPLAY_TABLE_NAME       = 'own_room_id_display'
  __OWN_ROOM_ID_DISPLAY_TABLE_HEADER     = ['start_time', 'platform', 'owner_user_id', 'room_id_display_index', 'room_id_display']
  __OWN_ROOM_ID_DISPLAY_TABLE_PRI_KEY    = ['room_id_display_index']
  __TABLE_AUTO_INCREMENT                 = ['room_id_display_index']
  __OWN_ROOM_ID_DISPLAY_TABLE_TUPLE      = {item:None for item in __OWN_ROOM_ID_DISPLAY_TABLE_HEADER}
  __SQL_CREATE_OWN_ROOM_ID_DISPLAY_TABLE = '''
                                           CREATE TABLE IF NOT EXISTS {} (
                                             start_time                timestamp     NOT NULL,
                                             platform                  varchar(20)   NOT NULL,
                                             owner_user_id             varchar(200)  NOT NULL,
                                             room_id_display_index     bigint        NOT NULL AUTO_INCREMENT,
                                             room_id_display           TBD           DEFAULT NULL,
                                             PRIMARY KEY (room_id_display_index),
                                             UNIQUE KEY unique_record (start_time, platform, owner_user_id, room_id_display)
                                             )
                                           '''.format(__OWN_ROOM_ID_DISPLAY_TABLE_NAME)
  __SQL_DROP_OWN_ROOM_ID_DISPLAY_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__OWN_ROOM_ID_DISPLAY_TABLE_NAME)

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
    return self.__OWN_ROOM_ID_DISPLAY_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__OWN_ROOM_ID_DISPLAY_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__OWN_ROOM_ID_DISPLAY_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__OWN_ROOM_ID_DISPLAY_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_OWN_ROOM_ID_DISPLAY_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_OWN_ROOM_ID_DISPLAY_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## fans club
##
## +-----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------+
## | Field                 | Type              | Null | Key | Default | Extra | Topology                                                 | Comment              |
## +-----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------+
## | now                   | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"                                            | 当前时间戳            | 
## | platform              | varchar(20)       | NO   | PRI |         |       |           -                                              | 平台                  |
## | room_id               | varchar(200)      |      |     | NULL    |       | "$.data.room.id"                                         | 直播间ID              | 
## | owner_user_id         | varchar(200)      | NO   | PRI |         |       | "$.data.room.owner_user_id"                              | 账号作者ID            |
## | anchor_id             | varchar(200)      | NO   | PRI |         |       | "$.data.room.owner.fans_club.data.anchor_id"             | 主播ID                |
## | anchor_open_id        | varchar(200)      |      |     | NULL    |       | "$.data.room.owner.fans_club.data.anchor_open_id"        | 主播OpenID            |
## | badge_type            | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.fans_club.data.badge_type"            | 勋章类型              |
## | badge_title           | tinytext          |      |     | NULL    |       | "$.data.room.owner.fans_club.data.badge.title"           | 勋章标题              |
## | club_name             | varchar(50)       |      |     | NULL    |       | "$.data.room.owner.fans_club.data.club_name"             | 俱乐部名称            |
## | guard_expired_time    | timestamp         |      |     | NULL    |       | "$.data.room.owner.fans_club.data.guard_expired_time"    | 俱乐部守护过期时间     |
## | level                 | unsigned smallint |      |     | NULL    |       | "$.data.room.owner.fans_club.data.level"                 | 俱乐部等级            |
## | user_fans_club_status | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.fans_club.data.user_fans_club_status" | 用户粉丝俱乐部状态     |
## | user_guard_status     | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.fans_club.data.user_guard_status"     | 用户守护状态           |
## | prefer_data           | json              |      |     | NULL    |       | "$.data.room.owner.fans_club.prefer_data"                | 偏好数据               |
## +-----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+-----------------------+
##
class FansClubTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __FANS_CLUB_TABLE_NAME       = 'fans_club'
  __FANS_CLUB_TABLE_HEADER     = ['now',                'platform',    'room_id',
                                  'owner_user_id',      'anchor_id',   'anchor_open_id',
                                  'badge_type',         'badge_title', 'club_name',
                                  'guard_expired_time', 'level',       'user_fans_club_status',
                                  'user_guard_status',  'prefer_data'
                                   ]
  __FANS_CLUB_TABLE_PRI_KEY    = ['now', 'platform', 'owner_user_id', 'anchor_id']
  __TABLE_AUTO_INCREMENT       = []
  __FANS_CLUB_TABLE_TUPLE      = {item:None for item in __FANS_CLUB_TABLE_HEADER}
  __SQL_CREATE_FANS_CLUB_TABLE = '''
                                 CREATE TABLE IF NOT EXISTS {} (
                                   now                   timestamp(3)  NOT NULL,
                                   platform              varchar(20)   NOT NULL,
                                   room_id               varchar(200)  DEFAULT NULL,
                                   owner_user_id         varchar(200)  NOT NULL,
                                   anchor_id             varchar(200)  NOT NULL,
                                   anchor_open_id        varchar(200)  DEFAULT NULL,
                                   badge_type            tinyint       DEFAULT NULL,
                                   badge_title           tinytext      DEFAULT NULL,
                                   club_name             varchar(50)   DEFAULT NULL,
                                   guard_expired_time    timestamp     DEFAULT NULL,
                                   level                 smallint      DEFAULT NULL,
                                   user_fans_club_status tinyint       DEFAULT NULL,
                                   user_guard_status     tinyint       DEFAULT NULL,
                                   prefer_data           json          DEFAULT NULL,
                                   PRIMARY KEY (now, platform, owner_user_id, anchor_id)
                                   )
                                   '''.format(__FANS_CLUB_TABLE_NAME)
  __SQL_DROP_FANS_CLUB_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__FANS_CLUB_TABLE_NAME)


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
    return self.__FANS_CLUB_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__FANS_CLUB_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__FANS_CLUB_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__FANS_CLUB_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_FANS_CLUB_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_FANS_CLUB_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## data.room.owner.fans_club.data.available_gift_ids
##
## +----------------------+-------------------+------+-----+---------+-------+-------------------------------------------------------+----------------------+
## | Field                | Type              | Null | Key | Default | Extra | Topology                                              | Comment              |
## +----------------------+-------------------+------+-----+---------+-------+-------------------------------------------------------+----------------------+
## | now                  | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"                                         | 当前时间戳            | 
## | platform             | varchar(20)       | NO   | PRI |         |       |           -                                           | 平台                  |
## | room_id              | varchar(200)      |      |     |         |       | "$.data.room.id"                                      | 直播间ID              | 
## | owner_user_id        | varchar(200)      | NO   | PRI |         |       | "$.data.room.owner_user_id"                           | 账号作者ID            |
## | anchor_id            | varchar(200)      | NO   | PRI |         |       | "$.data.room.owner.fans_club.data.anchor_id"          | 主播ID               |
## | available_gift_index | unsigned bigint   | NO   | PRI |         |       |           -                                           | 可用礼物序号          |
## | available_gift_id    | varchar(200)      |      |     | NULL    |       | "$.data.room.owner.fans_club.data.available_gift_ids" | 可用礼物ID列表        |
## +----------------------+-------------------+------+-----+---------+-------+-------------------------------------------------------+----------------------+
##
class FansClubAvailableGiftIdTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __FANS_CLUB_AVAILABLE_GIFT_ID_TABLE_NAME       = 'fans_club_available_gift_id'
  __FANS_CLUB_AVAILABLE_GIFT_ID_TABLE_HEADER     = ['now',                'platform',    'room_id',
                                                    'owner_user_id',      'anchor_id',   'available_gift_index',
                                                    'available_gift_id'
                                                     ]
  __FANS_CLUB_AVAILABLE_GIFT_ID_TABLE_PRI_KEY    = ['now', 'platform', 'owner_user_id', 'anchor_id', 'available_gift_index']
  __TABLE_AUTO_INCREMENT                         = []
  __FANS_CLUB_AVAILABLE_GIFT_ID_TABLE_TUPLE      = {item:None for item in __FANS_CLUB_AVAILABLE_GIFT_ID_TABLE_HEADER}
  __SQL_CREATE_FANS_CLUB_AVAILABLE_GIFT_ID_TABLE = '''
                                                   CREATE TABLE IF NOT EXISTS {} (
                                                     now                  timestamp(3)     NOT NULL,
                                                     platform             varchar(20)      NOT NULL,
                                                     room_id              varchar(200)     NOT NULL,
                                                     owner_user_id        varchar(200)     NOT NULL,
                                                     anchor_id            varchar(200)     NOT NULL,
                                                     available_gift_index bigint           NOT NULL,
                                                     available_gift_id    varchar(200)     DEFAULT NULL,
                                                     PRIMARY KEY (now, platform, room_id, owner_user_id, anchor_id, available_gift_index)
                                                     )
                                                     '''.format(__FANS_CLUB_AVAILABLE_GIFT_ID_TABLE_NAME)
  __SQL_DROP_FANS_CLUB_AVAILABLE_GIFT_ID_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__FANS_CLUB_AVAILABLE_GIFT_ID_TABLE_NAME)


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
    return self.__FANS_CLUB_AVAILABLE_GIFT_ID_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__FANS_CLUB_AVAILABLE_GIFT_ID_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__FANS_CLUB_AVAILABLE_GIFT_ID_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__FANS_CLUB_AVAILABLE_GIFT_ID_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_FANS_CLUB_AVAILABLE_GIFT_ID_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_FANS_CLUB_AVAILABLE_GIFT_ID_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## data.room.owner.fans_club.data
##
## +---------------+-------------------+------+-----+---------+-------+--------------------------------------------------------+----------------------+
## | Field         | Type              | Null | Key | Default | Extra | Topology                                               | Comment              |
## +---------------+-------------------+------+-----+---------+-------+--------------------------------------------------------+----------------------+
## | now           | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"                                          | 当前时间戳            | 
## | platform      | varchar(20)       | NO   | PRI |         |       |           -                                            | 平台                  |
## | room_id       | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                                       | 直播间ID              | 
## | owner_user_id | varchar(200)      | NO   | PRI |         |       | "$.data.room.owner_user_id"                            | 账号作者ID            |
## | anchor_id     | varchar(200)      |      |     | NULL    |       | "$.data.room.owner.fans_club.data.anchor_id"           | 主播ID                |
## | icon_index    | unsigned bigint   | NO   | PRI |         |       | "$.data.room.owner.fans_club.data.badge.icons.'0'"     | 勋章图标0             |
## | icon_uri      | text              |      |     | NULL    |       | "$.data.room.owner.fans_club.data.badge.icons.'0'.uri" | 勋章图标URI           |
## +---------------+-------------------+------+-----+---------+-------+--------------------------------------------------------+----------------------+
##
class FansClubBadgeIconTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __FANS_CLUB_BADGE_ICON_TABLE_NAME       = 'fans_club_badge_icon'
  __FANS_CLUB_BADGE_ICON_TABLE_HEADER     = ['now',                'platform',    'room_id',
                                             'owner_user_id',      'anchor_id',   'icon_index',
                                             'icon_uri'
                                             ]
  __FANS_CLUB_BADGE_ICON_TABLE_PRI_KEY    = ['now', 'platform', 'room_id', 'owner_user_id', 'icon_index']
  __TABLE_AUTO_INCREMENT                  = ['icon_index']
  __FANS_CLUB_BADGE_ICON_TABLE_TUPLE      = {item:None for item in __FANS_CLUB_BADGE_ICON_TABLE_HEADER}
  __SQL_CREATE_FANS_CLUB_BADGE_ICON_TABLE = '''
                                            CREATE TABLE IF NOT EXISTS {} (
                                              now                  timestamp(3)     NOT NULL,
                                              platform             varchar(20)      NOT NULL,
                                              room_id              varchar(200)     NOT NULL,
                                              owner_user_id        varchar(200)     NOT NULL,
                                              anchor_id            varchar(200)     DEFAULT NULL,
                                              icon_index           bigint           NOT NULL AUTO_INCREMENT,
                                              icon_uri             text             DEFAULT NULL,
                                              PRIMARY KEY (icon_index),
                                              UNIQUE KEY unique_record (now, platform, room_id, owner_user_id, icon_index)
                                              )
                                              '''.format(__FANS_CLUB_BADGE_ICON_TABLE_NAME)
  __SQL_DROP_FANS_CLUB_BADGE_ICON_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__FANS_CLUB_BADGE_ICON_TABLE_NAME)


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
    return self.__FANS_CLUB_BADGE_ICON_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__FANS_CLUB_BADGE_ICON_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__FANS_CLUB_BADGE_ICON_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__FANS_CLUB_BADGE_ICON_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_FANS_CLUB_BADGE_ICON_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_FANS_CLUB_BADGE_ICON_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## data.room.owner.user_attr
##
## +----------------+-------------------+------+-----+---------+-------+----------------------------------------------+---------------------+
## | Field          | Type              | Null | Key | Default | Extra | Topology                                     | Comment             |
## +----------------+-------------------+------+-----+---------+-------+----------------------------------------------+---------------------+
## | now            | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"                                | 当前时间戳           | 
## | platform       | varchar(20)       | NO   | PRI |         |       |           -                                  | 平台                 | 
## | room_id        | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                             | 直播间ID             | 
## | owner_user_id  | varchar(200)      | NO   | PRI |         |       | "$.data.room.owner_user_id"                  | 直播间主播ID         |
## | is_admin       | bool              |      |     | NULL    |       | "$.data.room.owner.user_attr.is_admin"       | 是否为管理员         |
## | is_muted       | bool              |      |     | NULL    |       | "$.data.room.owner.user_attr.is_muted"       | 是否被禁言           |
## | is_super_admin | bool              |      |     | NULL    |       | "$.data.room.owner.user_attr.is_super_admin" | 是否为超级管理员     |
## +----------------+-------------------+------+-----+---------+-------+----------------------------------------------+---------------------+
##
class RoomOwnerUserAttrTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_OWNER_USER_ATTR_TABLE_NAME       = 'room_owner_user_attr'
  __ROOM_OWNER_USER_ATTR_TABLE_HEADER     = ['now',                'platform',    'room_id',
                                             'owner_user_id',      'is_admin',    'is_muted',
                                             'is_super_admin'
                                             ]
  __ROOM_OWNER_USER_ATTR_TABLE_PRI_KEY    = ['now', 'platform', 'owner_user_id', 'room_id']
  __TABLE_AUTO_INCREMENT                  = []
  __ROOM_OWNER_USER_ATTR_TABLE_TUPLE      = {item:None for item in __ROOM_OWNER_USER_ATTR_TABLE_HEADER}
  __SQL_CREATE_ROOM_OWNER_USER_ATTR_TABLE = '''
                                            CREATE TABLE IF NOT EXISTS {} (
                                              now                  timestamp(3)     NOT NULL,
                                              platform             varchar(20)      NOT NULL,
                                              room_id              varchar(200)     NOT NULL,
                                              owner_user_id        varchar(200)     NOT NULL,
                                              is_admin             bool             DEFAULT NULL,
                                              is_muted             bool             DEFAULT NULL,
                                              is_super_admin       bool             DEFAULT NULL,
                                              PRIMARY KEY (now, platform, owner_user_id, room_id)
                                              )
                                              '''.format(__ROOM_OWNER_USER_ATTR_TABLE_NAME)
  __SQL_DROP_ROOM_OWNER_USER_ATTR_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_OWNER_USER_ATTR_TABLE_NAME)


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
    return self.__ROOM_OWNER_USER_ATTR_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_OWNER_USER_ATTR_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_OWNER_USER_ATTR_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_OWNER_USER_ATTR_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_OWNER_USER_ATTR_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_OWNER_USER_ATTR_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## data.room.owner.user_attr.admin_privileges
##
## +-----------------------+-------------------+------+-----+---------+-------+------------------------------------------------+---------------------+
## | Field                 | Type              | Null | Key | Default | Extra | Topology                                       | Comment             |
## +-----------------------+-------------------+------+-----+---------+-------+------------------------------------------------+---------------------+
## | now                   | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"                                  | 当前时间戳           | 
## | platform              | varchar(20)       | NO   | PRI |         |       |           -                                    | 平台                 | 
## | room_id               | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                               | 直播间ID             | 
## | owner_user_id         | varchar(200)      | NO   | PRI |         |       | "$.data.room.owner_user_id"                    | 直播间主播ID         |
## | admin_privilege_index | unsigned bigint   | NO   | PRI |         |       |           -                                    | 管理员权限序号       | 
## | admin_privilege       | text              |      |     | NULL    |       | "$.data.room.owner.user_attr.admin_privileges" | 管理员权限列表       |
## +-----------------------+-------------------+------+-----+---------+-------+------------------------------------------------+---------------------+
##
class RoomAdminPrivilegeTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_ADMIN_PRIVILEGE_TABLE_NAME       = 'room_admin_privilege'
  __ROOM_ADMIN_PRIVILEGE_TABLE_HEADER     = ['now',                'platform',                 'room_id',
                                             'owner_user_id',      'admin_privilege_index',    'admin_privilege'
                                             ]
  __ROOM_ADMIN_PRIVILEGE_TABLE_PRI_KEY    = ['now', 'platform', 'owner_user_id', 'room_id', 'admin_privilege_index']
  __TABLE_AUTO_INCREMENT                  = ['admin_privilege_index']
  __ROOM_ADMIN_PRIVILEGE_TABLE_TUPLE      = {item:None for item in __ROOM_ADMIN_PRIVILEGE_TABLE_HEADER}
  __SQL_CREATE_ROOM_ADMIN_PRIVILEGE_TABLE = '''
                                            CREATE TABLE IF NOT EXISTS {} (
                                              now                    timestamp(3)     NOT NULL,
                                              platform               varchar(20)      NOT NULL,
                                              room_id                varchar(200)     NOT NULL,
                                              owner_user_id          varchar(200)     NOT NULL,
                                              admin_privilege_index  bigint           NOT NULL AUTO_INCREMENT,
                                              admin_privilege        text             DEFAULT NULL,
                                              PRIMARY KEY (admin_privilege_index),
                                              UNIQUE KEY unique_record (now, platform, owner_user_id, room_id, admin_privilege_index)
                                              )
                                            '''.format(__ROOM_ADMIN_PRIVILEGE_TABLE_NAME)
  __SQL_DROP_ROOM_ADMIN_PRIVILEGE_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_ADMIN_PRIVILEGE_TABLE_NAME)


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
    return self.__ROOM_ADMIN_PRIVILEGE_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_ADMIN_PRIVILEGE_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_ADMIN_PRIVILEGE_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_ADMIN_PRIVILEGE_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_ADMIN_PRIVILEGE_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_ADMIN_PRIVILEGE_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

"""
authentication_info:
  account_cert_info: "{\"label_style\":5,\"label_text\":\"\u6D77\u53E3\u9F99\
    \u534E\u9A9E\u73AE\u670D\u9970\u5546\u884C\u5B98\u65B9\u8D26\u53F7\",\"\
    is_biz_account\":1,\"cert_label_list\":[{\"label_style\":5,\"label_text\"\
    :\"\u6D77\u53E3\u9F99\u534E\u9A9E\u73AE\u670D\u9970\u5546\u884C\u5B98\u65B9\
    \u8D26\u53F7\",\"is_biz_account\":1,\"badge\":{\"uri\":\"webcast/linear_blue_authentication_icon_3x.png\"\
    ,\"url_list\":[\"https://p11-webcast.douyinpic.com/img/webcast/linear_blue_authentication_icon_3x.png~tplv-obj.image\"\
    ,\"https://p3-webcast.douyinpic.com/img/webcast/linear_blue_authentication_icon_3x.png~tplv-obj.image\"\
    ],\"image_type\":66}},{\"label_style\":2,\"label_text\":\"\u6D77\u53E3\
    \u9F99\u534E\u9A9E\u73AE\u670D\u9970\u5546\u884C\u5B98\u65B9\u8D26\u53F7\
    \",\"is_biz_account\":1,\"badge\":{\"uri\":\"webcast/authentication_icon_02.png\"\
    ,\"url_list\":[\"https://p3-webcast.douyinpic.com/img/webcast/authentication_icon_02.png~tplv-obj.image\"\
    ,\"https://p11-webcast.douyinpic.com/img/webcast/authentication_icon_02.png~tplv-obj.image\"\
    ],\"image_type\":46}}]}"
  account_type_info:
    account_type_map: {}
  authentication_badge:
    avg_color: ''
    flex_setting_list: []
    height: 0
    image_type: 46
    is_animated: false
    open_web_url: sslocal://webcast_lynxview?type=popup&gravity=bottom&height=484&fixed_height=1&add_safe_area_height=0&url=https%3A%2F%2Flf-webcast-sourcecdn-tos.bytegecko.com%2Fobj%2Fbyte-gurd-source%2Fwebcast%2Fmono%2Flynx%2Fwebcast_native_lynx_community_douyin%2Fpages%2Fverifypage%2Ftemplate.js%3Fh5Url%3Daweme%253A%252F%252Fwebview%252F%253Furl%253Dhttps%25253A%25252F%25252Frenzheng.douyin.com%25252Fm%25252Fverified_account%25252Flanding%25253Fsource%25253Dc4k64t65kvkbf97sj3bg
    text_setting_list: []
    uri: webcast/authentication_icon_02.png
    url_list:
    - https://p3-webcast.douyinpic.com/img/webcast/authentication_icon_02.png~tplv-obj.image
    - https://p11-webcast.douyinpic.com/img/webcast/authentication_icon_02.png~tplv-obj.image
    width: 0
  authentication_badge_v2:
    avg_color: ''
    flex_setting_list: []
    height: 0
    image_type: 66
    is_animated: false
    open_web_url: ''
    text_setting_list: []
    uri: webcast/linear_blue_authentication_icon_3x.png
    url_list:
    - https://p11-webcast.douyinpic.com/img/webcast/linear_blue_authentication_icon_3x.png~tplv-obj.image
    - https://p3-webcast.douyinpic.com/img/webcast/linear_blue_authentication_icon_3x.png~tplv-obj.image
    width: 0
  custom_verify: ''
  enterprise_verify_reason: "\u6D77\u53E3\u9F99\u534E\u9A9E\u73AE\u670D\u9970\
    \u5546\u884C\u5B98\u65B9\u8D26\u53F7"
  level_list:
  - 1
  - 0
"""
##
## data.room.owner.authentication_info
## +-----------------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------------------------+----------------+
## | Field                       | Type              | Null | Key | Default | Extra | Topology                                                                   | Comment        |
## +-----------------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------------------------+----------------+
## | start_time                  | timestamp         | NO   | PRI |         |       | "$.extra.now"                                                              | 当前时间戳      | 
## | platform                    | varchar(20)       | NO   | PRI |         |       |           -                                                                | 平台            | 
## | room_id                     | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                                                           | 直播间ID        | 
## | owner_user_id               | varchar(200)      | NO   | PRI |         |       | "$.data.room.owner_user_id"                                                | 直播间主播ID     |
## | exist_authentication_info   | bool              |      |     |         |       |                                         -                                  | 存在认证信息     |
## | account_cert_info           | json              |      |     | NULL    |       | "$.data.room.owner.authentication_info.account_cert_info"                  | 认证证书信息     |
## | account_type_map            | json              |      |     | NULL    |       | "$.data.room.owner.authentication_info.account_type_info.account_type_map" | 认证账号类型映射 |
## | custom_verify               | text              |      |     | NULL    |       | "$.data.room.owner.authentication_info.custom_verify"                      | 顾客认证        |
## | enterprise_verify_reason    | text              |      |     | NULL    |       | "$.data.room.owner.authentication_info.enterprise_verify_reason"           | 企业认证理由    |
## +-----------------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------------------------+----------------+
##
class RoomOwnerAuthInfoTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_OWNER_AUTH_INFO_TABLE_NAME       = 'room_owner_auth_info'
  __ROOM_OWNER_AUTH_INFO_TABLE_HEADER     = ['start_time',       'platform',                  'room_id',
                                             'owner_user_id',    'exist_authentication_info', 'account_cert_info',
                                             'account_type_map', 'custom_verify',             'enterprise_verify_reason'
                                             ]
  __ROOM_OWNER_AUTH_INFO_TABLE_PRI_KEY    = ['start_time', 'platform', 'room_id', 'owner_user_id']
  __TABLE_AUTO_INCREMENT                  = []
  __ROOM_OWNER_AUTH_INFO_TABLE_TUPLE      = {item:None for item in __ROOM_OWNER_AUTH_INFO_TABLE_HEADER}
  __SQL_CREATE_ROOM_OWNER_AUTH_INFO_TABLE = '''
                                            CREATE TABLE IF NOT EXISTS {} (
                                              start_time             timestamp        NOT NULL,
                                              platform               varchar(20)      NOT NULL,
                                              room_id                varchar(200)     NOT NULL,
                                              owner_user_id          varchar(200)     NOT NULL,
                                              exist_authentication_info  bool         DEFAULT FALSE,
                                              account_cert_info          json         DEFAULT NULL,
                                              account_type_map           json         DEFAULT NULL,
                                              custom_verify              text         DEFAULT NULL,
                                              enterprise_verify_reason   text         DEFAULT NULL,
                                              PRIMARY KEY (start_time, platform, room_id, owner_user_id)
                                              )
                                            '''.format(__ROOM_OWNER_AUTH_INFO_TABLE_NAME)
  __SQL_DROP_ROOM_OWNER_AUTH_INFO_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_OWNER_AUTH_INFO_TABLE_NAME)


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
    return self.__ROOM_OWNER_AUTH_INFO_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_OWNER_AUTH_INFO_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_OWNER_AUTH_INFO_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_OWNER_AUTH_INFO_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_OWNER_AUTH_INFO_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_OWNER_AUTH_INFO_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## data.room.owner.authentication_info.level_list
## +---------------+-------------------+------+-----+---------+-------+----------------------------------------------------------------------------+---------------+
## | Field         | Type              | Null | Key | Default | Extra | Topology                                                                   | Comment       |
## +---------------+-------------------+------+-----+---------+-------+----------------------------------------------------------------------------+---------------+
## | start_time    | timestamp         | NO   |     |         |       | "$.extra.now"                                                              | 当前时间戳     | 
## | platform      | varchar(20)       | NO   |     |         |       |           -                                                                | 平台           | 
## | room_id       | varchar(200)      | NO   |     |         |       | "$.data.room.id"                                                           | 直播间ID       | 
## | owner_user_id | varchar(200)      | NO   |     |         |       | "$.data.room.owner_user_id"                                                | 直播间主播ID   |
## | level_index   | unsigned bigint   | NO   | PRI |         |       |                                 -                                          | 认证等级索引   |
## | level         | int               |      |     | NULL    |       | "$.data.room.owner.authentication_info.level_list"                         | 认证等级       |
## +---------------+-------------------+------+-----+---------+-------+----------------------------------------------------------------------------+---------------+
##
class RoomOwnerAuthLevelTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_OWNER_AUTH_LEVEL_TABLE_NAME       = 'room_owner_auth_level'
  __ROOM_OWNER_AUTH_LEVEL_TABLE_HEADER     = ['start_time',   'platform',    'room_id',
                                             'owner_user_id', 'level_index', 'level'
                                             ]
  __ROOM_OWNER_AUTH_LEVEL_TABLE_PRI_KEY    = ['start_time', 'platform', 'owner_user_id', 'room_id', 'level_index']
  __TABLE_AUTO_INCREMENT                   = []
  __ROOM_OWNER_AUTH_LEVEL_TABLE_TUPLE      = {item:None for item in __ROOM_OWNER_AUTH_LEVEL_TABLE_HEADER}
  __SQL_CREATE_ROOM_OWNER_AUTH_LEVEL_TABLE = '''
                                            CREATE TABLE IF NOT EXISTS {} (
                                              start_time    timestamp    NOT NULL,
                                              platform      varchar(20)  NOT NULL,
                                              room_id       varchar(200) NOT NULL,
                                              owner_user_id varchar(200) NOT NULL,
                                              level_index   bigint       NOT NULL,
                                              level         int          DEFAULT NULL,
                                              PRIMARY KEY (start_time, platform, owner_user_id, room_id, level_index)
                                              )
                                            '''.format(__ROOM_OWNER_AUTH_LEVEL_TABLE_NAME)
  __SQL_DROP_ROOM_OWNER_AUTH_LEVEL_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_OWNER_AUTH_LEVEL_TABLE_NAME)


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
    return self.__ROOM_OWNER_AUTH_LEVEL_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_OWNER_AUTH_LEVEL_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_OWNER_AUTH_LEVEL_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_OWNER_AUTH_LEVEL_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_OWNER_AUTH_LEVEL_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_OWNER_AUTH_LEVEL_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## user
##
## +------------------------------------------+------------------+------+-----+---------+-------+--------------------------------------------------------+--------------------------+
## | Field                                    | Type             | Null | Key | Default | Extra | Topology                                               | Comment                  |
## +------------------------------------------+------------------+------+-----+---------+-------+--------------------------------------------------------+--------------------------+
## | id                                       | varchar(200)     | NO   | PRI |         |       | "$.data.user.id"                                       | 直播间ID                  |
## | gender                                   | unsigned tinyint |      |     | NULL    |       | "$.data.user.gender"                                   | 性别（0-未知，1-男，2-女）  |
## | allow_be_located                         | bool             |      |     | NULL    |       | "$.data.user.owner.allow_be_located"                   | 是否允许被定位             |
## | age_range                                | unsigned tinyint |      |     | NULL    |       | "$.data.user.age_range"                                | 年龄范围                   |
## | adversary_authorization_info             | unsigned tinyint |      |     | NULL    |       | "$.data.user.adversary_authorization_info"             | 对手授权信息               |
## | adversary_user_status                    | unsigned tinyint |      |     | NULL    |       | "$.data.user.adversary_user_status"                    | 对手用户状态               |
## | allow_find_by_contacts                   | bool             |      |     | NULL    |       | "$.data.user.allow_find_by_contacts"                   | 是否允许通过联系人查找      |
## | allow_others_download_video              | bool             |      |     | NULL    |       | "$.data.user.allow_others_download_video"              | 是否允许其他人下载视频       |
## | allow_others_download_when_sharing_video | bool             |      |     | NULL    |       | "$.data.user.allow_others_download_when_sharing_video" | 是否允许其他人下载分享的视频  |
## | allow_share_show_profile                 | bool             |      |     | NULL    |       | "$.data.user.allow_share_show_profile"                 | 是否允许分享展示个人资料     |
## | allow_show_in_gossip                     | bool             |      |     | NULL    |       | "$.data.user.allow_show_in_gossip"                     | 是否允许在八卦中展示         |
## | allow_show_my_action                     | bool             |      |     | NULL    |       | "$.data.user.allow_show_my_action"                     | 是否允许展示我的动态         |
## | allow_strange_comment                    | bool             |      |     | NULL    |       | "$.data.user.allow_strange_comment"                    | 是否允许陌生人评论           |
## | allow_unfollower_comment                 | bool             |      |     | NULL    |       | "$.data.user.allow_unfollower_comment"                 | 是否允许非关注者评论         |
## | allow_use_linkmic                        | bool             |      |     | NULL    |       | "$.data.user.allow_use_linkmic"                        | 是否允许使用连麦            |
## | authorization_info                       | unsigned tinyint |      |     | NULL    |       | "$.data.user.authorization_info"                       | 授权信息                   |
## | bg_img_url                               | text             |      |     | NULL    |       | "$.data.user.bg_img_url"                               | 背景图片URL                 |
## | birthday                                 | timestamp        |      |     | NULL    |       | "$.data.user.birthday"                                 | 生日时间戳                  |
## | birthday_description                     | tinytext         |      |     | NULL    |       | "$.data.user.birthday_description"                     | 生日描述                   |
## | birthday_valid                           | bool             |      |     | NULL    |       | "$.data.user.birthday_valid"                           | 生日是否有效                |
## | block_status                             | unsigned tinyint |      |     | NULL    |       | "$.data.user.block_status"                             | 屏蔽状态：0-未屏蔽 1-已屏蔽  |
## | city                                     | varchar(100)     |      |     | NULL    |       | "$.data.user.city"                                     | 城市                       |
## | comment_restrict                         | unsigned tinyint |      |     | NULL    |       | "$.data.user.comment_restrict"                         | 评论限制                    |
## | constellation                            | varchar(20)      |      |     | NULL    |       | "$.data.user.constellation"                            | 星座                       |
## | consume_diamond_level                    | unsigned smallint|      |     | NULL    |       | "$.data.user.consume_diamond_level"                    | 消费钻石等级                |
## | create_time                              | timestamp        |      |     | NULL    |       | "$.data.user.create_time"                              | 账号创建时间戳              |
## | desensitized_nickname                    | varchar(50)      |      |     | NULL    |       | "$.data.user.desensitized_nickname"                    | 脱敏昵称                   |
## | disable_ichat                            | bool             |      |     | NULL    |       | "$.data.user.disable_ichat"                            | 是否禁用iChat               |
## | display_id                               | varchar(200)     |      |     | NULL    |       | "$.data.user.display_id"                               | 显示ID                     |
## | enable_ichat_img                         | unsigned tinyint |      |     | NULL    |       | "$.data.user.enable_ichat_img"                         | 是否启用iChat图片           |
## | fold_stranger_chat                       | bool             |      |     | NULL    |       | "$.data.user.fold_stranger_chat"                       | 是否折叠陌生人聊天          |
## | nickname                                 | varchar(50)      |      |     | NULL    |       | "$.data.user.nickname"                                 | 昵称                       |
## | pay_score                                | unsigned int     |      |     | NULL    |       | "$.data.user.pay_score"                                | 支付分                     |
## | pay_scores                               | unsigned int     |      |     | NULL    |       | "$.data.user.pay_scores"                               | 支付分                     |
## | need_profile_guide                       | bool             |      |     | NULL    |       | "$.data.user.need_profile_guide"                       | 是否需要个人资料引导         |
## | hotsoon_verified                         | bool             |      |     | NULL    |       | "$.data.user.hotsoon_verified"                         | 是否Hotsoon认证             |
## | hotsoon_verified_reason                  | bool             |      |     | NULL    |       | "$.data.user.hotsoon_verified_reason"                  | Hotsoon认证原因             |
## | ichat_restrict_type                      | unsigned tinyint |      |     | NULL    |       | "$.data.user.ichat_restrict_type"                      | iChat限制类型               |
## | income_share_percent                     | unsigned tinyint |      |     | NULL    |       | "$.data.user.income_share_percent"                     | 收入分成百分比              |
## | push_comment_status                      | bool             |      |     | NULL    |       | "$.data.user.push_comment_status"                      | 是否推送评论状态             |
## | push_digg                                | bool             |      |     | NULL    |       | "$.data.user.push_digg"                                | 是否推送点赞                |
## | push_follow                              | bool             |      |     | NULL    |       | "$.data.user.push_follow"                              | 是否推送关注                |
## | push_friend_action                       | bool             |      |     | NULL    |       | "$.data.user.push_friend_action"                       | 是否推送好友操作            |
## | push_ichat                               | bool             |      |     | NULL    |       | "$.data.user.push_ichat"                               | 是否推送iChat               |
## | push_status                              | bool             |      |     | NULL    |       | "$.data.user.push_status"                              | 是否推送状态                |
## | push_video_post                          | bool             |      |     | NULL    |       | "$.data.user.push_video_post"                          | 是否推送视频发布            |
## | push_video_recommend                     | bool             |      |     | NULL    |       | "$.data.user.push_video_recommend"                     | 是否推送视频推荐            |
## | remark_name                              | varchar(50)      |      |     | NULL    |       | "$.data.user.remark_name"                              | 备注名                     |
## | sec_uid                                  | varchar(200)     |      |     | NULL    |       | "$.data.user.sec_uid"                                  | 安全用户ID                 |
## | secret                                   | unsigned tinyint |      |     | NULL    |       | "$.data.user.secret"                                   | 是否私密                    |
## | share_qrcode_uri                         | text             |      |     | NULL    |       | "$.data.user.share_qrcode_uri"                         | 分享二维码URI               |
## | short_id                                 | varchar(200)     |      |     | NULL    |       | "$.data.user.short_id"                                 | 短ID                       |
## | signature                                | text             |      |     | NULL    |       | "$.data.user.signature"                                | 个性签名                    |
## | special_id                               | varchar(200)     |      |     | NULL    |       | "$.data.user.special_id"                               | 特殊ID                     |
## | status                                   | unsigned tinyint |      |     | NULL    |       | "$.data.user.status"                                   | 用户状态：0-注销 1-正常     |
## | telephone                                | varchar(20)      |      |     | NULL    |       | "$.data.user.telephone"                                | 电话号码                    |
## | total_recharge_diamond_count             | unsigned bigint  |      |     | NULL    |       | "$.data.user.total_recharge_diamond_count"             | 总充值钻石数量              |
## | user_canceled                            | bool             |      |     | NULL    |       | "$.data.user.user_canceled"                            | 用户是否已取消              |
## | user_open_id                             | varchar(200)     |      |     | NULL    |       | "$.data.user.user_open_id"                             | 用户开放ID                  |
## | user_role                                | unsigned tinyint |      |     | NULL    |       | "$.data.user.user_role"                                | 用户角色                    |
## | verified                                 | bool             |      |     | NULL    |       | "$.data.user.verified"                                 | 是否认证                    |
## | verified_content                         | tinytext         |      |     | NULL    |       | "$.data.user.verified_content"                         | 认证内容                    |
## | verified_mobile                          | bool             |      |     | NULL    |       | "$.data.user.verified_mobile"                          | 是否认证手机                |
## | verified_reason                          | tinytext         |      |     | NULL    |       | "$.data.user.verified_reason"                          | 认证原因                    |
## | watch_duration_month                     | unsigned tinyint |      |     | NULL    |       | "$.data.user.watch_duration_month"                     | 观看时长（月）              |
## | web_rid                                  | varchar(200)     |      |     | NULL    |       | "$.data.user.web_rid"                                  | Web用户ID                  |
## | webcast_uid                              | varchar(200)     |      |     | NULL    |       | "$.data.user.webcast_uid"                              | Webcast用户ID              |
## | with_car_management_permission           | bool             |      |     | NULL    |       | "$.data.user.with_car_management_permission"           | 是否具有汽车管理权限         |
## | with_commerce_permission                 | bool             |      |     | NULL    |       | "$.data.user.with_commerce_permission"                 | 是否具有商业权限            |
## | with_fusion_shop_entry                   | bool             |      |     | NULL    |       | "$.data.user.with_fusion_shop_entry"                   | 是否具有融合店铺入口         |
## +------------------------------------------+------------------+------+-----+---------+-------+--------------------------------------------------------+----------------------------+
##
class UserTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __USER_TABLE_NAME       = "user"
  __USER_TABLE_HEADER     = ['id',                    'gender',                       'allow_be_located',               'age_range',                                'adversary_authorization_info',
                             'adversary_user_status', 'allow_find_by_contacts',       'allow_others_download_video',    'allow_others_download_when_sharing_video', 'allow_share_show_profile',
                             'allow_show_in_gossip',  'allow_show_my_action',         'allow_strange_comment',          'allow_unfollower_comment',                 'allow_use_linkmic',
                             'authorization_info',    'bg_img_url',                   'birthday',                       'birthday_description',                     'birthday_valid',
                             'block_status',          'city',                         'comment_restrict',               'constellation',                            'consume_diamond_level',
                             'create_time',           'desensitized_nickname',        'disable_ichat',                  'display_id',                               'enable_ichat_img',
                             'fold_stranger_chat',    'nickname',                     'pay_score',                      'pay_scores',                               'need_profile_guide',
                             'hotsoon_verified',      'hotsoon_verified_reason',      'ichat_restrict_type',            'income_share_percent',                     'push_comment_status',
                             'push_digg',             'push_follow',                  'push_friend_action',             'push_ichat',                               'push_status',
                             'push_video_post',       'push_video_recommend',         'remark_name',                    'sec_uid',                                  'secret',
                             'share_qrcode_uri',      'short_id',                     'signature',                      'special_id',                               'status',
                             'telephone',             'total_recharge_diamond_count', 'user_canceled',                  'user_open_id',                             'user_role',
                             'verified',              'verified_content',             'verified_mobile',                'verified_reason',                          'watch_duration_month',
                             'web_rid',               'webcast_uid',                  'with_car_management_permission', 'with_commerce_permission',                 'with_fusion_shop_entry'
                             ]
  __USER_TABLE_PRI_KEY    = ['id']
  __TABLE_AUTO_INCREMENT  = []
  __USER_TABLE_TUPLE      = {item:None for item in __USER_TABLE_HEADER}
  __SQL_CREATE_USER_TABLE = '''
                            CREATE TABLE IF NOT EXISTS {} (
                              id                                        varchar(200)      NOT NULL,
                              gender                                    tinyint           DEFAULT NULL,
                              allow_be_located                          bool              DEFAULT NULL,
                              age_range                                 tinyint           DEFAULT NULL,
                              adversary_authorization_info              tinyint           DEFAULT NULL,
                              adversary_user_status                     tinyint           DEFAULT NULL,
                              allow_find_by_contacts                    bool              DEFAULT NULL,
                              allow_others_download_video               bool              DEFAULT NULL,
                              allow_others_download_when_sharing_video  bool              DEFAULT NULL,
                              allow_share_show_profile                  bool              DEFAULT NULL,
                              allow_show_in_gossip                      bool              DEFAULT NULL,
                              allow_show_my_action                      bool              DEFAULT NULL,
                              allow_strange_comment                     bool              DEFAULT NULL,
                              allow_unfollower_comment                  bool              DEFAULT NULL,
                              allow_use_linkmic                         bool              DEFAULT NULL,
                              authorization_info                        tinyint           DEFAULT NULL,
                              bg_img_url                                text              DEFAULT NULL,
                              birthday                                  timestamp         DEFAULT NULL,
                              birthday_description                      tinytext          DEFAULT NULL,
                              birthday_valid                            bool              DEFAULT NULL,
                              block_status                              tinyint           DEFAULT NULL,
                              city                                      varchar(100)      DEFAULT NULL,
                              comment_restrict                          tinyint           DEFAULT NULL,
                              constellation                             varchar(20)       DEFAULT NULL,
                              consume_diamond_level                     smallint          DEFAULT NULL,
                              create_time                               timestamp         DEFAULT NULL,
                              desensitized_nickname                     varchar(50)       DEFAULT NULL,
                              disable_ichat                             bool              DEFAULT NULL,
                              display_id                                varchar(200)      DEFAULT NULL,
                              enable_ichat_img                          tinyint           DEFAULT NULL,
                              fold_stranger_chat                        bool              DEFAULT NULL,
                              nickname                                  varchar(50)       DEFAULT NULL,
                              pay_score                                 int               DEFAULT NULL,
                              pay_scores                                int               DEFAULT NULL,
                              need_profile_guide                        bool              DEFAULT NULL,
                              hotsoon_verified                          bool              DEFAULT NULL,
                              hotsoon_verified_reason                   bool              DEFAULT NULL,
                              ichat_restrict_type                       tinyint           DEFAULT NULL,
                              income_share_percent                      tinyint           DEFAULT NULL,
                              push_comment_status                       bool              DEFAULT NULL,
                              push_digg                                 bool              DEFAULT NULL,
                              push_follow                               bool              DEFAULT NULL,
                              push_friend_action                        bool              DEFAULT NULL,
                              push_ichat                                bool              DEFAULT NULL,
                              push_status                               bool              DEFAULT NULL,
                              push_video_post                           bool              DEFAULT NULL,
                              push_video_recommend                      bool              DEFAULT NULL,
                              remark_name                               varchar(50)       DEFAULT NULL,
                              sec_uid                                   varchar(200)      DEFAULT NULL,
                              secret                                    tinyint           DEFAULT NULL,
                              share_qrcode_uri                          text              DEFAULT NULL,
                              short_id                                  varchar(200)      DEFAULT NULL,
                              signature                                 text              DEFAULT NULL,
                              special_id                                varchar(200)      DEFAULT NULL,
                              status                                    tinyint           DEFAULT NULL,
                              telephone                                 varchar(20)       DEFAULT NULL,
                              total_recharge_diamond_count              bigint            DEFAULT NULL,
                              user_canceled                             bool              DEFAULT NULL,
                              user_open_id                              varchar(200)      DEFAULT NULL,
                              user_role                                 tinyint           DEFAULT NULL,
                              verified                                  bool              DEFAULT NULL,
                              verified_content                          tinytext          DEFAULT NULL,
                              verified_mobile                           bool              DEFAULT NULL,
                              verified_reason                           tinytext          DEFAULT NULL,
                              watch_duration_month                      tinyint           DEFAULT NULL,
                              web_rid                                   varchar(200)      DEFAULT NULL,
                              webcast_uid                               varchar(200)      DEFAULT NULL,
                              with_car_management_permission            bool              DEFAULT NULL,
                              with_commerce_permission                  bool              DEFAULT NULL,
                              with_fusion_shop_entry                    bool              DEFAULT NULL,
                              PRIMARY KEY (id)
                            )
                            '''.format(__USER_TABLE_NAME)
  __SQL_DROP_USER_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__USER_TABLE_NAME)

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
    return self.__USER_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__USER_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__USER_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__USER_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_USER_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_USER_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## data.room.owner.author_stats
##
## +----------------------------+------------------+------+-----+---------+-------+----------------------------------------------------------------------------+--------------------------+
## | Field                      | Type             | Null | Key | Default | Extra | Topology                                                                   | Comment                  |
## +----------------------------+------------------+------+-----+---------+-------+----------------------------------------------------------------------------+--------------------------+
## | start_time                 | timestamp        | NO   | PRI |         |       | "$.extra.now"                                                              | 当前时间戳                | 
## | platform                   | varchar(20)      | NO   | PRI |         |       |           -                                                                | 平台                      | 
## | room_id                    | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                                                           | 直播间ID                  | 
## | owner_user_id              | varchar(200)     | NO   | PRI |         |       | "$.data.room.owner_user_id"                                                | 直播间主播ID              |
## | variety_show_play_count    | unsigned int     |      |     | 0       |       | "$.data.room.owner.author_stats.variety_show_play_count"                   |                          |
## | video_total_count          | unsigned int     |      |     | 0       |       | "$.data.room.owner.author_stats.video_total_count"                         |                          |      
## | video_total_favorite_count | unsigned int     |      |     | 0       |       | "$.data.room.owner.author_stats.video_total_favorite_count"                |                          |      
## | video_total_play_count     | unsigned int     |      |     | 0       |       | "$.data.room.owner.author_stats.video_total_play_count"                    |                          |      
## | video_total_series_count   | unsigned int     |      |     | 0       |       | "$.data.room.owner.author_stats.video_total_series_count"                  |                          |      
## | video_total_share_count    | unsigned int     |      |     | 0       |       | "$.data.room.owner.author_stats.video_total_share_count"                   |                          |      
## +----------------------------+------------------+------+-----+---------+-------+----------------------------------------------------------------------------+--------------------------+
##
class RoomOwnerAuthorStatsTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_OWNER_AUTHOR_STATS_TABLE_NAME       = 'room_owner_author_stats'
  __ROOM_OWNER_AUTHOR_STATS_TABLE_HEADER     = ['start_time',               'platform',               'room_id',                    'owner_user_id', 
                                                'variety_show_play_count',  'video_total_count',      'video_total_favorite_count', 'video_total_play_count',
                                                'video_total_series_count', 'video_total_share_count'
                                               ]
  __ROOM_OWNER_AUTHOR_STATS_TABLE_PRI_KEY    = ['start_time', 'platform', 'owner_user_id', 'room_id']
  __TABLE_AUTO_INCREMENT                     = []
  __ROOM_OWNER_AUTHOR_STATS_TABLE_TUPLE      = {item:None for item in __ROOM_OWNER_AUTHOR_STATS_TABLE_HEADER}
  __SQL_CREATE_ROOM_OWNER_AUTHOR_STATS_TABLE = '''
                                                 CREATE TABLE IF NOT EXISTS {} (
                                                   start_time                  timestamp     NOT NULL,
                                                   platform                    varchar(20)   NOT NULL,
                                                   room_id                     varchar(200)  NOT NULL,
                                                   owner_user_id               varchar(200)  NOT NULL,
                                                   variety_show_play_count     int           DEFAULT NULL,
                                                   video_total_count           int           DEFAULT NULL,
                                                   video_total_favorite_count  int           DEFAULT NULL,
                                                   video_total_play_count      int           DEFAULT NULL,
                                                   video_total_series_count    int           DEFAULT NULL,
                                                   video_total_share_count     int           DEFAULT NULL,
                                                   PRIMARY KEY (start_time, platform, owner_user_id, room_id)
                                                   )
                                               '''.format(__ROOM_OWNER_AUTHOR_STATS_TABLE_NAME)
  __SQL_DROP_ROOM_OWNER_AUTHOR_STATS_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_OWNER_AUTHOR_STATS_TABLE_NAME)


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
    return self.__ROOM_OWNER_AUTHOR_STATS_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_OWNER_AUTHOR_STATS_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_OWNER_AUTHOR_STATS_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_OWNER_AUTHOR_STATS_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_OWNER_AUTHOR_STATS_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_OWNER_AUTHOR_STATS_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()