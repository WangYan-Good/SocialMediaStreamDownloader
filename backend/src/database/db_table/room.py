##
## database table room topology
# data
# ├── 1. share_url
# ├── 2. favorite_owner
# ├── 3. live_record
# ├── 4. room_attribute
# │   ├── 4-1. room_admin_user_id
# │   ├── 4-2. room_admin_user_open_id
# │   ├── 4-3. room_assist_label - TBD
# │   ├── 4-4. room_deco - TBD
# │   ├── 4-5. room_realtime_playback_quality - TBD
# │   ├── 4-6. fans_group_admin_user_id
# │   ├── 4-7. fans_group_admin_user_open_id
# │   ├── 4-8. room_filter_word - TBD
# │   ├── 4-9. room_live_distribution - TBD
# │   ├── 4-10. room_owner
# │   │   ├── 4-10-1. badge_image
# │   │   ├── 4-10-2. commerce_webcast_config_id - TBD
# │   │   ├── 4-10-3. fans_club
# │   │   │   ├── 4-10-3-1. fans_club_available_gift_id
# │   │   │   └── 4-10-3-2. fans_club_badge_icon
# │   │   ├── 4-10-4. media_badge_image - TBD
# │   │   ├── 4-10-5. new_real_time_icon - TBD
# │   │   ├── 4-10-6. pay_grade_icon
# │   │   ├── 4-10-7. room_owner_real_time_icon - TBD
# │   │   ├── 4-10-8. room_subscribe
# │   │   ├── 4-10-9. room_owner_top_fans - TBD
# │   │   ├── 4-10-10. room_owner_user_attr
# │   │   │   └── 4-10-10-1. room_admin_privilege
# │   │   ├── 4-10-11. room_owner_user_dress_own_id
# │   │   └── 4-10-12. room_owner_dress_wear_id
# │   ├── 4-11. room_pack_meta
# |   ├── 4-12. room_paid_live_data
# |   ├── 4-13. room_auth
# |   ├── 4-14. room_tab
# │   ├── 4-15. room_sharing_music_id
# |   └── 4-16. room_short_touch_area_config
# |       ├── 4-16-1. room_short_touch_area_config_element
# |       ├── 4-16-2. room_short_touch_area_config_strategy_feat_whitelist
# |       ├── 4-16-3. room_temp_state_condition_map
# |       |   └── 4-16-3-1. room_temp_state_global_condition_ignore_strategy_type
# |       └── 4-16-4. room_temp_state_global_condition
# ├── 5. room_record
# ├── 6. live_stream
# |   ├── 6-1. stream_candidate_resolution
# |   ├── 6-2. stream_complete_push_url
# |   ├── 6-3. live_core_sdk_data
# |   |   └── 6-3-1. live_core_sdk_pull_data
# |   |       ├── 6-3-1-1. live_core_sdk_pull_flv_data
# |   |       ├── 6-3-1-2. live_core_sdk_pull_hls_data
# |   |       └── 6-3-1-3. live_core_sdk_pull_data_option
# |   |           ├── 6-3-1-3-1. live_core_sdk_pull_quality_data
# |   |           └── 6-3-1-3-2. live_core_sdk_pull_default_quality_data
# |   └── 6-4. stream_push_url
# ├── 7. room_tag
# ├── 8. room_top_fans
# ├── 9. room_upper_right_widget_data
# ├── 10. room_vs_role
# ├── 11. picture
# │   ├── 11-1. picture_flex_setting
# │   ├── 11-2. picture_text_setting
# │   ├── 11-3. picture_url
# │   └── 11-4. picture_content
# └── 12. user
#     ├── 12-1. badge_image
#     ├── 12-2. commerce_webcast_config_id - TBD
#     ├── 12-3. media_badge_image - TBD
#     ├── 12-4. new_real_time_icon - TBD
#     ├── 12-5. room_owner_real_time_icon - TBD
#     └── 12-6. room_owner_top_fans - TBD
#