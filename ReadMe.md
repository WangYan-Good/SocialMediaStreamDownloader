[TOC]

# 📝 项目功能\(Function\)

# 💻 程序界面\(Screenshot\)

![web-UI](./docs/media/entry.PNG)

# 📽 运行演示\(Example\)

## 直接下载演示

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

4. 执行脚本安装依赖并后台运行
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

5. 打开浏览器，`localhost:5000` 进入网页，在输入框添加分享链接即可下载
![web-UI](./docs/media/web-ui.PNG)

# 📋 项目说明\(Instructions\)

## 项目概述

SocialMediaStreamDownloader 是一个用于下载社交媒体平台视频、直播等内容的工具。它支持多种社交媒体平台，通过简单的Web界面提供便捷的下载功能。

## 架构设计

项目采用前后端分离的架构：

- **前端**：提供用户友好的Web界面，用户可以通过输入分享链接来触发下载
- **后端**：基于Flask的API服务，处理下载请求并分发给相应的平台处理器
- **核心引擎**：平台分发器（PlatformDispatcher）负责识别平台类型并调用相应处理器

## 支持的平台

- 抖音 (Douyin)
- 其他平台可通过配置轻松扩展

## 功能特性

- 支持批量下载
- 多线程下载
- 视频和直播内容下载
- 配置化管理
- 结构化日志记录
- 速率限制保护
- 动态平台扩展

## 配置说明

### 速率限制配置

系统默认启用了速率限制，如需调整，请参考以下配置：

- 默认限制：每小时100个请求
- POST端点限制：每分钟10个请求

### 日志配置

在 `config/base_config.yml` 中可以配置日志相关选项：

```yaml
log_enable: true      # 启用日志
log_path: ./logs      # 日志保存路径
structured_logging: false  # 结构化日志输出
```

### 平台配置

#### 添加新平台支持

通过编辑 `config/platforms.yml` 文件可以添加新平台支持：

```yaml
new_platform:
  handler: backend.src.platform.new_platform.handler_function
  domains:
    - example.com
    - www.example.com
  enabled: true
```

## 部署和运行

### 使用部署脚本

新版本的部署脚本支持以下命令：

```bash
# 启动服务
./run-server.sh start

# 停止服务
./run-server.sh stop

# 重启服务
./run-server.sh restart
```

# ⚠️ 免责声明\(Disclaimers\)

## **项目性质说明**
**SocialMediaStreamDownloader**（下称“本项目”）是一个**技术研究项目**，旨在探讨多媒体内容获取与处理的技术实现。本项目提供的所有代码、文档及相关资源**仅供学习、研究与合法合规用途参考**。

## **使用责任与法律风险**
- **用户责任**：您在使用本项目时，应自行了解并遵守所在国家/地区关于数据获取、版权保护、隐私保护等相关法律法规。**因使用本项目所产生的任何法律风险及后果，由用户自行承担**。    
- **内容限制**：禁止使用本项目下载、传播或用于以下内容：    
    - 受版权保护且未经授权的内容        
    - 侵犯他人隐私或肖像权的内容        
    - 违反平台服务条款的内容        
    - 任何违法、违规或破坏性用途        
- **平台规则**：使用本项目时，请严格遵守相关社交媒体平台（如 YouTube、Twitter、Instagram 等）的**服务条款**（Terms of Service）。违规使用可能导致您的账户被封禁或法律追责。

## **技术免责**
- **稳定性**：本项目不保证在所有平台、网络环境或系统配置下的稳定性和兼容性。    
- **维护**：开发者不承担因代码更新、API变更或第三方服务调整导致的故障修复义务。    
- **数据安全**：使用本项目时，请自行注意数据安全与隐私保护，开发者不对数据泄露或损失负责。 

## **版权声明**
- 本项目代码采用开源许可证（详见 `LICENSE` 文件）。    
- 项目中涉及的第三方库、API或平台商标归其所有者所有。    
- **本项目不授予任何使用其代码侵犯第三方权利的许可**。   

## **免责范围**
**开发者及贡献者不对以下情况承担责任**：
- 用户违反法律法规或平台条款的行为    
- 因使用本项目造成的直接或间接损失    
- 项目代码被用于任何非法或侵权活动    
- 因技术问题导致的数据丢失、系统故障或其他风险   

## **使用即表示同意**
**当您使用、复制或修改本项目代码时，即表示您已阅读、理解并同意本免责声明的全部内容。如您不同意，请立即停止使用本项目。**

⚠️  注意：请仅在遵守相关法律法规及平台条款的前提下使用本工具。
    开发者不对滥用行为负责，使用前请务必了解当地法律及平台政策。

# ✉️ 联系作者\(Contact\)

# ♥️ 支持项目\(Support\)

<img src="./docs/media/zhifubao.jpg" width=200px>

<img src="./docs/media/weixin.jpg" width=200px>

# 📜 变更记录\(Change\)

参考 [变更记录](./docs/history-ZH.md#-日志记录)

# 💡 项目参考\(Refer\)

* https://github.com/Johnserf-Seed/f2
* https://github.com/Johnserf-Seed/TikTokDownload
* https://github.com/ihmily/DouyinLiveRecorder
* https://github.com/JoeanAmier/TikTokDownloader

# 📄 开源许可\(License\)

本项目采用 **GNU Affero General Public License v3.0 (AGPL-3.0)** 开源协议。

**重要提示**：
- 本工具仅供**合法学习与研究**使用
- 使用前请确保遵守相关法律法规及平台条款
- 开发者对任何滥用行为不承担责任