##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Third-Part>>
from backend.src.database.social_media_stream_database                import SocialMediaStreamDataBase
from backend.src.database.table.social_media_stream_db_table          import SocialMediaStreamDataTable


##
## user table - 用户信息表
##
## +--------------------------------------+-------------------+------+-----+---------------------+-------+---------------------------------------------+----------------------+
## | Field                                | Type              | Null | Key | Default             | Extra | Topology                                    | Comment              |
## +--------------------------------------+-------------------+------+-----+---------------------+-------+---------------------------------------------+----------------------+
## | id                                   | varchar(200)      | NO   | PRI |                     |       | "$.data.user.id"                            | 用户 ID              |
## | adversary_authorization_info         | tinyint unsigned  | YES  |     | 0                   |       | "$.data.user.adversary_authorization_info"  | 对手授权信息         |
## | adversary_user_status                | tinyint unsigned  | YES  |     | 0                   |       | "$.data.user.adversary_user_status"         | 对手用户状态         |
## | age_range                            | tinyint unsigned  | YES  |     | 0                   |       | "$.data.user.age_range"                     | 年龄范围             |
## | allow_be_located                     | bool              | YES  |     | FALSE               |       | "$.data.user.allow_be_located"              | 允许被定位           |
## | allow_find_by_contacts               | bool              | YES  |     | FALSE               |       | "$.data.user.allow_find_by_contacts"        | 允许通过联系人找到   |
## | allow_others_download_video          | bool              | YES  |     | FALSE               |       | "$.data.user.allow_others_download_video"   | 允许他人下载视频     |
## | allow_others_download_when_sharing_video | bool         | YES  |     | FALSE               |       | "$.data.user.allow_others_download_when_sharing_video" | 分享视频时允许下载 |
## | allow_share_show_profile             | bool              | YES  |     | FALSE               |       | "$.data.user.allow_share_show_profile"      | 允许分享展示资料     |
## | allow_show_in_gossip                 | bool              | YES  |     | FALSE               |       | "$.data.user.allow_show_in_gossip"          | 允许在闲聊中展示     |
## | allow_show_my_action                 | bool              | YES  |     | FALSE               |       | "$.data.user.allow_show_my_action"          | 允许展示我的动态     |
## | allow_strange_comment                | bool              | YES  |     | FALSE               |       | "$.data.user.allow_strange_comment"         | 允许陌生人评论       |
## | allow_unfollower_comment             | bool              | YES  |     | FALSE               |       | "$.data.user.allow_unfollower_comment"      | 允许未关注者评论     |
## | allow_use_linkmic                    | bool              | YES  |     | FALSE               |       | "$.data.user.allow_use_linkmic"             | 允许使用连麦         |
## | authorization_info                   | tinyint unsigned  | YES  |     | 0                   |       | "$.data.user.authorization_info"            | 授权信息             |
## | badge_image_list                     | JSON              | YES  |     | NULL                |       | "$.data.user.badge_image_list"              | 徽章列表             |
## | badge_image_list_v2                  | JSON              | YES  |     | NULL                |       | "$.data.user.badge_image_list_v2"           | 徽章列表 V2          |
## | bg_img_url                           | text              | YES  |     | NULL                |       | "$.data.user.bg_img_url"                    | 背景图 URL           |
## | birthday                             | bigint            | YES  |     | 0                   |       | "$.data.user.birthday"                      | 生日时间戳           |
## | birthday_description                 | varchar(100)      | YES  |     | NULL                |       | "$.data.user.birthday_description"          | 生日描述             |
## | birthday_valid                       | bool              | YES  |     | FALSE               |       | "$.data.user.birthday_valid"                | 生日是否有效         |
## | block_status                         | tinyint unsigned  | YES  |     | 0                   |       | "$.data.user.block_status"                  | 屏蔽状态             |
## | city                                 | varchar(100)      | YES  |     | NULL                |       | "$.data.user.city"                          | 城市                 |
## | comment_restrict                     | tinyint unsigned  | YES  |     | 0                   |       | "$.data.user.comment_restrict"              | 评论限制             |
## | commerce_webcast_config_ids          | JSON              | YES  |     | NULL                |       | "$.data.user.commerce_webcast_config_ids"   | 电商直播配置 IDs     |
## | constellation                        | varchar(20)       | YES  |     | NULL                |       | "$.data.user.constellation"                 | 星座                 |
## | consume_diamond_level                | tinyint unsigned  | YES  |     | 0                   |       | "$.data.user.consume_diamond_level"         | 消费钻石等级         |
## | create_time                          | bigint            | YES  |     | 0                   |       | "$.data.user.create_time"                   | 创建时间             |
## | desensitized_nickname                | varchar(50)       | YES  |     | NULL                |       | "$.data.user.desensitized_nickname"         | 脱敏昵称             |
## | disable_ichat                        | tinyint unsigned  | YES  |     | 0                   |       | "$.data.user.disable_ichat"                 | 禁用聊天             |
## | display_id                           | varchar(50)       | YES  |     | NULL                |       | "$.data.user.display_id"                    | 展示 ID              |
## | enable_ichat_img                     | tinyint unsigned  | YES  |     | 0                   |       | "$.data.user.enable_ichat_img"              | 启用聊天图片         |
## | exp                                  | bigint            | YES  |     | 0                   |       | "$.data.user.exp"                           | 经验值               |
## | experience                           | bigint            | YES  |     | 0                   |       | "$.data.user.experience"                    | 经验                 |
## | fan_ticket_count                     | bigint            | YES  |     | 0                   |       | "$.data.user.fan_ticket_count"              | 粉丝票数             |
## | fold_stranger_chat                   | bool              | YES  |     | FALSE               |       | "$.data.user.fold_stranger_chat"            | 折叠陌生人聊天       |
## | follow_status                        | tinyint unsigned  | YES  |     | 0                   |       | "$.data.user.follow_status"                 | 关注状态             |
## | foreign_user                         | tinyint unsigned  | YES  |     | 0                   |       | "$.data.user.foreign_user"                  | 是否海外用户         |
## | gender                               | tinyint unsigned  | YES  |     | 0                   |       | "$.data.user.gender"                        | 性别                 |
## | hotsoon_verified                     | bool              | YES  |     | FALSE               |       | "$.data.user.hotsoon_verified"              | 快手认证             |
## | hotsoon_verified_reason              | varchar(255)      | YES  |     | NULL                |       | "$.data.user.hotsoon_verified_reason"       | 快手认证原因         |
## | ichat_restrict_type                  | tinyint unsigned  | YES  |     | 0                   |       | "$.data.user.ichat_restrict_type"           | 聊天限制类型         |
## | income_share_percent                 | tinyint unsigned  | YES  |     | 0                   |       | "$.data.user.income_share_percent"          | 收入分成比例         |
## | is_anonymous                         | bool              | YES  |     | FALSE               |       | "$.data.user.is_anonymous"                  | 是否匿名             |
## | is_follower                          | bool              | YES  |     | FALSE               |       | "$.data.user.is_follower"                   | 是否粉丝             |
## | is_following                         | bool              | YES  |     | FALSE               |       | "$.data.user.is_following"                  | 是否关注             |
## | level                                | smallint unsigned | YES  |     | 0                   |       | "$.data.user.level"                         | 等级                 |
## | link_mic_stats                       | tinyint unsigned  | YES  |     | 0                   |       | "$.data.user.link_mic_stats"                | 连麦统计             |
## | location_city                        | varchar(100)      | YES  |     | NULL                |       | "$.data.user.location_city"                 | 定位城市             |
## | media_badge_image_list               | JSON              | YES  |     | NULL                |       | "$.data.user.media_badge_image_list"        | 媒体徽章列表         |
## | modify_time                          | bigint            | YES  |     | 0                   |       | "$.data.user.modify_time"                   | 修改时间             |
## | mystery_man                          | tinyint unsigned  | YES  |     | 0                   |       | "$.data.user.mystery_man"                   | 神秘人标识           |
## | need_profile_guide                   | bool              | YES  |     | FALSE               |       | "$.data.user.need_profile_guide"            | 需要资料引导         |
## | new_real_time_icons                  | JSON              | YES  |     | NULL                |       | "$.data.user.new_real_time_icons"           | 新实时图标           |
## | nickname                             | varchar(50)       | YES  |     | NULL                |       | "$.data.user.nickname"                      | 昵称                 |
## | pay_score                            | bigint            | YES  |     | 0                   |       | "$.data.user.pay_score"                     | 支付分数             |
## | pay_scores                           | bigint            | YES  |     | 0                   |       | "$.data.user.pay_scores"                    | 支付分数（复数）     |
## | public_area_oper_freq                | tinyint unsigned  | YES  |     | 0                   |       | "$.data.user.public_area_oper_freq"         | 公共区域操作频率     |
## | push_comment_status                  | bool              | YES  |     | FALSE               |       | "$.data.user.push_comment_status"           | 推送评论状态         |
## | push_digg                            | bool              | YES  |     | FALSE               |       | "$.data.user.push_digg"                     | 推送点赞             |
## | push_follow                          | bool              | YES  |     | FALSE               |       | "$.data.user.push_follow"                   | 推送关注             |
## | push_friend_action                   | bool              | YES  |     | FALSE               |       | "$.data.user.push_friend_action"            | 推送好友动态         |
## | push_ichat                           | bool              | YES  |     | FALSE               |       | "$.data.user.push_ichat"                    | 推送聊天             |
## | push_status                          | bool              | YES  |     | FALSE               |       | "$.data.user.push_status"                   | 推送状态             |
## | push_video_post                      | bool              | YES  |     | FALSE               |       | "$.data.user.push_video_post"               | 推送视频发布         |
## | push_video_recommend                 | bool              | YES  |     | FALSE               |       | "$.data.user.push_video_recommend"          | 推送视频推荐         |
## | real_time_icons                      | JSON              | YES  |     | NULL                |       | "$.data.user.real_time_icons"               | 实时图标             |
## | remark_name                          | varchar(50)       | YES  |     | NULL                |       | "$.data.user.remark_name"                   | 备注名               |
## | sec_uid                              | text              | YES  |     | NULL                |       | "$.data.user.sec_uid"                       | 安全 UID             |
## | secret                               | tinyint unsigned  | YES  |     | 0                   |       | "$.data.user.secret"                        | 隐私设置             |
## | share_qrcode_uri                     | text              | YES  |     | NULL                |       | "$.data.user.share_qrcode_uri"              | 分享二维码 URI       |
## | short_id                             | varchar(50)       | YES  |     | NULL                |       | "$.data.user.short_id"                      | 短 ID                |
## | signature                            | text              | YES  |     | NULL                |       | "$.data.user.signature"                     | 签名                 |
## | special_id                           | varchar(100)      | YES  |     | NULL                |       | "$.data.user.special_id"                    | 特殊 ID              |
## | status                               | tinyint unsigned  | YES  |     | 0                   |       | "$.data.user.status"                        | 状态                 |
## | telephone                            | varchar(20)       | YES  |     | NULL                |       | "$.data.user.telephone"                     | 电话                 |
## | ticket_count                         | bigint            | YES  |     | 0                   |       | "$.data.user.ticket_count"                  | 门票数               |
## | top_fans                             | JSON              | YES  |     | NULL                |       | "$.data.user.top_fans"                      | 头部粉丝列表         |
## | top_vip_no                           | int unsigned      | YES  |     | 0                   |       | "$.data.user.top_vip_no"                    | VIP 排名             |
## | total_recharge_diamond_count         | bigint            | YES  |     | 0                   |       | "$.data.user.total_recharge_diamond_count"  | 总充值钻石           |
## | user_canceled                        | bool              | YES  |     | FALSE               |       | "$.data.user.user_canceled"                 | 用户是否注销         |
## | user_open_id                         | varchar(200)      | YES  |     | NULL                |       | "$.data.user.user_open_id"                  | 用户开放 ID          |
## | user_role                            | tinyint unsigned  | YES  |     | 0                   |       | "$.data.user.user_role"                     | 用户角色             |
## | verified                             | bool              | YES  |     | FALSE               |       | "$.data.user.verified"                      | 是否认证             |
## | verified_content                     | text              | YES  |     | NULL                |       | "$.data.user.verified_content"              | 认证内容             |
## | verified_mobile                      | bool              | YES  |     | FALSE               |       | "$.data.user.verified_mobile"               | 是否手机认证         |
## | verified_reason                      | varchar(255)      | YES  |     | NULL                |       | "$.data.user.verified_reason"               | 认证原因             |
## | watch_duration_month                 | int unsigned      | YES  |     | 0                   |       | "$.data.user.watch_duration_month"          | 月观看时长           |
## | web_rid                              | varchar(100)      | YES  |     | NULL                |       | "$.data.user.web_rid"                       | 网页 RID             |
## | webcast_uid                          | text              | YES  |     | NULL                |       | "$.data.user.webcast_uid"                   | Webcast UID          |
## | with_car_management_permission       | bool              | YES  |     | FALSE               |       | "$.data.user.with_car_management_permission"| 座驾管理权限         |
## | with_commerce_permission             | bool              | YES  |     | FALSE               |       | "$.data.user.with_commerce_permission"      | 电商权限             |
## | with_fusion_shop_entry               | bool              | YES  |     | FALSE               |       | "$.data.user.with_fusion_shop_entry"        | 融合店铺入口         |
## | can_view_webcast_private             | tinyint unsigned  | YES  |     | 0                   |       | "$.data.user.can_view_webcast_private"      | 可见私密直播         |
## | webcast_nick                         | varchar(50)       | YES  |     | NULL                |       | "$.data.user.webcast_nick"                  | Webcast 昵称         |
## | webcast_private                      | tinyint unsigned  | YES  |     | 0                   |       | "$.data.user.webcast_private"               | 私密直播状态         |
## | hide_by_room                         | tinyint unsigned  | YES  |     | 0                   |       | "$.data.user.hide_by_room"                  | 房间隐藏标记         |
## | link_mask                            | tinyint unsigned  | YES  |     | 0                   |       | "$.data.user.link_mask"                     | 连麦掩码             |
## | created_at                           | timestamp         | YES  |     | CURRENT_TIMESTAMP   |       | -                                           | 创建时间             |
## | updated_at                           | timestamp         | YES  |     | CURRENT_TIMESTAMP   |       | -                                           | 更新时间             |
## +--------------------------------------+-------------------+------+-----+---------------------+-------+---------------------------------------------+----------------------+
##
class UserTable(SocialMediaStreamDataTable):
##
## >>=============================== user ===============================>>
##
	__USER_TABLE_NAME: str = 'user'
	__USER_TABLE_HEADER: list[str] = [
		'id',
		'adversary_authorization_info',    'adversary_user_status',
		'age_range',                       'allow_be_located',
		'allow_find_by_contacts',          'allow_others_download_video',
		'allow_others_download_when_sharing_video',
		'allow_share_show_profile',        'allow_show_in_gossip',
		'allow_show_my_action',            'allow_strange_comment',
		'allow_unfollower_comment',        'allow_use_linkmic',
		'authorization_info',              'badge_image_list',
		'badge_image_list_v2',             'bg_img_url',
		'birthday',                        'birthday_description',
		'birthday_valid',                  'block_status',
		'city',                            'comment_restrict',
		'commerce_webcast_config_ids',     'constellation',
		'consume_diamond_level',           'create_time',
		'desensitized_nickname',           'disable_ichat',
		'display_id',                      'enable_ichat_img',
		'exp',                             'experience',
		'fan_ticket_count',                'fold_stranger_chat',
		'follow_status',                   'foreign_user',
		'gender',                          'hotsoon_verified',
		'hotsoon_verified_reason',         'ichat_restrict_type',
		'income_share_percent',            'is_anonymous',
		'is_follower',                     'is_following',
		'level',                           'link_mic_stats',
		'location_city',                   'media_badge_image_list',
		'modify_time',                     'mystery_man',
		'need_profile_guide',              'new_real_time_icons',
		'nickname',                        'pay_score',
		'pay_scores',                      'public_area_oper_freq',
		'push_comment_status',             'push_digg',
		'push_follow',                     'push_friend_action',
		'push_ichat',                      'push_status',
		'push_video_post',                 'push_video_recommend',
		'real_time_icons',                 'remark_name',
		'sec_uid',                         'secret',
		'share_qrcode_uri',                'short_id',
		'signature',                       'special_id',
		'status',                          'telephone',
		'ticket_count',                    'top_fans',
		'top_vip_no',                      'total_recharge_diamond_count',
		'user_canceled',                   'user_open_id',
		'user_role',                       'verified',
		'verified_content',                'verified_mobile',
		'verified_reason',                 'watch_duration_month',
		'web_rid',                         'webcast_uid',
		'with_car_management_permission',  'with_commerce_permission',
		'with_fusion_shop_entry',          'can_view_webcast_private',
		'webcast_nick',                    'webcast_private',
		'hide_by_room',                    'link_mask',
		'created_at',                      'updated_at'
	]
	__USER_TABLE_PRI_KEY: list[str] = ['id']
	__TABLE_AUTO_INCREMENT: list[str] = []
	__USER_TABLE_TUPLE: dict[str, None] = {item:None for item in __USER_TABLE_HEADER}
	__SQL_CREATE_USER_TABLE: str = '''
														CREATE TABLE IF NOT EXISTS `{}` (
															id                                       varchar(200)   NOT NULL,

															adversary_authorization_info             tinyint unsigned DEFAULT 0,
															adversary_user_status                    tinyint unsigned DEFAULT 0,
															age_range                                tinyint unsigned DEFAULT 0,
															allow_be_located                         bool           DEFAULT FALSE,
															allow_find_by_contacts                   bool           DEFAULT FALSE,
															allow_others_download_video              bool           DEFAULT FALSE,
															allow_others_download_when_sharing_video bool           DEFAULT FALSE,
															allow_share_show_profile                 bool           DEFAULT FALSE,
															allow_show_in_gossip                     bool           DEFAULT FALSE,
															allow_show_my_action                     bool           DEFAULT FALSE,
															allow_strange_comment                    bool           DEFAULT FALSE,
															allow_unfollower_comment                 bool           DEFAULT FALSE,
															allow_use_linkmic                        bool           DEFAULT FALSE,
															authorization_info                       tinyint unsigned DEFAULT 0,
															badge_image_list                         JSON           DEFAULT NULL,
															badge_image_list_v2                      JSON           DEFAULT NULL,
															bg_img_url                               text           DEFAULT NULL,
															birthday                                 bigint         DEFAULT 0,
															birthday_description                     varchar(100)   DEFAULT NULL,
															birthday_valid                           bool           DEFAULT FALSE,
															block_status                             tinyint unsigned DEFAULT 0,
															city                                     varchar(100)   DEFAULT NULL,
															comment_restrict                         tinyint unsigned DEFAULT 0,
															commerce_webcast_config_ids              JSON           DEFAULT NULL,
															constellation                            varchar(20)    DEFAULT NULL,
															consume_diamond_level                    tinyint unsigned DEFAULT 0,
															create_time                              bigint         DEFAULT 0,
															desensitized_nickname                    varchar(50)    DEFAULT NULL,
															disable_ichat                            tinyint unsigned DEFAULT 0,
															display_id                               varchar(50)    DEFAULT NULL,
															enable_ichat_img                         tinyint unsigned DEFAULT 0,
															exp                                      bigint         DEFAULT 0,
															experience                               bigint         DEFAULT 0,
															fan_ticket_count                         bigint         DEFAULT 0,
															fold_stranger_chat                       bool           DEFAULT FALSE,
															follow_status                            tinyint unsigned DEFAULT 0,
															foreign_user                             tinyint unsigned DEFAULT 0,
															gender                                   tinyint unsigned DEFAULT 0,
															hotsoon_verified                         bool           DEFAULT FALSE,
															hotsoon_verified_reason                  varchar(255)   DEFAULT NULL,
															ichat_restrict_type                      tinyint unsigned DEFAULT 0,
															income_share_percent                     tinyint unsigned DEFAULT 0,
															is_anonymous                             bool           DEFAULT FALSE,
															is_follower                              bool           DEFAULT FALSE,
															is_following                             bool           DEFAULT FALSE,
															level                                    smallint unsigned DEFAULT 0,
															link_mic_stats                           tinyint unsigned DEFAULT 0,
															location_city                            varchar(100)   DEFAULT NULL,
															media_badge_image_list                   JSON           DEFAULT NULL,
															modify_time                              bigint         DEFAULT 0,
															mystery_man                              tinyint unsigned DEFAULT 0,
															need_profile_guide                       bool           DEFAULT FALSE,
															new_real_time_icons                      JSON           DEFAULT NULL,
															nickname                                 varchar(50)    DEFAULT NULL,
															pay_score                                bigint         DEFAULT 0,
															pay_scores                               bigint         DEFAULT 0,
															public_area_oper_freq                    tinyint unsigned DEFAULT 0,
															push_comment_status                      bool           DEFAULT FALSE,
															push_digg                                bool           DEFAULT FALSE,
															push_follow                              bool           DEFAULT FALSE,
															push_friend_action                       bool           DEFAULT FALSE,
															push_ichat                               bool           DEFAULT FALSE,
															push_status                              bool           DEFAULT FALSE,
															push_video_post                          bool           DEFAULT FALSE,
															push_video_recommend                     bool           DEFAULT FALSE,
															real_time_icons                          JSON           DEFAULT NULL,
															remark_name                              varchar(50)    DEFAULT NULL,
															sec_uid                                  text           DEFAULT NULL,
															secret                                   tinyint unsigned DEFAULT 0,
															share_qrcode_uri                         text           DEFAULT NULL,
															short_id                                 varchar(50)    DEFAULT NULL,
															signature                                text           DEFAULT NULL,
															special_id                               varchar(100)   DEFAULT NULL,
															status                                   tinyint unsigned DEFAULT 0,
															telephone                                varchar(20)    DEFAULT NULL,
															ticket_count                             bigint         DEFAULT 0,
															top_fans                                 JSON           DEFAULT NULL,
															top_vip_no                               int unsigned   DEFAULT 0,
															total_recharge_diamond_count             bigint         DEFAULT 0,
															user_canceled                            bool           DEFAULT FALSE,
															user_open_id                             varchar(200)   DEFAULT NULL,
															user_role                                tinyint unsigned DEFAULT 0,
															verified                                 bool           DEFAULT FALSE,
															verified_content                         text           DEFAULT NULL,
															verified_mobile                          bool           DEFAULT FALSE,
															verified_reason                          varchar(255)   DEFAULT NULL,
															watch_duration_month                     int unsigned   DEFAULT 0,
															web_rid                                  varchar(100)   DEFAULT NULL,
															webcast_uid                              text           DEFAULT NULL,
															with_car_management_permission           bool           DEFAULT FALSE,
															with_commerce_permission                 bool           DEFAULT FALSE,
															with_fusion_shop_entry                   bool           DEFAULT FALSE,
															can_view_webcast_private                 tinyint unsigned DEFAULT 0,
															webcast_nick                             varchar(50)    DEFAULT NULL,
															webcast_private                          tinyint unsigned DEFAULT 0,
															hide_by_room                             tinyint unsigned DEFAULT 0,
															link_mask                                tinyint unsigned DEFAULT 0,

															created_at                               timestamp      DEFAULT CURRENT_TIMESTAMP,
															updated_at                               timestamp      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
															PRIMARY KEY (id)
														) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户信息表';
														'''.format(__USER_TABLE_NAME)

##
## <<=============================== user ==============================<<
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
		return self.__USER_TABLE_NAME

	##
	## get table header
	##
	def get_header(self) -> list[str]:
		return self.__USER_TABLE_HEADER

	##
	## get table tuple
	##
	def get_tuple(self) -> dict[str, None]:
		return self.__USER_TABLE_TUPLE

	##
	## get table primary key
	##
	def get_pri_key(self) -> list[str]:
		return self.__USER_TABLE_PRI_KEY

	##
	## auto increment field
	##
	def get_auto_increment_field(self) -> list[str]:
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
		return 'DROP TABLE IF EXISTS `{}`;'.format(self.__USER_TABLE_NAME)

	##
	## verify table schema
	##
	def verify_table_schema(self) -> bool:
		return super().verify_table_schema()
