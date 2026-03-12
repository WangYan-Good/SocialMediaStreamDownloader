# 数据库设计

[TOC]

---

## 概述

用户表
- 用户ID
- 用户名
- 用户密码
- 用户联系方式

---

## 数据类型存储原则
- 状态：unsigned tinyint, 占 1 个字节 0~255
- ID: varchar(200)
- 姓名昵称: varchar(50)
- 城市: varchar(100)
- 位置：varchar(100)
- 类型: unsigned tinyint, 占 1 个字节 0~255
- 模式: unsigned tinyint, 占 1 个字节 0~255
- 时间：timestamp
- URL: text，最大 64KB
- 星座: varchar(20)
- 等级: unsigned smallint, 占 2 个字节 0-65535
- 性别：unsigned tinyint, 占 1 个字节 0-255
- 签名：text, 最大 64KB
- 号码：varchar(20)
- 配置：text, 最大 64KB
- 参数：text, 最大 64KB
- 标题：tinytext, 最大 256 字节
- 版本：varchar(20)
- 标签：tinytext, 最大 256 字节
- 关注数量：unsigned int 占 4 个字节 0 - 4 294,967,295
- 粉丝数量：unsigned bigint 占 8 个字节 0 - 18,446,744,073,709,551,615
- 设置: tinytext, 最大 256 字节
- uri 的 url 索引: unsigned tinyint, 占 1 个字节
- 拓扑路径: tinyint, 最大 256 字节
- 颜色: varchar(7)
- 时长: unsinged int
- 选项: varchar(100)

---

## 抖音

### 源数据结构

```yaml
external_info:
  data:
    room:
      AnchorABMap: {}                                                                     # 主播AB映射
      acquaintance_status: 0                                                              # 直播间熟人状态
      admin_user_ids:                                                                     # 直播间管理员用户ID列表
      - 572164301142046
      - 98105276094
      - 1877579610464923
      - 2211848763215064
      - 97864774542
      - 62517518734
      admin_user_open_ids: []                                                             # 直播间管理员OpenID列表
      anchor_scheduled_time_text: ''                                                      # 主播预定时间文本
      anchor_share_text: "#\u5728\u6296\u97F3\uFF0C\u8BB0\u5F55\u7F8E\u597D\u751F\u6D3B\
        #\u3010Lvuuu\u3011\u6B63\u5728\u76F4\u64AD\uFF0C\u6765\u548C\u6211\u4E00\u8D77\
        \u652F\u6301Ta\u5427\u3002\u590D\u5236\u4E0B\u65B9\u94FE\u63A5\uFF0C\u6253\
        \u5F00\u3010\u6296\u97F3\u3011\uFF0C\u76F4\u63A5\u89C2\u770B\u76F4\u64AD\uFF01"   # 主播分享文本
      anchor_tab_type: 0                                                                  # 主播标签类型
      app_id: 1128                                                                        # 应用ID
      assist_label_list: []                                                               # 辅助标签列表
      auth_city: ''                                                                       # 直播间认证城市
      auto_cover: 0                                                                       # 自动封面
      base_category: 0                                                                    # 基础分类
      book_end_time: 0                                                                    # 直播间预约结束时间
      book_time: 0                                                                        # 直播间预约开始时间
      business_live: 0                                                                    # 商业直播
      category: 0                                                                         # 分类
      cell_style: 3                                                                       # 直播间单元样式
      challenge_info: ''                                                                  # 挑战信息
      city_top_distance: ''                                                               # 城市顶部距离
      client_version: 290600                                                              # 客户端版本
      comment_box:                                                                        # 评论框
        placeholder: "\u8BF4\u70B9\u4EC0\u4E48..."                                        # 评论框占位符
      comment_name_mode: 0                                                                # 评论名称模式
      common_label_list: ''                                                               # 常用标签列表
      content_tag: ''                                                                     # 内容标签
      cover:                                                                              # 直播间封面
        avg_color: '#F1FFEB'                                                              # 平均颜色
        flex_setting_list: []                                                             # 弹性设置列表
        height: 0                                                                         # 高度
        image_type: 0                                                                     # 图片类型
        is_animated: false                                                                # 是否为动画
        open_web_url: ''                                                                  # 开放网页URL
        text_setting_list: []                                                             # 文本设置列表
        uri: webcast-cover/7310930480756017947                                            # URI
        url_list:                                                                         # URL列表
        - https://p11-webcast-sign.douyinpic.com/webcast-cover/7310930480756017947~tplv-qz53dukwul-common-resize:0:0.image?biz_tag=aweme_webcast&from=webcast.room.pack&l=2025022317061645842BB1D723AB138B06&lk3s=39e7556e&s=reflow_room_info&sc=webcast_cover&x-expires=1742893576&x-signature=9FnU1Ut%2BEPXq5xHg3gGaNPpT6Mc%3D
        - https://p3-webcast-sign.douyinpic.com/webcast-cover/7310930480756017947~tplv-qz53dukwul-common-resize:0:0.image?biz_tag=aweme_webcast&from=webcast.room.pack&l=2025022317061645842BB1D723AB138B06&lk3s=39e7556e&s=reflow_room_info&sc=webcast_cover&x-expires=1742893576&x-signature=i9%2FZLOZpfcmxY%2F5Lt%2Bw%2B35pfsKA%3D
        width: 0                                                                          # 宽度
      create_time: 1714227431                                                             # 直播间创建时间
      danmaku_detail: 0                                                                   # 弹幕详情
      deco_list: []                                                                       # 装饰列表
      distance: ''                                                                        # 距离
      distance_city: ''                                                                   # 距离城市
      distance_km: ''                                                                     # 距离公里
      dynamic_cover_dict: {}                                                              # 动态封面字典
      dynamic_cover_uri: ''                                                               # 动态封面URI
      enable_room_perspective: true                                                       # 是否启用直播间透视
      extra:                                                                              # 额外信息
        create_scene: ''                                                                  # 创建场景
        facial_unrecognised: 0                                                            # 面部未识别
        geo_block: 0                                                                      # 地理封锁
        is_sandbox: false                                                                 # 是否为沙盒
        is_virtual_anchor: false                                                          # 是否为虚拟主播
        limit_appid: ''                                                                   # 限制应用ID
        limit_strategy: 0                                                                 # 限制策略
        realtime_playback_qualities: []                                                   # 实时回放质量列表
        realtime_playback_shift: 0                                                        # 实时回放偏移
        realtime_playback_start_shift: 0                                                  # 实时回放开始偏移
        realtime_replay_enabled: false                                                    # 是否启用实时回放
        vr_type: 0                                                                        # VR类型
        vs_type: 0                                                                        # VS类型
        xigua_uid: 0                                                                      # 西瓜用户ID
      fans_group_admin_user_ids: []                                                       # 粉丝群管理员用户ID列表
      fans_group_admin_user_open_ids: []                                                  # 粉丝群管理员OpenID列表
      fansclub_msg_style: 0                                                               # 粉丝俱乐部消息样式
      fcdn_appid: 0                                                                       # FCDN应用ID
      feed_room_label:                                                                    # 直播间标签
        avg_color: '#7A6D53'                                                              # 平均颜色
        content:                                                                          # 直播间标签内容
          alternative_text: ''                                                            # 替代文本
          font_color: ''                                                                  # 字体颜色
          level: 0                                                                        # 等级
          name: ''                                                                        # 名称
        flex_setting_list: []                                                             # 弹性设置列表
        height: 0                                                                         # 高度
        image_type: 0                                                                     # 图片类型
        is_animated: false                                                                # 是否为动画
        open_web_url: ''                                                                  # 开放网页URL
        text_setting_list: []                                                             # 文本设置列表
        uri: webcast/2ea90002aca1159b5c67                                                 # URI
        url_list:                                                                         # URL列表
        - https://p3-webcast.douyinpic.com/img/webcast/2ea90002aca1159b5c67~tplv-resize:0:0.image
        - https://p11-webcast.douyinpic.com/img/webcast/2ea90002aca1159b5c67~tplv-resize:0:0.image
        width: 0                                                                          # 宽度
      filter_words: []                                                                    # 过滤词列表
      finish_reason: 1                                                                    # 直播结束原因
      finish_time: 1714232860                                                             # 直播结束时间
      finish_url: ''                                                                      # 直播结束URL
      follow_msg_style: 0                                                                 # 关注消息样式
      forum_extra_data: ''                                                                # 论坛额外数据
      game_room_type: 0                                                                   # 游戏直播间类型
      gift_msg_style: 2                                                                   # 礼物消息样式
      group_id: 0                                                                         # 直播间组ID
      group_source: 0                                                                     # 直播间组来源
      guide_button:                                                                       # 引导按钮
        avg_color: '#E6FADC'                                                              # 平均颜色
        flex_setting_list: []                                                             # 弹性设置列表
        height: 0                                                                         # 高度
        image_type: 0                                                                     # 图片类型
        is_animated: false                                                                # 是否为动画
        open_web_url: ''                                                                  # 开放网页URL
        text_setting_list: []                                                             # 文本设置列表
        uri: webcast/aweme_button_call_3x.png                                             # URI
        url_list:                                                                         # URL列表
        - https://p3-webcast.douyinpic.com/img/webcast/aweme_button_call_3x.png~tplv-resize:0:0.image
        - https://p11-webcast.douyinpic.com/img/webcast/aweme_button_call_3x.png~tplv-resize:0:0.image
        width: 0                                                                          # 宽度
      has_commerce_goods: true                                                            # 是否有商品
      has_promotion_games: 0                                                              # 是否有推广游戏
      highlight: false                                                                    # 是否高亮
      hot_sentence_info: ''                                                               # 热门语句信息
      id: 7362550606306773794                                                             # 直播间ID
      id_str: '7362550606306773794'                                                       # 直播间ID字符串
      introduction: ''                                                                    # 直播间介绍
      is_need_check_list: false                                                           # 是否需要检查列表
      is_official_channel_room: false                                                     # 是否为官方频道直播间
      is_replay: false                                                                    # 是否为回放
      is_show_inquiry_ball: false                                                         # 是否显示询问球
      is_show_user_card_switch: true                                                      # 是否显示用户卡片开关
      item_explicit_info: ''                                                              # 物品显式信息
      last_ping_time: 0                                                                   # 最后ping时间
      layout: 0                                                                           # 直播间布局
      like_count: 14873                                                                   # 点赞数量
      linker_map: {}                                                                      # 连接器映射
      linkmic_display_type: 0                                                             # 连接器显示类型
      linkmic_layout: 1                                                                   # 连接器布局
      live_distribution: []                                                               # 直播分发列表
      live_id: 1                                                                          # 直播ID
      live_platform_source: ''                                                            # 直播平台来源
      live_room_mode: 0                                                                   # 直播间模式
      live_type_audio: false                                                              # 是否为音频直播
      live_type_linkmic: false                                                            # 是否为连麦直播
      live_type_normal: true                                                              # 是否为普通直播
      live_type_official: false                                                           # 是否为官方直播
      live_type_sandbox: false                                                            # 是否为沙盒直播
      live_type_screenshot: false                                                         # 是否为截图直播
      live_type_third_party: false                                                        # 是否为第三方直播
      live_type_vs_live: false                                                            # 是否为VS直播
      live_type_vs_premiere: false                                                        # 是否为VS首播
      living_room_attrs:                                                                  # 直播间属性
        admin_flag: 0                                                                     # 直播间管理员标志
        rank: 0                                                                           # 直播间等级
        room_id: 7362550606306773794                                                      # 直播间ID
        room_id_str: '7362550606306773794'                                                # 直播间ID字符串
        silence_flag: 0                                                                   # 直播间静音状态
      location: ''                                                                        # 直播间位置
      lottery_finish_time: 0                                                              # 抽奖结束时间
      luckymoney_num: 0                                                                   # 幸运红包数量
      mosaic_status: 0                                                                    # 马赛克状态
      mosaic_tip: ''                                                                      # 马赛克提示
      official_channel_open_id: ''                                                        # 官方频道OpenID
      official_channel_uid: 0                                                             # 官方频道用户ID
      orientation: 0                                                                      # 直播间方向
      os_type: 1                                                                          # 操作系统类型
      owner:                                                                              # 主播信息
        adversary_authorization_info: 3                                                   # 对手授权信息
        adversary_user_status: 0                                                          # 对手用户状态
        age_range: 0                                                                      # 年龄范围
        allow_be_located: false                                                           # 是否允许被定位
        allow_find_by_contacts: false                                                     # 是否允许通过联系人查找
        allow_others_download_video: false                                                # 是否允许其他人下载视频
        allow_others_download_when_sharing_video: false                                   # 是否允许其他人下载分享的视频
        allow_share_show_profile: false                                                   # 是否允许分享展示个人资料
        allow_show_in_gossip: false                                                       # 是否允许在八卦中展示
        allow_show_my_action: false                                                       # 是否允许展示我的动作
        allow_strange_comment: false                                                      # 是否允许陌生人评论
        allow_unfollower_comment: false                                                   # 是否允许非关注者评论
        allow_use_linkmic: false                                                          # 是否允许使用连麦
        authorization_info: 3                                                             # 授权信息
        avatar_large:                                                                     # 大头像
          avg_color: ''                                                                   # 平均颜色
          flex_setting_list: []                                                           # 弹性设置列表
          height: 0                                                                       # 高度
          image_type: 0                                                                   # 图片类型
          is_animated: false                                                              # 是否为动画
          open_web_url: ''                                                                # 开放网页URL
          text_setting_list: []                                                           # 文本设置列表
          uri: 1080x1080/aweme-avatar/tos-cn-avt-0015_073398e34f18e2e545861a83f392ad9f    # URI
          url_list:                                                                       # URL列表
          - https://p3.douyinpic.com/aweme/1080x1080/aweme-avatar/tos-cn-avt-0015_073398e34f18e2e545861a83f392ad9f.jpeg?from=3067671334
          - https://p11.douyinpic.com/aweme/1080x1080/aweme-avatar/tos-cn-avt-0015_073398e34f18e2e545861a83f392ad9f.jpeg?from=3067671334
          - https://p26.douyinpic.com/aweme/1080x1080/aweme-avatar/tos-cn-avt-0015_073398e34f18e2e545861a83f392ad9f.jpeg?from=3067671334
          width: 0                                                                        # 宽度
        avatar_medium:                                                                    # 中头像
          avg_color: ''                                                                   # 平均颜色
          flex_setting_list: []                                                           # 弹性设置列表
          height: 0                                                                       # 高度
          image_type: 0                                                                   # 图片类型
          is_animated: false                                                              # 是否为动画
          open_web_url: ''                                                                # 开放网页URL
          text_setting_list: []                                                           # 文本设置列表
          uri: 720x720/aweme-avatar/tos-cn-avt-0015_073398e34f18e2e545861a83f392ad9f      # URI
          url_list:                                                                       # URL列表
          - https://p3.douyinpic.com/aweme/720x720/aweme-avatar/tos-cn-avt-0015_073398e34f18e2e545861a83f392ad9f.jpeg?from=3067671334
          - https://p26.douyinpic.com/aweme/720x720/aweme-avatar/tos-cn-avt-0015_073398e34f18e2e545861a83f392ad9f.jpeg?from=3067671334
          - https://p11.douyinpic.com/aweme/720x720/aweme-avatar/tos-cn-avt-0015_073398e34f18e2e545861a83f392ad9f.jpeg?from=3067671334
          width: 0                                                                        # 宽度
        avatar_thumb:                                                                     # 小头像
          avg_color: ''                                                                   # 平均颜色
          flex_setting_list: []                                                           # 弹性设置列表
          height: 0                                                                       # 高度
          image_type: 0                                                                   # 图片类型
          is_animated: false                                                              # 是否为动画
          open_web_url: ''                                                                # 开放网页URL
          text_setting_list: []                                                           # 文本设置列表
          uri: 100x100/aweme-avatar/tos-cn-avt-0015_073398e34f18e2e545861a83f392ad9f      # URI
          url_list:                                                                       # URL列表
          - https://p11.douyinpic.com/aweme/100x100/aweme-avatar/tos-cn-avt-0015_073398e34f18e2e545861a83f392ad9f.jpeg?from=3067671334
          - https://p3.douyinpic.com/aweme/100x100/aweme-avatar/tos-cn-avt-0015_073398e34f18e2e545861a83f392ad9f.jpeg?from=3067671334
          - https://p26.douyinpic.com/aweme/100x100/aweme-avatar/tos-cn-avt-0015_073398e34f18e2e545861a83f392ad9f.jpeg?from=3067671334
          width: 0                                                                        # 宽度
        badge_image_list:                                                                 # 勋章图片列表
        - avg_color: ''                                                                   # 平均颜色
          content:                                                                        # 直播间勋章内容
            alternative_text: "\u8363\u8A89\u7B49\u7EA72\u7EA7\u52CB\u7AE0"               # 替代文本
            font_color: ''                                                                # 字体颜色
            level: 2                                                                      # 等级
            name: ''                                                                      # 名称
          flex_setting_list: []                                                           # 弹性设置列表
          height: 16                                                                      # 高度
          image_type: 1                                                                   # 图片类型
          is_animated: false                                                              # 是否为动画
          open_web_url: ''                                                                # 开放网页URL
          text_setting_list: []                                                           # 文本设置列表
          uri: webcast/new_user_grade_level_v1_2.png                                      # URI
          url_list:                                                                       # URL列表
          - https://p3-webcast.douyinpic.com/img/webcast/new_user_grade_level_v1_2.png~tplv-obj.image
          - https://p11-webcast.douyinpic.com/img/webcast/new_user_grade_level_v1_2.png~tplv-obj.image
          width: 32                                                                       # 宽度
        badge_image_list_v2:                                                              # 勋章图片列表V2
        - avg_color: ''                                                                   # 平均颜色
          content:                                                                        # 直播间勋章内容
            alternative_text: "\u8363\u8A89\u7B49\u7EA72\u7EA7\u52CB\u7AE0"               # 替代文本
            font_color: ''                                                                # 字体颜色
            level: 2                                                                      # 等级
            name: ''                                                                      # 名称
          flex_setting_list: []                                                           # 弹性设置列表
          height: 16                                                                      # 高度
          image_type: 1                                                                   # 图片类型
          is_animated: false                                                              # 是否为动画
          open_web_url: ''                                                                # 开放网页URL
          text_setting_list: []                                                           # 文本设置列表
          uri: webcast/new_user_grade_level_v1_2.png                                      # URI
          url_list:                                                                       # URL列表
          - https://p3-webcast.douyinpic.com/img/webcast/new_user_grade_level_v1_2.png~tplv-obj.image
          - https://p11-webcast.douyinpic.com/img/webcast/new_user_grade_level_v1_2.png~tplv-obj.image
          width: 32                                                                       # 宽度
        bg_img_url: ''                                                                    # 背景图片URL
        birthday: 0                                                                       # 生日
        birthday_description: ''                                                          # 生日描述
        birthday_valid: false                                                             # 生日有效
        block_status: 0                                                                   # 屏蔽状态
        city: ''                                                                          # 城市
        comment_restrict: 0                                                               # 评论限制
        commerce_webcast_config_ids: []                                                   # 商业直播配置ID列表
        constellation: ''                                                                 # 星座
        consume_diamond_level: 0                                                          # 消费钻石等级
        create_time: 0                                                                    # 创建时间
        desensitized_nickname: ''                                                         # 脱敏昵称
        disable_ichat: 0                                                                  # 禁用iChat
        display_id: '30266029732'                                                         # 显示ID
        enable_ichat_img: 0                                                               # 是否启用iChat图片
        exp: 0                                                                            # 经验值
        experience: 0                                                                     # 经验
        fan_ticket_count: 0                                                               # 粉丝票数量
        fans_club:                                                                        # 粉丝俱乐部
          data:                                                                           # 粉丝俱乐部数据
            anchor_id: 0                                                                  # 主播ID
            anchor_open_id: ''                                                            # 主播OpenID
            available_gift_ids: []                                                        # 可用礼物ID列表
            badge:                                                                        # 勋章信息
              icons:                                                                      # 勋章图标列表
                '0':                                                                      # 勋章图标0
                  avg_color: ''                                                           # 平均颜色
                  flex_setting_list: []                                                   # 弹性设置列表
                  height: 0                                                               # 高度
                  image_type: 0                                                           # 图片类型
                  is_animated: false                                                      # 是否为动画
                  open_web_url: ''                                                        # 开放网页URL
                  text_setting_list: []                                                   # 文本设置列表
                  uri: ''                                                                 # 勋章图标URI
                  url_list: []                                                            # 勋章图标URL列表
                  width: 0                                                                # 宽度
              title: ''                                                                   # 勋章标题
            badge_type: 0                                                                 # 勋章类型
            club_name: ''                                                                 # 俱乐部名称
            guard_expired_time: 0                                                         # 俱乐部守护过期时间
            level: 0                                                                      # 俱乐部等级
            user_fans_club_status: 0                                                      # 用户粉丝俱乐部状态
            user_guard_status: 0                                                          # 用户守护状态
          prefer_data: {}                                                                 # 偏好数据
        fans_group_info:                                                                  # 粉丝群信息
          list_fans_group_url: sslocal://webcast_lynxview?height=754&radius=8&gravity=bottom&type=popup&animation_type=present&url=https%3A%2F%2Flf-webcast-sourcecdn-tos.bytegecko.com%2Fobj%2Fbyte-gurd-source%2Fwebcast%2Fmono%2Flynx%2Fdouyin_lynx_fansclub%2Ftemplate%2Fpages%2Ffansclub%2Ffans_group%2Fuser%2Ftemplate.js&load_taro=0&fallback_url=sslocal%3A%2F%2Fwebcast_webview%3Furl%3Dhttps%253A%252F%252Flf-webcast-sourcecdn-tos.bytegecko.com%252Fobj%252Fbyte-gurd-source%252Fwebcast%252Fmono%252Flynx%252Fdouyin_lynx_fansclub%252Ftemplate%252Fpages%252Ffansclub%252Ffans_group%252Fuser%252Findex.html%26type%3Dpopup%26gravity%3Dbottom%26height%3D754%26radius%3D8%26load_taro%3D0 # 粉丝群列表URL
        fold_stranger_chat: false                                                         # 折叠陌生人聊天
        follow_info:                                                                      # 关注信息
          follow_status: 0                                                                # 关注状态
          follower_count: 333091                                                          # 粉丝数量
          follower_count_str: "33.3\u4E07"                                                # 粉丝数量字符串
          following_count: 95                                                             # 关注数量
          following_count_str: '95'                                                       # 关注数量字符串
          invalid_follow_status: false                                                    # 是否为无效关注状态
          push_status: 0                                                                  # 关注推送状态
          remark_name: ''                                                                 # 备注名称
        follow_status: 0                                                                  # 关注状态
        gender: 2                                                                         # 性别（0-未知，1-男，2-女）
        hotsoon_verified: false                                                           # 是否为Hotsoon认证
        hotsoon_verified_reason: ''                                                       # Hotsoon认证原因
        ichat_restrict_type: 0                                                            # iChat限制类型
        id: 2700838411446480                                                              # 主播用户ID
        id_str: '2700838411446480'                                                        # 主播用户ID字符串
        income_share_percent: 0                                                           # 收入分成百分比
        is_anonymous: false                                                               # 是否匿名
        is_follower: false                                                                # 是否是粉丝
        is_following: false                                                               # 是否关注
        j_accredit_info:                                                                  # 主播认证信息
          JAccreditAdvance: 0                                                             # 主播认证高级
          JAccreditBasic: 0                                                               # 主播认证基础
          JAccreditContent: 0                                                             # 主播认证内容
          JAccreditLive: 0                                                                # 主播认证直播
        level: 0                                                                          # 用户等级
        link_mic_stats: 1                                                                 # 连麦状态
        location_city: ''                                                                 # 定位城市
        media_badge_image_list: []                                                        # 媒体勋章图片列表
        modify_time: 1740042739                                                           # 修改时间戳
        mystery_man: 1                                                                    # 是否神秘人
        need_profile_guide: false                                                         # 是否需要个人资料引导
        new_real_time_icons: []                                                           # 新实时图标列表
        nickname: Lvuuu                                                                   # 昵称
        pay_grade:                                                                        # 付费等级
          grade_banner: ''                                                                # 付费等级横幅
          grade_describe: ''                                                              # 付费等级描述
          grade_describe_shining: false                                                   # 付费等级描述闪烁
          grade_icon_list: []                                                             # 付费等级图标列表
          level: 2                                                                        # 付费等级
          name: ''                                                                        # 付费等级名称
          new_im_icon_with_level:                                                         # 新带等级的IM图标
            avg_color: ''                                                                 # 平均颜色
            flex_setting_list: []                                                         # 弹性设置列表
            height: 16                                                                    # 高度
            image_type: 1                                                                 # 图片类型
            is_animated: false                                                            # 是否为动画
            open_web_url: ''                                                              # 开放网页URL
            text_setting_list: []                                                         # 文本设置列表
            uri: webcast/new_user_grade_level_v1_2.png                                    # URI
            url_list:                                                                     # URL列表
            - https://p3-webcast.douyinpic.com/img/webcast/new_user_grade_level_v1_2.png~tplv-obj.image
            - https://p11-webcast.douyinpic.com/img/webcast/new_user_grade_level_v1_2.png~tplv-obj.image
            width: 32                                                                     # 宽度
          new_live_icon:                                                                  # 新直播图标
            avg_color: ''                                                                 # 平均颜色
            flex_setting_list: []                                                         # 弹性设置列表
            height: 12                                                                    # 高度
            image_type: 1                                                                 # 图片类型
            is_animated: false                                                            # 是否为动画
            open_web_url: ''                                                              # 开放网页URL
            text_setting_list: []                                                         # 文本设置列表
            uri: webcast/aweme_pay_grade_2x_1_4.png                                       # URI
            url_list:                                                                     # URL列表
            - https://p3-webcast.douyinpic.com/img/webcast/aweme_pay_grade_2x_1_4.png~tplv-obj.image
            - https://p11-webcast.douyinpic.com/img/webcast/aweme_pay_grade_2x_1_4.png~tplv-obj.image
            width: 12                                                                     # 宽度
          next_diamond: 0                                                                 # 下一级所需钻石
          next_name: ''                                                                   # 下一级名称
          next_privileges: ''                                                             # 下一级特权
          now_diamond: 0                                                                  # 当前钻石
          pay_diamond_bak: 0                                                              # 付费钻石备份
          score: 0                                                                        # 分数
          screen_chat_type: 0                                                             # 屏幕聊天类型
          this_grade_max_diamond: 16                                                      # 当前等级最大钻石
          this_grade_min_diamond: 7                                                       # 当前等级最小钻石
          total_diamond_count: 0                                                          # 总钻石数量
          upgrade_need_consume: 0                                                         # 升级所需消费
        pay_score: 0                                                                      # 付费分数
        pay_scores: 0                                                                     # 付费分数
        public_area_oper_freq: 0                                                          # 公共区域操作频率
        push_comment_status: false                                                        # 推送评论状态
        push_digg: false                                                                  # 推送点赞状态
        push_follow: false                                                                # 推送关注状态
        push_friend_action: false                                                         # 推送好友动作状态
        push_ichat: false                                                                 # 推送iChat状态
        push_status: false                                                                # 推送状态
        push_video_post: false                                                            # 推送视频发布状态
        push_video_recommend: false                                                       # 推送视频推荐状态
        real_time_icons: []                                                               # TBD 实时图标列表
        remark_name: ''                                                                   # 备注名称
        sec_uid: MS4wLjABAAAA3REn4Oekpt-zrnovTqTVWrTPkevbUHRJZRX2td0l_EdDr8Zgzk1HlnNgKHEyguTr # 主播安全UID
        secret: 0                                                                         # 是否为私密用户
        share_qrcode_uri: 31c1300073f889131745b                                           # 分享二维码URI
        short_id: 30266029732                                                             # 短ID
        signature: "\u2764\u966A\u804A\U0001F50D\u516C\u4F17\u53F7\uFF1A\u5BF9\u4F60\
          \u6709\u610F\uFF08\U0001F448\u89E3\u9501\u5FC3\u52A8\u5973\u53CB\n\u7537\
          \u5B69\u5B50\u7684\u5FEB\u4E50@\u54E5\u54E5\u522B\u73A9\u5440\U0001F3AE\
          ... \u597D\u73A9\uFF01\n\U0001F234\uFE0F\U0001F454\U0001F457\u79C1"             # 主播签名
        special_id: ''                                                                    # 特殊ID
        status: 1                                                                         # 状态（0-注销，1-正常）
        subscribe:                                                                        # 订阅状态
          buy_type: 0                                                                     # 购买类型
          identity_type: 0                                                                # 身份类型
          is_member: false                                                                # 是否为会员
          level: 0                                                                        # 订阅等级
          open: 0                                                                         # 是否开启订阅
        telephone: ''                                                                              # 电话号码
        ticket_count: 0                                                                            # 票数
        top_fans: []                                                                               # TBD 顶级粉丝列表
        top_vip_no: 0                                                                              # 顶级VIP编号
        total_recharge_diamond_count: 0                                                            # 总充值钻石数量
        user_attr:                                                                                 # 用户属性
          admin_privileges: []                                                                     # 管理员权限列表
          is_admin: false                                                                          # 是否为管理员
          is_muted: false                                                                          # 是否被禁言
          is_super_admin: false                                                                    # 是否为超级管理员
        user_canceled: false                                                                       # 用户是否已取消
        user_dress_info:                                                                           # 用户着装信息
          dress_own_ids: []                                                                        # 用户拥有的着装ID列表
          dress_wear_ids: []                                                                       # 用户穿戴的着装ID列表
        user_open_id: ''                                                                           # 用户OpenID
        user_role: 0                                                                               # 用户角色
        verified: true                                                                             # 是否认证
        verified_content: ''                                                                       # 认证内容
        verified_mobile: false                                                                     # 是否为认证手机号
        verified_reason: ''                                                                        # 认证原因
        watch_duration_month: 0                                                                    # 观看时长（月）
        web_rid: '827868393976'                                                                    # Web RID
        webcast_uid: MS4wLjMljH3nsEUH1oduoEHICOyLO_mi_GCJdTJEys1TI9mE8kaaf7-cX-5cj3yS5qMPbqI       # 主播Webcast UID
        with_car_management_permission: false                                                      # 是否具有车辆管理权限
        with_commerce_permission: true                                                             # 是否具有商业权限
        with_fusion_shop_entry: true                                                               # 是否具有融合店铺入口
      owner_device_id: 0                                                                           # 主播设备ID
      owner_open_id: ''                                                                            # 主播OpenID
      owner_user_id: 2700838411446480                                                              # 主播用户ID
      pack_meta:                                                                                   # 包元数据
        cluster: default                                                                           # 集群
        dc: lf                                                                                     # 数据中心
        env: prod                                                                                  # 环境
        extras: {}                                                                                 # 附加信息
        scene: reflow_room_info(prod_single_dc/rpc/topo)                                           # 场景
        trace_id: ''                                                                               # 跟踪ID
      paid_live_data:                                                                              # 付费直播数据
        anchor_right: 0                                                                            # 主播权限
        delivery: 0                                                                                # 交付状态
        duration: 0                                                                                # 直播时长
        max_preview_duration: 0                                                                    # 最大预览时长
        need_delivery_notice: false                                                                # 是否需要交付通知
        paid_type: 0                                                                               # 付费类型
        pay_ab_type: 0                                                                             # 付费AB类型
        privilege_info: {}                                                                         # 特权信息
        privilege_info_map: {}                                                                     # 特权信息映射
        view_right: 0                                                                              # 观看权限
      popularity: 0                                                                                # 人气
      popularity_str: ''                                                                           # 人气字符串
      pre_enter_time: 0                                                                            # 预进入时间
      preview_copy: "\u4E16\u754C\u5F88\u5927\uFF0C\u4F46\u6211\u4EEC\u5F88\u6709\u7F18\
        ~"                                                                                         # 预览复制文本
      preview_flow_tag: 0                                                                          # 预览流量标签
      private_info: ''                                                                             # 私有信息
      ranklist_audience_type: 0                                                                    # 排行榜观众类型
      real_distance: ''                                                                            # 实际距离
      redpacket_audience_auth: 0                                                                   # 红包观众认证
      relation_tag: ''                                                                             # 关系标签
      replay: false                                                                                # 是否为回放
      replay_location: 0                                                                           # 回放位置
      room_audit_status: 0                                                                         # 直播间审核状态
      room_auth:                                                                                   # 直播间认证
        AIClone: 0                                                                                 # AI克隆
        AdminCommentWall: 0                                                                        # 管理员评论墙
        AnchorAudioChat: 0                                                                         # 主播音频聊天
        AnchorColdMessageTiled: 0                                                                  # 主播冷消息平铺
        AnchorHotMessageAggregated: 0                                                              # 主播热消息聚合
        AnchorMission: 0                                                                           # 主播任务
        AudioChat: 0                                                                               # 音频聊天
        AudioChatTotext: 0                                                                         # 音频聊天转文本
        Banner: 1                                                                                  # 横幅
        BulletStyle: 0                                                                             # 弹幕样式
        CanSellTicket: 0                                                                           # 是否可以售票
        CastScreen: 0                                                                              # 屏幕投射
        CastScreenExplicit: 0                                                                      # 屏幕投射显式
        Chat: true                                                                                 # 聊天
        ChatDispatch: 0                                                                            # 聊天分发
        ChatDynamicSlideSpeed: 0                                                                   # 聊天动态滑动速度
        ChatDynamicSlideSpeedAnchor: 0                                                             # 主播聊天动态滑动速度
        ChatGuideEmoji: 0                                                                          # 聊天引导表情
        ChatGuideImage: 0                                                                          # 聊天引导图片
        ChatIdentity: 0                                                                            # 聊天身份
        ChatMention: 0                                                                             # 聊天提及
        ChatMentionV2: 0                                                                           # 聊天提及V2
        ChatOperate: 0                                                                             # 聊天操作
        ChatReply: 0                                                                               # 聊天回复
        ClearEntranceOption: 0                                                                     # 清除入口选项
        Collect: 0                                                                                 # 收藏
        CommentWall: 0                                                                             # 评论墙 
        CommerceCard: 1                                                                            # 商业卡片
        CommerceComponent: 0                                                                       # 商业组件
        CommonCard: 0                                                                              # 通用卡片
        CountType: 0                                                                               # 计数类型
        Danmaku: false                                                                             # 弹幕
        DanmakuDefault: 0                                                                          # 弹幕默认
        Denounce: 0                                                                                # 举报
        Digg: true                                                                                 # 点赞
        Dislike: 0                                                                                 # 不喜欢
        DonationSticker: 0                                                                         # 捐赠贴纸
        DouPlus: 0                                                                                 # DouPlus
        DouPlusPopularityGem: 0                                                                    # DouPlus人气宝石
        DownloadVideo: 0                                                                           # 下载视频
        EcomFansClub: 0                                                                            # 电商粉丝俱乐部
        EmojiOutside: 0                                                                            # 外部表情
        EnhancedTouch: 0                                                                           # 增强触摸
        EnterEffects: 0                                                                            # 进入效果
        ExpandScreen: 0                                                                            # 扩展屏幕
        FansClub: 0                                                                                # 粉丝俱乐部
        FansClubBlessing: 0                                                                        # 粉丝俱乐部祝福
        FansClubDeclaration: 0                                                                     # 粉丝俱乐部宣言
        FansClubLetter: 0                                                                          # 粉丝俱乐部信件
        FansClubNotice: 0                                                                          # 粉丝俱乐部通知
        FansGroup: 0                                                                               # 粉丝群
        FeaturedPublicScreen: 0                                                                    # 精选公共屏幕
        FirstFeedHistChat: 0                                                                       # 首次Feed历史聊天
        FixedChat: 0                                                                               # 固定聊天
        FrequentlyChat: 0                                                                          # 常用聊天
        FusionEmoji: 0                                                                             # 融合表情
        GamePointsPlaying: 0                                                                       # 游戏积分玩法
        Gift: true                                                                                 # 礼物
        GiftAnchorMt: 0                                                                            # 主播礼物MT
        GiftVote: 0                                                                                # 礼物投票
        Highlights: 0                                                                              # 精彩片段
        HostTeam: 0                                                                                # 主播团队
        HostTeamChannel: 0                                                                         # 主播团队频道
        HotChatTray: 0                                                                             # 热聊天托盘
        HourRank: 0                                                                                # 小时排行榜
        ImHeatValue: 0                                                                             # IM热值
        IndustryService: 0                                                                         # 行业服务
        InteractionGift: 0                                                                         # 互动礼物
        InteractiveComponent: 0                                                                    # 互动组件
        ItemShare: 0                                                                               # 物品分享
        KtvOrderSong: 0                                                                            # KTV点歌
        Landscape: 1                                                                               # 横屏
        LandscapeChat: 1                                                                           # 横屏聊天
        LandscapeChatDynamicSlideSpeed: 0                                                          # 横屏聊天动态滑动速度
        LandscapeGift: 0                                                                           # 横屏礼物
        LandscapeScreenCapture: 0                                                                  # 横屏屏幕截图
        LandscapeScreenRecording: 0                                                                # 横屏屏幕录制
        LandscapeScreenShare: 0                                                                    # 横屏屏幕分享
        Like: 0                                                                                    # 点赞
        LinkmicGuestLike: 0                                                                        # 连麦嘉宾点赞
        LongPressOption: 0                                                                         # 长按选项
        LongTouch: 0                                                                               # 长按触摸
        LuckMoney: true                                                                            # 红包
        MarkUser: 0                                                                                # 标记用户
        MediaHistoryMessage: 0                                                                     # 媒体历史消息
        MediaLinkmic: 0                                                                            # 媒体连麦
        MessageDispatch: 0                                                                         # 消息分发
        MessageGift: 0                                                                             # 消息礼物
        MissionCenter: 0                                                                           # 任务中心
        MoreAnchor: 1                                                                              # 更多主播
        MoreHistChat: 0                                                                            # 更多历史聊天
        MultiplierPlayback: 0                                                                      # 倍速播放
        MyLiveEntrance: 0                                                                          # 我的直播入口
        OnlyTa: 0                                                                                  # 仅限TA
        PCPlay: 0                                                                                  # PC播放
        POI: true                                                                                  # POI
        PadPlay: 0                                                                                 # 平板播放
        PanelECService: 0                                                                          # 面板EC服务
        PlayerRankList: 0                                                                          # 播放器排行榜列表
        Poster: 0                                                                                  # 海报
        PosterCache: 0                                                                             # 海报缓存
        PreviewChatExpose: 0                                                                       # 预览聊天曝光
        PreviewHotCommentSwitch: 0                                                                 # 预览热评论开关
        ProjectionBtn: 0                                                                           # 投影按钮
        Props: true                                                                                # 道具
        PublicScreen: 1                                                                            # 公共屏幕
        QuizGamePointsPlaying: 0                                                                   # 测验游戏积分玩法
        RecordScreen: 2                                                                            # 录制屏幕
        RoomChannel: 0                                                                             # 直播间频道
        RoomChatLikeDisplay: 0                                                                     # 直播间聊天点赞显示
        RoomChatOperatePanel: 0                                                                    # 直播间聊天操作面板
        RoomContributor: false                                                                     # 直播间贡献者
        RoomWidget: 0                                                                              # 直播间小部件
        ScreenBottomInfo: 0                                                                        # 屏幕底部信息
        ScreenProjectionBarrage: 0                                                                 # 屏幕投影弹幕
        Seek: 0                                                                                    # 寻找
        Selection: 0                                                                               # 选择
        SelectionAlbum: 0                                                                          # 选择相册
        Share: 1                                                                                   # 分享
        ShortTouch: 0                                                                              # 短触摸
        ShortTouchTempState: 0                                                                     # 短触摸临时状态
        ShowGamePlugin: 0                                                                          # 显示游戏插件
        ShowQualification: 0                                                                       # 显示资格
        SmallWindowDisplay: 0                                                                      # 小窗口显示
        SmallWindowPlayer: 0                                                                       # 小窗口播放器
        StickyMessage: 0                                                                           # 固定消息
        StreamAdaptation: 0                                                                        # 流适应
        StrokeUpDownGuide: 0                                                                       # 上下滑动引导
        SubscribeCardPackage: 0                                                                    # 订阅卡包
        Teleprompter: 0                                                                            # 提词器
        TextGift: 0                                                                                # 文本礼物
        TimedShutdown: 0                                                                           # 定时关机
        ToolbarBubble: 0                                                                           # 工具栏气泡
        Topic: 0                                                                                   # 话题
        TypingCommentState: 0                                                                      # 输入评论状态
        UgcVSReplayDelete: 0                                                                       # Ugc VS回放删除
        UgcVsReplayVisibility: 0                                                                   # Ugc VS回放可见性
        UpRightStatsFloatingLayer: 0                                                               # 右上角统计浮动层
        UseHostInfo: 0                                                                             # 使用主机信息
        UserCard: true                                                                             # 用户卡片
        UserCorner: 0                                                                              # 用户角落
        VSGift: 0                                                                                  # VS礼物
        VSRank: 0                                                                                  # VS排行榜
        VSTopic: 0                                                                                 # VS话题
        VerticalRank: 0                                                                            # 垂直排行榜
        VerticalScreenShare: 0                                                                     # 垂直屏幕分享
        VideoAmplificationType: 0                                                                  # 视频放大类型
        VideoShare: 0                                                                              # 视频分享
        VsCommentBar: 0                                                                            # VS评论栏
        VsDouPlus: 0                                                                               # VS DouPlus
        VsExtensionEnableFollow: 0                                                                 # VS扩展启用关注
        VsFansClub: 0                                                                              # VS粉丝俱乐部
        VsWelcomeDanmaku: 0                                                                        # VS欢迎弹幕
        WordAssociation: 0                                                                         # 词关联
      room_create_ab_param: ''                                                                     # 直播间创建AB参数
      room_layout: 0                                                                               # 直播间布局
      room_tabs: []                                                                                # 直播间标签列表
      room_tag: 0                                                                                  # 直播间标签
      room_view_stats:                                                                             # 直播间观看统计
        display_long: "2.3\u4E07\u4EBA\u770B\u8FC7"                                                # 直播间观看人数
        display_long_anchor: "2.3\u4E07\u4EBA\u770B\u8FC7"                                         # 主播观看人数
        display_middle: "2.3\u4E07\u4EBA\u770B\u8FC7"                                              # 直播间观看人数（中）
        display_middle_anchor: "2.3\u4E07\u4EBA\u770B\u8FC7"                                       # 主播观看人数（中）
        display_short: "2.3\u4E07"                                                                 # 直播间观看人数（短）
        display_short_anchor: "2.3\u4E07"                                                          # 主播观看人数（短）
        display_type: 3                                                                            # 直播间观看人数显示类型
        display_value: 22537                                                                       # 直播间观看人数值
        display_version: 1663849727                                                                # 直播间观看人数显示版本
        incremental: true                                                                          # 是否增量更新
        is_hidden: false                                                                           # 是否隐藏
      screen_capture_sharing_title: ''                                                             # 屏幕截图分享标题
      scroll_config: ''                                                                            # 滚动配置
      search_id: 7362550607120452879                                                               # 直播间搜索ID
      sell_goods: false                                                                            # 是否售卖商品
      share_msg_style: 0                                                                           # 分享消息样式
      share_url: https://webcast.amemv.com/douyin/webcast/reflow/7362550606306773794?did=MS4wLjABAAAANwkJuWIRFOzg5uCpDRpMj4OX-QryoDgn-yYlXQnRwQQ&iid=MS4wLjABAAAANwkJuWIRFOzg5uCpDRpMj4OX-QryoDgn-yYlXQnRwQQ&with_sec_did=1&sec_user_id=MS4wLjABAAAA3REn4Oekpt-zrnovTqTVWrTPkevbUHRJZRX2td0l_EdDr8Zgzk1HlnNgKHEyguTr # 直播间分享链接
      sharing_music_id_list: []
      short_title: ''                                                                              # 直播间短标题
      short_touch_area_config:
        elements:                                                                                  # 短触摸区域配置元素
          '1':                                                                                     # 元素1
            priority: 1                                                                            # 优先级
            type: 1                                                                                # 类型
          '10':                                                                                    # 元素10
            priority: 3                                                                            # 优先级
            type: 10                                                                               # 类型
          '12':                                                                                    # 元素12
            priority: 3                                                                            # 优先级
            type: 12                                                                               # 类型
          '2':                                                                                     # 元素2
            priority: 1                                                                            # 优先级
            type: 2                                                                                # 类型
          '22':                                                                                    # 元素22
            priority: 1                                                                            # 优先级
            type: 22                                                                               # 类型
          '27':                                                                                    # 元素27
            priority: 3                                                                            # 优先级
            type: 27                                                                               # 类型
          '3':                                                                                     # 元素3
            priority: 1                                                                            # 优先级
            type: 3                                                                                # 类型
          '30':                                                                                    # 元素30
            priority: 2                                                                            # 优先级
            type: 30                                                                               # 类型
          '4':                                                                                     # 元素4
            priority: 3                                                                            # 优先级
            type: 4                                                                                # 类型
          '5':                                                                                     # 元素5
            priority: 4                                                                            # 优先级
            type: 5                                                                                # 类型
          '6':                                                                                     # 元素6
            priority: 3                                                                            # 优先级
            type: 6                                                                                # 类型
          '7':                                                                                     # 元素7
            priority: 3                                                                            # 优先级
            type: 7                                                                                # 类型
          '8':                                                                                     # 元素8
            priority: 3                                                                            # 优先级
            type: 8                                                                                # 类型
          '9':                                                                                     # 元素9
            priority: 3                                                                            # 优先级
            type: 9                                                                                # 类型
        forbidden_types_map: {}                                                                    # 禁止类型映射
        strategy_feat_whitelist:                                                                   # 策略特性白名单
        - feat_coin_lottery_amount
        - feat_redpack_amount
        - live_short_touch_ecom_redpack_type
        - live_short_touch_ecom_redpack_sub_type
        - live_short_touch_ecom_redpack_total_amount
        - live_short_touch_ecom_redpack_total_stock
        - live_ecom_cart_click_twice
        - live_ecom_cart_stop_buy
        - live_watch_6_min
        temp_state_condition_map:                                                                  # 临时状态条件映射
          '1':                                                                                     # 条件1
            minimum_gap: 900                                                                       # 最小间隔
            type:                                                                                  # 类型
              priority: 30                                                                         # 优先级
              strategy_type: 1                                                                     # 策略类型
          '2':                                                                                     # 条件2
            minimum_gap: 900                                                                       # 最小间隔
            type:                                                                                  # 类型
              priority: 20                                                                         # 优先级
              strategy_type: 2                                                                     # 策略类型
          '3':                                                                                     # 条件3
            minimum_gap: 900                                                                       # 最小间隔
            type:                                                                                  # 类型
              priority: 10                                                                         # 优先级
              strategy_type: 3                                                                     # 策略类型
          '4':                                                                                     # 条件4
            minimum_gap: 0                                                                         # 最小间隔
            type:                                                                                  # 类型
              priority: 1                                                                          # 优先级
              strategy_type: 4                                                                     # 策略类型
          '5':                                                                                     # 条件5
            minimum_gap: 0                                                                         # 最小间隔
            type:                                                                                  # 类型
              priority: 5                                                                          # 优先级
              strategy_type: 5                                                                     # 策略类型
          '6':                                                                                     # 条件6
            minimum_gap: 0                                                                         # 最小间隔
            type:                                                                                  # 类型
              priority: 7                                                                          # 优先级
              strategy_type: 6                                                                     # 策略类型
          '7':                                                                                     # 条件7
            minimum_gap: 0                                                                         # 最小间隔
            type:                                                                                  # 类型
              priority: 6                                                                          # 优先级
              strategy_type: 7                                                                     # 策略类型
        temp_state_global_condition:                                                               # 临时状态全局条件
          allow_count: 1                                                                           # 允许总数
          duration_gap: 300                                                                        # 持续间隔
          ignore_strategy_types:                                                                   # 忽略策略类型
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
      sofa_layout: 0                                                                               # 沙发布局
      stamps: ''                                                                                   # 印章
      start_time: 1714227435                                                                       # 直播开始时间戳
      stats:                                                                                       # 直播间统计信息
        comment_count: 0                                                                           # 评论数量
        digg_count: 0                                                                              # 点赞数量
        dou_plus_promotion: ''                                                                     # DouPlus推广
        enter_count: 0                                                                             # 进入数量
        fan_ticket: 0                                                                              # 粉丝票数量
        follow_count: 22                                                                           # 关注数量
        gift_uv_count: 0                                                                           # 礼物UV数量
        id: 7362550606306773794                                                                    # 直播间ID
        id_str: '7362550606306773794'                                                              # 直播间ID字符串
        like_count: 0                                                                              # 喜欢数量
        money: 0                                                                                   # 金额
        total_user: 15726                                                                          # 总用户数量
        total_user_desp: ''                                                                        # 总用户描述
        total_user_str: "1\u4E07+"                                                                 # 总用户字符串
        up_right_stats_str: ''                                                                     # 右上角统计字符串
        up_right_stats_str_complete: ''                                                            # 完整的右上角统计字符串
        user_count_composition:                                                                    # 用户数量组成
          city: 0                                                                                  # 城市用户数量
          my_follow: 0                                                                             # 我的关注用户数量
          other: 1                                                                                 # 其他
          video_detail: 0                                                                          # 视频详情
        user_count_str: '0'                                                                        # 用户数量字符串
        watermelon: 0                                                                              # 西瓜
        welfare_donation_amount: 0                                                                 # 福利捐赠金额
      status: 4                                                                                    # 直播状态：2-正在直播 4-直播已结束
      stream_close_time: 0                                                                         # 直播间流关闭时间戳
      stream_id: 691500607505433258                                                                # 直播间流ID
      stream_id_str: '691500607505433258'                                                          # 直播间流ID字符串
      stream_provider: 0                                                                           # 直播间流提供者
      stream_url:                                                                                  # 直播间流地址
        candidate_resolution: []                                                                   # 候选分辨率
        complete_push_urls: []                                                                     # 完整推流地址
        default_resolution: FULL_HD1                                                               # 默认分辨率
        extra:                                                                                     # 额外信息
          anchor_interact_profile: 0                                                               # 主播互动配置文件
          audience_interact_profile: 0                                                             # 观众互动配置文件
          bframe_enable: false                                                                     # B帧启用
          bitrate_adapt_strategy: 0                                                                # 比特率自适应策略
          bytevc1_enable: false                                                                    # ByteVC1启用
          default_bitrate: 0                                                                       # 默认比特率
          fps: 0                                                                                   # 帧率
          gop_sec: 0                                                                               # GOP秒数
          h265_enable: false                                                                       # H.265启用
          hardware_encode: false                                                                   # 硬件编码
          height: 1280                                                                             # 高度
          max_bitrate: 0                                                                           # 最大比特率
          min_bitrate: 0                                                                           # 最小比特率
          roi: false                                                                               # 是否启用ROI（Region of Interest）
          sw_roi: false                                                                            # 是否启用软件ROI
          video_profile: 0                                                                         # 视频配置文件
          width: 720                                                                               # 宽度
        flv_pull_url:                                                                              # 直播间FLV拉流地址
          FULL_HD1: http://pull-hs-f5.flive.douyincdn.com/stage/stream-691500607505433258_or4.flv?expire=1740906376&sign=37520dbe730f79b7af0d732f9b142ce7&unique_id=stream-691500607505433258_682_flv_or4&volcSecret=37520dbe730f79b7af0d732f9b142ce7&volcTime=1740906376
        flv_pull_url_params: {}                                                                    # FLV拉流地址参数
        hls_pull_url: http://pull-hs-f5.flive.douyincdn.com/stage/stream-691500607505433258_or4/index.m3u8?expire=1740906376&sign=1e96dffde05a71cf1e062a3677741155&volcSecret=1e96dffde05a71cf1e062a3677741155&volcTime=1740906376 # 直播间HLS拉流地址
        hls_pull_url_map:                                                                          # 直播间HLS拉流地址映射
          FULL_HD1: http://pull-hs-f5.flive.douyincdn.com/stage/stream-691500607505433258_or4/index.m3u8?expire=1740906376&sign=1e96dffde05a71cf1e062a3677741155&volcSecret=1e96dffde05a71cf1e062a3677741155&volcTime=1740906376
        hls_pull_url_params: '{"P2PFastOpenDuration":-1500,"BufferDataMs":1000,"FastOpenDuration":-500,"NetworkAdapt":{"HurryStopType":1,"SlowMillisecond":90,"HurryMillisecond":3500,"HurryType":0,"HurryStartMs":4000,"SlowSpeed":1,"HurrySpeed":1.1,"HurryTime":3500,"Enabled":0,"SlowTime":90},"VCodec":"h264","PlayingIntervalMs":20000}' # HLS拉流地址参数
        id: 691500607505433258                                                                     # 直播间流ID
        id_str: '691500607505433258'                                                               # 直播间流ID字符串
        live_core_sdk_data:                                                                        # 直播核心SDK数据
          pull_data:                                                                               # 拉流数据
            Flv: []                                                                                # FLV数据
            Hls: []                                                                                # HLS数据
            codec: ''                                                                              # 编解码器
            compensatory_data: ''                                                                  # 补偿数据
            hls_data_unencrypted: {}                                                               # HLS未加密数据
            kind: 0                                                                                # 类型
            options:                                                                               # 选项
              default_quality:                                                                     # 默认质量
                additional_content: ''                                                             # 附加内容
                disable: 0                                                                         # 禁用标志
                fps: 0                                                                             # 帧率
                level: 0                                                                           # 级别
                name: "\u6807\u6E05"                                                               # 名称
                resolution: ''                                                                     # 分辨率
                sdk_key: origin                                                                    # SDK密钥
                v_bit_rate: 0                                                                      # 视频比特率
                v_codec: ''                                                                        # 视频编解码器
              qualities:                                                                           # 质量列表
              - additional_content: ''                                                             # 附加内容
                disable: 0                                                                         # 禁用标志
                fps: 0                                                                             # 帧率
                level: 1                                                                           # 级别
                name: "\u6807\u6E05"                                                               # 名称
                resolution: ''                                                                     # 分辨率
                sdk_key: origin                                                                    # SDK密钥
                v_bit_rate: 0                                                                      # 视频比特率
                v_codec: '264'                                                                     # 视频编解码器
              vpass_default: false                                                                 # 视频默认通过
            stream_data: '{"common":{"ts":"1740301576","session_id":"037-2025022317061645842BB1D723AB138B06","stream":"691500607505433258","rule_ids":"{\"ab_version_trace\":null,\"sched\":\"{\\\"result\\\":{\\\"hit\\\":\\\"determined\\\",\\\"cdn\\\":847}}\"}","common_trace":"{\"StrategyTrace\":{\"Neptune\":{\"PlayStream\":{\"ids\":null}}},\"BusinessType\":\"\",\"BigeventAnchorLevel\":\"\"}","app_id":"100100","major_anchor_level":"","mode":"Normal","lines":{"main":"line_847"},"p2p_params":null,"stream_data_content_encoding":"default","common_sdk_params":{"main":"{}"},"stream_name":"stream-691500607505433258","main_push_id":682,"backup_push_id":0},"data":{"md":{"main":{"flv":"https://pull-hs-f5.flive.douyincdn.com/stage/stream-691500607505433258_md.flv?expire=1740906376&sign=5ae0c29aedb9ad114656303bfe824fc0&unique_id=stream-691500607505433258_682_flv_md&volcSecret=5ae0c29aedb9ad114656303bfe824fc0&volcTime=1740906376","hls":"http://pull-hs-f5.flive.douyincdn.com/stage/stream-691500607505433258_md/index.m3u8?expire=1740906376&sign=dac6a3f29ece599fd3deb672528ff8c2&volcSecret=dac6a3f29ece599fd3deb672528ff8c2&volcTime=1740906376","cmaf":"","dash":"","lls":"http://pull-lls-hs-f5.flive.douyincdn.com/stage/stream-691500607505433258_md.sdp?expire=1740906376&sign=795a6d09d502aeee7f09bc5b20ac4d28&unique_id=stream-691500607505433258_682_lls_md&volcSecret=795a6d09d502aeee7f09bc5b20ac4d28&volcTime=1740906376","tsl":"","tile":"","http_ts":"","ll_hls":"","sdk_params":"{\"FastOpenDuration\":-500,\"NetworkAdapt\":{\"SlowTime\":90,\"HurryStartMs\":4000,\"HurrySpeed\":1.1,\"Enabled\":0,\"HurryMillisecond\":3500,\"SlowSpeed\":1,\"HurryType\":0,\"HurryStopType\":1,\"HurryTime\":3500,\"SlowMillisecond\":90},\"PlayingIntervalMs\":20000,\"P2PFastOpenDuration\":-1500,\"BufferDataMs\":1000,\"VCodec\":\"h264\",\"vbitrate\":250000,\"resolution\":\"240P\",\"gop\":4,\"drType\":\"sdr\",\"fps\":15}","enableEncryption":false}},"ao":{"main":{"flv":"http://pull-hs-f5.flive.douyincdn.com/stage/stream-691500607505433258.flv?expire=1740906376&only_audio=1&sign=48ee468a79787bab67bb7b3db8070734&unique_id=stream-691500607505433258_682_flv&volcSecret=48ee468a79787bab67bb7b3db8070734&volcTime=1740906376","hls":"","cmaf":"","dash":"","lls":"","tsl":"","tile":"","http_ts":"","ll_hls":"","sdk_params":"{\"FastOpenDuration\":-500,\"NetworkAdapt\":{\"HurryMillisecond\":3500,\"HurryType\":0,\"SlowTime\":90,\"SlowSpeed\":1,\"Enabled\":0,\"HurrySpeed\":1.1,\"HurryStopType\":1,\"HurryTime\":3500,\"SlowMillisecond\":90,\"HurryStartMs\":4000},\"PlayingIntervalMs\":20000,\"P2PFastOpenDuration\":-1500,\"BufferDataMs\":1000,\"VCodec\":\"h264\",\"vbitrate\":0,\"resolution\":\"\",\"gop\":4,\"drType\":\"sdr\"}","enableEncryption":false}},"origin":{"main":{"flv":"http://pull-hs-f5.flive.douyincdn.com/stage/stream-691500607505433258_or4.flv?expire=1740906376&sign=37520dbe730f79b7af0d732f9b142ce7&unique_id=stream-691500607505433258_682_flv_or4&volcSecret=37520dbe730f79b7af0d732f9b142ce7&volcTime=1740906376","hls":"http://pull-hs-f5.flive.douyincdn.com/stage/stream-691500607505433258_or4/index.m3u8?expire=1740906376&sign=1e96dffde05a71cf1e062a3677741155&volcSecret=1e96dffde05a71cf1e062a3677741155&volcTime=1740906376","cmaf":"","dash":"","lls":"http://pull-lls-hs-f5.flive.douyincdn.com/stage/stream-691500607505433258_or4.sdp?expire=1740906376&sign=6babbebc719e3c4df5bdddfc6e2a629a&unique_id=stream-691500607505433258_682_lls_or4&volcSecret=6babbebc719e3c4df5bdddfc6e2a629a&volcTime=1740906376","tsl":"","tile":"","http_ts":"","ll_hls":"","sdk_params":"{\"P2PFastOpenDuration\":-1500,\"BufferDataMs\":1000,\"FastOpenDuration\":-500,\"NetworkAdapt\":{\"HurryStopType\":1,\"SlowMillisecond\":90,\"HurryMillisecond\":3500,\"HurryType\":0,\"HurryStartMs\":4000,\"SlowSpeed\":1,\"HurrySpeed\":1.1,\"HurryTime\":3500,\"Enabled\":0,\"SlowTime\":90},\"VCodec\":\"h264\",\"PlayingIntervalMs\":20000,\"vbitrate\":0,\"resolution\":\"\",\"gop\":4,\"drType\":\"sdr\"}","enableEncryption":false}}}}'  # 流数据内容
            version: 0                                                                             # 版本
          size: ''                                                                                 # 流大小
        provider: 0                                                                                # 直播间推流服务商
        pull_datas: {}                                                                             # 拉流数据
        push_datas: {}                                                                             # 推流数据
        push_stream_type: 0                                                                        # 推流类型
        push_urls: []                                                                              # 推流地址
        resolution_name:                                                                           # 分辨率名称
          FULL_HD1: "\u84DD\u5149"                                                                 # 蓝光
          HD1: "\u8D85\u6E05"                                                                      # 超清
          ORIGION: "\u539F\u753B"                                                                  # 原画
          SD1: "\u6807\u6E05"                                                                      # 标清
          SD2: "\u9AD8\u6E05"                                                                      # 高清
        rtmp_pull_url: http://pull-hs-f5.flive.douyincdn.com/stage/stream-691500607505433258_or4.flv?expire=1740906376&sign=37520dbe730f79b7af0d732f9b142ce7&unique_id=stream-691500607505433258_682_flv_or4&volcSecret=37520dbe730f79b7af0d732f9b142ce7&volcTime=1740906376 # 直播间RTMP拉流地址
        rtmp_pull_url_params: '{"P2PFastOpenDuration":-1500,"BufferDataMs":1000,"FastOpenDuration":-500,"NetworkAdapt":{"HurryStopType":1,"SlowMillisecond":90,"HurryMillisecond":3500,"HurryType":0,"HurryStartMs":4000,"SlowSpeed":1,"HurrySpeed":1.1,"HurryTime":3500,"Enabled":0,"SlowTime":90},"VCodec":"h264","PlayingIntervalMs":20000}' # RTMP拉流地址参数
        rtmp_push_url: ''                                                                          # 直播间RTMP推流地址
        rtmp_push_url_params: ''                                                                   # RTMP推流地址参数
        stream_control_type: 0                                                                     # 直播间流控制类型
        stream_orientation: 1                                                                      # 直播间流方向：1-竖屏 2-横屏
        vr_type: 0                                                                                 # VR类型
      sun_daily_icon_content: ''                                                                   # 日常图标内容
      tags: []                                                                                     # 标签列表
      title: "\u76F4\u64AD\u4E94\u5206\u949F"                                                      # 直播间标题
      title_recommend: false                                                                       # 是否推荐标题
      top_fans: []                                                                                 # 顶级粉丝列表
      toutiao_cover_recommend_level: 0                                                             # 头条封面推荐等级
      toutiao_title_recommend_level: 0                                                             # 头条标题推荐等级
      upper_right_widget_data_list: []                                                             # 右上角小组件数据列表
      use_filter: false                                                                            # 是否使用滤镜
      user_count: 0                                                                                # 用户数量
      user_share_text: "#\u5728\u6296\u97F3\uFF0C\u8BB0\u5F55\u7F8E\u597D\u751F\u6D3B\
        #\u3010Lvuuu\u3011\u6B63\u5728\u76F4\u64AD\uFF0C\u6765\u548C\u6211\u4E00\u8D77\
        \u652F\u6301Ta\u5427\u3002\u590D\u5236\u4E0B\u65B9\u94FE\u63A5\uFF0C\u6253\
        \u5F00\u3010\u6296\u97F3\u3011\uFF0C\u76F4\u63A5\u89C2\u770B\u76F4\u64AD\uFF01"            # 用户分享文本
      vertical_cover_uri: ''                                                                       # 竖屏封面URI
      vid: ''                                                                                      # 视频ID
      video_feed_tag: "\u76F4\u64AD\u4E2D"                                                         # 视频Feed标签
      visibility_range: 0                                                                          # 可见范围：X-公开 X-私密 X-好友可见
      vs_main_replay_id: 0                                                                         # VS主回放ID
      vs_roles: []                                                                                 # VS角色列表
      wait_copy: "\u4E0D\u8981\u6025\uFF0C\u6162\u6162\u6765\u3002\u591A\u4E00\u70B9\
        \u8010\u5FC3"                                                                              # 等待复制
      web_count: 0                                                                                 # 网页观看人数
      webcast_comment_tcs: 0                                                                       # 直播间评论TCs
      webcast_sdk_version: 0                                                                       # 直播间SDK版本
      with_aggregate_column: false                                                                 # 是否有聚合栏目
      with_draw_something: false                                                                   # 是否有抽奖
      with_ktv: false                                                                              # 是否有KTV
      with_linkmic: false                                                                          # 是否有连麦
    user:                                                                                          # 用户信息
      adversary_authorization_info: 0                                                              # 对手授权信息
      adversary_user_status: 0                                                                     # 对手用户状态
      age_range: 0                                                                                 # 年龄范围
      allow_be_located: false                                                                      # 是否允许被定位
      allow_find_by_contacts: false                                                                # 是否允许通过联系人查找
      allow_others_download_video: false                                                           # 是否允许其他人下载视频
      allow_others_download_when_sharing_video: false                                              # 是否允许其他人下载分享的视频
      allow_share_show_profile: false                                                              # 是否允许分享展示个人资料
      allow_show_in_gossip: false                                                                  # 是否允许在八卦中展示
      allow_show_my_action: false                                                                  # 是否允许展示我的动态
      allow_strange_comment: false                                                                 # 是否允许陌生人评论
      allow_unfollower_comment: false                                                              # 是否允许非关注者评论
      allow_use_linkmic: false                                                                     # 是否允许使用连麦
      authorization_info: 0                                                                        # 授权信息
      badge_image_list: []
      badge_image_list_v2: []
      bg_img_url: ''                                                                               # 背景图片URL
      birthday: 0                                                                                  # 生日时间戳
      birthday_description: ''                                                                     # 生日描述
      birthday_valid: false                                                                        # 生日是否有效
      block_status: 0                                                                              # 屏蔽状态：0-未屏蔽 1-已屏蔽
      city: ''                                                                                     # 城市
      comment_restrict: 0                                                                          # 评论限制
      commerce_webcast_config_ids: []
      constellation: ''                                                                            # 星座
      consume_diamond_level: 0                                                                     # 消费钻石等级
      create_time: 0                                                                               # 创建时间戳
      desensitized_nickname: ''                                                                    # 脱敏昵称
      disable_ichat: 0                                                                             # 是否禁用iChat
      display_id: ''                                                                               # 显示ID
      enable_ichat_img: 0                                                                          # 是否启用iChat图片
      exp: 0                                                                                       # 经验值
      experience: 0                                                                                # 经验值
      fan_ticket_count: 0                                                                          # 粉丝票数量
      fold_stranger_chat: false                                                                    # 是否折叠陌生人聊天
      follow_status: 0                                                                             # 关注状态：0-未关注 1-已关注
      gender: 0                                                                                    # 性别：0-未知 1-男 2-女
      hotsoon_verified: false                                                                      # 是否Hotsoon认证
      hotsoon_verified_reason: ''                                                                  # Hotsoon认证原因
      ichat_restrict_type: 0                                                                       # iChat限制类型
      id: 0                                                                                        # 用户ID
      id_str: ''                                                                                   # 用户ID字符串
      income_share_percent: 0                                                                      # 收入分成百分比
      is_anonymous: false                                                                          # 是否匿名
      is_follower: false                                                                           # 是否是粉丝
      is_following: false                                                                          # 是否正在关注
      level: 0                                                                                     # 用户等级
      link_mic_stats: 0                                                                            # 连麦状态
      location_city: ''                                                                            # 定位城市
      media_badge_image_list: []
      modify_time: 0                                                                               # 修改时间戳
      mystery_man: 0                                                                               # 是否神秘人
      need_profile_guide: false                                                                    # 是否需要个人资料引导
      new_real_time_icons: []
      nickname: ''                                                                                 # 昵称
      pay_score: 0                                                                                 # 支付分
      pay_scores: 0                                                                                # 支付分
      public_area_oper_freq: 0                                                                     # 公共区域操作频率
      push_comment_status: false                                                                   # 是否推送评论状态
      push_digg: false                                                                             # 是否推送点赞
      push_follow: false                                                                           # 是否推送关注
      push_friend_action: false                                                                    # 是否推送好友操作
      push_ichat: false                                                                            # 是否推送iChat
      push_status: false                                                                           # 是否推送状态
      push_video_post: false                                                                       # 是否推送视频发布
      push_video_recommend: false                                                                  # 是否推送视频推荐
      real_time_icons: []
      remark_name: ''                                                                              # 备注名
      sec_uid: ''                                                                                  # 安全用户ID
      secret: 0                                                                                    # 是否私密
      share_qrcode_uri: ''                                                                         # 分享二维码URI
      short_id: 0                                                                                  # 短ID
      signature: ''                                                                                # 个性签名
      special_id: ''                                                                               # 特殊ID
      status: 0                                                                                    # 用户状态：0-注销 1-正常
      telephone: ''                                                                                # 电话号码
      ticket_count: 0                                                                              # 票数
      top_fans: []
      top_vip_no: 0                                                                                # 顶级VIP编号
      total_recharge_diamond_count: 0                                                              # 总充值钻石数量
      user_canceled: false                                                                         # 用户是否取消
      user_open_id: ''                                                                             # 用户开放ID
      user_role: 0                                                                                 # 用户角色
      verified: false                                                                              # 是否认证
      verified_content: ''                                                                         # 认证内容
      verified_mobile: false                                                                       # 是否认证手机
      verified_reason: ''                                                                          # 认证原因
      watch_duration_month: 0                                                                      # 观看时长（月）
      web_rid: ''                                                                                  # Web用户ID
      webcast_uid: ''                                                                              # Webcast用户ID
      with_car_management_permission: false                                                        # 是否具有汽车管理权限
      with_commerce_permission: false                                                              # 是否具有商业权限
      with_fusion_shop_entry: false                                                                # 是否具有融合店铺入口
  extra:                                                                                           # 额外信息
    now: 1740301577026                                                                             # 当前时间戳
  status_code: 0  
```

---

### 原始数据

#### 直播信息
```shell
##
## overview ====================================== Level 1 ============================================================
##
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                               | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| data                           | table - data                       |      |     |         |       |                 |
| extra                          | table - extra                      |      |     |         |       |                 |
| status_code                    | tinyint                            |      |     |         |       |                 |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
```

---

#### 数据 - data
```shell
##
## data ========================================== Level 2-1 ==========================================================
##
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                               | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| room                           | table - room                       |      |     |         |       |                 |
| user                           | table - user                       |      |     |         |       |                 |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
```

#### 额外数据表 - extra
```shell
##
## extra ========================================== Level 2-2 ======================================================
##
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type              | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| now                                      | timestamp         |      |     |         |       |                    |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
```

---

#### 直播间 room
```shell
##
## data.room ========================================== Level 3-1 ======================================================
##
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                               | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| AnchorABMap                    | json                               | YES  |     | NULL    |       |                 |
| acquaintance_status            | unsigned tinyint                   |      |     | 0       |       | 熟人状态         |
| admin_user_ids                 | table - live_room_user_id          |      |     |         |       | 管理员ID列表     |
| admin_user_open_ids            | table - live_room_user_id          |      |     |         |       | 管理员公开ID列表 |
| anchor_scheduled_time_text     | tinytext                           |      |     |         |       | 锚定时间文本     |
| anchor_share_text              | tinytext                           |      |     |         |       | 锚定分享文本     |
| anchor_tab_type                | unsigned tinyint                   |      |     |         |       | 锚定标签类型     |
| app_id                         | varchar(200)                       |      |     |         |       |                 |
| assist_label_list              | varchar(200)                       |      |     |         |       |                 |
| auth_city                      | varchar(100)                       |      |     |         |       | 认证城市         |
| auto_cover                     | unsigned tinyint                   |      |     |         |       | 自动封面         |
| base_category                  | unsigned tinyint                   |      |     |         |       | 基本类别         |
| book_end_time                  | timestamp                          |      |     |         |       | 预定结束时间     |
| book_time                      | timestamp                          |      |     |         |       |                 |
| business_live                  | unsigned tinyint                   |      |     |         |       | 商业直播         |
| category                       | unsigned tinyint                   |      |     |         |       | 类别            |
| cell_style                     | unsigned tinyint                   |      |     |         |       |                 |
| challenge_info                 | tinytext                           |      |     |         |       |                 |
| city_top_distance              | tinytext                           |      |     |         |       |                 |
| client_version                 | varchar(20)                        |      |     |         |       | 客户端版本号     |
| comment_box                    | table - room_comment_box           |      |     |         |       |                 |
| comment_name_mode              | unsigned tinyint                   |      |     |         |       |                 |
| common_label_list              | tinytext                           |      |     |         |       |                 |
| content_tag                    | tinytext                           |      |     |         |       |                 |
| cover                          | table - live_room_pic              |      |     |         |       | 封面-图片信息表  |
| create_time                    | timestamp                          |      |     |         |       | 创建时间         |
| danmaku_detail                 | unsigned int                       |      |     |         |       | 弹幕详情         |
| deco_list                      | table - deco_list                  |      |     |         |       | 装饰清单         |
| distance                       | varchar(100)                       |      |     |         |       | 距离            |
| distance_city                  | varchar(100)                       |      |     |         |       | 城市距离        |
| distance_km                    | varchar(100)                       |      |     |         |       | 公里距离        |
| dynamic_cover_dict             | json                               |      |     |         |       |                 |
| dynamic_cover_uri              | text                               |      |     |         |       |                 |
| enable_room_perspective        | bool                               |      |     |         |       |                 |
| extra                          | table - live_room_extra            |      |     |         |       | 额外直播信息表   |
| fans_group_admin_user_ids      | table - live_room_user_id          |      |     |         |       | 直播间用户ID表   |
| fans_group_admin_user_open_ids | table - live_room_user_id          |      |     |         |       | 直播间用户ID表   |
| fansclub_msg_style             | unsigned tinyint                   |      |     |         |       |                 |
| fcdn_appid                     | varchar(200)                       |      |     |         |       |                 |
| feed_room_label                | table - live_room_pic              |      |     |         |       | -> 图片信息表    |
| filter_words                   | table - live_room_filter_word      |      |     |         |       |                 |
| finish_reason                  | unsigned tinyint                   |      |     |         |       |                 |
| finish_time                    | timestamp                          |      |     |         |       |                 |
| finish_url                     | text                               |      |     |         |       |                 |
| follow_msg_style               | unsigned tinyint                   |      |     |         |       |                 |
| forum_extra_data               | tinytext                           |      |     |         |       |                 |
| game_room_type                 | unsigned tinyint                   |      |     |         |       | 游戏房间类型     |
| gift_msg_style                 | unsigned tinyint                   |      |     |         |       | 礼物消息风格     |
| group_id                       | varchar(200)                       |      |     |         |       |                 |
| group_source                   | unsigned tinyint                   |      |     |         |       |                 |
| guide_button                   | table - live_room_pic              |      |     |         |       | -> 图片信息表    |
| has_commerce_goods             | bool                               |      |     |         |       |                 |
| has_promotion_games            | unsigned tinyint                   |      |     |         |       |                 |
| highlight                      | bool                               |      |     |         |       |                 |
| hot_sentence_info              | text                               |      |     |         |       |                 |
| id                             | varchar(200)                       |      |     |         |       |                 |
| id_str                         | varchar(200)                       |      |     |         |       |                 |
| introduction                   | text                               |      |     |         |       |                 |
| is_need_check_list             | bool                               |      |     |         |       |                 |
| is_official_channel_room       | bool                               |      |     |         |       |                 |
| is_replay                      | bool                               |      |     |         |       |                 |
| is_show_inquiry_ball           | bool                               |      |     |         |       |                 |
| is_show_user_card_switch       | bool                               |      |     |         |       |                 |
| item_explicit_info             | text                               |      |     |         |       |                 |
| last_ping_time                 | timestamp                          |      |     |         |       |                 |
| layout                         | unsigned tinyint                   |      |     |         |       |                 |
| like_count                     | unsigned int                       |      |     |         |       |                 |
| linker_map                     | json                               |      |     |         |       |                 |
| linkmic_display_type           | unsigned tinyint                   |      |     |         |       |                 |
| linkmic_layout                 | unsigned tinyint                   |      |     |         |       |                 |
| live_distribution              |                                    |      |     |         |       |                 |
| live_id                        | varchar(200)                       |      |     |         |       |                 |
| live_platform_source           | tinytext                           |      |     |         |       |                 |
| live_room_mode                 | unsigned tinyint                   |      |     |         |       |                 |
| live_type_audio                | bool                               |      |     |         |       |                 |
| live_type_linkmic              | bool                               |      |     |         |       |                 |
| live_type_normal               | bool                               |      |     |         |       |                 |
| live_type_official             | bool                               |      |     |         |       |                 |
| live_type_sandbox              | bool                               |      |     |         |       |                 |
| live_type_screenshot           | bool                               |      |     |         |       |                 |
| live_type_third_party          | bool                               |      |     |         |       |                 |
| live_type_vs_live              | bool                               |      |     |         |       |                 |
| live_type_vs_premiere          | bool                               |      |     |         |       |                 |
| living_room_attrs              | table - live_room_attribute        |      |     |         |       | 直播间属性表     |
| location                       | varchar(100)                       |      |     |         |       |                 |
| lottery_finish_time            | timestamp                          |      |     |         |       |                 |
| luckymoney_num                 | unsigned int                       |      |     |         |       |                 |
| mosaic_status                  | unsigned tinyint                   |      |     |         |       |                 |
| mosaic_tip                     | tinytext                           |      |     |         |       |                 |
| official_channel_open_id       | varchar(200)                       |      |     |         |       |                 |
| official_channel_uid           | varchar(200)                       |      |     |         |       |                 |
| orientation                    | unsigned tinyint                   |      |     |         |       |                 |
| os_type                        | unsigned tinyint                   |      |     |         |       |                 |
| owner                          | table - live_owner                 |      |     |         |       | 主播信息表       |
| owner_device_id                | unsigned tinyint                   |      |     |         |       |                 |
| owner_open_id                  | varchar(200)                       |      |     |         |       |                 |
| owner_user_id                  | varchar(200)                       |      |     |         |       |                 |
| pack_meta                      | json                               |      |     |         |       |                 |
| paid_live_data                 | json                               |      |     |         |       |                 |
| popularity                     | unsigned int                       |      |     |         |       | 人气            |
| popularity_str                 | varchar(200)                       |      |     |         |       |                 |
| pre_enter_time                 | timestamp                          |      |     |         |       | 预入时间         |
| preview_copy                   | tinytext                           |      |     |         |       |                 |
| preview_flow_tag               | unsigned tinyint                   |      |     |         |       |                 |
| private_info                   | text                               |      |     |         |       |                 |
| ranklist_audience_type         | unsigned tinyint                   |      |     |         |       | 排名列表受众类型  |
| real_distance                  | varchar(100)                       |      |     |         |       | 实时距离         |
| redpacket_audience_auth        | unsigned tinyint                   |      |     |         |       |                 |
| relation_tag                   | tinytext                           |      |     |         |       |                 |
| replay                         | bool                               |      |     |         |       | 重播            |
| replay_location                | unsigned tinyint                   |      |     |         |       | 重播位置         |
| room_audit_status              | unsigned tinyint                   |      |     |         |       | 房间审核状态     |
| room_auth                      | json                               |      |     |         |       |                 |
| room_create_ab_param           | text                               |      |     |         |       |                 |
| room_layout                    | unsigned tinyint                   |      |     |         |       |                 |
| room_tabs                      | text                               |      |     |         |       |                 |
| room_tag                       | unsigned tinyint                   |      |     |         |       |                 |
| room_view_stats                | json                               |      |     |         |       |                 |
| screen_capture_sharing_title   | tinytext                           |      |     |         |       | 屏幕截图共享标题  |
| scroll_config                  | text                               |      |     |         |       |                 |
| search_id                      | varchar(200)                       |      |     |         |       |                 |
| sell_goods                     | bool                               |      |     |         |       | 卖货            |
| share_msg_style                | unsigned tinyint                   |      |     |         |       |                 |
| share_url                      | text                               |      |     |         |       |                 |
| sharing_music_id_list          | table - live_room_sharing_music_id |      |     |         |       |                 |
| short_title                    | tinytext                           |      |     |         |       |                 |
| short_touch_area_config        | table - short_touch_area_config    |      |     |         |       |                 |
| sofa_layout                    | unsigned tinyint                   |      |     |         |       |                 |
| stamps                         | tinytext                           |      |     |         |       |                 |
| start_time                     | timestamp                          |      |     |         |       |                 |
| stats                          | table - live_room_stats            |      |     |         |       |                 |
| status                         | unsigned tinyint                   |      |     |         |       |                 |
| stream_close_time              | timestamp                          |      |     |         |       |                 |
| stream_id                      | varchar(200)                       |      |     |         |       |                 |
| stream_id_str                  | varchar(200)                       |      |     |         |       |                 |
| stream_provider                | unsigned tinyint                   |      |     |         |       |                 |
| stream_url                     | table - stream_url                 |      |     |         |       |                 |
| sun_daily_icon_content         | tinytext                           |      |     |         |       |                 |
| tags                           | table - live_room_tag              |      |     |         |       |                 |
| title                          | tinytext                           |      |     |         |       |                 |
| title_recommend                | bool                               |      |     |         |       |                 |
| top_fans                       |                                    |      |     |         |       |                 |
| toutiao_cover_recommend_level  | unsigned smallint                  |      |     |         |       |                 |
| toutiao_title_recommend_level  | unsigned smallint                  |      |     |         |       |                 |
| upper_right_widget_data_list   |                                    |      |     |         |       | 右上角小部件数据列表 |
| use_filter                     | bool                               |      |     |         |       |                 |
| user_count                     | unsigned int                       |      |     |         |       | 观众数量         |
| user_share_text                | text                               |      |     |         |       |                 |
| vertical_cover_uri             | text                               |      |     |         |       |                 |
| vid                            | varchar(200)                       |      |     |         |       |                 |
| video_feed_tag                 | tinytext                           |      |     |         |       |                 |
| visibility_range               | unsigned smallint                  |      |     |         |       |                 |
| vs_main_replay_id              | varchar(200)                       |      |     |         |       |                 |
| vs_roles                       |                                    |      |     |         |       |                 |
| wait_copy                      | tinytext                           |      |     |         |       |                 |
| web_count                      | unsigned smallint                  |      |     |         |       |                 |
| webcast_comment_tcs            | unsigned int                       |      |     |         |       |                 |
| webcast_sdk_version            | varchar(20)                        |      |     |         |       |                 |
| with_aggregate_column          | bool                               |      |     |         |       |                 |
| with_draw_something            | bool                               |      |     |         |       |                 |
| with_ktv                       | bool                               |      |     |         |       |                 |
| with_linkmic                   | bool                               |      |     |         |       |                 |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
```

#### 用户表 user
```shell
##
## data.user
##
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type              | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| adversary_authorization_info             | unsigned tinyint  |      |     |         |       |                    |
| adversary_user_status                    | unsigned tinyint  |      |     |         |       |                    |
| age_range                                | unsigned tinyint  |      |     |         |       | 年纪范围            |
| allow_be_located                         | bool              |      |     |         |       | 允许被定位          |
| allow_find_by_contacts                   | bool              |      |     |         |       | 允许通过通讯录被发现 |
| allow_others_download_video              | bool              |      |     |         |       | 允许其它人下载作品   |
| allow_others_download_when_sharing_video | bool              |      |     |         |       | 允许被分享人下载作品 |
| allow_share_show_profile                 | bool              |      |     |         |       | 允许分享显示个人资料 |
| allow_show_in_gossip                     | bool              |      |     |         |       | 允许在八卦中显示     |
| allow_show_my_action                     | bool              |      |     |         |       | 允许显示我的行为     |
| allow_strange_comment                    | bool              |      |     |         |       |                    |
| allow_unfollower_comment                 | bool              |      |     |         |       |                    |
| allow_use_linkmic                        | bool              |      |     |         |       |                    |
| authorization_info                       | unsigned tinyint  |      |     |         |       |                    |
| badge_image_list                         |                   |      |     |         |       | 头像，查看图片信息表 |
| badge_image_list_v2                      |                   |      |     |         |       | 头像，查看图片信息表 |
| bg_img_url                               | text              |      |     |         |       |                    |
| birthday                                 | timestamp         |      |     |         |       |                    |
| birthday_description                     | text              |      |     |         |       |                    |
| birthday_valid                           | bool              |      |     |         |       |                    |
| block_status                             | unsigned tinyint  |      |     |         |       |                    |
| city                                     | varchar(100)      |      |     |         |       | 城市               |
| comment_restrict                         | unsigned tinyint  |      |     |         |       | 限制评论            |
| commerce_webcast_config_ids              |                   |      |     |         |       |                    |
| constellation                            | varchar(20)       |      |     |         |       | 星座               |
| consume_diamond_level                    | unsigned smallint |      |     |         |       | 消费钻石等级        |
| create_time                              | timestamp         |      |     |         |       | 创建时间            |
| desensitized_nickname                    | varchar(50)       |      |     |         |       | 去敏感化的昵称      |
| disable_ichat                            | unsigned tinyint  |      |     |         |       | 禁止聊天            |
| display_id                               | varchar(200)      |      |     |         |       | 显示ID             |
| enable_ichat_img                         | unsigned tinyint  |      |     |         |       |                    |
| exp                                      | unsigned int      |      |     |         |       |                    |
| experience                               | unsigned int      |      |     |         |       |                    |
| fan_ticket_count                         | unsigned int      |      |     |         |       | 粉丝票数量          |
| fold_stranger_chat                       | bool              |      |     |         |       | 折叠陌生人聊天      |
| follow_status                            | unsigned tinyint  |      |     |         |       | 关注状态           |
| gender                                   | unsigned tinyint  |      |     |         |       | 性别               |
| hotsoon_verified                         | bool              |      |     |         |       |                    |
| hotsoon_verified_reason                  | text              |      |     |         |       |                    |
| ichat_restrict_type                      | unsigned tinyint  |      |     |         |       |                    |
| id                                       | varchar(200)      |      |     |         |       |                    |
| id_str                                   | varchar(200)      |      |     |         |       |                    |
| income_share_percent                     | unsigned tinyint  |      |     |         |       |                    |
| is_anonymous                             | bool              |      |     |         |       |                    |
| is_follower                              | bool              |      |     |         |       |                    |
| is_following                             | bool              |      |     |         |       |                    |
| level                                    | unsigned smallint |      |     |         |       | 等级               |
| link_mic_stats                           | unsigned smallint |      |     |         |       | 连麦统计           |
| location_city                            | varchar(100)      |      |     |         |       | 定位城市           |
| media_badge_image_list                   |                   |      |     |         |       |                   |
| modify_time                              | timestamp         |      |     |         |       |                   |
| mystery_man                              | unsigned tinyint  |      |     |         |       | 神秘人             |
| need_profile_guide                       | bool              |      |     |         |       |                   |
| new_real_time_icons                      | list              |      |     |         |       |                   |
| nickname                                 | varchar(50)       |      |     |         |       | 昵称              |
| pay_score                                | unsigned int      |      |     |         |       |                   |
| pay_scores                               | unsigned int      |      |     |         |       |                   |
| public_area_oper_freq                    | unsigned smallint |      |     |         |       |                   |
| push_comment_status                      | bool              |      |     |         |       |                   |
| push_digg                                | bool              |      |     |         |       |                   |
| push_follow                              | bool              |      |     |         |       |                   |
| push_friend_action                       | bool              |      |     |         |       |                   |
| push_ichat                               | bool              |      |     |         |       |                   |
| push_status                              | bool              |      |     |         |       |                   |
| push_video_post                          | bool              |      |     |         |       |                   |
| push_video_recommend                     | bool              |      |     |         |       |                   |
| real_time_icons                          |                   |      |     |         |       |                   |
| remark_name                              | varchar(50)       |      |     |         |       |                   |
| sec_uid                                  | varchar(200)      |      |     |         |       |                   |
| secret                                   | unsigned tinyint  |      |     |         |       |                   |
| share_qrcode_uri                         | text              |      |     |         |       |                   |
| short_id                                 | varchar(200)      |      |     |         |       |                   |
| signature                                | text              |      |     |         |       |                   |
| special_id                               | varchar(200)      |      |     |         |       |                   |
| status                                   | unsigned tinyint  |      |     |         |       | 主播状态         |
| telephone                                | varchar(20)       |      |     |         |       | 手机号码         |
| ticket_count                             | unsigned int      |      |     |         |       |                 |
| top_fans                                 |                   |      |     |         |       |                 |
| top_vip_no                               | unsigned int      |      |     |         |       |                 |
| total_recharge_diamond_count             | unsigned int      |      |     |         |       | 钻石充值总数     |
| user_canceled                            | bool              |      |     |         |       | 用户已取消       |
| user_open_id                             | varchar(200)      |      |     |         |       |                 |
| user_role                                | unsigned tinyint  |      |     |         |       |                 |
| verified                                 | bool              |      |     |         |       |                 |
| verified_content                         | tinytext          |      |     |         |       |                 |
| verified_mobile                          | bool              |      |     |         |       |                 |
| verified_reason                          | tinytext          |      |     |         |       |                 |
| watch_duration_month                     | unsigned smallint |      |     |         |       |                 |
| web_rid                                  | varchar(200)      |      |     |         |       |                 |
| webcast_uid                              | varchar(200)      |      |     |         |       |                 |
| with_car_management_permission           | bool              |      |     |         |       |                 |
| with_commerce_permission                 | bool              |      |     |         |       |                 |
| with_fusion_shop_entry                   | bool              |      |     |         |       |                 |
+------------------------------------------+-------------------+------+-----+---------+-------+-----------------+
```

直播间评论区 - room_comment_box
```shell
##
## data.room.comment_box
##
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type              | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| placeholder                              | tinytext          |      |     |         |       |                    |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
```

图片信息表 live_room_pic
```shell
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                 | Null | Key | Default | Extra | Comment         |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| avg_color                      | varchar(7)           |      |     |         |       | 平均颜色         | 
| content                        | json                 |      |     |         |       |                 |
| flex_setting_list              |                      |      |     |         |       | 灵活设置列表     |
| height                         | unsigned int         |      |     |         |       | 高度             |
| image_type                     | unsigned tinyint     |      |     |         |       | 图片类型         |
| is_animated                    | bool                 |      |     |         |       |                 |
| open_web_url                   | text                 |      |     |         |       |                 |
| text_setting_list              |                      |      |     |         |       | 文本设置列表     |
| uri                            | text                 |      |     |         |       |                 |
| url_list                       | table - live_pic_url |      |     |         |       | 直播图片资源表    |
| width                          | unsigned int         |      |     |         |       | 宽度             |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
```

直播间封面 - cover
```shell
参考 - live_room_pic
```

装饰清单 - deco_list
```shell
+--------------------------------+--------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                     | Null | Key | Default | Extra | Comment         |
+--------------------------------+--------------------------+------+-----+---------+-------+-----------------+
|                                | table - audit_text_color |      |     |         |       |                 |
+--------------------------------+--------------------------+------+-----+---------+-------+-----------------+
```

额外直播信息表 - room_extra
```shell
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                 | Null | Key | Default | Extra | Comment         |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| create_scene                   | tinytext             |      |     |         |       | 创建场景         |
| facial_unrecognised            | unsigned tinyint     |      |     |         |       | 面部无法识别     |
| geo_block                      | unsigned tinyint     |      |     |         |       | 地理封锁         |
| is_sandbox                     | bool                 |      |     |         |       |                 |
| is_virtual_anchor              | bool                 |      |     |         |       |                 |
| limit_appid                    | varchar(200)         |      |     |         |       |                 |
| limit_strategy                 | unsigned tinyint     |      |     |         |       |                 |
| realtime_playback_qualities    | table - live_quality |      |     |         |       | 直播质量表       |
| realtime_playback_shift        | unsigned tinyint     |      |     |         |       |                 |
| realtime_playback_start_shift  | unsigned tinyint     |      |     |         |       |                 |
| realtime_replay_enabled        | bool                 |      |     |         |       |                 |
| vr_type                        | unsigned tinyint     |      |     |         |       |                 |
| vs_type                        | unsigned tinyint     |      |     |         |       |                 |
| xigua_uid                      | varchar(200)         |      |     |         |       |                 |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
```

打赏直播间标签 - feed_room_label
```shell
参考 - live_room_pic
```

指引按钮 - guide_button
```shell
参考 - live_room_pic
```

直播间属性表 live_room_attrs
```shell
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                 | Null | Key | Default | Extra | Comment         |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| admin_flag                     | unsigned tinyint     |      |     |         |       | 管理员标识       |
| rank                           | unsigned smallint    |      |     |         |       | 排名            |
| room_id                        | varchar(200)         | PRI  |     |         |       |                 |
| room_id_str                    | varchar(200)         |      |     |         |       |                 |
| silence_flag                   | unsigned tinyint     |      |     |         |       | 沉默标识         |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
```

直播主播表 room_owner
```shell
+------------------------------------------+-------------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                    | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-------------------------+------+-----+---------+-------+--------------------+
| adversary_authorization_info             | unsigned tinyint        |      |     |         |       |                    |
| adversary_user_status                    | unsigned tinyint        |      |     |         |       |                    |
| age_range                                | unsigned tinyint        |      |     |         |       | 年纪范围            |
| allow_be_located                         | bool                    |      |     |         |       | 允许被定位          |
| allow_find_by_contacts                   | bool                    |      |     |         |       | 允许通过通讯录被发现 |
| allow_others_download_video              | bool                    |      |     |         |       | 允许其它人下载作品   |
| allow_others_download_when_sharing_video | bool                    |      |     |         |       | 允许被分享人下载作品 |
| allow_share_show_profile                 | bool                    |      |     |         |       | 允许分享显示个人资料 |
| allow_show_in_gossip                     | bool                    |      |     |         |       | 允许在八卦中显示    |
| allow_show_my_action                     | bool                    |      |     |         |       | 允许显示我的行为    |
| allow_strange_comment                    | bool                    |      |     |         |       |                    |
| allow_unfollower_comment                 | bool                    |      |     |         |       |                    |
| allow_use_linkmic                        | bool                    |      |     |         |       |                    |
| authorization_info                       | unsigned tinyint        |      |     |         |       |                    |
| avatar_large                             |                         |      |     |         |       | 头像，查看图片信息表 |
| avatar_medium                            |                         |      |     |         |       | 头像，查看图片信息表 |
| avatar_thumb                             |                         |      |     |         |       | 头像，查看图片信息表 |
| badge_image_list                         |                         |      |     |         |       | 头像，查看图片信息表 |
| badge_image_list_v2                      |                         |      |     |         |       | 头像，查看图片信息表 |
| bg_img_url                               | text                    |      |     |         |       |                    |
| birthday                                 | timestamp               |      |     |         |       |                    |
| birthday_description                     | text                    |      |     |         |       |                    |
| birthday_valid                           | bool                    |      |     |         |       |                    |
| block_status                             | unsigned tinyint        |      |     |         |       |                    |
| city                                     | varchar(100)            |      |     |         |       | 城市               |
| comment_restrict                         | unsigned tinyint        |      |     |         |       | 限制评论           |
| commerce_webcast_config_ids              |                         |      |     |         |       |                    |
| constellation                            | varchar(20)             |      |     |         |       | 星座               |
| consume_diamond_level                    | unsigned smallint       |      |     |         |       | 消费钻石等级        |
| create_time                              | timestamp               |      |     |         |       | 创建时间            |
| desensitized_nickname                    | varchar(50)             |      |     |         |       | 去敏感化的昵称      |
| disable_ichat                            | unsigned tinyint        |      |     |         |       | 禁止聊天            |
| display_id                               | varchar(200)            |      |     |         |       | 显示ID             |
| enable_ichat_img                         | unsigned tinyint        |      |     |         |       |                    |
| exp                                      | unsigned int            |      |     |         |       |                    |
| experience                               | unsigned int            |      |     |         |       |                    |
| fan_ticket_count                         | unsigned int            |      |     |         |       | 粉丝票数量          |
| fans_club                                |                         |      |     |         |       | 粉丝俱乐部          |
| fans_group_info                          | json                    |      |     |         |       | 粉丝群信息          |
| fold_stranger_chat                       | bool                    |      |     |         |       | 折叠陌生人聊天      |
| follow_info                              |                         |      |     |         |       | 关注信息            |
| follow_status                            | unsigned tinyint        |      |     |         |       | 关注状态            |
| gender                                   | unsigned tinyint        |      |     |         |       | 性别               |
| hotsoon_verified                         | bool                    |      |     |         |       |                 |
| hotsoon_verified_reason                  | text                    |      |     |         |       |                 |
| ichat_restrict_type                      | unsigned tinyint        |      |     |         |       |                 |
| id                                       | varchar(200)            |      |     |         |       |                 |
| id_str                                   | varchar(200)            |      |     |         |       |                 |
| income_share_percent                     | unsigned tinyint        |      |     |         |       |                 |
| is_anonymous                             | bool                    |      |     |         |       |                 |
| is_follower                              | bool                    |      |     |         |       |                 |
| is_following                             | bool                    |      |     |         |       |                 |
| j_accredit_info                          | json                    |      |     |         |       | 认证信息         |
| level                                    | unsigned smallint       |      |     |         |       | 等级            |
| link_mic_stats                           | unsigned smallint       |      |     |         |       | 连麦统计         |
| location_city                            | varchar(100)            |      |     |         |       | 定位城市         |
| media_badge_image_list                   |                         |      |     |         |       |                 |
| modify_time                              | timestamp               |      |     |         |       |                 |
| mystery_man                              | unsigned tinyint        |      |     |         |       | 神秘人           |
| need_profile_guide                       | bool                    |      |     |         |       |                 |
| new_real_time_icons                      | list                    |      |     |         |       |                 |
| nickname                                 | varchar(50)             |      |     |         |       | 昵称            |
| own_room                                 |                         |      |     |         |       |                 |
| pay_grade                                |                         |      |     |         |       |                 |
| pay_score                                | unsigned int            |      |     |         |       |                 |
| pay_scores                               | unsigned int            |      |     |         |       |                 |
| public_area_oper_freq                    | unsigned smallint       |      |     |         |       |                 |
| push_comment_status                      | bool                    |      |     |         |       |                 |
| push_digg                                | bool                    |      |     |         |       |                 |
| push_follow                              | bool                    |      |     |         |       |                 |
| push_friend_action                       | bool                    |      |     |         |       |                 |
| push_ichat                               | bool                    |      |     |         |       |                 |
| push_status                              | bool                    |      |     |         |       |                 |
| push_video_post                          | bool                    |      |     |         |       |                 |
| push_video_recommend                     | bool                    |      |     |         |       |                 |
| real_time_icons                          |                         |      |     |         |       |                 |
| remark_name                              | varchar(50)             |      |     |         |       |                 |
| sec_uid                                  | varchar(200)            |      |     |         |       |                 |
| secret                                   | unsigned tinyint        |      |     |         |       |                 |
| share_qrcode_uri                         | text                    |      |     |         |       |                 |
| short_id                                 | varchar(200)            |      |     |         |       |                 |
| signature                                | text                    |      |     |         |       |                 |
| special_id                               | varchar(200)            |      |     |         |       |                 |
| status                                   | unsigned tinyint        |      |     |         |       | 主播状态         |
| subscribe                                |                         |      |     |         |       | 订阅            |
| telephone                                | varchar(20)             |      |     |         |       | 手机号码         |
| ticket_count                             | unsigned int            |      |     |         |       |                 |
| top_fans                                 |                         |      |     |         |       |                 |
| top_vip_no                               | unsigned int            |      |     |         |       |                 |
| total_recharge_diamond_count             | unsigned int            |      |     |         |       | 钻石充值总数     |
| user_attr                                | table - user_attr       |      |     |         |       |                 |
| user_canceled                            | bool                    |      |     |         |       | 用户已取消       |
| user_dress_info                          | table - user_dress_info |      |     |         |       |                 |
| user_open_id                             | varchar(200)            |      |     |         |       |                 |
| user_role                                | unsigned tinyint        |      |     |         |       |                 |
| verified                                 | bool                    |      |     |         |       |                 |
| verified_content                         | tinytext                |      |     |         |       |                 |
| verified_mobile                          | bool                    |      |     |         |       |                 |
| verified_reason                          | tinytext                |      |     |         |       |                 |
| watch_duration_month                     | unsigned smallint       |      |     |         |       |                 |
| web_rid                                  | varchar(200)            |      |     |         |       |                 |
| webcast_uid                              | varchar(200)            |      |     |         |       |                 |
| with_car_management_permission           | bool                    |      |     |         |       |                 |
| with_commerce_permission                 | bool                    |      |     |         |       |                 |
| with_fusion_shop_entry                   | bool                    |      |     |         |       |                 |
+------------------------------------------+-------------------------+------+-----+---------+-------+-----------------+
```

打包元数据 - pack_meta
```shell
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                 | Null | Key | Default | Extra | Comment         |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| cluster                        | varchar(20)          |      |     |         |       |                 |
| dc                             | varchar(20)          |      |     |         |       |                 |
| env                            | varchar(20)          |      |     |         |       |                 |
| extras                         | json                 |      |     |         |       |                 |
| scene                          | tinytedt             |      |     |         |       |                 |
| trace_id                       | varchar(200)         |      |     |         |       |                 |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
```

支付直播数据 - paid_live_data
```shell
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                 | Null | Key | Default | Extra | Comment         |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| anchor_right                   | unsigned tinyint     |      |     |         |       | 锚定右侧         |
| delivery                       | unsigned tinyint     |      |     |         |       | 快递             |
| duration                       | timestamp            |      |     |         |       | 持续时间         |
| max_preview_duration           | timestamp            |      |     |         |       | 最大预览持续时间  |
| need_delivery_notice           | bool                 |      |     |         |       | 需要送货通知     |
| paid_type                      | unsigned tinyint     |      |     |         |       | 付费类型         |
| pay_ab_type                    | unsigned tinyint     |      |     |         |       |                 |
| privilege_info                 | json                 |      |     |         |       | 特权信息         |
| privilege_info_map             | json                 |      |     |         |       | 特权信息图       |
| view_right                     | unsigned tinyint     |      |     |         |       | 向右查看         |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
```

room_auth
```shell
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                 | Null | Key | Default | Extra | Comment         |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| AIClone                        |                      |      |     |         |       |                 |
| AdminCommentWall               |                      |      |     |         |       |                 |
| AnchorAudioChat                |                      |      |     |         |       |                 |
| AnchorColdMessageTiled         |                      |      |     |         |       |                 |
| AnchorHotMessageAggregated     |                      |      |     |         |       |                 |
| AnchorMission                  |                      |      |     |         |       |                 |
| AudioChat                      |                      |      |     |         |       |                 |
| AudioChatTotext                |                      |      |     |         |       |                 |
| Banner                         |                      |      |     |         |       |                 |
| BulletStyle                    |                      |      |     |         |       |                 |
| CanSellTicket                  |                      |      |     |         |       |                 |
| CastScreen                     |                      |      |     |         |       |                 |
| CastScreenExplicit             |                      |      |     |         |       |                 |
| Chat                           |                      |      |     |         |       |                 |
| ChatDispatch                   |                      |      |     |         |       |                 |
| ChatDynamicSlideSpeed          |                      |      |     |         |       |                 |
| ChatDynamicSlideSpeedAnchor    |                      |      |     |         |       |                 |
| ChatGuideEmoji                 |                      |      |     |         |       |                 |
| ChatGuideImage                 |                      |      |     |         |       |                 |
| ChatIdentity                   |                      |      |     |         |       |                 |
| ChatMention                    |                      |      |     |         |       |                 |
| ChatMentionV2                  |                      |      |     |         |       |                 |
| ChatOperate                    |                      |      |     |         |       |                 |
| ChatReply                      |                      |      |     |         |       |                 |
| ClearEntranceOption            |                      |      |     |         |       |                 |
| Collect                        |                      |      |     |         |       |                 |
| CommentWall                    |                      |      |     |         |       |                 |
| CommerceCard                   |                      |      |     |         |       |                 |
| CommerceComponent              |                      |      |     |         |       |                 |
| CommonCard                     |                      |      |     |         |       |                 |
| CountType                      |                      |      |     |         |       |                 |
| Danmaku                        |                      |      |     |         |       |                 |
| DanmakuDefault                 |                      |      |     |         |       |                 |
| Denounce                       |                      |      |     |         |       |                 |
| Digg                           |                      |      |     |         |       |                 |
| Dislike                        |                      |      |     |         |       |                 |
| DonationSticker                |                      |      |     |         |       |                 |
| DouPlus                        |                      |      |     |         |       |                 |
| DouPlusPopularityGem           |                      |      |     |         |       |                 |
| DownloadVideo                  |                      |      |     |         |       |                 |
| EcomFansClub                   |                      |      |     |         |       |                 |
| EmojiOutside                   |                      |      |     |         |       |                 |
| EnhancedTouch                  |                      |      |     |         |       |                 |
| EnterEffects                   |                      |      |     |         |       |                 |
| ExpandScreen                   |                      |      |     |         |       |                 |
| FansClub                       |                      |      |     |         |       |                 |
| FansClubBlessing               |                      |      |     |         |       |                 |
| FansClubDeclaration            |                      |      |     |         |       |                 |
| FansClubLetter                 |                      |      |     |         |       |                 |
| FansClubNotice                 |                      |      |     |         |       |                 |
| FansGroup                      |                      |      |     |         |       |                 |
| FeaturedPublicScreen           |                      |      |     |         |       |                 |
| FirstFeedHistChat              |                      |      |     |         |       |                 |
| FixedChat                      |                      |      |     |         |       |                 |
| FrequentlyChat                 |                      |      |     |         |       |                 |
| FusionEmoji                    |                      |      |     |         |       |                 |
| GamePointsPlaying              |                      |      |     |         |       |                 |
| Gift                           |                      |      |     |         |       |                 |
| GiftAnchorMt                   |                      |      |     |         |       |                 |
| GiftVote                       |                      |      |     |         |       |                 |
| Highlights                     |                      |      |     |         |       |                 |
| HostTeam                       |                      |      |     |         |       |                 |
| HostTeamChannel                |                      |      |     |         |       |                 |
| HotChatTray                    |                      |      |     |         |       |                 |
| HourRank                       |                      |      |     |         |       |                 |
| ImHeatValue                    |                      |      |     |         |       |                 |
| IndustryService                |                      |      |     |         |       |                 |
| InteractionGift                |                      |      |     |         |       |                 |
| InteractiveComponent           |                      |      |     |         |       |                 |
| ItemShare                      |                      |      |     |         |       |                 |
| KtvOrderSong                   |                      |      |     |         |       |                 |
| Landscape                      |                      |      |     |         |       |                 |
| LandscapeChat                  |                      |      |     |         |       |                 |
| LandscapeChatDynamicSlideSpeed |                      |      |     |         |       |                 |
| LandscapeGift                  |                      |      |     |         |       |                 |
| LandscapeScreenCapture         |                      |      |     |         |       |                 |
| LandscapeScreenRecording       |                      |      |     |         |       |                 |
| LandscapeScreenShare           |                      |      |     |         |       |                 |
| Like                           |                      |      |     |         |       |                 |
| LinkmicGuestLike               |                      |      |     |         |       |                 |
| LongPressOption                |                      |      |     |         |       |                 |
| LongTouch                      |                      |      |     |         |       |                 |
| LuckMoney                      |                      |      |     |         |       |                 |
| MarkUser                       |                      |      |     |         |       |                 |
| MediaHistoryMessage            |                      |      |     |         |       |                 |
| MediaLinkmic                   |                      |      |     |         |       |                 |
| MessageDispatch                |                      |      |     |         |       |                 |
| MessageGift                    |                      |      |     |         |       |                 |
| MissionCenter                  |                      |      |     |         |       |                 |
| MoreAnchor                     |                      |      |     |         |       |                 |
| MoreHistChat                   |                      |      |     |         |       |                 |
| MultiplierPlayback             |                      |      |     |         |       |                 |
| MyLiveEntrance                 |                      |      |     |         |       |                 |
| OnlyTa                         |                      |      |     |         |       |                 |
| PCPlay                         |                      |      |     |         |       |                 |
| POI                            |                      |      |     |         |       |                 |
| PadPlay                        |                      |      |     |         |       |                 |
| PanelECService                 |                      |      |     |         |       |                 |
| PlayerRankList                 |                      |      |     |         |       |                 |
| Poster                         |                      |      |     |         |       |                 |
| PosterCache                    |                      |      |     |         |       |                 |
| PreviewChatExpose              |                      |      |     |         |       |                 |
| PreviewHotCommentSwitch        |                      |      |     |         |       |                 |
| ProjectionBtn                  |                      |      |     |         |       |                 |
| Props                          |                      |      |     |         |       |                 |
| PublicScreen                   |                      |      |     |         |       |                 |
| QuizGamePointsPlaying          |                      |      |     |         |       |                 |
| RecordScreen                   |                      |      |     |         |       |                 |
| RoomChannel                    |                      |      |     |         |       |                 |
| RoomChatLikeDisplay            |                      |      |     |         |       |                 |
| RoomChatOperatePanel           |                      |      |     |         |       |                 |
| RoomContributor                |                      |      |     |         |       |                 |
| RoomWidget                     |                      |      |     |         |       |                 |
| ScreenBottomInfo               |                      |      |     |         |       |                 |
| ScreenProjectionBarrage        |                      |      |     |         |       |                 |
| Seek                           |                      |      |     |         |       |                 |
| Selection                      |                      |      |     |         |       |                 |
| SelectionAlbum                 |                      |      |     |         |       |                 |
| Share                          |                      |      |     |         |       |                 |
| ShortTouch                     |                      |      |     |         |       |                 |
| ShortTouchTempState            |                      |      |     |         |       |                 |
| ShowGamePlugin                 |                      |      |     |         |       |                 |
| ShowQualification              |                      |      |     |         |       |                 |
| SmallWindowDisplay             |                      |      |     |         |       |                 |
| SmallWindowPlayer              |                      |      |     |         |       |                 |
| StickyMessage                  |                      |      |     |         |       |                 |
| StreamAdaptation               |                      |      |     |         |       |                 |
| StrokeUpDownGuide              |                      |      |     |         |       |                 |
| SubscribeCardPackage           |                      |      |     |         |       |                 |
| Teleprompter                   |                      |      |     |         |       |                 |
| TextGift                       |                      |      |     |         |       |                 |
| TimedShutdown                  |                      |      |     |         |       |                 |
| ToolbarBubble                  |                      |      |     |         |       |                 |
| Topic                          |                      |      |     |         |       |                 |
| TypingCommentState             |                      |      |     |         |       |                 |
| UgcVSReplayDelete              |                      |      |     |         |       |                 |
| UgcVsReplayVisibility          |                      |      |     |         |       |                 |
| UpRightStatsFloatingLayer      |                      |      |     |         |       |                 |
| UseHostInfo                    |                      |      |     |         |       |                 |
| UserCard                       |                      |      |     |         |       |                 |
| UserCorner                     |                      |      |     |         |       |                 |
| VSGift                         |                      |      |     |         |       |                 |
| VSRank                         |                      |      |     |         |       |                 |
| VSTopic                        |                      |      |     |         |       |                 |
| VerticalRank                   |                      |      |     |         |       |                 |
| VerticalScreenShare            |                      |      |     |         |       |                 |
| VideoAmplificationType         |                      |      |     |         |       |                 |
| VideoShare                     |                      |      |     |         |       |                 |
| VsCommentBar                   |                      |      |     |         |       |                 |
| VsDouPlus                      |                      |      |     |         |       |                 |
| VsExtensionEnableFollow        |                      |      |     |         |       |                 |
| VsFansClub                     |                      |      |     |         |       |                 |
| VsWelcomeDanmaku               |                      |      |     |         |       |                 |
| WordAssociation                |                      |      |     |         |       |                 |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
```

room_view_stats
```shell
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                 | Null | Key | Default | Extra | Comment         |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| display_long                   | tinytext             |      |     |         |       | 直播间观看人数   |
| display_long_anchor            | tinytext             |      |     |         |       | 主播观看人数     |
| display_middle                 | tinytext             |      |     |         |       |                 |
| display_middle_anchor          | tinytext             |      |     |         |       |                 |
| display_short                  | tinytext             |      |     |         |       |                 |
| display_short_anchor           | tinytext             |      |     |         |       |                 |
| display_type                   | unsigned tinyint     |      |     |         |       |                 |
| display_value                  | unsigned int         |      |     |         |       |                 |
| display_version                | varchar(20)          |      |     |         |       |                 |
| incremental                    | bool                 |      |     |         |       |                 |
| is_hidden                      | bool                 |      |     |         |       |                 |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
```

short_touch_area_config
```shell
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                 | Null | Key | Default | Extra | Comment         |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| elements                       |                      |      |     |         |       |                 |
| forbidden_types_map            |                      |      |     |         |       |                 |
| strategy_feat_whitelist        |                      |      |     |         |       |                 |
| temp_state_condition_map       |                      |      |     |         |       |                 |
| temp_state_global_condition    |                      |      |     |         |       |                 |
| temp_state_strategy            |                      |      |     |         |       |                 |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
```

直播间状态 - room_stats
```shell
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                               | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| comment_count                  | unsigned bigint                    |      |     |         |       | 评论数量         |
| digg_count                     |                                    |      |     |         |       |                 |
| dou_plus_promotion             |                                    |      |     |         |       | 抖+促销          |
| enter_count                    | unsigned int                       |      |     |         |       | 进入数量         |
| fan_ticket                     | unsigned bigint                    |      |     |         |       | 粉丝票           |
| follow_count                   | unsigned bigint                    |      |     |         |       | 关注数量         |
| gift_uv_count                  | unsigned int                       |      |     |         |       | 礼物UV数量       |
| id                             | varchar(200)                       |      |     |         |       | 直播间ID         |
| id_str                         | varchar(200)                       |      |     |         |       | 直播间ID         |
| like_count                     | unsigned int                       |      |     |         |       | 点赞数量         |
| money                          | unsigned int                       |      |     |         |       | 金钱             |
| total_user                     | unsigned int                       |      |     |         |       | 用户数量         |
| total_user_desp                |
| total_user_str                 | varchar(100)                       |      |     |         |       | 用户数量         |
| up_right_stats_str             | varchar(100)                       |      |     |         |       | 右上角状态条     |
| up_right_stats_str_complete    |                                                                   | 右上角状态条完成  |
| user_count_composition         |                                                                   | 用户数量组成     |
| user_count_str                 | varchar(100)                       |      |     |         |       | 用户数量         |
| watermelon                     | 
| welfare_donation_amount        | unsigned int                       |      |     |         |       | 福利捐赠金额     |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
```

直播流信息表 - stream_url
```shell
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type              | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| candidate_resolution                     | varchar(20)       |      |     |         |       | 候选分辨率          |
| complete_push_urls                       |                   |      |     |         |       |                    |
| default_resolution                       | varchar(20)       |      |     |         |       | 默认分辨率          |
| extra                                    | json              |      |     |         |       |                    |
| flv_pull_url                             |                   |      |     |         |       |                    |
| flv_pull_url_params                      |                   |      |     |         |       |                    |
| hls_pull_url                             | text              |      |     |         |       |                    |
| hls_pull_url_map                         |                   |      |     |         |       |                    |
| hls_pull_url_params                      | text              |      |     |         |       |                    |
| id                                       | varchar(200)      |      |     |         |       |                    |
| id_str                                   | varchar(200)      |      |     |         |       |                    |
| live_core_sdk_data                       |                   |      |     |         |       |                    |
| provider                                 | unsigned tinyint  |      |     |         |       |                    |
| pull_datas                               | json              |      |     |         |       |                    |
| push_datas                               | json              |      |     |         |       |                    |
| push_stream_type                         | unsigned tinyint  |      |     |         |       | 推流类型            |
| push_urls                                |                   |      |     |         |       |                    |
| resolution_name                          |                   |      |     |         |       | 分辨率名称          |
| rtmp_pull_url                            | text              |      |     |         |       |                    |
| rtmp_pull_url_params                     | text              |      |     |         |       |                    |
| rtmp_push_url                            | text              |      |     |         |       |                    |
| rtmp_push_url_params                     | text              |      |     |         |       |                    |
| stream_control_type                      | unsigned tinyint  |      |     |         |       |                    |
| stream_orientation                       | unsigned tinyint  |      |     |         |       |                    |
| vr_type                                  | unsigned tinyint  |      |     |         |       |                    |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
```
===
审核文本颜色 - audit_text_color
```shell
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type              | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| content
| h
| id
| image
| input_rect
| kind
| max_length
| nine_patch_image
| reservation
| status
| sub_type
| text_color
| text_image_adjustable_end_position
| text_image_adjustable_start_position
| text_size
| text_special_effects
| type
| w
| x
| y
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
```

直播间打赏标签内容 - content
```shell
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type              | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| alternative_text
| font_color
| level
| name
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
```

badge_image_list
```shell
+------------------------------------------+-----------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                  | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-----------------------+------+-----+---------+-------+--------------------+
|                                          | table - live_room_pic |      |     |         |       |                    |
+------------------------------------------+-----------------------+------+-----+---------+-------+--------------------+
+-----
```

badge_image_list_v2
```shell
+------------------------------------------+-----------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                  | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-----------------------+------+-----+---------+-------+--------------------+
|                                          | table - live_room_pic |      |     |         |       |                    |
+------------------------------------------+-----------------------+------+-----+---------+-------+--------------------+
```

粉丝俱乐部 - fans_club
```shell
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                   | Null | Key | Default | Extra | Comment            |
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| data                                     | table - fans_club_data |      |     |         |       |                    |
| prefer_data                              | json                   |      |     |         |       |                    |
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
```

粉丝群信息 - fans_group_info
```shell
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                   | Null | Key | Default | Extra | Comment            |
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| list_fans_group_url                      | text                   |      |     |         |       |                    |
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
```

关注信息 - follow_info
```shell
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                   | Null | Key | Default | Extra | Comment            |
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| follow_status                            | tinyint                |      |     |         |       |                    |
| follower_count
| follower_count_str
| following_count
| following_count_str
| invalid_follow_status
| push_status
| remark_name
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
```

j_accredit_info
```shell
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                   | Null | Key | Default | Extra | Comment            |
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| JAccreditAdvance
| JAccreditBasic
| JAccreditContent
| JAccreditLive
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
```
own_room
```shell
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                   | Null | Key | Default | Extra | Comment            |
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| room_ids
| room_ids_display
| room_ids_str
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
```

支付等级 - pay_grade
```shell
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                   | Null | Key | Default | Extra | Comment            |
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| grade_banner
| grade_describe
| grade_describe_shining
| grade_icon_list
| level
| name
| new_im_icon_with_level
| new_live_icon
| next_diamond
| next_name
| next_privileges
| now_diamond
| pay_diamond_bak
| score
| screen_chat_type
| this_grade_max_diamond
| this_grade_min_diamond
| total_diamond_count
| upgrade_need_consume
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
```

订阅 - subscribe
```shell
##
## data.room.owner.subscribe
##
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                   | Null | Key | Default | Extra | Comment            |
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| buy_type                                 | unsigned tinyint       |      |     |         |       | 购买类型            |
| identity_type                            | unsigned tinyint       |      |     |         |       | 身份类型            |
| is_member                                | bool                   |      |     |         |       | 是否为会员          |
| level                                    | unsigned smallint      |      |     |         |       | 订阅等级            |
| open                                     | unsigned tinyint       |      |     |         |       | 是否开放            |
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
```

user_attr
```shell
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                   | Null | Key | Default | Extra | Comment            |
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| admin_privileges
| is_admin
| is_muted
| is_super_admin
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
```

user_dress_info
```shell
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                   | Null | Key | Default | Extra | Comment            |
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
| dress_own_ids
| dress_wear_ids
+------------------------------------------+------------------------+------+-----+---------+-------+--------------------+
```

elements
```shell
+------------------------------------------+------------------------------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                                     | Null | Key | Default | Extra | Comment            |
+------------------------------------------+------------------------------------------+------+-----+---------+-------+--------------------+
| '1'                                      | table - short_touch_area_config_elements |      |     |         |       |                    |
| ...                                      | table - short_touch_area_config_elements |      |     |         |       |                    |
+------------------------------------------+------------------------------------------+------+-----+---------+-------+--------------------+
```

临时状态条件图 - temp_state_condition_map
```shell
+------------------------------------------+------------------------------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                                     | Null | Key | Default | Extra | Comment            |
+------------------------------------------+------------------------------------------+------+-----+---------+-------+--------------------+
| '1'                                      | table - temp_state_condition             |      |     |         |       |                    |
| ...                                      | table - temp_state_condition             |      |     |         |       |                    |
+------------------------------------------+------------------------------------------+------+-----+---------+-------+--------------------+
```

temp_state_global_condition
```shell
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                               | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| allow_count
| duration_gap
| ignore_strategy_types
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
```

临时状态策略 - temp_state_strategy
```shell
+------------------------------------------+------------------------------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type                                     | Null | Key | Default | Extra | Comment            |
+------------------------------------------+------------------------------------------+------+-----+---------+-------+--------------------+
| '1'                                      | table - temp_state_condition             |      |     |         |       |                    |
| ...                                      | table - temp_state_condition             |      |     |         |       |                    |
+------------------------------------------+------------------------------------------+------+-----+---------+-------+--------------------+
```

user_count_composition
```shell
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                               | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| city                           | unsigned tinyint                   |      |     |         |       |                 |
| my_follow                      | unsigned tinyint                   |      |     |         |       |                 |
| other                          | unsigned tinyint                   |      |     |         |       |                 |
| video_detail                   | unsigned tinyint                   |      |     |         |       |                 |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
```

直播流额外信息表 - stream_url_extra
```shell
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type              | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| anchor_interact_profile                  |                   |      |     |         |       |                    |
| audience_interact_profile                |                   |      |     |         |       |                    |
| bframe_enable                            |                   |      |     |         |       |                    |
| bitrate_adapt_strategy                   |                   |      |     |         |       |                    |
| bytevc1_enable                           |                   |      |     |         |       |                    |
| default_bitrate                          |                   |      |     |         |       |                    |
| fps                                      |                   |      |     |         |       |                    |
| gop_sec                                  |                   |      |     |         |       |                    |
| h265_enable                              | bool              |      |     |         |       |                    |
| hardware_encode                          | bool              |      |     |         |       |                    |
| height                                   | unsigned smallint |      |     |         |       |                    |
| max_bitrate                              |                   |      |     |         |       |                    |
| min_bitrate                              |                   |      |     |         |       |                    |
| roi                                      | bool              |      |     |         |       |                    |
| sw_roi                                   | bool              |      |     |         |       |                    |
| video_profile                            |                   |      |     |         |       |                    |
| width                                    | unsigned smallint |      |     |         |       |                    |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
```

flv_pull_url
```shell
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type              | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| FULL_HD1
| HD1
| SD1
| SD2
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
```

flv_pull_url_params
```shell
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type              | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| HD1
| SD1
| SD2
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
```

hls_pull_url_map
```shell
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type              | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| FULL_HD1
| HD1
| SD1
| SD2
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
```

live_core_sdk_data
```shell
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type              | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| pull_data
| size
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
```

resolution_name
```shell
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| Field                                    | Type              | Null | Key | Default | Extra | Comment            |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
| FULL_HD1
| HD1
| ORIGIN
| SD1
| SD2
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------+
```
===

预定 - reservation
```shell
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| Field                          | Type             | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| anchor_id
| anchor_open_id
| appointment_id
| btn_color
| btn_rect
| end_time
| is_reserved
| room_id
| start_time
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
```

粉丝俱乐部数据 - fans_club_data

```shell
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| Field                          | Type             | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| anchor_id
| anchor_open_id
| available_gift_ids
| badge
| badge_type
| club_name
| guard_expired_time
| level
| user_fans_club_status
| user_guard_status
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
```

短接触区域配置元素 - short_touch_area_config_elements
```shell
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                               | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| priority                       | unsigned tinyint                   |      |     |         |       |                 |
| type                           | unsigned tinyint                   |      |     |         |       |                 |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
```

temp_state_condition
```shell
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                               | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| minimum_gap                    |                                    |      |     |         |       |                 |
| type                           | table                              |      |     |         |       |                 |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
```

temp_state_strategy_item
```shell
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                               | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| short_touch_type               | unsigned tinyint                   |      |     |         |       |                 |
| strategy_map                   |                                    |      |     |         |       |                 |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
```

pull_data
```shell
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| Field                          | Type             | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| Flv
| Hls
| codec
| compensatory_data
| hls_data_unencrypted
| kind
| options
| stream_data
| version
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
```

live_core_sdk_pull_data_options
```shell
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| Field                          | Type             | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| default_quality
| qualities
| vpass_default
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
```
===
fans_club_badge
```shell
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| Field                          | Type             | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| icons                          |                  |      |     |         |       |                 |
| title                          |                  |      |     |         |       |                 |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
```

temp_state_condition_map_type
```shell
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| Field                          | Type             | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| priority                       |                  |      |     |         |       |                 |
| strategy_type                  |                  |      |     |         |       |                 |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
```

strategy_map
```shell
+--------------------------------+---------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                      | Null | Key | Default | Extra | Comment         |
+--------------------------------+---------------------------+------+-----+---------+-------+-----------------+
| '1'                            | table - strategy_map_item |      |     |         |       |                 |
| ...                            | table - strategy_map_item |      |     |         |       |                 |
+--------------------------------+---------------------------+------+-----+---------+-------+-----------------+
```

strategy_map_item
```shell
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| Field                          | Type             | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| duration                       |                  |      |     |         |       |                 |
| strategy_method                |
| strategy_map                   |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
```

default_quality
```shell
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| Field                          | Type             | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| additional_content             |                  |      |     |         |       |                 |
| disable                        |
| fps                            |
| level
| name
| resolution
| sdk_key
| v_bit_rate
| v_codec
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
```

additional_content
```shell
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| Field                          | Type             | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| disable                        |
| fps                            |
| level
| name
| resolution
| sdk_key
| v_bit_rate
| v_codec
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
```

短接触区域配置 - short_touch_area_config
```shell
+--------------------------------+------------------------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                                     | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------------------------------+------+-----+---------+-------+-----------------+
| elements                       | table - short_touch_area_config_elements | NULL |     |         |       |                 |
| forbidden_types_map            | json                                     | NULL |     |         |       |                 |
| strategy_feat_whitelist        | table - strategy_feat_whitelist          | NULL |     |         |       |                 |
| temp_state_condition_map       | table - temp_state_condition_map         | NULL |     |         |       |                 |
| temp_state_global_condition    | table - temp_state_global_condition      | NULL |     |         |       |                 |
| temp_state_strategy            | table - temp_state_strategy              | NULL |     |         |       |                 |
+--------------------------------+------------------------------------------+------+-----+---------+-------+-----------------+
```

直播间用户 ID 记录表 - live_room_user_id
```shell
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| Field                          | Type             | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| room_id                        | varchar(200)     |      |     |         |       |                 |
| start_time                     | timestamp        |      |     |         |       |                 |
| owner                          | bool             |      |     |         |       |                 |
| room_admin                     | bool             |      |     |         |       |                 |
| fans_group_admin               | bool             |      |     |         |       |                 |
| user_id                        | varchar(200)     |      |     |         |       |                 |
| user_open_id                   | varchar(200)     |      |     |         |       |                 |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
```

直播流质量表 live_stream
```shell
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| Field                          | Type             | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
| quality                        | varchar(10)      |      |     |         |       |                 |
| url                            | text             |      |     |         |       |                 |
+--------------------------------+------------------+------+-----+---------+-------+-----------------+
```

直播间过滤词 - live_room_filter_word
```shell
##
## data.room.fliter_words
##
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                 | Null | Key | Default | Extra | Comment         |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| filter_word                    | varchar(20)          |      |     |         |       |                 |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
```

分享音乐ID - live_room_sharing_music_id
```shell
##
## data.room.sharing_music_id_list
##
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                 | Null | Key | Default | Extra | Comment         |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
| sharing_music_id               | varchar(200)         |      |     |         |       | 分享音乐ID       |
+--------------------------------+----------------------+------+-----+---------+-------+-----------------+
```

直播间标签 - live_room_tag
```shell
##
## 
##
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                               | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| tag                            | tinytext                           |      |     |         |       |                 |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
```

策略壮举白名单 - strategy_feat_whitelist

```shell
##
## data.room.short_touch_area_config.strategy_feat_whitelist
##
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                               | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| strategy_feat_whiteitem        | tinytext                           |      |     |         |       |                 |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
```


临时状态全局条件 - temp_state_global_condition
```shell
##
## data.room.short_touch_area_config.temp_state_global_condition
##
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| Field                          | Type                               | Null | Key | Default | Extra | Comment         |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
| allow_count                    | unsigned tinyint                   |      |     |         |       |                 |
| duration_gap                   | unsigned tinyint                   |      |     |         |       |                 |
| ignore_strategy_types          | unsigned tinyint                   |      |     |         |       |                 |
+--------------------------------+------------------------------------+------+-----+---------+-------+-----------------+
```

### tree 图
```shell
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
│   │   ├── 4-10-3. own_room
│   │   │   ├── 4-10-3-1. own_room_id
│   │   │   └── 4-10-3-2. own_room_id_display
│   │   ├── 4-10-4. media_badge_image - TBD
│   │   ├── 4-10-5. new_real_time_icon - TBD
│   │   ├── 4-10-6. pay_grade_icon
│   │   ├── 4-10-7. room_owner_real_time_icon - TBD
│   │   ├── 4-10-8. room_subscribe
│   │   ├── 4-10-9. room_owner_top_fans - TBD
│   │   ├── 4-10-10. room_owner_user_attr
│   │   │   └── 4-10-10-1. room_admin_privilege
│   │   ├── 4-10-11. room_owner_auth_info
│   │   │   └── 4-10-11-1. room_owner_auth_level
│   │   ├── 4-10-12. room_owner_user_dress_own_id
│   │   └── 4-10-14. room_owner_dress_wear_id
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
|       ├── 4-16-4. room_temp_state_global_condition
|       └── 4-16-5. room_temp_state_strategy
|           └── 4-16-5-1. room_temp_state_strategy_map
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
```

### 二次数据

1. 分享链接表 - share_url
```shell
+----------------+--------------+------+-----+---------+-------+------------------------------+-----------------+
| Field          | Type         | Null | Key | Default | Extra | Topology                     | Comment         |
+----------------+--------------+------+-----+---------+-------+------------------------------+-----------------+
| owner_user_id  | varchar(200) | NO   | PRI | NULL    |       | "$.data.room.owner_user_id"  | 账号作者ID       |
| sec_user_id    | varchar(200) | YES  |     | NULL    |       |                              | 安全用户ID       |
| nickname       | varchar(50)  | YES  |     | NULL    |       | "$.data.room.owner.nickname" | 昵称             |
| post_share_url | varchar(100) | YES  |     | NULL    |       |             -                | 主页分享链接     |
| live_share_url | varchar(100) | YES  |     | NULL    |       |             -                | 直播分享链接     |
| directory_name | varchar(100) | YES  |     | NULL    |       |             -                | 文件夹名称       |
| user_status    | varchar(100) | YES  |     | NULL    |       |             -                | 用户状态         |
| actived_count  | unsinged int | NO   |     | 0       |       |             -                | 访问次数         |
+----------------+--------------+------+-----+---------+-------+------------------------------+-----------------+
```

2. 喜爱的作者表 - favorite_owner
```shell
+---------------+------------------+------+-----+---------+-------+-----------------------------+-----------------+
| Field         | Type             | Null | Key | Default | Extra | Topology                    | Comment         |
+---------------+------------------+------+-----+---------+-------+-----------------------------+-----------------+
| owner_user_id | varchar(200)     | NO   | PRI | NULL    |       | "$.data.room.owner_user_id" | 账号作者ID       |
| platform      | varchar(20)      | NO   |     | NULL    |       |             -               | 平台             |
| score         | unsigned tinyint | NO   |     | 0       |       |             -               |     0-100       |
+---------------+------------------+------+-----+---------+-------+-----------------------------+-----------------+
```

3. 直播记录表 - live_record
```shell
+-------------+-------------------+------+-----+---------+-------+---------------------------+----------------------+
| Field       | Type              | Null | Key | Default | Extra | Topology                  | Comment              | 
+-------------+-------------------+------+-----+---------+-------+---------------------------+----------------------+
| now         | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"             | 当前时间戳            |
| platform    | varchar(20)       |      |     | NULL    |       |           -               | 平台                  | 
| room_id     | varchar(200)      |      |     | NULL    |       | "$.data.room.id"          | 直播间ID              | 
| user_id     | varchar(200)      |      |     | NULL    |       | "$.data.user.id"          | 当前观众ID            | 
| start_time  | timestamp         |      |     | NULL    |       | "$.data.room.start_time"  | 开始时间              | 
| finish_time | timestamp         |      |     | NULL    |       | "$.data.room.finish_time" | 结束时间              | 
| status_code | unsigned tinyint  |      |     | NULL    |       | "$.status_code"           | 网络请求状态          | 
+-------------+-------------------+------+-----+---------+-------+---------------------------+----------------------+
```

4. 直播间表(静态信息) - room_attribute
```shell
##
## room
##
+-------------------------------+-------------------+------+-----+---------+-------+---------------------------------------------------+---------------------------------+
| Field                         | Type              | Null | Key | Default | Extra |Topology                                           | Comment                         |
+-------------------------------+-------------------+------+-----+---------+-------+---------------------------------------------------+---------------------------------+
| AnchorABMap                   | json              |      |     |         |       | "$.data.room.living_room_attrs.rank"              | 主播AB映射                       | 
| acquaintance_status           | unsigned tinyint  |      |     |         |       | "$.data.room.acquaintance_status"                 | 直播间熟人状态                    |
| anchor_scheduled_time_text    | text              |      |     |         |       | "$.data.room.anchor_scheduled_time_text"          | 直播间布局                       |
| anchor_share_text             | text              |      |     |         |       | "$.data.room.anchor_share_text"                   | 主播分享文本                     |
| anchor_tab_type               | unsigned tinyint  |      |     |         |       | "$.data.room.anchor_tab_type"                     | 主播标签类型                     |
| app_id                        | varchar(200)      |      |     |         |       | "$.data.room.app_id"                              | 应用ID                          |
| auth_city                     | varchar(100)      |      |     |         |       | "$.data.room.auth_city"                           | 直播间认证城市                   |
| auto_cover                    | unsigned tinyint  |      |     |         |       | "$.data.room.auto_cover"                          | 自动封面                         |
| base_category                 | unsigned tinyint  |      |     |         |       | "$.data.room.base_category"                       | 基础分类                         |
| book_end_time                 | timestamp         |      |     |         |       | "$.data.room.book_end_time"                       | 直播间预约结束时间                |
| book_time                     | timestamp         |      |     |         |       | "$.data.room.book_time"                           | 直播间预约开始时间                |
| business_live                 | unsigned tinyint  |      |     |         |       | "$.data.room.business_live"                       | 商业直播                         |
| category                      | unsigned tinyint  |      |     |         |       | "$.data.room.category"                            | 分类                            |
| cell_style                    | unsigned tinyint  |      |     |         |       | "$.data.room.cell_style"                          | 直播间单元样式                   |
| city_top_distance             | tinytext          |      |     |         |       | "$.data.room.city_top_distance"                   | 城市顶部距离                     |
| client_version                | varchar(20)       |      |     |         |       | "$.data.room.client_version"                      | 客户端版本                       |
| placeholder                   | tinytext          |      |     |         |       | "$.data.room.comment_box.placeholder"             | 评论框占位符                     |
| comment_name_mode             | unsigned tinyint  |      |     |         |       | "$.data.room.comment_name_mode"                   | 评论名称模式                     |
| common_label_list             | tinytext          |      |     |         |       | "$.data.room.common_label_list"                   | 常用标签列表                     |
| content_tag                   | tinytext          |      |     |         |       | "$.data.room.content_tag"                         | 内容标签                         |
| create_time                   | timestamp         |      |     |         |       | "$.data.room.create_time"                         | 直播间创建时间                    | 
| distance                      | varchar(100)      |      |     |         |       | "$.data.room.distance"                            | 距离                             |
| distance_city                 | varchar(100)      |      |     |         |       | "$.data.room.distance_city"                       | 城市距离                         |
| distance_km                   | varchar(100)      |      |     |         |       | "$.data.room.distance_km"                         | 公里距离                         |
| dynamic_cover_dict            | json              |      |     |         |       | "$.data.room.dynamic_cover_dict"                  | 动态封面字典                     |
| dynamic_cover_uri             | text              |      |     |         |       | "$.data.room.dynamic_cover_uri"                   | 动态封面URI                      |
| enable_room_perspective       | bool              |      |     |         |       | "$.data.room.enable_room_perspective"             | 是否启用直播间透视                |
| create_scene                  | tinytext          |      |     |         |       | "$.data.room.extra.create_scene"                  | 创建场景                         |
| facial_unrecognised           | unsigned tinyint  |      |     |         |       | "$.data.room.extra.facial_unrecognised"           | 面部未识别                       |
| geo_block                     | unsigned tinyint  |      |     |         |       | "$.data.room.extra.geo_block"                     | 地理封锁                         |
| is_sandbox                    | bool              |      |     |         |       | "$.data.room.extra.is_sandbox"                    | 是否为沙盒                       |
| is_virtual_anchor             | bool              |      |     |         |       | "$.data.room.extra.is_virtual_anchor"             | 是否为虚拟主播                   |
| limit_appid                   | varchar(200)      |      |     |         |       | "$.data.room.extra.limit_appid"                   | 限制应用ID                      |
| limit_strategy                | unsigned tinyint  |      |     |         |       | "$.data.room.extra.limit_strategy"                | 地理封锁                        |
| realtime_playback_shift       | unsigned tinyint  |      |     |         |       | "$.data.room.extra.realtime_playback_shift"       | 实时回放偏移                    |
| realtime_playback_start_shift | unsigned tinyint  |      |     |         |       | "$.data.room.extra.realtime_playback_start_shift" | 实时回放开始偏移                 |
| realtime_replay_enabled       | bool              |      |     |         |       | "$.data.room.extra.realtime_replay_enabled"       | 是否启用实时回放                 |
| vr_type                       | unsigned tinyint  |      |     |         |       | "$.data.room.extra.vr_type"                       | VR类型                          |
| vs_type                       | unsigned tinyint  |      |     |         |       | "$.data.room.extra.vs_type"                       | VS类型                          |
| xigua_uid                     | varchar(200)      |      |     |         |       | "$.data.room.extra.xigua_uid"                     | 西瓜用户ID                       |
| fansclub_msg_style            | unsigned tinyint  |      |     |         |       | "$.data.room.fansclub_msg_style"                  | 粉丝俱乐部消息样式                |
| fcdn_appid                    | varchar(200)      |      |     |         |       | "$.data.room.fcdn_appid"                          | FCDN应用ID                       |
| finish_reason                 | unsigned tinyint  |      |     |         |       | "$.data.room.finish_reason"                       | 直播结束原因                     |
| finish_time                   | timestamp         |      |     |         |       | "$.data.room.finish_time"                         | 直播结束时间                     |
| finish_url                    | text              |      |     |         |       | "$.data.room.finish_url"                          | 直播结束URL                      |
| follow_msg_style              | unsigned tinyint  |      |     |         |       | "$.data.room.follow_msg_style"                    | 关注消息样式                     |
| forum_extra_data              | text              |      |     |         |       | "$.data.room.forum_extra_data"                    | 论坛额外数据                     |
| game_room_type                | unsigned tinyint  |      |     |         |       | "$.data.room.game_room_type"                      | 游戏直播间类型                   |
| gift_msg_style                | unsigned tinyint  |      |     |         |       | "$.data.room.gift_msg_style"                      | 礼物消息样式                     |
| group_id                      | varchar(200)      |      |     |         |       | "$.data.room.group_id"                            | 直播间组ID                       |
| group_source                  | unsigned tinyint  |      |     |         |       | "$.data.room.group_source"                        | 直播间组来源                     |
| has_commerce_goods            | bool              |      |     |         |       | "$.data.room.has_commerce_goods"                  | 是否有商品                       |
| has_promotion_games           | bool              |      |     |         |       | "$.data.room.has_promotion_games"                 | 是否有推广游戏                   |
| highlight                     | bool              |      |     |         |       | "$.data.room.highlight"                           | 是否高亮                         |
| id                            | varchar(200)      |      | PRI |         |       | "$.data.room.id"                                  | 直播间 ID                       |
| introduction                  | text              |      |     |         |       | "$.data.room.introduction"                        | 直播间介绍                       |
| is_need_check_list            | bool              |      |     |         |       | "$.data.room.is_need_check_list"                  | 是否需要检查列表                 |
| is_official_channel_room      | bool              |      |     |         |       | "$.data.room.is_official_channel_room"            | 是否为官方频道直播间              |
| is_replay                     | bool              |      |     |         |       | "$.data.room.is_replay"                           | 是否为回放                       |
| is_show_inquiry_ball          | bool              |      |     |         |       | "$.data.room.is_show_inquiry_ball"                | 是否显示询问球                   |
| is_show_user_card_switch      | bool              |      |     |         |       | "$.data.room.is_show_user_card_switch"            | 是否显示用户卡片开关              |
| item_explicit_info            | text              |      |     |         |       | "$.data.room.item_explicit_info"                  | 物品显式信息                     |
| layout                        | unsigned tinyint  |      |     |         |       | "$.data.room.layout"                              | 直播间布局                       |
| linkmic_display_type          | unsigned tinyint  |      |     |         |       | "$.data.room.linkmic_display_type"                | 连麦显示类型                     |
| linkmic_layout                | unsigned tinyint  |      |     |         |       | "$.data.room.linkmic_layout"                      | 连麦布局                         |
| live_id                       | varchar(200)      |      |     |         |       | "$.data.room.live_id"                             | 直播ID                          |
| live_platform_source          | tinytext          |      |     |         |       | "$.data.room.live_platform_source"                | 直播平台来源                     |
| live_room_mode                | unsigned tinyint  |      |     |         |       | "$.data.room.live_room_mode"                      | 直播间模式                       |
| live_type_audio               | bool              |      |     |         |       | "$.data.room.live_type_audio"                     | 是否为音频直播                   |
| live_type_linkmic             | bool              |      |     |         |       | "$.data.room.live_type_linkmic"                   | 是否为连麦直播                   |
| live_type_normal              | bool              |      |     |         |       | "$.data.room.live_type_normal"                    | 是否为普通直播                   |
| live_type_official            | bool              |      |     |         |       | "$.data.room.live_type_official"                  | 是否为官方直播                   |
| live_type_sandbox             | bool              |      |     |         |       | "$.data.room.live_type_sandbox"                   | 是否为沙盒直播                   |
| live_type_screenshot          | bool              |      |     |         |       | "$.data.room.live_type_screenshot"                | 是否为截图直播                   |
| live_type_third_party         | bool              |      |     |         |       | "$.data.room.live_type_third_party"               | 是否为第三方直播                 |
| live_type_vs_live             | bool              |      |     |         |       | "$.data.room.live_type_vs_live"                   | 是否为VS直播                     |
| live_type_vs_premiere         | bool              |      |     |         |       | "$.data.room.live_type_vs_premiere"               | 是否为VS首播                     |
| admin_flag                    | unsigned tinyint  |      |     |         |       | "$.data.room.living_room_attrs.admin_flag"        | 直播间管理员标志                  |
| location                      | varchar(100)      |      |     |         |       | "$.data.room.location"                            | 直播间位置                        |
| official_channel_open_id      | varchar(200)      |      |     |         |       | "$.data.room.official_channel_open_id"            | 官方频道OpenID                   |
| official_channel_uid          | varchar(200)      |      |     |         |       | "$.data.room.official_channel_uid"                | 官方频道用户ID                   |
| orientation                   | unsigned tinyint  |      |     |         |       | "$.data.room.orientation"                         | 直播间方向                       |
| os_type                       | unsigned tinyint  |      |     |         |       | "$.data.room.os_type"                             | 操作系统类型                     |
| owner_device_id               | varchar(200)      |      |     | 0       |       | "$.data.room.owner.owner_device_id"               | 主播设备ID                      |
| owner_open_id                 | varchar(200)      |      |     | 0       |       | "$.data.room.owner.owner_open_id"                 | 主播OpenID                      | 
| owner_user_id                 | varchar(200)      |      |     |         |       | "$.data.room.owner_user_id"                       | 账号作者ID                      |
| start_time                    | timestamp         |      |     | NULL    |       | "$.data.room.start_time"                          | 开始时间                         | 
| room_layout                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_layout"                         | 直播间布局                        |
| room_tag                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_tag"                            | 直播间标签                        |
| scroll_config                 | text              | YES  |     |         |       | "$.data.room.scroll_config"                       | 滚动配置                          |
| search_id                     | varchar(200)      |      |     |         |       | "$.data.room.search_id"                           | 直播间搜索ID                     |
| sell_goods                    | bool              |      |     |         |       | "$.data.room.sell_goods"                          | 卖货                             |
| share_msg_style               | unsigned tinyint  |      |     |         |       | "$.data.room.share_msg_style"                     | 分享消息样式                      |
| share_url                     | text              |      |     |         |       | "$.data.room.share_url"                           | 直播间分享链接                    |
| title                         | tinytext          |      |     |         |       | "$.data.room.title"                               | 直播间标题                       |
| title_recommend               | bool              |      |     |         |       | "$.data.room.title_recommend"                     | 是否推荐标题                     |
| toutiao_cover_recommend_level | unsigned tinyint  |      |     |         |       | "$.data.room.toutiao_cover_recommend_level"       | 头条封面推荐等级                 |
| toutiao_title_recommend_level | unsigned tinyint  |      |     |         |       | "$.data.room.toutiao_title_recommend_level"       | 头条标题推荐等级                 |
| use_filter                    | bool              |      |     |         |       | "$.data.room.use_filter"                          | 是否使用滤镜                     |
| user_count                    | unsigned int      |      |     |         |       | "$.data.room.user_count"                          | 用户数量                         |
| vertical_cover_uri            | text              |      |     |         |       | "$.data.room.vertical_cover_uri"                  | 竖屏封面URI                      |
| vid                           | varchar(200)      |      |     |         |       | "$.data.room.vid"                                 | 视频ID                          |
| video_feed_tag                | tinytext          |      |     |         |       | "$.data.room.video_feed_tag"                      | 视频Feed标签                     |
| visibility_range              | unsigned tinyint  |      |     |         |       | "$.data.room.visibility_range"                    | 可见范围：X-公开 X-私密 X-好友可见 |
| vs_main_replay_id             | varchar(200)      |      |     |         |       | "$.data.room.vs_main_replay_id"                   | VS主回放ID                       |
| wait_copy                     | tinytext          |      |     |         |       | "$.data.room.wait_copy"                           | 等待复制                         |
| webcast_sdk_version           | varchar(20)       |      |     |         |       | "$.data.room.webcast_sdk_version"                 | 直播间SDK版本                     |
+-------------------------------+-------------------+------+-----+---------+-------+---------------------------------------------------+----------------------------------+
```

4-16. 直播间短接触区域配置 - room_short_touch_area_config
```shell
##
## data.room.short_touch_area_config
##
+---------------------+--------------+------+-----+---------+-------+------------------+-----------------------+
| Field               | Type         | Null | Key | Default | Extra | Topology         | Comment               |
+---------------------+--------------+------+-----+---------+-------+------------------+-----------------------+
| now                 | timestamp    | YES  |     |         |       | "$.extra.now"    | 当前时间戳             |
| platform            | varchar(20)  |      |     | NULL    |       |           -      | 平台                  | 
| room_id             | varchar(200) |      |     |         |       | "$.data.room.id" | 直播间ID              | 
| forbidden_types_map | json         | NULL |     |         |       |                  | 禁止类型映射表         |
+---------------------+--------------+------+-----+---------+-------+------------------+-----------------------+
```

4-16-1. 直播间短接触区域配置元素 - room_short_touch_area_config_element
```shell
##
## data.room.short_touch_area_config.elements
##
+---------------+------------------+------+-----+---------+-------+-------------------------------------------------------------+-----------------------+
| Field         | Type             | Null | Key | Default | Extra | Topology                                                    | Comment               |
+---------------+------------------+------+-----+---------+-------+-------------------------------------------------------------+-----------------------+
| now           | timestamp        | YES  |     |         |       | "$.extra.now"                                               | 当前时间戳             |
| platform      | varchar(20)      |      |     | NULL    |       |           -                                                 | 平台                  | 
| room_id       | varchar(200)     |      |     |         |       | "$.data.room.id"                                            | 直播间ID              | 
| element_index | unsigned tinyint | NO   |     |         |       |           -                                                 | 短触摸区域配置元素     |
| priority      | unsigned tinyint |      |     |         |       | "$.data.room.short_touch_area_config.elements.'x'.priority" | 优先级                |
| type          | unsigned tinyint |      |     |         |       | "$.data.room.short_touch_area_config.elements.'x'.type"     | 类型                  |
+---------------+------------------+------+-----+---------+-------+-------------------------------------------------------------+-----------------------+
```

4-16-2. 直播间短接触区域配置策略特性白名单 - room_short_touch_area_config_strategy_feat_whitelist
```shell
##
## data.room.short_touch_area_config.strategy_feat_whitelist
##
+-----------------+------------------+------+-----+---------+-------+------------------+-----------------------+
| Field           | Type             | Null | Key | Default | Extra | Topology         | Comment               |
+-----------------+------------------+------+-----+---------+-------+------------------+-----------------------+
| now             | timestamp        | YES  |     |         |       | "$.extra.now"    | 当前时间戳             |
| platform        | varchar(20)      |      |     | NULL    |       |           -      | 平台                  | 
| room_id         | varchar(200)     |      |     |         |       | "$.data.room.id" | 直播间ID              | 
| whitelist_index | unsigned tinyint |      |     |         |       |           -      | 白名单索引             | 
| whitelist_tag   | tinytext         |      |     | NULL    |       |           -      | 白名单标签             | 
+-----------------+------------------+------+-----+---------+-------+------------------+-----------------------+
```

4-16-3. 直播间临时状态条件映射 - room_temp_state_condition_map
```shell
##
## data.room.short_touch_area_config.temp_state_condition_map
##
+---------------+------------------+------+-----+---------+-------+---------------------------------------------------------------------------------------+------------+
| Field         | Type             | Null | Key | Default | Extra | Topology                                                                              | Comment    |
+---------------+------------------+------+-----+---------+-------+---------------------------------------------------------------------------------------+------------+
| now           | timestamp        | YES  |     |         |       | "$.extra.now"                                                                         | 当前时间戳  |
| platform      | varchar(20)      |      |     | NULL    |       |           -                                                                           | 平台       | 
| room_id       | varchar(200)     |      |     |         |       | "$.data.room.id"                                                                      | 直播间ID   |
| map_index     | unsigned tinyint |      |     |         |       |           -                                                                           | 映射索引   |
| minimum_gap   | unsigned int     |      |     |         |       | "$.data.room.short_touch_area_config.temp_state_condition_map.'x'.minimum_gap"        | 最小间隔   |
| priority      | unsigned tinyint |      |     |         |       | "$.data.room.short_touch_area_config.temp_state_condition_map.'x'.type.priority"      | 优先级     |
| strategy_type | unsigned tinyint |      |     |         |       | "$.data.room.short_touch_area_config.temp_state_condition_map.'x'.type.strategy_type" | 策略类型   |
+---------------+------------------+------+-----+---------+-------+---------------------------------------------------------------------------------------+------------+
```

4-16-3-1. 直播间临时状态全局条件忽略类型 - room_temp_state_global_condition_ignore_strategy_type
```shell
##
## data.room.short_touch_area_config.temp_state_global_condition.ignore_strategy_types
##
+---------------+------------------+------+-----+---------+-------+-----------------------------------------------------------------------------------------+-------------+
| Field         | Type             | Null | Key | Default | Extra | Topology                                                                                | Comment     |
+---------------+------------------+------+-----+---------+-------+-----------------------------------------------------------------------------------------+-------------+
| now           | timestamp        | YES  |     |         |       | "$.extra.now"                                                                           | 当前时间戳   |
| platform      | varchar(20)      |      |     | NULL    |       |           -                                                                             | 平台        | 
| room_id       | varchar(200)     |      |     |         |       | "$.data.room.id"                                                                        | 直播间ID    |
| strategy_type | unsigned tinyint |      |     |         |       | "$.data.room.short_touch_area_config.temp_state_global_condition.ignore_strategy_types" | 忽略策略类型 |
+---------------+------------------+------+-----+---------+-------+-----------------------------------------------------------------------------------------+-------------+
```

4-16-4. 直播间临时状态全局条件 - room_temp_state_global_condition
```shell
##
## data.room.short_touch_area_config.temp_state_global_condition
##
+--------------+------------------+------+-----+---------+-------+--------------------------------------------------------------------------------+------------+
| Field        | Type             | Null | Key | Default | Extra | Topology                                                                       | Comment    |
+--------------+------------------+------+-----+---------+-------+--------------------------------------------------------------------------------+------------+
| now          | timestamp        | YES  |     |         |       | "$.extra.now"                                                                  | 当前时间戳 |
| platform     | varchar(20)      |      |     | NULL    |       |           -                                                                    | 平台       | 
| room_id      | varchar(200)     |      |     |         |       | "$.data.room.id"                                                               | 直播间ID   |
| allow_count  | unsigned tinyint |      |     |         |       | "$.data.room.short_touch_area_config.temp_state_global_condition.allow_count"  | 允许总数   |
| duration_gap | unsigned int     |      |     |         |       | "$.data.room.short_touch_area_config.temp_state_global_condition.duration_gap" | 持续间隔   |
+--------------+------------------+------+-----+---------+-------+--------------------------------------------------------------------------------+------------+
```

4-16-5. room_temp_state_strategy
```shell
##
## data.room.short_touch_area_config.temp_state_strategy
##
+-------------------+------------------+------+-----+---------+-------+-------------------------------------------------------------------------------------+------------+
| Field             | Type             | Null | Key | Default | Extra | Topology                                                                            | Comment    |
+-------------------+------------------+------+-----+---------+-------+-------------------------------------------------------------------------------------+------------+
| now               | timestamp        | NO   | PRI |         |       | "$.extra.now"                                                                       | 当前时间戳 |
| platform          | varchar(20)      | NO   | PRI |         |       |           -                                                                         | 平台       | 
| room_id           | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                                                                    | 直播间ID   |
| short_touch_type  | unsigned int     |      |     | NULL    |       | "$.data.room.short_touch_area_config.temp_state_global_condition.short_touch_type"  | 允许总数   |
+-------------------+------------------+------+-----+---------+-------+-------------------------------------------------------------------------------------+------------+
```

4-16-5-1. room_temp_state_strategy_map
```shell
##
## data.room.short_touch_area_config.temp_state_strategy.strategy_map
##
+-------------------+------------------+------+-----+---------+-------+--------------------------------------------------------------------------------------------+------------+
| Field             | Type             | Null | Key | Default | Extra | Topology                                                                                   | Comment    |
+-------------------+------------------+------+-----+---------+-------+--------------------------------------------------------------------------------------------+------------+
| now               | timestamp        | NO   | PRI |         |       | "$.extra.now"                                                                              | 当前时间戳 |
| platform          | varchar(20)      | NO   | PRI |         |       |           -                                                                                | 平      | 
| room_id           | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                                                                           | 直播间ID   |
| short_touch_type  | unsigned int     |      |     | NULL    |       | "$.data.room.short_touch_area_config.temp_state_strategy.'x'.short_touch_type"             | 允许总数   |
| duration          | unsigned int     |      |     | NULL    |       | "$.data.room.short_touch_area_config.temp_state_strategy.strategy_map.'x'.duration"        | 持续时间   |
| strategy_method   | varchar(100)     |      |     | NULL    |       | "$.data.room.short_touch_area_config.temp_state_strategy.strategy_map.'x'.strategy_method" | 策略方法   |
| priority          | unsigned tinyint |      |     | NULL    |       | "$.data.room.short_touch_area_config.temp_state_strategy.strategy_map.'x'.priority"        | 优先级     |
| strategy_type     | varchar(20)      |      |     | NULL    |       | "$.data.room.short_touch_area_config.temp_state_strategy.strategy_map.'x'.strategy_type"   | 策略类型   |
+-------------------+------------------+------+-----+---------+-------+--------------------------------------------------------------------------------------------+------------+
```

5. 直播间记录表(动态信息) - room_record
```shell
##
## room
##
+-------------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------+---------------------+
| Field                               | Type              | Null | Key | Default | Extra | Topology                                               | Comment             |
+-------------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------+---------------------+
| now                                 | timestamp         | YES  |     |         |       | "$.extra.now"                                          | 当前时间戳           | 
| platform                            | varchar(20)       |      |     | NULL    |       |           -                                            | 平台                 | 
| id                                  | varchar(200)      |      |     |         |       | "$.data.room.id"                                       | 直播间ID             | 
| rank                                | unsigned smallint |      |     |         |       | "$.data.room.AnchorABMap"                              | 排名/等级            |
| silence_flag                        | unsigned tinyint  |      |     |         |       | "$.data.room.living_room_attrs.silence_flag"           | 直播间静音状态       | 
| view_stats_display_long             | tinytext          |      |     |         |       | "$.data.room.room_view_stats.display_long"             | 直播间观看人数       | 
| view_stats_display_long_anchor      | tinytext          |      |     |         |       | "$.data.room.room_view_stats.display_long_anchor"      | 主播观看人数         | 
| view_stats_display_middle           | tinytext          |      |     |         |       | "$.data.room.room_view_stats.display_middle"           | 直播间观看人数（中）  |
| view_stats_display_middle_anchor    | tinytext          |      |     |         |       | "$.data.room.room_view_stats.display_middle_anchor"    | 主播观看人数（中）    |
| view_stats_display_short            | tinytext          |      |     |         |       | "$.data.room.room_view_stats.display_short"            | 直播间观看人数（短）  |
| view_stats_display_short_anchor     | tinytext          |      |     |         |       | "$.data.room.room_view_stats.display_short_anchor"     | 主播观看人数（短）    |
| view_stats_display_type             | unsigned tinyint  |      |     |         |       | "$.data.room.room_view_stats.display_type"             | 直播间观看人数显示类型 |
| view_stats_display_value            | unsigned int      |      |     |         |       | "$.data.room.room_view_stats.display_value"            | 直播间观看人数        |
| view_stats_display_version          | varchar(20)       |      |     |         |       | "$.data.room.room_view_stats.display_version"          | 直播间观看人数显示版本 |
| view_stats_incremental              | bool              |      |     |         |       | "$.data.room.room_view_stats.incremental"              | 是否增量更新          |
| view_stats_is_hidden                | bool              |      |     |         |       | "$.data.room.room_view_stats.is_hidden"                | 是否隐藏状态          |
| user_share_text                     | text              |      |     |         |       | "$.data.Froom.user_share_text"                         | 用户分享文本          |
| screen_capture_sharing_title        | tinytext          |      |     |         |       | "$.data.room.screen_capture_sharing_title"             | 屏幕截图分享标题       |
| short_title                         | tinytext          |      |     |         |       | "$.data.room.short_title"                              | 屏幕直播间短          |
| lottery_finish_time                 | timestamp         |      |     |         |       | "$.data.room.lottery_finish_time"                      | 抽奖结束时间          |
| luckymoney_num                      | unsigned int      |      |     |         |       | "$.data.room.luckymoney_num"                           | 幸运红包数量          |
| mosaic_status                       | unsigned int      |      |     |         |       | "$.data.room.mosaic_status"                            | 马赛克状态            |
| mosaic_tip                          | tinytext          |      |     |         |       | "$.data.room.mosaic_tip"                               | 马赛克提示            |
| popularity                          | unsigned bigint   |      |     |         |       | "$.data.room.popularity"                               | 人气                 |
| popularity_str                      | varchar(20)       |      |     |         |       | "$.data.room.popularity_str"                           | 人气字符串            |
| pre_enter_time                      | timestamp         |      |     |         |       | "$.data.room.pre_enter_time"                           | 预进入时间            |
| preview_copy                        | tinytext          |      |     |         |       | "$.data.room.preview_copy"                             | 预览复制文本          |
| preview_flow_tag                    | unsigned tinyint  |      |     |         |       | "$.data.room.preview_flow_tag"                         | 预览流量标签          |
| private_info                        | text              |      |     |         |       | "$.data.room.private_info"                             | 私有信息              |
| ranklist_audience_type              | unsigned tinyint  |      |     |         |       | "$.data.room.ranklist_audience_type"                   | 排行榜观众类型        |
| real_distance                       | varchar(100)      |      |     |         |       | "$.data.room.real_distance"                            | 实际距离              |
| redpacket_audience_auth             | unsigned tinyint  |      |     |         |       | "$.data.room.redpacket_audience_auth"                  | 红包观众认证          |
| relation_tag                        | tinytext          |      |     |         |       | "$.data.room.relation_tag"                             | 关系标签              |
| replay                              | bool              |      |     |         |       | "$.data.room.replay"                                   | 是否为回放            |
| replay_location                     | unsigned tinyint  |      |     |         |       | "$.data.room.replay_location"                          | 回放位置              |
| room_audit_status                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_audit_status"                        | 直播间审核状态        |
| room_create_ab_param                | text              |      |     |         |       | "$.data.room.room_create_ab_param"                     | 直播间创建AB参数      |
| sofa_layout                         | unsigned tinyint  |      |     |         |       | "$.data.room.sofa_layout"                              | 沙发布局              |
| stamps                              | tinytext          |      |     |         |       | "$.data.room.stamps"                                   | 印章                 |
| comment_count                       | unsigned bigint   |      |     |         |       | "$.data.room.stats.comment_count"                      | 评论数量              |
| digg_count                          | unsigned bigint   |      |     |         |       | "$.data.room.stats.digg_count"                         | 点赞数量              |
| dou_plus_promotion                  | tinytext          |      |     |         |       | "$.data.room.stats.dou_plus_promotion"                 | DouPlus推广          |
| enter_count                         | unsigned bigint   |      |     |         |       | "$.data.room.stats.enter_count"                        | 进入数量              |
| fan_ticket                          | unsigned bigint   |      |     |         |       | "$.data.room.stats.fan_ticket"                         | 粉丝票数量            |
| follow_count                        | unsigned bigint   |      |     |         |       | "$.data.room.stats.follow_count"                       | 关注数量              |
| gift_uv_count                       | unsigned int      |      |     |         |       | "$.data.room.stats.gift_uv_count"                      | 礼物UV数量            |
| like_count                          | unsigned int      |      |     |         |       | "$.data.room.stats.like_count"                         | 喜欢数量              |
| money                               | unsigned int      |      |     |         |       | "$.data.room.stats.money"                              | 金额                  |
| total_user                          | unsigned int      |      |     |         |       | "$.data.room.stats.total_user"                         | 用户数量              |
| total_user_desp                     | text              |      |     |         |       | "$.data.room.stats.total_user_desp"                    | 总用户描述            |
| total_user_str                      | varchar(100)      |      |     |         |       | "$.data.room.stats.total_user_str"                     | 总用户描述            |
| up_right_stats_str                  | varchar(100)      |      |     |         |       | "$.data.room.stats.up_right_stats_str"                 | 右上角统计字符串      |
| up_right_stats_str_complete         | tinytext          |      |     |         |       | "$.data.room.stats.up_right_stats_str_complete"        | 完整的右上角统计字符串 |
| user_count_composition_city         | unsigned tinyint  |      |     |         |       | "$.data.room.stats.user_count_composition.city"        | 城市                 |
| user_count_composition_my_follow    | unsigned bigint   |      |     |         |       | "$.data.room.stats.user_count_composition.my_follow"   | 我的关注              |
| user_count_composition_other        | unsigned bigint   |      |     |         |       | "$.data.room.stats.user_count_composition.other"       | 其他                 |
| user_count_composition_video_detail | unsigned bigint   |      |     |         |       | "$.data.room.stats.user_count_composition.video_detail"| 视频详情              |
| user_count_str                      | unsigned bigint   |      |     |         |       | "$.data.room.stats.user_count_str"                     | 用户数量字符串        |
| watermelon                          | unsigned bigint   |      |     |         |       | "$.data.room.stats.watermelon"                         | 西瓜                 |
| welfare_donation_amount             | unsigned bigint   |      |     |         |       | "$.data.room.stats.welfare_donation_amount"            | 福利捐赠金额          |
| status                              | unsigned tinyint  |      |     | 0       |       | "$.data.room.status"                                   | 直播状态             | 
| stream_close_time                   | timestamp         |      |     |         |       | "$.data.room.stream_close_time"                        | 直播间流关闭时间戳     |
| stream_id                           | varchar(200)      |      |     |         |       | "$.data.room.stream_id"                                | 直播间流ID            |
| stream_provider                     | unsigned tinyint  |      |     |         |       | "$.data.room.stream_provider"                          | 直播间流提供者         |
| sun_daily_icon_content              | text              |      |     |         |       | "$.data.room.sun_daily_icon_content"                   | 日常图标内容          |
| challenge_info                      | tinytext          |      |     |         |       | "$.data.room.challenge_info"                           | 挑战信息              |
| danmaku_detail                      | unsigned int      |      |     |         |       | "$.data.room.danmaku_detail"                           | 弹幕详情              |
| hot_sentence_info                   | text              |      |     |         |       | "$.data.room.hot_sentence_info"                        | 热门语句信息          |
| last_ping_time                      | timestamp         |      |     |         |       | "$.data.room.last_ping_time"                           | 最后ping时间          |
| like_count                          | unsigned bigint   |      |     |         |       | "$.data.room.like_count"                               | 点赞数量              |
| linker_map                          | json              |      |     |         |       | "$.data.room.linker_map"                               | 点连接器映射          |
| web_count                           | unsigned bigint   |      |     |         |       | "$.data.room.web_count"                                | 网页观看人数          |
| webcast_comment_tcs                 | unsigned int      |      |     |         |       | "$.data.room.webcast_comment_tcs"                      | 直播间评论TCs         |
| with_aggregate_column               | bool              |      |     |         |       | "$.data.room.with_aggregate_column"                    | 是否有聚合栏目        |
| with_draw_something                 | bool              |      |     |         |       | "$.data.room.with_draw_something"                      | 是否有抽奖            |
| with_ktv                            | bool              |      |     |         |       | "$.data.room.with_ktv"                                 | 是否有KTV             |
| with_linkmic                        | bool              |      |     |         |       | "$.data.room.with_linkmic"                             | 是否有连麦            |
+-------------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------+----------------------+
```

4-4. 直播间装饰清单 - room_deco
```shell
##
## $.data.room.deco_list
##
+--------------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------+---------------------+
| Field                                | Type              | Null | Key | Default | Extra | Topology                                                           | Comment             |
+--------------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------+---------------------+
| start_time                           | timestamp         | YES  |     |         |       | "$.extra.now"                                                      | 当前时间戳           | 
| platform                             | varchar(20)       |      |     | NULL    |       |           -                                                        | 平台                 | 
| room_id                              | varchar(200)      |      |     |         |       | "$.data.room.id"                                                   | 直播间ID             |
| deco_index                           | unsigned tinyint  |      |     |         |       |           -                                                        | 装饰索引号            |  
| audit_text_color                     | varchar(7)        |      |     |         |       | "$.data.room.deco_list.[x].audit_text_color"                       | 审核文本颜色          | 
| content                              | tinytext          |      |     |         |       | "$.data.room.deco_list.[x].content"                                | 内容                 | 
| h                                    | unsigned int      |      |     |         |       | "$.data.room.deco_list.[x].h"                                      | 高度                 | 
| id                                   | unsigned int      |      |     |         |       | "$.data.room.deco_list.[x].id"                                     | ID                   | 
| kind                                 | unsigned tinyint  |      |     |         |       | "$.data.room.deco_list.[x].kind"                                   | 种类                 | 
| max_length                           | unsigned tinyint  |      |     |         |       | "$.data.room.deco_list.[x].max_length"                             | 最大长度             | 
| status                               | unsigned tinyint  |      |     |         |       | "$.data.room.deco_list.[x].status"                                 | 状态                 |
| sub_type                             | unsigned tinyint  |      |     |         |       | "$.data.room.deco_list.[x].sub_type"                               | 子类型               |
| text_color                           | varchar(7)        |      |     |         |       | "$.data.room.deco_list.[x].text_color"                             | 文本颜色             |
| text_image_adjustable_end_position   | unsigned int      |      |     |         |       | "$.data.room.deco_list.[x].text_image_adjustable_end_position"     | 可调整文本图片结束位置 |
| text_image_adjustable_start_position | unsigned int      |      |     |         |       | "$.data.room.deco_list.[x].text_image_adjustable_start_position"   | 可调整文本图片开始位置 |
| text_size                            | unsigned int      |      |     |         |       | "$.data.room.deco_list.[x].text_size"                              | 文本大小              |
| type                                 | unsigned tinyint  |      |     |         |       | "$.data.room.deco_list.[x].type"                                   | 类型                 |
| w                                    | unsigned int      |      |     |         |       | "$.data.room.deco_list.[x].w"                                      |                      |
| x                                    | unsigned int      |      |     |         |       | "$.data.room.deco_list.[x].x"                                      |                      |
| y                                    | unsigned int      |      |     |         |       | "$.data.room.deco_list.[x].y"                                      |                      |
+--------------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------+----------------------+

##
## $.data.room.deco_list.[x].input_rect
##
+------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------+---------------------+
| Field            | Type              | Null | Key | Default | Extra | Topology                                                           | Comment             |
+------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------+---------------------+
| start_time       | timestamp         |  NO  |     |         |       | "$.extra.now"                                                      | 当前时间戳           | 
| platform         | varchar(20)       |  NO  |     |         |       |           -                                                        | 平台                 | 
| room_id          | varchar(200)      |  NO  |     |         |       | "$.data.room.id"                                                   | 直播间ID             |
| deco_index       | unsigned bigint   |      |     |         |       |           -                                                        | 装饰索引号            |
| input_rect_index | unsigned bigint   |  NO  | PRI |         |       | -                                                                  | 索引                 |
| input_rect       | unsigned int      |      |     | NULL    |       | "$.data.room.deco_list.[x].reservation.input_rect"                 |                      |
+------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------+----------------------+

##
## $.data.room.deco_list.[x].reservation
##
+------------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+---------------+
| Field                  | Type              | Null | Key | Default | Extra | Topology                                                 | Comment       |
+------------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+---------------+
| start_time             | timestamp         |  NO  |     |         |       | "$.extra.now"                                            | 当前时间戳     | 
| platform               | varchar(20)       |  NO  |     | NULL    |       |           -                                              | 平台           | 
| room_id                | varchar(200)      |  NO  |     |         |       | "$.data.room.id"                                         | 直播间ID       |
| deco_index             | unsigned bigint   |      |     |         |       |           -                                              | 装饰索引号      |
| anchor_id              | varchar(200)      |      |     |         |       | "$.data.room.deco_list.[x].reservation.anchor_id"        | 主播ID         | 
| anchor_open_id         | varchar(200)      |      |     |         |       | "$.data.room.deco_list.[x].reservation.anchor_open_id"   | 主播开放ID     | 
| appointment_id         | varchar(200)      |      |     |         |       | "$.data.room.deco_list.[x].reservation.appointment_id"   | 预约ID         | 
| btn_color              | varchar(7)        |      |     |         |       | "$.data.room.deco_list.[x].reservation.btn_color"        | 按钮颜色       | 
| reservation_end_time   | timestamp         |      |     |         |       | "$.data.room.deco_list.[x].reservation.end_time"         | 结束时间       | 
| is_reserved            | bool              |      |     |         |       | "$.data.room.deco_list.[x].reservation.is_reserved"      | 是否保留       | 
| reservation_room_id    | varchar(200)      |      |     |         |       | "$.data.room.deco_list.[x].reservation.room_id"          | 直播间ID       |
| reservation_start_time | timestamp         |      |     |         |       | "$.data.room.deco_list.[x].reservation.start_time"       | 开始时间       |
+------------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+---------------+

##
## $.data.room.deco_list.[x].reservation.btn_rect
##
+----------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------+---------------------+
| Field          | Type              | Null | Key | Default | Extra | Topology                                                           | Comment             |
+----------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------+---------------------+
| start_time     | timestamp         |  NO  |     |         |       | "$.extra.now"                                                      | 当前时间戳           | 
| platform       | varchar(20)       |  NO  |     | NULL    |       |           -                                                        | 平台                 | 
| room_id        | varchar(200)      |  NO  |     |         |       | "$.data.room.id"                                                   | 直播间ID             |
| deco_index     | unsigned bigint   |      |     |         |       |           -                                                        | 装饰索引号            |
| btn_rect_index | unsigned bigint   |      |     |         |       | -                                                                  | 索引                 |
| btn_rect       | TBD               |      |     |         |       | "$.data.room.deco_list.[x].reservation.btn_rect"                   |                      |
+----------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------+----------------------+
```

4-6. 粉丝群管理员ID表 - fans_group_admin_user_id
```shell
##
## data.room.fans_group_admin_user_ids
##
+--------------------------------+-------------------+------+-----+---------+-------+-----------------------------------------+---------------------+
| Field                          | Type              | Null | Key | Default | Extra | Topology                                | Comment             |
+--------------------------------+-------------------+------+-----+---------+-------+-----------------------------------------+---------------------+
| now                            | timestamp         | YES  | PRI |         |       | "$.extra.now"                           | 当前时间戳           | 
| platform                       | varchar(20)       |      | PRI | NULL    |       |           -                             | 平台                 |
| room_id                        | varchar(200)      |      |     |         |       | "$.data.room.id"                        | 直播间ID             | 
| fans_group_admin_user_id_index | unsigned tinyint  |      |     |         |       |           -                             | 粉丝群管理员ID序号   |
| fans_group_admin_user_id       | varchar(200)      | NO   | PRI | NULL    |       | "$.data.room.fans_group_admin_user_ids" | 粉丝群管理员用户ID   |
+--------------------------------+-------------------+------+-----+---------+-------+-----------------------------------------+---------------------+
```

4-7. 粉丝群管理员公开ID表 - fans_group_admin_user_open_id
```shell
##
## data.room.fans_group_admin_user_open_ids
##
+-------------------------------------+-------------------+------+-----+---------+-------+----------------------------------------------+----------------------+
| Field                               | Type              | Null | Key | Default | Extra | Topology                                     | Comment              |
+-------------------------------------+-------------------+------+-----+---------+-------+----------------------------------------------+----------------------+
| now                                 | timestamp         | YES  | PRI |         |       | "$.extra.now"                                | 当前时间戳            | 
| platform                            | varchar(20)       |      | PRI | NULL    |       |           -                                  | 平台                  |
| room_id                             | varchar(200)      |      |     |         |       | "$.data.room.id"                             | 直播间ID              | 
| fans_group_admin_user_open_id_index | unsigned tinyint  |      |     |         |       |           -                                  | 粉丝群管理员OpenID序号 |
| fans_group_admin_user_open_id       | varchar(200)      | NO   | PRI | NULL    |       | "$.data.room.fans_group_admin_user_open_ids" | 粉丝群管理员OpenID列表 |
+-------------------------------------+-------------------+------+-----+---------+-------+----------------------------------------------+-----------------------+
```

4-5. 直播间实时回放质量 - room_realtime_playback_quality
```shell
##
## data.room.extra.realtime_playback_qualities
##
+---------------------------+-------------------+------+-----+---------+-------+-------------------------------------------------+---------------------+
| Field                     | Type              | Null | Key | Default | Extra | Topology                                        | Comment             |
+---------------------------+-------------------+------+-----+---------+-------+-------------------------------------------------+---------------------+
| now                       | timestamp         | YES  |     |         |       | "$.extra.now"                                   | 当前时间戳           | 
| platform                  | varchar(20)       |      |     | NULL    |       |           -                                     | 平台                 | 
| room_id                   | varchar(200)      |      |     |         |       | "$.data.room.id"                                | 直播间ID             | 
| realtime_playback_index   | unsigned tinyint  |      |     |         |       |           -                                     | 实时回放质量序号     |
| realtime_playback_quality | TBD               | No   |     |         |       | "$.data.room.extra.realtime_playback_qualities" | 实时回放质量         | 
+---------------------------+-------------------+------+-----+---------+-------+-------------------------------------------------+---------------------+
```

4-8. 直播间过滤关键字 - room_filter_word
```shell
##
## data.room.filter_words
##
+-------------------+-------------------+------+-----+---------+-------+----------------------------+----------------------+
| Field             | Type              | Null | Key | Default | Extra | Topology                   | Comment              |
+-------------------+-------------------+------+-----+---------+-------+----------------------------+----------------------+
| now               | timestamp         | YES  | PRI |         |       | "$.extra.now"              | 当前时间戳            | 
| platform          | varchar(20)       |      | PRI | NULL    |       |           -                | 平台                  |
| room_id           | varchar(200)      |      |     |         |       | "$.data.room.id"           | 直播间ID              |
| filter_word_index | unsigned tinyint  | NO   | PRI | NULL    |       |           -                | 过滤词序号             |
| filter_word       | TBD               | NO   | PRI | NULL    |       | "$.data.room.filter_words" | 过滤词列表             |
+-------------------+-------------------+------+-----+---------+-------+----------------------------+-----------------------+
```

4-9. 直播分发表 - room_live_distribution
```shell
##
## data.room.live_distribution
##
+-------------------+-------------------+------+-----+---------+-------+---------------------------------+---------------------+
| Field             | Type              | Null | Key | Default | Extra | Topology                        | Comment             |
+-------------------+-------------------+------+-----+---------+-------+---------------------------------+---------------------+
| now               | timestamp         | YES  |     |         |       | "$.extra.now"                   | 当前时间戳           | 
| platform          | varchar(20)       |      |     | NULL    |       |           -                     | 平台                 | 
| room_id           | varchar(200)      |      |     |         |       | "$.data.room.id"                | 直播间ID             |
| description_index | unsigned tinyint  | No   |     | 0       |       |           -                     | 描述索引号           |  
| live_distribution | TBD               | No   |     |         |       | "$.data.room.live_distribution" | 描述内容             | 
+-------------------+-------------------+------+-----+---------+-------+---------------------------------+---------------------+
```

4-10-2/12-2. 主播商业直播配置ID表 - commerce_webcast_config_id
```shell
##
## data.room.owner.commerce_webcast_config_ids
##
+----------------------------+-------------------+------+-----+---------+-------+-------------------------------------------------+---------------------+
| Field                      | Type              | Null | Key | Default | Extra | Topology                                        | Comment             |
+----------------------------+-------------------+------+-----+---------+-------+-------------------------------------------------+---------------------+
| now                        | timestamp         | YES  |     |         |       | "$.extra.now"                                   | 当前时间戳           | 
| platform                   | varchar(20)       |      |     | NULL    |       |           -                                     | 平台                 | 
| room_id                    | varchar(200)      |      |     |         |       | "$.data.room.id"                                | 直播间ID             |
| id_index                   | unsigned tinyint  | No   |     | 0       |       |           -                                     | ID索引号             |  
| commerce_webcast_config_id | varchar(200)      | No   |     |         |       | "$.data.room.owner.commerce_webcast_config_ids" | 商业直播配置ID列表    | 
+----------------------------+-------------------+------+-----+---------+-------+-------------------------------------------------+----------------------+
```

4-10-3. 粉丝俱乐部信息表 - fans_club
```shell
##
## data.room.owner.fans_club
##
+-----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------+
| Field                 | Type              | Null | Key | Default | Extra | Topology                                                 | Comment              |
+-----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------+
| now                   | timestamp         | YES  | PRI |         |       | "$.extra.now"                                            | 当前时间戳            | 
| platform              | varchar(20)       |      | PRI | NULL    |       |           -                                              | 平台                  |
| room_id               | varchar(200)      |      |     |         |       | "$.data.room.id"                                         | 直播间ID              | 
| owner_user_id         | varchar(200)      | NO   | PRI | NULL    |       | "$.data.room.owner_user_id"                              | 账号作者ID            |
| anchor_id             | varchar(200)      | NO   | PRI | NULL    |       | "$.data.room.owner.fans_club.data.anchor_id"             | 主播ID                |
| anchor_open_id        | varchar(200)      | NO   | PRI | NULL    |       | "$.data.room.owner.fans_club.data.anchor_open_id"        | 主播OpenID            |
| badge_type            | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.fans_club.data.badge_type"            | 勋章类型              |
| badge_title           | tinytext          |      |     | NULL    |       | "$.data.room.owner.fans_club.data.badge.title"           | 勋章标题              |
| club_name             | varchar(50)       |      |     | NULL    |       | "$.data.room.owner.fans_club.data.club_name"             | 俱乐部名称            |
| guard_expired_time    | timestamp         |      |     | NULL    |       | "$.data.room.owner.fans_club.data.guard_expired_time"    | 俱乐部守护过期时间     |
| level                 | unsigned smallint |      |     | NULL    |       | "$.data.room.owner.fans_club.data.level"                 | 俱乐部等级            |
| user_fans_club_status | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.fans_club.data.user_fans_club_status" | 用户粉丝俱乐部状态     |
| user_guard_status     | unsigned tinyint  |      |     | NULL    |       | "$.data.room.owner.fans_club.data.user_guard_status"     | 用户守护状态           |
| prefer_data           | json              |      |     | NULL    |       | "$.data.room.owner.fans_club.prefer_data"                | 偏好数据               |
+-----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+-----------------------+
```

4-10-3-1. 粉丝俱乐部可用礼物ID表 - fans_club_available_gift_id
```shell
##
## data.room.owner.fans_club.data.available_gift_ids
##
+----------------------+-------------------+------+-----+---------+-------+-------------------------------------------------------+----------------------+
| Field                | Type              | Null | Key | Default | Extra | Topology                                              | Comment              |
+----------------------+-------------------+------+-----+---------+-------+-------------------------------------------------------+----------------------+
| now                  | timestamp         | YES  | PRI |         |       | "$.extra.now"                                         | 当前时间戳            | 
| platform             | varchar(20)       |      | PRI | NULL    |       |           -                                           | 平台                  |
| room_id              | varchar(200)      |      |     |         |       | "$.data.room.id"                                      | 直播间ID              | 
| owner_user_id        | varchar(200)      | NO   | PRI | NULL    |       | "$.data.room.owner_user_id"                           | 账号作者ID            |
| anchor_id            | varchar(200)      | NO   | PRI | NULL    |       | "$.data.room.owner.fans_club.data.anchor_id"          | 主播ID               |
| available_gift_index | unsigned tinyint  |      |     |         |       |           -                                           | 可用礼物序号          |
| available_gift_id    | varchar(200)      |      |     | NULL    |       | "$.data.room.owner.fans_club.data.available_gift_ids" | 可用礼物ID列表        |
+----------------------+-------------------+------+-----+---------+-------+-------------------------------------------------------+----------------------+
```

4-10-3-2. 粉丝俱乐部勋章图标表 - fans_club_badge_icon
```shell
##
## data.room.owner.fans_club.data
##
+---------------+-------------------+------+-----+---------+-------+--------------------------------------------------------+----------------------+
| Field         | Type              | Null | Key | Default | Extra | Topology                                               | Comment              |
+---------------+-------------------+------+-----+---------+-------+--------------------------------------------------------+----------------------+
| now           | timestamp         | YES  | PRI |         |       | "$.extra.now"                                          | 当前时间戳            | 
| platform      | varchar(20)       |      | PRI | NULL    |       |           -                                            | 平台                  |
| room_id       | varchar(200)      |      |     |         |       | "$.data.room.id"                                       | 直播间ID              | 
| owner_user_id | varchar(200)      | NO   | PRI | NULL    |       | "$.data.room.owner_user_id"                            | 账号作者ID            |
| anchor_id     | varchar(200)      | NO   | PRI | NULL    |       | "$.data.room.owner.fans_club.data.anchor_id"           | 主播ID                |
| icon_index    | unsigned tinyint  | NO   |     | NULL    |       | "$.data.room.owner.fans_club.data.badge.icons.'0'"     | 勋章图标0             |
| icon_uri      | text              | NO   |     | NULL    |       | "$.data.room.owner.fans_club.data.badge.icons.'0'.uri" | 勋章图标URI           |
+---------------+-------------------+------+-----+---------+-------+--------------------------------------------------------+----------------------+
```

4-10-4/12-3. 媒体勋章图片表 - media_badge_image
```shell
+-------------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------+
| Field                   | Type              | Null | Key | Default | Extra | Topology                                                 | Comment              |
+-------------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------+
| now                     | timestamp         | YES  | PRI |         |       | "$.extra.now"                                            | 当前时间戳            | 
| platform                | varchar(20)       |      | PRI | NULL    |       |           -                                              | 平台                  |
| room_id                 | varchar(200)      |      |     |         |       | "$.data.room.id"                                         | 直播间ID              | 
| user_id                 | varchar(200)      | NO   | PRI | NULL    |       | "$.data.room.owner_user_id"/"$.data.user.id"             | 账号作者ID/用户ID     |
| media_badge_image_index | unsigned tinyint  | NO   |     | 0       |       |           -                                              | 索引号               |
| media_badge_image       | TBD               | NO   |     | NULL    |       | "$.data.room.owner.media_badge_image_list"               | 媒体勋章图片列表      |
+-------------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------+
```

4-10-5/12-4. 新实时图标列表 - new_real_time_icon
```shell
##
## data.room.owner.new_real_time_icons
##
+----------------------+-------------------+------+-----+---------+-------+----------------------------------------------+----------------------+
| Field                | Type              | Null | Key | Default | Extra | Topology                                     | Comment              |
+----------------------+-------------------+------+-----+---------+-------+----------------------------------------------+----------------------+
| now                  | timestamp         | YES  | PRI |         |       | "$.extra.now"                                | 当前时间戳            | 
| platform             | varchar(20)       |      | PRI | NULL    |       |           -                                  | 平台                  |
| room_id              | varchar(200)      |      |     |         |       | "$.data.room.id"                             | 直播间ID              | 
| user_id              | varchar(200)      | NO   | PRI | NULL    |       | "$.data.room.owner_user_id"/"$.data.user.id" | 账号作者ID/用户ID     |
| real_time_icon_index | unsigned tinyint  | NO   |     | 0       |       |           -                                  | 索引号               |
| new_real_time_icon   | TBD               | NO   |     | NULL    |       | "$.data.room.owner.new_real_time_icons"      | 新实时图标列表        |
+----------------------+-------------------+------+-----+---------+-------+----------------------------------------------+----------------------+
```

12. 用户表 - user
```shell
+------------------------------------------+------------------+------+-----+---------+-------+--------------------------------------------------------+--------------------------+
| Field                                    | Type             | Null | Key | Default | Extra | Topology                                               | Comment                  |
+------------------------------------------+------------------+------+-----+---------+-------+--------------------------------------------------------+--------------------------+
| id                                       | varchar(200)     |      |     |         |       | "$.data.user.id"                                       | 直播间ID                  |
| gender                                   | unsigned tinyint |      |     | 0       |       | "$.data.user.gender"                                   | 性别（0-未知，1-男，2-女）  |
| allow_be_located                         | bool             |      |     |         |       | "$.data.user.owner.allow_be_located"                   | 是否允许被定位             |
| age_range                                | unsigned tinyint |      |     | 0       |       | "$.data.user.age_range"                                | 年龄范围                   |
| adversary_authorization_info             | unsigned tinyint |      |     | 0       |       | "$.data.user.adversary_authorization_info"             | 对手授权信息               |
| adversary_user_status                    | unsigned tinyint |      |     | 0       |       | "$.data.user.adversary_user_status"                    | 对手用户状态               |
| allow_find_by_contacts                   | bool             |      |     |         |       | "$.data.user.allow_find_by_contacts"                   | 是否允许通过联系人查找      |
| allow_others_download_video              | bool             |      |     |         |       | "$.data.user.allow_others_download_video"              | 是否允许其他人下载视频       |
| allow_others_download_when_sharing_video | bool             |      |     |         |       | "$.data.user.allow_others_download_when_sharing_video" | 是否允许其他人下载分享的视频  |
| allow_share_show_profile                 | bool             |      |     |         |       | "$.data.user.allow_share_show_profile"                 | 是否允许分享展示个人资料     |
| allow_show_in_gossip                     | bool             |      |     |         |       | "$.data.user.allow_show_in_gossip"                     | 是否允许在八卦中展示         |
| allow_show_my_action                     | bool             |      |     |         |       | "$.data.user.allow_show_my_action"                     | 是否允许展示我的动态         |
| allow_strange_comment                    | bool             |      |     |         |       | "$.data.user.allow_strange_comment"                    | 是否允许陌生人评论           |
| allow_unfollower_comment                 | bool             |      |     |         |       | "$.data.user.allow_unfollower_comment"                 | 是否允许非关注者评论         |
| allow_use_linkmic                        | bool             |      |     |         |       | "$.data.user.allow_use_linkmic"                        | 是否允许使用连麦            |
| authorization_info                       | unsigned tinyint |      |     |         |       | "$.data.user.authorization_info"                       | 授权信息                   |
| bg_img_url                               | text             |      |     |         |       | "$.data.user.bg_img_url"                               | 背景图片URL                 |
| birthday                                 | timestamp        |      |     |         |       | "$.data.user.birthday"                                 | 生日时间戳                  |
| birthday_description                     | tinytext         |      |     |         |       | "$.data.user.birthday_description"                     | 生日描述                   |
| birthday_valid                           | bool             |      |     |         |       | "$.data.user.birthday_valid"                           | 生日是否有效                |
| block_status                             | unsigned tinyint |      |     |         |       | "$.data.user.block_status"                             | 屏蔽状态：0-未屏蔽 1-已屏蔽  |
| city                                     | varchar(100)     |      |     |         |       | "$.data.user.city"                                     | 城市                       |
| comment_restrict                         | unsigned tinyint |      |     |         |       | "$.data.user.comment_restrict"                         | 评论限制                    |
| constellation                            | varchar(20)      |      |     |         |       | "$.data.user.constellation"                            | 星座                       |
| consume_diamond_level                    | unsigned smallint|      |     |         |       | "$.data.user.consume_diamond_level"                    | 消费钻石等级                |
| create_time                              | timestamp        |      |     |         |       | "$.data.user.create_time"                              | 账号创建时间戳              |
| desensitized_nickname                    | varchar(50)      |      |     |         |       | "$.data.user.desensitized_nickname"                    | 脱敏昵称                   |
| disable_ichat                            | bool             |      |     |         |       | "$.data.user.disable_ichat"                            | 是否禁用iChat               |
| display_id                               | varchar(200)     |      |     |         |       | "$.data.user.display_id"                               | 显示ID                     |
| enable_ichat_img                         | unsigned tinyint |      |     |         |       | "$.data.user.enable_ichat_img"                         | 是否启用iChat图片           |
| fold_stranger_chat                       | bool             |      |     |         |       | "$.data.user.fold_stranger_chat"                       | 是否折叠陌生人聊天          |
| nickname                                 | varchar(50)      |      |     |         |       | "$.data.user.nickname"                                 | 昵称                       |
| pay_score                                | unsigned int     |      |     |         |       | "$.data.user.pay_score"                                | 支付分                     |
| pay_scores                               | unsigned int     |      |     |         |       | "$.data.user.pay_scores"                               | 支付分                     |
| need_profile_guide                       | bool             |      |     |         |       | "$.data.user.need_profile_guide"                       | 是否需要个人资料引导         |
| hotsoon_verified                         | bool             |      |     |         |       | "$.data.user.hotsoon_verified"                         | 是否Hotsoon认证             |
| hotsoon_verified_reason                  | bool             |      |     |         |       | "$.data.user.hotsoon_verified_reason"                  | Hotsoon认证原因             |
| ichat_restrict_type                      | unsigned tinyint |      |     |         |       | "$.data.user.ichat_restrict_type"                      | iChat限制类型               |
| income_share_percent                     | unsigned tinyint |      |     |         |       | "$.data.user.income_share_percent"                     | 收入分成百分比              |
| push_comment_status                      | bool             |      |     |         |       | "$.data.user.push_comment_status"                      | 是否推送评论状态             |
| push_digg                                | bool             |      |     |         |       | "$.data.user.push_digg"                                | 是否推送点赞                |
| push_follow                              | bool             |      |     |         |       | "$.data.user.push_follow"                              | 是否推送关注                |
| push_friend_action                       | bool             |      |     |         |       | "$.data.user.push_friend_action"                       | 是否推送好友操作            |
| push_ichat                               | bool             |      |     |         |       | "$.data.user.push_ichat"                               | 是否推送iChat               |
| push_status                              | bool             |      |     |         |       | "$.data.user.push_status"                              | 是否推送状态                |
| push_video_post                          | bool             |      |     |         |       | "$.data.user.push_video_post"                          | 是否推送视频发布            |
| push_video_recommend                     | bool             |      |     |         |       | "$.data.user.push_video_recommend"                     | 是否推送视频推荐            |
| remark_name                              | varchar(50)      |      |     |         |       | "$.data.user.remark_name"                              | 备注名                     |
| sec_uid                                  | varchar(200)     |      |     |         |       | "$.data.user.sec_uid"                                  | 安全用户ID                 |
| secret                                   | unsigned tinyint |      |     |         |       | "$.data.user.secret"                                   | 是否私密                    |
| share_qrcode_uri                         | text             |      |     |         |       | "$.data.user.share_qrcode_uri"                         | 分享二维码URI               |
| short_id                                 | varchar(200)     |      |     |         |       | "$.data.user.short_id"                                 | 短ID                       |
| signature                                | text             |      |     |         |       | "$.data.user.signature"                                | 个性签名                    |
| special_id                               | varchar(200)     |      |     |         |       | "$.data.user.special_id"                               | 特殊ID                     |
| status                                   | unsigned tinyint |      |     | 0       |       | "$.data.user.status"                                   | 用户状态：0-注销 1-正常     |
| telephone                                | varchar(20)      |      |     |         |       | "$.data.user.telephone"                                | 电话号码                    |
| total_recharge_diamond_count             | unsigned bigint  |      |     |         |       | "$.data.user.total_recharge_diamond_count"             | 总充值钻石数量              |
| user_canceled                            | bool             |      |     |         |       | "$.data.user.user_canceled"                            | 用户是否已取消              |
| user_open_id                             | varchar(200)     |      |     |         |       | "$.data.user.user_open_id"                             | 用户开放ID                  |
| user_role                                | unsigned tinyint |      |     |         |       | "$.data.user.user_role"                                | 用户角色                    |
| verified                                 | bool             |      |     |         |       | "$.data.user.verified"                                 | 是否认证                    |
| verified_content                         | tinytext         |      |     |         |       | "$.data.user.verified_content"                         | 认证内容                    |
| verified_mobile                          | bool             |      |     |         |       | "$.data.user.verified_mobile"                          | 是否认证手机                |
| verified_reason                          | tinytext         |      |     |         |       | "$.data.user.verified_reason"                          | 认证原因                    |
| watch_duration_month                     | unsigned tinyint |      |     |         |       | "$.data.user.watch_duration_month"                     | 观看时长（月）              |
| web_rid                                  | varchar(200)     |      |     |         |       | "$.data.user.web_rid"                                  | Web用户ID                  |
| webcast_uid                              | varchar(200)     |      |     |         |       | "$.data.user.webcast_uid"                              | Webcast用户ID              |
| with_car_management_permission           | bool             |      |     |         |       | "$.data.user.with_car_management_permission"           | 是否具有汽车管理权限         |
| with_commerce_permission                 | bool             |      |     |         |       | "$.data.user.with_commerce_permission"                 | 是否具有商业权限            |
| with_fusion_shop_entry                   | bool             |      |     |         |       | "$.data.user.with_fusion_shop_entry"                   | 是否具有融合店铺入口         |
+------------------------------------------+------------------+------+-----+---------+-------+--------------------------------------------------------+----------------------------+
```

4-10. 直播间 owner 表 - room_owner
```shell
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------+----------------------------+
| Field                                    | Type              | Null | Key | Default | Extra |Topology                                                      | Comment                    |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------+----------------------------+
| now                                      | timestamp         | YES  |     |         |       | "$.extra.now"                                                | 当前时间戳                  |
| room_id                                  | varchar(200)      |      |     |         |       | "$.data.room.id"                                             | 直播间ID                    |
| owner_user_id                            | varchar(200)      |      |     |         |       | "$.data.room.owner_user_id"                                  | 直播间主播ID                |
| adversary_authorization_info             | unsigned tinyint  |      |     | 0       |       | "$.data.room.owner.adversary_authorization_info"             | 对手授权信息                 |
| adversary_user_status                    | unsigned tinyint  |      |     | 0       |       | "$.data.room.owner.adversary_user_status"                    | 对手用户状态                 |
| age_range                                | unsigned tinyint  |      |     | 0       |       | "$.data.room.owner.age_range"                                | 年龄范围                     |
| allow_be_located                         | bool              |      |     | 0       |       | "$.data.room.owner.allow_be_located"                         | 是否允许被定位               |
| allow_find_by_contacts                   | bool              |      |     |         |       | "$.data.room.owner.allow_find_by_contacts"                   | 是否允许通过联系人查找       |
| allow_others_download_video              | bool              |      |     |         |       | "$.data.room.owner.allow_others_download_video"              | 是否允许其他人下载视频       |
| allow_others_download_when_sharing_video | bool              |      |     |         |       | "$.data.room.owner.allow_others_download_when_sharing_video" | 是否允许其他人下载分享的视频  |
| allow_share_show_profile                 | bool              |      |     |         |       | "$.data.room.owner.allow_share_show_profile"                 | 是否允许分享展示个人资料      |
| allow_show_in_gossip                     | bool              |      |     |         |       | "$.data.room.owner.allow_show_in_gossip"                     | 是否允许在八卦中展示          |
| allow_show_my_action                     | bool              |      |     |         |       | "$.data.room.owner.allow_show_my_action"                     | 是否允许展示我的动态          |
| allow_strange_comment                    | bool              |      |     |         |       | "$.data.room.owner..allow_strange_comment"                   | 是否允许陌生人评论            |
| allow_unfollower_comment                 | bool              |      |     |         |       | "$.data.room.owner..allow_unfollower_comment"                | 是否允许非关注者评论          |
| allow_use_linkmic                        | bool              |      |     |         |       | "$.data.room.owner..allow_use_linkmic"                       | 是否允许使用连麦              |
| authorization_info                       | unsigned tinyint  |      |     |         |       | "$.data.room.owner..authorization_info"                      | 授权信息                     |
| bg_img_url                               | text              |      |     |         |       | "$.data.room.owner.bg_img_url"                               | 背景图片URL                 |
| birthday                                 | timestamp         |      |     |         |       | "$.data.room.owner.birthday"                                 | 生日时间戳                  |
| birthday_description                     | tinytext          |      |     |         |       | "$.data.room.owner.birthday_description"                     | 生日描述                   |
| birthday_valid                           | bool              |      |     |         |       | "$.data.room.owner.birthday_valid"                           | 生日是否有效                |
| block_status                             | unsigned tinyint  |      |     |         |       | "$.data.room.owner.block_status"                             | 屏蔽状态：0-未屏蔽 1-已屏蔽  |
| city                                     | varchar(100)      |      |     |         |       | "$.data.room.owner.city"                                     | 城市                       |
| comment_restrict                         | unsigned tinyint  |      |     |         |       | "$.data.room.owner.comment_restrict"                         | 评论限制                    |
| constellation                            | varchar(20)       |      |     |         |       | "$.data.room.owner.constellation"                            | 星座                       |
| consume_diamond_level                    | unsigned smallint |      |     |         |       | "$.data.room.owner.consume_diamond_level"                    | 消费钻石等级                |
| create_time                              | timestamp         |      |     |         |       | "$.data.room.owner.create_time"                              | 账号创建时间戳              |
| desensitized_nickname                    | varchar(50)       |      |     |         |       | "$.data.room.owner.desensitized_nickname"                    | 脱敏昵称                   |
| disable_ichat                            | bool              |      |     |         |       | "$.data.room.owner.disable_ichat"                            | 是否禁用iChat               |
| display_id                               | varchar(200)      |      |     |         |       | "$.data.room.owner.display_id"                               | 显示ID                     |
| enable_ichat_img                         | unsigned tinyint  |      |     |         |       | "$.data.room.owner.enable_ichat_img"                         | 是否启用iChat图片           |
| exp                                      | unsigned int      |      |     |         |       | "$.data.room.owner.exp"                                      | 经验值                      |
| experience                               | unsigned int      |      |     |         |       | "$.data.room.owner.experience"                               | 经验值                      |
| fan_ticket_count                         | unsigned bigint   |      |     |         |       | "$.data.room.owner.fan_ticket_count"                         | 粉丝票数量                  |
| list_fans_group_url                      | text              |      |     |         |       | "$.data.room.owner.fans_group_info.list_fans_group_url"      | 粉丝群列表URL               |
| fold_stranger_chat                       | bool              |      |     |         |       | "$.data.room.owner.fold_stranger_chat"                       | 是否折叠陌生人聊天           |
| follow_status                            | unsigned tinyint  |      |     |         |       | "$.data.room.owner.follow_info.follow_status"                | 关注状态                    |
| follower_count                           | unsigned bigint   |      |     | 0       |       | "$.data.room.owner.follow_info.follower_count"               | 粉丝数量                    |
| follower_count_str                       | varchar(20)       |      |     | 0       |       | "$.data.room.owner.follow_info.follower_count_str"           | 粉丝数量字符串              |
| following_count                          | unsigned int      |      |     | 0       |       | "$.data.room.owner.follow_info.following_count"              | 关注数量                    |
| following_count_str                      | varchar(20)       |      |     | 0       |       | "$.data.room.owner.follow_info.following_count_str"          | 关注数量字符串               |
| invalid_follow_status                    | bool              |      |     |         |       | "$.data.room.owner.follow_info.invalid_follow_status"        | 是否为无效关注状态           |
| push_status                              | bool              |      |     |         |       | "$.data.room.owner.follow_info.push_status"                  | 是否推送状态                |
| remark_name                              | varchar(50)       |      |     |         |       | "$.data.room.owner.follow_info.remark_name"                  | 备注名                     |
| gender                                   | unsigned tinyint  |      |     | 0       |       | "$.data.room.owner.follow_info.following_count_str"          | 性别（0-未知，1-男，2-女）   |
| hotsoon_verified                         | bool              |      |     |         |       | "$.data.room.owner.hotsoon_verified"                         | 是否Hotsoon认证             |
| hotsoon_verified_reason                  | tinytext          |      |     |         |       | "$.data.room.owner.hotsoon_verified_reason"                  | Hotsoon认证原因             |
| ichat_restrict_type                      | unsigned tinyint  |      |     |         |       | "$.data.room.owner.ichat_restrict_type"                      | iChat限制类型               |
| id                                       | varchar(200)      |      |     |         |       | "$.data.room.owner.id"                                       | 直播间 owner ID             |
| income_share_percent                     | unsigned tinyint  |      |     |         |       | "$.data.room.owner.income_share_percent"                     | 收入分成百分比               |
| is_anonymous                             | bool              |      |     |         |       | "$.data.room.owner.is_anonymous"                             | 是否匿名                    |
| is_follower                              | bool              |      |     |         |       | "$.data.room.owner.is_follower"                              | 是否是粉丝                  |
| is_following                             | bool              |      |     |         |       | "$.data.room.owner.is_following"                             | 是否正在关注                |
| JAccreditAdvance                         | unsigned tinyint  |      |     | 0       |       | "$.data.room.owner.j_accredit_info.JAccreditAdvance"         | 主播认证高级                |
| JAccreditBasic                           | unsigned tinyint  |      |     | 0       |       | "$.data.room.owner.j_accredit_info.JAccreditBasic"           | 主播认证基础                |
| JAccreditContent                         | unsigned tinyint  |      |     | 0       |       | "$.data.room.owner.j_accredit_info.JAccreditContent"         | 主播认证内容                | 
| JAccreditLive                            | unsigned tinyint  |      |     | 0       |       | "$.data.room.owner.j_accredit_info.JAccreditLive"            | 主播认证直播                |
| level                                    | unsigned smallint |      |     |         |       | "$.data.room.owner.level"                                    | 用户等级                    |
| link_mic_stats                           | unsigned tinyint  |      |     |         |       | "$.data.room.owner.link_mic_stats"                           | 连麦状态                    |
| location_city                            | varchar(100)      |      |     |         |       | "$.data.room.owner.location_city"                            | 定位城市                    |
| modify_time                              | timestamp         |      |     |         |       | "$.data.room.owner.modify_time"                              | 修改时间戳                  |
| mystery_man                              | unsigned tinyint  |      |     |         |       | "$.data.room.owner.mystery_man"                              | 是否神秘人                  |
| need_profile_guide                       | bool              |      |     |         |       | "$.data.room.owner.need_profile_guide"                       | 是否需要个人资料引导         |
| nickname                                 | varchar(50)       |      |     |         |       | "$.data.room.owner.nickname"                                 | 昵称                       |
| pay_grade_banner                         | tinytext          |      |     |         |       | "$.data.room.owner.pay_grade.grade_banner"                   | 付费等级横幅                |
| pay_grade_describe                       | tinytext          |      |     |         |       | "$.data.room.owner.pay_grade.grade_describe"                 | 付费等级描述                |
| pay_grade_describe_shining               | bool              |      |     |         |       | "$.data.room.owner.pay_grade.grade_describe_shining"         | 付费等级描述闪烁             | 
| pay_grade_level                          | unsigned smallint |      |     |         |       | "$.data.room.owner.pay_grade.level"                          | 付费等级                    |
| pay_grade_name                           | varchar(50)       |      |     |         |       | "$.data.room.owner.pay_grade.name"                           | 付费等级名称                 |
| pay_grade_next_diamond                   | unsigned bigint   |      |     |         |       | "$.data.room.owner.pay_grade.next_diamond"                   | 下一级所需钻石               |
| pay_grade_next_name                      | varchar(50)       |      |     |         |       | "$.data.room.owner.pay_grade.next_name"                      | 下一级名称                   |
| pay_grade_next_privileges                | tinytext          |      |     |         |       | "$.data.room.owner.pay_grade.next_privileges"                | 下一级特权                   |
| pay_grade_now_diamond                    | unsigned bigint   |      |     |         |       | "$.data.room.owner.pay_grade.now_diamond"                    | 当前钻石                     |
| pay_diamond_bak                          | unsigned bigint   |      |     |         |       | "$.data.room.owner.pay_grade.pay_diamond_bak"                | 付费钻石备份                 |
| pay_grade_score                          | unsigned int      |      |     |         |       | "$.data.room.owner.pay_grade.score"                          | 分数                        |
| screen_chat_type                         | unsigned tinyint  |      |     |         |       | "$.data.room.owner.pay_grade.screen_chat_type"               | 屏幕聊天类型                 |
| this_grade_max_diamond                   | unsigned bigint   |      |     |         |       | "$.data.room.owner.pay_grade.this_grade_max_diamond"         | 当前等级最大钻石             |
| this_grade_min_diamond                   | unsigned bigint   |      |     |         |       | "$.data.room.owner.pay_grade.this_grade_min_diamond"         | 当前等级最小钻石             |
| total_diamond_count                      | unsigned bigint   |      |     |         |       | "$.data.room.owner.pay_grade.total_diamond_count"            | 总钻石数量                   |
| upgrade_need_consume                     | unsigned bigint   |      |     |         |       | "$.data.room.owner.pay_grade.upgrade_need_consume"           | 升级所需消费                 |
| pay_score                                | unsigned int      |      |     |         |       | "$.data.room.owner.pay_score"                                | 支付分                     |
| pay_scores                               | unsigned int      |      |     |         |       | "$.data.room.owner.pay_scores"                               | 支付分                     |
| public_area_oper_freq                    | unsigned tinyint  |      |     |         |       | "$.data.room.owner.public_area_oper_freq"                    | 公共区域操作频率             |
| push_comment_status                      | bool              |      |     |         |       | "$.data.room.owner.push_comment_status"                      | 是否推送评论状态             |
| push_digg                                | bool              |      |     |         |       | "$.data.room.owner.push_digg"                                | 是否推送点赞                |
| push_follow                              | bool              |      |     |         |       | "$.data.room.owner.push_follow"                              | 是否推送关注                |
| push_friend_action                       | bool              |      |     |         |       | "$.data.room.owner.push_friend_action"                       | 是否推送好友操作            |
| push_ichat                               | bool              |      |     |         |       | "$.data.room.owner.push_ichat"                               | 是否推送iChat               |
| push_status                              | bool              |      |     |         |       | "$.data.room.owner.push_status"                              | 推送状态                   |
| push_video_post                          | bool              |      |     |         |       | "$.data.room.owner.push_video_post"                          | 是否推送视频发布            |
| push_video_recommend                     | bool              |      |     |         |       | "$.data.room.owner.push_video_recommend"                     | 是否推送视频推荐            |
| remark_name                              | varchar(50)       |      |     |         |       | "$.data.room.owner.remark_name"                              | 备注名称                   |
| sec_uid                                  | varchar(200)      |      |     |         |       | "$.data.room.owner.sec_uid"                                  | 安全用户ID                 |
| secret                                   | unsigned tinyint  |      |     |         |       | "$.data.room.owner.secret"                                   | 是否私密                    |
| share_qrcode_uri                         | text              |      |     |         |       | "$.data.room.owner.share_qrcode_uri"                         | 分享二维码URI               |
| short_id                                 | varchar(200)      |      |     |         |       | "$.data.room.owner.short_id"                                 | 短ID                       |
| signature                                | text              |      |     |         |       | "$.data.room.owner.signature"                                | 个性签名                    |
| special_id                               | varchar(200)      |      |     |         |       | "$.data.room.owner.special_id"                               | 特殊ID                     |
| status                                   | unsigned tinyint  |      |     | 0       |       | "$.data.room.owner.status"                                   | 用户状态：0-注销 1-正常     |
| telephone                                | varchar(20)       |      |     |         |       | "$.data.room.owner.telephone"                                | 电话号码                    |
| ticket_count                             | unsigned bigint   |      |     |         |       | "$.data.room.owner.ticket_count"                             | 票数                        |
| top_vip_no                               | unsigned smallint |      |     |         |       | "$.data.room.owner.top_vip_no"                               | 顶级VIP编号                 |
| total_recharge_diamond_count             | unsigned bigint   |      |     |         |       | "$.data.room.owner.total_recharge_diamond_count"             | 总充值钻石数量               |
| user_canceled                            | bool              |      |     |         |       | "$.data.room.owner.user_canceled"                            | 用户是否已取消               |
| user_open_id                             | varchar(200)      |      |     |         |       | "$.data.room.owner.user_open_id"                             | 用户OpenID                  |
| user_role                                | unsigned tinyint  |      |     |         |       | "$.data.room.owner.user_role"                                | 用户角色                    |
| verified                                 | bool              |      |     |         |       | "$.data.room.owner.verified"                                 | 是否认证                     |
| verified_content                         | tinytext          |      |     |         |       | "$.data.room.owner.verified_content"                         | 认证内容                     |
| verified_mobile                          | bool              |      |     |         |       | "$.data.room.owner.verified_mobile"                          | 是否为认证手机号              |
| verified_reason                          | tinytext          |      |     |         |       | "$.data.room.owner.verified_reason"                          | 认证原因                      |
| watch_duration_month                     | unsigned smallint |      |     |         |       | "$.data.room.owner.watch_duration_month"                     | 观看时长（月）                |
| web_rid                                  | varchar(200)      |      |     |         |       | "$.data.room.owner.web_rid"                                  | Web RID                      |
| webcast_uid                              | varchar(200)      |      |     |         |       | "$.data.room.owner.webcast_uid"                              | 主播Webcast UID              |
| with_car_management_permission           | bool              |      |     |         |       | "$.data.room.owner.with_car_management_permission"           | 是否具有车辆管理权限          |
| with_commerce_permission                 | bool              |      |     |         |       | "$.data.room.owner.with_commerce_permission"                 | 是否具有商业权限              |
| with_fusion_shop_entry                   | bool              |      |     |         |       | "$.data.room.owner.with_fusion_shop_entry"                   | 是否具有融合店铺入口          |
+------------------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------+-----------------------------+
```

4-10-9/12-6. 直播间owner顶部粉丝 - room_owner_top_fans
```shell
##
## data.room.owner.top_fans
##
+------------+-------------------+------+-----+---------+-------+----------------------------------------------+---------------------+
| Field      | Type              | Null | Key | Default | Extra | Topology                                     | Comment             |
+------------+-------------------+------+-----+---------+-------+----------------------------------------------+---------------------+
| now        | timestamp         |      |     |         |       | "$.data.room.create_time"                    | 当前时间戳           | 
| platform   | varchar(20)       |      |     | NULL    |       |           -                                  | 平台                 | 
| room_id    | varchar(200)      |      |     |         |       | "$.data.room.id"                             | 直播间ID             | 
| user_id    | varchar(200)      | NO   | PRI | NULL    |       | "$.data.room.owner_user_id"/"$.data.user.id" | 账号作者ID/用户ID    |
| fans_index | unsigned tinyint  |      |     |         |       |           -                                  | 粉丝序号             | 
| top_fans   | TBD               |      |     |         |       | "$.data.room.top_fans"                       | 顶级粉丝             |
+------------+-------------------+------+-----+---------+-------+----------------------------------------------+---------------------+
```

4-10-7/12-5. 直播间owner实时图标 - room_owner_real_time_icon
```shell
##
## data.room.owner.real_time_icons
##
+----------------------+-------------------+------+-----+---------+-------+----------------------------------------------+----------------------+
| Field                | Type              | Null | Key | Default | Extra | Topology                                     | Comment              |
+----------------------+-------------------+------+-----+---------+-------+----------------------------------------------+----------------------+
| now                  | timestamp         | YES  | PRI |         |       | "$.extra.now"                                | 当前时间戳            | 
| platform             | varchar(20)       |      | PRI | NULL    |       |           -                                  | 平台                  |
| room_id              | varchar(200)      |      |     |         |       | "$.data.room.id"                             | 直播间ID              | 
| user_id              | varchar(200)      | NO   | PRI | NULL    |       | "$.data.room.owner_user_id"/"$.data.user.id" | 账号作者ID/用户ID     |
| real_time_icon_index | unsigned tinyint  |      |     |         |       |           -                                  | 实时图标序号          |
| real_time_icon       | TBD               |      |     |         |       | "$.data.room.owner.real_time_icons"          | 实时图标              | 
+----------------------+-------------------+------+-----+---------+-------+----------------------------------------------+----------------------+
```

4-10-6. 付费等级图标 - pay_grade_icon
```shell
##
## data.room.owner.pay_grade.grade_icon_list
##
+----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------+
| Field                | Type              | Null | Key | Default | Extra | Topology                                                 | Comment              |
+----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------+
| now                  | timestamp         | YES  | PRI |         |       | "$.extra.now"                                            | 当前时间戳            | 
| platform             | varchar(20)       |      | PRI | NULL    |       |           -                                              | 平台                  |
| room_id              | varchar(200)      |      |     |         |       | "$.data.room.id"                                         | 直播间ID              | 
| owner_user_id        | varchar(200)      | NO   | PRI | NULL    |       | "$.data.room.owner_user_id"                              | 账号作者ID            |
| pay_grade_icon_index | unsigned tinyint  | NO   |     | 0       |       |           -                                              | 索引号               |
| pay_grade_icon       | TBD               | NO   |     | 0       |       | "$.data.room.owner.pay_grade.grade_icon_list"            | 付费等级图标列表      |
+----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------+
```

4-13. 直播间认证信息 - room_auth
```shell
##
## data.room.room_auth
##
+--------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------+----------------------+
| Field                          | Type              | Null | Key | Default | Extra | Topology                                               | Comment              |
+--------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------+----------------------+
| now                            | timestamp         | YES  | PRI |         |       | "$.extra.now"                                          | 当前时间戳            | 
| platform                       | varchar(20)       |      | PRI | NULL    |       |           -                                            | 平台                  |
| room_id                        | varchar(200)      |      |     |         |       | "$.data.room.id"                                       | 直播间ID              | 
| AIClone                        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.AIClone"                        | AI克隆                | 
| AdminCommentWall               | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.AdminCommentWall"               | 管理员评论墙          | 
| AnchorAudioChat                | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.AnchorAudioChat"                | 主播音频聊天          | 
| AnchorColdMessageTiled         | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.AnchorColdMessageTiled"         | 主播冷消息平铺        | 
| AnchorHotMessageAggregated     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.AnchorHotMessageAggregated"     | 主播热消息聚合        | 
| AnchorMission                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.AnchorMission"                  | 主播任务             | 
| AudioChat                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.AudioChat"                      | 音频聊天             | 
| AudioChatTotext                | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.AudioChatTotext"                | 音频聊天转文本        | 
| Banner                         | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Banner"                         | 横幅                 | 
| BulletStyle                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.BulletStyle"                    | 弹幕样式              | 
| CanSellTicket                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.CanSellTicket"                  | 是否可以售票          | 
| CastScreen                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.CastScreen"                     | 屏幕投射             | 
| CastScreenExplicit             | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.CastScreenExplicit"             | 屏幕投射显式          | 
| Chat                           | bool              |      |     |         |       | "$.data.room.room_auth.Chat"                           | 聊天                 | 
| ChatDispatch                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatDispatch"                   | 聊天分发             | 
| ChatDynamicSlideSpeed          | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatDynamicSlideSpeed"          | 聊天动态滑动速度      | 
| ChatDynamicSlideSpeedAnchor    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatDynamicSlideSpeedAnchor"    | 主播聊天动态滑动速度   | 
| ChatGuideEmoji                 | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatGuideEmoji"                 | 聊天引导表情          |
| ChatGuideImage                 | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatGuideImage"                 | 聊天引导图片          |
| ChatIdentity                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatIdentity"                   | 聊天身份              |
| ChatMention                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatMention"                    | 聊天提及             |
| ChatMentionV2                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatMentionV2"                  | 聊天提及V2            |
| ChatOperate                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatOperate"                    | 聊天操作             |
| ChatReply                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ChatReply"                      | 聊天回复              |
| ClearEntranceOption            | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ClearEntranceOption"            | 清除入口选项          |
| Collect                        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Collect"                        | 收藏                 |
| CommentWall                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.CommentWall"                    | 评论墙               |
| CommerceCard                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.CommerceCard"                   | 商业卡片             |
| CommerceComponent              | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.CommerceComponent"              | 商业组件             |
| CommonCard                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.CommonCard"                     | 通用卡片             |
| CountType                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.CountType"                      | 计数类型             | 
| Danmaku                        | bool              |      |     |         |       | "$.data.room.room_auth.Danmaku"                        | 弹幕                 | 
| DanmakuDefault                 | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.DanmakuDefault"                 | 弹幕默认             | 
| Denounce                       | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Denounce"                       | 举报                 | 
| Digg                           | bool              |      |     |         |       | "$.data.room.room_auth.Digg"                           | 点赞                 | 
| Dislike                        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Dislike"                        | 不喜欢               | 
| DonationSticker                | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.DonationSticker"                | 捐赠贴纸             | 
| DouPlus                        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.DouPlus"                        | DouPlus             | 
| DouPlusPopularityGem           | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.DouPlusPopularityGem"           | DouPlus人气宝石      | 
| DownloadVideo                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.DownloadVideo"                  | 下载视频             | 
| EcomFansClub                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.EcomFansClub"                   | 电商粉丝俱乐部        | 
| EmojiOutside                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.EmojiOutside"                   | 外部表情             | 
| EnhancedTouch                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.EnhancedTouch"                  | 增强触摸             | 
| EnterEffects                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.EnterEffects"                   | 进入效果             | 
| ExpandScreen                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ExpandScreen"                   | 扩展屏幕             | 
| FansClub                       | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FansClub"                       | 粉丝俱乐部           | 
| FansClubBlessing               | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FansClubBlessing"               | 粉丝俱乐部祝福        | 
| FansClubDeclaration            | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FansClubDeclaration"            | 粉丝俱乐部宣言        | 
| FansClubLetter                 | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FansClubLetter"                 | 粉丝俱乐部信件        | 
| FansClubNotice                 | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FansClubNotice"                 | 粉丝俱乐部通知        | 
| FansGroup                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FansGroup"                      | 粉丝群               | 
| FeaturedPublicScreen           | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FeaturedPublicScreen"           | 精选公共屏幕          | 
| FirstFeedHistChat              | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FirstFeedHistChat"              | 首次Feed历史聊天      | 
| FixedChat                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FixedChat"                      | 固定聊天             | 
| FrequentlyChat                 | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FrequentlyChat"                 | 常用聊天             | 
| FusionEmoji                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.FusionEmoji"                    | 融合表情             | 
| GamePointsPlaying              | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.GamePointsPlaying"              | 游戏积分玩法          | 
| Gift                           | bool              |      |     |         |       | "$.data.room.room_auth.Gift"                           | 礼物                 | 
| GiftAnchorMt                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.GiftAnchorMt"                   | 主播礼物MT           | 
| GiftVote                       | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.GiftVote"                       | 礼物投票             | 
| Highlights                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Highlights"                     | 精彩片段             | 
| HostTeam                       | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.HostTeam"                       | 主播团队             | 
| HostTeamChannel                | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.HostTeamChannel"                | 主播团队频道          | 
| HotChatTray                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.HotChatTray"                    | 热聊天托盘            | 
| HourRank                       | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.HourRank"                       | 小时排行榜            | 
| ImHeatValue                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ImHeatValue"                    | IM热值               | 
| IndustryService                | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.IndustryService"                | 行业服务             | 
| InteractionGift                | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.InteractionGift"                | 互动礼物             | 
| InteractiveComponent           | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.InteractiveComponent"           | 互动组件             | 
| ItemShare                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ItemShare"                      | 物品分享             | 
| KtvOrderSong                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.KtvOrderSong"                   | KTV点歌              | 
| Landscape                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Landscape"                      | 横屏                 | 
| LandscapeChat                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.LandscapeChat"                  | 横屏聊天             | 
| LandscapeChatDynamicSlideSpeed | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.LandscapeChatDynamicSlideSpeed" | 横屏聊天动态滑动速度   | 
| LandscapeGift                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.LandscapeGift"                  | 横屏礼物             | 
| LandscapeScreenCapture         | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.LandscapeScreenCapture"         | 横屏屏幕截图          | 
| LandscapeScreenRecording       | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.LandscapeScreenRecording"       | 横屏屏幕录制          | 
| LandscapeScreenShare           | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.LandscapeScreenShare"           | 横屏屏幕分享          | 
| Like                           | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Like"                           | 点赞                 | 
| LinkmicGuestLike               | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.LinkmicGuestLike"               | 连麦嘉宾点赞          | 
| LongPressOption                | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.LongPressOption"                | 长按选项              | 
| LongTouch                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.LongTouch"                      | 长按触摸              | 
| LuckMoney                      | bool              |      |     |         |       | "$.data.room.room_auth.LuckMoney"                      | 红包                 | 
| MarkUser                       | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MarkUser"                       | 标记用户             | 
| MediaHistoryMessage            | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MediaHistoryMessage"            | 媒体历史消息          | 
| MediaLinkmic                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MediaLinkmic"                   | 媒体连麦             | 
| MessageDispatch                | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MessageDispatch"                | 消息分发             | 
| MessageGift                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MessageGift"                    | 消息礼物             | 
| MissionCenter                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MissionCenter"                  | 任务中心             | 
| MoreAnchor                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MoreAnchor"                     | 更多主播             | 
| MoreHistChat                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MoreHistChat"                   | 更多历史聊天          | 
| MultiplierPlayback             | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MultiplierPlayback"             | 倍速播放             | 
| MyLiveEntrance                 | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.MyLiveEntrance"                 | 我的直播入口          | 
| OnlyTa                         | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.OnlyTa"                         | 仅限TA               | 
| PCPlay                         | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.PCPlay"                         | PC播放               | 
| POI                            | bool              |      |     |         |       | "$.data.room.room_auth.POI"                            | POI                  | 
| PadPlay                        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.PadPlay"                        | 平板播放             | 
| PanelECService                 | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.PanelECService"                 | 面板EC服务           | 
| PlayerRankList                 | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.PlayerRankList"                 | 播放器排行榜列表      | 
| Poster                         | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Poster"                         | 海报                 | 
| PosterCache                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.PosterCache"                    | 海报缓存             | 
| PreviewChatExpose              | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.PreviewChatExpose"              | 预览聊天曝光          | 
| PreviewHotCommentSwitch        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.PreviewHotCommentSwitch"        | 预览热评论开关        | 
| ProjectionBtn                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ProjectionBtn"                  | 投影按钮             | 
| Props                          | bool              |      |     |         |       | "$.data.room.room_auth.Props"                          | 道具                 | 
| PublicScreen                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.PublicScreen"                   | 公共屏幕             | 
| QuizGamePointsPlaying          | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.QuizGamePointsPlaying"          | 测验游戏积分玩法      | 
| RecordScreen                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.RecordScreen"                   | 录制屏幕             | 
| RoomChannel                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.RoomChannel"                    | 直播间频道            | 
| RoomChatLikeDisplay            | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.RoomChatLikeDisplay"            | 直播间聊天点赞显示    | 
| RoomChatOperatePanel           | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.RoomChatOperatePanel"           | 直播间聊天操作面板    | 
| RoomContributor                | bool              |      |     |         |       | "$.data.room.room_auth.RoomContributor"                | 直播间贡献者          | 
| RoomWidget                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.RoomWidget"                     | 直播间小部件          | 
| ScreenBottomInfo               | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ScreenBottomInfo"               | 屏幕底部信息          | 
| ScreenProjectionBarrage        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ScreenProjectionBarrage"        | 屏幕投影弹幕          | 
| Seek                           | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Seek"                           | 寻找                 | 
| Selection                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Selection"                      | 选择                 | 
| SelectionAlbum                 | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.SelectionAlbum"                 | 选择相册             | 
| Share                          | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Share"                          | 分享                 | 
| ShortTouch                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ShortTouch"                     | 短触摸               | 
| ShortTouchTempState            | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ShortTouchTempState"            | 短触摸临时状态        | 
| ShowGamePlugin                 | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ShowGamePlugin"                 | 显示游戏插件          | 
| ShowQualification              | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ShowQualification"              | 显示资格             | 
| SmallWindowDisplay             | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.SmallWindowDisplay"             | 小窗口显示            | 
| SmallWindowPlayer              | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.SmallWindowPlayer"              | 小窗口播放器          | 
| StickyMessage                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.StickyMessage"                  | 固定消息             | 
| StreamAdaptation               | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.StreamAdaptation"               | 流适应               | 
| StrokeUpDownGuide              | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.StrokeUpDownGuide"              | 上下滑动引导          | 
| SubscribeCardPackage           | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.SubscribeCardPackage"           | 订阅卡包             | 
| Teleprompter                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Teleprompter"                   | 提词器               | 
| TextGift                       | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.TextGift"                       | 文本礼物             | 
| TimedShutdown                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.TimedShutdown"                  | 定时关机             | 
| ToolbarBubble                  | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.ToolbarBubble"                  | 工具栏气泡            | 
| Topic                          | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.Topic"                          | 话题                 | 
| TypingCommentState             | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.TypingCommentState"             | 输入评论状态          | 
| UgcVSReplayDelete              | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.UgcVSReplayDelete"              | Ugc VS回放删除        | 
| UgcVsReplayVisibility          | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.UgcVsReplayVisibility"          | Ugc VS回放可见性      | 
| UpRightStatsFloatingLayer      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.UpRightStatsFloatingLayer"      | 右上角统计浮动层      | 
| UseHostInfo                    | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.UseHostInfo"                    | 使用主机信息          | 
| UserCard                       | bool              |      |     |         |       | "$.data.room.room_auth.UserCard"                       | 用户卡片              | 
| UserCorner                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.UserCorner"                     | 用户角落              | 
| VSGift                         | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VSGift"                         | VS礼物               | 
| VSRank                         | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VSRank"                         | VS排行榜             | 
| VSTopic                        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VSTopic"                        | VS话题               | 
| VerticalRank                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VerticalRank"                   | 垂直排行榜            | 
| VerticalScreenShare            | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VerticalScreenShare"            | 垂直屏幕分享          | 
| VideoAmplificationType         | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VideoAmplificationType"         | 视频放大类型          | 
| VideoShare                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VideoShare"                     | 视频分享             | 
| VsCommentBar                   | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VsCommentBar"                   | VS评论栏             | 
| VsDouPlus                      | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VsDouPlus"                      | VS DouPlus           | 
| VsExtensionEnableFollow        | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VsExtensionEnableFollow"        | VS扩展启用关注        | 
| VsFansClub                     | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VsFansClub"                     | VS粉丝俱乐部          | 
| VsWelcomeDanmaku               | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.VsWelcomeDanmaku"               | VS欢迎弹幕            | 
| WordAssociation                | unsigned tinyint  |      |     |         |       | "$.data.room.room_auth.WordAssociation"                | 词关联                | 
+--------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------+----------------------+
```

4-14. 直播间标签表 - room_tab
```shell
##
## data.room.room_tabs
##
+-----------+-------------------+------+-----+---------+-------+-------------------------+----------------------+
| Field     | Type              | Null | Key | Default | Extra | Topology                | Comment              |
+-----------+-------------------+------+-----+---------+-------+-------------------------+----------------------+
| now       | timestamp         | YES  | PRI |         |       | "$.extra.now"           | 当前时间戳            | 
| platform  | varchar(20)       |      | PRI | NULL    |       |           -             | 平台                  |
| room_id   | varchar(200)      |      |     |         |       | "$.data.room.id"        | 直播间ID              | 
| tab_index | unsigned tinyint  |      |     |         |       |           -             | tab序号               |
| room_tab  | TBD               |      |     |         |       | "$.data.room.room_tabs" | 直播间标签列表         |
+-----------+-------------------+------+-----+---------+-------+-------------------------+----------------------+
```

4-15. 直播间分享音乐ID表 - room_sharing_music_id
```shell
##
## data.room.sharing_music_id_list
##
+---------------------+------------------+------+-----+---------+-------+-------------------------------------+----------------------+
| Field               | Type             | Null | Key | Default | Extra | Topology                            | Comment              |
+---------------------+------------------+------+-----+---------+-------+-------------------------------------+----------------------+
| now                 | timestamp        | YES  | PRI |         |       | "$.extra.now"                       | 当前时间戳            | 
| platform            | varchar(20)      |      | PRI | NULL    |       |           -                         | 平台                  |
| room_id             | varchar(200)     |      |     |         |       | "$.data.room.id"                    | 直播间ID              | 
| sharing_music_index | unsigned tinyint |      |     |         |       |           -                         | 分享音乐ID序号        |
| sharing_music_id    | varchar(200)     |      |     |         |       | "$.data.room.sharing_music_id_list" | 分享音乐ID            | 
+---------------------+------------------+------+-----+---------+-------+-------------------------------------+----------------------+
```


6. 直播流数据表 - live_stream
```shell
+---------------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------------------+
| Field                     | Type              | Null | Key | Default | Extra | Topology                                                 | Comment                          | 
+---------------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------------------+
| default_resolution        | varchar(20)       |      |     |         |       | "$.data.room.stream_url.default_resolution"              | 默认分辨率                        |
| anchor_interact_profile   | unsigned tinyint  |      |     |         |       | "$.data.room.stream_url.extra.anchor_interact_profile"   | 主播互动配置文件                  |
| audience_interact_profile | unsigned tinyint  |      |     |         |       | "$.data.room.stream_url.extra.audience_interact_profile" | 观众互动配置文件                  |
| bframe_enable             | bool              |      |     |         |       | "$.data.room.stream_url.extra.bframe_enable"             | B帧启用                          |
| bitrate_adapt_strategy    | unsigned tinyint  |      |     |         |       | "$.data.room.stream_url.extra.bitrate_adapt_strategy"    | 比特率自适应策略                  |
| bytevc1_enable            | bool              |      |     |         |       | "$.data.room.stream_url.extra.bytevc1_enable"            | 比特率自适应策略                  |
| default_bitrate           | unsigned tinyint  |      |     |         |       | "$.data.room.stream_url.extra.default_bitrate"           | 默认比特率                        |
| fps                       | unsigned tinyint  |      |     |         |       | "$.data.room.stream_url.extra.fps"                       | 帧率                              |
| gop_sec                   | unsigned tinyint  |      |     |         |       | "$.data.room.stream_url.extra.gop_sec"                   | GOP秒数                          |
| h265_enable               | bool              |      |     |         |       | "$.data.room.stream_url.extra.h265_enable"               | H.265启用                        |
| hardware_encode           | bool              |      |     |         |       | "$.data.room.stream_url.extra.hardware_encode"           | 硬件编码                          |
| height                    | unsigned smallint |      |     |         |       | "$.data.room.stream_url.extra.height"                    | 高度                             |
| max_bitrate               | unsigned int      |      |     |         |       | "$.data.room.stream_url.extra.max_bitrate"               | 最大比特率                        |
| min_bitrate               | unsigned int      |      |     |         |       | "$.data.room.stream_url.extra.min_bitrate"               | 最小比特率                        |
| roi                       | bool              |      |     |         |       | "$.data.room.stream_url.extra.roi"                       | 是否启用ROI（Region of Interest） |
| sw_roi                    | bool              |      |     |         |       | "$.data.room.stream_url.extra.sw_roi"                    | 是否启用软件ROI                   |
| video_profile             | unsigned tinyint  |      |     |         |       | "$.data.room.stream_url.extra.video_profile"             | 视频配置文件                      |
| width                     | unsigned smallint |      |     |         |       | "$.data.room.stream_url.extra.width"                     | 宽度                             |
| resolution_name           | json              |      |     |         |       | "$.data.room.stream_url.resolution_name"                 | 分辨率名称                        |
| flv_pull_url              | json              |      |     |         |       | "$.data.room.stream_url.flv_pull_url"                    | 直播间FLV拉流地址                 |
| flv_pull_url_params       | json              |      |     |         |       | "$.data.room.stream_url.flv_pull_url_params"             | FLV拉流地址参数                   |
| hls_pull_url              | text              |      |     |         |       | "$.data.room.stream_url.hls_pull_url"                    | 直播间HLS拉流地址                 |
| hls_pull_url_map          | json              |      |     |         |       | "$.data.room.stream_url.hls_pull_url_map"                | 直播间HLS拉流地址映射              |
| hls_pull_url_params       | json              |      |     |         |       | "$.data.room.stream_url.hls_pull_url_params"             | HLS拉流地址参数                   |
| id                        | varchar(200)      |      |     |         |       | "$.data.room.stream_url.id"                              | 直播间流ID                        |
| provider                  | unsigned tinyint  |      |     |         |       | "$.data.room.stream_url.provider"                        | 直播间推流服务商                  |
| pull_datas                | json              |      |     |         |       | "$.data.room.stream_url.pull_datas"                      | 拉流数据                          |
| push_datas                | json              |      |     |         |       | "$.data.room.stream_url.push_datas"                      | 推流数据                          |
| push_stream_type          | unsigned tinyint  |      |     |         |       | "$.data.room.stream_url.push_stream_type"                | 推流类型                          |
| rtmp_pull_url             | text              |      |     |         |       | "$.data.room.stream_url.rtmp_pull_url"                   | 直播间RTMP拉流地址                |
| rtmp_pull_url_params      | json              |      |     |         |       | "$.data.room.stream_url.rtmp_pull_url_params"            | RTMP拉流地址参数                  |
| rtmp_push_url             | text              |      |     |         |       | "$.data.room.stream_url.rtmp_push_url"                   | 直播间RTMP推流地址                |
| rtmp_push_url_params      | text              |      |     |         |       | "$.data.room.stream_url.rtmp_push_url_params"            | RTMP推流地址参数                  |
| stream_control_type       | unsigned tinyint  |      |     |         |       | "$.data.room.stream_url.stream_control_type"             | 直播间流控制类型                  |
| stream_orientation        | unsigned tinyint  |      |     |         |       | "$.data.room.stream_url.stream_orientation"              | 直播间流方向：1-竖屏 2-横屏        |
| vr_type                   | unsigned tinyint  |      |     |         |       | "$.data.room.stream_url.vr_type"                         | VR类型                           |
+---------------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------------------+
```

6-1. 直播流候选分辨率 - stream_candidate_resolution
```shell
##
## data.room.stream_url.candidate_resolution
##
+----------------------+-------------------+------+-----+---------+-------+-----------------------------------------------+---------------------+
| Field                | Type              | Null | Key | Default | Extra | Topology                                      | Comment             |
+----------------------+-------------------+------+-----+---------+-------+-----------------------------------------------+---------------------+
| now                  | timestamp         |      |     |         |       | "$.data.room.create_time"                     | 当前时间戳           | 
| platform             | varchar(20)       |      |     | NULL    |       |           -                                   | 平台                 | 
| room_id              | varchar(200)      |      |     |         |       | "$.data.room.id"                              | 直播间ID             | 
| stream_id            | varchar(200)      |      |     |         |       | "$.data.room.stream_id"                       | 直播间流ID           |
| resolution_index     | unsigned tinyint  |      |     |         |       |           -                                   | 分辨率索引           | 
| candidate_resolution | varchar(20)       |      |     |         |       | "$.data.room.stream_url.candidate_resolution" | 候选分辨率           | 
+----------------------+-------------------+------+-----+---------+-------+-----------------------------------------------+---------------------+
```

6-2. 直播流完整推流地址 - stream_complete_push_url
```shell
##
## data.room.stream_url.complete_push_urls
##
+-------------------------+-------------------+------+-----+---------+-------+---------------------------------------------+---------------------+
| Field                   | Type              | Null | Key | Default | Extra | Topology                                    | Comment             |
+-------------------------+-------------------+------+-----+---------+-------+---------------------------------------------+---------------------+
| now                     | timestamp         |      |     |         |       | "$.data.room.create_time"                   | 当前时间戳           | 
| platform                | varchar(20)       |      |     | NULL    |       |           -                                 | 平台                 | 
| room_id                 | varchar(200)      |      |     |         |       | "$.data.room.id"                            | 直播间ID             |
| stream_id               | varchar(200)      |      |     |         |       | "$.data.room.stream_id"                     | 直播间流ID           |
| complete_push_url_index | unsigned tinyint  |      |     | NULL    |       |           -                                 | 完整推流地址序号     | 
| complete_push_url       | text              |      |     |         |       | "$.data.room.stream_url.complete_push_urls" | 完整推流地址         |
+-------------------------+-------------------+------+-----+---------+-------+---------------------------------------------+---------------------+
```

6-3. 直播核心SDK数据 - live_core_sdk_data
```shell
##
## data.room.stream_url.live_core_sdk_data
##
+----------+--------------+------+-----+---------+-------+--------------------------------------------------+---------------------+
| Field    | Type         | Null | Key | Default | Extra | Topology                                         | Comment             |
+----------+--------------+------+-----+---------+-------+--------------------------------------------------+---------------------+
| now      | timestamp    |      |     |         |       | "$.data.room.create_time"                        | 当前时间戳           | 
| platform | varchar(20)  |      |     | NULL    |       |           -                                      | 平台                 | 
| room_id  | varchar(200) |      |     |         |       | "$.data.room.id"                                 | 直播间ID             |
| size     | varchar(100) |      |     |         |       | "$.data.room.stream_url.live_core_sdk_data.size" | 流大小              |
+----------+--------------+------+-----+---------+-------+--------------------------------------------------+---------------------+
```

6-3-1. 直播核心SDK拉流数据 - live_core_sdk_pull_data
```shell
##
## data.room.stream_url.live_core_sdk_data.pull_data
##
+----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------------------------+---------------------+
| Field                | Type              | Null | Key | Default | Extra | Topology                                                                   | Comment             |
+----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------------------------+---------------------+
| now                  | timestamp         |      |     |         |       | "$.data.room.create_time"                                                  | 当前时间戳           | 
| platform             | varchar(20)       |      |     | NULL    |       |           -                                                                | 平台                 | 
| room_id              | varchar(200)      |      |     |         |       | "$.data.room.id"                                                           | 直播间ID             |
| codec                | varchar(100)      |      |     |         |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.codec"                | 编解码器             |
| compensatory_data    | text              |      |     |         |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.compensatory_data"    | 补偿数据             |
| hls_data_unencrypted | json              |      |     |         |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.hls_data_unencrypted" | HLS未加密数据        |
| kind                 | unsigned tinyint  |      |     |         |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.kind"                 | 类型                |
| stream_data          | text              |      |     |         |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.stream_data"          | 流数据内容           |
| version              | varchar(20)       |      |     |         |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.version"              | 版本                |
+----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------------------------+---------------------+
```

6-3-1-1. 直播核心SDK拉流flv数据 - live_core_sdk_pull_flv_data
```shell
##
## data.room.stream_url.live_core_sdk_data.pull_data.Flv
##
+-----------+------------------+------+-----+---------+-------+-----------------------------------------------------------+---------------------+
| Field     | Type             | Null | Key | Default | Extra | Topology                                                  | Comment             |
+-----------+------------------+------+-----+---------+-------+-----------------------------------------------------------+---------------------+
| now       | timestamp        |      |     |         |       | "$.data.room.create_time"                                 | 当前时间戳           | 
| platform  | varchar(20)      |      |     | NULL    |       |           -                                               | 平台                 | 
| room_id   | varchar(200)     |      |     |         |       | "$.data.room.id"                                          | 直播间ID             |
| Flv_index | unsigned tinyint |      |     | NULL    |       |           -                                               | Flv序号              | 
| Flv       | text             |      |     |         |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.Flv" | Flv数据             |
+-----------+------------------+------+-----+---------+-------+-----------------------------------------------------------+---------------------+
```

6-3-1-2. 直播核心SDK拉流Hls数据 - live_core_sdk_pull_hls_data
```shell
##
## data.room.stream_url.live_core_sdk_data.pull_data.Hls
##
+-----------+------------------+------+-----+---------+-------+-----------------------------------------------------------+---------------------+
| Field     | Type             | Null | Key | Default | Extra | Topology                                                  | Comment             |
+-----------+------------------+------+-----+---------+-------+-----------------------------------------------------------+---------------------+
| now       | timestamp        |      |     |         |       | "$.data.room.create_time"                                 | 当前时间戳           | 
| platform  | varchar(20)      |      |     | NULL    |       |           -                                               | 平台                 | 
| room_id   | varchar(200)     |      |     |         |       | "$.data.room.id"                                          | 直播间ID             |
| Hls_index | unsigned tinyint |      |     |         |       |           -                                               | Hls序号              | 
| Hls       | text             |      |     |         |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.Hls" | Hls数据             |
+-----------+------------------+------+-----+---------+-------+-----------------------------------------------------------+---------------------+
```

6-3-1-3. 直播核心SDK拉流数据选项 - live_core_sdk_pull_data_option
```shell
##
## data.room.stream_url.live_core_sdk_data.pull_data.options
##
+---------------+--------------+------+-----+---------+-------+----------------------------------------------------------------------------+---------------------+
| Field         | Type         | Null | Key | Default | Extra | Topology                                                                   | Comment             |
+---------------+--------------+------+-----+---------+-------+----------------------------------------------------------------------------+---------------------+
| now           | timestamp    |      |     |         |       | "$.data.room.create_time"                                                  | 当前时间戳           | 
| platform      | varchar(20)  |      |     | NULL    |       |           -                                                                | 平台                 | 
| room_id       | varchar(200) |      |     |         |       | "$.data.room.id"                                                           | 直播间ID             |
| vpass_default | bool         |      |     |         |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.vpass_default"| 视频默认通过         |
+---------------+--------------+------+-----+---------+-------+----------------------------------------------------------------------------+---------------------+
```

6-3-1-3-1. 直播核心SDK拉流质量数据 - live_core_sdk_pull_quality_data
```shell
##
## data.room.stream_url.live_core_sdk_data.pull_data.options.qualities
##
+--------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------------------------------+---------------------+
| Field              | Type              | Null | Key | Default | Extra | Topology                                                                                   | Comment             |
+--------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------------------------------+---------------------+
| now                | timestamp         |      |     |         |       | "$.data.room.create_time"                                                                  | 当前时间戳           | 
| platform           | varchar(20)       |      |     | NULL    |       |           -                                                                                | 平台                 | 
| room_id            | varchar(200)      |      |     |         |       | "$.data.room.id"                                                                           | 直播间ID             |
| quality_index      | unsigned tinyint  |      |     |         |       |           -                                                                                | 视频流质量序号        |
| additional_content | text              |      |     |         |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities.additional_content" | 附加内容             |
| disable            | unsigned tinyint  |      |     |         |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities.disable"            | 默认质量禁用标志     |
| fps                | unsigned tinyint  |      |     |         |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities.fps"                | 帧率                |
| level              | unsigned smallint |      |     |         |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities.level"              | 级别                |
| name               | varchar(50)       |      |     |         |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities.name"               | 名称                |
| resolution         | varchao(50)       |      |     |         |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities.resolution"         | 分辨率              |
| sdk_key            | varchar(100)      |      |     |         |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities.sdk_key"            | SDK密钥             |
| v_bit_rate         | unsigned tinyint  |      |     |         |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities.v_bit_rate"         | 视频比特率           |
| v_codec            | varchar(100)      |      |     |         |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.qualities.v_codec"            | 视频编解码器         |
+--------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------------------------------+---------------------+
```

6-3-1-3-2. 直播核心SDK拉流默认质量数据 - live_core_sdk_pull_default_quality_data
```shell
##
## data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality
##
+--------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------------------------------------+---------------------+
| Field              | Type              | Null | Key | Default | Extra | Topology                                                                                         | Comment             |
+--------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------------------------------------+---------------------+
| now                | timestamp         |      |     |         |       | "$.data.room.create_time"                                                                        | 当前时间戳           | 
| platform           | varchar(20)       |      |     | NULL    |       |           -                                                                                      | 平台                 | 
| room_id            | varchar(200)      |      |     |         |       | "$.data.room.id"                                                                                 | 直播间ID             |
| additional_content | text              |      |     |         |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.additional_content" | 附加内容            |
| disable            | unsigned tinyint  |      |     |         |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.disable"            | 默认质量禁用标志     |
| fps                | unsigned tinyint  |      |     |         |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.fps"                | 帧率                |
| level              | unsigned smallint |      |     |         |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.level"              | 级别                |
| name               | varchar(50)       |      |     |         |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.name"               | 名称                |
| resolution         | varchao(50)       |      |     |         |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.resolution"         | 分辨率              |
| sdk_key            | varchar(100)      |      |     |         |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.sdk_key"            | SDK密钥             |
| v_bit_rate         | unsigned tinyint  |      |     |         |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.v_bit_rate"         | 视频比特率           |
| v_codec            | varchar(100)      |      |     |         |       | "$.data.room.stream_url.live_core_sdk_data.pull_data.options.default_quality.v_codec"            | 视频编解码器         |
+--------------------+-------------------+------+-----+---------+-------+--------------------------------------------------------------------------------------------------+---------------------+
```

6-4. 直播推流地址 - stream_push_url
```shell
##
## data.room.stream_url.push_urls
##
+----------------+------------------+------+-----+---------+-------+------------------------------------+---------------------+
| Field          | Type             | Null | Key | Default | Extra | Topology                           | Comment             |
+----------------+------------------+------+-----+---------+-------+------------------------------------+---------------------+
| now            | timestamp        |      |     |         |       | "$.data.room.create_time"          | 当前时间戳           | 
| platform       | varchar(20)      |      |     | NULL    |       |           -                        | 平台                 | 
| room_id        | varchar(200)     |      |     |         |       | "$.data.room.id"                   | 直播间ID             |
| stream_id      | varchar(200)     |      |     |         |       | "$.data.room.stream_url.id"        | 直播流ID             |
| push_url_index | unsigned tinyint |      |     |         |       |           -                        | 推流地址序号         | 
| push_url       | text             |      |     |         |       | "$.data.room.stream_url.push_urls" | 推流地址             |
+----------------+------------------+------+-----+---------+-------+------------------------------------+---------------------+
```

4-10-1/12-1. 勋章图片表 - badge_image
```shell
##
## data.room.owner.badge_image_list
## data.user.badge_image_list
##
+-------------------+------------------+------+-----+---------+-------+--------------------------------------------+---------------------------+
| Field             | Type             | Null | Key | Default | Extra | Topology                                   | Comment                   |
+-------------------+------------------+------+-----+---------+-------+--------------------------------------------+---------------------------+
| badge_image_index | unsigned tinyint |      |     |         |       |                                            | 勋章图片索引               |
| version           | varchar(20)      |      |     |         |       |                                            |                           |
| uri               | text             |      |     |         |       | "$.data.room.owner.badge_image_list.x.uri" | 统一资源识别符             |
+-------------------+------------------+------+-----+---------+-------+--------------------------------------------+---------------------------+
```

11-4. 图片内容表 - picture_content
```shell
##
## data.room.owner.badge_image_list.content
##
+------------------+-------------------+------+-----+---------+-------+---------------------------------------------------------------+---------------------------+
| Field            | Type              | Null | Key | Default | Extra | Topology                                                      | Comment                   |
+------------------+-------------------+------+-----+---------+-------+---------------------------------------------------------------+---------------------------+
| uri              | unsigned tinyint  |      |     |         |       | "$.data.room.owner.badge_image_list.uri"                      | 统一资源识别符             |
| alternative_text | text              |      |     |         |       | "$.data.room.owner.badge_image_list.content.alternative_text" | 替代文本                  |
| font_color       | varchar(7)        |      |     |         |       | "$.data.room.owner.badge_image_list.content.font_color"       | 字体颜色                  |
| level            | unsigned smallint |      |     |         |       | "$.data.room.owner.badge_image_list.content.level"            | 等级                      |
| name             | varchar(50)       |      |     |         |       | "$.data.room.owner.badge_image_list.content.name"             | 名称                      |
+------------------+-------------------+------+-----+---------+-------+---------------------------------------------------------------+---------------------------+
```

11. 图片资源表 - picture
```shell
+--------------+------------------+------+-----+---------+-------+-----------------------------------------+---------------------------+
| Field        | Type             | Null | Key | Default | Extra | Topology                                | Comment                   |
+--------------+------------------+------+-----+---------+-------+-----------------------------------------+---------------------------+
| avg_color    | varchar(7)       |      |     |         |       | "$.data.room.guide_button.avg_color"    | 平均颜色                  |
| height       | unsigned int     |      |     |         |       | "$.data.room.guide_button.height"       | 高度                      |
| image_type   | unsigned tinyint |      |     |         |       | "$.data.room.guide_button.image_type"   | 图片类型                  |
| is_animated  | bool             |      |     |         |       | "$.data.room.guide_button.is_animated"  | 是否为动画                |
| open_web_url | text             |      |     |         |       | "$.data.room.guide_button.open_web_url" | 开放网页URL               |
| uri          | text             |      | PRI |         |       | "$.data.room.guide_button.uri"          | 统一资源识别符             |
| width        | unsigned int     |      |     |         |       | "$.data.room.guide_button.width"        | 宽度                      |
+--------------+------------------+------+-----+---------+-------+-----------------------------------------+---------------------------+
```

11-1. 图片弹性设置表 - picture_flex_setting
```shell
+--------------------+------------------+------+-----+---------+-------+----------------------------------------------+---------------------------+
| Field              | Type             | Null | Key | Default | Extra | Topology                                     | Comment                   |
+--------------------+------------------+------+-----+---------+-------+----------------------------------------------+---------------------------+
| uri                | text             |      |     |         |       | "$.data.room.guide_button.uri"               | 统一资源识别符             |
| flex_setting_index | unsigned tinyint |      |     |         |       | -                                            | 弹性设置序号               |
| flex_setting       | tinytext         |      |     |         |       | "$.data.room.guide_button.flex_setting_list" | 弹性设置                   |
+--------------------+------------------+------+-----+---------+-------+----------------------------------------------+---------------------------+
```

11-2. 图片文本设置表 - picture_text_setting
```shell
+--------------------+------------------+------+-----+---------+-------+----------------------------------------------+---------------------------+
| Field              | Type             | Null | Key | Default | Extra | Topology                                     | Comment                   |
+--------------------+------------------+------+-----+---------+-------+----------------------------------------------+---------------------------+
| uri                | text             |      |     |         |       | "$.data.room.guide_button.uri"               | 统一资源识别符             |
| text_setting_index | unsigned tinyint |      |     |         |       | -                                            | 文本设置序号               |
| text_setting       | tinytext         |      |     |         |       | "$.data.room.guide_button.text_setting_list" | 文本设置                   |
+--------------------+------------------+------+-----+---------+-------+----------------------------------------------+---------------------------+
```

11-3. 图片url表 - picture_url
```shell
+-----------+------------------+------+-----+---------+-------+-------------------------------------+---------------------------+
| Field     | Type             | Null | Key | Default | Extra | Topology                            | Comment                   |
+-----------+------------------+------+-----+---------+-------+-------------------------------------+---------------------------+
| uri       | text             |      |     |         |       | "$.data.room.guide_button.uri"      | 统一资源识别符             |
| url_index | unsigned tinyint |      |     |         |       | -                                   | url索引号                 |
| url       | text             |      |     |         |       | "$.data.room.guide_button.url_list" | url                       |
+-----------+------------------+------+-----+---------+-------+-------------------------------------+---------------------------+
```

图片资源拓扑表 - picture_topology
```shell
+----------+----------+------+-----+---------+-------+--------------------------------+---------------------------+
| Field    | Type     | Null | Key | Default | Extra | Topology                       | Comment                   |
+----------+----------+------+-----+---------+-------+--------------------------------+---------------------------+
| uri      | text     |      |     |         |       | "$.data.room.guide_button.uri" | 统一资源识别符             |
| topology | tinytext |      |     |         |       | -                              | 拓扑路径                   |
+----------+----------+------+-----+---------+-------+--------------------------------+---------------------------+
```

7. 直播间标签 - room_tag
```shell
##
## data.room.tags
##
+-----------+------------------+------+-----+---------+-------+---------------------------+---------------------+
| Field     | Type             | Null | Key | Default | Extra | Topology                  | Comment             |
+-----------+------------------+------+-----+---------+-------+---------------------------+---------------------+
| now       | timestamp        |      |     |         |       | "$.data.room.create_time" | 当前时间戳           | 
| platform  | varchar(20)      |      |     | NULL    |       |           -               | 平台                 | 
| room_id   | varchar(200)     |      |     |         |       | "$.data.room.id"          | 直播间ID             |
| tag_index | unsigned tinyint |      |     |         |       |           -               | 标签序号             | 
| tag       | tinytext         |      |     |         |       | "$.data.room.tags"        | 标签列表             |
+-----------+------------------+------+-----+---------+-------+---------------------------+---------------------+
```

8. 直播间顶级粉丝 - room_top_fans
```shell
##
## data.room.top_fans
##
+------------+-------------------+------+-----+---------+-------+---------------------------+---------------------+
| Field      | Type              | Null | Key | Default | Extra | Topology                  | Comment             |
+------------+-------------------+------+-----+---------+-------+---------------------------+---------------------+
| now        | timestamp         |      |     |         |       | "$.data.room.create_time" | 当前时间戳           | 
| platform   | varchar(20)       |      |     | NULL    |       |           -               | 平台                 | 
| room_id    | varchar(200)      |      |     |         |       | "$.data.room.id"          | 直播间ID             |
| fans_index | unsigned tinyint  |      |     |         |       |           -               | 粉丝序号             | 
| top_fans   | TBD               |      |     |         |       | "$.data.room.top_fans"    | 顶级粉丝             |
+------------+-------------------+------+-----+---------+-------+---------------------------+---------------------+
```

9. 直播间右上角小组件数据列表 - room_upper_right_widget_data
```shell
##
## data.room.upper_right_widget_data_list
##
+-------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------+---------------------+
| Field                         | Type              | Null | Key | Default | Extra | Topology                                   | Comment             |
+-------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------+---------------------+
| now                           | timestamp         |      |     |         |       | "$.data.room.create_time"                  | 当前时间戳           | 
| platform                      | varchar(20)       |      |     | NULL    |       |           -                                | 平台                 | 
| room_id                       | varchar(200)      |      |     |         |       | "$.data.room.id"                           | 直播间ID             |
| upper_right_widget_data_index | unsigned tinyint  |      |     |         |       |           -                                | 右上角小组件数据序号  | 
| upper_right_widget_data       | TBD               |      |     |         |       | "$.data.room.upper_right_widget_data_list" | 右上角小组件数据     |
+-------------------------------+-------------------+------+-----+---------+-------+--------------------------------------------+---------------------+
```

10. 直播间VS角色 - room_vs_role
```shell
##
## data.room.vs_roles
##
+---------------+------------------+------+-----+---------+-------+---------------------------+---------------------+
| Field         | Type             | Null | Key | Default | Extra | Topology                  | Comment             |
+---------------+------------------+------+-----+---------+-------+---------------------------+---------------------+
| now           | timestamp        |      |     |         |       | "$.data.room.create_time" | 当前时间戳           | 
| platform      | varchar(20)      |      |     | NULL    |       |           -               | 平台                 | 
| room_id       | varchar(200)     |      |     |         |       | "$.data.room.id"          | 直播间ID             |
| vs_role_index | unsigned tinyint |      |     |         |       |           -               | VS角色序号          | 
| vs_role       | TBD              |      |     |         |       | "$.data.room.vs_roles"    | VS角色              |
+---------------+------------------+------+-----+---------+-------+---------------------------+---------------------+
```

主播用户关系表 - room_owner_and_user
```shell
+-----------------------+------------------+------+-----+---------+-------+-------------------------------------------------------+------------------+
| Field                 | Type             | Null | Key | Default | Extra | Topology                                              | Comment          |
+-----------------------+------------------+------+-----+---------+-------+-------------------------------------------------------+------------------+
| now                   | timestamp        | YES  |     |         |       | "$.extra.now"                                         | 当前时间戳        |
| room_id               | varchar(200)     |      |     |         |       | "$.data.room.id"                                      | 直播间ID          |
| owner_user_id         | varchar(200)     |      |     |         |       | "$.data.room.owner_user_id"                           | 直播间主播ID      |
| user_id               | varchar(200)     |      |     |         |       | "$.data.user.id"                                      | 直播间用户ID      |
| follow_status         | unsigned tinyint |      |     |         |       | "$.data.room.owner.follow_status"                     | 关注状态          |
| invalid_follow_status | bool             |      |     |         |       | "$.data.room.owner.follow_info.invalid_follow_status" | 是否为无效关注状态 |
| remark_name           | varchar(50)      |      |     |         |       | "$.data.room.owner.follow_info.remark_name"           | 备注名称          |
| push_status           | unsigned tinyint |      |     |         |       | "$.data.room.owner.follow_info.push_status"           | 关注推送状态      |
| is_following          | bool             |      |     |         |       | "$.data.user.is_following"                            | 是否正在关注      |
+-----------------------+------------------+------+-----+---------+-------+-------------------------------------------------------+------------------+
```

直播间用户表 - room_user
```shell
+-----------------------+-------------------+------+-----+---------+-------+-------------------------------------+---------------------------+
| Field                 | Type              | Null | Key | Default | Extra | Topology                            | Comment                   |
+-----------------------+-------------------+------+-----+---------+-------+-------------------------------------+---------------------------+
| room_id               | varchar(200)      |      |     |         |       | "$.data.room.id"                    | 直播间ID                   |
| user_id               | varchar(200)      |      |     |         |       | "$.data.user.id"                    | 直播间用户ID               |
| exp                   | unsigned int      |      |     |         |       | "$.data.user.exp"                   | 经验值                     |
| experience            | unsigned int      |      |     |         |       | "$.data.user.experience"            | 经验值                     |
| fan_ticket_count      | unsigned bigint   |      |     |         |       | "$.data.user.fan_ticket_count"      | 粉丝票数量                  |
| is_follower           | bool              |      |     |         |       | "$.data.user.is_follower"           | 是否是粉丝                  |
| is_anonymous          | bool              |      |     |         |       | "$.data.user.is_anonymous"          | 是否匿名                    |
| level                 | unsigned smallint |      |     |         |       | "$.data.user.level"                 | 用户等级                    |
| link_mic_stats        | unsigned tinyint  |      |     |         |       | "$.data.user.link_mic_stats"        | 连麦状态                    |
| location_city         | varchar(100)      |      |     |         |       | "$.data.user.location_city"         | 定位城市                    |
| mystery_man           | unsigned tinyint  |      |     |         |       | "$.data.user.mystery_man"           | 是否神秘人                  |
| modify_time           | timestamp         |      |     |         |       | "$.data.user.modify_time"           | 修改时间戳                  |
| public_area_oper_freq | unsigned tinyint  |      |     |         |       | "$.data.user.public_area_oper_freq" | 公共区域操作频率             |
| ticket_count          | unsigned bigint   |      |     |         |       | "$.data.user.ticket_count"          | 票数                        |
| top_vip_no            | unsigned smallint |      |     |         |       | "$.data.user.top_vip_no"            | 顶级VIP编号                 |
+-----------------------+-------------------+------+-----+---------+-------+-------------------------------------+----------------------------+
```

4-1. 直播间管理员ID表 - room_admin_user_id
```shell
##
## data.room.admin_user_ids
##
+---------------------+-------------------+------+-----+---------+-------+------------------------------+---------------------+
| Field               | Type              | Null | Key | Default | Extra | Topology                     | Comment             |
+---------------------+-------------------+------+-----+---------+-------+------------------------------+---------------------+
| now                 | timestamp         |      |     |         |       | "$.data.room.create_time"    | 当前时间戳           |
| platform            | varchar(20)       |      |     | NULL    |       |           -                  | 平台                 |
| room_id             | varchar(200)      |      |     |         |       | "$.data.room.id"             | 直播间ID             |
| admin_user_id_index | unsigned tinyint  |      |     |         |       |           -                  | 直播间管理员ID序号    |
| admin_user_id       | varchar(200)      |      |     |         |       | "$.data.room.admin_user_ids" | 直播间管理员用户ID    | 
+---------------------+-------------------+------+-----+---------+-------+------------------------------+---------------------+
```

4-2. 直播间管理员开放ID表 - room_admin_user_open_id
```shell
##
## data.room.admin_user_open_ids
##
+-----------------------+-------------------+------+-----+---------+-------+-----------------------------------+---------------------+
| Field                 | Type              | Null | Key | Default | Extra | Topology                          | Comment             |
+-----------------------+-------------------+------+-----+---------+-------+-----------------------------------+---------------------+
| now                   | timestamp         |      | PRI |         |       | "$.extra.now"                     | 当前时间戳           | 
| platform              | varchar(20)       |      |     | NULL    |       |           -                       | 平台                 | 
| room_id               | varchar(200)      |      |     |         |       | "$.data.room.id"                  | 直播间ID             |
| admin_user_open_index | unsigned tinyint  |      |     |         |       |           -                       | 直播间管理员用户ID序号|
| admin_user_open_id    | varchar(200)      |      |     |         |       | "$.data.room.admin_user_open_ids" | 直播间管理员用户ID    | 
+-----------------------+-------------------+------+-----+---------+-------+-----------------------------------+---------------------+
```

4-3. 直播间助手标签列表 - room_assist_label
```shell
##
## data.room.assist_label_list
##
+--------------------+-------------------+------+-----+---------+-------+---------------------------------+---------------------+
| Field              | Type              | Null | Key | Default | Extra | Topology                        | Comment             |
+--------------------+-------------------+------+-----+---------+-------+---------------------------------+---------------------+
| now                | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"                   | 当前时间戳           | 
| platform           | varchar(20)       | NO   | PRI |         |       |           -                     | 平台                 | 
| room_id            | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                | 直播间ID             | 
| assist_label_index | unsigned tinyint  |      |     | NULL    |       |           -                     | 直播间辅助标签序号   |
| assist_label       | TBD               |      |     | NULL    |       | "$.data.room.assist_label_list" | 直播间辅助标签       | 
+--------------------+-------------------+------+-----+---------+-------+---------------------------------+---------------------+
```

 4-10-8. 直播间订阅信息表 - room_subscribe
```shell
##
## data.room.owner.subscribe
##
+---------------+-------------------+------+-----+---------+-------+---------------------------------------------+---------------------+
| Field         | Type              | Null | Key | Default | Extra | Topology                                    | Comment             |
+---------------+-------------------+------+-----+---------+-------+---------------------------------------------+---------------------+
| now           | timestamp         |      |     |         |       | "$.extra.now"                               | 当前时间戳           | 
| platform      | varchar(20)       |      |     | NULL    |       |           -                                 | 平台                 | 
| room_id       | varchar(200)      |      |     |         |       | "$.data.room.id"                            | 直播间ID             | 
| owner_user_id | varchar(200)      |      |     |         |       | "$.data.room.owner_user_id"                 | 直播间主播ID         |
| buy_type      | unsigned tinyint  |      |     |         |       | "$.data.room.owner.subscribe.buy_type"      | 购买类型             |
| identity_type | unsigned tinyint  |      |     |         |       | "$.data.room.owner.subscribe.identity_type" | 身份类型             |
| is_member     | bool              |      |     |         |       | "$.data.room.owner.subscribe.is_member"     | 是否为会员           |
| level         | unsigned smallint |      |     |         |       | "$.data.room.owner.subscribe.level"         | 订阅等级             |
| open          | unsigned tinyint  |      |     |         |       | "$.data.room.owner.subscribe.open"          | 是否开放             |
+---------------+-------------------+------+-----+---------+-------+---------------------------------------------+---------------------+
```

4-10-10. 直播间用户属性表 - room_owner_user_attr
```shell
##
## data.room.owner.user_attr
##
+----------------+-------------------+------+-----+---------+-------+----------------------------------------------+---------------------+
| Field          | Type              | Null | Key | Default | Extra | Topology                                     | Comment             |
+----------------+-------------------+------+-----+---------+-------+----------------------------------------------+---------------------+
| now            | timestamp         |      |     |         |       | "$.extra.now"                                | 当前时间戳           | 
| platform       | varchar(20)       |      |     | NULL    |       |           -                                  | 平台                 | 
| room_id        | varchar(200)      |      |     |         |       | "$.data.room.id"                             | 直播间ID             | 
| owner_user_id  | varchar(200)      |      |     |         |       | "$.data.room.owner_user_id"                  | 直播间主播ID         |
| is_admin       | bool              |      |     |         |       | "$.data.room.owner.user_attr.is_admin"       | 是否为管理员         |
| is_muted       | bool              |      |     |         |       | "$.data.room.owner.user_attr.is_muted"       | 是否被禁言           |
| is_super_admin | bool              |      |     |         |       | "$.data.room.owner.user_attr.is_super_admin" | 是否为超级管理员     |
+----------------+-------------------+------+-----+---------+-------+----------------------------------------------+---------------------+
```

4-10-10-1. 直播间管理员权限表 - room_admin_privilege
```shell
##
## data.room.owner.user_attr.admin_privileges
##
+-----------------------+-------------------+------+-----+---------+-------+------------------------------------------------+---------------------+
| Field                 | Type              | Null | Key | Default | Extra | Topology                                       | Comment             |
+-----------------------+-------------------+------+-----+---------+-------+------------------------------------------------+---------------------+
| now                   | timestamp         |      |     |         |       | "$.extra.now"                                  | 当前时间戳           | 
| platform              | varchar(20)       |      |     | NULL    |       |           -                                    | 平台                 | 
| room_id               | varchar(200)      |      |     |         |       | "$.data.room.id"                               | 直播间ID             | 
| owner_user_id         | varchar(200)      |      |     |         |       | "$.data.room.owner_user_id"                    | 直播间主播ID         |
| admin_privilege_index | unsigned tinyint  |      |     |         |       |           -                                    | 管理员权限序号       | 
| admin_privilege       | text              |      |     |         |       | "$.data.room.owner.user_attr.admin_privileges" | 管理员权限列表       |
+-----------------------+-------------------+------+-----+---------+-------+------------------------------------------------+---------------------+
```

4-10-11. 直播间用户拥有的着装ID信息 - room_owner_user_dress_own_id
```shell
##
## data.room.owner.user_dress_info.dress_own_ids
##
+-----------------+-------------------+------+-----+---------+-------+---------------------------------------------------+---------------------+
| Field           | Type              | Null | Key | Default | Extra | Topology                                          | Comment             |
+-----------------+-------------------+------+-----+---------+-------+---------------------------------------------------+---------------------+
| now             | timestamp         |      |     |         |       | "$.extra.now"                                     | 当前时间戳           | 
| platform        | varchar(20)       |      |     | NULL    |       |           -                                       | 平台                 | 
| room_id         | varchar(200)      |      |     |         |       | "$.data.room.id"                                  | 直播间ID             | 
| owner_user_id   | varchar(200)      |      |     |         |       | "$.data.room.owner_user_id"                       | 直播间主播ID         |
| dress_own_index | unsigned tinyint  |      |     |         |       |           -                                       | 用户拥有的着装序号   | 
| dress_own_id    | varchar(200)      |      |     |         |       | "$.data.room.owner.user_dress_info.dress_own_ids" | 用户拥有的着装ID     |
+-----------------+-------------------+------+-----+---------+-------+---------------------------------------------------+---------------------+
```

4-10-12. 直播间用户穿戴的着装ID信息 - room_owner_dress_wear_id
```shell
##
## data.room.owner.user_dress_info.dress_wear_ids
##
+------------------+-------------------+------+-----+---------+-------+----------------------------------------------------+---------------------+
| Field            | Type              | Null | Key | Default | Extra | Topology                                           | Comment             |
+------------------+-------------------+------+-----+---------+-------+----------------------------------------------------+---------------------+
| now              | timestamp         |      |     |         |       | "$.extra.now"                                      | 当前时间戳           | 
| platform         | varchar(20)       |      |     | NULL    |       |           -                                        | 平台                 | 
| room_id          | varchar(200)      |      |     |         |       | "$.data.room.id"                                   | 直播间ID             | 
| owner_user_id    | varchar(200)      |      |     |         |       | "$.data.room.owner_user_id"                        | 直播间主播ID         |
| dress_wear_index | unsigned tinyint  |      |     |         |       |           -                                        | 用户穿戴的着装序号   | 
| dress_wear_id    | varchar(200)      |      |     |         |       | "$.data.room.owner.user_dress_info.dress_wear_ids" | 用户穿戴的着装ID     |
+------------------+-------------------+------+-----+---------+-------+----------------------------------------------------+---------------------+
```

4-11. 直播间包元数据 - room_pack_meta
```shell
##
## data.room.pack_meta
##
+----------+-------------------+------+-----+---------+-------+----------------------------------+---------------------+
| Field    | Type              | Null | Key | Default | Extra | Topology                         | Comment             |
+----------+-------------------+------+-----+---------+-------+----------------------------------+---------------------+
| now      | timestamp         |      |     |         |       | "$.extra.now"                    | 当前时间戳           | 
| platform | varchar(20)       |      |     | NULL    |       |           -                      | 平台                 | 
| room_id  | varchar(200)      |      |     |         |       | "$.data.room.id"                 | 直播间ID             | 
| cluster  | varchar(50)       |      |     |         |       | "$.data.room.pack_meta.cluster"  | 集群                |
| dc       | varchar(50)       |      |     |         |       | "$.data.room.pack_meta.dc"       | 数据中心             |
| env      | varchar(50)       |      |     |         |       | "$.data.room.pack_meta.env"      | 环境                |
| extras   | json              |      |     |         |       | "$.data.room.pack_meta.extras"   | 附加信息             |
| scene    | text              |      |     |         |       | "$.data.room.pack_meta.scene"    | 场景                |
| trace_id | varchar(200)      |      |     |         |       | "$.data.room.pack_meta.trace_id" | 跟踪ID              |
+----------+-------------------+------+-----+---------+-------+----------------------------------+---------------------+
```

4-12. 直播间付费直播数据 - room_paid_live_data
```shell
##
## data.room.paid_live_data
##
+----------------------+-------------------+------+-----+---------+-------+---------------------------------------------------+---------------------+
| Field                | Type              | Null | Key | Default | Extra | Topology                                          | Comment             |
+----------------------+-------------------+------+-----+---------+-------+---------------------------------------------------+---------------------+
| now                  | timestamp         |      |     |         |       | "$.extra.now"                                     | 当前时间戳           | 
| platform             | varchar(20)       |      |     | NULL    |       |           -                                       | 平台                 | 
| room_id              | varchar(200)      |      |     |         |       | "$.data.room.id"                                  | 直播间ID             | 
| anchor_right         | unsigned tinyint  |      |     |         |       | "$.data.room.paid_live_data.anchor_right"         | 主播权限             |
| delivery             | unsigned tinyint  |      |     |         |       | "$.data.room.paid_live_data.delivery"             | 交付状态             |
| duration             | unsigned int      |      |     |         |       | "$.data.room.paid_live_data.duration"             | 直播时长             |
| max_preview_duration | unsigned int      |      |     |         |       | "$.data.room.paid_live_data.max_preview_duration" | 最大预览时长          |
| need_delivery_notice | bool              |      |     |         |       | "$.data.room.paid_live_data.need_delivery_notice" | 是否需要交付通知      |
| paid_type            | unsigned tinyint  |      |     |         |       | "$.data.room.paid_live_data.paid_type"            | 付费类型             |
| pay_ab_type          | unsigned tinyint  |      |     |         |       | "$.data.room.paid_live_data.pay_ab_type"          | 付费AB类型           |
| privilege_info       | json              |      |     |         |       | "$.data.room.paid_live_data.privilege_info"       | 特权信息             |
| privilege_info_map   | json              |      |     |         |       | "$.data.room.paid_live_data.privilege_info_map"   | 特权信息映射         |
| view_right           | unsigned tinyint  |      |     |         |       | "$.data.room.paid_live_data.view_right"           | 观看权限             |
+----------------------+-------------------+------+-----+---------+-------+---------------------------------------------------+---------------------+
```