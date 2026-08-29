# 配置与凭据安全

## 当前边界

- `config/config.yml` 是唯一持久运行时配置源。
- 真实配置被 Git 和 Docker 构建上下文排除，不得提交或复制到镜像。
- 应用容器只读挂载该文件到 `/run/secrets/config.yml`，不接收配置型环境变量。
- 容器入口以 root 校验配置并复制到可写层 `/app/config/config.yml`，设置为
  `appuser` 所有、权限 `0600` 后，通过 `initgroups/setgid/setuid` 降权执行服务。
- Docker Compose 必需的端口和 MySQL 初始化变量由 `run-docker.sh` 临时派生；
  临时文件权限为 `0600`，并在命令退出时删除。
- 缺失或非法配置会阻止本地与容器启动，错误只说明配置无效，不回显配置值。
- `download.test_mode` 不是安全隔离开关：它只跳过直播流数据传输，仍会访问平台网络接口
  和已启用的数据库。
- Alembic 不使用包含凭据的 `alembic.ini` 或 `sqlalchemy.url`；迁移 Engine 仅从统一 YAML
  在进程内构造，CLI 输出不会显示完整 URL 或密码。
- 服务启动只执行只读版本/schema 检查，不自动 `upgrade`、`stamp`、建表或删表。

## 初始化

```bash
mkdir -p config
cp docs/design/config.yml.example config/config.yml
chmod 600 config/config.yml
```

填写真实值后，本地使用 `sh ./run-server.sh`，容器使用
`./run-docker.sh up -d`。不要创建 `.env` 作为第二份配置。

## 凭据处理

- 使用最小权限的数据库账号。
- 定期轮换数据库密码、Cookie、Token 等凭据。
- 不在日志、测试 fixture、Issue、聊天记录或截图中粘贴真实值。
- `docs/design/config.yml.example` 只能保留脱敏占位符。

## 迁移安全

- 已有数据库必须先执行只读 `check`；只有严格兼容且尚未版本化时，`stamp` 才会写版本表。
- `upgrade`、`downgrade` 和生成的 revision 必须人工审查；任何可能删除或改写数据的迁移前
  必须完成可恢复备份。未版本化但已有受管表的数据库禁止直接 `upgrade`；非临时库降级
  必须用实际库名确认。任何会执行基线 downgrade 的目标（含 `base`、`-1` 等等价形式）
  只允许显式 override 且严格命名的临时迁移测试库，配置库名不能自动获得临时库身份。
- 真实 MySQL 集成测试只能创建匹配
  `^smsd_migration_test_[0-9a-f]{12}$` 的随机数据库，且在 `finally` 中删除；正式数据库名
  不能进入测试库删除逻辑。
- 非受管表只报告 warning，Alembic 自动生成、升级和降级均不得删除它们。

## 文件系统信任边界（媒体资产发现）

Library 列表回答的是「数据库记录了什么」；资产端点回答的是「磁盘上现在还有什么」。
这是两个不同的事实，允许同时成立且互相不一致——一条 `saved_count = 3 / 3` 的记录，
今天目录可能已经空了，两句话都仍然正确。

- **配置是唯一根**。可访问的文件根只有 `$.download.save_path`，读取时解析而非启动时固化。
  容器里的 `/app/downloads` 只是当前部署映射，不是权威；宿主机部署可以合法指向别处。
- **授权先于文件系统**。请求链固定为：认证 → 按角色/归属的精确数据库查询 → 只有查到行
  才触碰磁盘。跨用户请求在查询阶段就返回 404，解析器根本不会被调用，因此无法用来探测
  主机上存在哪些路径。该不变量由测试直接断言。
- **包含关系按路径段判断**，不是字符串前缀：`/x/downloads-evil` 不在 `/x/downloads` 之内，
  尽管 `startswith` 会说是。
- **符号链接不产出资产**。目录符号链接逃出根、路径中间的符号链接、以及作为媒体条目的
  符号链接，一律拒绝；录制的 `output_path` 本身是符号链接时视为 `unavailable`。
- **不递归、有上限**。作品目录只扫描直接子项，且有明确条目上限；超过即 `unavailable`，
  不会为一个被塞入大量条目的目录持续读取。
- **不回传路径**。响应只有 `asset_id`、`kind`、`name`、`size_bytes`、`media_type`
  （图片附 `image_index`）。`save_dir`、`output_path`、绝对路径、文件系统根都不出现，
  ADMIN 也一样——更宽的数据范围不等于可以了解宿主机目录结构。
- **`asset_id` 不是授权凭证**。它由资源身份与文件名确定性派生，不落库。后续阶段即使拿到
  它，也必须重新认证、重新授权父资源、重新发现资产并比对，才可能提供内容；仅凭
  `asset_id` 直接打开文件是被明确禁止的。
- **内部原因不外泄**。越界、符号链接、权限错误、路径无效全部收敛为 `unavailable`；
  具体分类只留在服务端日志，且不打印用户不可见的敏感路径。

## 二进制交付边界（授权媒体下载）

发现阶段只回答问题，答错了下一次再问；交付阶段要送出字节，而**发现与打开是两个时刻**，
两者之间的一切都是别人的机会窗口：

    发现 → ［文件被删除并替换为符号链接］ → 打开

路径只是一句关于文件系统的话，每次使用都会被重新解释。`open(已发现的路径)` 会重走每一段，
把发现阶段所有检查在最需要的一刻丢弃——这正是媒体交付禁止 `send_file(path)` 的原因。

每一次下载请求都必须完整走完：

    认证
      → 对**父资源**做按角色/归属的精确数据库查询
        → 只有查到行，才触碰磁盘
          → **重新发现**当前磁盘上有什么
            → 用请求的 `asset_id` 比对**这一次**的发现结果
              → 从配置根逐级安全打开，拒绝任何符号链接
                → 对真正打开的 fd 做 `fstat`
                  → 流式送出这个已打开的文件

- **`asset_id` 不是 capability**。父资源身份始终出现在 URL 中；不存在
  `/api/files/<asset_id>` 这类仅凭 id 授权的路由。某个 post 的 id 用在另一个 post 上必然
  404，即使文件名完全相同。
- **不缓存、不兑换**。没有 `asset_id → path` 映射，没有下载票据、签名 URL、临时令牌，
  也没有任何资产路径表或内存索引。元数据接口返回的列表是对某个已经过去的时刻的描述，
  绝不能被「兑换」成一次下载。
- **逐级 dirfd 遍历**。从规范化的配置根开始，每一级目录以 `O_DIRECTORY | O_NOFOLLOW`
  相对上一级 fd 打开，最终文件以 `O_RDONLY | O_NOFOLLOW | O_NONBLOCK` 打开（可用时附
  `O_CLOEXEC`）。只保护最后一段是不够的：发现之后，任何中间目录都可能被换成符号链接。
  fd 命名的是**当时真正打开的那个目录**，而不是一个事后可以改指向的名字。
- **打开后再验证类型**。对已打开的 fd 执行 `fstat` 并要求 `S_ISREG`；目录、FIFO、套接字、
  设备一律拒绝。非阻塞打开确保放在媒体位置上的 FIFO 不会把 worker 永久挂住。
- **平台不支持则 fail closed**。若 `O_NOFOLLOW`、`O_DIRECTORY`、`dir_fd` 任一不可用，
  二进制交付返回 503，绝不退化为普通 `open()`；元数据发现不受影响，继续工作。
- **送出的是已打开的文件对象**，不是路径。`send_file(已打开对象)` 写出的是已被证明的
  描述符；`send_file(path)` 会按名字重新打开，正是这个边界要消除的竞态。
- **不整体读入内存**。响应为 WSGI file wrapper 流式输出，Python 侧内存占用与媒体大小无关。
  一次录制可能有几十 GB。
- **`Content-Length` 来自打开后的 `fstat`**，不采用发现阶段的旧 size：文件可能在两者之间
  增长，长度必须描述真正要送出的字节。
- **一律 attachment**。包括图片在内，全部 `Content-Disposition: attachment`，本阶段没有
  inline 预览、播放器、缩略图。文件名交由框架生成（含中文的 RFC 5987 形式与转义），
  不手工拼接 header。
- **`Cache-Control: private, no-store` 与 `X-Content-Type-Options: nosniff`**，
  避免任何共享缓存保存用户私有媒体。
- **单一 byte range（Phase 10C）**。支持 `Range: bytes=...` 的**一个** range，返回 206 与
  `Content-Range`；`Accept-Ranges: bytes` 在 200 / 206 / 416 / HEAD 上一致给出。
  目的只有一个：大文件下载中断后可以续传，不是播放。
  - **Range 发生在边界之后**。解析所用的 complete length 来自 secure-open 后对 fd 的
    `fstat`，不是元数据里记住的旧 size，也不是打开之前的任何猜测。Range header 只改变
    「送哪些字节」，不改变认证、授权、重新发现、或是否触碰文件系统。
  - **不满足的 range** 返回 416 并带 `Content-Range: bytes */<length>`，让客户端能自行纠正。
  - **multi-range 不实现**。`bytes=0-1,5-6` 不返回 multipart/byteranges，而是返回完整 200；
    畸形 header、非 `bytes` 单位同样忽略 Range 返回 200——GET 永远可以用完整表示回答。
  - **suffix range 按 RFC 9110 §14.1.2 归一化**。Werkzeug 只做语法解析，它的
    `range_for_length()` 是工具而不是本服务的 contract：它拒绝「suffix 长于表示」并接受
    「suffix 为 0」，与 RFC 恰好相反。解析成功之后有一层**很窄的归一化**：
    - `bytes=-3`（size=10）→ `206 bytes 7-9/10`
    - `bytes=-5000`（size=10）→ `206 bytes 0-9/10`，整个表示（§14.1.2：表示短于
      suffix-length 时使用整个表示）
    - `bytes=-0` → `416 bytes */10`（suffix-length 为 0 时不可满足）
    - `bytes=0-100`（size=10）→ `206 bytes 0-9/10`，clamp 行为保持不变
    注意 `bytes=-0` 与 `bytes=0-` 解析后同为 `(0, None)`——整数零上的符号已经消失——
    两者语义相反，因此**后缀形式由 header 文本判断**（是否以 `-` 开头），这是唯一
    需要看原始文本的地方，其余语法仍全部由 Werkzeug 负责。
  - **零长度表示忽略 Range**。size=0 时任何 Range 都返回普通 `200`、`Content-Length: 0`、
    空 body（§14.2 允许在所选表示没有内容时忽略 Range）。不构造不存在的零长度
    `Content-Range`。
- **representation validator（ETag）**。强 ETag，来自 secure-open 之后对 fd 的 `fstat`：
  `st_dev / st_ino / st_size / st_mtime_ns / st_ctime_ns` 的 SHA-256 摘要。
  - **不是内容摘要**。不读取媒体内容计算 hash——一次录制可能几十 GB。
  - **不是 `asset_id`**。`asset_id` 由资源身份与文件名派生，文件被同名替换时**不会变化**；
    用它做续传校验会把新文件的尾部接到旧文件的头部，产生无人察觉的损坏文件。
  - **不是凭证**。知道 ETag 不扩大任何授权；每个请求仍完整重新认证、授权、发现、打开。
  - 字段本身（inode、设备号）绝不出现在响应中，只有不可逆摘要离开服务端。
  - **validator strength window 内不发布 ETag**。文件系统的时间戳只有有限精度
    （本机 xfs 约 1–2ms，其他文件系统可能只有 1 秒）。同一个 tick 内的两次写入事后
    无法区分，因此「刚被写过」的表示可能在内容不同的情况下给出相同 tuple。
    - 没有 `W/` 前缀的 ETag 在 HTTP 语义上**就是 strong validator**；RFC 9110 §8.8.1
      要求生成机制无法满足 strong 特征时服务器必须如实标记。因此
      `st_mtime_ns` 距当前时间不足 1 秒的表示**根本不发送 `ETag` header**，
      而不是发送一个看起来 strong 的 tag 再在服务端私下拒绝它——那会让 header
      声称一个背后机制并不提供的保证，而客户端有权用它构造 `If-Range`。
    - 选择「不发送」而不是 `W/"..."`：weak tag 同样无法满足 `If-Range`
      （§13.1.3 要求 strong comparison），只会多出一种状态；而这些响应本就是
      `no-store`，没有缓存需要 weak validator。
    - 结果契约：
      - settled representation → `ETag: "<strong-tag>"`，匹配的 `If-Range` → `206`
      - recent / 可能仍在变化的 representation → 无 `ETag`，任何 `If-Range` 都无法
        validate → 忽略 Range → 完整 `200`
    - 不受影响的部分：完整下载正常；不带 `If-Range` 的普通 Range 请求仍返回 `206`。
    方向是保守的：代价是重传一次文件，反面是静默产生损坏文件（RFC 9110 §8.8.2.2
    对 last-modified 给出的是同样的理由）。正在写入的录制文件正属于此类；
    已经写完一段时间的文件不受影响，续传正常工作。
- **If-Range 续传安全**。仅当服务器为当前 representation 发布了 strong ETag、
  且 `If-Range` 与之相同才返回 206；
  不同则返回**当前表示的完整 200**，绝不返回新文件的尾部。日期形式的 `If-Range` 一律
  忽略 Range 返回 200——mtime 只有秒级精度，无法区分「刚读完就被替换」的文件，
  而那正是会破坏续传的情形。没有 `Range` 时 `If-Range` 被忽略。
- **不扩展为通用条件请求**。本阶段不实现 `If-None-Match` → 304、`If-Match`、
  `If-Modified-Since`。ETag 仅作为 `If-Range` 的 representation validator。
  `Cache-Control` 仍为 `private, no-store`，不因引入 ETag 而变成可共享缓存。
- **206 的字节上限是硬约束**。分片响应交给受限 iterator，不是 file object：
  交给 WSGI 的 file wrapper 若能拿到 `fileno`，可能走 `sendfile` 直接把描述符拷贝到 socket，
  绕过一切 Python 层限制并把窗口之后的内容继续发出。该 iterator **不暴露 `fileno`，也不暴露
  `read`**，且每次最多读取 `min(chunk, remaining)`，读完即停。已有「请求 10 字节、响应恰好
  10 字节」的测试固定。
- **HEAD 忽略 Range**。Range 语义定义在 GET；HEAD 描述整个表示，返回完整
  `Content-Length`、`Accept-Ranges`、ETag，body 为空。HEAD 与 GET 走完全相同的认证与授权，
  不能成为 existence oracle。
- **描述符生命周期覆盖所有分支**。200、206、If-Range 不匹配的 200、HEAD 都会释放；
  416 因为不会发送任何字节，**立即关闭**而不是等到响应结束；分片流在正常结束、
  被提前放弃、以及读取异常时都会关闭。
- **描述符生命周期**。响应结束、客户端中断、异常，都通过 `call_on_close` 释放文件；
  遍历过程中的中间目录 fd 用完即关，异常路径亦然，长期运行的进程不会逐次累积。
- **失败一律 JSON，且统一措辞**。id 不存在、id 属于别的资源、文件已删除、已变成符号链接、
  越界——对浏览器都是同一个 404；差异会描述本机文件系统的形状。
- **URL 中没有凭据**。同源 `<a href>` 由浏览器携带 HttpOnly session cookie 完成下载；
  不放 token、csrf、session、user_id、role。下载是读操作，因此 CSRF EXEMPT。
- **前端不接收媒体字节**。不使用 `fetch(...).blob()`、`createObjectURL`；由浏览器原生下载
  处理大文件。代价是文件在点击瞬间消失时，错误由浏览器原生下载提示呈现，而非应用内 UX——
  本阶段接受该限制，不为此改用 Blob 抓取。

## 授权预览边界（Authorized Media Preview）

Preview 与 Download 是**同一批字节、同一套授权**，区别只在浏览器拿到之后做什么：
download 是保存（`attachment`，惰性），preview 是渲染（inline，浏览器会解释它）。
**解释**正是风险所在，因此 preview 比 download 多一道更窄的门。

- **不是 public media server**。每一次 preview（含 Range GET 与 HEAD）都完整重走：
  认证 → 父资源精确 scoped 查询 → 才触碰文件系统 → 重新发现 → 与当前 asset_id 比对 →
  root-relative no-follow 安全打开 → `fstat` → 交付。
  匿名 401、跨用户 404、auth 不可用 503，且**文件系统调用为 0**，与 download 同样由测试断言。
- **独立 endpoint，不是 download 的开关**。
  `GET .../assets/<asset_id>/preview`，不使用 `?inline=1` 之类参数。
  「渲染还是保存」是服务端的决定；query 参数会把这个决定交给写 URL 的人。
  delivery mode 只能由 route call-site 常量给出，客户端无法影响 `Content-Disposition`。
- **closed MIME allowlist**，由 `preview_kind_for()` 单一权威给出：
  - `image/jpeg` → `image`（原生 `<img>`）
  - `video/mp4` → `video`（原生 `<video src>`）
  - `audio/mpeg` → `audio`（原生 `<audio src>`）
  - `video/x-flv` → `flv`（浏览器内 transmux，见下节）
  - 其他一律 `None`
  精确匹配，不做前缀规则。任何形如「image/ 开头即安全」的规则都会放进
  `image/svg+xml`——那是可以携带脚本的文档。`text/html`、`application/pdf`、
  `application/javascript`、`application/xml` 等**永不**可预览。
  metadata 的 `preview_kind` 与 preview endpoint 的准入使用**同一个** helper，
  不存在两份将来会漂移的清单。
- **TS 只能下载**。`video/mp2t` 的 `preview_kind` 为 `null`，preview endpoint 返回 `415`；
  UI 不显示预览按钮（也不显示灰掉的按钮——那会让「本来就只能下载」看起来像故障）。
  理由是 upstream 对**静态 .ts 文件的 seek 仍有限制**：能播到一半、一拖进度条就失效，
  比不提供预览更糟。不引入 HLS.js、不做服务端转码。

## FLV 录制预览（Phase 10E）

Douyin 直播录制的主路径是 **FLV 优先、HLS 兜底**
（`get_live_stream_source()` 先试 FLV，失败才回落 HLS）。因此磁盘上大量录制是 `.flv`，
在 10E 之前只能下载、无法在库内查看。

- **浏览器内 transmux，不是服务端转码**。使用 npm 依赖 **mpegts.js**（Apache-2.0，
  版本在 `package.json` / `package-lock.json` 中精确锁定），在浏览器里把 FLV 解复用后
  经 Media Source Extensions 播放。
  - **没有**服务端 ffmpeg 转码、remux、临时文件、转换缓存或转换任务
  - **没有**新增 endpoint：字节仍来自同一个已授权的 `/preview` 路由
  - **没有**改变录制格式或协议选择
- **`flv` 是独立的 preview kind，不是 `video`**。原生 `<video src>` 无法解码 FLV，
  映射成 `video` 只会得到一个必然失败的元素。独立 kind 才能让前端把这些字节交给 transmuxer。
- **安全链完全未变**：认证 → 父资源精确授权 → 重新发现 → 当前 asset_id 比对 →
  root-relative no-follow 安全打开 → `fstat` → MIME 准入 → Phase 10C 的 Range/If-Range/ETag 传输。
  FLV 没有第二套 Range 实现；它的 seek 用的就是既有的 206。
- **第三方解析器的边界**。这引入了一个**浏览器侧的第三方媒体解析器**。它只能拿到
  **已经通过完整授权**的 `video/x-flv` 字节；它不能选择服务端路径、不能扩大用户范围、
  不能生成公开 URL、也无法访问其他用户的 asset。它拿到的 URL 由前端用
  parent identity + asset_id 构造，与 download 完全一致。
- **同源、带凭据**。`cors: false`、`withCredentials: true`，URL 是同源相对路径。
  **没有**新增 `Access-Control-Allow-Origin`、`Access-Control-Allow-Credentials`、
  `Access-Control-Expose-Headers`，也没有新增 `OPTIONS` 预检路由——
  同源请求不需要这些，加了只会扩大可读范围。响应仍是
  `Cross-Origin-Resource-Policy: same-origin`。
- **按需加载**。mpegts.js 通过 `await import('mpegts.js')` 动态引入，构建后是独立 lazy chunk；
  只有用户点击某个 FLV 的「预览」时浏览器才会请求它。只看图片和 MP4 的用户不为其付费。
- **不自动播放**。只 `attachMediaElement()` + `load()`，**不调用 `play()`**；
  `isLive: false`（这是已经落盘的录制，不是直播流），不启用 `liveSync` /
  `liveBufferLatencyChasing`，`seekType: 'range'`。
- **不传入过期的 filesize / 编造的 duration**。metadata 里的 `size_bytes` 是发现时刻的值，
  而 preview endpoint 会在安全打开后 `fstat` 得到更可信的长度；duration 数据库里并不存在，
  用 `started_at`/`finished_at` 推算等于喂给播放器一个它会当真的数字。两者都不传。
- **生命周期与竞态**。同一时刻只允许一个 player；关闭预览、切换 asset、切换资源、
  刷新文件列表、组件卸载、player 报错，都会 `unload → detachMediaElement → destroy`。
  动态 import 是异步的，因此有 **generation 令牌**：模块加载期间用户若关闭或切换，
  import 落地后**不会**创建一个已经过期的 player（该保护有 mutation 验证的回归测试）。
- **失败一律收敛为同一句话**。`mpegts.Events.ERROR`（网络、demux、容器内 codec 不受支持，
  例如 FLV 里封装 H.265）、`isSupported()` 为 false、创建抛错，全部显示
  「预览失败，可尝试下载文件。」——不显示 codec、网络细节或解析器内部信息，下载始终可用。
- **应用代码仍不接收媒体字节**：不使用 `fetch().blob()`、`createObjectURL`。
  mpegts.js 内部使用 MediaSource 与 object URL 属于其实现细节，不等于项目代码违反该约束。
- **415 之前必须先 404**。asset_id 不存在、属于其他资源、文件已删除，一律 `404`；
  只有当前 rediscovery 匹配成功之后，才轮到「这个类型能不能渲染」的问题。
  否则 `415` 会反过来确认这个 id 是真实存在的。
- **preview 响应头**：
  - 不发送 `Content-Disposition`（`<img>`/`<video>`/`<audio>` 不需要文件名，
    省掉一处 Unicode 文件名编码面）
  - `Content-Type` 只能来自服务端认定的 `media_type`，不接受任何客户端提供的 MIME
  - `X-Content-Type-Options: nosniff`——在这里是承重的：即使 `.jpg` 里不是 JPEG，
    浏览器也不得把它重新解释为 HTML 在本 origin 上执行
  - `Cross-Origin-Resource-Policy: same-origin`——私有媒体只允许本 origin 作为子资源使用，
    否则其他站点可以按 URL 嵌入已登录用户的视频，并从加载时序与尺寸推断信息
  - `Cache-Control: private, no-store` 不变
- **Range 传输完全复用 Phase 10C**，不存在第二套实现：200 / 206 / 416 / `Accept-Ranges` /
  `Content-Range` / suffix 归一化 / zero-size 忽略 Range / strong ETag window /
  `If-Range` / bounded iterator 的字节上限 / 描述符生命周期，全部与 download 共享。
  415 由于不会发送任何字节，**立即关闭**描述符。
- **前端不接收媒体字节**。`<img>` / `<video>` / `<audio>` 直接指向 endpoint，
  不使用 `fetch().blob()`、不使用 `createObjectURL`；大文件由浏览器自己流式获取与 seek。
  **不设置 `crossorigin`**——预览资源本来就是同源的，该属性只会把元素切换为 CORS fetch，
  没有任何收益。（它并不会去掉同源凭据：`anonymous` 对同源请求仍然发送 same-origin credentials。
  不设置的理由是「不适用」，而不是「会丢 cookie」。）
- **按需、且一次一个**。打开详情面板只读取 metadata，绝不自动请求媒体；
  用户点击「预览」后才插入媒体元素。同时最多一个 asset 处于预览状态；
  切换资源、刷新文件状态、以及该 asset 从列表中消失，都会立即关闭预览
  （刷新之后同一个 asset_id 可能对应不同的字节）。
- **不 autoplay、不 loop**，`preload="metadata"`：打开预览的代价是一次 header，不是一个文件。
- **URL 中没有凭据**，也没有 preview token / signed URL / 临时票据；
  metadata 不返回 `preview_url`，前端由 parent identity + asset_id 纯函数构造，与 download 一致。
- **本阶段不引入全站 CSP**。当前项目没有 CSP，为 preview 顺手建立全站策略影响面过大，
  应作为独立的 hardening 阶段处理。preview 的边界由
  closed MIME allowlist + `nosniff` + CORP same-origin + 授权 + secure-open 共同建立。

## 历史凭据

防止当前配置进入新镜像不等于撤销历史泄露。Git 历史中曾出现过的凭据应由维护者
在外部完成轮换；如需历史重写，必须单独协调所有协作者，本次配置迁移不执行该操作。
