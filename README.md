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

2. 配置环境配置 .env

参考下一节 [🔐 安全配置](#-安全配置security-configuration)

3. 执行运行脚本将自动安装依赖并部署
```shell
[userid@localhost SocialMediaStreamDownloader]$ sh ./run-server.sh 
激活Python虚拟环境
激活成功！
当前pip3的版本是：26.0.1
最新的pip3版本是：26.0.1
当前pip3版本已是最新。
🚀 安装/更新Python依赖...
... (省略依赖安装过程日志)
✅ 依赖安装完成
服务进入后台运行，可使用 tail -f ./logs/social_media_stream_downloader 查看日志
```

4. 打开浏览器，`localhost:5000` 进入网页，在输入框添加分享链接即可下载
![web-UI](./docs/media/web-ui.PNG)

# 🔐 安全配置\(Security Configuration\)
本项目支持使用环境变量管理敏感配置，避免将密码、Cookie 等凭据硬编码在配置文件中。

## 创建环境配置文件
```bash
# 复制模板文件
cp .env.example .env

# 编辑 .env 文件，填写实际的配置值
vim .env
```

## 配置项说明

| 环境变量 | 说明 | 示例值 |
|---------|------|--------|
| `DB_HOST` | 数据库主机 | `localhost` |
| `DB_PORT` | 数据库端口 | `3306` |
| `DB_NAME` | 数据库名称 | `social_media_stream_downloader` |
| `DB_USER` | 数据库用户 | `admin` |
| `DB_PASSWORD` | 数据库密码 | `your_secure_password` |
| `DOUYIN_COOKIE_SHARE_LIVE_URL` | 抖音分享页面 Cookie | 从浏览器获取 |
| `DOUYIN_COOKIE_LIVE_ROOM_INFO` | 抖音直播房间 Cookie | 从浏览器获取 |
| `DOUYIN_COOKIE_POST_INFO` | 抖音帖子请求 Cookie | 从浏览器获取 |
| `DOUYIN_MSTOKEN` | 抖音 msToken | 从浏览器获取 |
| `DOWNLOAD_SAVE_PATH` | 下载保存路径 | `/path/to/videos` |
| `SERVER_PORT` | 服务器端口 | `5000` |
| `FLASK_DEBUG` | 调试模式开关 | `false` |

## 获取抖音 Cookie 和 msToken

1. 浏览器打开抖音并登录
2. 按 F12 打开开发者工具
3. 进入 Network 标签，刷新页面
4. 点击任意请求，在 Headers 中找到 Cookie
5. 复制完整的 Cookie 值粘贴到 `.env` 文件对应位置

## 安全注意事项

- ⚠️ **切勿将 `.env` 文件提交到代码仓库**
- 定期更换数据库密码和 Cookie
- 生产环境务必关闭调试模式 (`FLASK_DEBUG=false`)
- 使用强密码，避免使用默认值

# 📋 项目说明\(Instructions\)

TODO

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