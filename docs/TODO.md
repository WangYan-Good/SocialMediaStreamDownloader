# 🚩待办列表\(TODO\)

## frontend
- ⌛添加前端下载结果响应
- ⌛优化前端链接单次请求下载处理
- ⌛添加优先偏好下载
- ⌛添加喜好程度

## backend
- ✅添加数据库后台
- ✅添加前端模块
- ⌛添加日志模块
- ⌛添加多用户模块
- ⌛剥离 F2 依赖
- ⌛添加 docker 部署
- ⌛添加直播记录
- ⌛简化数据库表设计，易于扩展和存储

### login
- ⌛添加自动从浏览器获取cookie功能
- ⌛更新登录信息

### post
- ⌛根据用户分享单视频下载
- ⌛根据分享主页批量视频下载
- ⌛根据用户来开启新的子线程下载
- ⌛添加同时下载最大用户数

### log
- ⌛添加日志打印功能
- ⌛添加日志分级功能

### live
- ✅添加通过分享链接直播下载功能
- ✅添加分享单个直播间链接下载功能
- ✅添加批量直播下载
- ✅添加自定义路径直播下载保存
- ⌛ 添加自动直播下载功能
- ✅ 添加最大下载数量限制
- ⌛ 动态控制直播下载

### feature
- ✅ 使用数据库对下载列表进行管理
- ✅ 使用 web 页面向数据库添加共享 url

### APP
- ✅添加多平台支持
- ⌛支持通过ffmpeg下载
- ⌛支持UI界面下载
- ⌛支持安装可执行文件
- ⌛添加动态命令参数控制下载
- ⌛添加远程下载到指定的服务器位置
- ⌛添加日志功能

### Improve

1. 整合前后端分离设计
2. 整理后端采用数据库连接池后的一致性处理
  - [x] 各个表连接数据库的代码更新
  - [x] get_db_connector() 弃用的处理（使用 get_connection() 接口）

### Bug & Know Issue & Limitation

#### Bug & Know Issue
1. 数据库结构一致性
  - [ ] 数据库图片资源表结构 `uri_index` 不一致
  - PictureTable
  - PictureUrlTable
  - PictureContentTable
  - PictureFlexSettingTable
  - PictureTextSettingTable

2. 关于图片资源的结构兼容性
  1. 当前不同记录存在结构不一致情况，需要考虑导入导出时的显示一致性
      - [ ] `deco_list.[x].nine_patch_image`
      - [ ] `$.data.room.owner.authentication_info`

3. 导入记录缺失
    - [x] `$.data.room.deco_list.[x].text_font_config`

```yml
room:
  owner:
    biz_relation:
      shop_fans_club_reverse: true

room:
  owner:
    border:
      dress_id: '7438838721359254537'
      icon:
        avg_color: ''
        flex_setting_list: []
        height: 282
        image_type: 0
        is_animated: false
        open_web_url: ''
        text_setting_list: []
        uri: webcast/ece2d36c6588da79caa693e5a7ba9555.png
        url_list:
        - https://p3-webcast.douyinpic.com/img/webcast/ece2d36c6588da79caa693e5a7ba9555.png~tplv-obj.image
        - https://p11-webcast.douyinpic.com/img/webcast/ece2d36c6588da79caa693e5a7ba9555.png~tplv-obj.image
        width: 282
      level: 0
      thumb_icon:
        avg_color: ''
        flex_setting_list: []
        height: 282
        image_type: 0
        is_animated: false
        open_web_url: ''
        text_setting_list: []
        uri: webcast/3e431cd7af73e47622258b2ffbd9368b.png
        url_list:
        - https://p3-webcast.douyinpic.com/img/webcast/3e431cd7af73e47622258b2ffbd9368b.png~tplv-obj.image
        - https://p11-webcast.douyinpic.com/img/webcast/3e431cd7af73e47622258b2ffbd9368b.png~tplv-obj.image
        width: 282
```

4. 针对原始列表，导出时排序不一致问题
    - [x] `admin_user_ids`
    - [x] `level_list`
    - [x] `new_im_icon_with_level`
    - [x] `new_live_icon`

#### Limitation