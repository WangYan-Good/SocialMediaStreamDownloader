##
## export.py
## This module handles the export of data from the Social Media Stream Downloader (SMSD) application.
## It provides functionality to export a record of living data to yml files.
##

##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from pathlib                                                          import   Path
from datetime                                                         import   datetime as dat
from math                                                             import   floor
import                                                                         json

## <<Extension>>

## <<Third-Part>>
from backend.src.library.baselib                                      import   load_yml, get_dict_attr, set_dict_attr, output_dict, save_dict_as_file
from backend.src.base.log                                             import   get_logger
from backend.src.database.social_media_stream_database                import   SocialMediaStreamDataBase
from backend.src.database.table.live                                  import   LiveRecordTable
from backend.src.database.table.room                                  import   RoomAttributeTable,                                  \
                                                                               RoomAdminUserIdTable,                                \
                                                                               RoomAdminUserOpenIdTable,                            \
                                                                               RoomAssistLabelTable,                                \
                                                                               RoomDecoTable,                                       \
                                                                               RoomDecoInputRectTable,                              \
                                                                               RoomDecoReservationTable,                            \
                                                                               RoomRealtimePlaybackQualityTable,                    \
                                                                               FansGroupAdminUserIdTable,                           \
                                                                               FansGroupAdminUserOpenIdTable,                       \
                                                                               RoomFilterWordTable,                                 \
                                                                               RoomLiveDistributionTable,                           \
                                                                               CommerceWebcastConfigIdTable,                        \
                                                                               MediaBadgeImageTable,                                \
                                                                               NewRealTimeIconTable,                                \
                                                                               RoomOwnerRealTimeIconTable,                          \
                                                                               RoomSubscribeTable,                                  \
                                                                               RoomOwnerTopFansTable,                               \
                                                                               RoomPackMetaTable,                                   \
                                                                               RoomPaidLiveDataTable,                               \
                                                                               RoomAuthTable,                                       \
                                                                               RoomTabTable,                                        \
                                                                               RoomShortTouchAreaConfigTable,                       \
                                                                               RoomShortTouchAreaConfigElementTable,                \
                                                                               RoomShortTouchAreaConfigStrategyFeatWhitelistTable,  \
                                                                               RoomTempStateConditionMapTable,                      \
                                                                               RoomTempStateGlobalConditionIgnoreStrategyTypeTable, \
                                                                               RoomTempStateGlobalConditionTable,                   \
                                                                               RoomRecordTable,                                     \
                                                                               RoomTagTable,                                        \
                                                                               RoomTempStateStrategyTable,                          \
                                                                               RoomTempStateStrategyMapTable,                       \
                                                                               RoomTopFansTable,                                    \
                                                                               RoomUpperRightWidgetDataTable,                       \
                                                                               RoomVsRoleTable
from backend.src.database.table.source                                import   BadgeImageTable,                                     \
                                                                               PayGradeIconTable,                                   \
                                                                               RoomOwnerUserDressOwnIdTable,                        \
                                                                               RoomOwnerDressWearIdTable,                           \
                                                                               RoomSharingMusicIdTable,                             \
                                                                               PictureTable,                                        \
                                                                               PictureFlexSettingTable,                             \
                                                                               PictureTextSettingTable,                             \
                                                                               PictureUrlTable,                                     \
                                                                               PictureContentTable,                                 \
                                                                               RoomDecoTextFootConfigTable
from backend.src.database.table.stream                                import   LiveStreamTable,                                     \
                                                                               StreamCandidateResolutionTable,                      \
                                                                               StreamCompletePushUrlTable,                          \
                                                                               LiveCoreSdkDataTable,                                \
                                                                               LiveCoreSdkPullDataTable,                            \
                                                                               LiveCoreSdkPullFlvDataTable,                         \
                                                                               LiveCoreSdkPullHlsDataTable,                         \
                                                                               LiveCoreSdkPullDataOptionTable,                      \
                                                                               LiveCoreSdkPullQualityDataTable,                     \
                                                                               LiveCoreSdkPullDefaultQualityDataTable,              \
                                                                               StreamPushUrlTable,                                  \
                                                                               RoomLinkMicTable,                                    \
                                                                               RoomLinkMicBattleScoreTable,                         \
                                                                               RoomLinkMicBattleSettingTable,                       \
                                                                               RoomLinkMicChannelInfoTable
from backend.src.database.table.user                                  import   RoomOwnerTable,                                      \
                                                                               OwnRoomFlagTable,                                    \
                                                                               OwnRoomIdTable,                                      \
                                                                               FansClubTable,                                       \
                                                                               FansClubAvailableGiftIdTable,                        \
                                                                               FansClubBadgeIconTable,                              \
                                                                               RoomOwnerUserAttrTable,                              \
                                                                               RoomAdminPrivilegeTable,                             \
                                                                               RoomOwnerAuthInfoTable,                              \
                                                                               RoomOwnerAuthLevelTable,                             \
                                                                               UserTable,                                           \
                                                                               RoomOwnerAuthorStatsTable
##
## initialize the layout of exported data
##
def initialize_export_data() -> dict:
  
  """
    data
  """
  data = dict()
  
  """
    data.room
  """
  room = dict()
  set_dict_attr(room,        "$.AnchorABMap",                        {},           force=True)
  set_dict_attr(room,        "$.acquaintance_status",                0,            force=True)
  set_dict_attr(room,        "$.admin_user_ids",                     [],           force=True)
  set_dict_attr(room,        "$.admin_user_open_ids",                [],           force=True)
  set_dict_attr(room,        "$.anchor_scheduled_time_text",         "",           force=True)
  set_dict_attr(room,        "$.anchor_share_text",                  "",           force=True)
  set_dict_attr(room,        "$.anchor_tab_type",                    0,            force=True)
  set_dict_attr(room,        "$.app_id",                             0,            force=True)
  set_dict_attr(room,        "$.assist_label_list",                  [],           force=True)
  set_dict_attr(room,        "$.auth_city",                          "",           force=True)
  set_dict_attr(room,        "$.auto_cover",                         0,            force=True)
  set_dict_attr(room,        "$.base_category",                      0,            force=True)
  set_dict_attr(room,        "$.book_end_time",                      0,            force=True)
  set_dict_attr(room,        "$.book_time",                          0,            force=True)
  set_dict_attr(room,        "$.business_live",                      0,            force=True)
  set_dict_attr(room,        "$.category",                           0,            force=True)
  set_dict_attr(room,        "$.cell_style",                         0,            force=True)
  set_dict_attr(room,        "$.challenge_info",                     "",           force=True)
  set_dict_attr(room,        "$.city_top_distance",                  "",           force=True)
  set_dict_attr(room,        "$.client_version",                     0,            force=True)
  
  """
    data.room.comment_box
  """
  comment_box = dict()
  set_dict_attr(comment_box, "$.placeholder",                        "",           force=True)
  set_dict_attr(room,        "$.comment_box",                        comment_box,  force=True)
  
  set_dict_attr(room,        "$.comment_name_mode",                  0,            force=True)
  set_dict_attr(room,        "$.common_label_list",                  "",           force=True)
  set_dict_attr(room,        "$.content_tag",                        "",           force=True)
  
  """
    data.room.cover
  """
  cover = dict()
  set_dict_attr(cover,       "$.avg_color",                          "",           force=True)
  set_dict_attr(cover,       "$.flex_setting_list",                  [],           force=True)
  set_dict_attr(cover,       "$.height",                             0,            force=True)
  set_dict_attr(cover,       "$.image_type",                         0,            force=True)
  set_dict_attr(cover,       "$.is_animated",                        False,        force=True)
  set_dict_attr(cover,       "$.open_web_url",                       "",           force=True)
  set_dict_attr(cover,       "$.text_setting_list",                  [],           force=True)
  set_dict_attr(cover,       "$.uri",                                "",           force=True)
  set_dict_attr(cover,       "$.url_list",                           [],           force=True)
  set_dict_attr(cover,       "$.width",                              0,            force=True)
  set_dict_attr(room,        "$.cover",                              cover,        force=True)
  
  set_dict_attr(room,        "$.create_time",                        0,            force=True)
  set_dict_attr(room,        "$.danmaku_detail",                     0,            force=True)
  set_dict_attr(room,        "$.deco_list",                          [],           force=True)
  set_dict_attr(room,        "$.distance",                           "",           force=True)
  set_dict_attr(room,        "$.distance_city",                      "",           force=True)
  set_dict_attr(room,        "$.distance_km",                        "",           force=True)
  set_dict_attr(room,        "$.dynamic_cover_dict",                 {},           force=True)
  set_dict_attr(room,        "$.dynamic_cover_uri",                  "",           force=True)
  set_dict_attr(room,        "$.enable_room_perspective",            False,        force=True)
  
  """
    data.room.extra
  """
  extra = {}
  set_dict_attr(extra,       "$.create_scene",                       "",           force=True)
  set_dict_attr(extra,       "$.facial_unrecognised",                0,            force=True)
  set_dict_attr(extra,       "$.geo_block",                          0,            force=True)
  set_dict_attr(extra,       "$.is_sandbox",                         False,        force=True)
  set_dict_attr(extra,       "$.is_virtual_anchor",                  False,        force=True)
  set_dict_attr(extra,       "$.limit_appid",                        "",           force=True)
  set_dict_attr(extra,       "$.limit_strategy",                     0,            force=True)
  set_dict_attr(extra,       "$.realtime_playback_qualities",        [],           force=True)
  set_dict_attr(extra,       "$.realtime_playback_shift",            0,            force=True)
  set_dict_attr(extra,       "$.realtime_playback_start_shift",      0,            force=True)
  set_dict_attr(extra,       "$.realtime_replay_enabled",            False,        force=True)
  set_dict_attr(extra,       "$.vr_type",                            0,            force=True)
  set_dict_attr(extra,       "$.vs_type",                            0,            force=True)
  set_dict_attr(extra,       "$.xigua_uid",                          0,            force=True)
  set_dict_attr(room,        "$.extra",                              extra,        force=True)
  
  set_dict_attr(room,        "$.fans_group_admin_user_ids",          [],           force=True)
  set_dict_attr(room,        "$.fans_group_admin_user_open_ids",     [],           force=True)
  set_dict_attr(room,        "$.fansclub_msg_style",                 0,            force=True)
  set_dict_attr(room,        "$.fcdn_appid",                         0,            force=True)
  
  """
    data.room.feed_room_label
  """
  feed_room_label = dict()
  set_dict_attr(feed_room_label, "$.avg_color",                      "",           force=True)
  
  """
    data.room.content
  """
  content = dict()
  set_dict_attr(content,         "$.alternative_text",               "",           force=True)
  set_dict_attr(content,         "$.font_color",                     "",           force=True)
  set_dict_attr(content,         "$.level",                          0,            force=True)
  set_dict_attr(content,         "$.name",                           "",           force=True)
  set_dict_attr(feed_room_label, "$.content",                        content,      force=True)
  
  set_dict_attr(feed_room_label, "$.flex_setting_list",              [],               force=True)
  set_dict_attr(feed_room_label, "$.height",                         0,                force=True)
  set_dict_attr(feed_room_label, "$.image_type",                     0,                force=True)
  set_dict_attr(feed_room_label, "$.is_animated",                    False,            force=True)
  set_dict_attr(feed_room_label, "$.open_web_url",                   "",               force=True)
  set_dict_attr(feed_room_label, "$.text_setting_list",              [],               force=True)
  set_dict_attr(feed_room_label, "$.uri",                            "",               force=True)
  set_dict_attr(feed_room_label, "$.url_list",                       [],               force=True)
  set_dict_attr(feed_room_label, "$.width",                          0,                force=True)
  set_dict_attr(room,            "$.feed_room_label",                feed_room_label,  force=True)
  
  set_dict_attr(room,            "$.filter_words",                   [],               force=True)
  set_dict_attr(room,            "$.finish_reason",                  0,                force=True)
  set_dict_attr(room,            "$.finish_time",                    0,                force=True)
  set_dict_attr(room,            "$.finish_url",                     "",               force=True)
  set_dict_attr(room,            "$.follow_msg_style",               0,                force=True)
  set_dict_attr(room,            "$.forum_extra_data",               "",               force=True)
  set_dict_attr(room,            "$.game_room_type",                 0,                force=True)
  set_dict_attr(room,            "$.gift_msg_style",                 0,                force=True)
  set_dict_attr(room,            "$.group_id",                       0,                force=True)
  set_dict_attr(room,            "$.group_source",                   0,                force=True)
  
  """
    data.room.guide_button
  """
  guide_button = dict()
  set_dict_attr(guide_button,    "$.avg_color",                      "",               force=True)
  set_dict_attr(guide_button,    "$.flex_setting_list",              [],               force=True)
  set_dict_attr(guide_button,    "$.height",                         0,                force=True)
  set_dict_attr(guide_button,    "$.image_type",                     0,                force=True)
  set_dict_attr(guide_button,    "$.is_animated",                    False,            force=True)
  set_dict_attr(guide_button,    "$.open_web_url",                   "",               force=True)
  set_dict_attr(guide_button,    "$.text_setting_list",              [],               force=True)
  set_dict_attr(guide_button,    "$.uri",                            "",               force=True)
  set_dict_attr(guide_button,    "$.url_list",                       [],               force=True)
  set_dict_attr(guide_button,    "$.width",                          0,                force=True)
  set_dict_attr(room,            "$.guide_button",                   guide_button,     force=True)
  
  set_dict_attr(room,            "$.has_commerce_goods",             False,            force=True)
  set_dict_attr(room,            "$.has_promotion_games",            0,                force=True)
  set_dict_attr(room,            "$.highlight",                      False,            force=True)
  set_dict_attr(room,            "$.hot_sentence_info",              "",               force=True)
  set_dict_attr(room,            "$.id",                             0,                force=True)
  set_dict_attr(room,            "$.id_str",                         "",               force=True)
  set_dict_attr(room,            "$.introduction",                   "",               force=True)
  set_dict_attr(room,            "$.is_need_check_list",             False,            force=True)
  set_dict_attr(room,            "$.is_official_channel_room",       False,            force=True)
  set_dict_attr(room,            "$.is_replay",                      False,            force=True)
  set_dict_attr(room,            "$.is_show_inquiry_ball",           False,            force=True)
  set_dict_attr(room,            "$.is_show_user_card_switch",       False,            force=True)
  set_dict_attr(room,            "$.item_explicit_info",             "",               force=True)
  set_dict_attr(room,            "$.last_ping_time",                 0,                force=True)
  set_dict_attr(room,            "$.layout",                         0,                force=True)
  set_dict_attr(room,            "$.like_count",                     0,                force=True)
  set_dict_attr(room,            "$.linker_map",                     {},               force=True)
  set_dict_attr(room,            "$.linkmic_display_type",           0,                force=True)
  set_dict_attr(room,            "$.linkmic_layout",                 0,                force=True)
  set_dict_attr(room,            "$.live_distribution",              [],               force=True)
  set_dict_attr(room,            "$.live_id",                        0,                force=True)
  set_dict_attr(room,            "$.live_platform_source",           "",               force=True)
  set_dict_attr(room,            "$.live_room_mode",                 0,                force=True)
  set_dict_attr(room,            "$.live_type_audio",                False,            force=True)
  set_dict_attr(room,            "$.live_type_linkmic",              False,            force=True)
  set_dict_attr(room,            "$.live_type_normal",               False,            force=True)
  set_dict_attr(room,            "$.live_type_official",             False,            force=True)
  set_dict_attr(room,            "$.live_type_sandbox",              False,            force=True)
  set_dict_attr(room,            "$.live_type_screenshot",           False,            force=True)
  set_dict_attr(room,            "$.live_type_third_party",          False,            force=True)
  set_dict_attr(room,            "$.live_type_vs_live",              False,            force=True)
  set_dict_attr(room,            "$.live_type_vs_premiere",          False,            force=True)
  
  """
    data.room.living_room_attrs
  """
  living_room_attrs = dict()
  set_dict_attr(living_room_attrs, "$.admin_flag",                   0,                 force=True)
  set_dict_attr(living_room_attrs, "$.rank",                         0,                 force=True)
  set_dict_attr(living_room_attrs, "$.room_id",                      0,                 force=True)
  set_dict_attr(living_room_attrs, "$.room_id_str",                  "",                force=True)
  set_dict_attr(living_room_attrs, "$.silence_flag",                 0,                 force=True)
  set_dict_attr(room,              "$.living_room_attrs",            living_room_attrs, force=True)
  
  set_dict_attr(room,              "$.location",                     "",                force=True)
  set_dict_attr(room,              "$.lottery_finish_time",          0,                 force=True)
  set_dict_attr(room,              "$.luckymoney_num",               0,                 force=True)
  set_dict_attr(room,              "$.mosaic_status",                0,                 force=True)
  set_dict_attr(room,              "$.mosaic_tip",                   "",                force=True)
  set_dict_attr(room,              "$.official_channel_open_id",     "",                force=True)
  set_dict_attr(room,              "$.official_channel_uid",         0,                 force=True)
  set_dict_attr(room,              "$.orientation",                  0,                 force=True)
  set_dict_attr(room,              "$.os_type",                      0,                 force=True)
  
  
  """
    data.room.owner
  """
  owner = dict()
  set_dict_attr(owner,        "$.adversary_authorization_info",             0,                    force=True)
  set_dict_attr(owner,        "$.adversary_user_status",                    0,                    force=True)
  set_dict_attr(owner,        "$.age_range",                                0,                    force=True)
  set_dict_attr(owner,        "$.allow_be_located",                         False,                force=True)
  set_dict_attr(owner,        "$.allow_find_by_contacts",                   False,                force=True)
  set_dict_attr(owner,        "$.allow_others_download_video",              False,                force=True)
  set_dict_attr(owner,        "$.allow_others_download_when_sharing_video", False,                force=True)
  set_dict_attr(owner,        "$.allow_share_show_profile",                 False,                force=True)
  set_dict_attr(owner,        "$.allow_show_in_gossip",                     False,                force=True)
  set_dict_attr(owner,        "$.allow_show_my_action",                     False,                force=True)
  set_dict_attr(owner,        "$.allow_strange_comment",                    False,                force=True)
  set_dict_attr(owner,        "$.allow_unfollower_comment",                 False,                force=True)
  set_dict_attr(owner,        "$.allow_use_linkmic",                        False,                force=True)
  set_dict_attr(owner,        "$.authorization_info",                       0,                    force=True)

  """
    data.room.owner.avatar_large
  """
  avatar_large = dict()
  set_dict_attr(avatar_large, "$.avg_color",                                '',                   force=True)
  set_dict_attr(avatar_large, "$.flex_setting_list",                        [],                   force=True)
  set_dict_attr(avatar_large, "$.height",                                   0,                    force=True)
  set_dict_attr(avatar_large, "$.image_type",                               0,                    force=True)
  set_dict_attr(avatar_large, "$.is_animated",                              False,                force=True)
  set_dict_attr(avatar_large, "$.open_web_url",                             '',                   force=True)
  set_dict_attr(avatar_large, "$.text_setting_list",                        [],                   force=True)
  set_dict_attr(avatar_large, "$.uri",                                      '',                   force=True)
  set_dict_attr(avatar_large, "$.url_list",                                 [],                   force=True)
  set_dict_attr(avatar_large, "$.width",                                    0,                    force=True)
  set_dict_attr(owner,        "$.avatar_large",                             avatar_large,         force=True)

  """
    data.room.owner.avatar_medium
  """
  avatar_medium = dict()
  set_dict_attr(avatar_medium, "$.avg_color",                               '',                   force=True)
  set_dict_attr(avatar_medium, "$.flex_setting_list",                       [],                   force=True)
  set_dict_attr(avatar_medium, "$.height",                                  0,                    force=True)
  set_dict_attr(avatar_medium, "$.image_type",                              0,                    force=True)
  set_dict_attr(avatar_medium, "$.is_animated",                             False,                force=True)
  set_dict_attr(avatar_medium, "$.open_web_url",                            '',                   force=True)
  set_dict_attr(avatar_medium, "$.text_setting_list",                       [],                   force=True)
  set_dict_attr(avatar_medium, "$.uri",                                     '',                   force=True)
  set_dict_attr(avatar_medium, "$.url_list",                                [],                   force=True)
  set_dict_attr(avatar_medium, "$.width",                                   0,                    force=True)
  set_dict_attr(owner,         "$.avatar_medium",                           avatar_medium,        force=True)
  
  """
    data.room.owner.avatar_thumb
  """
  avatar_thumb = dict()
  set_dict_attr(avatar_thumb, "$.avg_color",                                '',                   force=True)
  set_dict_attr(avatar_thumb, "$.flex_setting_list",                        [],                   force=True)
  set_dict_attr(avatar_thumb, "$.height",                                   0,                    force=True)
  set_dict_attr(avatar_thumb, "$.image_type",                               0,                    force=True)
  set_dict_attr(avatar_thumb, "$.is_animated",                              False,                force=True)
  set_dict_attr(avatar_thumb, "$.open_web_url",                             '',                   force=True)
  set_dict_attr(avatar_thumb, "$.text_setting_list",                        [],                   force=True)
  set_dict_attr(avatar_thumb, "$.uri",                                      '',                   force=True)
  set_dict_attr(avatar_thumb, "$.url_list",                                 [],                   force=True)
  set_dict_attr(avatar_thumb, "$.width",                                    0,                    force=True)
  set_dict_attr(owner,        "$.avatar_thumb",                             avatar_thumb,         force=True)

  set_dict_attr(owner,        "$.badge_image_list",                         [],                   force=True)
  set_dict_attr(owner,        "$.badge_image_list_v2",                      [],                   force=True)
  set_dict_attr(owner,        "$.bg_img_url",                               '',                   force=True)
  set_dict_attr(owner,        "$.birthday",                                 0,                    force=True)
  set_dict_attr(owner,        "$.birthday_description",                     '',                   force=True)
  set_dict_attr(owner,        "$.birthday_valid",                           False,                force=True)
  set_dict_attr(owner,        "$.block_status",                             0,                    force=True)
  set_dict_attr(owner,        "$.city",                                     '',                   force=True)
  set_dict_attr(owner,        "$.comment_restrict",                         0,                    force=True)
  set_dict_attr(owner,        "$.constellation",                            '',                   force=True)
  set_dict_attr(owner,        "$.consume_diamond_level",                    0,                    force=True)
  set_dict_attr(owner,        "$.create_time",                              0,                    force=True)
  set_dict_attr(owner,        "$.desensitized_nickname",                    '',                   force=True)
  set_dict_attr(owner,        "$.disable_ichat",                            0,                    force=True)
  set_dict_attr(owner,        "$.display_id",                               '',                   force=True)
  set_dict_attr(owner,        "$.enable_ichat_img",                         0,                    force=True)
  set_dict_attr(owner,        "$.exp",                                      0,                    force=True)
  set_dict_attr(owner,        "$.experience",                               0,                    force=True)
  set_dict_attr(owner,        "$.fan_ticket_count",                         0,                    force=True)
  
  """
  data.room.owner.fans_club
  """
  set_dict_attr(owner,        "$.fans_club",                                {},                   force=True)
  
  """
  data.room.owner.fans_group_info
  """
  set_dict_attr(owner,        "$.fans_group_info",                          {},                   force=True)
  set_dict_attr(owner,        "$.fold_stranger_chat",                       False,                force=True)
  
  """
  data.room.owner.follow_info
  """
  follow_info = dict()
  set_dict_attr(follow_info, "$.follow_status",                              0,                   force=True)
  set_dict_attr(follow_info, "$.follower_count",                             0,                   force=True)
  set_dict_attr(follow_info, "$.follower_count_str",                         '',                  force=True)
  set_dict_attr(follow_info, "$.following_count",                            0,                   force=True)
  set_dict_attr(follow_info, "$.following_count_str",                        '',                  force=True)
  set_dict_attr(follow_info, "$.invalid_follow_status",                      False,               force=True)
  set_dict_attr(follow_info, "$.push_status",                                0,                   force=True)
  set_dict_attr(follow_info, "$.remark_name",                                '',                  force=True)
  set_dict_attr(owner,       "$.follow_info",                                follow_info,         force=True)

  set_dict_attr(owner,       "$.follow_status",                              0,                   force=True)
  set_dict_attr(owner,       "$.gender",                                     0,                   force=True)
  set_dict_attr(owner,       "$.hotsoon_verified",                           False,               force=True)
  set_dict_attr(owner,       "$.hotsoon_verified_reason",                    '',                  force=True)
  set_dict_attr(owner,       "$.ichat_restrict_type",                        0,                   force=True)
  set_dict_attr(owner,       "$.id",                                         '',                  force=True)
  set_dict_attr(owner,       "$.id_str",                                     '',                  force=True)
  set_dict_attr(owner,       "$.income_share_percent",                       0,                   force=True)
  set_dict_attr(owner,       "$.is_anonymous",                               False,               force=True)
  set_dict_attr(owner,       "$.is_follower",                                False,               force=True)
  set_dict_attr(owner,       "$.is_following",                               False,               force=True)

  """
  data.room.owner.j_accredit_info
  """
  j_accredit_info = dict()
  set_dict_attr(j_accredit_info, "$.JAccreditAdvance",                       0,                   force=True)
  set_dict_attr(j_accredit_info, "$.JAccreditBasic",                         0,                   force=True)
  set_dict_attr(j_accredit_info, "$.JAccreditContent",                       0,                   force=True)
  set_dict_attr(j_accredit_info, "$.JAccreditLive",                          0,                   force=True)
  set_dict_attr(owner,           "$.j_accredit_info",                        j_accredit_info,     force=True)

  set_dict_attr(owner,           "$.level",                                  0,                   force=True)
  set_dict_attr(owner,           "$.link_mic_stats",                         0,                   force=True)
  set_dict_attr(owner,           "$.location_city",                          '',                  force=True)
  set_dict_attr(owner,           "$.modify_time",                            0,                   force=True)
  set_dict_attr(owner,           "$.mystery_man",                            0,                   force=True)
  set_dict_attr(owner,           "$.need_profile_guide",                     False,               force=True)
  set_dict_attr(owner,           "$.nickname",                               '',                  force=True)

  """
  data.room.owner.pay_grade
  """
  pay_grade = dict()
  set_dict_attr(pay_grade,       "$.grade_banner",                           '',                  force=True)
  set_dict_attr(pay_grade,       "$.grade_describe",                         '',                  force=True)
  set_dict_attr(pay_grade,       "$.grade_describe_shining",                 False,               force=True)
  set_dict_attr(pay_grade,       "$.grade_icon_list",                        [],                  force=True)
  set_dict_attr(pay_grade,       "$.level",                                  0,                   force=True)
  set_dict_attr(pay_grade,       "$.name",                                   '',                  force=True)
  
  """
    data.room.owner.pay_grade.new_im_icon_with_level
  """
  new_im_icon_with_level = dict()
  set_dict_attr(new_im_icon_with_level,       "$.avg_color",                              '',                  force=True)
  set_dict_attr(new_im_icon_with_level,       "$.flex_setting_list",                      [],                  force=True)
  set_dict_attr(new_im_icon_with_level,       "$.height",                                 0,                   force=True)
  set_dict_attr(new_im_icon_with_level,       "$.image_type",                             0,                   force=True)
  set_dict_attr(new_im_icon_with_level,       "$.is_animated",                            False,               force=True)
  set_dict_attr(new_im_icon_with_level,       "$.open_web_url",                           '',                  force=True)
  set_dict_attr(new_im_icon_with_level,       "$.text_setting_list",                      [],                  force=True)
  set_dict_attr(new_im_icon_with_level,       "$.uri",                                    '',                  force=True)
  set_dict_attr(new_im_icon_with_level,       "$.url_list",                               [],                  force=True)
  set_dict_attr(new_im_icon_with_level,       "$.width",                                  0,                   force=True)
  set_dict_attr(pay_grade,                    "$.new_im_icon_with_level",       new_im_icon_with_level,        force=True)

  """
    data.room.owner.pay_grade.new_live_icon
  """
  new_live_icon = dict()
  set_dict_attr(new_live_icon,                "$.avg_color",                              '',                  force=True)
  set_dict_attr(new_live_icon,                "$.flex_setting_list",                      [],                  force=True)
  set_dict_attr(new_live_icon,                "$.height",                                 0,                   force=True)
  set_dict_attr(new_live_icon,                "$.image_type",                             0,                   force=True)
  set_dict_attr(new_live_icon,                "$.is_animated",                            False,               force=True)
  set_dict_attr(new_live_icon,                "$.open_web_url",                           '',                  force=True)
  set_dict_attr(new_live_icon,                "$.text_setting_list",                      [],                  force=True)
  set_dict_attr(new_live_icon,                "$.uri",                                    '',                  force=True)
  set_dict_attr(new_live_icon,                "$.url_list",                               [],                  force=True)
  set_dict_attr(new_live_icon,                "$.width",                                  0,                   force=True)
  set_dict_attr(pay_grade,                    "$.new_live_icon",                          new_live_icon,       force=True)

  set_dict_attr(pay_grade,                    "$.next_diamond",                           0,                   force=True)
  set_dict_attr(pay_grade,                    "$.next_name",                              '',                  force=True)
  set_dict_attr(pay_grade,                    "$.next_privileges",                        '',                  force=True)
  set_dict_attr(pay_grade,                    "$.now_diamond",                            0,                   force=True)
  set_dict_attr(pay_grade,                    "$.pay_diamond_bak",                        0,                   force=True)
  set_dict_attr(pay_grade,                    "$.score",                                  0,                   force=True)
  set_dict_attr(pay_grade,                    "$.screen_chat_type",                       0,                   force=True)
  set_dict_attr(pay_grade,                    "$.this_grade_max_diamond",                 0,                   force=True)
  set_dict_attr(pay_grade,                    "$.this_grade_min_diamond",                 0,                   force=True)
  set_dict_attr(pay_grade,                    "$.total_diamond_count",                    0,                   force=True)
  set_dict_attr(pay_grade,                    "$.upgrade_need_consume",                   0,                   force=True)
  set_dict_attr(owner,                        "$.pay_grade",                              pay_grade,           force=True)

  set_dict_attr(owner,                        "$.pay_score",                              0,                   force=True)
  set_dict_attr(owner,                        "$.pay_scores",                             0,                   force=True)
  set_dict_attr(owner,                        "$.public_area_oper_freq",                  0,                   force=True)
  set_dict_attr(owner,                        "$.push_comment_status",                    False,               force=True)
  set_dict_attr(owner,                        "$.push_digg",                              False,               force=True)
  set_dict_attr(owner,                        "$.push_follow",                            False,               force=True)
  set_dict_attr(owner,                        "$.push_friend_action",                     False,               force=True)
  set_dict_attr(owner,                        "$.push_ichat",                             False,               force=True)
  set_dict_attr(owner,                        "$.push_status",                            False,               force=True)
  set_dict_attr(owner,                        "$.push_video_post",                        False,               force=True)
  set_dict_attr(owner,                        "$.push_video_recommend",                   False,               force=True)
  set_dict_attr(owner,                        "$.remark_name",                            '',                  force=True)
  set_dict_attr(owner,                        "$.sec_uid",                                '',                  force=True)
  set_dict_attr(owner,                        "$.secret",                                 0,                   force=True)
  set_dict_attr(owner,                        "$.share_qrcode_uri",                       '',                  force=True)
  set_dict_attr(owner,                        "$.short_id",                               '',                  force=True)
  set_dict_attr(owner,                        "$.signature",                              '',                  force=True)
  set_dict_attr(owner,                        "$.special_id",                             '',                  force=True)
  set_dict_attr(owner,                        "$.status",                                 0,                   force=True)

  """
  data.room.owner.subscribe
  """
  subscribe = dict()
  set_dict_attr(subscribe,       "$.buy_type",                               0,                   force=True)
  set_dict_attr(subscribe,       "$.identity_type",                          0,                   force=True)
  set_dict_attr(subscribe,       "$.is_member",                              0,                   force=True)
  set_dict_attr(subscribe,       "$.level",                                  0,                   force=True)
  set_dict_attr(subscribe,       "$.open",                                   0,                   force=True)
  set_dict_attr(owner,           "$.subscribe",                              subscribe,           force=True)

  set_dict_attr(owner,           "$.telephone",                              '',                  force=True)
  set_dict_attr(owner,           "$.ticket_count",                           0,                   force=True)
  set_dict_attr(owner,           "$.top_vip_no",                             0,                   force=True)
  set_dict_attr(owner,           "$.total_recharge_diamond_count",           0,                   force=True)

  """
  data.room.owner.user_attr
  """
  user_attr = dict()
  set_dict_attr(user_attr,       "$.admin_privileges",                       [],                  force=True)
  set_dict_attr(user_attr,       "$.is_admin",                               False,               force=True)
  set_dict_attr(user_attr,       "$.is_muted",                               False,               force=True)
  set_dict_attr(user_attr,       "$.is_super_admin",                         False,               force=True)
  set_dict_attr(owner,           "$.user_attr",                              user_attr,           force=True)

  set_dict_attr(owner,           "$.user_canceled",                          False,               force=True)
  
  """
  data.room.owner.user_dress_info
  """
  user_dress_info = dict()
  set_dict_attr(user_dress_info, "$.dress_own_ids",                          [],                  force=True)
  set_dict_attr(user_dress_info, "$.dress_wear_ids",                         [],                  force=True)
  set_dict_attr(owner,           "$.user_dress_info",                        user_dress_info,     force=True)

  set_dict_attr(owner,           "$.user_open_id",                           '',                  force=True)
  set_dict_attr(owner,           "$.user_role",                              0,                   force=True)
  set_dict_attr(owner,           "$.verified",                               False,               force=True)
  set_dict_attr(owner,           "$.verified_content",                       '',                  force=True)
  set_dict_attr(owner,           "$.verified_mobile",                        False,               force=True)
  set_dict_attr(owner,           "$.verified_reason",                        '',                  force=True)
  set_dict_attr(owner,           "$.watch_duration_month",                   0,                   force=True)
  set_dict_attr(owner,           "$.web_rid",                                '',                  force=True)
  set_dict_attr(owner,           "$.webcast_uid",                            '',                  force=True)
  set_dict_attr(owner,           "$.with_car_management_permission",         False,               force=True)
  set_dict_attr(owner,           "$.with_commerce_permission",               False,               force=True)
  set_dict_attr(owner,           "$.with_fusion_shop_entry",                 False,               force=True)
  set_dict_attr(data,            "$.data.room.owner",                        owner,               force=True)  
  
  set_dict_attr(room,            "$.owner_device_id",                        0,                   force=True)
  set_dict_attr(room,            "$.owner_open_id",                          "",                  force=True)
  set_dict_attr(room,            "$.owner_user_id",                          0,                   force=True)
  
  """
    data.room.pack_meta
  """
  pack_meta = dict()
  set_dict_attr(pack_meta,       "$.cluster",                                "",                  force=True)
  set_dict_attr(pack_meta,       "$.dc",                                     "",                  force=True)
  set_dict_attr(pack_meta,       "$.env",                                    "",                  force=True)
  set_dict_attr(pack_meta,       "$.extras",                                 {},                  force=True)
  set_dict_attr(pack_meta,       "$.scene",                                  "",                  force=True)
  set_dict_attr(pack_meta,       "$.trace_id",                               "",                  force=True)
  set_dict_attr(room,            "$.pack_meta",                              pack_meta,           force=True)
  
  """
    data.room.paid_live_data
  """
  paid_live_data = dict()
  set_dict_attr(paid_live_data, "$.anchor_right",                            0,                   force=True)
  set_dict_attr(paid_live_data, "$.delivery",                                0,                   force=True)
  set_dict_attr(paid_live_data, "$.duration",                                0,                   force=True)
  set_dict_attr(paid_live_data, "$.max_preview_duration",                    0,                   force=True)
  set_dict_attr(paid_live_data, "$.need_delivery_notice",                    False,               force=True)
  set_dict_attr(paid_live_data, "$.paid_type",                               0,                   force=True)
  set_dict_attr(paid_live_data, "$.pay_ab_type",                             0,                   force=True)
  set_dict_attr(paid_live_data, "$.privilege_info",                          {},                  force=True)
  set_dict_attr(paid_live_data, "$.privilege_info_map",                      {},                  force=True)
  set_dict_attr(paid_live_data, "$.view_right",                              0,                   force=True)
  set_dict_attr(room,           "$.paid_live_data",                          paid_live_data,      force=True)
  
  set_dict_attr(room,           "$.popularity",                              0,                   force=True)
  set_dict_attr(room,           "$.popularity_str",                          "",                  force=True)
  set_dict_attr(room,           "$.pre_enter_time",                          0,                   force=True)
  set_dict_attr(room,           "$.preview_copy",                            "",                  force=True)
  set_dict_attr(room,           "$.preview_flow_tag",                        0,                   force=True)
  set_dict_attr(room,           "$.private_info",                            "",                  force=True)
  set_dict_attr(room,           "$.ranklist_audience_type",                  0,                   force=True)
  set_dict_attr(room,           "$.real_distance",                           "",                  force=True)
  set_dict_attr(room,           "$.redpacket_audience_auth",                 0,                   force=True)
  set_dict_attr(room,           "$.relation_tag",                            "",                  force=True)
  set_dict_attr(room,           "$.replay",                                  False,               force=True)
  set_dict_attr(room,           "$.replay_location",                         0,                   force=True)
  set_dict_attr(room,           "$.room_audit_status",                       0,                   force=True)
  
  """
    data.room.room_auth
  """
  room_auth = dict()
  set_dict_attr(room_auth,      "$.AIClone",                                 0,                   force=True)
  set_dict_attr(room_auth,      "$.AdminCommentWall",                        0,                   force=True)
  set_dict_attr(room_auth,      "$.AnchorAudioChat",                         0,                   force=True)
  set_dict_attr(room_auth,      "$.AnchorColdMessageTiled",                  0,                   force=True)
  set_dict_attr(room_auth,      "$.AnchorHotMessageAggregated",              0,                   force=True)
  set_dict_attr(room_auth,      "$.AnchorMission",                           0,                   force=True)
  set_dict_attr(room_auth,      "$.AudioChat",                               0,                   force=True)
  set_dict_attr(room_auth,      "$.AudioChatTotext",                         0,                   force=True)
  set_dict_attr(room_auth,      "$.Banner",                                  0,                   force=True)
  set_dict_attr(room_auth,      "$.BulletStyle",                             0,                   force=True)
  set_dict_attr(room_auth,      "$.CanSellTicket",                           0,                   force=True)
  set_dict_attr(room_auth,      "$.CastScreen",                              0,                   force=True)
  set_dict_attr(room_auth,      "$.CastScreenExplicit",                      0,                   force=True)
  set_dict_attr(room_auth,      "$.Chat",                                    False,               force=True)
  set_dict_attr(room_auth,      "$.ChatDispatch",                            0,                   force=True)
  set_dict_attr(room_auth,      "$.ChatDynamicSlideSpeed",                   0,                   force=True)
  set_dict_attr(room_auth,      "$.ChatDynamicSlideSpeedAnchor",             0,                   force=True)
  set_dict_attr(room_auth,      "$.ChatGuideEmoji",                          0,                   force=True)
  set_dict_attr(room_auth,      "$.ChatGuideImage",                          0,                   force=True)
  set_dict_attr(room_auth,      "$.ChatIdentity",                            0,                   force=True)
  set_dict_attr(room_auth,      "$.ChatMention",                             0,                   force=True)
  set_dict_attr(room_auth,      "$.ChatMentionV2",                           0,                   force=True)
  set_dict_attr(room_auth,      "$.ChatOperate",                             0,                   force=True)
  set_dict_attr(room_auth,      "$.ChatReply",                               0,                   force=True)
  set_dict_attr(room_auth,      "$.ClearEntranceOption",                     0,                   force=True)
  set_dict_attr(room_auth,      "$.Collect",                                 0,                   force=True)
  set_dict_attr(room_auth,      "$.CommentWall",                             0,                   force=True)
  set_dict_attr(room_auth,      "$.CommerceCard",                            0,                   force=True)
  set_dict_attr(room_auth,      "$.CommerceComponent",                       0,                   force=True)
  set_dict_attr(room_auth,      "$.CommonCard",                              0,                   force=True)
  set_dict_attr(room_auth,      "$.CountType",                               0,                   force=True)
  set_dict_attr(room_auth,      "$.Danmaku",                                 False,               force=True)
  set_dict_attr(room_auth,      "$.DanmakuDefault",                          0,                   force=True)
  set_dict_attr(room_auth,      "$.Denounce",                                0,                   force=True)
  set_dict_attr(room_auth,      "$.Digg",                                    False,               force=True)
  set_dict_attr(room_auth,      "$.Dislike",                                 0,                   force=True)
  set_dict_attr(room_auth,      "$.DonationSticker",                         0,                   force=True)
  set_dict_attr(room_auth,      "$.DouPlus",                                 0,                   force=True)
  set_dict_attr(room_auth,      "$.DouPlusPopularityGem",                    0,                   force=True)
  set_dict_attr(room_auth,      "$.DownloadVideo",                           0,                   force=True)
  set_dict_attr(room_auth,      "$.EcomFansClub",                            0,                   force=True)
  set_dict_attr(room_auth,      "$.EmojiOutside",                            0,                   force=True)
  set_dict_attr(room_auth,      "$.EnhancedTouch",                           0,                   force=True)
  set_dict_attr(room_auth,      "$.EnterEffects",                            0,                   force=True)
  set_dict_attr(room_auth,      "$.ExpandScreen",                            0,                   force=True)
  set_dict_attr(room_auth,      "$.FansClub",                                0,                   force=True)
  set_dict_attr(room_auth,      "$.FansClubBlessing",                        0,                   force=True)
  set_dict_attr(room_auth,      "$.FansClubDeclaration",                     0,                   force=True)
  set_dict_attr(room_auth,      "$.FansClubLetter",                          0,                   force=True)
  set_dict_attr(room_auth,      "$.FansClubNotice",                          0,                   force=True)
  set_dict_attr(room_auth,      "$.FansGroup",                               0,                   force=True)
  set_dict_attr(room_auth,      "$.FeaturedPublicScreen",                    0,                   force=True)
  set_dict_attr(room_auth,      "$.FirstFeedHistChat",                       0,                   force=True)
  set_dict_attr(room_auth,      "$.FixedChat",                               0,                   force=True)
  set_dict_attr(room_auth,      "$.FrequentlyChat",                          0,                   force=True)
  set_dict_attr(room_auth,      "$.FusionEmoji",                             0,                   force=True)
  set_dict_attr(room_auth,      "$.GamePointsPlaying",                       0,                   force=True)
  set_dict_attr(room_auth,      "$.Gift",                                    False,               force=True)
  set_dict_attr(room_auth,      "$.GiftAnchorMt",                            0,                   force=True)
  set_dict_attr(room_auth,      "$.GiftVote",                                0,                   force=True)
  set_dict_attr(room_auth,      "$.Highlights",                              0,                   force=True)
  set_dict_attr(room_auth,      "$.HostTeam",                                0,                   force=True)
  set_dict_attr(room_auth,      "$.HostTeamChannel",                         0,                   force=True)
  set_dict_attr(room_auth,      "$.HotChatTray",                             0,                   force=True)
  set_dict_attr(room_auth,      "$.HourRank",                                0,                   force=True)
  set_dict_attr(room_auth,      "$.ImHeatValue",                             0,                   force=True)
  set_dict_attr(room_auth,      "$.IndustryService",                         0,                   force=True)
  set_dict_attr(room_auth,      "$.InteractionGift",                         0,                   force=True)
  set_dict_attr(room_auth,      "$.InteractiveComponent",                    0,                   force=True)
  set_dict_attr(room_auth,      "$.ItemShare",                               0,                   force=True)
  set_dict_attr(room_auth,      "$.KtvOrderSong",                            0,                   force=True)
  set_dict_attr(room_auth,      "$.Landscape",                               1,                   force=True)
  set_dict_attr(room_auth,      "$.LandscapeChat",                           1,                   force=True)
  set_dict_attr(room_auth,      "$.LandscapeChatDynamicSlideSpeed",          0,                   force=True)
  set_dict_attr(room_auth,      "$.LandscapeGift",                           0,                   force=True)
  set_dict_attr(room_auth,      "$.LandscapeScreenCapture",                  0,                   force=True)
  set_dict_attr(room_auth,      "$.LandscapeScreenRecording",                0,                   force=True)
  set_dict_attr(room_auth,      "$.LandscapeScreenShare",                    0,                   force=True)
  set_dict_attr(room_auth,      "$.Like",                                    0,                   force=True)
  set_dict_attr(room_auth,      "$.LinkmicGuestLike",                        0,                   force=True)
  set_dict_attr(room_auth,      "$.LongPressOption",                         0,                   force=True)
  set_dict_attr(room_auth,      "$.LongTouch",                               0,                   force=True)
  set_dict_attr(room_auth,      "$.LuckMoney",                               False,               force=True)
  set_dict_attr(room_auth,      "$.MarkUser",                                0,                   force=True)
  set_dict_attr(room_auth,      "$.MediaHistoryMessage",                     0,                   force=True)
  set_dict_attr(room_auth,      "$.MediaLinkmic",                            0,                   force=True)
  set_dict_attr(room_auth,      "$.MessageDispatch",                         0,                   force=True)
  set_dict_attr(room_auth,      "$.MessageGift",                             0,                   force=True)
  set_dict_attr(room_auth,      "$.MissionCenter",                           0,                   force=True)
  set_dict_attr(room_auth,      "$.MoreAnchor",                              1,                   force=True)
  set_dict_attr(room_auth,      "$.MoreHistChat",                            0,                   force=True)
  set_dict_attr(room_auth,      "$.MultiplierPlayback",                      0,                   force=True)
  set_dict_attr(room_auth,      "$.MyLiveEntrance",                          0,                   force=True)
  set_dict_attr(room_auth,      "$.OnlyTa",                                  0,                   force=True)
  set_dict_attr(room_auth,      "$.PCPlay",                                  0,                   force=True)
  set_dict_attr(room_auth,      "$.POI",                                     False,               force=True)
  set_dict_attr(room_auth,      "$.PadPlay",                                 0,                   force=True)
  set_dict_attr(room_auth,      "$.PanelECService",                          0,                   force=True)
  set_dict_attr(room_auth,      "$.PlayerRankList",                          0,                   force=True)
  set_dict_attr(room_auth,      "$.Poster",                                  0,                   force=True)
  set_dict_attr(room_auth,      "$.PosterCache",                             0,                   force=True)
  set_dict_attr(room_auth,      "$.PreviewChatExpose",                       0,                   force=True)
  set_dict_attr(room_auth,      "$.PreviewHotCommentSwitch",                 0,                   force=True)
  set_dict_attr(room_auth,      "$.ProjectionBtn",                           0,                   force=True)
  set_dict_attr(room_auth,      "$.Props",                                   False,               force=True)
  set_dict_attr(room_auth,      "$.PublicScreen",                            0,                   force=True)
  set_dict_attr(room_auth,      "$.QuizGamePointsPlaying",                   0,                   force=True)
  set_dict_attr(room_auth,      "$.RecordScreen",                            0,                   force=True)
  set_dict_attr(room_auth,      "$.RoomChannel",                             0,                   force=True)
  set_dict_attr(room_auth,      "$.RoomChatLikeDisplay",                     0,                   force=True)
  set_dict_attr(room_auth,      "$.RoomChatOperatePanel",                    0,                   force=True)
  set_dict_attr(room_auth,      "$.RoomContributor",                         False,               force=True)
  set_dict_attr(room_auth,      "$.RoomWidget",                              0,                   force=True)
  set_dict_attr(room_auth,      "$.ScreenBottomInfo",                        0,                   force=True)
  set_dict_attr(room_auth,      "$.ScreenProjectionBarrage",                 0,                   force=True)
  set_dict_attr(room_auth,      "$.Seek",                                    0,                   force=True)
  set_dict_attr(room_auth,      "$.Selection",                               0,                   force=True)
  set_dict_attr(room_auth,      "$.SelectionAlbum",                          0,                   force=True)
  set_dict_attr(room_auth,      "$.Share",                                   0,                   force=True)
  set_dict_attr(room_auth,      "$.ShortTouch",                              0,                   force=True)
  set_dict_attr(room_auth,      "$.ShortTouchTempState",                     0,                   force=True)
  set_dict_attr(room_auth,      "$.ShowGamePlugin",                          0,                   force=True)
  set_dict_attr(room_auth,      "$.ShowQualification",                       0,                   force=True)
  set_dict_attr(room_auth,      "$.SmallWindowDisplay",                      0,                   force=True)
  set_dict_attr(room_auth,      "$.SmallWindowPlayer",                       0,                   force=True)
  set_dict_attr(room_auth,      "$.StickyMessage",                           0,                   force=True)
  set_dict_attr(room_auth,      "$.StreamAdaptation",                        0,                   force=True)
  set_dict_attr(room_auth,      "$.StrokeUpDownGuide",                       0,                   force=True)
  set_dict_attr(room_auth,      "$.SubscribeCardPackage",                    0,                   force=True)
  set_dict_attr(room_auth,      "$.Teleprompter",                            0,                   force=True)
  set_dict_attr(room_auth,      "$.TextGift",                                0,                   force=True)
  set_dict_attr(room_auth,      "$.TimedShutdown",                           0,                   force=True)
  set_dict_attr(room_auth,      "$.ToolbarBubble",                           0,                   force=True)
  set_dict_attr(room_auth,      "$.Topic",                                   0,                   force=True)
  set_dict_attr(room_auth,      "$.TypingCommentState",                      0,                   force=True)
  set_dict_attr(room_auth,      "$.UgcVSReplayDelete",                       0,                   force=True)
  set_dict_attr(room_auth,      "$.UgcVsReplayVisibility",                   0,                   force=True)
  set_dict_attr(room_auth,      "$.UpRightStatsFloatingLayer",               0,                   force=True)
  set_dict_attr(room_auth,      "$.UseHostInfo",                             0,                   force=True)
  set_dict_attr(room_auth,      "$.UserCard",                                False,               force=True)
  set_dict_attr(room_auth,      "$.UserCorner",                              0,                   force=True)
  set_dict_attr(room_auth,      "$.VSGift",                                  0,                   force=True)
  set_dict_attr(room_auth,      "$.VSRank",                                  0,                   force=True)
  set_dict_attr(room_auth,      "$.VSTopic",                                 0,                   force=True)
  set_dict_attr(room_auth,      "$.VerticalRank",                            0,                   force=True)
  set_dict_attr(room_auth,      "$.VerticalScreenShare",                     0,                   force=True)
  set_dict_attr(room_auth,      "$.VideoAmplificationType",                  0,                   force=True)
  set_dict_attr(room_auth,      "$.VideoShare",                              0,                   force=True)
  set_dict_attr(room_auth,      "$.VsCommentBar",                            0,                   force=True)
  set_dict_attr(room_auth,      "$.VsDouPlus",                               0,                   force=True)
  set_dict_attr(room_auth,      "$.VsExtensionEnableFollow",                 0,                   force=True)
  set_dict_attr(room_auth,      "$.VsFansClub",                              0,                   force=True)
  set_dict_attr(room_auth,      "$.VsWelcomeDanmaku",                        0,                   force=True)
  set_dict_attr(room_auth,      "$.WordAssociation",                         0,                   force=True)
  set_dict_attr(room,           "$.room_auth",                               room_auth,           force=True)
  
  set_dict_attr(room,           "$.room_create_ab_param",                    "",                  force=True)
  set_dict_attr(room,           "$.room_layout",                             0,                   force=True)
  set_dict_attr(room,           "$.room_tabs",                               [],                  force=True)
  set_dict_attr(room,           "$.room_tag",                                0,                   force=True)
  
  """
    data.room.room_view_stats
  """
  room_view_stats = dict()
  set_dict_attr(room_view_stats,             "$.display_long",                           "",                  force=True)
  set_dict_attr(room_view_stats,             "$.display_long_anchor",                    "",                  force=True)
  set_dict_attr(room_view_stats,             "$.display_middle",                         "",                  force=True)
  set_dict_attr(room_view_stats,             "$.display_middle_anchor",                  "",                  force=True)
  set_dict_attr(room_view_stats,             "$.display_short",                          "",                  force=True)
  set_dict_attr(room_view_stats,             "$.display_short_anchor",                   "",                  force=True)
  set_dict_attr(room_view_stats,             "$.display_type",                           0,                   force=True)
  set_dict_attr(room_view_stats,             "$.display_value",                          0,                   force=True)
  set_dict_attr(room_view_stats,             "$.display_version",                        0,                   force=True)
  set_dict_attr(room_view_stats,             "$.incremental",                            False,               force=True)
  set_dict_attr(room_view_stats,             "$.is_hidden",                              False,               force=True)
  set_dict_attr(room,                        "$.room_view_stats",                        room_view_stats,     force=True)
  
  set_dict_attr(room,                        "$.screen_capture_sharing_title",           "",                  force=True)
  set_dict_attr(room,                        "$.scroll_config",                          "",                  force=True)
  set_dict_attr(room,                        "$.search_id",                              0,                   force=True)
  set_dict_attr(room,                        "$.sell_goods",                             False,               force=True)
  set_dict_attr(room,                        "$.share_msg_style",                        0,                   force=True)
  set_dict_attr(room,                        "$.share_url",                              "",                  force=True)
  set_dict_attr(room,                        "$.sharing_music_id_list",                  [],                  force=True)
  set_dict_attr(room,                        "$.short_title",                            "",                  force=True)
  
  """
    data.room.short_touch_area_config
  """
  short_touch_area_config = dict()
  set_dict_attr(short_touch_area_config,     "$.elements",                       {},                  force=True)
  set_dict_attr(short_touch_area_config,     "$.forbidden_types_map",            {},                  force=True)
  set_dict_attr(short_touch_area_config,     "$.strategy_feat_whitelist",        [],                  force=True)
  set_dict_attr(short_touch_area_config,     "$.temp_state_condition_map",       {},                  force=True)

  """
    data.room.short_touch_area_config.temp_state_global_condition
  """
  temp_state_global_condition = dict()
  set_dict_attr(temp_state_global_condition, "$.allow_count",                    0,                           force=True)
  set_dict_attr(temp_state_global_condition, "$.duration_gap",                   0,                           force=True)
  set_dict_attr(temp_state_global_condition, "$.ignore_strategy_types",          [],                          force=True)
  set_dict_attr(short_touch_area_config,     "$.temp_state_global_condition",    temp_state_global_condition, force=True)
  
  """
    data.room.short_touch_area_config.temp_state_strategy
    TODO: details field
  """
  set_dict_attr(short_touch_area_config,     "$.temp_state_strategy",            {},                          force=True)  
  set_dict_attr(room,                        "$.short_touch_area_config",        short_touch_area_config,     force=True)
  
  set_dict_attr(room, "$.sofa_layout",                                       0,                   force=True)
  set_dict_attr(room, "$.stamps",                                            "",                  force=True)
  set_dict_attr(room, "$.start_time",                                        0,                   force=True)
  
  """
    data.room.stats
  """
  stats = dict()
  set_dict_attr(stats,                   "$.comment_count",                  0,                   force=True)
  set_dict_attr(stats,                   "$.digg_count",                     0,                   force=True)
  set_dict_attr(stats,                   "$.dou_plus_promotion",             "",                  force=True)
  set_dict_attr(stats,                   "$.enter_count",                    0,                   force=True)
  set_dict_attr(stats,                   "$.fan_ticket",                     0,                   force=True)
  set_dict_attr(stats,                   "$.follow_count",                   0,                   force=True)
  set_dict_attr(stats,                   "$.gift_uv_count",                  0,                   force=True)
  set_dict_attr(stats,                   "$.id",                             0,                   force=True)
  set_dict_attr(stats,                   "$.id_str",                         "",                  force=True)
  set_dict_attr(stats,                   "$.like_count",                     0,                   force=True)
  set_dict_attr(stats,                   "$.money",                          0,                   force=True)
  set_dict_attr(stats,                   "$.total_user",                     0,                   force=True)
  set_dict_attr(stats,                   "$.total_user_desp",                "",                  force=True)
  set_dict_attr(stats,                   "$.total_user_str",                 "",                  force=True)
  set_dict_attr(stats,                   "$.up_right_stats_str",             "",                  force=True)
  set_dict_attr(stats,                   "$.up_right_stats_str_complete",    "",                  force=True)
  
  """
    data.room.stats.user_count_composition
  """
  user_count_composition = dict()
  set_dict_attr(user_count_composition, "$.city",                             0,                                             force=True)
  set_dict_attr(user_count_composition, "$.my_follow",                        0,                                             force=True)
  set_dict_attr(user_count_composition, "$.other",                            0,                                             force=True)
  set_dict_attr(user_count_composition, "$.video_detail",                     0,                                             force=True)
  set_dict_attr(stats,                  "$.user_count_composition",           user_count_composition,                        force=True)
  
  set_dict_attr(stats, "$.user_count_str",                                    "",                 force=True)
  set_dict_attr(stats, "$.watermelon",                                        0,                  force=True)
  set_dict_attr(stats, "$.welfare_donation_amount",                           0,                  force=True)
  set_dict_attr(room, "$.stats", stats, force=True)
  
  set_dict_attr(room, "$.status",                                             0,                  force=True)
  set_dict_attr(room, "$.stream_close_time",                                  0,                  force=True)
  set_dict_attr(room, "$.stream_id",                                          0,                  force=True)
  set_dict_attr(room, "$.stream_id_str",                                      "",                 force=True)
  set_dict_attr(room, "$.stream_provider",                                    0,                  force=True)
  
  """
    data.room.stream_url
  """
  stream_url = dict()
  set_dict_attr(stream_url, "$.candidate_resolution",      [],    force=True)
  set_dict_attr(stream_url, "$.complete_push_urls",        [],    force=True)
  set_dict_attr(stream_url, "$.default_resolution",        "",    force=True)
  
  """
    data.room.stream_url.extra
  """
  extra = dict()
  set_dict_attr(extra,      "$.anchor_interact_profile",   0,     force=True)
  set_dict_attr(extra,      "$.audience_interact_profile", 0,     force=True)
  set_dict_attr(extra,      "$.bframe_enable",             False, force=True)
  set_dict_attr(extra,      "$.bitrate_adapt_strategy",    0,     force=True)
  set_dict_attr(extra,      "$.bytevc1_enable",            False, force=True)
  set_dict_attr(extra,      "$.default_bitrate",           0,     force=True)
  set_dict_attr(extra,      "$.fps",                       0,     force=True)
  set_dict_attr(extra,      "$.gop_sec",                   0,     force=True)
  set_dict_attr(extra,      "$.h265_enable",               False, force=True)
  set_dict_attr(extra,      "$.hardware_encode",           False, force=True)
  set_dict_attr(extra,      "$.height",                    0,     force=True)
  set_dict_attr(extra,      "$.max_bitrate",               0,     force=True)
  set_dict_attr(extra,      "$.min_bitrate",               0,     force=True)
  set_dict_attr(extra,      "$.roi",                       False, force=True)
  set_dict_attr(extra,      "$.sw_roi",                    False, force=True)
  set_dict_attr(extra,      "$.video_profile",             0,     force=True)
  set_dict_attr(extra,      "$.width",                     0,     force=True)
  set_dict_attr(stream_url, "$.extra",                     extra, force=True)
  
  """
    data.room.stream_url.flv_pull_url
  """
  flv_pull_url = dict()
  set_dict_attr(flv_pull_url, "$.FULL_HD1",     "",           force=True)
  set_dict_attr(stream_url,   "$.flv_pull_url", flv_pull_url, force=True)
  
  set_dict_attr(stream_url,   "$.flv_pull_url_params", {}, force=True)
  set_dict_attr(stream_url,   "$.hls_pull_url",        "", force=True)
  
  """
    data.room.stream_url.hls_pull_url_map
  """
  hls_pull_url_map = dict()
  set_dict_attr(hls_pull_url_map, "$.FULL_HD1",         "",               force=True)
  set_dict_attr(stream_url,       "$.hls_pull_url_map", hls_pull_url_map, force=True)
  
  set_dict_attr(stream_url,       "$.hls_pull_url_params", '',            force=True)
  set_dict_attr(stream_url,       "$.id",                  0,             force=True)
  set_dict_attr(stream_url,       "$.id_str",              '',            force=True)
  
  """
    data.room.stream_url.hls_pull_url_map.live_core_sdk_data
  """
  live_core_sdk_data = dict()

  """
    data.room.stream_url.hls_pull_url_map.live_core_sdk_data.pull_data
  """
  pull_data = dict()
  set_dict_attr(pull_data, "$.Flv",                  [], force=True)
  set_dict_attr(pull_data, "$.Hls",                  [], force=True)
  set_dict_attr(pull_data, "$.codec",                '', force=True)
  set_dict_attr(pull_data, "$.compensatory_data",    '', force=True)
  set_dict_attr(pull_data, "$.hls_data_unencrypted", {}, force=True)
  set_dict_attr(pull_data, "$.kind",                 0,  force=True)

  """
    data.room.stream_url.hls_pull_url_map.live_core_sdk_data.pull_data.options
  """
  options = dict()

  """
    data.room.stream_url.hls_pull_url_map.live_core_sdk_data.pull_data.options.default_quality
  """
  default_quality = dict()
  set_dict_attr(default_quality, "$.additional_content", '',              force=True)
  set_dict_attr(default_quality, "$.disable",            0,               force=True)
  set_dict_attr(default_quality, "$.fps",                0,               force=True)
  set_dict_attr(default_quality, "$.level",              0,               force=True)
  set_dict_attr(default_quality, "$.name",               "",              force=True)
  set_dict_attr(default_quality, "$.resolution",         '',              force=True)
  set_dict_attr(default_quality, "$.sdk_key",            "",              force=True)
  set_dict_attr(default_quality, "$.v_bit_rate",         0,               force=True)
  set_dict_attr(default_quality, "$.v_codec",            '',              force=True)
  set_dict_attr(options,         "$.default_quality",    default_quality, force=True)
  
  """
    data.room.stream_url.hls_pull_url_map.live_core_sdk_data.pull_data.options.qualities
  """
  set_dict_attr(options,   "$.qualities",          [],                  force=True)
  
  set_dict_attr(options,   "$.vpass_default",      False,               force=True)
  set_dict_attr(pull_data, "$.options",            options,             force=True)
  
  set_dict_attr(pull_data,          "$.stream_data",        '',                  force=True)
  set_dict_attr(pull_data,          "$.version",            0,                   force=True)
  set_dict_attr(live_core_sdk_data, "$.pull_data", pull_data,           force=True)
  set_dict_attr(live_core_sdk_data, "$.size",      '',                  force=True)
  set_dict_attr(stream_url,         "$.live_core_sdk_data", live_core_sdk_data, force=True)
  
  set_dict_attr(stream_url, "$.provider",          0,                   force=True)
  set_dict_attr(stream_url, "$.pull_datas",        {},                  force=True)
  set_dict_attr(stream_url, "$.push_datas",        {},                  force=True)
  set_dict_attr(stream_url, "$.push_stream_type",  0,                   force=True)
  set_dict_attr(stream_url, "$.push_urls",         [],                  force=True)
  
  """
    data.room.stream_url.resolution_name
  """
  resolution_name = dict()
  set_dict_attr(resolution_name, "$.FULL_HD1",     "",                  force=True)
  set_dict_attr(resolution_name, "$.HD1",          "",                  force=True)
  set_dict_attr(resolution_name, "$.ORIGION",      "",                  force=True)
  set_dict_attr(resolution_name, "$.SD1",          "",                  force=True)
  set_dict_attr(resolution_name, "$.SD2",          "",                  force=True)
  set_dict_attr(stream_url,      "$.resolution_name", resolution_name,  force=True)
  
  set_dict_attr(stream_url, "$.rtmp_pull_url",        "",               force=True)
  set_dict_attr(stream_url, "$.rtmp_pull_url_params", '',               force=True)
  set_dict_attr(stream_url, "$.rtmp_push_url",        '',               force=True)
  set_dict_attr(stream_url, "$.rtmp_push_url_params", '',               force=True)
  set_dict_attr(stream_url, "$.stream_control_type",  0,                force=True)
  set_dict_attr(stream_url, "$.stream_orientation",   0,                force=True)
  set_dict_attr(stream_url, "$.vr_type",              0,                force=True)
  
  set_dict_attr(room,       "$.stream_url",           stream_url,       force=True)

  set_dict_attr(room,         "$.sun_daily_icon_content",            '',     force=True)
  set_dict_attr(room,         "$.tags",                              [],     force=True)
  set_dict_attr(room,         "$.title",                             "",     force=True)
  set_dict_attr(room,         "$.title_recommend",                   False,  force=True)
  set_dict_attr(room,         "$.top_fans",                          [],     force=True)
  set_dict_attr(room,         "$.toutiao_cover_recommend_level",     0,      force=True)
  set_dict_attr(room,         "$.toutiao_title_recommend_level",     0,      force=True)
  set_dict_attr(room,         "$.upper_right_widget_data_list",      [],     force=True)
  set_dict_attr(room,         "$.use_filter",                        False,  force=True)
  set_dict_attr(room,         "$.user_count",                        0,      force=True)
  set_dict_attr(room,         "$.user_share_text",                   "",     force=True)
  set_dict_attr(room,         "$.vertical_cover_uri",                '',     force=True)
  set_dict_attr(room,         "$.vid",                               '',     force=True)
  set_dict_attr(room,         "$.video_feed_tag",                    "",     force=True)
  set_dict_attr(room,         "$.visibility_range",                  0,      force=True)
  set_dict_attr(room,         "$.vs_main_replay_id",                 0,      force=True)
  set_dict_attr(room,         "$.vs_roles",                          [],     force=True)
  set_dict_attr(room,         "$.wait_copy",                         "",     force=True)
  set_dict_attr(room,         "$.web_count",                         0,      force=True)
  set_dict_attr(room,         "$.webcast_comment_tcs",               0,      force=True)
  set_dict_attr(room,         "$.webcast_sdk_version",               0,      force=True)
  set_dict_attr(room,         "$.with_aggregate_column",             False,  force=True)
  set_dict_attr(room,         "$.with_draw_something",               False,  force=True)
  set_dict_attr(room,         "$.with_ktv",                          False,  force=True)
  set_dict_attr(room,         "$.with_linkmic",                      False,  force=True)
  set_dict_attr(data,         "$.room",                              room,   force=True)

  """
    data.user
  """
  user = dict()
  set_dict_attr(user, "$.adversary_authorization_info",             0,      force=True)
  set_dict_attr(user, "$.adversary_user_status",                    0,      force=True)
  set_dict_attr(user, "$.age_range",                                0,      force=True)
  set_dict_attr(user, "$.allow_be_located",                         False,  force=True)
  set_dict_attr(user, "$.allow_find_by_contacts",                   False,  force=True)
  set_dict_attr(user, "$.allow_others_download_video",              False,  force=True)
  set_dict_attr(user, "$.allow_others_download_when_sharing_video", False,  force=True)
  set_dict_attr(user, "$.allow_share_show_profile",                 False,  force=True)
  set_dict_attr(user, "$.allow_show_in_gossip",                     False,  force=True)
  set_dict_attr(user, "$.allow_show_my_action",                     False,  force=True)
  set_dict_attr(user, "$.allow_strange_comment",                    False,  force=True)
  set_dict_attr(user, "$.allow_unfollower_comment",                 False,  force=True)
  set_dict_attr(user, "$.allow_use_linkmic",                        False,  force=True)
  set_dict_attr(user, "$.authorization_info",                       0,      force=True)
  set_dict_attr(user, "$.badge_image_list",                         [],     force=True)
  set_dict_attr(user, "$.badge_image_list_v2",                      [],     force=True)
  set_dict_attr(user, "$.bg_img_url",                               '',     force=True)
  set_dict_attr(user, "$.birthday",                                 0,      force=True)
  set_dict_attr(user, "$.birthday_description",                     '',     force=True)
  set_dict_attr(user, "$.birthday_valid",                           False,  force=True)
  set_dict_attr(user, "$.block_status",                             0,      force=True)
  set_dict_attr(user, "$.city",                                     '',     force=True)
  set_dict_attr(user, "$.comment_restrict",                         0,      force=True)
  set_dict_attr(user, "$.commerce_webcast_config_ids",              [],     force=True)
  set_dict_attr(user, "$.constellation",                            '',     force=True)
  set_dict_attr(user, "$.consume_diamond_level",                    0,      force=True)
  set_dict_attr(user, "$.create_time",                              0,      force=True)
  set_dict_attr(user, "$.desensitized_nickname",                    '',     force=True)
  set_dict_attr(user, "$.disable_ichat",                            0,      force=True)
  set_dict_attr(user, "$.display_id",                               '',     force=True)
  set_dict_attr(user, "$.enable_ichat_img",                         0,      force=True)
  set_dict_attr(user, "$.exp",                                      0,      force=True)
  set_dict_attr(user, "$.experience",                               0,      force=True)
  set_dict_attr(user, "$.fan_ticket_count",                         0,      force=True)
  set_dict_attr(user, "$.fold_stranger_chat",                       False,  force=True)
  set_dict_attr(user, "$.follow_status",                            0,      force=True)
  set_dict_attr(user, "$.gender",                                   0,      force=True)
  set_dict_attr(user, "$.hotsoon_verified",                         False,  force=True)
  set_dict_attr(user, "$.hotsoon_verified_reason",                  '',     force=True)
  set_dict_attr(user, "$.ichat_restrict_type",                      0,      force=True)
  set_dict_attr(user, "$.id",                                       0,      force=True)
  set_dict_attr(user, "$.id_str",                                   '',     force=True)
  set_dict_attr(user, "$.income_share_percent",                     0,      force=True)
  set_dict_attr(user, "$.is_anonymous",                             False,  force=True)
  set_dict_attr(user, "$.is_follower",                              False,  force=True)
  set_dict_attr(user, "$.is_following",                             False,  force=True)
  set_dict_attr(user, "$.level",                                    0,      force=True)
  set_dict_attr(user, "$.link_mic_stats",                           0,      force=True)
  set_dict_attr(user, "$.location_city",                            '',     force=True)
  set_dict_attr(user, "$.media_badge_image_list",                   [],     force=True)
  set_dict_attr(user, "$.modify_time",                              0,      force=True)
  set_dict_attr(user, "$.mystery_man",                              0,      force=True)
  set_dict_attr(user, "$.need_profile_guide",                       False,  force=True)
  set_dict_attr(user, "$.new_real_time_icons",                      [],     force=True)
  set_dict_attr(user, "$.nickname",                                 '',     force=True)
  set_dict_attr(user, "$.pay_score",                                0,      force=True)
  set_dict_attr(user, "$.pay_scores",                               0,      force=True)
  set_dict_attr(user, "$.public_area_oper_freq",                    0,      force=True)
  set_dict_attr(user, "$.push_comment_status",                      False,  force=True)
  set_dict_attr(user, "$.push_digg",                                False,  force=True)
  set_dict_attr(user, "$.push_follow",                              False,  force=True)
  set_dict_attr(user, "$.push_friend_action",                       False,  force=True)
  set_dict_attr(user, "$.push_ichat",                               False,  force=True)
  set_dict_attr(user, "$.push_status",                              False,  force=True)
  set_dict_attr(user, "$.push_video_post",                          False,  force=True)
  set_dict_attr(user, "$.push_video_recommend",                     False,  force=True)
  set_dict_attr(user, "$.real_time_icons",                          [],     force=True)
  set_dict_attr(user, "$.remark_name",                              '',     force=True)
  set_dict_attr(user, "$.sec_uid",                                  '',     force=True)
  set_dict_attr(user, "$.secret",                                   0,      force=True)
  set_dict_attr(user, "$.share_qrcode_uri",                         '',     force=True)
  set_dict_attr(user, "$.short_id",                                 0,      force=True)
  set_dict_attr(user, "$.signature",                                '',     force=True)
  set_dict_attr(user, "$.special_id",                               '',     force=True)
  set_dict_attr(user, "$.status",                                   0,      force=True)
  set_dict_attr(user, "$.telephone",                                '',     force=True)
  set_dict_attr(user, "$.ticket_count",                             0,      force=True)
  set_dict_attr(user, "$.top_fans",                                 [],     force=True)
  set_dict_attr(user, "$.top_vip_no",                               0,      force=True)
  set_dict_attr(user, "$.total_recharge_diamond_count",             0,      force=True)
  set_dict_attr(user, "$.user_canceled",                            False,  force=True)
  set_dict_attr(user, "$.user_open_id",                             '',     force=True)
  set_dict_attr(user, "$.user_role",                                0,      force=True)
  set_dict_attr(user, "$.verified",                                 False,  force=True)
  set_dict_attr(user, "$.verified_content",                         '',     force=True)
  set_dict_attr(user, "$.verified_mobile",                          False,  force=True)
  set_dict_attr(user, "$.verified_reason",                          '',     force=True)
  set_dict_attr(user, "$.watch_duration_month",                     0,      force=True)
  set_dict_attr(user, "$.web_rid",                                  '',     force=True)
  set_dict_attr(user, "$.webcast_uid",                              '',     force=True)
  set_dict_attr(user, "$.with_car_management_permission",           False,  force=True)
  set_dict_attr(user, "$.with_commerce_permission",                 False,  force=True)
  set_dict_attr(user, "$.with_fusion_shop_entry",                   False,  force=True)
  set_dict_attr(data, "$.user",                                     user,   force=True)
  
  """
    extra
  """
  extra = dict()
  set_dict_attr(extra, "$.now",   0,       force=True)
  set_dict_attr(data,  "$.extra", extra,   force=True)
  
  """
    status_code
  """
  set_dict_attr(data, "$.status_code", 0, force=True)
  return data

##
## export a living data from social media stream downloader databse to yml file.
##
def export_live_info_to_yml(db:SocialMediaStreamDataBase, identifier:dict = None, output_path:str = None) -> None:
  ##
  ## check living record key field
  ##
  owner_user_id = get_dict_attr(identifier, "$.data.room.owner_user_id")
  platform      = "douyin"
  room_id       = get_dict_attr(identifier, "$.data.room.id")
  
  #####################################
  ##     collect living data         ##
  #####################################

  """
  >> extra
  """
  extra = dict()
  live_record       = LiveRecordTable(db)
  live_record_tuple = {key: None for key in live_record.get_tuple()}
  set_dict_attr(live_record_tuple, "$.platform",      platform,                      force=True)
  set_dict_attr(live_record_tuple, "$.owner_user_id", str(owner_user_id),            force=True)
  set_dict_attr(live_record_tuple, "$.room_id",       str(room_id),                  force=True)
  
  try:
    record_list = live_record.get_record(live_record_tuple)
    live_record_tuple = record_list.pop()
    now         = get_dict_attr(live_record_tuple, "$.now")
    user_id     = get_dict_attr(live_record_tuple, "$.user_id")
    start_time  = get_dict_attr(live_record_tuple, "$.start_time")
    finish_time = get_dict_attr(live_record_tuple, "$.finish_time")
  except Exception as e:
    get_logger().error(f"{e}: {live_record.get_name()} >> extra")
    now         = 0
    user_id     = 0
    start_time  = 0
    finish_time = 0

  """
  >> status_code
  """
  try:
    status_code = get_dict_attr(live_record_tuple, "$.status_code")
  except Exception as e:
    get_logger().error(f"{e}: {live_record.get_name()} >> status_code")
    status_code = 0

  """
  >> data
  >> >> data.room
  +----------------------------------+-------------------+------+-----+---------+-------+-------------------------------------------------------+---------------------------------+
  | Field                            | Type              | Null | Key | Default | Extra |Topology                                               | Comment                         |
  +----------------------------------+-------------------+------+-----+---------+-------+-------------------------------------------------------+---------------------------------+
  | AnchorABMap                      | json              | YES  |     | NULL    |       | "$.data.room.AnchorABMap"                             | 主播AB映射                       | 
  | acquaintance_status              | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.acquaintance_status"                     | 直播间熟人状态                    |
  | anchor_scheduled_time_text       | text              | YES  |     | NULL    |       | "$.data.room.anchor_scheduled_time_text"              | 直播间布局                       |
  | anchor_share_text                | text              | YES  |     | NULL    |       | "$.data.room.anchor_share_text"                       | 主播分享文本                     |
  | anchor_tab_type                  | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.anchor_tab_type"                         | 主播标签类型                     |
  | app_id                           | varchar(200)      | YES  |     | NULL    |       | "$.data.room.app_id"                                  | 应用ID                          |
  | auth_city                        | varchar(100)      | YES  |     | NULL    |       | "$.data.room.auth_city"                               | 直播间认证城市                   |
  | auto_cover                       | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.auto_cover"                              | 自动封面                         |
  | base_category                    | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.base_category"                           | 基础分类                         |
  | book_end_time                    | timestamp         | YES  |     | NULL    |       | "$.data.room.book_end_time"                           | 直播间预约结束时间                |
  | book_time                        | timestamp         | YES  |     | NULL    |       | "$.data.room.book_time"                               | 直播间预约开始时间                |
  | business_live                    | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.business_live"                           | 商业直播                         |
  | category                         | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.category"                                | 分类                            |
  | cell_style                       | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.cell_style"                              | 直播间单元样式                   |
  | city_top_distance                | tinytext          | YES  |     | NULL    |       | "$.data.room.city_top_distance"                       | 城市顶部距离                     |
  | client_version                   | varchar(20)       | YES  |     | NULL    |       | "$.data.room.client_version"                          | 客户端版本                       |
  | placeholder                      | tinytext          | YES  |     | NULL    |       | "$.data.room.comment_box.placeholder"                 | 评论框占位符                     |
  | comment_name_mode                | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.comment_name_mode"                       | 评论名称模式                     |
  | common_label_list                | tinytext          | YES  |     | NULL    |       | "$.data.room.common_label_list"                       | 常用标签列表                     |
  | content_tag                      | tinytext          | YES  |     | NULL    |       | "$.data.room.content_tag"                             | 内容标签                         |
  | create_time                      | timestamp         | YES  |     | NULL    |       | "$.data.room.create_time"                             | 直播间创建时间                    | 
  | distance                         | varchar(100)      | YES  |     | NULL    |       | "$.data.room.distance"                                | 距离                             |
  | distance_city                    | varchar(100)      | YES  |     | NULL    |       | "$.data.room.distance_city"                           | 城市距离                         |
  | distance_km                      | varchar(100)      | YES  |     | NULL    |       | "$.data.room.distance_km"                             | 公里距离                         |
  | dynamic_cover_dict               | json              | YES  |     | NULL    |       | "$.data.room.dynamic_cover_dict"                      | 动态封面字典                     |
  | dynamic_cover_uri                | text              | YES  |     | NULL    |       | "$.data.room.dynamic_cover_uri"                       | 动态封面URI                      |
  | enable_room_perspective          | bool              | YES  |     | NULL    |       | "$.data.room.enable_room_perspective"                 | 是否启用直播间透视                |
  | create_scene                     | tinytext          | YES  |     | NULL    |       | "$.data.room.extra.create_scene"                      | 创建场景                         |
  | facial_unrecognised              | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.extra.facial_unrecognised"               | 面部未识别                       |
  | geo_block                        | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.extra.geo_block"                         | 地理封锁                         |
  | is_sandbox                       | bool              | YES  |     | NULL    |       | "$.data.room.extra.is_sandbox"                        | 是否为沙盒                       |
  | is_virtual_anchor                | bool              | YES  |     | NULL    |       | "$.data.room.extra.is_virtual_anchor"                 | 是否为虚拟主播                   |
  | limit_appid                      | varchar(200)      | YES  |     | NULL    |       | "$.data.room.extra.limit_appid"                       | 限制应用ID                      |
  | limit_strategy                   | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.extra.limit_strategy"                    | 地理封锁                        |
  | realtime_playback_shift          | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.extra.realtime_playback_shift"           | 实时回放偏移                    |
  | realtime_playback_start_shift    | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.extra.realtime_playback_start_shift"     | 实时回放开始偏移                 |
  | realtime_replay_enabled          | bool              | YES  |     | NULL    |       | "$.data.room.extra.realtime_replay_enabled"           | 是否启用实时回放                 |
  | vr_type                          | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.extra.vr_type"                           | VR类型                          |
  | vs_type                          | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.extra.vs_type"                           | VS类型                          |
  | xigua_uid                        | varchar(200)      | YES  |     | NULL    |       | "$.data.room.extra.xigua_uid"                         | 西瓜用户ID                       |
  | fansclub_msg_style               | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.fansclub_msg_style"                      | 粉丝俱乐部消息样式                |
  | fcdn_appid                       | varchar(200)      | YES  |     | NULL    |       | "$.data.room.fcdn_appid"                              | FCDN应用ID                       |
  | finish_reason                    | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.finish_reason"                           | 直播结束原因                     |
  | finish_time                      | timestamp         | YES  |     | NULL    |       | "$.data.room.finish_time"                             | 直播结束时间                     |
  | finish_url                       | text              | YES  |     | NULL    |       | "$.data.room.finish_url"                              | 直播结束URL                      |
  | follow_msg_style                 | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.follow_msg_style"                        | 关注消息样式                     |
  | forum_extra_data                 | text              | YES  |     | NULL    |       | "$.data.room.forum_extra_data"                        | 论坛额外数据                     |
  | game_room_type                   | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.game_room_type"                          | 游戏直播间类型                   |
  | gift_msg_style                   | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.gift_msg_style"                          | 礼物消息样式                     |
  | group_id                         | varchar(200)      | YES  |     | NULL    |       | "$.data.room.group_id"                                | 直播间组ID                       |
  | group_source                     | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.group_source"                            | 直播间组来源                     |
  | has_commerce_goods               | bool              | YES  |     | NULL    |       | "$.data.room.has_commerce_goods"                      | 是否有商品                       |
  | has_promotion_games              | bool              | YES  |     | NULL    |       | "$.data.room.has_promotion_games"                     | 是否有推广游戏                   |
  | highlight                        | bool              | YES  |     | NULL    |       | "$.data.room.highlight"                               | 是否高亮                         |
  | id                               | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                                      | 直播间 ID                       |
  | introduction                     | text              | YES  |     | NULL    |       | "$.data.room.introduction"                            | 直播间介绍                       |
  | is_need_check_list               | bool              | YES  |     | NULL    |       | "$.data.room.is_need_check_list"                      | 是否需要检查列表                 |
  | is_official_channel_room         | bool              | YES  |     | NULL    |       | "$.data.room.is_official_channel_room"                | 是否为官方频道直播间              |
  | is_replay                        | bool              | YES  |     | NULL    |       | "$.data.room.is_replay"                               | 是否为回放                       |
  | is_show_inquiry_ball             | bool              | YES  |     | NULL    |       | "$.data.room.is_show_inquiry_ball"                    | 是否显示询问球                   |
  | is_show_user_card_switch         | bool              | YES  |     | NULL    |       | "$.data.room.is_show_user_card_switch"                | 是否显示用户卡片开关              |
  | item_explicit_info               | text              | YES  |     | NULL    |       | "$.data.room.item_explicit_info"                      | 物品显式信息                     |
  | layout                           | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.layout"                                  | 直播间布局                       |
  | linkmic_display_type             | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.linkmic_display_type"                    | 连麦显示类型                     |
  | linkmic_layout                   | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.linkmic_layout"                          | 连麦布局                         |
  | live_id                          | varchar(200)      | YES  |     | NULL    |       | "$.data.room.live_id"                                 | 直播ID                          |
  | live_platform_source             | tinytext          | YES  |     | NULL    |       | "$.data.room.live_platform_source"                    | 直播平台来源                     |
  | live_room_mode                   | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.live_room_mode"                          | 直播间模式                       |
  | live_type_audio                  | bool              | YES  |     | NULL    |       | "$.data.room.live_type_audio"                         | 是否为音频直播                   |
  | live_type_linkmic                | bool              | YES  |     | NULL    |       | "$.data.room.live_type_linkmic"                       | 是否为连麦直播                   |
  | live_type_normal                 | bool              | YES  |     | NULL    |       | "$.data.room.live_type_normal"                        | 是否为普通直播                   |
  | live_type_official               | bool              | YES  |     | NULL    |       | "$.data.room.live_type_official"                      | 是否为官方直播                   |
  | live_type_sandbox                | bool              | YES  |     | NULL    |       | "$.data.room.live_type_sandbox"                       | 是否为沙盒直播                   |
  | live_type_screenshot             | bool              | YES  |     | NULL    |       | "$.data.room.live_type_screenshot"                    | 是否为截图直播                   |
  | live_type_third_party            | bool              | YES  |     | NULL    |       | "$.data.room.live_type_third_party"                   | 是否为第三方直播                 |
  | live_type_vs_live                | bool              | YES  |     | NULL    |       | "$.data.room.live_type_vs_live"                       | 是否为VS直播                     |
  | live_type_vs_premiere            | bool              | YES  |     | NULL    |       | "$.data.room.live_type_vs_premiere"                   | 是否为VS首播                     |
  | admin_flag                       | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.living_room_attrs.admin_flag"            | 直播间管理员标志                  |
  | location                         | varchar(100)      | YES  |     | NULL    |       | "$.data.room.location"                                | 直播间位置                        |
  | official_channel_open_id         | varchar(200)      | YES  |     | NULL    |       | "$.data.room.official_channel_open_id"                | 官方频道OpenID                   |
  | official_channel_uid             | varchar(200)      | YES  |     | NULL    |       | "$.data.room.official_channel_uid"                    | 官方频道用户ID                   |
  | orientation                      | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.orientation"                             | 直播间方向                       |
  | os_type                          | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.os_type"                                 | 操作系统类型                     |
  | owner_device_id                  | varchar(200)      | YES  |     | NULL    |       | "$.data.room.owner.owner_device_id"                   | 主播设备ID                      |
  | owner_open_id                    | varchar(200)      | YES  |     | NULL    |       | "$.data.room.owner.owner_open_id"                     | 主播OpenID                      | 
  | owner_user_id                    | varchar(200)      | YES  |     | NULL    |       | "$.data.room.owner_user_id"                           | 账号作者ID                      |
  | start_time                       | timestamp         | YES  |     | NULL    |       | "$.data.room.start_time"                              | 开始时间                         | 
  | room_layout                      | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.room_layout"                             | 直播间布局                        |
  | room_tag                         | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.room_tag"                                | 直播间标签                        |
  | scroll_config                    | text              | YES  |     | NULL    |       | "$.data.room.scroll_config"                           | 滚动配置                          |
  | search_id                        | varchar(200)      | YES  |     | NULL    |       | "$.data.room.search_id"                               | 直播间搜索ID                     |
  | sell_goods                       | bool              | YES  |     | NULL    |       | "$.data.room.sell_goods"                              | 卖货                             |
  | share_msg_style                  | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.share_msg_style"                         | 分享消息样式                      |
  | share_url                        | text              | YES  |     | NULL    |       | "$.data.room.share_url"                               | 直播间分享链接                    |
  | title                            | tinytext          | YES  |     | NULL    |       | "$.data.room.title"                                   | 直播间标题                       |
  | title_recommend                  | bool              | YES  |     | NULL    |       | "$.data.room.title_recommend"                         | 是否推荐标题                     |
  | toutiao_cover_recommend_level    | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.toutiao_cover_recommend_level"           | 头条封面推荐等级                 |
  | toutiao_title_recommend_level    | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.toutiao_title_recommend_level"           | 头条标题推荐等级                 |
  | use_filter                       | bool              | YES  |     | NULL    |       | "$.data.room.use_filter"                              | 是否使用滤镜                     |
  | user_count                       | unsigned int      | YES  |     | NULL    |       | "$.data.room.user_count"                              | 用户数量                         |
  | vertical_cover_uri               | text              | YES  |     | NULL    |       | "$.data.room.vertical_cover_uri"                      | 竖屏封面URI                      |
  | vid                              | varchar(200)      | YES  |     | NULL    |       | "$.data.room.vid"                                     | 视频ID                          |
  | video_feed_tag                   | tinytext          | YES  |     | NULL    |       | "$.data.room.video_feed_tag"                          | 视频Feed标签                     |
  | visibility_range                 | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.visibility_range"                        | 可见范围：X-公开 X-私密 X-好友可见 |
  | vs_main_replay_id                | varchar(200)      | YES  |     | NULL    |       | "$.data.room.vs_main_replay_id"                       | VS主回放ID                       |
  | wait_copy                        | tinytext          | YES  |     | NULL    |       | "$.data.room.wait_copy"                               | 等待复制                         |
  | webcast_sdk_version              | varchar(20)       | YES  |     | NULL    |       | "$.data.room.webcast_sdk_version"                     | 直播间SDK版本                     |
  +----------------------------------+-------------------+------+-----+---------+-------+-------------------------------------------------------+----------------------------------+YES
  """
  room_attribute       = RoomAttributeTable(db)
  room_attribute_tuple = {key: None for key in room_attribute.get_tuple()}
  set_dict_attr(room_attribute_tuple, "$.id",       str(room_id))
  
  try:
    room_attribute_tuple_list = room_attribute.get_record(room_attribute_tuple)
    if len(room_attribute_tuple_list) != 0:
      room_attribute_tuple = room_attribute_tuple_list.pop()
  except Exception as e:
    get_logger().error(f"{e}: {room_attribute.get_name()} >> >> data.room")

  """
  >> >> >> data.room.admin_user_ids
  """
  admin_user_id = RoomAdminUserIdTable(db)
  admin_user_id_tuple = {key: None for key in admin_user_id.get_tuple()}
  
  set_dict_attr(admin_user_id_tuple, "$.start_time", start_time)
  set_dict_attr(admin_user_id_tuple, "$.platform",   platform)
  set_dict_attr(admin_user_id_tuple, "$.room_id",    str(room_id))
  
  try:
    admin_user_ids = list()
    admin_user_id_list = admin_user_id.get_record(admin_user_id_tuple, fetchall=True)
    for admin_user_id_index in range(0, len(admin_user_id_list)):
      admin_user_ids.insert(admin_user_id_list[admin_user_id_index].get('admin_user_id_index'), int(admin_user_id_list[admin_user_id_index].get('admin_user_id', 0)))
  except Exception as e:
    get_logger().error(f"{e}: {admin_user_id.get_name()} >> >> >> data.room.admin_user_ids")
    admin_user_ids = []

  """
  >> >> >> data.room.admin_user_open_ids
  """
  admin_user_open_id       = RoomAdminUserOpenIdTable(db)
  admin_user_open_id_tuple = {key: None for key in admin_user_open_id.get_tuple()}
  
  set_dict_attr(admin_user_open_id_tuple, "$.now",      now)
  set_dict_attr(admin_user_open_id_tuple, "$.platform", platform)
  set_dict_attr(admin_user_open_id_tuple, "$.room_id",  str(room_id))
  
  try:
    admin_user_open_ids = list()
    admin_user_open_id_list = admin_user_open_id.get_record(admin_user_open_id_tuple, fetchall=True)
    if len(admin_user_open_id_list) != 0:
      for admin_user_open_id_record in admin_user_open_id_list:
        admin_user_open_ids.append(get_dict_attr(admin_user_open_id_record, "$.admin_user_open_id"))
  except Exception as e:
    get_logger().error(f"{e}: {admin_user_open_id.get_name()} >> >> >> data.room.admin_user_open_ids")
    admin_user_open_ids = []

  """
  +-------------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------+---------------------+
  | Field                               | Type              | Null | Key | Default | Extra | Topology                                               | Comment             |
  +-------------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------+---------------------+
  | now                                 | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"                                          | 当前时间戳           | 
  | platform                            | varchar(20)       | NO   | PRI |         |       |           -                                            | 平台                 | 
  | id                                  | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                                       | 直播间ID             | 
  | `rank`                              | unsigned smallint |      |     | NULL    |       | "$.data.room.living_room_attrs.rank"                   | 排名/等级            |
  | silence_flag                        | unsigned tinyint  |      |     | NULL    |       | "$.data.room.living_room_attrs.silence_flag"           | 直播间静音状态       | 
  | view_stats_display_long             | tinytext          |      |     | NULL    |       | "$.data.room.room_view_stats.display_long"             | 直播间观看人数       | 
  | view_stats_display_long_anchor      | tinytext          |      |     | NULL    |       | "$.data.room.room_view_stats.display_long_anchor"      | 主播观看人数         | 
  | view_stats_display_middle           | tinytext          |      |     | NULL    |       | "$.data.room.room_view_stats.display_middle"           | 直播间观看人数（中）  |
  | view_stats_display_middle_anchor    | tinytext          |      |     | NULL    |       | "$.data.room.room_view_stats.display_middle_anchor"    | 主播观看人数（中）    |
  | view_stats_display_short            | tinytext          |      |     | NULL    |       | "$.data.room.room_view_stats.display_short"            | 直播间观看人数（短）  |
  | view_stats_display_short_anchor     | tinytext          |      |     | NULL    |       | "$.data.room.room_view_stats.display_short_anchor"     | 主播观看人数（短）    |
  | view_stats_display_type             | unsigned tinyint  |      |     | NULL    |       | "$.data.room.room_view_stats.display_type"             | 直播间观看人数显示类型 |
  | view_stats_display_value            | unsigned int      |      |     | NULL    |       | "$.data.room.room_view_stats.display_value"            | 直播间观看人数        |
  | view_stats_display_version          | varchar(20)       |      |     | NULL    |       | "$.data.room.room_view_stats.display_version"          | 直播间观看人数显示版本 |
  | view_stats_incremental              | bool              |      |     | NULL    |       | "$.data.room.room_view_stats.incremental"              | 是否增量更新          |
  | view_stats_is_hidden                | bool              |      |     | NULL    |       | "$.data.room.room_view_stats.is_hidden"                | 是否隐藏状态          |
  | user_share_text                     | text              |      |     | NULL    |       | "$.data.room.user_share_text"                          | 用户分享文本          |
  | screen_capture_sharing_title        | tinytext          |      |     | NULL    |       | "$.data.room.screen_capture_sharing_title"             | 屏幕截图分享标题       |
  | short_title                         | tinytext          |      |     | NULL    |       | "$.data.room.short_title"                              | 屏幕直播间短          |
  | lottery_finish_time                 | timestamp         |      |     | NULL    |       | "$.data.room.lottery_finish_time"                      | 抽奖结束时间          |
  | luckymoney_num                      | unsigned int      |      |     | NULL    |       | "$.data.room.luckymoney_num"                           | 幸运红包数量          |
  | mosaic_status                       | unsigned int      |      |     | NULL    |       | "$.data.room.mosaic_status"                            | 马赛克状态            |
  | mosaic_tip                          | tinytext          |      |     | NULL    |       | "$.data.room.mosaic_tip"                               | 马赛克提示            |
  | popularity                          | unsigned bigint   |      |     | NULL    |       | "$.data.room.popularity"                               | 人气                 |
  | popularity_str                      | varchar(20)       |      |     | NULL    |       | "$.data.room.popularity_str"                           | 人气字符串            |
  | pre_enter_time                      | timestamp         |      |     | NULL    |       | "$.data.room.pre_enter_time"                           | 预进入时间            |
  | preview_copy                        | tinytext          |      |     | NULL    |       | "$.data.room.preview_copy"                             | 预览复制文本          |
  | preview_flow_tag                    | unsigned tinyint  |      |     | NULL    |       | "$.data.room.preview_flow_tag"                         | 预览流量标签          |
  | private_info                        | text              |      |     | NULL    |       | "$.data.room.private_info"                             | 私有信息              |
  | ranklist_audience_type              | unsigned tinyint  |      |     | NULL    |       | "$.data.room.ranklist_audience_type"                   | 排行榜观众类型        |
  | real_distance                       | varchar(100)      |      |     | NULL    |       | "$.data.room.real_distance"                            | 实际距离              |
  | redpacket_audience_auth             | unsigned tinyint  |      |     | NULL    |       | "$.data.room.redpacket_audience_auth"                  | 红包观众认证          |
  | relation_tag                        | tinytext          |      |     | NULL    |       | "$.data.room.relation_tag"                             | 关系标签              |
  | replay                              | bool              |      |     | NULL    |       | "$.data.room.replay"                                   | 是否为回放            |
  | replay_location                     | unsigned tinyint  |      |     | NULL    |       | "$.data.room.replay_location"                          | 回放位置              |
  | room_audit_status                   | unsigned tinyint  |      |     | NULL    |       | "$.data.room.room_audit_status"                        | 直播间审核状态        |
  | room_create_ab_param                | text              |      |     | NULL    |       | "$.data.room.room_create_ab_param"                     | 直播间创建AB参数      |
  | sofa_layout                         | unsigned tinyint  |      |     | NULL    |       | "$.data.room.sofa_layout"                              | 沙发布局              |
  | stamps                              | text              |      |     | NULL    |       | "$.data.room.stamps"                                   | 印章                 |
  | comment_count                       | unsigned bigint   |      |     | NULL    |       | "$.data.room.stats.comment_count"                      | 评论数量              |
  | digg_count                          | unsigned bigint   |      |     | NULL    |       | "$.data.room.stats.digg_count"                         | 点赞数量              |
  | dou_plus_promotion                  | tinytext          |      |     | NULL    |       | "$.data.room.stats.dou_plus_promotion"                 | DouPlus推广          |
  | enter_count                         | unsigned bigint   |      |     | NULL    |       | "$.data.room.stats.enter_count"                        | 进入数量              |
  | fan_ticket                          | unsigned bigint   |      |     | NULL    |       | "$.data.room.stats.fan_ticket"                         | 粉丝票数量            |
  | follow_count                        | unsigned bigint   |      |     | NULL    |       | "$.data.room.stats.follow_count"                       | 关注数量              |
  | gift_uv_count                       | unsigned int      |      |     | NULL    |       | "$.data.room.stats.gift_uv_count"                      | 礼物UV数量            |
  | like_count                          | unsigned int      |      |     | NULL    |       | "$.data.room.stats.like_count"                         | 喜欢数量              |
  | money                               | unsigned int      |      |     | NULL    |       | "$.data.room.stats.money"                              | 金额                  |
  | total_user                          | unsigned int      |      |     | NULL    |       | "$.data.room.stats.total_user"                         | 用户数量              |
  | total_user_desp                     | text              |      |     | NULL    |       | "$.data.room.stats.total_user_desp"                    | 总用户描述            |
  | total_user_str                      | varchar(100)      |      |     | NULL    |       | "$.data.room.stats.total_user_str"                     | 总用户描述            |
  | up_right_stats_str                  | varchar(100)      |      |     | NULL    |       | "$.data.room.stats.up_right_stats_str"                 | 右上角统计字符串      |
  | up_right_stats_str_complete         | tinytext          |      |     | NULL    |       | "$.data.room.stats.up_right_stats_str_complete"        | 完整的右上角统计字符串 |
  | user_count_composition_city         | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stats.user_count_composition.city"        | 城市                 |
  | user_count_composition_my_follow    | unsigned bigint   |      |     | NULL    |       | "$.data.room.stats.user_count_composition.my_follow"   | 我的关注              |
  | user_count_composition_other        | unsigned bigint   |      |     | NULL    |       | "$.data.room.stats.user_count_composition.other"       | 其他                 |
  | user_count_composition_video_detail | unsigned bigint   |      |     | NULL    |       | "$.data.room.stats.user_count_composition.video_detail"| 视频详情              |
  | user_count_str                      | unsigned bigint   |      |     | NULL    |       | "$.data.room.stats.user_count_str"                     | 用户数量字符串        |
  | watermelon                          | unsigned bigint   |      |     | NULL    |       | "$.data.room.stats.watermelon"                         | 西瓜                 |
  | welfare_donation_amount             | unsigned bigint   |      |     | NULL    |       | "$.data.room.stats.welfare_donation_amount"            | 福利捐赠金额          |
  | status                              | unsigned tinyint  |      |     | NULL    |       | "$.data.room.status"                                   | 直播状态             | 
  | stream_close_time                   | timestamp         |      |     | NULL    |       | "$.data.room.stream_close_time"                        | 直播间流关闭时间戳     |
  | stream_id                           | varchar(200)      |      |     | NULL    |       | "$.data.room.stream_id"                                | 直播间流ID            |
  | stream_provider                     | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stream_provider"                          | 直播间流提供者         |
  | sun_daily_icon_content              | text              |      |     | NULL    |       | "$.data.room.sun_daily_icon_content"                   | 日常图标内容          |
  | challenge_info                      | tinytext          |      |     | NULL    |       | "$.data.room.challenge_info"                           | 挑战信息              |
  | danmaku_detail                      | unsigned int      |      |     | NULL    |       | "$.data.room.danmaku_detail"                           | 弹幕详情              |
  | hot_sentence_info                   | text              |      |     | NULL    |       | "$.data.room.hot_sentence_info"                        | 热门语句信息          |
  | last_ping_time                      | timestamp         |      |     | NULL    |       | "$.data.room.last_ping_time"                           | 最后ping时间          |
  | room_like_count                     | unsigned bigint   |      |     | NULL    |       | "$.data.room.like_count"                               | 点赞数量              |
  | linker_map                          | json              |      |     | NULL    |       | "$.data.room.linker_map"                               | 点连接器映射          |
  | web_count                           | unsigned bigint   |      |     | NULL    |       | "$.data.room.web_count"                                | 网页观看人数          |
  | webcast_comment_tcs                 | unsigned int      |      |     | NULL    |       | "$.data.room.webcast_comment_tcs"                      | 直播间评论TCs         |
  | with_aggregate_column               | bool              |      |     | NULL    |       | "$.data.room.with_aggregate_column"                    | 是否有聚合栏目        |
  | with_draw_something                 | bool              |      |     | NULL    |       | "$.data.room.with_draw_something"                      | 是否有抽奖            |
  | with_ktv                            | bool              |      |     | NULL    |       | "$.data.room.with_ktv"                                 | 是否有KTV             |
  | with_linkmic                        | bool              |      |     | NULL    |       | "$.data.room.with_linkmic"                             | 是否有连麦            |
  +-------------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------+----------------------+
  """
  room_record       = RoomRecordTable(db)
  room_record_tuple = {key: None for key in room_record.get_tuple()}
  
  set_dict_attr(room_record_tuple, "$.platform", platform)
  set_dict_attr(room_record_tuple, "$.id",       str(room_id))

  try:
    room_record_tuple_list = room_record.get_record(room_record_tuple)
    if len(room_record_tuple_list) != 0:
      room_record_tuple = room_record_tuple_list.pop()
  except Exception as e:
    get_logger().error(f"{e}: {room_record.get_name()} >> >> data.room")

  """
  TODO
  >> >> >> data.room.assist_label_list
  """
  assist_label_list = list()
  
  """
  >> >> >> data.room.cover
  """
  cover = dict()

  ##
  ## PictureTable
  ##
  cover_picture       = PictureTable(db)
  cover_picture_tuple = {key: None for key in cover_picture.get_tuple()}

  set_dict_attr(cover_picture_tuple, "$.start_time",  start_time)
  set_dict_attr(cover_picture_tuple, "$.platform",    platform)
  set_dict_attr(cover_picture_tuple, "$.room_id",     str(room_id))
  set_dict_attr(cover_picture_tuple, "$.label",       'cover')

  try:
    cover_picture_tuple_list = cover_picture.get_record(cover_picture_tuple)
    if len(cover_picture_tuple_list) != 0:
      cover_picture_tuple = cover_picture_tuple_list.pop()
  except Exception as e:
    get_logger().error(f"{e}: {cover_picture.get_name()} >> >> >> data.room.cover")

  """
  >> >> >> >> data.room.cover.flex_setting_list
  """
  cover_pic_flex_setting = PictureFlexSettingTable(db)
  cover_pic_flex_setting_tuple = {key: None for key in cover_pic_flex_setting.get_tuple()}
  
  set_dict_attr(cover_pic_flex_setting_tuple, "$.uri",        cover_picture_tuple.get('uri', ''))
  set_dict_attr(cover_pic_flex_setting_tuple, "$.platform",   'douyin')
  set_dict_attr(cover_pic_flex_setting_tuple, "$.start_time", start_time)
  set_dict_attr(cover_pic_flex_setting_tuple, "$.room_id",    str(room_id))
  set_dict_attr(cover_pic_flex_setting_tuple, "$.label",      'cover')
  
  try:
    cover_flex_setting_list = list()
    cover_pic_flex_setting_tuple_list = cover_pic_flex_setting.get_record(cover_pic_flex_setting_tuple, fetchall=True)
    for flex_setting in cover_pic_flex_setting_tuple_list:
      cover_flex_setting_list.append(get_dict_attr(flex_setting, "$.flex_setting"))
  except Exception as e:
    get_logger().error(f"{e}: {cover_pic_flex_setting.get_name()} >> >> >> data.room.cover")
    cover_flex_setting_list = []
  
  """
  >> >> >> >> data.room.cover.text_setting_list
  """
  cover_pic_text_setting = PictureTextSettingTable(db)
  cover_pic_text_setting_tuple = {key: None for key in cover_pic_text_setting.get_tuple()}
  
  set_dict_attr(cover_pic_text_setting_tuple, "$.uri",        cover_picture_tuple.get('uri', ''))
  set_dict_attr(cover_pic_text_setting_tuple, "$.platform",   'douyin')
  set_dict_attr(cover_pic_text_setting_tuple, "$.start_time", start_time)
  set_dict_attr(cover_pic_text_setting_tuple, "$.room_id",    str(room_id))
  set_dict_attr(cover_pic_text_setting_tuple, "$.label",      'cover')
  
  try:
    cover_text_setting_list = list()
    cover_pic_text_setting_tuple_list = cover_pic_text_setting.get_record(cover_pic_text_setting_tuple, fetchall=True)
    for text_setting in cover_pic_text_setting_tuple_list:
      cover_text_setting_list.append(get_dict_attr(text_setting, "$.text_setting"))
  except Exception as e:
    get_logger().error(f"{e}: {cover_pic_text_setting.get_name()} >> >> >> data.room.cover")
    cover_text_setting_list = []

  """
  >> >> >> >> data.room.cover.url_list
  """
  cover_picture_url       = PictureUrlTable(db)
  cover_picture_url_tuple = {key: None for key in cover_picture_url.get_tuple()}
  
  set_dict_attr(cover_picture_url_tuple, "$.uri",        cover_picture_tuple.get('uri', ''))
  set_dict_attr(cover_picture_url_tuple, "$.platform",   'douyin')
  set_dict_attr(cover_picture_url_tuple, "$.start_time", start_time)
  set_dict_attr(cover_picture_url_tuple, "$.room_id",    str(room_id))
  set_dict_attr(cover_picture_url_tuple, "$.label",      'cover')
  
  try:
    cover_url_list = list()
    cover_picture_url_tuple_list = cover_picture_url.get_record(cover_picture_url_tuple, fetchall=True)
    for url in cover_picture_url_tuple_list:
      cover_url_list.append(get_dict_attr(url, "$.url"))
  except Exception as e:
    get_logger().error(f"{e}: {cover_picture_url.get_name()} >> >> >> >> data.room.cover.url_list")
    cover_url_list = []

  """
  >> >> >> data.room.deco_list
  """
  room_deco_list = list()
  room_deco_dict = dict()
  room_deco_table = RoomDecoTable(db)
  room_deco_tuple = {key:None for key in room_deco_table.get_tuple()}
  
  set_dict_attr(room_deco_tuple, "$.start_time",      start_time)
  set_dict_attr(room_deco_tuple, "$.platform",        platform)
  set_dict_attr(room_deco_tuple, "$.room_id",         str(room_id))

  room_deco_input_rect_table = RoomDecoInputRectTable(db)
  room_deco_input_rect_tuple = {key:None for key in room_deco_input_rect_table.get_tuple()}

  room_deco_reservation_table = RoomDecoReservationTable(db)
  room_deco_reservation_tuple = {key:None for key in room_deco_reservation_table.get_tuple()}

  room_deco_text_foot_config_table = RoomDecoTextFootConfigTable(db)
  room_deco_text_foot_config_tuple = {key:None for key in room_deco_text_foot_config_table.get_tuple()}

  try:
    ##
    ## RoomDecoTable
    ##
    room_deco_tuple_list = room_deco_table.get_record(room_deco_tuple, fetchall=True)
    room_deco_list                  = list()
    room_deco_input_rect_list       = list()
    room_deco_reservation_list      = list()
    room_deco_text_foot_config_list = list()
    for room_deco in room_deco_tuple_list:
      deco_index = get_dict_attr(room_deco, "$.deco_index")
      set_dict_attr(room_deco_dict, "$.audit_text_color",                     get_dict_attr(room_deco, "$.audit_text_color"))
      set_dict_attr(room_deco_dict, "$.content",                              get_dict_attr(room_deco, "$.content"))
      set_dict_attr(room_deco_dict, "$.h",                                    get_dict_attr(room_deco, "$.h"))
      set_dict_attr(room_deco_dict, "$.id",                                   get_dict_attr(room_deco, "$.id"))
      set_dict_attr(room_deco_dict, "$.kind",                                 get_dict_attr(room_deco, "$.kind"))
      set_dict_attr(room_deco_dict, "$.max_length",                           get_dict_attr(room_deco, "$.max_length"))
      set_dict_attr(room_deco_dict, "$.status",                               get_dict_attr(room_deco, "$.status"))
      set_dict_attr(room_deco_dict, "$.sub_type",                             get_dict_attr(room_deco, "$.sub_type"))
      set_dict_attr(room_deco_dict, "$.text_color",                           get_dict_attr(room_deco, "$.text_color"))
      set_dict_attr(room_deco_dict, "$.text_image_adjustable_end_position",   get_dict_attr(room_deco, "$.text_image_adjustable_end_position"))
      set_dict_attr(room_deco_dict, "$.text_image_adjustable_start_position", get_dict_attr(room_deco, "$.text_image_adjustable_start_position"))
      set_dict_attr(room_deco_dict, "$.text_size",                            get_dict_attr(room_deco, "$.text_size"))
      set_dict_attr(room_deco_dict, "$.type",                                 get_dict_attr(room_deco, "$.type"))
      set_dict_attr(room_deco_dict, "$.w",                                    get_dict_attr(room_deco, "$.w"))
      set_dict_attr(room_deco_dict, "$.x",                                    get_dict_attr(room_deco, "$.x"))
      set_dict_attr(room_deco_dict, "$.y",                                    get_dict_attr(room_deco, "$.y"))
      room_deco_list.insert(deco_index, room_deco_dict)
 
      ##
      ## RoomDecoInputRectTable
      ##
      set_dict_attr(room_deco_input_rect_tuple, "$.start_time", start_time)
      set_dict_attr(room_deco_input_rect_tuple, "$.platform",   platform)
      set_dict_attr(room_deco_input_rect_tuple, "$.room_id",    str(room_id))
      set_dict_attr(room_deco_input_rect_tuple, "$.deco_index", deco_index)
      
      try:
        deco_input_list = list()
        room_deco_input_rect_tuple_list = room_deco_input_rect_table.get_record(room_deco_input_rect_tuple, fetchall=True)
        # deco_input_list = [None] * len(room_deco_input_rect_tuple_list)
        for room_deco_input_rect in room_deco_input_rect_tuple_list:
          input_rect       = get_dict_attr(room_deco_input_rect, "$.input_rect")
          input_rect_index = get_dict_attr(room_deco_input_rect, "$.input_rect_index")
          deco_input_list.insert(input_rect_index, input_rect)
        room_deco_input_rect_list.insert(deco_index, deco_input_list)
      except Exception as e:
        get_logger().error(f"{e}: {room_deco_input_rect_table.get_name()} >> >> >> >> data.room.deco_list.input_rect")
        room_deco_input_rect_list = []
      
      ##
      ## RoomDecoReservationTable
      ##
      set_dict_attr(room_deco_reservation_tuple, "$.start_time", start_time)
      set_dict_attr(room_deco_reservation_tuple, "$.platform",   platform)
      set_dict_attr(room_deco_reservation_tuple, "$.room_id",    str(room_id))
      set_dict_attr(room_deco_reservation_tuple, "$.deco_index", deco_index)
      
      try:
        room_deco_reservation = dict()
        room_deco_reservation_tuple_list = room_deco_reservation_table.get_record(room_deco_reservation_tuple)
        if len(room_deco_reservation_tuple_list) != 0:
          room_deco_reservation_tuple = room_deco_reservation_tuple_list.pop()
          set_dict_attr(room_deco_reservation, "$.anchor_id",      get_dict_attr(room_deco_reservation_tuple, "$.anchor_id"),              force=True)
          set_dict_attr(room_deco_reservation, "$.anchor_open_id", get_dict_attr(room_deco_reservation_tuple, "$.anchor_open_id"),         force=True)
          set_dict_attr(room_deco_reservation, "$.appointment_id", get_dict_attr(room_deco_reservation_tuple, "$.appointment_id"),         force=True)
          set_dict_attr(room_deco_reservation, "$.btn_color",      get_dict_attr(room_deco_reservation_tuple, "$.btn_color"),              force=True)
          set_dict_attr(room_deco_reservation, "$.end_time",       get_dict_attr(room_deco_reservation_tuple, "$.reservation_end_time"),   force=True)
          set_dict_attr(room_deco_reservation, "$.is_reserved",    get_dict_attr(room_deco_reservation_tuple, "$.is_reserved"),            force=True)
          set_dict_attr(room_deco_reservation, "$.room_id",        get_dict_attr(room_deco_reservation_tuple, "$.reservation_room_id"),    force=True)
          set_dict_attr(room_deco_reservation, "$.start_time",     get_dict_attr(room_deco_reservation_tuple, "$.reservation_start_time"), force=True)
          room_deco_reservation_list.insert(deco_index, room_deco_reservation)          
      except Exception as e:
        get_logger().error(f"{e}: {room_deco_reservation_table.get_name()} >> >> >> >> data.room.deco_list.reservation")
        room_deco_reservation_list = []

      ##
      ## RoomDecoTextFootConfigTable
      ##
      set_dict_attr(room_deco_text_foot_config_tuple, "$.start_time", start_time)
      set_dict_attr(room_deco_text_foot_config_tuple, "$.platform",   platform)
      set_dict_attr(room_deco_text_foot_config_tuple, "$.room_id",    str(room_id))
      set_dict_attr(room_deco_text_foot_config_tuple, "$.deco_index", deco_index)
      
      try:
        room_deco_text_foot_config = dict()
        room_deco_text_foot_config_tuple_list = room_deco_text_foot_config_table.get_record(room_deco_text_foot_config_tuple, fetchall=True)
        if len(room_deco_text_foot_config_tuple_list) != 0:
          room_deco_text_foot_config_tuple = room_deco_text_foot_config_tuple_list.pop()
          set_dict_attr(room_deco_text_foot_config, "$.DownloadUrl", get_dict_attr(room_deco_text_foot_config_tuple, "$.DownloadUrl"), force=True)
          set_dict_attr(room_deco_text_foot_config, "$.FontID",      get_dict_attr(room_deco_text_foot_config_tuple, "$.FontID"),      force=True)
          set_dict_attr(room_deco_text_foot_config, "$.Status",      get_dict_attr(room_deco_text_foot_config_tuple, "$.Status"),      force=True)
          set_dict_attr(room_deco_text_foot_config, "$.font_name",   get_dict_attr(room_deco_text_foot_config_tuple, "$.font_name"),   force=True)
          room_deco_text_foot_config_list.insert(deco_index, room_deco_text_foot_config)
      except Exception as e:
        get_logger().error(f"{e}: {room_deco_text_foot_config_table.get_name()} >> >> >> >> data.room.deco_list.text_font_config")
        room_deco_text_foot_config_list = []

    ##
    ## TODO
    ## RoomDecoReservationBtnRectTable
    ##
    room_deco_reservation_btn_rect_list = [None] * len(room_deco_list)
    
    ##
    ## TODO: text_special_effects
    ##
    room_deco_text_special_effects = [None] * len(room_deco_list)
  except Exception as e:
    get_logger().error(f"{e}: {room_deco_table.get_name()} >> >> >> data.room.deco_list")
    room_deco_list = []
  
  if len(room_deco_list) != 0:
    """
    >> >> >> >> >> data.room.deco_list.[x].image
    """
    deco_image_avg_color_list    = list()
    deco_image_flex_setting_list = list()
    deco_image_height_list       = list()
    deco_image_image_type_list   = list()
    deco_image_is_animated_list  = list()
    deco_image_open_web_url_list = list()
    deco_image_text_setting_list = list()
    deco_image_uri_list          = list()
    deco_image_url_list          = list()
    deco_image_width_list        = list()
    
    ##
    ## PictureTable
    ##
    deco_image_exist_list = list()
    image_prefix   = 'image'
    deco_image_pic = PictureTable(db)
    deco_image_pic_tuple = {key: None for key in deco_image_pic.get_tuple()}
    
    set_dict_attr(deco_image_pic_tuple, "$.start_time",  start_time)
    set_dict_attr(deco_image_pic_tuple, "$.platform",    platform)
    set_dict_attr(deco_image_pic_tuple, "$.room_id",     str(room_id))
  
    try:
      deco_image_pic_tuple_list = deco_image_pic.get_record(deco_image_pic_tuple, fetchall=True)
      for deco_image_pic_tuple in deco_image_pic_tuple_list:
        deco_image_pic_label = deco_image_pic_tuple.get('label', 'unknown')
        if str(deco_image_pic_label).startswith(image_prefix):
          deco_index = int(deco_image_pic_label[len(image_prefix):])

          deco_image_avg_color_list.insert(deco_index, deco_image_pic_tuple.get("avg_color", ''))
          deco_image_height_list.insert(deco_index, deco_image_pic_tuple.get("height", 0))
          deco_image_image_type_list.insert(deco_index, deco_image_pic_tuple.get("image_type", 0))
          deco_image_is_animated_list.insert(deco_index, bool(deco_image_pic_tuple.get("is_animated", False)))
          deco_image_open_web_url_list.insert(deco_index, deco_image_pic_tuple.get("open_web_url", ''))
          deco_image_uri_list.insert(deco_index, deco_image_pic_tuple.get("uri", ''))
          deco_image_width_list.insert(deco_index, deco_image_pic_tuple.get("width", 0))
          deco_image_exist_list.insert(deco_index, True)
    except Exception as e:
      get_logger().error(f"{e}: {room_deco_table.get_name()} >> >> >> >> data.room.deco_list[{deco_index}].image")
      deco_image_avg_color_list.insert(deco_index, '')
      deco_image_height_list.insert(deco_index, 0)
      deco_image_image_type_list.insert(deco_index, 0)
      deco_image_is_animated_list.insert(deco_index, False)
      deco_image_open_web_url_list.insert(deco_index, '')
      deco_image_uri_list.insert(deco_index, '')
      deco_image_width_list.insert(deco_index, 0)
      deco_image_exist_list.insert(deco_index, False)
  
    for deco_index in range(0, len(room_deco_list)):
      if deco_image_exist_list[deco_index] is True:
        ##
        ## PictureFlexSettingTable
        ##
        deco_image_pic_flex_setting = PictureFlexSettingTable(db)
        deco_image_pic_flex_setting_tuple = {key: None for key in deco_image_pic_flex_setting.get_tuple()}
        
        set_dict_attr(deco_image_pic_flex_setting_tuple, "$.uri",        deco_image_uri_list[deco_index])
        set_dict_attr(deco_image_pic_flex_setting_tuple, "$.platform",   'douyin')
        set_dict_attr(deco_image_pic_flex_setting_tuple, "$.start_time", start_time)
        set_dict_attr(deco_image_pic_flex_setting_tuple, "$.room_id",    str(room_id))
        set_dict_attr(deco_image_pic_flex_setting_tuple, "$.label",      'image' + str(deco_index))
        
        try:
          deco_image_flex_setting = list()
          deco_image_pic_flex_setting_tuple_list = deco_image_pic_flex_setting.get_record(deco_image_pic_flex_setting_tuple, fetchall=True)
          for flex_setting in deco_image_pic_flex_setting_tuple_list:
            deco_image_flex_setting.append(get_dict_attr(flex_setting, "$.flex_setting"))
        except Exception as e:
          get_logger().error(f"{e}: {deco_image_pic_flex_setting.get_name()} >> >> >> >> >> data.room.deco_list[{deco_index}].image.flex_setting_list")
          deco_image_flex_setting = []
        finally:
          deco_image_flex_setting_list.insert(deco_index, deco_image_flex_setting)
    
        ##
        ## PictureTextSettingTable
        ##    
        deco_image_pic_text_setting = PictureTextSettingTable(db)
        deco_image_pic_text_setting_tuple = {key: None for key in deco_image_pic_text_setting.get_tuple()}
        
        set_dict_attr(deco_image_pic_text_setting_tuple, "$.uri",        deco_image_uri_list[deco_index])
        set_dict_attr(deco_image_pic_text_setting_tuple, "$.platform",   'douyin')
        set_dict_attr(deco_image_pic_text_setting_tuple, "$.start_time", start_time)
        set_dict_attr(deco_image_pic_text_setting_tuple, "$.room_id",    str(room_id))
        set_dict_attr(deco_image_pic_text_setting_tuple, "$.label",      'image' + str(deco_index))
        
        try:
          single_deco_image_pic_text_setting = list()
          deco_image_pic_text_setting_tuple_list = deco_image_pic_text_setting.get_record(deco_image_pic_text_setting_tuple, fetchall=True)
          for text_setting in deco_image_pic_text_setting_tuple_list:
            single_deco_image_pic_text_setting.append(get_dict_attr(text_setting, "$.text_setting"))
        except Exception as e:
          get_logger().error(f"{e}: {deco_image_pic_text_setting.get_name()} >> >> >> >> >> data.room.deco_list[{deco_index}].image.text_setting_list")
          single_deco_image_pic_text_setting = []
        finally:
          deco_image_text_setting_list.insert(deco_index, single_deco_image_pic_text_setting)
  
        ##
        ## PictureUrlTable
        ##
        deco_image_picture_url       = PictureUrlTable(db)
        deco_image_picture_url_tuple = {key: None for key in deco_image_picture_url.get_tuple()}
        
        set_dict_attr(deco_image_picture_url_tuple, "$.uri",        deco_image_uri_list[deco_index])
        set_dict_attr(deco_image_picture_url_tuple, "$.platform",   'douyin')
        set_dict_attr(deco_image_picture_url_tuple, "$.start_time", start_time)
        set_dict_attr(deco_image_picture_url_tuple, "$.room_id",    str(room_id))
        set_dict_attr(deco_image_picture_url_tuple, "$.label",      'image' + str(deco_index))
        
        try:
          deco_image_pic_url_list = list()
          deco_image_picture_url_tuple_list = deco_image_picture_url.get_record(deco_image_picture_url_tuple, fetchall=True)
          for url in deco_image_picture_url_tuple_list:
            deco_image_pic_url_list.append(get_dict_attr(url, "$.url"))
        except Exception as e:
          get_logger().error(f"{e}: {deco_image_picture_url.get_name()} >> >> >> >> >> data.room.deco_list[{deco_index}].image.url_list")
          deco_image_pic_url_list = []
        finally:
          deco_image_url_list.insert(deco_index, deco_image_pic_url_list)
  
    """
    >> >> >> data.room.deco_list.[x].nine_patch_image
    """
    deco_nine_patch_image_avg_color_list    = list() # [None] * len(room_deco_list)
    deco_nine_patch_image_flex_setting_list = list() # [None] * len(room_deco_list)
    deco_nine_patch_image_height_list       = list() # [None] * len(room_deco_list)
    deco_nine_patch_image_image_type_list   = list() # [None] * len(room_deco_list)
    deco_nine_patch_image_is_animated_list  = list() # [None] * len(room_deco_list)
    deco_nine_patch_image_open_web_url_list = list() # [None] * len(room_deco_list)
    deco_nine_patch_image_text_setting_list = list() # [None] * len(room_deco_list)
    deco_nine_patch_image_uri_list          = list() # [None] * len(room_deco_list)
    deco_nine_patch_image_url_list          = list() # [None] * len(room_deco_list)
    deco_nine_patch_image_width_list        = list() # [None] * len(room_deco_list)
    
    ##
    ## PictureTable
    ##
    nine_patch_image_exist_list = [None for _ in room_deco_list]
    image_prefix           = 'nine_patch_image'
    deco_nine_patch_image_pic = PictureTable(db)
    deco_nine_patch_image_pic_tuple = {key: None for key in deco_nine_patch_image_pic.get_tuple()}
    
    set_dict_attr(deco_nine_patch_image_pic_tuple, "$.start_time",  start_time)
    set_dict_attr(deco_nine_patch_image_pic_tuple, "$.platform",    platform)
    set_dict_attr(deco_nine_patch_image_pic_tuple, "$.room_id",     str(room_id))
  
    try:
      deco_nine_patch_image_pic_tuple_list = deco_nine_patch_image_pic.get_record(deco_nine_patch_image_pic_tuple, fetchall=True)
      for deco_nine_patch_image_pic_tuple in deco_nine_patch_image_pic_tuple_list:
        deco_nine_patch_image_pic_label = deco_nine_patch_image_pic_tuple.get('label', 'unknown')
        if str(deco_nine_patch_image_pic_label).startswith(image_prefix):
          deco_index = int(deco_nine_patch_image_pic_label[len(image_prefix):])

          deco_nine_patch_image_avg_color_list.insert(deco_index, deco_nine_patch_image_pic_tuple.get("avg_color", ''))
          deco_nine_patch_image_height_list.insert(deco_index, deco_nine_patch_image_pic_tuple.get("height", 0))
          deco_nine_patch_image_image_type_list.insert(deco_index, deco_nine_patch_image_pic_tuple.get("image_type", 0))
          deco_nine_patch_image_is_animated_list.insert(deco_index, bool(deco_nine_patch_image_pic_tuple.get("is_animated", False)))
          deco_nine_patch_image_open_web_url_list.insert(deco_index, deco_nine_patch_image_pic_tuple.get("open_web_url", ''))
          deco_nine_patch_image_uri_list.insert(deco_index, deco_nine_patch_image_pic_tuple.get("uri", ''))
          deco_nine_patch_image_width_list.insert(deco_index, deco_nine_patch_image_pic_tuple.get("width", 0))
          nine_patch_image_exist_list[deco_index] = True
    except Exception as e:
      get_logger().error(f"{e}: {room_deco_table.get_name()} >> >> >> >> data.room.deco_list[{deco_index}].image")
      deco_nine_patch_image_avg_color_list.insert(deco_index, '')
      deco_nine_patch_image_height_list.insert(deco_index, 0)
      deco_nine_patch_image_image_type_list.insert(deco_index, 0)
      deco_nine_patch_image_is_animated_list.insert(deco_index, False)
      deco_nine_patch_image_open_web_url_list.insert(deco_index, '')
      deco_nine_patch_image_uri_list.insert(deco_index, '')
      deco_nine_patch_image_width_list.insert(deco_index, 0)
      nine_patch_image_exist_list[deco_index] = None

    print(f"nine_patch_image_exist_list: {nine_patch_image_exist_list}")
    for deco_index in range(0, len(room_deco_list)):
      if len(nine_patch_image_exist_list) != 0 and nine_patch_image_exist_list[deco_index] is True:
        ##
        ## PictureFlexSettingTable
        ##
        deco_nine_patch_image_pic_flex_setting = PictureFlexSettingTable(db)
        deco_nine_patch_image_pic_flex_setting_tuple = {key: None for key in deco_nine_patch_image_pic_flex_setting.get_tuple()}

        print(f"len(room_deco_list): {len(room_deco_list)}")
        print(f"len(deco_nine_patch_image_uri_list): {len(deco_nine_patch_image_uri_list)}")
        set_dict_attr(deco_nine_patch_image_pic_flex_setting_tuple, "$.uri",        deco_nine_patch_image_uri_list[deco_index])
        set_dict_attr(deco_nine_patch_image_pic_flex_setting_tuple, "$.platform",   'douyin')
        set_dict_attr(deco_nine_patch_image_pic_flex_setting_tuple, "$.start_time", start_time)
        set_dict_attr(deco_nine_patch_image_pic_flex_setting_tuple, "$.room_id",    str(room_id))
        set_dict_attr(deco_nine_patch_image_pic_flex_setting_tuple, "$.label",      'nine_patch_image' + str(deco_index))

        try:
          deco_nine_patch_image_flex_setting = list()
          deco_nine_patch_image_pic_flex_setting_tuple_list = deco_nine_patch_image_pic_flex_setting.get_record(deco_nine_patch_image_pic_flex_setting_tuple, fetchall=True)
          for flex_setting in deco_nine_patch_image_pic_flex_setting_tuple_list:
            deco_nine_patch_image_flex_setting.append(get_dict_attr(flex_setting, "$.flex_setting"))
        except Exception as e:
          get_logger().error(f"{e}: {deco_nine_patch_image_pic_flex_setting.get_name()} >> >> >> >> >> data.room.deco_list[{deco_index}].image.flex_setting_list")
          deco_nine_patch_image_flex_setting = []
        finally:
          deco_nine_patch_image_flex_setting_list.insert(deco_index, deco_nine_patch_image_flex_setting)

        ##
        ## PictureTextSettingTable
        ##    
        deco_nine_patch_image_pic_text_setting = PictureTextSettingTable(db)
        deco_nine_patch_image_pic_text_setting_tuple = {key: None for key in deco_nine_patch_image_pic_text_setting.get_tuple()}

        set_dict_attr(deco_nine_patch_image_pic_text_setting_tuple, "$.uri",        deco_nine_patch_image_uri_list[deco_index])
        set_dict_attr(deco_nine_patch_image_pic_text_setting_tuple, "$.platform",   'douyin')
        set_dict_attr(deco_nine_patch_image_pic_text_setting_tuple, "$.start_time", start_time)
        set_dict_attr(deco_nine_patch_image_pic_text_setting_tuple, "$.room_id",    str(room_id))
        set_dict_attr(deco_nine_patch_image_pic_text_setting_tuple, "$.label",      'nine_patch_image' + str(deco_index))

        try:
          single_deco_nine_patch_image_pic_text_setting = list()
          deco_nine_patch_image_pic_text_setting_tuple_list = deco_nine_patch_image_pic_text_setting.get_record(deco_nine_patch_image_pic_text_setting_tuple, fetchall=True)
          for text_setting in deco_nine_patch_image_pic_text_setting_tuple_list:
            single_deco_nine_patch_image_pic_text_setting.append(get_dict_attr(text_setting, "$.text_setting"))
        except Exception as e:
          get_logger().error(f"{e}: {deco_nine_patch_image_pic_text_setting.get_name()} >> >> >> >> >> data.room.deco_list[{deco_index}].image.text_setting_list")
          single_deco_nine_patch_image_pic_text_setting = []
        finally:
          deco_nine_patch_image_text_setting_list.insert(deco_index, single_deco_nine_patch_image_pic_text_setting)

        ##
        ## PictureUrlTable
        ##
        deco_nine_patch_image_picture_url       = PictureUrlTable(db)
        deco_nine_patch_image_picture_url_tuple = {key: None for key in deco_nine_patch_image_picture_url.get_tuple()}

        set_dict_attr(deco_nine_patch_image_picture_url_tuple, "$.uri",        deco_nine_patch_image_uri_list[deco_index])
        set_dict_attr(deco_nine_patch_image_picture_url_tuple, "$.platform",   'douyin')
        set_dict_attr(deco_nine_patch_image_picture_url_tuple, "$.start_time", start_time)
        set_dict_attr(deco_nine_patch_image_picture_url_tuple, "$.room_id",    str(room_id))
        set_dict_attr(deco_nine_patch_image_picture_url_tuple, "$.label",      'nine_patch_image' + str(deco_index))

        try:
          deco_nine_patch_image_pic_url_list = list()
          deco_nine_patch_image_picture_url_tuple_list = deco_nine_patch_image_picture_url.get_record(deco_nine_patch_image_picture_url_tuple, fetchall=True)
          for url in deco_nine_patch_image_picture_url_tuple_list:
            deco_nine_patch_image_pic_url_list.append(get_dict_attr(url, "$.url"))
        except Exception as e:
          get_logger().error(f"{e}: {deco_nine_patch_image_picture_url.get_name()} >> >> >> >> >> data.room.deco_list[{deco_index}].image.url_list")
          deco_nine_patch_image_pic_url_list = []
        finally:
          deco_nine_patch_image_url_list.insert(deco_index, deco_nine_patch_image_pic_url_list)

  """
  TODO
  >> >> >> data.room.extra.realtime_playback_qualities
  """
  realtime_playback_qualities = list()

  """
  >> >> >> data.room.fans_group_admin_user_ids
  """
  fans_group_admin_user_id = FansGroupAdminUserIdTable(db)
  fans_group_admin_user_id_tuple = {key: None for key in fans_group_admin_user_id.get_tuple()}
  
  set_dict_attr(fans_group_admin_user_id_tuple, "$.now",      now)
  set_dict_attr(fans_group_admin_user_id_tuple, "$.platform", platform)
  set_dict_attr(fans_group_admin_user_id_tuple, "$.room_id",  str(room_id))
  
  try:
    fans_group_admin_user_ids = list()
    fans_group_admin_user_id_tuple_list = fans_group_admin_user_id.get_record(fans_group_admin_user_id_tuple, fetchall=True)
    for fans_group_admin_user_id_tuple in fans_group_admin_user_id_tuple_list:
      fans_group_admin_user_ids.append(get_dict_attr(fans_group_admin_user_id_tuple, "$.fans_group_admin_user_id"))
  except Exception as e:
    get_logger().error(f"{e}: {fans_group_admin_user_id.get_name()} >> >> >> data.room.fans_group_admin_user_ids")
    fans_group_admin_user_ids = []

  """
  >> >> >> data.room.fans_group_admin_user_open_ids
  """
  fans_group_admin_user_open_id = FansGroupAdminUserOpenIdTable(db)
  fans_group_admin_user_open_id_tuple = {key: None for key in fans_group_admin_user_open_id.get_tuple()}
  
  set_dict_attr(fans_group_admin_user_open_id_tuple, "$.now",      now)
  set_dict_attr(fans_group_admin_user_open_id_tuple, "$.platform", platform)
  set_dict_attr(fans_group_admin_user_open_id_tuple, "$.room_id",  str(room_id))
  
  try:
    fans_group_admin_user_open_ids = list()
    fans_group_admin_user_open_id_tuple_list = fans_group_admin_user_open_id.get_record(fans_group_admin_user_open_id_tuple)
    for fans_group_admin_user_open_id_tuple in fans_group_admin_user_open_id_tuple_list:
      fans_group_admin_user_open_ids.append(get_dict_attr(fans_group_admin_user_open_id_tuple, "$.fans_group_admin_user_id"))
  except Exception as e:
    get_logger().error(f"{e}: {fans_group_admin_user_open_id.get_name()} >> >> >> data.room.fans_group_admin_user_open_ids")
    fans_group_admin_user_open_ids = []

  """
  >> >> data.room.content_label
  """
  content_label = dict()

  ##
  ## PictureTable
  ##
  content_label_picture       = PictureTable(db)
  content_label_picture_tuple = {key: None for key in content_label_picture.get_tuple()}

  set_dict_attr(content_label_picture_tuple, "$.start_time",  start_time)
  set_dict_attr(content_label_picture_tuple, "$.platform",    platform)
  set_dict_attr(content_label_picture_tuple, "$.room_id",     str(room_id))
  set_dict_attr(content_label_picture_tuple, "$.label",       'content_label')

  try:
    content_label_picture_tuple_list = content_label_picture.get_record(content_label_picture_tuple)
    if len(content_label_picture_tuple_list) != 0:
      content_label_picture_tuple = content_label_picture_tuple_list.pop()
    else:
      content_label_picture_tuple = {}
  except Exception as e:
    get_logger().error(f"{e}: {content_label_picture.get_name()} >> >> data.room.content_label")
    content_label_picture_tuple = {}
  
  ##
  ## PictureContentTable
  ##
  content_label_picture_content       = PictureContentTable(db)
  content_label_picture_content_tuple = {key: None for key in content_label_picture_content.get_tuple()}
  
  set_dict_attr(content_label_picture_content_tuple, "$.uri",         content_label_picture_tuple.get('uri', ''))
  set_dict_attr(content_label_picture_content_tuple, "$.start_time",  start_time)
  set_dict_attr(content_label_picture_content_tuple, "$.platform",    platform)
  set_dict_attr(content_label_picture_content_tuple, "$.room_id",     str(room_id))
  set_dict_attr(content_label_picture_content_tuple, "$.label",       'content_label')
  
  try:
    content_label_picture_content_tuple_list = content_label_picture_content.get_record(content_label_picture_content_tuple)
    if len(content_label_picture_content_tuple_list) != 0:
      content_label_picture_content_tuple = content_label_picture_content_tuple_list.pop()
  except Exception as e:
    get_logger().error(f"{e}: {content_label_picture_content.get_name()} >> >> data.room.content_label")
    content_label_picture_content_tuple = {}

  ##
  ## PictureFlexSettingTable
  ##
  content_label_pic_flex_setting = PictureFlexSettingTable(db)
  content_label_pic_flex_setting_tuple = {key: None for key in content_label_pic_flex_setting.get_tuple()}
  
  set_dict_attr(content_label_pic_flex_setting_tuple, "$.uri",        content_label_picture_tuple.get('uri', ''))
  set_dict_attr(content_label_pic_flex_setting_tuple, "$.platform",   'douyin')
  set_dict_attr(content_label_pic_flex_setting_tuple, "$.start_time", start_time)
  set_dict_attr(content_label_pic_flex_setting_tuple, "$.room_id",    str(room_id))
  set_dict_attr(content_label_pic_flex_setting_tuple, "$.label",       'content_label')
  
  try:
    content_label_flex_setting_list = list()
    content_label_pic_flex_setting_tuple_list = content_label_pic_flex_setting.get_record(content_label_pic_flex_setting_tuple, fetchall=True)
    for flex_setting in content_label_pic_flex_setting_tuple_list:
      content_label_flex_setting_list.append(get_dict_attr(flex_setting, "$.flex_setting"))
  except Exception as e:
    get_logger().error(f"{e}: {content_label_pic_flex_setting.get_name()} >> >> data.room.content_label")
    content_label_flex_setting_list = []
  
  ##
  ## PictureTextSettingTable
  ##
  content_label_pic_text_setting = PictureTextSettingTable(db)
  content_label_pic_text_setting_tuple = {key: None for key in content_label_pic_text_setting.get_tuple()}
  
  set_dict_attr(content_label_pic_text_setting_tuple, "$.uri",         content_label_picture_tuple.get('uri', ''))
  set_dict_attr(content_label_pic_text_setting_tuple, "$.platform",    'douyin')
  set_dict_attr(content_label_pic_text_setting_tuple, "$.start_time",  start_time)
  set_dict_attr(content_label_pic_text_setting_tuple, "$.room_id",     str(room_id))
  set_dict_attr(content_label_pic_text_setting_tuple, "$.label",       'content_label')
  
  try:
    content_label_text_setting_list = list()
    content_label_pic_text_setting_tuple_list = content_label_pic_text_setting.get_record(content_label_pic_text_setting_tuple, fetchall=True)
    for text_setting in content_label_pic_text_setting_tuple_list:
      content_label_text_setting_list.append(get_dict_attr(text_setting, "$.text_setting"))
  except Exception as e:
    get_logger().error(f"{e}: {content_label_pic_text_setting.get_name()} >> >> >> >> data.room.content_label.text_setting_list")
    content_label_text_setting_list = []

  ##
  ## $.data.room.content_label.url_list
  ## PictureUrlTable
  ##
  content_label_picture_url       = PictureUrlTable(db)
  content_label_picture_url_tuple = {key: None for key in content_label_picture_url.get_tuple()}
  
  set_dict_attr(content_label_picture_url_tuple, "$.uri",         content_label_picture_tuple.get('uri', ''))
  set_dict_attr(content_label_picture_url_tuple, "$.platform",    'douyin')
  set_dict_attr(content_label_picture_url_tuple, "$.start_time",  start_time)
  set_dict_attr(content_label_picture_url_tuple, "$.room_id",     str(room_id))
  set_dict_attr(content_label_picture_url_tuple, "$.label",       'content_label')
  
  try:
    content_label_url_list = list()
    content_label_picture_url_tuple_list = content_label_picture_url.get_record(content_label_picture_url_tuple, fetchall=True)
    for url in content_label_picture_url_tuple_list:
      content_label_url_list.append(get_dict_attr(url, "$.url"))
  except Exception as e:
    get_logger().error(f"{e}: {content_label_picture_url.get_name()} >> >> >> >> data.room.content_label.url_list")
    content_label_url_list = []

  """
  >> >> data.room.feed_room_label
  """
  feed_room_label = dict()

  ##
  ## PictureTable
  ##
  feed_room_label_picture       = PictureTable(db)
  feed_room_label_picture_tuple = {key: None for key in feed_room_label_picture.get_tuple()}

  set_dict_attr(feed_room_label_picture_tuple, "$.start_time",  start_time)
  set_dict_attr(feed_room_label_picture_tuple, "$.platform",    platform)
  set_dict_attr(feed_room_label_picture_tuple, "$.room_id",     str(room_id))
  set_dict_attr(feed_room_label_picture_tuple, "$.label",       'feed_room_label')

  try:
    feed_room_label_picture_tuple_list = feed_room_label_picture.get_record(feed_room_label_picture_tuple)
    if len(feed_room_label_picture_tuple_list) != 0:
      feed_room_label_picture_tuple = feed_room_label_picture_tuple_list.pop()
  except Exception as e:
    get_logger().error(f"{e}: {feed_room_label_picture.get_name()} >> >> data.room.feed_room_label")
    feed_room_label_picture_tuple = dict()
  
  ##
  ## PictureContentTable
  ##
  feed_room_label_picture_content       = PictureContentTable(db)
  feed_room_label_picture_content_tuple = {key: None for key in feed_room_label_picture_content.get_tuple()}
  
  set_dict_attr(feed_room_label_picture_content_tuple, "$.uri",         feed_room_label_picture_tuple.get('uri', ''))
  set_dict_attr(feed_room_label_picture_content_tuple, "$.start_time",  start_time)
  set_dict_attr(feed_room_label_picture_content_tuple, "$.platform",    platform)
  set_dict_attr(feed_room_label_picture_content_tuple, "$.room_id",     str(room_id))
  set_dict_attr(feed_room_label_picture_content_tuple, "$.label",       'feed_room_label')
  
  try:
    feed_room_label_picture_content_tuple_list = feed_room_label_picture_content.get_record(feed_room_label_picture_content_tuple)
    if len(feed_room_label_picture_content_tuple_list) != 0:
      feed_room_label_picture_content_tuple = feed_room_label_picture_content_tuple_list.pop()
  except Exception as e:
    get_logger().error(f"{e}: {feed_room_label_picture_content.get_name()} >> >> data.room.feed_room_label")
    feed_room_label_picture_content_tuple = {}

  ##
  ## PictureFlexSettingTable
  ##
  feed_room_label_pic_flex_setting = PictureFlexSettingTable(db)
  feed_room_label_pic_flex_setting_tuple = {key: None for key in feed_room_label_pic_flex_setting.get_tuple()}
  
  set_dict_attr(feed_room_label_pic_flex_setting_tuple, "$.uri",        feed_room_label_picture_tuple.get('uri', ''))
  set_dict_attr(feed_room_label_pic_flex_setting_tuple, "$.platform",   'douyin')
  set_dict_attr(feed_room_label_pic_flex_setting_tuple, "$.start_time", start_time)
  set_dict_attr(feed_room_label_pic_flex_setting_tuple, "$.room_id",    str(room_id))
  set_dict_attr(feed_room_label_pic_flex_setting_tuple, "$.label",       'feed_room_label')
  
  try:
    feed_room_label_flex_setting_list = list()
    feed_room_label_pic_flex_setting_tuple_list = feed_room_label_pic_flex_setting.get_record(feed_room_label_pic_flex_setting_tuple, fetchall=True)
    for flex_setting in feed_room_label_pic_flex_setting_tuple_list:
      feed_room_label_flex_setting_list.append(get_dict_attr(flex_setting, "$.flex_setting"))
  except Exception as e:
    get_logger().error(f"{e}: {feed_room_label_pic_flex_setting.get_name()} >> >> data.room.feed_room_label")
    feed_room_label_flex_setting_list = []
  
  ##
  ## PictureTextSettingTable
  ##
  feed_room_label_pic_text_setting = PictureTextSettingTable(db)
  feed_room_label_pic_text_setting_tuple = {key: None for key in feed_room_label_pic_text_setting.get_tuple()}
  
  set_dict_attr(feed_room_label_pic_text_setting_tuple, "$.uri",         feed_room_label_picture_tuple.get('uri', ''))
  set_dict_attr(feed_room_label_pic_text_setting_tuple, "$.platform",    'douyin')
  set_dict_attr(feed_room_label_pic_text_setting_tuple, "$.start_time",  start_time)
  set_dict_attr(feed_room_label_pic_text_setting_tuple, "$.room_id",     str(room_id))
  set_dict_attr(feed_room_label_pic_text_setting_tuple, "$.label",       'feed_room_label')
  
  try:
    feed_room_label_text_setting_list = list()
    feed_room_label_pic_text_setting_tuple_list = feed_room_label_pic_text_setting.get_record(feed_room_label_pic_text_setting_tuple, fetchall=True)
    for text_setting in feed_room_label_pic_text_setting_tuple_list:
      feed_room_label_text_setting_list.append(get_dict_attr(text_setting, "$.text_setting"))
  except Exception as e:
    get_logger().error(f"{e}: {feed_room_label_pic_text_setting.get_name()} >> >> >> >> data.room.feed_room_label.text_setting_list")
    feed_room_label_text_setting_list = []

  ##
  ## $.data.room.feed_room_label.url_list
  ## PictureUrlTable
  ##
  feed_room_label_picture_url       = PictureUrlTable(db)
  feed_room_label_picture_url_tuple = {key: None for key in feed_room_label_picture_url.get_tuple()}
  
  set_dict_attr(feed_room_label_picture_url_tuple, "$.uri",         feed_room_label_picture_tuple.get('uri', ''))
  set_dict_attr(feed_room_label_picture_url_tuple, "$.platform",    'douyin')
  set_dict_attr(feed_room_label_picture_url_tuple, "$.start_time",  start_time)
  set_dict_attr(feed_room_label_picture_url_tuple, "$.room_id",     str(room_id))
  set_dict_attr(feed_room_label_picture_url_tuple, "$.label",       'feed_room_label')
  
  try:
    feed_room_label_url_list = list()
    feed_room_label_picture_url_tuple_list = feed_room_label_picture_url.get_record(feed_room_label_picture_url_tuple, fetchall=True)
    for url in feed_room_label_picture_url_tuple_list:
      feed_room_label_url_list.append(get_dict_attr(url, "$.url"))
  except Exception as e:
    get_logger().error(f"{e}: {feed_room_label_picture_url.get_name()} >> >> >> >> data.room.feed_room_label.url_list")
    feed_room_label_url_list = []

  """
  TODO
  >> >> >> data.room.filter_words
  """
  filter_words = list()
  
  """
  >> >> >> data.room.guide_button
  """
  guide_button = dict()
  
  ##
  ## PictureTable
  ##
  guide_button_picture       = PictureTable(db)
  guide_button_picture_tuple = {key: None for key in guide_button_picture.get_tuple()}
  
  set_dict_attr(guide_button_picture_tuple, "$.start_time",  start_time)
  set_dict_attr(guide_button_picture_tuple, "$.platform",    platform)
  set_dict_attr(guide_button_picture_tuple, "$.room_id",     str(room_id))
  set_dict_attr(guide_button_picture_tuple, "$.label",       'guide_button')
  
  try:
    guide_button_picture_tuple_list = guide_button_picture.get_record(guide_button_picture_tuple)
    if len(guide_button_picture_tuple_list) != 0:
      guide_button_picture_tuple = guide_button_picture_tuple_list.pop()
  except Exception as e:
    get_logger().error(f"{e}: {guide_button_picture.get_name()} >> >> >> data.room.guide_button")
    guide_button_picture_tuple = dict()
  
  ##
  ## PictureFlexSettingTable
  ##
  guide_button_pic_flex_setting = PictureFlexSettingTable(db)
  guide_button_pic_flex_setting_tuple = {key: None for key in guide_button_pic_flex_setting.get_tuple()}
  
  set_dict_attr(guide_button_pic_flex_setting_tuple, "$.uri",         guide_button_picture_tuple.get('uri', ''))
  set_dict_attr(guide_button_pic_flex_setting_tuple, "$.platform",    'douyin')
  set_dict_attr(guide_button_pic_flex_setting_tuple, "$.start_time",  start_time)
  set_dict_attr(guide_button_pic_flex_setting_tuple, "$.room_id",     str(room_id))
  set_dict_attr(guide_button_pic_flex_setting_tuple, "$.label",       'guide_button')
  
  try:
    guide_button_flex_setting_list = list()
    guide_button_pic_flex_setting_tuple_list = guide_button_pic_flex_setting.get_record(guide_button_pic_flex_setting_tuple, fetchall=True)
    for flex_setting in guide_button_pic_flex_setting_tuple_list:
      guide_button_flex_setting_list.append(get_dict_attr(flex_setting, "$.flex_setting"))
  except Exception as e:
    get_logger().error(f"{e}: {guide_button_pic_flex_setting.get_name()} >> >> >> >> data.room.guide_button.flex_setting_list")
    guide_button_flex_setting_list = []

  ##
  ## PictureTextSettingTable
  ##
  guide_button_pic_text_setting = PictureTextSettingTable(db)
  guide_button_pic_text_setting_tuple = {key: None for key in guide_button_pic_text_setting.get_tuple()}
  
  set_dict_attr(guide_button_pic_text_setting_tuple, "$.uri",         guide_button_picture_tuple.get('uri', ''))
  set_dict_attr(guide_button_pic_text_setting_tuple, "$.platform",    'douyin')
  set_dict_attr(guide_button_pic_text_setting_tuple, "$.start_time",  start_time)
  set_dict_attr(guide_button_pic_text_setting_tuple, "$.room_id",     str(room_id))
  set_dict_attr(guide_button_pic_text_setting_tuple, "$.label",       'guide_button')
  
  try:
    guide_button_text_setting_list = list()
    guide_button_pic_text_setting_tuple_list = guide_button_pic_text_setting.get_record(guide_button_pic_text_setting_tuple, fetchall=True)
    for text_setting in guide_button_pic_text_setting_tuple_list:
      guide_button_text_setting_list.append(get_dict_attr(text_setting, "$.text_setting"))
  except Exception as e:
    get_logger().error(f"{e}: {guide_button_pic_text_setting.get_name()} >> >> >> >> data.room.guide_button.text_setting_list")
    guide_button_text_setting_list = []
  
  ##
  ## PictureUrlTable
  ##
  guide_button_picture_url       = PictureUrlTable(db)
  guide_button_picture_url_tuple = {key: None for key in guide_button_picture_url.get_tuple()}
  
  set_dict_attr(guide_button_picture_url_tuple, "$.uri",         guide_button_picture_tuple.get('uri', ''))
  set_dict_attr(guide_button_picture_url_tuple, "$.platform",    'douyin')
  set_dict_attr(guide_button_picture_url_tuple, "$.start_time",  start_time)
  set_dict_attr(guide_button_picture_url_tuple, "$.room_id",     str(room_id))
  set_dict_attr(guide_button_picture_url_tuple, "$.label",       'guide_button')
  
  try:
    guide_button_url_list = list()
    guide_button_picture_url_tuple_list = guide_button_picture_url.get_record(guide_button_picture_url_tuple, fetchall=True)
    for url in guide_button_picture_url_tuple_list:
      guide_button_url_list.append(get_dict_attr(url, "$.url"))
  except Exception as e:
    get_logger().error(f"{e}: {guide_button_picture_url.get_name()} >> >> >> >> data.room.guide_button.url_list")
    guide_button_url_list = []

  """
  >> >> >> data.room.link_mic
  """
  room_link_mic_table = RoomLinkMicTable(db)
  room_link_mic_tuple = {key:None for key in room_link_mic_table.get_tuple()}
  
  set_dict_attr(room_link_mic_tuple, "$.now",           now)
  set_dict_attr(room_link_mic_tuple, "$.platform",      platform)
  set_dict_attr(room_link_mic_tuple, "$.room_id",       str(room_id))
  
  try:
    room_link_mic_tuple_list = room_link_mic_table.get_record(room_link_mic_tuple)
    if room_link_mic_tuple_list:
      room_link_mic_tuple = room_link_mic_tuple_list.pop()
    else:
      room_link_mic_tuple = {}
  except Exception as e:
    get_logger().error(f"{e}: {room_link_mic_table.get_name()} >> >> >> data.room.link_mic")
    room_link_mic_tuple = {}
  
  if room_link_mic_tuple:
    room_link_mic_channel_id = get_dict_attr(room_link_mic_tuple, "$.channel_id")
    
    ##
    ## data.room.link_mic.battle_scores
    ##
    room_link_mic_battle_score_table = RoomLinkMicBattleScoreTable(db)
    room_link_mic_battle_score_tuple = {key:None for key in room_link_mic_battle_score_table.get_tuple()}
    
    set_dict_attr(room_link_mic_battle_score_tuple, "$.now",           now)
    set_dict_attr(room_link_mic_battle_score_tuple, "$.platform",      platform)
    set_dict_attr(room_link_mic_battle_score_tuple, "$.room_id",       str(room_id))
    set_dict_attr(room_link_mic_battle_score_tuple, "$.channel_id",    room_link_mic_channel_id)
    
    try:
      room_link_mic_battle_score_list = list()
      room_link_mic_battle_score_tuple_list = room_link_mic_battle_score_table.get_record(room_link_mic_battle_score_tuple, fetchall=True)
      if room_link_mic_battle_score_tuple_list:
        for battle_score_tuple in room_link_mic_battle_score_tuple_list:
          room_link_mic_battle_score_dict = dict()
          battle_score_index = get_dict_attr(battle_score_tuple, "$.battle_score_index")
          set_dict_attr(room_link_mic_battle_score_dict, "$.open_id", get_dict_attr(battle_score_tuple, "$.open_id"),      force=True)
          set_dict_attr(room_link_mic_battle_score_dict, "$.score",   get_dict_attr(battle_score_tuple, "$.score"),        force=True)
          set_dict_attr(room_link_mic_battle_score_dict, "$.user_id", int(get_dict_attr(battle_score_tuple, "$.user_id")), force=True)
          room_link_mic_battle_score_list.insert(battle_score_index, room_link_mic_battle_score_dict)
      else:
        room_link_mic_battle_score_list = []
    except Exception as e:
      get_logger().error(f"{e}: {room_link_mic_battle_score_table.get_name()} >> >> >> >> data.room.link_mic.battle_scores")
      room_link_mic_battle_score_list = []
    
    ##
    ## data.room.link_mic.battle_settings
    ##
    room_link_mic_battle_setting_table = RoomLinkMicBattleSettingTable(db)
    room_link_mic_battle_setting_tuple = {key:None for key in room_link_mic_battle_setting_table.get_tuple()}
    
    set_dict_attr(room_link_mic_battle_setting_tuple, "$.now",           now)
    set_dict_attr(room_link_mic_battle_setting_tuple, "$.platform",      platform)
    set_dict_attr(room_link_mic_battle_setting_tuple, "$.room_id",       str(room_id))
    set_dict_attr(room_link_mic_battle_setting_tuple, "$.channel_id",    room_link_mic_channel_id)
    
    try:
      room_link_mic_battle_setting_tuple_list = room_link_mic_battle_setting_table.get_record(room_link_mic_battle_setting_tuple)
      if room_link_mic_battle_setting_tuple_list:
        room_link_mic_battle_setting_tuple = room_link_mic_battle_setting_tuple_list.pop()
      else:
        room_link_mic_battle_setting_tuple = {}
    except Exception as e:
      get_logger().error(f"{e}: {room_link_mic_battle_setting_table.get_name()} >> >> >> >> data.room.link_mic.battle_settings")
      room_link_mic_battle_setting_tuple = {}

    ##
    ## data.room.link_mic.channel_info
    ##
    room_link_mic_channel_info_table = RoomLinkMicChannelInfoTable(db)
    room_link_mic_channel_info_tuple = {key:None for key in room_link_mic_channel_info_table.get_tuple()}
    
    set_dict_attr(room_link_mic_channel_info_tuple, "$.now",           now)
    set_dict_attr(room_link_mic_channel_info_tuple, "$.platform",      platform)
    set_dict_attr(room_link_mic_channel_info_tuple, "$.room_id",       str(room_id))
    set_dict_attr(room_link_mic_channel_info_tuple, "$.channel_id",    room_link_mic_channel_id)
    
    try:
      room_link_mic_channel_info_tuple_list = room_link_mic_channel_info_table.get_record(room_link_mic_channel_info_tuple)
      if room_link_mic_channel_info_tuple_list:
        room_link_mic_channel_info_tuple = room_link_mic_channel_info_tuple_list.pop()
      else:
        room_link_mic_channel_info_tuple = {}
    except Exception as e:
      get_logger().error(f"{e}: {room_link_mic_channel_info_table.get_name()} >> >> >> >> data.room.link_mic.channel_info")
      room_link_mic_channel_info_tuple = {}

  """
  TODO
  >> >> >> data.room.live_distribution
  """
  live_distribution = list()

  """
  >> >> >> data.room.owner
  """  
  ##
  ## RoomOwnerTable
  ##
  room_owner_table = RoomOwnerTable(db)
  room_owner_tuple = {key: None for key in room_owner_table.get_tuple()}

  set_dict_attr(room_owner_tuple, "$.now",           now)
  set_dict_attr(room_owner_tuple, "$.platform",      platform)
  set_dict_attr(room_owner_tuple, "$.room_id",       str(room_id))
  set_dict_attr(room_owner_tuple, "$.owner_user_id", owner_user_id)
  
  try:
    room_owner_tuple_list = room_owner_table.get_record(room_owner_tuple)
    if len(room_owner_tuple_list) != 0:
      room_owner_tuple = room_owner_tuple_list.pop()
  except Exception as e:
    get_logger().error(f"{e}: {room_owner_table.get_name()} >> >> >> data.room.owner")
    room_owner_tuple = {}

  """
  >> >> >> >> data.room.owner.author_stats
  """
  room_owner_author_stats_table = RoomOwnerAuthorStatsTable(db)
  room_owner_author_stats_tuple = {key:None for key in room_owner_author_stats_table.get_tuple()}
  
  set_dict_attr(room_owner_author_stats_tuple, "$.start_time",    start_time)
  set_dict_attr(room_owner_author_stats_tuple, "$.platform",      platform)
  set_dict_attr(room_owner_author_stats_tuple, "$.room_id",       str(room_id))
  set_dict_attr(room_owner_author_stats_tuple, "$.owner_user_id", owner_user_id)
  
  try:
    room_owner_author_stats_tuple_list = room_owner_author_stats_table.get_record(room_owner_author_stats_tuple)
    if len(room_owner_author_stats_tuple_list) != 0:
      room_owner_author_stats_tuple = room_owner_author_stats_tuple_list.pop()
    else:
      room_owner_author_stats_tuple = {}
  except Exception as e:
    get_logger().error(f"{e}: {room_owner_author_stats_table.get_name()} >> >> >> >> data.room.owner.author_stats")
    room_owner_author_stats_tuple = {}
  
  """
  >> >> >> >> data.room.owner.authentication_info
  """
  room_owner_auth_info_table = RoomOwnerAuthInfoTable(db)
  room_owner_auth_info_tuple = {key:None for key in room_owner_auth_info_table.get_tuple()}
  
  set_dict_attr(room_owner_auth_info_tuple, "$.start_time",    start_time)
  set_dict_attr(room_owner_auth_info_tuple, "$.platform",      platform)
  set_dict_attr(room_owner_auth_info_tuple, "$.room_id",       str(room_id))
  set_dict_attr(room_owner_auth_info_tuple, "$.owner_user_id", owner_user_id)
  
  try:
    room_owner_auth_info_tuple_list = room_owner_auth_info_table.get_record(room_owner_auth_info_tuple)
    if len(room_owner_auth_info_tuple_list) != 0:
      room_owner_auth_info_tuple = room_owner_auth_info_tuple_list.pop()
  except Exception as e:
    get_logger().error(f"{e}: {room_owner_auth_info_table.get_name()} >> >> >> >> data.room.owner.authentication_info")
    room_owner_auth_info_tuple = {}

  if bool(room_owner_auth_info_tuple.get('exist_authentication_info', False)) is True:
    room_owner_auth_level_table = RoomOwnerAuthLevelTable(db)
    room_owner_auth_level_tuple = {key:None for key in room_owner_auth_level_table.get_tuple()}
    
    set_dict_attr(room_owner_auth_level_tuple, "$.start_time",    start_time)
    set_dict_attr(room_owner_auth_level_tuple, "$.platform",      platform)
    set_dict_attr(room_owner_auth_level_tuple, "$.room_id",       str(room_id))
    set_dict_attr(room_owner_auth_level_tuple, "$.owner_user_id", owner_user_id)
    
    try:
      room_owner_auth_level_list = list()
      room_owner_auth_level_tuple_list = room_owner_auth_level_table.get_record(room_owner_auth_level_tuple, fetchall=True)
      for room_owner_auth_level_tuple in room_owner_auth_level_tuple_list:
        room_owner_auth_level_list.insert(get_dict_attr(room_owner_auth_level_tuple, "$.level_index"), get_dict_attr(room_owner_auth_level_tuple, "$.level"))
    except Exception as e:
      get_logger().error(f"{e}: {room_owner_auth_level_table.get_name()} >> >> >> >> >> data.room.owner.authentication_info.level_list")
      room_owner_auth_level_list = []

    """
    >> >> >> >> >> data.room.owner.authentication_info.authentication_badge
    """
    ##
    ## PictureTable
    ##
    auth_info_picture       = PictureTable(db)
    auth_info_picture_tuple = {key: None for key in auth_info_picture.get_tuple()}
    
    set_dict_attr(auth_info_picture_tuple, "$.start_time",  start_time)
    set_dict_attr(auth_info_picture_tuple, "$.platform",    platform)
    set_dict_attr(auth_info_picture_tuple, "$.room_id",     str(room_id))
    set_dict_attr(auth_info_picture_tuple, "$.label",       'authentication_badge')
    
    try:
      auth_info_picture_tuple_list = auth_info_picture.get_record(auth_info_picture_tuple)
      if len(auth_info_picture_tuple_list) != 0:
        auth_info_picture_tuple = auth_info_picture_tuple_list.pop()
    except Exception as e:
      get_logger().error(f"{e}: {auth_info_picture.get_name()} >> >> >> >> >> data.room.owner.authentication_info.authentication_badge")
      auth_info_picture_tuple = dict()
    
    ##
    ## PictureFlexSettingTable
    ##
    auth_info_pic_flex_setting = PictureFlexSettingTable(db)
    auth_info_pic_flex_setting_tuple = {key: None for key in auth_info_pic_flex_setting.get_tuple()}
    
    set_dict_attr(auth_info_pic_flex_setting_tuple, "$.uri",         auth_info_picture_tuple.get('uri', ''))
    set_dict_attr(auth_info_pic_flex_setting_tuple, "$.platform",    'douyin')
    set_dict_attr(auth_info_pic_flex_setting_tuple, "$.start_time",  start_time)
    set_dict_attr(auth_info_pic_flex_setting_tuple, "$.room_id",     str(room_id))
    set_dict_attr(auth_info_pic_flex_setting_tuple, "$.label",       'authentication_badge')
    
    try:
      auth_info_flex_setting_list = list()
      auth_info_pic_flex_setting_tuple_list = auth_info_pic_flex_setting.get_record(auth_info_pic_flex_setting_tuple, fetchall=True)
      for flex_setting in auth_info_pic_flex_setting_tuple_list:
        auth_info_flex_setting_list.append(get_dict_attr(flex_setting, "$.flex_setting"))
    except Exception as e:
      get_logger().error(f"{e}: {auth_info_pic_flex_setting.get_name()} >> >> >> >> >> >> data.room.owner.authentication_info.authentication_badge.flex_setting_list")
      auth_info_flex_setting_list = []
  
    ##
    ## PictureTextSettingTable
    ##
    auth_info_pic_text_setting = PictureTextSettingTable(db)
    auth_info_pic_text_setting_tuple = {key: None for key in auth_info_pic_text_setting.get_tuple()}
    
    set_dict_attr(auth_info_pic_text_setting_tuple, "$.uri",         auth_info_picture_tuple.get('uri', ''))
    set_dict_attr(auth_info_pic_text_setting_tuple, "$.platform",    'douyin')
    set_dict_attr(auth_info_pic_text_setting_tuple, "$.start_time",  start_time)
    set_dict_attr(auth_info_pic_text_setting_tuple, "$.room_id",     str(room_id))
    set_dict_attr(auth_info_pic_text_setting_tuple, "$.label",       'authentication_badge')
    
    try:
      auth_info_text_setting_list = list()
      auth_info_pic_text_setting_tuple_list = auth_info_pic_text_setting.get_record(auth_info_pic_text_setting_tuple, fetchall=True)
      for text_setting in auth_info_pic_text_setting_tuple_list:
        auth_info_text_setting_list.append(get_dict_attr(text_setting, "$.text_setting"))
    except Exception as e:
      get_logger().error(f"{e}: {auth_info_pic_text_setting.get_name()} >> >> >> >> >> >> data.room.owner.authentication_info.text_setting_list")
      auth_info_text_setting_list = []
    
    ##
    ## PictureUrlTable
    ##
    auth_info_picture_url       = PictureUrlTable(db)
    auth_info_picture_url_tuple = {key: None for key in auth_info_picture_url.get_tuple()}
    
    set_dict_attr(auth_info_picture_url_tuple, "$.uri",         auth_info_picture_tuple.get('uri', ''))
    set_dict_attr(auth_info_picture_url_tuple, "$.platform",    'douyin')
    set_dict_attr(auth_info_picture_url_tuple, "$.start_time",  start_time)
    set_dict_attr(auth_info_picture_url_tuple, "$.room_id",     str(room_id))
    set_dict_attr(auth_info_picture_url_tuple, "$.label",       'authentication_badge')
    
    try:
      auth_info_url_list = list()
      auth_info_picture_url_tuple_list = auth_info_picture_url.get_record(auth_info_picture_url_tuple, fetchall=True)
      for url in auth_info_picture_url_tuple_list:
        auth_info_url_list.append(get_dict_attr(url, "$.url"))
    except Exception as e:
      get_logger().error(f"{e}: {auth_info_picture_url.get_name()} >> >> >> >> >> >> data.room.owner.authentication_info.url_list")
      auth_info_url_list = []

    """
    >> >> >> >> >> data.room.owner.authentication_info.authentication_badge_v2
    """
    ##
    ## PictureTable
    ##
    auth_info_v2_picture       = PictureTable(db)
    auth_info_v2_picture_tuple = {key: None for key in auth_info_v2_picture.get_tuple()}
    
    set_dict_attr(auth_info_v2_picture_tuple, "$.start_time",  start_time)
    set_dict_attr(auth_info_v2_picture_tuple, "$.platform",    platform)
    set_dict_attr(auth_info_v2_picture_tuple, "$.room_id",     str(room_id))
    set_dict_attr(auth_info_v2_picture_tuple, "$.label",       'authentication_badge_v2')
    
    try:
      auth_info_v2_picture_tuple_list = auth_info_v2_picture.get_record(auth_info_v2_picture_tuple)
      if len(auth_info_v2_picture_tuple_list) != 0:
        auth_info_v2_picture_tuple = auth_info_v2_picture_tuple_list.pop()
    except Exception as e:
      get_logger().error(f"{e}: {auth_info_v2_picture.get_name()} >> >> >> >> >> data.room.owner.authentication_info.authentication_badge_v2")
      auth_info_v2_picture_tuple = dict()
    
    ##
    ## PictureFlexSettingTable
    ##
    auth_info_v2_pic_flex_setting = PictureFlexSettingTable(db)
    auth_info_v2_pic_flex_setting_tuple = {key: None for key in auth_info_v2_pic_flex_setting.get_tuple()}
    
    set_dict_attr(auth_info_v2_pic_flex_setting_tuple, "$.uri",         auth_info_v2_picture_tuple.get('uri', ''))
    set_dict_attr(auth_info_v2_pic_flex_setting_tuple, "$.platform",    'douyin')
    set_dict_attr(auth_info_v2_pic_flex_setting_tuple, "$.start_time",  start_time)
    set_dict_attr(auth_info_v2_pic_flex_setting_tuple, "$.room_id",     str(room_id))
    set_dict_attr(auth_info_v2_pic_flex_setting_tuple, "$.label",       'authentication_badge_v2')
    
    try:
      auth_info_v2_flex_setting_list = list()
      auth_info_v2_pic_flex_setting_tuple_list = auth_info_v2_pic_flex_setting.get_record(auth_info_v2_pic_flex_setting_tuple, fetchall=True)
      for flex_setting in auth_info_v2_pic_flex_setting_tuple_list:
        auth_info_v2_flex_setting_list.append(get_dict_attr(flex_setting, "$.flex_setting"))
    except Exception as e:
      get_logger().error(f"{e}: {auth_info_v2_pic_flex_setting.get_name()} >> >> >> >> >> >> data.room.owner.authentication_info.authentication_badge_v2.flex_setting_list")
      auth_info_v2_flex_setting_list = []
  
    ##
    ## PictureTextSettingTable
    ##
    auth_info_v2_pic_text_setting = PictureTextSettingTable(db)
    auth_info_v2_pic_text_setting_tuple = {key: None for key in auth_info_v2_pic_text_setting.get_tuple()}
    
    set_dict_attr(auth_info_v2_pic_text_setting_tuple, "$.uri",         auth_info_v2_picture_tuple.get('uri', ''))
    set_dict_attr(auth_info_v2_pic_text_setting_tuple, "$.platform",    'douyin')
    set_dict_attr(auth_info_v2_pic_text_setting_tuple, "$.start_time",  start_time)
    set_dict_attr(auth_info_v2_pic_text_setting_tuple, "$.room_id",     str(room_id))
    set_dict_attr(auth_info_v2_pic_text_setting_tuple, "$.label",       'authentication_badge_v2')
    
    try:
      auth_info_v2_text_setting_list = list()
      auth_info_v2_pic_text_setting_tuple_list = auth_info_v2_pic_text_setting.get_record(auth_info_v2_pic_text_setting_tuple, fetchall=True)
      for text_setting in auth_info_v2_pic_text_setting_tuple_list:
        auth_info_v2_text_setting_list.append(get_dict_attr(text_setting, "$.text_setting"))
    except Exception as e:
      get_logger().error(f"{e}: {auth_info_v2_pic_text_setting.get_name()} >> >> >> >> >> >> data.room.owner.authentication_info.authentication_badge_v2.text_setting_list")
      auth_info_v2_text_setting_list = []
    
    ##
    ## PictureUrlTable
    ##
    auth_info_v2_picture_url       = PictureUrlTable(db)
    auth_info_v2_picture_url_tuple = {key: None for key in auth_info_v2_picture_url.get_tuple()}
    
    set_dict_attr(auth_info_v2_picture_url_tuple, "$.uri",         auth_info_v2_picture_tuple.get('uri', ''))
    set_dict_attr(auth_info_v2_picture_url_tuple, "$.platform",    'douyin')
    set_dict_attr(auth_info_v2_picture_url_tuple, "$.start_time",  start_time)
    set_dict_attr(auth_info_v2_picture_url_tuple, "$.room_id",     str(room_id))
    set_dict_attr(auth_info_v2_picture_url_tuple, "$.label",       'authentication_badge_v2')
    
    try:
      auth_info_v2_url_list = list()
      auth_info_v2_picture_url_tuple_list = auth_info_v2_picture_url.get_record(auth_info_v2_picture_url_tuple, fetchall=True)
      for url in auth_info_v2_picture_url_tuple_list:
        auth_info_v2_url_list.append(get_dict_attr(url, "$.url"))
    except Exception as e:
      get_logger().error(f"{e}: {auth_info_v2_picture_url.get_name()} >> >> >> >> >> >> data.room.owner.authentication_info.authentication_badge_v2.url_list")
      auth_info_v2_url_list = []
  
  """
  >> >> >> data.room.owner.avatar_large
  """  
  ##
  ## PictureTable
  ##
  avatar_large_picture       = PictureTable(db)
  avatar_large_picture_tuple = {key: None for key in avatar_large_picture.get_tuple()}
  
  set_dict_attr(avatar_large_picture_tuple, "$.start_time",  start_time)
  set_dict_attr(avatar_large_picture_tuple, "$.platform",    platform)
  set_dict_attr(avatar_large_picture_tuple, "$.room_id",     str(room_id))
  set_dict_attr(avatar_large_picture_tuple, "$.label",       'avatar_large')
  
  try:
    avatar_large_picture_tuple_list = avatar_large_picture.get_record(avatar_large_picture_tuple)
    if len(avatar_large_picture_tuple_list) != 0:
      avatar_large_picture_tuple = avatar_large_picture_tuple_list.pop()
  except Exception as e:
    get_logger().error(f"{e}: {avatar_large_picture.get_name()} >> >> >> data.room.avatar_large")
    avatar_large_picture_tuple = dict()
  
  ##
  ## PictureFlexSettingTable
  ##
  avatar_large_pic_flex_setting = PictureFlexSettingTable(db)
  avatar_large_pic_flex_setting_tuple = {key: None for key in avatar_large_pic_flex_setting.get_tuple()}
  
  set_dict_attr(avatar_large_pic_flex_setting_tuple, "$.uri",         avatar_large_picture_tuple.get('uri', ''))
  set_dict_attr(avatar_large_pic_flex_setting_tuple, "$.platform",    'douyin')
  set_dict_attr(avatar_large_pic_flex_setting_tuple, "$.start_time",  start_time)
  set_dict_attr(avatar_large_pic_flex_setting_tuple, "$.room_id",     str(room_id))
  set_dict_attr(avatar_large_pic_flex_setting_tuple, "$.label",       'avatar_large')
  
  try:
    avatar_large_flex_setting_list = list()
    avatar_large_pic_flex_setting_tuple_list = avatar_large_pic_flex_setting.get_record(avatar_large_pic_flex_setting_tuple, fetchall=True)
    for flex_setting in avatar_large_pic_flex_setting_tuple_list:
      avatar_large_flex_setting_list.append(get_dict_attr(flex_setting, "$.flex_setting"))
  except Exception as e:
    get_logger().error(f"{e}: {avatar_large_pic_flex_setting.get_name()} >> >> >> >> data.room.avatar_large.flex_setting_list")
    avatar_large_flex_setting_list = []

  ##
  ## PictureTextSettingTable
  ##
  avatar_large_pic_text_setting = PictureTextSettingTable(db)
  avatar_large_pic_text_setting_tuple = {key: None for key in avatar_large_pic_text_setting.get_tuple()}
  
  set_dict_attr(avatar_large_pic_text_setting_tuple, "$.uri",         avatar_large_picture_tuple.get('uri', ''))
  set_dict_attr(avatar_large_pic_text_setting_tuple, "$.platform",    'douyin')
  set_dict_attr(avatar_large_pic_text_setting_tuple, "$.start_time",  start_time)
  set_dict_attr(avatar_large_pic_text_setting_tuple, "$.room_id",     str(room_id))
  set_dict_attr(avatar_large_pic_text_setting_tuple, "$.label",       'avatar_large')
  
  try:
    avatar_large_text_setting_list = list()
    avatar_large_pic_text_setting_tuple_list = avatar_large_pic_text_setting.get_record(avatar_large_pic_text_setting_tuple, fetchall=True)
    for text_setting in avatar_large_pic_text_setting_tuple_list:
      avatar_large_text_setting_list.append(get_dict_attr(text_setting, "$.text_setting"))
  except Exception as e:
    get_logger().error(f"{e}: {avatar_large_pic_text_setting.get_name()} >> >> >> >> data.room.avatar_large.text_setting_list")
    avatar_large_text_setting_list = []
  
  ##
  ## PictureUrlTable
  ##
  avatar_large_picture_url       = PictureUrlTable(db)
  avatar_large_picture_url_tuple = {key: None for key in avatar_large_picture_url.get_tuple()}
  
  set_dict_attr(avatar_large_picture_url_tuple, "$.uri",         avatar_large_picture_tuple.get('uri', ''))
  set_dict_attr(avatar_large_picture_url_tuple, "$.platform",    'douyin')
  set_dict_attr(avatar_large_picture_url_tuple, "$.start_time",  start_time)
  set_dict_attr(avatar_large_picture_url_tuple, "$.room_id",     str(room_id))
  set_dict_attr(avatar_large_picture_url_tuple, "$.label",       'avatar_large')
  
  try:
    avatar_large_url_list = list()
    avatar_large_picture_url_tuple_list = avatar_large_picture_url.get_record(avatar_large_picture_url_tuple, fetchall=True)
    for url in avatar_large_picture_url_tuple_list:
      avatar_large_url_list.append(get_dict_attr(url, "$.url"))
  except Exception as e:
    get_logger().error(f"{e}: {avatar_large_picture_url.get_name()} >> >> >> >> data.room.avatar_large.url_list")
    avatar_large_url_list = []

  """
  >> >> >> data.room.owner.avatar_medium
  """  
  ##
  ## PictureTable
  ##
  avatar_medium_picture       = PictureTable(db)
  avatar_medium_picture_tuple = {key: None for key in avatar_medium_picture.get_tuple()}
  
  set_dict_attr(avatar_medium_picture_tuple, "$.start_time",  start_time)
  set_dict_attr(avatar_medium_picture_tuple, "$.platform",    platform)
  set_dict_attr(avatar_medium_picture_tuple, "$.room_id",     str(room_id))
  set_dict_attr(avatar_medium_picture_tuple, "$.label",       'avatar_medium')
  
  try:
    avatar_medium_picture_tuple_list = avatar_medium_picture.get_record(avatar_medium_picture_tuple)
    if len(avatar_medium_picture_tuple_list) != 0:
      avatar_medium_picture_tuple = avatar_medium_picture_tuple_list.pop()
  except Exception as e:
    get_logger().error(f"{e}: {avatar_medium_picture.get_name()} >> >> >> data.room.avatar_medium")
    avatar_medium_picture_tuple= {}
  
  ##
  ## PictureFlexSettingTable
  ##
  avatar_medium_pic_flex_setting = PictureFlexSettingTable(db)
  avatar_medium_pic_flex_setting_tuple = {key: None for key in avatar_medium_pic_flex_setting.get_tuple()}
  
  set_dict_attr(avatar_medium_pic_flex_setting_tuple, "$.uri",         avatar_medium_picture_tuple.get('uri', ''))
  set_dict_attr(avatar_medium_pic_flex_setting_tuple, "$.platform",    'douyin')
  set_dict_attr(avatar_medium_pic_flex_setting_tuple, "$.start_time",  start_time)
  set_dict_attr(avatar_medium_pic_flex_setting_tuple, "$.room_id",     str(room_id))
  set_dict_attr(avatar_medium_pic_flex_setting_tuple, "$.label",       'avatar_medium')
  
  try:
    avatar_medium_flex_setting_list = list()
    avatar_medium_pic_flex_setting_tuple_list = avatar_medium_pic_flex_setting.get_record(avatar_medium_pic_flex_setting_tuple, fetchall=True)
    for flex_setting in avatar_medium_pic_flex_setting_tuple_list:
      avatar_medium_flex_setting_list.append(get_dict_attr(flex_setting, "$.flex_setting"))
  except Exception as e:
    get_logger().error(f"{e}: {avatar_medium_pic_flex_setting.get_name()} >> >> >> >> data.room.avatar_medium.flex_setting_list")
    avatar_medium_flex_setting_list = []

  ##
  ## PictureTextSettingTable
  ##
  avatar_medium_pic_text_setting = PictureTextSettingTable(db)
  avatar_medium_pic_text_setting_tuple = {key: None for key in avatar_medium_pic_text_setting.get_tuple()}
  
  set_dict_attr(avatar_medium_pic_text_setting_tuple, "$.uri",         avatar_medium_picture_tuple.get('uri', ''))
  set_dict_attr(avatar_medium_pic_text_setting_tuple, "$.platform",    'douyin')
  set_dict_attr(avatar_medium_pic_text_setting_tuple, "$.start_time",  start_time)
  set_dict_attr(avatar_medium_pic_text_setting_tuple, "$.room_id",     str(room_id))
  set_dict_attr(avatar_medium_pic_text_setting_tuple, "$.label",       'avatar_medium')
  
  try:
    avatar_medium_text_setting_list = list()
    avatar_medium_pic_text_setting_tuple_list = avatar_medium_pic_text_setting.get_record(avatar_medium_pic_text_setting_tuple, fetchall=True)
    for text_setting in avatar_medium_pic_text_setting_tuple_list:
      avatar_medium_text_setting_list.append(get_dict_attr(text_setting, "$.text_setting"))
  except Exception as e:
    get_logger().error(f"{e}: {avatar_medium_pic_text_setting.get_name()} >> >> >> >> data.room.avatar_medium.text_setting_list")
    avatar_medium_text_setting_list = []
  
  ##
  ## PictureUrlTable
  ##
  avatar_medium_picture_url       = PictureUrlTable(db)
  avatar_medium_picture_url_tuple = {key: None for key in avatar_medium_picture_url.get_tuple()}
  
  set_dict_attr(avatar_medium_picture_url_tuple, "$.uri",         avatar_medium_picture_tuple.get('uri', ''))
  set_dict_attr(avatar_medium_picture_url_tuple, "$.platform",    'douyin')
  set_dict_attr(avatar_medium_picture_url_tuple, "$.start_time",  start_time)
  set_dict_attr(avatar_medium_picture_url_tuple, "$.room_id",     str(room_id))
  set_dict_attr(avatar_medium_picture_url_tuple, "$.label",       'avatar_medium')
  
  try:
    avatar_medium_url_list = list()
    avatar_medium_picture_url_tuple_list = avatar_medium_picture_url.get_record(avatar_medium_picture_url_tuple, fetchall=True)
    for url in avatar_medium_picture_url_tuple_list:
      avatar_medium_url_list.append(get_dict_attr(url, "$.url"))
  except Exception as e:
    get_logger().error(f"{e}: {avatar_medium_picture_url.get_name()} >> >> >> >> data.room.avatar_medium.url_list")
    avatar_medium_url_list = []

  """
  >> >> >> data.room.owner.avatar_thumb
  """
  ##
  ## PictureTable
  ##
  avatar_thumb_picture       = PictureTable(db)
  avatar_thumb_picture_tuple = {key: None for key in avatar_thumb_picture.get_tuple()}
  
  set_dict_attr(avatar_thumb_picture_tuple, "$.start_time",  start_time)
  set_dict_attr(avatar_thumb_picture_tuple, "$.platform",    platform)
  set_dict_attr(avatar_thumb_picture_tuple, "$.room_id",     str(room_id))
  set_dict_attr(avatar_thumb_picture_tuple, "$.label",       'avatar_thumb')
  
  try:
    avatar_thumb_picture_tuple_list = avatar_thumb_picture.get_record(avatar_thumb_picture_tuple)
    if len(avatar_thumb_picture_tuple_list) != 0:
      avatar_thumb_picture_tuple = avatar_thumb_picture_tuple_list.pop()
  except Exception as e:
    get_logger().error(f"{e}: {avatar_thumb_picture.get_name()} >> >> >> data.room.avatar_thumb")
    avatar_thumb_picture_tuple = {}
  
  ##
  ## PictureFlexSettingTable
  ##
  avatar_thumb_pic_flex_setting = PictureFlexSettingTable(db)
  avatar_thumb_pic_flex_setting_tuple = {key: None for key in avatar_thumb_pic_flex_setting.get_tuple()}
  
  set_dict_attr(avatar_thumb_pic_flex_setting_tuple, "$.uri",         avatar_thumb_picture_tuple.get('uri', ''))
  set_dict_attr(avatar_thumb_pic_flex_setting_tuple, "$.platform",    'douyin')
  set_dict_attr(avatar_thumb_pic_flex_setting_tuple, "$.start_time",  start_time)
  set_dict_attr(avatar_thumb_pic_flex_setting_tuple, "$.room_id",     str(room_id))
  set_dict_attr(avatar_thumb_pic_flex_setting_tuple, "$.label",       'avatar_thumb')
  
  try:
    avatar_thumb_flex_setting_list = list()
    avatar_thumb_pic_flex_setting_tuple_list = avatar_thumb_pic_flex_setting.get_record(avatar_thumb_pic_flex_setting_tuple, fetchall=True)
    for flex_setting in avatar_thumb_pic_flex_setting_tuple_list:
      avatar_thumb_flex_setting_list.append(get_dict_attr(flex_setting, "$.flex_setting"))
  except Exception as e:
    get_logger().error(f"{e}: {avatar_thumb_pic_flex_setting.get_name()} >> >> >> >> data.room.avatar_thumb.flex_setting_list")
    avatar_thumb_flex_setting_list = []

  ##
  ## PictureTextSettingTable
  ##
  avatar_thumb_pic_text_setting = PictureTextSettingTable(db)
  avatar_thumb_pic_text_setting_tuple = {key: None for key in avatar_thumb_pic_text_setting.get_tuple()}
  
  set_dict_attr(avatar_thumb_pic_text_setting_tuple, "$.uri",         avatar_thumb_picture_tuple.get('uri', ''))
  set_dict_attr(avatar_thumb_pic_text_setting_tuple, "$.platform",    'douyin')
  set_dict_attr(avatar_thumb_pic_text_setting_tuple, "$.start_time",  start_time)
  set_dict_attr(avatar_thumb_pic_text_setting_tuple, "$.room_id",     str(room_id))
  set_dict_attr(avatar_thumb_pic_text_setting_tuple, "$.label",       'avatar_thumb')
  
  try:
    avatar_thumb_text_setting_list = list()
    avatar_thumb_pic_text_setting_tuple_list = avatar_thumb_pic_text_setting.get_record(avatar_thumb_pic_text_setting_tuple, fetchall=True)
    for text_setting in avatar_thumb_pic_text_setting_tuple_list:
      avatar_thumb_text_setting_list.append(get_dict_attr(text_setting, "$.text_setting"))
  except Exception as e:
    get_logger().error(f"{e}: {avatar_thumb_pic_text_setting.get_name()} >> >> >> >> data.room.avatar_thumb.text_setting_list")
    avatar_thumb_text_setting_list = []
  
  ##
  ## PictureUrlTable
  ##
  avatar_thumb_picture_url       = PictureUrlTable(db)
  avatar_thumb_picture_url_tuple = {key: None for key in avatar_thumb_picture_url.get_tuple()}
  
  set_dict_attr(avatar_thumb_picture_url_tuple, "$.uri",         avatar_thumb_picture_tuple.get('uri', ''))
  set_dict_attr(avatar_thumb_picture_url_tuple, "$.platform",    'douyin')
  set_dict_attr(avatar_thumb_picture_url_tuple, "$.start_time",  start_time)
  set_dict_attr(avatar_thumb_picture_url_tuple, "$.room_id",     str(room_id))
  set_dict_attr(avatar_thumb_picture_url_tuple, "$.label",       'avatar_thumb')
  
  try:
    avatar_thumb_url_list = list()
    avatar_thumb_picture_url_tuple_list = avatar_thumb_picture_url.get_record(avatar_thumb_picture_url_tuple, fetchall=True)
    for url in avatar_thumb_picture_url_tuple_list:
      avatar_thumb_url_list.append(get_dict_attr(url, "$.url"))
  except Exception as e:
    get_logger().error(f"{e}: {avatar_thumb_picture_url.get_name()} >> >> >> >> data.room.avatar_thumb.url_list")
    avatar_thumb_url_list = []

  """
  >> >> >> data.room.owner.badge_image_list
  """
  owner_badge_image_list = list()
  
  owner_badge_image_avg_color_list              = list()
  owner_badge_image_content_list                = list()
  owner_badge_image_flex_setting_list           = list()
  owner_badge_image_height_list                 = list()
  owner_badge_image_image_type_list             = list()
  owner_badge_image_is_animated_list            = list()
  owner_badge_image_open_web_url_list           = list()
  owner_badge_image_text_setting_list           = list()
  owner_badge_image_uri_list                    = list()
  owner_badge_image_url_list                    = list()
  owner_badge_image_width_list                  = list()

  ##
  ## PictureTable
  ##
  owner_badge_image_list_picture       = PictureTable(db)
  owner_badge_image_list_picture_tuple = {key: None for key in owner_badge_image_list_picture.get_tuple()}
  
  set_dict_attr(owner_badge_image_list_picture_tuple, "$.start_time",  start_time)
  set_dict_attr(owner_badge_image_list_picture_tuple, "$.platform",    platform)
  set_dict_attr(owner_badge_image_list_picture_tuple, "$.room_id",     str(room_id))
  set_dict_attr(owner_badge_image_list_picture_tuple, "$.label",       'badge_image_list')

  try:
    owner_badge_image_list_picture_tuple_list = owner_badge_image_list_picture.get_record(owner_badge_image_list_picture_tuple, fetchall=True)
    for owner_badge_image_picture_tuple in owner_badge_image_list_picture_tuple_list:
      owner_badge_image_avg_color_list.append(get_dict_attr(owner_badge_image_picture_tuple,    "$.avg_color"))
      owner_badge_image_height_list.append(get_dict_attr(owner_badge_image_picture_tuple,       "$.height"))
      owner_badge_image_image_type_list.append(get_dict_attr(owner_badge_image_picture_tuple,   "$.image_type"))
      owner_badge_image_is_animated_list.append(get_dict_attr(owner_badge_image_picture_tuple,  "$.is_animated"))
      owner_badge_image_open_web_url_list.append(get_dict_attr(owner_badge_image_picture_tuple, "$.open_web_url"))
      owner_badge_image_uri_list.append(get_dict_attr(owner_badge_image_picture_tuple,          "$.uri"))
      owner_badge_image_width_list.append(get_dict_attr(owner_badge_image_picture_tuple,        "$.width"))
  except Exception as e:
    get_logger().error(f"{e}: {owner_badge_image_list_picture.get_name()} >> >> >> >> data.room.owner.badge_image_list")
    owner_badge_image_avg_color_list.append('')
    owner_badge_image_height_list.append(0)
    owner_badge_image_image_type_list.append(0)
    owner_badge_image_is_animated_list.append(False)
    owner_badge_image_open_web_url_list.append('')
    owner_badge_image_uri_list.append('')
    owner_badge_image_width_list.append(0)

  for badge_image_index in range(0, len(owner_badge_image_uri_list)):
    ##
    ## PictureContentTable
    ##
    owner_badge_image_picture_content       = PictureContentTable(db)
    owner_badge_image_picture_content_tuple = {key: None for key in owner_badge_image_picture_content.get_tuple()}
    
    set_dict_attr(owner_badge_image_picture_content_tuple, "$.uri",         owner_badge_image_uri_list[badge_image_index])
    set_dict_attr(owner_badge_image_picture_content_tuple, "$.start_time",  start_time)
    set_dict_attr(owner_badge_image_picture_content_tuple, "$.platform",    platform)
    set_dict_attr(owner_badge_image_picture_content_tuple, "$.room_id",     str(room_id))
    set_dict_attr(owner_badge_image_picture_content_tuple, "$.label",       "badge_image_list")
    
    try:
      owner_badge_image_content = dict()
      owner_badge_image_picture_content_tuple_list = owner_badge_image_picture_content.get_record(owner_badge_image_picture_content_tuple)
      if len(owner_badge_image_picture_content_tuple_list) != 0:
        owner_badge_image_picture_content_tuple = owner_badge_image_picture_content_tuple_list.pop()
  
        owner_badge_image_content_alternative_text = get_dict_attr(owner_badge_image_picture_content_tuple, "$.alternative_text")
        owner_badge_image_content_font_color       = get_dict_attr(owner_badge_image_picture_content_tuple, "$.font_color")
        owner_badge_image_content_level            = get_dict_attr(owner_badge_image_picture_content_tuple, "$.level")
        owner_badge_image_content_name             = get_dict_attr(owner_badge_image_picture_content_tuple, "$.name")
    except Exception as e:
      get_logger().error(f"{e}: {owner_badge_image_picture_content.get_name()} >> >> >> >> >> data.room.owner.badge_image_list.content")
      owner_badge_image_content_alternative_text = ''
      owner_badge_image_content_font_color       = ''
      owner_badge_image_content_level            = 0
      owner_badge_image_content_name             = ''
    finally:
      set_dict_attr(owner_badge_image_content, "$.alternative_text", owner_badge_image_content_alternative_text, force=True)
      set_dict_attr(owner_badge_image_content, "$.font_color",       owner_badge_image_content_font_color,       force=True)
      set_dict_attr(owner_badge_image_content, "$.level",            owner_badge_image_content_level,            force=True)
      set_dict_attr(owner_badge_image_content, "$.name",             owner_badge_image_content_name,             force=True)
      owner_badge_image_content_list.append(owner_badge_image_content)

    ##
    ## PictureFlexSettingTable
    ##
    owner_badge_image_pic_flex_setting = PictureFlexSettingTable(db)
    owner_badge_image_pic_flex_setting_tuple = {key: None for key in owner_badge_image_pic_flex_setting.get_tuple()}
    
    set_dict_attr(owner_badge_image_pic_flex_setting_tuple, "$.uri",         owner_badge_image_uri_list[badge_image_index])
    set_dict_attr(owner_badge_image_pic_flex_setting_tuple, "$.platform",    'douyin')
    set_dict_attr(owner_badge_image_pic_flex_setting_tuple, "$.start_time",  start_time)
    set_dict_attr(owner_badge_image_pic_flex_setting_tuple, "$.room_id",     str(room_id))
    set_dict_attr(owner_badge_image_pic_flex_setting_tuple, "$.label",       'badge_image_list')
    
    try:
      owner_badge_image_flex_setting = list()
      owner_badge_image_pic_flex_setting_tuple_list = owner_badge_image_pic_flex_setting.get_record(owner_badge_image_pic_flex_setting_tuple, fetchall=True)
      for flex_setting in owner_badge_image_pic_flex_setting_tuple_list:
        owner_badge_image_flex_setting.append(get_dict_attr(flex_setting, "$.flex_setting"))
    except Exception as e:
      get_logger().error(f"{e}: {owner_badge_image_pic_flex_setting.get_name()} >> >> >> >> >> data.room.owner.badge_image_list.flex_setting_list")
      owner_badge_image_flex_setting = []
    finally:
      owner_badge_image_flex_setting_list.append(owner_badge_image_flex_setting)
  
    ##
    ## PictureTextSettingTable
    ##
    owner_badge_image_pic_text_setting = PictureTextSettingTable(db)
    owner_badge_image_pic_text_setting_tuple = {key: None for key in owner_badge_image_pic_text_setting.get_tuple()}
    
    set_dict_attr(owner_badge_image_pic_text_setting_tuple, "$.uri",        owner_badge_image_uri_list[badge_image_index])
    set_dict_attr(owner_badge_image_pic_text_setting_tuple, "$.platform",   'douyin')
    set_dict_attr(owner_badge_image_pic_text_setting_tuple, "$.start_time", start_time)
    set_dict_attr(owner_badge_image_pic_text_setting_tuple, "$.room_id",    str(room_id))
    set_dict_attr(owner_badge_image_pic_text_setting_tuple, "$.label",       'badge_image_list')
    
    try:
      badge_image_pic_text_setting_list = list()
      owner_badge_image_pic_text_setting_tuple_list = owner_badge_image_pic_text_setting.get_record(owner_badge_image_pic_text_setting_tuple, fetchall=True)
      for text_setting in owner_badge_image_pic_text_setting_tuple_list:
        badge_image_pic_text_setting_list.append(get_dict_attr(text_setting, "$.text_setting"))
    except Exception as e:
      get_logger().error(f"{e}: {owner_badge_image_pic_text_setting.get_name()} >> >> >> >> >> data.room.owner.badge_image_list.text_setting_list")
      badge_image_pic_text_setting_list = []
    finally:
      owner_badge_image_text_setting_list.append(badge_image_pic_text_setting_list)
    
    ##
    ## PictureUrlTable
    ##
    owner_badge_image_picture_url       = PictureUrlTable(db)
    owner_badge_image_picture_url_tuple = {key: None for key in owner_badge_image_picture_url.get_tuple()}
    
    set_dict_attr(owner_badge_image_picture_url_tuple, "$.uri",         owner_badge_image_uri_list[badge_image_index])
    set_dict_attr(owner_badge_image_picture_url_tuple, "$.platform",    'douyin')
    set_dict_attr(owner_badge_image_picture_url_tuple, "$.start_time",  start_time)
    set_dict_attr(owner_badge_image_picture_url_tuple, "$.room_id",     str(room_id))
    set_dict_attr(owner_badge_image_picture_url_tuple, "$.label",       'badge_image_list')
    
    try:
      owner_badge_image_pic_url_list = list()
      owner_badge_image_picture_url_tuple_list = owner_badge_image_picture_url.get_record(owner_badge_image_picture_url_tuple, fetchall=True)
      for url in owner_badge_image_picture_url_tuple_list:
        owner_badge_image_pic_url_list.append(get_dict_attr(url, "$.url"))
    except Exception as e:
      get_logger().error(f"{e}: {owner_badge_image_picture_url.get_name()} >> >> >> >> >> data.room.owner.badge_image_list.url_list")
      owner_badge_image_pic_url_list = []
    finally:
      owner_badge_image_url_list.append(owner_badge_image_pic_url_list)

  """
  >> >> >> >> data.room.owner.badge_image_list_v2
  """
  owner_badge_image_v2_list = list()
  
  owner_badge_image_v2_avg_color_list              = list()
  owner_badge_image_v2_content_list                = list()
  owner_badge_image_v2_flex_setting_list           = list()
  owner_badge_image_v2_height_list                 = list()
  owner_badge_image_v2_image_type_list             = list()
  owner_badge_image_v2_is_animated_list            = list()
  owner_badge_image_v2_open_web_url_list           = list()
  owner_badge_image_v2_text_setting_list           = list()
  owner_badge_image_v2_uri_list                    = list()
  owner_badge_image_v2_url_list                    = list()
  owner_badge_image_v2_width_list                  = list()

  ##
  ## PictureTable
  ##
  owner_badge_image_v2_list_picture       = PictureTable(db)
  owner_badge_image_v2_list_picture_tuple = {key: None for key in owner_badge_image_v2_list_picture.get_tuple()}
  
  set_dict_attr(owner_badge_image_v2_list_picture_tuple, "$.start_time",  start_time)
  set_dict_attr(owner_badge_image_v2_list_picture_tuple, "$.platform",    platform)
  set_dict_attr(owner_badge_image_v2_list_picture_tuple, "$.room_id",     str(room_id))
  set_dict_attr(owner_badge_image_v2_list_picture_tuple, "$.label",       'badge_image_list_v2')

  try:
    owner_badge_image_v2_list_picture_tuple_list = owner_badge_image_v2_list_picture.get_record(owner_badge_image_v2_list_picture_tuple, fetchall=True)
    for owner_badge_image_v2_picture_tuple in owner_badge_image_v2_list_picture_tuple_list:
      owner_badge_image_v2_avg_color_list.append(get_dict_attr(owner_badge_image_v2_picture_tuple,    "$.avg_color"))
      owner_badge_image_v2_height_list.append(get_dict_attr(owner_badge_image_v2_picture_tuple,       "$.height"))
      owner_badge_image_v2_image_type_list.append(get_dict_attr(owner_badge_image_v2_picture_tuple,   "$.image_type"))
      owner_badge_image_v2_is_animated_list.append(get_dict_attr(owner_badge_image_v2_picture_tuple,  "$.is_animated"))
      owner_badge_image_v2_open_web_url_list.append(get_dict_attr(owner_badge_image_v2_picture_tuple, "$.open_web_url"))
      owner_badge_image_v2_uri_list.append(get_dict_attr(owner_badge_image_v2_picture_tuple,          "$.uri"))
      owner_badge_image_v2_width_list.append(get_dict_attr(owner_badge_image_v2_picture_tuple,        "$.width"))
  except Exception as e:
    get_logger().error(f"{e}: {owner_badge_image_v2_list_picture.get_name()} >> >> >> >> data.room.owner.badge_image_list")
    owner_badge_image_v2_avg_color_list.append('')
    owner_badge_image_v2_height_list.append(0)
    owner_badge_image_v2_image_type_list.append(0)
    owner_badge_image_v2_is_animated_list.append(False)
    owner_badge_image_v2_open_web_url_list.append('')
    owner_badge_image_v2_uri_list.append('')
    owner_badge_image_v2_width_list.append(0)

  for badge_image_index in range(0, len(owner_badge_image_v2_uri_list)):
    ##
    ## PictureContentTable
    ##
    owner_badge_image_v2_picture_content       = PictureContentTable(db)
    owner_badge_image_v2_picture_content_tuple = {key: None for key in owner_badge_image_v2_picture_content.get_tuple()}
    
    set_dict_attr(owner_badge_image_v2_picture_content_tuple, "$.uri",         owner_badge_image_v2_uri_list[badge_image_index])
    set_dict_attr(owner_badge_image_v2_picture_content_tuple, "$.start_time",  start_time)
    set_dict_attr(owner_badge_image_v2_picture_content_tuple, "$.platform",    platform)
    set_dict_attr(owner_badge_image_v2_picture_content_tuple, "$.room_id",     str(room_id))
    set_dict_attr(owner_badge_image_v2_picture_content_tuple, "$.label",       "badge_image_list_v2")
    
    try:
      owner_badge_image_v2_content = dict()
      owner_badge_image_v2_picture_content_tuple_list = owner_badge_image_v2_picture_content.get_record(owner_badge_image_v2_picture_content_tuple)
      if len(owner_badge_image_v2_picture_content_tuple_list) != 0:
        owner_badge_image_v2_picture_content_tuple = owner_badge_image_v2_picture_content_tuple_list.pop()
  
        owner_badge_image_v2_content_alternative_text = get_dict_attr(owner_badge_image_v2_picture_content_tuple, "$.alternative_text")
        owner_badge_image_v2_content_font_color       = get_dict_attr(owner_badge_image_v2_picture_content_tuple, "$.font_color")
        owner_badge_image_v2_content_level            = get_dict_attr(owner_badge_image_v2_picture_content_tuple, "$.level")
        owner_badge_image_v2_content_name             = get_dict_attr(owner_badge_image_v2_picture_content_tuple, "$.name")
    except Exception as e:
      get_logger().error(f"{e}: {owner_badge_image_v2_picture_content.get_name()} >> >> >> >> >> data.room.owner.badge_image_list.content")
      owner_badge_image_v2_content_alternative_text = ''
      owner_badge_image_v2_content_font_color       = ''
      owner_badge_image_v2_content_level            = 0
      owner_badge_image_v2_content_name             = ''
    finally:
      set_dict_attr(owner_badge_image_v2_content, "$.alternative_text", owner_badge_image_v2_content_alternative_text, force=True)
      set_dict_attr(owner_badge_image_v2_content, "$.font_color",       owner_badge_image_v2_content_font_color,       force=True)
      set_dict_attr(owner_badge_image_v2_content, "$.level",            owner_badge_image_v2_content_level,            force=True)
      set_dict_attr(owner_badge_image_v2_content, "$.name",             owner_badge_image_v2_content_name,             force=True)
      owner_badge_image_v2_content_list.append(owner_badge_image_v2_content)

    ##
    ## PictureFlexSettingTable
    ##
    owner_badge_image_v2_pic_flex_setting = PictureFlexSettingTable(db)
    owner_badge_image_v2_pic_flex_setting_tuple = {key: None for key in owner_badge_image_v2_pic_flex_setting.get_tuple()}
    
    set_dict_attr(owner_badge_image_v2_pic_flex_setting_tuple, "$.uri",         owner_badge_image_v2_uri_list[badge_image_index])
    set_dict_attr(owner_badge_image_v2_pic_flex_setting_tuple, "$.platform",    'douyin')
    set_dict_attr(owner_badge_image_v2_pic_flex_setting_tuple, "$.start_time",  start_time)
    set_dict_attr(owner_badge_image_v2_pic_flex_setting_tuple, "$.room_id",     str(room_id))
    set_dict_attr(owner_badge_image_v2_pic_flex_setting_tuple, "$.label",       'badge_image_list_v2')
    
    try:
      owner_badge_image_v2_flex_setting = list()
      owner_badge_image_v2_pic_flex_setting_tuple_list = owner_badge_image_v2_pic_flex_setting.get_record(owner_badge_image_v2_pic_flex_setting_tuple, fetchall=True)
      for flex_setting in owner_badge_image_v2_pic_flex_setting_tuple_list:
        owner_badge_image_v2_flex_setting.append(get_dict_attr(flex_setting, "$.flex_setting"))
    except Exception as e:
      get_logger().error(f"{e}: {owner_badge_image_v2_pic_flex_setting.get_name()} >> >> >> >> >> data.room.owner.badge_image_list_v2.flex_setting_list")
      owner_badge_image_v2_flex_setting = []
    finally:
      owner_badge_image_v2_flex_setting_list.append(owner_badge_image_v2_flex_setting)
  
    ##
    ## PictureTextSettingTable
    ##
    owner_badge_image_v2_pic_text_setting = PictureTextSettingTable(db)
    owner_badge_image_v2_pic_text_setting_tuple = {key: None for key in owner_badge_image_v2_pic_text_setting.get_tuple()}
    
    set_dict_attr(owner_badge_image_v2_pic_text_setting_tuple, "$.uri",         owner_badge_image_v2_uri_list[badge_image_index])
    set_dict_attr(owner_badge_image_v2_pic_text_setting_tuple, "$.platform",    'douyin')
    set_dict_attr(owner_badge_image_v2_pic_text_setting_tuple, "$.start_time",  start_time)
    set_dict_attr(owner_badge_image_v2_pic_text_setting_tuple, "$.room_id",     str(room_id))
    set_dict_attr(owner_badge_image_v2_pic_text_setting_tuple, "$.label",       'badge_image_list_v2')
    
    try:
      badge_image_v2_pic_text_setting = list()
      owner_badge_image_v2_pic_text_setting_tuple_list = owner_badge_image_v2_pic_text_setting.get_record(owner_badge_image_v2_pic_text_setting_tuple, fetchall=True)
      for text_setting in owner_badge_image_v2_pic_text_setting_tuple_list:
        badge_image_v2_pic_text_setting.append(get_dict_attr(text_setting, "$.text_setting"))
    except Exception as e:
      get_logger().error(f"{e}: {owner_badge_image_v2_pic_text_setting.get_name()} >> >> >> >> >> data.room.owner.badge_image_list.text_setting_list")
      badge_image_v2_pic_text_setting = []
    finally:
      owner_badge_image_v2_text_setting_list.append(badge_image_v2_pic_text_setting)
    
    ##
    ## PictureUrlTable
    ##
    owner_badge_image_v2_picture_url       = PictureUrlTable(db)
    owner_badge_image_v2_picture_url_tuple = {key: None for key in owner_badge_image_v2_picture_url.get_tuple()}
    
    set_dict_attr(owner_badge_image_v2_picture_url_tuple, "$.uri",         owner_badge_image_v2_uri_list[badge_image_index])
    set_dict_attr(owner_badge_image_v2_picture_url_tuple, "$.platform",    'douyin')
    set_dict_attr(owner_badge_image_v2_picture_url_tuple, "$.start_time",  start_time)
    set_dict_attr(owner_badge_image_v2_picture_url_tuple, "$.room_id",     str(room_id))
    set_dict_attr(owner_badge_image_v2_picture_url_tuple, "$.label",       'badge_image_list_v2')
    
    try:
      owner_badge_image_v2_pic_url_list = list()
      owner_badge_image_v2_picture_url_tuple_list = owner_badge_image_v2_picture_url.get_record(owner_badge_image_v2_picture_url_tuple, fetchall=True)
      for url in owner_badge_image_v2_picture_url_tuple_list:
        owner_badge_image_v2_pic_url_list.append(get_dict_attr(url, "$.url"))
    except Exception as e:
      get_logger().error(f"{e}: {owner_badge_image_v2_picture_url.get_name()} >> >> >> >> >> data.room.owner.badge_image_list.url_list")
      owner_badge_image_v2_pic_url_list = []
    finally:
      owner_badge_image_v2_url_list.append(owner_badge_image_v2_pic_url_list)

  """
  >> >> >> >> data.room.owner.commerce_webcast_config_ids
  """
  owner_commerce_webcast_config_ids = list()

  """
  >> >> >> >> data.room.owner.fans_club
  """
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
  owner_fans_club = FansClubTable(db)
  owner_fans_club_tuple = {key: None for key in owner_fans_club.get_tuple()}

  set_dict_attr(owner_fans_club_tuple, "$.now",      now)
  set_dict_attr(owner_fans_club_tuple, "$.platform", platform)
  # TODO
  set_dict_attr(owner_fans_club_tuple, "$.owner_user_id",  owner_user_id)
  set_dict_attr(owner_fans_club_tuple, "$.room_id",  str(room_id))
  
  try:
    owner_fans_club_tuple_list = list()
    owner_fans_club_tuple_list = owner_fans_club.get_record(owner_fans_club_tuple)
    if len(owner_fans_club_tuple_list) != 0:
      owner_fans_club_tuple = owner_fans_club_tuple_list.pop()
  except Exception as e:
    get_logger().error(f"{e}: {owner_fans_club.get_name()} >> >> >> >> data.room.owner.fans_club")
    owner_fans_club_tuple = dict()

  """
  >> >> >> >> >> >> data.room.owner.fans_club.data.available_gift_ids
  """
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
  fans_club_available_gift_id = FansClubAvailableGiftIdTable(db)
  fans_club_available_gift_id_tuple = {key: None for key in fans_club_available_gift_id.get_tuple()}

  set_dict_attr(fans_club_available_gift_id_tuple, "$.now",            now)
  set_dict_attr(fans_club_available_gift_id_tuple, "$.platform",       platform)
  set_dict_attr(fans_club_available_gift_id_tuple, "$.owner_user_id",  str(owner_user_id))
  set_dict_attr(fans_club_available_gift_id_tuple, "$.room_id",        str(room_id))
  
  try:
    fans_club_available_gift_ids = list()
    fans_club_available_gift_id_list = fans_club_available_gift_id.get_record(fans_club_available_gift_id_tuple, fetchall=True)
    for record in fans_club_available_gift_id_list:
      fans_club_available_gift_ids.insert(get_dict_attr(record, "$.available_gift_id_index"), get_dict_attr(record, "$.available_gift_id"))
  except Exception as e:
    get_logger().error(f"{e}: {fans_club_available_gift_id.get_name()} >> >> >> >> >> >> data.room.owner.fans_club.data.available_gift_ids")
    fans_club_available_gift_ids = []

  """
  >> >> >> >> >> >> data.room.owner.fans_club.data.badge
  """
  badge_icons_label_list       = list()
  badge_icon_pic_label_list    = list()
  badge_icon_avg_color_list    = list()
  badge_icon_flex_setting_list = list()
  badge_icon_height_list       = list()
  badge_icon_image_type_list   = list()
  badge_icon_is_animated_list  = list()
  badge_icon_open_web_url_list = list()
  badge_icon_text_setting_list = list()
  badge_icon_uri_list          = list()
  badge_icon_url_list          = list()
  badge_icon_width_list        = list()
  
  ##
  ## PictureTable
  ##
  icons_prefix   = 'icons'
  badge_icon_pic = PictureTable(db)
  badge_icon_pic_tuple = {key: None for key in badge_icon_pic.get_tuple()}
  
  set_dict_attr(badge_icon_pic_tuple, "$.start_time",  start_time)
  set_dict_attr(badge_icon_pic_tuple, "$.platform",    platform)
  set_dict_attr(badge_icon_pic_tuple, "$.room_id",     str(room_id))

  try:
    badge_icon_pic_tuple_list = badge_icon_pic.get_record(badge_icon_pic_tuple, fetchall=True)
    for badge_icon_pic_tuple in badge_icon_pic_tuple_list:
      badge_icon_pic_label = badge_icon_pic_tuple.get('label', 'unknown')
      if str(badge_icon_pic_label).startswith(icons_prefix):
        badge_icon_pic_label_list.append(badge_icon_pic_label)
        badge_icons_label_list.append(badge_icon_pic_label[len(icons_prefix):])
      else:
        continue
      badge_icon_avg_color_list.append(badge_icon_pic_tuple.get("avg_color", ''))
      badge_icon_height_list.append(badge_icon_pic_tuple.get("height", 0))
      badge_icon_image_type_list.append(badge_icon_pic_tuple.get("image_type", 0))
      badge_icon_is_animated_list.append(badge_icon_pic_tuple.get("is_animated", False))
      badge_icon_open_web_url_list.append(badge_icon_pic_tuple.get("open_web_url", ''))
      badge_icon_uri_list.append(badge_icon_pic_tuple.get("uri", ''))
      badge_icon_width_list.append(badge_icon_pic_tuple.get("width", 0))
  except Exception as e:
    get_logger().error(f"{e}: {fans_club_available_gift_id.get_name()} >> >> >> >> >> >> data.room.owner.fans_club.data.badge")
    badge_icons_label_list.append('')
    badge_icon_pic_label_list.append('')
    badge_icon_avg_color_list.append('')
    badge_icon_height_list.append(0)
    badge_icon_image_type_list.append(0)
    badge_icon_is_animated_list.append(False)
    badge_icon_open_web_url_list.append('')
    badge_icon_uri_list.append('')
    badge_icon_width_list.append(0)

  for badge_icons_label_index in range(0, len(badge_icons_label_list)):
    ##
    ## PictureFlexSettingTable
    ##
    badge_icons_pic_flex_setting = PictureFlexSettingTable(db)
    badge_icons_pic_flex_setting_tuple = {key: None for key in badge_icons_pic_flex_setting.get_tuple()}
    
    set_dict_attr(badge_icons_pic_flex_setting_tuple, "$.uri",        badge_icon_uri_list[badge_icons_label_index])
    set_dict_attr(badge_icons_pic_flex_setting_tuple, "$.platform",   'douyin')
    set_dict_attr(badge_icons_pic_flex_setting_tuple, "$.start_time", start_time)
    set_dict_attr(badge_icons_pic_flex_setting_tuple, "$.room_id",    str(room_id))
    set_dict_attr(badge_icons_pic_flex_setting_tuple, "$.label",      badge_icon_pic_label_list[badge_icons_label_index])
    
    try:
      badge_icons_flex_setting = list()
      badge_icons_pic_flex_setting_tuple_list = badge_icons_pic_flex_setting.get_record(badge_icons_pic_flex_setting_tuple, fetchall=True)
      for flex_setting in badge_icons_pic_flex_setting_tuple_list:
        badge_icons_flex_setting.append(get_dict_attr(flex_setting, "$.flex_setting"))
    except Exception as e:
      get_logger().error(f"{e}: {badge_icons_pic_flex_setting.get_name()} >> >> >> >> >> data.room.owner.badge_image_list.flex_setting_list")
      badge_icons_flex_setting = []
    finally:
      badge_icon_flex_setting_list.append(badge_icons_flex_setting)

    ##
    ## PictureTextSettingTable
    ##    
    badge_icons_pic_text_setting = PictureTextSettingTable(db)
    badge_icons_pic_text_setting_tuple = {key: None for key in badge_icons_pic_text_setting.get_tuple()}
    
    set_dict_attr(badge_icons_pic_text_setting_tuple, "$.uri",        badge_icon_uri_list[badge_icons_label_index])
    set_dict_attr(badge_icons_pic_text_setting_tuple, "$.platform",   'douyin')
    set_dict_attr(badge_icons_pic_text_setting_tuple, "$.start_time", start_time)
    set_dict_attr(badge_icons_pic_text_setting_tuple, "$.room_id",    str(room_id))
    set_dict_attr(badge_icons_pic_text_setting_tuple, "$.label",      badge_icon_pic_label_list[badge_icons_label_index])
    
    try:
      single_badge_icons_pic_text_setting = list()
      badge_icons_pic_text_setting_tuple_list = badge_icons_pic_text_setting.get_record(badge_icons_pic_text_setting_tuple, fetchall=True)
      for text_setting in badge_icons_pic_text_setting_tuple_list:
        single_badge_icons_pic_text_setting.append(get_dict_attr(text_setting, "$.text_setting"))
    except Exception as e:
      get_logger().error(f"{e}: {badge_icons_pic_text_setting.get_name()} >> >> >> >> >> data.room.owner.badge_image_list.text_setting_list")
      single_badge_icons_pic_text_setting = []
    finally:
      badge_icon_text_setting_list.append(single_badge_icons_pic_text_setting)

    ##
    ## PictureUrlTable
    ##
    badge_icons_picture_url       = PictureUrlTable(db)
    badge_icons_picture_url_tuple = {key: None for key in badge_icons_picture_url.get_tuple()}
    
    set_dict_attr(badge_icons_picture_url_tuple, "$.uri",        badge_icon_uri_list[badge_icons_label_index])
    set_dict_attr(badge_icons_picture_url_tuple, "$.platform",   'douyin')
    set_dict_attr(badge_icons_picture_url_tuple, "$.start_time", start_time)
    set_dict_attr(badge_icons_picture_url_tuple, "$.room_id",    str(room_id))
    set_dict_attr(badge_icons_picture_url_tuple, "$.label",      badge_icon_pic_label_list[badge_icons_label_index])
    
    try:
      badge_icons_pic_url_list = list()
      badge_icons_picture_url_tuple_list = badge_icons_picture_url.get_record(badge_icons_picture_url_tuple, fetchall=True)
      for url in badge_icons_picture_url_tuple_list:
        badge_icons_pic_url_list.append(get_dict_attr(url, "$.url"))
    except Exception as e:
      get_logger().error(f"{e}: {badge_icons_picture_url.get_name()} >> >> >> >> >> data.room.owner.badge_image_list.url_list")
      badge_icons_pic_url_list = []
    finally:
      badge_icon_url_list.append(badge_icons_pic_url_list)

  """
  TODO
  >> >> >> data.room.owner.media_badge_image_list
  """
  owner_media_badge_image_list = list()

  """
  TODO
  >> >> >> >> data.room.owner.new_real_time_icons
  """
  owner_new_real_time_icons = list()
  
  """
  >> >> >> >> data.room.owner.own_room
  """
  own_room_flag_table = OwnRoomFlagTable(db)
  own_room_flag_tuple = {key:None for key in own_room_flag_table.get_tuple()}

  set_dict_attr(own_room_flag_tuple, "$.start_time",       start_time)
  set_dict_attr(own_room_flag_tuple, "$.platform",         platform)
  set_dict_attr(own_room_flag_tuple, "$.owner_user_id",    owner_user_id)
  
  try:
    own_room_flag_tuple_list = own_room_flag_table.get_record(own_room_flag_tuple)
    if len(own_room_flag_tuple_list) != 0:
      own_room_flag_tuple = own_room_flag_tuple_list.pop()
  except Exception as e:
    get_logger().error(f"{e}: {own_room_flag_table.get_name()} >> >> >> >> data.room.owner.own_room")
    own_room_flag_tuple = {}
  
  try:
    own_room_exist_flag = bool(get_dict_attr(own_room_flag_tuple, "$.exist_flag"))
  except Exception as e:
    get_logger().error(f"{e}: {own_room_flag_table.get_name()} get exist_flag fail")
    own_room_exist_flag = False

  if own_room_exist_flag is True:
    """
    >> >> >> >> >> data.room.owner.own_room.room_ids
    """
    owner_own_room_id_table = OwnRoomIdTable(db)
    owner_own_room_id_tuple = {key:None for key in owner_own_room_id_table.get_tuple()}
    
    set_dict_attr(owner_own_room_id_tuple, "$.start_time",       start_time)
    set_dict_attr(owner_own_room_id_tuple, "$.platform",         platform)
    set_dict_attr(owner_own_room_id_tuple, "$.owner_user_id",    owner_user_id)
    
    try:
      owner_own_room_id_list = list()
      owner_own_room_id_tuple_list = owner_own_room_id_table.get_record(owner_own_room_id_tuple, fetchall=True)
      for owner_own_room_id in owner_own_room_id_tuple_list:
        owner_own_room_id_list.insert(int(get_dict_attr(owner_own_room_id, "$.room_id_index")), int(get_dict_attr(owner_own_room_id, "$.room_id")))
    except Exception as e:
      get_logger().error(f"{e}: {owner_own_room_id_table.get_name()} >> >> >> >> data.room.owner.own_room.room_ids")
      owner_own_room_id_list = []
    
    """
    TODO
    >> >> >> >> data.room.owner.own_room.room_id_display
    """
    owner_own_room_id_display_list = list()
  
    """
    >> >> >> >> data.room.owner.own_room.room_ids_str
    """
    owner_own_room_id_str_list = [str(room_id) for room_id in owner_own_room_id_list]
  
  """
  TODO
  >> >> >> >> >> data.room.owner.pay_grade.grade_icon_list
  """
  owner_pay_grade_icon_list = list()

  """
  >> >> >> >> >> data.room.owner.pay_grade.new_im_icon_with_level
  """
  ##
  ## PictureTable
  ##
  owner_new_im_icon_with_level_picture       = PictureTable(db)
  owner_new_im_icon_with_level_picture_tuple = {key: None for key in owner_new_im_icon_with_level_picture.get_tuple()}

  set_dict_attr(owner_new_im_icon_with_level_picture_tuple, "$.start_time",  start_time)
  set_dict_attr(owner_new_im_icon_with_level_picture_tuple, "$.platform",    platform)
  set_dict_attr(owner_new_im_icon_with_level_picture_tuple, "$.room_id",     str(room_id))
  set_dict_attr(owner_new_im_icon_with_level_picture_tuple, "$.label",       'new_im_icon_with_level')

  try:
    owner_new_im_icon_with_level_picture_tuple_list = owner_new_im_icon_with_level_picture.get_record(owner_new_im_icon_with_level_picture_tuple)
    if len(owner_new_im_icon_with_level_picture_tuple_list) != 0:
      owner_new_im_icon_with_level_picture_tuple = owner_new_im_icon_with_level_picture_tuple_list.pop()
    else:
      owner_new_im_icon_with_level_picture_tuple = {}
  except Exception as e:
    get_logger().error(f"{e}: {owner_new_im_icon_with_level_picture.get_name()} >> >> >> >> >> data.room.owner.pay_grade.new_im_icon_with_level")
    owner_new_im_icon_with_level_picture_tuple = {}

  """
  >> >> >> >> data.room.owner.pay_grade.new_im_icon_with_level.flex_setting_list
  """
  ##
  ## PictureFlexSettingTable
  ##
  owner_new_im_icon_with_level_flex_setting = PictureFlexSettingTable(db)
  owner_new_im_icon_with_level_flex_setting_tuple = {key: None for key in owner_new_im_icon_with_level_flex_setting.get_tuple()}

  set_dict_attr(owner_new_im_icon_with_level_flex_setting_tuple, "$.uri",         owner_new_im_icon_with_level_picture_tuple.get('uri', ''))
  set_dict_attr(owner_new_im_icon_with_level_flex_setting_tuple, "$.platform",    'douyin')
  set_dict_attr(owner_new_im_icon_with_level_flex_setting_tuple, "$.start_time",  start_time)
  set_dict_attr(owner_new_im_icon_with_level_flex_setting_tuple, "$.room_id",     str(room_id))
  set_dict_attr(owner_new_im_icon_with_level_flex_setting_tuple, "$.label",       'new_im_icon_with_level')

  try:
    owner_new_im_icon_with_level_flex_setting_list = list()
    owner_new_im_icon_with_level_flex_setting_tuple_list = owner_new_im_icon_with_level_flex_setting.get_record(owner_new_im_icon_with_level_flex_setting_tuple, fetchall=True)
    for flex_setting in owner_new_im_icon_with_level_flex_setting_tuple_list:
      owner_new_im_icon_with_level_flex_setting_list.append(get_dict_attr(flex_setting, "$.flex_setting"))
  except Exception as e:
    get_logger().error(f"{e}: {owner_new_im_icon_with_level_flex_setting.get_name()} >> >> >> data.room.owner.new_im_icon_with_level")
    owner_new_im_icon_with_level_flex_setting_list = []

  """
  >> >> >> >> data.room.owner.pay_grade.new_im_icon_with_level.text_setting_list
  """
  ##
  ## PictureTextSettingTable
  ##
  owner_new_im_icon_with_level_pic_text_setting = PictureTextSettingTable(db)
  owner_new_im_icon_with_level_pic_text_setting_tuple = {key: None for key in owner_new_im_icon_with_level_pic_text_setting.get_tuple()}
  
  set_dict_attr(owner_new_im_icon_with_level_pic_text_setting_tuple, "$.uri",         owner_new_im_icon_with_level_picture_tuple.get('uri', ''))
  set_dict_attr(owner_new_im_icon_with_level_pic_text_setting_tuple, "$.platform",    'douyin')
  set_dict_attr(owner_new_im_icon_with_level_pic_text_setting_tuple, "$.start_time",  start_time)
  set_dict_attr(owner_new_im_icon_with_level_pic_text_setting_tuple, "$.room_id",     str(room_id))
  set_dict_attr(owner_new_im_icon_with_level_pic_text_setting_tuple, "$.label",       'new_im_icon_with_level')

  try:
    owner_new_im_icon_with_level_pic_text_setting_list = list()
    owner_new_im_icon_with_level_pic_text_setting_tuple_list = owner_new_im_icon_with_level_pic_text_setting.get_record(owner_new_im_icon_with_level_pic_text_setting_tuple, fetchall=True)
    for text_setting in owner_new_im_icon_with_level_pic_text_setting_tuple_list:
      owner_new_im_icon_with_level_pic_text_setting_list.append(get_dict_attr(text_setting, "$.text_setting"))
  except Exception as e:
    get_logger().error(f"{e}: {owner_new_im_icon_with_level_pic_text_setting.get_name()} >> >> >> >> data.room.owner.pay_grade.new_im_icon_with_level.text_setting_list")
    owner_new_im_icon_with_level_pic_text_setting_list = []

  """
  >> >> >> >> data.room.owner_new_im_icon_with_level.url_list
  """
  ##
  ## PictureUrlTable
  ##
  owner_new_im_icon_with_level_picture_url       = PictureUrlTable(db)
  owner_new_im_icon_with_level_picture_url_tuple = {key: None for key in owner_new_im_icon_with_level_picture_url.get_tuple()}
  
  set_dict_attr(owner_new_im_icon_with_level_picture_url_tuple, "$.uri",         owner_new_im_icon_with_level_picture_tuple.get('uri', ''))
  set_dict_attr(owner_new_im_icon_with_level_picture_url_tuple, "$.platform",    'douyin')
  set_dict_attr(owner_new_im_icon_with_level_picture_url_tuple, "$.start_time",  start_time)
  set_dict_attr(owner_new_im_icon_with_level_picture_url_tuple, "$.room_id",     str(room_id))
  set_dict_attr(owner_new_im_icon_with_level_picture_url_tuple, "$.label",       'new_im_icon_with_level')
  
  try:
    owner_new_im_icon_with_level_picture_url_list = list()
    owner_new_im_icon_with_level_picture_url_tuple_list = owner_new_im_icon_with_level_picture_url.get_record(owner_new_im_icon_with_level_picture_url_tuple, fetchall=True)
    for url in owner_new_im_icon_with_level_picture_url_tuple_list:
      owner_new_im_icon_with_level_picture_url_list.append(get_dict_attr(url, "$.url"))
  except Exception as e:
    get_logger().error(f"{e}: {owner_new_im_icon_with_level_picture_url.get_name()} >> >> >> >> data.room.owner_new_im_icon_with_level.url_list")
    owner_new_im_icon_with_level_picture_url_list = []

  """
  >> >> >> >> >> data.room.owner.pay_grade.new_live_icon
  """
  ##
  ## PictureTable
  ##
  owner_new_live_icon_picture       = PictureTable(db)
  owner_new_live_icon_picture_tuple = {key: None for key in owner_new_live_icon_picture.get_tuple()}

  set_dict_attr(owner_new_live_icon_picture_tuple, "$.start_time",  start_time)
  set_dict_attr(owner_new_live_icon_picture_tuple, "$.platform",    platform)
  set_dict_attr(owner_new_live_icon_picture_tuple, "$.room_id",     str(room_id))
  set_dict_attr(owner_new_live_icon_picture_tuple, "$.label",       'new_live_icon')

  try:
    owner_new_live_icon_picture_tuple_list = owner_new_live_icon_picture.get_record(owner_new_live_icon_picture_tuple)
    if len(owner_new_live_icon_picture_tuple_list) != 0:
      owner_new_live_icon_picture_tuple = owner_new_live_icon_picture_tuple_list.pop()
    else:
      owner_new_live_icon_picture_tuple = {}
  except Exception as e:
    get_logger().error(f"{e}: {owner_new_live_icon_picture.get_name()} >> >> >> >> >> data.room.owner.pay_grade.new_live_icon")
    owner_new_live_icon_picture_tuple = {}

  """
  >> >> >> >> data.room.owner.pay_grade.new_live_icon.flex_setting_list
  """
  ##
  ## PictureFlexSettingTable
  ##
  owner_new_live_icon_flex_setting = PictureFlexSettingTable(db)
  owner_new_live_icon_flex_setting_tuple = {key: None for key in owner_new_live_icon_flex_setting.get_tuple()}

  set_dict_attr(owner_new_live_icon_flex_setting_tuple, "$.uri",         owner_new_live_icon_picture_tuple.get('uri', ''))
  set_dict_attr(owner_new_live_icon_flex_setting_tuple, "$.platform",    'douyin')
  set_dict_attr(owner_new_live_icon_flex_setting_tuple, "$.start_time",  start_time)
  set_dict_attr(owner_new_live_icon_flex_setting_tuple, "$.room_id",     str(room_id))
  set_dict_attr(owner_new_live_icon_flex_setting_tuple, "$.label",       'new_live_icon')

  try:
    owner_new_live_icon_flex_setting_list = list()
    owner_new_live_icon_flex_setting_tuple_list = owner_new_live_icon_flex_setting.get_record(owner_new_live_icon_flex_setting_tuple, fetchall=True)
    for flex_setting in owner_new_live_icon_flex_setting_tuple_list:
      owner_new_live_icon_flex_setting_list.append(get_dict_attr(flex_setting, "$.flex_setting"))
  except Exception as e:
    get_logger().error(f"{e}: {owner_new_live_icon_flex_setting.get_name()} >> >> >> data.room.owner.new_live_icon")
    owner_new_live_icon_flex_setting_list = []

  """
  >> >> >> >> data.room.owner.pay_grade.new_live_icon.text_setting_list
  """
  ##
  ## PictureTextSettingTable
  ##
  owner_new_live_icon_pic_text_setting = PictureTextSettingTable(db)
  owner_new_live_icon_pic_text_setting_tuple = {key: None for key in owner_new_live_icon_pic_text_setting.get_tuple()}
  
  set_dict_attr(owner_new_live_icon_pic_text_setting_tuple, "$.uri",         owner_new_live_icon_picture_tuple.get('uri', ''))
  set_dict_attr(owner_new_live_icon_pic_text_setting_tuple, "$.platform",    'douyin')
  set_dict_attr(owner_new_live_icon_pic_text_setting_tuple, "$.start_time",  start_time)
  set_dict_attr(owner_new_live_icon_pic_text_setting_tuple, "$.room_id",     str(room_id))
  set_dict_attr(owner_new_live_icon_pic_text_setting_tuple, "$.label",       'new_live_icon')

  try:
    owner_new_live_icon_pic_text_setting_list = list()
    owner_new_live_icon_pic_text_setting_tuple_list = owner_new_live_icon_pic_text_setting.get_record(owner_new_live_icon_pic_text_setting_tuple, fetchall=True)
    for text_setting in owner_new_live_icon_pic_text_setting_tuple_list:
      owner_new_live_icon_pic_text_setting_list.append(get_dict_attr(text_setting, "$.text_setting"))
  except Exception as e:
    get_logger().error(f"{e}: {owner_new_live_icon_pic_text_setting.get_name()} >> >> >> >> data.room.owner.pay_grade.new_live_icon.text_setting_list")
    owner_new_live_icon_pic_text_setting_list = []

  """
  >> >> >> >> data.room.owner_new_live_icon.url_list
  """
  ##
  ## PictureUrlTable
  ##
  owner_new_live_icon_picture_url       = PictureUrlTable(db)
  owner_new_live_icon_picture_url_tuple = {key: None for key in owner_new_live_icon_picture_url.get_tuple()}
  
  set_dict_attr(owner_new_live_icon_picture_url_tuple, "$.uri",        owner_new_live_icon_picture_tuple.get('uri', ''))
  set_dict_attr(owner_new_live_icon_picture_url_tuple, "$.platform",   'douyin')
  set_dict_attr(owner_new_live_icon_picture_url_tuple, "$.start_time", start_time)
  set_dict_attr(owner_new_live_icon_picture_url_tuple, "$.room_id",    str(room_id))
  set_dict_attr(owner_new_live_icon_picture_url_tuple, "$.label",      'new_live_icon')
  
  try:
    owner_new_live_icon_picture_url_list = list()
    owner_new_live_icon_picture_url_tuple_list = owner_new_live_icon_picture_url.get_record(owner_new_live_icon_picture_url_tuple, fetchall=True)
    for url in owner_new_live_icon_picture_url_tuple_list:
      owner_new_live_icon_picture_url_list.append(get_dict_attr(url, "$.url"))
  except Exception as e:
    get_logger().error(f"{e}: {owner_new_live_icon_picture_url.get_name()} >> >> >> >> data.room.owner_new_live_icon.url_list")
    owner_new_live_icon_picture_url_list = []

  """
  TODO
  >> >> >> >> data.room.owner.real_time_icons
  """
  owner_real_time_icons = list()

  """
  >> >> >> >> data.room.owner.subscribe
  """
  owner_subscribe = RoomSubscribeTable(db)
  owner_subscribe_tuple = {key: None for key in owner_subscribe.get_tuple()}

  set_dict_attr(owner_subscribe_tuple, "$.now",      now)
  set_dict_attr(owner_subscribe_tuple, "$.platform", platform)
  set_dict_attr(owner_subscribe_tuple, "$.room_id",  str(room_id))
  set_dict_attr(owner_subscribe_tuple, "$.owner_user_id",  owner_user_id)
  
  try:
    owner_subscribe_tuple_list = owner_subscribe.get_record(owner_subscribe_tuple)
    if len(owner_subscribe_tuple_list) != 0:
      owner_subscribe_tuple = owner_subscribe_tuple_list.pop()
  except Exception as e:
    get_logger().error(f"{e}: {owner_subscribe.get_name()} >> >> >> >> data.room.owner.subscribe")
    owner_subscribe_tuple = dict()

  """
  TODO
  >> >> >> data.room.owner.top_fans
  """
  owner_top_fans = list()

  """
  >> >> >> >> data.room.owner.user_attr
  """
  owner_user_attr = RoomOwnerUserAttrTable(db)
  owner_user_attr_tuple = {key: None for key in owner_user_attr.get_tuple()}
  
  set_dict_attr(owner_user_attr_tuple, "$.now",      now)
  set_dict_attr(owner_user_attr_tuple, "$.platform", platform)
  set_dict_attr(owner_user_attr_tuple, "$.room_id",  str(room_id))
  set_dict_attr(owner_user_attr_tuple, "$.owner_user_id",  owner_user_id)

  try:
    owner_user_attr_tuple_list = owner_user_attr.get_record(owner_user_attr_tuple)
    if len(owner_user_attr_tuple_list) != 0:
      owner_user_attr_tuple = owner_user_attr_tuple_list.pop()
  except Exception as e:
    get_logger().error(f"{e}: {owner_user_attr.get_name()} >> >> >> >> data.room.owner.user_attr")
    owner_user_attr_tuple = dict()
    
  """
  >> >> >> >> >> data.room.owner.user_attr.admin_privileges

  +-----------------------+-------------------+------+-----+---------+-------+------------------------------------------------+---------------------+
  | Field                 | Type              | Null | Key | Default | Extra | Topology                                       | Comment             |
  +-----------------------+-------------------+------+-----+---------+-------+------------------------------------------------+---------------------+
  | now                   | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"                                  | 当前时间戳           | 
  | platform              | varchar(20)       | NO   | PRI |         |       |           -                                    | 平台                 | 
  | room_id               | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                               | 直播间ID             | 
  | owner_user_id         | varchar(200)      | NO   | PRI |         |       | "$.data.room.owner_user_id"                    | 直播间主播ID         |
  | admin_privilege_index | unsigned bigint   | NO   | PRI |         |       |           -                                    | 管理员权限序号       | 
  | admin_privilege       | text              |      |     | NULL    |       | "$.data.room.owner.user_attr.admin_privileges" | 管理员权限列表       |
  +-----------------------+-------------------+------+-----+---------+-------+------------------------------------------------+---------------------+
  """
  owner_user_attr_admin_privileges = RoomAdminPrivilegeTable(db)
  owner_user_attr_admin_privileges_tuple = {key: None for key in owner_user_attr_admin_privileges.get_tuple()}
  
  set_dict_attr(owner_user_attr_admin_privileges_tuple, "$.now",      now)
  set_dict_attr(owner_user_attr_admin_privileges_tuple, "$.platform", platform)
  set_dict_attr(owner_user_attr_admin_privileges_tuple, "$.room_id",  str(room_id))
  set_dict_attr(owner_user_attr_admin_privileges_tuple, "$.owner_user_id",  owner_user_id)
  
  try:
    owner_user_attr_admin_privileges_list = list()
    owner_user_attr_admin_privileges_tuple_list = owner_user_attr_admin_privileges.get_record(owner_user_attr_admin_privileges_tuple, fetchall=True)
    for record in owner_user_attr_admin_privileges_tuple_list:
      owner_user_attr_admin_privileges_list.append(get_dict_attr(record, "$.admin_privilege"))
  except Exception as e:
    get_logger().error(f"{e}: {owner_user_attr_admin_privileges.get_name()} >> >> >> >> >> data.room.owner.user_attr.admin_privileges")
    owner_user_attr_admin_privileges_list = []
  
  """
  >> >> >> >> data.room.owner.user_dress_info
  """
  
  """
  >> >> >> >> data.room.owner.user_dress_info.dress_own_ids
  """
  owner_dress_own_ids = RoomOwnerUserDressOwnIdTable(db)
  owner_dress_own_ids_tuple = {key: None for key in owner_dress_own_ids.get_tuple()}
  
  set_dict_attr(owner_dress_own_ids_tuple, "$.start_time",  start_time)
  set_dict_attr(owner_dress_own_ids_tuple, "$.platform", platform)
  set_dict_attr(owner_dress_own_ids_tuple, "$.room_id",  str(room_id))
  set_dict_attr(owner_dress_own_ids_tuple, "$.owner_user_id",  owner_user_id)
  
  try:
    owner_dress_own_ids_list = list()
    owner_dress_own_ids_tuple_list = owner_dress_own_ids.get_record(owner_dress_own_ids_tuple, fetchall=True)
    for record in owner_dress_own_ids_tuple_list:
      owner_dress_own_ids_list.append(get_dict_attr(record, "$.dress_own_id"))
  except Exception as e:
    get_logger().error(f"{e}: {owner_dress_own_ids.get_name()} >> >> >> >> >> data.room.owner.user_dress_info.dress_own_ids")
    owner_dress_own_ids_list = []

  """
  >> >> >> >> data.room.owner.user_dress_info.dress_wear_ids
  """
  owner_dress_wear_ids = RoomOwnerDressWearIdTable(db)
  owner_dress_wear_ids_tuple = {key: None for key in owner_dress_wear_ids.get_tuple()}
  
  set_dict_attr(owner_dress_wear_ids_tuple, "$.start_time",  start_time)
  set_dict_attr(owner_dress_wear_ids_tuple, "$.platform", platform)
  set_dict_attr(owner_dress_wear_ids_tuple, "$.room_id",  str(room_id))
  set_dict_attr(owner_dress_wear_ids_tuple, "$.owner_user_id",  owner_user_id)
  
  try:
    owner_dress_wear_ids_list = list()
    owner_dress_wear_ids_tuple_list = owner_dress_wear_ids.get_record(owner_dress_wear_ids_tuple, fetchall=True)
    for record in owner_dress_wear_ids_tuple_list:
      owner_dress_wear_ids_list.append(get_dict_attr(record, "$.dress_wear_id"))
  except Exception as e:
    get_logger().error(f"{e}: {owner_dress_wear_ids.get_name()} >> >> >> >> >> data.room.owner.user_dress_info.dress_wear_ids")
    owner_dress_wear_ids_list = []

  """
  >> >> >> data.room.pack_meta
  """
  pack_meta       = RoomPackMetaTable(db)
  pack_meta_tuple = {key: None for key in pack_meta.get_tuple()}
  
  set_dict_attr(pack_meta_tuple, "$.now",      now)
  set_dict_attr(pack_meta_tuple, "$.platform", platform)
  set_dict_attr(pack_meta_tuple, "$.room_id",  str(room_id))
  
  try:
    pack_meta_tuple_list = pack_meta.get_record(pack_meta_tuple)
    if len(pack_meta_tuple_list) != 0:
      pack_meta_tuple = pack_meta_tuple_list.pop()
  except Exception as e:
    get_logger().error(f"{e}: {pack_meta.get_name()} >> >> data.room.pack_meta")
    pack_meta_tuple = dict()

  """
  >> >> >> data.room.paid_live_data
  +----------------------------------+-------------------+------+-----+---------+-------+------------------------------------------------------+---------------------+
  | Field                            | Type              | Null | Key | Default | Extra | Topology                                             | Comment             |
  +----------------------------------+-------------------+------+-----+---------+-------+------------------------------------------------------+---------------------+
  | now                              | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"                                        | 当前时间戳           | 
  | platform                         | varchar(20)       | NO   | PRI |         |       |           -                                          | 平台                 | 
  | room_id                          | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                                     | 直播间ID             | 
  | anchor_right                     | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.paid_live_data.anchor_right"            | 主播权限             |
  | delivery                         | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.paid_live_data.delivery"                | 交付状态             |
  | duration                         | unsigned int      | YES  |     | NULL    |       | "$.data.room.paid_live_data.duration"                | 直播时长             |
  | max_preview_duration             | unsigned int      | YES  |     | NULL    |       | "$.data.room.paid_live_data.max_preview_duration"    | 最大预览时长          |
  | need_delivery_notice             | bool              | YES  |     | NULL    |       | "$.data.room.paid_live_data.need_delivery_notice"    | 是否需要交付通知      |
  | paid_type                        | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.paid_live_data.paid_type"               | 付费类型             |
  | pay_ab_type                      | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.paid_live_data.pay_ab_type"             | 付费AB类型           |
  | privilege_info                   | json              | YES  |     | NULL    |       | "$.data.room.paid_live_data.privilege_info"          | 特权信息             |
  | privilege_info_map               | json              | YES  |     | NULL    |       | "$.data.room.paid_live_data.privilege_info_map"      | 特权信息映射         |
  | view_right                       | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.paid_live_data.view_right"              | 观看权限             |
  +----------------------------------+-------------------+------+-----+---------+-------+------------------------------------------------------+---------------------+
  """
  paid_live_data       = RoomPaidLiveDataTable(db)
  paid_live_data_tuple = {key: None for key in paid_live_data.get_tuple()}

  set_dict_attr(paid_live_data_tuple, "$.now",      now)
  set_dict_attr(paid_live_data_tuple, "$.platform", platform)
  set_dict_attr(paid_live_data_tuple, "$.room_id",  str(room_id))

  try:
    paid_live_data_tuple_list = paid_live_data.get_record(paid_live_data_tuple)
    if len(paid_live_data_tuple_list) != 0:
      paid_live_data_tuple = paid_live_data_tuple_list.pop()
  except Exception as e:
    get_logger().error(f"{e}: {paid_live_data.get_name()} >> >> >> data.room.paid_live_data")
    paid_live_data_tuple = dict()

  """
  >> >> data.room.room_auth
  +----------------------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------+
  | Field                            | Type              | Null | Key | Default | Extra | Topology                                                 | Comment              |
  +----------------------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------+
  | now                              | timestamp         | YES  | PRI |         |       | "$.extra.now"                                            | 当前时间戳            | 
  | platform                         | varchar(20)       |      | PRI | NULL    |       |           -                                              | 平台                  |
  | room_id                          | varchar(200)      |      |     |         |       | "$.data.room.id"                                         | 直播间ID              | 
  | AIClone                          | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.AIClone"                          | AI克隆                | 
  | AdminCommentWall                 | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.AdminCommentWall"                 | 管理员评论墙          | 
  | AnchorAudioChat                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.AnchorAudioChat"                  | 主播音频聊天          | 
  | AnchorColdMessageTiled           | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.AnchorColdMessageTiled"           | 主播冷消息平铺        | 
  | AnchorHotMessageAggregated       | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.AnchorHotMessageAggregated"       | 主播热消息聚合        | 
  | AnchorMission                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.AnchorMission"                    | 主播任务             | 
  | AudioChat                        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.AudioChat"                        | 音频聊天             | 
  | AudioChatTotext                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.AudioChatTotext"                  | 音频聊天转文本        | 
  | Banner                           | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Banner"                           | 横幅                 | 
  | BulletStyle                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.BulletStyle"                      | 弹幕样式              | 
  | CanSellTicket                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.CanSellTicket"                    | 是否可以售票          | 
  | CastScreen                       | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.CastScreen"                       | 屏幕投射             | 
  | CastScreenExplicit               | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.CastScreenExplicit"               | 屏幕投射显式          | 
  | Chat                             | bool              |      |     |         |       | "$.data.room.room_auth.Chat"                             | 聊天                 | 
  | ChatDispatch                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatDispatch"                     | 聊天分发             | 
  | ChatDynamicSlideSpeed            | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatDynamicSlideSpeed"            | 聊天动态滑动速度      | 
  | ChatDynamicSlideSpeedAnchor      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatDynamicSlideSpeedAnchor"      | 主播聊天动态滑动速度   | 
  | ChatGuideEmoji                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatGuideEmoji"                   | 聊天引导表情          |
  | ChatGuideImage                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatGuideImage"                   | 聊天引导图片          |
  | ChatIdentity                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatIdentity"                     | 聊天身份              |
  | ChatMention                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatMention"                      | 聊天提及             |
  | ChatMentionV2                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatMentionV2"                    | 聊天提及V2            |
  | ChatOperate                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatOperate"                      | 聊天操作             |
  | ChatReply                        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatReply"                        | 聊天回复              |
  | ClearEntranceOption              | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ClearEntranceOption"              | 清除入口选项          |
  | Collect                          | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Collect"                          | 收藏                 |
  | CommentWall                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.CommentWall"                      | 评论墙               |
  | CommerceCard                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.CommerceCard"                     | 商业卡片             |
  | CommerceComponent                | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.CommerceComponent"                | 商业组件             |
  | CommonCard                       | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.CommonCard"                       | 通用卡片             |
  | CountType                        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.CountType"                        | 计数类型             | 
  | Danmaku                          | bool              |      |     |         |       | "$.data.room.room_auth.Danmaku"                          | 弹幕                 | 
  | DanmakuDefault                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.DanmakuDefault"                   | 弹幕默认             | 
  | Denounce                         | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Denounce"                         | 举报                 | 
  | Digg                             | bool              |      |     |         |       | "$.data.room.room_auth.Digg"                             | 点赞                 | 
  | Dislike                          | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Dislike"                          | 不喜欢               | 
  | DonationSticker                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.DonationSticker"                  | 捐赠贴纸             | 
  | DouPlus                          | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.DouPlus"                          | DouPlus             | 
  | DouPlusPopularityGem             | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.DouPlusPopularityGem"             | DouPlus人气宝石      | 
  | DownloadVideo                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.DownloadVideo"                    | 下载视频             | 
  | EcomFansClub                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.EcomFansClub"                     | 电商粉丝俱乐部        | 
  | EmojiOutside                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.EmojiOutside"                     | 外部表情             | 
  | EnhancedTouch                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.EnhancedTouch"                    | 增强触摸             | 
  | EnterEffects                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.EnterEffects"                     | 进入效果             | 
  | ExpandScreen                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ExpandScreen"                     | 扩展屏幕             | 
  | FansClub                         | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FansClub"                         | 粉丝俱乐部           | 
  | FansClubBlessing                 | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FansClubBlessing"                 | 粉丝俱乐部祝福        | 
  | FansClubDeclaration              | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FansClubDeclaration"              | 粉丝俱乐部宣言        | 
  | FansClubLetter                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FansClubLetter"                   | 粉丝俱乐部信件        | 
  | FansClubNotice                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FansClubNotice"                   | 粉丝俱乐部通知        | 
  | FansGroup                        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FansGroup"                        | 粉丝群               | 
  | FeaturedPublicScreen             | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FeaturedPublicScreen"             | 精选公共屏幕          | 
  | FirstFeedHistChat                | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FirstFeedHistChat"                | 首次Feed历史聊天      | 
  | FixedChat                        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FixedChat"                        | 固定聊天             | 
  | FrequentlyChat                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FrequentlyChat"                   | 常用聊天             | 
  | FusionEmoji                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FusionEmoji"                      | 融合表情             | 
  | GamePointsPlaying                | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.GamePointsPlaying"                | 游戏积分玩法          | 
  | Gift                             | bool              |      |     |         |       | "$.data.room.room_auth.Gift"                             | 礼物                 | 
  | GiftAnchorMt                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.GiftAnchorMt"                     | 主播礼物MT           | 
  | GiftVote                         | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.GiftVote"                         | 礼物投票             | 
  | Highlights                       | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Highlights"                       | 精彩片段             | 
  | HostTeam                         | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.HostTeam"                         | 主播团队             | 
  | HostTeamChannel                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.HostTeamChannel"                  | 主播团队频道          | 
  | HotChatTray                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.HotChatTray"                      | 热聊天托盘            | 
  | HourRank                         | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.HourRank"                         | 小时排行榜            | 
  | ImHeatValue                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ImHeatValue"                      | IM热值               | 
  | IndustryService                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.IndustryService"                  | 行业服务             | 
  | InteractionGift                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.InteractionGift"                  | 互动礼物             | 
  | InteractiveComponent             | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.InteractiveComponent"             | 互动组件             | 
  | ItemShare                        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ItemShare"                        | 物品分享             | 
  | KtvOrderSong                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.KtvOrderSong"                     | KTV点歌              | 
  | Landscape                        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Landscape"                        | 横屏                 | 
  | LandscapeChat                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.LandscapeChat"                    | 横屏聊天             | 
  | LandscapeChatDynamicSlideSpeed   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.LandscapeChatDynamicSlideSpeed"   | 横屏聊天动态滑动速度   | 
  | LandscapeGift                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.LandscapeGift"                    | 横屏礼物             | 
  | LandscapeScreenCapture           | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.LandscapeScreenCapture"           | 横屏屏幕截图          | 
  | LandscapeScreenRecording         | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.LandscapeScreenRecording"         | 横屏屏幕录制          | 
  | LandscapeScreenShare             | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.LandscapeScreenShare"             | 横屏屏幕分享          | 
  | `Like`                           | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Like"                             | 点赞                 | 
  | LinkmicGuestLike                 | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.LinkmicGuestLike"                 | 连麦嘉宾点赞          | 
  | LongPressOption                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.LongPressOption"                  | 长按选项              | 
  | LongTouch                        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.LongTouch"                        | 长按触摸              | 
  | LuckMoney                        | bool              |      |     |         |       | "$.data.room.room_auth.LuckMoney"                        | 红包                 | 
  | MarkUser                         | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MarkUser"                         | 标记用户             | 
  | MediaHistoryMessage              | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MediaHistoryMessage"              | 媒体历史消息          | 
  | MediaLinkmic                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MediaLinkmic"                     | 媒体连麦             | 
  | MessageDispatch                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MessageDispatch"                  | 消息分发             | 
  | MessageGift                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MessageGift"                      | 消息礼物             | 
  | MissionCenter                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MissionCenter"                    | 任务中心             | 
  | MoreAnchor                       | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MoreAnchor"                       | 更多主播             | 
  | MoreHistChat                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MoreHistChat"                     | 更多历史聊天          | 
  | MultiplierPlayback               | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MultiplierPlayback"               | 倍速播放             | 
  | MyLiveEntrance                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MyLiveEntrance"                   | 我的直播入口          | 
  | OnlyTa                           | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.OnlyTa"                           | 仅限TA               | 
  | PCPlay                           | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.PCPlay"                           | PC播放               | 
  | POI                              | bool              |      |     |         |       | "$.data.room.room_auth.POI"                              | POI                  | 
  | PadPlay                          | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.PadPlay"                          | 平板播放             | 
  | PanelECService                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.PanelECService"                   | 面板EC服务           | 
  | PlayerRankList                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.PlayerRankList"                   | 播放器排行榜列表      | 
  | Poster                           | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Poster"                           | 海报                 | 
  | PosterCache                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.PosterCache"                      | 海报缓存             | 
  | PreviewChatExpose                | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.PreviewChatExpose"                | 预览聊天曝光          | 
  | PreviewHotCommentSwitch          | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.PreviewHotCommentSwitch"          | 预览热评论开关        | 
  | ProjectionBtn                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ProjectionBtn"                    | 投影按钮             | 
  | Props                            | bool              |      |     |         |       | "$.data.room.room_auth.Props"                            | 道具                 | 
  | PublicScreen                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.PublicScreen"                     | 公共屏幕             | 
  | QuizGamePointsPlaying            | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.QuizGamePointsPlaying"            | 测验游戏积分玩法      | 
  | RecordScreen                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.RecordScreen"                     | 录制屏幕             | 
  | RoomChannel                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.RoomChannel"                      | 直播间频道            | 
  | RoomChatLikeDisplay              | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.RoomChatLikeDisplay"              | 直播间聊天点赞显示    | 
  | RoomChatOperatePanel             | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.RoomChatOperatePanel"             | 直播间聊天操作面板    | 
  | RoomContributor                  | bool              |      |     |         |       | "$.data.room.room_auth.RoomContributor"                  | 直播间贡献者          | 
  | RoomWidget                       | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.RoomWidget"                       | 直播间小部件          | 
  | ScreenBottomInfo                 | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ScreenBottomInfo"                 | 屏幕底部信息          | 
  | ScreenProjectionBarrage          | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ScreenProjectionBarrage"          | 屏幕投影弹幕          | 
  | Seek                             | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Seek"                             | 寻找                 | 
  | Selection                        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Selection"                        | 选择                 | 
  | SelectionAlbum                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.SelectionAlbum"                   | 选择相册             | 
  | Share                            | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Share"                            | 分享                 | 
  | ShortTouch                       | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ShortTouch"                       | 短触摸               | 
  | ShortTouchTempState              | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ShortTouchTempState"              | 短触摸临时状态        | 
  | ShowGamePlugin                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ShowGamePlugin"                   | 显示游戏插件          | 
  | ShowQualification                | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ShowQualification"                | 显示资格             | 
  | SmallWindowDisplay               | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.SmallWindowDisplay"               | 小窗口显示            | 
  | SmallWindowPlayer                | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.SmallWindowPlayer"                | 小窗口播放器          | 
  | StickyMessage                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.StickyMessage"                    | 固定消息             | 
  | StreamAdaptation                 | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.StreamAdaptation"                 | 流适应               | 
  | StrokeUpDownGuide                | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.StrokeUpDownGuide"                | 上下滑动引导          | 
  | SubscribeCardPackage             | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.SubscribeCardPackage"             | 订阅卡包             | 
  | Teleprompter                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Teleprompter"                     | 提词器               | 
  | TextGift                         | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.TextGift"                         | 文本礼物             | 
  | TimedShutdown                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.TimedShutdown"                    | 定时关机             | 
  | ToolbarBubble                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ToolbarBubble"                    | 工具栏气泡            | 
  | Topic                            | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Topic"                            | 话题                 | 
  | TypingCommentState               | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.TypingCommentState"               | 输入评论状态          | 
  | UgcVSReplayDelete                | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.UgcVSReplayDelete"                | Ugc VS回放删除        | 
  | UgcVsReplayVisibility            | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.UgcVsReplayVisibility"            | Ugc VS回放可见性      | 
  | UpRightStatsFloatingLayer        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.UpRightStatsFloatingLayer"        | 右上角统计浮动层      | 
  | UseHostInfo                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.UseHostInfo"                      | 使用主机信息          | 
  | UserCard                         | bool              |      |     |         |       | "$.data.room.room_auth.UserCard"                         | 用户卡片              | 
  | UserCorner                       | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.UserCorner"                       | 用户角落              | 
  | VSGift                           | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VSGift"                           | VS礼物               | 
  | VSRank                           | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VSRank"                           | VS排行榜             | 
  | VSTopic                          | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VSTopic"                          | VS话题               | 
  | VerticalRank                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VerticalRank"                     | 垂直排行榜            | 
  | VerticalScreenShare              | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VerticalScreenShare"              | 垂直屏幕分享          | 
  | VideoAmplificationType           | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VideoAmplificationType"           | 视频放大类型          | 
  | VideoShare                       | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VideoShare"                       | 视频分享             | 
  | VsCommentBar                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VsCommentBar"                     | VS评论栏             | 
  | VsDouPlus                        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VsDouPlus"                        | VS DouPlus           | 
  | VsExtensionEnableFollow          | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VsExtensionEnableFollow"          | VS扩展启用关注        | 
  | VsFansClub                       | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VsFansClub"                       | VS粉丝俱乐部          | 
  | VsWelcomeDanmaku                 | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VsWelcomeDanmaku"                 | VS欢迎弹幕            | 
  | WordAssociation                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.WordAssociation"                  | 词关联                | 
  +----------------------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------+
  """
  room_auth = RoomAuthTable(db)
  room_auth_tuple = {key: None for key in room_auth.get_tuple()}

  set_dict_attr(room_auth_tuple, "$.now",      now)
  set_dict_attr(room_auth_tuple, "$.platform", platform)
  set_dict_attr(room_auth_tuple, "$.room_id",  str(room_id))
  
  try:
    room_auth_tuple_list = room_auth.get_record(room_auth_tuple)
    if len(room_auth_tuple_list) != 0:
      room_auth_tuple = room_auth_tuple_list.pop()
  except Exception as e:
    get_logger().error(f"{e}: {room_auth.get_name()} >> >> >> data.room.room_auth")
    room_auth_tuple = dict()

  """
  >> >> >> data.room.room_tabs
  +-----------+-------------------+------+-----+---------+-------+-------------------------+----------------------+
  | Field     | Type              | Null | Key | Default | Extra | Topology                | Comment              |
  +-----------+-------------------+------+-----+---------+-------+-------------------------+----------------------+
  | now       | timestamp         | NO   | PRI |         |       | "$.extra.now"           | 当前时间戳            | 
  | platform  | varchar(20)       | NO   | PRI |         |       |           -             | 平台                  |
  | room_id   | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"        | 直播间ID              | 
  | tab_index | unsigned bigint   |      |     | NULL    |       |           -             | tab序号               |
  | room_tab  | TBD               |      |     | NULL    |       | "$.data.room.room_tabs" | 直播间标签列表         |
  +-----------+-------------------+------+-----+---------+-------+-------------------------+----------------------+

  room_tabs = RoomTabTable(db)
  room_tabs_tuple = {key: None for key in room_tabs.get_tuple()}
  
  set_dict_attr(room_tabs_tuple, "$.now",      now)
  set_dict_attr(room_tabs_tuple, "$.platform", platform)
  set_dict_attr(room_tabs_tuple, "$.room_id",  str(room_id))
  
  try:
    room_tab_list = list()
    room_tabs_tuple_list = room_tabs.get_record(room_tabs_tuple, fetchall=True)
    if len(room_tabs_tuple_list) != 0:
      for room_tab in room_tabs_tuple_list:
        room_tab_list.append(get_dict_attr(room_tab, "$.room_tab"))
    else:
      room_tab_list = []      
  except Exception as e:
    get_logger().error(f"{e}: {room_tabs.get_name()} >> >> >> data.room.room_tabs")
    room_tab_list = []
  """
  room_tab_list = list()

  """
  >> >> data.room.room_view_stats
  +-------------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------+---------------------+
  | Field                               | Type              | Null | Key | Default | Extra | Topology                                               | Comment             |
  +-------------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------+---------------------+
  | view_stats_display_long             | tinytext          |      |     | NULL    |       | "$.data.room.room_view_stats.display_long"             | 直播间观看人数       | 
  | view_stats_display_long_anchor      | tinytext          |      |     | NULL    |       | "$.data.room.room_view_stats.display_long_anchor"      | 主播观看人数         | 
  | view_stats_display_middle           | tinytext          |      |     | NULL    |       | "$.data.room.room_view_stats.display_middle"           | 直播间观看人数（中）  |
  | view_stats_display_middle_anchor    | tinytext          |      |     | NULL    |       | "$.data.room.room_view_stats.display_middle_anchor"    | 主播观看人数（中）    |
  | view_stats_display_short            | tinytext          |      |     | NULL    |       | "$.data.room.room_view_stats.display_short"            | 直播间观看人数（短）  |
  | view_stats_display_short_anchor     | tinytext          |      |     | NULL    |       | "$.data.room.room_view_stats.display_short_anchor"     | 主播观看人数（短）    |
  | view_stats_display_type             | unsigned tinyint  |      |     | NULL    |       | "$.data.room.room_view_stats.display_type"             | 直播间观看人数显示类型 |
  | view_stats_display_value            | unsigned int      |      |     | NULL    |       | "$.data.room.room_view_stats.display_value"            | 直播间观看人数        |
  | view_stats_display_version          | varchar(20)       |      |     | NULL    |       | "$.data.room.room_view_stats.display_version"          | 直播间观看人数显示版本 |
  | view_stats_incremental              | bool              |      |     | NULL    |       | "$.data.room.room_view_stats.incremental"              | 是否增量更新          |
  | view_stats_is_hidden                | bool              |      |     | NULL    |       | "$.data.room.room_view_stats.is_hidden"                | 是否隐藏状态          |
  +-------------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------+---------------------+
  """

  """
  >> >> >> data.room.sharing_music_id_list
  +---------------------+------------------+------+-----+---------+-------+-------------------------------------+----------------------+
  | Field               | Type             | Null | Key | Default | Extra | Topology                            | Comment              |
  +---------------------+------------------+------+-----+---------+-------+-------------------------------------+----------------------+
  | start_time          | timestamp        | NO   | PRI |         |       | "$.data.room.start_time"            | 开始时间              | 
  | platform            | varchar(20)      | NO   | PRI |         |       |           -                         | 平台                  |
  | room_id             | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                    | 直播间ID              | 
  | sharing_music_index | unsigned bigint  | NO   | PRI |         |       |           -                         | 分享音乐ID序号        |
  | sharing_music_id    | varchar(200)     |      |     | NULL    |       | "$.data.room.sharing_music_id_list" | 分享音乐ID            | 
  +---------------------+------------------+------+-----+---------+-------+-------------------------------------+----------------------+
  """
  room_sharing_music_id = RoomSharingMusicIdTable(db)
  room_sharing_music_id_tuple = {key: None for key in room_sharing_music_id.get_tuple()}
  
  set_dict_attr(room_sharing_music_id_tuple, "$.start_time", start_time)
  set_dict_attr(room_sharing_music_id_tuple, "$.platform",   platform)
  set_dict_attr(room_sharing_music_id_tuple, "$.room_id",    str(room_id))

  try:
    room_sharing_music_id_list = list()
    room_sharing_music_id_tuple_list = room_sharing_music_id.get_record(room_sharing_music_id_tuple)
    for room_sharing_music_id in room_sharing_music_id_tuple_list:
      room_sharing_music_id_list.append(get_dict_attr(room_sharing_music_id, "$.sharing_music_id"))
  except Exception as e:
    get_logger().error(f"{e}: {room_sharing_music_id.get_name()} >> >> >> data.room.sharing_music_id_list")
    room_sharing_music_id_list = []

  """
  >> >> data.room.short_touch_area_config
  +---------------------+--------------+------+-----+---------+-------+-----------------------------------------------------------+-----------------------+
  | Field               | Type         | Null | Key | Default | Extra | Topology                                                  | Comment               |
  +---------------------+--------------+------+-----+---------+-------+-----------------------------------------------------------+-----------------------+
  | now                 | timestamp(3) | NO   | PRI |         |       | "$.extra.now"                                             | 当前时间戳             |
  | platform            | varchar(20)  | NO   | PRI |         |       |           -                                               | 平台                  | 
  | room_id             | varchar(200) | NO   | PRI |         |       | "$.data.room.id"                                          | 直播间ID              | 
  | forbidden_types_map | json         |      |     | NULL    |       | "$.data.room.short_touch_area_config.forbidden_types_map" | 禁止类型映射表         |
  +---------------------+--------------+------+-----+---------+-------+-----------------------------------------------------------+-----------------------+
  """
  room_short_touch_area_config =  RoomShortTouchAreaConfigTable(db)
  room_short_touch_area_config_tuple = {key: None for key in room_short_touch_area_config.get_tuple()}

  set_dict_attr(room_short_touch_area_config_tuple, "$.now", now)
  set_dict_attr(room_short_touch_area_config_tuple, "$.platform", platform)
  set_dict_attr(room_short_touch_area_config_tuple, "$.room_id", str(room_id))

  try:
    room_short_touch_area_config_tuple_list = room_short_touch_area_config.get_record(room_short_touch_area_config_tuple)
    if len(room_short_touch_area_config_tuple_list) != 0:
      room_short_touch_area_config_tuple = room_short_touch_area_config_tuple_list.pop()
  except Exception as e:
    get_logger().error(f"{e}: {room_short_touch_area_config.get_name()} >> >> >> data.room.short_touch_area_config")
    room_short_touch_area_config_tuple = {}

  """
  >> >> >> data.room.short_touch_area_config.elements
  +---------------+------------------+------+-----+---------+-------+-------------------------------------------------------------+-----------------------+
  | Field         | Type             | Null | Key | Default | Extra | Topology                                                    | Comment               |
  +---------------+------------------+------+-----+---------+-------+-------------------------------------------------------------+-----------------------+
  | now           | timestamp(3)     | NO   | PRI |         |       | "$.extra.now"                                               | 当前时间戳             |
  | platform      | varchar(20)      | NO   | PRI |         |       |           -                                                 | 平台                  | 
  | room_id       | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                                            | 直播间ID              | 
  | element_index | unsigned bigint  | NO   | PRI |         |       |           -                                                 | 短触摸区域配置元素     |
  | priority      | unsigned tinyint |      |     | NULL    |       | "$.data.room.short_touch_area_config.elements.'x'.priority" | 优先级                |
  | type          | unsigned tinyint |      |     | NULL    |       | "$.data.room.short_touch_area_config.elements.'x'.type"     | 类型                  |
  +---------------+------------------+------+-----+---------+-------+-------------------------------------------------------------+-----------------------+
  """
  room_short_touch_area_config_elements = RoomShortTouchAreaConfigElementTable(db)
  room_short_touch_area_config_element_tuple = {key: None for key in room_short_touch_area_config_elements.get_tuple()}
  
  set_dict_attr(room_short_touch_area_config_element_tuple, "$.now", now)
  set_dict_attr(room_short_touch_area_config_element_tuple, "$.platform", platform)
  set_dict_attr(room_short_touch_area_config_element_tuple, "$.room_id", str(room_id))
  
  try:
    room_short_touch_area_config_element_list = list()
    room_short_touch_area_config_element_tuple_list = room_short_touch_area_config_elements.get_record(room_short_touch_area_config_element_tuple, fetchall=True)
    for room_short_touch_area_config_element in room_short_touch_area_config_element_tuple_list:
      element = dict()
      priority = room_short_touch_area_config_element.get('priority', 0)
      set_dict_attr(element, "$.priority", priority)
      type = room_short_touch_area_config_element.get('type', 0)
      set_dict_attr(element, "$.type", type)
      room_short_touch_area_config_element_list.append(element)
  except Exception as e:
    get_logger().error(f"{e}: {room_short_touch_area_config_elements.get_name()} >> >> >> data.room.short_touch_area_config.elements")
    room_short_touch_area_config_element_list = []

  """
  >> >> >> data.room.short_touch_area_config.strategy_feat_whitelist
  +-----------------+------------------+------+-----+---------+-------+---------------------------------------------------------------+-----------------------+
  | Field           | Type             | Null | Key | Default | Extra | Topology                                                      | Comment               |
  +-----------------+------------------+------+-----+---------+-------+---------------------------------------------------------------+-----------------------+
  | start_time      | timestamp        | NO   | PRI |         |       | "$.extra.now"                                                 | 当前时间戳             |
  | platform        | varchar(20)      | NO   | PRI |         |       |           -                                                   | 平台                  | 
  | room_id         | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                                              | 直播间ID              | 
  | whitelist_index | unsigned bigint  | NO   | PRI |         |       |           -                                                   | 白名单索引             | 
  | whitelist_tag   | tinytext         |      |     | NULL    |       | "$.data.room.short_touch_area_config.strategy_feat_whitelist" | 白名单标签             | 
  +-----------------+------------------+------+-----+---------+-------+---------------------------------------------------------------+-----------------------+
  """
  room_strategy_feat_whitelist = RoomShortTouchAreaConfigStrategyFeatWhitelistTable(db)
  room_strategy_feat_whitelist_tuple = {key: None for key in room_strategy_feat_whitelist.get_tuple()}
  
  set_dict_attr(room_strategy_feat_whitelist_tuple, "$.start_time", start_time)
  set_dict_attr(room_strategy_feat_whitelist_tuple, "$.platform",   platform)
  set_dict_attr(room_strategy_feat_whitelist_tuple, "$.room_id",    str(room_id))
  
  try:
    room_strategy_feat_whitelist_list = list()
    room_strategy_feat_whitelist_tuple_list = room_strategy_feat_whitelist.get_record(room_strategy_feat_whitelist_tuple, fetchall=True)
    for room_strategy_feat_whitelist in room_strategy_feat_whitelist_tuple_list:
      whitelist_tag = room_strategy_feat_whitelist.get('whitelist_tag', "")
      room_strategy_feat_whitelist_list.append(whitelist_tag)
  except Exception as e:
    get_logger().error(f"{e}: {room_strategy_feat_whitelist.get_name()} >> >> >> data.room.short_touch_area_config.strategy_feat_whitelist")
    room_strategy_feat_whitelist_list = []

  """
  >> >> >> >> data.room.short_touch_area_config.temp_state_condition_map
  +---------------+------------------+------+-----+---------+-------+---------------------------------------------------------------------------------------+------------+
  | Field         | Type             | Null | Key | Default | Extra | Topology                                                                              | Comment    |
  +---------------+------------------+------+-----+---------+-------+---------------------------------------------------------------------------------------+------------+
  | now           | timestamp(3)     | NO   | PRI |         |       | "$.extra.now"                                                                         | 当前时间戳  |
  | platform      | varchar(20)      | NO   | PRI |         |       |           -                                                                           | 平台       | 
  | room_id       | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                                                                      | 直播间ID   |
  | map_index     | unsigned bigint  | NO   | PRI |         |       |           -                                                                           | 映射索引   |
  | minimum_gap   | unsigned int     |      |     | NULL    |       | "$.data.room.short_touch_area_config.temp_state_condition_map.'x'.minimum_gap"        | 最小间隔   |
  | priority      | unsigned tinyint |      |     | NULL    |       | "$.data.room.short_touch_area_config.temp_state_condition_map.'x'.type.priority"      | 优先级     |
  | strategy_type | unsigned tinyint |      |     | NULL    |       | "$.data.room.short_touch_area_config.temp_state_condition_map.'x'.type.strategy_type" | 策略类型   |
  +---------------+------------------+------+-----+---------+-------+---------------------------------------------------------------------------------------+------------+
  """
  room_temp_state_condition_map = RoomTempStateConditionMapTable(db)
  room_temp_state_condition_map_tuple = {key: None for key in room_temp_state_condition_map.get_tuple()}
  
  set_dict_attr(room_temp_state_condition_map_tuple, "$.now", now)
  set_dict_attr(room_temp_state_condition_map_tuple, "$.platform", platform)
  set_dict_attr(room_temp_state_condition_map_tuple, "$.room_id", str(room_id))
  
  try:
    room_temp_state_condition_map_list = list()
    room_temp_state_condition_map_tuple_list = room_temp_state_condition_map.get_record(room_temp_state_condition_map_tuple, fetchall=True)
    for room_temp_state_condition in room_temp_state_condition_map_tuple_list:
      temp_state_condition = dict()
      minimum_gap = room_temp_state_condition.get('minimum_gap', 0)
      set_dict_attr(temp_state_condition, "$.minimum_gap", minimum_gap, force=True)
      priority = room_temp_state_condition.get('priority', 0)
      set_dict_attr(temp_state_condition, "$.type.priority", priority, force=True)
      strategy_type = room_temp_state_condition.get('strategy_type', 0)
      set_dict_attr(temp_state_condition, "$.type.strategy_type", strategy_type, force=True)
      room_temp_state_condition_map_list.append(temp_state_condition)
  except Exception as e:
    get_logger().error(f"{e}: {room_temp_state_condition_map.get_name()} >> >> >> >> data.room.short_touch_area_config.temp_state_condition_map")
    room_temp_state_condition_map_list = []

  """
  >> >> >> >> data.room.short_touch_area_config.temp_state_global_condition
  +--------------+------------------+------+-----+---------+-------+--------------------------------------------------------------------------------+------------+
  | Field        | Type             | Null | Key | Default | Extra | Topology                                                                       | Comment    |
  +--------------+------------------+------+-----+---------+-------+--------------------------------------------------------------------------------+------------+
  | now          | timestamp        | NO   | PRI |         |       | "$.extra.now"                                                                  | 当前时间戳 |
  | platform     | varchar(20)      | NO   | PRI |         |       |           -                                                                    | 平台       | 
  | room_id      | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                                                               | 直播间ID   |
  | allow_count  | unsigned tinyint |      |     | NULL    |       | "$.data.room.short_touch_area_config.temp_state_global_condition.allow_count"  | 允许总数   |
  | duration_gap | unsigned int     |      |     | NULL    |       | "$.data.room.short_touch_area_config.temp_state_global_condition.duration_gap" | 持续间隔   |
  +--------------+------------------+------+-----+---------+-------+--------------------------------------------------------------------------------+------------+
  """
  room_temp_state_global_condition = RoomTempStateGlobalConditionTable(db)
  room_temp_state_global_condition_tuple = {key: None for key in room_temp_state_global_condition.get_tuple()}
  
  set_dict_attr(room_temp_state_global_condition_tuple, "$.now",      now)
  set_dict_attr(room_temp_state_global_condition_tuple, "$.platform", platform)
  set_dict_attr(room_temp_state_global_condition_tuple, "$.room_id", str(room_id))
  
  try:
    room_temp_state_global_condition_dict = dict()
    room_temp_state_global_condition_tuple_list = room_temp_state_global_condition.get_record(room_temp_state_global_condition_tuple)
    if len(room_temp_state_global_condition_tuple_list) != 0:
      room_temp_state_global_condition_dict = room_temp_state_global_condition_tuple_list.pop()
  except Exception as e:
    get_logger().error(f"{e}: {room_temp_state_global_condition.get_name()} >> >> >> >> data.room.short_touch_area_config.temp_state_global_condition")
    room_temp_state_global_condition_dict = {}
  
  """
  >> >> >> >> >> data.room.short_touch_area_config.temp_state_global_condition.ignore_strategy_types
  +-----------------------------+------------------+------+-----+---------+-------+-----------------------------------------------------------------------------------------+----------------+
  | Field                       | Type             | Null | Key | Default | Extra | Topology                                                                                | Comment        |
  +-----------------------------+------------------+------+-----+---------+-------+-----------------------------------------------------------------------------------------+----------------+
  | now                         | timestamp(3)     | NO   | PRI |         |       | "$.extra.now"                                                                           | 当前时间戳      |
  | platform                    | varchar(20)      | NO   | PRI |         |       |           -                                                                             | 平台            | 
  | room_id                     | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                                                                        | 直播间ID        |
  | ignore_strategy_type_index  | unsigned bigint  |      |     | NULL    |       |                                  -                                                      | 忽略策略类型索引 |
  | ignore_strategy_type        | unsigned tinyint |      |     | NULL    |       | "$.data.room.short_touch_area_config.temp_state_global_condition.ignore_strategy_types" | 忽略策略类型     |
  +-----------------------------+------------------+------+-----+---------+-------+-----------------------------------------------------------------------------------------+-----------------+
  """
  room_temp_state_global_condition_ignore_strategy_type = RoomTempStateGlobalConditionIgnoreStrategyTypeTable(db)
  room_temp_state_global_condition_ignore_strategy_type_tuple = {key: None for key in room_temp_state_global_condition_ignore_strategy_type.get_tuple()}
  
  set_dict_attr(room_temp_state_global_condition_ignore_strategy_type_tuple, "$.now", now)
  set_dict_attr(room_temp_state_global_condition_ignore_strategy_type_tuple, "$.platform", platform)
  set_dict_attr(room_temp_state_global_condition_ignore_strategy_type_tuple, "$.room_id", str(room_id))
  
  try:
    room_temp_state_global_condition_ignore_strategy_type_list = list()
    room_temp_state_global_condition_ignore_strategy_type_tuple_list = room_temp_state_global_condition_ignore_strategy_type.get_record(room_temp_state_global_condition_ignore_strategy_type_tuple)
    for room_temp_state_global_condition_ignore_strategy in room_temp_state_global_condition_ignore_strategy_type_tuple_list:
      ignore_strategy_type = room_temp_state_global_condition_ignore_strategy.get('ignore_strategy_type', 0)
      room_temp_state_global_condition_ignore_strategy_type_list.append(ignore_strategy_type)
  except Exception as e:
    get_logger().error(f"{e}: {room_temp_state_global_condition_ignore_strategy_type.get_name()} >> >> >> >> >> data.room.short_touch_area_config.temp_state_global_condition.ignore_strategy_types")
    room_temp_state_global_condition_ignore_strategy_type_list = []

  """
  >> >> >> >> >> data.room.short_touch_area_config.temp_state_strategy
  +-------------------+------------------+------+-----+---------+-------+-------------------------------------------------------------------------------------+------------+
  | Field             | Type             | Null | Key | Default | Extra | Topology                                                                            | Comment    |
  +-------------------+------------------+------+-----+---------+-------+-------------------------------------------------------------------------------------+------------+
  | now               | timestamp        | NO   | PRI |         |       | "$.extra.now"                                                                       | 当前时间戳 |
  | platform          | varchar(20)      | NO   | PRI |         |       |           -                                                                         | 平台       | 
  | room_id           | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                                                                    | 直播间ID   |
  | short_touch_type  | unsigned int     |      |     | NULL    |       | "$.data.room.short_touch_area_config.temp_state_global_condition.short_touch_type"  | 允许总数   |
  +-------------------+------------------+------+-----+---------+-------+-------------------------------------------------------------------------------------+------------+
  """
  room_temp_state_strategy = RoomTempStateStrategyTable(db)
  room_temp_state_strategy_tuple = {key: None for key in room_temp_state_strategy.get_tuple()}

  set_dict_attr(room_temp_state_strategy_tuple, "$.now", now)
  set_dict_attr(room_temp_state_strategy_tuple, "$.platform", platform)
  set_dict_attr(room_temp_state_strategy_tuple, "$.room_id", str(room_id))
  
  try:
    short_touch_type_list = list()
    room_temp_state_strategy_tuple_list = room_temp_state_strategy.get_record(room_temp_state_strategy_tuple, fetchall=True)
    for temp_state_strategy in room_temp_state_strategy_tuple_list:
      short_touch_type_list.append(get_dict_attr(temp_state_strategy, "$.short_touch_type"))
  except Exception as e:
    get_logger().error(f"{e}: {room_temp_state_strategy.get_name()} >> >> >> >> >> data.room.short_touch_area_config.temp_state_strategy")
    short_touch_type_list = []
  
  """
  >> >> >> >> >> data.room.short_touch_area_config.temp_state_strategy.'x'.strategy_map
  +-------------------+------------------+------+-----+---------+-------+--------------------------------------------------------------------------------------------+------------+
  | Field             | Type             | Null | Key | Default | Extra | Topology                                                                                   | Comment    |
  +-------------------+------------------+------+-----+---------+-------+--------------------------------------------------------------------------------------------+------------+
  | now               | timestamp        | NO   | PRI |         |       | "$.extra.now"                                                                              | 当前时间戳 |
  | platform          | varchar(20)      | NO   | PRI |         |       |           -                                                                                | 平台       | 
  | room_id           | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                                                                           | 直播间ID   |
  | short_touch_type  | unsigned int     |      |     | NULL    |       | "$.data.room.short_touch_area_config.temp_state_strategy.'x'.short_touch_type"             | 允许总数   |
  | duration          | unsigned int     |      |     | NULL    |       | "$.data.room.short_touch_area_config.temp_state_strategy.strategy_map.'x'.duration"        | 持续时间   |
  | strategy_method   | varchar(100)     |      |     | NULL    |       | "$.data.room.short_touch_area_config.temp_state_strategy.strategy_map.'x'.strategy_method" | 策略方法   |
  | priority          | unsigned tinyint |      |     | NULL    |       | "$.data.room.short_touch_area_config.temp_state_strategy.strategy_map.'x'.type.priority"        | 优先级     |
  | strategy_type     | unsigned tinyint |      |     | NULL    |       | "$.data.room.short_touch_area_config.temp_state_strategy.strategy_map.'x'.type.strategy_type"   | 策略类型   |
  +-------------------+------------------+------+-----+---------+-------+--------------------------------------------------------------------------------------------+------------+
  """
  room_temp_state_strategy_map = RoomTempStateStrategyMapTable(db)
  room_temp_state_strategy_map_tuple = {key: None for key in room_temp_state_strategy_map.get_tuple()}
  
  try:
    room_temp_state_strategy_dict = dict()
    for short_touch_type in short_touch_type_list:
      set_dict_attr(room_temp_state_strategy_map_tuple, "$.now",              now)
      set_dict_attr(room_temp_state_strategy_map_tuple, "$.platform",         platform)
      set_dict_attr(room_temp_state_strategy_map_tuple, "$.room_id",          str(room_id))
      set_dict_attr(room_temp_state_strategy_map_tuple, "$.short_touch_type", short_touch_type)
      
      strategy_map = dict()
      room_temp_state_strategy_map_tuple_list = room_temp_state_strategy_map.get_record(room_temp_state_strategy_map_tuple, fetchall=True)
      for temp_state_strategy_map in room_temp_state_strategy_map_tuple_list:
        duration        = temp_state_strategy_map.get('duration', 0)
        strategy_method = temp_state_strategy_map.get('strategy_method', "")
        priority        = temp_state_strategy_map.get('priority', 0)
        strategy_type   = temp_state_strategy_map.get('strategy_type', 0)

        set_dict_attr(strategy_map, f"$.{strategy_type}.duration",              duration,        force=True)
        set_dict_attr(strategy_map, f"$.{strategy_type}.strategy_method",       strategy_method, force=True)
        set_dict_attr(strategy_map, f"$.{strategy_type}.type.priority",         priority,        force=True)
        set_dict_attr(strategy_map, f"$.{strategy_type}.type.strategy_type",    strategy_type,   force=True)
      set_dict_attr(room_temp_state_strategy_dict, f"$.{short_touch_type}.short_touch_type", short_touch_type, force=True)
      set_dict_attr(room_temp_state_strategy_dict, f"$.{short_touch_type}.strategy_map",     strategy_map,             force=True)
  except Exception as e:
    get_logger().error(f"{e}: {room_temp_state_strategy_map.get_name()} >> >> >> >> >> data.room.short_touch_area_config.temp_state_strategy")
    room_temp_state_strategy_dict = {}

  """
  >> >> >> >> data.room.stream_url.candidate_resolution
  +----------------------+-------------------+------+-----+---------+-------+-----------------------------------------------+---------------------+
  | Field                | Type              | Null | Key | Default | Extra | Topology                                      | Comment             |
  +----------------------+-------------------+------+-----+---------+-------+-----------------------------------------------+---------------------+
  | start_time           | timestamp(3)      | NO   | PRI |         |       | "$.data.room.create_time"                     | 当前时间戳           | 
  | platform             | varchar(20)       | NO   | PRI |         |       |           -                                   | 平台                 | 
  | room_id              | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                              | 直播间ID             | 
  | stream_id            | varchar(200)      | NO   | PRI |         |       | "$.data.room.stream_id"                       | 直播间流ID           |
  | resolution_index     | unsigned bigint   | NO   | PRI |         |       |           -                                   | 分辨率索引           | 
  | candidate_resolution | varchar(20)       |      |     | NULL    |       | "$.data.room.stream_url.candidate_resolution" | 候选分辨率           | 
  +----------------------+-------------------+------+-----+---------+-------+-----------------------------------------------+---------------------+
  """
  stream_url_candidate_resolution = StreamCandidateResolutionTable(db)
  stream_url_candidate_resolution_tuple = {key: None for key in stream_url_candidate_resolution.get_tuple()}
  
  set_dict_attr(stream_url_candidate_resolution_tuple, "$.start_time",   start_time)
  set_dict_attr(stream_url_candidate_resolution_tuple, "$.platform",     platform)
  set_dict_attr(stream_url_candidate_resolution_tuple, "$.room_id",      str(room_id))
  set_dict_attr(stream_url_candidate_resolution_tuple, "$.stream_id",    str(room_record_tuple.get("stream_id", 0)))
  
  try:
    candidate_resolution_list = list()
    stream_url_candidate_resolution_tuple_list = stream_url_candidate_resolution.get_record(stream_url_candidate_resolution_tuple, fetchall=True)
    for stream_url_candidate_resolution in stream_url_candidate_resolution_tuple_list:
      candidate_resolution_list.append(get_dict_attr(stream_url_candidate_resolution, "$.candidate_resolution"))
  except Exception as e:
    get_logger().error(f"{e}: {stream_url_candidate_resolution.get_name()} >> >> >> >> data.room.stream_url.candidate_resolution")
    candidate_resolution_list = []

  """
  >> >> >> >> data.room.stream_url.complete_push_urls
  +-------------------------+-------------------+------+-----+---------+-------+---------------------------------------------+---------------------+
  | Field                   | Type              | Null | Key | Default | Extra | Topology                                    | Comment             |
  +-------------------------+-------------------+------+-----+---------+-------+---------------------------------------------+---------------------+
  | now                     | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"                               | 当前时间戳           | 
  | platform                | varchar(20)       | NO   | PRI |         |       |           -                                 | 平台                 | 
  | room_id                 | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                            | 直播间ID             |
  | stream_id               | varchar(200)      | NO   | PRI |         |       | "$.data.room.stream_id"                     | 直播间流ID           |
  | complete_push_url_index | unsigned bigint   | NO   | PRI |         |       |           -                                 | 完整推流地址序号     | 
  | complete_push_url       | text              |      |     | NULL    |       | "$.data.room.stream_url.complete_push_urls" | 完整推流地址         |
  +-------------------------+-------------------+------+-----+---------+-------+---------------------------------------------+---------------------+
  """
  stream_url_complete_push_url = StreamCompletePushUrlTable(db)
  stream_url_complete_push_url_tuple = {key: None for key in stream_url_complete_push_url.get_tuple()}
  
  set_dict_attr(stream_url_complete_push_url_tuple, "$.now",       now)
  set_dict_attr(stream_url_complete_push_url_tuple, "$.platform",  platform)
  set_dict_attr(stream_url_complete_push_url_tuple, "$.room_id",   str(room_id))
  set_dict_attr(stream_url_complete_push_url_tuple, "$.stream_id", str(room_record_tuple.get("stream_id", 0)))
  
  try:
    complete_push_url_list = list()
    stream_url_complete_push_url_tuple_list = stream_url_complete_push_url.get_record(stream_url_complete_push_url_tuple, fetchall=True)
    for stream_url_complete_push_url in stream_url_complete_push_url_tuple_list:
      complete_push_url_list.append(get_dict_attr(stream_url_complete_push_url, "$.complete_push_url"))
  except Exception as e:
    get_logger().error(f"{e}: {stream_url_complete_push_url.get_name()} >> >> >> >> data.room.stream_url.complete_push_urls")
    complete_push_url_list = []

  """
  >> >> >> data.room.stream_url
  +------------------------------------------+-------------------+------+-----+---------+-------+------------------------------------------------------------+----------------------------------+
  | Field                                    | Type              | Null | Key | Default | Extra | Topology                                                   | Comment                          | 
  +------------------------------------------+-------------------+------+-----+---------+-------+------------------------------------------------------------+----------------------------------+
  | default_resolution                       | varchar(20)       | YES  |     | NULL    |       | "$.data.room.stream_url.default_resolution"                | 默认分辨率                        |
  | anchor_interact_profile                  | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.stream_url.extra.anchor_interact_profile"     | 主播互动配置文件                  |
  | audience_interact_profile                | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.stream_url.extra.audience_interact_profile"   | 观众互动配置文件                  |
  | bframe_enable                            | bool              | YES  |     | NULL    |       | "$.data.room.stream_url.extra.bframe_enable"               | B帧启用                          |
  | bitrate_adapt_strategy                   | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.stream_url.extra.bitrate_adapt_strategy"      | 比特率自适应策略                  |
  | bytevc1_enable                           | bool              | YES  |     | NULL    |       | "$.data.room.stream_url.extra.bytevc1_enable"              | 比特率自适应策略                  |
  | default_bitrate                          | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.stream_url.extra.default_bitrate"             | 默认比特率                        |
  | fps                                      | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.stream_url.extra.fps"                         | 帧率                              |
  | gop_sec                                  | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.stream_url.extra.gop_sec"                     | GOP秒数                          |
  | h265_enable                              | bool              | YES  |     | NULL    |       | "$.data.room.stream_url.extra.h265_enable"                 | H.265启用                        |
  | hardware_encode                          | bool              | YES  |     | NULL    |       | "$.data.room.stream_url.extra.hardware_encode"             | 硬件编码                          |
  | height                                   | unsigned smallint | YES  |     | NULL    |       | "$.data.room.stream_url.extra.height"                      | 高度                             |
  | max_bitrate                              | unsigned int      | YES  |     | NULL    |       | "$.data.room.stream_url.extra.max_bitrate"                 | 最大比特率                        |
  | min_bitrate                              | unsigned int      | YES  |     | NULL    |       | "$.data.room.stream_url.extra.min_bitrate"                 | 最小比特率                        |
  | roi                                      | bool              | YES  |     | NULL    |       | "$.data.room.stream_url.extra.roi"                         | 是否启用ROI（Region of Interest） |
  | sw_roi                                   | bool              | YES  |     | NULL    |       | "$.data.room.stream_url.extra.sw_roi"                      | 是否启用软件ROI                   |
  | video_profile                            | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.stream_url.extra.video_profile"               | 视频配置文件                      |
  | width                                    | unsigned smallint | YES  |     | NULL    |       | "$.data.room.stream_url.extra.width"                       | 宽度                             |
  | resolution_name                          | json              | YES  |     | NULL    |       | "$.data.room.stream_url.resolution_name"                   | 分辨率名称                        |
  | flv_pull_url                             | json              | YES  |     | NULL    |       | "$.data.room.stream_url.flv_pull_url"                      | 直播间FLV拉流地址                 |
  | flv_pull_url_params                      | json              | YES  |     | NULL    |       | "$.data.room.stream_url.flv_pull_url_params"               | FLV拉流地址参数                   |
  | hls_pull_url                             | text              | YES  |     | NULL    |       | "$.data.room.stream_url.hls_pull_url"                      | 直播间HLS拉流地址                 |
  | hls_pull_url_map                         | json              | YES  |     | NULL    |       | "$.data.room.stream_url.hls_pull_url_map"                  | 直播间HLS拉流地址映射              |
  | hls_pull_url_params                      | json              | YES  |     | NULL    |       | "$.data.room.stream_url.hls_pull_url_params"               | HLS拉流地址参数                   |
  | id                                       | varchar(200)      | NO   | PRI |         |       | "$.data.room.stream_url.id"                                | 直播间流ID                        |
  | provider                                 | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.stream_url.provider"                          | 直播间推流服务商                  |
  | pull_datas                               | json              | YES  |     | NULL    |       | "$.data.room.stream_url.pull_datas"                        | 拉流数据                          |
  | push_datas                               | json              | YES  |     | NULL    |       | "$.data.room.stream_url.push_datas"                        | 推流数据                          |
  | push_stream_type                         | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.stream_url.push_stream_type"                  | 推流类型                          |
  | rtmp_pull_url                            | text              | YES  |     | NULL    |       | "$.data.room.stream_url.rtmp_pull_url"                     | 直播间RTMP拉流地址                |
  | rtmp_pull_url_params                     | json              | YES  |     | NULL    |       | "$.data.room.stream_url.rtmp_pull_url_params"              | RTMP拉流地址参数                  |
  | rtmp_push_url                            | text              | YES  |     | NULL    |       | "$.data.room.stream_url.rtmp_push_url"                     | 直播间RTMP推流地址                |
  | rtmp_push_url_params                     | text              | YES  |     | NULL    |       | "$.data.room.stream_url.rtmp_push_url_params"              | RTMP推流地址参数                  |
  | stream_control_type                      | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.stream_url.stream_control_type"               | 直播间流控制类型                  |
  | stream_orientation                       | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.stream_url.stream_orientation"                | 直播间流方向：1-竖屏 2-横屏        |
  | vr_type                                  | unsigned tinyint  | YES  |     | NULL    |       | "$.data.room.stream_url.vr_type"                           | VR类型                           |
  +------------------------------------------+-------------------+------+-----+---------+-------+------------------------------------------------------------+----------------------------------+
  """
  live_stream = LiveStreamTable(db)
  live_stream_tuple = {key: None for key in live_stream.get_tuple()}
  
  set_dict_attr(live_stream_tuple, "$.id",       str(room_record_tuple.get("stream_id", 0)))
  
  try:
    live_stream_tuple_list = live_stream.get_record(live_stream_tuple)
    if len(live_stream_tuple_list) != 0:
      live_stream_tuple = live_stream_tuple_list.pop()
  except Exception as e:
    get_logger().error(f"{e}: {live_stream.get_name()} >> >> >> >> data.room.stream_url")
    live_stream_tuple = {}
  
  """
  >> >> >> >> data.room.stream_url.extra.live_core_sdk_data.pull_data.Flv
  +-----------+------------------+------+-----+---------+-------+-----------------------------------------------------------+---------------------+
  | Field     | Type             | Null | Key | Default | Extra | Topology                                                  | Comment             |
  +-----------+------------------+------+-----+---------+-------+-----------------------------------------------------------+---------------------+
  | now       | timestamp(3)     | NO   | PRI |         |       | "$.data.room.create_time"                                 | 当前时间戳           | 
  | platform  | varchar(20)      | NO   | PRI |         |       |           -                                               | 平台                 | 
  | room_id   | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                                          | 直播间ID             |
  | Flv_index | unsigned bigint  | NO   | PRI |         |       |           -                                               | Flv序号              | 
  | Flv       | text             |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.Flv" | Flv数据             |
  +-----------+------------------+------+-----+---------+-------+-----------------------------------------------------------+---------------------+
  """
  live_core_sdk_data_pull_data_flv = LiveCoreSdkPullFlvDataTable(db)
  live_core_sdk_data_pull_data_flv_tuple = {key: None for key in live_core_sdk_data_pull_data_flv.get_tuple()}
  
  set_dict_attr(live_core_sdk_data_pull_data_flv_tuple, "$.now",       now)
  set_dict_attr(live_core_sdk_data_pull_data_flv_tuple, "$.platform",  platform)
  set_dict_attr(live_core_sdk_data_pull_data_flv_tuple, "$.room_id",   str(room_id))
  
  try:
    live_core_sdk_data_pull_data_flv_list = list()
    live_core_sdk_data_pull_data_flv_tuple_list = live_core_sdk_data_pull_data_flv.get_record(live_core_sdk_data_pull_data_flv_tuple, fetchall=True)
    for live_pull_data_flv in live_core_sdk_data_pull_data_flv_tuple_list:
      live_core_sdk_data_pull_data_flv_list.append(live_pull_data_flv.get('Flv', ''))
  except Exception as e:
    get_logger().error(f"{e}: {live_core_sdk_data_pull_data_flv.get_name()} >> >> >> >> >> data.room.stream_url.extra.live_core_sdk_data.pull_data.Flv")
    live_core_sdk_data_pull_data_flv_list = []

  """
  >> >> >> >> data.room.stream_url.extra.live_core_sdk_data.pull_data.Hls
  +-----------+------------------+------+-----+---------+-------+-----------------------------------------------------------+---------------------+
  | Field     | Type             | Null | Key | Default | Extra | Topology                                                  | Comment             |
  +-----------+------------------+------+-----+---------+-------+-----------------------------------------------------------+---------------------+
  | now       | timestamp(3)     | NO   | PRI |         |       | "$.data.room.create_time"                                 | 当前时间戳           | 
  | platform  | varchar(20)      | NO   | PRI |         |       |           -                                               | 平台                 | 
  | room_id   | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                                          | 直播间ID             |
  | Hls_index | unsigned bigint  | NO   | PRI |         |       |           -                                               | Hls序号              | 
  | Hls       | text             |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.Hls" | Hls数据             |
  +-----------+------------------+------+-----+---------+-------+-----------------------------------------------------------+---------------------+
  """
  live_core_sdk_data_pull_data_hls = LiveCoreSdkPullFlvDataTable(db)
  live_core_sdk_data_pull_data_hls_tuple = {key: None for key in live_core_sdk_data_pull_data_hls.get_tuple()}
  
  set_dict_attr(live_core_sdk_data_pull_data_hls_tuple, "$.now",       now)
  set_dict_attr(live_core_sdk_data_pull_data_hls_tuple, "$.platform",  platform)
  set_dict_attr(live_core_sdk_data_pull_data_hls_tuple, "$.room_id",   str(room_id))
  
  try:
    live_core_sdk_data_pull_data_hls_list = list()
    live_core_sdk_data_pull_data_hls_tuple_list = live_core_sdk_data_pull_data_hls.get_record(live_core_sdk_data_pull_data_hls_tuple, fetchall=True)
    for live_pull_data_hls in live_core_sdk_data_pull_data_hls_tuple_list:
      live_core_sdk_data_pull_data_hls_list.append(live_pull_data_hls.get('Hls', ''))
  except Exception as e:
    get_logger().error(f"{e}: {live_core_sdk_data_pull_data_hls.get_name()} >> >> >> >> >> data.room.stream_url.extra.live_core_sdk_data.pull_data.Hls")
    live_core_sdk_data_pull_data_hls_list = []

  """
  >> >> >> >> >> data.room.stream_url.extra.live_core_sdk_data.pull_data
  +----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------------------------+---------------------+
  | Field                | Type              | Null | Key | Default | Extra | Topology                                                                   | Comment             |
  +----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------------------------+---------------------+
  | now                  | timestamp(3)      | NO   | PRI |         |       | "$.data.room.create_time"                                                  | 当前时间戳           | 
  | platform             | varchar(20)       | NO   | PRI |         |       |           -                                                                | 平台                 | 
  | room_id              | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                                                           | 直播间ID             |
  | codec                | varchar(100)      |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.codec"                | 编解码器             |
  | compensatory_data    | text              |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.compensatory_data"    | 补偿数据             |
  | hls_data_unencrypted | json              |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.hls_data_unencrypted" | HLS未加密数据        |
  | kind                 | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.kind"                 | 类型                |
  | stream_data          | text              |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.stream_data"          | 流数据内容           |
  | version              | varchar(20)       |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.version"              | 版本                |
  +----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------------------------+---------------------+
  """
  live_core_sdk_pull_data = LiveCoreSdkPullDataTable(db)
  live_core_sdk_pull_data_tuple = {key: None for key in live_core_sdk_pull_data.get_tuple()}

  set_dict_attr(live_core_sdk_pull_data_tuple, "$.now",       now)
  set_dict_attr(live_core_sdk_pull_data_tuple, "$.platform",  platform)
  set_dict_attr(live_core_sdk_pull_data_tuple, "$.room_id",   str(room_id))
  
  try:
    live_core_sdk_pull_data_tuple_list = live_core_sdk_pull_data.get_record(live_core_sdk_pull_data_tuple)
    if len(live_core_sdk_pull_data_tuple_list) != 0:
      live_core_sdk_pull_data_tuple = live_core_sdk_pull_data_tuple_list.pop()
  except Exception as e:
    get_logger().error(f"{e}: {live_core_sdk_pull_data.get_name()} >> >> >> >> >> data.room.stream_url.extra.live_core_sdk_data.pull_data")
    live_core_sdk_pull_data_tuple = {}

  """
  >> >> >> >> data.room.stream_url.extra.live_core_sdk_data.pull_data.options.default_quality
  +--------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------------------------------------+---------------------+
  | Field              | Type              | Null | Key | Default | Extra | Topology                                                                                         | Comment             |
  +--------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------------------------------------+---------------------+
  | now                | timestamp(3)      | NO   | PRI |         |       | "$.data.room.create_time"                                                                        | 当前时间戳           | 
  | platform           | varchar(20)       | NO   | PRI |         |       |           -                                                                                      | 平台                 | 
  | room_id            | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                                                                                 | 直播间ID             |
  | additional_content | text              |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.additional_content" | 附加内容            |
  | disable            | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.disable"            | 默认质量禁用标志     |
  | fps                | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.fps"                | 帧率                |
  | level              | unsigned smallint |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.level"              | 级别                |
  | name               | varchar(50)       |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.name"               | 名称                |
  | resolution         | varchao(50)       |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.resolution"         | 分辨率              |
  | sdk_key            | varchar(100)      |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.sdk_key"            | SDK密钥             |
  | v_bit_rate         | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.v_bit_rate"         | 视频比特率           |
  | v_codec            | varchar(100)      |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.v_codec"            | 视频编解码器         |
  +--------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------------------------------------+---------------------+
  """
  live_core_sdk_pull_default_quality = LiveCoreSdkPullDefaultQualityDataTable(db)
  live_core_sdk_pull_default_quality_tuple = {key: None for key in live_core_sdk_pull_default_quality.get_tuple()}
  
  set_dict_attr(live_core_sdk_pull_default_quality_tuple, "$.now",       now)
  set_dict_attr(live_core_sdk_pull_default_quality_tuple, "$.platform",  platform)
  set_dict_attr(live_core_sdk_pull_default_quality_tuple, "$.room_id",   str(room_id))
  
  try:
    live_core_sdk_pull_default_quality_tuple_list = live_core_sdk_pull_default_quality.get_record(live_core_sdk_pull_default_quality_tuple)
    if len(live_core_sdk_pull_default_quality_tuple_list) != 0:
      live_core_sdk_pull_default_quality_tuple = live_core_sdk_pull_default_quality_tuple_list.pop()
  except Exception as e:
    get_logger().error(f"{e}: {live_core_sdk_pull_default_quality.get_name()} >> >> >> >> >> >> data.room.stream_url.extra.live_core_sdk_data.pull_data.options.default_quality")
    live_core_sdk_pull_default_quality_tuple = {}

  """
  >> >> >> >> data.room.stream_url.extra.live_core_sdk_data.pull_data.options.qualities
  +--------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------------------------------+---------------------+
  | Field              | Type              | Null | Key | Default | Extra | Topology                                                                                   | Comment             |
  +--------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------------------------------+---------------------+
  | start_time         | timestamp(3)      | NO   | PRI |         |       | "$.data.room.create_time"                                                                  | 当前时间戳           | 
  | platform           | varchar(20)       | NO   | PRI |         |       |           -                                                                                | 平台                 | 
  | room_id            | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                                                                           | 直播间ID             |
  | quality_index      | unsigned bigint   | NO   | PRI |         |       |           -                                                                                | 视频流质量序号        |
  | additional_content | text              |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities.additional_content" | 附加内容             |
  | disable            | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities.disable"            | 默认质量禁用标志     |
  | fps                | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities.fps"                | 帧率                |
  | level              | unsigned smallint |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities.level"              | 级别                |
  | name               | varchar(50)       |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities.name"               | 名称                |
  | resolution         | varchao(50)       |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities.resolution"         | 分辨率              |
  | sdk_key            | varchar(100)      |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities.sdk_key"            | SDK密钥             |
  | v_bit_rate         | unsigned tinyint  |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities.v_bit_rate"         | 视频比特率           |
  | v_codec            | varchar(100)      |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities.v_codec"            | 视频编解码器         |
  +--------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------------------------------+---------------------+
  """
  live_core_sdk_pull_quality =  LiveCoreSdkPullQualityDataTable(db)
  live_core_sdk_pull_quality_tuple = {key: None for key in live_core_sdk_pull_quality.get_tuple()}
  
  set_dict_attr(live_core_sdk_pull_quality_tuple, "$.start_time", start_time)
  set_dict_attr(live_core_sdk_pull_quality_tuple, "$.platform",   platform)
  set_dict_attr(live_core_sdk_pull_quality_tuple, "$.room_id",    str(room_id))
  
  try:
    live_core_sdk_pull_quality_list = list()
    live_core_sdk_pull_quality_tuple_list = live_core_sdk_pull_quality.get_record(live_core_sdk_pull_quality_tuple, fetchall=True)
    for live_pull_quality in live_core_sdk_pull_quality_tuple_list:
      quality_info = dict()
      set_dict_attr(quality_info, "$.additional_content", live_pull_quality.get('additional_content', ''), force=True)
      set_dict_attr(quality_info, "$.disable",            live_pull_quality.get('disable', 0),             force=True)
      set_dict_attr(quality_info, "$.fps",                live_pull_quality.get('fps', 0),                 force=True)
      set_dict_attr(quality_info, "$.level",              live_pull_quality.get('level', 0),               force=True)
      set_dict_attr(quality_info, "$.name",               live_pull_quality.get('name', ''),               force=True)
      set_dict_attr(quality_info, "$.resolution",         live_pull_quality.get('resolution', ''),         force=True)
      set_dict_attr(quality_info, "$.sdk_key",            live_pull_quality.get('sdk_key', ''),            force=True)
      set_dict_attr(quality_info, "$.v_bit_rate",         live_pull_quality.get('v_bit_rate', 0),          force=True)
      set_dict_attr(quality_info, "$.v_codec",            live_pull_quality.get('v_codec', ''),            force=True)
      live_core_sdk_pull_quality_list.append(quality_info)
  except Exception as e:
    get_logger().error(f"{e}: {live_core_sdk_pull_quality.get_name()} >> >> >> >> >> >> data.room.stream_url.extra.live_core_sdk_data.pull_data.options.qualities")
    live_core_sdk_pull_quality_list = []

  """
  >> >> >> >> >> >> data.room.stream_url.live_core_sdk_data.pull_data.options
  +---------------+--------------+------+-----+---------+-------+----------------------------------------------------------------------------+---------------------+
  | Field         | Type         | Null | Key | Default | Extra | Topology                                                                   | Comment             |
  +---------------+--------------+------+-----+---------+-------+----------------------------------------------------------------------------+---------------------+
  | now           | timestamp(3) | NO   | PRI |         |       | "$.data.room.create_time"                                                  | 当前时间戳           | 
  | platform      | varchar(20)  | NO   | PRI |         |       |           -                                                                | 平台                 | 
  | room_id       | varchar(200) | NO   | PRI |         |       | "$.data.room.id"                                                           | 直播间ID             |
  | vpass_default | bool         |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.vpass_default"| 视频默认通过         |
  +---------------+--------------+------+-----+---------+-------+----------------------------------------------------------------------------+---------------------+
  """
  live_core_sdk_pull_data_options = LiveCoreSdkPullDataOptionTable(db)
  live_core_sdk_pull_data_options_tuple = {key: None for key in live_core_sdk_pull_data_options.get_tuple()}
  
  set_dict_attr(live_core_sdk_pull_data_options_tuple, "$.now",       now)
  set_dict_attr(live_core_sdk_pull_data_options_tuple, "$.platform",  platform)
  set_dict_attr(live_core_sdk_pull_data_options_tuple, "$.room_id",   str(room_id))
  
  try:
    live_core_sdk_pull_data_options_tuple_list = live_core_sdk_pull_data_options.get_record(live_core_sdk_pull_data_options_tuple)
    if len(live_core_sdk_pull_data_options_tuple_list) != 0:
      live_core_sdk_pull_data_options_tuple = live_core_sdk_pull_data_options_tuple_list.pop()
  except Exception as e:
    get_logger().error(f"{e}: {live_core_sdk_pull_data_options.get_name()} >> >> >> >> >> >> data.room.stream_url.extra.live_core_sdk_data.pull_data.options")
    live_core_sdk_pull_data_options_tuple = {}

  """
  >> >> >> >> data.room.stream_url.extra.live_core_sdk_data
  +----------+--------------+------+-----+---------+-------+--------------------------------------------------+---------------------+
  | Field    | Type         | Null | Key | Default | Extra | Topology                                         | Comment             |
  +----------+--------------+------+-----+---------+-------+--------------------------------------------------+---------------------+
  | now      | timestamp(3) | NO   | PRI |         |       | "$.data.room.create_time"                        | 当前时间戳           | 
  | platform | varchar(20)  | NO   | PRI |         |       |           -                                      | 平台                 | 
  | room_id  | varchar(200) | NO   | PRI |         |       | "$.data.room.id"                                 | 直播间ID             |
  | size     | varchar(100) |      |     | NULL    |       | "$.data.room.stream_url.live_core_sdk_data.size" | 流大小              |
  +----------+--------------+------+-----+---------+-------+--------------------------------------------------+---------------------+
  """
  live_core_sdk_data = LiveCoreSdkDataTable(db)
  live_core_sdk_data_tuple = {key: None for key in live_core_sdk_data.get_tuple()}

  set_dict_attr(live_core_sdk_data_tuple, "$.now",       now)
  set_dict_attr(live_core_sdk_data_tuple, "$.platform",  platform)
  set_dict_attr(live_core_sdk_data_tuple, "$.room_id",   str(room_id))
  
  try:
    live_core_sdk_data_tuple_list = live_core_sdk_data.get_record(live_core_sdk_data_tuple)
    if len(live_core_sdk_data_tuple_list) != 0:
      live_core_sdk_data_tuple = live_core_sdk_data_tuple_list.pop()
  except Exception as e:
    get_logger().error(f"{e}: {live_core_sdk_data.get_name()} >> >> >> >> >> data.room.stream_url.extra.live_core_sdk_data")
    live_core_sdk_data_tuple = {}

  """
  >> >> >> >> data.room.stream_url.push_urls
  +----------------+------------------+------+-----+---------+-------+------------------------------------+---------------------+
  | Field          | Type             | Null | Key | Default | Extra | Topology                           | Comment             |
  +----------------+------------------+------+-----+---------+-------+------------------------------------+---------------------+
  | now            | timestamp(3)     | NO   | PRI |         |       | "$.data.room.create_time"          | 当前时间戳           | 
  | platform       | varchar(20)      | NO   | PRI |         |       |           -                        | 平台                 | 
  | room_id        | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                   | 直播间ID             |
  | stream_url_id  | varchar(200)     | NO   | PRI |         |       | "$.data.room.stream_url.id"        | 直播流ID             |
  | push_url_index | unsigned bigint  | NO   | PRI |         |       |           -                        | 推流地址序号         | 
  | push_url       | text             |      |     | NULL    |       | "$.data.room.stream_url.push_urls" | 推流地址             |
  +----------------+------------------+------+-----+---------+-------+------------------------------------+---------------------+
  """
  stream_url_push_urls = StreamPushUrlTable(db)
  stream_url_push_urls_tuple = {key: None for key in stream_url_push_urls.get_tuple()}
  
  set_dict_attr(stream_url_push_urls_tuple, "$.now",        now)
  set_dict_attr(stream_url_push_urls_tuple, "$.platform",   platform)
  set_dict_attr(stream_url_push_urls_tuple, "$.room_id",    str(room_id))
  set_dict_attr(stream_url_push_urls_tuple, "$.stream_url_id", str(live_stream_tuple.get("id", '')))
  
  try:
    stream_url_push_urls_list = list()
    stream_url_push_urls_tuple_list = stream_url_push_urls.get_record(stream_url_push_urls_tuple, fetchall=True)
    for stream_push_url in stream_url_push_urls_tuple_list:
      stream_url_push_urls_list.append(stream_push_url.get('push_url', ''))
  except Exception as e:
    get_logger().error(f"{e}: {stream_url_push_urls.get_name()} >> >> >> >> >> data.room.stream_url.push_urls")
    stream_url_push_urls_list = []

  """
  >> >> >> data.room.tags
  +-----------+------------------+------+-----+---------+-------+---------------------------+---------------------+
  | Field     | Type             | Null | Key | Default | Extra | Topology                  | Comment             |
  +-----------+------------------+------+-----+---------+-------+---------------------------+---------------------+
  | now       | timestamp(3)     | NO   | PRI |         |       | "$.data.room.create_time" | 当前时间戳           | 
  | platform  | varchar(20)      | NO   | PRI |         |       |           -               | 平台                 | 
  | room_id   | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"          | 直播间ID             |
  | tag_index | unsigned bigint  | NO   | PRI |         |       |           -               | 标签序号             | 
  | tag       | tinytext         |      |     | NULL    |       | "$.data.room.tags"        | 标签列表             |
  +-----------+------------------+------+-----+---------+-------+---------------------------+---------------------+
  """
  room_tag = RoomTagTable(db)
  room_tag_tuple = {key: None for key in room_tag.get_tuple()}
  
  set_dict_attr(room_tag_tuple, "$.now",       now)
  set_dict_attr(room_tag_tuple, "$.platform",  platform)
  set_dict_attr(room_tag_tuple, "$.room_id",   str(room_id))
  
  try:
    room_tag_list = list()
    room_tag_tuple_list = room_tag.get_record(room_tag_tuple, fetchall=True)
    for room_tag_info in room_tag_tuple_list:
      room_tag.append(room_tag_info.get('tag', ''))
  except Exception as e:
    get_logger().error(f"{e}: {room_tag.get_name()} >> >> >> >> data.room.tags")
    room_tag_list = []

  """
  TBD
  >> >> >> data.room.top_fans
  """
  room_top_fans = list()

  """
  TBD
  >> >> >> data.room.upper_right_widget_data_list
  """
  room_upper_right_widget_data_list = list()

  """
  TBD
  >> >> >> data.room.vs_roles
  """
  room_vs_roles = list()

  """
  >> >> data.user
  """
  user = dict()
  user_record       = UserTable(db)
  user_record_tuple = {key: None for key in user_record.get_tuple()}
  set_dict_attr(user_record_tuple, "$.id", int(user_id), force=True)
  
  try:
    user_record_list = user_record.get_record(user_record_tuple)
    if len(user_record_list) != 0:
      user_record_tuple = user_record_list.pop()
  except Exception as e:
    get_logger().error(f"{e}: {user_record.get_name()} >> >> data.user")

  """
  >> >> >> data.user.badge_image_list
  """
  user_badge_image_list = list()
  
  """
  >> >> >> data.user.badge_image_list_v2
  """
  user_badge_image_list_v2 = list()

  """
  >> >> >> data.user.commerce_webcast_config_ids
  """
  user_commerce_webcast_config_ids = list()

  ##
  ## RoomOwnerTable for user
  ##
  user_owner_table = RoomOwnerTable(db)
  user_owner_tuple = {key: None for key in user_owner_table.get_tuple()}

  set_dict_attr(user_owner_tuple, "$.now",           now)
  set_dict_attr(user_owner_tuple, "$.platform",      platform)
  set_dict_attr(user_owner_tuple, "$.room_id",       str(room_id))
  set_dict_attr(user_owner_tuple, "$.owner_user_id", str(user_record_tuple.get('id', 0)))
  
  try:
    user_owner_tuple_list = user_owner_table.get_record(user_owner_tuple)
    if len(user_owner_tuple_list) != 0:
      user_owner_tuple = user_owner_tuple_list.pop()
  except Exception as e:
    get_logger().error(f"{e}: {user_owner_table.get_name()} >> >> >> data.user")
    user_owner_tuple = {}

  """
  >> >> >> data.user.media_badge_image_list
  """
  user_media_badge_image_list = list()

  """
  >> >> >> data.user.new_real_time_icons
  """
  user_new_real_time_icons = list()

  """
  >> >> >> data.user.real_time_icons
  """
  user_real_time_icons = list()

  """
  >> >> >> data.user.top_fans
  """
  user_top_fans = list()

  #####################################
  ##      export living data         ##
  #####################################
  """
  >> data
  """
  data = dict()

  """
  >> >> data.room
  """
  room = dict()
  set_dict_attr(room, "$.AnchorABMap",                          json.loads(room_attribute_tuple.get('AnchorABMap', {})),    force=True)
  set_dict_attr(room, "$.acquaintance_status",                  room_attribute_tuple.get('acquaintance_status', 0),         force=True)
  
  """
  >> >> >> data.room.admin_user_ids
  """
  set_dict_attr(room, "$.admin_user_ids",                       admin_user_ids,                                             force=True)

  """
  >> >> >> data.room.admin_user_open_ids
  """
  set_dict_attr(room, "$.admin_user_open_ids",                  admin_user_open_ids,                                        force=True)

  set_dict_attr(room, "$.anchor_scheduled_time_text",           room_attribute_tuple.get('anchor_scheduled_time_text', ''), force=True)
  set_dict_attr(room, "$.anchor_share_text",                    room_attribute_tuple.get('anchor_share_text', ''),          force=True)
  set_dict_attr(room, "$.anchor_tab_type",                      room_attribute_tuple.get('anchor_tab_type', 0),             force=True)
  set_dict_attr(room, "$.app_id",                               int(room_attribute_tuple.get('app_id', 0)),                      force=True)
  
  """
  >> >> >> data.room.assist_label_list
  """
  set_dict_attr(room, "$.assist_label_list",                    assist_label_list,                                          force=True)

  set_dict_attr(room, "$.auth_city",                            room_attribute_tuple.get('auth_city', ''),                  force=True)
  set_dict_attr(room, "$.auto_cover",                           room_attribute_tuple.get('auto_cover', 0),                  force=True)
  set_dict_attr(room, "$.base_category",                        room_attribute_tuple.get('base_category', 0),               force=True)
  
  if room_attribute_tuple.get('book_end_time', 0) is None:
    set_dict_attr(room, "$.book_end_time",                        0,               force=True)
  else:
    set_dict_attr(room, "$.book_end_time",                        room_attribute_tuple.get('book_end_time', 0),               force=True)
  
  if room_attribute_tuple.get('book_time', 0) is None:
    set_dict_attr(room, "$.book_time",                            0,                   force=True)
  else:
    set_dict_attr(room, "$.book_time",                            room_attribute_tuple.get('book_time', 0),                   force=True)
  set_dict_attr(room, "$.business_live",                        room_attribute_tuple.get('business_live', 0),               force=True)
  set_dict_attr(room, "$.category",                             room_attribute_tuple.get('category', 0),                    force=True)
  set_dict_attr(room, "$.cell_style",                           room_attribute_tuple.get('cell_style', 0),                  force=True)
  set_dict_attr(room, "$.challenge_info",                       room_record_tuple.get('challenge_info', ''),                force=True)
  set_dict_attr(room, "$.city_top_distance",                    room_attribute_tuple.get('city_top_distance', ''),          force=True)
  set_dict_attr(room, "$.client_version",                       int(room_attribute_tuple.get('client_version', 0)),              force=True)
  
  """
  >> >> >> data.room.comment_box
  """
  set_dict_attr(room, "$.comment_box.placeholder",              room_attribute_tuple.get('placeholder', ''),                force=True)
  
  set_dict_attr(room, "$.comment_name_mode",                    room_attribute_tuple.get('comment_name_mode', 0),           force=True)
  set_dict_attr(room, "$.common_label_list",                    room_attribute_tuple.get('common_label_list', ''),          force=True)
  
  """
  >> >> >> data.room.content_label
  """
  if content_label_picture_tuple:
    set_dict_attr(room, "$.content_label.avg_color",                content_label_picture_tuple.get('avg_color', ''),                force=True)

    """
    >> >> >> >> data.room.content_label.content
    """
    set_dict_attr(room, "$.content_label.content.alternative_text", content_label_picture_content_tuple.get('alternative_text', ''), force=True)
    set_dict_attr(room, "$.content_label.content.font_color",       content_label_picture_content_tuple.get('font_color', ''),       force=True)
    set_dict_attr(room, "$.content_label.content.level",            content_label_picture_content_tuple.get('level', 0),             force=True)
    set_dict_attr(room, "$.content_label.content.name",             content_label_picture_content_tuple.get('name', ''),             force=True)

    set_dict_attr(room, "$.content_label.flex_setting_list",        content_label_flex_setting_list,                                 force=True)
    set_dict_attr(room, "$.content_label.height",                   content_label_picture_tuple.get('height', 0),                    force=True)
    set_dict_attr(room, "$.content_label.image_type",               content_label_picture_tuple.get('image_type', 0),                force=True)
    set_dict_attr(room, "$.content_label.is_animated",              bool(content_label_picture_tuple.get('is_animated', False)),     force=True)
    set_dict_attr(room, "$.content_label.open_web_url",             content_label_picture_tuple.get('open_web_url', ''),             force=True)
    set_dict_attr(room, "$.content_label.text_setting_list",        content_label_text_setting_list,                                 force=True)
    set_dict_attr(room, "$.content_label.uri",                      content_label_picture_tuple.get('uri', ''),                      force=True)
    set_dict_attr(room, "$.content_label.url_list",                 content_label_url_list,                                          force=True)
    set_dict_attr(room, "$.content_label.width",                    content_label_picture_tuple.get('width', 0),                     force=True)
  
  set_dict_attr(room, "$.content_tag",                          room_attribute_tuple.get('content_tag', ''),                force=True)
  
  """
  >> >> >> data.room.cover
  """
  set_dict_attr(room, "$.cover.avg_color",                      cover_picture_tuple.get('avg_color', ''),             force=True)
  set_dict_attr(room, "$.cover.flex_setting_list",              cover_flex_setting_list,                              force=True)
  set_dict_attr(room, "$.cover.height",                         cover_picture_tuple.get('height', 0),                 force=True)
  set_dict_attr(room, "$.cover.image_type",                     cover_picture_tuple.get('image_type', 0),             force=True)
  set_dict_attr(room, "$.cover.is_animated",                    bool(cover_picture_tuple.get('is_animated', False)),        force=True)
  set_dict_attr(room, "$.cover.open_web_url",                   cover_picture_tuple.get('open_web_url', ''),          force=True)
  set_dict_attr(room, "$.cover.text_setting_list",              cover_text_setting_list,                              force=True)
  set_dict_attr(room, "$.cover.uri",                            cover_picture_tuple.get('uri', ''),                   force=True)
  set_dict_attr(room, "$.cover.url_list",                       cover_url_list,                                       force=True)
  set_dict_attr(room, "$.cover.width",                          cover_picture_tuple.get('width', 0),                  force=True)
  
  set_dict_attr(room, "$.create_time",                          floor(room_attribute_tuple.get('create_time', 0).timestamp()),           force=True)
  set_dict_attr(room, "$.danmaku_detail",                       room_record_tuple.get('danmaku_detail', 0),           force=True)

  """
  >> >> >> data.room.deco_list
  """
  deco_list = list()
  if len(room_deco_list) != 0:
    room_deco_dict = dict()
    for deco_index in range(0, len(room_deco_list)):
      set_dict_attr(room_deco_dict, "$.audit_text_color",          get_dict_attr(room_deco_list[deco_index], '$.audit_text_color'),  force=True)
      set_dict_attr(room_deco_dict, "$.content",                   get_dict_attr(room_deco_list[deco_index], '$.content'),           force=True)
      set_dict_attr(room_deco_dict, "$.h",                         get_dict_attr(room_deco_list[deco_index], '$.h'),                 force=True)
      set_dict_attr(room_deco_dict, "$.id",                        get_dict_attr(room_deco_list[deco_index], '$.id'),                force=True)
      
      """
      >> >> >> >> data.room.deco_list.image
      """
      if deco_image_exist_list[deco_index] is True:
        set_dict_attr(room_deco_dict, "$.image.avg_color",           deco_image_avg_color_list[deco_index],                  force=True)
        set_dict_attr(room_deco_dict, "$.image.flex_setting_list",   deco_image_flex_setting_list[deco_index],               force=True)
        set_dict_attr(room_deco_dict, "$.image.height",              deco_image_height_list[deco_index],                     force=True)
        set_dict_attr(room_deco_dict, "$.image.image_type",          deco_image_image_type_list[deco_index],                 force=True)
        set_dict_attr(room_deco_dict, "$.image.is_animated",         deco_image_is_animated_list[deco_index],                force=True)
        set_dict_attr(room_deco_dict, "$.image.open_web_url",        deco_image_open_web_url_list[deco_index],               force=True)
        set_dict_attr(room_deco_dict, "$.image.text_setting_list",   deco_image_text_setting_list[deco_index],               force=True)
        set_dict_attr(room_deco_dict, "$.image.uri",                 deco_image_uri_list[deco_index],                        force=True)
        set_dict_attr(room_deco_dict, "$.image.url_list",            deco_image_url_list[deco_index],                        force=True)
        set_dict_attr(room_deco_dict, "$.image.width",               deco_image_width_list[deco_index],                      force=True)
  
      """
      >> >> >> >> data.room.deco_list.input_rect
      """
      set_dict_attr(room_deco_dict, "$.input_rect",                room_deco_input_rect_list[deco_index],                        force=True)
      
      set_dict_attr(room_deco_dict, "$.kind",                      get_dict_attr(room_deco_list[deco_index], '$.kind'),              force=True)
      set_dict_attr(room_deco_dict, "$.max_length",                get_dict_attr(room_deco_list[deco_index], '$.max_length'),        force=True)
      
      """
      >> >> >> >> data.room.deco_list.nine_patch_image
      """
      if nine_patch_image_exist_list[deco_index] is True:
        set_dict_attr(room_deco_dict, "$.nine_patch_image.avg_color",         deco_nine_patch_image_avg_color_list[deco_index],     force=True)
        set_dict_attr(room_deco_dict, "$.nine_patch_image.flex_setting_list", deco_nine_patch_image_flex_setting_list[deco_index],  force=True)
        set_dict_attr(room_deco_dict, "$.nine_patch_image.height",            deco_nine_patch_image_height_list[deco_index],        force=True)
        set_dict_attr(room_deco_dict, "$.nine_patch_image.image_type",        deco_nine_patch_image_image_type_list[deco_index],    force=True)
        set_dict_attr(room_deco_dict, "$.nine_patch_image.is_animated",       deco_nine_patch_image_is_animated_list[deco_index],   force=True)
        set_dict_attr(room_deco_dict, "$.nine_patch_image.open_web_url",      deco_nine_patch_image_open_web_url_list[deco_index],  force=True)
        set_dict_attr(room_deco_dict, "$.nine_patch_image.text_setting_list", deco_nine_patch_image_text_setting_list[deco_index],  force=True)
        set_dict_attr(room_deco_dict, "$.nine_patch_image.uri",               deco_nine_patch_image_uri_list[deco_index],           force=True)
        set_dict_attr(room_deco_dict, "$.nine_patch_image.url_list",          deco_nine_patch_image_url_list[deco_index],           force=True)
        set_dict_attr(room_deco_dict, "$.nine_patch_image.width",             deco_nine_patch_image_width_list[deco_index],         force=True)
  
      """
      >> >> >> >> data.room.deco_list.reservation
      """
      set_dict_attr(room_deco_dict, "$.reservation.anchor_id",      get_dict_attr(room_deco_reservation_list[deco_index], '$.hanchor_id'),           force=True)
      set_dict_attr(room_deco_dict, "$.reservation.anchor_open_id", get_dict_attr(room_deco_reservation_list[deco_index], '$.anchor_open_id'),       force=True)
      set_dict_attr(room_deco_dict, "$.reservation.appointment_id", int(get_dict_attr(room_deco_reservation_list[deco_index], '$.appointment_id')),  force=True)
      set_dict_attr(room_deco_dict, "$.reservation.btn_color",      get_dict_attr(room_deco_reservation_list[deco_index], '$.btn_color'),            force=True)
      set_dict_attr(room_deco_dict, "$.reservation.btn_rect",       room_deco_reservation_btn_rect_list[deco_index],                                 force=True)
      set_dict_attr(room_deco_dict, "$.reservation.end_time",       get_dict_attr(room_deco_reservation_list[deco_index], '$.end_time'),             force=True)
      set_dict_attr(room_deco_dict, "$.reservation.is_reserved",    bool(get_dict_attr(room_deco_reservation_list[deco_index], '$.is_reserved')),    force=True)
      set_dict_attr(room_deco_dict, "$.reservation.room_id",        int(get_dict_attr(room_deco_reservation_list[deco_index], '$.room_id')),         force=True)
      set_dict_attr(room_deco_dict, "$.reservation.start_time",     get_dict_attr(room_deco_reservation_list[deco_index], '$.start_time'),           force=True)
      
      """
      >> >> >> >> 
      """
      if len(room_deco_text_foot_config_list) > deco_index:
        set_dict_attr(room_deco_dict, "$.text_font_config.DownloadUrl", get_dict_attr(room_deco_text_foot_config_list[deco_index], '$.DownloadUrl'), force=True)
        set_dict_attr(room_deco_dict, "$.text_font_config.FontID",      int(get_dict_attr(room_deco_text_foot_config_list[deco_index], '$.FontID')),      force=True)
        set_dict_attr(room_deco_dict, "$.text_font_config.Status",      get_dict_attr(room_deco_text_foot_config_list[deco_index], '$.Status'),      force=True)
        set_dict_attr(room_deco_dict, "$.text_font_config.font_name",   get_dict_attr(room_deco_text_foot_config_list[deco_index], '$.font_name'),   force=True)
      
      set_dict_attr(room_deco_dict, "$.status",                               get_dict_attr(room_deco_list[deco_index], '$.status'),                                force=True)
      set_dict_attr(room_deco_dict, "$.sub_type",                             get_dict_attr(room_deco_list[deco_index], '$.sub_type'),                              force=True)
      set_dict_attr(room_deco_dict, "$.text_color",                           get_dict_attr(room_deco_list[deco_index], '$.text_color'),                            force=True)
      set_dict_attr(room_deco_dict, "$.text_image_adjustable_end_position",   get_dict_attr(room_deco_list[deco_index], '$.text_image_adjustable_end_position'),    force=True)
      set_dict_attr(room_deco_dict, "$.text_image_adjustable_start_position", get_dict_attr(room_deco_list[deco_index], '$.text_image_adjustable_start_position'),  force=True)
      set_dict_attr(room_deco_dict, "$.text_size",                            get_dict_attr(room_deco_list[deco_index], '$.text_size'),                             force=True)
      set_dict_attr(room_deco_dict, "$.text_special_effects",                 room_deco_text_special_effects[deco_index],                                           force=True)
      set_dict_attr(room_deco_dict, "$.type",                                 get_dict_attr(room_deco_list[deco_index], '$.type'),                                  force=True)
      set_dict_attr(room_deco_dict, "$.w",                                    get_dict_attr(room_deco_list[deco_index], '$.w'),                                     force=True)
      set_dict_attr(room_deco_dict, "$.x",                                    get_dict_attr(room_deco_list[deco_index], '$.x'),                                     force=True)
      set_dict_attr(room_deco_dict, "$.y",                                    get_dict_attr(room_deco_list[deco_index], '$.y'),                                     force=True)
      deco_list.append(room_deco_dict)      
    set_dict_attr(room, "$.deco_list",                          deco_list,                                            force=True)
  else:
    set_dict_attr(room, "$.deco_list",                          [],                                                   force=True)

  set_dict_attr(room, "$.distance",                             room_attribute_tuple.get('distance', ''),             force=True)
  set_dict_attr(room, "$.distance_city",                        room_attribute_tuple.get('distance_city', ''),        force=True)
  set_dict_attr(room, "$.distance_km",                          room_attribute_tuple.get('distance_km', ''),          force=True)
  
  """
  >> >> >> data.room.dynamic_cover_dict
  """
  set_dict_attr(room, "$.dynamic_cover_dict",                   json.loads(room_attribute_tuple.get('dynamic_cover_dict', {})),   force=True)

  set_dict_attr(room, "$.dynamic_cover_uri",                    room_attribute_tuple.get('dynamic_cover_uri', ''),                force=True)
  set_dict_attr(room, "$.enable_room_perspective",              bool(room_attribute_tuple.get('enable_room_perspective', False)), force=True)
  
  """
  >> >> >> data.room.extra
  """
  set_dict_attr(room, "$.extra.create_scene",                   room_attribute_tuple.get('create_scene', ''),                     force=True)
  set_dict_attr(room, "$.extra.facial_unrecognised",            room_attribute_tuple.get('facial_unrecognised', 0),               force=True)
  set_dict_attr(room, "$.extra.geo_block",                      room_attribute_tuple.get('geo_block', 0),                         force=True)
  set_dict_attr(room, "$.extra.is_sandbox",                     bool(room_attribute_tuple.get('is_sandbox', False)),              force=True)
  set_dict_attr(room, "$.extra.is_virtual_anchor",              bool(room_attribute_tuple.get('is_virtual_anchor', False)),       force=True)
  set_dict_attr(room, "$.extra.limit_appid",                    room_attribute_tuple.get('limit_appid', ''),                      force=True)
  set_dict_attr(room, "$.extra.limit_strategy",                 room_attribute_tuple.get('limit_strategy', 0),                    force=True)
  set_dict_attr(room, "$.extra.realtime_playback_qualities",    realtime_playback_qualities,                                      force=True)
  set_dict_attr(room, "$.extra.realtime_playback_shift",        room_attribute_tuple.get('realtime_playback_shift', 0),           force=True)
  set_dict_attr(room, "$.extra.realtime_playback_start_shift",  room_attribute_tuple.get('realtime_playback_start_shift', 0),     force=True)
  set_dict_attr(room, "$.extra.realtime_replay_enabled",        bool(room_attribute_tuple.get('realtime_replay_enabled', False)), force=True)
  set_dict_attr(room, "$.extra.vr_type",                        room_attribute_tuple.get('vr_type', 0),                           force=True)
  set_dict_attr(room, "$.extra.vs_type",                        room_attribute_tuple.get('vs_type', 0),                           force=True)
  set_dict_attr(room, "$.extra.xigua_uid",                      int(room_attribute_tuple.get('xigua_uid', 0)),                         force=True)

  """
  >> >> >> data.room.fans_group_admin_user_ids
  """
  set_dict_attr(room, "$.fans_group_admin_user_ids",            fans_group_admin_user_ids,                                        force=True)

  """
  >> >> >> data.room.fans_group_admin_user_open_ids
  """
  set_dict_attr(room, "$.fans_group_admin_user_open_ids",       fans_group_admin_user_open_ids,                                   force=True)

  set_dict_attr(room, "$.fansclub_msg_style",                   room_attribute_tuple.get('fansclub_msg_style', 0),                force=True)
  set_dict_attr(room, "$.fcdn_appid",                           int(room_attribute_tuple.get('fcdn_appid', 0)),                        force=True)
  
  """
  >> >> >> data.room.feed_room_label
  """
  set_dict_attr(room, "$.feed_room_label.avg_color",                feed_room_label_picture_tuple.get('avg_color', ''),                force=True)
  
  """
  >> >> >> >> data.room.feed_room_label.content
  """
  set_dict_attr(room, "$.feed_room_label.content.alternative_text", feed_room_label_picture_content_tuple.get('alternative_text', ''), force=True)
  set_dict_attr(room, "$.feed_room_label.content.font_color",       feed_room_label_picture_content_tuple.get('font_color', ''),       force=True)
  set_dict_attr(room, "$.feed_room_label.content.level",            feed_room_label_picture_content_tuple.get('level', 0),             force=True)
  set_dict_attr(room, "$.feed_room_label.content.name",             feed_room_label_picture_content_tuple.get('name', ''),             force=True)
  set_dict_attr(room, "$.feed_room_label.flex_setting_list",        feed_room_label_flex_setting_list,                                 force=True)
  set_dict_attr(room, "$.feed_room_label.height",                   feed_room_label_picture_tuple.get('height', 0),                    force=True)
  set_dict_attr(room, "$.feed_room_label.image_type",               feed_room_label_picture_tuple.get('image_type', 0),                force=True)
  set_dict_attr(room, "$.feed_room_label.is_animated",              bool(feed_room_label_picture_tuple.get('is_animated', False)),     force=True)
  set_dict_attr(room, "$.feed_room_label.open_web_url",             feed_room_label_picture_tuple.get('open_web_url', ''),             force=True)
  set_dict_attr(room, "$.feed_room_label.text_setting_list",        feed_room_label_text_setting_list,                                 force=True)
  set_dict_attr(room, "$.feed_room_label.uri",                      feed_room_label_picture_tuple.get('uri', ''),                      force=True)
  set_dict_attr(room, "$.feed_room_label.url_list",                 feed_room_label_url_list,                                          force=True)
  set_dict_attr(room, "$.feed_room_label.width",                    feed_room_label_picture_tuple.get('width', 0),                     force=True)
  
  set_dict_attr(room, "$.filter_words",                             filter_words,                                                      force=True)

  set_dict_attr(room, "$.finish_reason",    room_attribute_tuple.get('finish_reason', 0),     force=True)
  set_dict_attr(room, "$.finish_time",      floor(room_attribute_tuple.get('finish_time', 0).timestamp()),       force=True)
  set_dict_attr(room, "$.finish_url",       room_attribute_tuple.get('finish_url', ''),       force=True)
  set_dict_attr(room, "$.follow_msg_style", room_attribute_tuple.get('follow_msg_style', 0),  force=True)
  set_dict_attr(room, "$.forum_extra_data", room_attribute_tuple.get('forum_extra_data', ''), force=True)
  set_dict_attr(room, "$.game_room_type",   room_attribute_tuple.get('game_room_type', 0),    force=True)
  set_dict_attr(room, "$.gift_msg_style",   room_attribute_tuple.get('gift_msg_style', 0),    force=True)
  set_dict_attr(room, "$.group_id",         int(room_attribute_tuple.get('group_id', 0)),          force=True)
  set_dict_attr(room, "$.group_source",     room_attribute_tuple.get('group_source', 0),      force=True)

  """
  >> >> >> data.room.guide_button
  """
  set_dict_attr(room, "$.guide_button.avg_color",         guide_button_picture_tuple.get('avg_color' ,''),            force=True)
  set_dict_attr(room, "$.guide_button.flex_setting_list", guide_button_flex_setting_list,                             force=True)
  set_dict_attr(room, "$.guide_button.height",            guide_button_picture_tuple.get('height', 0),                force=True)
  set_dict_attr(room, "$.guide_button.image_type",        guide_button_picture_tuple.get('image_type', 0),            force=True)
  set_dict_attr(room, "$.guide_button.is_animated",       bool(guide_button_picture_tuple.get('is_animated', False)), force=True)
  set_dict_attr(room, "$.guide_button.open_web_url",      guide_button_picture_tuple.get('open_web_url', ''),         force=True)
  set_dict_attr(room, "$.guide_button.text_setting_list", guide_button_text_setting_list,                             force=True)
  set_dict_attr(room, "$.guide_button.uri",               guide_button_picture_tuple.get('uri', ''),                  force=True)
  set_dict_attr(room, "$.guide_button.url_list",          guide_button_url_list,                                      force=True)
  set_dict_attr(room, "$.guide_button.width",             guide_button_picture_tuple.get('width', 0),                 force=True)

  set_dict_attr(room, "$.has_commerce_goods",  bool(room_attribute_tuple.get('has_commerce_goods', False)),           force=True)
  set_dict_attr(room, "$.has_promotion_games", room_attribute_tuple.get('has_promotion_games', 0),                    force=True)
  set_dict_attr(room, "$.highlight",           bool(room_attribute_tuple.get('highlight', False)),                    force=True)
  set_dict_attr(room, "$.hot_sentence_info",   room_record_tuple.get('hot_sentence_info', ''),                        force=True)
  set_dict_attr(room, "$.id",                  int(room_attribute_tuple.get('id', 0)),                                force=True)
  if room_attribute_tuple.get('id', 0) == 0:
    set_dict_attr(room, "$.id_str",                 '',                                                                force=True)
  else:
    set_dict_attr(room, "$.id_str",                 str(room_attribute_tuple.get('id', 0)),                            force=True)
  set_dict_attr(room, "$.introduction",             room_attribute_tuple.get('introduction', ''),                      force=True)
  set_dict_attr(room, "$.is_need_check_list",       bool(room_attribute_tuple.get('is_need_check_list', False)),       force=True)
  set_dict_attr(room, "$.is_official_channel_room", bool(room_attribute_tuple.get('is_official_channel_room', False)), force=True)
  set_dict_attr(room, "$.is_replay",                bool(room_attribute_tuple.get('is_replay', False)),                force=True)
  set_dict_attr(room, "$.is_show_inquiry_ball",     bool(room_attribute_tuple.get('is_show_inquiry_ball', False)),     force=True)
  set_dict_attr(room, "$.is_show_user_card_switch", bool(room_attribute_tuple.get('is_show_user_card_switch', False)), force=True)
  set_dict_attr(room, "$.item_explicit_info",       room_attribute_tuple.get('item_explicit_info', ''),                force=True)
  
  if room_record_tuple.get('last_ping_time', 0) is None:
    set_dict_attr(room, "$.last_ping_time",           0,                        force=True)
  else:
    set_dict_attr(room, "$.last_ping_time",           floor(room_record_tuple.get('last_ping_time', 0).timestamp()),                        force=True)
  set_dict_attr(room, "$.layout",                   room_attribute_tuple.get('layout', 0),                             force=True)
  set_dict_attr(room, "$.like_count",               room_record_tuple.get('room_like_count', 0),                       force=True)

  """
  >> >> >> data.room.link_mic
  """
  if room_link_mic_tuple:
    set_dict_attr(room, "$.link_mic.battle_scores", room_link_mic_battle_score_list, force=True)

    set_dict_attr(room, "$.link_mic.battle_settings.activity_mode", get_dict_attr(room_link_mic_battle_setting_tuple, "$.activity_mode"),                           force=True)
    set_dict_attr(room, "$.link_mic.battle_settings.battle_id",     int(get_dict_attr(room_link_mic_battle_setting_tuple, "$.battle_id")),                          force=True)
    set_dict_attr(room, "$.link_mic.battle_settings.channel_id",    int(get_dict_attr(room_link_mic_battle_setting_tuple, "$.channel_id")),                         force=True)
    set_dict_attr(room, "$.link_mic.battle_settings.duration",      get_dict_attr(room_link_mic_battle_setting_tuple, "$.duration"),                                force=True)
    set_dict_attr(room, "$.link_mic.battle_settings.finished",      get_dict_attr(room_link_mic_battle_setting_tuple, "$.finished"),                                force=True)
    set_dict_attr(room, "$.link_mic.battle_settings.match_type",    get_dict_attr(room_link_mic_battle_setting_tuple, "$.match_type"),                              force=True)
    set_dict_attr(room, "$.link_mic.battle_settings.play_mode",     get_dict_attr(room_link_mic_battle_setting_tuple, "$.play_mode"),                               force=True)
    set_dict_attr(room, "$.link_mic.battle_settings.start_time",    floor(get_dict_attr(room_link_mic_battle_setting_tuple, "$.start_time").timestamp()),           force=True)
    set_dict_attr(room, "$.link_mic.battle_settings.start_time_ms", floor(get_dict_attr(room_link_mic_battle_setting_tuple, "$.start_time_ms").timestamp() * 1000), force=True)
    set_dict_attr(room, "$.link_mic.battle_settings.team_mode",     get_dict_attr(room_link_mic_battle_setting_tuple, "$.team_mode"),                               force=True)
    set_dict_attr(room, "$.link_mic.battle_settings.theme",         get_dict_attr(room_link_mic_battle_setting_tuple, "$.theme"),                                   force=True)
    
    set_dict_attr(room, "$.link_mic.channel_id", get_dict_attr(room_link_mic_tuple, "$.channel_id"), force=True)
    
    set_dict_attr(room, "$.link_mic.channel_info.dimension", get_dict_attr(room_link_mic_channel_info_tuple, "$.dimension"), force=True)
    set_dict_attr(room, "$.link_mic.channel_info.layout",    get_dict_attr(room_link_mic_channel_info_tuple, "$.layout"),    force=True)
    set_dict_attr(room, "$.link_mic.channel_info.vendor",    get_dict_attr(room_link_mic_channel_info_tuple, "$.vendor"),    force=True)
    
    set_dict_attr(room, "$.link_mic.linkmic_anchor_count", get_dict_attr(room_link_mic_tuple, "$.linkmic_anchor_count"), force=True)
    set_dict_attr(room, "$.link_mic.rival_anchor_id",      int(get_dict_attr(room_link_mic_tuple, "$.rival_anchor_id")), force=True)
    set_dict_attr(room, "$.link_mic.rival_anchor_open_id", get_dict_attr(room_link_mic_tuple, "$.rival_anchor_open_id"), force=True)
  
  """
  >> >> >> data.room.linker_map
  """
  set_dict_attr(room, "$.linker_map",               json.loads(room_record_tuple.get('linker_map', {})),         force=True)
  set_dict_attr(room, "$.linkmic_display_type",     room_attribute_tuple.get('linkmic_display_type', 0),         force=True)
  set_dict_attr(room, "$.linkmic_layout",           room_attribute_tuple.get('linkmic_layout', 0),               force=True)

  """
  >> >> >> data.room.live_distribution
  """
  set_dict_attr(room, "$.live_distribution",     live_distribution,                                              force=True)

  set_dict_attr(room, "$.live_id",               int(room_attribute_tuple.get('live_id', 0)),                         force=True)
  set_dict_attr(room, "$.live_platform_source",  room_attribute_tuple.get('live_platform_source', ''),           force=True)
  set_dict_attr(room, "$.live_room_mode",        room_attribute_tuple.get('live_room_mode', 0),                  force=True)
  set_dict_attr(room, "$.live_type_audio",       bool(room_attribute_tuple.get('live_type_audio', False)),       force=True)
  set_dict_attr(room, "$.live_type_linkmic",     bool(room_attribute_tuple.get('live_type_linkmic', False)),     force=True)
  set_dict_attr(room, "$.live_type_normal",      bool(room_attribute_tuple.get('live_type_normal', False)),      force=True)
  set_dict_attr(room, "$.live_type_official",    bool(room_attribute_tuple.get('live_type_official', False)),    force=True)
  set_dict_attr(room, "$.live_type_sandbox",     bool(room_attribute_tuple.get('live_type_sandbox', False)),     force=True)
  set_dict_attr(room, "$.live_type_screenshot",  bool(room_attribute_tuple.get('live_type_screenshot', False)),  force=True)
  set_dict_attr(room, "$.live_type_third_party", bool(room_attribute_tuple.get('live_type_third_party', False)), force=True)
  set_dict_attr(room, "$.live_type_vs_live",     bool(room_attribute_tuple.get('live_type_vs_live', False)),     force=True)
  set_dict_attr(room, "$.live_type_vs_premiere", bool(room_attribute_tuple.get('live_type_vs_premiere', False)), force=True)

  """
  >> >> >> data.room.living_room_attrs
  """
  set_dict_attr(room, "$.living_room_attrs.admin_flag",    room_attribute_tuple.get('admin_flag', 0), force=True)
  set_dict_attr(room, "$.living_room_attrs.rank",          room_record_tuple.get('`rank`', 0),        force=True)
  set_dict_attr(room, "$.living_room_attrs.room_id",       int(room_record_tuple.get('id', 0)),            force=True)
  if room_record_tuple.get('id', 0) == 0:
    set_dict_attr(room, "$.living_room_attrs.room_id_str", '',                                        force=True)
  else:
    set_dict_attr(room, "$.living_room_attrs.room_id_str", str(room_record_tuple.get('id', 0)),       force=True)
  set_dict_attr(room, "$.living_room_attrs.silence_flag",  room_record_tuple.get('silence_flag', 0),  force=True)

  set_dict_attr(room, "$.location",                 room_attribute_tuple.get('location', ''),                 force=True)
  
  if room_record_tuple.get('lottery_finish_time', 0) is None:
    set_dict_attr(room, "$.lottery_finish_time",      0,          force=True)
  else:
    set_dict_attr(room, "$.lottery_finish_time",      room_record_tuple.get('lottery_finish_time', 0),          force=True)
  set_dict_attr(room, "$.luckymoney_num",           room_record_tuple.get('luckymoney_num', 0),               force=True)
  set_dict_attr(room, "$.mosaic_status",            room_record_tuple.get('mosaic_status', 0),                force=True)
  set_dict_attr(room, "$.mosaic_tip",               room_record_tuple.get('mosaic_tip', ''),                  force=True)
  set_dict_attr(room, "$.official_channel_open_id", room_attribute_tuple.get('official_channel_open_id', ''), force=True)
  set_dict_attr(room, "$.official_channel_uid",     int(room_attribute_tuple.get('official_channel_uid', 0)),      force=True)
  set_dict_attr(room, "$.orientation",              room_attribute_tuple.get('orientation', 0),               force=True)
  set_dict_attr(room, "$.os_type",                  room_attribute_tuple.get('os_type', 0),                   force=True)

  """
  >> >> >> data.room.owner
  """
  set_dict_attr(room, "$.owner.adversary_authorization_info",             room_owner_tuple.get('adversary_authorization_info', 0),                       force=True)
  set_dict_attr(room, "$.owner.adversary_user_status",                    room_owner_tuple.get('adversary_user_status', 0),                              force=True)
  set_dict_attr(room, "$.owner.age_range",                                room_owner_tuple.get('age_range', 0),                                          force=True)
  set_dict_attr(room, "$.owner.allow_be_located",                         bool(room_owner_tuple.get('allow_be_located', False)),                         force=True)
  set_dict_attr(room, "$.owner.allow_find_by_contacts",                   bool(room_owner_tuple.get('allow_find_by_contacts', False)),                   force=True)
  set_dict_attr(room, "$.owner.allow_others_download_video",              bool(room_owner_tuple.get('allow_others_download_video', False)),              force=True)
  set_dict_attr(room, "$.owner.allow_others_download_when_sharing_video", bool(room_owner_tuple.get('allow_others_download_when_sharing_video', False)), force=True)
  set_dict_attr(room, "$.owner.allow_share_show_profile",                 bool(room_owner_tuple.get('allow_share_show_profile', False)),                 force=True)
  set_dict_attr(room, "$.owner.allow_show_in_gossip",                     bool(room_owner_tuple.get('allow_show_in_gossip', False)),                     force=True)
  set_dict_attr(room, "$.owner.allow_show_my_action",                     bool(room_owner_tuple.get('allow_show_my_action', False)),                     force=True)
  set_dict_attr(room, "$.owner.allow_strange_comment",                    bool(room_owner_tuple.get('allow_strange_comment', False)),                    force=True)
  set_dict_attr(room, "$.owner.allow_unfollower_comment",                 bool(room_owner_tuple.get('allow_unfollower_comment', False)),                 force=True)
  set_dict_attr(room, "$.owner.allow_use_linkmic",                        bool(room_owner_tuple.get('allow_use_linkmic', False)),                        force=True)
  
  """
  >> >> >> >> data.room.owner.author_stats
  """
  if room_owner_author_stats_tuple:
    set_dict_attr(room, "$.owner.author_stats.variety_show_play_count",    get_dict_attr(room_owner_author_stats_tuple, "$.variety_show_play_count"),    force=True)
    set_dict_attr(room, "$.owner.author_stats.video_total_count",          get_dict_attr(room_owner_author_stats_tuple, "$.video_total_count"),          force=True)
    set_dict_attr(room, "$.owner.author_stats.video_total_favorite_count", get_dict_attr(room_owner_author_stats_tuple, "$.video_total_favorite_count"), force=True)
    set_dict_attr(room, "$.owner.author_stats.video_total_play_count",     get_dict_attr(room_owner_author_stats_tuple, "$.video_total_play_count"),     force=True)
    set_dict_attr(room, "$.owner.author_stats.video_total_series_count",   get_dict_attr(room_owner_author_stats_tuple, "$.video_total_series_count"),   force=True)
    set_dict_attr(room, "$.owner.author_stats.video_total_share_count",    get_dict_attr(room_owner_author_stats_tuple, "$.video_total_share_count"),    force=True)

  """
  >> >> >> >> data.room.owner.authentication_info
  """
  if bool(room_owner_auth_info_tuple.get('exist_authentication_info', False)) is True:
    set_dict_attr(room, "$.owner.authentication_info.account_cert_info",                   json.loads(room_owner_auth_info_tuple.get('account_cert_info', {})),     force=True)
    set_dict_attr(room, "$.owner.authentication_info.account_type_info.account_type_map",  json.loads(room_owner_auth_info_tuple.get('account_type_map', {})),      force=True)

    """
    >> >> >> >> >> data.room.owner.authentication_info.authentication_badge
    """
    set_dict_attr(room, "$.owner.authentication_info.authentication_badge.avg_color",         auth_info_picture_tuple.get('avg_color', ''),            force=True)
    set_dict_attr(room, "$.owner.authentication_info.authentication_badge.flex_setting_list", auth_info_flex_setting_list,                             force=True)
    set_dict_attr(room, "$.owner.authentication_info.authentication_badge.height",            auth_info_picture_tuple.get('height', 0),                force=True)
    set_dict_attr(room, "$.owner.authentication_info.authentication_badge.image_type",        auth_info_picture_tuple.get('image_type', 0),            force=True)
    set_dict_attr(room, "$.owner.authentication_info.authentication_badge.is_animated",       bool(auth_info_picture_tuple.get('is_animated', False)), force=True)
    set_dict_attr(room, "$.owner.authentication_info.authentication_badge.open_web_url",      auth_info_picture_tuple.get('open_web_url', ''),         force=True)
    set_dict_attr(room, "$.owner.authentication_info.authentication_badge.text_setting_list", auth_info_text_setting_list,                             force=True)
    set_dict_attr(room, "$.owner.authentication_info.authentication_badge.uri",               auth_info_picture_tuple.get('uri', ''),                  force=True)
    set_dict_attr(room, "$.owner.authentication_info.authentication_badge.url_list",          auth_info_url_list,                                      force=True)
    set_dict_attr(room, "$.owner.authentication_info.authentication_badge.width",             auth_info_picture_tuple.get('width', 0),                 force=True)

    """
    >> >> >> >> >> data.room.owner.authentication_info.authentication_badge_v2
    """
    set_dict_attr(room, "$.owner.authentication_info.authentication_badge_v2.avg_color",         auth_info_v2_picture_tuple.get('avg_color', ''),            force=True)
    set_dict_attr(room, "$.owner.authentication_info.authentication_badge_v2.flex_setting_list", auth_info_v2_flex_setting_list,                             force=True)
    set_dict_attr(room, "$.owner.authentication_info.authentication_badge_v2.height",            auth_info_v2_picture_tuple.get('height', 0),                force=True)
    set_dict_attr(room, "$.owner.authentication_info.authentication_badge_v2.image_type",        auth_info_v2_picture_tuple.get('image_type', 0),            force=True)
    set_dict_attr(room, "$.owner.authentication_info.authentication_badge_v2.is_animated",       bool(auth_info_v2_picture_tuple.get('is_animated', False)), force=True)
    set_dict_attr(room, "$.owner.authentication_info.authentication_badge_v2.open_web_url",      auth_info_v2_picture_tuple.get('open_web_url', ''),         force=True)
    set_dict_attr(room, "$.owner.authentication_info.authentication_badge_v2.text_setting_list", auth_info_v2_text_setting_list,                             force=True)
    set_dict_attr(room, "$.owner.authentication_info.authentication_badge_v2.uri",               auth_info_v2_picture_tuple.get('uri', ''),                  force=True)
    set_dict_attr(room, "$.owner.authentication_info.authentication_badge_v2.url_list",          auth_info_v2_url_list,                                      force=True)
    set_dict_attr(room, "$.owner.authentication_info.authentication_badge_v2.width",             auth_info_v2_picture_tuple.get('width', 0),                 force=True)
    
    set_dict_attr(room, "$.owner.authentication_info.custom_verify",            room_owner_auth_info_tuple.get('custom_verify', ''),            force=True)
    set_dict_attr(room, "$.owner.authentication_info.enterprise_verify_reason", room_owner_auth_info_tuple.get('enterprise_verify_reason', ''), force=True)
    set_dict_attr(room, "$.owner.authentication_info.level_list",               room_owner_auth_level_list,                                     force=True)

  set_dict_attr(room, "$.owner.authorization_info",                       room_owner_tuple.get('authorization_info', 0),                                            force=True)

  """
  >> >> >> >> data.room.owner.avatar_large
  """
  set_dict_attr(room, "$.owner.avatar_large.avg_color",         avatar_large_picture_tuple.get('avg_color', ''),            force=True)
  set_dict_attr(room, "$.owner.avatar_large.flex_setting_list", avatar_large_flex_setting_list,                             force=True)
  set_dict_attr(room, "$.owner.avatar_large.height",            avatar_large_picture_tuple.get('height', 0),                force=True)
  set_dict_attr(room, "$.owner.avatar_large.image_type",        avatar_large_picture_tuple.get('image_type', 0),            force=True)
  set_dict_attr(room, "$.owner.avatar_large.is_animated",       bool(avatar_large_picture_tuple.get('is_animated', False)), force=True)
  set_dict_attr(room, "$.owner.avatar_large.open_web_url",      avatar_large_picture_tuple.get('open_web_url', ''),         force=True)
  set_dict_attr(room, "$.owner.avatar_large.text_setting_list", avatar_large_text_setting_list,                             force=True)
  set_dict_attr(room, "$.owner.avatar_large.uri",               avatar_large_picture_tuple.get('uri', ''),                  force=True)
  set_dict_attr(room, "$.owner.avatar_large.url_list",          avatar_large_url_list,                                      force=True)
  set_dict_attr(room, "$.owner.avatar_large.width",             avatar_large_picture_tuple.get('width', 0),                 force=True)

  """
  >> >> >> >> data.room.owner.avatar_medium
  """
  set_dict_attr(room, "$.owner.avatar_medium.avg_color",         avatar_medium_picture_tuple.get('avg_color', ''),            force=True)
  set_dict_attr(room, "$.owner.avatar_medium.flex_setting_list", avatar_medium_flex_setting_list,                             force=True)
  set_dict_attr(room, "$.owner.avatar_medium.height",            avatar_medium_picture_tuple.get('height', 0),                force=True)
  set_dict_attr(room, "$.owner.avatar_medium.image_type",        avatar_medium_picture_tuple.get('image_type', 0),            force=True)
  set_dict_attr(room, "$.owner.avatar_medium.is_animated",       bool(avatar_medium_picture_tuple.get('is_animated', False)), force=True)
  set_dict_attr(room, "$.owner.avatar_medium.open_web_url",      avatar_medium_picture_tuple.get('open_web_url', ''),         force=True)
  set_dict_attr(room, "$.owner.avatar_medium.text_setting_list", avatar_medium_text_setting_list,                             force=True)
  set_dict_attr(room, "$.owner.avatar_medium.uri",               avatar_medium_picture_tuple.get('uri', ''),                  force=True)
  set_dict_attr(room, "$.owner.avatar_medium.url_list",          avatar_medium_url_list,                                      force=True)
  set_dict_attr(room, "$.owner.avatar_medium.width",             avatar_medium_picture_tuple.get('width', 0),                 force=True)

  """
  >> >> >> >> data.room.owner.avatar_thumb
  """
  set_dict_attr(room, "$.owner.avatar_thumb.avg_color",         avatar_thumb_picture_tuple.get('avg_color', ''),            force=True)
  set_dict_attr(room, "$.owner.avatar_thumb.flex_setting_list", avatar_thumb_flex_setting_list,                             force=True)
  set_dict_attr(room, "$.owner.avatar_thumb.height",            avatar_thumb_picture_tuple.get('height', 0),                force=True)
  set_dict_attr(room, "$.owner.avatar_thumb.image_type",        avatar_thumb_picture_tuple.get('image_type', 0),            force=True)
  set_dict_attr(room, "$.owner.avatar_thumb.is_animated",       bool(avatar_thumb_picture_tuple.get('is_animated', False)), force=True)
  set_dict_attr(room, "$.owner.avatar_thumb.open_web_url",      avatar_thumb_picture_tuple.get('open_web_url', ''),         force=True)
  set_dict_attr(room, "$.owner.avatar_thumb.text_setting_list", avatar_thumb_text_setting_list,                             force=True)
  set_dict_attr(room, "$.owner.avatar_thumb.uri",               avatar_thumb_picture_tuple.get('uri', ''),                  force=True)
  set_dict_attr(room, "$.owner.avatar_thumb.url_list",          avatar_thumb_url_list,                                      force=True)
  set_dict_attr(room, "$.owner.avatar_thumb.width",             avatar_thumb_picture_tuple.get('width', 0),                 force=True)
  
  """
  >> >> >> >> data.room.owner.badge_image_list
  """
  owner_badge_image_list = list()
  for index in range(0, len(owner_badge_image_uri_list)):
    owner_badge_image = dict()
    set_dict_attr(owner_badge_image, "$.avg_color", owner_badge_image_avg_color_list[index], force=True)

    """
    >> >> >> >> data.room.owner.badge_image_list[index].content
    """
    set_dict_attr(owner_badge_image, "$.content",           owner_badge_image_content_list[index],      force=True)

    set_dict_attr(owner_badge_image, "$.flex_setting_list", owner_badge_image_flex_setting_list[index], force=True)
    set_dict_attr(owner_badge_image, "$.height",            owner_badge_image_height_list[index],       force=True)
    set_dict_attr(owner_badge_image, "$.image_type",        owner_badge_image_image_type_list[index],   force=True)
    set_dict_attr(owner_badge_image, "$.is_animated",       bool(owner_badge_image_is_animated_list[index]),  force=True)
    set_dict_attr(owner_badge_image, "$.open_web_url",      owner_badge_image_open_web_url_list[index], force=True)
    set_dict_attr(owner_badge_image, "$.text_setting_list", owner_badge_image_text_setting_list[index], force=True)
    set_dict_attr(owner_badge_image, "$.uri",               owner_badge_image_uri_list[index],          force=True)
    set_dict_attr(owner_badge_image, "$.url_list",          owner_badge_image_url_list[index],          force=True)
    set_dict_attr(owner_badge_image, "$.width",             owner_badge_image_width_list[index],        force=True)
    owner_badge_image_list.insert(index, owner_badge_image)
  set_dict_attr(room, "$.owner.badge_image_list",                       owner_badge_image_list,                     force=True)

  """
  >> >> >> >> data.room.owner.badge_image_list_v2
  """
  owner_badge_image_list_v2 = list()
  for index in range(0, len(owner_badge_image_v2_uri_list)):
    owner_badge_image_list_v2_dict = dict()
    set_dict_attr(owner_badge_image_list_v2_dict, "$.avg_color", owner_badge_image_v2_avg_color_list[index], force=True)

    """
    >> >> >> >> data.room.owner.badge_image_list_v2[index].content
    """
    set_dict_attr(owner_badge_image_list_v2_dict, "$.content",           owner_badge_image_v2_content_list[index],      force=True)

    set_dict_attr(owner_badge_image_list_v2_dict, "$.flex_setting_list", owner_badge_image_v2_flex_setting_list[index], force=True)
    set_dict_attr(owner_badge_image_list_v2_dict, "$.height",            owner_badge_image_v2_height_list[index],       force=True)
    set_dict_attr(owner_badge_image_list_v2_dict, "$.image_type",        owner_badge_image_v2_image_type_list[index],   force=True)
    set_dict_attr(owner_badge_image_list_v2_dict, "$.is_animated",       bool(owner_badge_image_v2_is_animated_list[index]),  force=True)
    set_dict_attr(owner_badge_image_list_v2_dict, "$.open_web_url",      owner_badge_image_v2_open_web_url_list[index], force=True)
    set_dict_attr(owner_badge_image_list_v2_dict, "$.text_setting_list", owner_badge_image_v2_text_setting_list[index], force=True)
    set_dict_attr(owner_badge_image_list_v2_dict, "$.uri",               owner_badge_image_v2_uri_list[index],          force=True)
    set_dict_attr(owner_badge_image_list_v2_dict, "$.url_list",          owner_badge_image_v2_url_list[index],          force=True)
    set_dict_attr(owner_badge_image_list_v2_dict, "$.width",             owner_badge_image_v2_width_list[index],        force=True)
    owner_badge_image_list_v2.append(owner_badge_image_list_v2_dict)
  set_dict_attr(room, "$.owner.badge_image_list_v2",                       owner_badge_image_list_v2,                     force=True)

  if room_owner_tuple.get('bg_img_url','') is None:
    set_dict_attr(room, "$.owner.bg_img_url",          '',                  force=True)
  else:
    set_dict_attr(room, "$.owner.bg_img_url",          room_owner_tuple.get('bg_img_url',''),                  force=True)

  if room_owner_tuple.get('birthday', 0) is None:
    set_dict_attr(room, "$.owner.birthday",            0,                    force=True)
  else:
    set_dict_attr(room, "$.owner.birthday",            room_owner_tuple.get('birthday', 0),                    force=True)
  set_dict_attr(room, "$.owner.birthday_description",room_owner_tuple.get('birthday_description', ''),       force=True)
  set_dict_attr(room, "$.owner.birthday_valid",      bool(room_owner_tuple.get('birthday_valid', False)),    force=True)
  set_dict_attr(room, "$.owner.block_status",        room_owner_tuple.get('block_status', 0),                force=True)
  set_dict_attr(room, "$.owner.city",                room_owner_tuple.get('city',''),                        force=True)
  set_dict_attr(room, "$.owner.comment_restrict",    room_owner_tuple.get("comment_restrict", 0),            force=True)

  """
  >> >> >> >> data.room.owner.commerce_webcast_config_ids
  """
  set_dict_attr(room, "$.owner.commerce_webcast_config_ids", owner_commerce_webcast_config_ids,           force=True)
  
  set_dict_attr(room, "$.owner.constellation",         room_owner_tuple.get('constellation',         ''), force=True)
  set_dict_attr(room, "$.owner.consume_diamond_level", room_owner_tuple.get('consume_diamond_level', 0),  force=True)
  if room_owner_tuple.get('create_time',           0) is None:
    set_dict_attr(room, "$.owner.create_time",           0,  force=True)
  else:
    set_dict_attr(room, "$.owner.create_time",           room_owner_tuple.get('create_time',           0),  force=True)
  set_dict_attr(room, "$.owner.desensitized_nickname", room_owner_tuple.get('desensitized_nickname', ''), force=True)
  set_dict_attr(room, "$.owner.disable_ichat",         room_owner_tuple.get('disable_ichat',         0),  force=True)
  set_dict_attr(room, "$.owner.display_id",            room_owner_tuple.get('display_id',            ''), force=True)
  set_dict_attr(room, "$.owner.enable_ichat_img",      room_owner_tuple.get('enable_ichat_img',      0),  force=True)
  set_dict_attr(room, "$.owner.exp",                   room_owner_tuple.get('exp',                   0),  force=True)
  set_dict_attr(room, "$.owner.experience",            room_owner_tuple.get('experience',            0),  force=True)
  set_dict_attr(room, "$.owner.fan_ticket_count",      room_owner_tuple.get('fan_ticket_count',      0),  force=True)

  
  """
  >> >> >> >> data.room.owner.fans_club
  """

  """
  >> >> >> >> >> data.room.owner.fans_club.data
  """
  set_dict_attr(room, "$.owner.fans_club.data.anchor_id",               int(owner_fans_club_tuple.get('anchor_id',       0)),  force=True)
  set_dict_attr(room, "$.owner.fans_club.data.anchor_open_id",          owner_fans_club_tuple.get('anchor_open_id', ''),  force=True)

  """
  >> >> >> >> >> >> data.room.owner.fans_club.data.available_gift_ids
  """
  set_dict_attr(room, "$.owner.fans_club.data.available_gift_ids",      fans_club_available_gift_ids,                     force=True)

  """
  >> >> >> >> >> >> data.room.owner.fans_club.data.badge
  """
  for index in range(0, len(badge_icons_label_list)):
    set_dict_attr(room, f"$.owner.fans_club.data.badge.icons.{badge_icons_label_list[index]}.avg_color",         badge_icon_avg_color_list[index],          force=True)
    set_dict_attr(room, f"$.owner.fans_club.data.badge.icons.{badge_icons_label_list[index]}.flex_setting_list", badge_icon_flex_setting_list[index],       force=True)
    set_dict_attr(room, f"$.owner.fans_club.data.badge.icons.{badge_icons_label_list[index]}.height",            badge_icon_height_list[index],             force=True)
    set_dict_attr(room, f"$.owner.fans_club.data.badge.icons.{badge_icons_label_list[index]}.image_type",        badge_icon_image_type_list[index],         force=True)
    set_dict_attr(room, f"$.owner.fans_club.data.badge.icons.{badge_icons_label_list[index]}.is_animated",       bool(badge_icon_is_animated_list[index]),  force=True)
    set_dict_attr(room, f"$.owner.fans_club.data.badge.icons.{badge_icons_label_list[index]}.open_web_url",      badge_icon_open_web_url_list[index],       force=True)
    set_dict_attr(room, f"$.owner.fans_club.data.badge.icons.{badge_icons_label_list[index]}.text_setting_list", badge_icon_text_setting_list[index],       force=True)
    set_dict_attr(room, f"$.owner.fans_club.data.badge.icons.{badge_icons_label_list[index]}.uri",               badge_icon_uri_list[index],                force=True)
    set_dict_attr(room, f"$.owner.fans_club.data.badge.icons.{badge_icons_label_list[index]}.url_list",          badge_icon_url_list[index],                force=True)
    set_dict_attr(room, f"$.owner.fans_club.data.badge.icons.{badge_icons_label_list[index]}.width",             badge_icon_width_list[index],              force=True)
  
  
  set_dict_attr(room, "$.owner.fans_club.data.badge.title",           owner_fans_club_tuple.get('title', ''),                            force=True)
  
  set_dict_attr(room, "$.owner.fans_club.data.badge_type",            owner_fans_club_tuple.get('badge_type', ''),                       force=True)
  set_dict_attr(room, "$.owner.fans_club.data.club_name",             owner_fans_club_tuple.get('club_name', ''),                        force=True)
  set_dict_attr(room, "$.owner.fans_club.data.guard_expired_time",    owner_fans_club_tuple.get('badge_type', 0),                        force=True)
  set_dict_attr(room, "$.owner.fans_club.data.level",                 owner_fans_club_tuple.get('level', 0),                             force=True)
  set_dict_attr(room, "$.owner.fans_club.data.user_fans_club_status", owner_fans_club_tuple.get('user_fans_club_status', 0),             force=True)
  set_dict_attr(room, "$.owner.fans_club.data.user_guard_status",     owner_fans_club_tuple.get('badge_type', 0),                        force=True)
  
  set_dict_attr(room, "$.owner.fans_club.prefer_data",                json.loads(owner_fans_club_tuple.get('prefer_data', {})),          force=True)

  """
  >> >> >> >> data.room.owner.fans_group_info
  """
  set_dict_attr(room, "$.owner.fans_group_info.list_fans_group_url",  room_owner_tuple.get('list_fans_group_url', ''),             force=True)

  set_dict_attr(room, "$.owner.fold_stranger_chat",                   bool(room_owner_tuple.get('fold_stranger_chat', False)),     force=True)

  """
  >> >> >> >> data.room.owner.follow_info
  """
  set_dict_attr(room, "$.owner.follow_info.follow_status",                room_owner_tuple.get('follow_info_follow_status', 0),         force=True)
  set_dict_attr(room, "$.owner.follow_info.follower_count",               room_owner_tuple.get('follower_count', 0),                    force=True)
  set_dict_attr(room, "$.owner.follow_info.follower_count_str",           room_owner_tuple.get('follower_count_str', ''),               force=True)
  set_dict_attr(room, "$.owner.follow_info.following_count",              room_owner_tuple.get('following_count', 0),                   force=True)
  set_dict_attr(room, "$.owner.follow_info.following_count_str",          room_owner_tuple.get('following_count_str', ''),              force=True)
  set_dict_attr(room, "$.owner.follow_info.invalid_follow_status",        bool(room_owner_tuple.get('invalid_follow_status', False)),   force=True)
  set_dict_attr(room, "$.owner.follow_info.push_status",                  room_owner_tuple.get('follow_info_push_status', 0), force=True)
  set_dict_attr(room, "$.owner.follow_info.remark_name",                  room_owner_tuple.get('follow_info_remark_name', ''),          force=True)

  set_dict_attr(room, "$.owner.follow_status",                    room_owner_tuple.get('follow_status', 0),                  force=True)
  set_dict_attr(room, "$.owner.gender",                           room_owner_tuple.get('gender', 0),                         force=True)
  set_dict_attr(room, "$.owner.hotsoon_verified",                 bool(room_owner_tuple.get('hotsoon_verified', False)),     force=True)
  set_dict_attr(room, "$.owner.hotsoon_verified_reason",          room_owner_tuple.get('hotsoon_verified_reason', ''),       force=True)
  set_dict_attr(room, "$.owner.ichat_restrict_type",              room_owner_tuple.get('ichat_restrict_type', 0),            force=True)
  set_dict_attr(room, "$.owner.id",                               int(room_owner_tuple.get('id', 0)),                        force=True)
  if room_owner_tuple.get('id', 0) == 0:
    set_dict_attr(room, "$.owner.id_str",                         '',                                                        force=True)
  else:
    set_dict_attr(room, "$.owner.id_str",                         str(room_owner_tuple.get('id', '')),                       force=True)
  set_dict_attr(room, "$.owner.income_share_percent",             room_owner_tuple.get('income_share_percent', 0),           force=True)
  set_dict_attr(room, "$.owner.is_anonymous",                     bool(room_owner_tuple.get('is_anonymous', False)),         force=True)
  set_dict_attr(room, "$.owner.is_follower",                      bool(room_owner_tuple.get('is_follower', False)),          force=True)
  set_dict_attr(room, "$.owner.is_following",                     bool(room_owner_tuple.get('is_following', False)),         force=True)
  
  """
  >> >> >> >> >> data.room.owner.j_accredit_info
  """
  set_dict_attr(room, "$.owner.j_accredit_info.JAccreditAdvance", room_owner_tuple.get('JAccreditAdvance', 0),         force=True)
  set_dict_attr(room, "$.owner.j_accredit_info.JAccreditBasic",   room_owner_tuple.get('JAccreditBasic', 0),           force=True)
  set_dict_attr(room, "$.owner.j_accredit_info.JAccreditContent", room_owner_tuple.get('JAccreditContent', 0),         force=True)
  set_dict_attr(room, "$.owner.j_accredit_info.JAccreditLive",    room_owner_tuple.get('JAccreditLive', 0),            force=True)

  set_dict_attr(room, "$.owner.level",                            room_owner_tuple.get('level', 0),                    force=True)
  set_dict_attr(room, "$.owner.link_mic_stats",                   room_owner_tuple.get('link_mic_stats', 0),           force=True)
  set_dict_attr(room, "$.owner.location_city",                    room_owner_tuple.get('location_city', ''),           force=True)

  """
  TODO
  >> >> >> >> data.room.owner.media_badge_image_list
  """
  set_dict_attr(room, "$.owner.media_badge_image_list",           owner_media_badge_image_list,                              force=True)

  if room_owner_tuple.get('modify_time', 0) is not None:
    set_dict_attr(room, "$.owner.modify_time",                      floor(room_owner_tuple.get('modify_time', 0).timestamp()), force=True)
  else:
    set_dict_attr(room, "$.owner.modify_time",                      0, force=True)
  set_dict_attr(room, "$.owner.mystery_man",                      room_owner_tuple.get('mystery_man', 0),                    force=True)
  set_dict_attr(room, "$.owner.need_profile_guide",               bool(room_owner_tuple.get('need_profile_guide', False)),   force=True)

  """
  >> >> >> >> data.room.owner.new_real_time_icons
  """
  set_dict_attr(room, "$.owner.new_real_time_icons",             owner_new_real_time_icons,                           force=True)

  set_dict_attr(room, "$.owner.nickname",                        room_owner_tuple.get('nickname', ''),                force=True)
  
  """
  >> >> >> >> data.room.owner.own_room
  """
  if own_room_exist_flag is True:
    set_dict_attr(room, "$.owner.own_room.room_ids",                   owner_own_room_id_list,                            force=True)
    set_dict_attr(room, "$.owner.own_room.room_ids_display",           owner_own_room_id_display_list,                    force=True)
    set_dict_attr(room, "$.owner.own_room.room_ids_str",               owner_own_room_id_str_list,                        force=True)
  
  """
  >> >> >> >> data.room.owner.pay_grade
  """
  set_dict_attr(room, "$.owner.pay_grade.grade_banner",                   room_owner_tuple.get('pay_grade_banner', ''),                            force=True)
  set_dict_attr(room, "$.owner.pay_grade.grade_describe",                 room_owner_tuple.get('pay_grade_describe', ''),                          force=True)
  set_dict_attr(room, "$.owner.pay_grade.grade_describe_shining",         bool(room_owner_tuple.get('pay_grade_describe_shining', False)),         force=True)
  
  """
  TODO
  >> >> >> >> >> data.room.owner.pay_grade.grade_icon_list
  """
  set_dict_attr(room, "$.owner.pay_grade.grade_icon_list",                owner_pay_grade_icon_list,                                                force=True)

  set_dict_attr(room, "$.owner.pay_grade.level",                          room_owner_tuple.get('pay_grade_level', 0),                              force=True)
  set_dict_attr(room, "$.owner.pay_grade.name",                           room_owner_tuple.get('pay_grade_name', ''),                              force=True)

  """
  >> >> >> >> >> data.room.owner.pay_grade.new_im_icon_with_level
  """
  if owner_new_im_icon_with_level_picture_tuple:
    set_dict_attr(room, "$.owner.pay_grade.new_im_icon_with_level.avg_color",         owner_new_im_icon_with_level_picture_tuple.get('avg_color', ''),            force=True)
    set_dict_attr(room, "$.owner.pay_grade.new_im_icon_with_level.flex_setting_list", owner_new_im_icon_with_level_flex_setting_list,                             force=True)
    set_dict_attr(room, "$.owner.pay_grade.new_im_icon_with_level.height",            owner_new_im_icon_with_level_picture_tuple.get('height', 0),                force=True)
    set_dict_attr(room, "$.owner.pay_grade.new_im_icon_with_level.image_type",        owner_new_im_icon_with_level_picture_tuple.get('image_type', 0),            force=True)
    set_dict_attr(room, "$.owner.pay_grade.new_im_icon_with_level.is_animated",       bool(owner_new_im_icon_with_level_picture_tuple.get('is_animated', False)), force=True)
    set_dict_attr(room, "$.owner.pay_grade.new_im_icon_with_level.open_web_url",      owner_new_im_icon_with_level_picture_tuple.get('open_web_url', ''),         force=True)
    set_dict_attr(room, "$.owner.pay_grade.new_im_icon_with_level.text_setting_list", owner_new_im_icon_with_level_pic_text_setting_list,                         force=True)
    set_dict_attr(room, "$.owner.pay_grade.new_im_icon_with_level.uri",               owner_new_im_icon_with_level_picture_tuple.get('uri', ''),                  force=True)
    set_dict_attr(room, "$.owner.pay_grade.new_im_icon_with_level.url_list",          owner_new_im_icon_with_level_picture_url_list,                              force=True)
    set_dict_attr(room, "$.owner.pay_grade.new_im_icon_with_level.width",             owner_new_im_icon_with_level_picture_tuple.get('width', 0),                 force=True)

  """
  >> >> >> >> >> data.room.owner.pay_grade.new_live_icon
  """
  if owner_new_live_icon_picture_tuple:
    set_dict_attr(room, "$.owner.pay_grade.new_live_icon.avg_color",         owner_new_live_icon_picture_tuple.get('avg_color', ''),            force=True)
    set_dict_attr(room, "$.owner.pay_grade.new_live_icon.flex_setting_list", owner_new_live_icon_flex_setting_list,                             force=True)
    set_dict_attr(room, "$.owner.pay_grade.new_live_icon.height",            owner_new_live_icon_picture_tuple.get('height', 0),                force=True)
    set_dict_attr(room, "$.owner.pay_grade.new_live_icon.image_type",        owner_new_live_icon_picture_tuple.get('image_type', 0),            force=True)
    set_dict_attr(room, "$.owner.pay_grade.new_live_icon.is_animated",       bool(owner_new_live_icon_picture_tuple.get('is_animated', False)), force=True)
    set_dict_attr(room, "$.owner.pay_grade.new_live_icon.open_web_url",      owner_new_live_icon_picture_tuple.get('open_web_url', ''),         force=True)
    set_dict_attr(room, "$.owner.pay_grade.new_live_icon.text_setting_list", owner_new_live_icon_pic_text_setting_list,                         force=True)
    set_dict_attr(room, "$.owner.pay_grade.new_live_icon.uri",               owner_new_live_icon_picture_tuple.get('uri', ''),                  force=True)
    set_dict_attr(room, "$.owner.pay_grade.new_live_icon.url_list",          owner_new_live_icon_picture_url_list,                              force=True)
    set_dict_attr(room, "$.owner.pay_grade.new_live_icon.width",             owner_new_live_icon_picture_tuple.get('width', 0),                 force=True)

  set_dict_attr(room, "$.owner.pay_grade.next_diamond",           room_owner_tuple.get('pay_grade_next_diamond', 0),     force=True)
  set_dict_attr(room, "$.owner.pay_grade.next_name",              room_owner_tuple.get('pay_grade_next_name', ''),       force=True)
  set_dict_attr(room, "$.owner.pay_grade.next_privileges",        room_owner_tuple.get('pay_grade_next_privileges', ''), force=True)
  set_dict_attr(room, "$.owner.pay_grade.now_diamond",            room_owner_tuple.get('pay_grade_now_diamond', 0),      force=True)
  set_dict_attr(room, "$.owner.pay_grade.pay_diamond_bak",        room_owner_tuple.get('pay_diamond_bak', 0),            force=True)
  set_dict_attr(room, "$.owner.pay_grade.score",                  room_owner_tuple.get('pay_grade_score', 0),            force=True)
  set_dict_attr(room, "$.owner.pay_grade.screen_chat_type",       room_owner_tuple.get('screen_chat_type', 0),           force=True)
  set_dict_attr(room, "$.owner.pay_grade.this_grade_max_diamond", room_owner_tuple.get('this_grade_max_diamond', 0),     force=True)
  set_dict_attr(room, "$.owner.pay_grade.this_grade_min_diamond", room_owner_tuple.get('this_grade_min_diamond', 0),     force=True)
  set_dict_attr(room, "$.owner.pay_grade.total_diamond_count",    room_owner_tuple.get('total_diamond_count', 0),        force=True)
  set_dict_attr(room, "$.owner.pay_grade.upgrade_need_consume",   room_owner_tuple.get('upgrade_need_consume', 0),       force=True)

  set_dict_attr(room, "$.owner.pay_score",             room_owner_tuple.get('pay_score', 0),                      force=True)
  set_dict_attr(room, "$.owner.pay_scores",            room_owner_tuple.get('pay_scores', 0),                     force=True)
  set_dict_attr(room, "$.owner.public_area_oper_freq", room_owner_tuple.get('public_area_oper_freq', 0),          force=True)
  set_dict_attr(room, "$.owner.push_comment_status",   bool(room_owner_tuple.get('push_comment_status', False)),  force=True)
  set_dict_attr(room, "$.owner.push_digg",             bool(room_owner_tuple.get('push_digg', False)),            force=True)
  set_dict_attr(room, "$.owner.push_follow",           bool(room_owner_tuple.get('push_follow', False)),          force=True)
  set_dict_attr(room, "$.owner.push_friend_action",    bool(room_owner_tuple.get('push_friend_action', False)),   force=True)
  set_dict_attr(room, "$.owner.push_ichat",            bool(room_owner_tuple.get('push_ichat', False)),           force=True)
  set_dict_attr(room, "$.owner.push_status",           bool(room_owner_tuple.get('push_status', False)),          force=True)
  set_dict_attr(room, "$.owner.push_video_post",       bool(room_owner_tuple.get('push_video_post', False)),      force=True)
  set_dict_attr(room, "$.owner.push_video_recommend",  bool(room_owner_tuple.get('push_video_recommend', False)), force=True)
  
  """
  >> >> >> >> data.room.owner.real_time_icons
  """
  set_dict_attr(room, "$.owner.real_time_icons",  owner_real_time_icons,                        force=True)
  
  set_dict_attr(room, "$.owner.remark_name",      room_owner_tuple.get('remark_name', ''),      force=True)
  set_dict_attr(room, "$.owner.sec_uid",          room_owner_tuple.get('sec_uid', ''),          force=True)
  set_dict_attr(room, "$.owner.secret",           room_owner_tuple.get('secret', 0),            force=True)
  set_dict_attr(room, "$.owner.share_qrcode_uri", room_owner_tuple.get('share_qrcode_uri', ''), force=True)
  set_dict_attr(room, "$.owner.short_id",         int(room_owner_tuple.get('short_id', 0)),         force=True)
  set_dict_attr(room, "$.owner.signature",        room_owner_tuple.get('signature', ''),        force=True)
  set_dict_attr(room, "$.owner.special_id",       room_owner_tuple.get('special_id', ''),       force=True)
  set_dict_attr(room, "$.owner.status",           room_owner_tuple.get('status', 0),            force=True)

  """
  >> >> >> >> data.room.owner.subscribe
  """
  set_dict_attr(room, "$.owner.subscribe.buy_type",      owner_subscribe_tuple.get('buy_type', 0),            force=True)
  set_dict_attr(room, "$.owner.subscribe.identity_type", owner_subscribe_tuple.get('identity_type', 0),       force=True)
  set_dict_attr(room, "$.owner.subscribe.is_member",     bool(owner_subscribe_tuple.get('is_member', False)), force=True)
  set_dict_attr(room, "$.owner.subscribe.level",         owner_subscribe_tuple.get('level', 0),               force=True)
  set_dict_attr(room, "$.owner.subscribe.open",          owner_subscribe_tuple.get('open', 0),                force=True)

  set_dict_attr(room, "$.owner.telephone",    room_owner_tuple.get('telephone', ''),   force=True)
  set_dict_attr(room, "$.owner.ticket_count", room_owner_tuple.get('ticket_count', 0), force=True)

  """
  >> >> >> >> data.room.owner.top_fans
  """
  set_dict_attr(room, "$.owner.top_fans",                     owner_top_fans,                                          force=True)

  set_dict_attr(room, "$.owner.top_vip_no",                   room_owner_tuple.get('top_vip_no', 0),                   force=True)
  set_dict_attr(room, "$.owner.total_recharge_diamond_count", room_owner_tuple.get('total_recharge_diamond_count', 0), force=True)

  """
  >> >> >> >> data.room.owner.user_attr
  """

  """
  >> >> >> >> >> data.room.owner.user_attr.admin_privileges
  """
  set_dict_attr(room, "$.owner.user_attr.admin_privileges", owner_user_attr_admin_privileges_list,         force=True)

  set_dict_attr(room, "$.owner.user_attr.is_admin",         bool(room_owner_tuple.get('is_admin', False)),       force=True)
  set_dict_attr(room, "$.owner.user_attr.is_muted",         bool(room_owner_tuple.get('is_muted', False)),       force=True)
  set_dict_attr(room, "$.owner.user_attr.is_super_admin",   bool(room_owner_tuple.get('is_super_admin', False)), force=True)

  set_dict_attr(room, "$.owner.user_canceled",                  bool(room_owner_tuple.get('user_canceled', False)),                  force=True)
  
  """
  >> >> >> >> data.room.owner.user_dress_info
  """
  set_dict_attr(room, "$.owner.user_dress_info.dress_own_ids",  owner_dress_own_ids_list,  force=True)
  set_dict_attr(room, "$.owner.user_dress_info.dress_wear_ids", owner_dress_wear_ids_list, force=True)

  set_dict_attr(room, "$.owner.user_open_id",                   room_owner_tuple.get('user_open_id', ''),                      force=True)
  set_dict_attr(room, "$.owner.user_role",                      room_owner_tuple.get('user_role', 0),                          force=True)
  set_dict_attr(room, "$.owner.verified",                       bool(room_owner_tuple.get('verified', False)),                       force=True)
  set_dict_attr(room, "$.owner.verified_content",               room_owner_tuple.get('verified_content', ''),                  force=True)
  set_dict_attr(room, "$.owner.verified_mobile",                bool(room_owner_tuple.get('verified_mobile', False)),                force=True)
  set_dict_attr(room, "$.owner.verified_reason",                room_owner_tuple.get('verified_reason', ''),                   force=True)
  set_dict_attr(room, "$.owner.watch_duration_month",           room_owner_tuple.get('watch_duration_month', 0),               force=True)
  set_dict_attr(room, "$.owner.web_rid",                        room_owner_tuple.get('web_rid', ''),                           force=True)
  set_dict_attr(room, "$.owner.webcast_uid",                    room_owner_tuple.get('webcast_uid', ''),                       force=True)
  set_dict_attr(room, "$.owner.with_car_management_permission", bool(room_owner_tuple.get('with_car_management_permission', False)), force=True)
  set_dict_attr(room, "$.owner.with_commerce_permission",       bool(room_owner_tuple.get('with_commerce_permission', False)),       force=True)
  set_dict_attr(room, "$.owner.with_fusion_shop_entry",         bool(room_owner_tuple.get('with_fusion_shop_entry', False)),         force=True)

  set_dict_attr(room, "$.owner_device_id", int(room_attribute_tuple.get('owner_device_id', 0)), force=True)
  set_dict_attr(room, "$.owner_open_id",   room_attribute_tuple.get('owner_open_id', ''),  force=True)
  set_dict_attr(room, "$.owner_user_id",   int(room_attribute_tuple.get('owner_user_id', 0)),   force=True)

  """
  >> >> >> data.room.pack_meta
  """
  set_dict_attr(room, "$.pack_meta.cluster",  pack_meta_tuple.get('cluster', ''),  force=True)
  set_dict_attr(room, "$.pack_meta.dc",       pack_meta_tuple.get('dc', ''),       force=True)
  set_dict_attr(room, "$.pack_meta.env",      pack_meta_tuple.get('env', ''),      force=True)
  set_dict_attr(room, "$.pack_meta.extras",   json.loads(pack_meta_tuple.get('extras', {})),   force=True)
  set_dict_attr(room, "$.pack_meta.scene",    pack_meta_tuple.get('scene', ''),    force=True)
  set_dict_attr(room, "$.pack_meta.trace_id", pack_meta_tuple.get('trace_id', ''), force=True)
  
  """
  >> >> >> data.room.paid_live_data
  """
  set_dict_attr(room, "$.paid_live_data.anchor_right",        room_attribute_tuple.get('anchor_right', 0),        force=True)
  set_dict_attr(room, "$.paid_live_data.delivery",   room_attribute_tuple.get('delivery', 0),   force=True)
  set_dict_attr(room, "$.paid_live_data.duration",   room_attribute_tuple.get('duration', 0),   force=True)
  set_dict_attr(room, "$.paid_live_data.max_preview_duration", room_attribute_tuple.get('max_preview_duration', 0), force=True)
  set_dict_attr(room, "$.paid_live_data.need_delivery_notice", bool(room_attribute_tuple.get('need_delivery_notice', False)), force=True)
  set_dict_attr(room, "$.paid_live_data.paid_type",    room_attribute_tuple.get('paid_type', 0),    force=True)
  set_dict_attr(room, "$.paid_live_data.pay_ab_type",  room_attribute_tuple.get('pay_ab_type', 0),  force=True)
  set_dict_attr(room, "$.paid_live_data.privilege_info", room_attribute_tuple.get('privilege_info', {}), force=True)
  set_dict_attr(room, "$.paid_live_data.privilege_info_map", room_attribute_tuple.get('privilege_info_map', {}), force=True)
  set_dict_attr(room, "$.paid_live_data.view_right", room_attribute_tuple.get('view_right', 0), force=True)

  set_dict_attr(room, "$.popularity",              room_record_tuple.get('popularity', 0),              force=True)
  set_dict_attr(room, "$.popularity_str",          room_record_tuple.get('popularity_str', ''),         force=True)
  
  if room_record_tuple.get('pre_enter_time', 0) is None:
    set_dict_attr(room, "$.pre_enter_time",          0,          force=True)
  else:
    set_dict_attr(room, "$.pre_enter_time",          room_record_tuple.get('pre_enter_time', 0),          force=True)
  set_dict_attr(room, "$.preview_copy",            room_record_tuple.get('preview_copy', ''),           force=True)
  set_dict_attr(room, "$.preview_flow_tag",        room_record_tuple.get('preview_flow_tag', 0),        force=True)
  set_dict_attr(room, "$.private_info",            room_record_tuple.get('private_info', ''),           force=True)
  set_dict_attr(room, "$.ranklist_audience_type",  room_record_tuple.get('ranklist_audience_type', 0),  force=True)
  set_dict_attr(room, "$.real_distance",           room_record_tuple.get('real_distance', 0),           force=True)
  set_dict_attr(room, "$.redpacket_audience_auth", room_record_tuple.get('redpacket_audience_auth', 0), force=True)
  set_dict_attr(room, "$.relation_tag",            room_record_tuple.get('relation_tag', ''),           force=True)
  set_dict_attr(room, "$.replay",                  bool(room_record_tuple.get('replay', False)),              force=True)
  set_dict_attr(room, "$.replay_location",         room_record_tuple.get('replay_location', 0),         force=True)
  set_dict_attr(room, "$.room_audit_status",       room_record_tuple.get('room_audit_status', 0),       force=True)

  """
  >> >> >> data.room.room_auth
  """
  set_dict_attr(room, "$.room_auth.AIClone",                        room_auth_tuple.get('AIClone', 0),                        force=True)
  set_dict_attr(room, "$.room_auth.AdminCommentWall",               room_auth_tuple.get('AdminCommentWall', 0),               force=True)
  set_dict_attr(room, "$.room_auth.AnchorAudioChat",                room_auth_tuple.get('AnchorAudioChat', 0),                force=True)
  set_dict_attr(room, "$.room_auth.AnchorColdMessageTiled",         room_auth_tuple.get('AnchorColdMessageTiled', 0),         force=True)
  set_dict_attr(room, "$.room_auth.AnchorHotMessageAggregated",     room_auth_tuple.get('AnchorHotMessageAggregated', 0),     force=True)
  set_dict_attr(room, "$.room_auth.AnchorMission",                  room_auth_tuple.get('AnchorMission', 0),                  force=True)
  set_dict_attr(room, "$.room_auth.AudioChat",                      room_auth_tuple.get('AudioChat', 0),                      force=True)
  set_dict_attr(room, "$.room_auth.AudioChatTotext",                room_auth_tuple.get('AudioChatTotext', 0),                force=True)
  set_dict_attr(room, "$.room_auth.Banner",                         room_auth_tuple.get('Banner', 0),                         force=True)
  set_dict_attr(room, "$.room_auth.BulletStyle",                    room_auth_tuple.get('BulletStyle', 0),                    force=True)
  set_dict_attr(room, "$.room_auth.CanSellTicket",                  room_auth_tuple.get('CanSellTicket', 0),                  force=True)
  set_dict_attr(room, "$.room_auth.CastScreen",                     room_auth_tuple.get('CastScreen', 0),                     force=True)
  set_dict_attr(room, "$.room_auth.CastScreenExplicit",             room_auth_tuple.get('CastScreenExplicit', 0),             force=True)
  set_dict_attr(room, "$.room_auth.Chat",                           bool(room_auth_tuple.get('Chat', False)),                 force=True)
  set_dict_attr(room, "$.room_auth.ChatDispatch",                   room_auth_tuple.get('ChatDispatch', 0),                   force=True)
  set_dict_attr(room, "$.room_auth.ChatDynamicSlideSpeed",          room_auth_tuple.get('ChatDynamicSlideSpeed', 0),          force=True)
  set_dict_attr(room, "$.room_auth.ChatDynamicSlideSpeedAnchor",    room_auth_tuple.get('ChatDynamicSlideSpeedAnchor', 0),    force=True)
  set_dict_attr(room, "$.room_auth.ChatGuideEmoji",                 room_auth_tuple.get('ChatGuideEmoji', 0),                 force=True)
  set_dict_attr(room, "$.room_auth.ChatGuideImage",                 room_auth_tuple.get('ChatGuideImage', 0),                 force=True)
  set_dict_attr(room, "$.room_auth.ChatIdentity",                   room_auth_tuple.get('ChatIdentity', 0),                   force=True)
  set_dict_attr(room, "$.room_auth.ChatMention",                    room_auth_tuple.get('ChatMention', 0),                    force=True)
  set_dict_attr(room, "$.room_auth.ChatMentionV2",                  room_auth_tuple.get('ChatMentionV2', 0),                  force=True)
  set_dict_attr(room, "$.room_auth.ChatOperate",                    room_auth_tuple.get('ChatOperate', 0),                    force=True)
  set_dict_attr(room, "$.room_auth.ChatReply",                      room_auth_tuple.get('ChatReply', 0),                      force=True)
  set_dict_attr(room, "$.room_auth.ClearEntranceOption",            room_auth_tuple.get('ClearEntranceOption', 0),            force=True)
  set_dict_attr(room, "$.room_auth.Collect",                        room_auth_tuple.get('Collect', 0),                        force=True)
  set_dict_attr(room, "$.room_auth.CommentWall",                    room_auth_tuple.get('CommentWall', 0),                    force=True)
  set_dict_attr(room, "$.room_auth.CommerceCard",                   room_auth_tuple.get('CommerceCard', 0),                   force=True)
  set_dict_attr(room, "$.room_auth.CommerceComponent",              room_auth_tuple.get('CommerceComponent', 0),              force=True)
  set_dict_attr(room, "$.room_auth.CommonCard",                     room_auth_tuple.get('CommonCard', 0),                     force=True)
  set_dict_attr(room, "$.room_auth.CountType",                      room_auth_tuple.get('CountType', 0),                      force=True)
  set_dict_attr(room, "$.room_auth.Danmaku",                        bool(room_auth_tuple.get('Danmaku', False)),              force=True)
  set_dict_attr(room, "$.room_auth.DanmakuDefault",                 room_auth_tuple.get('DanmakuDefault', 0),                 force=True)
  set_dict_attr(room, "$.room_auth.Denounce",                       room_auth_tuple.get('Denounce', 0),                       force=True)
  set_dict_attr(room, "$.room_auth.Digg",                           bool(room_auth_tuple.get('Digg', False)),                 force=True)
  set_dict_attr(room, "$.room_auth.Dislike",                        room_auth_tuple.get('Dislike', 0),                        force=True)
  set_dict_attr(room, "$.room_auth.DonationSticker",                room_auth_tuple.get('DonationSticker', 0),                force=True)
  set_dict_attr(room, "$.room_auth.DouPlus",                        room_auth_tuple.get('DouPlus', 0),                        force=True)
  set_dict_attr(room, "$.room_auth.DouPlusPopularityGem",           room_auth_tuple.get('DouPlusPopularityGem', 0),           force=True)
  set_dict_attr(room, "$.room_auth.DownloadVideo",                  room_auth_tuple.get('DownloadVideo', 0),                  force=True)
  set_dict_attr(room, "$.room_auth.EcomFansClub",                   room_auth_tuple.get('EcomFansClub', 0),                   force=True)
  set_dict_attr(room, "$.room_auth.EmojiOutside",                   room_auth_tuple.get('EmojiOutside', 0),                   force=True)
  set_dict_attr(room, "$.room_auth.EnhancedTouch",                  room_auth_tuple.get('EnhancedTouch', 0),                  force=True)
  set_dict_attr(room, "$.room_auth.EnterEffects",                   room_auth_tuple.get('EnterEffects', 0),                   force=True)
  set_dict_attr(room, "$.room_auth.ExpandScreen",                   room_auth_tuple.get('ExpandScreen', 0),                   force=True)
  set_dict_attr(room, "$.room_auth.FansClub",                       room_auth_tuple.get('FansClub', 0),                       force=True)
  set_dict_attr(room, "$.room_auth.FansClubBlessing",               room_auth_tuple.get('FansClubBlessing', 0),               force=True)
  set_dict_attr(room, "$.room_auth.FansClubDeclaration",            room_auth_tuple.get('FansClubDeclaration', 0),            force=True)
  set_dict_attr(room, "$.room_auth.FansClubLetter",                 room_auth_tuple.get('FansClubLetter', 0),                 force=True)
  set_dict_attr(room, "$.room_auth.FansClubNotice",                 room_auth_tuple.get('FansClubNotice', 0),                 force=True)
  set_dict_attr(room, "$.room_auth.FansGroup",                      room_auth_tuple.get('FansGroup', 0),                      force=True)
  set_dict_attr(room, "$.room_auth.FeaturedPublicScreen",           room_auth_tuple.get('FeaturedPublicScreen', 0),           force=True)
  set_dict_attr(room, "$.room_auth.FirstFeedHistChat",              room_auth_tuple.get('FirstFeedHistChat', 0),              force=True)
  set_dict_attr(room, "$.room_auth.FixedChat",                      room_auth_tuple.get('FixedChat', 0),                      force=True)
  set_dict_attr(room, "$.room_auth.FrequentlyChat",                 room_auth_tuple.get('FrequentlyChat', 0),                 force=True)
  set_dict_attr(room, "$.room_auth.FusionEmoji",                    room_auth_tuple.get('FusionEmoji', 0),                    force=True)
  set_dict_attr(room, "$.room_auth.GamePointsPlaying",              room_auth_tuple.get('GamePointsPlaying', 0),              force=True)
  set_dict_attr(room, "$.room_auth.Gift",                           bool(room_auth_tuple.get('Gift', False)),                 force=True)
  set_dict_attr(room, "$.room_auth.GiftAnchorMt",                   room_auth_tuple.get('GiftAnchorMt', 0),                   force=True)
  set_dict_attr(room, "$.room_auth.GiftVote",                       room_auth_tuple.get('GiftVote', 0),                       force=True)
  set_dict_attr(room, "$.room_auth.Highlights",                     room_auth_tuple.get('Highlights', 0),                     force=True)
  set_dict_attr(room, "$.room_auth.HostTeam",                       room_auth_tuple.get('HostTeam', 0),                       force=True)
  set_dict_attr(room, "$.room_auth.HostTeamChannel",                room_auth_tuple.get('HostTeamChannel', 0),                force=True)
  set_dict_attr(room, "$.room_auth.HotChatTray",                    room_auth_tuple.get('HotChatTray', 0),                    force=True)
  set_dict_attr(room, "$.room_auth.HourRank",                       room_auth_tuple.get('HourRank', 0),                       force=True)
  set_dict_attr(room, "$.room_auth.ImHeatValue",                    room_auth_tuple.get('ImHeatValue', 0),                    force=True)
  set_dict_attr(room, "$.room_auth.IndustryService",                room_auth_tuple.get('IndustryService', 0),                force=True)
  set_dict_attr(room, "$.room_auth.InteractionGift",                room_auth_tuple.get('InteractionGift', 0),                force=True)
  set_dict_attr(room, "$.room_auth.InteractiveComponent",           room_auth_tuple.get('InteractiveComponent', 0),           force=True)
  set_dict_attr(room, "$.room_auth.ItemShare",                      room_auth_tuple.get('ItemShare', 0),                      force=True)
  set_dict_attr(room, "$.room_auth.KtvOrderSong",                   room_auth_tuple.get('KtvOrderSong', 0),                   force=True)
  set_dict_attr(room, "$.room_auth.Landscape",                      room_auth_tuple.get('Landscape', 0),                      force=True)
  set_dict_attr(room, "$.room_auth.LandscapeChat",                  room_auth_tuple.get('LandscapeChat', 0),                  force=True)
  set_dict_attr(room, "$.room_auth.LandscapeChatDynamicSlideSpeed", room_auth_tuple.get('LandscapeChatDynamicSlideSpeed', 0), force=True)
  set_dict_attr(room, "$.room_auth.LandscapeGift",                  room_auth_tuple.get('LandscapeGift', 0),                  force=True)
  set_dict_attr(room, "$.room_auth.LandscapeScreenCapture",         room_auth_tuple.get('LandscapeScreenCapture', 0),         force=True)
  set_dict_attr(room, "$.room_auth.LandscapeScreenRecording",       room_auth_tuple.get('LandscapeScreenRecording', 0),       force=True)
  set_dict_attr(room, "$.room_auth.LandscapeScreenShare",           room_auth_tuple.get('LandscapeScreenShare', 0),           force=True)
  set_dict_attr(room, "$.room_auth.Like",                           room_auth_tuple.get('`Like`', 0),                         force=True)
  set_dict_attr(room, "$.room_auth.LinkmicGuestLike",               room_auth_tuple.get('LinkmicGuestLike', 0),               force=True)
  set_dict_attr(room, "$.room_auth.LongPressOption",                room_auth_tuple.get('LongPressOption', 0),                force=True)
  set_dict_attr(room, "$.room_auth.LongTouch",                      room_auth_tuple.get('LongTouch', 0),                      force=True)
  set_dict_attr(room, "$.room_auth.LuckMoney",                      bool(room_auth_tuple.get('LuckMoney', False)),            force=True)
  set_dict_attr(room, "$.room_auth.MarkUser",                       room_auth_tuple.get('MarkUser', 0),                       force=True)
  set_dict_attr(room, "$.room_auth.MediaHistoryMessage",            room_auth_tuple.get('MediaHistoryMessage', 0),            force=True)
  set_dict_attr(room, "$.room_auth.MediaLinkmic",                   room_auth_tuple.get('MediaLinkmic', 0),                   force=True)
  set_dict_attr(room, "$.room_auth.MessageDispatch",                room_auth_tuple.get('MessageDispatch', 0),                force=True)
  set_dict_attr(room, "$.room_auth.MessageGift",                    room_auth_tuple.get('MessageGift', 0),                    force=True)
  set_dict_attr(room, "$.room_auth.MissionCenter",                  room_auth_tuple.get('MissionCenter', 0),                  force=True)
  set_dict_attr(room, "$.room_auth.MoreAnchor",                     room_auth_tuple.get('MoreAnchor', 0),                     force=True)
  set_dict_attr(room, "$.room_auth.MoreHistChat",                   room_auth_tuple.get('MoreHistChat', 0),                   force=True)
  set_dict_attr(room, "$.room_auth.MultiplierPlayback",             room_auth_tuple.get('MultiplierPlayback', 0),             force=True)
  set_dict_attr(room, "$.room_auth.MyLiveEntrance",                 room_auth_tuple.get('MyLiveEntrance', 0),                 force=True)
  set_dict_attr(room, "$.room_auth.OnlyTa",                         room_auth_tuple.get('OnlyTa', 0),                         force=True)
  set_dict_attr(room, "$.room_auth.PCPlay",                         room_auth_tuple.get('PCPlay', 0),                         force=True)
  set_dict_attr(room, "$.room_auth.POI",                            bool(room_auth_tuple.get('POI', False)),                  force=True)
  set_dict_attr(room, "$.room_auth.PadPlay",                        room_auth_tuple.get('PadPlay', 0),                        force=True)
  set_dict_attr(room, "$.room_auth.PanelECService",                 room_auth_tuple.get('PanelECService', 0),                 force=True)
  set_dict_attr(room, "$.room_auth.PlayerRankList",                 room_auth_tuple.get('PlayerRankList', 0),                 force=True)
  set_dict_attr(room, "$.room_auth.Poster",                         room_auth_tuple.get('Poster', 0),                         force=True)
  set_dict_attr(room, "$.room_auth.PosterCache",                    room_auth_tuple.get('PosterCache', 0),                    force=True)
  set_dict_attr(room, "$.room_auth.PreviewChatExpose",              room_auth_tuple.get('PreviewChatExpose', 0),              force=True)
  set_dict_attr(room, "$.room_auth.PreviewHotCommentSwitch",        room_auth_tuple.get('PreviewHotCommentSwitch', 0),        force=True)
  set_dict_attr(room, "$.room_auth.ProjectionBtn",                  room_auth_tuple.get('ProjectionBtn', 0),                  force=True)
  set_dict_attr(room, "$.room_auth.Props",                          bool(room_auth_tuple.get('Props', False)),                force=True)
  set_dict_attr(room, "$.room_auth.PublicScreen",                   room_auth_tuple.get('PublicScreen', 0),                   force=True)
  set_dict_attr(room, "$.room_auth.QuizGamePointsPlaying",          room_auth_tuple.get('QuizGamePointsPlaying', 0),          force=True)
  set_dict_attr(room, "$.room_auth.RecordScreen",                   room_auth_tuple.get('RecordScreen', 0),                   force=True)
  set_dict_attr(room, "$.room_auth.RoomChannel",                    room_auth_tuple.get('RoomChannel', 0),                    force=True)
  set_dict_attr(room, "$.room_auth.RoomChatLikeDisplay",            room_auth_tuple.get('RoomChatLikeDisplay', 0),            force=True)
  set_dict_attr(room, "$.room_auth.RoomChatOperatePanel",           room_auth_tuple.get('RoomChatOperatePanel', 0),           force=True)
  set_dict_attr(room, "$.room_auth.RoomContributor",                bool(room_auth_tuple.get('RoomContributor', False)),      force=True)
  set_dict_attr(room, "$.room_auth.RoomWidget",                     room_auth_tuple.get('RoomWidget', 0),                     force=True)
  set_dict_attr(room, "$.room_auth.ScreenBottomInfo",               room_auth_tuple.get('ScreenBottomInfo', 0),               force=True)
  set_dict_attr(room, "$.room_auth.ScreenProjectionBarrage",        room_auth_tuple.get('ScreenProjectionBarrage', 0),        force=True)
  set_dict_attr(room, "$.room_auth.Seek",                           room_auth_tuple.get('Seek', 0),                           force=True)
  set_dict_attr(room, "$.room_auth.Selection",                      room_auth_tuple.get('Selection', 0),                      force=True)
  set_dict_attr(room, "$.room_auth.SelectionAlbum",                 room_auth_tuple.get('SelectionAlbum', 0),                 force=True)
  set_dict_attr(room, "$.room_auth.Share",                          room_auth_tuple.get('Share', 0),                          force=True)
  set_dict_attr(room, "$.room_auth.ShortTouch",                     room_auth_tuple.get('ShortTouch', 0),                     force=True)
  set_dict_attr(room, "$.room_auth.ShortTouchTempState",            room_auth_tuple.get('ShortTouchTempState', 0),            force=True)
  set_dict_attr(room, "$.room_auth.ShowGamePlugin",                 room_auth_tuple.get('ShowGamePlugin', 0),                 force=True)
  set_dict_attr(room, "$.room_auth.ShowQualification",              room_auth_tuple.get('ShowQualification', 0),              force=True)
  set_dict_attr(room, "$.room_auth.SmallWindowDisplay",             room_auth_tuple.get('SmallWindowDisplay', 0),             force=True)
  set_dict_attr(room, "$.room_auth.SmallWindowPlayer",              room_auth_tuple.get('SmallWindowPlayer', 0),              force=True)
  set_dict_attr(room, "$.room_auth.StickyMessage",                  room_auth_tuple.get('StickyMessage', 0),                  force=True)
  set_dict_attr(room, "$.room_auth.StreamAdaptation",               room_auth_tuple.get('StreamAdaptation', 0),               force=True)
  set_dict_attr(room, "$.room_auth.StrokeUpDownGuide",              room_auth_tuple.get('StrokeUpDownGuide', 0),              force=True)
  set_dict_attr(room, "$.room_auth.SubscribeCardPackage",           room_auth_tuple.get('SubscribeCardPackage', 0),           force=True)
  set_dict_attr(room, "$.room_auth.Teleprompter",                   room_auth_tuple.get('Teleprompter', 0),                   force=True)
  set_dict_attr(room, "$.room_auth.TextGift",                       room_auth_tuple.get('TextGift', 0),                       force=True)
  set_dict_attr(room, "$.room_auth.TimedShutdown",                  room_auth_tuple.get('TimedShutdown', 0),                  force=True)
  set_dict_attr(room, "$.room_auth.ToolbarBubble",                  room_auth_tuple.get('ToolbarBubble', 0),                  force=True)
  set_dict_attr(room, "$.room_auth.Topic",                          room_auth_tuple.get('Topic', 0),                          force=True)
  set_dict_attr(room, "$.room_auth.TypingCommentState",             room_auth_tuple.get('TypingCommentState', 0),             force=True)
  set_dict_attr(room, "$.room_auth.UgcVSReplayDelete",              room_auth_tuple.get('UgcVSReplayDelete', 0),              force=True)
  set_dict_attr(room, "$.room_auth.UgcVsReplayVisibility",          room_auth_tuple.get('UgcVsReplayVisibility', 0),          force=True)
  set_dict_attr(room, "$.room_auth.UpRightStatsFloatingLayer",      room_auth_tuple.get('UpRightStatsFloatingLayer', 0),      force=True)
  set_dict_attr(room, "$.room_auth.UseHostInfo",                    room_auth_tuple.get('UseHostInfo', 0),                    force=True)
  set_dict_attr(room, "$.room_auth.UserCard",                       bool(room_auth_tuple.get('UserCard', False)),             force=True)
  set_dict_attr(room, "$.room_auth.UserCorner",                     room_auth_tuple.get('UserCorner', 0),                     force=True)
  set_dict_attr(room, "$.room_auth.VSGift",                         room_auth_tuple.get('VSGift', 0),                         force=True)
  set_dict_attr(room, "$.room_auth.VSRank",                         room_auth_tuple.get('VSRank', 0),                         force=True)
  set_dict_attr(room, "$.room_auth.VSTopic",                        room_auth_tuple.get('VSTopic', 0),                        force=True)
  set_dict_attr(room, "$.room_auth.VerticalRank",                   room_auth_tuple.get('VerticalRank', 0),                   force=True)
  set_dict_attr(room, "$.room_auth.VerticalScreenShare",            room_auth_tuple.get('VerticalScreenShare', 0),            force=True)
  set_dict_attr(room, "$.room_auth.VideoAmplificationType",         room_auth_tuple.get('VideoAmplificationType', 0),         force=True)
  set_dict_attr(room, "$.room_auth.VideoShare",                     room_auth_tuple.get('VideoShare', 0),                     force=True)
  set_dict_attr(room, "$.room_auth.VsCommentBar",                   room_auth_tuple.get('VsCommentBar', 0),                   force=True)
  set_dict_attr(room, "$.room_auth.VsDouPlus",                      room_auth_tuple.get('VsDouPlus', 0),                      force=True)
  set_dict_attr(room, "$.room_auth.VsExtensionEnableFollow",        room_auth_tuple.get('VsExtensionEnableFollow', 0),        force=True)
  set_dict_attr(room, "$.room_auth.VsFansClub",                     room_auth_tuple.get('VsFansClub', 0),                     force=True)
  set_dict_attr(room, "$.room_auth.VsWelcomeDanmaku",               room_auth_tuple.get('VsWelcomeDanmaku', 0),               force=True)
  set_dict_attr(room, "$.room_auth.WordAssociation",                room_auth_tuple.get('WordAssociation', 0),                force=True)

  set_dict_attr(room, "$.room_create_ab_param",          room_record_tuple.get('room_create_ab_param', ''),                   force=True)
  set_dict_attr(room, "$.room_layout",                   room_attribute_tuple.get('room_layout', 0),                          force=True)

  """
  >> >> >> data.room.room_tabs
  """
  set_dict_attr(room, "$.room_tabs",                      room_tab_list,                      force=True)

  set_dict_attr(room, "$.room_tag",                      room_attribute_tuple.get('room_tag', ''),                      force=True)

  """
  >> >> >> data.room.room_view_stats
  """
  set_dict_attr(room, "$.room_view_stats.display_long",          room_record_tuple.get('view_stats_display_long', ''),          force=True)
  set_dict_attr(room, "$.room_view_stats.display_long_anchor",   room_record_tuple.get('view_stats_display_long_anchor', ''),   force=True)
  set_dict_attr(room, "$.room_view_stats.display_middle",        room_record_tuple.get('view_stats_display_middle', ''),        force=True)
  set_dict_attr(room, "$.room_view_stats.display_middle_anchor", room_record_tuple.get('view_stats_display_middle_anchor', ''), force=True)
  set_dict_attr(room, "$.room_view_stats.display_short",         room_record_tuple.get('view_stats_display_short', ''),         force=True)
  set_dict_attr(room, "$.room_view_stats.display_short_anchor",  room_record_tuple.get('view_stats_display_short_anchor', ''),  force=True)
  set_dict_attr(room, "$.room_view_stats.display_type",          room_record_tuple.get('view_stats_display_type', 0),           force=True)
  set_dict_attr(room, "$.room_view_stats.display_value",         room_record_tuple.get('view_stats_display_value', 0),          force=True)
  set_dict_attr(room, "$.room_view_stats.display_version",       int(room_record_tuple.get('view_stats_display_version', 0)),   force=True)
  set_dict_attr(room, "$.room_view_stats.incremental",           bool(room_record_tuple.get('view_stats_incremental', False)),  force=True)
  set_dict_attr(room, "$.room_view_stats.is_hidden",             bool(room_record_tuple.get('view_stats_is_hidden', False)),    force=True)

  set_dict_attr(room, "$.screen_capture_sharing_title",          room_record_tuple.get('screen_capture_sharing_title', ''),     force=True)
  set_dict_attr(room, "$.scroll_config",                         room_attribute_tuple.get('scroll_config', ''),                 force=True)
  set_dict_attr(room, "$.search_id",                             int(room_attribute_tuple.get('search_id', 0)),                 force=True)
  set_dict_attr(room, "$.sell_goods",                            bool(room_attribute_tuple.get('sell_goods', False)),           force=True)
  set_dict_attr(room, "$.share_msg_style",                       room_attribute_tuple.get('share_msg_style', 0),                force=True)
  set_dict_attr(room, "$.share_url",                             room_attribute_tuple.get('share_url', ''),                     force=True)  
  
  """
  >> >> >> data.room.sharing_music_id_list
  """
  set_dict_attr(room, "$.sharing_music_id_list",                           room_sharing_music_id_list,                                    force=True)

  set_dict_attr(room, "$.short_title",                                     room_record_tuple.get('short_title', ''),                      force=True)      

  """
  >> >> >> data.room.short_touch_area_config
  """
  """
  >> >> >> data.room.short_touch_area_config.elements
  """
  for element in room_short_touch_area_config_element_list:
    set_dict_attr(room, "$.short_touch_area_config.elements." + str(element.get('type', 0)), element, force=True)

  set_dict_attr(room, "$.short_touch_area_config.forbidden_types_map",                             json.loads(room_short_touch_area_config_tuple.get('forbidden_types_map', {})),   force=True)

  """
  >> >> >> >> data.room.short_touch_area_config.strategy_feat_whitelist
  """
  set_dict_attr(room, "$.short_touch_area_config.strategy_feat_whitelist", room_strategy_feat_whitelist_list,              force=True)

  """
  >> >> >> >> data.room.short_touch_area_config.temp_state_condition_map
  """
  for temp_state_condition in room_temp_state_condition_map_list:
    set_dict_attr(room, f"$.short_touch_area_config.temp_state_condition_map.{temp_state_condition.get('type', {}).get('strategy_type', 0)}", temp_state_condition, force=True)

  """
  >> >> >> >> data.room.short_touch_area_config.temp_state_global_condition
  """
  set_dict_attr(room, "$.short_touch_area_config.temp_state_global_condition.allow_count",  room_temp_state_global_condition_dict.get('allow_count', 0),  force=True)
  set_dict_attr(room, "$.short_touch_area_config.temp_state_global_condition.duration_gap", room_temp_state_global_condition_dict.get('duration_gap', 0), force=True)
  
  """
  >> >> >> >> >> data.room.short_touch_area_config.temp_state_global_condition.ignore_strategy_types
  """
  set_dict_attr(room, "$.short_touch_area_config.temp_state_global_condition.ignore_strategy_types", room_temp_state_global_condition_ignore_strategy_type_list, force=True)
  
  """
  >> >> >> >> >> data.room.short_touch_area_config.temp_state_strategy
  >> >> >> >> >> data.room.short_touch_area_config.temp_state_strategy.'x'.strategy_map
  """
  set_dict_attr(room, "$.short_touch_area_config.temp_state_strategy", room_temp_state_strategy_dict, force=True)

  set_dict_attr(room, "$.sofa_layout",                       room_record_tuple.get('sofa_layout', 0),                      force=True)
  set_dict_attr(room, "$.stamps",                            room_record_tuple.get('stamps', ''),                           force=True)
  set_dict_attr(room, "$.start_time",                        floor(room_attribute_tuple.get('start_time', 0).timestamp()),                    force=True)

  """
  >> >> >> data.room.stats
  """
  set_dict_attr(room, "$.stats.comment_count",                       room_record_tuple.get('comment_count', 0),                       force=True)
  set_dict_attr(room, "$.stats.digg_count",                          room_record_tuple.get('digg_count', 0),                          force=True)
  set_dict_attr(room, "$.stats.dou_plus_promotion",                  room_record_tuple.get('dou_plus_promotion', ''),                 force=True)
  set_dict_attr(room, "$.stats.enter_count",                         room_record_tuple.get('enter_count', 0),                         force=True)
  set_dict_attr(room, "$.stats.fan_ticket",                          room_record_tuple.get('fan_ticket', 0),                          force=True)
  set_dict_attr(room, "$.stats.follow_count",                        room_record_tuple.get('follow_count', 0),                        force=True)
  set_dict_attr(room, "$.stats.gift_uv_count",                       room_record_tuple.get('gift_uv_count', 0),                       force=True)
  set_dict_attr(room, "$.stats.id",                                  int(room_attribute_tuple.get('id', 0)),                               force=True)
  if room_attribute_tuple.get('id', 0) == 0:
    set_dict_attr(room, "$.stats.id_str",                            '',                       force=True)
  else:
    set_dict_attr(room, "$.stats.id_str",                            str(room_attribute_tuple.get('id', 0)),                       force=True)
  set_dict_attr(room, "$.stats.like_count",                          room_record_tuple.get('like_count', 0),                          force=True)
  set_dict_attr(room, "$.stats.money",                               room_record_tuple.get('money', 0),                               force=True)
  set_dict_attr(room, "$.stats.total_user",                          room_record_tuple.get('total_user', 0),                          force=True)
  set_dict_attr(room, "$.stats.total_user_desp",                     room_record_tuple.get('total_user_desp', ''),                    force=True)
  set_dict_attr(room, "$.stats.total_user_str",                      room_record_tuple.get('total_user_str', ''),                     force=True)
  set_dict_attr(room, "$.stats.up_right_stats_str",                  room_record_tuple.get('up_right_stats_str', ''),                 force=True)
  set_dict_attr(room, "$.stats.up_right_stats_str_complete",         room_record_tuple.get('up_right_stats_str_complete', ''),        force=True)
  
  """
  >> >> >> >> data.room.stats.user_count_composition
  """
  set_dict_attr(room, "$.stats.user_count_composition.city",         room_record_tuple.get('user_count_composition_city', 0),         force=True)
  set_dict_attr(room, "$.stats.user_count_composition.my_follow",    room_record_tuple.get('user_count_composition_my_follow', 0),    force=True)
  set_dict_attr(room, "$.stats.user_count_composition.other",        room_record_tuple.get('user_count_composition_other', 0),        force=True)
  set_dict_attr(room, "$.stats.user_count_composition.video_detail", room_record_tuple.get('user_count_composition_video_detail', 0), force=True)
  
  set_dict_attr(room, "$.stats.user_count_str",                      str(room_record_tuple.get('user_count_str', '')),                     force=True)
  set_dict_attr(room, "$.stats.watermelon",                          room_record_tuple.get('watermelon', 0),                          force=True)
  set_dict_attr(room, "$.stats.welfare_donation_amount",             room_record_tuple.get('welfare_donation_amount', 0),             force=True)

  set_dict_attr(room, "$.status",            room_record_tuple.get('status', 0),                              force=True)
  if room_record_tuple.get('stream_close_time', 0) is None:
    set_dict_attr(room, "$.stream_close_time", 0,                   force=True)
  else:
    set_dict_attr(room, "$.stream_close_time", room_record_tuple.get('stream_close_time', 0),                   force=True)
  set_dict_attr(room, "$.stream_id",         int(room_record_tuple.get('stream_id', 0)),                           force=True)
  if room_record_tuple.get('stream_id', 0) != 0:
    set_dict_attr(room, "$.stream_id_str",   str(room_record_tuple.get('stream_id', 0)),                      force=True)
  else:
    set_dict_attr(room, "$.stream_id_str",   '',                                                              force=True)
  set_dict_attr(room, "$.stream_provider",   room_record_tuple.get('stream_provider', 0),                     force=True)

  """
  >> >> >> data.room.stream_url
  >> >> >> >> data.room.stream_url.candidate_resolution
  """
  set_dict_attr(room, "$.stream_url.candidate_resolution", candidate_resolution_list, force=True)

  """
  >> >> >> >> data.room.stream_url.complete_push_urls
  """
  set_dict_attr(room, "$.stream_url.complete_push_urls", complete_push_url_list, force=True)
  set_dict_attr(room, "$.stream_url.default_resolution", live_stream_tuple.get('default_resolution', ''), force=True)

  """
  >> >> >> >> data.room.stream_url.extra
  """
  set_dict_attr(room, "$.stream_url.extra.anchor_interact_profile",   live_stream_tuple.get('anchor_interact_profile', 0),   force=True)
  set_dict_attr(room, "$.stream_url.extra.audience_interact_profile", live_stream_tuple.get('audience_interact_profile', 0), force=True)
  set_dict_attr(room, "$.stream_url.extra.bframe_enable",             bool(live_stream_tuple.get('bframe_enable', False)),         force=True)
  set_dict_attr(room, "$.stream_url.extra.bitrate_adapt_strategy",    live_stream_tuple.get('bitrate_adapt_strategy', 0),    force=True)
  set_dict_attr(room, "$.stream_url.extra.bytevc1_enable",            bool(live_stream_tuple.get('bytevc1_enable', False)),        force=True)
  set_dict_attr(room, "$.stream_url.extra.default_bitrate",           live_stream_tuple.get('default_bitrate', 0),           force=True)
  set_dict_attr(room, "$.stream_url.extra.fps",                       live_stream_tuple.get('fps', 0),                       force=True)
  set_dict_attr(room, "$.stream_url.extra.gop_sec",                   live_stream_tuple.get('gop_sec', 0),                   force=True)
  set_dict_attr(room, "$.stream_url.extra.h265_enable",               bool(live_stream_tuple.get('h265_enable', False)),           force=True)
  set_dict_attr(room, "$.stream_url.extra.hardware_encode",           bool(live_stream_tuple.get('hardware_encode', False)),       force=True)
  set_dict_attr(room, "$.stream_url.extra.height",                    live_stream_tuple.get('height', 0),                    force=True)
  set_dict_attr(room, "$.stream_url.extra.max_bitrate",               live_stream_tuple.get('max_bitrate', 0),               force=True)
  set_dict_attr(room, "$.stream_url.extra.min_bitrate",               live_stream_tuple.get('min_bitrate', 0),               force=True)
  set_dict_attr(room, "$.stream_url.extra.roi",                       bool(live_stream_tuple.get('roi', False)),                    force=True)
  set_dict_attr(room, "$.stream_url.extra.sw_roi",                    bool(live_stream_tuple.get('sw_roi', False)),                 force=True)
  set_dict_attr(room, "$.stream_url.extra.video_profile",             live_stream_tuple.get('video_profile', 0),              force=True)
  set_dict_attr(room, "$.stream_url.extra.width",                     live_stream_tuple.get('width', 0),                      force=True)

  """
  >> >> >> >> data.room.stream_url.flv_pull_url
  """
  set_dict_attr(room, "$.stream_url.flv_pull_url", json.loads(live_stream_tuple.get('flv_pull_url', '')), force=True)

  """
  >> >> >> >> data.room.stream_url.flv_pull_url_params
  """
  set_dict_attr(room, "$.stream_url.flv_pull_url_params", json.loads(live_stream_tuple.get('flv_pull_url_params', {})), force=True)
  set_dict_attr(room, "$.stream_url.hls_pull_url", live_stream_tuple.get('hls_pull_url', ''), force=True)

  """
  >> >> >> >> data.room.stream_url.hls_pull_url_map
  """
  set_dict_attr(room, "$.stream_url.hls_pull_url_map", json.loads(live_stream_tuple.get('hls_pull_url_map', {})), force=True)
  set_dict_attr(room, "$.stream_url.hls_pull_url_params", json.loads(live_stream_tuple.get('hls_pull_url_params', '')), force=True)
  set_dict_attr(room, "$.stream_url.id", int(live_stream_tuple.get('id', 0)), force=True)
  if live_stream_tuple.get('id', 0) != 0:
    set_dict_attr(room, "$.stream_url.id_str", str(live_stream_tuple.get('id', 0)), force=True)
  else:
    set_dict_attr(room, "$.stream_url.id_str", '', force=True)

  """
  >> >> >> >> data.room.stream_url.live_core_sdk_data
  >> >> >> >> >> data.room.stream_url.live_core_sdk_data.pull_data
  >> >> >> >> >> >> data.room.stream_url.live_core_sdk_data.pull_data.Flv
  """
  set_dict_attr(room, "$.stream_url.live_core_sdk_data.pull_data.Flv", live_core_sdk_data_pull_data_flv_list, force=True)

  """
  >> >> >> >> data.room.stream_url.live_core_sdk_data.pull_data.Hls
  """
  set_dict_attr(room, "$.stream_url.live_core_sdk_data.pull_data.Hls", live_core_sdk_data_pull_data_hls_list, force=True)

  set_dict_attr(room, "$.stream_url.live_core_sdk_data.pull_data.codec",             live_core_sdk_pull_data_tuple.get('codec', ''),             force=True)
  set_dict_attr(room, "$.stream_url.live_core_sdk_data.pull_data.compensatory_data", live_core_sdk_pull_data_tuple.get('compensatory_data', ''), force=True)

  """
  >> >> >> >> data.room.stream_url.live_core_sdk_data.pull_data.hls_data_unencrypted
  """
  set_dict_attr(room, "$.stream_url.live_core_sdk_data.pull_data.hls_data_unencrypted", json.loads(live_core_sdk_pull_data_tuple.get('hls_data_unencrypted', {})), force=True)
  set_dict_attr(room, "$.stream_url.live_core_sdk_data.pull_data.kind",                 live_core_sdk_pull_data_tuple.get('kind', 0),                  force=True)
  
  """
  >> >> >> >> data.room.stream_url.live_core_sdk_data.pull_data.options
  >> >> >> >> data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality
  """
  set_dict_attr(room, "$.stream_url.live_core_sdk_data.pull_data.options.default_quality.additional_content", live_core_sdk_pull_default_quality_tuple.get('additional_content', ''), force=True)
  set_dict_attr(room, "$.stream_url.live_core_sdk_data.pull_data.options.default_quality.disable",            live_core_sdk_pull_default_quality_tuple.get('disable', 0),             force=True)
  set_dict_attr(room, "$.stream_url.live_core_sdk_data.pull_data.options.default_quality.fps",                live_core_sdk_pull_default_quality_tuple.get('fps', 0),                 force=True)
  set_dict_attr(room, "$.stream_url.live_core_sdk_data.pull_data.options.default_quality.level",              live_core_sdk_pull_default_quality_tuple.get('level', 0),               force=True)
  set_dict_attr(room, "$.stream_url.live_core_sdk_data.pull_data.options.default_quality.name",               live_core_sdk_pull_default_quality_tuple.get('name', ''),               force=True)
  set_dict_attr(room, "$.stream_url.live_core_sdk_data.pull_data.options.default_quality.resolution",         live_core_sdk_pull_default_quality_tuple.get('resolution', ''),         force=True)
  set_dict_attr(room, "$.stream_url.live_core_sdk_data.pull_data.options.default_quality.sdk_key",            live_core_sdk_pull_default_quality_tuple.get('sdk_key', ''),            force=True)
  set_dict_attr(room, "$.stream_url.live_core_sdk_data.pull_data.options.default_quality.v_bit_rate",         live_core_sdk_pull_default_quality_tuple.get('v_bit_rate', 0),          force=True)
  set_dict_attr(room, "$.stream_url.live_core_sdk_data.pull_data.options.default_quality.v_codec",            live_core_sdk_pull_default_quality_tuple.get('v_codec', ''),            force=True)

  """
  >> >> >> >> data.room.stream_url.live_core_sdk_data.pull_data.options.qualities
  """
  set_dict_attr(room, "$.stream_url.live_core_sdk_data.pull_data.options.qualities",     live_core_sdk_pull_quality_list, force=True)

  set_dict_attr(room, "$.stream_url.live_core_sdk_data.pull_data.options.vpass_default", bool(live_core_sdk_pull_data_options_tuple.get('vpass_default', False)), force=True)

  set_dict_attr(room, "$.stream_url.live_core_sdk_data.pull_data.stream_data",           live_core_sdk_pull_data_tuple.get('stream_data', ''),    force=True)
  set_dict_attr(room, "$.stream_url.live_core_sdk_data.pull_data.version",               int(live_core_sdk_pull_data_tuple.get('version', 0)), force=True)

  set_dict_attr(room, "$.stream_url.live_core_sdk_data.size",                            live_core_sdk_data_tuple.get('size', ''),                       force=True)

  set_dict_attr(room, "$.stream_url.provider",                                                 live_stream_tuple.get('stream_provider', 0), force=True)

  """
  >> >> >> >> data.room.stream_url.pull_datas
  """
  set_dict_attr(room, "$.stream_url.pull_datas",            room_record_tuple.get('pull_datas', {}),                        force=True)

  """
  >> >> >> >> data.room.stream_url.push_datas
  """
  set_dict_attr(room, "$.stream_url.push_datas",       room_record_tuple.get('push_datas', {}),      force=True)
  set_dict_attr(room, "$.stream_url.push_stream_type", room_record_tuple.get('push_stream_type', 0), force=True)

  """
  >> >> >> >> data.room.stream_url.push_urls
  """
  set_dict_attr(room, "$.stream_url.push_urls",   stream_url_push_urls_list,                     force=True)

  """
  >> >> >> >> data.room.stream_url.resolution_name
  """
  set_dict_attr(room, "$.stream_url.resolution_name",        json.loads(live_stream_tuple.get('resolution_name', {})),                force=True)

  set_dict_attr(room, "$.stream_url.rtmp_pull_url",          live_stream_tuple.get('rtmp_pull_url', ''),         force=True)
  set_dict_attr(room, "$.stream_url.rtmp_pull_url_params",   json.loads(live_stream_tuple.get('rtmp_pull_url_params', {})),  force=True)
  set_dict_attr(room, "$.stream_url.rtmp_push_url",          live_stream_tuple.get('rtmp_push_url', ''),         force=True)
  set_dict_attr(room, "$.stream_url.rtmp_push_url_params",   live_stream_tuple.get('rtmp_push_url_params', ''),  force=True)
  set_dict_attr(room, "$.stream_url.stream_control_type",    live_stream_tuple.get('stream_control_type', 0),    force=True)
  set_dict_attr(room, "$.stream_url.stream_orientation",     live_stream_tuple.get('stream_orientation', 0),     force=True)
  set_dict_attr(room, "$.stream_url.vr_type",                live_stream_tuple.get('vr_type', 0),                force=True)

  set_dict_attr(room, "$.sun_daily_icon_content",            room_record_tuple.get('sun_daily_icon_content', 0), force=True)

  """
  >> >> >> data.room.tags
  """
  set_dict_attr(room, "$.tags",                              room_tag_list,                                      force=True)
  
  set_dict_attr(room, "$.title",                         room_attribute_tuple.get('title', ''),                        force=True)
  set_dict_attr(room, "$.title_recommend",               bool(room_attribute_tuple.get('title_recommend', False)),           force=True)

  """
  >> >> >> data.room.top_fans
  """
  set_dict_attr(room, "$.top_fans",                      room_top_fans,                                                force=True)

  set_dict_attr(room, "$.toutiao_cover_recommend_level", room_attribute_tuple.get('toutiao_cover_recommend_level', 0), force=True)
  set_dict_attr(room, "$.toutiao_title_recommend_level", room_attribute_tuple.get('toutiao_title_recommend_level', 0), force=True)
  
  """
  >> >> >> data.room.upper_right_widget_data_list
  """
  set_dict_attr(room, "$.upper_right_widget_data_list",  room_upper_right_widget_data_list,                            force=True)
  
  set_dict_attr(room, "$.use_filter",                    bool(room_attribute_tuple.get('use_filter', False)),                force=True)
  set_dict_attr(room, "$.user_count",                    room_attribute_tuple.get('user_count', 0),                    force=True)
  set_dict_attr(room, "$.user_share_text",               room_record_tuple.get('user_share_text', ''),                 force=True)
  set_dict_attr(room, "$.vertical_cover_uri",            room_attribute_tuple.get('vertical_cover_uri', ''),           force=True)
  set_dict_attr(room, "$.vid",                           room_attribute_tuple.get('vid', ''),                          force=True)
  set_dict_attr(room, "$.video_feed_tag",                room_attribute_tuple.get('video_feed_tag', ''),               force=True)
  set_dict_attr(room, "$.visibility_range",              room_attribute_tuple.get('visibility_range', 0),              force=True)
  set_dict_attr(room, "$.vs_main_replay_id",             int(room_attribute_tuple.get('vs_main_replay_id', 0)),             force=True)

  """
  >> >> >> data.room.vs_roles
  """
  set_dict_attr(room, "$.vs_roles",                      room_vs_roles,                                                force=True)

  set_dict_attr(room, "$.wait_copy",                     room_attribute_tuple.get('wait_copy', ''),                    force=True)
  set_dict_attr(room, "$.web_count",                     room_record_tuple.get('web_count', 0),                        force=True)
  set_dict_attr(room, "$.webcast_comment_tcs",           room_record_tuple.get('webcast_comment_tcs', 0),              force=True)
  set_dict_attr(room, "$.webcast_sdk_version",           int(room_attribute_tuple.get('webcast_sdk_version', 0)),           force=True)
  set_dict_attr(room, "$.with_aggregate_column",         bool(room_record_tuple.get('with_aggregate_column', False)),        force=True)
  set_dict_attr(room, "$.with_draw_something",           bool(room_record_tuple.get('with_draw_something', False)),          force=True)
  set_dict_attr(room, "$.with_ktv",                      bool(room_record_tuple.get('with_ktv', False)),                     force=True)
  set_dict_attr(room, "$.with_linkmic",                  bool(room_record_tuple.get('with_linkmic', False)),                 force=True)

  ##
  ## set data.room
  ##
  set_dict_attr(data, "$.data.room", room, force=True)

  """
  >> >> data.user
  """
  set_dict_attr(data, "$.data.user.id",                                       int(user_record_tuple.get('id', 0)),                                           force=True)
  set_dict_attr(data, "$.data.user.adversary_authorization_info",             user_record_tuple.get('adversary_authorization_info', 0),                 force=True)
  set_dict_attr(data, "$.data.user.adversary_user_status",                    user_record_tuple.get('adversary_user_status', 0),                        force=True)
  set_dict_attr(data, "$.data.user.age_range",                                user_record_tuple.get('age_range', 0),                                    force=True)
  set_dict_attr(data, "$.data.user.allow_be_located",                         bool(user_record_tuple.get('allow_be_located', False)),                         force=True)
  set_dict_attr(data, "$.data.user.allow_find_by_contacts",                   bool(user_record_tuple.get('allow_find_by_contacts', False)),                   force=True)
  set_dict_attr(data, "$.data.user.allow_others_download_video",              bool(user_record_tuple.get('allow_others_download_video', False)),              force=True)
  set_dict_attr(data, "$.data.user.allow_others_download_when_sharing_video", bool(user_record_tuple.get('allow_others_download_when_sharing_video', False)), force=True)
  set_dict_attr(data, "$.data.user.allow_share_show_profile",                 bool(user_record_tuple.get('allow_share_show_profile', False)),                 force=True)
  set_dict_attr(data, "$.data.user.allow_show_in_gossip",                     bool(user_record_tuple.get('allow_show_in_gossip', False)),                     force=True)
  set_dict_attr(data, "$.data.user.allow_show_my_action",                     bool(user_record_tuple.get('allow_show_my_action', False)),                     force=True)
  set_dict_attr(data, "$.data.user.allow_strange_comment",                    bool(user_record_tuple.get('allow_strange_comment', False)),                    force=True)
  set_dict_attr(data, "$.data.user.allow_unfollower_comment",                 bool(user_record_tuple.get('allow_unfollower_comment', False)),                 force=True)
  set_dict_attr(data, "$.data.user.allow_use_linkmic",                        bool(user_record_tuple.get('allow_use_linkmic', False)),                        force=True)
  set_dict_attr(data, "$.data.user.authorization_info",                       user_record_tuple.get('authorization_info', 0),                           force=True)

  """
  >> >> >> data.user.badge_image_list
  """
  set_dict_attr(data, "$.data.user.badge_image_list",                         user_badge_image_list,                                    force=True)

  """
  >> >> >> data.user.badge_image_list_v2
  """
  set_dict_attr(data, "$.data.user.badge_image_list_v2",                      user_badge_image_list_v2,                                 force=True)

  if user_record_tuple.get('bg_img_url', '') is None:
    set_dict_attr(data, "$.data.user.bg_img_url",                               '',                  force=True)
  else:
    set_dict_attr(data, "$.data.user.bg_img_url",                               user_record_tuple.get('bg_img_url', ''),                  force=True)
  if user_record_tuple.get('birthday', 0) is None:
    set_dict_attr(data, "$.data.user.birthday",                                 0,                     force=True)
  else:
    set_dict_attr(data, "$.data.user.birthday",                                 user_record_tuple.get('birthday', 0),                     force=True)
  set_dict_attr(data, "$.data.user.birthday_description",                     user_record_tuple.get('birthday_description', ''),        force=True)
  set_dict_attr(data, "$.data.user.birthday_valid",                           bool(user_record_tuple.get('birthday_valid', False)),           force=True)
  set_dict_attr(data, "$.data.user.block_status",                             user_record_tuple.get('block_status', 0),                 force=True)
  set_dict_attr(data, "$.data.user.city",                                     user_record_tuple.get('city', ''),                        force=True)
  set_dict_attr(data, "$.data.user.comment_restrict",                         user_record_tuple.get('comment_restrict', 0),             force=True)

  """
  >> >> >> data.user.commerce_webcast_config_ids
  """
  set_dict_attr(data, "$.data.user.commerce_webcast_config_ids",              user_commerce_webcast_config_ids,                         force=True)
  
  set_dict_attr(data, "$.data.user.constellation",                            user_record_tuple.get('constellation', ''),               force=True)
  set_dict_attr(data, "$.data.user.consume_diamond_level",                    user_record_tuple.get('consume_diamond_level', 0),        force=True)
  if user_record_tuple.get('create_time', 0) is None:
    set_dict_attr(data, "$.data.user.create_time",                              0,                  force=True)
  else:
    set_dict_attr(data, "$.data.user.create_time",                              user_record_tuple.get('create_time', 0),                  force=True)
  set_dict_attr(data, "$.data.user.desensitized_nickname",                    user_record_tuple.get('desensitized_nickname', ''),       force=True)
  set_dict_attr(data, "$.data.user.disable_ichat",                            user_record_tuple.get('disable_ichat', 0),                force=True)
  set_dict_attr(data, "$.data.user.display_id",                               user_record_tuple.get('display_id', ''),                  force=True)
  set_dict_attr(data, "$.data.user.enable_ichat_img",                         user_record_tuple.get('enable_ichat_img', 0),             force=True)
  set_dict_attr(data, "$.data.user.exp",                                      user_owner_tuple.get('exp', 0),                           force=True)
  set_dict_attr(data, "$.data.user.experience",                               user_owner_tuple.get('experience', 0),                    force=True)
  set_dict_attr(data, "$.data.user.fan_ticket_count",                         user_owner_tuple.get('fan_ticket_count', 0),              force=True)
  set_dict_attr(data, "$.data.user.fold_stranger_chat",                       user_record_tuple.get('fold_stranger_chat', ''),          force=True)
  set_dict_attr(data, "$.data.user.follow_status",                            user_owner_tuple.get('follow_status', 0),                 force=True)
  set_dict_attr(data, "$.data.user.gender",                                   user_record_tuple.get('gender', 0),                       force=True)
  set_dict_attr(data, "$.data.user.hotsoon_verified",                         bool(user_record_tuple.get('hotsoon_verified', False)),         force=True)
  set_dict_attr(data, "$.data.user.hotsoon_verified_reason",                  user_record_tuple.get('hotsoon_verified_reason', ''),     force=True)
  set_dict_attr(data, "$.data.user.ichat_restrict_type",                      user_record_tuple.get('ichat_restrict_type', 0),          force=True)
  set_dict_attr(data, "$.data.user.id",                                       user_owner_tuple.get('id', 0),                            force=True)
  if user_owner_tuple.get('id', 0) == 0:
    set_dict_attr(data, "$.data.user.id_str",                                 '',                                                       force=True)
  else:
    set_dict_attr(data, "$.data.user.id_str",                                 str(user_owner_tuple.get('id', 0)),                       force=True)
  set_dict_attr(data, "$.data.user.income_share_percent",                     user_record_tuple.get('income_share_percent', 0),         force=True)
  set_dict_attr(data, "$.data.user.is_anonymous",                             bool(user_owner_tuple.get('is_anonymous', False)),              force=True)
  set_dict_attr(data, "$.data.user.is_follower",                              bool(user_owner_tuple.get('is_follower', False)),               force=True)
  set_dict_attr(data, "$.data.user.is_following",                             bool(user_owner_tuple.get('is_following', False)),              force=True)
  set_dict_attr(data, "$.data.user.level",                                    user_owner_tuple.get('level', 0),                     force=True)
  set_dict_attr(data, "$.data.user.link_mic_stats",                           user_owner_tuple.get('link_mic_stats', 0),            force=True)
  
  if user_owner_tuple.get('location_city', '') is None:
    set_dict_attr(data, "$.data.user.location_city",                            '',             force=True)
  else:
    set_dict_attr(data, "$.data.user.location_city",                            str(user_owner_tuple.get('location_city', '')),             force=True)

  """
  >> >> >> data.user.media_badge_image_list
  """
  set_dict_attr(data, "$.data.user.media_badge_image_list",                   user_media_badge_image_list,                              force=True)

  if user_owner_tuple.get('modify_time', 0) is None:
    set_dict_attr(data, "$.data.user.modify_time",                              0,               force=True)
  else:
    set_dict_attr(data, "$.data.user.modify_time",                              user_owner_tuple.get('modify_time', 0),               force=True)
  
  if user_owner_tuple.get('mystery_man', 0) is None:
    set_dict_attr(data, "$.data.user.mystery_man",                              0,               force=True)
  else:
    set_dict_attr(data, "$.data.user.mystery_man",                              user_owner_tuple.get('mystery_man', 0),               force=True)
  set_dict_attr(data, "$.data.user.need_profile_guide",                       bool(user_owner_tuple.get('need_profile_guide', False)),        force=True)

  """
  >> >> >> data.user.new_real_time_icons
  """
  set_dict_attr(data, "$.data.user.new_real_time_icons",                      user_new_real_time_icons,                               force=True)

  set_dict_attr(data, "$.data.user.nickname",                                 user_record_tuple.get('nickname', ''),                  force=True)
  set_dict_attr(data, "$.data.user.pay_score",                                user_record_tuple.get('pay_score', 0),                  force=True)
  set_dict_attr(data, "$.data.user.pay_scores",                               user_record_tuple.get('pay_scores', 0),                 force=True)
  set_dict_attr(data, "$.data.user.public_area_oper_freq",                    user_owner_tuple.get('public_area_oper_freq', 0),       force=True)
  set_dict_attr(data, "$.data.user.push_comment_status",                      bool(user_record_tuple.get('push_comment_status', False)),    force=True)
  set_dict_attr(data, "$.data.user.push_digg",                                bool(user_record_tuple.get('push_digg', False)),              force=True)
  set_dict_attr(data, "$.data.user.push_follow",                              bool(user_record_tuple.get('push_follow', False)),            force=True)
  set_dict_attr(data, "$.data.user.push_friend_action",                       bool(user_record_tuple.get('push_friend_action', False)),     force=True)
  set_dict_attr(data, "$.data.user.push_ichat",                               bool(user_record_tuple.get('push_ichat', False)),             force=True)
  set_dict_attr(data, "$.data.user.push_status",                              bool(user_record_tuple.get('push_status', False)),            force=True)
  set_dict_attr(data, "$.data.user.push_video_post",                          bool(user_record_tuple.get('push_video_post', False)),        force=True)
  set_dict_attr(data, "$.data.user.push_video_recommend",                     bool(user_record_tuple.get('push_video_recommend', False)),   force=True)

  """
  >> >> >> data.user.real_time_icons
  """
  set_dict_attr(data, "$.data.user.real_time_icons",                          user_real_time_icons,                            force=True)

  set_dict_attr(data, "$.data.user.remark_name",                              user_record_tuple.get('remark_name', ''),        force=True)
  set_dict_attr(data, "$.data.user.sec_uid",                                  user_record_tuple.get('sec_uid', ''),            force=True)
  set_dict_attr(data, "$.data.user.secret",                                   user_record_tuple.get('secret', 0),              force=True)
  set_dict_attr(data, "$.data.user.share_qrcode_uri",                         user_record_tuple.get('share_qrcode_uri', ''),   force=True)
  set_dict_attr(data, "$.data.user.short_id",                                 user_record_tuple.get('short_id', 0),            force=True)
  set_dict_attr(data, "$.data.user.signature",                                user_record_tuple.get('signature', ''),          force=True)
  set_dict_attr(data, "$.data.user.special_id",                               user_record_tuple.get('special_id', ''),         force=True)
  set_dict_attr(data, "$.data.user.status",                                   user_record_tuple.get('status', 0),              force=True)
  set_dict_attr(data, "$.data.user.telephone",                                user_record_tuple.get('telephone', ''),          force=True)
  set_dict_attr(data, "$.data.user.ticket_count",                             user_owner_tuple.get('ticket_count', 0),         force=True)

  """
  >> >> >> data.user.top_fans
  """
  set_dict_attr(data, "$.data.user.top_fans",                                 user_top_fans,                                   force=True)

  set_dict_attr(data, "$.data.user.top_vip_no",                               user_owner_tuple.get('top_vip_no', 0),                          force=True)
  set_dict_attr(data, "$.data.user.total_recharge_diamond_count",             user_record_tuple.get('total_recharge_diamond_count', 0),       force=True)
  set_dict_attr(data, "$.data.user.user_canceled",                            bool(user_record_tuple.get('user_canceled', False)),                  force=True)
  set_dict_attr(data, "$.data.user.user_open_id",                             user_record_tuple.get('user_open_id', ''),                      force=True)
  set_dict_attr(data, "$.data.user.user_role",                                user_record_tuple.get('user_role', 0),                          force=True)
  set_dict_attr(data, "$.data.user.verified",                                 bool(user_record_tuple.get('verified', False)),                       force=True)
  set_dict_attr(data, "$.data.user.verified_content",                         user_record_tuple.get('verified_content', ''),                  force=True)
  set_dict_attr(data, "$.data.user.verified_mobile",                          bool(user_record_tuple.get('verified_mobile', False)),                force=True)
  set_dict_attr(data, "$.data.user.verified_reason",                          user_record_tuple.get('verified_reason', ''),                   force=True)
  set_dict_attr(data, "$.data.user.watch_duration_month",                     user_record_tuple.get('watch_duration_month', 0),               force=True)
  set_dict_attr(data, "$.data.user.web_rid",                                  user_record_tuple.get('web_rid', ''),                           force=True)
  set_dict_attr(data, "$.data.user.webcast_uid",                              user_record_tuple.get('webcast_uid', ''),                       force=True)
  set_dict_attr(data, "$.data.user.with_car_management_permission",           bool(user_record_tuple.get('with_car_management_permission', False)), force=True)
  set_dict_attr(data, "$.data.user.with_commerce_permission",                 bool(user_record_tuple.get('with_commerce_permission', False)),       force=True)
  set_dict_attr(data, "$.data.user.with_fusion_shop_entry",                   bool(user_record_tuple.get('with_fusion_shop_entry', False)),         force=True)

  """
  >>  extra
  """
  set_dict_attr(data,  "$.extra.now",                               floor(now.timestamp() * 1000),          force=True)

  """
  >> status_code
  """
  set_dict_attr(data,  "$.status_code",                             status_code,  force=True)
  
  if output_path is not None:
    save_dict_as_file(data, Path(output_path))