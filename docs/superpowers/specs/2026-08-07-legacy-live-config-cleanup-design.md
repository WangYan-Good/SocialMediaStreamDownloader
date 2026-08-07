# Live 旧配置清理设计

## 目标

删除已经不再被 Live Download 链路消费、且没有其他代码引用的旧配置或响应样本，避免统一 YAML 与旧文件并存造成误导。

## 删除范围

- `config/douyin/live.yml`：Live Download 已改为读取 `config/config.yml` 中的 `platform.douyin.live`。
- `config/douyin/live_response.yml`：旧直播响应样本，不属于运行配置，当前没有代码引用。
- `config/user_config.yml`：旧覆盖配置，当前没有代码引用，有效字段已经进入统一配置。

## 保留范围

- `config/config.yml`：唯一运行配置源。
- `docs/design/config.yml.example`：统一配置的脱敏示例。
- `config/douyin/conf.ini`：直播和作品分享链接列表，仍由运行链路读取。
- `config/base_config.yml`、`config/douyin/download.yml`、`headers.yml`、`login.yml`、`post.yml` 和 `api.yml`：作品下载或日志等尚未迁移的消费端仍在引用，本批不删除、不迁移。

## 代码与数据流

本批不改变 Live Download 的配置加载和消费逻辑。删除后仍保持：

```text
config/config.yml
  -> platform.douyin.live
  -> DouyinLiveConfig
  -> DouyinLiveDownloader
```

分享链接列表继续通过统一配置中的 `share_url_file` 定位 `config/douyin/conf.ini`。

## 验证

1. 增加测试，确认三个冗余文件不存在。
2. 确认 Live Download 相关运行代码不引用三个被删除文件。
3. 运行配置加载、统一配置结构和 Live Download 聚焦回归测试。
4. 运行 `git diff --check`，确认删除没有引入格式问题。

## 非目标

- 不迁移作品下载、日志或其他消费端。
- 不删除仍被引用的旧配置。
- 不修改数据库、下载协议或消费逻辑。
