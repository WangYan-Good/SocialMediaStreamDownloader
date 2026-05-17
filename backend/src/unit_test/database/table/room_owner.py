##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from datetime                                                         import datetime as dat
import json

## <<Third-Part>>
from backend.src.database.social_media_stream_database                import SocialMediaStreamDataBase
from backend.src.database.table.room_owner                            import RoomOwnerV2Table
from backend.src.base.log                                             import get_logger
from backend.src.unit_test.test_db_config                             import get_test_db_config

##
## >>================================ room_owner table test method ===============================>>
##

##
## test: create room_owner table
##
def test_create_room_owner_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## create room_owner table
  ##
  room_owner = RoomOwnerV2Table(db_instance=db)
  room_owner.create()
  return

##
## test: drop room_owner table
##
def test_drop_room_owner_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## drop room_owner table
  ##
  room_owner = RoomOwnerV2Table(db_instance=db)
  room_owner.drop(confirm=True)
  return

##
## test: check if room_owner table exists
##
def test_check_room_owner_table_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  room_owner = RoomOwnerV2Table(db)

  ##
  ## check if room_owner table exists
  ##
  if db.is_table_exist(room_owner.get_name()):
    get_logger().info("{} table exists!".format(room_owner.get_name()))
  else:
    get_logger().info("{} table not exists!".format(room_owner.get_name()))
  return

##
## test: insert room_owner record
##
def test_insert_room_owner_record(db:SocialMediaStreamDataBase = None):
  """
  Test inserting a room_owner record into the room_owner table.
  """
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## create room_owner table if not exists
  ##
  room_owner = RoomOwnerV2Table(db_instance=db)

  ##
  ## insert a sample owner record
  ##
  sample_owner = {
    'room_id': '7362550606306773794',
    'user_id': 2700838411446480,
    'owner_open_id': '',
    'owner_device_id': 0,
    'sec_uid': 'MS4wLjABAAAA3REn4Oekpt-zrnovTqTVWrTPkevbUHRJZRX2td0l_EdDr8Zgzk1HlnNgKHEyguTr',
    'user_open_id': '',
    'short_id': '30266029732',
    'display_id': '30266029732',
    'nickname': 'Lvuuu',
    'signature': '❤️ 陪伴🔍 公众号：对你有意（👈解锁心动女孩\n男孩子的快乐@哥哥别玩呀🎮... 好玩！\n🈴️👔👗私',
    'special_id': '',
    'status': 1,
    'bg_img_url': '',
    'gender': 2,
    'city': '常德',
    'constellation': '',
    'age_range': 0,
    'birthday': 0,
    'birthday_description': '',
    'birthday_valid': False,
    'location_city': '',
    'foreign_user': 0,
    'mystery_man': 1,
    'level': 0,
    'exp': 0,
    'experience': 0,
    'fan_ticket_count': 0,
    'consume_diamond_level': 0,
    'income_share_percent': 0,
    'link_mic_stats': 1,
    'modify_time': 1740042739,
    'pay_score': 0,
    'pay_scores': 0,
    'need_profile_guide': False,
    'follow_status': 0,
    'is_follower': False,
    'is_following': False,
    'is_anonymous': False,
    'hotsoon_verified': False,
    'hotsoon_verified_reason': '',
    'ichat_restrict_type': 0,
    'disable_ichat': 0,
    'enable_ichat_img': 0,
    'fold_stranger_chat': False,
    'desensitized_nickname': '',
    'verified': True,
    'verified_reason': '',
    'verified_content': '',
    'verified_mobile': False,
    'enterprise_verify_reason': '店铺账号',
    'custom_verify': '',
    'block_status': 0,
    'comment_restrict': 0,
    'public_area_oper_freq': 0,
    'secret': 0,
    'user_role': 0,
    'webcast_private': 0,
    'can_view_webcast_private': 0,
    'user_canceled': False,
    'telephone': '',
    'with_commerce_permission': True,
    'with_fusion_shop_entry': True,
    'with_car_management_permission': False,
    'adversary_authorization_info': 3,
    'adversary_user_status': 0,
    'authorization_info': 3,
    'allow_be_located': False,
    'allow_find_by_contacts': False,
    'allow_others_download_video': False,
    'allow_others_download_when_sharing_video': False,
    'allow_share_show_profile': False,
    'allow_show_in_gossip': False,
    'allow_show_my_action': False,
    'allow_strange_comment': False,
    'allow_unfollower_comment': False,
    'allow_use_linkmic': False,
    'remark_name': '',
    'avatar_large': json.dumps({
      'avg_color': '',
      'uri': '1080x1080/aweme-avatar/tos-cn-avt-0015_073398e34f18e2e545861a83f392ad9f',
      'url_list': [
        'https://p3.douyinpic.com/aweme/1080x1080/aweme-avatar/tos-cn-avt-0015_073398e34f18e2e545861a83f392ad9f.jpeg?from=3067671334',
        'https://p11.douyinpic.com/aweme/1080x1080/aweme-avatar/tos-cn-avt-0015_073398e34f18e2e545861a83f392ad9f.jpeg?from=3067671334'
      ],
      'width': 0,
      'height': 0,
      'image_type': 0,
      'is_animated': False
    }),
    'avatar_medium': json.dumps({
      'avg_color': '',
      'uri': '720x720/aweme-avatar/tos-cn-avt-0015_073398e34f18e2e545861a83f392ad9f',
      'url_list': [
        'https://p3.douyinpic.com/aweme/720x720/aweme-avatar/tos-cn-avt-0015_073398e34f18e2e545861a83f392ad9f.jpeg?from=3067671334'
      ],
      'width': 0,
      'height': 0,
      'image_type': 0,
      'is_animated': False
    }),
    'avatar_thumb': json.dumps({
      'avg_color': '',
      'uri': '100x100/aweme-avatar/tos-cn-avt-0015_073398e34f18e2e545861a83f392ad9f',
      'url_list': [
        'https://p11.douyinpic.com/aweme/100x100/aweme-avatar/tos-cn-avt-0015_073398e34f18e2e545861a83f392ad9f.jpeg?from=3067671334'
      ],
      'width': 0,
      'height': 0,
      'image_type': 0,
      'is_animated': False
    }),
    'badge_image_list': json.dumps([]),
    'badge_image_list_v2': json.dumps([]),
    'commerce_webcast_config_ids': json.dumps([]),
    'authentication_info': json.dumps({
      'account_cert_info': '{"label_style":5,"label_text":"店铺账号","is_biz_account":1}',
      'enterprise_verify_reason': '店铺账号',
      'custom_verify': '',
      'level_list': [1, 10002]
    }),
    'border_data': json.dumps({
      'dress_id': '7390557818492818458',
      'level': 0,
      'icon': {
        'uri': 'webcast/42a7f5750a0f767361543edb61cb8535.png',
        'url_list': [
          'https://p11-webcast.douyinpic.com/img/webcast/42a7f5750a0f767361543edb61cb8535.png~tplv-obj.image'
        ],
        'width': 282,
        'height': 282,
        'image_type': 0
      }
    }),
    'pay_grade_data': json.dumps({
      'level': 2,
      'name': '',
      'grade_banner': '',
      'grade_describe': '',
      'grade_describe_shining': False,
      'in_rebirth': False,
      'score': 0,
      'this_grade_max_diamond': 16,
      'this_grade_min_diamond': 7,
      'total_diamond_count': 0
    }),
    'fans_club_data': json.dumps({
      'data': {
        'anchor_id': 0,
        'anchor_open_id': '',
        'available_gift_ids': [],
        'badge': {
          'icons': {},
          'title': ''
        },
        'badge_type': 0,
        'club_name': '',
        'guard_expired_time': 0,
        'level': 0,
        'user_fans_club_status': 0,
        'user_guard_status': 0
      },
      'prefer_data': {}
    }),
    'fans_group_info': json.dumps({
      'list_fans_group_url': 'sslocal://webcast_lynxview?height=754&radius=8&gravity=bottom&type=popup'
    }),
    'subscribe_data': json.dumps({
      'buy_type': 0,
      'identity_type': 0,
      'is_member': False,
      'level': 0,
      'open': 0
    }),
    'user_attr_data': json.dumps({
      'admin_privileges': [],
      'is_admin': False,
      'is_chat_self_see': False,
      'is_muted': False,
      'is_super_admin': False
    }),
    'user_dress_info_data': json.dumps({
      'dress_own_ids': [],
      'dress_wear_ids': []
    }),
    'biz_relation_data': json.dumps({
      'shop_fans_club_reverse': True
    }),
    'j_accredit_info_data': json.dumps({
      'JAccreditAdvance': 0,
      'JAccreditBasic': 0,
      'JAccreditContent': 0,
      'JAccreditLive': 0
    }),
    'own_room_data': json.dumps({
      'room_ids': [7509539722306521892],
      'room_ids_display': [],
      'room_ids_str': ['7509539722306521892']
    }),
    'total_recharge_diamond_count': 0,
    'watch_duration_month': 0,
    'web_rid': '827868393976',
    'webcast_nick': '',
    'webcast_uid': 'MS4wLjMljH3nsEUH1oduoEHICOyLO_mi_GCJdTJEys1TI9mE8kaaf7-cX-5cj3yS5qMPbqI',
    'created_at': dat.fromtimestamp(1714227431),
    'updated_at': dat.fromtimestamp(1740042739)
  }

  try:
    room_owner.insert_record(sample_owner)
    get_logger().info("sample room_owner record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample room_owner record: {}".format(e))
    raise e

##
## test: get room_owner record
##
def test_get_room_owner_record(db:SocialMediaStreamDataBase = None):
  """
  Test getting a room_owner record from the room_owner table.
  """
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## create room_owner table if not exists
  ##
  room_owner = RoomOwnerV2Table(db_instance=db)

  ##
  ## get record by room_id
  ##
  try:
    record = room_owner.get_record({'room_id': '7362550606306773794'})
    if record:
      get_logger().info("room_owner record found: {}".format(record))
    else:
      get_logger().info("room_owner record not found")
  except Exception as e:
    get_logger().error("failed to get room_owner record: {}".format(e))
    raise e

##
## test: update room_owner record
##
def test_update_room_owner_record(db:SocialMediaStreamDataBase = None):
  """
  Test updating a room_owner record in the room_owner table.
  """
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## create room_owner table if not exists
  ##
  room_owner = RoomOwnerV2Table(db_instance=db)

  ##
  ## update a sample owner record
  ##
  update_data = {
    'room_id': '7362550606306773794',
    'fan_ticket_count': 1000,
    'pay_score': 500,
    'updated_at': dat.now()
  }

  try:
    room_owner.update_record(update_data)
    get_logger().info("room_owner record updated successfully")
  except Exception as e:
    get_logger().error("failed to update room_owner record: {}".format(e))
    raise e

##
## test: delete room_owner record
##
def test_delete_room_owner_record(db:SocialMediaStreamDataBase = None):
  """
  Test deleting a room_owner record from the room_owner table.
  """
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## create room_owner table if not exists
  ##
  room_owner = RoomOwnerV2Table(db_instance=db)

  ##
  ## delete record by room_id
  ##
  try:
    room_owner.delete_record({'room_id': '7362550606306773794'})
    get_logger().info("room_owner record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete room_owner record: {}".format(e))
    raise e

##
## >>================================ main method ===============================>>
##
if __name__ == "__main__":
  db = SocialMediaStreamDataBase(**get_test_db_config())

  ##
  ## room_owner table
  ##
  test_check_room_owner_table_exists(db)
  test_create_room_owner_table(db)
  test_insert_room_owner_record(db)
  test_check_room_owner_table_exists(db)
  test_get_room_owner_record(db)
  test_update_room_owner_record(db)
  test_delete_room_owner_record(db)
  test_drop_room_owner_table(db)
  test_check_room_owner_table_exists(db)
