[TOC]

# 📝 项目功能\(Function\)

本项目是一个社交媒体音视频流下载器，目前提供：

- [x] 抖音直播下载
- [x] 抖音单作品下载（视频 / 图集 / 原声 / 封面）
- [x] 主播主页浏览：读取详情与作品列表，勾选或一键批量下载
- [x] 下载历史筛选 + 直播状态检查

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

生产入口固定为 `python ./server.py`，由单进程、4 个应用线程的 **Waitress** WSGI server
提供服务；`run-server.sh` 与 Docker 均进入这个入口。`server.debug_mode` 只控制项目自身经过
字段白名单约束的安全诊断日志，即使设为 `true` 也不会启用 Werkzeug development server、
interactive debugger、reloader 或 traceback response。示例配置默认关闭该选项。

默认的直接部署只监听 `127.0.0.1`。本机通过 HTTP 使用时保留 `cookie_secure: false`；需要
对外服务时，使用 **HTTPS reverse proxy** 终止 TLS、反向代理到该 loopback Waitress，且将
`cookie_secure: true`。禁止把原始 Waitress HTTP 端口直接暴露到外网，也不要把裸机配置改成
`0.0.0.0`。Docker 内部会显式适配为 `0.0.0.0`，但 Compose 只把应用端口发布到宿主机
`127.0.0.1`，该内部 bind 不是外部暴露许可。

`POST /api/auth/login` 具有进程内、application-local 的有界滥用防护：请求体最多 4096
bytes；每 60 秒全局最多 60 次、同一 transport peer 最多 20 次；最多同时执行 2 个
scrypt 认证，第三个请求立即返回带 `Retry-After` 的 429。连续密码失败从第 3 次开始采用
1、2、4…最多 60 秒的无 sleep backoff。peer 只取直连 socket 的 `remote_addr`，不信任
`X-Forwarded-For` 或 `X-Real-IP`；因此在反向代理后，所有请求会保守地共享代理 peer bucket。
本阶段不启用 trusted-proxy 重写，部署者不能用转发 header 绕过该边界。

直播流始终优先选择 FLV；所有 FLV 清晰度均无可用地址时，才按 `hls_clarity` 自动回退
HLS，并通过 ffmpeg stream-copy 保存为 `.ts` 文件。Docker 镜像已经安装 ffmpeg；直接在
宿主机运行时必须保证 `ffmpeg` 可执行文件位于 `PATH`。测试模式不会启动 ffmpeg，因此
不要求宿主机安装该程序。

FLV 录制只有在完整传输与 Content-Length 校验后，依次完成 Python buffer flush、媒体文件
`fsync`、文件关闭和父目录 `fsync` 才报告成功。任一存储提交步骤失败都会保留已捕获字节，
但不会产生成功结果、recovery journal 或数据库记录，也不会重新请求直播流。

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

## 单作品下载

**用法与直播完全相同** —— 同一个输入框，粘贴作品分享链接即可，不需要选类型。后端跟随
分享链接的跳转，按落地地址分流：直播间走直播链路，`/video/`、`/note/`、
`/share/video/`、`discover?modal_id=` 走作品链路。识别不出来的链接会记一条 warning 后丢弃。

一个作品会取回**四类文件**（各自可在 `platform.douyin.aweme.media` 下单独关闭）：
无水印视频、图集各图、原声、封面。

**存放结构：每个作品一个目录。**

```
{download.save_path}/douyin/aweme/{主播目录}/{发布时间}_{aweme_id}/
    20260701081200_7657271784144009946.mp4
    20260701081200_7657271784144009946_music.mp3
    20260701081200_7657271784144009946_cover.jpg
```

一个视频作品本身就产出 3 个文件，平铺会把多个作品的碎片混在一起，所以按作品归档。

**文件名不含作品文案**：文案可被作者修改、长度无上限，放进文件名会让「已下载」判定失效。
文案保存在 `aweme_record.desc`。

**不会重复下载。** 唯一性由五层保证：文件名里的 `aweme_id` 按 `_` 边界匹配；每类文件有
稳定尾（`.mp4` / `_music.mp3` / `_cover.jpg` / `_NN.jpg`）；主播改名时沿用数据库里记录的
原目录；不同账号同昵称时目录追加 `owner_user_id`（抖音不要求昵称唯一）；同一作品并发提交时
串行处理。判定**以磁盘上的文件为准**，因此数据库关闭、记录被删、平台某次响应少给一个文件，
都不会导致重复下载或永久漏文件。

作品之间的并发由 `platform.douyin.aweme.concurrency` 控制（默认 3），使用独立线程池 ——
不与直播下载、不与直播状态探测共享，避免相互阻塞。同一作品内的多个文件串行下载。

无登录时抖音的签名接口可用性不可控，因此 `POST_DETAIL` 失败后会回落解析分享页内嵌的
JSON（`platform.douyin.aweme.html_fallback`，默认开启）。作品已删除、设为私密或仅粉丝可见
属于正常结果，只记 info 日志，不重试、不写库。

## 主播作品浏览与批量下载

侧边栏「Posts」页。粘贴主播**主页**分享链接（App 里「查看TA的更多作品」），
上方显示主播详情，下方是作品列表：勾选想要的点「下载所选」，或者点「一键下载全部」。

**这两个接口必须有有效的登录 cookie。** 与单作品下载不同（那个无登录可用），
`USER_DETAIL` 和 `USER_POST` 在没有有效会话时返回 **HTTP 200 加空响应体** ——
读起来像「这个主播没有作品」，而不是「请重新登录」。因此：

- 程序会显式判定这种情况并提示「抖音登录已失效，请更新
  `platform.douyin.headers.post_info.cookie`」，不会把它显示成空列表
- 详情卡片上会显示「登录凭据 N 天后过期」（从 cookie 的 `sid_guard` 算出），
  少于 7 天时高亮

获取 cookie：浏览器登录 `www.douyin.com` → F12 → Network → 任选一个
`www.douyin.com/aweme/v1/web/...` 请求 → 复制 Request Headers 里整条 `Cookie` 的值。
必须用 Network 那条，`document.cookie` 拿不到 `HttpOnly` 的 `sessionid`。

**列表是增量的**：打开时拉第一页（约 19 条），点「加载更多」翻下一页。每页一个平台
请求并带随机延迟，所以翻页有可感知的耗时。「一键下载全部」是后台作业，自己把所有页
翻完再逐个下载，不需要你先把列表翻到底。

作品列表返回的每一项就是完整的作品对象，因此**下载 N 个作品不需要 N 次详情请求**。
下载本身完全复用单作品链路：目录布局、`identity` 去重、同名主播消歧、同作品并发串行、
落库全部一致。列表里会标出哪些作品已经下载过（读 `aweme_record`），部分下载显示为
`部分 2/3`。

封面缩略图由浏览器直连抖音 CDN，防盗链导致加载失败只影响缩略图，不影响下载。

**目录里会附带说明文件**，因为文件名和目录名里不含文案（文案可被作者修改，放进名字会让
「已下载」判定失效）：

```
douyin/aweme/{主播目录}/
    owner.txt                     主播详情：昵称、抖音号、签名、粉丝/关注/作品/获赞、采集时间
    avatar.jpg                    头像
    {发布时间}_{aweme_id}/
        {发布时间}_{aweme_id}.mp4
        {发布时间}_{aweme_id}_music.mp3
        {发布时间}_{aweme_id}_cover.jpg
        info.txt                  首行是文案，其后是作品 ID、类型、发布时间、主播
```

两个说明文件都**每次下载都会重写**。这带来三种增量效果：先前下过的作品会补上 `info.txt`；
作者改了文案会被更新；主播的粉丝数等快照会刷新（所以 `owner.txt` 里带「采集时间」而不是
假装是当前值）。`owner.txt` 每个下载任务只请求一次主播详情，不是每个作品一次；获取失败
不影响下载本身。

**默认保存最高分辨率。** 由 `platform.douyin.aweme.video_quality` 控制：

- `highest`（默认）：从 `video.bit_rate` 里按**实测的宽高**挑最大，同分辨率再比码率
- `default`：用 `video.play_addr` 给的地址

必须按实测排序，不能按 `gear_name`：实测某作品的 2160x3840 那一档名字叫
`adapt_lowest_4_1`。`play_addr` 的元数据也不可信——它自称 1080x1920，实际一次下到的是
576x1024。同一作品实测 `default` 为 4,178,167 字节、`highest` 为 6,545,850 字节（2160x3840），
约 1.57 倍。

头像取 `avatar_larger`（1080x1080）、封面取 `video.cover`（720x720），实测已是各自可得的最大，
无需选择。

## 下载历史筛选与直播状态检查

Download 与 History 两个页面共用同一个历史主播列表（Download 页是精简版）。
筛选和判定是分开的两件事：

1. **筛选**只读数据库，不发任何平台请求。可按昵称、收藏与评分区间、用户状态、
   「上次见到在播」时间窗筛选，并按评分 / 下载次数 / 上次见到在播排序。
   升序即「下载次数最少」与「最久未下载」。每页上限由 `history.page_size_limit` 控制。
2. **判定**只来自点击「检查直播状态」后发出的真实请求，且只针对当前这一页。
   一次探测约 5-12 秒，因此并发与批量都受 `platform.douyin.live.probe` 约束。
   探测到正在直播的行会出现「立即下载」，走既有的下载入口。

`share_url` 上的 `last_live_status` / `last_checked_at` / `last_room_id` 是探测结果的
缓存，用来支撑筛选排序和「上次见到：3 天前」这类提示，**不代表此刻是否在播**。
数据库关闭或不可用时，历史列表返回 503 并在界面上说明，直播下载本身不受影响。

## 数据库结构迁移
数据库启用时，服务启动只检查 schema，不会自动建表或执行迁移。支持的操作入口为：

```shell
python -m backend.src.database.migration_cli status
python -m backend.src.database.migration_cli check
python -m backend.src.database.migration_cli upgrade
```

`status` 输出数据库的 `current` 与代码的 `heads`，不要从 README 猜测当前 head。正式升级、
已有库的 `stamp`、显式 downgrade、preflight、backup 与 post-upgrade gate 见
[数据库迁移操作指南](./docs/operations/migrations.md)。完整 backup/restore、rollback、凭据与
账户生命周期见 [Release Operations Runbook](./docs/operations/release.md)。

## 方式二：Docker Compose

完成同一份 `config/config.yml` 后，通过包装脚本启动：

```shell
./run-docker.sh up -d
```

脚本仅在本次 Compose 命令期间派生权限为 `0600` 的临时插值文件，并在退出时删除；
应用容器将 `config/config.yml` 只读挂载到 `/run/secrets/`，入口以 root 校验并复制到
容器可写层的 canonical 路径，设置 `appuser` 所有权和 `0600` 后立即降权运行服务。
镜像仍执行 `python ./server.py`，因此与宿主机启动使用同一个 Waitress production launcher
和同一套 SIGINT/SIGTERM 清理流程。
Compose 只在宿主 `127.0.0.1` 发布应用端口；外部访问仍必须通过 HTTPS reverse proxy，
并在配置中使用 `cookie_secure: true`。本机直接 HTTP 可使用 `cookie_secure: false`。
容器内连接配套 MySQL 时，将
`database.host` 配置为 `mysql`。

首次执行 `run-docker.sh` 会在被 Git 忽略的 `config/mysql-root-password` 生成独立的随机
MySQL root secret，权限固定为 `0600`，以后启动复用同一值；该文件同时被 Git 与 Docker
build context 排除。Compose 只把它作为
`MYSQL_ROOT_PASSWORD_FILE` secret 挂载给 MySQL；应用容器看不到 root secret，并继续只用
`config/config.yml` 中的 application database credential。MySQL 不发布任何宿主端口，只能
由 Compose 内部网络上的 app 访问。

应用日志保存在 Compose named volume `log_data`，而不是宿主 bind mount；该卷从镜像中继承
仅供非 root `appuser` 写入的目录权限，容器重启后日志仍保留。如需查看日志，使用 Docker
提供的容器/volume 工具，不要对 `/app` 或下载目录做递归 `chown`。

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
