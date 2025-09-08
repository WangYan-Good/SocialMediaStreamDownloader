##
## table aagent.py
## This module handles the table of the Social Media Stream Downloader (SMSD) database.
## It provides a data operation of table level in social_media_stream_downloader.
##

##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from pathlib                                                          import   Path
from datetime                                                         import   datetime as dat
import                                                                         json

## <<Extension>>

## <<Third-Part>>
from backend.src.library.baselib                                      import   load_yml, get_dict_attr, set_dict_attr, output_dict
from backend.src.base.log                                             import   get_logger
from backend.src.database.social_media_stream_database                import   SocialMediaStreamDataBase
from backend.src.database.table.live                                  import   LiveRecordTable
from backend.src.database.table.room                                  import   RoomAttributeTable,                                  \
                                                                               RoomAdminUserIdTable,                                \
                                                                               RoomAdminUserOpenIdTable,                            \
                                                                               RoomAssistLabelTable,                                \
                                                                               RoomDecoTable,                                       \
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
                                                                               PictureContentTable
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
                                                                               StreamPushUrlTable
from backend.src.database.table.user                                  import   RoomOwnerTable,                                      \
                                                                               FansClubTable,                                       \
                                                                               FansClubAvailableGiftIdTable,                        \
                                                                               FansClubBadgeIconTable,                              \
                                                                               RoomOwnerUserAttrTable,                              \
                                                                               RoomAdminPrivilegeTable,                             \
                                                                               UserTable

##
## import a living data to relative tables of social media stream downloader.
##
def import_douyin_live_info_to_database(data:dict, db:SocialMediaStreamDataBase) -> None:
  """
  data
  ├── 1. share_url
  ├── 2. favorite_owner
  ├── 3. live_record
  ├── 4. room_attribute
  │   ├── 4-1. room_admin_user_id
  │   ├── 4-2. room_admin_user_open_id
  │   ├── 4-3. room_assist_label - TBD
  │   ├── 4-4. room_deco - TBD
  │   ├── 4-5. room_realtime_playback_quality - TBD
  │   ├── 4-6. fans_group_admin_user_id
  │   ├── 4-7. fans_group_admin_user_open_id
  │   ├── 4-8. room_filter_word - TBD
  │   ├── 4-9. room_live_distribution - TBD
  │   ├── 4-10. room_owner
  │   │   ├── 4-10-1. badge_image
  │   │   ├── 4-10-2. commerce_webcast_config_id - TBD
  │   │   ├── 4-10-3. fans_club
  │   │   │   ├── 4-10-3-1. fans_club_available_gift_id
  │   │   │   └── 4-10-3-2. fans_club_badge_icon
  │   │   ├── 4-10-4. media_badge_image - TBD
  │   │   ├── 4-10-5. new_real_time_icon - TBD
  │   │   ├── 4-10-6. pay_grade_icon
  │   │   ├── 4-10-7. room_owner_real_time_icon - TBD
  │   │   ├── 4-10-8. room_subscribe
  │   │   ├── 4-10-9. room_owner_top_fans - TBD
  │   │   ├── 4-10-10. room_owner_user_attr
  │   │   │   └── 4-10-10-1. room_admin_privilege
  │   │   ├── 4-10-11. room_owner_user_dress_own_id
  │   │   └── 4-10-12. room_owner_dress_wear_id
  │   ├── 4-11. room_pack_meta
  |   ├── 4-12. room_paid_live_data
  |   ├── 4-13. room_auth
  |   ├── 4-14. room_tab
  │   ├── 4-15. room_sharing_music_id
  |   └── 4-16. room_short_touch_area_config
  |       ├── 4-16-1. room_short_touch_area_config_element
  |       ├── 4-16-2. room_short_touch_area_config_strategy_feat_whitelist
  |       ├── 4-16-3. room_temp_state_condition_map
  |       |   └── 4-16-3-1. room_temp_state_global_condition_ignore_strategy_type
  |       └── 4-16-4. room_temp_state_global_condition
  ├── 5. room_record
  ├── 6. live_stream
  |   ├── 6-1. stream_candidate_resolution
  |   ├── 6-2. stream_complete_push_url
  |   ├── 6-3. live_core_sdk_data
  |   |   └── 6-3-1. live_core_sdk_pull_data
  |   |       ├── 6-3-1-1. live_core_sdk_pull_flv_data
  |   |       ├── 6-3-1-2. live_core_sdk_pull_hls_data
  |   |       └── 6-3-1-3. live_core_sdk_pull_data_option
  |   |           ├── 6-3-1-3-1. live_core_sdk_pull_quality_data
  |   |           └── 6-3-1-3-2. live_core_sdk_pull_default_quality_data
  |   └── 6-4. stream_push_url
  ├── 7. room_tag
  ├── 8. room_top_fans
  ├── 9. room_upper_right_widget_data
  ├── 10. room_vs_role
  ├── 11. picture
  │   ├── 11-1. picture_flex_setting
  │   ├── 11-2. picture_text_setting
  │   ├── 11-3. picture_url
  │   └── 11-4. picture_content
  └── 12. user
      ├── 12-1. badge_image
      ├── 12-2. commerce_webcast_config_id - TBD
      ├── 12-3. media_badge_image - TBD
      ├── 12-4. new_real_time_icon - TBD
      ├── 12-5. room_owner_real_time_icon - TBD
      └── 12-6. room_owner_top_fans - TBD
  """

  ##
  ## LiveRecordTable
  ## 
  live_record_table = LiveRecordTable(db)
  try:
    ##
    ## +----------------------------------+
    ## | Field                            |
    ## +----------------------------------+
    ## | now                              |
    ## | platform                         |
    ## | room_id                          |
    ## | user_id                          |
    ## | start_time                       |
    ## | finish_time                      |
    ## | status_code                      |
    ## +----------------------------------+
    ##
    live_record_table_tuple = live_record_table.get_tuple()

    now             = dat.fromtimestamp(get_dict_attr(data, "$.extra.now")/1000.0)
    DOUYIN_PLATFORM = "douyin"
    room_id         = get_dict_attr(data,    "$.data.room.id")
    owner_user_id   = get_dict_attr(data,    "$.data.room.owner_user_id")
    user_id         = get_dict_attr(data,    "$.data.user.id")
    start_time      = get_dict_attr(data,    "$.data.room.start_time")
    finish_time     = get_dict_attr(data,    "$.data.room.finish_time")
    status_code     = get_dict_attr(data,    "$.status_code")

    set_dict_attr(live_record_table_tuple,   "$.now",           now)
    set_dict_attr(live_record_table_tuple,   "$.platform",      DOUYIN_PLATFORM)
    set_dict_attr(live_record_table_tuple,   "$.room_id",       str(room_id))
    set_dict_attr(live_record_table_tuple,   "$.owner_user_id", str(owner_user_id))
    set_dict_attr(live_record_table_tuple,   "$.user_id",       str(user_id))
    if start_time != 0:
      set_dict_attr(live_record_table_tuple, "$.start_time",    dat.fromtimestamp(start_time))
    if finish_time != 0:
      set_dict_attr(live_record_table_tuple, "$.finish_time",   dat.fromtimestamp(finish_time))
    set_dict_attr(live_record_table_tuple,   "$.status_code",   status_code)

    ##
    ## 1. check is the table is exist
    ## 2. if not exist, create it
    ## 3. insert the record
    ##
    if db.is_table_exist(live_record_table.get_name()) is False:
      live_record_table.create()
    live_record_table.insert_record(live_record_table_tuple)
  except Exception as e:
    get_logger().error("insert LiveRecordTable failed: {}".format(e))
    raise e

  ##
  ## RoomAttributeTable
  ##
  room_attribute_table = RoomAttributeTable(db)
  try:
    ##
    ## +----------------------------------+
    ## | Field                            |
    ## +----------------------------------+
    ## | AnchorABMap                      |
    ## | acquaintance_status              |
    ## | anchor_scheduled_time_text       |
    ## | anchor_share_text                |
    ## | anchor_tab_type                  |
    ## | app_id                           |
    ## | auth_city                        |
    ## | auto_cover                       |
    ## | base_category                    |
    ## | book_end_time                    |
    ## | book_time                        |
    ## | business_live                    |
    ## | category                         |
    ## | cell_style                       |
    ## | city_top_distance                |
    ## | client_version                   |
    ## | placeholder                      |
    ## | comment_name_mode                |
    ## | common_label_list                |
    ## | content_tag                      |
    ## | create_time                      |
    ## | distance                         |
    ## | distance_city                    |
    ## | distance_km                      |
    ## | dynamic_cover_dict               |
    ## | dynamic_cover_uri                |
    ## | enable_room_perspective          |
    ## | create_scene                     |
    ## | facial_unrecognised              |
    ## | geo_block                        |
    ## | is_sandbox                       |
    ## | is_virtual_anchor                |
    ## | limit_appid                      |
    ## | limit_strategy                   |
    ## | realtime_playback_shift          |
    ## | realtime_playback_start_shift    |
    ## | realtime_replay_enabled          |
    ## | vr_type                          |
    ## | vs_type                          |
    ## | xigua_uid                        |
    ## | fansclub_msg_style               |
    ## | fcdn_appid                       |
    ## | finish_reason                    |
    ## | finish_time                      |
    ## | finish_url                       |
    ## | follow_msg_style                 |
    ## | forum_extra_data                 |
    ## | game_room_type                   |
    ## | gift_msg_style                   |
    ## | group_id                         |
    ## | group_source                     |
    ## | has_commerce_goods               |
    ## | has_promotion_games              |
    ## | highlight                        |
    ## | id                               |
    ## | introduction                     |
    ## | is_need_check_list               |
    ## | is_official_channel_room         |
    ## | is_replay                        |
    ## | is_show_inquiry_ball             |
    ## | is_show_user_card_switch         |
    ## | item_explicit_info               |
    ## | layout                           |
    ## | linkmic_display_type             |
    ## | linkmic_layout                   |
    ## | live_id                          |
    ## | live_platform_source             |
    ## | live_room_mode                   |
    ## | live_type_audio                  |
    ## | live_type_linkmic                |
    ## | live_type_normal                 |
    ## | live_type_official               |
    ## | live_type_sandbox                |
    ## | live_type_screenshot             |
    ## | live_type_third_party            |
    ## | live_type_vs_live                |
    ## | live_type_vs_premiere            |
    ## | admin_flag                       |
    ## | location                         |
    ## | official_channel_open_id         |
    ## | official_channel_uid             |
    ## | orientation                      |
    ## | os_type                          |
    ## | owner_device_id                  |
    ## | owner_open_id                    |
    ## | owner_user_id                    |
    ## | start_time                       |
    ## | room_layout                      |
    ## | room_tag                         |
    ## | scroll_config                    |
    ## | search_id                        |
    ## | sell_goods                       |
    ## | share_msg_style                  |
    ## | share_url                        |
    ## | title                            |
    ## | title_recommend                  |
    ## | toutiao_cover_recommend_level    |
    ## | toutiao_title_recommend_level    |
    ## | use_filter                       |
    ## | user_count                       |
    ## | vertical_cover_uri               |
    ## | vid                              |
    ## | video_feed_tag                   |
    ## | visibility_range                 |
    ## | vs_main_replay_id                |
    ## | wait_copy                        |
    ## | webcast_sdk_version              |
    ## +----------------------------------+
    ##
    room_attribute_table_tuple = room_attribute_table.get_tuple()

    AnchorABMap                   = get_dict_attr(data, "$.data.room.AnchorABMap")
    acquaintance_status           = get_dict_attr(data, "$.data.room.acquaintance_status")
    anchor_scheduled_time_text    = get_dict_attr(data, "$.data.room.anchor_scheduled_time_text")
    anchor_share_text             = get_dict_attr(data, "$.data.room.anchor_share_text")
    anchor_tab_type               = get_dict_attr(data, "$.data.room.anchor_tab_type")
    app_id                        = get_dict_attr(data, "$.data.room.app_id")
    auth_city                     = get_dict_attr(data, "$.data.room.auth_city")
    auto_cover                    = get_dict_attr(data, "$.data.room.auto_cover")
    base_category                 = get_dict_attr(data, "$.data.room.base_category")
    book_end_time                 = get_dict_attr(data, "$.data.room.book_end_time")
    book_time                     = get_dict_attr(data, "$.data.room.book_time")
    business_live                 = get_dict_attr(data, "$.data.room.business_live")
    category                      = get_dict_attr(data, "$.data.room.category")
    cell_style                    = get_dict_attr(data, "$.data.room.cell_style")
    city_top_distance             = get_dict_attr(data, "$.data.room.city_top_distance")
    client_version                = get_dict_attr(data, "$.data.room.client_version")
    placeholder                   = get_dict_attr(data, "$.data.room.comment_box.placeholder")
    comment_name_mode             = get_dict_attr(data, "$.data.room.comment_name_mode")
    common_label_list             = get_dict_attr(data, "$.data.room.common_label_list")
    content_tag                   = get_dict_attr(data, "$.data.room.content_tag")
    create_time                   = get_dict_attr(data, "$.data.room.create_time")
    distance                      = get_dict_attr(data, "$.data.room.distance")
    distance_city                 = get_dict_attr(data, "$.data.room.distance_city")
    distance_km                   = get_dict_attr(data, "$.data.room.distance_km")
    dynamic_cover_dict            = get_dict_attr(data, "$.data.room.dynamic_cover_dict")
    dynamic_cover_uri             = get_dict_attr(data, "$.data.room.dynamic_cover_uri")
    enable_room_perspective       = get_dict_attr(data, "$.data.room.enable_room_perspective")
    create_scene                  = get_dict_attr(data, "$.data.room.extra.create_scene")
    facial_unrecognised           = get_dict_attr(data, "$.data.room.extra.facial_unrecognised")
    geo_block                     = get_dict_attr(data, "$.data.room.extra.geo_block")
    is_sandbox                    = get_dict_attr(data, "$.data.room.extra.is_sandbox")
    is_virtual_anchor             = get_dict_attr(data, "$.data.room.extra.is_virtual_anchor")
    limit_appid                   = get_dict_attr(data, "$.data.room.extra.limit_appid")
    limit_strategy                = get_dict_attr(data, "$.data.room.extra.limit_strategy")
    realtime_playback_shift       = get_dict_attr(data, "$.data.room.extra.realtime_playback_shift")
    realtime_playback_start_shift = get_dict_attr(data, "$.data.room.extra.realtime_playback_start_shift")
    realtime_replay_enabled       = get_dict_attr(data, "$.data.room.extra.realtime_replay_enabled")
    vr_type                       = get_dict_attr(data, "$.data.room.extra.vr_type")
    vs_type                       = get_dict_attr(data, "$.data.room.extra.vs_type")
    xigua_uid                     = get_dict_attr(data, "$.data.room.extra.xigua_uid")
    fansclub_msg_style            = get_dict_attr(data, "$.data.room.fansclub_msg_style")
    fcdn_appid                    = get_dict_attr(data, "$.data.room.fcdn_appid")
    finish_reason                 = get_dict_attr(data, "$.data.room.finish_reason")
    finish_time                   = get_dict_attr(data, "$.data.room.finish_time")
    finish_url                    = get_dict_attr(data, "$.data.room.finish_url")
    follow_msg_style              = get_dict_attr(data, "$.data.room.follow_msg_style")
    forum_extra_data              = get_dict_attr(data, "$.data.room.forum_extra_data")
    game_room_type                = get_dict_attr(data, "$.data.room.game_room_type")
    gift_msg_style                = get_dict_attr(data, "$.data.room.gift_msg_style")
    group_id                      = get_dict_attr(data, "$.data.room.group_id")
    group_source                  = get_dict_attr(data, "$.data.room.group_source")
    has_commerce_goods            = get_dict_attr(data, "$.data.room.has_commerce_goods")
    has_promotion_games           = get_dict_attr(data, "$.data.room.has_promotion_games")
    highlight                     = get_dict_attr(data, "$.data.room.highlight")
    id                            = get_dict_attr(data, "$.data.room.id")
    introduction                  = get_dict_attr(data, "$.data.room.introduction")
    is_need_check_list            = get_dict_attr(data, "$.data.room.is_need_check_list")
    is_official_channel_room      = get_dict_attr(data, "$.data.room.is_official_channel_room")
    is_replay                     = get_dict_attr(data, "$.data.room.is_replay")
    is_show_inquiry_ball          = get_dict_attr(data, "$.data.room.is_show_inquiry_ball")
    is_show_user_card_switch      = get_dict_attr(data, "$.data.room.is_show_user_card_switch")
    item_explicit_info            = get_dict_attr(data, "$.data.room.item_explicit_info")
    layout                        = get_dict_attr(data, "$.data.room.layout")
    linkmic_display_type          = get_dict_attr(data, "$.data.room.linkmic_display_type")
    linkmic_layout                = get_dict_attr(data, "$.data.room.linkmic_layout")
    live_id                       = get_dict_attr(data, "$.data.room.live_id")
    live_platform_source          = get_dict_attr(data, "$.data.room.live_platform_source")
    live_room_mode                = get_dict_attr(data, "$.data.room.live_room_mode")
    live_type_audio               = get_dict_attr(data, "$.data.room.live_type_audio")
    live_type_linkmic             = get_dict_attr(data, "$.data.room.live_type_linkmic")
    live_type_normal              = get_dict_attr(data, "$.data.room.live_type_normal")
    live_type_official            = get_dict_attr(data, "$.data.room.live_type_official")
    live_type_sandbox             = get_dict_attr(data, "$.data.room.live_type_sandbox")
    live_type_screenshot          = get_dict_attr(data, "$.data.room.live_type_screenshot")
    live_type_third_party         = get_dict_attr(data, "$.data.room.live_type_third_party")
    live_type_vs_live             = get_dict_attr(data, "$.data.room.live_type_vs_live")
    live_type_vs_premiere         = get_dict_attr(data, "$.data.room.live_type_vs_premiere")
    admin_flag                    = get_dict_attr(data, "$.data.room.living_room_attrs.admin_flag")
    location                      = get_dict_attr(data, "$.data.room.location")
    official_channel_open_id      = get_dict_attr(data, "$.data.room.official_channel_open_id")
    official_channel_uid          = get_dict_attr(data, "$.data.room.official_channel_uid")
    orientation                   = get_dict_attr(data, "$.data.room.orientation")
    os_type                       = get_dict_attr(data, "$.data.room.os_type")
    owner_device_id               = get_dict_attr(data, "$.data.room.owner_device_id")
    owner_open_id                 = get_dict_attr(data, "$.data.room.owner_open_id")
    owner_user_id                 = get_dict_attr(data, "$.data.room.owner_user_id")
    start_time                    = get_dict_attr(data, "$.data.room.start_time")
    room_layout                   = get_dict_attr(data, "$.data.room.room_layout")
    room_tag                      = get_dict_attr(data, "$.data.room.room_tag")
    scroll_config                 = get_dict_attr(data, "$.data.room.scroll_config")
    search_id                     = get_dict_attr(data, "$.data.room.search_id")
    sell_goods                    = get_dict_attr(data, "$.data.room.sell_goods")
    share_msg_style               = get_dict_attr(data, "$.data.room.share_msg_style")
    share_url                     = get_dict_attr(data, "$.data.room.share_url")
    title                         = get_dict_attr(data, "$.data.room.title")
    title_recommend               = get_dict_attr(data, "$.data.room.title_recommend")
    toutiao_cover_recommend_level = get_dict_attr(data, "$.data.room.toutiao_cover_recommend_level")
    toutiao_title_recommend_level = get_dict_attr(data, "$.data.room.toutiao_title_recommend_level")
    use_filter                    = get_dict_attr(data, "$.data.room.use_filter")
    user_count                    = get_dict_attr(data, "$.data.room.user_count")
    vertical_cover_uri            = get_dict_attr(data, "$.data.room.vertical_cover_uri")
    vid                           = get_dict_attr(data, "$.data.room.vid")
    video_feed_tag                = get_dict_attr(data, "$.data.room.video_feed_tag")
    visibility_range              = get_dict_attr(data, "$.data.room.visibility_range")
    vs_main_replay_id             = get_dict_attr(data, "$.data.room.vs_main_replay_id")
    wait_copy                     = get_dict_attr(data, "$.data.room.wait_copy")
    webcast_sdk_version           = get_dict_attr(data, "$.data.room.webcast_sdk_version")

    set_dict_attr(room_attribute_table_tuple, "$.AnchorABMap",                   json.dumps(AnchorABMap))
    set_dict_attr(room_attribute_table_tuple, "$.acquaintance_status",           acquaintance_status)
    set_dict_attr(room_attribute_table_tuple, "$.anchor_scheduled_time_text",    anchor_scheduled_time_text)
    set_dict_attr(room_attribute_table_tuple, "$.anchor_share_text",             anchor_share_text)
    set_dict_attr(room_attribute_table_tuple, "$.anchor_tab_type",               anchor_tab_type)
    set_dict_attr(room_attribute_table_tuple, "$.app_id",                        str(app_id))
    set_dict_attr(room_attribute_table_tuple, "$.auth_city",                     auth_city)
    set_dict_attr(room_attribute_table_tuple, "$.auto_cover",                    auto_cover)
    set_dict_attr(room_attribute_table_tuple, "$.base_category",                 base_category)
    if book_end_time != 0:
      set_dict_attr(room_attribute_table_tuple, "$.book_end_time",                 dat.fromtimestamp(book_end_time))
    if book_time != 0:
      set_dict_attr(room_attribute_table_tuple, "$.book_time",                     dat.fromtimestamp(book_time))
    set_dict_attr(room_attribute_table_tuple, "$.business_live",                 business_live)
    set_dict_attr(room_attribute_table_tuple, "$.category",                      category)
    set_dict_attr(room_attribute_table_tuple, "$.cell_style",                    cell_style)
    set_dict_attr(room_attribute_table_tuple, "$.city_top_distance",             city_top_distance)
    set_dict_attr(room_attribute_table_tuple, "$.client_version",                str(client_version))
    set_dict_attr(room_attribute_table_tuple, "$.placeholder",                   placeholder)
    set_dict_attr(room_attribute_table_tuple, "$.comment_name_mode",             comment_name_mode)
    set_dict_attr(room_attribute_table_tuple, "$.common_label_list",             common_label_list)
    set_dict_attr(room_attribute_table_tuple, "$.content_tag",                   content_tag)
    if create_time != 0:
      set_dict_attr(room_attribute_table_tuple, "$.create_time",                   dat.fromtimestamp(create_time))
    set_dict_attr(room_attribute_table_tuple, "$.distance",                      distance)
    set_dict_attr(room_attribute_table_tuple, "$.distance_city",                 distance_city)
    set_dict_attr(room_attribute_table_tuple, "$.distance_km",                   distance_km)
    set_dict_attr(room_attribute_table_tuple, "$.dynamic_cover_dict",            json.dumps(dynamic_cover_dict))
    set_dict_attr(room_attribute_table_tuple, "$.dynamic_cover_uri",             dynamic_cover_uri)
    set_dict_attr(room_attribute_table_tuple, "$.enable_room_perspective",       enable_room_perspective)
    set_dict_attr(room_attribute_table_tuple, "$.create_scene",                  create_scene)
    set_dict_attr(room_attribute_table_tuple, "$.facial_unrecognised",           facial_unrecognised)
    set_dict_attr(room_attribute_table_tuple, "$.geo_block",                     geo_block)
    set_dict_attr(room_attribute_table_tuple, "$.is_sandbox",                    is_sandbox)
    set_dict_attr(room_attribute_table_tuple, "$.is_virtual_anchor",             is_virtual_anchor)
    set_dict_attr(room_attribute_table_tuple, "$.limit_appid",                   limit_appid)
    set_dict_attr(room_attribute_table_tuple, "$.limit_strategy",                limit_strategy)
    set_dict_attr(room_attribute_table_tuple, "$.realtime_playback_shift",       realtime_playback_shift)
    set_dict_attr(room_attribute_table_tuple, "$.realtime_playback_start_shift", realtime_playback_start_shift)
    set_dict_attr(room_attribute_table_tuple, "$.realtime_replay_enabled",       realtime_replay_enabled)
    set_dict_attr(room_attribute_table_tuple, "$.vr_type",                       vr_type)
    set_dict_attr(room_attribute_table_tuple, "$.vs_type",                       vs_type)
    set_dict_attr(room_attribute_table_tuple, "$.xigua_uid",                     str(xigua_uid))
    set_dict_attr(room_attribute_table_tuple, "$.fansclub_msg_style",            fansclub_msg_style)
    set_dict_attr(room_attribute_table_tuple, "$.fcdn_appid",                    str(fcdn_appid))
    set_dict_attr(room_attribute_table_tuple, "$.finish_reason",                 finish_reason)
    if finish_time != 0:
      set_dict_attr(room_attribute_table_tuple, "$.finish_time",                   dat.fromtimestamp(finish_time))
    set_dict_attr(room_attribute_table_tuple, "$.finish_url",                    finish_url)
    set_dict_attr(room_attribute_table_tuple, "$.follow_msg_style",              follow_msg_style)
    set_dict_attr(room_attribute_table_tuple, "$.forum_extra_data",              forum_extra_data)
    set_dict_attr(room_attribute_table_tuple, "$.game_room_type",                game_room_type)
    set_dict_attr(room_attribute_table_tuple, "$.gift_msg_style",                gift_msg_style)
    set_dict_attr(room_attribute_table_tuple, "$.group_id",                      str(group_id))
    set_dict_attr(room_attribute_table_tuple, "$.group_source",                  group_source)
    set_dict_attr(room_attribute_table_tuple, "$.has_commerce_goods",            has_commerce_goods)
    set_dict_attr(room_attribute_table_tuple, "$.has_promotion_games",           has_promotion_games)
    set_dict_attr(room_attribute_table_tuple, "$.highlight",                     highlight)
    set_dict_attr(room_attribute_table_tuple, "$.id",                            str(id))
    set_dict_attr(room_attribute_table_tuple, "$.introduction",                  introduction)
    set_dict_attr(room_attribute_table_tuple, "$.is_need_check_list",            is_need_check_list)
    set_dict_attr(room_attribute_table_tuple, "$.is_official_channel_room",      is_official_channel_room)
    set_dict_attr(room_attribute_table_tuple, "$.is_replay",                     is_replay)
    set_dict_attr(room_attribute_table_tuple, "$.is_show_inquiry_ball",          is_show_inquiry_ball)
    set_dict_attr(room_attribute_table_tuple, "$.is_show_user_card_switch",      is_show_user_card_switch)
    set_dict_attr(room_attribute_table_tuple, "$.item_explicit_info",            item_explicit_info)
    set_dict_attr(room_attribute_table_tuple, "$.layout",                        layout)
    set_dict_attr(room_attribute_table_tuple, "$.linkmic_display_type",          linkmic_display_type)
    set_dict_attr(room_attribute_table_tuple, "$.linkmic_layout",                linkmic_layout)
    set_dict_attr(room_attribute_table_tuple, "$.live_id",                       str(live_id))
    set_dict_attr(room_attribute_table_tuple, "$.live_platform_source",          live_platform_source)
    set_dict_attr(room_attribute_table_tuple, "$.live_room_mode",                live_room_mode)
    set_dict_attr(room_attribute_table_tuple, "$.live_type_audio",               live_type_audio)
    set_dict_attr(room_attribute_table_tuple, "$.live_type_linkmic",             live_type_linkmic)
    set_dict_attr(room_attribute_table_tuple, "$.live_type_normal",              live_type_normal)
    set_dict_attr(room_attribute_table_tuple, "$.live_type_official",            live_type_official)
    set_dict_attr(room_attribute_table_tuple, "$.live_type_sandbox",             live_type_sandbox)
    set_dict_attr(room_attribute_table_tuple, "$.live_type_screenshot",          live_type_screenshot)
    set_dict_attr(room_attribute_table_tuple, "$.live_type_third_party",         live_type_third_party)
    set_dict_attr(room_attribute_table_tuple, "$.live_type_vs_live",             live_type_vs_live)
    set_dict_attr(room_attribute_table_tuple, "$.live_type_vs_premiere",         live_type_vs_premiere)
    set_dict_attr(room_attribute_table_tuple, "$.admin_flag",                    admin_flag)
    set_dict_attr(room_attribute_table_tuple, "$.location",                      location)
    set_dict_attr(room_attribute_table_tuple, "$.official_channel_open_id",      official_channel_open_id)
    set_dict_attr(room_attribute_table_tuple, "$.official_channel_uid",          str(official_channel_uid))
    set_dict_attr(room_attribute_table_tuple, "$.orientation",                   orientation)
    set_dict_attr(room_attribute_table_tuple, "$.os_type",                       os_type)
    set_dict_attr(room_attribute_table_tuple, "$.owner_device_id",               str(owner_device_id))
    set_dict_attr(room_attribute_table_tuple, "$.owner_open_id",                 owner_open_id)
    set_dict_attr(room_attribute_table_tuple, "$.owner_user_id",                 str(owner_user_id))
    if start_time != 0:
      set_dict_attr(room_attribute_table_tuple, "$.start_time",                    dat.fromtimestamp(start_time))
    set_dict_attr(room_attribute_table_tuple, "$.room_layout",                   room_layout)
    set_dict_attr(room_attribute_table_tuple, "$.room_tag",                      room_tag)
    set_dict_attr(room_attribute_table_tuple, "$.scroll_config",                 scroll_config)
    set_dict_attr(room_attribute_table_tuple, "$.search_id",                     str(search_id))
    set_dict_attr(room_attribute_table_tuple, "$.sell_goods",                    sell_goods)
    set_dict_attr(room_attribute_table_tuple, "$.share_msg_style",               share_msg_style)
    set_dict_attr(room_attribute_table_tuple, "$.share_url",                     share_url)
    set_dict_attr(room_attribute_table_tuple, "$.title",                         title)
    set_dict_attr(room_attribute_table_tuple, "$.title_recommend",               title_recommend)
    set_dict_attr(room_attribute_table_tuple, "$.toutiao_cover_recommend_level", toutiao_cover_recommend_level)
    set_dict_attr(room_attribute_table_tuple, "$.toutiao_title_recommend_level", toutiao_title_recommend_level)
    set_dict_attr(room_attribute_table_tuple, "$.use_filter",                    use_filter)
    set_dict_attr(room_attribute_table_tuple, "$.user_count",                    user_count)
    set_dict_attr(room_attribute_table_tuple, "$.vertical_cover_uri",            vertical_cover_uri)
    set_dict_attr(room_attribute_table_tuple, "$.vid",                           vid)
    set_dict_attr(room_attribute_table_tuple, "$.video_feed_tag",                video_feed_tag)
    set_dict_attr(room_attribute_table_tuple, "$.visibility_range",              visibility_range)
    set_dict_attr(room_attribute_table_tuple, "$.vs_main_replay_id",             str(vs_main_replay_id))
    set_dict_attr(room_attribute_table_tuple, "$.wait_copy",                     wait_copy)
    set_dict_attr(room_attribute_table_tuple, "$.webcast_sdk_version",           str(webcast_sdk_version))

    ##
    ## 1. check is the table is exist
    ## 2. if not exist, create it
    ## 3. insert the record
    ##
    if db.is_table_exist(room_attribute_table.get_name()) is False:
      room_attribute_table.create()
    room_attribute_table.insert_record(room_attribute_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_attribute_table.get_name(), e))
    raise e

  ##
  ## RoomAdminUserIdTable
  ##
  room_admin_user_id_table = RoomAdminUserIdTable(db)
  try:
    ##
    ## +---------------------+
    ## | Field               |
    ## +---------------------+
    ## | now                 |
    ## | platform            |
    ## | room_id             |
    ## | admin_user_id_index |
    ## | admin_user_id       |
    ## +---------------------+
    ##
    room_admin_user_id_table_tuple = room_admin_user_id_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    # admin_user_id_index = None
    admin_user_ids = get_dict_attr(data, "$.data.room.admin_user_ids")
    if len(admin_user_ids) != 0:
      set_dict_attr(room_admin_user_id_table_tuple, "$.now",      now)
      set_dict_attr(room_admin_user_id_table_tuple, "$.platform", DOUYIN_PLATFORM)
      set_dict_attr(room_admin_user_id_table_tuple, "$.room_id",  str(room_id))
  
      for admin_user_id in admin_user_ids:
        # admin_user_id_index auto increment
        set_dict_attr(room_admin_user_id_table_tuple, "$.admin_user_id", str(admin_user_id))
        
        ##
        ## 1. check is the table is exist
        ## 2. if not exist, create it
        ## 3. insert the record
        ##
        if db.is_table_exist(room_admin_user_id_table.get_name()) is False:
          room_admin_user_id_table.create()
        room_admin_user_id_table.insert_record(room_admin_user_id_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_admin_user_id_table.get_name(), e))
    raise e

  ##
  ## RoomAdminUserOpenIdTable
  ##
  room_admin_user_open_id_table = RoomAdminUserOpenIdTable(db)
  try:
    ##
    ## +-----------------------+
    ## | Field                 |
    ## +-----------------------+
    ## | now                   |
    ## | platform              |
    ## | room_id               |
    ## | admin_user_open_index |
    ## | admin_user_open_id    |
    ## +-----------------------+  
    ##
    room_admin_user_open_id_table_tuple = room_admin_user_open_id_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    # admin_user_open_index = None
    admin_user_open_ids = get_dict_attr(data, "$.data.room.admin_user_open_ids")
    if len(admin_user_open_ids) != 0:
      set_dict_attr(room_admin_user_open_id_table_tuple, "$.now",      now)
      set_dict_attr(room_admin_user_open_id_table_tuple, "$.platform", DOUYIN_PLATFORM)
      set_dict_attr(room_admin_user_open_id_table_tuple, "$.room_id",  str(room_id))
      for admin_user_open_id in admin_user_open_ids:
        # admin_user_open_index auto increment
        set_dict_attr(room_admin_user_open_id_table_tuple, "$.admin_user_open_id", str(admin_user_open_id))
        
        ##
        ## 1. check is the table is exist
        ## 2. if not exist, create it
        ## 3. insert the record
        ##
        if db.is_table_exist(room_admin_user_open_id_table.get_name()) is False:
          room_admin_user_open_id_table.create()
        room_admin_user_open_id_table.insert_record(room_admin_user_open_id_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_admin_user_open_id_table.get_name(), e))
    raise e

  """
  ##
  ## RoomAssistLabelTable
  ## TBD
  ##
  room_assist_label_table = RoomAssistLabelTable(db)
  try:
    ##
    ## +--------------------+
    ## | Field              |
    ## +--------------------+
    ## | now                |
    ## | platform           |
    ## | room_id            |
    ## | assist_label_index |
    ## | assist_label       |
    ## +--------------------+
    ##
    get_logger().warning("{} TBD".format(room_assist_label_table.get_name()))
    '''
    room_assist_label_table_tuple = room_assist_label_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    # assist_label_index auto increment
    assist_label_list = get_dict_attr(data, "$.data.room.assist_label_list")
    if assist_label_list is None:
      get_logger().warning("none found assist label")
      return
    
    set_dict_attr(room_assist_label_table_tuple, "$.now",      now)
    set_dict_attr(room_assist_label_table_tuple, "$.platform", DOUYIN_PLATFORM)
    set_dict_attr(room_assist_label_table_tuple, "$.room_id",  str(room_id))
    for assist_label in assist_label_list:
      # assist_label_index auto increment
      set_dict_attr(room_assist_label_table_tuple, "$.assist_label", assist_label)
      ##
      ## 1. check is the table is exist
      ## 2. if not exist, create it
      ## 3. insert the record
      ##
      if db.is_table_exist(room_assist_label_table.get_name()) is False:
        room_assist_label_table.create()
      room_assist_label_table.insert_record(room_assist_label_table_tuple)
    '''
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_assist_label_table.get_name(), e))
    raise e

  ##
  ## RoomDecoTable
  ## TBD
  ##
  room_deco_table = RoomDecoTable(db)
  try:
    ##
    ## +------------+
    ## | Field      |
    ## +------------+
    ## | now        |
    ## | platform   |
    ## | room_id    |
    ## | deco_index |
    ## | deco       |
    ## +------------+
    ##
    get_logger().warning("{} TBD".format(room_deco_table.get_name()))
    '''
    room_deco_table_tuple = room_deco_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    # deco_index auto increment
    deco_list = get_dict_attr(data, "$.data.room.deco_list")
    if deco_list is None:
      get_logger().warning("none found in deco list")
      return    
    
    set_dict_attr(room_deco_table_tuple, "$.now",      now)
    set_dict_attr(room_deco_table_tuple, "$.platform", DOUYIN_PLATFORM)
    set_dict_attr(room_deco_table_tuple, "$.room_id",  str(room_id))
    for deco in deco_list:
      # deco_index auto increment
      set_dict_attr(room_deco_table_tuple, "$.deco", deco)

      ##
      ## 1. check is the table is exist
      ## 2. if not exist, create it
      ## 3. insert the record
      ##
      if db.is_table_exist(room_deco_table.get_name()) is False:
        room_deco_table.create()
      room_deco_table.insert_record(room_deco_table_tuple)
    '''
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_deco_table.get_name(), e))
    raise e
  
  ##
  ## RoomRealtimePlaybackQualityTable
  ## TBD
  ##
  room_realtime_playback_quality_table = RoomRealtimePlaybackQualityTable(db)
  try:
    get_logger().warning("{} TBD".format(room_realtime_playback_quality_table.get_name()))
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_realtime_playback_quality_table.get_name(), e))
    raise e
  """
  ##
  ## FansGroupAdminUserIdTable
  ##
  fans_group_admin_user_id_table = FansGroupAdminUserIdTable(db)
  try:
    ##
    ## +--------------------------------+
    ## | Field                          |
    ## +--------------------------------+
    ## | now                            |
    ## | platform                       |
    ## | room_id                        |
    ## | fans_group_admin_user_id_index |
    ## | fans_group_admin_user_id       |
    ## +--------------------------------+
    ##
    fans_group_admin_user_id_table_tuple = fans_group_admin_user_id_table.get_tuple()
    
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    # fans_group_admin_user_id_index = None
    fans_group_admin_user_ids = get_dict_attr(data, "$.data.room.fans_group_admin_user_ids")
    if len(fans_group_admin_user_ids) != 0:
      set_dict_attr(fans_group_admin_user_id_table_tuple, "$.now",      now)
      set_dict_attr(fans_group_admin_user_id_table_tuple, "$.platform", DOUYIN_PLATFORM)
      set_dict_attr(fans_group_admin_user_id_table_tuple, "$.room_id",  str(room_id))
      for fans_group_admin_user_id in fans_group_admin_user_ids:
        # set_dict_attr(fans_group_admin_user_id_table_tuple, "$.fans_group_admin_user_open_id_index", fans_group_admin_user_open_id_index)
        set_dict_attr(fans_group_admin_user_id_table_tuple, "$.fans_group_admin_user_id", str(fans_group_admin_user_id))

        if db.is_table_exist(fans_group_admin_user_id_table.get_name()) is False:
          fans_group_admin_user_id_table.create()
        fans_group_admin_user_id_table.insert_record(fans_group_admin_user_id_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(fans_group_admin_user_id_table.get_name(), e))
    raise e

  ##
  ## FansGroupAdminUserOpenIdTable
  ##
  fans_group_admin_user_open_id_table = FansGroupAdminUserOpenIdTable(db)
  try:
    ##
    ## +-------------------------------------+
    ## | Field                               |
    ## +-------------------------------------+
    ## | now                                 |
    ## | platform                            |
    ## | room_id                             |
    ## | fans_group_admin_user_open_id_index |
    ## | fans_group_admin_user_open_id       |
    ## +-------------------------------------+
    ##
    fans_group_admin_user_open_id_table_tuple = fans_group_admin_user_open_id_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    # fans_group_admin_user_open_id_index = None
    fans_group_admin_user_open_id_list = get_dict_attr(data, "$.data.room.fans_group_admin_user_open_ids")
    if len(fans_group_admin_user_open_id_list) != 0:
      set_dict_attr(fans_group_admin_user_open_id_table_tuple, "$.now",      now)
      set_dict_attr(fans_group_admin_user_open_id_table_tuple, "$.platform", DOUYIN_PLATFORM)
      set_dict_attr(fans_group_admin_user_open_id_table_tuple, "$.room_id",  str(room_id))
      for fans_group_admin_user_open_id in fans_group_admin_user_open_id_list:
        # fans_group_admin_user_open_id_index auto increment
        set_dict_attr(fans_group_admin_user_open_id_table_tuple, "$.fans_group_admin_user_open_id", str(fans_group_admin_user_open_id))
        
        if db.is_table_exist(fans_group_admin_user_open_id_table.get_name()) is False:
          fans_group_admin_user_open_id_table.create()
        fans_group_admin_user_open_id_table.insert_record(fans_group_admin_user_open_id_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(fans_group_admin_user_open_id_table.get_name(), e))
    raise e

  """
  ##
  ## RoomFilterWordTable
  ## TBD
  ##
  room_filter_word_table = RoomFilterWordTable(db)
  try:
    get_logger().warning("{} TBD".format(room_filter_word_table.get_name()))
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_filter_word_table.get_name(), e))
    raise e
  
  ##
  ## RoomLiveDistributionTable
  ## TBD
  ##
  room_live_distribution_table = RoomLiveDistributionTable(db)
  try:
    get_logger().warning("{} TBD".format(room_live_distribution_table.get_name()))
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_live_distribution_table.get_name(), e))
    raise e
  """
  ##
  ## RoomOwnerTable
  ##
  room_owner_table = RoomOwnerTable(db)
  try:
    ##
    ## +------------------------------------------+
    ## | Field                                    |
    ## +------------------------------------------+
    ## | now                                      |
    ## | platform                                 |
    ## | room_id                                  |
    ## | owner_user_id                            |
    ## | adversary_authorization_info             |
    ## | adversary_user_status                    |
    ## | age_range                                |
    ## | allow_be_located                         |
    ## | allow_find_by_contacts                   |
    ## | allow_others_download_video              |
    ## | allow_others_download_when_sharing_video |
    ## | allow_share_show_profile                 |
    ## | allow_show_in_gossip                     |
    ## | allow_show_my_action                     |
    ## | allow_strange_comment                    |
    ## | allow_unfollower_comment                 |
    ## | allow_use_linkmic                        |
    ## | authorization_info                       |
    ## | bg_img_url                               |
    ## | birthday                                 |
    ## | birthday_description                     |
    ## | birthday_valid                           |
    ## | block_status                             |
    ## | city                                     |
    ## | comment_restrict                         |
    ## | constellation                            |
    ## | consume_diamond_level                    |
    ## | create_time                              |
    ## | desensitized_nickname                    |
    ## | disable_ichat                            |
    ## | display_id                               |
    ## | enable_ichat_img                         |
    ## | exp                                      |
    ## | experience                               |
    ## | fan_ticket_count                         |
    ## | list_fans_group_url                      |
    ## | fold_stranger_chat                       |
    ## | follow_status                            |
    ## | follower_count                           |
    ## | follower_count_str                       |
    ## | following_count                          |
    ## | following_count_str                      |
    ## | invalid_follow_status                    |
    ## | follow_info_push_status                  |
    ## | follow_info_remark_name                  |
    ## | gender                                   |
    ## | hotsoon_verified                         |
    ## | hotsoon_verified_reason                  |
    ## | ichat_restrict_type                      |
    ## | id                                       |
    ## | income_share_percent                     |
    ## | is_anonymous                             |
    ## | is_follower                              |
    ## | is_following                             |
    ## | JAccreditAdvance                         |
    ## | JAccreditBasic                           |
    ## | JAccreditContent                         |
    ## | JAccreditLive                            |
    ## | level                                    |
    ## | link_mic_stats                           |
    ## | location_city                            |
    ## | modify_time                              |
    ## | mystery_man                              |
    ## | need_profile_guide                       |
    ## | nickname                                 |
    ## | pay_grade_banner                         |
    ## | pay_grade_describe                       |
    ## | pay_grade_describe_shining               |
    ## | pay_grade_level                          |
    ## | pay_grade_name                           |
    ## | pay_grade_next_diamond                   |
    ## | pay_grade_next_name                      |
    ## | pay_grade_next_privileges                |
    ## | pay_grade_now_diamond                    |
    ## | pay_diamond_bak                          |
    ## | pay_grade_score                          |
    ## | screen_chat_type                         |
    ## | this_grade_max_diamond                   |
    ## | this_grade_min_diamond                   |
    ## | total_diamond_count                      |
    ## | upgrade_need_consume                     |
    ## | pay_score                                |
    ## | pay_scores                               |
    ## | public_area_oper_freq                    |
    ## | push_comment_status                      |
    ## | push_digg                                |
    ## | push_follow                              |
    ## | push_friend_action                       |
    ## | push_ichat                               |
    ## | push_status                              |
    ## | push_video_post                          |
    ## | push_video_recommend                     |
    ## | remark_name                              |
    ## | sec_uid                                  |
    ## | secret                                   |
    ## | share_qrcode_uri                         |
    ## | short_id                                 |
    ## | signature                                |
    ## | special_id                               |
    ## | status                                   |
    ## | telephone                                |
    ## | ticket_count                             |
    ## | top_vip_no                               |
    ## | total_recharge_diamond_count             |
    ## | user_canceled                            |
    ## | user_open_id                             |
    ## | user_role                                |
    ## | verified                                 |
    ## | verified_content                         |
    ## | verified_mobile                          |
    ## | verified_reason                          |
    ## | watch_duration_month                     |
    ## | web_rid                                  |
    ## | webcast_uid                              |
    ## | with_car_management_permission           |
    ## | with_commerce_permission                 |
    ## | with_fusion_shop_entry                   |
    ## +------------------------------------------+
    ##
    room_owner_table_tuple = room_owner_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    owner_user_id                            = get_dict_attr(data, "$.data.room.owner_user_id")
    adversary_authorization_info             = get_dict_attr(data, "$.data.room.owner.adversary_authorization_info")
    adversary_user_status                    = get_dict_attr(data, "$.data.room.owner.adversary_user_status")
    age_range                                = get_dict_attr(data, "$.data.room.owner.age_range")
    allow_be_located                         = get_dict_attr(data, "$.data.room.owner.allow_be_located")
    allow_find_by_contacts                   = get_dict_attr(data, "$.data.room.owner.allow_find_by_contacts")
    allow_others_download_video              = get_dict_attr(data, "$.data.room.owner.allow_others_download_video")
    allow_others_download_when_sharing_video = get_dict_attr(data, "$.data.room.owner.allow_others_download_when_sharing_video")
    allow_share_show_profile                 = get_dict_attr(data, "$.data.room.owner.allow_share_show_profile")
    allow_show_in_gossip                     = get_dict_attr(data, "$.data.room.owner.allow_show_in_gossip")
    allow_show_my_action                     = get_dict_attr(data, "$.data.room.owner.allow_show_my_action")
    allow_strange_comment                    = get_dict_attr(data, "$.data.room.owner.allow_strange_comment")
    allow_unfollower_comment                 = get_dict_attr(data, "$.data.room.owner.allow_unfollower_comment")
    allow_use_linkmic                        = get_dict_attr(data, "$.data.room.owner.allow_use_linkmic")
    authorization_info                       = get_dict_attr(data, "$.data.room.owner.authorization_info")
    bg_img_url                               = get_dict_attr(data, "$.data.room.owner.bg_img_url")
    birthday                                 = get_dict_attr(data, "$.data.room.owner.birthday")
    birthday_description                     = get_dict_attr(data, "$.data.room.owner.birthday_description")
    birthday_valid                           = get_dict_attr(data, "$.data.room.owner.birthday_valid")
    block_status                             = get_dict_attr(data, "$.data.room.owner.block_status")
    city                                     = get_dict_attr(data, "$.data.room.owner.city")
    comment_restrict                         = get_dict_attr(data, "$.data.room.owner.comment_restrict")
    constellation                            = get_dict_attr(data, "$.data.room.owner.constellation")
    consume_diamond_level                    = get_dict_attr(data, "$.data.room.owner.consume_diamond_level")
    create_time                              = get_dict_attr(data, "$.data.room.owner.create_time")
    desensitized_nickname                    = get_dict_attr(data, "$.data.room.owner.desensitized_nickname")
    disable_ichat                            = get_dict_attr(data, "$.data.room.owner.disable_ichat")
    display_id                               = get_dict_attr(data, "$.data.room.owner.display_id")
    enable_ichat_img                         = get_dict_attr(data, "$.data.room.owner.enable_ichat_img")
    exp                                      = get_dict_attr(data, "$.data.room.owner.exp")
    experience                               = get_dict_attr(data, "$.data.room.owner.experience")
    fan_ticket_count                         = get_dict_attr(data, "$.data.room.owner.fan_ticket_count")
    list_fans_group_url                      = get_dict_attr(data, "$.data.room.owner.fans_group_info.list_fans_group_url")
    fold_stranger_chat                       = get_dict_attr(data, "$.data.room.owner.fold_stranger_chat")
    follow_status                            = get_dict_attr(data, "$.data.room.owner.follow_info.follow_status")
    follower_count                           = get_dict_attr(data, "$.data.room.owner.follow_info.follower_count")
    follower_count_str                       = get_dict_attr(data, "$.data.room.owner.follow_info.follower_count_str")
    following_count                          = get_dict_attr(data, "$.data.room.owner.follow_info.following_count")
    following_count_str                      = get_dict_attr(data, "$.data.room.owner.follow_info.following_count_str")
    invalid_follow_status                    = get_dict_attr(data, "$.data.room.owner.follow_info.invalid_follow_status")
    follow_info_push_status                  = get_dict_attr(data, "$.data.room.owner.follow_info.push_status")
    follow_info_remark_name                  = get_dict_attr(data, "$.data.room.owner.follow_info.remark_name")
    gender                                   = get_dict_attr(data, "$.data.room.owner.follow_info.following_count_str")
    hotsoon_verified                         = get_dict_attr(data, "$.data.room.owner.hotsoon_verified")
    hotsoon_verified_reason                  = get_dict_attr(data, "$.data.room.owner.hotsoon_verified_reason")
    ichat_restrict_type                      = get_dict_attr(data, "$.data.room.owner.ichat_restrict_type")
    id                                       = get_dict_attr(data, "$.data.room.owner.id")
    income_share_percent                     = get_dict_attr(data, "$.data.room.owner.income_share_percent")
    is_anonymous                             = get_dict_attr(data, "$.data.room.owner.is_anonymous")
    is_follower                              = get_dict_attr(data, "$.data.room.owner.is_follower")
    is_following                             = get_dict_attr(data, "$.data.room.owner.is_following")
    JAccreditAdvance                         = get_dict_attr(data, "$.data.room.owner.j_accredit_info.JAccreditAdvance")
    JAccreditBasic                           = get_dict_attr(data, "$.data.room.owner.j_accredit_info.JAccreditBasic")
    JAccreditContent                         = get_dict_attr(data, "$.data.room.owner.j_accredit_info.JAccreditContent")
    JAccreditLive                            = get_dict_attr(data, "$.data.room.owner.j_accredit_info.JAccreditLive")
    level                                    = get_dict_attr(data, "$.data.room.owner.level")
    link_mic_stats                           = get_dict_attr(data, "$.data.room.owner.link_mic_stats")
    location_city                            = get_dict_attr(data, "$.data.room.owner.location_city")
    modify_time                              = get_dict_attr(data, "$.data.room.owner.modify_time")
    mystery_man                              = get_dict_attr(data, "$.data.room.owner.mystery_man")
    need_profile_guide                       = get_dict_attr(data, "$.data.room.owner.need_profile_guide")
    nickname                                 = get_dict_attr(data, "$.data.room.owner.nickname")
    pay_grade_banner                         = get_dict_attr(data, "$.data.room.owner.pay_grade.grade_banner")
    pay_grade_describe                       = get_dict_attr(data, "$.data.room.owner.pay_grade.grade_describe")
    pay_grade_describe_shining               = get_dict_attr(data, "$.data.room.owner.pay_grade.grade_describe_shining")
    pay_grade_level                          = get_dict_attr(data, "$.data.room.owner.pay_grade.level")
    pay_grade_name                           = get_dict_attr(data, "$.data.room.owner.pay_grade.name")
    pay_grade_next_diamond                   = get_dict_attr(data, "$.data.room.owner.pay_grade.next_diamond")
    pay_grade_next_name                      = get_dict_attr(data, "$.data.room.owner.pay_grade.next_name")
    pay_grade_next_privileges                = get_dict_attr(data, "$.data.room.owner.pay_grade.next_privileges")
    pay_grade_now_diamond                    = get_dict_attr(data, "$.data.room.owner.pay_grade.now_diamond")
    pay_diamond_bak                          = get_dict_attr(data, "$.data.room.owner.pay_grade.pay_diamond_bak")
    pay_grade_score                          = get_dict_attr(data, "$.data.room.owner.pay_grade.score")
    screen_chat_type                         = get_dict_attr(data, "$.data.room.owner.pay_grade.screen_chat_type")
    this_grade_max_diamond                   = get_dict_attr(data, "$.data.room.owner.pay_grade.this_grade_max_diamond")
    this_grade_min_diamond                   = get_dict_attr(data, "$.data.room.owner.pay_grade.this_grade_min_diamond")
    total_diamond_count                      = get_dict_attr(data, "$.data.room.owner.pay_grade.total_diamond_count")
    upgrade_need_consume                     = get_dict_attr(data, "$.data.room.owner.pay_grade.upgrade_need_consume")
    pay_score                                = get_dict_attr(data, "$.data.room.owner.pay_score")
    pay_scores                               = get_dict_attr(data, "$.data.room.owner.pay_scores")
    public_area_oper_freq                    = get_dict_attr(data, "$.data.room.owner.public_area_oper_freq")
    push_comment_status                      = get_dict_attr(data, "$.data.room.owner.push_comment_status")
    push_digg                                = get_dict_attr(data, "$.data.room.owner.push_digg")
    push_follow                              = get_dict_attr(data, "$.data.room.owner.push_follow")
    push_friend_action                       = get_dict_attr(data, "$.data.room.owner.push_friend_action")
    push_ichat                               = get_dict_attr(data, "$.data.room.owner.push_ichat")
    push_status                              = get_dict_attr(data, "$.data.room.owner.push_status")
    push_video_post                          = get_dict_attr(data, "$.data.room.owner.push_video_post")
    push_video_recommend                     = get_dict_attr(data, "$.data.room.owner.push_video_recommend")
    remark_name                              = get_dict_attr(data, "$.data.room.owner.remark_name")
    sec_uid                                  = get_dict_attr(data, "$.data.room.owner.sec_uid")
    secret                                   = get_dict_attr(data, "$.data.room.owner.secret")
    share_qrcode_uri                         = get_dict_attr(data, "$.data.room.owner.share_qrcode_uri")
    short_id                                 = get_dict_attr(data, "$.data.room.owner.short_id")
    signature                                = get_dict_attr(data, "$.data.room.owner.signature")
    special_id                               = get_dict_attr(data, "$.data.room.owner.special_id")
    status                                   = get_dict_attr(data, "$.data.room.owner.status")
    telephone                                = get_dict_attr(data, "$.data.room.owner.telephone")
    ticket_count                             = get_dict_attr(data, "$.data.room.owner.ticket_count")
    top_vip_no                               = get_dict_attr(data, "$.data.room.owner.top_vip_no")
    total_recharge_diamond_count             = get_dict_attr(data, "$.data.room.owner.total_recharge_diamond_count")
    user_canceled                            = get_dict_attr(data, "$.data.room.owner.user_canceled")
    user_open_id                             = get_dict_attr(data, "$.data.room.owner.user_open_id")
    user_role                                = get_dict_attr(data, "$.data.room.owner.user_role")
    verified                                 = get_dict_attr(data, "$.data.room.owner.verified")
    verified_content                         = get_dict_attr(data, "$.data.room.owner.verified_content")
    verified_mobile                          = get_dict_attr(data, "$.data.room.owner.verified_mobile")
    verified_reason                          = get_dict_attr(data, "$.data.room.owner.verified_reason")
    watch_duration_month                     = get_dict_attr(data, "$.data.room.owner.watch_duration_month")
    web_rid                                  = get_dict_attr(data, "$.data.room.owner.web_rid")
    webcast_uid                              = get_dict_attr(data, "$.data.room.owner.webcast_uid")
    with_car_management_permission           = get_dict_attr(data, "$.data.room.owner.with_car_management_permission")
    with_commerce_permission                 = get_dict_attr(data, "$.data.room.owner.with_commerce_permission")
    with_fusion_shop_entry                   = get_dict_attr(data, "$.data.room.owner.with_fusion_shop_entry")
    
    set_dict_attr(room_owner_table_tuple, "$.now",                                      now)
    set_dict_attr(room_owner_table_tuple, "$.platform",                                 DOUYIN_PLATFORM)
    set_dict_attr(room_owner_table_tuple, "$.room_id",                                  str(room_id))
    set_dict_attr(room_owner_table_tuple, "$.owner_user_id",                            str(owner_user_id))
    set_dict_attr(room_owner_table_tuple, "$.adversary_authorization_info",             adversary_authorization_info)
    set_dict_attr(room_owner_table_tuple, "$.adversary_user_status",                    adversary_user_status)
    set_dict_attr(room_owner_table_tuple, "$.age_range",                                age_range)
    set_dict_attr(room_owner_table_tuple, "$.allow_be_located",                         allow_be_located)
    set_dict_attr(room_owner_table_tuple, "$.allow_find_by_contacts",                   allow_find_by_contacts)
    set_dict_attr(room_owner_table_tuple, "$.allow_others_download_video",              allow_others_download_video)
    set_dict_attr(room_owner_table_tuple, "$.allow_others_download_when_sharing_video", allow_others_download_when_sharing_video)
    set_dict_attr(room_owner_table_tuple, "$.allow_share_show_profile",                 allow_share_show_profile)
    set_dict_attr(room_owner_table_tuple, "$.allow_show_in_gossip",                     allow_show_in_gossip)
    set_dict_attr(room_owner_table_tuple, "$.allow_show_my_action",                     allow_show_my_action)
    set_dict_attr(room_owner_table_tuple, "$.allow_strange_comment",                    allow_strange_comment)
    set_dict_attr(room_owner_table_tuple, "$.allow_unfollower_comment",                 allow_unfollower_comment)
    set_dict_attr(room_owner_table_tuple, "$.allow_use_linkmic",                        allow_use_linkmic)
    set_dict_attr(room_owner_table_tuple, "$.authorization_info",                       authorization_info)
    set_dict_attr(room_owner_table_tuple, "$.bg_img_url",                               bg_img_url)
    if birthday != 0:
      set_dict_attr(room_owner_table_tuple, "$.birthday",                                 birthday)
    set_dict_attr(room_owner_table_tuple, "$.birthday_description",                     birthday_description)
    set_dict_attr(room_owner_table_tuple, "$.birthday_valid",                           birthday_valid)
    set_dict_attr(room_owner_table_tuple, "$.block_status",                             block_status)
    set_dict_attr(room_owner_table_tuple, "$.city",                                     city)
    set_dict_attr(room_owner_table_tuple, "$.comment_restrict",                         comment_restrict)
    set_dict_attr(room_owner_table_tuple, "$.constellation",                            constellation)
    set_dict_attr(room_owner_table_tuple, "$.consume_diamond_level",                    consume_diamond_level)
    if create_time != 0:
      set_dict_attr(room_owner_table_tuple, "$.create_time",                              dat.fromtimestamp(create_time))
    set_dict_attr(room_owner_table_tuple, "$.desensitized_nickname",                    desensitized_nickname)
    set_dict_attr(room_owner_table_tuple, "$.disable_ichat",                            disable_ichat)
    set_dict_attr(room_owner_table_tuple, "$.display_id",                               display_id)
    set_dict_attr(room_owner_table_tuple, "$.enable_ichat_img",                         enable_ichat_img)
    set_dict_attr(room_owner_table_tuple, "$.exp",                                      exp)
    set_dict_attr(room_owner_table_tuple, "$.experience",                               experience)
    set_dict_attr(room_owner_table_tuple, "$.fan_ticket_count",                         fan_ticket_count)
    set_dict_attr(room_owner_table_tuple, "$.list_fans_group_url",                      list_fans_group_url)
    set_dict_attr(room_owner_table_tuple, "$.fold_stranger_chat",                       fold_stranger_chat)
    set_dict_attr(room_owner_table_tuple, "$.follow_status",                            follow_status)
    set_dict_attr(room_owner_table_tuple, "$.follower_count",                           follower_count)
    set_dict_attr(room_owner_table_tuple, "$.follower_count_str",                       follower_count_str)
    set_dict_attr(room_owner_table_tuple, "$.following_count",                          following_count)
    set_dict_attr(room_owner_table_tuple, "$.following_count_str",                      following_count_str)
    set_dict_attr(room_owner_table_tuple, "$.invalid_follow_status",                    invalid_follow_status)
    set_dict_attr(room_owner_table_tuple, "$.follow_info_push_status",                  follow_info_push_status)
    set_dict_attr(room_owner_table_tuple, "$.follow_info_remark_name",                  follow_info_remark_name)
    set_dict_attr(room_owner_table_tuple, "$.gender",                                   gender)
    set_dict_attr(room_owner_table_tuple, "$.hotsoon_verified",                         hotsoon_verified)
    set_dict_attr(room_owner_table_tuple, "$.hotsoon_verified_reason",                  hotsoon_verified_reason)
    set_dict_attr(room_owner_table_tuple, "$.ichat_restrict_type",                      ichat_restrict_type)
    set_dict_attr(room_owner_table_tuple, "$.id",                                       str(id))
    set_dict_attr(room_owner_table_tuple, "$.income_share_percent",                     income_share_percent)
    set_dict_attr(room_owner_table_tuple, "$.is_anonymous",                             is_anonymous)
    set_dict_attr(room_owner_table_tuple, "$.is_follower",                              is_follower)
    set_dict_attr(room_owner_table_tuple, "$.is_following",                             is_following)
    set_dict_attr(room_owner_table_tuple, "$.JAccreditAdvance",                         JAccreditAdvance)
    set_dict_attr(room_owner_table_tuple, "$.JAccreditBasic",                           JAccreditBasic)
    set_dict_attr(room_owner_table_tuple, "$.JAccreditContent",                         JAccreditContent)
    set_dict_attr(room_owner_table_tuple, "$.JAccreditLive",                            JAccreditLive)
    set_dict_attr(room_owner_table_tuple, "$.level",                                    level)
    set_dict_attr(room_owner_table_tuple, "$.link_mic_stats",                           link_mic_stats)
    set_dict_attr(room_owner_table_tuple, "$.location_city",                            location_city)
    if modify_time != 0:
      set_dict_attr(room_owner_table_tuple, "$.modify_time",                              dat.fromtimestamp(modify_time))
    set_dict_attr(room_owner_table_tuple, "$.mystery_man",                              mystery_man)
    set_dict_attr(room_owner_table_tuple, "$.need_profile_guide",                       need_profile_guide)
    set_dict_attr(room_owner_table_tuple, "$.nickname",                                 nickname)
    set_dict_attr(room_owner_table_tuple, "$.pay_grade_banner",                         pay_grade_banner)
    set_dict_attr(room_owner_table_tuple, "$.pay_grade_describe",                       pay_grade_describe)
    set_dict_attr(room_owner_table_tuple, "$.pay_grade_describe_shining",               pay_grade_describe_shining)
    set_dict_attr(room_owner_table_tuple, "$.pay_grade_level",                          pay_grade_level)
    set_dict_attr(room_owner_table_tuple, "$.pay_grade_name",                           pay_grade_name)
    set_dict_attr(room_owner_table_tuple, "$.pay_grade_next_diamond",                   pay_grade_next_diamond)
    set_dict_attr(room_owner_table_tuple, "$.pay_grade_next_name",                      pay_grade_next_name)
    set_dict_attr(room_owner_table_tuple, "$.pay_grade_next_privileges",                pay_grade_next_privileges)
    set_dict_attr(room_owner_table_tuple, "$.pay_grade_now_diamond",                    pay_grade_now_diamond)
    set_dict_attr(room_owner_table_tuple, "$.pay_diamond_bak",                          pay_diamond_bak)
    set_dict_attr(room_owner_table_tuple, "$.pay_grade_score",                          pay_grade_score)
    set_dict_attr(room_owner_table_tuple, "$.screen_chat_type",                         screen_chat_type)
    set_dict_attr(room_owner_table_tuple, "$.this_grade_max_diamond",                   this_grade_max_diamond)
    set_dict_attr(room_owner_table_tuple, "$.this_grade_min_diamond",                   this_grade_min_diamond)
    set_dict_attr(room_owner_table_tuple, "$.total_diamond_count",                      total_diamond_count)
    set_dict_attr(room_owner_table_tuple, "$.upgrade_need_consume",                     upgrade_need_consume)
    set_dict_attr(room_owner_table_tuple, "$.pay_score",                                pay_score)
    set_dict_attr(room_owner_table_tuple, "$.pay_scores",                               pay_scores)
    set_dict_attr(room_owner_table_tuple, "$.public_area_oper_freq",                    public_area_oper_freq)
    set_dict_attr(room_owner_table_tuple, "$.push_comment_status",                      push_comment_status)
    set_dict_attr(room_owner_table_tuple, "$.push_digg",                                push_digg)
    set_dict_attr(room_owner_table_tuple, "$.push_follow",                              push_follow)
    set_dict_attr(room_owner_table_tuple, "$.push_friend_action",                       push_friend_action)
    set_dict_attr(room_owner_table_tuple, "$.push_ichat",                               push_ichat)
    set_dict_attr(room_owner_table_tuple, "$.push_status",                              push_status)
    set_dict_attr(room_owner_table_tuple, "$.push_video_post",                          push_video_post)
    set_dict_attr(room_owner_table_tuple, "$.push_video_recommend",                     push_video_recommend)
    set_dict_attr(room_owner_table_tuple, "$.remark_name",                              remark_name)
    set_dict_attr(room_owner_table_tuple, "$.sec_uid",                                  sec_uid)
    set_dict_attr(room_owner_table_tuple, "$.secret",                                   secret)
    set_dict_attr(room_owner_table_tuple, "$.share_qrcode_uri",                         share_qrcode_uri)
    set_dict_attr(room_owner_table_tuple, "$.short_id",                                 str(short_id))
    set_dict_attr(room_owner_table_tuple, "$.signature",                                signature)
    set_dict_attr(room_owner_table_tuple, "$.special_id",                               special_id)
    set_dict_attr(room_owner_table_tuple, "$.status",                                   status)
    set_dict_attr(room_owner_table_tuple, "$.telephone",                                telephone)
    set_dict_attr(room_owner_table_tuple, "$.ticket_count",                             ticket_count)
    set_dict_attr(room_owner_table_tuple, "$.top_vip_no",                               top_vip_no)
    set_dict_attr(room_owner_table_tuple, "$.total_recharge_diamond_count",             total_recharge_diamond_count)
    set_dict_attr(room_owner_table_tuple, "$.user_canceled",                            user_canceled)
    set_dict_attr(room_owner_table_tuple, "$.user_open_id",                             user_open_id)
    set_dict_attr(room_owner_table_tuple, "$.user_role",                                user_role)
    set_dict_attr(room_owner_table_tuple, "$.verified",                                 verified)
    set_dict_attr(room_owner_table_tuple, "$.verified_content",                         verified_content)
    set_dict_attr(room_owner_table_tuple, "$.verified_mobile",                          verified_mobile)
    set_dict_attr(room_owner_table_tuple, "$.verified_reason",                          verified_reason)
    set_dict_attr(room_owner_table_tuple, "$.watch_duration_month",                     watch_duration_month)
    set_dict_attr(room_owner_table_tuple, "$.web_rid",                                  web_rid)
    set_dict_attr(room_owner_table_tuple, "$.webcast_uid",                              webcast_uid)
    set_dict_attr(room_owner_table_tuple, "$.with_car_management_permission",           with_car_management_permission)
    set_dict_attr(room_owner_table_tuple, "$.with_commerce_permission",                 with_commerce_permission)
    set_dict_attr(room_owner_table_tuple, "$.with_fusion_shop_entry",                   with_fusion_shop_entry)

    if db.is_table_exist(room_owner_table.get_name()) is False:
      room_owner_table.create()
    room_owner_table.insert_record(room_owner_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_owner_table.get_name(), e))
    raise e

  """
  ##
  ## BadgeImageTable
  ## TODO: handle auto_increment primary key
  ##
  badge_image_table = BadgeImageTable(db)
  try:
    ##
    ## +-------------------+
    ## | Field             |
    ## +-------------------+
    ## | badge_image_index |
    ## | label             |
    ## | uri               |
    ## +-------------------+
    ##
    badge_image_table_tuple = badge_image_table.get_tuple()
    # badge_image_index auto increment
    # TODO: label
    uri     = get_dict_attr(data, "$.data.room.badge_image.uri")
    
    # badge_image_index auto increment
    set_dict_attr(badge_image_table_tuple, "$.version",           version)
    set_dict_attr(badge_image_table_tuple, "$.uri",               uri)
    
    if db.is_table_exist(badge_image_table.get_name()) is False:
      badge_image_table.create()
    badge_image_table.insert_record(badge_image_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(badge_image_table.get_name(), e))
    raise e
  """
  
  """
  ##
  ## CommerceWebcastConfigIdTable
  ## TBD
  ##
  commerce_webcast_config_id_table = CommerceWebcastConfigIdTable(db)
  try:
    get_logger().warning("{} TBD".format(commerce_webcast_config_id_table.get_name()))
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(commerce_webcast_config_id_table.get_name(), e))
    raise e
  """
  ##
  ## FansClubTable
  ##
  fans_club_table = FansClubTable(db)
  try:
    ##
    ## +-----------------------+
    ## | Field                 |
    ## +-----------------------+
    ## | now                   |
    ## | platform              |
    ## | room_id               |
    ## | owner_user_id         |
    ## | anchor_id             |
    ## | anchor_open_id        |
    ## | badge_type            |
    ## | badge_title           |
    ## | club_name             |
    ## | guard_expired_time    |
    ## | level                 |
    ## | user_fans_club_status |
    ## | user_guard_status     |
    ## | prefer_data           |
    ## +-----------------------+
    ##
    fans_club_table_tuple = fans_club_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    owner_user_id          = get_dict_attr(data, "$.data.room.owner_user_id")
    anchor_id              = get_dict_attr(data, "$.data.room.owner.fans_club.data.anchor_id")
    anchor_open_id         = get_dict_attr(data, "$.data.room.owner.fans_club.data.anchor_open_id")
    badge_type             = get_dict_attr(data, "$.data.room.owner.fans_club.data.badge_type")
    badge_title            = get_dict_attr(data, "$.data.room.owner.fans_club.data.badge.title")
    club_name              = get_dict_attr(data, "$.data.room.owner.fans_club.data.club_name")
    guard_expired_time     = get_dict_attr(data, "$.data.room.owner.fans_club.data.guard_expired_time")
    level                  = get_dict_attr(data, "$.data.room.owner.fans_club.data.level")
    user_fans_club_status  = get_dict_attr(data, "$.data.room.owner.fans_club.data.user_fans_club_status")
    user_guard_status      = get_dict_attr(data, "$.data.room.owner.fans_club.data.user_guard_status")
    prefer_data            = get_dict_attr(data, "$.data.room.owner.fans_club.prefer_data")
  
    set_dict_attr(fans_club_table_tuple, "$.now",                                      now)
    set_dict_attr(fans_club_table_tuple, "$.platform",                                 DOUYIN_PLATFORM)
    set_dict_attr(fans_club_table_tuple, "$.room_id",                                  str(room_id))
    set_dict_attr(fans_club_table_tuple, "$.owner_user_id",                            str(owner_user_id))
    set_dict_attr(fans_club_table_tuple, "$.anchor_id",                                str(anchor_id))
    set_dict_attr(fans_club_table_tuple, "$.anchor_open_id",                           anchor_open_id)
    set_dict_attr(fans_club_table_tuple, "$.badge_type",                               badge_type)
    set_dict_attr(fans_club_table_tuple, "$.badge_title",                              badge_title)
    set_dict_attr(fans_club_table_tuple, "$.club_name",                                club_name)
    if guard_expired_time != 0:
      set_dict_attr(fans_club_table_tuple, "$.guard_expired_time",                       dat.fromtimestamp(guard_expired_time))
    set_dict_attr(fans_club_table_tuple, "$.level",                                    level)
    set_dict_attr(fans_club_table_tuple, "$.user_fans_club_status",                    user_fans_club_status)
    set_dict_attr(fans_club_table_tuple, "$.user_guard_status",                        user_guard_status)
    set_dict_attr(fans_club_table_tuple, "$.prefer_data",                              json.dumps(prefer_data))

    if db.is_table_exist(fans_club_table.get_name()) is False:
      fans_club_table.create()
    fans_club_table.insert_record(fans_club_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(fans_club_table.get_name(), e))
    raise e

  ##
  ## FansClubAvailableGiftIdTable
  ##
  fans_club_available_gift_id_table = FansClubAvailableGiftIdTable(db)
  try:
    ##
    ## +----------------------+
    ## | Field                |
    ## +----------------------+
    ## | now                  |
    ## | platform             |
    ## | room_id              |
    ## | owner_user_id        |
    ## | anchor_id            |
    ## | available_gift_index |
    ## | available_gift_id    |
    ## +----------------------+
    ##
    fans_club_available_gift_id_table_tuple = fans_club_available_gift_id_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    owner_user_id          = get_dict_attr(data, "$.data.room.owner_user_id")
    anchor_id              = get_dict_attr(data, "$.data.room.owner.fans_club.data.anchor_id")
    available_gift_ids     = get_dict_attr(data, "$.data.room.owner.fans_club.data.available_gift_ids")
    if len(available_gift_ids) != 0:
      set_dict_attr(fans_club_available_gift_id_table_tuple, "$.now",                                      now)
      set_dict_attr(fans_club_available_gift_id_table_tuple, "$.platform",                                 DOUYIN_PLATFORM)
      set_dict_attr(fans_club_available_gift_id_table_tuple, "$.room_id",                                  str(room_id))
      set_dict_attr(fans_club_available_gift_id_table_tuple, "$.owner_user_id",                            str(owner_user_id))
      set_dict_attr(fans_club_available_gift_id_table_tuple, "$.anchor_id",                                str(anchor_id))
      for available_gift_id in available_gift_ids:
        # available_gift_index auto increment
        set_dict_attr(fans_club_available_gift_id_table_tuple, "$.available_gift_id",                      str(available_gift_id))
  
        if db.is_table_exist(fans_club_available_gift_id_table.get_name()) is False:
          fans_club_available_gift_id_table.create()
        fans_club_available_gift_id_table.insert_record(fans_club_available_gift_id_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(fans_club_available_gift_id_table.get_name(), e))
    raise e
  """
  ##
  ## FansClubBadgeIconTable
  ## TODO: handle multiple icon url
  ##
  fans_club_badge_icon_table = FansClubBadgeIconTable(db)
  try:
    ##
    ## +---------------+
    ## | Field         |
    ## +---------------+
    ## | now           |
    ## | platform      |
    ## | room_id       |
    ## | owner_user_id |
    ## | anchor_id     |
    ## | icon_index    |
    ## | icon_uri      |
    ## +---------------+
    ##
    fans_club_badge_icon_table_tuple = fans_club_badge_icon_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    owner_user_id          = get_dict_attr(data, "$.data.room.owner_user_id")
    anchor_id              = get_dict_attr(data, "$.data.room.owner.fans_club.data.anchor_id")
    # icon_index auto increment
    icon_uri               = get_dict_attr(data, "$.data.room.owner.fans_club.data.badge.icons.'0'.uri")
  
    set_dict_attr(fans_club_badge_icon_table_tuple, "$.now",                                      now)
    set_dict_attr(fans_club_badge_icon_table_tuple, "$.platform",                                 DOUYIN_PLATFORM)
    set_dict_attr(fans_club_badge_icon_table_tuple, "$.room_id",                                  str(room_id))
    set_dict_attr(fans_club_badge_icon_table_tuple, "$.owner_user_id",                            str(owner_user_id))
    set_dict_attr(fans_club_badge_icon_table_tuple, "$.anchor_id",                                str(anchor_id))
    set_dict_attr(fans_club_badge_icon_table_tuple, "$.icon_uri",                                 icon_uri)
    
    if db.is_table_exist(fans_club_badge_icon_table.get_name()) is False:
      fans_club_badge_icon_table.create()
    fans_club_badge_icon_table.insert_record(fans_club_badge_icon_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(fans_club_badge_icon_table.get_name(), e))
    raise e
  """

  """
  ##
  ## MediaBadgeImageTable
  ## TBD
  ##
  media_badge_image_table = MediaBadgeImageTable(db)
  try:
    get_logger().warning("{} TBD".format(media_badge_image_table.get_name()))
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(media_badge_image_table.get_name(), e))
    raise e

  ##
  ## NewRealTimeIconTable
  ## TBD
  ##
  new_real_time_icon_table = NewRealTimeIconTable(db)
  try:
    get_logger().warning("{} TBD".format(new_real_time_icon_table.get_name()))
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(new_real_time_icon_table.get_name(), e))
    raise e
  """
  ##
  ## PayGradeIconTable
  ## TBD
  ## 
  pay_grade_icon_table = PayGradeIconTable(db)
  try:
    ##
    ## +----------------------+
    ## | Field                |
    ## +----------------------+
    ## | now                  |
    ## | platform             |
    ## | room_id              |
    ## | owner_user_id        |
    ## | pay_grade_icon_index |
    ## | pay_grade_icon       |
    ## +----------------------+
    ##
    pass
    """
    pay_grade_icon_table_tuple = pay_grade_icon_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    owner_user_id = get_dict_attr(data, "$.data.room.owner.user_id")
    # pay_grade_icon_index
    pay_grade_icon_list = get_dict_attr(data, "$.data.room.owner.pay_grade.grade_icon_list")
    if pay_grade_icon_list is None:
      return
    
    set_dict_attr(pay_grade_icon_table_tuple, "$.now",           now)
    set_dict_attr(pay_grade_icon_table_tuple, "$.platform",      DOUYIN_PLATFORM)
    set_dict_attr(pay_grade_icon_table_tuple, "$.room_id",       room_id)
    set_dict_attr(pay_grade_icon_table_tuple, "$.owner_user_id", owner_user_id)
    for pay_grade_icon in pay_grade_icon_list:
      # set_dict_attr(pay_grade_icon_table_tuple, "$.pay_grade_icon_index", pay_grade_icon_index)
      set_dict_attr(pay_grade_icon_table_tuple, "$.pay_grade_icon",       pay_grade_icon)
      
      if db.is_table_exist(pay_grade_icon_table.get_name()) is False:
        pay_grade_icon_table.create()
      pay_grade_icon_table.insert_record(pay_grade_icon_table_tuple)
    """
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(pay_grade_icon_table.get_name(), e))
    raise e
  """
  ##
  ## RoomOwnerRealTimeIconTable
  ## TBD
  ##
  room_owner_real_time_icon_table = RoomOwnerRealTimeIconTable(db)
  try:
    get_logger().warning("{} TBD".format(room_owner_real_time_icon_table.get_name()))
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_owner_real_time_icon_table.get_name(), e))
    raise e
  """
  ##
  ## RoomSubscribeTable
  ##
  room_subscribe_table = RoomSubscribeTable(db)
  try:
    ##
    ## +---------------+
    ## | Field         |
    ## +---------------+
    ## | now           |
    ## | platform      |
    ## | room_id       |
    ## | owner_user_id |
    ## | buy_type      |
    ## | identity_type |
    ## | is_member     |
    ## | level         |
    ## | open          |
    ## +---------------+
    ##
    room_subscribe_table_tuple = room_subscribe_table.get_tuple()
    # now             = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id         = get_dict_attr(data, "$.data.room.id")
    owner_user_id     = get_dict_attr(data, "$.data.room.owner_user_id")
    buy_type          = get_dict_attr(data, "$.data.room.owner.subscribe.buy_type")
    identity_type     = get_dict_attr(data, "$.data.room.owner.subscribe.identity_type")
    is_member         = get_dict_attr(data, "$.data.room.owner.subscribe.is_member")
    level             = get_dict_attr(data, "$.data.room.owner.subscribe.level")
    open              = get_dict_attr(data, "$.data.room.owner.subscribe.open")
    
    set_dict_attr(room_subscribe_table_tuple, "$.now",           now)
    set_dict_attr(room_subscribe_table_tuple, "$.platform",      DOUYIN_PLATFORM)
    set_dict_attr(room_subscribe_table_tuple, "$.room_id",       str(room_id))
    set_dict_attr(room_subscribe_table_tuple, "$.owner_user_id", str(owner_user_id))
    set_dict_attr(room_subscribe_table_tuple, "$.buy_type",      buy_type)
    set_dict_attr(room_subscribe_table_tuple, "$.identity_type", identity_type)
    set_dict_attr(room_subscribe_table_tuple, "$.is_member",     is_member)
    set_dict_attr(room_subscribe_table_tuple, "$.level",         level)
    set_dict_attr(room_subscribe_table_tuple, "$.open",          open)

    ##
    ## 1. check is the table is exist
    ## 2. if not exist, create it
    ## 3. insert the record
    ##
    if db.is_table_exist(room_subscribe_table.get_name()) is False:
      room_subscribe_table.create()
    room_subscribe_table.insert_record(room_subscribe_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_subscribe_table.get_name(), e))
    raise e


  """
  ##
  ## RoomOwnerTopFansTable
  ## TBD
  ##
  room_owner_top_fans_table = RoomOwnerTopFansTable(db)
  try:
    get_logger().warning("{} TBD".format(room_owner_top_fans_table.get_name()))
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_owner_top_fans_table.get_name(), e))
    raise e
  """
  ##
  ## RoomOwnerUserAttrTable
  ##
  room_owner_user_attr_table = RoomOwnerUserAttrTable(db)
  try:
    ##
    ## +----------------+
    ## | Field          |
    ## +----------------+
    ## | now            |
    ## | platform       |
    ## | room_id        |
    ## | owner_user_id  |
    ## | is_admin       |
    ## | is_muted       |
    ## | is_super_admin |
    ## +----------------+
    ##
    room_owner_user_attr_table_tuple = room_owner_user_attr_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    owner_user_id     = get_dict_attr(data, "$.data.room.owner_user_id")
    is_admin          = get_dict_attr(data, "$.data.room.owner.user_attr.is_admin")
    is_muted          = get_dict_attr(data, "$.data.room.owner.user_attr.is_muted")
    is_super_admin    = get_dict_attr(data, "$.data.room.owner.user_attr.is_super_admin")
    
    set_dict_attr(room_owner_user_attr_table_tuple, "$.now",                                      now)
    set_dict_attr(room_owner_user_attr_table_tuple, "$.platform",                                 DOUYIN_PLATFORM)
    set_dict_attr(room_owner_user_attr_table_tuple, "$.room_id",                                  str(room_id))
    set_dict_attr(room_owner_user_attr_table_tuple, "$.owner_user_id",                            str(owner_user_id))
    set_dict_attr(room_owner_user_attr_table_tuple, "$.is_admin",                                 is_admin)
    set_dict_attr(room_owner_user_attr_table_tuple, "$.is_muted",                                 is_muted)
    set_dict_attr(room_owner_user_attr_table_tuple, "$.is_super_admin",                           is_super_admin)

    if db.is_table_exist(room_owner_user_attr_table.get_name()) is False:
      room_owner_user_attr_table.create()
    room_owner_user_attr_table.insert_record(room_owner_user_attr_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_owner_user_attr_table.get_name(), e))
    raise e

  ##
  ## RoomAdminPrivilegeTable
  ##
  room_admin_privilege_table = RoomAdminPrivilegeTable(db)
  try:
    ##
    ## +-----------------------+
    ## | Field                 |
    ## +-----------------------+
    ## | now                   |
    ## | platform              |
    ## | room_id               |
    ## | owner_user_id         |
    ## | admin_privilege_index |
    ## | admin_privilege       |
    ## +-----------------------+
    ##
    room_admin_privilege_table_tuple = room_admin_privilege_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    owner_user_id     = get_dict_attr(data, "$.data.room.owner_user_id")
    # admin_privilege_index auto increment
    admin_privileges  = get_dict_attr(data, "$.data.room.owner.user_attr.admin_privileges")
    if len(admin_privileges) != 0:
      set_dict_attr(room_admin_privilege_table_tuple, "$.now",                                      now)
      set_dict_attr(room_admin_privilege_table_tuple, "$.platform",                                 DOUYIN_PLATFORM)
      set_dict_attr(room_admin_privilege_table_tuple, "$.room_id",                                  str(room_id))
      set_dict_attr(room_admin_privilege_table_tuple, "$.owner_user_id",                            str(owner_user_id))
      for admin_privilege in admin_privileges:
        # admin_privilege_index auto increment
        set_dict_attr(room_admin_privilege_table_tuple, "$.admin_privilege",                        admin_privilege)
        if db.is_table_exist(room_admin_privilege_table.get_name()) is False:
          room_admin_privilege_table.create()
        room_admin_privilege_table.insert_record(room_admin_privilege_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_admin_privilege_table.get_name(), e))
    raise e

  ##
  ## RoomOwnerUserDressOwnIdTable
  ##
  room_owner_user_dress_own_id_table = RoomOwnerUserDressOwnIdTable(db)
  try:
    ##
    ## +-----------------+
    ## | Field           |
    ## +-----------------+
    ## | now             |
    ## | platform        |
    ## | room_id         |
    ## | owner_user_id   |
    ## | dress_own_index |
    ## | dress_own_id    |
    ## +-----------------+
    ##
    room_owner_user_dress_own_id_table_tuple = room_owner_user_dress_own_id_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    # owner_user_id = get_dict_attr(data, "$.data.room.owner_user_id")
    # dress_own_index auto increment
    dress_own_ids = get_dict_attr(data, "$.data.room.owner.user_dress_info.dress_own_ids")
    if len(dress_own_ids) != 0:
      set_dict_attr(room_owner_user_dress_own_id_table_tuple, "$.now",             now)
      set_dict_attr(room_owner_user_dress_own_id_table_tuple, "$.platform",        DOUYIN_PLATFORM)
      set_dict_attr(room_owner_user_dress_own_id_table_tuple, "$.room_id",         str(room_id))
      set_dict_attr(room_owner_user_dress_own_id_table_tuple, "$.owner_user_id",   str(owner_user_id))
      for dress_own_id in dress_own_ids:
        # dress_own_index auto increment
        set_dict_attr(room_owner_user_dress_own_id_table_tuple, "$.dress_own_id",   dress_own_id)
        
        if db.is_table_exist(room_owner_user_dress_own_id_table.get_name()) is False:
          room_owner_user_dress_own_id_table.create()
        room_owner_user_dress_own_id_table.insert_record(room_owner_user_dress_own_id_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_owner_user_dress_own_id_table.get_name(), e))
    raise e

  ##
  ## RoomOwnerDressWearIdTable
  ##
  room_owner_dress_wear_id_table = RoomOwnerDressWearIdTable(db)
  try:
    ##
    ## +------------------+
    ## | Field            |
    ## +------------------+
    ## | now              |
    ## | platform         |
    ## | room_id          |
    ## | owner_user_id    |
    ## | dress_wear_index |
    ## | dress_wear_id    |
    ## +------------------+
    ##
    room_owner_dress_wear_id_table_tuple = room_owner_dress_wear_id_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    # owner_user_id = get_dict_attr(data, "$.data.room.owner_user_id")
    # dress_wear_index
    dress_wear_ids = get_dict_attr(data, "$.data.room.owner.user_dress_info.dress_wear_ids")
    if len(dress_wear_ids) != 0:
      set_dict_attr(room_owner_dress_wear_id_table_tuple, "$.now",             now)
      set_dict_attr(room_owner_dress_wear_id_table_tuple, "$.platform",        DOUYIN_PLATFORM)
      set_dict_attr(room_owner_dress_wear_id_table_tuple, "$.room_id",         str(room_id))
      set_dict_attr(room_owner_dress_wear_id_table_tuple, "$.owner_user_id",   str(owner_user_id))
      for dress_wear_id in dress_wear_ids:
        # set_dict_attr(room_owner_dress_wear_id_table_tuple, "$.dress_wear_index",   dress_wear_index)
        set_dict_attr(room_owner_dress_wear_id_table_tuple, "$.dress_wear_id",   str(dress_own_id))
        
        if db.is_table_exist(room_owner_dress_wear_id_table.get_name()) is False:
          room_owner_dress_wear_id_table.create()
        room_owner_dress_wear_id_table.insert_record(room_owner_dress_wear_id_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_owner_dress_wear_id_table.get_name(), e))
    raise e

  ##
  ## RoomPackMetaTable
  ##
  room_pack_meta_table = RoomPackMetaTable(db)
  try:
    ##
    ## +----------------------------------+
    ## | Field                            |
    ## +----------------------------------+
    ## | now                              |
    ## | platform                         |
    ## | room_id                          |
    ## | cluster                          |
    ## | dc                               |
    ## | env                              |
    ## | extras                           |
    ## | scene                            |
    ## | trace_id                         |
    ## +----------------------------------+
    ##
    room_pack_meta_table_tuple = room_pack_meta_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    cluster  = get_dict_attr(data, "$.data.room.pack_meta.cluster")
    dc       = get_dict_attr(data, "$.data.room.pack_meta.dc")
    env      = get_dict_attr(data, "$.data.room.pack_meta.env")
    extras   = get_dict_attr(data, "$.data.room.pack_meta.extras")
    scene    = get_dict_attr(data, "$.data.room.pack_meta.scene")
    trace_id = get_dict_attr(data, "$.data.room.pack_meta.trace_id")
    
    set_dict_attr(room_pack_meta_table_tuple, "$.now",      now)
    set_dict_attr(room_pack_meta_table_tuple, "$.platform", DOUYIN_PLATFORM)
    set_dict_attr(room_pack_meta_table_tuple, "$.room_id",  str(room_id))
    set_dict_attr(room_pack_meta_table_tuple, "$.cluster",  cluster)
    set_dict_attr(room_pack_meta_table_tuple, "$.dc",       dc)
    set_dict_attr(room_pack_meta_table_tuple, "$.env",      env)
    set_dict_attr(room_pack_meta_table_tuple, "$.extras",   json.dumps(extras))
    set_dict_attr(room_pack_meta_table_tuple, "$.scene",    scene)
    set_dict_attr(room_pack_meta_table_tuple, "$.trace_id", trace_id)

    if db.is_table_exist(room_pack_meta_table.get_name()) is False:
      room_pack_meta_table.create()
    room_pack_meta_table.insert_record(room_pack_meta_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_pack_meta_table.get_name(), e))
    raise e

  ##
  ## RoomPaidLiveDataTable
  ##
  room_paid_live_data_table = RoomPaidLiveDataTable(db)
  try:
    ##
    ## +----------------------------------+
    ## | Field                            |
    ## +----------------------------------+
    ## | now                              |
    ## | platform                         |
    ## | room_id                          |
    ## | anchor_right                     |
    ## | delivery                         |
    ## | duration                         |
    ## | max_preview_duration             |
    ## | need_delivery_notice             |
    ## | paid_type                        |
    ## | pay_ab_type                      |
    ## | privilege_info                   |
    ## | privilege_info_map               |
    ## | view_right                       |
    ## +----------------------------------+
    ##
    room_paid_live_data_table_tuple = room_paid_live_data_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    anchor_right            = get_dict_attr(data, "$.data.room.paid_live_data.anchor_right")
    delivery                = get_dict_attr(data, "$.data.room.paid_live_data.delivery")
    duration                = get_dict_attr(data, "$.data.room.paid_live_data.duration")
    max_preview_duration    = get_dict_attr(data, "$.data.room.paid_live_data.max_preview_duration")
    need_delivery_notice    = get_dict_attr(data, "$.data.room.paid_live_data.need_delivery_notice")
    paid_type               = get_dict_attr(data, "$.data.room.paid_live_data.paid_type")
    pay_ab_type             = get_dict_attr(data, "$.data.room.paid_live_data.pay_ab_type")
    privilege_info          = get_dict_attr(data, "$.data.room.paid_live_data.privilege_info")
    privilege_info_map      = get_dict_attr(data, "$.data.room.paid_live_data.privilege_info_map")
    view_right              = get_dict_attr(data, "$.data.room.paid_live_data.view_right")
    
    set_dict_attr(room_paid_live_data_table_tuple, "$.now",                  now)
    set_dict_attr(room_paid_live_data_table_tuple, "$.platform",             DOUYIN_PLATFORM)
    set_dict_attr(room_paid_live_data_table_tuple, "$.room_id",              str(room_id))
    set_dict_attr(room_paid_live_data_table_tuple, "$.anchor_right",         anchor_right)
    set_dict_attr(room_paid_live_data_table_tuple, "$.delivery",             delivery)
    set_dict_attr(room_paid_live_data_table_tuple, "$.duration",             duration)
    set_dict_attr(room_paid_live_data_table_tuple, "$.max_preview_duration", max_preview_duration)
    set_dict_attr(room_paid_live_data_table_tuple, "$.need_delivery_notice", need_delivery_notice)
    set_dict_attr(room_paid_live_data_table_tuple, "$.paid_type",            paid_type)
    set_dict_attr(room_paid_live_data_table_tuple, "$.pay_ab_type",          pay_ab_type)
    set_dict_attr(room_paid_live_data_table_tuple, "$.privilege_info",       json.dumps(privilege_info))
    set_dict_attr(room_paid_live_data_table_tuple, "$.privilege_info_map",   json.dumps(privilege_info_map))
    set_dict_attr(room_paid_live_data_table_tuple, "$.view_right",           view_right)

    if db.is_table_exist(room_paid_live_data_table.get_name()) is False:
      room_paid_live_data_table.create()
    room_paid_live_data_table.insert_record(room_paid_live_data_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_paid_live_data_table.get_name(), e))
    raise e

  ##
  ## RoomAuthTable
  ##
  room_auth_table = RoomAuthTable(db)
  try:
    ##
    ## +----------------------------------+
    ## | Field                            |
    ## +----------------------------------+
    ## | now                              |
    ## | platform                         |
    ## | room_id                          |
    ## | AIClone                          |
    ## | AdminCommentWall                 |
    ## | AnchorAudioChat                  |
    ## | AnchorColdMessageTiled           |
    ## | AnchorHotMessageAggregated       |
    ## | AnchorMission                    |
    ## | AudioChat                        |
    ## | AudioChatTotext                  |
    ## | Banner                           |
    ## | BulletStyle                      |
    ## | CanSellTicket                    |
    ## | CastScreen                       |
    ## | CastScreenExplicit               |
    ## | Chat                             |
    ## | ChatDispatch                     |
    ## | ChatDynamicSlideSpeed            |
    ## | ChatDynamicSlideSpeedAnchor      |
    ## | ChatGuideEmoji                   |
    ## | ChatGuideImage                   |
    ## | ChatIdentity                     |
    ## | ChatMention                      |
    ## | ChatMentionV2                    |
    ## | ChatOperate                      |
    ## | ChatReply                        |
    ## | ClearEntranceOption              |
    ## | Collect                          |
    ## | CommentWall                      |
    ## | CommerceCard                     |
    ## | CommerceComponent                |
    ## | CommonCard                       |
    ## | CountType                        |
    ## | Danmaku                          |
    ## | DanmakuDefault                   |
    ## | Denounce                         |
    ## | Digg                             |
    ## | Dislike                          |
    ## | DonationSticker                  |
    ## | DouPlus                          |
    ## | DouPlusPopularityGem             |
    ## | DownloadVideo                    |
    ## | EcomFansClub                     |
    ## | EmojiOutside                     |
    ## | EnhancedTouch                    |
    ## | EnterEffects                     |
    ## | ExpandScreen                     |
    ## | FansClub                         |
    ## | FansClubBlessing                 |
    ## | FansClubDeclaration              |
    ## | FansClubLetter                   |
    ## | FansClubNotice                   |
    ## | FansGroup                        |
    ## | FeaturedPublicScreen             |
    ## | FirstFeedHistChat                |
    ## | FixedChat                        |
    ## | FrequentlyChat                   |
    ## | FusionEmoji                      |
    ## | GamePointsPlaying                |
    ## | Gift                             |
    ## | GiftAnchorMt                     |
    ## | GiftVote                         |
    ## | Highlights                       |
    ## | HostTeam                         |
    ## | HostTeamChannel                  |
    ## | HotChatTray                      |
    ## | HourRank                         |
    ## | ImHeatValue                      |
    ## | IndustryService                  |
    ## | InteractionGift                  |
    ## | InteractiveComponent             |
    ## | ItemShare                        |
    ## | KtvOrderSong                     |
    ## | Landscape                        |
    ## | LandscapeChat                    |
    ## | LandscapeChatDynamicSlideSpeed   |
    ## | LandscapeGift                    |
    ## | LandscapeScreenCapture           |
    ## | LandscapeScreenRecording         |
    ## | LandscapeScreenShare             |
    ## | `Like`                           |
    ## | LinkmicGuestLike                 |
    ## | LongPressOption                  |
    ## | LongTouch                        |
    ## | LuckMoney                        |
    ## | MarkUser                         |
    ## | MediaHistoryMessage              |
    ## | MediaLinkmic                     |
    ## | MessageDispatch                  |
    ## | MessageGift                      |
    ## | MissionCenter                    |
    ## | MoreAnchor                       |
    ## | MoreHistChat                     |
    ## | MultiplierPlayback               |
    ## | MyLiveEntrance                   |
    ## | OnlyTa                           |
    ## | PCPlay                           |
    ## | POI                              |
    ## | PadPlay                          |
    ## | PanelECService                   |
    ## | PlayerRankList                   |
    ## | Poster                           |
    ## | PosterCache                      |
    ## | PreviewChatExpose                |
    ## | PreviewHotCommentSwitch          |
    ## | ProjectionBtn                    |
    ## | Props                            |
    ## | PublicScreen                     |
    ## | QuizGamePointsPlaying            |
    ## | RecordScreen                     |
    ## | RoomChannel                      |
    ## | RoomChatLikeDisplay              |
    ## | RoomChatOperatePanel             |
    ## | RoomContributor                  |
    ## | RoomWidget                       |
    ## | ScreenBottomInfo                 |
    ## | ScreenProjectionBarrage          |
    ## | Seek                             |
    ## | Selection                        |
    ## | SelectionAlbum                   |
    ## | Share                            |
    ## | ShortTouch                       |
    ## | ShortTouchTempState              |
    ## | ShowGamePlugin                   |
    ## | ShowQualification                |
    ## | SmallWindowDisplay               |
    ## | SmallWindowPlayer                |
    ## | StickyMessage                    |
    ## | StreamAdaptation                 |
    ## | StrokeUpDownGuide                |
    ## | SubscribeCardPackage             |
    ## | Teleprompter                     |
    ## | TextGift                         |
    ## | TimedShutdown                    |
    ## | ToolbarBubble                    |
    ## | Topic                            |
    ## | TypingCommentState               |
    ## | UgcVSReplayDelete                |
    ## | UgcVsReplayVisibility            |
    ## | UpRightStatsFloatingLayer        |
    ## | UseHostInfo                      |
    ## | UserCard                         |
    ## | UserCorner                       |
    ## | VSGift                           |
    ## | VSRank                           |
    ## | VSTopic                          |
    ## | VerticalRank                     |
    ## | VerticalScreenShare              |
    ## | VideoAmplificationType           |
    ## | VideoShare                       |
    ## | VsCommentBar                     |
    ## | VsDouPlus                        |
    ## | VsExtensionEnableFollow          |
    ## | VsFansClub                       |
    ## | VsWelcomeDanmaku                 |
    ## | WordAssociation                  |
    ## +----------------------------------+
    ##
    room_auth_table_tuple = room_auth_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    AIClone                          = get_dict_attr(data, "$.data.room.room_auth.AIClone")
    AdminCommentWall                 = get_dict_attr(data, "$.data.room.room_auth.AdminCommentWall")
    AnchorAudioChat                  = get_dict_attr(data, "$.data.room.room_auth.AnchorAudioChat")
    AnchorColdMessageTiled           = get_dict_attr(data, "$.data.room.room_auth.AnchorColdMessageTiled")
    AnchorHotMessageAggregated       = get_dict_attr(data, "$.data.room.room_auth.AnchorHotMessageAggregated")
    AnchorMission                    = get_dict_attr(data, "$.data.room.room_auth.AnchorMission")
    AudioChat                        = get_dict_attr(data, "$.data.room.room_auth.AudioChat")
    AudioChatTotext                  = get_dict_attr(data, "$.data.room.room_auth.AudioChatTotext")
    Banner                           = get_dict_attr(data, "$.data.room.room_auth.Banner")
    BulletStyle                      = get_dict_attr(data, "$.data.room.room_auth.BulletStyle")
    CanSellTicket                    = get_dict_attr(data, "$.data.room.room_auth.CanSellTicket")
    CastScreen                       = get_dict_attr(data, "$.data.room.room_auth.CastScreen")
    CastScreenExplicit               = get_dict_attr(data, "$.data.room.room_auth.CastScreenExplicit")
    Chat                             = get_dict_attr(data, "$.data.room.room_auth.Chat")
    ChatDispatch                     = get_dict_attr(data, "$.data.room.room_auth.ChatDispatch")
    ChatDynamicSlideSpeed            = get_dict_attr(data, "$.data.room.room_auth.ChatDynamicSlideSpeed")
    ChatDynamicSlideSpeedAnchor      = get_dict_attr(data, "$.data.room.room_auth.ChatDynamicSlideSpeedAnchor")
    ChatGuideEmoji                   = get_dict_attr(data, "$.data.room.room_auth.ChatGuideEmoji")
    ChatGuideImage                   = get_dict_attr(data, "$.data.room.room_auth.ChatGuideImage")
    ChatIdentity                     = get_dict_attr(data, "$.data.room.room_auth.ChatIdentity")
    ChatMention                      = get_dict_attr(data, "$.data.room.room_auth.ChatMention")
    ChatMentionV2                    = get_dict_attr(data, "$.data.room.room_auth.ChatMentionV2")
    ChatOperate                      = get_dict_attr(data, "$.data.room.room_auth.ChatOperate")
    ChatReply                        = get_dict_attr(data, "$.data.room.room_auth.ChatReply")
    ClearEntranceOption              = get_dict_attr(data, "$.data.room.room_auth.ClearEntranceOption")
    Collect                          = get_dict_attr(data, "$.data.room.room_auth.Collect")
    CommentWall                      = get_dict_attr(data, "$.data.room.room_auth.CommentWall")
    CommerceCard                     = get_dict_attr(data, "$.data.room.room_auth.CommerceCard")
    CommerceComponent                = get_dict_attr(data, "$.data.room.room_auth.CommerceComponent")
    CommonCard                       = get_dict_attr(data, "$.data.room.room_auth.CommonCard")
    CountType                        = get_dict_attr(data, "$.data.room.room_auth.CountType")
    Danmaku                          = get_dict_attr(data, "$.data.room.room_auth.Danmaku")
    DanmakuDefault                   = get_dict_attr(data, "$.data.room.room_auth.DanmakuDefault")
    Denounce                         = get_dict_attr(data, "$.data.room.room_auth.Denounce")
    Digg                             = get_dict_attr(data, "$.data.room.room_auth.Digg")
    Dislike                          = get_dict_attr(data, "$.data.room.room_auth.Dislike")
    DonationSticker                  = get_dict_attr(data, "$.data.room.room_auth.DonationSticker")
    DouPlus                          = get_dict_attr(data, "$.data.room.room_auth.DouPlus")
    DouPlusPopularityGem             = get_dict_attr(data, "$.data.room.room_auth.DouPlusPopularityGem")
    DownloadVideo                    = get_dict_attr(data, "$.data.room.room_auth.DownloadVideo")
    EcomFansClub                     = get_dict_attr(data, "$.data.room.room_auth.EcomFansClub")
    EmojiOutside                     = get_dict_attr(data, "$.data.room.room_auth.EmojiOutside")
    EnhancedTouch                    = get_dict_attr(data, "$.data.room.room_auth.EnhancedTouch")
    EnterEffects                     = get_dict_attr(data, "$.data.room.room_auth.EnterEffects")
    ExpandScreen                     = get_dict_attr(data, "$.data.room.room_auth.ExpandScreen")
    FansClub                         = get_dict_attr(data, "$.data.room.room_auth.FansClub")
    FansClubBlessing                 = get_dict_attr(data, "$.data.room.room_auth.FansClubBlessing")
    FansClubDeclaration              = get_dict_attr(data, "$.data.room.room_auth.FansClubDeclaration")
    FansClubLetter                   = get_dict_attr(data, "$.data.room.room_auth.FansClubLetter")
    FansClubNotice                   = get_dict_attr(data, "$.data.room.room_auth.FansClubNotice")
    FansGroup                        = get_dict_attr(data, "$.data.room.room_auth.FansGroup")
    FeaturedPublicScreen             = get_dict_attr(data, "$.data.room.room_auth.FeaturedPublicScreen")
    FirstFeedHistChat                = get_dict_attr(data, "$.data.room.room_auth.FirstFeedHistChat")
    FixedChat                        = get_dict_attr(data, "$.data.room.room_auth.FixedChat")
    FrequentlyChat                   = get_dict_attr(data, "$.data.room.room_auth.FrequentlyChat")
    FusionEmoji                      = get_dict_attr(data, "$.data.room.room_auth.FusionEmoji")
    GamePointsPlaying                = get_dict_attr(data, "$.data.room.room_auth.GamePointsPlaying")
    Gift                             = get_dict_attr(data, "$.data.room.room_auth.Gift")
    GiftAnchorMt                     = get_dict_attr(data, "$.data.room.room_auth.GiftAnchorMt")
    GiftVote                         = get_dict_attr(data, "$.data.room.room_auth.GiftVote")
    Highlights                       = get_dict_attr(data, "$.data.room.room_auth.Highlights")
    HostTeam                         = get_dict_attr(data, "$.data.room.room_auth.HostTeam")
    HostTeamChannel                  = get_dict_attr(data, "$.data.room.room_auth.HostTeamChannel")
    HotChatTray                      = get_dict_attr(data, "$.data.room.room_auth.HotChatTray")
    HourRank                         = get_dict_attr(data, "$.data.room.room_auth.HourRank")
    ImHeatValue                      = get_dict_attr(data, "$.data.room.room_auth.ImHeatValue")
    IndustryService                  = get_dict_attr(data, "$.data.room.room_auth.IndustryService")
    InteractionGift                  = get_dict_attr(data, "$.data.room.room_auth.InteractionGift")
    InteractiveComponent             = get_dict_attr(data, "$.data.room.room_auth.InteractiveComponent")
    ItemShare                        = get_dict_attr(data, "$.data.room.room_auth.ItemShare")
    KtvOrderSong                     = get_dict_attr(data, "$.data.room.room_auth.KtvOrderSong")
    Landscape                        = get_dict_attr(data, "$.data.room.room_auth.Landscape")
    LandscapeChat                    = get_dict_attr(data, "$.data.room.room_auth.LandscapeChat")
    LandscapeChatDynamicSlideSpeed   = get_dict_attr(data, "$.data.room.room_auth.LandscapeChatDynamicSlideSpeed")
    LandscapeGift                    = get_dict_attr(data, "$.data.room.room_auth.LandscapeGift")
    LandscapeScreenCapture           = get_dict_attr(data, "$.data.room.room_auth.LandscapeScreenCapture")
    LandscapeScreenRecording         = get_dict_attr(data, "$.data.room.room_auth.LandscapeScreenRecording")
    LandscapeScreenShare             = get_dict_attr(data, "$.data.room.room_auth.LandscapeScreenShare")
    Like                             = get_dict_attr(data, "$.data.room.room_auth.Like")
    LinkmicGuestLike                 = get_dict_attr(data, "$.data.room.room_auth.LinkmicGuestLike")
    LongPressOption                  = get_dict_attr(data, "$.data.room.room_auth.LongPressOption")
    LongTouch                        = get_dict_attr(data, "$.data.room.room_auth.LongTouch")
    LuckMoney                        = get_dict_attr(data, "$.data.room.room_auth.LuckMoney")
    MarkUser                         = get_dict_attr(data, "$.data.room.room_auth.MarkUser")
    MediaHistoryMessage              = get_dict_attr(data, "$.data.room.room_auth.MediaHistoryMessage")
    MediaLinkmic                     = get_dict_attr(data, "$.data.room.room_auth.MediaLinkmic")
    MessageDispatch                  = get_dict_attr(data, "$.data.room.room_auth.MessageDispatch")
    MessageGift                      = get_dict_attr(data, "$.data.room.room_auth.MessageGift")
    MissionCenter                    = get_dict_attr(data, "$.data.room.room_auth.MissionCenter")
    MoreAnchor                       = get_dict_attr(data, "$.data.room.room_auth.MoreAnchor")
    MoreHistChat                     = get_dict_attr(data, "$.data.room.room_auth.MoreHistChat")
    MultiplierPlayback               = get_dict_attr(data, "$.data.room.room_auth.MultiplierPlayback")
    MyLiveEntrance                   = get_dict_attr(data, "$.data.room.room_auth.MyLiveEntrance")
    OnlyTa                           = get_dict_attr(data, "$.data.room.room_auth.OnlyTa")
    PCPlay                           = get_dict_attr(data, "$.data.room.room_auth.PCPlay")
    POI                              = get_dict_attr(data, "$.data.room.room_auth.POI")
    PadPlay                          = get_dict_attr(data, "$.data.room.room_auth.PadPlay")
    PanelECService                   = get_dict_attr(data, "$.data.room.room_auth.PanelECService")
    PlayerRankList                   = get_dict_attr(data, "$.data.room.room_auth.PlayerRankList")
    Poster                           = get_dict_attr(data, "$.data.room.room_auth.Poster")
    PosterCache                      = get_dict_attr(data, "$.data.room.room_auth.PosterCache")
    PreviewChatExpose                = get_dict_attr(data, "$.data.room.room_auth.PreviewChatExpose")
    PreviewHotCommentSwitch          = get_dict_attr(data, "$.data.room.room_auth.PreviewHotCommentSwitch")
    ProjectionBtn                    = get_dict_attr(data, "$.data.room.room_auth.ProjectionBtn")
    Props                            = get_dict_attr(data, "$.data.room.room_auth.Props")
    PublicScreen                     = get_dict_attr(data, "$.data.room.room_auth.PublicScreen")
    QuizGamePointsPlaying            = get_dict_attr(data, "$.data.room.room_auth.QuizGamePointsPlaying")
    RecordScreen                     = get_dict_attr(data, "$.data.room.room_auth.RecordScreen")
    RoomChannel                      = get_dict_attr(data, "$.data.room.room_auth.RoomChannel")
    RoomChatLikeDisplay              = get_dict_attr(data, "$.data.room.room_auth.RoomChatLikeDisplay")
    RoomChatOperatePanel             = get_dict_attr(data, "$.data.room.room_auth.RoomChatOperatePanel")
    RoomContributor                  = get_dict_attr(data, "$.data.room.room_auth.RoomContributor")
    RoomWidget                       = get_dict_attr(data, "$.data.room.room_auth.RoomWidget")
    ScreenBottomInfo                 = get_dict_attr(data, "$.data.room.room_auth.ScreenBottomInfo")
    ScreenProjectionBarrage          = get_dict_attr(data, "$.data.room.room_auth.ScreenProjectionBarrage")
    Seek                             = get_dict_attr(data, "$.data.room.room_auth.Seek")
    Selection                        = get_dict_attr(data, "$.data.room.room_auth.Selection")
    SelectionAlbum                   = get_dict_attr(data, "$.data.room.room_auth.SelectionAlbum")
    Share                            = get_dict_attr(data, "$.data.room.room_auth.Share")
    ShortTouch                       = get_dict_attr(data, "$.data.room.room_auth.ShortTouch")
    ShortTouchTempState              = get_dict_attr(data, "$.data.room.room_auth.ShortTouchTempState")
    ShowGamePlugin                   = get_dict_attr(data, "$.data.room.room_auth.ShowGamePlugin")
    ShowQualification                = get_dict_attr(data, "$.data.room.room_auth.ShowQualification")
    SmallWindowDisplay               = get_dict_attr(data, "$.data.room.room_auth.SmallWindowDisplay")
    SmallWindowPlayer                = get_dict_attr(data, "$.data.room.room_auth.SmallWindowPlayer")
    StickyMessage                    = get_dict_attr(data, "$.data.room.room_auth.StickyMessage")
    StreamAdaptation                 = get_dict_attr(data, "$.data.room.room_auth.StreamAdaptation")
    StrokeUpDownGuide                = get_dict_attr(data, "$.data.room.room_auth.StrokeUpDownGuide")
    SubscribeCardPackage             = get_dict_attr(data, "$.data.room.room_auth.SubscribeCardPackage")
    Teleprompter                     = get_dict_attr(data, "$.data.room.room_auth.Teleprompter")
    TextGift                         = get_dict_attr(data, "$.data.room.room_auth.TextGift")
    TimedShutdown                    = get_dict_attr(data, "$.data.room.room_auth.TimedShutdown")
    ToolbarBubble                    = get_dict_attr(data, "$.data.room.room_auth.ToolbarBubble")
    Topic                            = get_dict_attr(data, "$.data.room.room_auth.Topic")
    TypingCommentState               = get_dict_attr(data, "$.data.room.room_auth.TypingCommentState")
    UgcVSReplayDelete                = get_dict_attr(data, "$.data.room.room_auth.UgcVSReplayDelete")
    UgcVsReplayVisibility            = get_dict_attr(data, "$.data.room.room_auth.UgcVsReplayVisibility")
    UpRightStatsFloatingLayer        = get_dict_attr(data, "$.data.room.room_auth.UpRightStatsFloatingLayer")
    UseHostInfo                      = get_dict_attr(data, "$.data.room.room_auth.UseHostInfo")
    UserCard                         = get_dict_attr(data, "$.data.room.room_auth.UserCard")
    UserCorner                       = get_dict_attr(data, "$.data.room.room_auth.UserCorner")
    VSGift                           = get_dict_attr(data, "$.data.room.room_auth.VSGift")
    VSRank                           = get_dict_attr(data, "$.data.room.room_auth.VSRank")
    VSTopic                          = get_dict_attr(data, "$.data.room.room_auth.VSTopic")
    VerticalRank                     = get_dict_attr(data, "$.data.room.room_auth.VerticalRank")
    VerticalScreenShare              = get_dict_attr(data, "$.data.room.room_auth.VerticalScreenShare")
    VideoAmplificationType           = get_dict_attr(data, "$.data.room.room_auth.VideoAmplificationType")
    VideoShare                       = get_dict_attr(data, "$.data.room.room_auth.VideoShare")
    VsCommentBar                     = get_dict_attr(data, "$.data.room.room_auth.VsCommentBar")
    VsDouPlus                        = get_dict_attr(data, "$.data.room.room_auth.VsDouPlus")
    VsExtensionEnableFollow          = get_dict_attr(data, "$.data.room.room_auth.VsExtensionEnableFollow")
    VsFansClub                       = get_dict_attr(data, "$.data.room.room_auth.VsFansClub")
    VsWelcomeDanmaku                 = get_dict_attr(data, "$.data.room.room_auth.VsWelcomeDanmaku")
    WordAssociation                  = get_dict_attr(data, "$.data.room.room_auth.WordAssociation")
    
    set_dict_attr(room_auth_table_tuple, "$.now",                        now)
    set_dict_attr(room_auth_table_tuple, "$.platform",                   DOUYIN_PLATFORM)
    set_dict_attr(room_auth_table_tuple, "$.room_id",                    str(room_id))
    set_dict_attr(room_auth_table_tuple, "$.AIClone",                    AIClone)
    set_dict_attr(room_auth_table_tuple, "$.AdminCommentWall",           AdminCommentWall)
    set_dict_attr(room_auth_table_tuple, "$.AnchorAudioChat",            AnchorAudioChat)
    set_dict_attr(room_auth_table_tuple, "$.AnchorColdMessageTiled",     AnchorColdMessageTiled)
    set_dict_attr(room_auth_table_tuple, "$.AnchorHotMessageAggregated", AnchorHotMessageAggregated)
    set_dict_attr(room_auth_table_tuple, "$.AnchorMission",              AnchorMission)
    set_dict_attr(room_auth_table_tuple, "$.AudioChat",                  AudioChat)
    set_dict_attr(room_auth_table_tuple, "$.AudioChatTotext",            AudioChatTotext)
    set_dict_attr(room_auth_table_tuple, "$.Banner",                     Banner)
    set_dict_attr(room_auth_table_tuple, "$.BulletStyle",                BulletStyle)
    set_dict_attr(room_auth_table_tuple, "$.CanSellTicket",              CanSellTicket)
    set_dict_attr(room_auth_table_tuple, "$.CastScreen",                 CastScreen)
    set_dict_attr(room_auth_table_tuple, "$.CastScreenExplicit",         CastScreenExplicit)
    set_dict_attr(room_auth_table_tuple, "$.Chat",                       Chat)
    set_dict_attr(room_auth_table_tuple, "$.ChatDispatch",               ChatDispatch)
    set_dict_attr(room_auth_table_tuple, "$.ChatDynamicSlideSpeed",      ChatDynamicSlideSpeed)
    set_dict_attr(room_auth_table_tuple, "$.ChatDynamicSlideSpeedAnchor",ChatDynamicSlideSpeedAnchor)
    set_dict_attr(room_auth_table_tuple, "$.ChatGuideEmoji",             ChatGuideEmoji)
    set_dict_attr(room_auth_table_tuple, "$.ChatGuideImage",             ChatGuideImage)
    set_dict_attr(room_auth_table_tuple, "$.ChatIdentity",               ChatIdentity)
    set_dict_attr(room_auth_table_tuple, "$.ChatMention",                ChatMention)
    set_dict_attr(room_auth_table_tuple, "$.ChatMentionV2",              ChatMentionV2)
    set_dict_attr(room_auth_table_tuple, "$.ChatOperate",                ChatOperate)
    set_dict_attr(room_auth_table_tuple, "$.ChatReply",                  ChatReply)
    set_dict_attr(room_auth_table_tuple, "$.ClearEntranceOption",        ClearEntranceOption)
    set_dict_attr(room_auth_table_tuple, "$.Collect",                    Collect)
    set_dict_attr(room_auth_table_tuple, "$.CommentWall",                CommentWall)
    set_dict_attr(room_auth_table_tuple, "$.CommerceCard",               CommerceCard)
    set_dict_attr(room_auth_table_tuple, "$.CommerceComponent",          CommerceComponent)
    set_dict_attr(room_auth_table_tuple, "$.CommonCard",                 CommonCard)
    set_dict_attr(room_auth_table_tuple, "$.CountType",                  CountType)
    set_dict_attr(room_auth_table_tuple, "$.Danmaku",                    Danmaku)
    set_dict_attr(room_auth_table_tuple, "$.DanmakuDefault",             DanmakuDefault)
    set_dict_attr(room_auth_table_tuple, "$.Denounce",                   Denounce)
    set_dict_attr(room_auth_table_tuple, "$.Digg",                       Digg)
    set_dict_attr(room_auth_table_tuple, "$.Dislike",                    Dislike)
    set_dict_attr(room_auth_table_tuple, "$.DonationSticker",            DonationSticker)
    set_dict_attr(room_auth_table_tuple, "$.DouPlus",                    DouPlus)
    set_dict_attr(room_auth_table_tuple, "$.DouPlusPopularityGem",       DouPlusPopularityGem)
    set_dict_attr(room_auth_table_tuple, "$.DownloadVideo",              DownloadVideo)
    set_dict_attr(room_auth_table_tuple, "$.EcomFansClub",               EcomFansClub)
    set_dict_attr(room_auth_table_tuple, "$.EmojiOutside",               EmojiOutside)
    set_dict_attr(room_auth_table_tuple, "$.EnhancedTouch",              EnhancedTouch)
    set_dict_attr(room_auth_table_tuple, "$.EnterEffects",               EnterEffects)
    set_dict_attr(room_auth_table_tuple, "$.ExpandScreen",               ExpandScreen)
    set_dict_attr(room_auth_table_tuple, "$.FansClub",                   FansClub)
    set_dict_attr(room_auth_table_tuple, "$.FansClubBlessing",           FansClubBlessing)
    set_dict_attr(room_auth_table_tuple, "$.FansClubDeclaration",        FansClubDeclaration)
    set_dict_attr(room_auth_table_tuple, "$.FansClubLetter",             FansClubLetter)
    set_dict_attr(room_auth_table_tuple, "$.FansClubNotice",             FansClubNotice)
    set_dict_attr(room_auth_table_tuple, "$.FansGroup",                  FansGroup)
    set_dict_attr(room_auth_table_tuple, "$.FeaturedPublicScreen",       FeaturedPublicScreen)
    set_dict_attr(room_auth_table_tuple, "$.FirstFeedHistChat",          FirstFeedHistChat)
    set_dict_attr(room_auth_table_tuple, "$.FixedChat",                  FixedChat)
    set_dict_attr(room_auth_table_tuple, "$.FrequentlyChat",             FrequentlyChat)
    set_dict_attr(room_auth_table_tuple, "$.FusionEmoji",                FusionEmoji)
    set_dict_attr(room_auth_table_tuple, "$.GamePointsPlaying",          GamePointsPlaying)
    set_dict_attr(room_auth_table_tuple, "$.Gift",                       Gift)
    set_dict_attr(room_auth_table_tuple, "$.GiftAnchorMt",               GiftAnchorMt)
    set_dict_attr(room_auth_table_tuple, "$.GiftVote",                   GiftVote)
    set_dict_attr(room_auth_table_tuple, "$.Highlights",                 Highlights)
    set_dict_attr(room_auth_table_tuple, "$.HostTeam",                   HostTeam)
    set_dict_attr(room_auth_table_tuple, "$.HostTeamChannel",            HostTeamChannel)
    set_dict_attr(room_auth_table_tuple, "$.HotChatTray",                HotChatTray)
    set_dict_attr(room_auth_table_tuple, "$.HourRank",                   HourRank)
    set_dict_attr(room_auth_table_tuple, "$.ImHeatValue",                ImHeatValue)
    set_dict_attr(room_auth_table_tuple, "$.IndustryService",            IndustryService)
    set_dict_attr(room_auth_table_tuple, "$.InteractionGift",            InteractionGift)
    set_dict_attr(room_auth_table_tuple, "$.InteractiveComponent",       InteractiveComponent)
    set_dict_attr(room_auth_table_tuple, "$.ItemShare",                  ItemShare)
    set_dict_attr(room_auth_table_tuple, "$.KtvOrderSong",               KtvOrderSong)
    set_dict_attr(room_auth_table_tuple, "$.Landscape",                  Landscape)
    set_dict_attr(room_auth_table_tuple, "$.LandscapeChat",              LandscapeChat)
    set_dict_attr(room_auth_table_tuple, "$.LandscapeChatDynamicSlideSpeed",LandscapeChatDynamicSlideSpeed)
    set_dict_attr(room_auth_table_tuple, "$.LandscapeGift",              LandscapeGift)
    set_dict_attr(room_auth_table_tuple, "$.LandscapeScreenCapture",     LandscapeScreenCapture)
    set_dict_attr(room_auth_table_tuple, "$.LandscapeScreenRecording",   LandscapeScreenRecording)
    set_dict_attr(room_auth_table_tuple, "$.LandscapeScreenShare",       LandscapeScreenShare)
    set_dict_attr(room_auth_table_tuple, "$.`Like`",                     Like)
    set_dict_attr(room_auth_table_tuple, "$.LinkmicGuestLike",           LinkmicGuestLike)
    set_dict_attr(room_auth_table_tuple, "$.LongPressOption",            LongPressOption)
    set_dict_attr(room_auth_table_tuple, "$.LongTouch",                  LongTouch)
    set_dict_attr(room_auth_table_tuple, "$.LuckMoney",                  LuckMoney)
    set_dict_attr(room_auth_table_tuple, "$.MarkUser",                   MarkUser)
    set_dict_attr(room_auth_table_tuple, "$.MediaHistoryMessage",        MediaHistoryMessage)
    set_dict_attr(room_auth_table_tuple, "$.MediaLinkmic",               MediaLinkmic)
    set_dict_attr(room_auth_table_tuple, "$.MessageDispatch",            MessageDispatch)
    set_dict_attr(room_auth_table_tuple, "$.MessageGift",                MessageGift)
    set_dict_attr(room_auth_table_tuple, "$.MissionCenter",              MissionCenter)
    set_dict_attr(room_auth_table_tuple, "$.MoreAnchor",                 MoreAnchor)
    set_dict_attr(room_auth_table_tuple, "$.MoreHistChat",               MoreHistChat)
    set_dict_attr(room_auth_table_tuple, "$.MultiplierPlayback",         MultiplierPlayback)
    set_dict_attr(room_auth_table_tuple, "$.MyLiveEntrance",             MyLiveEntrance)
    set_dict_attr(room_auth_table_tuple, "$.OnlyTa",                     OnlyTa)
    set_dict_attr(room_auth_table_tuple, "$.PCPlay",                     PCPlay)
    set_dict_attr(room_auth_table_tuple, "$.POI",                        POI)
    set_dict_attr(room_auth_table_tuple, "$.PadPlay",                    PadPlay)
    set_dict_attr(room_auth_table_tuple, "$.PanelECService",             PanelECService)
    set_dict_attr(room_auth_table_tuple, "$.PlayerRankList",             PlayerRankList)
    set_dict_attr(room_auth_table_tuple, "$.Poster",                     Poster)
    set_dict_attr(room_auth_table_tuple, "$.PosterCache",                PosterCache)
    set_dict_attr(room_auth_table_tuple, "$.PreviewChatExpose",          PreviewChatExpose)
    set_dict_attr(room_auth_table_tuple, "$.PreviewHotCommentSwitch",    PreviewHotCommentSwitch)
    set_dict_attr(room_auth_table_tuple, "$.ProjectionBtn",              ProjectionBtn)
    set_dict_attr(room_auth_table_tuple, "$.Props",                      Props)
    set_dict_attr(room_auth_table_tuple, "$.PublicScreen",               PublicScreen)
    set_dict_attr(room_auth_table_tuple, "$.QuizGamePointsPlaying",      QuizGamePointsPlaying)
    set_dict_attr(room_auth_table_tuple, "$.RecordScreen",               RecordScreen)
    set_dict_attr(room_auth_table_tuple, "$.RoomChannel",                RoomChannel)
    set_dict_attr(room_auth_table_tuple, "$.RoomChatLikeDisplay",        RoomChatLikeDisplay)
    set_dict_attr(room_auth_table_tuple, "$.RoomChatOperatePanel",       RoomChatOperatePanel)
    set_dict_attr(room_auth_table_tuple, "$.RoomContributor",            RoomContributor)
    set_dict_attr(room_auth_table_tuple, "$.RoomWidget",                 RoomWidget)
    set_dict_attr(room_auth_table_tuple, "$.ScreenBottomInfo",           ScreenBottomInfo)
    set_dict_attr(room_auth_table_tuple, "$.ScreenProjectionBarrage",    ScreenProjectionBarrage)
    set_dict_attr(room_auth_table_tuple, "$.Seek",                       Seek)
    set_dict_attr(room_auth_table_tuple, "$.Selection",                  Selection)
    set_dict_attr(room_auth_table_tuple, "$.SelectionAlbum",             SelectionAlbum)
    set_dict_attr(room_auth_table_tuple, "$.Share",                      Share)
    set_dict_attr(room_auth_table_tuple, "$.ShortTouch",                 ShortTouch)
    set_dict_attr(room_auth_table_tuple, "$.ShortTouchTempState",        ShortTouchTempState)
    set_dict_attr(room_auth_table_tuple, "$.ShowGamePlugin",             ShowGamePlugin)
    set_dict_attr(room_auth_table_tuple, "$.ShowQualification",          ShowQualification)
    set_dict_attr(room_auth_table_tuple, "$.SmallWindowDisplay",         SmallWindowDisplay)
    set_dict_attr(room_auth_table_tuple, "$.SmallWindowPlayer",          SmallWindowPlayer)
    set_dict_attr(room_auth_table_tuple, "$.StickyMessage",              StickyMessage)
    set_dict_attr(room_auth_table_tuple, "$.StreamAdaptation",           StreamAdaptation)
    set_dict_attr(room_auth_table_tuple, "$.StrokeUpDownGuide",          StrokeUpDownGuide)
    set_dict_attr(room_auth_table_tuple, "$.SubscribeCardPackage",       SubscribeCardPackage)
    set_dict_attr(room_auth_table_tuple, "$.Teleprompter",               Teleprompter)
    set_dict_attr(room_auth_table_tuple, "$.TextGift",                   TextGift)
    set_dict_attr(room_auth_table_tuple, "$.TimedShutdown",              TimedShutdown)
    set_dict_attr(room_auth_table_tuple, "$.ToolbarBubble",              ToolbarBubble)
    set_dict_attr(room_auth_table_tuple, "$.Topic",                      Topic)
    set_dict_attr(room_auth_table_tuple, "$.TypingCommentState",         TypingCommentState)
    set_dict_attr(room_auth_table_tuple, "$.UgcVSReplayDelete",          UgcVSReplayDelete)
    set_dict_attr(room_auth_table_tuple, "$.UgcVsReplayVisibility",      UgcVsReplayVisibility)
    set_dict_attr(room_auth_table_tuple, "$.UpRightStatsFloatingLayer",  UpRightStatsFloatingLayer)
    set_dict_attr(room_auth_table_tuple, "$.UseHostInfo",                UseHostInfo)
    set_dict_attr(room_auth_table_tuple, "$.UserCard",                   UserCard)
    set_dict_attr(room_auth_table_tuple, "$.UserCorner",                 UserCorner)
    set_dict_attr(room_auth_table_tuple, "$.VSGift",                     VSGift)
    set_dict_attr(room_auth_table_tuple, "$.VSRank",                     VSRank)
    set_dict_attr(room_auth_table_tuple, "$.VSTopic",                    VSTopic)
    set_dict_attr(room_auth_table_tuple, "$.VerticalRank",               VerticalRank)
    set_dict_attr(room_auth_table_tuple, "$.VerticalScreenShare",        VerticalScreenShare)
    set_dict_attr(room_auth_table_tuple, "$.VideoAmplificationType",     VideoAmplificationType)
    set_dict_attr(room_auth_table_tuple, "$.VideoShare",                 VideoShare)
    set_dict_attr(room_auth_table_tuple, "$.VsCommentBar",               VsCommentBar)
    set_dict_attr(room_auth_table_tuple, "$.VsDouPlus",                  VsDouPlus)
    set_dict_attr(room_auth_table_tuple, "$.VsExtensionEnableFollow",    VsExtensionEnableFollow)
    set_dict_attr(room_auth_table_tuple, "$.VsFansClub",                 VsFansClub)
    set_dict_attr(room_auth_table_tuple, "$.VsWelcomeDanmaku",           VsWelcomeDanmaku)
    set_dict_attr(room_auth_table_tuple, "$.WordAssociation",            WordAssociation)

    if db.is_table_exist(room_auth_table.get_name()) is False:
      room_auth_table.create()
    room_auth_table.insert_record(room_auth_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_auth_table.get_name(), e))
    raise e

  """
  ##
  ## RoomTabTable
  ## TBD
  ##
  room_tab_table = RoomTabTable(db)
  try:
    get_logger().warning("{} TBD".format(room_tab_table.get_name()))
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_tab_table.get_name(), e))
    raise e
  """
  ##
  ## RoomSharingMusicIdTable
  ##
  room_sharing_music_id_table = RoomSharingMusicIdTable(db)
  try:
    ##
    ## +---------------------+
    ## | Field               |
    ## +---------------------+
    ## | now                 |
    ## | platform            |
    ## | room_id             |
    ## | sharing_music_index |
    ## | sharing_music_id    |
    ## +---------------------+
    ##
    room_sharing_music_id_table_tuple = room_sharing_music_id_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    # dress_wear_index
    sharing_music_id_list = get_dict_attr(data, "$.data.room.sharing_music_id_list")
    if len(sharing_music_id_list) != 0:
      set_dict_attr(room_sharing_music_id_table_tuple, "$.now",             now)
      set_dict_attr(room_sharing_music_id_table_tuple, "$.platform",        DOUYIN_PLATFORM)
      set_dict_attr(room_sharing_music_id_table_tuple, "$.room_id",         str(room_id))
      for sharing_music_id in sharing_music_id_list:
        # sharing_music_index auto increment
        set_dict_attr(room_sharing_music_id_table_tuple, "$.sharing_music_id",   str(sharing_music_id))
        
        if db.is_table_exist(room_sharing_music_id_table.get_name()) is False:
          room_sharing_music_id_table.create()
        room_sharing_music_id_table.insert_record(room_sharing_music_id_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_sharing_music_id_table.get_name(), e))
    raise e

  ##
  ## RoomShortTouchAreaConfigTable
  ##
  room_short_touch_area_config_table = RoomShortTouchAreaConfigTable(db)
  try:
    ##
    ## +---------------------+
    ## | Field               |
    ## +---------------------+
    ## | now                 |
    ## | platform            |
    ## | room_id             |
    ## | forbidden_types_map |
    ## +---------------------+
    ##
    room_short_touch_area_config_table_tuple = room_short_touch_area_config_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    forbidden_types_map = get_dict_attr(data, "$.data.room.short_touch_area_config.forbidden_types_map")
    
    set_dict_attr(room_short_touch_area_config_table_tuple, "$.now",                 now)
    set_dict_attr(room_short_touch_area_config_table_tuple, "$.platform",            DOUYIN_PLATFORM)
    set_dict_attr(room_short_touch_area_config_table_tuple, "$.room_id",             str(room_id))
    set_dict_attr(room_short_touch_area_config_table_tuple, "$.forbidden_types_map", json.dumps(forbidden_types_map))

    if db.is_table_exist(room_short_touch_area_config_table.get_name()) is False:
      room_short_touch_area_config_table.create()
    room_short_touch_area_config_table.insert_record(room_short_touch_area_config_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_short_touch_area_config_table.get_name(), e))
    raise e

  ##
  ## RoomShortTouchAreaConfigElementTable
  ##
  room_short_touch_area_config_element_table = RoomShortTouchAreaConfigElementTable(db)
  try:
    ##
    ## +---------------+
    ## | Field         |
    ## +---------------+
    ## | now           |
    ## | platform      |
    ## | room_id       |
    ## | element_index |
    ## | priority      |
    ## | type          |
    ## +---------------+
    ##
    room_short_touch_area_config_element_table_tuple = room_short_touch_area_config_element_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    # element_index
    elements = get_dict_attr(data, "$.data.room.short_touch_area_config.elements")
    if elements is not None:
      set_dict_attr(room_short_touch_area_config_element_table_tuple, "$.now",           now)
      set_dict_attr(room_short_touch_area_config_element_table_tuple, "$.platform",      DOUYIN_PLATFORM)
      set_dict_attr(room_short_touch_area_config_element_table_tuple, "$.room_id",       str(room_id))
  
      for element_key, element_value in dict(elements).items():
        # element_index auto increment
        priority = get_dict_attr(element_value, "$.priority")
        type     = get_dict_attr(element_value, "$.type")
      
        set_dict_attr(room_short_touch_area_config_element_table_tuple, "$.priority",      priority)
        set_dict_attr(room_short_touch_area_config_element_table_tuple, "$.type",          type)
      
        if db.is_table_exist(room_short_touch_area_config_element_table.get_name()) is False:
          room_short_touch_area_config_element_table.create()
        room_short_touch_area_config_element_table.insert_record(room_short_touch_area_config_element_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_short_touch_area_config_element_table.get_name(), e))
    raise e

  ##
  ## RoomShortTouchAreaConfigStrategyFeatWhitelistTable
  ##
  room_short_touch_area_config_strategy_feat_whitelist_table = RoomShortTouchAreaConfigStrategyFeatWhitelistTable(db)
  try:
    ##
    ## +-----------------+
    ## | Field           |
    ## +-----------------+
    ## | now             |
    ## | platform        |
    ## | room_id         |
    ## | whitelist_index |
    ## | whitelist_tag   |
    ## +-----------------+
    ##
    room_short_touch_area_config_strategy_feat_whitelist_table_tuple = room_short_touch_area_config_strategy_feat_whitelist_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    # whitelist_index auto increment
    strategy_feat_whitelist = get_dict_attr(data, "$.data.room.short_touch_area_config.strategy_feat_whitelist")
    if len(strategy_feat_whitelist) != 0:
      set_dict_attr(room_short_touch_area_config_strategy_feat_whitelist_table_tuple, "$.now",           now)
      set_dict_attr(room_short_touch_area_config_strategy_feat_whitelist_table_tuple, "$.platform",      DOUYIN_PLATFORM)
      set_dict_attr(room_short_touch_area_config_strategy_feat_whitelist_table_tuple, "$.room_id",       str(room_id))
  
      for whitelist_tag in strategy_feat_whitelist:
        # whitelist_index auto increment
        set_dict_attr(room_short_touch_area_config_strategy_feat_whitelist_table_tuple, "$.whitelist_tag",   whitelist_tag)
      
        if db.is_table_exist(room_short_touch_area_config_strategy_feat_whitelist_table.get_name()) is False:
          room_short_touch_area_config_strategy_feat_whitelist_table.create()
        room_short_touch_area_config_strategy_feat_whitelist_table.insert_record(room_short_touch_area_config_strategy_feat_whitelist_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_short_touch_area_config_strategy_feat_whitelist_table.get_name(), e))
    raise e

  ##
  ## RoomTempStateConditionMapTable
  ##
  room_temp_state_condition_map_table = RoomTempStateConditionMapTable(db)
  try:
    ##
    ## +---------------+
    ## | Field         |
    ## +---------------+
    ## | now           |
    ## | platform      |
    ## | room_id       |
    ## | map_index     |
    ## | minimum_gap   |
    ## | priority      |
    ## | strategy_type |
    ## +---------------+
    ##
    room_temp_state_condition_map_table_tuple = room_temp_state_condition_map_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    # map_index
    temp_state_condition_map = get_dict_attr(data, "$.data.room.short_touch_area_config.temp_state_condition_map")
    if temp_state_condition_map is not None:
      set_dict_attr(room_temp_state_condition_map_table_tuple, "$.now",           now)
      set_dict_attr(room_temp_state_condition_map_table_tuple, "$.platform",      DOUYIN_PLATFORM)
      set_dict_attr(room_temp_state_condition_map_table_tuple, "$.room_id",       str(room_id))
  
      for temp_state_condition_key, temp_state_condition_value in  dict(temp_state_condition_map).items():
        minimum_gap   = get_dict_attr(temp_state_condition_value, "$.minimum_gap")
        priority      = get_dict_attr(temp_state_condition_value, "$.type.priority")
        strategy_type = get_dict_attr(temp_state_condition_value, "$.type.strategy_type")
        
        # map_index auto increment
        set_dict_attr(room_temp_state_condition_map_table_tuple, "$.minimum_gap",   minimum_gap)
        set_dict_attr(room_temp_state_condition_map_table_tuple, "$.priority",      priority)
        set_dict_attr(room_temp_state_condition_map_table_tuple, "$.strategy_type", strategy_type)
      
        if db.is_table_exist(room_temp_state_condition_map_table.get_name()) is False:
          room_temp_state_condition_map_table.create()
        room_temp_state_condition_map_table.insert_record(room_temp_state_condition_map_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_temp_state_condition_map_table.get_name(), e))
    raise e

  ##
  ## RoomTempStateGlobalConditionIgnoreStrategyTypeTable
  ##
  room_temp_state_global_condition_ignore_strategy_type_table = RoomTempStateGlobalConditionIgnoreStrategyTypeTable(db)
  try:
    ##
    ## +-----------------------------+
    ## | Field                       |
    ## +-----------------------------+
    ## | now                         |
    ## | platform                    |
    ## | room_id                     |
    ## | ignore_strategy_type_index  |
    ## | ignore_strategy_type        |
    ## +-----------------------------+
    ##
    room_temp_state_global_condition_ignore_strategy_type_table_tuple = room_temp_state_global_condition_ignore_strategy_type_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    ignore_strategy_types = get_dict_attr(data, "$.data.room.short_touch_area_config.temp_state_global_condition.ignore_strategy_types")
    if len(ignore_strategy_types) != 0:
      set_dict_attr(room_temp_state_global_condition_ignore_strategy_type_table_tuple, "$.now",           now)
      set_dict_attr(room_temp_state_global_condition_ignore_strategy_type_table_tuple, "$.platform",      DOUYIN_PLATFORM)
      set_dict_attr(room_temp_state_global_condition_ignore_strategy_type_table_tuple, "$.room_id",       str(room_id))
      for ignore_strategy_type in ignore_strategy_types:
        # ignore_strategy_type_index auto increment
        set_dict_attr(room_temp_state_global_condition_ignore_strategy_type_table_tuple, "$.ignore_strategy_type", ignore_strategy_type)
      
        if db.is_table_exist(room_temp_state_global_condition_ignore_strategy_type_table.get_name()) is False:
          room_temp_state_global_condition_ignore_strategy_type_table.create()
        room_temp_state_global_condition_ignore_strategy_type_table.insert_record(room_temp_state_global_condition_ignore_strategy_type_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_temp_state_global_condition_ignore_strategy_type_table.get_name(), e))
    raise e

  ##
  ## RoomTempStateGlobalConditionTable
  ##
  room_temp_state_global_condition_table = RoomTempStateGlobalConditionTable(db)
  try:
    ##
    ## +--------------+
    ## | Field        |
    ## +--------------+
    ## | now          |
    ## | platform     |
    ## | room_id      |
    ## | allow_count  |
    ## | duration_gap |
    ## +--------------+
    ##
    room_temp_state_global_condition_table_tuple = room_temp_state_global_condition_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    allow_count = get_dict_attr(data, "$.data.room.short_touch_area_config.temp_state_global_condition.allow_count")
    duration_gap = get_dict_attr(data, "$.data.room.short_touch_area_config.temp_state_global_condition.duration_gap")
    
    set_dict_attr(room_temp_state_global_condition_table_tuple, "$.now",          now)
    set_dict_attr(room_temp_state_global_condition_table_tuple, "$.platform",     DOUYIN_PLATFORM)
    set_dict_attr(room_temp_state_global_condition_table_tuple, "$.room_id",      str(room_id))
    set_dict_attr(room_temp_state_global_condition_table_tuple, "$.allow_count",  allow_count)
    set_dict_attr(room_temp_state_global_condition_table_tuple, "$.duration_gap", duration_gap)

    if db.is_table_exist(room_temp_state_global_condition_table.get_name()) is False:
      room_temp_state_global_condition_table.create()
    room_temp_state_global_condition_table.insert_record(room_temp_state_global_condition_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_temp_state_global_condition_table.get_name(), e))
    raise e

  ##
  ## RoomRecordTable
  ##
  room_record_table = RoomRecordTable(db)
  try:
    ##
    ## +-------------------------------------+
    ## | Field                               |
    ## +-------------------------------------+
    ## | now                                 |
    ## | platform                            |
    ## | id                                  |
    ## | rank                                |
    ## | silence_flag                        |
    ## | view_stats_display_long             |
    ## | view_stats_display_long_anchor      |
    ## | view_stats_display_middle           |
    ## | view_stats_display_middle_anchor    |
    ## | view_stats_display_short            |
    ## | view_stats_display_short_anchor     |
    ## | view_stats_display_type             |
    ## | view_stats_display_value            |
    ## | view_stats_display_version          |
    ## | view_stats_incremental              |
    ## | view_stats_is_hidden                |
    ## | user_share_text                     |
    ## | screen_capture_sharing_title        |
    ## | short_title                         |
    ## | lottery_finish_time                 |
    ## | luckymoney_num                      |
    ## | mosaic_status                       |
    ## | mosaic_tip                          |
    ## | popularity                          |
    ## | popularity_str                      |
    ## | pre_enter_time                      |
    ## | preview_copy                        |
    ## | preview_flow_tag                    |
    ## | private_info                        |
    ## | ranklist_audience_type              |
    ## | real_distance                       |
    ## | redpacket_audience_auth             |
    ## | relation_tag                        |
    ## | replay                              |
    ## | replay_location                     |
    ## | room_audit_status                   |
    ## | room_create_ab_param                |
    ## | sofa_layout                         |
    ## | stamps                              |
    ## | comment_count                       |
    ## | digg_count                          |
    ## | dou_plus_promotion                  |
    ## | enter_count                         |
    ## | fan_ticket                          |
    ## | follow_count                        |
    ## | gift_uv_count                       |
    ## | like_count                          |
    ## | money                               |
    ## | total_user                          |
    ## | total_user_desp                     |
    ## | total_user_str                      |
    ## | up_right_stats_str                  |
    ## | up_right_stats_str_complete         |
    ## | user_count_composition_city         |
    ## | user_count_composition_my_follow    |
    ## | user_count_composition_other        |
    ## | user_count_composition_video_detail |
    ## | user_count_str                      |
    ## | watermelon                          |
    ## | welfare_donation_amount             |
    ## | status                              |
    ## | stream_close_time                   |
    ## | stream_id                           |
    ## | stream_provider                     |
    ## | sun_daily_icon_content              |
    ## | challenge_info                      |
    ## | danmaku_detail                      |
    ## | hot_sentence_info                   |
    ## | last_ping_time                      |
    ## | room_like_count                     |
    ## | linker_map                          |
    ## | web_count                           |
    ## | webcast_comment_tcs                 |
    ## | with_aggregate_column               |
    ## | with_draw_something                 |
    ## | with_ktv                            |
    ## | with_linkmic                        |
    ## +-------------------------------------+
    ##
    room_record_table_tuple = room_record_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    id                                  = get_dict_attr(data, "$.data.room.id")
    rank                                = get_dict_attr(data, "$.data.room.living_room_attrs.rank")
    silence_flag                        = get_dict_attr(data, "$.data.room.living_room_attrs.silence_flag")
    view_stats_display_long             = get_dict_attr(data, "$.data.room.room_view_stats.display_long")
    view_stats_display_long_anchor      = get_dict_attr(data, "$.data.room.room_view_stats.display_long_anchor")
    view_stats_display_middle           = get_dict_attr(data, "$.data.room.room_view_stats.display_middle")
    view_stats_display_middle_anchor    = get_dict_attr(data, "$.data.room.room_view_stats.display_middle_anchor")
    view_stats_display_short            = get_dict_attr(data, "$.data.room.room_view_stats.display_short")
    view_stats_display_short_anchor     = get_dict_attr(data, "$.data.room.room_view_stats.display_short_anchor")
    view_stats_display_type             = get_dict_attr(data, "$.data.room.room_view_stats.display_type")
    view_stats_display_value            = get_dict_attr(data, "$.data.room.room_view_stats.display_value")
    view_stats_display_version          = get_dict_attr(data, "$.data.room.room_view_stats.display_version")
    view_stats_incremental              = get_dict_attr(data, "$.data.room.room_view_stats.incremental")
    view_stats_is_hidden                = get_dict_attr(data, "$.data.room.room_view_stats.is_hidden")
    user_share_text                     = get_dict_attr(data, "$.data.room.user_share_text")
    screen_capture_sharing_title        = get_dict_attr(data, "$.data.room.screen_capture_sharing_title")
    short_title                         = get_dict_attr(data, "$.data.room.short_title")
    lottery_finish_time                 = get_dict_attr(data, "$.data.room.lottery_finish_time")
    luckymoney_num                      = get_dict_attr(data, "$.data.room.luckymoney_num")
    mosaic_status                       = get_dict_attr(data, "$.data.room.mosaic_status")
    mosaic_tip                          = get_dict_attr(data, "$.data.room.mosaic_tip")
    popularity                          = get_dict_attr(data, "$.data.room.popularity")
    popularity_str                      = get_dict_attr(data, "$.data.room.popularity_str")
    pre_enter_time                      = get_dict_attr(data, "$.data.room.pre_enter_time")
    preview_copy                        = get_dict_attr(data, "$.data.room.preview_copy")
    preview_flow_tag                    = get_dict_attr(data, "$.data.room.preview_flow_tag")
    private_info                        = get_dict_attr(data, "$.data.room.private_info")
    ranklist_audience_type              = get_dict_attr(data, "$.data.room.ranklist_audience_type")
    real_distance                       = get_dict_attr(data, "$.data.room.real_distance")
    redpacket_audience_auth             = get_dict_attr(data, "$.data.room.redpacket_audience_auth")
    relation_tag                        = get_dict_attr(data, "$.data.room.relation_tag")
    replay                              = get_dict_attr(data, "$.data.room.replay")
    replay_location                     = get_dict_attr(data, "$.data.room.replay_location")
    room_audit_status                   = get_dict_attr(data, "$.data.room.room_audit_status")
    room_create_ab_param                = get_dict_attr(data, "$.data.room.room_create_ab_param")
    sofa_layout                         = get_dict_attr(data, "$.data.room.sofa_layout")
    stamps                              = get_dict_attr(data, "$.data.room.stamps")
    comment_count                       = get_dict_attr(data, "$.data.room.stats.comment_count")
    digg_count                          = get_dict_attr(data, "$.data.room.stats.digg_count")
    dou_plus_promotion                  = get_dict_attr(data, "$.data.room.stats.dou_plus_promotion")
    enter_count                         = get_dict_attr(data, "$.data.room.stats.enter_count")
    fan_ticket                          = get_dict_attr(data, "$.data.room.stats.fan_ticket")
    follow_count                        = get_dict_attr(data, "$.data.room.stats.follow_count")
    gift_uv_count                       = get_dict_attr(data, "$.data.room.stats.gift_uv_count")
    like_count                          = get_dict_attr(data, "$.data.room.stats.like_count")
    money                               = get_dict_attr(data, "$.data.room.stats.money")
    total_user                          = get_dict_attr(data, "$.data.room.stats.total_user")
    total_user_desp                     = get_dict_attr(data, "$.data.room.stats.total_user_desp")
    total_user_str                      = get_dict_attr(data, "$.data.room.stats.total_user_str")
    up_right_stats_str                  = get_dict_attr(data, "$.data.room.stats.up_right_stats_str")
    up_right_stats_str_complete         = get_dict_attr(data, "$.data.room.stats.up_right_stats_str_complete")
    user_count_composition_city         = get_dict_attr(data, "$.data.room.stats.user_count_composition.city")
    user_count_composition_my_follow    = get_dict_attr(data, "$.data.room.stats.user_count_composition.my_follow")
    user_count_composition_other        = get_dict_attr(data, "$.data.room.stats.user_count_composition.other")
    user_count_composition_video_detail = get_dict_attr(data, "$.data.room.stats.user_count_composition.video_detail")
    user_count_str                      = get_dict_attr(data, "$.data.room.stats.user_count_str")
    watermelon                          = get_dict_attr(data, "$.data.room.stats.watermelon")
    welfare_donation_amount             = get_dict_attr(data, "$.data.room.stats.welfare_donation_amount")
    status                              = get_dict_attr(data, "$.data.room.status")
    stream_close_time                   = get_dict_attr(data, "$.data.room.stream_close_time")
    stream_id                           = get_dict_attr(data, "$.data.room.stream_id")
    stream_provider                     = get_dict_attr(data, "$.data.room.stream_provider")
    sun_daily_icon_content              = get_dict_attr(data, "$.data.room.sun_daily_icon_content")
    challenge_info                      = get_dict_attr(data, "$.data.room.challenge_info")
    danmaku_detail                      = get_dict_attr(data, "$.data.room.danmaku_detail")
    hot_sentence_info                   = get_dict_attr(data, "$.data.room.hot_sentence_info")
    last_ping_time                      = get_dict_attr(data, "$.data.room.last_ping_time")
    room_like_count                     = get_dict_attr(data, "$.data.room.like_count")
    linker_map                          = get_dict_attr(data, "$.data.room.linker_map")
    web_count                           = get_dict_attr(data, "$.data.room.web_count")
    webcast_comment_tcs                 = get_dict_attr(data, "$.data.room.webcast_comment_tcs")
    with_aggregate_column               = get_dict_attr(data, "$.data.room.with_aggregate_column")
    with_draw_something                 = get_dict_attr(data, "$.data.room.with_draw_something")
    with_ktv                            = get_dict_attr(data, "$.data.room.with_ktv")
    with_linkmic                        = get_dict_attr(data, "$.data.room.with_linkmic")
    
    set_dict_attr(room_record_table_tuple, "$.now",                                 now)
    set_dict_attr(room_record_table_tuple, "$.platform",                            DOUYIN_PLATFORM)
    set_dict_attr(room_record_table_tuple, "$.id",                                  str(id))
    set_dict_attr(room_record_table_tuple, "$.`rank`",                              rank)
    set_dict_attr(room_record_table_tuple, "$.silence_flag",                        silence_flag)
    set_dict_attr(room_record_table_tuple, "$.view_stats_display_long",             view_stats_display_long)
    set_dict_attr(room_record_table_tuple, "$.view_stats_display_long_anchor",      view_stats_display_long_anchor)
    set_dict_attr(room_record_table_tuple, "$.view_stats_display_middle",           view_stats_display_middle)
    set_dict_attr(room_record_table_tuple, "$.view_stats_display_middle_anchor",    view_stats_display_middle_anchor)
    set_dict_attr(room_record_table_tuple, "$.view_stats_display_short",            view_stats_display_short)
    set_dict_attr(room_record_table_tuple, "$.view_stats_display_short_anchor",     view_stats_display_short_anchor)
    set_dict_attr(room_record_table_tuple, "$.view_stats_display_type",             view_stats_display_type)
    set_dict_attr(room_record_table_tuple, "$.view_stats_display_value",            view_stats_display_value)
    set_dict_attr(room_record_table_tuple, "$.view_stats_display_version",          str(view_stats_display_version))
    set_dict_attr(room_record_table_tuple, "$.view_stats_incremental",              view_stats_incremental)
    set_dict_attr(room_record_table_tuple, "$.view_stats_is_hidden",                view_stats_is_hidden)
    set_dict_attr(room_record_table_tuple, "$.user_share_text",                     user_share_text)
    set_dict_attr(room_record_table_tuple, "$.screen_capture_sharing_title",        screen_capture_sharing_title)
    set_dict_attr(room_record_table_tuple, "$.short_title",                         short_title)
    if lottery_finish_time != 0:
      set_dict_attr(room_record_table_tuple, "$.lottery_finish_time",                 dat.fromtimestamp(lottery_finish_time))
    set_dict_attr(room_record_table_tuple, "$.luckymoney_num",                      luckymoney_num)
    set_dict_attr(room_record_table_tuple, "$.mosaic_status",                       mosaic_status)
    set_dict_attr(room_record_table_tuple, "$.mosaic_tip",                          mosaic_tip)
    set_dict_attr(room_record_table_tuple, "$.popularity",                          popularity)
    set_dict_attr(room_record_table_tuple, "$.popularity_str",                      popularity_str)
    if pre_enter_time != 0:
      set_dict_attr(room_record_table_tuple, "$.pre_enter_time",                      dat.fromtimestamp(pre_enter_time))
    set_dict_attr(room_record_table_tuple, "$.preview_copy",                        preview_copy)
    set_dict_attr(room_record_table_tuple, "$.preview_flow_tag",                    preview_flow_tag)
    set_dict_attr(room_record_table_tuple, "$.private_info",                        private_info)
    set_dict_attr(room_record_table_tuple, "$.ranklist_audience_type",              ranklist_audience_type)
    set_dict_attr(room_record_table_tuple, "$.real_distance",                       real_distance)
    set_dict_attr(room_record_table_tuple, "$.redpacket_audience_auth",             redpacket_audience_auth)
    set_dict_attr(room_record_table_tuple, "$.relation_tag",                        relation_tag)
    set_dict_attr(room_record_table_tuple, "$.replay",                              replay)
    set_dict_attr(room_record_table_tuple, "$.replay_location",                     replay_location)
    set_dict_attr(room_record_table_tuple, "$.room_audit_status",                   room_audit_status)
    set_dict_attr(room_record_table_tuple, "$.room_create_ab_param",                room_create_ab_param)
    set_dict_attr(room_record_table_tuple, "$.sofa_layout",                         sofa_layout)
    set_dict_attr(room_record_table_tuple, "$.stamps",                              stamps)
    set_dict_attr(room_record_table_tuple, "$.comment_count",                       comment_count)
    set_dict_attr(room_record_table_tuple, "$.digg_count",                          digg_count)
    set_dict_attr(room_record_table_tuple, "$.dou_plus_promotion",                  dou_plus_promotion)
    set_dict_attr(room_record_table_tuple, "$.enter_count",                         enter_count)
    set_dict_attr(room_record_table_tuple, "$.fan_ticket",                          fan_ticket)
    set_dict_attr(room_record_table_tuple, "$.follow_count",                        follow_count)
    set_dict_attr(room_record_table_tuple, "$.gift_uv_count",                       gift_uv_count)
    set_dict_attr(room_record_table_tuple, "$.like_count",                          like_count)
    set_dict_attr(room_record_table_tuple, "$.money",                               money)
    set_dict_attr(room_record_table_tuple, "$.total_user",                          total_user)
    set_dict_attr(room_record_table_tuple, "$.total_user_desp",                     total_user_desp)
    set_dict_attr(room_record_table_tuple, "$.total_user_str",                      total_user_str)
    set_dict_attr(room_record_table_tuple, "$.up_right_stats_str",                  up_right_stats_str)
    set_dict_attr(room_record_table_tuple, "$.up_right_stats_str_complete",         up_right_stats_str_complete)
    set_dict_attr(room_record_table_tuple, "$.user_count_composition_city",         user_count_composition_city)
    set_dict_attr(room_record_table_tuple, "$.user_count_composition_my_follow",    user_count_composition_my_follow)
    set_dict_attr(room_record_table_tuple, "$.user_count_composition_other",        user_count_composition_other)
    set_dict_attr(room_record_table_tuple, "$.user_count_composition_video_detail", user_count_composition_video_detail)
    set_dict_attr(room_record_table_tuple, "$.user_count_str",                      user_count_str)
    set_dict_attr(room_record_table_tuple, "$.watermelon",                          watermelon)
    set_dict_attr(room_record_table_tuple, "$.welfare_donation_amount",             welfare_donation_amount)
    set_dict_attr(room_record_table_tuple, "$.status",                              status)
    if stream_close_time != 0:
      set_dict_attr(room_record_table_tuple, "$.stream_close_time",                   dat.fromtimestamp(stream_close_time))
    set_dict_attr(room_record_table_tuple, "$.stream_id",                           str(stream_id))
    set_dict_attr(room_record_table_tuple, "$.stream_provider",                     stream_provider)
    set_dict_attr(room_record_table_tuple, "$.sun_daily_icon_content",              sun_daily_icon_content)
    set_dict_attr(room_record_table_tuple, "$.challenge_info",                      challenge_info)
    set_dict_attr(room_record_table_tuple, "$.danmaku_detail",                      danmaku_detail)
    set_dict_attr(room_record_table_tuple, "$.hot_sentence_info",                   hot_sentence_info)
    if last_ping_time != 0:
      set_dict_attr(room_record_table_tuple, "$.last_ping_time",                      dat.fromtimestamp(last_ping_time))
    set_dict_attr(room_record_table_tuple, "$.room_like_count",                     room_like_count)
    set_dict_attr(room_record_table_tuple, "$.linker_map",                          json.dumps(linker_map))
    set_dict_attr(room_record_table_tuple, "$.web_count",                           web_count)
    set_dict_attr(room_record_table_tuple, "$.webcast_comment_tcs",                 webcast_comment_tcs)
    set_dict_attr(room_record_table_tuple, "$.with_aggregate_column",               with_aggregate_column)
    set_dict_attr(room_record_table_tuple, "$.with_draw_something",                 with_draw_something)
    set_dict_attr(room_record_table_tuple, "$.with_ktv",                            with_ktv)
    set_dict_attr(room_record_table_tuple, "$.with_linkmic",                        with_linkmic)

    if db.is_table_exist(room_record_table.get_name()) is False:
      room_record_table.create()
    room_record_table.insert_record(room_record_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_record_table.get_name(), e))
    raise e

  ##
  ## LiveStreamTable
  ##
  live_stream_table = LiveStreamTable(db)
  try:
    ##
    ## +------------------------------------------+
    ## | Field                                    |
    ## +------------------------------------------+
    ## | default_resolution                       |
    ## | anchor_interact_profile                  |
    ## | audience_interact_profile                |
    ## | bframe_enable                            |
    ## | bitrate_adapt_strategy                   |
    ## | bytevc1_enable                           |
    ## | default_bitrate                          |
    ## | fps                                      |
    ## | gop_sec                                  |
    ## | h265_enable                              |
    ## | hardware_encode                          |
    ## | height                                   |
    ## | max_bitrate                              |
    ## | min_bitrate                              |
    ## | roi                                      |
    ## | sw_roi                                   |
    ## | video_profile                            |
    ## | width                                    |
    ## | resolution_name                          |
    ## | flv_pull_url                             |
    ## | flv_pull_url_params                      |
    ## | hls_pull_url                             |
    ## | hls_pull_url_map                         |
    ## | hls_pull_url_params                      |
    ## | id                                       |
    ## | provider                                 |
    ## | pull_datas                               |
    ## | push_datas                               |
    ## | push_stream_type                         |
    ## | rtmp_pull_url                            |
    ## | rtmp_pull_url_params                     |
    ## | rtmp_push_url                            |
    ## | rtmp_push_url_params                     |
    ## | stream_control_type                      |
    ## | stream_orientation                       |
    ## | vr_type                                  |
    ## +------------------------------------------+
    ##
    live_stream_table_tuple = live_stream_table.get_tuple()
    default_resolution         = get_dict_attr(data, "$.data.room.stream_url.default_resolution")
    anchor_interact_profile    = get_dict_attr(data, "$.data.room.stream_url.extra.anchor_interact_profile")
    audience_interact_profile  = get_dict_attr(data, "$.data.room.stream_url.extra.audience_interact_profile")
    bframe_enable              = get_dict_attr(data, "$.data.room.stream_url.extra.bframe_enable")
    bitrate_adapt_strategy     = get_dict_attr(data, "$.data.room.stream_url.extra.bitrate_adapt_strategy")
    bytevc1_enable             = get_dict_attr(data, "$.data.room.stream_url.extra.bytevc1_enable")
    default_bitrate            = get_dict_attr(data, "$.data.room.stream_url.extra.default_bitrate")
    fps                        = get_dict_attr(data, "$.data.room.stream_url.extra.fps")
    gop_sec                    = get_dict_attr(data, "$.data.room.stream_url.extra.gop_sec")
    h265_enable                = get_dict_attr(data, "$.data.room.stream_url.extra.h265_enable")
    hardware_encode            = get_dict_attr(data, "$.data.room.stream_url.extra.hardware_encode")
    height                     = get_dict_attr(data, "$.data.room.stream_url.extra.height")
    max_bitrate                = get_dict_attr(data, "$.data.room.stream_url.extra.max_bitrate")
    min_bitrate                = get_dict_attr(data, "$.data.room.stream_url.extra.min_bitrate")
    roi                        = get_dict_attr(data, "$.data.room.stream_url.extra.roi")
    sw_roi                     = get_dict_attr(data, "$.data.room.stream_url.extra.sw_roi")
    video_profile              = get_dict_attr(data, "$.data.room.stream_url.extra.video_profile")
    width                      = get_dict_attr(data, "$.data.room.stream_url.extra.width")
    resolution_name            = get_dict_attr(data, "$.data.room.stream_url.resolution_name")
    flv_pull_url               = get_dict_attr(data, "$.data.room.stream_url.flv_pull_url")
    flv_pull_url_params        = get_dict_attr(data, "$.data.room.stream_url.flv_pull_url_params")
    hls_pull_url               = get_dict_attr(data, "$.data.room.stream_url.hls_pull_url")
    hls_pull_url_map           = get_dict_attr(data, "$.data.room.stream_url.hls_pull_url_map")
    hls_pull_url_params        = get_dict_attr(data, "$.data.room.stream_url.hls_pull_url_params")
    id                         = get_dict_attr(data, "$.data.room.stream_url.id")
    provider                   = get_dict_attr(data, "$.data.room.stream_url.provider")
    pull_datas                 = get_dict_attr(data, "$.data.room.stream_url.pull_datas")
    push_datas                 = get_dict_attr(data, "$.data.room.stream_url.push_datas")
    push_stream_type           = get_dict_attr(data, "$.data.room.stream_url.push_stream_type")
    rtmp_pull_url              = get_dict_attr(data, "$.data.room.stream_url.rtmp_pull_url")
    rtmp_pull_url_params       = get_dict_attr(data, "$.data.room.stream_url.rtmp_pull_url_params")
    rtmp_push_url              = get_dict_attr(data, "$.data.room.stream_url.rtmp_push_url")
    rtmp_push_url_params       = get_dict_attr(data, "$.data.room.stream_url.rtmp_push_url_params")
    stream_control_type        = get_dict_attr(data, "$.data.room.stream_url.stream_control_type")
    stream_orientation         = get_dict_attr(data, "$.data.room.stream_url.stream_orientation")
    vr_type                    = get_dict_attr(data, "$.data.room.stream_url.vr_type")
    
    set_dict_attr(live_stream_table_tuple, "$.default_resolution",        default_resolution)
    set_dict_attr(live_stream_table_tuple, "$.anchor_interact_profile",   anchor_interact_profile)
    set_dict_attr(live_stream_table_tuple, "$.audience_interact_profile", audience_interact_profile)
    set_dict_attr(live_stream_table_tuple, "$.bframe_enable",             bframe_enable)
    set_dict_attr(live_stream_table_tuple, "$.bitrate_adapt_strategy",    bitrate_adapt_strategy)
    set_dict_attr(live_stream_table_tuple, "$.bytevc1_enable",            bytevc1_enable)
    set_dict_attr(live_stream_table_tuple, "$.default_bitrate",           default_bitrate)
    set_dict_attr(live_stream_table_tuple, "$.fps",                       fps)
    set_dict_attr(live_stream_table_tuple, "$.gop_sec",                   gop_sec)
    set_dict_attr(live_stream_table_tuple, "$.h265_enable",               h265_enable)
    set_dict_attr(live_stream_table_tuple, "$.hardware_encode",           hardware_encode)
    set_dict_attr(live_stream_table_tuple, "$.height",                    height)
    set_dict_attr(live_stream_table_tuple, "$.max_bitrate",               max_bitrate)
    set_dict_attr(live_stream_table_tuple, "$.min_bitrate",               min_bitrate)
    set_dict_attr(live_stream_table_tuple, "$.roi",                       roi)
    set_dict_attr(live_stream_table_tuple, "$.sw_roi",                    sw_roi)
    set_dict_attr(live_stream_table_tuple, "$.video_profile",             video_profile)
    set_dict_attr(live_stream_table_tuple, "$.width",                     width)
    set_dict_attr(live_stream_table_tuple, "$.resolution_name",           json.dumps(resolution_name))
    set_dict_attr(live_stream_table_tuple, "$.flv_pull_url",              json.dumps(flv_pull_url))
    set_dict_attr(live_stream_table_tuple, "$.flv_pull_url_params",       json.dumps(flv_pull_url_params))
    set_dict_attr(live_stream_table_tuple, "$.hls_pull_url",              hls_pull_url)
    set_dict_attr(live_stream_table_tuple, "$.hls_pull_url_map",          json.dumps(hls_pull_url_map))
    set_dict_attr(live_stream_table_tuple, "$.hls_pull_url_params",       json.dumps(hls_pull_url_params))
    set_dict_attr(live_stream_table_tuple, "$.id",                        str(id))
    set_dict_attr(live_stream_table_tuple, "$.provider",                  provider)
    set_dict_attr(live_stream_table_tuple, "$.pull_datas",                json.dumps(pull_datas))
    set_dict_attr(live_stream_table_tuple, "$.push_datas",                json.dumps(push_datas))
    set_dict_attr(live_stream_table_tuple, "$.push_stream_type",          push_stream_type)
    set_dict_attr(live_stream_table_tuple, "$.rtmp_pull_url",             rtmp_pull_url)
    set_dict_attr(live_stream_table_tuple, "$.rtmp_pull_url_params",      json.dumps(rtmp_pull_url_params))
    set_dict_attr(live_stream_table_tuple, "$.rtmp_push_url",             rtmp_push_url)
    set_dict_attr(live_stream_table_tuple, "$.rtmp_push_url_params",      rtmp_push_url_params)
    set_dict_attr(live_stream_table_tuple, "$.stream_control_type",       stream_control_type)
    set_dict_attr(live_stream_table_tuple, "$.stream_orientation",        stream_orientation)
    set_dict_attr(live_stream_table_tuple, "$.vr_type",                   vr_type)

    if db.is_table_exist(live_stream_table.get_name()) is False:
      live_stream_table.create()
    live_stream_table.insert_record(live_stream_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(live_stream_table.get_name(), e))
    raise e

  ##
  ## StreamCandidateResolutionTable
  ##
  stream_candidate_resulution_table = StreamCandidateResolutionTable(db)
  try:
    ##
    ## +----------------------+
    ## | Field                |
    ## +----------------------+
    ## | now                  |
    ## | platform             |
    ## | room_id              |
    ## | stream_id            |
    ## | resolution_index     |
    ## | candidate_resolution |
    ## +----------------------+
    ##
    stream_candidate_resulution_table_tuple = stream_candidate_resulution_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    stream_id = get_dict_attr(data, "$.data.room.stream_id")
    # resolution_index auto increment
    candidate_resolutions = get_dict_attr(data, "$.data.room.stream_url.candidate_resolution")
    if len(candidate_resolutions) != 0:
      set_dict_attr(stream_candidate_resulution_table_tuple, "$.now",                  now)
      set_dict_attr(stream_candidate_resulution_table_tuple, "$.platform",             DOUYIN_PLATFORM)
      set_dict_attr(stream_candidate_resulution_table_tuple, "$.room_id",              str(room_id))
      set_dict_attr(stream_candidate_resulution_table_tuple, "$.stream_id",            str(stream_id))
      for candidate_resolution in candidate_resolutions:
        # resolution_index auto increment
        if not isinstance(candidate_resolution, str):
          raise TypeError
        set_dict_attr(stream_candidate_resulution_table_tuple, "$.candidate_resolution", candidate_resolution)
      
        if db.is_table_exist(stream_candidate_resulution_table.get_name()) is False:
          stream_candidate_resulution_table.create()
        stream_candidate_resulution_table.insert_record(stream_candidate_resulution_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(stream_candidate_resulution_table.get_name(), e))
    raise e

  ##
  ## StreamCompletePushUrlTable
  ##
  stream_complete_push_url_table = StreamCompletePushUrlTable(db)
  try:
    ##
    ## +-------------------------+
    ## | Field                   |
    ## +-------------------------+
    ## | now                     |
    ## | platform                |
    ## | room_id                 |
    ## | stream_id               |
    ## | complete_push_url_index |
    ## | complete_push_url       |
    ## +-------------------------+
    ##
    stream_complete_push_url_table_tuple = stream_complete_push_url_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    stream_id = get_dict_attr(data, "$.data.room.stream_id")
    # complete_push_url_index auto increment
    complete_push_urls = get_dict_attr(data, "$.data.room.stream_url.complete_push_urls")
    if complete_push_urls is None:
      get_logger().warning("none found complete_push_urls")
      return
    
    set_dict_attr(stream_complete_push_url_table_tuple, "$.now",                  now)
    set_dict_attr(stream_complete_push_url_table_tuple, "$.platform",             DOUYIN_PLATFORM)
    set_dict_attr(stream_complete_push_url_table_tuple, "$.room_id",              str(room_id))
    set_dict_attr(stream_complete_push_url_table_tuple, "$.stream_id",            str(stream_id))
    for complete_push_url in complete_push_urls:
      # complete_push_url_index auto increment
      set_dict_attr(stream_complete_push_url_table_tuple, "$.complete_push_url", complete_push_url)
    
      if db.is_table_exist(stream_complete_push_url_table.get_name()) is False:
        stream_complete_push_url_table.create()
      stream_complete_push_url_table.insert_record(stream_complete_push_url_table_tuple)    
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(stream_complete_push_url_table.get_name(), e))
    raise e

  ##
  ## LiveCoreSdkDataTable
  ##
  live_core_sdk_data_table = LiveCoreSdkDataTable(db)
  try:
    ##
    ## +----------+
    ## | Field    |
    ## +----------+
    ## | now      |
    ## | platform |
    ## | room_id  |
    ## | size     |
    ## +----------+
    ##
    live_core_sdk_data_table_tuple = live_core_sdk_data_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    size = get_dict_attr(data, "$.data.room.stream_url.live_core_sdk_data.size")
    
    set_dict_attr(live_core_sdk_data_table_tuple, "$.now",      now)
    set_dict_attr(live_core_sdk_data_table_tuple, "$.platform", DOUYIN_PLATFORM)
    set_dict_attr(live_core_sdk_data_table_tuple, "$.room_id",  str(room_id))
    set_dict_attr(live_core_sdk_data_table_tuple, "$.size",     size)

    if db.is_table_exist(live_core_sdk_data_table.get_name()) is False:
      live_core_sdk_data_table.create()
    live_core_sdk_data_table.insert_record(live_core_sdk_data_table_tuple) 
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(live_core_sdk_data_table.get_name(), e))
    raise e

  ##
  ## LiveCoreSdkPullDataTable
  ##
  live_core_sdk_pull_data_table = LiveCoreSdkPullDataTable(db)
  try:
    ##
    ## +----------------------+
    ## | Field                |
    ## +----------------------+
    ## | now                  |
    ## | platform             |
    ## | room_id              |
    ## | codec                |
    ## | compensatory_data    |
    ## | hls_data_unencrypted |
    ## | kind                 |
    ## | stream_data          |
    ## | version              |
    ## +----------------------+
    ##
    live_core_sdk_pull_data_table_tuple = live_core_sdk_pull_data_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    codec                = get_dict_attr(data, "$.data.room.stream_url.live_core_sdk_data.pull_data.codec")
    compensatory_data    = get_dict_attr(data, "$.data.room.stream_url.live_core_sdk_data.pull_data.compensatory_data")
    hls_data_unencrypted = get_dict_attr(data, "$.data.room.stream_url.live_core_sdk_data.pull_data.hls_data_unencrypted")
    kind                 = get_dict_attr(data, "$.data.room.stream_url.live_core_sdk_data.pull_data.kind")
    stream_data          = get_dict_attr(data, "$.data.room.stream_url.live_core_sdk_data.pull_data.stream_data")
    version              = get_dict_attr(data, "$.data.room.stream_url.live_core_sdk_data.pull_data.version")
    
    set_dict_attr(live_core_sdk_pull_data_table_tuple, "$.now",                  now)
    set_dict_attr(live_core_sdk_pull_data_table_tuple, "$.platform",             DOUYIN_PLATFORM)
    set_dict_attr(live_core_sdk_pull_data_table_tuple, "$.room_id",              str(room_id))
    set_dict_attr(live_core_sdk_pull_data_table_tuple, "$.codec",                codec)
    set_dict_attr(live_core_sdk_pull_data_table_tuple, "$.compensatory_data",    compensatory_data)
    set_dict_attr(live_core_sdk_pull_data_table_tuple, "$.hls_data_unencrypted", json.dumps(hls_data_unencrypted))
    set_dict_attr(live_core_sdk_pull_data_table_tuple, "$.kind",                 kind)
    set_dict_attr(live_core_sdk_pull_data_table_tuple, "$.stream_data",          stream_data)
    set_dict_attr(live_core_sdk_pull_data_table_tuple, "$.version",              str(version))

    if db.is_table_exist(live_core_sdk_pull_data_table.get_name()) is False:
      live_core_sdk_pull_data_table.create()
    live_core_sdk_pull_data_table.insert_record(live_core_sdk_pull_data_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(stream_complete_push_url_table.get_name(), e))
    raise e

  ##
  ## LiveCoreSdkPullFlvDataTable
  ##
  live_core_sdk_pull_flv_data_table = LiveCoreSdkPullFlvDataTable(db)
  try:
    ##
    ## +-----------+
    ## | Field     |
    ## +-----------+
    ## | now       |
    ## | platform  |
    ## | room_id   |
    ## | Flv_index |
    ## | Flv       |
    ## +-----------+
    ##
    live_core_sdk_pull_flv_data_table_tuple = live_core_sdk_pull_flv_data_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    Flvs = get_dict_attr(data, "$.data.room.stream_url.live_core_sdk_data.pull_data.Flv")
    if len(Flvs) != 0:
      set_dict_attr(live_core_sdk_pull_flv_data_table_tuple, "$.now",                  now)
      set_dict_attr(live_core_sdk_pull_flv_data_table_tuple, "$.platform",             DOUYIN_PLATFORM)
      set_dict_attr(live_core_sdk_pull_flv_data_table_tuple, "$.room_id",              str(room_id))
  
      for Flv in Flvs:
        # Flv_index auto increment
        set_dict_attr(live_core_sdk_pull_flv_data_table_tuple, "$.Flv",                  Flv)
  
      if db.is_table_exist(live_core_sdk_pull_flv_data_table.get_name()) is False:
        live_core_sdk_pull_flv_data_table.create()
      live_core_sdk_pull_flv_data_table.insert_record(live_core_sdk_pull_flv_data_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(live_core_sdk_pull_flv_data_table.get_name(), e))
    raise e

  ##
  ## LiveCoreSdkPullHlsDataTable
  ##
  live_core_sdk_pull_hls_data_table = LiveCoreSdkPullHlsDataTable(db)
  try:
    ##
    ## +-----------+
    ## | Field     |
    ## +-----------+
    ## | now       |
    ## | platform  |
    ## | room_id   |
    ## | Hls_index |
    ## | Hls       |
    ## +-----------+
    ##
    live_core_sdk_pull_hls_data_table_tuple = live_core_sdk_pull_hls_data_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    Hlses = get_dict_attr(data, "$.data.room.stream_url.live_core_sdk_data.pull_data.Hls")
    if len(Hlses) != 0:
      set_dict_attr(live_core_sdk_pull_hls_data_table_tuple, "$.now",                  now)
      set_dict_attr(live_core_sdk_pull_hls_data_table_tuple, "$.platform",             DOUYIN_PLATFORM)
      set_dict_attr(live_core_sdk_pull_hls_data_table_tuple, "$.room_id",              str(room_id))
      for Hls in Hlses:
        # Hls_index auto increment
        set_dict_attr(live_core_sdk_pull_hls_data_table_tuple, "$.Hls",                  Hls)
      
        if db.is_table_exist(live_core_sdk_pull_hls_data_table.get_name()) is False:
          live_core_sdk_pull_hls_data_table.create()
        live_core_sdk_pull_hls_data_table.insert_record(live_core_sdk_pull_hls_data_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(live_core_sdk_pull_hls_data_table.get_name(), e))
    raise e

  ##
  ## LiveCoreSdkPullDataOptionTable
  ##
  live_core_sdk_pull_data_option_table = LiveCoreSdkPullDataOptionTable(db)
  try:
    ##
    ## +---------------+
    ## | Field         |
    ## +---------------+
    ## | now           |
    ## | platform      |
    ## | room_id       |
    ## | vpass_default |
    ## +---------------+
    ##
    live_core_sdk_pull_data_option_table_tuple = live_core_sdk_pull_data_option_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    vpass_default = get_dict_attr(data, "$.data.room.stream_url.live_core_sdk_data.pull_data.options.vpass_default")
    
    set_dict_attr(live_core_sdk_pull_data_option_table_tuple, "$.now",                  now)
    set_dict_attr(live_core_sdk_pull_data_option_table_tuple, "$.platform",             DOUYIN_PLATFORM)
    set_dict_attr(live_core_sdk_pull_data_option_table_tuple, "$.room_id",              str(room_id))
    set_dict_attr(live_core_sdk_pull_data_option_table_tuple, "$.vpass_default",        vpass_default)

    if db.is_table_exist(live_core_sdk_pull_data_option_table.get_name()) is False:
      live_core_sdk_pull_data_option_table.create()
    
    if vpass_default is not None:
      live_core_sdk_pull_data_option_table.insert_record(live_core_sdk_pull_data_option_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(live_core_sdk_pull_data_option_table.get_name(), e))
    raise e

  ##
  ## LiveCoreSdkPullQualityDataTable
  ##
  live_core_sdk_pull_quality_data_table = LiveCoreSdkPullQualityDataTable(db)
  try:
    ##
    ## +--------------------+
    ## | Field              |
    ## +--------------------+
    ## | now                |
    ## | platform           |
    ## | room_id            |
    ## | quality_index      |
    ## | additional_content |
    ## | disable            |
    ## | fps                |
    ## | level              |
    ## | name               |
    ## | resolution         |
    ## | sdk_key            |
    ## | v_bit_rate         |
    ## | v_codec            |
    ## +--------------------+
    ##
    live_core_sdk_pull_quality_data_table_tuple = live_core_sdk_pull_quality_data_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    # quality_index auto increment
    qualities          = get_dict_attr(data, "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities")
    if len(qualities) != 0:
      set_dict_attr(live_core_sdk_pull_quality_data_table_tuple, "$.now",                  now)
      set_dict_attr(live_core_sdk_pull_quality_data_table_tuple, "$.platform",             DOUYIN_PLATFORM)
      set_dict_attr(live_core_sdk_pull_quality_data_table_tuple, "$.room_id",              str(room_id))

      for quality in qualities:
        additional_content = get_dict_attr(quality, "$.additional_content")
        disable            = get_dict_attr(quality, "$.disable")
        fps                = get_dict_attr(quality, "$.fps")
        level              = get_dict_attr(quality, "$.level")
        name               = get_dict_attr(quality, "$.name")
        resolution         = get_dict_attr(quality, "$.resolution")
        sdk_key            = get_dict_attr(quality, "$.sdk_key")
        v_bit_rate         = get_dict_attr(quality, "$.v_bit_rate")
        v_codec            = get_dict_attr(quality, "$.v_codec")
        
        # quality_index auto increment
        set_dict_attr(live_core_sdk_pull_quality_data_table_tuple, "$.additional_content",   additional_content)
        set_dict_attr(live_core_sdk_pull_quality_data_table_tuple, "$.disable",              disable)
        set_dict_attr(live_core_sdk_pull_quality_data_table_tuple, "$.fps",                  fps)
        set_dict_attr(live_core_sdk_pull_quality_data_table_tuple, "$.level",                level)
        set_dict_attr(live_core_sdk_pull_quality_data_table_tuple, "$.name",                 name)
        set_dict_attr(live_core_sdk_pull_quality_data_table_tuple, "$.resolution",           resolution)
        set_dict_attr(live_core_sdk_pull_quality_data_table_tuple, "$.sdk_key",              sdk_key)
        set_dict_attr(live_core_sdk_pull_quality_data_table_tuple, "$.v_bit_rate",           v_bit_rate)
        set_dict_attr(live_core_sdk_pull_quality_data_table_tuple, "$.v_codec",              v_codec)
        
        if db.is_table_exist(live_core_sdk_pull_quality_data_table.get_name()) is False:
          live_core_sdk_pull_quality_data_table.create()
        live_core_sdk_pull_quality_data_table.insert_record(live_core_sdk_pull_quality_data_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(live_core_sdk_pull_quality_data_table.get_name(), e))
    raise e

  ##
  ## LiveCoreSdkPullDefaultQualityDataTable
  ##
  live_core_sdk_pull_default_quality_data_table = LiveCoreSdkPullDefaultQualityDataTable(db)
  try:
    ##
    ## +--------------------+
    ## | Field              |
    ## +--------------------+
    ## | now                |
    ## | platform           |
    ## | room_id            |
    ## | additional_content |
    ## | disable            |
    ## | fps                |
    ## | level              |
    ## | name               |
    ## | resolution         |
    ## | sdk_key            |
    ## | v_bit_rate         |
    ## | v_codec            |
    ## +--------------------+
    ##
    live_core_sdk_pull_default_quality_data_table_tuple = live_core_sdk_pull_default_quality_data_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    # quality_index auto increment
    additional_content = get_dict_attr(data, "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.additional_content")
    disable            = get_dict_attr(data, "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.disable")
    fps                = get_dict_attr(data, "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.fps")
    level              = get_dict_attr(data, "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.level")
    name               = get_dict_attr(data, "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.name")
    resolution         = get_dict_attr(data, "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.resolution")
    sdk_key            = get_dict_attr(data, "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.sdk_key")
    v_bit_rate         = get_dict_attr(data, "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.v_bit_rate")
    v_codec            = get_dict_attr(data, "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.v_codec")
    
    set_dict_attr(live_core_sdk_pull_default_quality_data_table_tuple, "$.now",                  now)
    set_dict_attr(live_core_sdk_pull_default_quality_data_table_tuple, "$.platform",             DOUYIN_PLATFORM)
    set_dict_attr(live_core_sdk_pull_default_quality_data_table_tuple, "$.room_id",              str(room_id))
    set_dict_attr(live_core_sdk_pull_default_quality_data_table_tuple, "$.additional_content",   additional_content)
    set_dict_attr(live_core_sdk_pull_default_quality_data_table_tuple, "$.disable",              disable)
    set_dict_attr(live_core_sdk_pull_default_quality_data_table_tuple, "$.fps",                  fps)
    set_dict_attr(live_core_sdk_pull_default_quality_data_table_tuple, "$.level",                level)
    set_dict_attr(live_core_sdk_pull_default_quality_data_table_tuple, "$.name",                 name)
    set_dict_attr(live_core_sdk_pull_default_quality_data_table_tuple, "$.resolution",           resolution)
    set_dict_attr(live_core_sdk_pull_default_quality_data_table_tuple, "$.sdk_key",              sdk_key)
    set_dict_attr(live_core_sdk_pull_default_quality_data_table_tuple, "$.v_bit_rate",           v_bit_rate)
    set_dict_attr(live_core_sdk_pull_default_quality_data_table_tuple, "$.v_codec",              v_codec)

    if db.is_table_exist(live_core_sdk_pull_default_quality_data_table.get_name()) is False:
      live_core_sdk_pull_default_quality_data_table.create()
    live_core_sdk_pull_default_quality_data_table.insert_record(live_core_sdk_pull_default_quality_data_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(live_core_sdk_pull_default_quality_data_table.get_name(), e))
    raise e
  
  ##
  ## StreamPushUrlTable
  ##
  stream_push_url_table = StreamPushUrlTable(db)
  try:
    ##
    ## +----------------+
    ## | Field          |
    ## +----------------+
    ## | now            |
    ## | platform       |
    ## | room_id        |
    ## | stream_url_id  |
    ## | push_url_index |
    ## | push_url       |
    ## +----------------+
    ##
    stream_push_url_table_tuple = stream_push_url_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    stream_url_id = get_dict_attr(data, "$.data.room.stream_url.id")
    # push_url_index auto increment
    push_urls = get_dict_attr(data, "$.data.room.stream_url.push_urls")
    if len(push_urls) != 0:
      set_dict_attr(stream_push_url_table_tuple, "$.now",                  now)
      set_dict_attr(stream_push_url_table_tuple, "$.platform",             DOUYIN_PLATFORM)
      set_dict_attr(stream_push_url_table_tuple, "$.room_id",              str(room_id))
      set_dict_attr(stream_push_url_table_tuple, "$.stream_url_id",        str(stream_url_id))
      for push_url in push_urls:
        # push_url_index auto increment
        set_dict_attr(stream_push_url_table_tuple, "$.push_url",           push_url)
        if db.is_table_exist(stream_push_url_table.get_name()) is False:
          stream_push_url_table.create()
        stream_push_url_table.insert_record(stream_push_url_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(stream_push_url_table.get_name(), e))
    raise e      

  ##
  ## RoomTagTable
  ##
  room_tag_table = RoomTagTable(db)
  try:
    ##
    ## +-----------+
    ## | Field     |
    ## +-----------+
    ## | now       |
    ## | platform  |
    ## | room_id   |
    ## | tag_index |
    ## | tag       |
    ## +-----------+
    ##
    room_tag_table_tuple = room_tag_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    # tag_index
    tags = get_dict_attr(data, "$.data.room.tags")
    if len(tags) != 0:
      set_dict_attr(room_tag_table_tuple, "$.now",       now)
      set_dict_attr(room_tag_table_tuple, "$.platform",  DOUYIN_PLATFORM)
      set_dict_attr(room_tag_table_tuple, "$.room_id",   str(room_id))
      for tag in tags:
        # tag_index auto increment
        set_dict_attr(room_tag_table_tuple, "$.tag",       tag)
  
        if db.is_table_exist(room_tag_table.get_name()) is False:
          room_tag_table.create()
        room_tag_table.insert_record(room_tag_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_tag_table.get_name(), e))
    raise e

  ##
  ## RoomTopFansTable
  ##
  room_top_fans_table = RoomTopFansTable(db)
  try:
    ##
    ## +------------+
    ## | Field      |
    ## +------------+
    ## | now        |
    ## | platform   |
    ## | room_id    |
    ## | fans_index |
    ## | top_fans   |
    ## +------------+
    ##
    room_top_fans_table_tuple = room_top_fans_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    # fans_index = get_dict_attr(data, "$.data.room.fans_index")
    top_fans = get_dict_attr(data, "$.data.room.top_fans")
    if len(top_fans) != 0:
      set_dict_attr(room_top_fans_table_tuple, "$.now",      now)
      set_dict_attr(room_top_fans_table_tuple, "$.platform", DOUYIN_PLATFORM)
      set_dict_attr(room_top_fans_table_tuple, "$.room_id",  str(room_id))
      
      for top_fan in top_fans:
        # set_dict_attr(room_top_fans_table_tuple, "$.fans_index", fans_index)
        set_dict_attr(room_top_fans_table_tuple, "$.top_fans",   top_fan)
        
        if db.is_table_exist(room_top_fans_table.get_name()) is False:
          room_top_fans_table.create()
        room_top_fans_table.insert_record(room_top_fans_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_top_fans_table.get_name(), e))
    raise e

  """
  ##
  ## RoomUpperRightWidgetDataTable
  ## TBD
  ##
  room_upper_right_widget_data_table = RoomUpperRightWidgetDataTable(db)
  try:
    ##
    ## +-------------------------------+
    ## | Field                         |
    ## +-------------------------------+
    ## | now                           |
    ## | platform                      |
    ## | room_id                       |
    ## | upper_right_widget_data_index |
    ## | upper_right_widget_data       |
    ## +-------------------------------+
    ##
    room_upper_right_widget_data_table_tuple = room_upper_right_widget_data_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    # upper_right_widget_data_index
    upper_right_widget_data_list = get_dict_attr(data, "$.data.room.upper_right_widget_data")
    if upper_right_widget_data_list is None:
    return

    set_dict_attr(room_upper_right_widget_data_table_tuple, "$.now",       now)
    set_dict_attr(room_upper_right_widget_data_table_tuple, "$.platform",  DOUYIN_PLATFORM)
    set_dict_attr(room_upper_right_widget_data_table_tuple, "$.room_id",   room_id)
    for upper_right_widget_data in upper_right_widget_data_list:
        # set_dict_attr(room_upper_right_widget_data_table_tuple, "$.upper_right_widget_data_index", index)
        set_dict_attr(room_upper_right_widget_data_table_tuple, "$.upper_right_widget_data", upper_right_widget_data)

        if db.is_table_exist(room_upper_right_widget_data_table.get_name()) is False:
            room_upper_right_widget_data_table.create()
        room_upper_right_widget_data_table.insert_record(room_upper_right_widget_data_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_upper_right_widget_data_table.get_name(), e))
    raise e
  
  ##
  ## RoomVsRoleTable
  ## TBD
  ##
  room_vs_role_table = RoomVsRoleTable(db)
  try:
    ##
    ## +---------------+
    ## | Field         |
    ## +---------------+
    ## | now           |
    ## | platform      |
    ## | room_id       |
    ## | vs_role_index |
    ## | vs_role       |
    ## +---------------+
    ##
    room_vs_role_table_tuple = room_vs_role_table.get_tuple()
    # now = get_dict_attr(data, "$.extra.now")
    # DOUYIN_PLATFORM = "douyin"
    # room_id = get_dict_attr(data, "$.data.room.id")
    # vs_role_index
    vs_roles = get_dict_attr(data, "$.data.room.vs_roles")
    if vs_roles is None:
      return
    
    set_dict_attr(room_vs_role_table_tuple, "$.now",       now)
    set_dict_attr(room_vs_role_table_tuple, "$.platform",  DOUYIN_PLATFORM)
    set_dict_attr(room_vs_role_table_tuple, "$.room_id",   str(room_id))
    for vs_role in vs_roles:
      # set_dict_attr(room_vs_role_table_tuple, "$.vs_role_index", vs_role_index)
      set_dict_attr(room_vs_role_table_tuple, "$.vs_role",       vs_role)

      if db.is_table_exist(room_vs_role_table.get_name()) is False:
        room_vs_role_table.create()
      room_vs_role_table.insert_record(room_vs_role_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_vs_role_table.get_name(), e))
    raise e
  """
  ##
  ## PictureTable
  ##
  picture_table = PictureTable(db)
  try:
    ##
    ## +--------------+
    ## | Field        |
    ## +--------------+
    ## | picture_index|
    ## | label        |
    ## | avg_color    |
    ## | height       |
    ## | image_type   |
    ## | is_animated  |
    ## | open_web_url |
    ## | uri          |
    ## | width        |
    ## +--------------+
    ##
    picture_table_tuple = picture_table.get_tuple()
    
    ##
    ## <=========================== cover ==================================>
    ##
    cover = get_dict_attr(data, "$.data.room.cover")
    # picture_index auto increment
    label        = "cover"
    avg_color    = get_dict_attr(cover, "$.avg_color")
    height       = get_dict_attr(cover, "$.height")
    image_type   = get_dict_attr(cover, "$.image_type")
    is_animated  = get_dict_attr(cover, "$.is_animated")
    open_web_url = get_dict_attr(cover, "$.open_web_url")
    uri          = get_dict_attr(cover, "$.uri")
    width        = get_dict_attr(cover, "$.width")
    
    set_dict_attr(picture_table_tuple, "$.label",        label)
    set_dict_attr(picture_table_tuple, "$.avg_color",    avg_color)
    set_dict_attr(picture_table_tuple, "$.height",       height)
    set_dict_attr(picture_table_tuple, "$.image_type",   image_type)
    set_dict_attr(picture_table_tuple, "$.is_animated",  is_animated)
    set_dict_attr(picture_table_tuple, "$.open_web_url", open_web_url)
    set_dict_attr(picture_table_tuple, "$.uri",          uri)
    set_dict_attr(picture_table_tuple, "$.width",        width)
    
    if db.is_table_exist(picture_table.get_name()) is False:
      picture_table.create()
    
    if uri is not None:
      picture_table.insert_record(picture_table_tuple)

    ##
    ## <=========================== feed_room_label ==================================>
    ##
    feed_room_label = get_dict_attr(data, "$.data.room.feed_room_label")
    # picture_index auto increment
    label        = "feed_room_label"
    avg_color    = get_dict_attr(feed_room_label, "$.avg_color")
    height       = get_dict_attr(feed_room_label, "$.height")
    image_type   = get_dict_attr(feed_room_label, "$.image_type")
    is_animated  = get_dict_attr(feed_room_label, "$.is_animated")
    open_web_url = get_dict_attr(feed_room_label, "$.open_web_url")
    uri          = get_dict_attr(feed_room_label, "$.uri")
    width        = get_dict_attr(feed_room_label, "$.width")
    
    set_dict_attr(picture_table_tuple, "$.label",        label)
    set_dict_attr(picture_table_tuple, "$.avg_color",    avg_color)
    set_dict_attr(picture_table_tuple, "$.height",       height)
    set_dict_attr(picture_table_tuple, "$.image_type",   image_type)
    set_dict_attr(picture_table_tuple, "$.is_animated",  is_animated)
    set_dict_attr(picture_table_tuple, "$.open_web_url", open_web_url)
    set_dict_attr(picture_table_tuple, "$.uri",          uri)
    set_dict_attr(picture_table_tuple, "$.width",        width)
    
    if db.is_table_exist(picture_table.get_name()) is False:
      picture_table.create()
    
    if uri is not None:
      picture_table.insert_record(picture_table_tuple)
    
    ##
    ## <=========================== guide_button ==================================>
    ##
    guide_button = get_dict_attr(data, "$.data.room.guide_button")
    # picture_index auto increment
    label        = "guide_button"
    avg_color    = get_dict_attr(guide_button, "$.avg_color")
    height       = get_dict_attr(guide_button, "$.height")
    image_type   = get_dict_attr(guide_button, "$.image_type")
    is_animated  = get_dict_attr(guide_button, "$.is_animated")
    open_web_url = get_dict_attr(guide_button, "$.open_web_url")
    uri          = get_dict_attr(guide_button, "$.uri")
    width        = get_dict_attr(guide_button, "$.width")
    
    set_dict_attr(picture_table_tuple, "$.label",        label)
    set_dict_attr(picture_table_tuple, "$.avg_color",    avg_color)
    set_dict_attr(picture_table_tuple, "$.height",       height)
    set_dict_attr(picture_table_tuple, "$.image_type",   image_type)
    set_dict_attr(picture_table_tuple, "$.is_animated",  is_animated)
    set_dict_attr(picture_table_tuple, "$.open_web_url", open_web_url)
    set_dict_attr(picture_table_tuple, "$.uri",          uri)
    set_dict_attr(picture_table_tuple, "$.width",        width)
    
    if db.is_table_exist(picture_table.get_name()) is False:
      picture_table.create()
    
    if uri is not None:
      picture_table.insert_record(picture_table_tuple)
    
    ##
    ## <=========================== avatar_large ==================================>
    ##
    avatar_large = get_dict_attr(data, "$.data.room.owner.avatar_large")
    # picture_index auto increment
    label        = "avatar_large"
    avg_color    = get_dict_attr(avatar_large, "$.avg_color")
    height       = get_dict_attr(avatar_large, "$.height")
    image_type   = get_dict_attr(avatar_large, "$.image_type")
    is_animated  = get_dict_attr(avatar_large, "$.is_animated")
    open_web_url = get_dict_attr(avatar_large, "$.open_web_url")
    uri          = get_dict_attr(avatar_large, "$.uri")
    width        = get_dict_attr(avatar_large, "$.width")
    
    set_dict_attr(picture_table_tuple, "$.label",        label)
    set_dict_attr(picture_table_tuple, "$.avg_color",    avg_color)
    set_dict_attr(picture_table_tuple, "$.height",       height)
    set_dict_attr(picture_table_tuple, "$.image_type",   image_type)
    set_dict_attr(picture_table_tuple, "$.is_animated",  is_animated)
    set_dict_attr(picture_table_tuple, "$.open_web_url", open_web_url)
    set_dict_attr(picture_table_tuple, "$.uri",          uri)
    set_dict_attr(picture_table_tuple, "$.width",        width)
    
    if db.is_table_exist(picture_table.get_name()) is False:
      picture_table.create()
    
    if uri is not None:
      picture_table.insert_record(picture_table_tuple)

    ##
    ## <=========================== avatar_medium ==================================>
    ##
    avatar_medium = get_dict_attr(data, "$.data.room.owner.avatar_medium")
    # picture_index auto increment
    label        = "avatar_medium"
    avg_color    = get_dict_attr(avatar_medium, "$.avg_color")
    height       = get_dict_attr(avatar_medium, "$.height")
    image_type   = get_dict_attr(avatar_medium, "$.image_type")
    is_animated  = get_dict_attr(avatar_medium, "$.is_animated")
    open_web_url = get_dict_attr(avatar_medium, "$.open_web_url")
    uri          = get_dict_attr(avatar_medium, "$.uri")
    width        = get_dict_attr(avatar_medium, "$.width")
    
    set_dict_attr(picture_table_tuple, "$.label",        label)
    set_dict_attr(picture_table_tuple, "$.avg_color",    avg_color)
    set_dict_attr(picture_table_tuple, "$.height",       height)
    set_dict_attr(picture_table_tuple, "$.image_type",   image_type)
    set_dict_attr(picture_table_tuple, "$.is_animated",  is_animated)
    set_dict_attr(picture_table_tuple, "$.open_web_url", open_web_url)
    set_dict_attr(picture_table_tuple, "$.uri",          uri)
    set_dict_attr(picture_table_tuple, "$.width",        width)
    
    if db.is_table_exist(picture_table.get_name()) is False:
      picture_table.create()
    
    if uri is not None:
      picture_table.insert_record(picture_table_tuple)

    ##
    ## <=========================== avatar_thumb ==================================>
    ##
    avatar_thumb = get_dict_attr(data, "$.data.room.owner.avatar_thumb")
    # picture_index auto increment
    label        = "avatar_thumb"
    avg_color    = get_dict_attr(avatar_thumb, "$.avg_color")
    height       = get_dict_attr(avatar_thumb, "$.height")
    image_type   = get_dict_attr(avatar_thumb, "$.image_type")
    is_animated  = get_dict_attr(avatar_thumb, "$.is_animated")
    open_web_url = get_dict_attr(avatar_thumb, "$.open_web_url")
    uri          = get_dict_attr(avatar_thumb, "$.uri")
    width        = get_dict_attr(avatar_thumb, "$.width")
    
    set_dict_attr(picture_table_tuple, "$.label",        label)
    set_dict_attr(picture_table_tuple, "$.avg_color",    avg_color)
    set_dict_attr(picture_table_tuple, "$.height",       height)
    set_dict_attr(picture_table_tuple, "$.image_type",   image_type)
    set_dict_attr(picture_table_tuple, "$.is_animated",  is_animated)
    set_dict_attr(picture_table_tuple, "$.open_web_url", open_web_url)
    set_dict_attr(picture_table_tuple, "$.uri",          uri)
    set_dict_attr(picture_table_tuple, "$.width",        width)
    
    if db.is_table_exist(picture_table.get_name()) is False:
      picture_table.create()
    
    if uri is not None:
      picture_table.insert_record(picture_table_tuple)

    ##
    ## <=========================== badge_image_list ==================================>
    ##
    badge_image_list = get_dict_attr(data, "$.data.room.owner.badge_image_list")
    if len(badge_image_list) != 0:
      # picture_index auto increment
      label        = "badge_image_list"
      for badge_image in badge_image_list:
        avg_color    = get_dict_attr(badge_image, "$.avg_color")
        height       = get_dict_attr(badge_image, "$.height")
        image_type   = get_dict_attr(badge_image, "$.image_type")
        is_animated  = get_dict_attr(badge_image, "$.is_animated")
        open_web_url = get_dict_attr(badge_image, "$.open_web_url")
        uri          = get_dict_attr(badge_image, "$.uri")
        width        = get_dict_attr(badge_image, "$.width")
        
        set_dict_attr(picture_table_tuple, "$.label",        label)
        set_dict_attr(picture_table_tuple, "$.avg_color",    avg_color)
        set_dict_attr(picture_table_tuple, "$.height",       height)
        set_dict_attr(picture_table_tuple, "$.image_type",   image_type)
        set_dict_attr(picture_table_tuple, "$.is_animated",  is_animated)
        set_dict_attr(picture_table_tuple, "$.open_web_url", open_web_url)
        set_dict_attr(picture_table_tuple, "$.uri",          uri)
        set_dict_attr(picture_table_tuple, "$.width",        width)
        
        if db.is_table_exist(picture_table.get_name()) is False:
          picture_table.create()
        
        if uri is not None:
          picture_table.insert_record(picture_table_tuple)

    ##
    ## <=========================== badge_image_list_v2 ==================================>
    ##
    badge_image_list_v2 = get_dict_attr(data, "$.data.room.owner.badge_image_list_v2")
    if len(badge_image_list_v2) != 0:
      # picture_index auto increment
      label        = "badge_image_list"
      for badge_image in badge_image_list_v2:
        avg_color    = get_dict_attr(badge_image, "$.avg_color")
        height       = get_dict_attr(badge_image, "$.height")
        image_type   = get_dict_attr(badge_image, "$.image_type")
        is_animated  = get_dict_attr(badge_image, "$.is_animated")
        open_web_url = get_dict_attr(badge_image, "$.open_web_url")
        uri          = get_dict_attr(badge_image, "$.uri")
        width        = get_dict_attr(badge_image, "$.width")
        
        set_dict_attr(picture_table_tuple, "$.label",        label)
        set_dict_attr(picture_table_tuple, "$.avg_color",    avg_color)
        set_dict_attr(picture_table_tuple, "$.height",       height)
        set_dict_attr(picture_table_tuple, "$.image_type",   image_type)
        set_dict_attr(picture_table_tuple, "$.is_animated",  is_animated)
        set_dict_attr(picture_table_tuple, "$.open_web_url", open_web_url)
        set_dict_attr(picture_table_tuple, "$.uri",          uri)
        set_dict_attr(picture_table_tuple, "$.width",        width)
        
        if db.is_table_exist(picture_table.get_name()) is False:
          picture_table.create()
        
        if uri is not None:
          picture_table.insert_record(picture_table_tuple)

    ##
    ## <=========================== icons ==================================>
    ##
    icons = get_dict_attr(data, "$.data.room.owner.fans_club.data.badge.icons")
    if icons is not None:
      # picture_index auto increment
      for icon_key, icon_value in dict(icons).items():
        label        = "icons" + icon_key
        avg_color    = get_dict_attr(icon_value, "$.avg_color")
        height       = get_dict_attr(icon_value, "$.height")
        image_type   = get_dict_attr(icon_value, "$.image_type")
        is_animated  = get_dict_attr(icon_value, "$.is_animated")
        open_web_url = get_dict_attr(icon_value, "$.open_web_url")
        uri          = get_dict_attr(icon_value, "$.uri")
        width        = get_dict_attr(icon_value, "$.width")
        
        set_dict_attr(picture_table_tuple, "$.label",        label)
        set_dict_attr(picture_table_tuple, "$.avg_color",    avg_color)
        set_dict_attr(picture_table_tuple, "$.height",       height)
        set_dict_attr(picture_table_tuple, "$.image_type",   image_type)
        set_dict_attr(picture_table_tuple, "$.is_animated",  is_animated)
        set_dict_attr(picture_table_tuple, "$.open_web_url", open_web_url)
        set_dict_attr(picture_table_tuple, "$.uri",          uri)
        set_dict_attr(picture_table_tuple, "$.width",        width)
        
        if db.is_table_exist(picture_table.get_name()) is False:
          picture_table.create()
        
        if uri is not None:
          picture_table.insert_record(picture_table_tuple)

    ##
    ## <=========================== new_im_icon_with_level ==================================>
    ##
    new_im_icon_with_level = get_dict_attr(data, "$.data.room.owner.pay_grade.new_im_icon_with_level")
    if new_im_icon_with_level is not None:
      # picture_index auto increment
      label        = "new_im_icon_with_level"
      avg_color    = get_dict_attr(new_im_icon_with_level, "$.avg_color")
      height       = get_dict_attr(new_im_icon_with_level, "$.height")
      image_type   = get_dict_attr(new_im_icon_with_level, "$.image_type")
      is_animated  = get_dict_attr(new_im_icon_with_level, "$.is_animated")
      open_web_url = get_dict_attr(new_im_icon_with_level, "$.open_web_url")
      uri          = get_dict_attr(new_im_icon_with_level, "$.uri")
      width        = get_dict_attr(new_im_icon_with_level, "$.width")
      
      set_dict_attr(picture_table_tuple, "$.label",        label)
      set_dict_attr(picture_table_tuple, "$.avg_color",    avg_color)
      set_dict_attr(picture_table_tuple, "$.height",       height)
      set_dict_attr(picture_table_tuple, "$.image_type",   image_type)
      set_dict_attr(picture_table_tuple, "$.is_animated",  is_animated)
      set_dict_attr(picture_table_tuple, "$.open_web_url", open_web_url)
      set_dict_attr(picture_table_tuple, "$.uri",          uri)
      set_dict_attr(picture_table_tuple, "$.width",        width)
      
      if db.is_table_exist(picture_table.get_name()) is False:
        picture_table.create()
      
      if uri is not None:
        picture_table.insert_record(picture_table_tuple)
      
    ##
    ## <=========================== new_live_icon ==================================>
    ##
    new_live_icon = get_dict_attr(data, "$.data.room.owner.pay_grade.new_live_icon")
    if new_live_icon is not None:
      # picture_index auto increment
      label        = "new_live_icon"
      avg_color    = get_dict_attr(new_live_icon, "$.avg_color")
      height       = get_dict_attr(new_live_icon, "$.height")
      image_type   = get_dict_attr(new_live_icon, "$.image_type")
      is_animated  = get_dict_attr(new_live_icon, "$.is_animated")
      open_web_url = get_dict_attr(new_live_icon, "$.open_web_url")
      uri          = get_dict_attr(new_live_icon, "$.uri")
      width        = get_dict_attr(new_live_icon, "$.width")
      
      set_dict_attr(picture_table_tuple, "$.label",        label)
      set_dict_attr(picture_table_tuple, "$.avg_color",    avg_color)
      set_dict_attr(picture_table_tuple, "$.height",       height)
      set_dict_attr(picture_table_tuple, "$.image_type",   image_type)
      set_dict_attr(picture_table_tuple, "$.is_animated",  is_animated)
      set_dict_attr(picture_table_tuple, "$.open_web_url", open_web_url)
      set_dict_attr(picture_table_tuple, "$.uri",          uri)
      set_dict_attr(picture_table_tuple, "$.width",        width)
      
      if db.is_table_exist(picture_table.get_name()) is False:
        picture_table.create()
      
      if uri is not None:
        picture_table.insert_record(picture_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(picture_table.get_name(), e))
    raise e  

  ##
  ## PictureFlexSettingTable
  ##
  picture_flex_setting_table = PictureFlexSettingTable(db)
  try:
    ##
    ## +--------------------+
    ## | Field              |
    ## +--------------------+
    ## | uri                |
    ## | flex_setting_index |
    ## | flex_setting       |
    ## +--------------------+    
    ##
    picture_flex_setting_table_tuple = picture_flex_setting_table.get_tuple()
    
    ##
    ## <=========================== cover ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.cover.uri")
    # flex_setting_index auto increment
    flex_setting_list   = get_dict_attr(data, "$.data.room.cover.flex_setting_list")
    if len(flex_setting_list) != 0:
      set_dict_attr(picture_flex_setting_table_tuple, "$.uri",    uri)
      for flex_setting in flex_setting_list:
        set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting",      flex_setting)
      
        if db.is_table_exist(picture_flex_setting_table.get_name()) is False:
          picture_flex_setting_table.create()
        picture_flex_setting_table.insert_record(picture_flex_setting_table_tuple)
      
    ##
    ## <=========================== feed_room_label ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.feed_room_label.uri")
    # flex_setting_index auto increment
    flex_setting_list   = get_dict_attr(data, "$.data.room.feed_room_label.flex_setting_list")
    if len(flex_setting_list) != 0:
      set_dict_attr(picture_flex_setting_table_tuple, "$.uri",    uri)
      for flex_setting in flex_setting_list:
        set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting",      flex_setting)
      
        if db.is_table_exist(picture_flex_setting_table.get_name()) is False:
          picture_flex_setting_table.create()
        picture_flex_setting_table.insert_record(picture_flex_setting_table_tuple)

    ##
    ## <=========================== guide_button ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.guide_button.uri")
    # flex_setting_index auto increment
    flex_setting_list   = get_dict_attr(data, "$.data.room.guide_button.flex_setting_list")
    if len(flex_setting_list) != 0:
      set_dict_attr(picture_flex_setting_table_tuple, "$.uri",    uri)
      for flex_setting in flex_setting_list:
        set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting",      flex_setting)
      
        if db.is_table_exist(picture_flex_setting_table.get_name()) is False:
          picture_flex_setting_table.create()
        picture_flex_setting_table.insert_record(picture_flex_setting_table_tuple)

    ##
    ## <=========================== avatar_large ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.owner.avatar_large.uri")
    # flex_setting_index auto increment
    flex_setting_list   = get_dict_attr(data, "$.data.room.owner.avatar_large.flex_setting_list")
    if len(flex_setting_list) != 0:
      set_dict_attr(picture_flex_setting_table_tuple, "$.uri",    uri)
      for flex_setting in flex_setting_list:
        set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting",      flex_setting)
      
        if db.is_table_exist(picture_flex_setting_table.get_name()) is False:
          picture_flex_setting_table.create()
        picture_flex_setting_table.insert_record(picture_flex_setting_table_tuple)

    ##
    ## <=========================== avatar_medium ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.owner.avatar_medium.uri")
    # flex_setting_index auto increment
    flex_setting_list   = get_dict_attr(data, "$.data.room.owner.avatar_medium.flex_setting_list")
    if len(flex_setting_list) != 0:
      set_dict_attr(picture_flex_setting_table_tuple, "$.uri",    uri)
      for flex_setting in flex_setting_list:
        set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting",      flex_setting)
      
        if db.is_table_exist(picture_flex_setting_table.get_name()) is False:
          picture_flex_setting_table.create()
        picture_flex_setting_table.insert_record(picture_flex_setting_table_tuple)
        
    ##
    ## <=========================== avatar_thumb ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.owner.avatar_thumb.uri")
    # flex_setting_index auto increment
    flex_setting_list   = get_dict_attr(data, "$.data.room.owner.avatar_thumb.flex_setting_list")
    if len(flex_setting_list) != 0:
      set_dict_attr(picture_flex_setting_table_tuple, "$.uri",    uri)
      for flex_setting in flex_setting_list:
        set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting",      flex_setting)
      
        if db.is_table_exist(picture_flex_setting_table.get_name()) is False:
          picture_flex_setting_table.create()
        picture_flex_setting_table.insert_record(picture_flex_setting_table_tuple)

    ##
    ## <=========================== badge_image_list ==================================>
    ##
    badge_image_list    = get_dict_attr(data, "$.data.room.owner.badge_image_list")
    
    ##
    ## loop badge image list
    ##
    for badge_image in badge_image_list:
      
      ##
      ## loop flex setting list
      ##
      uri                 = get_dict_attr(badge_image, "$.uri")
      # flex_setting_index auto increment
      flex_setting_list   = get_dict_attr(badge_image, "$.flex_setting_list")
      if len(flex_setting_list) != 0:
        
        ##
        ## set for every record
        ##
        set_dict_attr(picture_flex_setting_table_tuple, "$.uri",    uri)
        for flex_setting in flex_setting_list:
          # flex_setting_index auto increment
          set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting",      flex_setting)
        
          if db.is_table_exist(picture_flex_setting_table.get_name()) is False:
            picture_flex_setting_table.create()
          
          if uri is not None:
            picture_flex_setting_table.insert_record(picture_flex_setting_table_tuple)

    ##
    ## <=========================== badge_image_list_v2 ==================================>
    ##
    badge_image_list_v2    = get_dict_attr(data, "$.data.room.owner.badge_image_list_v2")
    
    ##
    ## loop badge image list
    ##
    for badge_image in badge_image_list_v2:
      
      ##
      ## loop flex setting list
      ##
      uri                 = get_dict_attr(badge_image, "$.uri")
      # flex_setting_index auto increment
      flex_setting_list   = get_dict_attr(badge_image, "$.flex_setting_list")
      if len(flex_setting_list) != 0:
        
        ##
        ## set for every record
        ##
        set_dict_attr(picture_flex_setting_table_tuple, "$.uri",    uri)
        for flex_setting in flex_setting_list:
          # flex_setting_index auto increment
          set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting",      flex_setting)
        
          if db.is_table_exist(picture_flex_setting_table.get_name()) is False:
            picture_flex_setting_table.create()
          
          if uri is not None:
            picture_flex_setting_table.insert_record(picture_flex_setting_table_tuple)

    ##
    ## <=========================== icons ==================================>
    ##
    icons    = get_dict_attr(data, "$.data.room.owner.fans_club.data.badge.icons")
    
    ##
    ## loop icons
    ##
    for icon_key, icon_value in dict(icons).items():
      
      ##
      ## loop flex setting list
      ##
      uri                 = get_dict_attr(icon_value, "$.uri")
      # flex_setting_index auto increment
      flex_setting_list   = get_dict_attr(icon_value, "$.flex_setting_list")
      if len(flex_setting_list) != 0:
        
        ##
        ## set for every record
        ##
        set_dict_attr(picture_flex_setting_table_tuple, "$.uri",    uri)
        for flex_setting in flex_setting_list:
          # flex_setting_index auto increment
          set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting",      flex_setting)
        
          if db.is_table_exist(picture_flex_setting_table.get_name()) is False:
            picture_flex_setting_table.create()
          
          if uri is not None:
            picture_flex_setting_table.insert_record(picture_flex_setting_table_tuple)

    ##
    ## <=========================== new_im_icon_with_level ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.owner.pay_grade.new_im_icon_with_level.uri")
    # flex_setting_index auto increment
    flex_setting_list   = get_dict_attr(data, "$.data.room.owner.pay_grade.new_im_icon_with_level.flex_setting_list")
    if len(flex_setting_list) != 0:
      set_dict_attr(picture_flex_setting_table_tuple, "$.uri",    uri)
      for flex_setting in flex_setting_list:
        set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting",      flex_setting)
      
        if db.is_table_exist(picture_flex_setting_table.get_name()) is False:
          picture_flex_setting_table.create()
        
        if uri is not None:
          picture_flex_setting_table.insert_record(picture_flex_setting_table_tuple)

    ##
    ## <=========================== new_live_icon ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.owner.pay_grade.new_live_icon.uri")
    # flex_setting_index auto increment
    flex_setting_list   = get_dict_attr(data, "$.data.room.owner.pay_grade.new_live_icon.flex_setting_list")
    if len(flex_setting_list) != 0:
      set_dict_attr(picture_flex_setting_table_tuple, "$.uri",    uri)
      for flex_setting in flex_setting_list:
        set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting",      flex_setting)
      
        if db.is_table_exist(picture_flex_setting_table.get_name()) is False:
          picture_flex_setting_table.create()
        
        if uri is not None:
          picture_flex_setting_table.insert_record(picture_flex_setting_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(picture_flex_setting_table.get_name(), e))
    raise e  

  ## 
  ## PictureTextSettingTable
  ##
  picture_text_setting_table = PictureTextSettingTable(db)
  try:
    ##
    ## +--------------------+
    ## | Field              |
    ## +--------------------+
    ## | uri                |
    ## | text_setting_index |
    ## | text_setting       |
    ## +--------------------+
    ##
    picture_text_setting_table_tuple = picture_text_setting_table.get_tuple()

    ##
    ## <=========================== cover ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.cover.uri")
    # text_setting_index auto increment
    text_setting_list   = get_dict_attr(data, "$.data.room.cover.text_setting_list")
    if len(text_setting_list) != 0:
      set_dict_attr(picture_text_setting_table_tuple, "$.uri",    uri)
      for text_setting in text_setting_list:
        set_dict_attr(picture_text_setting_table_tuple, "$.text_setting",      text_setting)

        if db.is_table_exist(picture_text_setting_table.get_name()) is False:
          picture_text_setting_table.create()
        
        if uri is not None:
          picture_text_setting_table.insert_record(picture_text_setting_table_tuple)

    ##
    ## <=========================== feed_room_label ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.feed_room_label.uri")
    # text_setting_index auto increment
    text_setting_list   = get_dict_attr(data, "$.data.room.feed_room_label.text_setting_list")
    if len(text_setting_list) != 0:
      set_dict_attr(picture_text_setting_table_tuple, "$.uri",    uri)
      for text_setting in text_setting_list:
        set_dict_attr(picture_text_setting_table_tuple, "$.text_setting",      text_setting)

        if db.is_table_exist(picture_text_setting_table.get_name()) is False:
          picture_text_setting_table.create()
        
        if uri is not None:
          picture_text_setting_table.insert_record(picture_text_setting_table_tuple)

    ##
    ## <=========================== guide_button ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.guide_button.uri")
    # text_setting_index auto increment
    text_setting_list   = get_dict_attr(data, "$.data.room.guide_button.text_setting_list")
    if len(text_setting_list) != 0:
      set_dict_attr(picture_text_setting_table_tuple, "$.uri",    uri)
      for text_setting in text_setting_list:
        set_dict_attr(picture_text_setting_table_tuple, "$.text_setting",      text_setting)

        if db.is_table_exist(picture_text_setting_table.get_name()) is False:
          picture_text_setting_table.create()
        
        if uri is not None:
          picture_text_setting_table.insert_record(picture_text_setting_table_tuple)

    ##
    ## <=========================== avatar_large ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.owner.avatar_large.uri")
    # text_setting_index auto increment
    text_setting_list   = get_dict_attr(data, "$.data.room.owner.avatar_large.text_setting_list")
    if len(text_setting_list) != 0:
      set_dict_attr(picture_text_setting_table_tuple, "$.uri",    uri)
      for text_setting in text_setting_list:
        set_dict_attr(picture_text_setting_table_tuple, "$.text_setting",      text_setting)

        if db.is_table_exist(picture_text_setting_table.get_name()) is False:
          picture_text_setting_table.create()
        
        if uri is not None:
          picture_text_setting_table.insert_record(picture_text_setting_table_tuple)

    ##
    ## <=========================== avatar_medium ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.owner.avatar_medium.uri")
    # text_setting_index auto increment
    text_setting_list   = get_dict_attr(data, "$.data.room.owner.avatar_medium.text_setting_list")
    if len(text_setting_list) != 0:
      set_dict_attr(picture_text_setting_table_tuple, "$.uri",    uri)
      for text_setting in text_setting_list:
        set_dict_attr(picture_text_setting_table_tuple, "$.text_setting",      text_setting)

        if db.is_table_exist(picture_text_setting_table.get_name()) is False:
          picture_text_setting_table.create()
        
        if uri is not None:
          picture_text_setting_table.insert_record(picture_text_setting_table_tuple)

    ##
    ## <=========================== avatar_thumb ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.owner.avatar_thumb.uri")
    # text_setting_index auto increment
    text_setting_list   = get_dict_attr(data, "$.data.room.owner.avatar_thumb.text_setting_list")
    if len(text_setting_list) != 0:
      set_dict_attr(picture_text_setting_table_tuple, "$.uri",    uri)
      for text_setting in text_setting_list:
        set_dict_attr(picture_text_setting_table_tuple, "$.text_setting",      text_setting)

        if db.is_table_exist(picture_text_setting_table.get_name()) is False:
          picture_text_setting_table.create()
        
        if uri is not None:
          picture_text_setting_table.insert_record(picture_text_setting_table_tuple)

    ##
    ## <=========================== badge_image_list ==================================>
    ##
    badge_image_list    = get_dict_attr(data, "$.data.room.owner.badge_image_list")
    
    ##
    ## loop badge image list
    ##
    for badge_image in badge_image_list:
      
      ##
      ## loop text setting list
      ##
      uri                 = get_dict_attr(badge_image, "$.uri")
      # text_setting_index auto increment
      text_setting_list   = get_dict_attr(badge_image, "$.text_setting_list")
      if len(text_setting_list) != 0:
        
        ##
        ## set for every record
        ##
        set_dict_attr(picture_text_setting_table_tuple, "$.uri",    uri)
        for text_setting in text_setting_list:
          # text_setting_index auto increment
          set_dict_attr(picture_text_setting_table_tuple, "$.text_setting",      text_setting)
        
          if db.is_table_exist(picture_text_setting_table.get_name()) is False:
            picture_text_setting_table.create()
          
          if uri is not None:
            picture_text_setting_table.insert_record(picture_text_setting_table_tuple)

    ##
    ## <=========================== badge_image_list_v2 ==================================>
    ##
    badge_image_list_v2    = get_dict_attr(data, "$.data.room.owner.badge_image_list_v2")
    
    ##
    ## loop badge image list
    ##
    for badge_image in badge_image_list_v2:
      
      ##
      ## loop text setting list
      ##
      uri                 = get_dict_attr(badge_image, "$.uri")
      # text_setting_index auto increment
      text_setting_list   = get_dict_attr(badge_image, "$.text_setting_list")
      if len(text_setting_list) != 0:
        
        ##
        ## set for every record
        ##
        set_dict_attr(picture_text_setting_table_tuple, "$.uri",    uri)
        for text_setting in text_setting_list:
          # text_setting_index auto increment
          set_dict_attr(picture_text_setting_table_tuple, "$.text_setting",      text_setting)
        
          if db.is_table_exist(picture_text_setting_table.get_name()) is False:
            picture_text_setting_table.create()
          
          if uri is not None:
            picture_text_setting_table.insert_record(picture_text_setting_table_tuple)

    ##
    ## <=========================== icons ==================================>
    ##
    icons    = get_dict_attr(data, "$.data.room.owner.fans_club.data.badge.icons")
    
    ##
    ## loop icons
    ##
    for icon_key, icon_value in dict(icons).items():
      
      ##
      ## loop text setting list
      ##
      uri                 = get_dict_attr(icon_value, "$.uri")
      # text_setting_index auto increment
      text_setting_list   = get_dict_attr(icon_value, "$.text_setting_list")
      if len(text_setting_list) != 0:
        
        ##
        ## set for every record
        ##
        set_dict_attr(picture_text_setting_table_tuple, "$.uri",    uri)
        for text_setting in text_setting_list:
          # text_setting_index auto increment
          set_dict_attr(picture_text_setting_table_tuple, "$.text_setting",      text_setting)
        
          if db.is_table_exist(picture_text_setting_table.get_name()) is False:
            picture_text_setting_table.create()
          
          if uri is not None:
            picture_text_setting_table.insert_record(picture_text_setting_table_tuple)

    ##
    ## <=========================== new_im_icon_with_level ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.owner.pay_grade.new_im_icon_with_level.uri")
    # text_setting_index auto increment
    text_setting_list   = get_dict_attr(data, "$.data.room.owner.pay_grade.new_im_icon_with_level.text_setting_list")
    if len(text_setting_list) != 0:
      set_dict_attr(picture_text_setting_table_tuple, "$.uri",    uri)
      for text_setting in text_setting_list:
        set_dict_attr(picture_text_setting_table_tuple, "$.text_setting",      text_setting)
      
        if db.is_table_exist(picture_text_setting_table.get_name()) is False:
          picture_text_setting_table.create()
        
        if uri is not None:
          picture_text_setting_table.insert_record(picture_text_setting_table_tuple)

    ##
    ## <=========================== new_live_icon ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.owner.pay_grade.new_live_icon.uri")
    # text_setting_index auto increment
    text_setting_list   = get_dict_attr(data, "$.data.room.owner.pay_grade.new_live_icon.text_setting_list")
    if len(text_setting_list) != 0:
      set_dict_attr(picture_text_setting_table_tuple, "$.uri",    uri)
      for text_setting in text_setting_list:
        set_dict_attr(picture_text_setting_table_tuple, "$.text_setting",      text_setting)
      
        if db.is_table_exist(picture_text_setting_table.get_name()) is False:
          picture_text_setting_table.create()
        
        if uri is not None:
          picture_text_setting_table.insert_record(picture_text_setting_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(picture_text_setting_table.get_name(), e))
    raise e

  ##
  ## PictureUrlTable
  ##
  picture_url_table = PictureUrlTable(db)
  try:
    ##
    ## +-----------+
    ## | Field     |
    ## +-----------+
    ## | uri       |
    ## | url_index |
    ## | url       |
    ## +-----------+
    ##
    picture_url_table_tuple = picture_url_table.get_tuple()

    ##
    ## <=========================== cover ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.cover.uri")
    # url_index auto increment
    url_list            = get_dict_attr(data, "$.data.room.cover.url_list")
    if len(url_list) != 0:
      set_dict_attr(picture_url_table_tuple, "$.uri",    uri)
      for url in url_list:
        set_dict_attr(picture_url_table_tuple, "$.url",      url)

        if db.is_table_exist(picture_url_table.get_name()) is False:
          picture_url_table.create()
        
        if uri is not None:
          picture_url_table.insert_record(picture_url_table_tuple)

    ##
    ## <=========================== feed_room_label ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.feed_room_label.uri")
    # url_index auto increment
    url_list            = get_dict_attr(data, "$.data.room.feed_room_label.url_list")
    if len(url_list) != 0:
      set_dict_attr(picture_url_table_tuple, "$.uri",    uri)
      for url in url_list:
        set_dict_attr(picture_url_table_tuple, "$.url",      url)

        if db.is_table_exist(picture_url_table.get_name()) is False:
          picture_url_table.create()
        
        if uri is not None:
          picture_url_table.insert_record(picture_url_table_tuple)

    ##
    ## <=========================== guide_button ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.guide_button.uri")
    # url_index auto increment
    url_list   = get_dict_attr(data, "$.data.room.guide_button.url_list")
    if len(url_list) != 0:
      set_dict_attr(picture_url_table_tuple, "$.uri",    uri)
      for url in url_list:
        set_dict_attr(picture_url_table_tuple, "$.url",      url)

        if db.is_table_exist(picture_url_table.get_name()) is False:
          picture_url_table.create()
        
        if uri is not None:
          picture_url_table.insert_record(picture_url_table_tuple)

    ##
    ## <=========================== avatar_large ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.owner.avatar_large.uri")
    # url_index auto increment
    url_list   = get_dict_attr(data, "$.data.room.owner.avatar_large.url_list")
    if len(url_list) != 0:
      set_dict_attr(picture_url_table_tuple, "$.uri",    uri)
      for url in url_list:
        set_dict_attr(picture_url_table_tuple, "$.url",      url)

        if db.is_table_exist(picture_url_table.get_name()) is False:
          picture_url_table.create()
        
        if uri is not None:
          picture_url_table.insert_record(picture_url_table_tuple)

    ##
    ## <=========================== avatar_medium ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.owner.avatar_medium.uri")
    # url_index auto increment
    url_list   = get_dict_attr(data, "$.data.room.owner.avatar_medium.url_list")
    if len(url_list) != 0:
      set_dict_attr(picture_url_table_tuple, "$.uri",    uri)
      for url in url_list:
        set_dict_attr(picture_url_table_tuple, "$.url",      url)

        if db.is_table_exist(picture_url_table.get_name()) is False:
          picture_url_table.create()
        
        if uri is not None:
          picture_url_table.insert_record(picture_url_table_tuple)

    ##
    ## <=========================== avatar_thumb ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.owner.avatar_thumb.uri")
    # url_index auto increment
    url_list   = get_dict_attr(data, "$.data.room.owner.avatar_thumb.url_list")
    if len(url_list) != 0:
      set_dict_attr(picture_url_table_tuple, "$.uri",    uri)
      for url in url_list:
        set_dict_attr(picture_url_table_tuple, "$.url",      url)

        if db.is_table_exist(picture_url_table.get_name()) is False:
          picture_url_table.create()
        
        if uri is not None:
          picture_url_table.insert_record(picture_url_table_tuple)

    ##
    ## <=========================== badge_image_list ==================================>
    ##
    badge_image_list    = get_dict_attr(data, "$.data.room.owner.badge_image_list")
    
    ##
    ## loop badge image list
    ##
    for badge_image in badge_image_list:
      
      ##
      ## loop text setting list
      ##
      uri                 = get_dict_attr(badge_image, "$.uri")
      # url_index auto increment
      url_list   = get_dict_attr(badge_image, "$.url_list")
      if len(url_list) != 0:
        
        ##
        ## set for every record
        ##
        set_dict_attr(picture_url_table_tuple, "$.uri",    uri)
        for url in url_list:
          # url_index auto increment
          set_dict_attr(picture_url_table_tuple, "$.url",      url)
        
          if db.is_table_exist(picture_url_table.get_name()) is False:
            picture_url_table.create()
          
          if uri is not None:
            picture_url_table.insert_record(picture_url_table_tuple)

    ##
    ## <=========================== badge_image_list_v2 ==================================>
    ##
    badge_image_list_v2    = get_dict_attr(data, "$.data.room.owner.badge_image_list_v2")
    
    ##
    ## loop badge image list
    ##
    for badge_image in badge_image_list_v2:
      
      ##
      ## loop text setting list
      ##
      uri                 = get_dict_attr(badge_image, "$.uri")
      # url_index auto increment
      url_list   = get_dict_attr(badge_image, "$.url_list")
      if len(url_list) != 0:
        
        ##
        ## set for every record
        ##
        set_dict_attr(picture_url_table_tuple, "$.uri",    uri)
        for url in url_list:
          # url_index auto increment
          set_dict_attr(picture_url_table_tuple, "$.url",      url)
        
          if db.is_table_exist(picture_url_table.get_name()) is False:
            picture_url_table.create()
          
          if uri is not None:
            picture_url_table.insert_record(picture_url_table_tuple)

    ##
    ## <=========================== icons ==================================>
    ##
    icons    = get_dict_attr(data, "$.data.room.owner.fans_club.data.badge.icons")
    
    ##
    ## loop icons
    ##
    for icon_key, icon_value in dict(icons).items():
      
      ##
      ## loop text setting list
      ##
      uri                 = get_dict_attr(icon_value, "$.uri")
      # url_index auto increment
      url_list   = get_dict_attr(icon_value, "$.url_list")
      if len(url_list) != 0:
        
        ##
        ## set for every record
        ##
        set_dict_attr(picture_url_table_tuple, "$.uri",    uri)
        for url in url_list:
          # url_index auto increment
          set_dict_attr(picture_url_table_tuple, "$.url",      url)
        
          if db.is_table_exist(picture_url_table.get_name()) is False:
            picture_url_table.create()
          
          if uri is not None:
            picture_url_table.insert_record(picture_url_table_tuple)

    ##
    ## <=========================== new_im_icon_with_level ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.owner.pay_grade.new_im_icon_with_level.uri")
    # url_index auto increment
    url_list   = get_dict_attr(data, "$.data.room.owner.pay_grade.new_im_icon_with_level.url_list")
    if len(url_list) != 0:
      set_dict_attr(picture_url_table_tuple, "$.uri",    uri)
      for url in url_list:
        set_dict_attr(picture_url_table_tuple, "$.url",      url)
      
        if db.is_table_exist(picture_url_table.get_name()) is False:
          picture_url_table.create()
        
        if uri is not None:
          picture_url_table.insert_record(picture_url_table_tuple)

    ##
    ## <=========================== new_live_icon ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.owner.pay_grade.new_live_icon.uri")
    # url_index auto increment
    url_list   = get_dict_attr(data, "$.data.room.owner.pay_grade.new_live_icon.url_list")
    if len(url_list) != 0:
      set_dict_attr(picture_url_table_tuple, "$.uri",    uri)
      for url in url_list:
        set_dict_attr(picture_url_table_tuple, "$.url",      url)
      
        if db.is_table_exist(picture_url_table.get_name()) is False:
          picture_url_table.create()
        
        if uri is not None:
          picture_url_table.insert_record(picture_url_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(picture_url_table.get_name(), e))
    raise e

  ##
  ## PictureContentTable
  ##
  picture_content_table = PictureContentTable(db)
  try:
    ##
    ## +------------------+
    ## | Field            |
    ## +------------------+
    ## | uri_index        |
    ## | uri              |
    ## | alternative_text |
    ## | font_color       |
    ## | level            |
    ## | name             |
    ## +------------------+
    ##
    picture_content_table_tuple = picture_content_table.get_tuple()

    ##
    ## <=========================== feed_room_label ==================================>
    ##
    # uri_index auto increment
    uri                 = get_dict_attr(data, "$.data.room.feed_room_label.uri")
    alternative_text    = get_dict_attr(data, "$.data.room.feed_room_label.content.alternative_text")
    font_color          = get_dict_attr(data, "$.data.room.feed_room_label.content.font_color")
    level               = get_dict_attr(data, "$.data.room.feed_room_label.content.level")
    name                = get_dict_attr(data, "$.data.room.feed_room_label.content.name")

    # uri_index auto increment
    set_dict_attr(picture_content_table_tuple, "$.uri",                 uri)
    set_dict_attr(picture_content_table_tuple, "$.alternative_text",    alternative_text)
    set_dict_attr(picture_content_table_tuple, "$.font_color",          font_color)
    set_dict_attr(picture_content_table_tuple, "$.level",               level)
    set_dict_attr(picture_content_table_tuple, "$.name",                name)

    if db.is_table_exist(picture_content_table.get_name()) is False:
      picture_content_table.create()
    
    if uri is not None:
      picture_content_table.insert_record(picture_content_table_tuple)

    ##
    ## <=========================== badge_image_list ==================================>
    ##
    badge_image_list    = get_dict_attr(data, "$.data.room.owner.badge_image_list")
    
    ##
    ## loop badge image list
    ##
    for badge_image in badge_image_list:
      
      ##
      ## loop text setting list
      ##
      ## url_index auto increment
      uri              = get_dict_attr(badge_image, "$.uri")
      alternative_text = get_dict_attr(badge_image, "$.content.alternative_text")
      font_color       = get_dict_attr(badge_image, "$.content.font_color")
      level            = get_dict_attr(badge_image, "$.content.level")
      name             = get_dict_attr(badge_image, "$.content.name")
        
      ##
      ## url_index auto increment
      ##
      set_dict_attr(picture_content_table_tuple, "$.uri",              uri)
      set_dict_attr(picture_content_table_tuple, "$.alternative_text", alternative_text)
      set_dict_attr(picture_content_table_tuple, "$.font_color",       font_color)
      set_dict_attr(picture_content_table_tuple, "$.level",            level)
      set_dict_attr(picture_content_table_tuple, "$.name",             name)

      if db.is_table_exist(picture_url_table.get_name()) is False:
        picture_url_table.create()
      
      if uri is not None:
        picture_url_table.insert_record(picture_url_table_tuple)

    ##
    ## <=========================== badge_image_list_v2 ==================================>
    ##
    badge_image_list_v2    = get_dict_attr(data, "$.data.room.owner.badge_image_list_v2")
    
    ##
    ## loop badge image list
    ##
    for badge_image in badge_image_list_v2:
      
      ##
      ## loop text setting list
      ##
      ## url_index auto increment
      uri              = get_dict_attr(badge_image, "$.uri")
      alternative_text = get_dict_attr(badge_image, "$.content.alternative_text")
      font_color       = get_dict_attr(badge_image, "$.content.font_color")
      level            = get_dict_attr(badge_image, "$.content.level")
      name             = get_dict_attr(badge_image, "$.content.name")
        
      ##
      ## url_index auto increment
      ##
      set_dict_attr(picture_content_table_tuple, "$.uri",              uri)
      set_dict_attr(picture_content_table_tuple, "$.alternative_text", alternative_text)
      set_dict_attr(picture_content_table_tuple, "$.font_color",       font_color)
      set_dict_attr(picture_content_table_tuple, "$.level",            level)
      set_dict_attr(picture_content_table_tuple, "$.name",             name)

      if db.is_table_exist(picture_url_table.get_name()) is False:
        picture_url_table.create()
      
      if uri is not None:
        picture_url_table.insert_record(picture_url_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(picture_content_table.get_name(), e))
    raise e
  
  ##
  ## UserTable
  ##
  user_table = UserTable(db)
  try:
    ##
    ## +------------------------------------------+
    ## | Field                                    |
    ## +------------------------------------------+
    ## | id                                       |
    ## | gender                                   |
    ## | allow_be_located                         |
    ## | age_range                                |
    ## | adversary_authorization_info             |
    ## | adversary_user_status                    |
    ## | allow_find_by_contacts                   |
    ## | allow_others_download_video              |
    ## | allow_others_download_when_sharing_video |
    ## | allow_share_show_profile                 |
    ## | allow_show_in_gossip                     |
    ## | allow_show_my_action                     |
    ## | allow_strange_comment                    |
    ## | allow_unfollower_comment                 |
    ## | allow_use_linkmic                        |
    ## | authorization_info                       |
    ## | bg_img_url                               |
    ## | birthday                                 |
    ## | birthday_description                     |
    ## | birthday_valid                           |
    ## | block_status                             |
    ## | city                                     |
    ## | comment_restrict                         |
    ## | constellation                            |
    ## | consume_diamond_level                    |
    ## | create_time                              |
    ## | desensitized_nickname                    |
    ## | disable_ichat                            |
    ## | display_id                               |
    ## | enable_ichat_img                         |
    ## | fold_stranger_chat                       |
    ## | nickname                                 |
    ## | pay_score                                |
    ## | pay_scores                               |
    ## | need_profile_guide                       |
    ## | hotsoon_verified                         |
    ## | hotsoon_verified_reason                  |
    ## | ichat_restrict_type                      |
    ## | income_share_percent                     |
    ## | push_comment_status                      |
    ## | push_digg                                |
    ## | push_follow                              |
    ## | push_friend_action                       |
    ## | push_ichat                               |
    ## | push_status                              |
    ## | push_video_post                          |
    ## | push_video_recommend                     |
    ## | remark_name                              |
    ## | sec_uid                                  |
    ## | secret                                   |
    ## | share_qrcode_uri                         |
    ## | short_id                                 |
    ## | signature                                |
    ## | special_id                               |
    ## | status                                   |
    ## | telephone                                |
    ## | total_recharge_diamond_count             |
    ## | user_canceled                            |
    ## | user_open_id                             |
    ## | user_role                                |
    ## | verified                                 |
    ## | verified_content                         |
    ## | verified_mobile                          |
    ## | verified_reason                          |
    ## | watch_duration_month                     |
    ## | web_rid                                  |
    ## | webcast_uid                              |
    ## | with_car_management_permission           |
    ## | with_commerce_permission                 |
    ## | with_fusion_shop_entry                   |
    ## +------------------------------------------+
    ##
    user_table_tuple                          = user_table.get_tuple()
    id                                        = get_dict_attr(data, "$.data.user.id")
    gender                                    = get_dict_attr(data, "$.data.user.gender")
    allow_be_located                          = get_dict_attr(data, "$.data.user.allow_be_located")
    age_range                                 = get_dict_attr(data, "$.data.user.age_range")
    adversary_authorization_info              = get_dict_attr(data, "$.data.user.adversary_authorization_info")
    adversary_user_status                     = get_dict_attr(data, "$.data.user.adversary_user_status")
    allow_find_by_contacts                    = get_dict_attr(data, "$.data.user.allow_find_by_contacts")
    allow_others_download_video               = get_dict_attr(data, "$.data.user.allow_others_download_video")
    allow_others_download_when_sharing_video  = get_dict_attr(data, "$.data.user.allow_others_download_when_sharing_video")
    allow_share_show_profile                  = get_dict_attr(data, "$.data.user.allow_share_show_profile")
    allow_show_in_gossip                      = get_dict_attr(data, "$.data.user.allow_show_in_gossip")
    allow_show_my_action                      = get_dict_attr(data, "$.data.user.allow_show_my_action")
    allow_strange_comment                     = get_dict_attr(data, "$.data.user.allow_strange_comment")
    allow_unfollower_comment                  = get_dict_attr(data, "$.data.user.allow_unfollower_comment")
    allow_use_linkmic                         = get_dict_attr(data, "$.data.user.allow_use_linkmic")
    authorization_info                        = get_dict_attr(data, "$.data.user.authorization_info")
    bg_img_url                                = get_dict_attr(data, "$.data.user.bg_img_url")
    if birthday != 0:
      birthday                                  = get_dict_attr(data, "$.data.user.birthday")
    birthday_description                      = get_dict_attr(data, "$.data.user.birthday_description")
    birthday_valid                            = get_dict_attr(data, "$.data.user.birthday_valid")
    block_status                              = get_dict_attr(data, "$.data.user.block_status")
    city                                      = get_dict_attr(data, "$.data.user.city")
    comment_restrict                          = get_dict_attr(data, "$.data.user.comment_restrict")
    constellation                             = get_dict_attr(data, "$.data.user.constellation")
    consume_diamond_level                     = get_dict_attr(data, "$.data.user.consume_diamond_level")
    create_time                               = get_dict_attr(data, "$.data.user.create_time")
    desensitized_nickname                     = get_dict_attr(data, "$.data.user.desensitized_nickname")
    disable_ichat                             = get_dict_attr(data, "$.data.user.disable_ichat")
    display_id                                = get_dict_attr(data, "$.data.user.display_id")
    enable_ichat_img                          = get_dict_attr(data, "$.data.user.enable_ichat_img")
    fold_stranger_chat                        = get_dict_attr(data, "$.data.user.fold_stranger_chat")
    nickname                                  = get_dict_attr(data, "$.data.user.nickname")
    pay_score                                 = get_dict_attr(data, "$.data.user.pay_score")
    pay_scores                                = get_dict_attr(data, "$.data.user.pay_scores")
    need_profile_guide                        = get_dict_attr(data, "$.data.user.need_profile_guide")
    hotsoon_verified                          = get_dict_attr(data, "$.data.user.hotsoon_verified")
    hotsoon_verified_reason                   = get_dict_attr(data, "$.data.user.hotsoon_verified_reason")
    ichat_restrict_type                       = get_dict_attr(data, "$.data.user.ichat_restrict_type")
    income_share_percent                      = get_dict_attr(data, "$.data.user.income_share_percent")
    push_comment_status                       = get_dict_attr(data, "$.data.user.push_comment_status")
    push_digg                                 = get_dict_attr(data, "$.data.user.push_digg")
    push_follow                               = get_dict_attr(data, "$.data.user.push_follow")
    push_friend_action                        = get_dict_attr(data, "$.data.user.push_friend_action")
    push_ichat                                = get_dict_attr(data, "$.data.user.push_ichat")
    push_status                               = get_dict_attr(data, "$.data.user.push_status")
    push_video_post                           = get_dict_attr(data, "$.data.user.push_video_post")
    push_video_recommend                      = get_dict_attr(data, "$.data.user.push_video_recommend")
    remark_name                               = get_dict_attr(data, "$.data.user.remark_name")
    sec_uid                                   = get_dict_attr(data, "$.data.user.sec_uid")
    secret                                    = get_dict_attr(data, "$.data.user.secret")
    share_qrcode_uri                          = get_dict_attr(data, "$.data.user.share_qrcode_uri")
    short_id                                  = get_dict_attr(data, "$.data.user.short_id")
    signature                                 = get_dict_attr(data, "$.data.user.signature")
    special_id                                = get_dict_attr(data, "$.data.user.special_id")
    status                                    = get_dict_attr(data, "$.data.user.status")
    telephone                                 = get_dict_attr(data, "$.data.user.telephone")
    total_recharge_diamond_count              = get_dict_attr(data, "$.data.user.total_recharge_diamond_count")
    user_canceled                             = get_dict_attr(data, "$.data.user.user_canceled")
    user_open_id                              = get_dict_attr(data, "$.data.user.user_open_id")
    user_role                                 = get_dict_attr(data, "$.data.user.user_role")
    verified                                  = get_dict_attr(data, "$.data.user.verified")
    verified_content                          = get_dict_attr(data, "$.data.user.verified_content")
    verified_mobile                           = get_dict_attr(data, "$.data.user.verified_mobile")
    verified_reason                           = get_dict_attr(data, "$.data.user.verified_reason")
    watch_duration_month                      = get_dict_attr(data, "$.data.user.watch_duration_month")
    web_rid                                   = get_dict_attr(data, "$.data.user.web_rid")
    webcast_uid                               = get_dict_attr(data, "$.data.user.webcast_uid")
    with_car_management_permission            = get_dict_attr(data, "$.data.user.with_car_management_permission")
    with_commerce_permission                  = get_dict_attr(data, "$.data.user.with_commerce_permission")
    with_fusion_shop_entry                    = get_dict_attr(data, "$.data.user.with_fusion_shop_entry")
    
    set_dict_attr(user_table_tuple, "$.id",                                          str(id))
    set_dict_attr(user_table_tuple, "$.gender",                                      gender)
    set_dict_attr(user_table_tuple, "$.allow_be_located",                            allow_be_located)
    set_dict_attr(user_table_tuple, "$.age_range",                                   age_range)
    set_dict_attr(user_table_tuple, "$.adversary_authorization_info",                adversary_authorization_info)
    set_dict_attr(user_table_tuple, "$.adversary_user_status",                       adversary_user_status)
    set_dict_attr(user_table_tuple, "$.allow_find_by_contacts",                      allow_find_by_contacts)
    set_dict_attr(user_table_tuple, "$.allow_others_download_video",                 allow_others_download_video)
    set_dict_attr(user_table_tuple, "$.allow_others_download_when_sharing_video",    allow_others_download_when_sharing_video)
    set_dict_attr(user_table_tuple, "$.allow_share_show_profile",                    allow_share_show_profile)
    set_dict_attr(user_table_tuple, "$.allow_show_in_gossip",                        allow_show_in_gossip)
    set_dict_attr(user_table_tuple, "$.allow_show_my_action",                        allow_show_my_action)
    set_dict_attr(user_table_tuple, "$.allow_strange_comment",                       allow_strange_comment)
    set_dict_attr(user_table_tuple, "$.allow_unfollower_comment",                    allow_unfollower_comment)
    set_dict_attr(user_table_tuple, "$.allow_use_linkmic",                           allow_use_linkmic)
    set_dict_attr(user_table_tuple, "$.authorization_info",                          authorization_info)
    set_dict_attr(user_table_tuple, "$.bg_img_url",                                  bg_img_url)
    if birthday != 0:
      set_dict_attr(user_table_tuple, "$.birthday",                                    birthday)
    set_dict_attr(user_table_tuple, "$.birthday_description",                        birthday_description)
    set_dict_attr(user_table_tuple, "$.birthday_valid",                              birthday_valid)
    set_dict_attr(user_table_tuple, "$.block_status",                                block_status)
    set_dict_attr(user_table_tuple, "$.city",                                        city)
    set_dict_attr(user_table_tuple, "$.comment_restrict",                            comment_restrict)
    set_dict_attr(user_table_tuple, "$.constellation",                               constellation)
    set_dict_attr(user_table_tuple, "$.consume_diamond_level",                       consume_diamond_level)
    if create_time != 0:
      set_dict_attr(user_table_tuple, "$.create_time",                                 dat.fromtimestamp(create_time))
    set_dict_attr(user_table_tuple, "$.desensitized_nickname",                       desensitized_nickname)
    set_dict_attr(user_table_tuple, "$.disable_ichat",                               disable_ichat)
    set_dict_attr(user_table_tuple, "$.display_id",                                  display_id)
    set_dict_attr(user_table_tuple, "$.enable_ichat_img",                            enable_ichat_img)
    set_dict_attr(user_table_tuple, "$.fold_stranger_chat",                          fold_stranger_chat)
    set_dict_attr(user_table_tuple, "$.nickname",                                    nickname)
    set_dict_attr(user_table_tuple, "$.pay_score",                                   pay_score)
    set_dict_attr(user_table_tuple, "$.pay_scores",                                  pay_scores)
    set_dict_attr(user_table_tuple, "$.need_profile_guide",                          need_profile_guide)
    set_dict_attr(user_table_tuple, "$.hotsoon_verified",                            hotsoon_verified)
    set_dict_attr(user_table_tuple, "$.hotsoon_verified_reason",                     hotsoon_verified_reason)
    set_dict_attr(user_table_tuple, "$.ichat_restrict_type",                         ichat_restrict_type)
    set_dict_attr(user_table_tuple, "$.income_share_percent",                        income_share_percent)
    set_dict_attr(user_table_tuple, "$.push_comment_status",                         push_comment_status)
    set_dict_attr(user_table_tuple, "$.push_digg",                                   push_digg)
    set_dict_attr(user_table_tuple, "$.push_follow",                                 push_follow)
    set_dict_attr(user_table_tuple, "$.push_friend_action",                          push_friend_action)
    set_dict_attr(user_table_tuple, "$.push_ichat",                                  push_ichat)
    set_dict_attr(user_table_tuple, "$.push_status",                                 push_status)
    set_dict_attr(user_table_tuple, "$.push_video_post",                             push_video_post)
    set_dict_attr(user_table_tuple, "$.push_video_recommend",                        push_video_recommend)
    set_dict_attr(user_table_tuple, "$.remark_name",                                 remark_name)
    set_dict_attr(user_table_tuple, "$.sec_uid",                                     sec_uid)
    set_dict_attr(user_table_tuple, "$.secret",                                      secret)
    set_dict_attr(user_table_tuple, "$.share_qrcode_uri",                            share_qrcode_uri)
    set_dict_attr(user_table_tuple, "$.short_id",                                    str(short_id))
    set_dict_attr(user_table_tuple, "$.signature",                                   signature)
    set_dict_attr(user_table_tuple, "$.special_id",                                  special_id)
    set_dict_attr(user_table_tuple, "$.status",                                      status)
    set_dict_attr(user_table_tuple, "$.telephone",                                   telephone)
    set_dict_attr(user_table_tuple, "$.total_recharge_diamond_count",                total_recharge_diamond_count)
    set_dict_attr(user_table_tuple, "$.user_canceled",                               user_canceled)
    set_dict_attr(user_table_tuple, "$.user_open_id",                                user_open_id)
    set_dict_attr(user_table_tuple, "$.user_role",                                   user_role)
    set_dict_attr(user_table_tuple, "$.verified",                                    verified)
    set_dict_attr(user_table_tuple, "$.verified_content",                            verified_content)
    set_dict_attr(user_table_tuple, "$.verified_mobile",                             verified_mobile)
    set_dict_attr(user_table_tuple, "$.verified_reason",                             verified_reason)
    set_dict_attr(user_table_tuple, "$.watch_duration_month",                        watch_duration_month)
    set_dict_attr(user_table_tuple, "$.web_rid",                                     web_rid)
    set_dict_attr(user_table_tuple, "$.webcast_uid",                                 webcast_uid)
    set_dict_attr(user_table_tuple, "$.with_car_management_permission",              with_car_management_permission)
    set_dict_attr(user_table_tuple, "$.with_commerce_permission",                    with_commerce_permission)
    set_dict_attr(user_table_tuple, "$.with_fusion_shop_entry",                      with_fusion_shop_entry)
    
    if db.is_table_exist(user_table.get_name()) is False:
      user_table.create()
    
    if id != 0:
      user_table.insert_record(user_table_tuple)
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(user_table.get_name(), e))
    raise e

##
## export a living data from social media stream downloader databse to yml file.
##
def export_live_info_to_yml(db:SocialMediaStreamDataBase, data:dict, output_path:str) -> None:
  pass

##
## >>================================ table agent test method ===============================>>
##
def test_import_live_info_to_database() -> None:
  ##
  ## load yml file
  ##
  data = load_yml(Path('./docs/design/Lvuuu.yml'))
  
  ##
  ## parse living data
  ##
  living_data = get_dict_attr(data, "$.external_info")
  
  ##
  ## import living data to database
  ##
  db = SocialMediaStreamDataBase(host='192.168.1.12', user='wangyan', passwd='wuyu1998', database='social_media_stream_downloader')
  import_douyin_live_info_to_database(living_data, db)
  

if __name__ == "__main__":
  test_import_live_info_to_database()