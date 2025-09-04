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

## <<Extension>>

## <<Third-Part>>
from backend.src.library.baselib                                      import   load_yml, get_dict_attr, set_dict_attr
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
  ##
  ## common elements
  ##
  now             = dat.fromtimestamp(get_dict_attr(data, "$.extra.now")/1000.0)
  DOUYIN_PLATFORM = "douyin"
  room_id         = get_dict_attr(data, "$.data.room.id")
  user_id         = get_dict_attr(data, "$.data.user.id")
  start_time      = get_dict_attr(data, "$.data.room.start_time")
  finish_time     = get_dict_attr(data, "$.data.room.finish_time")
  status_code     = get_dict_attr(data, "$.status_code")

  ##
  ## LiveRecordTable
  ## 
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
    live_record_table = LiveRecordTable(db)
    live_record_table_tuple = live_record_table.get_tuple()
    set_dict_attr(live_record_table_tuple, "$.now", now)
    set_dict_attr(live_record_table_tuple, "$.platform", DOUYIN_PLATFORM)
    set_dict_attr(live_record_table_tuple, "$.room_id", room_id)
    set_dict_attr(live_record_table_tuple, "$.user_id", user_id)
    set_dict_attr(live_record_table_tuple, "$.start_time", start_time)
    set_dict_attr(live_record_table_tuple, "$.finish_time", finish_time)
    set_dict_attr(live_record_table_tuple, "$.status_code", status_code)
    
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

  ##
  ## RoomAttributeTable
  ##
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
    room_attribute_table = RoomAttributeTable(db)
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
    owner_device_id               = get_dict_attr(data, "$.data.room.owner.owner_device_id")
    owner_open_id                 = get_dict_attr(data, "$.data.room.owner.owner_open_id")
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

    set_dict_attr(room_attribute_table_tuple, "$.AnchorABMap",                   AnchorABMap)
    set_dict_attr(room_attribute_table_tuple, "$.acquaintance_status",           acquaintance_status)
    set_dict_attr(room_attribute_table_tuple, "$.anchor_scheduled_time_text",    anchor_scheduled_time_text)
    set_dict_attr(room_attribute_table_tuple, "$.anchor_share_text",             anchor_share_text)
    set_dict_attr(room_attribute_table_tuple, "$.anchor_tab_type",               anchor_tab_type)
    set_dict_attr(room_attribute_table_tuple, "$.app_id",                        str(app_id))
    set_dict_attr(room_attribute_table_tuple, "$.auth_city",                     auth_city)
    set_dict_attr(room_attribute_table_tuple, "$.auto_cover",                    auto_cover)
    set_dict_attr(room_attribute_table_tuple, "$.base_category",                 base_category)
    set_dict_attr(room_attribute_table_tuple, "$.book_end_time",                 dat.fromtimestamp(book_end_time))
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
    set_dict_attr(room_attribute_table_tuple, "$.create_time",                   create_time)
    set_dict_attr(room_attribute_table_tuple, "$.distance",                      distance)
    set_dict_attr(room_attribute_table_tuple, "$.distance_city",                 distance_city)
    set_dict_attr(room_attribute_table_tuple, "$.distance_km",                   distance_km)
    set_dict_attr(room_attribute_table_tuple, "$.dynamic_cover_dict",            dynamic_cover_dict)
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
  except Exception as e:
    get_logger().error("insert RoomAttributeTable failed: {}".format(e))

  ##
  ## RoomAdminUserIdTable
  ##
  try:
    now = get_dict_attr(data, "$.data.room.create_time")
    # platform
    # room_id = get_dict_attr(data, "$.data.room.id")
    # admin_user_id_index = None
    admin_user_id = get_dict_attr(data, "$.data.room.admin_user_ids")
  except Exception as e:
    get_logger().error("insert RoomAdminUserIdTable failed: {}".format(e))

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
  data = load_yml(Path('/mnt/code_space/SocialMediaStreamDownloader/docs/design/Lvuuu.yml'))
  
  ##
  ## parse living data
  ##
  living_data = get_dict_attr(data, "$.external_info")
  
  ##
  ## import living data to database
  ##
  db = SocialMediaStreamDataBase(host='192.168.1.12', user='wangyan', passwd='wuyu1998', database='social_media_stream_downloader')
  import_douyin_live_info_to_database(living_data)
  

if __name__ == "__main__":
  test_import_live_info_to_database()