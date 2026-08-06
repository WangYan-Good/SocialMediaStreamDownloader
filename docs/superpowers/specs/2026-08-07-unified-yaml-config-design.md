# 单一 YAML 配置整合设计

## 目标

将项目的持久配置统一收敛到项目根目录的 `config/config.yml`，使它成为唯一配置源。统一后的层级结构既便于人工维护，也能在后续按领域迁移到数据库表或 JSON 配置记录。

本设计采用分批迁移。第一批只合并配置内容并验证结构，不切换任何消费端，不删除旧文件。

## 配置边界

纳入统一配置：

- 当前 `config/config.yml` 中的数据库、下载、日志、服务和迁移配置。
- `config/base_config.yml` 与 `config/user_config.yml` 中仍有效且未重复的下载配置。
- `config/douyin/api.yml` 中的 API 地址。
- `config/douyin/download.yml` 中的斗音下载策略。
- `config/douyin/headers.yml` 中的请求头模板。
- `config/douyin/login.yml` 中的登录、代理和凭据初始值。
- `config/douyin/post.yml` 中的作品请求参数默认值。
- `config/douyin/live.yml` 中的直播 API、清晰度和请求参数默认值。

不纳入统一配置：

- `config/douyin/live_response.yml`。它是直播响应样本，当前也不是合法 YAML 配置。
- 运行时生成或注入的 `stream_url`、`stream_name`、`post.share_url`、`post.nickname`、下载计数和直播响应内容。
- 程序可以根据项目根目录推导的 `*_config_path`、`build_path` 等路径。

`msToken`、`verifyFp` 和 `a_bogus` 可以作为初始配置保留；运行时刷新值只保存在内存中，本阶段不写回 YAML。

## 统一结构

```yaml
database:
  enable:
  name:
  host:
  port:
  username:
  password:

download:
  save_path:
  folderize:
  max_threads:
  max_retry:
  save_response:
  save_error_response:
  test_mode:
  listening:
  tick_naming:
  user_login:

log:
  log_enable:
  log_level:
  log_save:
  log_file_path:

server:
  host:
  port:
  debug_mode:

migrate:
  source_db_name:
  source_db_host:
  source_db_port:
  source_db_username:
  source_db_password:

platform:
  douyin:
    download:
      type:
      multiple_download:
      share_url_file:
    api:
    headers:
    login:
    post:
    live:
```

`api`、`headers`、`login`、`post` 和 `live` 保留各自旧 YAML 中的领域字段，但位于 `platform.douyin` 下。

## 字段归一化

重复字段只保留一份，并使用当前顶层命名：

| 旧字段 | 统一字段 |
| --- | --- |
| `max_thread` | `download.max_threads` |
| `login` | `download.user_login` |
| `debug` | `server.debug_mode` |
| `database_enable` | `database.enable` |
| `database_ip` | `database.host` |
| `database_name` | `database.name` |
| `database_user` | `database.username` |
| `database_password` | `database.password` |

`base_config.yml` 中的文件名和派生路径字段不进入新结构。斗音下载策略只保留业务字段；不再通过配置拼接其他 YAML 文件路径。

`live.yml` 中的 `MAX_TIMEOUT` 在统一结构中规范为 `max_timeout`。API 配置现有的大写键本阶段保持原名，避免在尚未切换消费端前混入无关重命名。

## 迁移批次

### 第一批：合并配置

- 将全部有效配置合并到本地 `config/config.yml`。
- 更新 `docs/design/config.yml.example`，提供相同的完整结构并使用脱敏示例值。
- 验证两个文件均为合法 YAML，且统一结构的必要 section 和字段完整。
- 保留所有旧 YAML，不修改任何消费端。

第一批完成后停止。

### 第二批：直播构造链

- `DouyinLiveConfig` 改为读取统一配置中的 section。
- 直播所需 API、Headers 和 Login 对象改为接收配置字典。
- 取消直播模块导入时自动实例化下载器，改为按调用延迟创建。
- `test_mode=true` 时不初始化数据库、不访问网络、不写视频。

### 第三批：直播网络链路

- 验证分享链接解析。
- 验证直播信息查询和流地址提取。
- 最后验证流文件写入。

### 第四批：剩余消费端

- 逐个切换作品下载等其他消费端。
- 所有消费端切换完成后删除旧 YAML。

## 第一批错误处理与验证

合并时任何源 YAML 解析失败都必须明确指出文件；`live_response.yml` 不参与解析。合并后的目标文件必须以映射为根节点。

第一批验证内容：

1. `config/config.yml` 能被现有 `load_config()` 加载。
2. `docs/design/config.yml.example` 能被 YAML 安全解析。
3. 两者都包含顶层 `database`、`download`、`log`、`server`、`migrate` 和 `platform.douyin`。
4. `platform.douyin` 包含 `download`、`api`、`headers`、`login`、`post` 和 `live`。
5. `platform.douyin.live` 不包含 `stream_url` 和 `stream_name`。
6. 旧 YAML 文件仍然存在，第一批没有消费端代码变更。
