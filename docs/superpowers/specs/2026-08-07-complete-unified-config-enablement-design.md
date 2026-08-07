# 完整启用统一配置设计

## 目标

将项目所有运行时持久配置统一切换到项目根目录的
`config/config.yml`，完成此前只覆盖配置加载、直播和日志的分批迁移。
迁移结束后，Server、Database、Logger、Download、Douyin API、Headers、
Login、Live 和 Post 均通过同一条配置线路构造，不再读取旧 YAML、配置型环境变量
或派生的配置文件路径。

本设计保持配置为只读输入，为后续按领域迁移到数据库保留清晰 section 边界；不实现
YAML 写回、热加载或数据库配置存储。

## 当前状态

已经完成：

- `BaseConfig` 从稳定的项目绝对路径加载 `config/config.yml`。
- `configlib.load_config()` 返回完整配置映射。
- Live 下载构造链消费统一配置。
- `DouyinApi()` 无参构造可读取统一 `api` section。
- `LoggerManager` 消费统一 `log` section。
- Database 参数在 Live 构造链中来自统一 `database` section。

尚未完成：

- Server 启动参数和错误响应 debug 行为仍读取环境变量。
- `Downloader`、`Login`、`DouyinConfig`、`DouyinPostConfig` 和
  `DouyinPostDownloader` 仍读取或派生旧配置文件路径。
- `Header`、`DouyinHeader`、`DouyinApi` 和 `Login` 仍保留路径输入或旧文件回退。
- `configlib.get_config()` 对字典使用 `getattr()`，无法按配置路径可靠读取。
- `configlib.set_config()` 和 `BaseConfig.update_config()` 是无调用的空实现。
- 生产运行链仍保留从 `conf.ini` 读取 URL 的构造依赖。

## 唯一配置源

持久配置的数据流固定为：

```text
config/config.yml
        ↓
BaseConfig（唯一文件读取、进程内单例缓存）
        ↓
configlib（完整配置和严格路径读取）
        ↓
Server / Database / Logger / Download / Douyin
        ↓
API / Headers / Login / Live / Post
```

约束如下：

- `config/config.yml` 是项目唯一持久配置源。
- 不读取旧 YAML，不在配置缺失时回退旧文件。
- `SERVER_HOST`、`SERVER_PORT`、`FLASK_DEBUG` 等环境变量不再覆盖 YAML。
- `msToken`、`verifyFp`、`a_bogus` 等运行时刷新值只修改消费对象自己的内存副本。
- 运行时对象不得把动态值写回 `config/config.yml`。
- 消费端只接收完整统一配置或自己负责的 section，不接收配置文件路径。

## 配置公共接口

保留两个只读入口：

```python
def load_config() -> dict:
  """返回进程内已经加载的完整配置。"""

def get_config(path: str):
  """严格读取 `$.server` 形式的配置路径。"""
```

`get_config()` 使用现有字典路径工具读取值。路径为空、路径不存在或中间节点类型错误时，
抛出包含完整路径的明确异常，不记录错误后返回 `None`。

删除无调用且没有真实行为的 `configlib.set_config()` 和
`BaseConfig.update_config()`。本轮不提供进程内更新、YAML 写回或热加载能力。

`BaseConfig` 只负责根映射加载、缓存和失败重试。领域字段由实际消费该 section 的对象
校验，避免在配置核心中复制全部业务知识。

## 消费端装配

### Server

Server 提供可测试的应用创建与启动参数解析边界。`host`、`port` 和 `debug_mode`
只来自 `server` section；错误响应是否包含 traceback 使用同一个 debug 值。
导入 Server 模块不得启动服务或依赖尚未创建的全局对象。

### Header、Login 和 API

- `Header(config: dict)` 深拷贝 Header section；移除 YAML 路径读取。
- `DouyinHeader` 及其 Share、Live、Post 子类只接收完整 Douyin Headers section。
- `Login(config: dict)` 深拷贝 Login section，并从其中构造代理配置。
- `DouyinLogin(config: dict)` 不再使用默认 `login.yml`。
- `DouyinApi(config: dict = None)` 无参时读取统一 `api` section；显式参数只接受映射。
- 上述对象缺少映射或必要子 section 时立即失败，不回退旧文件。

### Download、Live 和 Post

通用 `Downloader` 保留下载算法，只从注入的 `download` section 初始化下载策略；它不再
构造 Header、Login 或平台配置对象。

Live 保持当前完整配置注入方式，并继续把 `api`、`headers` 和 `login` section 分别传给
成员对象。Live 的现有网络和文件写入行为不在本次重新设计。

`DouyinPostConfig(config: dict = None)` 无参时加载完整统一配置，有参时使用注入配置。
它深拷贝并组合顶层 `download`、`platform.douyin.download` 和
`platform.douyin.post`，对外提供 Post 下载链现有需要的字段和运行时更新方法。
它不继承 `BaseConfig`，不读取或保存其他 YAML。

`DouyinPostDownloader(config: dict = None)` 使用同一份完整配置装配：

```text
DouyinPostConfig(full config)
DouyinPostInfoHeader(platform.douyin.headers)
DouyinLogin(platform.douyin.login)
DouyinApi(platform.douyin.api)
```

无参调用保持可用；测试通过显式字典注入隔离文件、网络和数据库。

旧 `DouyinConfig` 的多文件聚合职责被统一配置取代。确认没有独立运行时调用后删除
`douyin_config.py`，不保留转发旧路径的兼容空壳。

## URL 输入边界

生产 URL 的唯一输入来源是前端 Web 请求。现有已接通的 Live 数据流保持为：

```text
POST / -> PlatformDispatcher -> Douyin handler -> Live downloader token
```

从统一配置删除 `platform.douyin.download.share_url_file`。运行时构造不再创建
`UrlListConfig`，也不读取 `config/douyin/conf.ini`。

`conf.ini` 作为历史样例保留，仅允许测试代码显式读取作为 URL 输入 fixture；生产模块
不得导入、派生或默认引用它。

Post 配置和下载对象提供显式 token/URL 输入边界，但本轮不新增 Post URL 分类或 Web
路由。该限制防止配置迁移混入尚未设计的消费功能；它不允许 Post 回退读取 `conf.ini`。

## 校验与错误处理

- 配置根节点必须是映射。
- 必要顶层 section 为 `database`、`download`、`log`、`server`、`migrate` 和
  `platform.douyin`。
- Douyin 必要 section 为 `download`、`api`、`headers`、`login`、`post` 和 `live`。
- 每个消费端校验自己使用字段的存在性和类型，错误信息包含完整字段路径。
- 初始化错误停止对应对象构造，不使用旧 YAML、环境变量或硬编码配置继续运行。
- `BaseConfig` 首次加载失败后保持可重试；成功后在进程内只读取一次。
- `test_mode=true` 时 Live/Post 构造测试不得访问真实网络、数据库或写下载文件。

## 遗留文件处理

全部消费端迁移并通过依赖扫描后删除：

- `config/base_config.yml`
- `config/douyin/api.yml`
- `config/douyin/download.yml`
- `config/douyin/headers.yml`
- `config/douyin/login.yml`
- `config/douyin/post.yml`
- `backend/src/base/default.py`
- 无运行时用途的 `backend/src/platform/douyin/douyin_config.py`
- 只为旧文件输入服务的 `backend/src/platform/douyin/douyin_url_list_config.py`

保留：

- `config/douyin/conf.ini`，仅作为测试 URL fixture。
- `config/config.yml`，本地真实配置。
- `docs/design/config.yml.example`，结构一致且脱敏的公开示例。

## 分批实施

为控制改动范围，按以下顺序交付，每批独立执行 TDD 和审查：

1. 修正只读配置公共接口和 schema 校验。
2. 切换 Server 启动与 debug 行为。
3. 收敛 Header、Login、API 和通用 Downloader 的字典输入。
4. 切换 Douyin Post 配置与下载构造链。
5. 移除生产 `conf.ini` 输入依赖和旧 DouyinConfig 聚合层。
6. 删除遗留配置文件并执行全仓完成审计。

## 验收标准

完成必须同时满足：

1. `load_config()` 和严格路径读取接口有成功、缺失和类型错误测试。
2. Server 的 host、port、debug 和错误响应行为由注入的 `server` section 验证。
3. Live 与 Post 均能从同一份完整注入配置完成无副作用构造。
4. Header、Login 和 API 行为测试证明只消费字典，不读取旧文件。
5. Web 请求传入的 URL 能沿现有链路到达 Live 下载入口；Post 对象接收显式 token/URL；
   任何生产链都不读取 `conf.ini`。
6. `conf.ini` 只被测试代码引用。
7. 全仓运行时代码不包含旧 YAML 路径、`DEFAULT_BASE_CONFIG_PATH` 或配置型环境变量读取。
8. 遗留文件清单全部删除，统一示例不再包含 `share_url_file`。
9. 完整单元测试、配置 schema 测试、Python 编译和 diff 静态检查全部通过。

## 非目标

- 不实现配置热加载、YAML 写回或数据库配置表。
- 不新增前端 URL 输入协议；沿用当前 POST JSON `urls` 数组。
- 不新增 Post URL 分类或 Web 路由。
- 不重写 Live 网络协议、HLS/FLV 提取或下载算法。
- 不迁移 `f2` 子项目自身的配置系统。
- 不把直播响应、作品响应或下载结果写入统一配置。
