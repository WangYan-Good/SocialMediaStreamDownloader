[TOC]

# 📝 项目功能\(Function\)

本项目是一个社交媒体音视频流下载器，目前提供：

- [x] 抖音直播下载

# 💻 程序界面\(Screenshot\)

![web-UI](./docs/media/entry.PNG)

# 📽 运行演示\(Example\)

## 方式一：直接下载演示

1. 下载本项目后，进入项目根目录
```shell
# 示例
[userid@localhost SocialMediaStreamDownloader]$ pwd
~/SocialMediaStreamDownloader
```

2. 创建唯一运行时配置并填写实际值

```shell
mkdir -p config
cp docs/design/config.yml.example config/config.yml
chmod 600 config/config.yml
```

`config/config.yml` 是唯一持久配置源；不要提交该文件，也不要另建 `.env`
保存数据库、端口、Cookie 或 Token。

`download.test_mode: true` 只跳过最终的直播流数据传输。分享链接解析、直播信息请求、
状态判断、流地址提取、数据库读写、目录准备和任务调度与正常模式保持一致，因此测试模式
仍会访问网络和数据库，也不能作为离线或沙箱模式使用。

直播流始终优先选择 FLV；所有 FLV 清晰度均无可用地址时，才按 `hls_clarity` 自动回退
HLS，并通过 ffmpeg stream-copy 保存为 `.ts` 文件。Docker 镜像已经安装 ffmpeg；直接在
宿主机运行时必须保证 `ffmpeg` 可执行文件位于 `PATH`。测试模式不会启动 ffmpeg，因此
不要求宿主机安装该程序。

HLS 的短暂网络中断由 ffmpeg 有界重连处理：`max_timeout` 限制单次网络 I/O 等待，
`hls_stall_timeout` 限制无输出进展时长，`hls_terminate_grace` 是 TERM 后的退出宽限，
`max_retry` 是首次尝试后的进程重启次数。健康直播没有总录制时长限制；这些参数统一在
YAML 中配置。

3. 执行运行脚本将自动安装依赖并部署
```shell
# 需要提前安装 python3.12，此处不做介绍
[SocialMediaStreamDownloader]$ sh ./run-server.sh
```

4. 使用 `config/config.yml` 中的 `server.port` 打开网页，在输入框添加分享链接即可下载
![web-UI](./docs/media/web-ui.PNG)

## 数据库结构迁移

数据库启用时，先显式确认 schema 状态；服务启动不会自动建表或执行迁移：

```shell
python -m backend.src.database.migration_cli status
python -m backend.src.database.migration_cli check
```

新数据库使用：

```shell
python -m backend.src.database.migration_cli upgrade
```

已有数据库必须先通过 `check`，备份并人工复核后，才可纳入当前基线：

```shell
python -m backend.src.database.migration_cli stamp
```

其余显式命令为：

```shell
python -m backend.src.database.migration_cli downgrade REVISION --confirm-database DATABASE_NAME
python -m backend.src.database.migration_cli revision "change description"
```

`stamp` 只写 Alembic 版本，不执行建表或 `ALTER`，但只有 12 张受管表的严格结构校验
全部通过时才会执行。`upgrade` 会拒绝含受管表但尚未版本化的数据库，已有库必须走
`check + stamp`。非临时库执行 `downgrade` 必须用实际库名进行显式确认；基线
revision 的任何降级路径（包括 `base`、`-1` 等等价写法）只允许通过显式数据库名 override
创建且严格命名的临时迁移测试库。所有降级操作前必须备份并人工审查 revision。
运行时状态为 `ready` 时才允许持久化写入；`unavailable` 或 `blocked` 不阻断 live 网络请求
和流下载，但会跳过数据库写入。

## 方式二：Docker Compose

完成同一份 `config/config.yml` 后，通过包装脚本启动：

```shell
./run-docker.sh up -d
```

脚本仅在本次 Compose 命令期间派生权限为 `0600` 的临时插值文件，并在退出时删除；
应用容器将 `config/config.yml` 只读挂载到 `/run/secrets/`，入口以 root 校验并复制到
容器可写层的 canonical 路径，设置 `appuser` 所有权和 `0600` 后立即降权运行服务。
容器内连接配套 MySQL 时，将
`database.host` 配置为 `mysql`。

# 🔐 安全配置\(Security Configuration\)
本项目使用本地且被 Git/Docker 构建上下文排除的 `config/config.yml` 管理敏感配置。

## 安全要求

- 保持 `config/config.yml` 权限最小化，并定期轮换数据库密码、Cookie 和 Token。
- 不要将真实配置复制进镜像、日志、Issue 或测试 fixture。
- Alembic 配置不保存数据库 URL；迁移命令只从统一 YAML 在内存中构造连接。
- 仓库历史中曾暴露的凭据需要在外部完成轮换；本项目不会自动重写 Git 历史。

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

- 本项目的 Github 仓库链接 [SocialMediaStreamDownloader](https://github.com/WangYan-Good/SocialMediaStreamDownloader.git)

针对本项目有任何问题请在公开仓库中提交 [issue](https://github.com/WangYan-Good/SocialMediaStreamDownloader/issues) 或参与讨论。

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
