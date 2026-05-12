##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Third-Part>>
from backend.src.database.social_media_stream_database                import SocialMediaStreamDataBase
from backend.src.database.table.social_media_stream_db_table          import SocialMediaStreamDataTable

##
## room_owner_v2 table - 主播信息表
##
## 优化后的核心表，包含主播详细信息和 JSON 扩展字段
## 字段数：80 独立字段 + 18 JSON 字段 = 98 字段
##
class RoomOwnerV2Table(SocialMediaStreamDataTable):
##
## >>=============================== room_owner_v2 ===============================>>
##
  __ROOM_OWNER_V2_TABLE_NAME   = 'room_owner_v2'
  __ROOM_OWNER_V2_TABLE_HEADER = [
    # 主键
    'room_id',
    # 基本信息
    'user_id',                  'owner_open_id',            'owner_device_id',          'sec_uid',
    'user_open_id',             'short_id',                 'display_id',               'nickname',
    'signature',                'share_qrcode_uri',         'special_id',               'status',
    'bg_img_url',
    # 个人信息
    'gender',                   'city',                     'constellation',            'age_range',
    'birthday',                 'birthday_description',     'birthday_valid',           'location_city',
    'foreign_user',             'mystery_man',
    # 等级
    'level',                    'exp',                      'experience',               'fan_ticket_count',
    'consume_diamond_level',    'income_share_percent',     'link_mic_stats',           'media_badge_image_list',
    'modify_time',              'pay_score',                'pay_scores',               'need_profile_guide',
    'new_real_time_icons',      'real_time_icons',
    # 关注
    'follow_status',            'is_follower',              'is_following',             'follow_info',
    # 匿名和认证
    'is_anonymous',             'hotsoon_verified',         'hotsoon_verified_reason',  'ichat_restrict_type',
    'disable_ichat',            'enable_ichat_img',         'fold_stranger_chat',       'desensitized_nickname',
    # 认证
    'verified',                 'verified_reason',          'verified_content',         'verified_mobile',
    'enterprise_verify_reason', 'custom_verify',            'block_status',             'comment_restrict',
    'public_area_oper_freq',    'push_comment_status',      'push_digg',                'push_follow',
    'push_friend_action',       'push_ichat',               'push_status',              'push_video_post',
    'push_video_recommend',     'remark_name',              'secret',                   'user_role',
    'webcast_private',          'can_view_webcast_private', 'user_canceled',            'telephone',
    # 权限
    'with_commerce_permission', 'with_fusion_shop_entry',   'with_car_management_permission', 'adversary_authorization_info',
    'adversary_user_status',    'authorization_info',       'allow_be_located',         'allow_find_by_contacts',
    'allow_others_download_video', 'allow_others_download_when_sharing_video', 'allow_share_show_profile', 'allow_show_in_gossip',
    'allow_show_my_action',     'allow_strange_comment',    'allow_unfollower_comment', 'allow_use_linkmic',
    # JSON 扩展字段
    'avatar_large',             'avatar_medium',            'avatar_thumb',             'badge_image_list',
    'badge_image_list_v2',      'commerce_webcast_config_ids', 'authentication_info',   'border_data',
    'pay_grade_data',           'fans_club_data',           'fans_group_info',          'subscribe_data',
    'user_attr_data',           'user_dress_info_data',     'biz_relation_data',        'j_accredit_info_data',
    'own_room_data',            'total_recharge_diamond_count', 'watch_duration_month', 'web_rid',
    'webcast_nick',             'webcast_uid',
    # 时间戳
    'created_at',               'updated_at'
  ]
  __ROOM_OWNER_V2_TABLE_PRI_KEY = ['room_id']
  __TABLE_AUTO_INCREMENT         = []
  __ROOM_OWNER_V2_TABLE_TUPLE   = {item:None for item in __ROOM_OWNER_V2_TABLE_HEADER}
  __SQL_CREATE_ROOM_OWNER_V2_TABLE = '''
                                      CREATE TABLE IF NOT EXISTS {} (

                                        room_id                          varchar(200)   NOT NULL,

                                        user_id                          bigint         DEFAULT NULL,
                                        owner_open_id                    varchar(200)   DEFAULT NULL,
                                        owner_device_id                  bigint         DEFAULT NULL,
                                        sec_uid                          text           DEFAULT NULL,
                                        user_open_id                     varchar(200)   DEFAULT NULL,
                                        short_id                         varchar(50)    DEFAULT NULL,
                                        display_id                       varchar(50)    DEFAULT NULL,
                                        nickname                         varchar(50)    DEFAULT NULL,
                                        signature                        text           DEFAULT NULL,
                                        share_qrcode_uri                 text           DEFAULT NULL,
                                        special_id                       varchar(100)   DEFAULT NULL,
                                        status                           tinyint        DEFAULT 0,
                                        bg_img_url                       text           DEFAULT NULL,

                                        gender                           tinyint        DEFAULT 0,
                                        city                             varchar(100)   DEFAULT NULL,
                                        constellation                    varchar(20)    DEFAULT NULL,
                                        age_range                        tinyint        DEFAULT 0,
                                        birthday                         bigint         DEFAULT 0,
                                        birthday_description             varchar(100)   DEFAULT NULL,
                                        birthday_valid                   bool           DEFAULT FALSE,
                                        location_city                    varchar(100)   DEFAULT NULL,
                                        foreign_user                     tinyint        DEFAULT 0,
                                        mystery_man                      tinyint        DEFAULT 0,

                                        level                            smallint       DEFAULT 0,
                                        exp                              bigint         DEFAULT 0,
                                        experience                       bigint         DEFAULT 0,
                                        fan_ticket_count                 bigint         DEFAULT 0,
                                        consume_diamond_level            tinyint        DEFAULT 0,
                                        income_share_percent             tinyint        DEFAULT 0,
                                        link_mic_stats                   tinyint        DEFAULT 0,
                                        media_badge_image_list           JSON           DEFAULT NULL,
                                        modify_time                      bigint         DEFAULT 0,
                                        pay_score                        bigint         DEFAULT 0,
                                        pay_scores                       bigint         DEFAULT 0,
                                        need_profile_guide               bool           DEFAULT FALSE,
                                        new_real_time_icons              JSON           DEFAULT NULL,
                                        real_time_icons                  JSON           DEFAULT NULL,

                                        follow_status                    tinyint        DEFAULT 0,
                                        is_follower                      bool           DEFAULT FALSE,
                                        is_following                     bool           DEFAULT FALSE,
                                        follow_info                      JSON           DEFAULT NULL,

                                        is_anonymous                     bool           DEFAULT FALSE,
                                        hotsoon_verified                 bool           DEFAULT FALSE,
                                        hotsoon_verified_reason          varchar(255)   DEFAULT NULL,
                                        ichat_restrict_type              tinyint        DEFAULT 0,
                                        disable_ichat                    tinyint        DEFAULT 0,
                                        enable_ichat_img                 tinyint        DEFAULT 0,
                                        fold_stranger_chat               bool           DEFAULT FALSE,
                                        desensitized_nickname            varchar(50)    DEFAULT NULL,

                                        verified                         bool           DEFAULT FALSE,
                                        verified_reason                  varchar(255)   DEFAULT NULL,
                                        verified_content                 text           DEFAULT NULL,
                                        verified_mobile                  bool           DEFAULT FALSE,
                                        enterprise_verify_reason         varchar(255)   DEFAULT NULL,
                                        custom_verify                    varchar(100)   DEFAULT NULL,
                                        block_status                     tinyint        DEFAULT 0,
                                        comment_restrict                 tinyint        DEFAULT 0,
                                        public_area_oper_freq            tinyint        DEFAULT 0,
                                        push_comment_status              bool           DEFAULT FALSE,
                                        push_digg                        bool           DEFAULT FALSE,
                                        push_follow                      bool           DEFAULT FALSE,
                                        push_friend_action               bool           DEFAULT FALSE,
                                        push_ichat                       bool           DEFAULT FALSE,
                                        push_status                      bool           DEFAULT FALSE,
                                        push_video_post                  bool           DEFAULT FALSE,
                                        push_video_recommend             bool           DEFAULT FALSE,
                                        secret                           tinyint        DEFAULT 0,
                                        user_role                        tinyint        DEFAULT 0,
                                        webcast_private                  tinyint        DEFAULT 0,
                                        can_view_webcast_private         tinyint        DEFAULT 0,
                                        user_canceled                    bool           DEFAULT FALSE,
                                        telephone                        varchar(20)    DEFAULT NULL,

                                        with_commerce_permission         bool           DEFAULT FALSE,
                                        with_fusion_shop_entry           bool           DEFAULT FALSE,
                                        with_car_management_permission   bool           DEFAULT FALSE,
                                        adversary_authorization_info     tinyint        DEFAULT 0,
                                        adversary_user_status            tinyint        DEFAULT 0,
                                        authorization_info               tinyint        DEFAULT 0,
                                        allow_be_located                 bool           DEFAULT FALSE,
                                        allow_find_by_contacts           bool           DEFAULT FALSE,
                                        allow_others_download_video      bool           DEFAULT FALSE,
                                        allow_others_download_when_sharing_video bool   DEFAULT FALSE,
                                        allow_share_show_profile         bool           DEFAULT FALSE,
                                        allow_show_in_gossip             bool           DEFAULT FALSE,
                                        allow_show_my_action             bool           DEFAULT FALSE,
                                        allow_strange_comment            bool           DEFAULT FALSE,
                                        allow_unfollower_comment         bool           DEFAULT FALSE,
                                        allow_use_linkmic                bool           DEFAULT FALSE,
                                        remark_name                      varchar(50)    DEFAULT NULL,

                                        avatar_large                     JSON           DEFAULT NULL,
                                        avatar_medium                    JSON           DEFAULT NULL,
                                        avatar_thumb                     JSON           DEFAULT NULL,
                                        badge_image_list                 JSON           DEFAULT NULL,
                                        badge_image_list_v2              JSON           DEFAULT NULL,
                                        commerce_webcast_config_ids      JSON           DEFAULT NULL,
                                        authentication_info              JSON           DEFAULT NULL,
                                        border_data                      JSON           DEFAULT NULL,
                                        pay_grade_data                   JSON           DEFAULT NULL,
                                        fans_club_data                   JSON           DEFAULT NULL,
                                        fans_group_info                  JSON           DEFAULT NULL,
                                        subscribe_data                   JSON           DEFAULT NULL,
                                        user_attr_data                   JSON           DEFAULT NULL,
                                        user_dress_info_data             JSON           DEFAULT NULL,
                                        biz_relation_data                JSON           DEFAULT NULL,
                                        j_accredit_info_data             JSON           DEFAULT NULL,
                                        own_room_data                    JSON           DEFAULT NULL,
                                        total_recharge_diamond_count     bigint         DEFAULT 0,
                                        watch_duration_month             int            DEFAULT 0,
                                        web_rid                          varchar(100)   DEFAULT NULL,
                                        webcast_nick                     varchar(50)    DEFAULT NULL,
                                        webcast_uid                      text           DEFAULT NULL,

                                        created_at                       timestamp      DEFAULT CURRENT_TIMESTAMP,
                                        updated_at                       timestamp      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                                        PRIMARY KEY (room_id),
                                        INDEX idx_user_id (user_id),
                                        INDEX idx_nickname (nickname)
                                      ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                                      '''.format(__ROOM_OWNER_V2_TABLE_NAME)
##
## <<=============================== room_owner_v2 ==============================<<
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
    return self.__ROOM_OWNER_V2_TABLE_NAME

  def get_header(self) -> list:
    return self.__ROOM_OWNER_V2_TABLE_HEADER

  def get_tuple(self) -> dict:
    return self.__ROOM_OWNER_V2_TABLE_TUPLE

  def get_pri_key(self) -> list:
    return self.__ROOM_OWNER_V2_TABLE_PRI_KEY

  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_OWNER_V2_TABLE

  def get_drop_sql_cmd(self) -> str:
    return 'DROP TABLE IF EXISTS {};'.format(self.__ROOM_OWNER_V2_TABLE_NAME)

  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()
