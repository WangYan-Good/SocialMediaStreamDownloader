[TOC]

# 📝 项目功能\(Function\)

## douyin

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
- ⌛添加分享单个直播间链接下载功能
- ✅添加批量直播下载
- ✅添加自定义路径直播下载保存
- ⌛ 添加自动直播下载功能
- ✅ 添加最大下载数量限制
- ⌛ 动态控制直播下载

### feature
- ✅ 使用数据库对下载列表进行管理
- ⌛ 使用 web 页面向数据库添加共享 url

### APP
- ✅添加多平台支持
- ⌛支持通过ffmpeg下载
- ⌛支持UI界面下载
- ⌛支持安装可执行文件
- ⌛添加动态命令参数控制下载
- ⌛添加远程下载到指定的服务器位置
- ⌛添加日志功能

# 💻 程序界面\(Screenshot\)

TODO

# 📽 运行演示\(Example\)

1. 下载本项目后，进入项目根目录
```shell
# 示例
[userid@localhost SocialMediaStreamDownloader]$ pwd
/mnt/nvme/CodeSpace/OpenSource/SocialMediaStreamDownloader
```
2. 执行前请确认已经下载安装 python3.11 或之后的版本
```shell
[userid@localhost SocialMediaStreamDownloader]$ python3 --version
Python 3.11.8
```
3. 创建虚拟环境 venv 并激活
```shell
[userid@localhost SocialMediaStreamDownloader]$ python3 -m venv venv

[userid@localhost SocialMediaStreamDownloader]$ . ./venv/bin/activate
(venv) [userid@localhost SocialMediaStreamDownloader]$
```

4. 执行脚本安装依赖
```shell
(venv) [userid@localhost SocialMediaStreamDownloader]$ sh run-server.sh # 等待执行完成即可
你处于Python虚拟环境中，路径为：/mnt/nvme/CodeSpace/OpenSource/SocialMediaStreamDownloader/venv
当前pip3的版本是：24.2
当前pip3版本不是最新，正在更新...
Looking in indexes: https://pypi.tuna.tsinghua.edu.cn/simple/
Requirement already satisfied: pip in ./venv/lib/python3.11/site-packages (24.2)
pip3 更新完成，新版本为：
Looking in indexes: https://pypi.tuna.tsinghua.edu.cn/simple/
...
```

5. 配置分享链接，以 douyin 为例
```shell
# 编辑文件 ./config/douyin/conf.ini
# 在 [live] 添加直播分享链接，以行分隔
[live]
  https://v.douyin.com/XXX1/  # URL1
  https://v.douyin.com/XXX2/  # URL2

# 
# 编辑文件 ./config/base_config.yml
# 配置同一时间最大下载数量
save_path: XXX
max_thread: XXX
```

6. 开始下载，执行下载命令
```shell
(venv) [userid@localhost SocialMediaStreamDownloader]$ python3 ./src/platform/douyin/douyin_live_downloader.py
```

7. 开启下载后，应用会不断轮询 [live] 列表，会不断监听直播状态，如需退出，输入以下命令：
```shell
# 触发退出线程，停止监听器，当前正在下载的直播不会中断
quit
```

# 📋 项目说明\(Instructions\)

TODO

# 🚩待办列表\(TODO\)

- ✅添加数据库后台
- ⌛剥离 F2 依赖
- ⌛添加前端模块
- ⌛添加日志模块

# ⚠️ 免责声明\(Disclaimers\)

TODO

# ✉️ 联系作者\(Contact\)

TODO

# ♥️ 支持项目\(Support\)

TODO

# 💡 项目参考\(Refer\)

* https://github.com/Johnserf-Seed/f2
* https://github.com/Johnserf-Seed/TikTokDownload
* https://github.com/ihmily/DouyinLiveRecorder
* https://github.com/JoeanAmier/TikTokDownloader