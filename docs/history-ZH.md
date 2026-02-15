# 📜 日志记录

## 🎉 v0.1 - 2024.08.05
### 🚀 功能开发

- ⬆️支持直播视频下载

## 🎉 v0.2 - 2024.09.06
### 🚀 功能开发
- ✨支持从默认文件配置参数
- ♻️重构直播链接下载

### 🐞 BUG修复/优化
- 📈优化直播视频链接配置逻辑

## 🎉 v0.3 - 2025.02.23
### 🚀 功能开发
- ✨支持批量直播链接下载
- ✨支持无人值守直播下载
- ✨支持多线程直播视频下载
- 📝更新文档-使用演示

### 🐞 BUG修复/优化
- 🩹修复下载直播出错 - 'NoneType' object has no attribute 'group'
- 🩹修复下载直播视频发生超时错误

## 🎉 v0.4 - 2025.03.01

### 🚀 功能开发

- ⬆️支持数据库功能，持久化存储直播分享链接和存储路径
- ✨增加下载功能测试用例

### 🐞 BUG修复/优化

- 🩹修复下载过程中发生 “TypeError: 'tuple'” 的类型错误

## 🎉 v0.5 - 2025.05.05

### 🚀 功能开发

- ✨启用前端功能，支持用户通过分享直播间视频链接下载
- ✨支持一次性提交多个直播间视频链接下载
- ✨UI 添加喜爱等级滑动评分进度条
- ✨后台数据库支持喜爱列表的添加
- 📝更新了 ReadMe 文档
- ✨增添了剪切板粘贴按钮， 支持从剪切板直接复制到文本框

### 🐞 Bug修复/优化

- 📈优化了数据库喜爱列表结构，喜爱列表中添加 owner_user_id 属性
- 📈优化了前端架构，各组件解耦
- 📈优化了提交按钮的处理逻辑和位置显示
- 📈优化了后台直播间喜好评分的处理逻辑

## 🎉 v0.6 - 2025.05.29

### 🚀 功能开发

- ✨支持用户UI下添加喜爱功能和等级
- ✨支持了日志记录功能

## 🎉 v0.7 - 2025.11.03
### 🚀 功能开发
- 📖增加了项目日志变更记录
- ✨启用保存直播响应数据到数据库

### 🐞 BUG修复/优化
- 🩹修复了当主播修改抖音用户名后，分享的直播间链接在下载时会创建新的直播视频目录。
- 🩹修复了长期运行服务下的日志轮转问题，按照 `年-月-日` 文件格式保存。
- 🩹修复了在网页上一次性下载多个链接的情况下会触发多次重复下载的情况。

## 🎉 v0.7.1 - 2025.11.29
### 🚀 功能开发
- ✨构造了前端页面的基本框架结构
- ✨优化了服务启动脚本

### 🐞 BUG修复/优化
- 🩹修复了下载出错时, 错误响应数据无法保存.
```shell
[2025-11-01 23:11:07,613]-[default]-[ERROR]: Try download live stream https://v.douyin.com/yipKRJGSAbY/ failed! 'FULL_HD1'
Exception in thread Thread-259 (run):
Traceback (most recent call last):
  File "/usr/local/python312/lib/python3.12/threading.py", line 1075, in _bootstrap_inner
    self.run()
  File "/usr/local/python312/lib/python3.12/threading.py", line 1012, in run
    self._target(*self._args, **self._kwargs)
  File "/mnt/main/Service/SocialMediaStreamDownloader/backend/src/platform/douyin/douyin_live_downloader.py", line 422, in run
    raise e
  File "/mnt/main/Service/SocialMediaStreamDownloader/backend/src/platform/douyin/douyin_live_downloader.py", line 402, in run
    stream_url, stream_name = self.live_external_info.get_flv_pull_url(live_response, self.config.get_config_dict_attr("$.flv_clarity"))
                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/mnt/main/Service/SocialMediaStreamDownloader/backend/src/platform/douyin/douyin_live_external_info.py", line 98, in get_flv_pull_url
    raise e
  File "/mnt/main/Service/SocialMediaStreamDownloader/backend/src/platform/douyin/douyin_live_external_info.py", line 72, in get_flv_pull_url
    if flv_clarity == 1 and build_dict["data"]["room"]["stream_url"]["flv_pull_url"]["FULL_HD1"] is not None:
                            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
KeyError: 'FULL_HD1'
```

- 🩹修复了直播响应数据由于数据库表因为不一致保存失败的问题.
```shell
[2025-11-04 13:41:17,703]-[default]-[DEBUG]: xxx
[2025-11-04 13:41:17,706]-[default]-[INFO]: connect database social_media_stream_downloader successfully!
[2025-11-04 13:41:17,709]-[default]-[ERROR]: failed to insert record into room_owner: (1054, "Unknown column 'follow_info_follow_status' in 'field list'")
[2025-11-04 13:41:17,710]-[default]-[ERROR]: record data: xxx
[2025-11-04 13:41:17,711]-[default]-[ERROR]: insert room_owner failed: (1054, "Unknown column 'follow_info_follow_status' in 'field list'")
[2025-11-04 13:41:17,711]-[default]-[ERROR]: import live info to database failed! (1054, "Unknown column 'follow_info_follow_status' in 'field list'")
skip this step!
```

- 🩹修复了直播下载由于网络负载失败时，下载线程数不能正确反应当前下载线程情况的问题
```shell
[2025-11-30 03:26:33,601]-[default]-[INFO]: 当前总下载数：13

[2025-11-30 03:34:57,538]-[default]-[ERROR]: request error: [Errno 104] Connection reset by peer
[2025-11-30 03:34:57,539]-[default]-[ERROR]: 	name:xx👩🏻
	path:/mnt/video/douyin/live/xx__/20251129234109_stream-406639270267978411_or4.flv
	url:http://xxx
	download failed!!!
```

- 🩹修复了前端页面链接文本框内容超过当前页面时显示错乱的情况

## 🎉 v0.8 - 2026.02.13
### 🚀 功能开发

- ✨实现动态平台配置系统，支持通过配置文件添加新平台
- ✨增强输入验证和错误处理机制
- ✨添加速率限制功能，防止API滥用
- ✨实现结构化日志输出，支持JSON格式
- ✨改进资源管理，添加线程池清理机制
- ✨重构部署脚本，支持start/stop/restart命令
- ✨添加基础单元测试框架
- ✨实现页脚动态年份显示，替代硬编码年份 (2026.02.15)

### 🐞 BUG修复/优化

- 🩹修复了硬编码平台列表问题，改为配置驱动
- 🩹改进了URL解析和验证逻辑，增强安全性
- 🩹优化了错误处理机制，提供更准确的错误信息
- 🩹解决了线程池资源泄漏问题
- 🩹改进了部署脚本的健壮性和错误处理
- 📝更新了项目文档，完善了架构说明
- 📝将改进总结整合到README.md中
- 📝将问题日志整合到develop_note.md中
- 📝将数据库设计整合到design.md中
- 📝将功能特性整合到design.md中
- 📝将用户指南整合到README.md中
- 📝删除冗余文档文件，减少维护负担
- 📝优化文档结构，提高可维护性
- 🩹修复了页脚年份硬编码问题，实现动态更新 (2026.02.15)
- ✨实现下载数量统计和显示功能 (2026.02.15)
- ✨添加下载限制功能，基于max_thread配置参数 (2026.02.15)
- ✨创建API端点/api/download-status获取当前下载状态 (2026.02.15)
- ✨实现在前端显示当前/最大/可用下载槽位 (2026.02.15)
- ✨添加下载状态轮询更新机制 (2026.02.15)
- ✨增强提交按钮逻辑，检查下载限制后再提交 (2026.02.15)
- ✨增强日志系统，添加全面的后端操作日志 (2026.02.15)
- ✨实现API端点/api/logs以检索最近的日志条目 (2026.02.15)
- ✨添加前端日志查看器UI，支持过滤和刷新功能 (2026.02.15)
- ✨为日志显示添加带颜色编码的日志级别样式 (2026.02.15)
