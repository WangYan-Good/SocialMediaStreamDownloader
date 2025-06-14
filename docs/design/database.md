# 数据库设计

## 概述

用户表
- 用户ID
- 用户名
- 用户密码
- 用户联系方式

## 抖音

作者信息表
```shell
+----------------+-----------+------+-----+---------+-------+
| Field          | Type      | Null | Key | Default | Extra |
+----------------+-----------+------+-----+---------+-------+
| owner_user_id  | char(200) | NO   | PRI | NULL    |       |
| sec_user_id    | char(200) | YES  |     | NULL    |       |
| nickname       | char(20)  | YES  |     | NULL    |       |
| post_share_url | char(100) | YES  |     | NULL    |       |
| live_share_url | char(100) | YES  |     | NULL    |       |
| directory_name | char(100) | YES  |     | NULL    |       |
| user_status    | char(100) | YES  |     | NULL    |       |
| actived_count  | int       | NO   |     | 0       |       |
+----------------+-----------+------+-----+---------+-------+
```

喜爱的作者表
```shell
+---------------+-----------+------+-----+---------+-------+
| Field         | Type      | Null | Key | Default | Extra |
+---------------+-----------+------+-----+---------+-------+
| owner_user_id | char(200) | NO   | PRI | NULL    |       |
| platform      | char(20)  | YES  |     | NULL    |       |
| level         | int       | NO   |     | 0       |       |
+---------------+-----------+------+-----+---------+-------+
```
直播记录
  - 时间戳(ms)
  - 直播状态(status_code)
  - 直播间信息
    - *AnchorABMap
    - *熟悉状态(acquaintance_status)
    - 管理员列表(admin_user_ids)
    - *管理员开放ID(admin_user_open_ids)
    - *anchor_scheduled_time_text
    - 锚定分享文本(anchor_share_text)
    - *锚定标签类型(anchor_tab_type)
    - *app_id
    - *assist_label_list
    - 作者地址(auth_city)
    - *自动封面(auto_cover)
    - *基本类别(base_category)
    - *book_end_time
    - *book_time
    - 商业直播(business_live)
    - category
    - cell_style
    - challenge_info
    - city_top_distance
    - client_version
    - 评论区(comment_box)
      - 占位符(placeholder)
    - 评论名称模式(comment_name_mode)
    - common_label_list
    - content_tag
    - 封面(cover)
    - 创建时间(create_time/s)
    - 弹幕详情(danmaku_detail)
    
    - 当前观众人数
    - 管理员信息 admin_user_ids
    - 分享链接文本 anchor_share_text
    - 商业直播 business_live
    - 基础类型 base_category
    - 类别 category: 2969
    - cell_style: 3
    - 封面 cover
    - 主播信息
    - 城市 auth_city
观众人次

```yml
  data:
    room:
      AnchorABMap: {}
      acquaintance_status: 0
      admin_user_open_ids: []
      anchor_scheduled_time_text: ''
      anchor_tab_type: 0
      app_id: 1128
      assist_label_list: []
      auto_cover: 0
      base_category: 0
      book_end_time: 0
      book_time: 0
      challenge_info: ''
      city_top_distance: ''
      client_version: 290200
      comment_box:
        placeholder: "\u8BF4\u70B9\u4EC0\u4E48..."
      comment_name_mode: 0
      common_label_list: ''
      content_tag: ''
      cover:
        avg_color: '#A3897C'
        flex_setting_list: []
        height: 0
        image_type: 0
        is_animated: false
        open_web_url: ''
        text_setting_list: []
        uri: webcast-cover/7021106520540711712
        url_list:
        - https://p3-webcast-sign.douyinpic.com/webcast-cover/7021106520540711712~tplv-qz53dukwul-common-resize:0:0.image?biz_tag=aweme_webcast&from=webcast.room.pack&l=202502231706117471BF8451DEE31425FC&lk3s=39e7556e&s=reflow_room_info&sc=webcast_cover&x-expires=1742893571&x-signature=7xMRTQOgFFJVNm107UFLP5yeDoA%3D
        - https://p11-webcast-sign.douyinpic.com/webcast-cover/7021106520540711712~tplv-qz53dukwul-common-resize:0:0.image?biz_tag=aweme_webcast&from=webcast.room.pack&l=202502231706117471BF8451DEE31425FC&lk3s=39e7556e&s=reflow_room_info&sc=webcast_cover&x-expires=1742893571&x-signature=qXezgz6mstQx0WXifHRhssOgvKg%3D
        width: 0
      create_time: 1711548627
      danmaku_detail: 0
      deco_list: []
      distance: ''
      distance_city: ''
      distance_km: ''
      dynamic_cover_dict: {}
      dynamic_cover_uri: ''
      enable_room_perspective: true
      extra:
        create_scene: ''
        facial_unrecognised: 0
        geo_block: 0
        is_sandbox: false
        is_virtual_anchor: false
        limit_appid: ''
        limit_strategy: 0
        realtime_playback_qualities: []
        realtime_playback_shift: 0
        realtime_playback_start_shift: 0
        realtime_replay_enabled: false
        vr_type: 0
        vs_type: 0
        xigua_uid: 0
      fans_group_admin_user_ids: []
      fans_group_admin_user_open_ids: []
      fansclub_msg_style: 0
      fcdn_appid: 0
      feed_room_label:
        avg_color: '#7A5353'
        content:
          alternative_text: ''
          font_color: ''
          level: 0
          name: ''
        flex_setting_list: []
        height: 0
        image_type: 0
        is_animated: false
        open_web_url: ''
        text_setting_list: []
        uri: webcast/2ea90002aca1159b5c67
        url_list:
        - https://p3-webcast.douyinpic.com/img/webcast/2ea90002aca1159b5c67~tplv-resize:0:0.image
        - https://p11-webcast.douyinpic.com/img/webcast/2ea90002aca1159b5c67~tplv-resize:0:0.image
        width: 0
      filter_words: []
      finish_reason: 1
      finish_time: 1711556816
      finish_url: ''
      follow_msg_style: 0
      forum_extra_data: ''
      game_room_type: 0
      gift_msg_style: 2
      group_id: 0
      group_source: 0
      guide_button:
        avg_color: '#7A6D53'
        flex_setting_list: []
        height: 0
        image_type: 0
        is_animated: false
        open_web_url: ''
        text_setting_list: []
        uri: webcast/aweme_button_togather_3x.png
        url_list:
        - https://p3-webcast.douyinpic.com/img/webcast/aweme_button_togather_3x.png~tplv-resize:0:0.image
        - https://p11-webcast.douyinpic.com/img/webcast/aweme_button_togather_3x.png~tplv-resize:0:0.image
        width: 0
      has_commerce_goods: false
      has_promotion_games: 0
      highlight: false
      hot_sentence_info: ''
      id: 7351045287940524851
      id_str: '7351045287940524851'
      introduction: ''
      is_need_check_list: false
      is_official_channel_room: false
      is_replay: false
      is_show_inquiry_ball: false
      is_show_user_card_switch: true
      item_explicit_info: ''
      last_ping_time: 0
      layout: 0
      like_count: 61605
      linker_map: {}
      linkmic_display_type: 0
      linkmic_layout: 1
      live_distribution: []
      live_id: 1
      live_platform_source: ''
      live_room_mode: 0
      live_type_audio: false
      live_type_linkmic: false
      live_type_normal: true
      live_type_official: false
      live_type_sandbox: false
      live_type_screenshot: false
      live_type_third_party: false
      live_type_vs_live: false
      live_type_vs_premiere: false
      living_room_attrs:
        admin_flag: 0
        rank: 0
        room_id: 7351045287940524851
        room_id_str: '7351045287940524851'
        silence_flag: 0
      location: ''
      lottery_finish_time: 0
      luckymoney_num: 0
      mosaic_status: 0
      mosaic_tip: ''
      official_channel_open_id: ''
      official_channel_uid: 0
      orientation: 0
      os_type: 1
      owner:
        adversary_authorization_info: 3
        adversary_user_status: 0
        age_range: 0
        allow_be_located: false
        allow_find_by_contacts: false
        allow_others_download_video: false
        allow_others_download_when_sharing_video: false
        allow_share_show_profile: false
        allow_show_in_gossip: false
        allow_show_my_action: false
        allow_strange_comment: false
        allow_unfollower_comment: false
        allow_use_linkmic: false
        authorization_info: 3
        avatar_large:
          avg_color: ''
          flex_setting_list: []
          height: 0
          image_type: 0
          is_animated: false
          open_web_url: ''
          text_setting_list: []
          uri: 1080x1080/aweme-avatar/tos-cn-avt-0015_8bd362f00f33a506181a46cb287fed58
          url_list:
          - https://p11.douyinpic.com/aweme/1080x1080/aweme-avatar/tos-cn-avt-0015_8bd362f00f33a506181a46cb287fed58.jpeg?from=3067671334
          - https://p3.douyinpic.com/aweme/1080x1080/aweme-avatar/tos-cn-avt-0015_8bd362f00f33a506181a46cb287fed58.jpeg?from=3067671334
          - https://p26.douyinpic.com/aweme/1080x1080/aweme-avatar/tos-cn-avt-0015_8bd362f00f33a506181a46cb287fed58.jpeg?from=3067671334
          width: 0
        avatar_medium:
          avg_color: ''
          flex_setting_list: []
          height: 0
          image_type: 0
          is_animated: false
          open_web_url: ''
          text_setting_list: []
          uri: 720x720/aweme-avatar/tos-cn-avt-0015_8bd362f00f33a506181a46cb287fed58
          url_list:
          - https://p11.douyinpic.com/aweme/720x720/aweme-avatar/tos-cn-avt-0015_8bd362f00f33a506181a46cb287fed58.jpeg?from=3067671334
          - https://p3.douyinpic.com/aweme/720x720/aweme-avatar/tos-cn-avt-0015_8bd362f00f33a506181a46cb287fed58.jpeg?from=3067671334
          - https://p26.douyinpic.com/aweme/720x720/aweme-avatar/tos-cn-avt-0015_8bd362f00f33a506181a46cb287fed58.jpeg?from=3067671334
          width: 0
        avatar_thumb:
          avg_color: ''
          flex_setting_list: []
          height: 0
          image_type: 0
          is_animated: false
          open_web_url: ''
          text_setting_list: []
          uri: 100x100/aweme-avatar/tos-cn-avt-0015_8bd362f00f33a506181a46cb287fed58
          url_list:
          - https://p26.douyinpic.com/aweme/100x100/aweme-avatar/tos-cn-avt-0015_8bd362f00f33a506181a46cb287fed58.jpeg?from=3067671334
          - https://p3.douyinpic.com/aweme/100x100/aweme-avatar/tos-cn-avt-0015_8bd362f00f33a506181a46cb287fed58.jpeg?from=3067671334
          - https://p11.douyinpic.com/aweme/100x100/aweme-avatar/tos-cn-avt-0015_8bd362f00f33a506181a46cb287fed58.jpeg?from=3067671334
          width: 0
        badge_image_list:
        - avg_color: ''
          content:
            alternative_text: "\u8363\u8A89\u7B49\u7EA728\u7EA7\u52CB\u7AE0"
            font_color: ''
            level: 28
            name: ''
          flex_setting_list: []
          height: 16
          image_type: 1
          is_animated: false
          open_web_url: ''
          text_setting_list: []
          uri: webcast/new_user_grade_level_v1_28.png
          url_list:
          - https://p11-webcast.douyinpic.com/img/webcast/new_user_grade_level_v1_28.png~tplv-obj.image
          - https://p3-webcast.douyinpic.com/img/webcast/new_user_grade_level_v1_28.png~tplv-obj.image
          width: 32
        badge_image_list_v2:
        - avg_color: ''
          content:
            alternative_text: "\u8363\u8A89\u7B49\u7EA728\u7EA7\u52CB\u7AE0"
            font_color: ''
            level: 28
            name: ''
          flex_setting_list: []
          height: 16
          image_type: 1
          is_animated: false
          open_web_url: ''
          text_setting_list: []
          uri: webcast/new_user_grade_level_v1_28.png
          url_list:
          - https://p11-webcast.douyinpic.com/img/webcast/new_user_grade_level_v1_28.png~tplv-obj.image
          - https://p3-webcast.douyinpic.com/img/webcast/new_user_grade_level_v1_28.png~tplv-obj.image
          width: 32
        bg_img_url: ''
        birthday: 0
        birthday_description: ''
        birthday_valid: false
        block_status: 0
        city: "\u5929\u6D25"
        comment_restrict: 0
        commerce_webcast_config_ids: []
        constellation: ''
        consume_diamond_level: 0
        create_time: 0
        desensitized_nickname: ''
        disable_ichat: 0
        display_id: '89681716730'
        enable_ichat_img: 0
        exp: 0
        experience: 0
        fan_ticket_count: 0
        fans_club:
          data:
            anchor_id: 0
            anchor_open_id: ''
            available_gift_ids: []
            badge:
              icons:
                '0':
                  avg_color: ''
                  flex_setting_list: []
                  height: 0
                  image_type: 0
                  is_animated: false
                  open_web_url: ''
                  text_setting_list: []
                  uri: ''
                  url_list: []
                  width: 0
              title: ''
            badge_type: 0
            club_name: ''
            guard_expired_time: 0
            level: 0
            user_fans_club_status: 0
            user_guard_status: 0
          prefer_data: {}
        fans_group_info:
          list_fans_group_url: sslocal://webcast_lynxview?height=754&radius=8&gravity=bottom&type=popup&animation_type=present&url=https%3A%2F%2Flf-webcast-sourcecdn-tos.bytegecko.com%2Fobj%2Fbyte-gurd-source%2Fwebcast%2Fmono%2Flynx%2Fdouyin_lynx_fansclub%2Ftemplate%2Fpages%2Ffansclub%2Ffans_group%2Fuser%2Ftemplate.js&load_taro=0&fallback_url=sslocal%3A%2F%2Fwebcast_webview%3Furl%3Dhttps%253A%252F%252Flf-webcast-sourcecdn-tos.bytegecko.com%252Fobj%252Fbyte-gurd-source%252Fwebcast%252Fmono%252Flynx%252Fdouyin_lynx_fansclub%252Ftemplate%252Fpages%252Ffansclub%252Ffans_group%252Fuser%252Findex.html%26type%3Dpopup%26gravity%3Dbottom%26height%3D754%26radius%3D8%26load_taro%3D0
        fold_stranger_chat: false
        follow_info:
          follow_status: 0
          follower_count: 414440
          follower_count_str: "41.4\u4E07"
          following_count: 155
          following_count_str: '155'
          invalid_follow_status: false
          push_status: 0
          remark_name: ''
        follow_status: 0
        gender: 2
        hotsoon_verified: false
        hotsoon_verified_reason: ''
        ichat_restrict_type: 0
        id: 343476932459843
        id_str: '343476932459843'
        income_share_percent: 0
        is_anonymous: false
        is_follower: false
        is_following: false
        j_accredit_info:
          JAccreditAdvance: 0
          JAccreditBasic: 0
          JAccreditContent: 0
          JAccreditLive: 0
        level: 0
        link_mic_stats: 0
        location_city: "\u5929\u6D25"
        media_badge_image_list: []
        modify_time: 1740272884
        mystery_man: 1
        need_profile_guide: false
        new_real_time_icons: []
        nickname: "\u9526\u9CA4\u4F1A\u8DF3\u821E\uFF08\u5FAE\u80D6\u5929\u82B1\u677F\
          \uFF09"
        pay_grade:
          grade_banner: ''
          grade_describe: ''
          grade_describe_shining: false
          grade_icon_list: []
          level: 28
          name: ''
          new_im_icon_with_level:
            avg_color: ''
            flex_setting_list: []
            height: 16
            image_type: 1
            is_animated: false
            open_web_url: ''
            text_setting_list: []
            uri: webcast/new_user_grade_level_v1_28.png
            url_list:
            - https://p11-webcast.douyinpic.com/img/webcast/new_user_grade_level_v1_28.png~tplv-obj.image
            - https://p3-webcast.douyinpic.com/img/webcast/new_user_grade_level_v1_28.png~tplv-obj.image
            width: 32
          new_live_icon:
            avg_color: ''
            flex_setting_list: []
            height: 12
            image_type: 1
            is_animated: false
            open_web_url: ''
            text_setting_list: []
            uri: webcast/aweme_pay_grade_2x_25_29.png
            url_list:
            - https://p3-webcast.douyinpic.com/img/webcast/aweme_pay_grade_2x_25_29.png~tplv-obj.image
            - https://p11-webcast.douyinpic.com/img/webcast/aweme_pay_grade_2x_25_29.png~tplv-obj.image
            width: 12
          next_diamond: 0
          next_name: ''
          next_privileges: ''
          now_diamond: 0
          pay_diamond_bak: 0
          score: 0
          screen_chat_type: 0
          this_grade_max_diamond: 44000
          this_grade_min_diamond: 34000
          total_diamond_count: 0
          upgrade_need_consume: 0
        pay_score: 0
        pay_scores: 0
        public_area_oper_freq: 0
        push_comment_status: false
        push_digg: false
        push_follow: false
        push_friend_action: false
        push_ichat: false
        push_status: false
        push_video_post: false
        push_video_recommend: false
        real_time_icons: []
        remark_name: ''
        sec_uid: MS4wLjABAAAAcvZ0hP4dBGDyls8uy-YYvHk7A6h4O_PRXJvMmls0xXE
        secret: 0
        share_qrcode_uri: 31b470007cd3afe938fa3
        short_id: 89681716730
        signature: "\u5F88\u559C\u6B22\u5BFC\u822A\u91CC\u9762\u7684\u4E00\u53E5\u8BDD\
          \uFF0C\n\u5DF2\u4E3A\u60A8\u91CD\u65B0\u89C4\u5212\u8DEF\u7EBF\n\u6444\u5F71\
          \u5E08\U0001F933@\u674E\u4E0D\u4F1A\u98DE"
        special_id: ''
        status: 1
        subscribe:
          buy_type: 0
          identity_type: 0
          is_member: false
          level: 0
          open: 0
        telephone: ''
        ticket_count: 0
        top_fans: []
        top_vip_no: 0
        total_recharge_diamond_count: 0
        user_attr:
          admin_privileges: []
          is_admin: false
          is_muted: false
          is_super_admin: false
        user_canceled: false
        user_dress_info:
          dress_own_ids: []
          dress_wear_ids: []
        user_open_id: ''
        user_role: 0
        verified: true
        verified_content: ''
        verified_mobile: false
        verified_reason: ''
        watch_duration_month: 0
        web_rid: '466441982464'
        webcast_uid: MS4wLjO4SVHuOYjVLzfCwUa35kEly_rB0sFkJ-M6-4zD4XPf61dbFqeYKo_71VD1eQtGbgU
        with_car_management_permission: false
        with_commerce_permission: false
        with_fusion_shop_entry: false
      owner_device_id: 0
      owner_open_id: ''
      owner_user_id: 343476932459843
      pack_meta:
        cluster: default
        dc: lf
        env: prod
        extras: {}
        scene: reflow_room_info(prod_single_dc/rpc/topo)
        trace_id: ''
      paid_live_data:
        anchor_right: 0
        delivery: 0
        duration: 0
        max_preview_duration: 0
        need_delivery_notice: false
        paid_type: 0
        pay_ab_type: 0
        privilege_info: {}
        privilege_info_map: {}
        view_right: 0
      popularity: 0
      popularity_str: ''
      pre_enter_time: 0
      preview_copy: " \u6628\u5929\u64E6\u80A9\u800C\u8FC7\uFF0C\u4ECA\u5929\u4E0D\
        \u518D\u9519\u8FC7~"
      preview_flow_tag: 0
      private_info: ''
      ranklist_audience_type: 0
      real_distance: ''
      redpacket_audience_auth: 0
      relation_tag: ''
      replay: false
      replay_location: 0
      room_audit_status: 0
      room_auth:
        AIClone: 0
        AdminCommentWall: 0
        AnchorAudioChat: 0
        AnchorColdMessageTiled: 0
        AnchorHotMessageAggregated: 0
        AnchorMission: 0
        AudioChat: 0
        AudioChatTotext: 0
        Banner: 1
        BulletStyle: 0
        CanSellTicket: 0
        CastScreen: 0
        CastScreenExplicit: 0
        Chat: true
        ChatDispatch: 0
        ChatDynamicSlideSpeed: 0
        ChatDynamicSlideSpeedAnchor: 0
        ChatGuideEmoji: 0
        ChatGuideImage: 0
        ChatIdentity: 0
        ChatMention: 0
        ChatMentionV2: 0
        ChatOperate: 0
        ChatReply: 0
        ClearEntranceOption: 0
        Collect: 0
        CommentWall: 0
        CommerceCard: 1
        CommerceComponent: 0
        CommonCard: 0
        CountType: 0
        Danmaku: false
        DanmakuDefault: 0
        Denounce: 0
        Digg: true
        Dislike: 0
        DonationSticker: 0
        DouPlus: 0
        DouPlusPopularityGem: 0
        DownloadVideo: 0
        EcomFansClub: 0
        EmojiOutside: 0
        EnhancedTouch: 0
        EnterEffects: 0
        ExpandScreen: 0
        FansClub: 0
        FansClubBlessing: 0
        FansClubDeclaration: 0
        FansClubLetter: 0
        FansClubNotice: 0
        FansGroup: 0
        FeaturedPublicScreen: 0
        FirstFeedHistChat: 0
        FixedChat: 0
        FrequentlyChat: 0
        FusionEmoji: 0
        GamePointsPlaying: 0
        Gift: true
        GiftAnchorMt: 0
        GiftVote: 0
        Highlights: 0
        HostTeam: 0
        HostTeamChannel: 0
        HotChatTray: 0
        HourRank: 0
        ImHeatValue: 0
        IndustryService: 0
        InteractionGift: 0
        InteractiveComponent: 0
        ItemShare: 0
        KtvOrderSong: 0
        Landscape: 1
        LandscapeChat: 1
        LandscapeChatDynamicSlideSpeed: 0
        LandscapeGift: 0
        LandscapeScreenCapture: 0
        LandscapeScreenRecording: 0
        LandscapeScreenShare: 0
        Like: 0
        LinkmicGuestLike: 0
        LongPressOption: 0
        LongTouch: 0
        LuckMoney: true
        MarkUser: 0
        MediaHistoryMessage: 0
        MediaLinkmic: 0
        MessageDispatch: 0
        MessageGift: 0
        MissionCenter: 0
        MoreAnchor: 1
        MoreHistChat: 0
        MultiplierPlayback: 0
        MyLiveEntrance: 0
        OnlyTa: 0
        PCPlay: 0
        POI: true
        PadPlay: 0
        PanelECService: 0
        PlayerRankList: 0
        Poster: 0
        PosterCache: 0
        PreviewChatExpose: 0
        PreviewHotCommentSwitch: 0
        ProjectionBtn: 0
        Props: true
        PublicScreen: 1
        QuizGamePointsPlaying: 0
        RecordScreen: 2
        RoomChannel: 0
        RoomChatLikeDisplay: 0
        RoomChatOperatePanel: 0
        RoomContributor: false
        RoomWidget: 0
        ScreenBottomInfo: 0
        ScreenProjectionBarrage: 0
        Seek: 0
        Selection: 0
        SelectionAlbum: 0
        Share: 1
        ShortTouch: 0
        ShortTouchTempState: 0
        ShowGamePlugin: 0
        ShowQualification: 0
        SmallWindowDisplay: 0
        SmallWindowPlayer: 0
        StickyMessage: 0
        StreamAdaptation: 0
        StrokeUpDownGuide: 0
        SubscribeCardPackage: 0
        Teleprompter: 0
        TextGift: 0
        TimedShutdown: 0
        ToolbarBubble: 0
        Topic: 0
        TypingCommentState: 0
        UgcVSReplayDelete: 0
        UgcVsReplayVisibility: 0
        UpRightStatsFloatingLayer: 0
        UseHostInfo: 0
        UserCard: true
        UserCorner: 0
        VSGift: 0
        VSRank: 0
        VSTopic: 0
        VerticalRank: 0
        VerticalScreenShare: 0
        VideoAmplificationType: 0
        VideoShare: 0
        VsCommentBar: 0
        VsDouPlus: 0
        VsExtensionEnableFollow: 0
        VsFansClub: 0
        VsWelcomeDanmaku: 0
        WordAssociation: 0
      room_create_ab_param: ''
      room_layout: 0
      room_tabs: []
      room_tag: 0
      room_view_stats:
        display_long: "6.1\u4E07\u4EBA\u770B\u8FC7"
        display_long_anchor: "6.1\u4E07\u4EBA\u770B\u8FC7"
        display_middle: "6.1\u4E07\u4EBA\u770B\u8FC7"
        display_middle_anchor: "6.1\u4E07\u4EBA\u770B\u8FC7"
        display_short: "6.1\u4E07"
        display_short_anchor: "6.1\u4E07"
        display_type: 3
        display_value: 60917
        display_version: 1663849727
        incremental: true
        is_hidden: false
      screen_capture_sharing_title: ''
      scroll_config: ''
      search_id: 7351045298967285043
      sell_goods: false
      share_msg_style: 0
      share_url: https://webcast.amemv.com/douyin/webcast/reflow/7351045287940524851?did=MS4wLjABAAAANwkJuWIRFOzg5uCpDRpMj4OX-QryoDgn-yYlXQnRwQQ&iid=MS4wLjABAAAANwkJuWIRFOzg5uCpDRpMj4OX-QryoDgn-yYlXQnRwQQ&with_sec_did=1&sec_user_id=MS4wLjABAAAAcvZ0hP4dBGDyls8uy-YYvHk7A6h4O_PRXJvMmls0xXE
      sharing_music_id_list: []
      short_title: ''
      short_touch_area_config:
        elements:
          '1':
            priority: 1
            type: 1
          '10':
            priority: 3
            type: 10
          '12':
            priority: 3
            type: 12
          '2':
            priority: 1
            type: 2
          '22':
            priority: 1
            type: 22
          '27':
            priority: 3
            type: 27
          '3':
            priority: 1
            type: 3
          '30':
            priority: 2
            type: 30
          '4':
            priority: 3
            type: 4
          '5':
            priority: 4
            type: 5
          '6':
            priority: 3
            type: 6
          '7':
            priority: 3
            type: 7
          '8':
            priority: 3
            type: 8
          '9':
            priority: 3
            type: 9
        forbidden_types_map: {}
        strategy_feat_whitelist:
        - feat_coin_lottery_amount
        - feat_redpack_amount
        - live_short_touch_ecom_redpack_type
        - live_short_touch_ecom_redpack_sub_type
        - live_short_touch_ecom_redpack_total_amount
        - live_short_touch_ecom_redpack_total_stock
        - live_ecom_cart_click_twice
        - live_ecom_cart_stop_buy
        - live_watch_6_min
        temp_state_condition_map:
          '1':
            minimum_gap: 900
            type:
              priority: 30
              strategy_type: 1
          '2':
            minimum_gap: 900
            type:
              priority: 20
              strategy_type: 2
          '3':
            minimum_gap: 900
            type:
              priority: 10
              strategy_type: 3
          '4':
            minimum_gap: 0
            type:
              priority: 1
              strategy_type: 4
          '5':
            minimum_gap: 0
            type:
              priority: 5
              strategy_type: 5
          '6':
            minimum_gap: 0
            type:
              priority: 7
              strategy_type: 6
          '7':
            minimum_gap: 0
            type:
              priority: 6
              strategy_type: 7
        temp_state_global_condition:
          allow_count: 1
          duration_gap: 300
          ignore_strategy_types:
          - 4
        temp_state_strategy:
          '136':
            short_touch_type: 136
            strategy_map:
              '1':
                duration: 30
                strategy_method: ''
                type:
                  priority: 30
                  strategy_type: 1
              '2':
                duration: 10
                strategy_method: ''
                type:
                  priority: 20
                  strategy_type: 2
          '141':
            short_touch_type: 141
            strategy_map:
              '1':
                duration: 30
                strategy_method: ''
                type:
                  priority: 30
                  strategy_type: 1
              '2':
                duration: 10
                strategy_method: ''
                type:
                  priority: 20
                  strategy_type: 2
              '3':
                duration: 10
                strategy_method: ''
                type:
                  priority: 10
                  strategy_type: 3
          '149':
            short_touch_type: 149
            strategy_map:
              '1':
                duration: 30
                strategy_method: ''
                type:
                  priority: 30
                  strategy_type: 1
              '2':
                duration: 10
                strategy_method: ''
                type:
                  priority: 20
                  strategy_type: 2
          '152':
            short_touch_type: 152
            strategy_map:
              '1':
                duration: 30
                strategy_method: ''
                type:
                  priority: 30
                  strategy_type: 1
              '2':
                duration: 10
                strategy_method: ''
                type:
                  priority: 20
                  strategy_type: 2
          '153':
            short_touch_type: 153
            strategy_map:
              '1':
                duration: 10
                strategy_method: ''
                type:
                  priority: 30
                  strategy_type: 1
              '2':
                duration: 10
                strategy_method: ''
                type:
                  priority: 20
                  strategy_type: 2
              '4':
                duration: 10
                strategy_method: ''
                type:
                  priority: 1
                  strategy_type: 4
          '159':
            short_touch_type: 159
            strategy_map:
              '1':
                duration: 30
                strategy_method: ''
                type:
                  priority: 30
                  strategy_type: 1
          '161':
            short_touch_type: 161
            strategy_map:
              '1':
                duration: 30
                strategy_method: ''
                type:
                  priority: 30
                  strategy_type: 1
              '2':
                duration: 10
                strategy_method: ''
                type:
                  priority: 20
                  strategy_type: 2
          '210':
            short_touch_type: 210
            strategy_map:
              '1':
                duration: 30
                strategy_method: ''
                type:
                  priority: 30
                  strategy_type: 1
          '306':
            short_touch_type: 306
            strategy_map:
              '3':
                duration: 30
                strategy_method: test_temp_30
                type:
                  priority: 10
                  strategy_type: 3
          '307':
            short_touch_type: 307
            strategy_map:
              '4':
                duration: 15
                strategy_method: test_strategy_5
                type:
                  priority: 1
                  strategy_type: 4
          '308':
            short_touch_type: 308
            strategy_map:
              '5':
                duration: 10
                strategy_method: test_strategy_5
                type:
                  priority: 5
                  strategy_type: 5
          '311':
            short_touch_type: 311
            strategy_map:
              '3':
                duration: 30
                strategy_method: ''
                type:
                  priority: 10
                  strategy_type: 3
          '312':
            short_touch_type: 312
            strategy_map:
              '1':
                duration: 30
                strategy_method: ''
                type:
                  priority: 30
                  strategy_type: 1
          '313':
            short_touch_type: 313
            strategy_map:
              '2':
                duration: 30
                strategy_method: test_strategy_2
                type:
                  priority: 20
                  strategy_type: 2
          '4':
            short_touch_type: 4
            strategy_map:
              '1':
                duration: 10
                strategy_method: ''
                type:
                  priority: 30
                  strategy_type: 1
              '2':
                duration: 10
                strategy_method: ''
                type:
                  priority: 20
                  strategy_type: 2
              '3':
                duration: 10
                strategy_method: ''
                type:
                  priority: 10
                  strategy_type: 3
              '6':
                duration: 10
                strategy_method: ''
                type:
                  priority: 7
                  strategy_type: 6
              '7':
                duration: 10
                strategy_method: ''
                type:
                  priority: 6
                  strategy_type: 7
          '7':
            short_touch_type: 7
            strategy_map:
              '1':
                duration: 10
                strategy_method: ''
                type:
                  priority: 30
                  strategy_type: 1
              '2':
                duration: 10
                strategy_method: ''
                type:
                  priority: 20
                  strategy_type: 2
              '3':
                duration: 10
                strategy_method: ''
                type:
                  priority: 10
                  strategy_type: 3
              '4':
                duration: 0
                strategy_method: ''
                type:
                  priority: 1
                  strategy_type: 4
              '5':
                duration: 10
                strategy_method: ''
                type:
                  priority: 5
                  strategy_type: 5
              '6':
                duration: 10
                strategy_method: ''
                type:
                  priority: 7
                  strategy_type: 6
          '8':
            short_touch_type: 8
            strategy_map:
              '1':
                duration: 30
                strategy_method: ''
                type:
                  priority: 30
                  strategy_type: 1
              '2':
                duration: 10
                strategy_method: ''
                type:
                  priority: 20
                  strategy_type: 2
          '97':
            short_touch_type: 97
            strategy_map:
              '1':
                duration: 30
                strategy_method: ''
                type:
                  priority: 30
                  strategy_type: 1
              '2':
                duration: 10
                strategy_method: ''
                type:
                  priority: 20
                  strategy_type: 2
              '3':
                duration: 30
                strategy_method: ''
                type:
                  priority: 10
                  strategy_type: 3
              '5':
                duration: 10
                strategy_method: short_touch_tempstate_redpack_entry_type
                type:
                  priority: 5
                  strategy_type: 5
              '6':
                duration: 10
                strategy_method: short_touch_tempstate_redpack_match_amunt
                type:
                  priority: 7
                  strategy_type: 6
              '7':
                duration: 10
                strategy_method: short_touch_tempstate_redpack_user_wish_tobuy
                type:
                  priority: 6
                  strategy_type: 7
      sofa_layout: 0
      stamps: ''
      start_time: 1711548632
      stats:
        comment_count: 0
        digg_count: 0
        dou_plus_promotion: ''
        enter_count: 0
        fan_ticket: 0
        follow_count: 673
        gift_uv_count: 0
        id: 7351045287940524851
        id_str: '7351045287940524851'
        like_count: 0
        money: 0
        total_user: 46531
        total_user_desp: ''
        total_user_str: "4\u4E07+"
        up_right_stats_str: ''
        up_right_stats_str_complete: ''
        user_count_composition:
          city: 0
          my_follow: 0
          other: 1
          video_detail: 0
        user_count_str: '0'
        watermelon: 0
        welfare_donation_amount: 0
      status: 4
      stream_close_time: 0
      stream_id: 114860083778682911
      stream_id_str: '114860083778682911'
      stream_provider: 0
      stream_url:
        candidate_resolution: []
        complete_push_urls: []
        default_resolution: FULL_HD1
        extra:
          anchor_interact_profile: 0
          audience_interact_profile: 0
          bframe_enable: false
          bitrate_adapt_strategy: 0
          bytevc1_enable: false
          default_bitrate: 0
          fps: 0
          gop_sec: 0
          h265_enable: false
          hardware_encode: false
          height: 1280
          max_bitrate: 0
          min_bitrate: 0
          roi: false
          sw_roi: false
          video_profile: 0
          width: 720
        flv_pull_url:
          FULL_HD1: http://pull-flv-l6.douyincdn.com/stage/stream-114860083778682911_or4.flv?k=a03a8b38ad97673a&t=1740906371&unique_id=stream-114860083778682911_31_flv_or4
        flv_pull_url_params: {}
        hls_pull_url: http://pull-hls-l6.douyincdn.com/stage/stream-114860083778682911_or4/index.m3u8?k=cf94b05618a591d2&t=1740906371
        hls_pull_url_map:
          FULL_HD1: http://pull-hls-l6.douyincdn.com/stage/stream-114860083778682911_or4/index.m3u8?k=cf94b05618a591d2&t=1740906371
        hls_pull_url_params: '{"PlayingIntervalMs":20000,"P2PFastOpenDuration":-1500,"VCodec":"h264","BufferDataMs":1000,"FastOpenDuration":-500,"NetworkAdapt":{"Enabled":0,"HurryTime":3500,"HurryType":0,"SlowMillisecond":90,"HurrySpeed":1.1,"HurryStartMs":4000,"SlowSpeed":1,"SlowTime":90,"HurryMillisecond":3500,"HurryStopType":1}}'
        id: 114860083778682911
        id_str: '114860083778682911'
        live_core_sdk_data:
          pull_data:
            Flv: []
            Hls: []
            codec: ''
            compensatory_data: ''
            hls_data_unencrypted: {}
            kind: 0
            options:
              default_quality:
                additional_content: ''
                disable: 0
                fps: 0
                level: 0
                name: "\u6807\u6E05"
                resolution: ''
                sdk_key: origin
                v_bit_rate: 0
                v_codec: ''
              qualities:
              - additional_content: ''
                disable: 0
                fps: 0
                level: 1
                name: "\u6807\u6E05"
                resolution: ''
                sdk_key: origin
                v_bit_rate: 0
                v_codec: '264'
              vpass_default: false
            stream_data: '{"common":{"ts":"1740301571","session_id":"037-202502231706117471BF8451DEE31425FC","stream":"114860083778682911","rule_ids":"{\"ab_version_trace\":null,\"sched\":\"{\\\"result\\\":{\\\"hit\\\":\\\"default\\\",\\\"cdn\\\":39}}\"}","common_trace":"{\"StrategyTrace\":{\"Neptune\":{\"PlayStream\":{\"ids\":null}}},\"BusinessType\":\"\",\"BigeventAnchorLevel\":\"\"}","app_id":"100100","major_anchor_level":"","mode":"Normal","lines":{"main":"line_39"},"p2p_params":null,"stream_data_content_encoding":"default","common_sdk_params":{"main":"{}"},"stream_name":"stream-114860083778682911","main_push_id":31,"backup_push_id":0},"data":{"origin":{"main":{"flv":"http://pull-flv-l6.douyincdn.com/stage/stream-114860083778682911_or4.flv?k=a03a8b38ad97673a&t=1740906371&unique_id=stream-114860083778682911_31_flv_or4","hls":"http://pull-hls-l6.douyincdn.com/stage/stream-114860083778682911_or4/index.m3u8?k=cf94b05618a591d2&t=1740906371","cmaf":"","dash":"","lls":"http://pull-lls-l6.douyincdn.com/stage/stream-114860083778682911_or4.sdp?k=d73be117b578e4c1&t=1740906371&unique_id=stream-114860083778682911_31_lls_or4","tsl":"","tile":"","http_ts":"","ll_hls":"","sdk_params":"{\"PlayingIntervalMs\":20000,\"P2PFastOpenDuration\":-1500,\"VCodec\":\"h264\",\"BufferDataMs\":1000,\"FastOpenDuration\":-500,\"NetworkAdapt\":{\"Enabled\":0,\"HurryTime\":3500,\"HurryType\":0,\"SlowMillisecond\":90,\"HurrySpeed\":1.1,\"HurryStartMs\":4000,\"SlowSpeed\":1,\"SlowTime\":90,\"HurryMillisecond\":3500,\"HurryStopType\":1},\"vbitrate\":0,\"resolution\":\"\",\"gop\":4,\"drType\":\"sdr\"}","enableEncryption":false}},"ao":{"main":{"flv":"http://pull-flv-l6.douyincdn.com/stage/stream-114860083778682911.flv?k=5c03106c35c2a82b&only_audio=1&t=1740906371&unique_id=stream-114860083778682911_31_flv","hls":"","cmaf":"","dash":"","lls":"","tsl":"","tile":"","http_ts":"","ll_hls":"","sdk_params":"{\"BufferDataMs\":1000,\"FastOpenDuration\":-500,\"NetworkAdapt\":{\"Enabled\":0,\"HurryType\":0,\"HurryStartMs\":4000,\"HurrySpeed\":1.1,\"SlowSpeed\":1,\"HurryMillisecond\":3500,\"HurryStopType\":1,\"HurryTime\":3500,\"SlowMillisecond\":90,\"SlowTime\":90},\"PlayingIntervalMs\":20000,\"P2PFastOpenDuration\":-1500,\"VCodec\":\"h264\",\"vbitrate\":0,\"resolution\":\"\",\"gop\":4,\"drType\":\"sdr\"}","enableEncryption":false}},"md":{"main":{"flv":"https://pull-flv-l6-admin.douyincdn.com/stage/stream-114860083778682911_md.flv?k=0c04f6395fe8f5cd&t=1740906371&unique_id=stream-114860083778682911_31_flv_md","hls":"http://pull-hls-l6.douyincdn.com/stage/stream-114860083778682911_md/index.m3u8?k=8681d2ee9ebdf04c&t=1740906371","cmaf":"","dash":"","lls":"http://pull-lls-l6.douyincdn.com/stage/stream-114860083778682911_md.sdp?k=d392cad9d9272af1&t=1740906371&unique_id=stream-114860083778682911_31_lls_md","tsl":"","tile":"","http_ts":"","ll_hls":"","sdk_params":"{\"BufferDataMs\":1000,\"VCodec\":\"h264\",\"FastOpenDuration\":-500,\"NetworkAdapt\":{\"HurryStartMs\":4000,\"SlowSpeed\":1,\"SlowTime\":90,\"HurrySpeed\":1.1,\"Enabled\":0,\"HurryMillisecond\":3500,\"HurryStopType\":1,\"HurryTime\":3500,\"HurryType\":0,\"SlowMillisecond\":90},\"PlayingIntervalMs\":20000,\"P2PFastOpenDuration\":-1500,\"vbitrate\":250000,\"resolution\":\"240P\",\"gop\":4,\"drType\":\"sdr\",\"fps\":15}","enableEncryption":false}}}}'
            version: 0
          size: ''
        provider: 0
        pull_datas: {}
        push_datas: {}
        push_stream_type: 0
        push_urls: []
        resolution_name:
          FULL_HD1: "\u84DD\u5149"
          HD1: "\u8D85\u6E05"
          ORIGION: "\u539F\u753B"
          SD1: "\u6807\u6E05"
          SD2: "\u9AD8\u6E05"
        rtmp_pull_url: http://pull-flv-l6.douyincdn.com/stage/stream-114860083778682911_or4.flv?k=a03a8b38ad97673a&t=1740906371&unique_id=stream-114860083778682911_31_flv_or4
        rtmp_pull_url_params: '{"PlayingIntervalMs":20000,"P2PFastOpenDuration":-1500,"VCodec":"h264","BufferDataMs":1000,"FastOpenDuration":-500,"NetworkAdapt":{"Enabled":0,"HurryTime":3500,"HurryType":0,"SlowMillisecond":90,"HurrySpeed":1.1,"HurryStartMs":4000,"SlowSpeed":1,"SlowTime":90,"HurryMillisecond":3500,"HurryStopType":1}}'
        rtmp_push_url: ''
        rtmp_push_url_params: ''
        stream_control_type: 0
        stream_orientation: 1
        vr_type: 0
      sun_daily_icon_content: ''
      tags: []
      title: "\u58F0\u97F3\u6CBB\u6108 \u611F\u6069\u77E5\u9047"
      title_recommend: false
      top_fans: []
      toutiao_cover_recommend_level: 0
      toutiao_title_recommend_level: 0
      upper_right_widget_data_list: []
      use_filter: false
      user_count: 0
      user_share_text: "#\u5728\u6296\u97F3\uFF0C\u8BB0\u5F55\u7F8E\u597D\u751F\u6D3B\
        #\u3010\u9526\u9CA4\u4F1A\u8DF3\u821E\uFF08\u5FAE\u80D6\u5929\u82B1\u677F\uFF09\
        \u3011\u6B63\u5728\u76F4\u64AD\uFF0C\u6765\u548C\u6211\u4E00\u8D77\u652F\u6301\
        Ta\u5427\u3002\u590D\u5236\u4E0B\u65B9\u94FE\u63A5\uFF0C\u6253\u5F00\u3010\
        \u6296\u97F3\u3011\uFF0C\u76F4\u63A5\u89C2\u770B\u76F4\u64AD\uFF01"
      vertical_cover_uri: ''
      vid: ''
      video_feed_tag: "\u76F4\u64AD\u4E2D"
      visibility_range: 0
      vs_main_replay_id: 0
      vs_roles: []
      wait_copy: "\u8010\u5FC3\u548C\u6301\u4E45\u80DC\u8FC7\u6FC0\u70C8\u548C\u72C2\
        \u70ED"
      web_count: 0
      webcast_comment_tcs: 0
      webcast_sdk_version: 0
      with_aggregate_column: false
      with_draw_something: false
      with_ktv: false
      with_linkmic: false
    user:
      adversary_authorization_info: 0
      adversary_user_status: 0
      age_range: 0
      allow_be_located: false
      allow_find_by_contacts: false
      allow_others_download_video: false
      allow_others_download_when_sharing_video: false
      allow_share_show_profile: false
      allow_show_in_gossip: false
      allow_show_my_action: false
      allow_strange_comment: false
      allow_unfollower_comment: false
      allow_use_linkmic: false
      authorization_info: 0
      badge_image_list: []
      badge_image_list_v2: []
      bg_img_url: ''
      birthday: 0
      birthday_description: ''
      birthday_valid: false
      block_status: 0
      city: ''
      comment_restrict: 0
      commerce_webcast_config_ids: []
      constellation: ''
      consume_diamond_level: 0
      create_time: 0
      desensitized_nickname: ''
      disable_ichat: 0
      display_id: ''
      enable_ichat_img: 0
      exp: 0
      experience: 0
      fan_ticket_count: 0
      fold_stranger_chat: false
      follow_status: 0
      gender: 0
      hotsoon_verified: false
      hotsoon_verified_reason: ''
      ichat_restrict_type: 0
      id: 0
      id_str: ''
      income_share_percent: 0
      is_anonymous: false
      is_follower: false
      is_following: false
      level: 0
      link_mic_stats: 0
      location_city: ''
      media_badge_image_list: []
      modify_time: 0
      mystery_man: 0
      need_profile_guide: false
      new_real_time_icons: []
      nickname: ''
      pay_score: 0
      pay_scores: 0
      public_area_oper_freq: 0
      push_comment_status: false
      push_digg: false
      push_follow: false
      push_friend_action: false
      push_ichat: false
      push_status: false
      push_video_post: false
      push_video_recommend: false
      real_time_icons: []
      remark_name: ''
      sec_uid: ''
      secret: 0
      share_qrcode_uri: ''
      short_id: 0
      signature: ''
      special_id: ''
      status: 0
      telephone: ''
      ticket_count: 0
      top_fans: []
      top_vip_no: 0
      total_recharge_diamond_count: 0
      user_canceled: false
      user_open_id: ''
      user_role: 0
      verified: false
      verified_content: ''
      verified_mobile: false
      verified_reason: ''
      watch_duration_month: 0
      web_rid: ''
      webcast_uid: ''
      with_car_management_permission: false
      with_commerce_permission: false
      with_fusion_shop_entry: false
  extra:
    now: 1740301571630
  status_code: 0
```