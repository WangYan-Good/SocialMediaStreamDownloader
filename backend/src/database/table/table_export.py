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
from backend.src.library.loglib                                       import   get_logger
from backend.src.database.social_media_stream_database                import   SocialMediaStreamDataBase
from backend.src.database.table.live                                  import   LiveRecordTable
from backend.src.database.table.room_base                             import   RoomBaseTable
from backend.src.database.table.room                                  import   RoomAdminUserIdTable,                                \
                                                                               RoomAdminUserOpenIdTable,                            \
                                                                               RoomStatsTable,                                      \
                                                                               RoomDecoTable,                                       \
                                                                               FansGroupAdminUserIdTable,                           \
                                                                               FansGroupAdminUserOpenIdTable
from backend.src.database.table.room_owner                            import   RoomOwnerV2Table
from backend.src.database.table.user                                  import   UserTable
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
## sort export fields by key, for better readability and consistency.
##
def _sort_export_fields(source):
  if isinstance(source, dict):
    target = dict()
    for key in sorted(source.keys()):
      target[key] = _sort_export_fields(source[key])
    return target

  if isinstance(source, list):
    return [_sort_export_fields(item) for item in source]

  return source

##
## normalize export data types, for better readability and consistency.
##
def _normalize_export_types(source:dict) -> dict:
  template = initialize_export_data()

  def _coerce(value, model):
    if isinstance(model, dict):
      target = dict(value) if isinstance(value, dict) else dict()
      for key, sub_model in model.items():
        target[key] = _coerce(target.get(key), sub_model)
      return target

    if isinstance(model, list):
      if value is None:
        return []
      return value if isinstance(value, list) else value

    if isinstance(model, bool):
      if isinstance(value, bool):
        return value
      if isinstance(value, int):
        return bool(value)
      if isinstance(value, str):
        raw = value.strip().lower()
        if raw in ("1", "true", "yes", "on"):
          return True
        if raw in ("0", "false", "no", "off", ""):
          return False
      return model if value is None else bool(value)

    if isinstance(model, int):
      if value is None:
        return 0
      if isinstance(value, bool):
        return int(value)
      if isinstance(value, int):
        return value
      if isinstance(value, float):
        return int(value)
      if isinstance(value, str):
        raw = value.strip()
        if len(raw) == 0:
          return 0
        try:
          return int(raw)
        except Exception:
          return value
      return value

    if isinstance(model, str):
      if value is None:
        return ""
      return str(value)

    return model if value is None else value

  return _coerce(source, template)

##
## export a living data from social media stream downloader database to yml file.
## identifier: primary key of live_record table
##
def export_live_data(db:SocialMediaStreamDataBase, identifier:dict = None, output_path:str = None) :
  ##
  ## check living record key field
  ##  
  if identifier is None:
    raise ValueError("identifier is required")

  data = dict()
  try:
    now_id        = get_dict_attr(identifier, "$.now")
    platform      = get_dict_attr(identifier, "$.platform")
    room_id       = get_dict_attr(identifier, "$.room_id")
    owner_user_id = get_dict_attr(identifier, "$.owner_user_id")
    user_id       = get_dict_attr(identifier, "$.user_id")
    start_time_id = get_dict_attr(identifier, "$.start_time")
    finish_time   = get_dict_attr(identifier, "$.finish_time")
    status_code   = get_dict_attr(identifier, "$.status_code")
  except Exception as e:
    raise ValueError(f"invalid identifier, error: {e}")

  def _to_int_or_none(value):
    if value is None:
      return None
    if isinstance(value, bool):
      return None
    if isinstance(value, int):
      return value
    if isinstance(value, float):
      return int(value)
    if isinstance(value, str):
      raw = value.strip()
      if len(raw) == 0:
        return None
      try:
        return int(raw)
      except Exception:
        return None
    return None

  def _to_datetime_or_none(seconds_or_millis):
    value = _to_int_or_none(seconds_or_millis)
    if value is None:
      return None
    if abs(value) > 10_000_000_000:
      value = value / 1000.0
    return dat.fromtimestamp(value)

  ##
  ## live_record
  ##
  live_record       = LiveRecordTable(db)
  live_record_tuple = {key: None for key in live_record.get_tuple()}
  set_dict_attr(live_record_tuple, "$.platform",      "douyin",                                                  force=True)
  set_dict_attr(live_record_tuple, "$.owner_user_id", str(owner_user_id) if owner_user_id is not None else None, force=True)
  set_dict_attr(live_record_tuple, "$.room_id",       str(room_id) if room_id is not None else None,             force=True)
  now_id_dt = _to_datetime_or_none(now_id)
  if now_id_dt is not None:
    set_dict_attr(live_record_tuple, "$.now", now_id_dt, force=True)
  
  try:
    record_list = live_record.get_record(live_record_tuple, fetchall=True)
    if record_list is None or len(record_list) == 0:
      raise ValueError("live_record not found")

    start_time_id_dt = _to_datetime_or_none(start_time_id)
    if start_time_id_dt is not None:
      matched = [item for item in record_list if get_dict_attr(item, "$.start_time") == start_time_id_dt]
      if len(matched) != 0:
        record_list = matched

    record_list = sorted(record_list, key=lambda item: get_dict_attr(item, "$.now") or dat.min)
    live_record_tuple = record_list[-1]
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

  try:
    status_code = get_dict_attr(live_record_tuple, "$.status_code")
  except Exception as e:
    get_logger().error(f"{e}: {live_record.get_name()} >> status_code")
    status_code = 0

  def _parse_json_field(value):
    if isinstance(value, str) is False:
      return value
    value = value.strip()
    if len(value) == 0:
      return value
    try:
      return json.loads(value)
    except Exception:
      return value

  ##
  ## room_base
  ##
  room_base = RoomBaseTable(db)
  room_base_tuple = {key: None for key in room_base.get_tuple()}
  if now not in (None, 0):
    set_dict_attr(room_base_tuple, "$.now", now, force=True)
  set_dict_attr(room_base_tuple, "$.id", str(room_id) if room_id is not None else None, force=True)
  start_time_query = start_time
  if hasattr(start_time_query, "timestamp"):
    start_time_query = int(start_time_query.timestamp())
  else:
    start_time_query = _to_int_or_none(start_time_query)
  if start_time_query is None:
    start_time_query = _to_int_or_none(start_time_id)
  if start_time_query is not None:
    set_dict_attr(room_base_tuple, "$.start_time", start_time_query, force=True)
  try:
    room_base_record_list = room_base.get_record(room_base_tuple, fetchall=True)
    if room_base_record_list is None or len(room_base_record_list) == 0:
      raise ValueError("room_base not found")
    room_base_record_list = sorted(room_base_record_list, key=lambda item: get_dict_attr(item, "$.start_time") or 0)
    room_base_tuple = room_base_record_list[-1]
  except Exception as e:
    get_logger().error(f"{e}: {room_base.get_name()} >> data")

  """
  >> data.room
  """
  set_dict_attr(data, "$.room.AnchorABMap",                     _parse_json_field(get_dict_attr(room_base_tuple, "$.AnchorABMap")),                    force=True)
  set_dict_attr(data, "$.room.acquaintance_status",             get_dict_attr(room_base_tuple, "$.acquaintance_status"),                                force=True)
  set_dict_attr(data, "$.room.admin_user_ids",                  _parse_json_field(get_dict_attr(room_base_tuple, "$.admin_user_ids")),                 force=True)
  set_dict_attr(data, "$.room.admin_user_open_ids",             _parse_json_field(get_dict_attr(room_base_tuple, "$.admin_user_open_ids")),            force=True)
  set_dict_attr(data, "$.room.anchor_scheduled_time_text",      get_dict_attr(room_base_tuple, "$.anchor_scheduled_time_text"),                         force=True)
  set_dict_attr(data, "$.room.anchor_share_text",               get_dict_attr(room_base_tuple, "$.anchor_share_text"),                                  force=True)
  set_dict_attr(data, "$.room.anchor_tab_type",                 get_dict_attr(room_base_tuple, "$.anchor_tab_type"),                                    force=True)
  set_dict_attr(data, "$.room.app_id",                          get_dict_attr(room_base_tuple, "$.app_id"),                                             force=True)
  set_dict_attr(data, "$.room.assist_label_list",               _parse_json_field(get_dict_attr(room_base_tuple, "$.assist_label_list")),              force=True)
  set_dict_attr(data, "$.room.auth_city",                       get_dict_attr(room_base_tuple, "$.auth_city"),                                          force=True)
  set_dict_attr(data, "$.room.auto_cover",                      get_dict_attr(room_base_tuple, "$.auto_cover"),                                         force=True)
  set_dict_attr(data, "$.room.base_category",                   get_dict_attr(room_base_tuple, "$.base_category"),                                      force=True)
  set_dict_attr(data, "$.room.book_end_time",                   get_dict_attr(room_base_tuple, "$.book_end_time"),                                      force=True)
  set_dict_attr(data, "$.room.book_time",                       get_dict_attr(room_base_tuple, "$.book_time"),                                          force=True)
  set_dict_attr(data, "$.room.business_live",                   get_dict_attr(room_base_tuple, "$.business_live"),                                      force=True)
  set_dict_attr(data, "$.room.category",                        get_dict_attr(room_base_tuple, "$.category"),                                           force=True)
  set_dict_attr(data, "$.room.cell_style",                      get_dict_attr(room_base_tuple, "$.cell_style"),                                         force=True)
  set_dict_attr(data, "$.room.challenge_info",                  get_dict_attr(room_base_tuple, "$.challenge_info"),                                     force=True)
  set_dict_attr(data, "$.room.city_top_distance",               get_dict_attr(room_base_tuple, "$.city_top_distance"),                                  force=True)
  set_dict_attr(data, "$.room.client_version",                  get_dict_attr(room_base_tuple, "$.client_version"),                                     force=True)
  set_dict_attr(data, "$.room.comment_box",                     _parse_json_field(get_dict_attr(room_base_tuple, "$.comment_box")),                    force=True)
  set_dict_attr(data, "$.room.comment_name_mode",               get_dict_attr(room_base_tuple, "$.comment_name_mode"),                                  force=True)
  set_dict_attr(data, "$.room.common_label_list",               get_dict_attr(room_base_tuple, "$.common_label_list"),                                  force=True)
  set_dict_attr(data, "$.room.content_tag",                     get_dict_attr(room_base_tuple, "$.content_tag"),                                        force=True)
  set_dict_attr(data, "$.room.cover",                           _parse_json_field(get_dict_attr(room_base_tuple, "$.cover")),                          force=True)
  set_dict_attr(data, "$.room.create_time",                     get_dict_attr(room_base_tuple, "$.create_time"),                                        force=True)
  set_dict_attr(data, "$.room.danmaku_detail",                  get_dict_attr(room_base_tuple, "$.danmaku_detail"),                                     force=True)
  set_dict_attr(data, "$.room.deco_list",                       _parse_json_field(get_dict_attr(room_base_tuple, "$.deco_list")),                       force=True)
  set_dict_attr(data, "$.room.distance",                        get_dict_attr(room_base_tuple, "$.distance"),                                           force=True)
  set_dict_attr(data, "$.room.distance_city",                   get_dict_attr(room_base_tuple, "$.distance_city"),                                      force=True)
  set_dict_attr(data, "$.room.distance_km",                     get_dict_attr(room_base_tuple, "$.distance_km"),                                        force=True)
  set_dict_attr(data, "$.room.dynamic_cover_dict",              _parse_json_field(get_dict_attr(room_base_tuple, "$.dynamic_cover_dict")),             force=True)
  set_dict_attr(data, "$.room.dynamic_cover_uri",               get_dict_attr(room_base_tuple, "$.dynamic_cover_uri"),                                  force=True)
  set_dict_attr(data, "$.room.enable_room_perspective",         get_dict_attr(room_base_tuple, "$.enable_room_perspective"),                           force=True)
  set_dict_attr(data, "$.room.extra",                           _parse_json_field(get_dict_attr(room_base_tuple, "$.extra")),                          force=True)
  set_dict_attr(data, "$.room.fans_group_admin_user_ids",       _parse_json_field(get_dict_attr(room_base_tuple, "$.fans_group_admin_user_ids")),      force=True)
  set_dict_attr(data, "$.room.fans_group_admin_user_open_ids",  _parse_json_field(get_dict_attr(room_base_tuple, "$.fans_group_admin_user_open_ids")), force=True)
  set_dict_attr(data, "$.room.fansclub_msg_style",              get_dict_attr(room_base_tuple, "$.fansclub_msg_style"),                                 force=True)
  set_dict_attr(data, "$.room.fcdn_appid",                      get_dict_attr(room_base_tuple, "$.fcdn_appid"),                                         force=True)
  set_dict_attr(data, "$.room.feed_room_label",                 _parse_json_field(get_dict_attr(room_base_tuple, "$.feed_room_label")),                force=True)
  set_dict_attr(data, "$.room.filter_words",                    _parse_json_field(get_dict_attr(room_base_tuple, "$.filter_words")),                   force=True)
  set_dict_attr(data, "$.room.finish_reason",                   get_dict_attr(room_base_tuple, "$.finish_reason"),                                      force=True)
  set_dict_attr(data, "$.room.finish_time",                     get_dict_attr(room_base_tuple, "$.finish_time"),                                        force=True)
  set_dict_attr(data, "$.room.finish_url",                      get_dict_attr(room_base_tuple, "$.finish_url"),                                         force=True)
  set_dict_attr(data, "$.room.follow_msg_style",                get_dict_attr(room_base_tuple, "$.follow_msg_style"),                                   force=True)
  set_dict_attr(data, "$.room.forum_extra_data",                get_dict_attr(room_base_tuple, "$.forum_extra_data"),                                   force=True)
  set_dict_attr(data, "$.room.game_room_type",                  get_dict_attr(room_base_tuple, "$.game_room_type"),                                     force=True)
  set_dict_attr(data, "$.room.gift_msg_style",                  get_dict_attr(room_base_tuple, "$.gift_msg_style"),                                     force=True)
  set_dict_attr(data, "$.room.group_id",                        get_dict_attr(room_base_tuple, "$.group_id"),                                           force=True)
  set_dict_attr(data, "$.room.group_source",                    get_dict_attr(room_base_tuple, "$.group_source"),                                       force=True)
  set_dict_attr(data, "$.room.guide_button",                    _parse_json_field(get_dict_attr(room_base_tuple, "$.guide_button")),                   force=True)
  set_dict_attr(data, "$.room.has_commerce_goods",              get_dict_attr(room_base_tuple, "$.has_commerce_goods"),                                 force=True)
  set_dict_attr(data, "$.room.has_promotion_games",             get_dict_attr(room_base_tuple, "$.has_promotion_games"),                                force=True)
  set_dict_attr(data, "$.room.highlight",                       get_dict_attr(room_base_tuple, "$.highlight"),                                          force=True)
  set_dict_attr(data, "$.room.hot_sentence_info",               get_dict_attr(room_base_tuple, "$.hot_sentence_info"),                                  force=True)
  set_dict_attr(data, "$.room.id",                              get_dict_attr(room_base_tuple, "$.id"),                                                 force=True)
  set_dict_attr(data, "$.room.id_str",                          get_dict_attr(room_base_tuple, "$.id_str"),                                             force=True)
  set_dict_attr(data, "$.room.introduction",                    get_dict_attr(room_base_tuple, "$.introduction"),                                       force=True)
  set_dict_attr(data, "$.room.is_need_check_list",              get_dict_attr(room_base_tuple, "$.is_need_check_list"),                                 force=True)
  set_dict_attr(data, "$.room.is_official_channel_room",        get_dict_attr(room_base_tuple, "$.is_official_channel_room"),                           force=True)
  set_dict_attr(data, "$.room.is_replay",                       get_dict_attr(room_base_tuple, "$.is_replay"),                                          force=True)
  set_dict_attr(data, "$.room.is_show_inquiry_ball",            get_dict_attr(room_base_tuple, "$.is_show_inquiry_ball"),                               force=True)
  set_dict_attr(data, "$.room.is_show_user_card_switch",        get_dict_attr(room_base_tuple, "$.is_show_user_card_switch"),                           force=True)
  set_dict_attr(data, "$.room.item_explicit_info",              get_dict_attr(room_base_tuple, "$.item_explicit_info"),                                 force=True)
  set_dict_attr(data, "$.room.last_ping_time",                  get_dict_attr(room_base_tuple, "$.last_ping_time"),                                     force=True)
  set_dict_attr(data, "$.room.layout",                          get_dict_attr(room_base_tuple, "$.layout"),                                             force=True)
  set_dict_attr(data, "$.room.like_count",                      get_dict_attr(room_base_tuple, "$.like_count"),                                         force=True)
  set_dict_attr(data, "$.room.linker_map",                      _parse_json_field(get_dict_attr(room_base_tuple, "$.linker_map")),                     force=True)
  set_dict_attr(data, "$.room.linkmic_display_type",            get_dict_attr(room_base_tuple, "$.linkmic_display_type"),                               force=True)
  set_dict_attr(data, "$.room.linkmic_layout",                  get_dict_attr(room_base_tuple, "$.linkmic_layout"),                                     force=True)
  set_dict_attr(data, "$.room.live_distribution",               _parse_json_field(get_dict_attr(room_base_tuple, "$.live_distribution")),              force=True)
  set_dict_attr(data, "$.room.live_id",                         get_dict_attr(room_base_tuple, "$.live_id"),                                            force=True)
  set_dict_attr(data, "$.room.live_platform_source",            get_dict_attr(room_base_tuple, "$.live_platform_source"),                               force=True)
  set_dict_attr(data, "$.room.live_room_mode",                  get_dict_attr(room_base_tuple, "$.live_room_mode"),                                     force=True)
  set_dict_attr(data, "$.room.live_type_audio",                 get_dict_attr(room_base_tuple, "$.live_type_audio"),                                    force=True)
  set_dict_attr(data, "$.room.live_type_linkmic",               get_dict_attr(room_base_tuple, "$.live_type_linkmic"),                                  force=True)
  set_dict_attr(data, "$.room.live_type_normal",                get_dict_attr(room_base_tuple, "$.live_type_normal"),                                   force=True)
  set_dict_attr(data, "$.room.live_type_official",              get_dict_attr(room_base_tuple, "$.live_type_official"),                                 force=True)
  set_dict_attr(data, "$.room.live_type_sandbox",               get_dict_attr(room_base_tuple, "$.live_type_sandbox"),                                  force=True)
  set_dict_attr(data, "$.room.live_type_screenshot",            get_dict_attr(room_base_tuple, "$.live_type_screenshot"),                               force=True)
  set_dict_attr(data, "$.room.live_type_third_party",           get_dict_attr(room_base_tuple, "$.live_type_third_party"),                              force=True)
  set_dict_attr(data, "$.room.live_type_vs_live",               get_dict_attr(room_base_tuple, "$.live_type_vs_live"),                                  force=True)
  set_dict_attr(data, "$.room.live_type_vs_premiere",           get_dict_attr(room_base_tuple, "$.live_type_vs_premiere"),                              force=True)
  set_dict_attr(data, "$.room.living_room_attrs",               _parse_json_field(get_dict_attr(room_base_tuple, "$.living_room_attrs")),              force=True)
  set_dict_attr(data, "$.room.location",                        get_dict_attr(room_base_tuple, "$.location"),                                           force=True)
  set_dict_attr(data, "$.room.lottery_finish_time",             get_dict_attr(room_base_tuple, "$.lottery_finish_time"),                                force=True)
  set_dict_attr(data, "$.room.luckymoney_num",                  get_dict_attr(room_base_tuple, "$.luckymoney_num"),                                     force=True)
  set_dict_attr(data, "$.room.mosaic_status",                   get_dict_attr(room_base_tuple, "$.mosaic_status"),                                      force=True)
  set_dict_attr(data, "$.room.mosaic_tip",                      get_dict_attr(room_base_tuple, "$.mosaic_tip"),                                         force=True)
  set_dict_attr(data, "$.room.official_channel_open_id",        get_dict_attr(room_base_tuple, "$.official_channel_open_id"),                           force=True)
  set_dict_attr(data, "$.room.official_channel_uid",            get_dict_attr(room_base_tuple, "$.official_channel_uid"),                               force=True)
  set_dict_attr(data, "$.room.orientation",                     get_dict_attr(room_base_tuple, "$.orientation"),                                        force=True)
  set_dict_attr(data, "$.room.os_type",                         get_dict_attr(room_base_tuple, "$.os_type"),                                            force=True)
  set_dict_attr(data, "$.room.owner",                          _parse_json_field(get_dict_attr(room_base_tuple, "$.owner")),                          force=True)
  set_dict_attr(data, "$.room.owner_device_id",                get_dict_attr(room_base_tuple, "$.owner_device_id"),                                   force=True)
  set_dict_attr(data, "$.room.owner_open_id",                  get_dict_attr(room_base_tuple, "$.owner_open_id"),                                     force=True)
  set_dict_attr(data, "$.room.owner_user_id",                   get_dict_attr(room_base_tuple, "$.owner_user_id"),                                      force=True)
  set_dict_attr(data, "$.room.pack_meta",                      _parse_json_field(get_dict_attr(room_base_tuple, "$.pack_meta")),                      force=True)
  set_dict_attr(data, "$.room.paid_live_data",                 _parse_json_field(get_dict_attr(room_base_tuple, "$.paid_live_data")),                 force=True)
  set_dict_attr(data, "$.room.popularity",                     get_dict_attr(room_base_tuple, "$.popularity"),                                         force=True)
  set_dict_attr(data, "$.room.popularity_str",                 get_dict_attr(room_base_tuple, "$.popularity_str"),                                     force=True)
  set_dict_attr(data, "$.room.pre_enter_time",                 get_dict_attr(room_base_tuple, "$.pre_enter_time"),                                     force=True)
  set_dict_attr(data, "$.room.preview_copy",                   get_dict_attr(room_base_tuple, "$.preview_copy"),                                       force=True)
  set_dict_attr(data, "$.room.preview_flow_tag",               get_dict_attr(room_base_tuple, "$.preview_flow_tag"),                                   force=True)
  set_dict_attr(data, "$.room.private_info",                   get_dict_attr(room_base_tuple, "$.private_info"),                                       force=True)
  set_dict_attr(data, "$.room.ranklist_audience_type",         get_dict_attr(room_base_tuple, "$.ranklist_audience_type"),                             force=True)
  set_dict_attr(data, "$.room.real_distance",                  get_dict_attr(room_base_tuple, "$.real_distance"),                                      force=True)
  set_dict_attr(data, "$.room.redpacket_audience_auth",        get_dict_attr(room_base_tuple, "$.redpacket_audience_auth"),                            force=True)
  set_dict_attr(data, "$.room.relation_tag",                   get_dict_attr(room_base_tuple, "$.relation_tag"),                                       force=True)
  set_dict_attr(data, "$.room.replay",                         get_dict_attr(room_base_tuple, "$.replay"),                                             force=True)
  set_dict_attr(data, "$.room.replay_location",                get_dict_attr(room_base_tuple, "$.replay_location"),                                    force=True)
  set_dict_attr(data, "$.room.room_audit_status",              get_dict_attr(room_base_tuple, "$.room_audit_status"),                                  force=True)
  set_dict_attr(data, "$.room.room_auth",                      _parse_json_field(get_dict_attr(room_base_tuple, "$.room_auth")),                      force=True)
  set_dict_attr(data, "$.room.room_create_ab_param",           get_dict_attr(room_base_tuple, "$.room_create_ab_param"),                               force=True)
  set_dict_attr(data, "$.room.room_layout",                    get_dict_attr(room_base_tuple, "$.room_layout"),                                        force=True)
  set_dict_attr(data, "$.room.room_tabs",                       _parse_json_field(get_dict_attr(room_base_tuple, "$.room_tabs")),                      force=True)
  set_dict_attr(data, "$.room.room_tag",                        get_dict_attr(room_base_tuple, "$.room_tag"),                                           force=True)
  set_dict_attr(data, "$.room.room_view_stats",                 _parse_json_field(get_dict_attr(room_base_tuple, "$.room_view_stats")),                force=True)
  set_dict_attr(data, "$.room.stats",                           _parse_json_field(get_dict_attr(room_base_tuple, "$.stats")),                          force=True)
  set_dict_attr(data, "$.room.screen_capture_sharing_title",    get_dict_attr(room_base_tuple, "$.screen_capture_sharing_title"),                       force=True)
  set_dict_attr(data, "$.room.scroll_config",                   get_dict_attr(room_base_tuple, "$.scroll_config"),                                      force=True)
  set_dict_attr(data, "$.room.search_id",                       get_dict_attr(room_base_tuple, "$.search_id"),                                          force=True)
  set_dict_attr(data, "$.room.sell_goods",                      get_dict_attr(room_base_tuple, "$.sell_goods"),                                         force=True)
  set_dict_attr(data, "$.room.share_msg_style",                 get_dict_attr(room_base_tuple, "$.share_msg_style"),                                    force=True)
  set_dict_attr(data, "$.room.share_url",                       get_dict_attr(room_base_tuple, "$.share_url"),                                          force=True)
  set_dict_attr(data, "$.room.sharing_music_id_list",           _parse_json_field(get_dict_attr(room_base_tuple, "$.sharing_music_id_list")),          force=True)
  set_dict_attr(data, "$.room.short_title",                     get_dict_attr(room_base_tuple, "$.short_title"),                                        force=True)
  set_dict_attr(data, "$.room.short_touch_area_config",         _parse_json_field(get_dict_attr(room_base_tuple, "$.short_touch_area_config")),        force=True)
  set_dict_attr(data, "$.room.sofa_layout",                     get_dict_attr(room_base_tuple, "$.sofa_layout"),                                        force=True)
  set_dict_attr(data, "$.room.stamps",                          get_dict_attr(room_base_tuple, "$.stamps"),                                             force=True)
  set_dict_attr(data, "$.room.start_time",                      get_dict_attr(room_base_tuple, "$.start_time"),                                         force=True)
  set_dict_attr(data, "$.room.status",                          get_dict_attr(room_base_tuple, "$.status"),                                             force=True)
  set_dict_attr(data, "$.room.stream_close_time",               get_dict_attr(room_base_tuple, "$.stream_close_time"),                                  force=True)
  set_dict_attr(data, "$.room.stream_id",                       get_dict_attr(room_base_tuple, "$.stream_id"),                                          force=True)
  set_dict_attr(data, "$.room.stream_id_str",                   get_dict_attr(room_base_tuple, "$.stream_id_str"),                                      force=True)
  set_dict_attr(data, "$.room.stream_provider",                 get_dict_attr(room_base_tuple, "$.stream_provider"),                                    force=True)
  set_dict_attr(data, "$.room.stream_url",                      _parse_json_field(get_dict_attr(room_base_tuple, "$.stream_url")),                     force=True)
  set_dict_attr(data, "$.room.sun_daily_icon_content",          get_dict_attr(room_base_tuple, "$.sun_daily_icon_content"),                             force=True)
  set_dict_attr(data, "$.room.tags",                            _parse_json_field(get_dict_attr(room_base_tuple, "$.tags")),                           force=True)
  set_dict_attr(data, "$.room.title",                           get_dict_attr(room_base_tuple, "$.title"),                                              force=True)
  set_dict_attr(data, "$.room.title_recommend",                 get_dict_attr(room_base_tuple, "$.title_recommend"),                                    force=True)
  set_dict_attr(data, "$.room.top_fans",                        _parse_json_field(get_dict_attr(room_base_tuple, "$.top_fans")),                       force=True)
  set_dict_attr(data, "$.room.toutiao_cover_recommend_level",   get_dict_attr(room_base_tuple, "$.toutiao_cover_recommend_level"),                      force=True)
  set_dict_attr(data, "$.room.toutiao_title_recommend_level",   get_dict_attr(room_base_tuple, "$.toutiao_title_recommend_level"),                      force=True)
  set_dict_attr(data, "$.room.upper_right_widget_data_list",    _parse_json_field(get_dict_attr(room_base_tuple, "$.upper_right_widget_data_list")),   force=True)
  set_dict_attr(data, "$.room.use_filter",                      get_dict_attr(room_base_tuple, "$.use_filter"),                                         force=True)
  set_dict_attr(data, "$.room.user_count",                      get_dict_attr(room_base_tuple, "$.user_count"),                                         force=True)
  set_dict_attr(data, "$.room.user_share_text",                 get_dict_attr(room_base_tuple, "$.user_share_text"),                                    force=True)
  set_dict_attr(data, "$.room.vertical_cover_uri",              get_dict_attr(room_base_tuple, "$.vertical_cover_uri"),                                 force=True)
  set_dict_attr(data, "$.room.vid",                             get_dict_attr(room_base_tuple, "$.vid"),                                                force=True)
  set_dict_attr(data, "$.room.video_feed_tag",                  get_dict_attr(room_base_tuple, "$.video_feed_tag"),                                     force=True)
  set_dict_attr(data, "$.room.visibility_range",                get_dict_attr(room_base_tuple, "$.visibility_range"),                                   force=True)
  set_dict_attr(data, "$.room.vs_main_replay_id",               get_dict_attr(room_base_tuple, "$.vs_main_replay_id"),                                  force=True)
  set_dict_attr(data, "$.room.vs_roles",                        _parse_json_field(get_dict_attr(room_base_tuple, "$.vs_roles")),                       force=True)
  set_dict_attr(data, "$.room.wait_copy",                       get_dict_attr(room_base_tuple, "$.wait_copy"),                                          force=True)
  set_dict_attr(data, "$.room.web_count",                       get_dict_attr(room_base_tuple, "$.web_count"),                                          force=True)
  set_dict_attr(data, "$.room.webcast_comment_tcs",             get_dict_attr(room_base_tuple, "$.webcast_comment_tcs"),                                force=True)
  set_dict_attr(data, "$.room.webcast_sdk_version",             get_dict_attr(room_base_tuple, "$.webcast_sdk_version"),                                force=True)
  set_dict_attr(data, "$.room.with_aggregate_column",           get_dict_attr(room_base_tuple, "$.with_aggregate_column"),                              force=True)
  set_dict_attr(data, "$.room.with_draw_something",             get_dict_attr(room_base_tuple, "$.with_draw_something"),                                force=True)
  set_dict_attr(data, "$.room.with_ktv",                        get_dict_attr(room_base_tuple, "$.with_ktv"),                                           force=True)
  set_dict_attr(data, "$.room.with_linkmic",                    get_dict_attr(room_base_tuple, "$.with_linkmic"),                                       force=True)
  set_dict_attr(data, "$.room.content_label",                   _parse_json_field(get_dict_attr(room_base_tuple, "$.content_label")),                  force=True)
  set_dict_attr(data, "$.room.link_mic",                        _parse_json_field(get_dict_attr(room_base_tuple, "$.link_mic")),                       force=True)
  set_dict_attr(data, "$.room.official_channel",                _parse_json_field(get_dict_attr(room_base_tuple, "$.official_channel")),               force=True)

  ##
  ## user
  ##
  user_table = UserTable(db)
  user_table_tuple = {key: None for key in user_table.get_tuple()}
  set_dict_attr(user_table_tuple, "$.id", str(user_id) if user_id not in (None, 0, "") else (str(owner_user_id) if owner_user_id not in (None, 0, "") else None), force=True)
  try:
    user_table_tuple = user_table.get_record(user_table_tuple).pop()
  except Exception as e:
    get_logger().error(f"{e}: {user_table.get_name()} >> data.user")

  """
  >> data.user
  """
  set_dict_attr(data, "$.user.id",                                     get_dict_attr(user_table_tuple, "$.id"),                                     force=True)
  set_dict_attr(data, "$.user.id_str",                                 str(get_dict_attr(user_table_tuple, "$.id")) if get_dict_attr(user_table_tuple, "$.id") is not None else None, force=True)
  set_dict_attr(data, "$.user.adversary_authorization_info",           get_dict_attr(user_table_tuple, "$.adversary_authorization_info"),           force=True)
  set_dict_attr(data, "$.user.adversary_user_status",                  get_dict_attr(user_table_tuple, "$.adversary_user_status"),                  force=True)
  set_dict_attr(data, "$.user.age_range",                              get_dict_attr(user_table_tuple, "$.age_range"),                              force=True)
  set_dict_attr(data, "$.user.allow_be_located",                       get_dict_attr(user_table_tuple, "$.allow_be_located"),                       force=True)
  set_dict_attr(data, "$.user.allow_find_by_contacts",                 get_dict_attr(user_table_tuple, "$.allow_find_by_contacts"),                 force=True)
  set_dict_attr(data, "$.user.allow_others_download_video",            get_dict_attr(user_table_tuple, "$.allow_others_download_video"),            force=True)
  set_dict_attr(data, "$.user.allow_others_download_when_sharing_video", get_dict_attr(user_table_tuple, "$.allow_others_download_when_sharing_video"), force=True)
  set_dict_attr(data, "$.user.allow_share_show_profile",               get_dict_attr(user_table_tuple, "$.allow_share_show_profile"),               force=True)
  set_dict_attr(data, "$.user.allow_show_in_gossip",                   get_dict_attr(user_table_tuple, "$.allow_show_in_gossip"),                   force=True)
  set_dict_attr(data, "$.user.allow_show_my_action",                   get_dict_attr(user_table_tuple, "$.allow_show_my_action"),                   force=True)
  set_dict_attr(data, "$.user.allow_strange_comment",                  get_dict_attr(user_table_tuple, "$.allow_strange_comment"),                  force=True)
  set_dict_attr(data, "$.user.allow_unfollower_comment",               get_dict_attr(user_table_tuple, "$.allow_unfollower_comment"),               force=True)
  set_dict_attr(data, "$.user.allow_use_linkmic",                      get_dict_attr(user_table_tuple, "$.allow_use_linkmic"),                      force=True)
  set_dict_attr(data, "$.user.authorization_info",                     get_dict_attr(user_table_tuple, "$.authorization_info"),                     force=True)
  set_dict_attr(data, "$.user.badge_image_list",                       _parse_json_field(get_dict_attr(user_table_tuple, "$.badge_image_list")),    force=True)
  set_dict_attr(data, "$.user.badge_image_list_v2",                    _parse_json_field(get_dict_attr(user_table_tuple, "$.badge_image_list_v2")), force=True)
  set_dict_attr(data, "$.user.bg_img_url",                             get_dict_attr(user_table_tuple, "$.bg_img_url"),                             force=True)
  set_dict_attr(data, "$.user.birthday",                               get_dict_attr(user_table_tuple, "$.birthday"),                               force=True)
  set_dict_attr(data, "$.user.birthday_description",                   get_dict_attr(user_table_tuple, "$.birthday_description"),                   force=True)
  set_dict_attr(data, "$.user.birthday_valid",                         get_dict_attr(user_table_tuple, "$.birthday_valid"),                         force=True)
  set_dict_attr(data, "$.user.block_status",                           get_dict_attr(user_table_tuple, "$.block_status"),                           force=True)
  set_dict_attr(data, "$.user.city",                                   get_dict_attr(user_table_tuple, "$.city"),                                   force=True)
  set_dict_attr(data, "$.user.comment_restrict",                       get_dict_attr(user_table_tuple, "$.comment_restrict"),                       force=True)
  set_dict_attr(data, "$.user.commerce_webcast_config_ids",            _parse_json_field(get_dict_attr(user_table_tuple, "$.commerce_webcast_config_ids")), force=True)
  set_dict_attr(data, "$.user.constellation",                          get_dict_attr(user_table_tuple, "$.constellation"),                          force=True)
  set_dict_attr(data, "$.user.consume_diamond_level",                  get_dict_attr(user_table_tuple, "$.consume_diamond_level"),                  force=True)
  set_dict_attr(data, "$.user.create_time",                            get_dict_attr(user_table_tuple, "$.create_time"),                            force=True)
  set_dict_attr(data, "$.user.desensitized_nickname",                  get_dict_attr(user_table_tuple, "$.desensitized_nickname"),                  force=True)
  set_dict_attr(data, "$.user.disable_ichat",                          get_dict_attr(user_table_tuple, "$.disable_ichat"),                          force=True)
  set_dict_attr(data, "$.user.display_id",                             get_dict_attr(user_table_tuple, "$.display_id"),                             force=True)
  set_dict_attr(data, "$.user.enable_ichat_img",                       get_dict_attr(user_table_tuple, "$.enable_ichat_img"),                       force=True)
  set_dict_attr(data, "$.user.exp",                                    get_dict_attr(user_table_tuple, "$.exp"),                                    force=True)
  set_dict_attr(data, "$.user.experience",                             get_dict_attr(user_table_tuple, "$.experience"),                             force=True)
  set_dict_attr(data, "$.user.fan_ticket_count",                       get_dict_attr(user_table_tuple, "$.fan_ticket_count"),                       force=True)
  set_dict_attr(data, "$.user.fold_stranger_chat",                     get_dict_attr(user_table_tuple, "$.fold_stranger_chat"),                     force=True)
  set_dict_attr(data, "$.user.follow_status",                          get_dict_attr(user_table_tuple, "$.follow_status"),                          force=True)
  set_dict_attr(data, "$.user.foreign_user",                           get_dict_attr(user_table_tuple, "$.foreign_user"),                           force=True)
  set_dict_attr(data, "$.user.gender",                                 get_dict_attr(user_table_tuple, "$.gender"),                                 force=True)
  set_dict_attr(data, "$.user.hotsoon_verified",                       get_dict_attr(user_table_tuple, "$.hotsoon_verified"),                       force=True)
  set_dict_attr(data, "$.user.hotsoon_verified_reason",                get_dict_attr(user_table_tuple, "$.hotsoon_verified_reason"),                force=True)
  set_dict_attr(data, "$.user.ichat_restrict_type",                    get_dict_attr(user_table_tuple, "$.ichat_restrict_type"),                    force=True)
  set_dict_attr(data, "$.user.income_share_percent",                   get_dict_attr(user_table_tuple, "$.income_share_percent"),                   force=True)
  set_dict_attr(data, "$.user.is_anonymous",                           get_dict_attr(user_table_tuple, "$.is_anonymous"),                           force=True)
  set_dict_attr(data, "$.user.is_follower",                            get_dict_attr(user_table_tuple, "$.is_follower"),                            force=True)
  set_dict_attr(data, "$.user.is_following",                           get_dict_attr(user_table_tuple, "$.is_following"),                           force=True)
  set_dict_attr(data, "$.user.level",                                  get_dict_attr(user_table_tuple, "$.level"),                                  force=True)
  set_dict_attr(data, "$.user.link_mic_stats",                         get_dict_attr(user_table_tuple, "$.link_mic_stats"),                         force=True)
  set_dict_attr(data, "$.user.location_city",                          get_dict_attr(user_table_tuple, "$.location_city"),                          force=True)
  set_dict_attr(data, "$.user.media_badge_image_list",                 _parse_json_field(get_dict_attr(user_table_tuple, "$.media_badge_image_list")), force=True)
  set_dict_attr(data, "$.user.modify_time",                            get_dict_attr(user_table_tuple, "$.modify_time"),                            force=True)
  set_dict_attr(data, "$.user.mystery_man",                            get_dict_attr(user_table_tuple, "$.mystery_man"),                            force=True)
  set_dict_attr(data, "$.user.need_profile_guide",                     get_dict_attr(user_table_tuple, "$.need_profile_guide"),                     force=True)
  set_dict_attr(data, "$.user.new_real_time_icons",                    _parse_json_field(get_dict_attr(user_table_tuple, "$.new_real_time_icons")), force=True)
  set_dict_attr(data, "$.user.nickname",                               get_dict_attr(user_table_tuple, "$.nickname"),                               force=True)
  set_dict_attr(data, "$.user.pay_score",                              get_dict_attr(user_table_tuple, "$.pay_score"),                              force=True)
  set_dict_attr(data, "$.user.pay_scores",                             get_dict_attr(user_table_tuple, "$.pay_scores"),                             force=True)
  set_dict_attr(data, "$.user.public_area_oper_freq",                  get_dict_attr(user_table_tuple, "$.public_area_oper_freq"),                  force=True)
  set_dict_attr(data, "$.user.push_comment_status",                    get_dict_attr(user_table_tuple, "$.push_comment_status"),                    force=True)
  set_dict_attr(data, "$.user.push_digg",                              get_dict_attr(user_table_tuple, "$.push_digg"),                              force=True)
  set_dict_attr(data, "$.user.push_follow",                            get_dict_attr(user_table_tuple, "$.push_follow"),                            force=True)
  set_dict_attr(data, "$.user.push_friend_action",                     get_dict_attr(user_table_tuple, "$.push_friend_action"),                     force=True)
  set_dict_attr(data, "$.user.push_ichat",                             get_dict_attr(user_table_tuple, "$.push_ichat"),                             force=True)
  set_dict_attr(data, "$.user.push_status",                            get_dict_attr(user_table_tuple, "$.push_status"),                            force=True)
  set_dict_attr(data, "$.user.push_video_post",                        get_dict_attr(user_table_tuple, "$.push_video_post"),                        force=True)
  set_dict_attr(data, "$.user.push_video_recommend",                   get_dict_attr(user_table_tuple, "$.push_video_recommend"),                   force=True)
  set_dict_attr(data, "$.user.real_time_icons",                        _parse_json_field(get_dict_attr(user_table_tuple, "$.real_time_icons")),     force=True)
  set_dict_attr(data, "$.user.remark_name",                            get_dict_attr(user_table_tuple, "$.remark_name"),                            force=True)
  set_dict_attr(data, "$.user.sec_uid",                                get_dict_attr(user_table_tuple, "$.sec_uid"),                                force=True)
  set_dict_attr(data, "$.user.secret",                                 get_dict_attr(user_table_tuple, "$.secret"),                                 force=True)
  set_dict_attr(data, "$.user.share_qrcode_uri",                       get_dict_attr(user_table_tuple, "$.share_qrcode_uri"),                       force=True)
  set_dict_attr(data, "$.user.short_id",                               get_dict_attr(user_table_tuple, "$.short_id"),                               force=True)
  set_dict_attr(data, "$.user.signature",                              get_dict_attr(user_table_tuple, "$.signature"),                              force=True)
  set_dict_attr(data, "$.user.special_id",                             get_dict_attr(user_table_tuple, "$.special_id"),                             force=True)
  set_dict_attr(data, "$.user.status",                                 get_dict_attr(user_table_tuple, "$.status"),                                 force=True)
  set_dict_attr(data, "$.user.telephone",                              get_dict_attr(user_table_tuple, "$.telephone"),                              force=True)
  set_dict_attr(data, "$.user.ticket_count",                           get_dict_attr(user_table_tuple, "$.ticket_count"),                           force=True)
  set_dict_attr(data, "$.user.top_fans",                               _parse_json_field(get_dict_attr(user_table_tuple, "$.top_fans")),            force=True)
  set_dict_attr(data, "$.user.top_vip_no",                             get_dict_attr(user_table_tuple, "$.top_vip_no"),                             force=True)
  set_dict_attr(data, "$.user.total_recharge_diamond_count",           get_dict_attr(user_table_tuple, "$.total_recharge_diamond_count"),           force=True)
  set_dict_attr(data, "$.user.user_canceled",                          get_dict_attr(user_table_tuple, "$.user_canceled"),                          force=True)
  set_dict_attr(data, "$.user.user_open_id",                           get_dict_attr(user_table_tuple, "$.user_open_id"),                           force=True)
  set_dict_attr(data, "$.user.user_role",                              get_dict_attr(user_table_tuple, "$.user_role"),                              force=True)
  set_dict_attr(data, "$.user.verified",                               get_dict_attr(user_table_tuple, "$.verified"),                               force=True)
  set_dict_attr(data, "$.user.verified_content",                       get_dict_attr(user_table_tuple, "$.verified_content"),                       force=True)
  set_dict_attr(data, "$.user.verified_mobile",                        get_dict_attr(user_table_tuple, "$.verified_mobile"),                        force=True)
  set_dict_attr(data, "$.user.verified_reason",                        get_dict_attr(user_table_tuple, "$.verified_reason"),                        force=True)
  set_dict_attr(data, "$.user.watch_duration_month",                   get_dict_attr(user_table_tuple, "$.watch_duration_month"),                   force=True)
  set_dict_attr(data, "$.user.web_rid",                                get_dict_attr(user_table_tuple, "$.web_rid"),                                force=True)
  set_dict_attr(data, "$.user.webcast_uid",                            get_dict_attr(user_table_tuple, "$.webcast_uid"),                            force=True)
  set_dict_attr(data, "$.user.with_car_management_permission",         get_dict_attr(user_table_tuple, "$.with_car_management_permission"),         force=True)
  set_dict_attr(data, "$.user.with_commerce_permission",               get_dict_attr(user_table_tuple, "$.with_commerce_permission"),               force=True)
  set_dict_attr(data, "$.user.with_fusion_shop_entry",                 get_dict_attr(user_table_tuple, "$.with_fusion_shop_entry"),                 force=True)
  set_dict_attr(data, "$.user.can_view_webcast_private",               get_dict_attr(user_table_tuple, "$.can_view_webcast_private"),               force=True)
  set_dict_attr(data, "$.user.webcast_nick",                           get_dict_attr(user_table_tuple, "$.webcast_nick"),                           force=True)
  set_dict_attr(data, "$.user.webcast_private",                        get_dict_attr(user_table_tuple, "$.webcast_private"),                        force=True)
  set_dict_attr(data, "$.user.hide_by_room",                           get_dict_attr(user_table_tuple, "$.hide_by_room"),                           force=True)
  set_dict_attr(data, "$.user.link_mask",                              get_dict_attr(user_table_tuple, "$.link_mask"),                              force=True)

  """
  >> extra
  """
  if hasattr(now, "timestamp"):
    set_dict_attr(data, "$.extra.now", floor(now.timestamp() * 1000), force=True)
  else:
    set_dict_attr(data, "$.extra.now", now if now is not None else 0, force=True)
  
  """
  >> status_code
  """
  set_dict_attr(data, "$.status_code", status_code, force=True)

  ##
  ## normalize scalar representation to reduce type drift (bool/int/str/null)
  ##
  data = _normalize_export_types(data)

  ##
  ## export format: external_info.data / external_info.extra / external_info.status_code
  ##
  export_data = dict()
  set_dict_attr(export_data, "$.external_info.data",        {"room": get_dict_attr(data, "$.room"), "user": get_dict_attr(data, "$.user")}, force=True)
  set_dict_attr(export_data, "$.external_info.extra",       get_dict_attr(data, "$.extra"),        force=True)
  set_dict_attr(export_data, "$.external_info.status_code", get_dict_attr(data, "$.status_code"),  force=True)
  
  if output_path is not None:
    save_dict_as_file(_sort_export_fields(export_data), Path(output_path), allow_unicode=False)
  else:
    return _sort_export_fields(export_data)