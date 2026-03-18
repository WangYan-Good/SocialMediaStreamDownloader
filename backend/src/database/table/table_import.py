##
## import.py
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
                                                                               RoomDecoInputRectTable,                              \
                                                                               RoomDecoReservationTable,                            \
                                                                               RoomDecoReservationBtnRectTable,                     \
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
                                                                               RoomTempStateStrategyTable,                          \
                                                                               RoomTempStateStrategyMapTable,                       \
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
                                                                               RoomDecoTextFootConfigTable,                         \
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
                                                                               StreamPushUrlTable,                                  \
                                                                               RoomLinkMicTable,                                    \
                                                                               RoomLinkMicBattleScoreTable,                         \
                                                                               RoomLinkMicBattleSettingTable,                       \
                                                                               RoomLinkMicChannelInfoTable
from backend.src.database.table.user                                  import   RoomOwnerTable,                                      \
                                                                               OwnRoomFlagTable,                                    \
                                                                               OwnRoomIdTable,                                      \
                                                                               OwnRoomIdDisplayTable,                               \
                                                                               FansClubTable,                                       \
                                                                               FansClubAvailableGiftIdTable,                        \
                                                                               FansClubBadgeIconTable,                              \
                                                                               RoomOwnerUserAttrTable,                              \
                                                                               RoomAdminPrivilegeTable,                             \
                                                                               RoomOwnerAuthInfoTable,                              \
                                                                               RoomOwnerAuthLevelTable,                             \
                                                                               UserTable,                                           \
                                                                               RoomOwnerAuthorStatsTable
from backend.src.database.table.room_base                             import   RoomBaseTable
from backend.src.database.table.room_owner                            import   RoomOwnerV2Table

##
## import a living data to relative tables of social media stream downloader.
##
def import_douyin_live_info_to_database(db:SocialMediaStreamDataBase, data:dict) -> None:
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
    ## create the table if not exist
    ##
    if db.is_table_exist(live_record_table.get_name()) is False:
      live_record_table.create()
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
    live_record_table_tuple = {key:None for key in live_record_table.get_tuple()}

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
    live_record_table.insert_record(live_record_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert LiveRecordTable failed: {}".format(e))
    raise e

  ##
  ## RoomAttributeTable
  ##
  room_attribute_table = RoomAttributeTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(room_attribute_table.get_name()) is False:
      room_attribute_table.create()
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
    room_attribute_table_tuple = {key:None for key in room_attribute_table.get_tuple()}

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

    room_attribute_table.insert_record(room_attribute_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_attribute_table.get_name(), e))
    raise e

  ##
  ## RoomAdminUserIdTable
  ##
  room_admin_user_id_table = RoomAdminUserIdTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(room_admin_user_id_table.get_name()) is False:
      room_admin_user_id_table.create()
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
    room_admin_user_id_table_tuple = {key:None for key in room_admin_user_id_table.get_tuple()}
    admin_user_ids = get_dict_attr(data, "$.data.room.admin_user_ids")
    if len(admin_user_ids) != 0:
      set_dict_attr(room_admin_user_id_table_tuple, "$.start_time",      dat.fromtimestamp(start_time))
      set_dict_attr(room_admin_user_id_table_tuple, "$.platform",        DOUYIN_PLATFORM)
      set_dict_attr(room_admin_user_id_table_tuple, "$.room_id",         str(room_id))
  
      for admin_user_id_index in range(0, len(admin_user_ids)):
        set_dict_attr(room_admin_user_id_table_tuple, "$.admin_user_id_index", admin_user_id_index)
        set_dict_attr(room_admin_user_id_table_tuple, "$.admin_user_id",       str(admin_user_ids[admin_user_id_index]))

        room_admin_user_id_table.insert_record(room_admin_user_id_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_admin_user_id_table.get_name(), e))
    raise e

  ##
  ## RoomAdminUserOpenIdTable
  ##
  room_admin_user_open_id_table = RoomAdminUserOpenIdTable(db)
  try:
    ##
    ## create table if not exist
    ##
    if db.is_table_exist(room_admin_user_open_id_table.get_name()) is False:
      room_admin_user_open_id_table.create()
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
    room_admin_user_open_id_table_tuple = {key:None for key in room_admin_user_open_id_table.get_tuple()}
    admin_user_open_ids = get_dict_attr(data, "$.data.room.admin_user_open_ids")
    if len(admin_user_open_ids) != 0:
      set_dict_attr(room_admin_user_open_id_table_tuple, "$.now",      now)
      set_dict_attr(room_admin_user_open_id_table_tuple, "$.platform", DOUYIN_PLATFORM)
      set_dict_attr(room_admin_user_open_id_table_tuple, "$.room_id",  str(room_id))
      for admin_user_open_id in admin_user_open_ids:
        # admin_user_open_index auto increment
        set_dict_attr(room_admin_user_open_id_table_tuple, "$.admin_user_open_id", str(admin_user_open_id))
        room_admin_user_open_id_table.insert_record(room_admin_user_open_id_table_tuple, on_duplicate='ignore')
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
    room_assist_label_table_tuple = {key:None for key in room_assist_label_table.get_tuple()}
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
      room_assist_label_table.insert_record(room_assist_label_table_tuple, on_duplicate='ignore')
    '''
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_assist_label_table.get_name(), e))
    raise e

  """
  ##
  ## RoomDecoTable
  ##
  room_deco_table = RoomDecoTable(db)

  ##
  ## RoomDecoInputRectTable
  ##
  room_deco_input_rect_table = RoomDecoInputRectTable(db)

  ##
  ## RoomDecoReservationTable
  ##
  room_deco_reservation_table = RoomDecoReservationTable(db)
  
  ##
  ## TODO
  ## RoomDecoReservationBtnRectTable
  ##
  """
  room_deco_reservation_btn_rect_table = RoomDecoReservationBtnRectTable(db)
  """  

  ##
  ## RoomDecoTextFootConfigTable
  ##
  room_deco_text_foot_config_table = RoomDecoTextFootConfigTable(db)
  
  ##
  ## TODO
  ## RoomDecoTextSpecialEffectsTable
  ##
  """
  room_deco_text_special_effect_table = RoomDecoTextSpecialEffectsTable(db)
  """
  
  deco_list = get_dict_attr(data, "$.data.room.deco_list")
  if deco_list is not None:
      for deco_index in range(0, len(deco_list)):
        try:
          ##
          ## create the table if not exist
          ##
          if db.is_table_exist(room_deco_table.get_name()) is False:
            room_deco_table.create()
          ##
          ## +--------------------------------------+
          ## | Field                                |
          ## +--------------------------------------+
          ## | start_time                           |
          ## | platform                             |
          ## | room_id                              |
          ## | deco_index                           |
          ## | audit_text_color                     |
          ## | content                              |
          ## | h                                    |
          ## | id                                   |
          ## | kind                                 |
          ## | max_length                           |
          ## | status                               |
          ## | sub_type                             |
          ## | text_color                           |
          ## | text_image_adjustable_end_position   |
          ## | text_image_adjustable_start_position |
          ## | text_size                            |
          ## | type                                 |
          ## | w                                    |
          ## | x                                    |
          ## | y                                    |
          ## +--------------------------------------+
          ##
          room_deco_table_tuple = {key:None for key in room_deco_table.get_tuple()}
          set_dict_attr(room_deco_table_tuple, "$.start_time",                           dat.fromtimestamp(start_time))
          set_dict_attr(room_deco_table_tuple, "$.platform",                             DOUYIN_PLATFORM)
          set_dict_attr(room_deco_table_tuple, "$.room_id",                              str(room_id))
          set_dict_attr(room_deco_table_tuple, "$.deco_index",                           deco_index)
          set_dict_attr(room_deco_table_tuple, "$.audit_text_color",                     get_dict_attr(deco_list[deco_index], "$.audit_text_color"))
          set_dict_attr(room_deco_table_tuple, "$.content",                              get_dict_attr(deco_list[deco_index], "$.content"))
          set_dict_attr(room_deco_table_tuple, "$.h",                                    get_dict_attr(deco_list[deco_index], "$.h"))
          set_dict_attr(room_deco_table_tuple, "$.id",                                   get_dict_attr(deco_list[deco_index], "$.id"))
          set_dict_attr(room_deco_table_tuple, "$.kind",                                 get_dict_attr(deco_list[deco_index], "$.kind"))
          set_dict_attr(room_deco_table_tuple, "$.max_length",                           get_dict_attr(deco_list[deco_index], "$.max_length"))
          set_dict_attr(room_deco_table_tuple, "$.status",                               get_dict_attr(deco_list[deco_index], "$.status"))
          set_dict_attr(room_deco_table_tuple, "$.sub_type",                             get_dict_attr(deco_list[deco_index], "$.sub_type"))
          set_dict_attr(room_deco_table_tuple, "$.text_color",                           get_dict_attr(deco_list[deco_index], "$.text_color"))
          set_dict_attr(room_deco_table_tuple, "$.text_image_adjustable_end_position",   get_dict_attr(deco_list[deco_index], "$.text_image_adjustable_end_position"))
          set_dict_attr(room_deco_table_tuple, "$.text_image_adjustable_start_position", get_dict_attr(deco_list[deco_index], "$.text_image_adjustable_start_position"))
          set_dict_attr(room_deco_table_tuple, "$.text_size",                            get_dict_attr(deco_list[deco_index], "$.text_size"))
          set_dict_attr(room_deco_table_tuple, "$.type",                                 get_dict_attr(deco_list[deco_index], "$.type"))
          set_dict_attr(room_deco_table_tuple, "$.w",                                    get_dict_attr(deco_list[deco_index], "$.w"))
          set_dict_attr(room_deco_table_tuple, "$.x",                                    get_dict_attr(deco_list[deco_index], "$.x"))
          set_dict_attr(room_deco_table_tuple, "$.y",                                    get_dict_attr(deco_list[deco_index], "$.y"))
  
          room_deco_table.insert_record(room_deco_table_tuple, on_duplicate='ignore')
        except Exception as e:
          get_logger().error("insert {} failed: {}".format(room_deco_table.get_name(), e))
          raise e

        try:
          input_rect_list = get_dict_attr(deco_list[deco_index], "$.input_rect")
          ##
          ## create the table if not exist
          ##
          if db.is_table_exist(room_deco_input_rect_table.get_name()) is False:
            room_deco_input_rect_table.create()
          ##
          ## +------------------+
          ## | Field            |
          ## +------------------+
          ## | start_time       |
          ## | platform         |
          ## | room_id          |
          ## | deco_index       |
          ## | input_rect_index |
          ## | input_rect       |
          ## +------------------+
          ##
          room_deco_input_rect_tuple = {key:None for key in room_deco_input_rect_table.get_tuple()}
          set_dict_attr(room_deco_input_rect_tuple, "$.start_time",                           dat.fromtimestamp(start_time))
          set_dict_attr(room_deco_input_rect_tuple, "$.platform",                             DOUYIN_PLATFORM)
          set_dict_attr(room_deco_input_rect_tuple, "$.room_id",                              str(room_id))
          set_dict_attr(room_deco_input_rect_tuple, "$.deco_index",                           deco_index)
          for input_rect_index in range(0, len(input_rect_list)):
            set_dict_attr(room_deco_input_rect_tuple, "$.input_rect_index",                   input_rect_index)
            set_dict_attr(room_deco_input_rect_tuple, "$.input_rect",                         input_rect_list[input_rect_index])
            room_deco_input_rect_table.insert_record(room_deco_input_rect_tuple, on_duplicate='ignore')          
        except Exception as e:
          get_logger().error("insert {} failed: {}".format(room_deco_input_rect_table.get_name(), e))
          raise e
        
        try:
          reservation = get_dict_attr(deco_list[deco_index], "$.reservation")
          ##
          ## create the table if not exist
          ##
          if db.is_table_exist(room_deco_reservation_table.get_name()) is False:
            room_deco_reservation_table.create()
          ##
          ## +------------------------+
          ## | Field                  |
          ## +------------------------+
          ## | start_time             |
          ## | platform               |
          ## | room_id                |
          ## | deco_index             |
          ## | anchor_id              |
          ## | anchor_open_id         |
          ## | appointment_id         |
          ## | btn_color              |
          ## | reservation_end_time   |
          ## | is_reserved            |
          ## | reservation_room_id    |
          ## | reservation_start_time |
          ## +------------------------+
          ##
          room_deco_reservation_tuple = {key:None for key in room_deco_reservation_table.get_tuple()}
          set_dict_attr(room_deco_reservation_tuple, "$.start_time",             dat.fromtimestamp(start_time))
          set_dict_attr(room_deco_reservation_tuple, "$.platform",               DOUYIN_PLATFORM)
          set_dict_attr(room_deco_reservation_tuple, "$.room_id",                str(room_id))
          set_dict_attr(room_deco_reservation_tuple, "$.deco_index",             deco_index)
          set_dict_attr(room_deco_reservation_tuple, "$.anchor_id",              get_dict_attr(reservation, "$.anchor_id"))
          set_dict_attr(room_deco_reservation_tuple, "$.anchor_open_id",         get_dict_attr(reservation, "$.anchor_open_id"))
          set_dict_attr(room_deco_reservation_tuple, "$.appointment_id",         get_dict_attr(reservation, "$.appointment_id"))
          set_dict_attr(room_deco_reservation_tuple, "$.btn_color",              get_dict_attr(reservation, "$.btn_color"))
          if get_dict_attr(reservation, "$.end_time") != 0:
            set_dict_attr(room_deco_reservation_tuple, "$.reservation_end_time",   get_dict_attr(reservation, "$.end_time"))
          set_dict_attr(room_deco_reservation_tuple, "$.is_reserved",            get_dict_attr(reservation, "$.is_reserved"))
          set_dict_attr(room_deco_reservation_tuple, "$.reservation_room_id",    get_dict_attr(reservation, "$.room_id"))
          if get_dict_attr(reservation, "$.start_time") != 0:
            set_dict_attr(room_deco_reservation_tuple, "$.reservation_start_time", get_dict_attr(reservation, "$.start_time"))
          room_deco_reservation_table.insert_record(room_deco_reservation_tuple, on_duplicate='ignore')
        except Exception as e:
          get_logger().error("insert {} failed: {}".format(room_deco_reservation_table.get_name(), e))
          raise e
        
        ##
        ## TODO
        ## RoomDecoReservationBtnRectTable
        ##
        try:
          """
          btn_rect = get_dict_attr(reservation, "$.btn_rect")
          """
          pass
        except Exception as e:
          # get_logger().error("insert {} failed: {}".format(room_deco_reservation_table.get_name(), e))
          raise e

        ##
        ##
        ##
        try:
          ##
          ## create the table if not exist
          ##
          if db.is_table_exist(room_deco_text_foot_config_table.get_name()) is False:
            room_deco_text_foot_config_table.create()
          ##
          ## +------------------+
          ## | Field            |
          ## +------------------+
          ## | start_time       |
          ## | platform         |
          ## | room_id          |
          ## | deco_index       |
          ## | FontID           |
          ## | font_name        |
          ## | Status           |
          ## | DownloadUrl      |
          ## +------------------+
          ##
          text_font_config = get_dict_attr(deco_list[deco_index], "$.text_font_config")
          if text_font_config is not None:
            room_deco_text_foot_config_tuple = {key:None for key in room_deco_text_foot_config_table.get_tuple()}
            set_dict_attr(room_deco_text_foot_config_tuple, "$.start_time",             dat.fromtimestamp(start_time))
            set_dict_attr(room_deco_text_foot_config_tuple, "$.platform",               DOUYIN_PLATFORM)
            set_dict_attr(room_deco_text_foot_config_tuple, "$.room_id",                str(room_id))
            set_dict_attr(room_deco_text_foot_config_tuple, "$.deco_index",             deco_index)
            
            FontID      = get_dict_attr(text_font_config, "$.FontID")
            font_name   = get_dict_attr(text_font_config, "$.font_name")
            Status      = get_dict_attr(text_font_config, "$.Status")
            DownloadUrl = get_dict_attr(text_font_config, "$.DownloadUrl")
            
            set_dict_attr(room_deco_text_foot_config_tuple, "$.FontID",                 FontID)
            set_dict_attr(room_deco_text_foot_config_tuple, "$.font_name",              font_name)
            set_dict_attr(room_deco_text_foot_config_tuple, "$.Status",                 Status)
            set_dict_attr(room_deco_text_foot_config_tuple, "$.DownloadUrl",            DownloadUrl)
            
            room_deco_text_foot_config_table.insert_record(room_deco_text_foot_config_tuple, on_duplicate='ignore')
        except Exception as e:
          get_logger().error("insert {} failed: {}".format(room_deco_reservation_table.get_name(), e))
          raise e

        ##
        ## TODO
        ## RoomDecoTextSpecialEffectsTable
        ##
        try:
          """
          text_special_effects = get_dict_attr(deco_list[deco_index], "$.text_special_effects")
          """
          pass
        except Exception as e:
          # get_logger().error("insert {} failed: {}".format(room_deco_reservation_table.get_name(), e))
          raise e
  """
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
    ## create the table if not exist
    ##
    if db.is_table_exist(fans_group_admin_user_id_table.get_name()) is False:
      fans_group_admin_user_id_table.create()
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
    fans_group_admin_user_id_table_tuple = {key:None for key in fans_group_admin_user_id_table.get_tuple()}

    fans_group_admin_user_ids = get_dict_attr(data, "$.data.room.fans_group_admin_user_ids")
    if len(fans_group_admin_user_ids) != 0:
      set_dict_attr(fans_group_admin_user_id_table_tuple, "$.now",      now)
      set_dict_attr(fans_group_admin_user_id_table_tuple, "$.platform", DOUYIN_PLATFORM)
      set_dict_attr(fans_group_admin_user_id_table_tuple, "$.room_id",  str(room_id))
      for fans_group_admin_user_id in fans_group_admin_user_ids:
        set_dict_attr(fans_group_admin_user_id_table_tuple, "$.fans_group_admin_user_id", str(fans_group_admin_user_id))

        fans_group_admin_user_id_table.insert_record(fans_group_admin_user_id_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(fans_group_admin_user_id_table.get_name(), e))
    raise e

  ##
  ## FansGroupAdminUserOpenIdTable
  ##
  fans_group_admin_user_open_id_table = FansGroupAdminUserOpenIdTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(fans_group_admin_user_open_id_table.get_name()) is False:
      fans_group_admin_user_open_id_table.create()

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
    fans_group_admin_user_open_id_table_tuple = {key:None for key in fans_group_admin_user_open_id_table.get_tuple()}
    fans_group_admin_user_open_id_list = get_dict_attr(data, "$.data.room.fans_group_admin_user_open_ids")
    if len(fans_group_admin_user_open_id_list) != 0:
      set_dict_attr(fans_group_admin_user_open_id_table_tuple, "$.now",      now)
      set_dict_attr(fans_group_admin_user_open_id_table_tuple, "$.platform", DOUYIN_PLATFORM)
      set_dict_attr(fans_group_admin_user_open_id_table_tuple, "$.room_id",  str(room_id))
      for fans_group_admin_user_open_id in fans_group_admin_user_open_id_list:
        # fans_group_admin_user_open_id_index auto increment
        set_dict_attr(fans_group_admin_user_open_id_table_tuple, "$.fans_group_admin_user_open_id", str(fans_group_admin_user_open_id))

        fans_group_admin_user_open_id_table.insert_record(fans_group_admin_user_open_id_table_tuple, on_duplicate='ignore')
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
    ## create the table if not exist
    ##
    if db.is_table_exist(room_owner_table.get_name()) is False:
      room_owner_table.create()

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
    ## | follow_info_follow_status                |
    ## | follower_count                           |
    ## | follower_count_str                       |
    ## | following_count                          |
    ## | following_count_str                      |
    ## | invalid_follow_status                    |
    ## | follow_info_push_status                  |
    ## | follow_info_remark_name                  |
    ## | follow_status                            |
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
    room_owner_table_tuple = {key:None for key in room_owner_table.get_tuple()}
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
    ##
    ## 针对已经注销的账号
    ## TODO：判断账号状态
    ##
    try:
      list_fans_group_url                      = get_dict_attr(data, "$.data.room.owner.fans_group_info.list_fans_group_url")
    except AttributeError as e:
      list_fans_group_url = ''
      get_logger().error(f"{e}")
    fold_stranger_chat                       = get_dict_attr(data, "$.data.room.owner.fold_stranger_chat")
    follow_info_follow_status                = get_dict_attr(data, "$.data.room.owner.follow_info.follow_status")
    follower_count                           = get_dict_attr(data, "$.data.room.owner.follow_info.follower_count")
    follower_count_str                       = get_dict_attr(data, "$.data.room.owner.follow_info.follower_count_str")
    following_count                          = get_dict_attr(data, "$.data.room.owner.follow_info.following_count")
    following_count_str                      = get_dict_attr(data, "$.data.room.owner.follow_info.following_count_str")
    invalid_follow_status                    = get_dict_attr(data, "$.data.room.owner.follow_info.invalid_follow_status")
    follow_info_push_status                  = get_dict_attr(data, "$.data.room.owner.follow_info.push_status")
    follow_info_remark_name                  = get_dict_attr(data, "$.data.room.owner.follow_info.remark_name")
    follow_status                            = get_dict_attr(data, "$.data.room.owner.follow_status")
    gender                                   = get_dict_attr(data, "$.data.room.owner.gender")
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
    set_dict_attr(room_owner_table_tuple, "$.follow_info_follow_status",                follow_info_follow_status)
    set_dict_attr(room_owner_table_tuple, "$.follower_count",                           follower_count)
    set_dict_attr(room_owner_table_tuple, "$.follower_count_str",                       follower_count_str)
    set_dict_attr(room_owner_table_tuple, "$.following_count",                          following_count)
    set_dict_attr(room_owner_table_tuple, "$.following_count_str",                      following_count_str)
    set_dict_attr(room_owner_table_tuple, "$.invalid_follow_status",                    invalid_follow_status)
    set_dict_attr(room_owner_table_tuple, "$.follow_info_push_status",                  follow_info_push_status)
    set_dict_attr(room_owner_table_tuple, "$.follow_info_remark_name",                  follow_info_remark_name)
    set_dict_attr(room_owner_table_tuple, "$.follow_status",                            follow_status)
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

    room_owner_table.insert_record(room_owner_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_owner_table.get_name(), e))
    raise e

  ##
  ## data.room.owner.author_stats
  ## RoomOwnerAuthorStatsTable
  ##
  room_owner_author_stats_table = RoomOwnerAuthorStatsTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(room_owner_author_stats_table.get_name()) is False:
      room_owner_author_stats_table.create()
    ##
    ## +----------------------------+
    ## | Field                      |
    ## +----------------------------+
    ## | start_time                 |
    ## | platform                   |
    ## | room_id                    |
    ## | owner_user_id              |
    ## | variety_show_play_count    |
    ## | video_total_count          |
    ## | video_total_favorite_count |
    ## | video_total_play_count     |
    ## | video_total_series_count   |
    ## | video_total_share_count    |
    ## +----------------------------+
    ##
    author_stats = get_dict_attr(data, "$.data.room.owner.author_stats")
    if author_stats:
      room_owner_author_stats_tuple = {key:None for key in room_owner_author_stats_table.get_tuple()}
      set_dict_attr(room_owner_author_stats_tuple, "$.start_time",                  dat.fromtimestamp(start_time))
      set_dict_attr(room_owner_author_stats_tuple, "$.platform",                    DOUYIN_PLATFORM)
      set_dict_attr(room_owner_author_stats_tuple, "$.room_id",                     str(room_id))
      set_dict_attr(room_owner_author_stats_tuple, "$.owner_user_id",               str(owner_user_id))
      set_dict_attr(room_owner_author_stats_tuple, "$.variety_show_play_count",     get_dict_attr(author_stats, "$.variety_show_play_count"))
      set_dict_attr(room_owner_author_stats_tuple, "$.video_total_count",           get_dict_attr(author_stats, "$.video_total_count"))
      set_dict_attr(room_owner_author_stats_tuple, "$.video_total_favorite_count",  get_dict_attr(author_stats, "$.video_total_favorite_count"))
      set_dict_attr(room_owner_author_stats_tuple, "$.video_total_play_count",      get_dict_attr(author_stats, "$.video_total_play_count"))
      set_dict_attr(room_owner_author_stats_tuple, "$.video_total_series_count",    get_dict_attr(author_stats, "$.video_total_series_count"))
      set_dict_attr(room_owner_author_stats_tuple, "$.video_total_share_count",     get_dict_attr(author_stats, "$.video_total_share_count"))
      room_owner_author_stats_table.insert_record(room_owner_author_stats_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_owner_author_stats_table.get_name(), e))
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
    badge_image_table_tuple = {key:None for key in badge_image_table.get_tuple()}
    # badge_image_index auto increment
    # TODO: label
    uri     = get_dict_attr(data, "$.data.room.badge_image.uri")
    
    # badge_image_index auto increment
    set_dict_attr(badge_image_table_tuple, "$.version",           version)
    set_dict_attr(badge_image_table_tuple, "$.uri",               uri)
    
    if db.is_table_exist(badge_image_table.get_name()) is False:
      badge_image_table.create()
    badge_image_table.insert_record(badge_image_table_tuple, on_duplicate='ignore')
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
  ## OwnRoomFlagTable
  ##
  own_room_flag_table = OwnRoomFlagTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(own_room_flag_table.get_name()) is False:
      own_room_flag_table.create()
    ##
    ## +-----------------------+
    ## | Field                 |
    ## +-----------------------+
    ## | start_time            |
    ## | platform              |
    ## | owner_user_id         |
    ## | exist_flag_index      |
    ## | exist_flag            |
    ## +-----------------------+
    ##
    own_room_flag_tuple = {key:None for key in own_room_flag_table.get_tuple()}

    try:
      own_room_dict = get_dict_attr(data, "$.data.room.owner.own_room")
      if own_room_dict is not None:
        exist_flag = True
      else:
        exist_flag = False
    except AttributeError as e:
      get_logger().error(f"{e}: {own_room_flag_table.get_name()} get exist_flag fail, set FALSE as default!")
      exist_flag = False
    
    set_dict_attr(own_room_flag_tuple, "$.start_time",     dat.fromtimestamp(start_time))
    set_dict_attr(own_room_flag_tuple, "$.platform",       DOUYIN_PLATFORM)
    set_dict_attr(own_room_flag_tuple, "$.owner_user_id",  str(owner_user_id))
    set_dict_attr(own_room_flag_tuple, "$.exist_flag",     exist_flag)

    own_room_flag_table.insert_record(own_room_flag_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(own_room_flag_table.get_name(), e))
    raise e

  if exist_flag is True:
    ##
    ## OwnRoomIdTable
    ##
    own_room_id_table = OwnRoomIdTable(db)
    try:
      ##
      ## create the table if not exist
      ##
      if db.is_table_exist(own_room_id_table.get_name()) is False:
        own_room_id_table.create()
      ##
      ## +-----------------------+
      ## | Field                 |
      ## +-----------------------+
      ## | start_time            |
      ## | platform              |
      ## | owner_user_id         |
      ## | room_id_index         |
      ## | room_id               |
      ## +-----------------------+
      ##
      own_room_id_tuple = {key:None for key in own_room_id_table.get_tuple()}
  
      own_room_id_list = get_dict_attr(data, "$.data.room.owner.own_room.room_ids")
      if len(own_room_id_list) != 0:
        set_dict_attr(own_room_id_tuple, "$.start_time",     dat.fromtimestamp(start_time))
        set_dict_attr(own_room_id_tuple, "$.platform",       DOUYIN_PLATFORM)
        set_dict_attr(own_room_id_tuple, "$.owner_user_id",  str(owner_user_id))
        for room_id_index in range(0, len(own_room_id_list)):
          # room_id_index auto increment
          set_dict_attr(own_room_id_tuple, "$.room_id_index",room_id_index)
          set_dict_attr(own_room_id_tuple, "$.room_id",      str(own_room_id_list[room_id_index]))
          own_room_id_table.insert_record(own_room_id_tuple, on_duplicate='ignore')
    except Exception as e:
      get_logger().error("insert {} failed: {}".format(own_room_id_table.get_name(), e))
      raise e
  
    ##
    ## TODO
    ## OwnRoomIdDisplayTable
    ##
    """
    own_room_id_display_table = OwnRoomIdDisplayTable(db)
    try:
      ##
      ## create the table if not exist
      ##
      if db.is_table_exist(own_room_id_display_table.get_name()) is False:
        own_room_id_display_table.create()
      ##
      ## +-----------------------+
      ## | Field                 |
      ## +-----------------------+
      ## | now                   |
      ## | platform              |
      ## | owner_user_id         |
      ## | room_id_index         |
      ## | room_id               |
      ## +-----------------------+
      ##
      own_room_id_tuple = {key:None for key in own_room_id_display_table.get_tuple()}
      
      own_room_id_list = get_dict_attr(data, "$.data.room.owner.own_room.room_ids")
      if len(own_room_id_list) != 0:
        set_dict_attr(own_room_id_tuple, "$.now",            now)
        set_dict_attr(own_room_id_tuple, "$.platform",       DOUYIN_PLATFORM)
        set_dict_attr(own_room_id_tuple, "$.owner_user_id",  str(owner_user_id))
        for room_id in own_room_id_list:
          # room_id_index auto increment
          set_dict_attr(own_room_id_tuple, "$.room_id",      str(room_id))
          own_room_id_display_table.insert_record(own_room_id_tuple, on_duplicate='ignore')    
    except Exception as e:
      get_logger().error("insert {} failed: {}".format(own_room_id_display_table.get_name(), e))
      raise e
    """

  ##
  ## FansClubTable
  ##
  fans_club_table = FansClubTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(fans_club_table.get_name()) is False:
      fans_club_table.create()

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
    fans_club_table_tuple = {key:None for key in fans_club_table.get_tuple()}
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
    if guard_expired_time != None and guard_expired_time != 0:
      set_dict_attr(fans_club_table_tuple, "$.guard_expired_time",                       dat.fromtimestamp(guard_expired_time))
    set_dict_attr(fans_club_table_tuple, "$.level",                                    level)
    set_dict_attr(fans_club_table_tuple, "$.user_fans_club_status",                    user_fans_club_status)
    set_dict_attr(fans_club_table_tuple, "$.user_guard_status",                        user_guard_status)
    set_dict_attr(fans_club_table_tuple, "$.prefer_data",                              json.dumps(prefer_data))

    fans_club_table.insert_record(fans_club_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(fans_club_table.get_name(), e))
    raise e

  ##
  ## FansClubAvailableGiftIdTable
  ##
  fans_club_available_gift_id_table = FansClubAvailableGiftIdTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(fans_club_available_gift_id_table.get_name()) is False:
      fans_club_available_gift_id_table.create()

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
    fans_club_available_gift_id_table_tuple = {key:None for key in fans_club_available_gift_id_table.get_tuple()}
    owner_user_id          = get_dict_attr(data, "$.data.room.owner_user_id")
    anchor_id              = get_dict_attr(data, "$.data.room.owner.fans_club.data.anchor_id")
    available_gift_ids     = get_dict_attr(data, "$.data.room.owner.fans_club.data.available_gift_ids")
    if len(available_gift_ids) != 0:
      set_dict_attr(fans_club_available_gift_id_table_tuple, "$.now",           now)
      set_dict_attr(fans_club_available_gift_id_table_tuple, "$.platform",      DOUYIN_PLATFORM)
      set_dict_attr(fans_club_available_gift_id_table_tuple, "$.room_id",       str(room_id))
      set_dict_attr(fans_club_available_gift_id_table_tuple, "$.owner_user_id", str(owner_user_id))
      set_dict_attr(fans_club_available_gift_id_table_tuple, "$.anchor_id",     str(anchor_id))
      for available_gift_id_index in range(0, len(available_gift_ids)):
        set_dict_attr(fans_club_available_gift_id_table_tuple, "$.available_gift_id_index", available_gift_id_index)
        set_dict_attr(fans_club_available_gift_id_table_tuple, "$.available_gift_id",       str(available_gift_ids[available_gift_id_index]))

        fans_club_available_gift_id_table.insert_record(fans_club_available_gift_id_table_tuple, on_duplicate='ignore')
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
    fans_club_badge_icon_table_tuple = {key:None for key in fans_club_badge_icon_table.get_tuple()}
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
    fans_club_badge_icon_table.insert_record(fans_club_badge_icon_table_tuple, on_duplicate='ignore')
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
    pay_grade_icon_table_tuple = {key:None for key in pay_grade_icon_table.get_tuple()}
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
      pay_grade_icon_table.insert_record(pay_grade_icon_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(pay_grade_icon_table.get_name(), e))
    raise e
  """
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
    ## create the table if not exist
    ##
    if db.is_table_exist(room_subscribe_table.get_name()) is False:
      room_subscribe_table.create()
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
    room_subscribe_table_tuple = {key:None for key in room_subscribe_table.get_tuple()}
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

    room_subscribe_table.insert_record(room_subscribe_table_tuple, on_duplicate='ignore')
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
    ## create the table if not exist
    ##
    if db.is_table_exist(room_owner_user_attr_table.get_name()) is False:
      room_owner_user_attr_table.create()
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
    room_owner_user_attr_table_tuple = {key:None for key in room_owner_user_attr_table.get_tuple()}
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

    room_owner_user_attr_table.insert_record(room_owner_user_attr_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_owner_user_attr_table.get_name(), e))
    raise e

  ##
  ## RoomAdminPrivilegeTable
  ##
  room_admin_privilege_table = RoomAdminPrivilegeTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(room_admin_privilege_table.get_name()) is False:
      room_admin_privilege_table.create()
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
    room_admin_privilege_table_tuple = {key:None for key in room_admin_privilege_table.get_tuple()}
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

        room_admin_privilege_table.insert_record(room_admin_privilege_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_admin_privilege_table.get_name(), e))
    raise e

  ##
  ## RoomOwnerAuthorStatsTable
  ##
  room_owner_author_stats_table = RoomOwnerAuthorStatsTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(room_owner_author_stats_table.get_name()) is False:
      room_owner_author_stats_table.create()
      ##
      ## +----------------------------+
      ## | Field                      |
      ## +----------------------------+
      ## | start_time                 |
      ## | platform                   |
      ## | room_id                    |
      ## | owner_user_id              |
      ## | variety_show_play_count    |
      ## | video_total_count          |
      ## | video_total_favorite_count |
      ## | video_total_play_count     |
      ## | video_total_series_count   |
      ## | video_total_share_count    |
      ## +----------------------------+
      ##
      author_stats = get_dict_attr(data, "$.data.room.owner.author_stats")
      if author_stats:
        room_owner_author_stats_tuple = {key:None for key in room_owner_author_stats_table.get_tuple()}
        set_dict_attr(room_owner_author_stats_tuple, "$.start_time",                 dat.fromtimestamp(start_time))
        set_dict_attr(room_owner_author_stats_tuple, "$.platform",                   DOUYIN_PLATFORM)
        set_dict_attr(room_owner_author_stats_tuple, "$.room_id",                    str(room_id))
        set_dict_attr(room_owner_author_stats_tuple, "$.owner_user_id",              str(owner_user_id))
        set_dict_attr(room_owner_author_stats_tuple, "$.variety_show_play_count",    get_dict_attr(author_stats, "$.variety_show_play_count"))
        set_dict_attr(room_owner_author_stats_tuple, "$.video_total_count",          get_dict_attr(author_stats, "$.video_total_count"))
        set_dict_attr(room_owner_author_stats_tuple, "$.video_total_favorite_count", get_dict_attr(author_stats, "$.video_total_favorite_count"))
        set_dict_attr(room_owner_author_stats_tuple, "$.video_total_play_count",     get_dict_attr(author_stats, "$.video_total_play_count"))
        set_dict_attr(room_owner_author_stats_tuple, "$.video_total_series_count",   get_dict_attr(author_stats, "$.video_total_series_count"))
        set_dict_attr(room_owner_author_stats_tuple, "$.video_total_share_count",    get_dict_attr(author_stats, "$.video_total_share_count"))
        room_owner_author_stats_table.insert_record(room_owner_author_stats_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_owner_auth_info_table.get_name(), e))
    raise e

  ##
  ## RoomOwnerAuthInfoTable
  ##
  room_owner_auth_info_table = RoomOwnerAuthInfoTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(room_owner_auth_info_table.get_name()) is False:
      room_owner_auth_info_table.create()
    ##
    ## +-----------------------------+
    ## | Field                       |
    ## +-----------------------------+
    ## | start_time                  |
    ## | platform                    |
    ## | room_id                     |
    ## | owner_user_id               |
    ## | exist_authentication_info   |
    ## | account_cert_info           |
    ## | account_type_map            |
    ## | custom_verify               |
    ## | enterprise_verify_reason    |
    ## +-----------------------------+
    ##
    room_owner_auth_info_tuple = {key:None for key in room_owner_auth_info_table.get_tuple()}
    
    owner_user_id         = get_dict_attr(data, "$.data.room.owner_user_id")
    try:
      authentication_info = get_dict_attr(data, "$.data.room.owner.authentication_info")
      if authentication_info is None:
        exist_authentication_info = False
      else:
        exist_authentication_info = True
        account_cert_info         = get_dict_attr(data, "$.data.room.owner.authentication_info.account_cert_info")
        account_type_map          = get_dict_attr(data, "$.data.room.owner.authentication_info.account_type_info.account_type_map")
        custom_verify             = get_dict_attr(data, "$.data.room.owner.authentication_info.custom_verify")
        enterprise_verify_reason  = get_dict_attr(data, "$.data.room.owner.authentication_info.enterprise_verify_reason")
    except AttributeError as e:
      get_logger().error(f"{e}: {room_owner_auth_info_table.get_name()} get exist_authentication_info fail, set FALSE as default!")
      exist_authentication_info = False

    set_dict_attr(room_owner_auth_info_tuple, "$.start_time",                               dat.fromtimestamp(start_time))
    set_dict_attr(room_owner_auth_info_tuple, "$.platform",                                 DOUYIN_PLATFORM)
    set_dict_attr(room_owner_auth_info_tuple, "$.room_id",                                  str(room_id))
    set_dict_attr(room_owner_auth_info_tuple, "$.owner_user_id",                            str(owner_user_id))
    set_dict_attr(room_owner_auth_info_tuple, "$.exist_authentication_info",                exist_authentication_info)
    if exist_authentication_info is True:
      set_dict_attr(room_owner_auth_info_tuple, "$.account_cert_info",        json.dumps(account_cert_info))
      set_dict_attr(room_owner_auth_info_tuple, "$.account_type_map",         json.dumps(account_type_map))
      set_dict_attr(room_owner_auth_info_tuple, "$.custom_verify",            custom_verify)
      set_dict_attr(room_owner_auth_info_tuple, "$.enterprise_verify_reason", enterprise_verify_reason)
    room_owner_auth_info_table.insert_record(room_owner_auth_info_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_owner_auth_info_table.get_name(), e))
    raise e

  if exist_authentication_info is True:
    ##
    ## RoomOwnerAuthLevelTable
    ##
    room_owner_auth_level_table = RoomOwnerAuthLevelTable(db)
    try:
      ##
      ## create the table if not exist
      ##
      if db.is_table_exist(room_owner_auth_level_table.get_name()) is False:
        room_owner_auth_level_table.create()
      ##
      ## +---------------+
      ## | Field         |
      ## +---------------+
      ## | start_time    |
      ## | platform      |
      ## | room_id       |
      ## | owner_user_id |
      ## | level_index   |
      ## | level         |
      ## +---------------+
      ##
      room_owner_auth_level_tuple = {key:None for key in room_owner_auth_level_table.get_tuple()}
      set_dict_attr(room_owner_auth_level_tuple, "$.start_time",    dat.fromtimestamp(start_time))
      set_dict_attr(room_owner_auth_level_tuple, "$.platform",      DOUYIN_PLATFORM)
      set_dict_attr(room_owner_auth_level_tuple, "$.room_id",       str(room_id))
      set_dict_attr(room_owner_auth_level_tuple, "$.owner_user_id", str(owner_user_id))
      level_list = get_dict_attr(data, "$.data.room.owner.authentication_info.level_list")
      for level_index in range(0, len(level_list)):
        set_dict_attr(room_owner_auth_level_tuple, "$.level_index", level_index)
        set_dict_attr(room_owner_auth_level_tuple, "$.level",       level_list[level_index])
        room_owner_auth_level_table.insert_record(room_owner_auth_level_tuple, on_duplicate='ignore')
    except Exception as e:
      get_logger().error("insert {} failed: {}".format(room_owner_auth_level_table.get_name(), e))
      raise e

  ##
  ## RoomOwnerUserDressOwnIdTable
  ##
  room_owner_user_dress_own_id_table = RoomOwnerUserDressOwnIdTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(room_owner_user_dress_own_id_table.get_name()) is False:
      room_owner_user_dress_own_id_table.create()

    ##
    ## +-----------------+
    ## | start_time      |
    ## | platform        |
    ## | room_id         |
    ## | owner_user_id   |
    ## | dress_own_index |
    ## | dress_own_id    |
    ## +-----------------+
    ##
    room_owner_user_dress_own_id_table_tuple = {key:None for key in room_owner_user_dress_own_id_table.get_tuple()}
    start_time = get_dict_attr(data, "$.data.room.start_time")
    # dress_own_index auto increment
    dress_own_ids = get_dict_attr(data, "$.data.room.owner.user_dress_info.dress_own_ids")
    if len(dress_own_ids) != 0:
      set_dict_attr(room_owner_user_dress_own_id_table_tuple, "$.start_time",      start_time)
      set_dict_attr(room_owner_user_dress_own_id_table_tuple, "$.platform",        DOUYIN_PLATFORM)
      set_dict_attr(room_owner_user_dress_own_id_table_tuple, "$.room_id",         str(room_id))
      set_dict_attr(room_owner_user_dress_own_id_table_tuple, "$.owner_user_id",   str(owner_user_id))
      for dress_own_id in dress_own_ids:
        # dress_own_index auto increment
        set_dict_attr(room_owner_user_dress_own_id_table_tuple, "$.dress_own_id",   dress_own_id)

        room_owner_user_dress_own_id_table.insert_record(room_owner_user_dress_own_id_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_owner_user_dress_own_id_table.get_name(), e))
    raise e

  ##
  ## RoomOwnerDressWearIdTable
  ##
  room_owner_dress_wear_id_table = RoomOwnerDressWearIdTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(room_owner_dress_wear_id_table.get_name()) is False:
      room_owner_dress_wear_id_table.create()

    ##
    ## +------------------+
    ## | Field            |
    ## +------------------+
    ## | start_time       |
    ## | platform         |
    ## | room_id          |
    ## | owner_user_id    |
    ## | dress_wear_index |
    ## | dress_wear_id    |
    ## +------------------+
    ##
    room_owner_dress_wear_id_table_tuple = {key:None for key in room_owner_dress_wear_id_table.get_tuple()}
    start_time = get_dict_attr(data, "$.data.room.start_time")
    # dress_wear_index
    dress_wear_ids = get_dict_attr(data, "$.data.room.owner.user_dress_info.dress_wear_ids")
    if len(dress_wear_ids) != 0:
      set_dict_attr(room_owner_dress_wear_id_table_tuple, "$.start_time",      start_time)
      set_dict_attr(room_owner_dress_wear_id_table_tuple, "$.platform",        DOUYIN_PLATFORM)
      set_dict_attr(room_owner_dress_wear_id_table_tuple, "$.room_id",         str(room_id))
      set_dict_attr(room_owner_dress_wear_id_table_tuple, "$.owner_user_id",   str(owner_user_id))
      for dress_wear_id in dress_wear_ids:
        # set_dict_attr(room_owner_dress_wear_id_table_tuple, "$.dress_wear_index",   dress_wear_index)
        set_dict_attr(room_owner_dress_wear_id_table_tuple, "$.dress_wear_id",   str(dress_own_id))

        room_owner_dress_wear_id_table.insert_record(room_owner_dress_wear_id_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_owner_dress_wear_id_table.get_name(), e))
    raise e

  ##
  ## RoomPackMetaTable
  ##
  room_pack_meta_table = RoomPackMetaTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(room_pack_meta_table.get_name()) is False:
      room_pack_meta_table.create()

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
    room_pack_meta_table_tuple = {key:None for key in room_pack_meta_table.get_tuple()}
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

    room_pack_meta_table.insert_record(room_pack_meta_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_pack_meta_table.get_name(), e))
    raise e

  ##
  ## RoomPaidLiveDataTable
  ##
  room_paid_live_data_table = RoomPaidLiveDataTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(room_paid_live_data_table.get_name()) is False:
      room_paid_live_data_table.create()

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
    room_paid_live_data_table_tuple = {key:None for key in room_paid_live_data_table.get_tuple()}
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

    room_paid_live_data_table.insert_record(room_paid_live_data_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_paid_live_data_table.get_name(), e))
    raise e

  ##
  ## RoomAuthTable
  ##
  room_auth_table = RoomAuthTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(room_auth_table.get_name()) is False:
      room_auth_table.create()

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
    room_auth_table_tuple = {key:None for key in room_auth_table.get_tuple()}
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

    room_auth_table.insert_record(room_auth_table_tuple, on_duplicate='ignore')
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
    ## create the table if not exist
    ##
    if db.is_table_exist(room_sharing_music_id_table.get_name()) is False:
      room_sharing_music_id_table.create()
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
    room_sharing_music_id_table_tuple = {key:None for key in room_sharing_music_id_table.get_tuple()}
    start_time = get_dict_attr(data, "$.data.room.start_time")
    # dress_wear_index
    sharing_music_id_list = get_dict_attr(data, "$.data.room.sharing_music_id_list")
    if len(sharing_music_id_list) != 0:
      set_dict_attr(room_sharing_music_id_table_tuple, "$.start_time",      start_time)
      set_dict_attr(room_sharing_music_id_table_tuple, "$.platform",        DOUYIN_PLATFORM)
      set_dict_attr(room_sharing_music_id_table_tuple, "$.room_id",         str(room_id))
      for sharing_music_id in sharing_music_id_list:
        # sharing_music_index auto increment
        set_dict_attr(room_sharing_music_id_table_tuple, "$.sharing_music_id",   str(sharing_music_id))

        room_sharing_music_id_table.insert_record(room_sharing_music_id_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_sharing_music_id_table.get_name(), e))
    raise e

  ##
  ## RoomShortTouchAreaConfigTable
  ##
  room_short_touch_area_config_table = RoomShortTouchAreaConfigTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(room_short_touch_area_config_table.get_name()) is False:
      room_short_touch_area_config_table.create()
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
    room_short_touch_area_config_table_tuple = {key:None for key in room_short_touch_area_config_table.get_tuple()}
    forbidden_types_map = get_dict_attr(data, "$.data.room.short_touch_area_config.forbidden_types_map")
    
    set_dict_attr(room_short_touch_area_config_table_tuple, "$.now",                 now)
    set_dict_attr(room_short_touch_area_config_table_tuple, "$.platform",            DOUYIN_PLATFORM)
    set_dict_attr(room_short_touch_area_config_table_tuple, "$.room_id",             str(room_id))
    set_dict_attr(room_short_touch_area_config_table_tuple, "$.forbidden_types_map", json.dumps(forbidden_types_map))

    room_short_touch_area_config_table.insert_record(room_short_touch_area_config_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_short_touch_area_config_table.get_name(), e))
    raise e

  ##
  ## RoomShortTouchAreaConfigElementTable
  ##
  room_short_touch_area_config_element_table = RoomShortTouchAreaConfigElementTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(room_short_touch_area_config_element_table.get_name()) is False:
      room_short_touch_area_config_element_table.create()
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
    room_short_touch_area_config_element_table_tuple = {key:None for key in room_short_touch_area_config_element_table.get_tuple()}
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

        room_short_touch_area_config_element_table.insert_record(room_short_touch_area_config_element_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_short_touch_area_config_element_table.get_name(), e))
    raise e

  ##
  ## RoomShortTouchAreaConfigStrategyFeatWhitelistTable
  ##
  room_short_touch_area_config_strategy_feat_whitelist_table = RoomShortTouchAreaConfigStrategyFeatWhitelistTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(room_short_touch_area_config_strategy_feat_whitelist_table.get_name()) is False:
      room_short_touch_area_config_strategy_feat_whitelist_table.create()
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
    room_short_touch_area_config_strategy_feat_whitelist_table_tuple = {key:None for key in room_short_touch_area_config_strategy_feat_whitelist_table.get_tuple()}
    strategy_feat_whitelist = get_dict_attr(data, "$.data.room.short_touch_area_config.strategy_feat_whitelist")
    if len(strategy_feat_whitelist) != 0:
      set_dict_attr(room_short_touch_area_config_strategy_feat_whitelist_table_tuple, "$.start_time",    dat.fromtimestamp(start_time))
      set_dict_attr(room_short_touch_area_config_strategy_feat_whitelist_table_tuple, "$.platform",      DOUYIN_PLATFORM)
      set_dict_attr(room_short_touch_area_config_strategy_feat_whitelist_table_tuple, "$.room_id",       str(room_id))
  
      for whitelist_tag_index in range(0, len(strategy_feat_whitelist)):
        set_dict_attr(room_short_touch_area_config_strategy_feat_whitelist_table_tuple, "$.whitelist_tag_index", whitelist_tag_index)
        set_dict_attr(room_short_touch_area_config_strategy_feat_whitelist_table_tuple, "$.whitelist_tag",       strategy_feat_whitelist[whitelist_tag_index])
        room_short_touch_area_config_strategy_feat_whitelist_table.insert_record(room_short_touch_area_config_strategy_feat_whitelist_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_short_touch_area_config_strategy_feat_whitelist_table.get_name(), e))
    raise e

  ##
  ## RoomTempStateConditionMapTable
  ##
  room_temp_state_condition_map_table = RoomTempStateConditionMapTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(room_temp_state_condition_map_table.get_name()) is False:
      room_temp_state_condition_map_table.create()
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
    room_temp_state_condition_map_table_tuple = {key:None for key in room_temp_state_condition_map_table.get_tuple()}
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

        room_temp_state_condition_map_table.insert_record(room_temp_state_condition_map_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_temp_state_condition_map_table.get_name(), e))
    raise e

  ##
  ## RoomTempStateGlobalConditionIgnoreStrategyTypeTable
  ##
  room_temp_state_global_condition_ignore_strategy_type_table = RoomTempStateGlobalConditionIgnoreStrategyTypeTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(room_temp_state_global_condition_ignore_strategy_type_table.get_name()) is False:
      room_temp_state_global_condition_ignore_strategy_type_table.create()
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
    room_temp_state_global_condition_ignore_strategy_type_table_tuple = {key:None for key in room_temp_state_global_condition_ignore_strategy_type_table.get_tuple()}
    ignore_strategy_types = get_dict_attr(data, "$.data.room.short_touch_area_config.temp_state_global_condition.ignore_strategy_types")
    if len(ignore_strategy_types) != 0:
      set_dict_attr(room_temp_state_global_condition_ignore_strategy_type_table_tuple, "$.now",           now)
      set_dict_attr(room_temp_state_global_condition_ignore_strategy_type_table_tuple, "$.platform",      DOUYIN_PLATFORM)
      set_dict_attr(room_temp_state_global_condition_ignore_strategy_type_table_tuple, "$.room_id",       str(room_id))
      for ignore_strategy_type in ignore_strategy_types:
        # ignore_strategy_type_index auto increment
        set_dict_attr(room_temp_state_global_condition_ignore_strategy_type_table_tuple, "$.ignore_strategy_type", ignore_strategy_type)

        room_temp_state_global_condition_ignore_strategy_type_table.insert_record(room_temp_state_global_condition_ignore_strategy_type_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_temp_state_global_condition_ignore_strategy_type_table.get_name(), e))
    raise e

  ##
  ## RoomTempStateGlobalConditionTable
  ##
  room_temp_state_global_condition_table = RoomTempStateGlobalConditionTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(room_temp_state_global_condition_table.get_name()) is False:
      room_temp_state_global_condition_table.create()
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
    room_temp_state_global_condition_table_tuple = {key:None for key in room_temp_state_global_condition_table.get_tuple()}
    allow_count = get_dict_attr(data, "$.data.room.short_touch_area_config.temp_state_global_condition.allow_count")
    duration_gap = get_dict_attr(data, "$.data.room.short_touch_area_config.temp_state_global_condition.duration_gap")
    
    set_dict_attr(room_temp_state_global_condition_table_tuple, "$.now",          now)
    set_dict_attr(room_temp_state_global_condition_table_tuple, "$.platform",     DOUYIN_PLATFORM)
    set_dict_attr(room_temp_state_global_condition_table_tuple, "$.room_id",      str(room_id))
    set_dict_attr(room_temp_state_global_condition_table_tuple, "$.allow_count",  allow_count)
    set_dict_attr(room_temp_state_global_condition_table_tuple, "$.duration_gap", duration_gap)

    room_temp_state_global_condition_table.insert_record(room_temp_state_global_condition_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_temp_state_global_condition_table.get_name(), e))
    raise e

  ##
  ## RoomTempStateStrategyTable
  ##
  room_temp_state_strategy_table = RoomTempStateStrategyTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(room_temp_state_strategy_table.get_name()) is False:
      room_temp_state_strategy_table.create()
    ##
    ## +-------------------+
    ## | Field             |
    ## +-------------------+
    ## | now               |
    ## | platform          |
    ## | room_id           |
    ## | short_touch_type  |
    ## +-------------------+
    ##
    room_temp_state_strategy_table_tuple = {key:None for key in room_temp_state_strategy_table.get_tuple()}
    temp_state_strategy = get_dict_attr(data, "$.data.room.short_touch_area_config.temp_state_strategy")
    if temp_state_strategy is not None:
      set_dict_attr(room_temp_state_strategy_table_tuple, "$.now",           now)
      set_dict_attr(room_temp_state_strategy_table_tuple, "$.platform",      DOUYIN_PLATFORM)
      set_dict_attr(room_temp_state_strategy_table_tuple, "$.room_id",       str(room_id))
  
      for temp_state_strategy_key, temp_state_strategy_value in dict(temp_state_strategy).items():
        short_touch_type   = get_dict_attr(temp_state_strategy_value, "$.short_touch_type")

        set_dict_attr(room_temp_state_strategy_table_tuple, "$.short_touch_type",   short_touch_type)
        room_temp_state_strategy_table.insert_record(room_temp_state_strategy_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_temp_state_strategy_table.get_name(), e))
    raise e

  ##
  ## RoomTempStateStrategyMapTable
  ##
  room_temp_state_strategy_map_table = RoomTempStateStrategyMapTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(room_temp_state_strategy_map_table.get_name()) is False:
      room_temp_state_strategy_map_table.create()
    ##
    ## +-------------------+
    ## | Field             |
    ## +-------------------+
    ## | now               |
    ## | platform          |
    ## | room_id           |
    ## | short_touch_type  |
    ## | duration          |
    ## | strategy_method   |
    ## | priority          |
    ## | strategy_type     |
    ## +-------------------+
    ##
    room_temp_state_strategy_map_table_tuple = {key:None for key in room_temp_state_strategy_map_table.get_tuple()}
    temp_state_strategy = get_dict_attr(data, "$.data.room.short_touch_area_config.temp_state_strategy")
    if temp_state_strategy is not None:
      set_dict_attr(room_temp_state_strategy_map_table_tuple, "$.now",           now)
      set_dict_attr(room_temp_state_strategy_map_table_tuple, "$.platform",      DOUYIN_PLATFORM)
      set_dict_attr(room_temp_state_strategy_map_table_tuple, "$.room_id",       str(room_id))
  
      ##
      ## loop temp_state_strategy
      ##
      for temp_state_strategy_key, temp_state_strategy_value in  dict(temp_state_strategy).items():
        short_touch_type   = get_dict_attr(temp_state_strategy_value, "$.short_touch_type")
        set_dict_attr(room_temp_state_strategy_map_table_tuple, "$.short_touch_type",   short_touch_type)

        ##
        ## loop strategy_map
        ##
        strategy_map = get_dict_attr(temp_state_strategy_value, "$.strategy_map")
        for strategy_map_key, strategy_map_value in dict(strategy_map).items():
          duration        = get_dict_attr(strategy_map_value, "$.duration")
          strategy_method = get_dict_attr(strategy_map_value, "$.strategy_method")
          priority        = get_dict_attr(strategy_map_value, "$.type.priority")
          strategy_type   = get_dict_attr(strategy_map_value, "$.type.strategy_type")

          set_dict_attr(room_temp_state_strategy_map_table_tuple, "$.duration",        duration)
          set_dict_attr(room_temp_state_strategy_map_table_tuple, "$.strategy_method", strategy_method)
          set_dict_attr(room_temp_state_strategy_map_table_tuple, "$.priority",        priority)
          set_dict_attr(room_temp_state_strategy_map_table_tuple, "$.strategy_type",   strategy_type)
          room_temp_state_strategy_map_table.insert_record(room_temp_state_strategy_map_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_temp_state_strategy_map_table.get_name(), e))
    raise e

  ##
  ## RoomRecordTable
  ##
  room_record_table = RoomRecordTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(room_record_table.get_name()) is False:
      room_record_table.create()
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
    room_record_table_tuple = {key:None for key in room_record_table.get_tuple()}
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

    room_record_table.insert_record(room_record_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_record_table.get_name(), e))
    raise e

  ##
  ## LiveStreamTable
  ##
  live_stream_table = LiveStreamTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(live_stream_table.get_name()) is False:
      live_stream_table.create()
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
    live_stream_table_tuple = {key:None for key in live_stream_table.get_tuple()}
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

    live_stream_table.insert_record(live_stream_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(live_stream_table.get_name(), e))
    raise e

  ##
  ## RoomLinkMicTable
  ##
  room_link_mic_table = RoomLinkMicTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(room_link_mic_table.get_name()) is False:
      room_link_mic_table.create()
    ##
    ## +-----------------------+
    ## | Field                 |
    ## +-----------------------+
    ## | now                   |
    ## | platform              |
    ## | room_id               |
    ## | channel_id            |
    ## | linkmic_anchor_count  |
    ## | rival_anchor_id       |
    ## | rival_anchor_open_id  |
    ## +-----------------------+
    ##
    room_link_mic = get_dict_attr(data, "$.data.room.link_mic")
    if room_link_mic:
      room_link_mic_tuple = {key:None for key in room_link_mic_table.get_tuple()}
      set_dict_attr(room_link_mic_tuple, "$.now",       now)
      set_dict_attr(room_link_mic_tuple, "$.platform",  DOUYIN_PLATFORM)
      set_dict_attr(room_link_mic_tuple, "$.room_id",   str(room_id))

      room_link_mic_channel_id = get_dict_attr(room_link_mic, "$.channel_id")
      set_dict_attr(room_link_mic_tuple, "$.channel_id",           str(room_link_mic_channel_id))
      set_dict_attr(room_link_mic_tuple, "$.linkmic_anchor_count", get_dict_attr(room_link_mic, "$.linkmic_anchor_count"))
      set_dict_attr(room_link_mic_tuple, "$.rival_anchor_id",      str(get_dict_attr(room_link_mic, "$.rival_anchor_id")))
      set_dict_attr(room_link_mic_tuple, "$.rival_anchor_open_id", str(get_dict_attr(room_link_mic, "$.rival_anchor_open_id")))
      room_link_mic_table.insert_record(room_link_mic_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_link_mic_table.get_name(), e))
    raise e

  if room_link_mic:
    ##
    ## RoomLinkMicBattleScoreTable
    ##
    room_link_mic_battle_score_table = RoomLinkMicBattleScoreTable(db)
    try:
      ##
      ## create the table if not exist
      ##
      if db.is_table_exist(room_link_mic_battle_score_table.get_name()) is False:
        room_link_mic_battle_score_table.create()
      ##
      ## +-----------------------+
      ## | Field                 |
      ## +-----------------------+
      ## | now                   |
      ## | platform              |
      ## | room_id               |
      ## | channel_id            |
      ## | battle_score_index    |
      ## | open_id               |
      ## | score                 |
      ## | user_id               |
      ## +-----------------------+
      ##
      battle_scores = get_dict_attr(data, "$.data.room.link_mic.battle_scores")
      if battle_scores:
        room_link_mic_battle_score_tuple = {key:None for key in room_link_mic_battle_score_table.get_tuple()}
        for battle_score_index in range(0, len(battle_scores)):
          set_dict_attr(room_link_mic_battle_score_tuple, "$.now",                  now)
          set_dict_attr(room_link_mic_battle_score_tuple, "$.platform",             DOUYIN_PLATFORM)
          set_dict_attr(room_link_mic_battle_score_tuple, "$.room_id",              str(room_id))
          set_dict_attr(room_link_mic_battle_score_tuple, "$.channel_id",           str(room_link_mic_channel_id))
          set_dict_attr(room_link_mic_battle_score_tuple, "$.battle_score_index",   battle_score_index)
          set_dict_attr(room_link_mic_battle_score_tuple, "$.open_id",              get_dict_attr(battle_scores[battle_score_index], "$.open_id"))
          set_dict_attr(room_link_mic_battle_score_tuple, "$.score",                str(get_dict_attr(battle_scores[battle_score_index], "$.score")))
          set_dict_attr(room_link_mic_battle_score_tuple, "$.user_id",              str(get_dict_attr(battle_scores[battle_score_index], "$.user_id")))
          room_link_mic_battle_score_table.insert_record(room_link_mic_battle_score_tuple, on_duplicate='ignore')
    except Exception as e:
      get_logger().error("insert {} failed: {}".format(room_link_mic_battle_score_table.get_name(), e))
      raise e

    ##
    ## RoomLinkMicBattleSettingTable
    ##
    room_link_mic_battle_setting_table = RoomLinkMicBattleSettingTable(db)
    try:
      ##
      ## create the table if not exist
      ##
      if db.is_table_exist(room_link_mic_battle_setting_table.get_name()) is False:
        room_link_mic_battle_setting_table.create()
      ##
      ## +---------------+
      ## | Field         |
      ## +---------------+
      ## | now           |
      ## | platform      |
      ## | room_id       |
      ## | channel_id    |
      ## | activity_mode |
      ## | battle_id     |
      ## | duration      |
      ## | finished      |
      ## | match_type    |
      ## | play_mode     |
      ## | start_time    |
      ## | start_time_ms |
      ## | team_mode     |
      ## | theme         |
      ## +---------------+
      ##
      room_link_mic_battle_settings = get_dict_attr(data, "$.data.room.link_mic.battle_settings")
      if room_link_mic_battle_settings:
        room_link_mic_battle_setting_tuple = {key:None for key in room_link_mic_battle_setting_table.get_tuple()}
        set_dict_attr(room_link_mic_battle_setting_tuple, "$.now",           now)
        set_dict_attr(room_link_mic_battle_setting_tuple, "$.platform",      DOUYIN_PLATFORM)
        set_dict_attr(room_link_mic_battle_setting_tuple, "$.room_id",       str(room_id))

        set_dict_attr(room_link_mic_battle_setting_tuple, "$.channel_id",    str(room_link_mic_channel_id))
        set_dict_attr(room_link_mic_battle_setting_tuple, "$.activity_mode", get_dict_attr(room_link_mic_battle_settings, "$.activity_mode"))
        set_dict_attr(room_link_mic_battle_setting_tuple, "$.battle_id",     str(get_dict_attr(room_link_mic_battle_settings, "$.battle_id")))
        set_dict_attr(room_link_mic_battle_setting_tuple, "$.duration",      get_dict_attr(room_link_mic_battle_settings, "$.duration"))
        set_dict_attr(room_link_mic_battle_setting_tuple, "$.finished",      get_dict_attr(room_link_mic_battle_settings, "$.finished"))
        set_dict_attr(room_link_mic_battle_setting_tuple, "$.match_type",    get_dict_attr(room_link_mic_battle_settings, "$.match_type"))
        set_dict_attr(room_link_mic_battle_setting_tuple, "$.play_mode",     get_dict_attr(room_link_mic_battle_settings, "$.play_mode"))
        set_dict_attr(room_link_mic_battle_setting_tuple, "$.start_time",    dat.fromtimestamp(get_dict_attr(room_link_mic_battle_settings, "$.start_time")))
        set_dict_attr(room_link_mic_battle_setting_tuple, "$.start_time_ms", dat.fromtimestamp(get_dict_attr(room_link_mic_battle_settings, "$.start_time_ms")/1000.0))
        set_dict_attr(room_link_mic_battle_setting_tuple, "$.team_mode",     get_dict_attr(room_link_mic_battle_settings, "$.team_mode"))
        set_dict_attr(room_link_mic_battle_setting_tuple, "$.theme",         str(get_dict_attr(room_link_mic_battle_settings, "$.theme")))
        room_link_mic_battle_setting_table.insert_record(room_link_mic_battle_setting_tuple, on_duplicate='ignore')
    except Exception as e:
      get_logger().error("insert {} failed: {}".format(room_link_mic_battle_setting_table.get_name(), e))
      raise e

    ##
    ## RoomLinkMicChannelInfoTable
    ##
    room_link_mic_channel_info_table = RoomLinkMicChannelInfoTable(db)
    try:
      ##
      ## create the table if not exist
      ##
      if db.is_table_exist(room_link_mic_channel_info_table.get_name()) is False:
        room_link_mic_channel_info_table.create()
      ##
      ## +---------------+
      ## | Field         |
      ## +---------------+
      ## | now           |
      ## | platform      |
      ## | room_id       |
      ## | channel_id    |
      ## | dimension     |
      ## | layout        |
      ## | vendor        |
      ## +---------------+
      ##
      room_link_mic_channel_info = get_dict_attr(data, "$.data.room.link_mic.channel_info")
      if room_link_mic_channel_info:
        room_link_mic_channel_info_tuple = {key:None for key in room_link_mic_channel_info_table.get_tuple()}
        set_dict_attr(room_link_mic_channel_info_tuple, "$.now",        now)
        set_dict_attr(room_link_mic_channel_info_tuple, "$.platform",   DOUYIN_PLATFORM)
        set_dict_attr(room_link_mic_channel_info_tuple, "$.room_id",    str(room_id))

        set_dict_attr(room_link_mic_channel_info_tuple, "$.channel_id", str(room_link_mic_channel_id))
        set_dict_attr(room_link_mic_channel_info_tuple, "$.dimension",  get_dict_attr(room_link_mic_channel_info, "$.dimension"))
        set_dict_attr(room_link_mic_channel_info_tuple, "$.layout",     get_dict_attr(room_link_mic_channel_info, "$.layout"))
        set_dict_attr(room_link_mic_channel_info_tuple, "$.vendor",     get_dict_attr(room_link_mic_channel_info, "$.vendor"))
        room_link_mic_channel_info_table.insert_record(room_link_mic_channel_info_tuple, on_duplicate='ignore')
    except Exception as e:
      get_logger().error("insert {} failed: {}".format(room_link_mic_channel_info_table.get_name(), e))
      raise e

  ##
  ## StreamCandidateResolutionTable
  ##
  stream_candidate_resulution_table = StreamCandidateResolutionTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(stream_candidate_resulution_table.get_name()) is False:
      stream_candidate_resulution_table.create()
    ##
    ## +----------------------+
    ## | Field                |
    ## +----------------------+
    ## | start_time           |
    ## | platform             |
    ## | room_id              |
    ## | stream_id            |
    ## | resolution_index     |
    ## | candidate_resolution |
    ## +----------------------+
    ##
    stream_candidate_resulution_table_tuple = {key:None for key in stream_candidate_resulution_table.get_tuple()}
    stream_id = get_dict_attr(data, "$.data.room.stream_id")
    candidate_resolutions = get_dict_attr(data, "$.data.room.stream_url.candidate_resolution")
    if len(candidate_resolutions) != 0:
      set_dict_attr(stream_candidate_resulution_table_tuple, "$.start_time",           dat.fromtimestamp(start_time))
      set_dict_attr(stream_candidate_resulution_table_tuple, "$.platform",             DOUYIN_PLATFORM)
      set_dict_attr(stream_candidate_resulution_table_tuple, "$.room_id",              str(room_id))
      set_dict_attr(stream_candidate_resulution_table_tuple, "$.stream_id",            str(stream_id))
      for resolution_index in range(0, len(candidate_resolutions)):
        set_dict_attr(stream_candidate_resulution_table_tuple, "$.resolution_index",     resolution_index)
        set_dict_attr(stream_candidate_resulution_table_tuple, "$.candidate_resolution", candidate_resolutions[resolution_index])
        stream_candidate_resulution_table.insert_record(stream_candidate_resulution_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(stream_candidate_resulution_table.get_name(), e))
    raise e

  ##
  ## StreamCompletePushUrlTable
  ##
  stream_complete_push_url_table = StreamCompletePushUrlTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(stream_complete_push_url_table.get_name()) is False:
      stream_complete_push_url_table.create()
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
    stream_complete_push_url_table_tuple = {key:None for key in stream_complete_push_url_table.get_tuple()}
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

      stream_complete_push_url_table.insert_record(stream_complete_push_url_table_tuple, on_duplicate='ignore')    
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(stream_complete_push_url_table.get_name(), e))
    raise e

  ##
  ## LiveCoreSdkDataTable
  ##
  live_core_sdk_data_table = LiveCoreSdkDataTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(live_core_sdk_data_table.get_name()) is False:
      live_core_sdk_data_table.create()
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
    live_core_sdk_data_table_tuple = {key:None for key in live_core_sdk_data_table.get_tuple()}
    size = get_dict_attr(data, "$.data.room.stream_url.live_core_sdk_data.size")
    
    set_dict_attr(live_core_sdk_data_table_tuple, "$.now",      now)
    set_dict_attr(live_core_sdk_data_table_tuple, "$.platform", DOUYIN_PLATFORM)
    set_dict_attr(live_core_sdk_data_table_tuple, "$.room_id",  str(room_id))
    set_dict_attr(live_core_sdk_data_table_tuple, "$.size",     size)

    live_core_sdk_data_table.insert_record(live_core_sdk_data_table_tuple, on_duplicate='ignore') 
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(live_core_sdk_data_table.get_name(), e))
    raise e

  ##
  ## LiveCoreSdkPullDataTable
  ##
  live_core_sdk_pull_data_table = LiveCoreSdkPullDataTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(live_core_sdk_pull_data_table.get_name()) is False:
      live_core_sdk_pull_data_table.create()
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
    live_core_sdk_pull_data_table_tuple = {key:None for key in live_core_sdk_pull_data_table.get_tuple()}
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

    live_core_sdk_pull_data_table.insert_record(live_core_sdk_pull_data_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(stream_complete_push_url_table.get_name(), e))
    raise e

  ##
  ## LiveCoreSdkPullFlvDataTable
  ##
  live_core_sdk_pull_flv_data_table = LiveCoreSdkPullFlvDataTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(live_core_sdk_pull_flv_data_table.get_name()) is False:
      live_core_sdk_pull_flv_data_table.create()
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
    live_core_sdk_pull_flv_data_table_tuple = {key:None for key in live_core_sdk_pull_flv_data_table.get_tuple()}
    Flvs = get_dict_attr(data, "$.data.room.stream_url.live_core_sdk_data.pull_data.Flv")
    if len(Flvs) != 0:
      set_dict_attr(live_core_sdk_pull_flv_data_table_tuple, "$.now",                  now)
      set_dict_attr(live_core_sdk_pull_flv_data_table_tuple, "$.platform",             DOUYIN_PLATFORM)
      set_dict_attr(live_core_sdk_pull_flv_data_table_tuple, "$.room_id",              str(room_id))
  
      for Flv in Flvs:
        # Flv_index auto increment
        set_dict_attr(live_core_sdk_pull_flv_data_table_tuple, "$.Flv",                  Flv)
        live_core_sdk_pull_flv_data_table.insert_record(live_core_sdk_pull_flv_data_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(live_core_sdk_pull_flv_data_table.get_name(), e))
    raise e

  ##
  ## LiveCoreSdkPullHlsDataTable
  ##
  live_core_sdk_pull_hls_data_table = LiveCoreSdkPullHlsDataTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(live_core_sdk_pull_hls_data_table.get_name()) is False:
      live_core_sdk_pull_hls_data_table.create()
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
    live_core_sdk_pull_hls_data_table_tuple = {key:None for key in live_core_sdk_pull_hls_data_table.get_tuple()}
    Hlses = get_dict_attr(data, "$.data.room.stream_url.live_core_sdk_data.pull_data.Hls")
    if len(Hlses) != 0:
      set_dict_attr(live_core_sdk_pull_hls_data_table_tuple, "$.now",                  now)
      set_dict_attr(live_core_sdk_pull_hls_data_table_tuple, "$.platform",             DOUYIN_PLATFORM)
      set_dict_attr(live_core_sdk_pull_hls_data_table_tuple, "$.room_id",              str(room_id))
      for Hls in Hlses:
        # Hls_index auto increment
        set_dict_attr(live_core_sdk_pull_hls_data_table_tuple, "$.Hls",                  Hls)
        live_core_sdk_pull_hls_data_table.insert_record(live_core_sdk_pull_hls_data_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(live_core_sdk_pull_hls_data_table.get_name(), e))
    raise e

  ##
  ## LiveCoreSdkPullDataOptionTable
  ##
  live_core_sdk_pull_data_option_table = LiveCoreSdkPullDataOptionTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(live_core_sdk_pull_data_option_table.get_name()) is False:
      live_core_sdk_pull_data_option_table.create()
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
    live_core_sdk_pull_data_option_table_tuple = {key:None for key in live_core_sdk_pull_data_option_table.get_tuple()}
    vpass_default = get_dict_attr(data, "$.data.room.stream_url.live_core_sdk_data.pull_data.options.vpass_default")
    
    set_dict_attr(live_core_sdk_pull_data_option_table_tuple, "$.now",                  now)
    set_dict_attr(live_core_sdk_pull_data_option_table_tuple, "$.platform",             DOUYIN_PLATFORM)
    set_dict_attr(live_core_sdk_pull_data_option_table_tuple, "$.room_id",              str(room_id))
    set_dict_attr(live_core_sdk_pull_data_option_table_tuple, "$.vpass_default",        vpass_default)
    
    if vpass_default is not None:
      live_core_sdk_pull_data_option_table.insert_record(live_core_sdk_pull_data_option_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(live_core_sdk_pull_data_option_table.get_name(), e))
    raise e

  ##
  ## LiveCoreSdkPullQualityDataTable
  ##
  live_core_sdk_pull_quality_data_table = LiveCoreSdkPullQualityDataTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(live_core_sdk_pull_quality_data_table.get_name()) is False:
      live_core_sdk_pull_quality_data_table.create()
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
    live_core_sdk_pull_quality_data_table_tuple = {key: None for key in live_core_sdk_pull_quality_data_table.get_tuple()}
    qualities          = get_dict_attr(data, "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities")
    if len(qualities) != 0:
      set_dict_attr(live_core_sdk_pull_quality_data_table_tuple, "$.start_time",           dat.fromtimestamp(start_time))
      set_dict_attr(live_core_sdk_pull_quality_data_table_tuple, "$.platform",             DOUYIN_PLATFORM)
      set_dict_attr(live_core_sdk_pull_quality_data_table_tuple, "$.room_id",              str(room_id))

      for quality_index in range(0, len(qualities)):
        additional_content = get_dict_attr(qualities[quality_index], "$.additional_content")
        disable            = get_dict_attr(qualities[quality_index], "$.disable")
        fps                = get_dict_attr(qualities[quality_index], "$.fps")
        level              = get_dict_attr(qualities[quality_index], "$.level")
        name               = get_dict_attr(qualities[quality_index], "$.name")
        resolution         = get_dict_attr(qualities[quality_index], "$.resolution")
        sdk_key            = get_dict_attr(qualities[quality_index], "$.sdk_key")
        v_bit_rate         = get_dict_attr(qualities[quality_index], "$.v_bit_rate")
        v_codec            = get_dict_attr(qualities[quality_index], "$.v_codec")
        
        set_dict_attr(live_core_sdk_pull_quality_data_table_tuple, "$.quality_index",        quality_index)
        set_dict_attr(live_core_sdk_pull_quality_data_table_tuple, "$.additional_content",   additional_content)
        set_dict_attr(live_core_sdk_pull_quality_data_table_tuple, "$.disable",              disable)
        set_dict_attr(live_core_sdk_pull_quality_data_table_tuple, "$.fps",                  fps)
        set_dict_attr(live_core_sdk_pull_quality_data_table_tuple, "$.level",                level)
        set_dict_attr(live_core_sdk_pull_quality_data_table_tuple, "$.name",                 name)
        set_dict_attr(live_core_sdk_pull_quality_data_table_tuple, "$.resolution",           resolution)
        set_dict_attr(live_core_sdk_pull_quality_data_table_tuple, "$.sdk_key",              sdk_key)
        set_dict_attr(live_core_sdk_pull_quality_data_table_tuple, "$.v_bit_rate",           v_bit_rate)
        set_dict_attr(live_core_sdk_pull_quality_data_table_tuple, "$.v_codec",              v_codec)

        live_core_sdk_pull_quality_data_table.insert_record(live_core_sdk_pull_quality_data_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(live_core_sdk_pull_quality_data_table.get_name(), e))
    raise e

  ##
  ## LiveCoreSdkPullDefaultQualityDataTable
  ##
  live_core_sdk_pull_default_quality_data_table = LiveCoreSdkPullDefaultQualityDataTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(live_core_sdk_pull_default_quality_data_table.get_name()) is False:
      live_core_sdk_pull_default_quality_data_table.create()
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
    live_core_sdk_pull_default_quality_data_table_tuple = {key:None for key in live_core_sdk_pull_default_quality_data_table.get_tuple()}
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

    live_core_sdk_pull_default_quality_data_table.insert_record(live_core_sdk_pull_default_quality_data_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(live_core_sdk_pull_default_quality_data_table.get_name(), e))
    raise e
  
  ##
  ## StreamPushUrlTable
  ##
  stream_push_url_table = StreamPushUrlTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(stream_push_url_table.get_name()) is False:
      stream_push_url_table.create()
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
    stream_push_url_table_tuple = {key:None for key in stream_push_url_table.get_tuple()}
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
        stream_push_url_table.insert_record(stream_push_url_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(stream_push_url_table.get_name(), e))
    raise e      

  ##
  ## RoomTagTable
  ##
  room_tag_table = RoomTagTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(room_tag_table.get_name()) is False:
      room_tag_table.create()
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
    room_tag_table_tuple = {key:None for key in room_tag_table.get_tuple()}
    # tag_index
    tags = get_dict_attr(data, "$.data.room.tags")
    if len(tags) != 0:
      set_dict_attr(room_tag_table_tuple, "$.now",       now)
      set_dict_attr(room_tag_table_tuple, "$.platform",  DOUYIN_PLATFORM)
      set_dict_attr(room_tag_table_tuple, "$.room_id",   str(room_id))
      for tag in tags:
        # tag_index auto increment
        set_dict_attr(room_tag_table_tuple, "$.tag",       tag)

        room_tag_table.insert_record(room_tag_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_tag_table.get_name(), e))
    raise e

  """
  ##
  ## RoomTopFansTable
  ##
  room_top_fans_table = RoomTopFansTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(room_top_fans_table.get_name()) is False:
      room_top_fans_table.create()
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
    room_top_fans_table_tuple = {key:None for key in room_top_fans_table.get_tuple()}
    top_fans = get_dict_attr(data, "$.data.room.top_fans")
    if len(top_fans) != 0:
      set_dict_attr(room_top_fans_table_tuple, "$.now",      now)
      set_dict_attr(room_top_fans_table_tuple, "$.platform", DOUYIN_PLATFORM)
      set_dict_attr(room_top_fans_table_tuple, "$.room_id",  str(room_id))
      
      for top_fan in top_fans:
        # set_dict_attr(room_top_fans_table_tuple, "$.fans_index", fans_index)
        set_dict_attr(room_top_fans_table_tuple, "$.top_fans",   top_fan)

        room_top_fans_table.insert_record(room_top_fans_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_top_fans_table.get_name(), e))
    raise e

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
    room_upper_right_widget_data_table_tuple = {key:None for key in room_upper_right_widget_data_table.get_tuple()}
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
        room_upper_right_widget_data_table.insert_record(room_upper_right_widget_data_table_tuple, on_duplicate='ignore')
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
    room_vs_role_table_tuple = {key:None for key in room_vs_role_table.get_tuple()}
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
      room_vs_role_table.insert_record(room_vs_role_table_tuple, on_duplicate='ignore')
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
    ## create the table if not exist
    ##
    if db.is_table_exist(picture_table.get_name()) is False:
      picture_table.create()
    ##
    ## +--------------+
    ## | Field        |
    ## +--------------+
    ## | start_time   |
    ## | platform     |
    ## | room_id      |
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
    picture_table_tuple = {key:None for key in picture_table.get_tuple()}

    ##
    ## <=========================== content_label ==================================>
    ##
    content_label         = get_dict_attr(data, "$.data.room.content_label")
    if content_label is not None:
      start_time    = get_dict_attr(data, "$.data.room.start_time")
      label         = "content_label"
      picture_index = 0
      avg_color     = get_dict_attr(content_label, "$.avg_color")
      height        = get_dict_attr(content_label, "$.height")
      image_type    = get_dict_attr(content_label, "$.image_type")
      is_animated   = get_dict_attr(content_label, "$.is_animated")
      open_web_url  = get_dict_attr(content_label, "$.open_web_url")
      uri           = get_dict_attr(content_label, "$.uri")
      width         = get_dict_attr(content_label, "$.width")

      set_dict_attr(picture_table_tuple, "$.start_time",    dat.fromtimestamp(start_time))
      set_dict_attr(picture_table_tuple, "$.platform",      DOUYIN_PLATFORM)
      set_dict_attr(picture_table_tuple, "$.room_id",       str(room_id))
      set_dict_attr(picture_table_tuple, "$.label",         label)
      set_dict_attr(picture_table_tuple, "$.avg_color",     avg_color)
      set_dict_attr(picture_table_tuple, "$.height",        height)
      set_dict_attr(picture_table_tuple, "$.image_type",    image_type)
      set_dict_attr(picture_table_tuple, "$.is_animated",   is_animated)
      set_dict_attr(picture_table_tuple, "$.open_web_url",  open_web_url)
      set_dict_attr(picture_table_tuple, "$.uri",           uri)
      set_dict_attr(picture_table_tuple, "$.width",         width)
      set_dict_attr(picture_table_tuple, "$.picture_index", picture_index)

      if uri is not None:
        picture_table.insert_record(picture_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== cover ==================================>
    ##
    cover         = get_dict_attr(data, "$.data.room.cover")
    start_time    = get_dict_attr(data, "$.data.room.start_time")
    label         = "cover"
    picture_index = 0
    avg_color     = get_dict_attr(cover, "$.avg_color")
    height        = get_dict_attr(cover, "$.height")
    image_type    = get_dict_attr(cover, "$.image_type")
    is_animated   = get_dict_attr(cover, "$.is_animated")
    open_web_url  = get_dict_attr(cover, "$.open_web_url")
    uri           = get_dict_attr(cover, "$.uri")
    width         = get_dict_attr(cover, "$.width")
    
    set_dict_attr(picture_table_tuple, "$.start_time",    dat.fromtimestamp(start_time))
    set_dict_attr(picture_table_tuple, "$.platform",      DOUYIN_PLATFORM)
    set_dict_attr(picture_table_tuple, "$.room_id",       str(room_id))
    set_dict_attr(picture_table_tuple, "$.label",         label)
    set_dict_attr(picture_table_tuple, "$.avg_color",     avg_color)
    set_dict_attr(picture_table_tuple, "$.height",        height)
    set_dict_attr(picture_table_tuple, "$.image_type",    image_type)
    set_dict_attr(picture_table_tuple, "$.is_animated",   is_animated)
    set_dict_attr(picture_table_tuple, "$.open_web_url",  open_web_url)
    set_dict_attr(picture_table_tuple, "$.uri",           uri)
    set_dict_attr(picture_table_tuple, "$.width",         width)
    set_dict_attr(picture_table_tuple, "$.picture_index", picture_index)
    
    if uri is not None:
      picture_table.insert_record(picture_table_tuple, on_duplicate='ignore')

    if deco_list is not None:
      for deco_index in range(0, len(deco_list)):
        ##
        ## <=========================== deco_list.[x].image ==================================>
        ##
        image         = get_dict_attr(deco_list[deco_index], "$.image")
        if image is not None:
          label         = "image" + str(deco_index)
          picture_index = 0
          avg_color     = get_dict_attr(image, "$.avg_color")
          height        = get_dict_attr(image, "$.height")
          image_type    = get_dict_attr(image, "$.image_type")
          is_animated   = get_dict_attr(image, "$.is_animated")
          open_web_url  = get_dict_attr(image, "$.open_web_url")
          uri           = get_dict_attr(image, "$.uri")
          width         = get_dict_attr(image, "$.width")

          set_dict_attr(picture_table_tuple, "$.start_time",    dat.fromtimestamp(start_time))
          set_dict_attr(picture_table_tuple, "$.platform",      DOUYIN_PLATFORM)
          set_dict_attr(picture_table_tuple, "$.room_id",       str(room_id))
          set_dict_attr(picture_table_tuple, "$.label",         label)
          set_dict_attr(picture_table_tuple, "$.avg_color",     avg_color)
          set_dict_attr(picture_table_tuple, "$.height",        height)
          set_dict_attr(picture_table_tuple, "$.image_type",    image_type)
          set_dict_attr(picture_table_tuple, "$.is_animated",   is_animated)
          set_dict_attr(picture_table_tuple, "$.open_web_url",  open_web_url)
          set_dict_attr(picture_table_tuple, "$.uri",           uri)
          set_dict_attr(picture_table_tuple, "$.width",         width)
          set_dict_attr(picture_table_tuple, "$.picture_index", picture_index)
          if uri is not None:
            picture_table.insert_record(picture_table_tuple, on_duplicate='ignore')

        ##
        ## <=========================== deco_list.[x].nine_patch_image ==================================>
        ##
        nine_patch_image = get_dict_attr(deco_list[deco_index], "$.nine_patch_image")
        if nine_patch_image is not None:
          label            = "nine_patch_image" + str(deco_index)
          picture_index    = 0
          avg_color        = get_dict_attr(nine_patch_image, "$.avg_color")
          height           = get_dict_attr(nine_patch_image, "$.height")
          image_type       = get_dict_attr(nine_patch_image, "$.image_type")
          is_animated      = get_dict_attr(nine_patch_image, "$.is_animated")
          open_web_url     = get_dict_attr(nine_patch_image, "$.open_web_url")
          uri              = get_dict_attr(nine_patch_image, "$.uri")
          width            = get_dict_attr(nine_patch_image, "$.width")

          set_dict_attr(picture_table_tuple, "$.start_time",    dat.fromtimestamp(start_time))
          set_dict_attr(picture_table_tuple, "$.platform",      DOUYIN_PLATFORM)
          set_dict_attr(picture_table_tuple, "$.room_id",       str(room_id))
          set_dict_attr(picture_table_tuple, "$.label",         label)
          set_dict_attr(picture_table_tuple, "$.avg_color",     avg_color)
          set_dict_attr(picture_table_tuple, "$.height",        height)
          set_dict_attr(picture_table_tuple, "$.image_type",    image_type)
          set_dict_attr(picture_table_tuple, "$.is_animated",   is_animated)
          set_dict_attr(picture_table_tuple, "$.open_web_url",  open_web_url)
          set_dict_attr(picture_table_tuple, "$.uri",           uri)
          set_dict_attr(picture_table_tuple, "$.width",         width)
          set_dict_attr(picture_table_tuple, "$.picture_index", picture_index)
          if uri is not None:
            picture_table.insert_record(picture_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== feed_room_label ==================================>
    ##
    feed_room_label  = get_dict_attr(data, "$.data.room.feed_room_label")
    label            = "feed_room_label"
    picture_index    = 0
    avg_color        = get_dict_attr(feed_room_label, "$.avg_color")
    height           = get_dict_attr(feed_room_label, "$.height")
    image_type       = get_dict_attr(feed_room_label, "$.image_type")
    is_animated      = get_dict_attr(feed_room_label, "$.is_animated")
    open_web_url     = get_dict_attr(feed_room_label, "$.open_web_url")
    uri              = get_dict_attr(feed_room_label, "$.uri")
    width            = get_dict_attr(feed_room_label, "$.width")
    
    set_dict_attr(picture_table_tuple, "$.start_time",    dat.fromtimestamp(start_time))
    set_dict_attr(picture_table_tuple, "$.platform",      DOUYIN_PLATFORM)
    set_dict_attr(picture_table_tuple, "$.room_id",       str(room_id))
    set_dict_attr(picture_table_tuple, "$.label",         label)
    set_dict_attr(picture_table_tuple, "$.avg_color",     avg_color)
    set_dict_attr(picture_table_tuple, "$.height",        height)
    set_dict_attr(picture_table_tuple, "$.image_type",    image_type)
    set_dict_attr(picture_table_tuple, "$.is_animated",   is_animated)
    set_dict_attr(picture_table_tuple, "$.open_web_url",  open_web_url)
    set_dict_attr(picture_table_tuple, "$.uri",           uri)
    set_dict_attr(picture_table_tuple, "$.width",         width)
    set_dict_attr(picture_table_tuple, "$.picture_index", picture_index)
    if uri is not None:
      picture_table.insert_record(picture_table_tuple, on_duplicate='ignore')
    
    ##
    ## <=========================== guide_button ==================================>
    ##
    guide_button     = get_dict_attr(data, "$.data.room.guide_button")
    label            = "guide_button"
    picture_index    = 0
    avg_color        = get_dict_attr(guide_button, "$.avg_color")
    height           = get_dict_attr(guide_button, "$.height")
    image_type       = get_dict_attr(guide_button, "$.image_type")
    is_animated      = get_dict_attr(guide_button, "$.is_animated")
    open_web_url     = get_dict_attr(guide_button, "$.open_web_url")
    uri              = get_dict_attr(guide_button, "$.uri")
    width            = get_dict_attr(guide_button, "$.width")
    
    set_dict_attr(picture_table_tuple, "$.start_time",    dat.fromtimestamp(start_time))
    set_dict_attr(picture_table_tuple, "$.platform",      DOUYIN_PLATFORM)
    set_dict_attr(picture_table_tuple, "$.room_id",       str(room_id))
    set_dict_attr(picture_table_tuple, "$.label",         label)
    set_dict_attr(picture_table_tuple, "$.avg_color",     avg_color)
    set_dict_attr(picture_table_tuple, "$.height",        height)
    set_dict_attr(picture_table_tuple, "$.image_type",    image_type)
    set_dict_attr(picture_table_tuple, "$.is_animated",   is_animated)
    set_dict_attr(picture_table_tuple, "$.open_web_url",  open_web_url)
    set_dict_attr(picture_table_tuple, "$.uri",           uri)
    set_dict_attr(picture_table_tuple, "$.width",         width)
    set_dict_attr(picture_table_tuple, "$.picture_index", picture_index)
    if uri is not None:
      picture_table.insert_record(picture_table_tuple, on_duplicate='ignore')
    
    if exist_authentication_info is True:
      ##
      ## <=========================== authentication_badge ==================================>
      ##
      authentication_badge = get_dict_attr(data, "$.data.room.owner.authentication_info.authentication_badge")
      label                = "authentication_badge"
      picture_index        = 0
      avg_color            = get_dict_attr(authentication_badge, "$.avg_color")
      height               = get_dict_attr(authentication_badge, "$.height")
      image_type           = get_dict_attr(authentication_badge, "$.image_type")
      is_animated          = get_dict_attr(authentication_badge, "$.is_animated")
      open_web_url         = get_dict_attr(authentication_badge, "$.open_web_url")
      uri                  = get_dict_attr(authentication_badge, "$.uri")
      width                = get_dict_attr(authentication_badge, "$.width")
      
      set_dict_attr(picture_table_tuple, "$.start_time",    dat.fromtimestamp(start_time))
      set_dict_attr(picture_table_tuple, "$.platform",      DOUYIN_PLATFORM)
      set_dict_attr(picture_table_tuple, "$.room_id",       str(room_id))
      set_dict_attr(picture_table_tuple, "$.label",         label)
      set_dict_attr(picture_table_tuple, "$.avg_color",     avg_color)
      set_dict_attr(picture_table_tuple, "$.height",        height)
      set_dict_attr(picture_table_tuple, "$.image_type",    image_type)
      set_dict_attr(picture_table_tuple, "$.is_animated",   is_animated)
      set_dict_attr(picture_table_tuple, "$.open_web_url",  open_web_url)
      set_dict_attr(picture_table_tuple, "$.uri",           uri)
      set_dict_attr(picture_table_tuple, "$.width",         width)
      set_dict_attr(picture_table_tuple, "$.picture_index", picture_index)
      if uri is not None:
        picture_table.insert_record(picture_table_tuple, on_duplicate='ignore')

      ##
      ## <=========================== authentication_badge_v2 ==================================>
      ##
      authentication_badge_v2 = get_dict_attr(data, "$.data.room.owner.authentication_info.authentication_badge_v2")
      if authentication_badge_v2:
        label                   = "authentication_badge_v2"
        picture_index           = 0
        avg_color               = get_dict_attr(authentication_badge_v2, "$.avg_color")
        height                  = get_dict_attr(authentication_badge_v2, "$.height")
        image_type              = get_dict_attr(authentication_badge_v2, "$.image_type")
        is_animated             = get_dict_attr(authentication_badge_v2, "$.is_animated")
        open_web_url            = get_dict_attr(authentication_badge_v2, "$.open_web_url")
        uri                     = get_dict_attr(authentication_badge_v2, "$.uri")
        width                   = get_dict_attr(authentication_badge_v2, "$.width")
        
        set_dict_attr(picture_table_tuple, "$.start_time",    dat.fromtimestamp(start_time))
        set_dict_attr(picture_table_tuple, "$.platform",      DOUYIN_PLATFORM)
        set_dict_attr(picture_table_tuple, "$.room_id",       str(room_id))
        set_dict_attr(picture_table_tuple, "$.label",         label)
        set_dict_attr(picture_table_tuple, "$.avg_color",     avg_color)
        set_dict_attr(picture_table_tuple, "$.height",        height)
        set_dict_attr(picture_table_tuple, "$.image_type",    image_type)
        set_dict_attr(picture_table_tuple, "$.is_animated",   is_animated)
        set_dict_attr(picture_table_tuple, "$.open_web_url",  open_web_url)
        set_dict_attr(picture_table_tuple, "$.uri",           uri)
        set_dict_attr(picture_table_tuple, "$.width",         width)
        set_dict_attr(picture_table_tuple, "$.picture_index", picture_index)
        if uri is not None:
          picture_table.insert_record(picture_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== avatar_large ==================================>
    ##
    avatar_large            = get_dict_attr(data, "$.data.room.owner.avatar_large")
    label                   = "avatar_large"
    picture_index           = 0
    avg_color               = get_dict_attr(avatar_large, "$.avg_color")
    height                  = get_dict_attr(avatar_large, "$.height")
    image_type              = get_dict_attr(avatar_large, "$.image_type")
    is_animated             = get_dict_attr(avatar_large, "$.is_animated")
    open_web_url            = get_dict_attr(avatar_large, "$.open_web_url")
    uri                     = get_dict_attr(avatar_large, "$.uri")
    width                   = get_dict_attr(avatar_large, "$.width")
    
    set_dict_attr(picture_table_tuple, "$.start_time",    dat.fromtimestamp(start_time))
    set_dict_attr(picture_table_tuple, "$.platform",      DOUYIN_PLATFORM)
    set_dict_attr(picture_table_tuple, "$.room_id",       str(room_id))
    set_dict_attr(picture_table_tuple, "$.label",         label)
    set_dict_attr(picture_table_tuple, "$.avg_color",     avg_color)
    set_dict_attr(picture_table_tuple, "$.height",        height)
    set_dict_attr(picture_table_tuple, "$.image_type",    image_type)
    set_dict_attr(picture_table_tuple, "$.is_animated",   is_animated)
    set_dict_attr(picture_table_tuple, "$.open_web_url",  open_web_url)
    set_dict_attr(picture_table_tuple, "$.uri",           uri)
    set_dict_attr(picture_table_tuple, "$.width",         width)
    set_dict_attr(picture_table_tuple, "$.picture_index", picture_index)
    if uri is not None:
      picture_table.insert_record(picture_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== avatar_medium ==================================>
    ##
    avatar_medium           = get_dict_attr(data, "$.data.room.owner.avatar_medium")
    label                   = "avatar_medium"
    picture_index           = 0
    avg_color               = get_dict_attr(avatar_medium, "$.avg_color")
    height                  = get_dict_attr(avatar_medium, "$.height")
    image_type              = get_dict_attr(avatar_medium, "$.image_type")
    is_animated             = get_dict_attr(avatar_medium, "$.is_animated")
    open_web_url            = get_dict_attr(avatar_medium, "$.open_web_url")
    uri                     = get_dict_attr(avatar_medium, "$.uri")
    width                   = get_dict_attr(avatar_medium, "$.width")
    
    set_dict_attr(picture_table_tuple, "$.start_time",    dat.fromtimestamp(start_time))
    set_dict_attr(picture_table_tuple, "$.platform",      DOUYIN_PLATFORM)
    set_dict_attr(picture_table_tuple, "$.room_id",       str(room_id))
    set_dict_attr(picture_table_tuple, "$.label",         label)
    set_dict_attr(picture_table_tuple, "$.avg_color",     avg_color)
    set_dict_attr(picture_table_tuple, "$.height",        height)
    set_dict_attr(picture_table_tuple, "$.image_type",    image_type)
    set_dict_attr(picture_table_tuple, "$.is_animated",   is_animated)
    set_dict_attr(picture_table_tuple, "$.open_web_url",  open_web_url)
    set_dict_attr(picture_table_tuple, "$.uri",           uri)
    set_dict_attr(picture_table_tuple, "$.width",         width)
    set_dict_attr(picture_table_tuple, "$.picture_index", picture_index)
    if uri is not None:
      picture_table.insert_record(picture_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== avatar_thumb ==================================>
    ##
    avatar_thumb            = get_dict_attr(data, "$.data.room.owner.avatar_thumb")
    label                   = "avatar_thumb"
    picture_index           = 0
    avg_color               = get_dict_attr(avatar_thumb, "$.avg_color")
    height                  = get_dict_attr(avatar_thumb, "$.height")
    image_type              = get_dict_attr(avatar_thumb, "$.image_type")
    is_animated             = get_dict_attr(avatar_thumb, "$.is_animated")
    open_web_url            = get_dict_attr(avatar_thumb, "$.open_web_url")
    uri                     = get_dict_attr(avatar_thumb, "$.uri")
    width                   = get_dict_attr(avatar_thumb, "$.width")
    
    set_dict_attr(picture_table_tuple, "$.start_time",    dat.fromtimestamp(start_time))
    set_dict_attr(picture_table_tuple, "$.platform",      DOUYIN_PLATFORM)
    set_dict_attr(picture_table_tuple, "$.room_id",       str(room_id))
    set_dict_attr(picture_table_tuple, "$.label",         label)
    set_dict_attr(picture_table_tuple, "$.avg_color",     avg_color)
    set_dict_attr(picture_table_tuple, "$.height",        height)
    set_dict_attr(picture_table_tuple, "$.image_type",    image_type)
    set_dict_attr(picture_table_tuple, "$.is_animated",   is_animated)
    set_dict_attr(picture_table_tuple, "$.open_web_url",  open_web_url)
    set_dict_attr(picture_table_tuple, "$.uri",           uri)
    set_dict_attr(picture_table_tuple, "$.width",         width)
    set_dict_attr(picture_table_tuple, "$.picture_index", picture_index)
    if uri is not None:
      picture_table.insert_record(picture_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== badge_image_list ==================================>
    ##
    badge_image_list = get_dict_attr(data, "$.data.room.owner.badge_image_list")
    if len(badge_image_list) != 0:
      # picture_index auto increment
      label        = "badge_image_list"
      for badge_image_index in range(0, len(badge_image_list)):
        picture_index = badge_image_index
        avg_color     = get_dict_attr(badge_image_list[badge_image_index], "$.avg_color")
        height        = get_dict_attr(badge_image_list[badge_image_index], "$.height")
        image_type    = get_dict_attr(badge_image_list[badge_image_index], "$.image_type")
        is_animated   = get_dict_attr(badge_image_list[badge_image_index], "$.is_animated")
        open_web_url  = get_dict_attr(badge_image_list[badge_image_index], "$.open_web_url")
        uri           = get_dict_attr(badge_image_list[badge_image_index], "$.uri")
        width         = get_dict_attr(badge_image_list[badge_image_index], "$.width")
        
        set_dict_attr(picture_table_tuple, "$.start_time",    dat.fromtimestamp(start_time))
        set_dict_attr(picture_table_tuple, "$.platform",      DOUYIN_PLATFORM)
        set_dict_attr(picture_table_tuple, "$.room_id",       str(room_id))
        set_dict_attr(picture_table_tuple, "$.label",         label)
        set_dict_attr(picture_table_tuple, "$.avg_color",     avg_color)
        set_dict_attr(picture_table_tuple, "$.height",        height)
        set_dict_attr(picture_table_tuple, "$.image_type",    image_type)
        set_dict_attr(picture_table_tuple, "$.is_animated",   is_animated)
        set_dict_attr(picture_table_tuple, "$.open_web_url",  open_web_url)
        set_dict_attr(picture_table_tuple, "$.uri",           uri)
        set_dict_attr(picture_table_tuple, "$.width",         width)
        set_dict_attr(picture_table_tuple, "$.picture_index", picture_index)
        if uri is not None:
          picture_table.insert_record(picture_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== badge_image_list_v2 ==================================>
    ##
    badge_image_list_v2 = get_dict_attr(data, "$.data.room.owner.badge_image_list_v2")
    if len(badge_image_list_v2) != 0:
      # picture_index auto increment
      label        = "badge_image_list_v2"
      for badge_image_index in range(0, len(badge_image_list_v2)):
        picture_index = badge_image_index
        avg_color     = get_dict_attr(badge_image_list_v2[badge_image_index], "$.avg_color")
        height        = get_dict_attr(badge_image_list_v2[badge_image_index], "$.height")
        image_type    = get_dict_attr(badge_image_list_v2[badge_image_index], "$.image_type")
        is_animated   = get_dict_attr(badge_image_list_v2[badge_image_index], "$.is_animated")
        open_web_url  = get_dict_attr(badge_image_list_v2[badge_image_index], "$.open_web_url")
        uri           = get_dict_attr(badge_image_list_v2[badge_image_index], "$.uri")
        width         = get_dict_attr(badge_image_list_v2[badge_image_index], "$.width")
        
        set_dict_attr(picture_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
        set_dict_attr(picture_table_tuple, "$.platform",     DOUYIN_PLATFORM)
        set_dict_attr(picture_table_tuple, "$.room_id",      str(room_id))
        set_dict_attr(picture_table_tuple, "$.label",        label)
        set_dict_attr(picture_table_tuple, "$.avg_color",    avg_color)
        set_dict_attr(picture_table_tuple, "$.height",       height)
        set_dict_attr(picture_table_tuple, "$.image_type",   image_type)
        set_dict_attr(picture_table_tuple, "$.is_animated",  is_animated)
        set_dict_attr(picture_table_tuple, "$.open_web_url", open_web_url)
        set_dict_attr(picture_table_tuple, "$.uri",          uri)
        set_dict_attr(picture_table_tuple, "$.width",        width)
        set_dict_attr(picture_table_tuple, "$.picture_index", picture_index)
        if uri is not None:
          picture_table.insert_record(picture_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== icons ==================================>
    ##
    icons = get_dict_attr(data, "$.data.room.owner.fans_club.data.badge.icons")
    if icons is not None:
      for icon_key, icon_value in dict(icons).items():
        label         = "icons" + icon_key
        picture_index = 0
        avg_color     = get_dict_attr(icon_value, "$.avg_color")
        height        = get_dict_attr(icon_value, "$.height")
        image_type    = get_dict_attr(icon_value, "$.image_type")
        is_animated   = get_dict_attr(icon_value, "$.is_animated")
        open_web_url  = get_dict_attr(icon_value, "$.open_web_url")
        uri           = get_dict_attr(icon_value, "$.uri")
        width         = get_dict_attr(icon_value, "$.width")

        set_dict_attr(picture_table_tuple, "$.start_time",    dat.fromtimestamp(start_time))
        set_dict_attr(picture_table_tuple, "$.platform",      DOUYIN_PLATFORM)
        set_dict_attr(picture_table_tuple, "$.room_id",       str(room_id))
        set_dict_attr(picture_table_tuple, "$.label",         label)
        set_dict_attr(picture_table_tuple, "$.avg_color",     avg_color)
        set_dict_attr(picture_table_tuple, "$.height",        height)
        set_dict_attr(picture_table_tuple, "$.image_type",    image_type)
        set_dict_attr(picture_table_tuple, "$.is_animated",   is_animated)
        set_dict_attr(picture_table_tuple, "$.open_web_url",  open_web_url)
        set_dict_attr(picture_table_tuple, "$.uri",           uri)
        set_dict_attr(picture_table_tuple, "$.width",         width)
        set_dict_attr(picture_table_tuple, "$.picture_index", picture_index)
        if uri is not None:
          picture_table.insert_record(picture_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== new_im_icon_with_level ==================================>
    ##
    new_im_icon_with_level = get_dict_attr(data, "$.data.room.owner.pay_grade.new_im_icon_with_level")
    if new_im_icon_with_level is not None:
      label         = "new_im_icon_with_level"
      picture_index = 0
      avg_color     = get_dict_attr(new_im_icon_with_level, "$.avg_color")
      height        = get_dict_attr(new_im_icon_with_level, "$.height")
      image_type    = get_dict_attr(new_im_icon_with_level, "$.image_type")
      is_animated   = get_dict_attr(new_im_icon_with_level, "$.is_animated")
      open_web_url  = get_dict_attr(new_im_icon_with_level, "$.open_web_url")
      uri           = get_dict_attr(new_im_icon_with_level, "$.uri")
      width         = get_dict_attr(new_im_icon_with_level, "$.width")
      
      set_dict_attr(picture_table_tuple, "$.start_time",    dat.fromtimestamp(start_time))
      set_dict_attr(picture_table_tuple, "$.platform",      DOUYIN_PLATFORM)
      set_dict_attr(picture_table_tuple, "$.room_id",       str(room_id))
      set_dict_attr(picture_table_tuple, "$.label",         label)
      set_dict_attr(picture_table_tuple, "$.avg_color",     avg_color)
      set_dict_attr(picture_table_tuple, "$.height",        height)
      set_dict_attr(picture_table_tuple, "$.image_type",    image_type)
      set_dict_attr(picture_table_tuple, "$.is_animated",   is_animated)
      set_dict_attr(picture_table_tuple, "$.open_web_url",  open_web_url)
      set_dict_attr(picture_table_tuple, "$.uri",           uri)
      set_dict_attr(picture_table_tuple, "$.width",         width)
      set_dict_attr(picture_table_tuple, "$.picture_index", picture_index)
      if uri is not None:
        picture_table.insert_record(picture_table_tuple, on_duplicate='ignore')
      
    ##
    ## <=========================== new_live_icon ==================================>
    ##
    new_live_icon = get_dict_attr(data, "$.data.room.owner.pay_grade.new_live_icon")
    if new_live_icon is not None:
      label         = "new_live_icon"
      picture_index = 0
      avg_color     = get_dict_attr(new_live_icon, "$.avg_color")
      height        = get_dict_attr(new_live_icon, "$.height")
      image_type    = get_dict_attr(new_live_icon, "$.image_type")
      is_animated   = get_dict_attr(new_live_icon, "$.is_animated")
      open_web_url  = get_dict_attr(new_live_icon, "$.open_web_url")
      uri           = get_dict_attr(new_live_icon, "$.uri")
      width         = get_dict_attr(new_live_icon, "$.width")

      set_dict_attr(picture_table_tuple, "$.start_time",    dat.fromtimestamp(start_time))
      set_dict_attr(picture_table_tuple, "$.platform",      DOUYIN_PLATFORM)
      set_dict_attr(picture_table_tuple, "$.room_id",       str(room_id))
      set_dict_attr(picture_table_tuple, "$.label",         label)
      set_dict_attr(picture_table_tuple, "$.avg_color",     avg_color)
      set_dict_attr(picture_table_tuple, "$.height",        height)
      set_dict_attr(picture_table_tuple, "$.image_type",    image_type)
      set_dict_attr(picture_table_tuple, "$.is_animated",   is_animated)
      set_dict_attr(picture_table_tuple, "$.open_web_url",  open_web_url)
      set_dict_attr(picture_table_tuple, "$.uri",           uri)
      set_dict_attr(picture_table_tuple, "$.width",         width)
      set_dict_attr(picture_table_tuple, "$.picture_index", picture_index)
      if uri is not None:
        picture_table.insert_record(picture_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(picture_table.get_name(), e))
    raise e  

  ##
  ## PictureFlexSettingTable
  ##
  picture_flex_setting_table = PictureFlexSettingTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(picture_flex_setting_table.get_name()) is False:
      picture_flex_setting_table.create()
    ##
    ## +--------------------+
    ## | start_time         |
    ## | platform           |
    ## | room_id            |
    ## | label              |
    ## | uri                |
    ## | flex_setting_index |
    ## | flex_setting       |
    ## +--------------------+
    ##
    picture_flex_setting_table_tuple = {key:None for key in picture_flex_setting_table.get_tuple()}
    
    start_time          = get_dict_attr(data, "$.data.room.start_time")
    ##
    ## <=========================== content_label ==================================>
    ##
    if content_label is not None:
      uri                 = get_dict_attr(data, "$.data.room.content_label.uri")
      label               = 'content_label'
      flex_setting_list   = get_dict_attr(data, "$.data.room.content_label.flex_setting_list")
      if len(flex_setting_list) != 0:
        set_dict_attr(picture_flex_setting_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
        set_dict_attr(picture_flex_setting_table_tuple, "$.platform",     DOUYIN_PLATFORM)
        set_dict_attr(picture_flex_setting_table_tuple, "$.room_id",      str(room_id))
        set_dict_attr(picture_flex_setting_table_tuple, "$.label",        label)
        set_dict_attr(picture_flex_setting_table_tuple, "$.uri",          uri)
        for flex_setting_index in range(0, len(flex_setting_list)):
          set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting_index", flex_setting_index)
          set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting",       flex_setting_list[flex_setting_index])
          picture_flex_setting_table.insert_record(picture_flex_setting_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== cover ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.cover.uri")
    label               = 'cover'
    flex_setting_list   = get_dict_attr(data, "$.data.room.cover.flex_setting_list")
    if len(flex_setting_list) != 0:
      set_dict_attr(picture_flex_setting_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
      set_dict_attr(picture_flex_setting_table_tuple, "$.platform",     DOUYIN_PLATFORM)
      set_dict_attr(picture_flex_setting_table_tuple, "$.room_id",      str(room_id))
      set_dict_attr(picture_flex_setting_table_tuple, "$.label",        label)
      set_dict_attr(picture_flex_setting_table_tuple, "$.uri",          uri)
      for flex_setting_index in range(0, len(flex_setting_list)):
        set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting_index", flex_setting_index)
        set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting",       flex_setting_list[flex_setting_index])
        picture_flex_setting_table.insert_record(picture_flex_setting_table_tuple, on_duplicate='ignore')
      
    ##
    ## <=========================== feed_room_label ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.feed_room_label.uri")
    label               = 'feed_room_label'
    flex_setting_list   = get_dict_attr(data, "$.data.room.feed_room_label.flex_setting_list")
    if len(flex_setting_list) != 0:
      set_dict_attr(picture_flex_setting_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
      set_dict_attr(picture_flex_setting_table_tuple, "$.platform",     DOUYIN_PLATFORM)
      set_dict_attr(picture_flex_setting_table_tuple, "$.room_id",      str(room_id))
      set_dict_attr(picture_flex_setting_table_tuple, "$.label",        label)
      set_dict_attr(picture_flex_setting_table_tuple, "$.uri",          uri)
      for flex_setting_index in range(0, len(flex_setting_list)):
        set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting_index", flex_setting_index)
        set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting",       flex_setting_list[flex_setting_index])
        picture_flex_setting_table.insert_record(picture_flex_setting_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== guide_button ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.guide_button.uri")
    label               = 'guide_button'
    flex_setting_list   = get_dict_attr(data, "$.data.room.guide_button.flex_setting_list")
    if len(flex_setting_list) != 0:
      set_dict_attr(picture_flex_setting_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
      set_dict_attr(picture_flex_setting_table_tuple, "$.platform",     DOUYIN_PLATFORM)
      set_dict_attr(picture_flex_setting_table_tuple, "$.room_id",      str(room_id))
      set_dict_attr(picture_flex_setting_table_tuple, "$.label",        label)
      set_dict_attr(picture_flex_setting_table_tuple, "$.uri",          uri)
      for flex_setting_index in range(0, len(flex_setting_list)):
        set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting_index", flex_setting_index)
        set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting",       flex_setting_list[flex_setting_index])
        picture_flex_setting_table.insert_record(picture_flex_setting_table_tuple, on_duplicate='ignore')

    if exist_authentication_info is True:
      ##
      ## <=========================== authentication_badge ==================================>
      ##
      uri                 = get_dict_attr(data, "$.data.room.owner.authentication_info.authentication_badge.uri")
      label               = 'authentication_badge'
      flex_setting_list   = get_dict_attr(data, "$.data.room.owner.authentication_info.authentication_badge.flex_setting_list")
      if len(flex_setting_list) != 0:
        set_dict_attr(picture_flex_setting_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
        set_dict_attr(picture_flex_setting_table_tuple, "$.platform",     DOUYIN_PLATFORM)
        set_dict_attr(picture_flex_setting_table_tuple, "$.room_id",      str(room_id))
        set_dict_attr(picture_flex_setting_table_tuple, "$.label",        label)
        set_dict_attr(picture_flex_setting_table_tuple, "$.uri",          uri)
        for flex_setting_index in range(0, len(flex_setting_list)):
          set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting_index", flex_setting_index)
          set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting",       flex_setting_list[flex_setting_index])
          picture_flex_setting_table.insert_record(picture_flex_setting_table_tuple, on_duplicate='ignore')

      ##
      ## <=========================== authentication_badge_v2 ==================================>
      ##
      authentication_badge_v2 = get_dict_attr(data, "$.data.room.owner.authentication_info.authentication_badge_v2")
      if authentication_badge_v2:
        uri                 = get_dict_attr(data, "$.data.room.owner.authentication_info.authentication_badge_v2.uri")
        label               = 'authentication_badge_v2'
        flex_setting_list   = get_dict_attr(data, "$.data.room.owner.authentication_info.authentication_badge_v2.flex_setting_list")
        if len(flex_setting_list) != 0:
          set_dict_attr(picture_flex_setting_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
          set_dict_attr(picture_flex_setting_table_tuple, "$.platform",     DOUYIN_PLATFORM)
          set_dict_attr(picture_flex_setting_table_tuple, "$.room_id",      str(room_id))
          set_dict_attr(picture_flex_setting_table_tuple, "$.label",        label)
          set_dict_attr(picture_flex_setting_table_tuple, "$.uri",          uri)
          for flex_setting_index in range(0, len(flex_setting_list)):
            set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting_index", flex_setting_index)
            set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting",       flex_setting_list[flex_setting_index])
            picture_flex_setting_table.insert_record(picture_flex_setting_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== avatar_large ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.owner.avatar_large.uri")
    label               = 'avatar_large'
    flex_setting_list   = get_dict_attr(data, "$.data.room.owner.avatar_large.flex_setting_list")
    if len(flex_setting_list) != 0:
      set_dict_attr(picture_flex_setting_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
      set_dict_attr(picture_flex_setting_table_tuple, "$.platform",     DOUYIN_PLATFORM)
      set_dict_attr(picture_flex_setting_table_tuple, "$.room_id",      str(room_id))
      set_dict_attr(picture_flex_setting_table_tuple, "$.label",        label)
      set_dict_attr(picture_flex_setting_table_tuple, "$.uri",          uri)
      for flex_setting_index in range(0, len(flex_setting_list)):
        set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting_index", flex_setting_index)
        set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting",       flex_setting_list[flex_setting_index])
        picture_flex_setting_table.insert_record(picture_flex_setting_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== avatar_medium ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.owner.avatar_medium.uri")
    label               = 'avatar_medium'
    flex_setting_list   = get_dict_attr(data, "$.data.room.owner.avatar_medium.flex_setting_list")
    if len(flex_setting_list) != 0:
      set_dict_attr(picture_flex_setting_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
      set_dict_attr(picture_flex_setting_table_tuple, "$.platform",     DOUYIN_PLATFORM)
      set_dict_attr(picture_flex_setting_table_tuple, "$.room_id",      str(room_id))
      set_dict_attr(picture_flex_setting_table_tuple, "$.label",        label)
      set_dict_attr(picture_flex_setting_table_tuple, "$.uri",          uri)
      for flex_setting_index in range(0, len(flex_setting_list)):
        set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting_index", flex_setting_index)
        set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting",       flex_setting_list[flex_setting_index])
        picture_flex_setting_table.insert_record(picture_flex_setting_table_tuple, on_duplicate='ignore')
        
    ##
    ## <=========================== avatar_thumb ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.owner.avatar_thumb.uri")
    label               = 'avatar_thumb'
    flex_setting_list   = get_dict_attr(data, "$.data.room.owner.avatar_thumb.flex_setting_list")
    if len(flex_setting_list) != 0:
      set_dict_attr(picture_flex_setting_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
      set_dict_attr(picture_flex_setting_table_tuple, "$.platform",     DOUYIN_PLATFORM)
      set_dict_attr(picture_flex_setting_table_tuple, "$.room_id",      str(room_id))
      set_dict_attr(picture_flex_setting_table_tuple, "$.label",        label)
      set_dict_attr(picture_flex_setting_table_tuple, "$.uri",          uri)
      for flex_setting_index in range(0, len(flex_setting_list)):
        set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting_index", flex_setting_index)
        set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting",       flex_setting_list[flex_setting_index])
        picture_flex_setting_table.insert_record(picture_flex_setting_table_tuple, on_duplicate='ignore')

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
      label               = 'badge_image_list'
      flex_setting_list   = get_dict_attr(badge_image, "$.flex_setting_list")
      if len(flex_setting_list) != 0:
        
        ##
        ## set for every record
        ##
        set_dict_attr(picture_flex_setting_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
        set_dict_attr(picture_flex_setting_table_tuple, "$.platform",     DOUYIN_PLATFORM)
        set_dict_attr(picture_flex_setting_table_tuple, "$.room_id",      str(room_id))
        set_dict_attr(picture_flex_setting_table_tuple, "$.label",        label)
        set_dict_attr(picture_flex_setting_table_tuple, "$.uri",          uri)
        for flex_setting_index in range(0, len(flex_setting_list)):
          set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting_index", flex_setting_index)
          set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting",       flex_setting_list[flex_setting_index])
          if uri is not None:
            picture_flex_setting_table.insert_record(picture_flex_setting_table_tuple, on_duplicate='ignore')

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
      label               = 'badge_image_list_v2'
      flex_setting_list   = get_dict_attr(badge_image, "$.flex_setting_list")
      if len(flex_setting_list) != 0:
        
        ##
        ## set for every record
        ##
        set_dict_attr(picture_flex_setting_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
        set_dict_attr(picture_flex_setting_table_tuple, "$.platform",     DOUYIN_PLATFORM)
        set_dict_attr(picture_flex_setting_table_tuple, "$.room_id",      str(room_id))
        set_dict_attr(picture_flex_setting_table_tuple, "$.label",        label)
        set_dict_attr(picture_flex_setting_table_tuple, "$.uri",          uri)
        for flex_setting_index in range(0, len(flex_setting_list)):
          set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting_index", flex_setting_index)
          set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting",       flex_setting_list[flex_setting_index])
          if uri is not None:
            picture_flex_setting_table.insert_record(picture_flex_setting_table_tuple, on_duplicate='ignore')

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
      label               = "icons" + icon_key
      uri                 = get_dict_attr(icon_value, "$.uri")
      flex_setting_list   = get_dict_attr(icon_value, "$.flex_setting_list")
      if len(flex_setting_list) != 0:
        
        ##
        ## set for every record
        ##
        set_dict_attr(picture_flex_setting_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
        set_dict_attr(picture_flex_setting_table_tuple, "$.platform",     DOUYIN_PLATFORM)
        set_dict_attr(picture_flex_setting_table_tuple, "$.room_id",      str(room_id))
        set_dict_attr(picture_flex_setting_table_tuple, "$.label",        label)
        set_dict_attr(picture_flex_setting_table_tuple, "$.uri",          uri)
        for flex_setting_index in range(0, len(flex_setting_list)):
          set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting_index", flex_setting_index)
          set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting",       flex_setting_list[flex_setting_index])
          if uri is not None:
            picture_flex_setting_table.insert_record(picture_flex_setting_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== new_im_icon_with_level ==================================>
    ##
    try:
      uri                 = get_dict_attr(data, "$.data.room.owner.pay_grade.new_im_icon_with_level.uri")
      label               = "new_im_icon_with_level"
      flex_setting_list   = get_dict_attr(data, "$.data.room.owner.pay_grade.new_im_icon_with_level.flex_setting_list")
      if len(flex_setting_list) != 0:
        set_dict_attr(picture_flex_setting_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
        set_dict_attr(picture_flex_setting_table_tuple, "$.platform",     DOUYIN_PLATFORM)
        set_dict_attr(picture_flex_setting_table_tuple, "$.room_id",      str(room_id))
        set_dict_attr(picture_flex_setting_table_tuple, "$.label",        label)
        set_dict_attr(picture_flex_setting_table_tuple, "$.uri",          uri)
        for flex_setting_index in range(0, len(flex_setting_list)):
          set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting_index", flex_setting_index)
          set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting",       flex_setting_list[flex_setting_index])
          if uri is not None:
            picture_flex_setting_table.insert_record(picture_flex_setting_table_tuple, on_duplicate='ignore')
    except AttributeError as e:
      get_logger().error(f"{e}")

    ##
    ## <=========================== new_live_icon ==================================>
    ##
    try:
      uri                 = get_dict_attr(data, "$.data.room.owner.pay_grade.new_live_icon.uri")
      label               = "new_live_icon"
      flex_setting_list   = get_dict_attr(data, "$.data.room.owner.pay_grade.new_live_icon.flex_setting_list")
      if len(flex_setting_list) != 0:
        set_dict_attr(picture_flex_setting_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
        set_dict_attr(picture_flex_setting_table_tuple, "$.platform",     DOUYIN_PLATFORM)
        set_dict_attr(picture_flex_setting_table_tuple, "$.room_id",      str(room_id))
        set_dict_attr(picture_flex_setting_table_tuple, "$.label",        label)
        set_dict_attr(picture_flex_setting_table_tuple, "$.uri",          uri)
        for flex_setting_index in range(0, len(flex_setting_list)):
          set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting_index", flex_setting_index)
          set_dict_attr(picture_flex_setting_table_tuple, "$.flex_setting",       flex_setting_list[flex_setting_index])
          if uri is not None:
            picture_flex_setting_table.insert_record(picture_flex_setting_table_tuple, on_duplicate='ignore')
    except AttributeError as e:
      get_logger().error(f"{e}")
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(picture_flex_setting_table.get_name(), e))
    raise e  

  ## 
  ## PictureTextSettingTable
  ##
  picture_text_setting_table = PictureTextSettingTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(picture_text_setting_table.get_name()) is False:
      picture_text_setting_table.create()
    ##
    ## +--------------------+
    ## | start_time         |
    ## | platform           |
    ## | room_id            |
    ## | label              |
    ## | uri                |
    ## | text_setting_index |
    ## | text_setting       |
    ## +--------------------+
    ##
    picture_text_setting_table_tuple = {key:None for key in picture_text_setting_table.get_tuple()}

    start_time          = get_dict_attr(data, "$.data.room.start_time")
    ##
    ## <=========================== content_label ==================================>
    ##
    if content_label is not None:
      uri                 = get_dict_attr(data, "$.data.room.content_label.uri")
      label               = "content_label"
      text_setting_list   = get_dict_attr(data, "$.data.room.content_label.text_setting_list")
      if len(text_setting_list) != 0:
        set_dict_attr(picture_text_setting_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
        set_dict_attr(picture_text_setting_table_tuple, "$.platform",     DOUYIN_PLATFORM)
        set_dict_attr(picture_text_setting_table_tuple, "$.room_id",      str(room_id))
        set_dict_attr(picture_text_setting_table_tuple, "$.label",        label)
        set_dict_attr(picture_text_setting_table_tuple, "$.uri",          uri)
        for text_setting_index in range(0, len(text_setting_list)):
          set_dict_attr(picture_text_setting_table_tuple, "$.text_setting_index",      text_setting_index)
          set_dict_attr(picture_text_setting_table_tuple, "$.text_setting",            text_setting_list[text_setting_index])
          if uri is not None:
            picture_text_setting_table.insert_record(picture_text_setting_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== cover ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.cover.uri")
    label               = "cover"
    text_setting_list   = get_dict_attr(data, "$.data.room.cover.text_setting_list")
    if len(text_setting_list) != 0:
      set_dict_attr(picture_text_setting_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
      set_dict_attr(picture_text_setting_table_tuple, "$.platform",     DOUYIN_PLATFORM)
      set_dict_attr(picture_text_setting_table_tuple, "$.room_id",      str(room_id))
      set_dict_attr(picture_text_setting_table_tuple, "$.label",        label)
      set_dict_attr(picture_text_setting_table_tuple, "$.uri",          uri)
      for text_setting_index in range(0, len(text_setting_list)):
        set_dict_attr(picture_text_setting_table_tuple, "$.text_setting_index",      text_setting_index)
        set_dict_attr(picture_text_setting_table_tuple, "$.text_setting",            text_setting_list[text_setting_index])
        if uri is not None:
          picture_text_setting_table.insert_record(picture_text_setting_table_tuple, on_duplicate='ignore')
    ##
    ## <=========================== feed_room_label ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.feed_room_label.uri")
    label               = "feed_room_label"
    text_setting_list   = get_dict_attr(data, "$.data.room.feed_room_label.text_setting_list")
    if len(text_setting_list) != 0:
      set_dict_attr(picture_text_setting_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
      set_dict_attr(picture_text_setting_table_tuple, "$.platform",     DOUYIN_PLATFORM)
      set_dict_attr(picture_text_setting_table_tuple, "$.room_id",      str(room_id))
      set_dict_attr(picture_text_setting_table_tuple, "$.label",        label)
      set_dict_attr(picture_text_setting_table_tuple, "$.uri",          uri)
      for text_setting_index in range(0, len(text_setting_list)):
        set_dict_attr(picture_text_setting_table_tuple, "$.text_setting_index",      text_setting_index)
        set_dict_attr(picture_text_setting_table_tuple, "$.text_setting",            text_setting_list[text_setting_index])
        if uri is not None:
          picture_text_setting_table.insert_record(picture_text_setting_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== guide_button ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.guide_button.uri")
    label               = "guide_button"
    text_setting_list   = get_dict_attr(data, "$.data.room.guide_button.text_setting_list")
    if len(text_setting_list) != 0:
      set_dict_attr(picture_text_setting_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
      set_dict_attr(picture_text_setting_table_tuple, "$.platform",     DOUYIN_PLATFORM)
      set_dict_attr(picture_text_setting_table_tuple, "$.room_id",      str(room_id))
      set_dict_attr(picture_text_setting_table_tuple, "$.label",        label)
      set_dict_attr(picture_text_setting_table_tuple, "$.uri",          uri)
      for text_setting_index in range(0, len(text_setting_list)):
        set_dict_attr(picture_text_setting_table_tuple, "$.text_setting_index",      text_setting_index)
        set_dict_attr(picture_text_setting_table_tuple, "$.text_setting",            text_setting_list[text_setting_index])
        if uri is not None:
          picture_text_setting_table.insert_record(picture_text_setting_table_tuple, on_duplicate='ignore')

    if exist_authentication_info is True:
      ##
      ## <=========================== authentication_badge ==================================>
      ##
      uri                 = get_dict_attr(data, "$.data.room.owner.authentication_info.authentication_badge.uri")
      label               = 'authentication_badge'
      text_setting_list   = get_dict_attr(data, "$.data.room.owner.authentication_info.authentication_badge.text_setting_list")
      if len(text_setting_list) != 0:
        set_dict_attr(picture_text_setting_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
        set_dict_attr(picture_text_setting_table_tuple, "$.platform",     DOUYIN_PLATFORM)
        set_dict_attr(picture_text_setting_table_tuple, "$.room_id",      str(room_id))
        set_dict_attr(picture_text_setting_table_tuple, "$.label",        label)
        set_dict_attr(picture_text_setting_table_tuple, "$.uri",          uri)
        for text_setting_index in range(0, len(text_setting_list)):
          set_dict_attr(picture_text_setting_table_tuple, "$.text_setting_index",      text_setting_index)
          set_dict_attr(picture_text_setting_table_tuple, "$.text_setting",            text_setting_list[text_setting_index])
          picture_flex_setting_table.insert_record(picture_text_setting_table_tuple, on_duplicate='ignore')

      ##
      ## <=========================== authentication_badge_v2 ==================================>
      ##
      authentication_badge_v2 = get_dict_attr(data, "$.data.room.owner.authentication_info.authentication_badge_v2")
      if authentication_badge_v2:
        uri                 = get_dict_attr(data, "$.data.room.owner.authentication_info.authentication_badge_v2.uri")
        label               = 'authentication_badge_v2'
        text_setting_list   = get_dict_attr(data, "$.data.room.owner.authentication_info.authentication_badge_v2.text_setting_list")
        if len(text_setting_list) != 0:
          set_dict_attr(picture_text_setting_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
          set_dict_attr(picture_text_setting_table_tuple, "$.platform",     DOUYIN_PLATFORM)
          set_dict_attr(picture_text_setting_table_tuple, "$.room_id",      str(room_id))
          set_dict_attr(picture_text_setting_table_tuple, "$.label",        label)
          set_dict_attr(picture_text_setting_table_tuple, "$.uri",          uri)
          for text_setting_index in range(0, len(text_setting_list)):
            set_dict_attr(picture_text_setting_table_tuple, "$.text_setting_index",      text_setting_index)
            set_dict_attr(picture_text_setting_table_tuple, "$.text_setting",            text_setting_list[text_setting_index])
            picture_flex_setting_table.insert_record(picture_text_setting_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== avatar_large ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.owner.avatar_large.uri")
    label               = "avatar_large"
    text_setting_list   = get_dict_attr(data, "$.data.room.owner.avatar_large.text_setting_list")
    if len(text_setting_list) != 0:
      set_dict_attr(picture_text_setting_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
      set_dict_attr(picture_text_setting_table_tuple, "$.platform",     DOUYIN_PLATFORM)
      set_dict_attr(picture_text_setting_table_tuple, "$.room_id",      str(room_id))
      set_dict_attr(picture_text_setting_table_tuple, "$.label",        label)
      set_dict_attr(picture_text_setting_table_tuple, "$.uri",          uri)
      for text_setting_index in range(0, len(text_setting_list)):
        set_dict_attr(picture_text_setting_table_tuple, "$.text_setting_index",      text_setting_index)
        set_dict_attr(picture_text_setting_table_tuple, "$.text_setting",            text_setting_list[text_setting_index])
        if uri is not None:
          picture_text_setting_table.insert_record(picture_text_setting_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== avatar_medium ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.owner.avatar_medium.uri")
    label               = "avatar_medium"
    text_setting_list   = get_dict_attr(data, "$.data.room.owner.avatar_medium.text_setting_list")
    if len(text_setting_list) != 0:
      set_dict_attr(picture_text_setting_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
      set_dict_attr(picture_text_setting_table_tuple, "$.platform",     DOUYIN_PLATFORM)
      set_dict_attr(picture_text_setting_table_tuple, "$.room_id",      str(room_id))
      set_dict_attr(picture_text_setting_table_tuple, "$.label",        label)
      set_dict_attr(picture_text_setting_table_tuple, "$.uri",          uri)
      for text_setting_index in range(0, len(text_setting_list)):
        set_dict_attr(picture_text_setting_table_tuple, "$.text_setting_index",      text_setting_index)
        set_dict_attr(picture_text_setting_table_tuple, "$.text_setting",            text_setting_list[text_setting_index])
        if uri is not None:
          picture_text_setting_table.insert_record(picture_text_setting_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== avatar_thumb ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.owner.avatar_thumb.uri")
    label               = "avatar_thumb"
    text_setting_list   = get_dict_attr(data, "$.data.room.owner.avatar_thumb.text_setting_list")
    if len(text_setting_list) != 0:
      set_dict_attr(picture_text_setting_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
      set_dict_attr(picture_text_setting_table_tuple, "$.platform",     DOUYIN_PLATFORM)
      set_dict_attr(picture_text_setting_table_tuple, "$.room_id",      str(room_id))
      set_dict_attr(picture_text_setting_table_tuple, "$.label",        label)
      set_dict_attr(picture_text_setting_table_tuple, "$.uri",          uri)
      for text_setting_index in range(0, len(text_setting_list)):
        set_dict_attr(picture_text_setting_table_tuple, "$.text_setting_index",      text_setting_index)
        set_dict_attr(picture_text_setting_table_tuple, "$.text_setting",            text_setting_list[text_setting_index])
        if uri is not None:
          picture_text_setting_table.insert_record(picture_text_setting_table_tuple, on_duplicate='ignore')

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
      label               = "badge_image_list"
      text_setting_list   = get_dict_attr(badge_image, "$.text_setting_list")
      if len(text_setting_list) != 0:
        
        ##
        ## set for every record
        ##
        set_dict_attr(picture_text_setting_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
        set_dict_attr(picture_text_setting_table_tuple, "$.platform",     DOUYIN_PLATFORM)
        set_dict_attr(picture_text_setting_table_tuple, "$.room_id",      str(room_id))
        set_dict_attr(picture_text_setting_table_tuple, "$.label",        label)
        set_dict_attr(picture_text_setting_table_tuple, "$.uri",    uri)
        for text_setting_index in range(0, len(text_setting_list)):
          set_dict_attr(picture_text_setting_table_tuple, "$.text_setting_index",      text_setting_index)
          set_dict_attr(picture_text_setting_table_tuple, "$.text_setting",            text_setting_list[text_setting_index])
          if uri is not None:
            picture_text_setting_table.insert_record(picture_text_setting_table_tuple, on_duplicate='ignore')

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
      label               = "badge_image_list_v2"
      text_setting_list   = get_dict_attr(badge_image, "$.text_setting_list")
      if len(text_setting_list) != 0:
        
        ##
        ## set for every record
        ##
        set_dict_attr(picture_text_setting_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
        set_dict_attr(picture_text_setting_table_tuple, "$.platform",     DOUYIN_PLATFORM)
        set_dict_attr(picture_text_setting_table_tuple, "$.room_id",      str(room_id))
        set_dict_attr(picture_text_setting_table_tuple, "$.label",        label)
        set_dict_attr(picture_text_setting_table_tuple, "$.uri",          uri)
        for text_setting_index in range(0, len(text_setting_list)):
          set_dict_attr(picture_text_setting_table_tuple, "$.text_setting_index",      text_setting_index)
          set_dict_attr(picture_text_setting_table_tuple, "$.text_setting",            text_setting_list[text_setting_index])
          if uri is not None:
            picture_text_setting_table.insert_record(picture_text_setting_table_tuple, on_duplicate='ignore')

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
      label               = "icons" + icon_key
      uri                 = get_dict_attr(icon_value, "$.uri")
      text_setting_list   = get_dict_attr(icon_value, "$.text_setting_list")
      if len(text_setting_list) != 0:
        
        ##
        ## set for every record
        ##
        set_dict_attr(picture_text_setting_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
        set_dict_attr(picture_text_setting_table_tuple, "$.platform",     DOUYIN_PLATFORM)
        set_dict_attr(picture_text_setting_table_tuple, "$.room_id",      str(room_id))
        set_dict_attr(picture_text_setting_table_tuple, "$.label",        label)
        set_dict_attr(picture_text_setting_table_tuple, "$.uri",          uri)
        for text_setting_index in range(0, len(text_setting_list)):
          set_dict_attr(picture_text_setting_table_tuple, "$.text_setting_index",      text_setting_index)
          set_dict_attr(picture_text_setting_table_tuple, "$.text_setting",            text_setting_list[text_setting_index])
          if uri is not None:
            picture_text_setting_table.insert_record(picture_text_setting_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== new_im_icon_with_level ==================================>
    ##
    try:
      uri                 = get_dict_attr(data, "$.data.room.owner.pay_grade.new_im_icon_with_level.uri")
      label               = "new_im_icon_with_level"
      text_setting_list   = get_dict_attr(data, "$.data.room.owner.pay_grade.new_im_icon_with_level.text_setting_list")
      if len(text_setting_list) != 0:
        set_dict_attr(picture_text_setting_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
        set_dict_attr(picture_text_setting_table_tuple, "$.platform",     DOUYIN_PLATFORM)
        set_dict_attr(picture_text_setting_table_tuple, "$.room_id",      str(room_id))
        set_dict_attr(picture_text_setting_table_tuple, "$.label",        label)
        set_dict_attr(picture_text_setting_table_tuple, "$.uri",          uri)
        for text_setting_index in range(0, len(text_setting_list)):
          set_dict_attr(picture_text_setting_table_tuple, "$.text_setting_index",      text_setting_index)
          set_dict_attr(picture_text_setting_table_tuple, "$.text_setting",            text_setting_list[text_setting_index])
          if uri is not None:
            picture_text_setting_table.insert_record(picture_text_setting_table_tuple, on_duplicate='ignore')
    except AttributeError as e:
      get_logger().error(f"{e}")

    ##
    ## <=========================== new_live_icon ==================================>
    ##
    try:
      uri                 = get_dict_attr(data, "$.data.room.owner.pay_grade.new_live_icon.uri")
      label               = "new_live_icon"
      text_setting_list   = get_dict_attr(data, "$.data.room.owner.pay_grade.new_live_icon.text_setting_list")
      if len(text_setting_list) != 0:
        set_dict_attr(picture_text_setting_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
        set_dict_attr(picture_text_setting_table_tuple, "$.platform",     DOUYIN_PLATFORM)
        set_dict_attr(picture_text_setting_table_tuple, "$.room_id",      str(room_id))
        set_dict_attr(picture_text_setting_table_tuple, "$.label",        label)
        set_dict_attr(picture_text_setting_table_tuple, "$.uri",          uri)
        for text_setting_index in range(0, len(text_setting_list)):
          set_dict_attr(picture_text_setting_table_tuple, "$.text_setting_index",      text_setting_index)
          set_dict_attr(picture_text_setting_table_tuple, "$.text_setting",            text_setting_list[text_setting_index])
          if uri is not None:
            picture_text_setting_table.insert_record(picture_text_setting_table_tuple, on_duplicate='ignore')
    except AttributeError as e:
      get_logger().error(f"{e}")
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(picture_text_setting_table.get_name(), e))
    raise e

  ##
  ## PictureUrlTable
  ##
  picture_url_table = PictureUrlTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(picture_url_table.get_name()) is False:
      picture_url_table.create()
    ##
    ## +-------------+
    ## | start_time  |
    ## | platform    |
    ## | room_id     |
    ## | uri         |
    ## | url_index   |
    ## | url         |
    ## +-------------+
    ##
    picture_url_table_tuple = {key:None for key in picture_url_table.get_tuple()}

    start_time          = get_dict_attr(data, "$.data.room.start_time")
    ##
    ## <=========================== content_label ==================================>
    ##
    if content_label is not None:
      uri                 = get_dict_attr(data, "$.data.room.content_label.uri")
      label               = "content_label"
      url_list            = get_dict_attr(data, "$.data.room.content_label.url_list")
      if len(url_list) != 0:
        set_dict_attr(picture_url_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
        set_dict_attr(picture_url_table_tuple, "$.platform",     DOUYIN_PLATFORM)
        set_dict_attr(picture_url_table_tuple, "$.room_id",      str(room_id))
        set_dict_attr(picture_url_table_tuple, "$.label",        label)
        set_dict_attr(picture_url_table_tuple, "$.uri_index",    0)
        set_dict_attr(picture_url_table_tuple, "$.uri",          uri)
        for url_index in range(0, len(url_list)):
          set_dict_attr(picture_url_table_tuple, "$.url_index",  url_index)
          set_dict_attr(picture_url_table_tuple, "$.url",        url_list[url_index])
          if uri is not None:
            picture_url_table.insert_record(picture_url_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== cover ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.cover.uri")
    label               = "cover"
    url_list            = get_dict_attr(data, "$.data.room.cover.url_list")
    if len(url_list) != 0:
      set_dict_attr(picture_url_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
      set_dict_attr(picture_url_table_tuple, "$.platform",     DOUYIN_PLATFORM)
      set_dict_attr(picture_url_table_tuple, "$.room_id",      str(room_id))
      set_dict_attr(picture_url_table_tuple, "$.label",        label)
      set_dict_attr(picture_url_table_tuple, "$.uri_index",    0)
      set_dict_attr(picture_url_table_tuple, "$.uri",          uri)
      for url_index in range(0, len(url_list)):
        set_dict_attr(picture_url_table_tuple, "$.url_index",  url_index)
        set_dict_attr(picture_url_table_tuple, "$.url",        url_list[url_index])
        if uri is not None:
          picture_url_table.insert_record(picture_url_table_tuple, on_duplicate='ignore')

    if deco_list is not None:
      for deco_index in range(0, len(deco_list)):
        ##
        ## <=========================== deco_list.image ==================================>
        ##
        if get_dict_attr(deco_list[deco_index], "$.image") is not None:
          uri                 = get_dict_attr(deco_list[deco_index], "$.image.uri")
          label               = "image" + str(deco_index)
          url_list            = get_dict_attr(deco_list[deco_index], "$.image.url_list")
          if len(url_list) != 0:
            set_dict_attr(picture_url_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
            set_dict_attr(picture_url_table_tuple, "$.platform",     DOUYIN_PLATFORM)
            set_dict_attr(picture_url_table_tuple, "$.room_id",      str(room_id))
            set_dict_attr(picture_url_table_tuple, "$.label",        label)
            set_dict_attr(picture_url_table_tuple, "$.uri_index",    0)
            set_dict_attr(picture_url_table_tuple, "$.uri",          uri)
            for url_index in range(0, len(url_list)):
              set_dict_attr(picture_url_table_tuple, "$.url_index",  url_index)
              set_dict_attr(picture_url_table_tuple, "$.url",        url_list[url_index])
              if uri is not None:
                picture_url_table.insert_record(picture_url_table_tuple, on_duplicate='ignore')

        ##
        ## <=========================== deco_list.nine_patch_image ==================================>
        ##
        if get_dict_attr(deco_list[deco_index], "$.nine_patch_image") is not None:
          uri                 = get_dict_attr(deco_list[deco_index], "$.nine_patch_image.uri")
          label               = "nine_patch_image" + str(deco_index)
          url_list            = get_dict_attr(deco_list[deco_index], "$.nine_patch_image.url_list")
          if len(url_list) != 0:
            set_dict_attr(picture_url_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
            set_dict_attr(picture_url_table_tuple, "$.platform",     DOUYIN_PLATFORM)
            set_dict_attr(picture_url_table_tuple, "$.room_id",      str(room_id))
            set_dict_attr(picture_url_table_tuple, "$.label",        label)
            set_dict_attr(picture_url_table_tuple, "$.uri_index",    0)
            set_dict_attr(picture_url_table_tuple, "$.uri",          uri)
            for url_index in range(0, len(url_list)):
              set_dict_attr(picture_url_table_tuple, "$.url_index",  url_index)
              set_dict_attr(picture_url_table_tuple, "$.url",        url_list[url_index])
              if uri is not None:
                picture_url_table.insert_record(picture_url_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== feed_room_label ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.feed_room_label.uri")
    label               = "feed_room_label"
    url_list            = get_dict_attr(data, "$.data.room.feed_room_label.url_list")
    if len(url_list) != 0:
      set_dict_attr(picture_url_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
      set_dict_attr(picture_url_table_tuple, "$.platform",     DOUYIN_PLATFORM)
      set_dict_attr(picture_url_table_tuple, "$.room_id",      str(room_id))
      set_dict_attr(picture_url_table_tuple, "$.label",        label)
      set_dict_attr(picture_url_table_tuple, "$.uri_index",    0)
      set_dict_attr(picture_url_table_tuple, "$.uri",          uri)
      for url_index in range(0, len(url_list)):
        set_dict_attr(picture_url_table_tuple, "$.url_index",  url_index)
        set_dict_attr(picture_url_table_tuple, "$.url",        url_list[url_index])
        if uri is not None:
          picture_url_table.insert_record(picture_url_table_tuple, on_duplicate='ignore')
    ##
    ## <=========================== guide_button ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.guide_button.uri")
    label               = "guide_button"
    url_list   = get_dict_attr(data, "$.data.room.guide_button.url_list")
    if len(url_list) != 0:
      set_dict_attr(picture_url_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
      set_dict_attr(picture_url_table_tuple, "$.platform",     DOUYIN_PLATFORM)
      set_dict_attr(picture_url_table_tuple, "$.room_id",      str(room_id))
      set_dict_attr(picture_url_table_tuple, "$.label",        label)
      set_dict_attr(picture_url_table_tuple, "$.uri_index",    0)
      set_dict_attr(picture_url_table_tuple, "$.uri",          uri)
      for url_index in range(0, len(url_list)):
        set_dict_attr(picture_url_table_tuple, "$.url_index",  url_index)
        set_dict_attr(picture_url_table_tuple, "$.url",        url_list[url_index])
        if uri is not None:
          picture_url_table.insert_record(picture_url_table_tuple, on_duplicate='ignore')

    if exist_authentication_info is True:
      ##
      ## <=========================== authentication_badge ==================================>
      ##
      uri                 = get_dict_attr(data, "$.data.room.owner.authentication_info.authentication_badge.uri")
      label               = "authentication_badge"
      url_list   = get_dict_attr(data, "$.data.room.owner.authentication_info.authentication_badge.url_list")
      if len(url_list) != 0:
        set_dict_attr(picture_url_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
        set_dict_attr(picture_url_table_tuple, "$.platform",     DOUYIN_PLATFORM)
        set_dict_attr(picture_url_table_tuple, "$.room_id",      str(room_id))
        set_dict_attr(picture_url_table_tuple, "$.label",        label)
        set_dict_attr(picture_url_table_tuple, "$.uri_index",    0)
        set_dict_attr(picture_url_table_tuple, "$.uri",          uri)
        for url_index in range(0, len(url_list)):
          set_dict_attr(picture_url_table_tuple, "$.url_index",  url_index)
          set_dict_attr(picture_url_table_tuple, "$.url",        url_list[url_index])
          if uri is not None:
            picture_url_table.insert_record(picture_url_table_tuple, on_duplicate='ignore')

      ##
      ## <=========================== authentication_badge_v2 ==================================>
      ##
      authentication_badge_v2 = get_dict_attr(data, "$.data.room.owner.authentication_info.authentication_badge_v2")
      if authentication_badge_v2:
        uri                 = get_dict_attr(data, "$.data.room.owner.authentication_info.authentication_badge_v2.uri")
        label               = "authentication_badge_v2"
        url_list   = get_dict_attr(data, "$.data.room.owner.authentication_info.authentication_badge_v2.url_list")
        if len(url_list) != 0:
          set_dict_attr(picture_url_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
          set_dict_attr(picture_url_table_tuple, "$.platform",     DOUYIN_PLATFORM)
          set_dict_attr(picture_url_table_tuple, "$.room_id",      str(room_id))
          set_dict_attr(picture_url_table_tuple, "$.label",        label)
          set_dict_attr(picture_url_table_tuple, "$.uri_index",    0)
          set_dict_attr(picture_url_table_tuple, "$.uri",          uri)
          for url_index in range(0, len(url_list)):
            set_dict_attr(picture_url_table_tuple, "$.url_index",  url_index)
            set_dict_attr(picture_url_table_tuple, "$.url",        url_list[url_index])
            if uri is not None:
              picture_url_table.insert_record(picture_url_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== avatar_large ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.owner.avatar_large.uri")
    label               = "avatar_large"
    url_list   = get_dict_attr(data, "$.data.room.owner.avatar_large.url_list")
    if len(url_list) != 0:
      set_dict_attr(picture_url_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
      set_dict_attr(picture_url_table_tuple, "$.platform",     DOUYIN_PLATFORM)
      set_dict_attr(picture_url_table_tuple, "$.room_id",      str(room_id))
      set_dict_attr(picture_url_table_tuple, "$.label",        label)
      set_dict_attr(picture_url_table_tuple, "$.uri_index",    0)
      set_dict_attr(picture_url_table_tuple, "$.uri",          uri)
      for url_index in range(0, len(url_list)):
        set_dict_attr(picture_url_table_tuple, "$.url_index",  url_index)
        set_dict_attr(picture_url_table_tuple, "$.url",        url_list[url_index])
        if uri is not None:
          picture_url_table.insert_record(picture_url_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== avatar_medium ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.owner.avatar_medium.uri")
    label               = "avatar_medium"
    url_list   = get_dict_attr(data, "$.data.room.owner.avatar_medium.url_list")
    if len(url_list) != 0:
      set_dict_attr(picture_url_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
      set_dict_attr(picture_url_table_tuple, "$.platform",     DOUYIN_PLATFORM)
      set_dict_attr(picture_url_table_tuple, "$.room_id",      str(room_id))
      set_dict_attr(picture_url_table_tuple, "$.label",        label)
      set_dict_attr(picture_url_table_tuple, "$.uri_index",    0)
      set_dict_attr(picture_url_table_tuple, "$.uri",          uri)
      for url_index in range(0, len(url_list)):
        set_dict_attr(picture_url_table_tuple, "$.url_index",  url_index)
        set_dict_attr(picture_url_table_tuple, "$.url",        url_list[url_index])
        if uri is not None:
          picture_url_table.insert_record(picture_url_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== avatar_thumb ==================================>
    ##
    uri                 = get_dict_attr(data, "$.data.room.owner.avatar_thumb.uri")
    label               = "avatar_thumb"
    url_list            = get_dict_attr(data, "$.data.room.owner.avatar_thumb.url_list")
    if len(url_list) != 0:
      set_dict_attr(picture_url_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
      set_dict_attr(picture_url_table_tuple, "$.platform",     DOUYIN_PLATFORM)
      set_dict_attr(picture_url_table_tuple, "$.room_id",      str(room_id))
      set_dict_attr(picture_url_table_tuple, "$.label",        label)
      set_dict_attr(picture_url_table_tuple, "$.uri_index",    0)
      set_dict_attr(picture_url_table_tuple, "$.uri",          uri)
      for url_index in range(0, len(url_list)):
        set_dict_attr(picture_url_table_tuple, "$.url_index",  url_index)
        set_dict_attr(picture_url_table_tuple, "$.url",        url_list[url_index])
        if uri is not None:
          picture_url_table.insert_record(picture_url_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== badge_image_list ==================================>
    ##
    badge_image_list    = get_dict_attr(data, "$.data.room.owner.badge_image_list")
    
    ##
    ## loop badge image list
    ##
    for badge_image_index in range(0, len(badge_image_list)):
      
      ##
      ## loop text setting list
      ##
      uri                 = get_dict_attr(badge_image_list[badge_image_index], "$.uri")
      label               = "badge_image_list"
      url_list            = get_dict_attr(badge_image_list[badge_image_index], "$.url_list")
      if len(url_list) != 0:
        
        ##
        ## set for every record
        ##
        set_dict_attr(picture_url_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
        set_dict_attr(picture_url_table_tuple, "$.platform",     DOUYIN_PLATFORM)
        set_dict_attr(picture_url_table_tuple, "$.room_id",      str(room_id))
        set_dict_attr(picture_url_table_tuple, "$.label",        label)
        set_dict_attr(picture_url_table_tuple, "$.uri_index",    badge_image_index)
        set_dict_attr(picture_url_table_tuple, "$.uri",          uri)
        for url_index in range(0, len(url_list)):
          set_dict_attr(picture_url_table_tuple, "$.url_index",  url_index)
          set_dict_attr(picture_url_table_tuple, "$.url",        url_list[url_index])
          if uri is not None:
            picture_url_table.insert_record(picture_url_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== badge_image_list_v2 ==================================>
    ##
    badge_image_list_v2    = get_dict_attr(data, "$.data.room.owner.badge_image_list_v2")
    
    ##
    ## loop badge image list
    ##
    for badge_image_index in range(0, len(badge_image_list_v2)):      
      ##
      ## loop text setting list
      ##
      uri                 = get_dict_attr(badge_image_list_v2[badge_image_index], "$.uri")
      label               = "badge_image_list_v2"
      url_list            = get_dict_attr(badge_image_list_v2[badge_image_index], "$.url_list")
      if len(url_list) != 0:        
        ##
        ## set for every record
        ##
        set_dict_attr(picture_url_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
        set_dict_attr(picture_url_table_tuple, "$.platform",     DOUYIN_PLATFORM)
        set_dict_attr(picture_url_table_tuple, "$.room_id",      str(room_id))
        set_dict_attr(picture_url_table_tuple, "$.label",        label)
        set_dict_attr(picture_url_table_tuple, "$.uri_index",    badge_image_index)
        set_dict_attr(picture_url_table_tuple, "$.uri",          uri)
        for url_index in range(0, len(url_list)):
          set_dict_attr(picture_url_table_tuple, "$.url_index",  url_index)
          set_dict_attr(picture_url_table_tuple, "$.url",        url_list[url_index])
          if uri is not None:
            picture_url_table.insert_record(picture_url_table_tuple, on_duplicate='ignore')

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
      label               = "icons" + icon_key
      uri                 = get_dict_attr(icon_value, "$.uri")
      url_list   = get_dict_attr(icon_value, "$.url_list")
      if len(url_list) != 0:
        
        ##
        ## set for every record
        ##
        set_dict_attr(picture_url_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
        set_dict_attr(picture_url_table_tuple, "$.platform",     DOUYIN_PLATFORM)
        set_dict_attr(picture_url_table_tuple, "$.room_id",      str(room_id))
        set_dict_attr(picture_url_table_tuple, "$.label",        label)
        set_dict_attr(picture_url_table_tuple, "$.uri_index",    0)
        set_dict_attr(picture_url_table_tuple, "$.uri",          uri)
        for url_index in range(0, len(url_list)):
          set_dict_attr(picture_url_table_tuple, "$.url_index",  url_index)
          set_dict_attr(picture_url_table_tuple, "$.url",        url_list[url_index])
          if uri is not None:
            picture_url_table.insert_record(picture_url_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== new_im_icon_with_level ==================================>
    ##
    try:
      uri                 = get_dict_attr(data, "$.data.room.owner.pay_grade.new_im_icon_with_level.uri")
      label               = "new_im_icon_with_level"
      url_list            = get_dict_attr(data, "$.data.room.owner.pay_grade.new_im_icon_with_level.url_list")
      if len(url_list) != 0:
        set_dict_attr(picture_url_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
        set_dict_attr(picture_url_table_tuple, "$.platform",     DOUYIN_PLATFORM)
        set_dict_attr(picture_url_table_tuple, "$.room_id",      str(room_id))
        set_dict_attr(picture_url_table_tuple, "$.label",        label)
        set_dict_attr(picture_url_table_tuple, "$.uri_index",    0)
        set_dict_attr(picture_url_table_tuple, "$.uri",          uri)
        for url_index in range(0, len(url_list)):
          set_dict_attr(picture_url_table_tuple, "$.url_index",  url_index)
          set_dict_attr(picture_url_table_tuple, "$.url",        url_list[url_index])
          if uri is not None:
            picture_url_table.insert_record(picture_url_table_tuple, on_duplicate='ignore')
    except AttributeError as e:
      get_logger().error(f"{e}")

    ##
    ## <=========================== new_live_icon ==================================>
    ##
    try:
      uri                 = get_dict_attr(data, "$.data.room.owner.pay_grade.new_live_icon.uri")
      label               = "new_live_icon"
      url_list            = get_dict_attr(data, "$.data.room.owner.pay_grade.new_live_icon.url_list")
      if len(url_list) != 0:
        set_dict_attr(picture_url_table_tuple, "$.start_time",   dat.fromtimestamp(start_time))
        set_dict_attr(picture_url_table_tuple, "$.platform",     DOUYIN_PLATFORM)
        set_dict_attr(picture_url_table_tuple, "$.room_id",      str(room_id))
        set_dict_attr(picture_url_table_tuple, "$.label",        label)
        set_dict_attr(picture_url_table_tuple, "$.uri_index",    0)
        set_dict_attr(picture_url_table_tuple, "$.uri",          uri)
        for url_index in range(0, len(url_list)):
          set_dict_attr(picture_url_table_tuple, "$.url_index",  url_index)
          set_dict_attr(picture_url_table_tuple, "$.url",        url_list[url_index])
          if uri is not None:
            picture_url_table.insert_record(picture_url_table_tuple, on_duplicate='ignore')
    except AttributeError as e:
      get_logger().error(f"{e}")
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(picture_url_table.get_name(), e))
    raise e

  ##
  ## PictureContentTable
  ##
  picture_content_table = PictureContentTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(picture_content_table.get_name()) is False:
      picture_content_table.create()
    ##
    ## +------------------+
    ## | start_time       |
    ## | platform         |
    ## | room_id          |
    ## | uri_index        |
    ## | label            |
    ## | uri              |
    ## | alternative_text |
    ## | font_color       |
    ## | level            |
    ## | name             |
    ## +------------------+
    ##
    picture_content_table_tuple = {key:None for key in picture_content_table.get_tuple()}

    start_time          = get_dict_attr(data, "$.data.room.start_time")
    ##
    ## <=========================== content_label ==================================>
    ##
    if content_label is not None:
      label               = "content_label"
      uri                 = get_dict_attr(data, "$.data.room.content_label.uri")
      alternative_text    = get_dict_attr(data, "$.data.room.content_label.content.alternative_text")
      font_color          = get_dict_attr(data, "$.data.room.content_label.content.font_color")
      level               = get_dict_attr(data, "$.data.room.content_label.content.level")
      name                = get_dict_attr(data, "$.data.room.content_label.content.name")

      # uri_index auto increment
      set_dict_attr(picture_content_table_tuple, "$.start_time",          dat.fromtimestamp(start_time))
      set_dict_attr(picture_content_table_tuple, "$.platform",            DOUYIN_PLATFORM)
      set_dict_attr(picture_content_table_tuple, "$.room_id",             str(room_id))
      set_dict_attr(picture_content_table_tuple, "$.label",               label)
      set_dict_attr(picture_content_table_tuple, "$.uri",                 uri)
      set_dict_attr(picture_content_table_tuple, "$.alternative_text",    alternative_text)
      set_dict_attr(picture_content_table_tuple, "$.font_color",          font_color)
      set_dict_attr(picture_content_table_tuple, "$.level",               level)
      set_dict_attr(picture_content_table_tuple, "$.name",                name)

      if uri is not None:
        picture_content_table.insert_record(picture_content_table_tuple, on_duplicate='ignore')

    ##
    ## <=========================== feed_room_label ==================================>
    ##
    # uri_index auto increment
    label               = "feed_room_label"
    uri                 = get_dict_attr(data, "$.data.room.feed_room_label.uri")
    alternative_text    = get_dict_attr(data, "$.data.room.feed_room_label.content.alternative_text")
    font_color          = get_dict_attr(data, "$.data.room.feed_room_label.content.font_color")
    level               = get_dict_attr(data, "$.data.room.feed_room_label.content.level")
    name                = get_dict_attr(data, "$.data.room.feed_room_label.content.name")

    # uri_index auto increment
    set_dict_attr(picture_content_table_tuple, "$.start_time",          dat.fromtimestamp(start_time))
    set_dict_attr(picture_content_table_tuple, "$.platform",            DOUYIN_PLATFORM)
    set_dict_attr(picture_content_table_tuple, "$.room_id",             str(room_id))
    set_dict_attr(picture_content_table_tuple, "$.label",               label)
    set_dict_attr(picture_content_table_tuple, "$.uri",                 uri)
    set_dict_attr(picture_content_table_tuple, "$.alternative_text",    alternative_text)
    set_dict_attr(picture_content_table_tuple, "$.font_color",          font_color)
    set_dict_attr(picture_content_table_tuple, "$.level",               level)
    set_dict_attr(picture_content_table_tuple, "$.name",                name)
    
    if uri is not None:
      picture_content_table.insert_record(picture_content_table_tuple, on_duplicate='ignore')

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
      label            = "badge_image_list"
      uri              = get_dict_attr(badge_image, "$.uri")
      alternative_text = get_dict_attr(badge_image, "$.content.alternative_text")
      font_color       = get_dict_attr(badge_image, "$.content.font_color")
      level            = get_dict_attr(badge_image, "$.content.level")
      name             = get_dict_attr(badge_image, "$.content.name")
        
      ##
      ## url_index auto increment
      ##
      set_dict_attr(picture_content_table_tuple, "$.start_time",       dat.fromtimestamp(start_time))
      set_dict_attr(picture_content_table_tuple, "$.platform",         DOUYIN_PLATFORM)
      set_dict_attr(picture_content_table_tuple, "$.room_id",          str(room_id))
      set_dict_attr(picture_content_table_tuple, "$.label",            label)
      set_dict_attr(picture_content_table_tuple, "$.uri",              uri)
      set_dict_attr(picture_content_table_tuple, "$.alternative_text", alternative_text)
      set_dict_attr(picture_content_table_tuple, "$.font_color",       font_color)
      set_dict_attr(picture_content_table_tuple, "$.level",            level)
      set_dict_attr(picture_content_table_tuple, "$.name",             name)

      if uri is not None:
        picture_content_table.insert_record(picture_content_table_tuple, on_duplicate='ignore')

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
      label            = "badge_image_list_v2"
      uri              = get_dict_attr(badge_image, "$.uri")
      alternative_text = get_dict_attr(badge_image, "$.content.alternative_text")
      font_color       = get_dict_attr(badge_image, "$.content.font_color")
      level            = get_dict_attr(badge_image, "$.content.level")
      name             = get_dict_attr(badge_image, "$.content.name")
        
      ##
      ## url_index auto increment
      ##
      set_dict_attr(picture_content_table_tuple, "$.start_time",       dat.fromtimestamp(start_time))
      set_dict_attr(picture_content_table_tuple, "$.platform",         DOUYIN_PLATFORM)
      set_dict_attr(picture_content_table_tuple, "$.room_id",          str(room_id))
      set_dict_attr(picture_content_table_tuple, "$.label",            label)
      set_dict_attr(picture_content_table_tuple, "$.uri",              uri)
      set_dict_attr(picture_content_table_tuple, "$.alternative_text", alternative_text)
      set_dict_attr(picture_content_table_tuple, "$.font_color",       font_color)
      set_dict_attr(picture_content_table_tuple, "$.level",            level)
      set_dict_attr(picture_content_table_tuple, "$.name",             name)

      if uri is not None:
        picture_content_table.insert_record(picture_content_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(picture_content_table.get_name(), e))
    raise e
  
  ##
  ## UserTable
  ##
  user_table = UserTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(user_table.get_name()) is False:
      user_table.create()
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
    user_table_tuple                          = {key:None for key in user_table.get_tuple()}
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
    
    if id != 0:
      user_table.insert_record(user_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(user_table.get_name(), e))
    raise e

  ##
  ## RoomBaseTable
  ##
  room_base_table = RoomBaseTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(room_base_table.get_name()) is False:
      room_base_table.create()
    ##
    ## +----------------------------------+
    ## | Field                            |
    ## +----------------------------------+
    ## | id                               |
    ## | id_str                           |
    ## | title                            |
    ## | introduction                     |
    ## | share_url                        |
    ## | user_share_text                  |
    ## | anchor_share_text                |
    ## | create_time                      |
    ## | start_time                      |
    ## | finish_time                      |
    ## | stream_close_time                |
    ## | status                           |
    ## | finish_reason                    |
    ## | acquaintance_status              |
    ## | owner_user_id                    |
    ## | app_id                           |
    ## | base_category                    |
    ## | category                         |
    ## | client_version                   |
    ## | orientation                      |
    ## | layout                           |
    ## | room_layout                      |
    ## | room_tag                         |
    ## | live_room_mode                   |
    ## | live_platform_source             |
    ## | cell_style                       |
    ## | os_type                          |
    ## | visibility_range                 |
    ## | webcast_sdk_version              |
    ## | stream_id                        |
    ## | stream_id_str                    |
    ## | live_id                          |
    ## | stream_provider                  |
    ## | danmaku_detail                   |
    ## | web_count                        |
    ## | webcast_comment_tcs              |
    ## | gift_msg_style                   |
    ## | share_msg_style                  |
    ## | follow_msg_style                 |
    ## | fansclub_msg_style               |
    ## | sell_goods                       |
    ## | has_commerce_goods               |
    ## | is_replay                        |
    ## | highlight                        |
    ## | use_filter                       |
    ## | title_recommend                  |
    ## | enable_room_perspective          |
    ## | with_aggregate_column            |
    ## | with_draw_something              |
    ## | with_ktv                         |
    ## | with_linkmic                     |
    ## | live_type_normal                 |
    ## | live_type_audio                  |
    ## | live_type_linkmic                |
    ## | live_type_official               |
    ## | live_type_sandbox                |
    ## | live_type_screenshot             |
    ## | live_type_third_party            |
    ## | live_type_vs_live                |
    ## | live_type_vs_premiere            |
    ## | linkmic_layout                   |
    ## | rival_anchor_id                  |
    ## | auth_city                        |
    ## | location                         |
    ## | distance                         |
    ## | distance_city                    |
    ## | distance_km                      |
    ## | real_distance                    |
    ## | dynamic_cover_uri                |
    ## | vertical_cover_uri               |
    ## | finish_url                       |
    ## | forum_extra_data                 |
    ## | item_explicit_info               |
    ## | hot_sentence_info                |
    ## | relation_tag                     |
    ## | stamps                           |
    ## | room_create_ab_param             |
    ## | scroll_config                    |
    ## | mosaic_tip                       |
    ## | popularity_str                   |
    ## | preview_copy                     |
    ## | wait_copy                        |
    ## | short_title                      |
    ## | video_feed_tag                   |
    ## | screen_capture_sharing_title     |
    ## | common_label_list                |
    ## | content_tag                      |
    ## | challenge_info                   |
    ## | anchor_scheduled_time_text       |
    ## | anchor_tab_type                  |
    ## | comment_name_mode                |
    ## | fcdn_appid                       |
    ## | game_room_type                   |
    ## | official_channel_open_id         |
    ## | official_channel_uid             |
    ## | search_id                        |
    ## | group_id                         |
    ## | group_source                     |
    ## | sofa_layout                      |
    ## | ranklist_audience_type           |
    ## | redpacket_audience_auth          |
    ## | toutiao_cover_recommend_level    |
    ## | toutiao_title_recommend_level    |
    ## | preview_flow_tag                 |
    ## | replay_location                  |
    ## | room_audit_status                |
    ## | mosaic_status                    |
    ## | lottery_finish_time              |
    ## | luckymoney_num                   |
    ## | has_promotion_games              |
    ## | is_need_check_list               |
    ## | is_official_channel_room         |
    ## | is_show_inquiry_ball             |
    ## | is_show_user_card_switch         |
    ## | auto_cover                       |
    ## | business_live                    |
    ## | book_time                        |
    ## | book_end_time                    |
    ## | linkmic_display_type             |
    ## | vid                              |
    ## | vs_main_replay_id                |
    ## | last_ping_time                   |
    ## | pre_enter_time                   |
    ## | city_top_distance                |
    ## | cover_data                       |
    ## | content_label_data               |
    ## | feed_room_label_data             |
    ## | guide_button_data                |
    ## | comment_box_data                 |
    ## | link_mic_data                    |
    ## | living_room_attrs_data           |
    ## | pack_meta_data                   |
    ## | paid_live_data                   |
    ## | view_stats_data                  |
    ## | extra_data                       |
    ## | room_auth_data                   |
    ## | short_touch_config_data          |
    ## | stream_url_data                  |
    ## | stream_extra_data                |
    ## | stats_data                       |
    ## | admin_user_ids                   |
    ## | admin_user_open_ids              |
    ## | fans_group_admin_user_ids        |
    ## | fans_group_admin_user_open_ids   |
    ## | filter_words                     |
    ## | live_distribution                |
    ## | sharing_music_ids                |
    ## | tags                             |
    ## | top_fans                         |
    ## | ticket_count                     |
    ## | top_vip_no                       |
    ## | upper_right_widget_data_list     |
    ## | vs_roles                         |
    ## | room_tabs                        |
    ## | assist_labels                    |
    ## | anchor_ab_map                    |
    ## | linker_map                       |
    ## | dynamic_cover_dict               |
    ## | created_at                       |
    ## | updated_at                       |
    ## +----------------------------------+
    ##
    room_base_table_tuple = {key:None for key in room_base_table.get_tuple()}

    id                               = get_dict_attr(data, "$.data.room.id")
    id_str                           = get_dict_attr(data, "$.data.room.id_str")
    title                            = get_dict_attr(data, "$.data.room.title")
    introduction                     = get_dict_attr(data, "$.data.room.introduction")
    share_url                        = get_dict_attr(data, "$.data.room.share_url")
    user_share_text                  = get_dict_attr(data, "$.data.room.user_share_text")
    anchor_share_text                = get_dict_attr(data, "$.data.room.anchor_share_text")
    create_time                      = get_dict_attr(data, "$.data.room.create_time")
    start_time_rb                    = get_dict_attr(data, "$.data.room.start_time")
    finish_time_rb                   = get_dict_attr(data, "$.data.room.finish_time")
    stream_close_time                = get_dict_attr(data, "$.data.room.stream_close_time")
    status                           = get_dict_attr(data, "$.data.room.status")
    finish_reason                    = get_dict_attr(data, "$.data.room.finish_reason")
    acquaintance_status              = get_dict_attr(data, "$.data.room.acquaintance_status")
    owner_user_id_rb                 = get_dict_attr(data, "$.data.room.owner_user_id")
    app_id_rb                        = get_dict_attr(data, "$.data.room.app_id")
    base_category                    = get_dict_attr(data, "$.data.room.base_category")
    category_rb                      = get_dict_attr(data, "$.data.room.category")
    client_version_rb                = get_dict_attr(data, "$.data.room.client_version")
    orientation                      = get_dict_attr(data, "$.data.room.orientation")
    layout                           = get_dict_attr(data, "$.data.room.layout")
    room_layout                      = get_dict_attr(data, "$.data.room.room_layout")
    room_tag                         = get_dict_attr(data, "$.data.room.room_tag")
    live_room_mode                   = get_dict_attr(data, "$.data.room.live_room_mode")
    live_platform_source             = get_dict_attr(data, "$.data.room.live_platform_source")
    cell_style                       = get_dict_attr(data, "$.data.room.cell_style")
    os_type                          = get_dict_attr(data, "$.data.room.os_type")
    visibility_range                 = get_dict_attr(data, "$.data.room.visibility_range")
    webcast_sdk_version              = get_dict_attr(data, "$.data.room.webcast_sdk_version")
    stream_id                        = get_dict_attr(data, "$.data.room.stream_id")
    stream_id_str                    = get_dict_attr(data, "$.data.room.stream_id_str")
    live_id_rb                       = get_dict_attr(data, "$.data.room.live_id")
    stream_provider                  = get_dict_attr(data, "$.data.room.stream_provider")
    danmaku_detail                   = get_dict_attr(data, "$.data.room.danmaku_detail")
    web_count                        = get_dict_attr(data, "$.data.room.web_count")
    webcast_comment_tcs              = get_dict_attr(data, "$.data.room.webcast_comment_tcs")
    gift_msg_style_rb                = get_dict_attr(data, "$.data.room.gift_msg_style")
    share_msg_style_rb               = get_dict_attr(data, "$.data.room.share_msg_style")
    follow_msg_style_rb              = get_dict_attr(data, "$.data.room.follow_msg_style")
    fansclub_msg_style_rb            = get_dict_attr(data, "$.data.room.fansclub_msg_style")
    sell_goods_rb                    = get_dict_attr(data, "$.data.room.sell_goods")
    has_commerce_goods_rb            = get_dict_attr(data, "$.data.room.has_commerce_goods")
    is_replay_rb                     = get_dict_attr(data, "$.data.room.is_replay")
    highlight_rb                     = get_dict_attr(data, "$.data.room.highlight")
    use_filter_rb                    = get_dict_attr(data, "$.data.room.use_filter")
    title_recommend                  = get_dict_attr(data, "$.data.room.title_recommend")
    enable_room_perspective_rb       = get_dict_attr(data, "$.data.room.enable_room_perspective")
    with_aggregate_column            = get_dict_attr(data, "$.data.room.with_aggregate_column")
    with_draw_something              = get_dict_attr(data, "$.data.room.with_draw_something")
    with_ktv                         = get_dict_attr(data, "$.data.room.with_ktv")
    with_linkmic                     = get_dict_attr(data, "$.data.room.with_linkmic")
    live_type_normal_rb              = get_dict_attr(data, "$.data.room.live_type_normal")
    live_type_audio_rb               = get_dict_attr(data, "$.data.room.live_type_audio")
    live_type_linkmic_rb             = get_dict_attr(data, "$.data.room.live_type_linkmic")
    live_type_official_rb            = get_dict_attr(data, "$.data.room.live_type_official")
    live_type_sandbox_rb             = get_dict_attr(data, "$.data.room.live_type_sandbox")
    live_type_screenshot_rb          = get_dict_attr(data, "$.data.room.live_type_screenshot")
    live_type_third_party_rb         = get_dict_attr(data, "$.data.room.live_type_third_party")
    live_type_vs_live_rb             = get_dict_attr(data, "$.data.room.live_type_vs_live")
    live_type_vs_premiere_rb         = get_dict_attr(data, "$.data.room.live_type_vs_premiere")
    linkmic_layout_rb                = get_dict_attr(data, "$.data.room.linkmic_layout")
    rival_anchor_id                  = get_dict_attr(data, "$.data.room.rival_anchor_id")
    auth_city_rb                     = get_dict_attr(data, "$.data.room.auth_city")
    location_rb                      = get_dict_attr(data, "$.data.room.location")
    distance_rb                      = get_dict_attr(data, "$.data.room.distance")
    distance_city_rb                 = get_dict_attr(data, "$.data.room.distance_city")
    distance_km_rb                   = get_dict_attr(data, "$.data.room.distance_km")
    real_distance                    = get_dict_attr(data, "$.data.room.real_distance")
    dynamic_cover_uri_rb             = get_dict_attr(data, "$.data.room.dynamic_cover_uri")
    vertical_cover_uri_rb            = get_dict_attr(data, "$.data.room.vertical_cover_uri")
    finish_url_rb                    = get_dict_attr(data, "$.data.room.finish_url")
    forum_extra_data_rb              = get_dict_attr(data, "$.data.room.forum_extra_data")
    item_explicit_info_rb            = get_dict_attr(data, "$.data.room.item_explicit_info")
    hot_sentence_info                = get_dict_attr(data, "$.data.room.hot_sentence_info")
    relation_tag                     = get_dict_attr(data, "$.data.room.relation_tag")
    stamps                           = get_dict_attr(data, "$.data.room.stamps")
    room_create_ab_param             = get_dict_attr(data, "$.data.room.room_create_ab_param")
    scroll_config_rb                 = get_dict_attr(data, "$.data.room.scroll_config")
    mosaic_tip                       = get_dict_attr(data, "$.data.room.mosaic_tip")
    popularity_str                   = get_dict_attr(data, "$.data.room.popularity_str")
    preview_copy                     = get_dict_attr(data, "$.data.room.preview_copy")
    wait_copy_rb                     = get_dict_attr(data, "$.data.room.wait_copy")
    short_title                      = get_dict_attr(data, "$.data.room.short_title")
    video_feed_tag_rb                = get_dict_attr(data, "$.data.room.video_feed_tag")
    screen_capture_sharing_title     = get_dict_attr(data, "$.data.room.screen_capture_sharing_title")
    common_label_list_rb             = get_dict_attr(data, "$.data.room.common_label_list")
    content_tag_rb                   = get_dict_attr(data, "$.data.room.content_tag")
    challenge_info                   = get_dict_attr(data, "$.data.room.challenge_info")
    anchor_scheduled_time_text_rb    = get_dict_attr(data, "$.data.room.anchor_scheduled_time_text")
    anchor_tab_type_rb               = get_dict_attr(data, "$.data.room.anchor_tab_type")
    comment_name_mode_rb             = get_dict_attr(data, "$.data.room.comment_name_mode")
    fcdn_appid_rb                    = get_dict_attr(data, "$.data.room.fcdn_appid")
    game_room_type_rb                = get_dict_attr(data, "$.data.room.game_room_type")
    official_channel_open_id_rb      = get_dict_attr(data, "$.data.room.official_channel_open_id")
    official_channel_uid_rb          = get_dict_attr(data, "$.data.room.official_channel_uid")
    search_id_rb                     = get_dict_attr(data, "$.data.room.search_id")
    group_id_rb                      = get_dict_attr(data, "$.data.room.group_id")
    group_source_rb                  = get_dict_attr(data, "$.data.room.group_source")
    sofa_layout                      = get_dict_attr(data, "$.data.room.sofa_layout")
    ranklist_audience_type           = get_dict_attr(data, "$.data.room.ranklist_audience_type")
    redpacket_audience_auth          = get_dict_attr(data, "$.data.room.redpacket_audience_auth")
    toutiao_cover_recommend_level_rb = get_dict_attr(data, "$.data.room.toutiao_cover_recommend_level")
    toutiao_title_recommend_level_rb = get_dict_attr(data, "$.data.room.toutiao_title_recommend_level")
    preview_flow_tag                 = get_dict_attr(data, "$.data.room.preview_flow_tag")
    replay_location                  = get_dict_attr(data, "$.data.room.replay_location")
    room_audit_status                = get_dict_attr(data, "$.data.room.room_audit_status")
    mosaic_status                    = get_dict_attr(data, "$.data.room.mosaic_status")
    lottery_finish_time              = get_dict_attr(data, "$.data.room.lottery_finish_time")
    luckymoney_num                   = get_dict_attr(data, "$.data.room.luckymoney_num")
    has_promotion_games_rb           = get_dict_attr(data, "$.data.room.has_promotion_games")
    is_need_check_list_rb            = get_dict_attr(data, "$.data.room.is_need_check_list")
    is_official_channel_room_rb      = get_dict_attr(data, "$.data.room.is_official_channel_room")
    is_show_inquiry_ball             = get_dict_attr(data, "$.data.room.is_show_inquiry_ball")
    is_show_user_card_switch         = get_dict_attr(data, "$.data.room.is_show_user_card_switch")
    auto_cover_rb                    = get_dict_attr(data, "$.data.room.auto_cover")
    business_live_rb                 = get_dict_attr(data, "$.data.room.business_live")
    book_time_rb                     = get_dict_attr(data, "$.data.room.book_time")
    book_end_time_rb                 = get_dict_attr(data, "$.data.room.book_end_time")
    linkmic_display_type_rb          = get_dict_attr(data, "$.data.room.linkmic_display_type")
    vid_rb                           = get_dict_attr(data, "$.data.room.vid")
    vs_main_replay_id_rb             = get_dict_attr(data, "$.data.room.vs_main_replay_id")
    last_ping_time                   = get_dict_attr(data, "$.data.room.last_ping_time")
    pre_enter_time                   = get_dict_attr(data, "$.data.room.pre_enter_time")
    city_top_distance_rb             = get_dict_attr(data, "$.data.room.city_top_distance")

    ## JSON 扩展字段
    cover_data                       = get_dict_attr(data, "$.data.room.cover_data")
    content_label_data               = get_dict_attr(data, "$.data.room.content_label_data")
    feed_room_label_data             = get_dict_attr(data, "$.data.room.feed_room_label_data")
    guide_button_data                = get_dict_attr(data, "$.data.room.guide_button_data")
    comment_box_data                 = get_dict_attr(data, "$.data.room.comment_box_data")
    link_mic_data                    = get_dict_attr(data, "$.data.room.link_mic_data")
    living_room_attrs_data           = get_dict_attr(data, "$.data.room.living_room_attrs_data")
    pack_meta_data                   = get_dict_attr(data, "$.data.room.pack_meta_data")
    paid_live_data                   = get_dict_attr(data, "$.data.room.paid_live_data")
    view_stats_data                  = get_dict_attr(data, "$.data.room.view_stats_data")
    extra_data                       = get_dict_attr(data, "$.data.room.extra_data")
    room_auth_data                   = get_dict_attr(data, "$.data.room.room_auth_data")
    short_touch_config_data          = get_dict_attr(data, "$.data.room.short_touch_config_data")
    stream_url_data                  = get_dict_attr(data, "$.data.room.stream_url_data")
    stream_extra_data                = get_dict_attr(data, "$.data.room.stream_extra_data")
    stats_data                       = get_dict_attr(data, "$.data.room.stats_data")

    ## JSON 数组字段
    admin_user_ids_rb                = get_dict_attr(data, "$.data.room.admin_user_ids")
    admin_user_open_ids              = get_dict_attr(data, "$.data.room.admin_user_open_ids")
    fans_group_admin_user_ids        = get_dict_attr(data, "$.data.room.fans_group_admin_user_ids")
    fans_group_admin_user_open_ids   = get_dict_attr(data, "$.data.room.fans_group_admin_user_open_ids")
    filter_words_rb                  = get_dict_attr(data, "$.data.room.filter_words")
    live_distribution_rb             = get_dict_attr(data, "$.data.room.live_distribution")
    sharing_music_ids                = get_dict_attr(data, "$.data.room.sharing_music_ids")
    tags_rb                          = get_dict_attr(data, "$.data.room.tags")
    top_fans_rb                      = get_dict_attr(data, "$.data.room.top_fans")
    ticket_count                     = get_dict_attr(data, "$.data.room.ticket_count")
    top_vip_no                       = get_dict_attr(data, "$.data.room.top_vip_no")
    upper_right_widget_data_list     = get_dict_attr(data, "$.data.room.upper_right_widget_data_list")
    vs_roles_rb                      = get_dict_attr(data, "$.data.room.vs_roles")
    room_tabs                        = get_dict_attr(data, "$.data.room.room_tabs")
    assist_labels                    = get_dict_attr(data, "$.data.room.assist_labels")
    anchor_ab_map_rb                 = get_dict_attr(data, "$.data.room.anchor_ab_map")
    linker_map                       = get_dict_attr(data, "$.data.room.linker_map")
    dynamic_cover_dict_rb            = get_dict_attr(data, "$.data.room.dynamic_cover_dict")

    set_dict_attr(room_base_table_tuple, "$.id",                            str(id) if id is not None else None)
    set_dict_attr(room_base_table_tuple, "$.id_str",                        str(id_str) if id_str is not None else None)
    set_dict_attr(room_base_table_tuple, "$.title",                         title)
    set_dict_attr(room_base_table_tuple, "$.introduction",                  introduction)
    set_dict_attr(room_base_table_tuple, "$.share_url",                     share_url)
    set_dict_attr(room_base_table_tuple, "$.user_share_text",               user_share_text)
    set_dict_attr(room_base_table_tuple, "$.anchor_share_text",             anchor_share_text)
    set_dict_attr(room_base_table_tuple, "$.create_time",                   create_time if create_time != 0 else None)
    set_dict_attr(room_base_table_tuple, "$.start_time",                    start_time_rb if start_time_rb != 0 else None)
    set_dict_attr(room_base_table_tuple, "$.finish_time",                   finish_time_rb if finish_time_rb != 0 else None)
    set_dict_attr(room_base_table_tuple, "$.stream_close_time",             stream_close_time if stream_close_time != 0 else None)
    set_dict_attr(room_base_table_tuple, "$.status",                        status)
    set_dict_attr(room_base_table_tuple, "$.finish_reason",                 finish_reason)
    set_dict_attr(room_base_table_tuple, "$.acquaintance_status",           acquaintance_status)
    set_dict_attr(room_base_table_tuple, "$.owner_user_id",                 str(owner_user_id_rb) if owner_user_id_rb is not None else None)
    set_dict_attr(room_base_table_tuple, "$.app_id",                        str(app_id_rb) if app_id_rb is not None else None)
    set_dict_attr(room_base_table_tuple, "$.base_category",                 base_category)
    set_dict_attr(room_base_table_tuple, "$.category",                      category_rb)
    set_dict_attr(room_base_table_tuple, "$.client_version",                str(client_version_rb) if client_version_rb is not None else None)
    set_dict_attr(room_base_table_tuple, "$.orientation",                   orientation)
    set_dict_attr(room_base_table_tuple, "$.layout",                        layout)
    set_dict_attr(room_base_table_tuple, "$.room_layout",                   room_layout)
    set_dict_attr(room_base_table_tuple, "$.room_tag",                      room_tag)
    set_dict_attr(room_base_table_tuple, "$.live_room_mode",                live_room_mode)
    set_dict_attr(room_base_table_tuple, "$.live_platform_source",          live_platform_source)
    set_dict_attr(room_base_table_tuple, "$.cell_style",                    cell_style)
    set_dict_attr(room_base_table_tuple, "$.os_type",                       os_type)
    set_dict_attr(room_base_table_tuple, "$.visibility_range",              visibility_range)
    set_dict_attr(room_base_table_tuple, "$.webcast_sdk_version",           str(webcast_sdk_version) if webcast_sdk_version is not None else None)
    set_dict_attr(room_base_table_tuple, "$.stream_id",                     str(stream_id) if stream_id is not None else None)
    set_dict_attr(room_base_table_tuple, "$.stream_id_str",                 str(stream_id_str) if stream_id_str is not None else None)
    set_dict_attr(room_base_table_tuple, "$.live_id",                       str(live_id_rb) if live_id_rb is not None else None)
    set_dict_attr(room_base_table_tuple, "$.stream_provider",               stream_provider)
    set_dict_attr(room_base_table_tuple, "$.danmaku_detail",                danmaku_detail)
    set_dict_attr(room_base_table_tuple, "$.web_count",                     web_count)
    set_dict_attr(room_base_table_tuple, "$.webcast_comment_tcs",           webcast_comment_tcs)
    set_dict_attr(room_base_table_tuple, "$.gift_msg_style",                gift_msg_style_rb)
    set_dict_attr(room_base_table_tuple, "$.share_msg_style",               share_msg_style_rb)
    set_dict_attr(room_base_table_tuple, "$.follow_msg_style",              follow_msg_style_rb)
    set_dict_attr(room_base_table_tuple, "$.fansclub_msg_style",            fansclub_msg_style_rb)
    set_dict_attr(room_base_table_tuple, "$.sell_goods",                    sell_goods_rb)
    set_dict_attr(room_base_table_tuple, "$.has_commerce_goods",            has_commerce_goods_rb)
    set_dict_attr(room_base_table_tuple, "$.is_replay",                     is_replay_rb)
    set_dict_attr(room_base_table_tuple, "$.highlight",                     highlight_rb)
    set_dict_attr(room_base_table_tuple, "$.use_filter",                    use_filter_rb)
    set_dict_attr(room_base_table_tuple, "$.title_recommend",               title_recommend)
    set_dict_attr(room_base_table_tuple, "$.enable_room_perspective",       enable_room_perspective_rb)
    set_dict_attr(room_base_table_tuple, "$.with_aggregate_column",         with_aggregate_column)
    set_dict_attr(room_base_table_tuple, "$.with_draw_something",           with_draw_something)
    set_dict_attr(room_base_table_tuple, "$.with_ktv",                      with_ktv)
    set_dict_attr(room_base_table_tuple, "$.with_linkmic",                  with_linkmic)
    set_dict_attr(room_base_table_tuple, "$.live_type_normal",              live_type_normal_rb)
    set_dict_attr(room_base_table_tuple, "$.live_type_audio",               live_type_audio_rb)
    set_dict_attr(room_base_table_tuple, "$.live_type_linkmic",             live_type_linkmic_rb)
    set_dict_attr(room_base_table_tuple, "$.live_type_official",            live_type_official_rb)
    set_dict_attr(room_base_table_tuple, "$.live_type_sandbox",             live_type_sandbox_rb)
    set_dict_attr(room_base_table_tuple, "$.live_type_screenshot",          live_type_screenshot_rb)
    set_dict_attr(room_base_table_tuple, "$.live_type_third_party",         live_type_third_party_rb)
    set_dict_attr(room_base_table_tuple, "$.live_type_vs_live",             live_type_vs_live_rb)
    set_dict_attr(room_base_table_tuple, "$.live_type_vs_premiere",         live_type_vs_premiere_rb)
    set_dict_attr(room_base_table_tuple, "$.linkmic_layout",                linkmic_layout_rb)
    set_dict_attr(room_base_table_tuple, "$.rival_anchor_id",               str(rival_anchor_id) if rival_anchor_id is not None else None)
    set_dict_attr(room_base_table_tuple, "$.auth_city",                     auth_city_rb)
    set_dict_attr(room_base_table_tuple, "$.location",                      location_rb)
    set_dict_attr(room_base_table_tuple, "$.distance",                      distance_rb)
    set_dict_attr(room_base_table_tuple, "$.distance_city",                 distance_city_rb)
    set_dict_attr(room_base_table_tuple, "$.distance_km",                   distance_km_rb)
    set_dict_attr(room_base_table_tuple, "$.real_distance",                 real_distance)
    set_dict_attr(room_base_table_tuple, "$.dynamic_cover_uri",             dynamic_cover_uri_rb)
    set_dict_attr(room_base_table_tuple, "$.vertical_cover_uri",            vertical_cover_uri_rb)
    set_dict_attr(room_base_table_tuple, "$.finish_url",                    finish_url_rb)
    set_dict_attr(room_base_table_tuple, "$.forum_extra_data",              forum_extra_data_rb)
    set_dict_attr(room_base_table_tuple, "$.item_explicit_info",            item_explicit_info_rb)
    set_dict_attr(room_base_table_tuple, "$.hot_sentence_info",             hot_sentence_info)
    set_dict_attr(room_base_table_tuple, "$.relation_tag",                  relation_tag)
    set_dict_attr(room_base_table_tuple, "$.stamps",                        stamps)
    set_dict_attr(room_base_table_tuple, "$.room_create_ab_param",          room_create_ab_param)
    set_dict_attr(room_base_table_tuple, "$.scroll_config",                 scroll_config_rb)
    set_dict_attr(room_base_table_tuple, "$.mosaic_tip",                    mosaic_tip)
    set_dict_attr(room_base_table_tuple, "$.popularity_str",                popularity_str)
    set_dict_attr(room_base_table_tuple, "$.preview_copy",                  preview_copy)
    set_dict_attr(room_base_table_tuple, "$.wait_copy",                     wait_copy_rb)
    set_dict_attr(room_base_table_tuple, "$.short_title",                   short_title)
    set_dict_attr(room_base_table_tuple, "$.video_feed_tag",                video_feed_tag_rb)
    set_dict_attr(room_base_table_tuple, "$.screen_capture_sharing_title",  screen_capture_sharing_title)
    set_dict_attr(room_base_table_tuple, "$.common_label_list",             common_label_list_rb)
    set_dict_attr(room_base_table_tuple, "$.content_tag",                   content_tag_rb)
    set_dict_attr(room_base_table_tuple, "$.challenge_info",                challenge_info)
    set_dict_attr(room_base_table_tuple, "$.anchor_scheduled_time_text",    anchor_scheduled_time_text_rb)
    set_dict_attr(room_base_table_tuple, "$.anchor_tab_type",               anchor_tab_type_rb)
    set_dict_attr(room_base_table_tuple, "$.comment_name_mode",             comment_name_mode_rb)
    set_dict_attr(room_base_table_tuple, "$.fcdn_appid",                    str(fcdn_appid_rb) if fcdn_appid_rb is not None else None)
    set_dict_attr(room_base_table_tuple, "$.game_room_type",                game_room_type_rb)
    set_dict_attr(room_base_table_tuple, "$.official_channel_open_id",      official_channel_open_id_rb)
    set_dict_attr(room_base_table_tuple, "$.official_channel_uid",          str(official_channel_uid_rb) if official_channel_uid_rb is not None else None)
    set_dict_attr(room_base_table_tuple, "$.search_id",                     str(search_id_rb) if search_id_rb is not None else None)
    set_dict_attr(room_base_table_tuple, "$.group_id",                      str(group_id_rb) if group_id_rb is not None else None)
    set_dict_attr(room_base_table_tuple, "$.group_source",                  group_source_rb)
    set_dict_attr(room_base_table_tuple, "$.sofa_layout",                   sofa_layout)
    set_dict_attr(room_base_table_tuple, "$.ranklist_audience_type",        ranklist_audience_type)
    set_dict_attr(room_base_table_tuple, "$.redpacket_audience_auth",       redpacket_audience_auth)
    set_dict_attr(room_base_table_tuple, "$.toutiao_cover_recommend_level", toutiao_cover_recommend_level_rb)
    set_dict_attr(room_base_table_tuple, "$.toutiao_title_recommend_level", toutiao_title_recommend_level_rb)
    set_dict_attr(room_base_table_tuple, "$.preview_flow_tag",              preview_flow_tag)
    set_dict_attr(room_base_table_tuple, "$.replay_location",               replay_location)
    set_dict_attr(room_base_table_tuple, "$.room_audit_status",             room_audit_status)
    set_dict_attr(room_base_table_tuple, "$.mosaic_status",                 mosaic_status)
    set_dict_attr(room_base_table_tuple, "$.lottery_finish_time",           lottery_finish_time)
    set_dict_attr(room_base_table_tuple, "$.luckymoney_num",                luckymoney_num)
    set_dict_attr(room_base_table_tuple, "$.has_promotion_games",           has_promotion_games_rb)
    set_dict_attr(room_base_table_tuple, "$.is_need_check_list",            is_need_check_list_rb)
    set_dict_attr(room_base_table_tuple, "$.is_official_channel_room",      is_official_channel_room_rb)
    set_dict_attr(room_base_table_tuple, "$.is_show_inquiry_ball",          is_show_inquiry_ball)
    set_dict_attr(room_base_table_tuple, "$.is_show_user_card_switch",      is_show_user_card_switch)
    set_dict_attr(room_base_table_tuple, "$.auto_cover",                    auto_cover_rb)
    set_dict_attr(room_base_table_tuple, "$.business_live",                 business_live_rb)
    set_dict_attr(room_base_table_tuple, "$.book_time",                     book_time_rb if book_time_rb != 0 else None)
    set_dict_attr(room_base_table_tuple, "$.book_end_time",                 book_end_time_rb if book_end_time_rb != 0 else None)
    set_dict_attr(room_base_table_tuple, "$.linkmic_display_type",          linkmic_display_type_rb)
    set_dict_attr(room_base_table_tuple, "$.vid",                           vid_rb)
    set_dict_attr(room_base_table_tuple, "$.vs_main_replay_id",             str(vs_main_replay_id_rb) if vs_main_replay_id_rb is not None else None)
    set_dict_attr(room_base_table_tuple, "$.last_ping_time",                last_ping_time)
    set_dict_attr(room_base_table_tuple, "$.pre_enter_time",                pre_enter_time)
    set_dict_attr(room_base_table_tuple, "$.city_top_distance",             city_top_distance_rb)

    ## JSON 扩展字段
    set_dict_attr(room_base_table_tuple, "$.cover_data",                    json.dumps(cover_data) if cover_data else None)
    set_dict_attr(room_base_table_tuple, "$.content_label_data",            json.dumps(content_label_data) if content_label_data else None)
    set_dict_attr(room_base_table_tuple, "$.feed_room_label_data",          json.dumps(feed_room_label_data) if feed_room_label_data else None)
    set_dict_attr(room_base_table_tuple, "$.guide_button_data",             json.dumps(guide_button_data) if guide_button_data else None)
    set_dict_attr(room_base_table_tuple, "$.comment_box_data",              json.dumps(comment_box_data) if comment_box_data else None)
    set_dict_attr(room_base_table_tuple, "$.link_mic_data",                 json.dumps(link_mic_data) if link_mic_data else None)
    set_dict_attr(room_base_table_tuple, "$.living_room_attrs_data",        json.dumps(living_room_attrs_data) if living_room_attrs_data else None)
    set_dict_attr(room_base_table_tuple, "$.pack_meta_data",                json.dumps(pack_meta_data) if pack_meta_data else None)
    set_dict_attr(room_base_table_tuple, "$.paid_live_data",                json.dumps(paid_live_data) if paid_live_data else None)
    set_dict_attr(room_base_table_tuple, "$.view_stats_data",               json.dumps(view_stats_data) if view_stats_data else None)
    set_dict_attr(room_base_table_tuple, "$.extra_data",                    json.dumps(extra_data) if extra_data else None)
    set_dict_attr(room_base_table_tuple, "$.room_auth_data",                json.dumps(room_auth_data) if room_auth_data else None)
    set_dict_attr(room_base_table_tuple, "$.short_touch_config_data",       json.dumps(short_touch_config_data) if short_touch_config_data else None)
    set_dict_attr(room_base_table_tuple, "$.stream_url_data",               json.dumps(stream_url_data) if stream_url_data else None)
    set_dict_attr(room_base_table_tuple, "$.stream_extra_data",             json.dumps(stream_extra_data) if stream_extra_data else None)
    set_dict_attr(room_base_table_tuple, "$.stats_data",                    json.dumps(stats_data) if stats_data else None)

    ## JSON 数组字段
    set_dict_attr(room_base_table_tuple, "$.admin_user_ids",                json.dumps(admin_user_ids_rb) if admin_user_ids_rb else None)
    set_dict_attr(room_base_table_tuple, "$.admin_user_open_ids",           json.dumps(admin_user_open_ids) if admin_user_open_ids else None)
    set_dict_attr(room_base_table_tuple, "$.fans_group_admin_user_ids",     json.dumps(fans_group_admin_user_ids) if fans_group_admin_user_ids else None)
    set_dict_attr(room_base_table_tuple, "$.fans_group_admin_user_open_ids",json.dumps(fans_group_admin_user_open_ids) if fans_group_admin_user_open_ids else None)
    set_dict_attr(room_base_table_tuple, "$.filter_words",                  json.dumps(filter_words_rb) if filter_words_rb else None)
    set_dict_attr(room_base_table_tuple, "$.live_distribution",             json.dumps(live_distribution_rb) if live_distribution_rb else None)
    set_dict_attr(room_base_table_tuple, "$.sharing_music_ids",             json.dumps(sharing_music_ids) if sharing_music_ids else None)
    set_dict_attr(room_base_table_tuple, "$.tags",                          json.dumps(tags_rb) if tags_rb else None)
    set_dict_attr(room_base_table_tuple, "$.top_fans",                      json.dumps(top_fans_rb) if top_fans_rb else None)
    set_dict_attr(room_base_table_tuple, "$.ticket_count",                  ticket_count)
    set_dict_attr(room_base_table_tuple, "$.top_vip_no",                    top_vip_no)
    set_dict_attr(room_base_table_tuple, "$.upper_right_widget_data_list",  json.dumps(upper_right_widget_data_list) if upper_right_widget_data_list else None)
    set_dict_attr(room_base_table_tuple, "$.vs_roles",                      json.dumps(vs_roles_rb) if vs_roles_rb else None)
    set_dict_attr(room_base_table_tuple, "$.room_tabs",                     json.dumps(room_tabs) if room_tabs else None)
    set_dict_attr(room_base_table_tuple, "$.assist_labels",                 json.dumps(assist_labels) if assist_labels else None)
    set_dict_attr(room_base_table_tuple, "$.anchor_ab_map",                 json.dumps(anchor_ab_map_rb) if anchor_ab_map_rb else None)
    set_dict_attr(room_base_table_tuple, "$.linker_map",                    json.dumps(linker_map) if linker_map else None)
    set_dict_attr(room_base_table_tuple, "$.dynamic_cover_dict",            json.dumps(dynamic_cover_dict_rb) if dynamic_cover_dict_rb else None)

    room_base_table.insert_record(room_base_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_base_table.get_name(), e))
    raise e

  ##
  ## RoomOwnerV2Table
  ##
  room_owner_v2_table = RoomOwnerV2Table(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(room_owner_v2_table.get_name()) is False:
      room_owner_v2_table.create()
    ##
    ## +----------------------------------+
    ## | Field                            |
    ## +----------------------------------+
    ## | room_id                          |
    ## | user_id                          |
    ## | owner_open_id                    |
    ## | owner_device_id                  |
    ## | sec_uid                          |
    ## | user_open_id                     |
    ## | short_id                         |
    ## | display_id                       |
    ## | nickname                         |
    ## | signature                        |
    ## | share_qrcode_uri                 |
    ## | special_id                       |
    ## | status                           |
    ## | bg_img_url                       |
    ## | gender                           |
    ## | city                             |
    ## | constellation                    |
    ## | age_range                        |
    ## | birthday                         |
    ## | birthday_description             |
    ## | birthday_valid                   |
    ## | location_city                    |
    ## | foreign_user                     |
    ## | mystery_man                      |
    ## | level                            |
    ## | exp                              |
    ## | experience                       |
    ## | fan_ticket_count                 |
    ## | consume_diamond_level            |
    ## | income_share_percent             |
    ## | link_mic_stats                   |
    ## | media_badge_image_list           |
    ## | modify_time                      |
    ## | pay_score                        |
    ## | pay_scores                       |
    ## | need_profile_guide               |
    ## | new_real_time_icons              |
    ## | real_time_icons                  |
    ## | follow_status                    |
    ## | is_follower                      |
    ## | is_following                     |
    ## | follow_info                      |
    ## | is_anonymous                     |
    ## | hotsoon_verified                 |
    ## | hotsoon_verified_reason          |
    ## | ichat_restrict_type              |
    ## | disable_ichat                    |
    ## | enable_ichat_img                 |
    ## | fold_stranger_chat               |
    ## | desensitized_nickname            |
    ## | verified                         |
    ## | verified_reason                  |
    ## | verified_content                 |
    ## | verified_mobile                  |
    ## | enterprise_verify_reason         |
    ## | custom_verify                    |
    ## | block_status                     |
    ## | comment_restrict                 |
    ## | public_area_oper_freq            |
    ## | secret                           |
    ## | user_role                        |
    ## | webcast_private                  |
    ## | can_view_webcast_private         |
    ## | user_canceled                    |
    ## | telephone                        |
    ## | with_commerce_permission         |
    ## | with_fusion_shop_entry           |
    ## | with_car_management_permission   |
    ## | adversary_authorization_info     |
    ## | adversary_user_status            |
    ## | authorization_info               |
    ## | allow_be_located                 |
    ## | allow_find_by_contacts           |
    ## | allow_others_download_video      |
    ## | allow_others_download_when_sharing_video |
    ## | allow_share_show_profile         |
    ## | allow_show_in_gossip             |
    ## | allow_show_my_action             |
    ## | allow_strange_comment            |
    ## | allow_unfollower_comment         |
    ## | allow_use_linkmic                |
    ## | remark_name                      |
    ## | avatar_large                     |
    ## | avatar_medium                    |
    ## | avatar_thumb                     |
    ## | badge_image_list                 |
    ## | badge_image_list_v2              |
    ## | commerce_webcast_config_ids      |
    ## | authentication_info              |
    ## | border_data                      |
    ## | pay_grade_data                   |
    ## | fans_club_data                   |
    ## | fans_group_info                  |
    ## | subscribe_data                   |
    ## | user_attr_data                   |
    ## | user_dress_info_data             |
    ## | biz_relation_data                |
    ## | j_accredit_info_data             |
    ## | own_room_data                    |
    ## | total_recharge_diamond_count     |
    ## | watch_duration_month             |
    ## | web_rid                          |
    ## | webcast_nick                     |
    ## | webcast_uid                      |
    ## | created_at                       |
    ## | updated_at                       |
    ## +----------------------------------+
    ##
    room_owner_v2_table_tuple = {key:None for key in room_owner_v2_table.get_tuple()}

    room_id_ro                       = get_dict_attr(data, "$.data.room.id")
    user_id_ro                       = get_dict_attr(data, "$.data.room.owner_user_id")
    owner_open_id_ro                 = get_dict_attr(data, "$.data.room.owner_open_id")
    owner_device_id_ro               = get_dict_attr(data, "$.data.room.owner_device_id")
    sec_uid                          = get_dict_attr(data, "$.data.room.sec_uid")
    user_open_id_ro                  = get_dict_attr(data, "$.data.room.user_open_id")
    short_id                         = get_dict_attr(data, "$.data.room.short_id")
    display_id                       = get_dict_attr(data, "$.data.room.display_id")
    nickname                         = get_dict_attr(data, "$.data.room.nickname")
    signature                        = get_dict_attr(data, "$.data.room.signature")
    share_qrcode_uri                 = get_dict_attr(data, "$.data.room.share_qrcode_uri")
    special_id                       = get_dict_attr(data, "$.data.room.special_id")
    status_ro                        = get_dict_attr(data, "$.data.room.status")
    bg_img_url                       = get_dict_attr(data, "$.data.room.bg_img_url")
    gender_ro                        = get_dict_attr(data, "$.data.room.gender")
    city_ro                          = get_dict_attr(data, "$.data.room.city")
    constellation                    = get_dict_attr(data, "$.data.room.constellation")
    age_range                        = get_dict_attr(data, "$.data.room.age_range")
    birthday                         = get_dict_attr(data, "$.data.room.birthday")
    birthday_description             = get_dict_attr(data, "$.data.room.birthday_description")
    birthday_valid                   = get_dict_attr(data, "$.data.room.birthday_valid")
    location_city                    = get_dict_attr(data, "$.data.room.location_city")
    foreign_user                     = get_dict_attr(data, "$.data.room.foreign_user")
    mystery_man                      = get_dict_attr(data, "$.data.room.mystery_man")
    level_ro                         = get_dict_attr(data, "$.data.room.level")
    exp                              = get_dict_attr(data, "$.data.room.exp")
    experience                       = get_dict_attr(data, "$.data.room.experience")
    fan_ticket_count                 = get_dict_attr(data, "$.data.room.fan_ticket_count")
    consume_diamond_level            = get_dict_attr(data, "$.data.room.consume_diamond_level")
    income_share_percent             = get_dict_attr(data, "$.data.room.income_share_percent")
    link_mic_stats                   = get_dict_attr(data, "$.data.room.link_mic_stats")
    media_badge_image_list_ro        = get_dict_attr(data, "$.data.room.media_badge_image_list")
    modify_time                      = get_dict_attr(data, "$.data.room.modify_time")
    pay_score                        = get_dict_attr(data, "$.data.room.pay_score")
    pay_scores                       = get_dict_attr(data, "$.data.room.pay_scores")
    need_profile_guide               = get_dict_attr(data, "$.data.room.need_profile_guide")
    new_real_time_icons_ro           = get_dict_attr(data, "$.data.room.new_real_time_icons")
    real_time_icons_ro               = get_dict_attr(data, "$.data.room.real_time_icons")
    follow_status                    = get_dict_attr(data, "$.data.room.follow_status")
    is_follower                      = get_dict_attr(data, "$.data.room.is_follower")
    is_following                     = get_dict_attr(data, "$.data.room.is_following")
    follow_info                      = get_dict_attr(data, "$.data.room.follow_info")
    is_anonymous                     = get_dict_attr(data, "$.data.room.is_anonymous")
    hotsoon_verified                 = get_dict_attr(data, "$.data.room.hotsoon_verified")
    hotsoon_verified_reason          = get_dict_attr(data, "$.data.room.hotsoon_verified_reason")
    ichat_restrict_type              = get_dict_attr(data, "$.data.room.ichat_restrict_type")
    disable_ichat                    = get_dict_attr(data, "$.data.room.disable_ichat")
    enable_ichat_img                 = get_dict_attr(data, "$.data.room.enable_ichat_img")
    fold_stranger_chat               = get_dict_attr(data, "$.data.room.fold_stranger_chat")
    desensitized_nickname            = get_dict_attr(data, "$.data.room.desensitized_nickname")
    verified_ro                      = get_dict_attr(data, "$.data.room.verified")
    verified_reason                  = get_dict_attr(data, "$.data.room.verified_reason")
    verified_content                 = get_dict_attr(data, "$.data.room.verified_content")
    verified_mobile                  = get_dict_attr(data, "$.data.room.verified_mobile")
    enterprise_verify_reason         = get_dict_attr(data, "$.data.room.enterprise_verify_reason")
    custom_verify                    = get_dict_attr(data, "$.data.room.custom_verify")
    block_status                     = get_dict_attr(data, "$.data.room.block_status")
    comment_restrict                 = get_dict_attr(data, "$.data.room.comment_restrict")
    public_area_oper_freq            = get_dict_attr(data, "$.data.room.public_area_oper_freq")
    secret                           = get_dict_attr(data, "$.data.room.secret")
    user_role                        = get_dict_attr(data, "$.data.room.user_role")
    webcast_private                  = get_dict_attr(data, "$.data.room.webcast_private")
    can_view_webcast_private         = get_dict_attr(data, "$.data.room.can_view_webcast_private")
    user_canceled                    = get_dict_attr(data, "$.data.room.user_canceled")
    telephone                        = get_dict_attr(data, "$.data.room.telephone")
    with_commerce_permission         = get_dict_attr(data, "$.data.room.with_commerce_permission")
    with_fusion_shop_entry           = get_dict_attr(data, "$.data.room.with_fusion_shop_entry")
    with_car_management_permission   = get_dict_attr(data, "$.data.room.with_car_management_permission")
    adversary_authorization_info     = get_dict_attr(data, "$.data.room.adversary_authorization_info")
    adversary_user_status            = get_dict_attr(data, "$.data.room.adversary_user_status")
    authorization_info               = get_dict_attr(data, "$.data.room.authorization_info")
    allow_be_located                 = get_dict_attr(data, "$.data.room.allow_be_located")
    allow_find_by_contacts           = get_dict_attr(data, "$.data.room.allow_find_by_contacts")
    allow_others_download_video      = get_dict_attr(data, "$.data.room.allow_others_download_video")
    allow_others_download_when_sharing_video = get_dict_attr(data, "$.data.room.allow_others_download_when_sharing_video")
    allow_share_show_profile         = get_dict_attr(data, "$.data.room.allow_share_show_profile")
    allow_show_in_gossip             = get_dict_attr(data, "$.data.room.allow_show_in_gossip")
    allow_show_my_action             = get_dict_attr(data, "$.data.room.allow_show_my_action")
    allow_strange_comment            = get_dict_attr(data, "$.data.room.allow_strange_comment")
    allow_unfollower_comment         = get_dict_attr(data, "$.data.room.allow_unfollower_comment")
    allow_use_linkmic                = get_dict_attr(data, "$.data.room.allow_use_linkmic")
    remark_name                      = get_dict_attr(data, "$.data.room.remark_name")

    ## JSON 扩展字段
    avatar_large                     = get_dict_attr(data, "$.data.room.avatar_large")
    avatar_medium                    = get_dict_attr(data, "$.data.room.avatar_medium")
    avatar_thumb                     = get_dict_attr(data, "$.data.room.avatar_thumb")
    badge_image_list                 = get_dict_attr(data, "$.data.room.badge_image_list")
    badge_image_list_v2              = get_dict_attr(data, "$.data.room.badge_image_list_v2")
    commerce_webcast_config_ids      = get_dict_attr(data, "$.data.room.commerce_webcast_config_ids")
    authentication_info              = get_dict_attr(data, "$.data.room.authentication_info")
    border_data                      = get_dict_attr(data, "$.data.room.border_data")
    pay_grade_data                   = get_dict_attr(data, "$.data.room.pay_grade_data")
    fans_club_data                   = get_dict_attr(data, "$.data.room.fans_club_data")
    fans_group_info                  = get_dict_attr(data, "$.data.room.fans_group_info")
    subscribe_data                   = get_dict_attr(data, "$.data.room.subscribe_data")
    user_attr_data                   = get_dict_attr(data, "$.data.room.user_attr_data")
    user_dress_info_data             = get_dict_attr(data, "$.data.room.user_dress_info_data")
    biz_relation_data                = get_dict_attr(data, "$.data.room.biz_relation_data")
    j_accredit_info_data             = get_dict_attr(data, "$.data.room.j_accredit_info_data")
    own_room_data                    = get_dict_attr(data, "$.data.room.own_room_data")
    total_recharge_diamond_count     = get_dict_attr(data, "$.data.room.total_recharge_diamond_count")
    watch_duration_month             = get_dict_attr(data, "$.data.room.watch_duration_month")
    web_rid                          = get_dict_attr(data, "$.data.room.web_rid")
    webcast_nick                     = get_dict_attr(data, "$.data.room.webcast_nick")
    webcast_uid                      = get_dict_attr(data, "$.data.room.webcast_uid")

    set_dict_attr(room_owner_v2_table_tuple, "$.room_id",                    str(room_id_ro))
    set_dict_attr(room_owner_v2_table_tuple, "$.user_id",                    str(user_id_ro))
    set_dict_attr(room_owner_v2_table_tuple, "$.owner_open_id",              owner_open_id_ro)
    set_dict_attr(room_owner_v2_table_tuple, "$.owner_device_id",            str(owner_device_id_ro))
    set_dict_attr(room_owner_v2_table_tuple, "$.sec_uid",                    sec_uid)
    set_dict_attr(room_owner_v2_table_tuple, "$.user_open_id",               user_open_id_ro)
    set_dict_attr(room_owner_v2_table_tuple, "$.short_id",                   short_id)
    set_dict_attr(room_owner_v2_table_tuple, "$.display_id",                 display_id)
    set_dict_attr(room_owner_v2_table_tuple, "$.nickname",                   nickname)
    set_dict_attr(room_owner_v2_table_tuple, "$.signature",                  signature)
    set_dict_attr(room_owner_v2_table_tuple, "$.share_qrcode_uri",           share_qrcode_uri)
    set_dict_attr(room_owner_v2_table_tuple, "$.special_id",                 special_id)
    set_dict_attr(room_owner_v2_table_tuple, "$.status",                     status_ro)
    set_dict_attr(room_owner_v2_table_tuple, "$.bg_img_url",                 bg_img_url)
    set_dict_attr(room_owner_v2_table_tuple, "$.gender",                     gender_ro)
    set_dict_attr(room_owner_v2_table_tuple, "$.city",                       city_ro)
    set_dict_attr(room_owner_v2_table_tuple, "$.constellation",              constellation)
    set_dict_attr(room_owner_v2_table_tuple, "$.age_range",                  age_range)
    set_dict_attr(room_owner_v2_table_tuple, "$.birthday",                   birthday)
    set_dict_attr(room_owner_v2_table_tuple, "$.birthday_description",       birthday_description)
    set_dict_attr(room_owner_v2_table_tuple, "$.birthday_valid",             birthday_valid)
    set_dict_attr(room_owner_v2_table_tuple, "$.location_city",              location_city)
    set_dict_attr(room_owner_v2_table_tuple, "$.foreign_user",               foreign_user)
    set_dict_attr(room_owner_v2_table_tuple, "$.mystery_man",                mystery_man)
    set_dict_attr(room_owner_v2_table_tuple, "$.level",                      level_ro)
    set_dict_attr(room_owner_v2_table_tuple, "$.exp",                        exp)
    set_dict_attr(room_owner_v2_table_tuple, "$.experience",                 experience)
    set_dict_attr(room_owner_v2_table_tuple, "$.fan_ticket_count",           fan_ticket_count)
    set_dict_attr(room_owner_v2_table_tuple, "$.consume_diamond_level",      consume_diamond_level)
    set_dict_attr(room_owner_v2_table_tuple, "$.income_share_percent",       income_share_percent)
    set_dict_attr(room_owner_v2_table_tuple, "$.link_mic_stats",             link_mic_stats)
    set_dict_attr(room_owner_v2_table_tuple, "$.media_badge_image_list",     json.dumps(media_badge_image_list_ro) if media_badge_image_list_ro else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.modify_time",                modify_time)
    set_dict_attr(room_owner_v2_table_tuple, "$.pay_score",                  pay_score)
    set_dict_attr(room_owner_v2_table_tuple, "$.pay_scores",                 pay_scores)
    set_dict_attr(room_owner_v2_table_tuple, "$.need_profile_guide",         need_profile_guide)
    set_dict_attr(room_owner_v2_table_tuple, "$.new_real_time_icons",        json.dumps(new_real_time_icons_ro) if new_real_time_icons_ro else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.real_time_icons",            json.dumps(real_time_icons_ro) if real_time_icons_ro else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.follow_status",              follow_status)
    set_dict_attr(room_owner_v2_table_tuple, "$.is_follower",                is_follower)
    set_dict_attr(room_owner_v2_table_tuple, "$.is_following",               is_following)
    set_dict_attr(room_owner_v2_table_tuple, "$.follow_info",                json.dumps(follow_info) if follow_info else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.is_anonymous",               is_anonymous)
    set_dict_attr(room_owner_v2_table_tuple, "$.hotsoon_verified",           hotsoon_verified)
    set_dict_attr(room_owner_v2_table_tuple, "$.hotsoon_verified_reason",    hotsoon_verified_reason)
    set_dict_attr(room_owner_v2_table_tuple, "$.ichat_restrict_type",        ichat_restrict_type)
    set_dict_attr(room_owner_v2_table_tuple, "$.disable_ichat",              disable_ichat)
    set_dict_attr(room_owner_v2_table_tuple, "$.enable_ichat_img",           enable_ichat_img)
    set_dict_attr(room_owner_v2_table_tuple, "$.fold_stranger_chat",         fold_stranger_chat)
    set_dict_attr(room_owner_v2_table_tuple, "$.desensitized_nickname",      desensitized_nickname)
    set_dict_attr(room_owner_v2_table_tuple, "$.verified",                   verified_ro)
    set_dict_attr(room_owner_v2_table_tuple, "$.verified_reason",            verified_reason)
    set_dict_attr(room_owner_v2_table_tuple, "$.verified_content",           verified_content)
    set_dict_attr(room_owner_v2_table_tuple, "$.verified_mobile",            verified_mobile)
    set_dict_attr(room_owner_v2_table_tuple, "$.enterprise_verify_reason",   enterprise_verify_reason)
    set_dict_attr(room_owner_v2_table_tuple, "$.custom_verify",              custom_verify)
    set_dict_attr(room_owner_v2_table_tuple, "$.block_status",               block_status)
    set_dict_attr(room_owner_v2_table_tuple, "$.comment_restrict",           comment_restrict)
    set_dict_attr(room_owner_v2_table_tuple, "$.public_area_oper_freq",      public_area_oper_freq)
    set_dict_attr(room_owner_v2_table_tuple, "$.secret",                     secret)
    set_dict_attr(room_owner_v2_table_tuple, "$.user_role",                  user_role)
    set_dict_attr(room_owner_v2_table_tuple, "$.webcast_private",            webcast_private)
    set_dict_attr(room_owner_v2_table_tuple, "$.can_view_webcast_private",   can_view_webcast_private)
    set_dict_attr(room_owner_v2_table_tuple, "$.user_canceled",              user_canceled)
    set_dict_attr(room_owner_v2_table_tuple, "$.telephone",                  telephone)
    set_dict_attr(room_owner_v2_table_tuple, "$.with_commerce_permission",   with_commerce_permission)
    set_dict_attr(room_owner_v2_table_tuple, "$.with_fusion_shop_entry",     with_fusion_shop_entry)
    set_dict_attr(room_owner_v2_table_tuple, "$.with_car_management_permission", with_car_management_permission)
    set_dict_attr(room_owner_v2_table_tuple, "$.adversary_authorization_info", adversary_authorization_info)
    set_dict_attr(room_owner_v2_table_tuple, "$.adversary_user_status",      adversary_user_status)
    set_dict_attr(room_owner_v2_table_tuple, "$.authorization_info",         authorization_info)
    set_dict_attr(room_owner_v2_table_tuple, "$.allow_be_located",           allow_be_located)
    set_dict_attr(room_owner_v2_table_tuple, "$.allow_find_by_contacts",     allow_find_by_contacts)
    set_dict_attr(room_owner_v2_table_tuple, "$.allow_others_download_video", allow_others_download_video)
    set_dict_attr(room_owner_v2_table_tuple, "$.allow_others_download_when_sharing_video", allow_others_download_when_sharing_video)
    set_dict_attr(room_owner_v2_table_tuple, "$.allow_share_show_profile",   allow_share_show_profile)
    set_dict_attr(room_owner_v2_table_tuple, "$.allow_show_in_gossip",       allow_show_in_gossip)
    set_dict_attr(room_owner_v2_table_tuple, "$.allow_show_my_action",       allow_show_my_action)
    set_dict_attr(room_owner_v2_table_tuple, "$.allow_strange_comment",      allow_strange_comment)
    set_dict_attr(room_owner_v2_table_tuple, "$.allow_unfollower_comment",   allow_unfollower_comment)
    set_dict_attr(room_owner_v2_table_tuple, "$.allow_use_linkmic",          allow_use_linkmic)
    set_dict_attr(room_owner_v2_table_tuple, "$.remark_name",                remark_name)

    ## JSON 扩展字段
    set_dict_attr(room_owner_v2_table_tuple, "$.avatar_large",              json.dumps(avatar_large) if avatar_large else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.avatar_medium",             json.dumps(avatar_medium) if avatar_medium else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.avatar_thumb",              json.dumps(avatar_thumb) if avatar_thumb else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.badge_image_list",          json.dumps(badge_image_list) if badge_image_list else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.badge_image_list_v2",       json.dumps(badge_image_list_v2) if badge_image_list_v2 else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.commerce_webcast_config_ids", json.dumps(commerce_webcast_config_ids) if commerce_webcast_config_ids else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.authentication_info",       json.dumps(authentication_info) if authentication_info else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.border_data",               json.dumps(border_data) if border_data else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.pay_grade_data",            json.dumps(pay_grade_data) if pay_grade_data else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.fans_club_data",            json.dumps(fans_club_data) if fans_club_data else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.fans_group_info",           json.dumps(fans_group_info) if fans_group_info else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.subscribe_data",            json.dumps(subscribe_data) if subscribe_data else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.user_attr_data",            json.dumps(user_attr_data) if user_attr_data else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.user_dress_info_data",      json.dumps(user_dress_info_data) if user_dress_info_data else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.biz_relation_data",         json.dumps(biz_relation_data) if biz_relation_data else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.j_accredit_info_data",      json.dumps(j_accredit_info_data) if j_accredit_info_data else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.own_room_data",             json.dumps(own_room_data) if own_room_data else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.total_recharge_diamond_count", total_recharge_diamond_count)
    set_dict_attr(room_owner_v2_table_tuple, "$.watch_duration_month",      watch_duration_month)
    set_dict_attr(room_owner_v2_table_tuple, "$.web_rid",                   web_rid)
    set_dict_attr(room_owner_v2_table_tuple, "$.webcast_nick",              webcast_nick)
    set_dict_attr(room_owner_v2_table_tuple, "$.webcast_uid",               webcast_uid)

    room_owner_v2_table.insert_record(room_owner_v2_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_owner_v2_table.get_name(), e))
    raise e
