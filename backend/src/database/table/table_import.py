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
from backend.src.library.loglib                                       import   get_logger
from backend.src.database.social_media_stream_database                import   SocialMediaStreamDataBase
from backend.src.database.table.live                                  import   LiveRecordTable
from backend.src.database.table.room                                  import   RoomAdminUserIdTable,                                \
                                                                               RoomAdminUserOpenIdTable,                            \
                                                                               RoomStatsTable,                                      \
                                                                               RoomDecoTable,                                       \
                                                                               FansGroupAdminUserIdTable,                           \
                                                                               FansGroupAdminUserOpenIdTable
from backend.src.database.table.room_base                             import   RoomBaseTable
from backend.src.database.table.room_owner                            import   RoomOwnerV2Table
from backend.src.database.table.user                                  import   UserTable

def import_douyin_live_record_to_database(db:SocialMediaStreamDataBase, data:dict) -> None:
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
    set_dict_attr(live_record_table_tuple,   "$.room_id",       str(room_id) if room_id is not None else None)
    set_dict_attr(live_record_table_tuple,   "$.owner_user_id", str(owner_user_id) if owner_user_id is not None else None)
    set_dict_attr(live_record_table_tuple,   "$.user_id",       str(user_id) if user_id is not None else None)
    if start_time not in (None, 0):
      set_dict_attr(live_record_table_tuple, "$.start_time",    dat.fromtimestamp(start_time))
    if finish_time not in (None, 0):
      set_dict_attr(live_record_table_tuple, "$.finish_time",   dat.fromtimestamp(finish_time))
    set_dict_attr(live_record_table_tuple,   "$.status_code",   status_code)
    live_record_table.insert_record(live_record_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert LiveRecordTable failed: {}".format(e))
    raise e

def import_douyin_room_stats_to_database(db:SocialMediaStreamDataBase, data:dict) -> None:
  now             = dat.fromtimestamp(get_dict_attr(data, "$.extra.now")/1000.0)
  DOUYIN_PLATFORM = "douyin"
  room_id         = get_dict_attr(data, "$.data.room.id")

  ##
  ## RoomStatsTable
  ##
  room_stats_table = RoomStatsTable(db)
  try:
    ##
    ## create the table if not exist
    ##
    if db.is_table_exist(room_stats_table.get_name()) is False:
      room_stats_table.create()
    room_stats_table_tuple = {key:None for key in room_stats_table.get_tuple()}
    
    DOUYIN_PLATFORM = "douyin"
    room_id         = get_dict_attr(data,    "$.data.room.id")
    room_stats      = get_dict_attr(data,    "$.data.room.stats") or {}
    
    set_dict_attr(room_stats_table_tuple, "$.now",                                 now)
    set_dict_attr(room_stats_table_tuple, "$.platform",                            DOUYIN_PLATFORM)
    set_dict_attr(room_stats_table_tuple, "$.room_id",                             str(room_id) if room_id is not None else None)
    set_dict_attr(room_stats_table_tuple, "$.comment_count",                       get_dict_attr(room_stats, "$.comment_count"))
    set_dict_attr(room_stats_table_tuple, "$.digg_count",                          get_dict_attr(room_stats, "$.digg_count"))
    set_dict_attr(room_stats_table_tuple, "$.dou_plus_promotion",                  get_dict_attr(room_stats, "$.dou_plus_promotion"))
    set_dict_attr(room_stats_table_tuple, "$.enter_count",                         get_dict_attr(room_stats, "$.enter_count"))
    set_dict_attr(room_stats_table_tuple, "$.fan_ticket",                          get_dict_attr(room_stats, "$.fan_ticket"))
    set_dict_attr(room_stats_table_tuple, "$.follow_count",                        get_dict_attr(room_stats, "$.follow_count"))
    set_dict_attr(room_stats_table_tuple, "$.gift_uv_count",                       get_dict_attr(room_stats, "$.gift_uv_count"))
    set_dict_attr(room_stats_table_tuple, "$.like_count",                          get_dict_attr(room_stats, "$.like_count"))
    set_dict_attr(room_stats_table_tuple, "$.money",                               get_dict_attr(room_stats, "$.money"))
    set_dict_attr(room_stats_table_tuple, "$.total_user",                          get_dict_attr(room_stats, "$.total_user"))
    set_dict_attr(room_stats_table_tuple, "$.total_user_desp",                     get_dict_attr(room_stats, "$.total_user_desp"))
    set_dict_attr(room_stats_table_tuple, "$.total_user_str",                      get_dict_attr(room_stats, "$.total_user_str"))
    set_dict_attr(room_stats_table_tuple, "$.up_right_stats_str",                  get_dict_attr(room_stats, "$.up_right_stats_str"))
    set_dict_attr(room_stats_table_tuple, "$.up_right_stats_str_complete",         get_dict_attr(room_stats, "$.up_right_stats_str_complete"))
    set_dict_attr(room_stats_table_tuple, "$.user_count_str",                      get_dict_attr(room_stats, "$.user_count_str"))
    set_dict_attr(room_stats_table_tuple, "$.watermelon",                          get_dict_attr(room_stats, "$.watermelon"))
    set_dict_attr(room_stats_table_tuple, "$.welfare_donation_amount",             get_dict_attr(room_stats, "$.welfare_donation_amount"))
    set_dict_attr(room_stats_table_tuple, "$.user_count_composition_city",         get_dict_attr(room_stats, "$.user_count_composition.city"))
    set_dict_attr(room_stats_table_tuple, "$.user_count_composition_my_follow",    get_dict_attr(room_stats, "$.user_count_composition.my_follow"))
    set_dict_attr(room_stats_table_tuple, "$.user_count_composition_other",        get_dict_attr(room_stats, "$.user_count_composition.other"))
    set_dict_attr(room_stats_table_tuple, "$.user_count_composition_video_detail", get_dict_attr(room_stats, "$.user_count_composition.video_detail"))

    room_stats_table.insert_record(room_stats_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert RoomStatsTable failed: {}".format(e))
    raise e

def import_douyin_room_admin_user_id_to_database(db:SocialMediaStreamDataBase, data:dict) -> None:
  now             = dat.fromtimestamp(get_dict_attr(data, "$.extra.now")/1000.0)
  DOUYIN_PLATFORM = "douyin"
  room_id         = get_dict_attr(data, "$.data.room.id")

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
    room_admin_user_id_table_tuple = {key:None for key in room_admin_user_id_table.get_tuple()}

    room_id = get_dict_attr(data, "$.data.room.id")
    admin_user_ids = get_dict_attr(data, "$.data.room.admin_user_ids")
    if admin_user_ids is None:
      admin_user_ids = []
    elif isinstance(admin_user_ids, list) is False:
      admin_user_ids = [admin_user_ids]

    if len(admin_user_ids) != 0 and room_id is not None:
      set_dict_attr(room_admin_user_id_table_tuple, "$.platform", DOUYIN_PLATFORM)
      set_dict_attr(room_admin_user_id_table_tuple, "$.room_id",  str(room_id))
      for admin_user_id in admin_user_ids:
        if admin_user_id in (None, ""):
          continue
        set_dict_attr(room_admin_user_id_table_tuple, "$.admin_user_id", str(admin_user_id))
        room_admin_user_id_table.insert_record(room_admin_user_id_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_admin_user_id_table.get_name(), e))
    raise e

def import_douyin_room_admin_user_open_id_to_database(db:SocialMediaStreamDataBase, data:dict) -> None:
  now             = dat.fromtimestamp(get_dict_attr(data, "$.extra.now")/1000.0)
  DOUYIN_PLATFORM = "douyin"
  room_id         = get_dict_attr(data, "$.data.room.id")

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
    room_admin_user_open_id_table_tuple = {key:None for key in room_admin_user_open_id_table.get_tuple()}

    room_id = get_dict_attr(data, "$.data.room.id")
    admin_user_open_ids = get_dict_attr(data, "$.data.room.admin_user_open_ids")
    if admin_user_open_ids is None:
      admin_user_open_ids = []
    elif isinstance(admin_user_open_ids, list) is False:
      admin_user_open_ids = [admin_user_open_ids]

    if len(admin_user_open_ids) != 0 and room_id is not None:
      set_dict_attr(room_admin_user_open_id_table_tuple, "$.platform", DOUYIN_PLATFORM)
      set_dict_attr(room_admin_user_open_id_table_tuple, "$.room_id",  str(room_id))
      for admin_user_open_id in admin_user_open_ids:
        if admin_user_open_id in (None, ""):
          continue
        set_dict_attr(room_admin_user_open_id_table_tuple, "$.admin_user_open_id", str(admin_user_open_id))
        room_admin_user_open_id_table.insert_record(room_admin_user_open_id_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_admin_user_open_id_table.get_name(), e))
    raise e

def import_douyin_room_deco_to_database(db:SocialMediaStreamDataBase, data:dict) -> None:
  now             = dat.fromtimestamp(get_dict_attr(data, "$.extra.now")/1000.0)
  DOUYIN_PLATFORM = "douyin"
  room_id         = get_dict_attr(data, "$.data.room.id")

  ##
  ##  RoomDecoTable
  ##
  room_deco_table = RoomDecoTable(db)  
  room_id = get_dict_attr(data, "$.data.room.id")
  deco_list = get_dict_attr(data, "$.data.room.deco_list")
  if deco_list is None:
      deco_list = []
  elif isinstance(deco_list, list) is False:
      deco_list = [deco_list]

  if len(deco_list) != 0 and room_id is not None:
      for deco_index in range(0, len(deco_list)):
        deco_data = deco_list[deco_index]
        if isinstance(deco_data, dict) is False:
          continue
        try:
          ##
          ## create the table if not exist
          ##
          if db.is_table_exist(room_deco_table.get_name()) is False:
            room_deco_table.create()
          room_deco_table_tuple = {key:None for key in room_deco_table.get_tuple()}

          set_dict_attr(room_deco_table_tuple, "$.platform",                             DOUYIN_PLATFORM)
          set_dict_attr(room_deco_table_tuple, "$.room_id",                              str(room_id))
          set_dict_attr(room_deco_table_tuple, "$.deco_id",                              get_dict_attr(deco_data,            "$.id"))
          set_dict_attr(room_deco_table_tuple, "$.deco_type",                            get_dict_attr(deco_data,            "$.type"))
          set_dict_attr(room_deco_table_tuple, "$.kind",                                 get_dict_attr(deco_data,            "$.kind"))
          set_dict_attr(room_deco_table_tuple, "$.audit_text_color",                     get_dict_attr(deco_data,            "$.audit_text_color"))
          set_dict_attr(room_deco_table_tuple, "$.content",                              get_dict_attr(deco_data,            "$.content"))
          set_dict_attr(room_deco_table_tuple, "$.status",                               get_dict_attr(deco_data,            "$.status"))
          set_dict_attr(room_deco_table_tuple, "$.text_color",                           get_dict_attr(deco_data,            "$.text_color"))
          set_dict_attr(room_deco_table_tuple, "$.text_size",                            get_dict_attr(deco_data,            "$.text_size"))
          set_dict_attr(room_deco_table_tuple, "$.position_x",                           get_dict_attr(deco_data,            "$.x"))
          set_dict_attr(room_deco_table_tuple, "$.position_y",                           get_dict_attr(deco_data,            "$.y"))
          set_dict_attr(room_deco_table_tuple, "$.width",                                get_dict_attr(deco_data,            "$.w"))
          set_dict_attr(room_deco_table_tuple, "$.height",                               get_dict_attr(deco_data,            "$.h"))
          set_dict_attr(room_deco_table_tuple, "$.max_length",                           get_dict_attr(deco_data,            "$.max_length"))
          set_dict_attr(room_deco_table_tuple, "$.sub_type",                             get_dict_attr(deco_data,            "$.sub_type"))
          set_dict_attr(room_deco_table_tuple, "$.text_image_adjustable_start_position", get_dict_attr(deco_data,            "$.text_image_adjustable_start_position"))
          set_dict_attr(room_deco_table_tuple, "$.text_image_adjustable_end_position",   get_dict_attr(deco_data,            "$.text_image_adjustable_end_position"))
          set_dict_attr(room_deco_table_tuple, "$.input_rect",                           json.dumps(get_dict_attr(deco_data, "$.input_rect")) if get_dict_attr(deco_data, "$.input_rect") is not None else None)
          set_dict_attr(room_deco_table_tuple, "$.nine_patch_image",                     json.dumps(get_dict_attr(deco_data, "$.nine_patch_image")) if get_dict_attr(deco_data, "$.nine_patch_image") is not None else None)
          set_dict_attr(room_deco_table_tuple, "$.reservation",                          json.dumps(get_dict_attr(deco_data, "$.reservation")) if get_dict_attr(deco_data, "$.reservation") is not None else None)
          set_dict_attr(room_deco_table_tuple, "$.text_font_config",                     json.dumps(get_dict_attr(deco_data, "$.text_font_config")) if get_dict_attr(deco_data, "$.text_font_config") is not None else None)
          set_dict_attr(room_deco_table_tuple, "$.text_special_effects",                 json.dumps(get_dict_attr(deco_data, "$.text_special_effects")) if get_dict_attr(deco_data, "$.text_special_effects") is not None else None)
          set_dict_attr(room_deco_table_tuple, "$.image_data",                           json.dumps(get_dict_attr(deco_data, "$.image")) if get_dict_attr(deco_data, "$.image") is not None else None)

          room_deco_table.insert_record(room_deco_table_tuple, on_duplicate='ignore')
        except Exception as e:
          get_logger().error("insert {} failed: {}".format(room_deco_table.get_name(), e))
          raise e

        ##
        ## NOTE:
        ## input_rect / reservation are stored as JSON columns in room_deco table.
        ## Legacy split-table logic has been removed because those table instances
        ## no longer exist in the current schema.
        ##

def import_douyin_fans_group_admin_user_id_to_database(db:SocialMediaStreamDataBase, data:dict) -> None:
  now             = dat.fromtimestamp(get_dict_attr(data, "$.extra.now")/1000.0)
  DOUYIN_PLATFORM = "douyin"
  room_id         = get_dict_attr(data, "$.data.room.id")

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
    fans_group_admin_user_id_table_tuple = {key:None for key in fans_group_admin_user_id_table.get_tuple()}

    room_id = get_dict_attr(data, "$.data.room.id")
    fans_group_admin_user_ids = get_dict_attr(data, "$.data.room.fans_group_admin_user_ids")
    if fans_group_admin_user_ids is None:
      fans_group_admin_user_ids = []
    elif isinstance(fans_group_admin_user_ids, list) is False:
      fans_group_admin_user_ids = [fans_group_admin_user_ids]

    if len(fans_group_admin_user_ids) != 0 and room_id is not None:
      set_dict_attr(fans_group_admin_user_id_table_tuple, "$.platform", DOUYIN_PLATFORM)
      set_dict_attr(fans_group_admin_user_id_table_tuple, "$.room_id",  str(room_id))
      for fans_group_admin_user_id in fans_group_admin_user_ids:
        if fans_group_admin_user_id in (None, ""):
          continue
        set_dict_attr(fans_group_admin_user_id_table_tuple, "$.fans_group_admin_user_id", str(fans_group_admin_user_id))

        fans_group_admin_user_id_table.insert_record(fans_group_admin_user_id_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(fans_group_admin_user_id_table.get_name(), e))
    raise e

def import_douyin_fans_group_admin_user_open_id_to_database(db:SocialMediaStreamDataBase, data:dict) -> None:
  now             = dat.fromtimestamp(get_dict_attr(data, "$.extra.now")/1000.0)
  DOUYIN_PLATFORM = "douyin"
  room_id         = get_dict_attr(data, "$.data.room.id")

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
    fans_group_admin_user_open_id_table_tuple = {key:None for key in fans_group_admin_user_open_id_table.get_tuple()}

    room_id = get_dict_attr(data, "$.data.room.id")
    fans_group_admin_user_open_id_list = get_dict_attr(data, "$.data.room.fans_group_admin_user_open_ids")
    if fans_group_admin_user_open_id_list is None:
      fans_group_admin_user_open_id_list = []
    elif isinstance(fans_group_admin_user_open_id_list, list) is False:
      fans_group_admin_user_open_id_list = [fans_group_admin_user_open_id_list]

    if len(fans_group_admin_user_open_id_list) != 0 and room_id is not None:
      set_dict_attr(fans_group_admin_user_open_id_table_tuple, "$.platform", DOUYIN_PLATFORM)
      set_dict_attr(fans_group_admin_user_open_id_table_tuple, "$.room_id",  str(room_id))
      for fans_group_admin_user_open_id in fans_group_admin_user_open_id_list:
        if fans_group_admin_user_open_id in (None, ""):
          continue
        set_dict_attr(fans_group_admin_user_open_id_table_tuple, "$.fans_group_admin_user_open_id", str(fans_group_admin_user_open_id))

        fans_group_admin_user_open_id_table.insert_record(fans_group_admin_user_open_id_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(fans_group_admin_user_open_id_table.get_name(), e))
    raise e

def import_douyin_room_base_to_database(db:SocialMediaStreamDataBase, data:dict) -> None:
  now             = dat.fromtimestamp(get_dict_attr(data, "$.extra.now")/1000.0)
  DOUYIN_PLATFORM = "douyin"
  room_id         = get_dict_attr(data, "$.data.room.id")

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
    room_owner_data                  = get_dict_attr(data, "$.data.room.owner")
    if isinstance(room_owner_data, dict) is False:
      room_owner_data = {}
    owner_device_id_rb               = get_dict_attr(data, "$.data.room.owner_device_id")
    owner_open_id_rb                 = get_dict_attr(data, "$.data.room.owner_open_id")
    if owner_device_id_rb is None:
      owner_device_id_rb = get_dict_attr(room_owner_data, "$.owner_device_id")
    if owner_open_id_rb is None:
      owner_open_id_rb = get_dict_attr(room_owner_data, "$.owner_open_id")
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
    like_count_rb                    = get_dict_attr(data, "$.data.room.like_count")
    user_count_rb                    = get_dict_attr(data, "$.data.room.user_count")
    popularity_rb                    = get_dict_attr(data, "$.data.room.popularity")
    sell_goods_rb                    = get_dict_attr(data, "$.data.room.sell_goods")
    has_commerce_goods_rb            = get_dict_attr(data, "$.data.room.has_commerce_goods")
    is_replay_rb                     = get_dict_attr(data, "$.data.room.is_replay")
    replay_rb                        = get_dict_attr(data, "$.data.room.replay")
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
    private_info_rb                  = get_dict_attr(data, "$.data.room.private_info")
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
    sun_daily_icon_content           = get_dict_attr(data, "$.data.room.sun_daily_icon_content")
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
    cover                            = get_dict_attr(data, "$.data.room.cover")
    if cover is None:
      cover = get_dict_attr(data, "$.data.room.cover_data")
    content_label                    = get_dict_attr(data, "$.data.room.content_label")
    if content_label is None:
      content_label = get_dict_attr(data, "$.data.room.content_label_data")
    feed_room_label                  = get_dict_attr(data, "$.data.room.feed_room_label")
    if feed_room_label is None:
      feed_room_label = get_dict_attr(data, "$.data.room.feed_room_label_data")
    guide_button                     = get_dict_attr(data, "$.data.room.guide_button")
    if guide_button is None:
      guide_button = get_dict_attr(data, "$.data.room.guide_button_data")
    comment_box                      = get_dict_attr(data, "$.data.room.comment_box")
    if comment_box is None:
      comment_box = get_dict_attr(data, "$.data.room.comment_box_data")
    link_mic                         = get_dict_attr(data, "$.data.room.link_mic")
    if link_mic is None:
      link_mic = get_dict_attr(data, "$.data.room.link_mic_data")
    living_room_attrs                = get_dict_attr(data, "$.data.room.living_room_attrs")
    if living_room_attrs is None:
      living_room_attrs = get_dict_attr(data, "$.data.room.living_room_attrs_data")
    pack_meta                        = get_dict_attr(data, "$.data.room.pack_meta")
    if pack_meta is None:
      pack_meta = get_dict_attr(data, "$.data.room.pack_meta_data")
    paid_live_data                   = get_dict_attr(data, "$.data.room.paid_live_data")
    room_view_stats                  = get_dict_attr(data, "$.data.room.room_view_stats")
    if room_view_stats is None:
      room_view_stats = get_dict_attr(data, "$.data.room.view_stats_data")
    extra                            = get_dict_attr(data, "$.data.room.extra")
    if extra is None:
      extra = get_dict_attr(data, "$.data.room.extra_data")
    room_auth                        = get_dict_attr(data, "$.data.room.room_auth")
    if room_auth is None:
      room_auth = get_dict_attr(data, "$.data.room.room_auth_data")
    short_touch_area_config          = get_dict_attr(data, "$.data.room.short_touch_area_config")
    if short_touch_area_config is None:
      short_touch_area_config = get_dict_attr(data, "$.data.room.short_touch_config_data")
    stream_url                       = get_dict_attr(data, "$.data.room.stream_url")
    if stream_url is None:
      stream_url = get_dict_attr(data, "$.data.room.stream_url_data")
    stats                            = get_dict_attr(data, "$.data.room.stats")
    if stats is None:
      stats = get_dict_attr(data, "$.data.room.stats_data")
    owner_json                       = get_dict_attr(data, "$.data.room.owner")
    official_channel_json            = get_dict_attr(data, "$.data.room.official_channel")

    ## JSON 数组字段
    admin_user_ids_rb                = get_dict_attr(data, "$.data.room.admin_user_ids")
    admin_user_open_ids              = get_dict_attr(data, "$.data.room.admin_user_open_ids")
    deco_list_rb                     = get_dict_attr(data, "$.data.room.deco_list")
    fans_group_admin_user_ids        = get_dict_attr(data, "$.data.room.fans_group_admin_user_ids")
    fans_group_admin_user_open_ids   = get_dict_attr(data, "$.data.room.fans_group_admin_user_open_ids")
    filter_words_rb                  = get_dict_attr(data, "$.data.room.filter_words")
    live_distribution_rb             = get_dict_attr(data, "$.data.room.live_distribution")
    sharing_music_id_list            = get_dict_attr(data, "$.data.room.sharing_music_id_list")
    tags_rb                          = get_dict_attr(data, "$.data.room.tags")
    top_fans_rb                      = get_dict_attr(data, "$.data.room.top_fans")
    upper_right_widget_data_list     = get_dict_attr(data, "$.data.room.upper_right_widget_data_list")
    vs_roles_rb                      = get_dict_attr(data, "$.data.room.vs_roles")
    room_tabs                        = get_dict_attr(data, "$.data.room.room_tabs")
    assist_label_list                = get_dict_attr(data, "$.data.room.assist_label_list")
    anchor_ab_map_rb                 = get_dict_attr(data, "$.data.room.AnchorABMap")
    linker_map                       = get_dict_attr(data, "$.data.room.linker_map")
    dynamic_cover_dict_rb            = get_dict_attr(data, "$.data.room.dynamic_cover_dict")

    if id is None:
      id = room_id
    if id_str is None and id is not None:
      id_str = str(id)

    set_dict_attr(room_base_table_tuple, "$.now",                           now)
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
    set_dict_attr(room_base_table_tuple, "$.owner_device_id",               owner_device_id_rb if owner_device_id_rb is not None else None)
    set_dict_attr(room_base_table_tuple, "$.owner_open_id",                 owner_open_id_rb)
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
    set_dict_attr(room_base_table_tuple, "$.like_count",                    like_count_rb)
    set_dict_attr(room_base_table_tuple, "$.user_count",                    user_count_rb)
    set_dict_attr(room_base_table_tuple, "$.popularity",                    popularity_rb)
    set_dict_attr(room_base_table_tuple, "$.sell_goods",                    sell_goods_rb)
    set_dict_attr(room_base_table_tuple, "$.has_commerce_goods",            has_commerce_goods_rb)
    set_dict_attr(room_base_table_tuple, "$.is_replay",                     is_replay_rb)
    set_dict_attr(room_base_table_tuple, "$.replay",                        replay_rb)
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
    set_dict_attr(room_base_table_tuple, "$.private_info",                  private_info_rb)
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
    set_dict_attr(room_base_table_tuple, "$.sun_daily_icon_content",        sun_daily_icon_content)
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
    set_dict_attr(room_base_table_tuple, "$.cover",                         json.dumps(cover) if cover is not None else None)
    set_dict_attr(room_base_table_tuple, "$.content_label",                 json.dumps(content_label) if content_label is not None else None)
    set_dict_attr(room_base_table_tuple, "$.feed_room_label",               json.dumps(feed_room_label) if feed_room_label is not None else None)
    set_dict_attr(room_base_table_tuple, "$.guide_button",                  json.dumps(guide_button) if guide_button is not None else None)
    set_dict_attr(room_base_table_tuple, "$.comment_box",                   json.dumps(comment_box) if comment_box is not None else None)
    set_dict_attr(room_base_table_tuple, "$.link_mic",                      json.dumps(link_mic) if link_mic is not None else None)
    set_dict_attr(room_base_table_tuple, "$.living_room_attrs",             json.dumps(living_room_attrs) if living_room_attrs is not None else None)
    set_dict_attr(room_base_table_tuple, "$.pack_meta",                     json.dumps(pack_meta) if pack_meta is not None else None)
    set_dict_attr(room_base_table_tuple, "$.paid_live_data",                json.dumps(paid_live_data) if paid_live_data is not None else None)
    set_dict_attr(room_base_table_tuple, "$.room_view_stats",               json.dumps(room_view_stats) if room_view_stats is not None else None)
    set_dict_attr(room_base_table_tuple, "$.extra",                         json.dumps(extra) if extra is not None else None)
    set_dict_attr(room_base_table_tuple, "$.room_auth",                     json.dumps(room_auth) if room_auth is not None else None)
    set_dict_attr(room_base_table_tuple, "$.short_touch_area_config",       json.dumps(short_touch_area_config) if short_touch_area_config is not None else None)
    set_dict_attr(room_base_table_tuple, "$.stream_url",                    json.dumps(stream_url) if stream_url is not None else None)
    set_dict_attr(room_base_table_tuple, "$.stats",                         json.dumps(stats) if stats is not None else None)
    set_dict_attr(room_base_table_tuple, "$.owner",                         json.dumps(owner_json) if owner_json is not None else None)
    set_dict_attr(room_base_table_tuple, "$.official_channel",              json.dumps(official_channel_json) if official_channel_json is not None else None)

    ## JSON 数组字段
    set_dict_attr(room_base_table_tuple, "$.admin_user_ids",                json.dumps(admin_user_ids_rb) if admin_user_ids_rb is not None else None)
    set_dict_attr(room_base_table_tuple, "$.admin_user_open_ids",           json.dumps(admin_user_open_ids) if admin_user_open_ids is not None else None)
    set_dict_attr(room_base_table_tuple, "$.deco_list",                     json.dumps(deco_list_rb) if deco_list_rb is not None else None)
    set_dict_attr(room_base_table_tuple, "$.fans_group_admin_user_ids",     json.dumps(fans_group_admin_user_ids) if fans_group_admin_user_ids is not None else None)
    set_dict_attr(room_base_table_tuple, "$.fans_group_admin_user_open_ids",json.dumps(fans_group_admin_user_open_ids) if fans_group_admin_user_open_ids is not None else None)
    set_dict_attr(room_base_table_tuple, "$.filter_words",                  json.dumps(filter_words_rb) if filter_words_rb is not None else None)
    set_dict_attr(room_base_table_tuple, "$.live_distribution",             json.dumps(live_distribution_rb) if live_distribution_rb is not None else None)
    set_dict_attr(room_base_table_tuple, "$.sharing_music_id_list",         json.dumps(sharing_music_id_list) if sharing_music_id_list is not None else None)
    set_dict_attr(room_base_table_tuple, "$.tags",                          json.dumps(tags_rb) if tags_rb is not None else None)
    set_dict_attr(room_base_table_tuple, "$.top_fans",                      json.dumps(top_fans_rb) if top_fans_rb is not None else None)
    set_dict_attr(room_base_table_tuple, "$.upper_right_widget_data_list",  json.dumps(upper_right_widget_data_list) if upper_right_widget_data_list is not None else None)
    set_dict_attr(room_base_table_tuple, "$.vs_roles",                      json.dumps(vs_roles_rb) if vs_roles_rb is not None else None)
    set_dict_attr(room_base_table_tuple, "$.room_tabs",                     json.dumps(room_tabs) if room_tabs is not None else None)
    set_dict_attr(room_base_table_tuple, "$.assist_label_list",             json.dumps(assist_label_list) if assist_label_list is not None else None)
    set_dict_attr(room_base_table_tuple, "$.AnchorABMap",                   json.dumps(anchor_ab_map_rb) if anchor_ab_map_rb is not None else None)
    set_dict_attr(room_base_table_tuple, "$.linker_map",                    json.dumps(linker_map) if linker_map is not None else None)
    set_dict_attr(room_base_table_tuple, "$.dynamic_cover_dict",            json.dumps(dynamic_cover_dict_rb) if dynamic_cover_dict_rb is not None else None)

    if id is not None and start_time_rb not in (None, 0):
      room_base_table.insert_record(room_base_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_base_table.get_name(), e))
    raise e

def import_douyin_room_owner_v2_to_database(db:SocialMediaStreamDataBase, data:dict) -> None:
  now             = dat.fromtimestamp(get_dict_attr(data, "$.extra.now")/1000.0)
  DOUYIN_PLATFORM = "douyin"
  room_id         = get_dict_attr(data, "$.data.room.id")

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
    room_owner_v2_table_tuple = {key:None for key in room_owner_v2_table.get_tuple()}

    owner_data = get_dict_attr(data, "$.data.room.owner")
    if isinstance(owner_data, dict) is False:
      owner_data = {}

    room_id_ro                               = get_dict_attr(data, "$.data.room.id")
    user_id_ro                               = get_dict_attr(owner_data, "$.id")
    owner_open_id_ro                         = get_dict_attr(owner_data, "$.owner_open_id")
    owner_device_id_ro                       = get_dict_attr(owner_data, "$.owner_device_id")
    sec_uid                                  = get_dict_attr(owner_data, "$.sec_uid")
    user_open_id_ro                          = get_dict_attr(owner_data, "$.user_open_id")
    short_id                                 = get_dict_attr(owner_data, "$.short_id")
    display_id                               = get_dict_attr(owner_data, "$.display_id")
    nickname                                 = get_dict_attr(owner_data, "$.nickname")
    signature                                = get_dict_attr(owner_data, "$.signature")
    share_qrcode_uri                         = get_dict_attr(owner_data, "$.share_qrcode_uri")
    special_id                               = get_dict_attr(owner_data, "$.special_id")
    status_ro                                = get_dict_attr(owner_data, "$.status")
    bg_img_url                               = get_dict_attr(owner_data, "$.bg_img_url")
    gender_ro                                = get_dict_attr(owner_data, "$.gender")
    city_ro                                  = get_dict_attr(owner_data, "$.city")
    constellation                            = get_dict_attr(owner_data, "$.constellation")
    age_range                                = get_dict_attr(owner_data, "$.age_range")
    birthday                                 = get_dict_attr(owner_data, "$.birthday")
    birthday_description                     = get_dict_attr(owner_data, "$.birthday_description")
    birthday_valid                           = get_dict_attr(owner_data, "$.birthday_valid")
    location_city                            = get_dict_attr(owner_data, "$.location_city")
    foreign_user                             = get_dict_attr(owner_data, "$.foreign_user")
    mystery_man                              = get_dict_attr(owner_data, "$.mystery_man")
    level_ro                                 = get_dict_attr(owner_data, "$.level")
    exp                                      = get_dict_attr(owner_data, "$.exp")
    experience                               = get_dict_attr(owner_data, "$.experience")
    fan_ticket_count                         = get_dict_attr(owner_data, "$.fan_ticket_count")
    consume_diamond_level                    = get_dict_attr(owner_data, "$.consume_diamond_level")
    income_share_percent                     = get_dict_attr(owner_data, "$.income_share_percent")
    link_mic_stats                           = get_dict_attr(owner_data, "$.link_mic_stats")
    media_badge_image_list_ro                = get_dict_attr(owner_data, "$.media_badge_image_list")
    modify_time                              = get_dict_attr(owner_data, "$.modify_time")
    pay_score                                = get_dict_attr(owner_data, "$.pay_score")
    pay_scores                               = get_dict_attr(owner_data, "$.pay_scores")
    need_profile_guide                       = get_dict_attr(owner_data, "$.need_profile_guide")
    new_real_time_icons_ro                   = get_dict_attr(owner_data, "$.new_real_time_icons")
    real_time_icons_ro                       = get_dict_attr(owner_data, "$.real_time_icons")
    follow_status                            = get_dict_attr(owner_data, "$.follow_status")
    is_follower                              = get_dict_attr(owner_data, "$.is_follower")
    is_following                             = get_dict_attr(owner_data, "$.is_following")
    follow_info                              = get_dict_attr(owner_data, "$.follow_info")
    is_anonymous                             = get_dict_attr(owner_data, "$.is_anonymous")
    hotsoon_verified                         = get_dict_attr(owner_data, "$.hotsoon_verified")
    hotsoon_verified_reason                  = get_dict_attr(owner_data, "$.hotsoon_verified_reason")
    ichat_restrict_type                      = get_dict_attr(owner_data, "$.ichat_restrict_type")
    disable_ichat                            = get_dict_attr(owner_data, "$.disable_ichat")
    enable_ichat_img                         = get_dict_attr(owner_data, "$.enable_ichat_img")
    fold_stranger_chat                       = get_dict_attr(owner_data, "$.fold_stranger_chat")
    desensitized_nickname                    = get_dict_attr(owner_data, "$.desensitized_nickname")
    verified_ro                              = get_dict_attr(owner_data, "$.verified")
    verified_reason                          = get_dict_attr(owner_data, "$.verified_reason")
    verified_content                         = get_dict_attr(owner_data, "$.verified_content")
    verified_mobile                          = get_dict_attr(owner_data, "$.verified_mobile")
    enterprise_verify_reason                 = get_dict_attr(owner_data, "$.authentication_info.enterprise_verify_reason")
    custom_verify                            = get_dict_attr(owner_data, "$.authentication_info.custom_verify")
    block_status                             = get_dict_attr(owner_data, "$.block_status")
    comment_restrict                         = get_dict_attr(owner_data, "$.comment_restrict")
    public_area_oper_freq                    = get_dict_attr(owner_data, "$.public_area_oper_freq")
    push_comment_status                      = get_dict_attr(owner_data, "$.push_comment_status")
    push_digg                                = get_dict_attr(owner_data, "$.push_digg")
    push_follow                              = get_dict_attr(owner_data, "$.push_follow")
    push_friend_action                       = get_dict_attr(owner_data, "$.push_friend_action")
    push_ichat                               = get_dict_attr(owner_data, "$.push_ichat")
    push_status                              = get_dict_attr(owner_data, "$.push_status")
    push_video_post                          = get_dict_attr(owner_data, "$.push_video_post")
    push_video_recommend                     = get_dict_attr(owner_data, "$.push_video_recommend")
    remark_name                              = get_dict_attr(owner_data, "$.remark_name")
    secret                                   = get_dict_attr(owner_data, "$.secret")
    user_role                                = get_dict_attr(owner_data, "$.user_role")
    webcast_private                          = get_dict_attr(owner_data, "$.webcast_private")
    can_view_webcast_private                 = get_dict_attr(owner_data, "$.can_view_webcast_private")
    user_canceled                            = get_dict_attr(owner_data, "$.user_canceled")
    telephone                                = get_dict_attr(owner_data, "$.telephone")
    with_commerce_permission                 = get_dict_attr(owner_data, "$.with_commerce_permission")
    with_fusion_shop_entry                   = get_dict_attr(owner_data, "$.with_fusion_shop_entry")
    with_car_management_permission           = get_dict_attr(owner_data, "$.with_car_management_permission")
    adversary_authorization_info             = get_dict_attr(owner_data, "$.adversary_authorization_info")
    adversary_user_status                    = get_dict_attr(owner_data, "$.adversary_user_status")
    authorization_info                       = get_dict_attr(owner_data, "$.authorization_info")
    allow_be_located                         = get_dict_attr(owner_data, "$.allow_be_located")
    allow_find_by_contacts                   = get_dict_attr(owner_data, "$.allow_find_by_contacts")
    allow_others_download_video              = get_dict_attr(owner_data, "$.allow_others_download_video")
    allow_others_download_when_sharing_video = get_dict_attr(owner_data, "$.allow_others_download_when_sharing_video")
    allow_share_show_profile                 = get_dict_attr(owner_data, "$.allow_share_show_profile")
    allow_show_in_gossip                     = get_dict_attr(owner_data, "$.allow_show_in_gossip")
    allow_show_my_action                     = get_dict_attr(owner_data, "$.allow_show_my_action")
    allow_strange_comment                    = get_dict_attr(owner_data, "$.allow_strange_comment")
    allow_unfollower_comment                 = get_dict_attr(owner_data, "$.allow_unfollower_comment")
    allow_use_linkmic                        = get_dict_attr(owner_data, "$.allow_use_linkmic")
    
    ## JSON 扩展字段
    avatar_large                             = get_dict_attr(owner_data, "$.avatar_large")
    avatar_medium                            = get_dict_attr(owner_data, "$.avatar_medium")
    avatar_thumb                             = get_dict_attr(owner_data, "$.avatar_thumb")
    badge_image_list                         = get_dict_attr(owner_data, "$.badge_image_list")
    badge_image_list_v2                      = get_dict_attr(owner_data, "$.badge_image_list_v2")
    commerce_webcast_config_ids              = get_dict_attr(owner_data, "$.commerce_webcast_config_ids")
    authentication_info                      = get_dict_attr(owner_data, "$.authentication_info")
    border_data                              = get_dict_attr(owner_data, "$.border")
    pay_grade_data                           = get_dict_attr(owner_data, "$.pay_grade")
    fans_club_data                           = get_dict_attr(owner_data, "$.fans_club")
    fans_group_info                          = get_dict_attr(owner_data, "$.fans_group_info")
    subscribe_data                           = get_dict_attr(owner_data, "$.subscribe")
    user_attr_data                           = get_dict_attr(owner_data, "$.user_attr")
    user_dress_info_data                     = get_dict_attr(owner_data, "$.user_dress_info")
    biz_relation_data                        = get_dict_attr(owner_data, "$.biz_relation")
    j_accredit_info_data                     = get_dict_attr(owner_data, "$.j_accredit_info")
    own_room_data                            = get_dict_attr(owner_data, "$.own_room")
    total_recharge_diamond_count             = get_dict_attr(owner_data, "$.total_recharge_diamond_count")
    watch_duration_month                     = get_dict_attr(owner_data, "$.watch_duration_month")
    web_rid                                  = get_dict_attr(owner_data, "$.web_rid")
    webcast_nick                             = get_dict_attr(owner_data, "$.webcast_nick")
    webcast_uid                              = get_dict_attr(owner_data, "$.webcast_uid")

    if room_id_ro is None:
      room_id_ro = room_id

    set_dict_attr(room_owner_v2_table_tuple, "$.room_id",                                  str(room_id_ro) if room_id_ro is not None else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.user_id",                                  str(user_id_ro) if user_id_ro is not None else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.owner_open_id",                            owner_open_id_ro)
    set_dict_attr(room_owner_v2_table_tuple, "$.owner_device_id",                          owner_device_id_ro if owner_device_id_ro is not None else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.sec_uid",                                  sec_uid)
    set_dict_attr(room_owner_v2_table_tuple, "$.user_open_id",                             user_open_id_ro)
    set_dict_attr(room_owner_v2_table_tuple, "$.short_id",                                 short_id)
    set_dict_attr(room_owner_v2_table_tuple, "$.display_id",                               display_id)
    set_dict_attr(room_owner_v2_table_tuple, "$.nickname",                                 nickname)
    set_dict_attr(room_owner_v2_table_tuple, "$.signature",                                signature)
    set_dict_attr(room_owner_v2_table_tuple, "$.share_qrcode_uri",                         share_qrcode_uri)
    set_dict_attr(room_owner_v2_table_tuple, "$.special_id",                               special_id)
    set_dict_attr(room_owner_v2_table_tuple, "$.status",                                   status_ro)
    set_dict_attr(room_owner_v2_table_tuple, "$.bg_img_url",                               bg_img_url)
    set_dict_attr(room_owner_v2_table_tuple, "$.gender",                                   gender_ro)
    set_dict_attr(room_owner_v2_table_tuple, "$.city",                                     city_ro)
    set_dict_attr(room_owner_v2_table_tuple, "$.constellation",                            constellation)
    set_dict_attr(room_owner_v2_table_tuple, "$.age_range",                                age_range)
    set_dict_attr(room_owner_v2_table_tuple, "$.birthday",                                 birthday)
    set_dict_attr(room_owner_v2_table_tuple, "$.birthday_description",                     birthday_description)
    set_dict_attr(room_owner_v2_table_tuple, "$.birthday_valid",                           birthday_valid)
    set_dict_attr(room_owner_v2_table_tuple, "$.location_city",                            location_city)
    set_dict_attr(room_owner_v2_table_tuple, "$.foreign_user",                             foreign_user)
    set_dict_attr(room_owner_v2_table_tuple, "$.mystery_man",                              mystery_man)
    set_dict_attr(room_owner_v2_table_tuple, "$.level",                                    level_ro)
    set_dict_attr(room_owner_v2_table_tuple, "$.exp",                                      exp)
    set_dict_attr(room_owner_v2_table_tuple, "$.experience",                               experience)
    set_dict_attr(room_owner_v2_table_tuple, "$.fan_ticket_count",                         fan_ticket_count)
    set_dict_attr(room_owner_v2_table_tuple, "$.consume_diamond_level",                    consume_diamond_level)
    set_dict_attr(room_owner_v2_table_tuple, "$.income_share_percent",                     income_share_percent)
    set_dict_attr(room_owner_v2_table_tuple, "$.link_mic_stats",                           link_mic_stats)
    set_dict_attr(room_owner_v2_table_tuple, "$.media_badge_image_list",                   json.dumps(media_badge_image_list_ro) if media_badge_image_list_ro is not None else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.modify_time",                              modify_time)
    set_dict_attr(room_owner_v2_table_tuple, "$.pay_score",                                pay_score)
    set_dict_attr(room_owner_v2_table_tuple, "$.pay_scores",                               pay_scores)
    set_dict_attr(room_owner_v2_table_tuple, "$.need_profile_guide",                       need_profile_guide)
    set_dict_attr(room_owner_v2_table_tuple, "$.new_real_time_icons",                      json.dumps(new_real_time_icons_ro) if new_real_time_icons_ro is not None else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.real_time_icons",                          json.dumps(real_time_icons_ro) if real_time_icons_ro is not None else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.follow_status",                            follow_status)
    set_dict_attr(room_owner_v2_table_tuple, "$.is_follower",                              is_follower)
    set_dict_attr(room_owner_v2_table_tuple, "$.is_following",                             is_following)
    set_dict_attr(room_owner_v2_table_tuple, "$.follow_info",                              json.dumps(follow_info) if follow_info is not None else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.is_anonymous",                             is_anonymous)
    set_dict_attr(room_owner_v2_table_tuple, "$.hotsoon_verified",                         hotsoon_verified)
    set_dict_attr(room_owner_v2_table_tuple, "$.hotsoon_verified_reason",                  hotsoon_verified_reason)
    set_dict_attr(room_owner_v2_table_tuple, "$.ichat_restrict_type",                      ichat_restrict_type)
    set_dict_attr(room_owner_v2_table_tuple, "$.disable_ichat",                            disable_ichat)
    set_dict_attr(room_owner_v2_table_tuple, "$.enable_ichat_img",                         enable_ichat_img)
    set_dict_attr(room_owner_v2_table_tuple, "$.fold_stranger_chat",                       fold_stranger_chat)
    set_dict_attr(room_owner_v2_table_tuple, "$.desensitized_nickname",                    desensitized_nickname)
    set_dict_attr(room_owner_v2_table_tuple, "$.verified",                                 verified_ro)
    set_dict_attr(room_owner_v2_table_tuple, "$.verified_reason",                          verified_reason)
    set_dict_attr(room_owner_v2_table_tuple, "$.verified_content",                         verified_content)
    set_dict_attr(room_owner_v2_table_tuple, "$.verified_mobile",                          verified_mobile)
    set_dict_attr(room_owner_v2_table_tuple, "$.enterprise_verify_reason",                 enterprise_verify_reason)
    set_dict_attr(room_owner_v2_table_tuple, "$.custom_verify",                            custom_verify)
    set_dict_attr(room_owner_v2_table_tuple, "$.block_status",                             block_status)
    set_dict_attr(room_owner_v2_table_tuple, "$.comment_restrict",                         comment_restrict)
    set_dict_attr(room_owner_v2_table_tuple, "$.public_area_oper_freq",                    public_area_oper_freq)
    set_dict_attr(room_owner_v2_table_tuple, "$.push_comment_status",                      push_comment_status)
    set_dict_attr(room_owner_v2_table_tuple, "$.push_digg",                                push_digg)
    set_dict_attr(room_owner_v2_table_tuple, "$.push_follow",                              push_follow)
    set_dict_attr(room_owner_v2_table_tuple, "$.push_friend_action",                       push_friend_action)
    set_dict_attr(room_owner_v2_table_tuple, "$.push_ichat",                               push_ichat)
    set_dict_attr(room_owner_v2_table_tuple, "$.push_status",                              push_status)
    set_dict_attr(room_owner_v2_table_tuple, "$.push_video_post",                          push_video_post)
    set_dict_attr(room_owner_v2_table_tuple, "$.push_video_recommend",                     push_video_recommend)
    set_dict_attr(room_owner_v2_table_tuple, "$.secret",                                   secret)
    set_dict_attr(room_owner_v2_table_tuple, "$.user_role",                                user_role)
    set_dict_attr(room_owner_v2_table_tuple, "$.webcast_private",                          webcast_private)
    set_dict_attr(room_owner_v2_table_tuple, "$.can_view_webcast_private",                 can_view_webcast_private)
    set_dict_attr(room_owner_v2_table_tuple, "$.user_canceled",                            user_canceled)
    set_dict_attr(room_owner_v2_table_tuple, "$.telephone",                                telephone)
    set_dict_attr(room_owner_v2_table_tuple, "$.with_commerce_permission",                 with_commerce_permission)
    set_dict_attr(room_owner_v2_table_tuple, "$.with_fusion_shop_entry",                   with_fusion_shop_entry)
    set_dict_attr(room_owner_v2_table_tuple, "$.with_car_management_permission",           with_car_management_permission)
    set_dict_attr(room_owner_v2_table_tuple, "$.adversary_authorization_info",             adversary_authorization_info)
    set_dict_attr(room_owner_v2_table_tuple, "$.adversary_user_status",                    adversary_user_status)
    set_dict_attr(room_owner_v2_table_tuple, "$.authorization_info",                       authorization_info)
    set_dict_attr(room_owner_v2_table_tuple, "$.allow_be_located",                         allow_be_located)
    set_dict_attr(room_owner_v2_table_tuple, "$.allow_find_by_contacts",                   allow_find_by_contacts)
    set_dict_attr(room_owner_v2_table_tuple, "$.allow_others_download_video",              allow_others_download_video)
    set_dict_attr(room_owner_v2_table_tuple, "$.allow_others_download_when_sharing_video", allow_others_download_when_sharing_video)
    set_dict_attr(room_owner_v2_table_tuple, "$.allow_share_show_profile",                 allow_share_show_profile)
    set_dict_attr(room_owner_v2_table_tuple, "$.allow_show_in_gossip",                     allow_show_in_gossip)
    set_dict_attr(room_owner_v2_table_tuple, "$.allow_show_my_action",                     allow_show_my_action)
    set_dict_attr(room_owner_v2_table_tuple, "$.allow_strange_comment",                    allow_strange_comment)
    set_dict_attr(room_owner_v2_table_tuple, "$.allow_unfollower_comment",                 allow_unfollower_comment)
    set_dict_attr(room_owner_v2_table_tuple, "$.allow_use_linkmic",                        allow_use_linkmic)
    set_dict_attr(room_owner_v2_table_tuple, "$.remark_name",                              remark_name)

    ## JSON 扩展字段
    set_dict_attr(room_owner_v2_table_tuple, "$.avatar_large",                             json.dumps(avatar_large) if avatar_large is not None else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.avatar_medium",                            json.dumps(avatar_medium) if avatar_medium is not None else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.avatar_thumb",                             json.dumps(avatar_thumb) if avatar_thumb is not None else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.badge_image_list",                         json.dumps(badge_image_list) if badge_image_list is not None else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.badge_image_list_v2",                      json.dumps(badge_image_list_v2) if badge_image_list_v2 is not None else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.commerce_webcast_config_ids",              json.dumps(commerce_webcast_config_ids) if commerce_webcast_config_ids is not None else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.authentication_info",                      json.dumps(authentication_info) if authentication_info is not None else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.border_data",                              json.dumps(border_data) if border_data is not None else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.pay_grade_data",                           json.dumps(pay_grade_data) if pay_grade_data is not None else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.fans_club_data",                           json.dumps(fans_club_data) if fans_club_data is not None else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.fans_group_info",                          json.dumps(fans_group_info) if fans_group_info is not None else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.subscribe_data",                           json.dumps(subscribe_data) if subscribe_data is not None else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.user_attr_data",                           json.dumps(user_attr_data) if user_attr_data is not None else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.user_dress_info_data",                     json.dumps(user_dress_info_data) if user_dress_info_data is not None else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.biz_relation_data",                        json.dumps(biz_relation_data) if biz_relation_data is not None else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.j_accredit_info_data",                     json.dumps(j_accredit_info_data) if j_accredit_info_data is not None else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.own_room_data",                            json.dumps(own_room_data) if own_room_data is not None else None)
    set_dict_attr(room_owner_v2_table_tuple, "$.total_recharge_diamond_count",             total_recharge_diamond_count)
    set_dict_attr(room_owner_v2_table_tuple, "$.watch_duration_month",                     watch_duration_month)
    set_dict_attr(room_owner_v2_table_tuple, "$.web_rid",                                  web_rid)
    set_dict_attr(room_owner_v2_table_tuple, "$.webcast_nick",                             webcast_nick)
    set_dict_attr(room_owner_v2_table_tuple, "$.webcast_uid",                              webcast_uid)

    if room_id_ro is not None:
      room_owner_v2_table.insert_record(room_owner_v2_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(room_owner_v2_table.get_name(), e))
    raise e

def import_douyin_user_to_database(db:SocialMediaStreamDataBase, data:dict) -> None:
  now             = dat.fromtimestamp(get_dict_attr(data, "$.extra.now")/1000.0)
  DOUYIN_PLATFORM = "douyin"
  room_id         = get_dict_attr(data, "$.data.room.id")

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
    user_table_tuple = {key:None for key in user_table.get_tuple()}

    user_data = get_dict_attr(data, "$.data.user")
    if isinstance(user_data, dict) is False:
      user_data = {}

    user_id_ut                              = get_dict_attr(user_data, "$.id")
    adversary_authorization_info_ut         = get_dict_attr(user_data, "$.adversary_authorization_info")
    adversary_user_status_ut                = get_dict_attr(user_data, "$.adversary_user_status")
    age_range_ut                            = get_dict_attr(user_data, "$.age_range")
    allow_be_located_ut                     = get_dict_attr(user_data, "$.allow_be_located")
    allow_find_by_contacts_ut               = get_dict_attr(user_data, "$.allow_find_by_contacts")
    allow_others_download_video_ut          = get_dict_attr(user_data, "$.allow_others_download_video")
    allow_others_download_when_sharing_video_ut = get_dict_attr(user_data, "$.allow_others_download_when_sharing_video")
    allow_share_show_profile_ut             = get_dict_attr(user_data, "$.allow_share_show_profile")
    allow_show_in_gossip_ut                 = get_dict_attr(user_data, "$.allow_show_in_gossip")
    allow_show_my_action_ut                 = get_dict_attr(user_data, "$.allow_show_my_action")
    allow_strange_comment_ut                = get_dict_attr(user_data, "$.allow_strange_comment")
    allow_unfollower_comment_ut             = get_dict_attr(user_data, "$.allow_unfollower_comment")
    allow_use_linkmic_ut                    = get_dict_attr(user_data, "$.allow_use_linkmic")
    authorization_info_ut                   = get_dict_attr(user_data, "$.authorization_info")
    bg_img_url_ut                           = get_dict_attr(user_data, "$.bg_img_url")
    birthday_ut                             = get_dict_attr(user_data, "$.birthday")
    birthday_description_ut                 = get_dict_attr(user_data, "$.birthday_description")
    birthday_valid_ut                       = get_dict_attr(user_data, "$.birthday_valid")
    block_status_ut                         = get_dict_attr(user_data, "$.block_status")
    city_ut                                 = get_dict_attr(user_data, "$.city")
    comment_restrict_ut                     = get_dict_attr(user_data, "$.comment_restrict")
    constellation_ut                        = get_dict_attr(user_data, "$.constellation")
    consume_diamond_level_ut                = get_dict_attr(user_data, "$.consume_diamond_level")
    create_time_ut                          = get_dict_attr(user_data, "$.create_time")
    desensitized_nickname_ut                = get_dict_attr(user_data, "$.desensitized_nickname")
    disable_ichat_ut                        = get_dict_attr(user_data, "$.disable_ichat")
    display_id_ut                           = get_dict_attr(user_data, "$.display_id")
    enable_ichat_img_ut                     = get_dict_attr(user_data, "$.enable_ichat_img")
    exp_ut                                  = get_dict_attr(user_data, "$.exp")
    experience_ut                           = get_dict_attr(user_data, "$.experience")
    fan_ticket_count_ut                     = get_dict_attr(user_data, "$.fan_ticket_count")
    fold_stranger_chat_ut                   = get_dict_attr(user_data, "$.fold_stranger_chat")
    follow_status_ut                        = get_dict_attr(user_data, "$.follow_status")
    foreign_user_ut                         = get_dict_attr(user_data, "$.foreign_user")
    gender_ut                               = get_dict_attr(user_data, "$.gender")
    hotsoon_verified_ut                     = get_dict_attr(user_data, "$.hotsoon_verified")
    hotsoon_verified_reason_ut              = get_dict_attr(user_data, "$.hotsoon_verified_reason")
    ichat_restrict_type_ut                  = get_dict_attr(user_data, "$.ichat_restrict_type")
    income_share_percent_ut                 = get_dict_attr(user_data, "$.income_share_percent")
    is_anonymous_ut                         = get_dict_attr(user_data, "$.is_anonymous")
    is_follower_ut                          = get_dict_attr(user_data, "$.is_follower")
    is_following_ut                         = get_dict_attr(user_data, "$.is_following")
    level_ut                                = get_dict_attr(user_data, "$.level")
    link_mic_stats_ut                       = get_dict_attr(user_data, "$.link_mic_stats")
    location_city_ut                        = get_dict_attr(user_data, "$.location_city")
    modify_time_ut                          = get_dict_attr(user_data, "$.modify_time")
    mystery_man_ut                          = get_dict_attr(user_data, "$.mystery_man")
    need_profile_guide_ut                   = get_dict_attr(user_data, "$.need_profile_guide")
    nickname_ut                             = get_dict_attr(user_data, "$.nickname")
    pay_score_ut                            = get_dict_attr(user_data, "$.pay_score")
    pay_scores_ut                           = get_dict_attr(user_data, "$.pay_scores")
    public_area_oper_freq_ut                = get_dict_attr(user_data, "$.public_area_oper_freq")
    push_comment_status_ut                  = get_dict_attr(user_data, "$.push_comment_status")
    push_digg_ut                            = get_dict_attr(user_data, "$.push_digg")
    push_follow_ut                          = get_dict_attr(user_data, "$.push_follow")
    push_friend_action_ut                   = get_dict_attr(user_data, "$.push_friend_action")
    push_ichat_ut                           = get_dict_attr(user_data, "$.push_ichat")
    push_status_ut                          = get_dict_attr(user_data, "$.push_status")
    push_video_post_ut                      = get_dict_attr(user_data, "$.push_video_post")
    push_video_recommend_ut                 = get_dict_attr(user_data, "$.push_video_recommend")
    remark_name_ut                          = get_dict_attr(user_data, "$.remark_name")
    sec_uid_ut                              = get_dict_attr(user_data, "$.sec_uid")
    secret_ut                               = get_dict_attr(user_data, "$.secret")
    share_qrcode_uri_ut                     = get_dict_attr(user_data, "$.share_qrcode_uri")
    short_id_ut                             = get_dict_attr(user_data, "$.short_id")
    signature_ut                            = get_dict_attr(user_data, "$.signature")
    special_id_ut                           = get_dict_attr(user_data, "$.special_id")
    status_ut                               = get_dict_attr(user_data, "$.status")
    telephone_ut                            = get_dict_attr(user_data, "$.telephone")
    ticket_count_ut                         = get_dict_attr(user_data, "$.ticket_count")
    top_vip_no_ut                           = get_dict_attr(user_data, "$.top_vip_no")
    total_recharge_diamond_count_ut         = get_dict_attr(user_data, "$.total_recharge_diamond_count")
    user_canceled_ut                        = get_dict_attr(user_data, "$.user_canceled")
    user_open_id_ut                         = get_dict_attr(user_data, "$.user_open_id")
    user_role_ut                            = get_dict_attr(user_data, "$.user_role")
    verified_ut                             = get_dict_attr(user_data, "$.verified")
    verified_content_ut                     = get_dict_attr(user_data, "$.verified_content")
    verified_mobile_ut                      = get_dict_attr(user_data, "$.verified_mobile")
    verified_reason_ut                      = get_dict_attr(user_data, "$.verified_reason")
    watch_duration_month_ut                 = get_dict_attr(user_data, "$.watch_duration_month")
    web_rid_ut                              = get_dict_attr(user_data, "$.web_rid")
    webcast_uid_ut                          = get_dict_attr(user_data, "$.webcast_uid")
    with_car_management_permission_ut       = get_dict_attr(user_data, "$.with_car_management_permission")
    with_commerce_permission_ut             = get_dict_attr(user_data, "$.with_commerce_permission")
    with_fusion_shop_entry_ut               = get_dict_attr(user_data, "$.with_fusion_shop_entry")
    can_view_webcast_private_ut             = get_dict_attr(user_data, "$.can_view_webcast_private")
    webcast_nick_ut                         = get_dict_attr(user_data, "$.webcast_nick")
    webcast_private_ut                      = get_dict_attr(user_data, "$.webcast_private")
    hide_by_room_ut                         = get_dict_attr(user_data, "$.hide_by_room")
    link_mask_ut                            = get_dict_attr(user_data, "$.link_mask")

    ## JSON 扩展字段
    badge_image_list_ut                     = get_dict_attr(user_data, "$.badge_image_list")
    badge_image_list_v2_ut                  = get_dict_attr(user_data, "$.badge_image_list_v2")
    media_badge_image_list_ut               = get_dict_attr(user_data, "$.media_badge_image_list")
    new_real_time_icons_ut                  = get_dict_attr(user_data, "$.new_real_time_icons")
    real_time_icons_ut                      = get_dict_attr(user_data, "$.real_time_icons")
    top_fans_ut                             = get_dict_attr(user_data, "$.top_fans")
    commerce_webcast_config_ids_ut          = get_dict_attr(user_data, "$.commerce_webcast_config_ids")

    if user_id_ut is None:
      user_id_ut = get_dict_attr(data, "$.data.room.owner_user_id")

    set_dict_attr(user_table_tuple, "$.id",                                 str(user_id_ut) if user_id_ut is not None else None)
    set_dict_attr(user_table_tuple, "$.adversary_authorization_info",       adversary_authorization_info_ut)
    set_dict_attr(user_table_tuple, "$.adversary_user_status",              adversary_user_status_ut)
    set_dict_attr(user_table_tuple, "$.age_range",                          age_range_ut)
    set_dict_attr(user_table_tuple, "$.allow_be_located",                   allow_be_located_ut)
    set_dict_attr(user_table_tuple, "$.allow_find_by_contacts",             allow_find_by_contacts_ut)
    set_dict_attr(user_table_tuple, "$.allow_others_download_video",        allow_others_download_video_ut)
    set_dict_attr(user_table_tuple, "$.allow_others_download_when_sharing_video", allow_others_download_when_sharing_video_ut)
    set_dict_attr(user_table_tuple, "$.allow_share_show_profile",           allow_share_show_profile_ut)
    set_dict_attr(user_table_tuple, "$.allow_show_in_gossip",               allow_show_in_gossip_ut)
    set_dict_attr(user_table_tuple, "$.allow_show_my_action",               allow_show_my_action_ut)
    set_dict_attr(user_table_tuple, "$.allow_strange_comment",              allow_strange_comment_ut)
    set_dict_attr(user_table_tuple, "$.allow_unfollower_comment",           allow_unfollower_comment_ut)
    set_dict_attr(user_table_tuple, "$.allow_use_linkmic",                  allow_use_linkmic_ut)
    set_dict_attr(user_table_tuple, "$.authorization_info",                 authorization_info_ut)
    set_dict_attr(user_table_tuple, "$.badge_image_list",                   json.dumps(badge_image_list_ut) if badge_image_list_ut is not None else None)
    set_dict_attr(user_table_tuple, "$.badge_image_list_v2",                json.dumps(badge_image_list_v2_ut) if badge_image_list_v2_ut is not None else None)
    set_dict_attr(user_table_tuple, "$.bg_img_url",                         bg_img_url_ut)
    set_dict_attr(user_table_tuple, "$.birthday",                           birthday_ut)
    set_dict_attr(user_table_tuple, "$.birthday_description",               birthday_description_ut)
    set_dict_attr(user_table_tuple, "$.birthday_valid",                     birthday_valid_ut)
    set_dict_attr(user_table_tuple, "$.block_status",                       block_status_ut)
    set_dict_attr(user_table_tuple, "$.city",                               city_ut)
    set_dict_attr(user_table_tuple, "$.comment_restrict",                   comment_restrict_ut)
    set_dict_attr(user_table_tuple, "$.commerce_webcast_config_ids",        json.dumps(commerce_webcast_config_ids_ut) if commerce_webcast_config_ids_ut is not None else None)
    set_dict_attr(user_table_tuple, "$.constellation",                      constellation_ut)
    set_dict_attr(user_table_tuple, "$.consume_diamond_level",              consume_diamond_level_ut)
    set_dict_attr(user_table_tuple, "$.create_time",                        create_time_ut)
    set_dict_attr(user_table_tuple, "$.desensitized_nickname",              desensitized_nickname_ut)
    set_dict_attr(user_table_tuple, "$.disable_ichat",                      disable_ichat_ut)
    set_dict_attr(user_table_tuple, "$.display_id",                         display_id_ut)
    set_dict_attr(user_table_tuple, "$.enable_ichat_img",                   enable_ichat_img_ut)
    set_dict_attr(user_table_tuple, "$.exp",                                exp_ut)
    set_dict_attr(user_table_tuple, "$.experience",                         experience_ut)
    set_dict_attr(user_table_tuple, "$.fan_ticket_count",                   fan_ticket_count_ut)
    set_dict_attr(user_table_tuple, "$.fold_stranger_chat",                 fold_stranger_chat_ut)
    set_dict_attr(user_table_tuple, "$.follow_status",                      follow_status_ut)
    set_dict_attr(user_table_tuple, "$.foreign_user",                       foreign_user_ut)
    set_dict_attr(user_table_tuple, "$.gender",                             gender_ut)
    set_dict_attr(user_table_tuple, "$.hotsoon_verified",                   hotsoon_verified_ut)
    set_dict_attr(user_table_tuple, "$.hotsoon_verified_reason",            hotsoon_verified_reason_ut)
    set_dict_attr(user_table_tuple, "$.ichat_restrict_type",                ichat_restrict_type_ut)
    set_dict_attr(user_table_tuple, "$.income_share_percent",               income_share_percent_ut)
    set_dict_attr(user_table_tuple, "$.is_anonymous",                       is_anonymous_ut)
    set_dict_attr(user_table_tuple, "$.is_follower",                        is_follower_ut)
    set_dict_attr(user_table_tuple, "$.is_following",                       is_following_ut)
    set_dict_attr(user_table_tuple, "$.level",                              level_ut)
    set_dict_attr(user_table_tuple, "$.link_mic_stats",                     link_mic_stats_ut)
    set_dict_attr(user_table_tuple, "$.location_city",                      location_city_ut)
    set_dict_attr(user_table_tuple, "$.media_badge_image_list",             json.dumps(media_badge_image_list_ut) if media_badge_image_list_ut is not None else None)
    set_dict_attr(user_table_tuple, "$.modify_time",                        modify_time_ut)
    set_dict_attr(user_table_tuple, "$.mystery_man",                        mystery_man_ut)
    set_dict_attr(user_table_tuple, "$.need_profile_guide",                 need_profile_guide_ut)
    set_dict_attr(user_table_tuple, "$.new_real_time_icons",                json.dumps(new_real_time_icons_ut) if new_real_time_icons_ut is not None else None)
    set_dict_attr(user_table_tuple, "$.nickname",                           nickname_ut)
    set_dict_attr(user_table_tuple, "$.pay_score",                          pay_score_ut)
    set_dict_attr(user_table_tuple, "$.pay_scores",                         pay_scores_ut)
    set_dict_attr(user_table_tuple, "$.public_area_oper_freq",              public_area_oper_freq_ut)
    set_dict_attr(user_table_tuple, "$.push_comment_status",                push_comment_status_ut)
    set_dict_attr(user_table_tuple, "$.push_digg",                          push_digg_ut)
    set_dict_attr(user_table_tuple, "$.push_follow",                        push_follow_ut)
    set_dict_attr(user_table_tuple, "$.push_friend_action",                 push_friend_action_ut)
    set_dict_attr(user_table_tuple, "$.push_ichat",                         push_ichat_ut)
    set_dict_attr(user_table_tuple, "$.push_status",                        push_status_ut)
    set_dict_attr(user_table_tuple, "$.push_video_post",                    push_video_post_ut)
    set_dict_attr(user_table_tuple, "$.push_video_recommend",               push_video_recommend_ut)
    set_dict_attr(user_table_tuple, "$.real_time_icons",                    json.dumps(real_time_icons_ut) if real_time_icons_ut is not None else None)
    set_dict_attr(user_table_tuple, "$.remark_name",                        remark_name_ut)
    set_dict_attr(user_table_tuple, "$.sec_uid",                            sec_uid_ut)
    set_dict_attr(user_table_tuple, "$.secret",                             secret_ut)
    set_dict_attr(user_table_tuple, "$.share_qrcode_uri",                   share_qrcode_uri_ut)
    set_dict_attr(user_table_tuple, "$.short_id",                           short_id_ut)
    set_dict_attr(user_table_tuple, "$.signature",                          signature_ut)
    set_dict_attr(user_table_tuple, "$.special_id",                         special_id_ut)
    set_dict_attr(user_table_tuple, "$.status",                             status_ut)
    set_dict_attr(user_table_tuple, "$.telephone",                          telephone_ut)
    set_dict_attr(user_table_tuple, "$.ticket_count",                       ticket_count_ut)
    set_dict_attr(user_table_tuple, "$.top_fans",                           json.dumps(top_fans_ut) if top_fans_ut is not None else None)
    set_dict_attr(user_table_tuple, "$.top_vip_no",                         top_vip_no_ut)
    set_dict_attr(user_table_tuple, "$.total_recharge_diamond_count",       total_recharge_diamond_count_ut)
    set_dict_attr(user_table_tuple, "$.user_canceled",                      user_canceled_ut)
    set_dict_attr(user_table_tuple, "$.user_open_id",                       user_open_id_ut)
    set_dict_attr(user_table_tuple, "$.user_role",                          user_role_ut)
    set_dict_attr(user_table_tuple, "$.verified",                           verified_ut)
    set_dict_attr(user_table_tuple, "$.verified_content",                   verified_content_ut)
    set_dict_attr(user_table_tuple, "$.verified_mobile",                    verified_mobile_ut)
    set_dict_attr(user_table_tuple, "$.verified_reason",                    verified_reason_ut)
    set_dict_attr(user_table_tuple, "$.watch_duration_month",               watch_duration_month_ut)
    set_dict_attr(user_table_tuple, "$.web_rid",                            web_rid_ut)
    set_dict_attr(user_table_tuple, "$.webcast_uid",                        webcast_uid_ut)
    set_dict_attr(user_table_tuple, "$.with_car_management_permission",     with_car_management_permission_ut)
    set_dict_attr(user_table_tuple, "$.with_commerce_permission",           with_commerce_permission_ut)
    set_dict_attr(user_table_tuple, "$.with_fusion_shop_entry",             with_fusion_shop_entry_ut)
    set_dict_attr(user_table_tuple, "$.can_view_webcast_private",           can_view_webcast_private_ut)
    set_dict_attr(user_table_tuple, "$.webcast_nick",                       webcast_nick_ut)
    set_dict_attr(user_table_tuple, "$.webcast_private",                    webcast_private_ut)
    set_dict_attr(user_table_tuple, "$.hide_by_room",                       hide_by_room_ut)
    set_dict_attr(user_table_tuple, "$.link_mask",                          link_mask_ut)
    set_dict_attr(user_table_tuple, "$.created_at",                         now)
    set_dict_attr(user_table_tuple, "$.updated_at",                         now)

    if user_id_ut is not None:
      user_table.insert_record(user_table_tuple, on_duplicate='ignore')
  except Exception as e:
    get_logger().error("insert {} failed: {}".format(user_table.get_name(), e))
    raise e

##
## import a living data to relative tables of social media stream downloader.
##
def import_douyin_live_info_to_database(db:SocialMediaStreamDataBase, data:dict) -> None:
  import_douyin_live_record_to_database(db, data)
  import_douyin_room_base_to_database(db, data)
  import_douyin_room_owner_v2_to_database(db, data)
  import_douyin_room_stats_to_database(db, data)
  import_douyin_room_admin_user_id_to_database(db, data)
  import_douyin_room_admin_user_open_id_to_database(db, data)
  import_douyin_room_deco_to_database(db, data)
  import_douyin_fans_group_admin_user_id_to_database(db, data)
  import_douyin_fans_group_admin_user_open_id_to_database(db, data)
  import_douyin_user_to_database(db, data)
