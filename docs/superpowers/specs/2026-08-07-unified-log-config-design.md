# 统一 YAML 日志配置迁移设计

## 目标

将 `LoggerManager` 从 `config/base_config.yml` 迁移到统一配置 `config/config.yml` 的 `log` section，消除日志链对 `DEFAULT_BASE_CONFIG_PATH` 的运行时依赖。

本批只迁移日志配置，不修改作品下载及其他仍依赖旧配置的消费端。

## 配置线路

```text
config/config.yml
  -> BaseConfig
  -> log section
  -> LoggerManager
  -> console/file handlers
```

`LoggerManager()` 无参数构造时，从 `BaseConfig().get_config()` 取得 `log` section。构造器也接受一个日志配置字典，用于依赖注入和隔离测试。单例首次初始化后继续保持现有的一次性初始化语义。

## 字段行为

- `log_enable`：为 `false` 时禁用由管理器创建的 Logger。
- `log_level`：设置默认 Logger、控制台 Handler 和默认文件 Handler 的级别；只接受 Python logging 支持的标准级别名称。
- `log_save`：为 `true` 时创建轮转文件 Handler；为 `false` 时不创建日志目录和默认文件 Handler。
- `log_file_path`：默认日志文件的完整路径。启用文件日志时创建其父目录，并直接使用该文件路径，不再拼接旧的固定文件名。

## 公共接口

保持以下接口名称和调用方式不变：

- `register_logger()`
- `get_logger()`
- `set_logger_file_handler()`
- `set_logger_console_handler()`

`register_logger()` 创建的 Logger 同样遵循全局 `log_enable`。显式添加文件 Handler 时仍使用统一配置文件路径的父目录作为默认目录，保持原有相对文件名行为。

## 校验与错误处理

- `log` 必须是映射。
- `log_enable` 和 `log_save` 必须是布尔值。
- `log_level` 必须是标准日志级别字符串。
- `log_save=true` 时，`log_file_path` 必须是非空字符串且具有文件名。
- 配置错误在 `LoggerManager` 初始化阶段明确抛出，不回退到 `base_config.yml`。
- 目录或文件 Handler 创建失败时保留异常原因并停止初始化，下一次构造仍可重试。

## 测试

测试使用临时目录和注入配置，不读取真实运行配置：

1. 配置的日志级别应用到默认 Logger 和 Handler。
2. `log_save=true` 创建父目录并使用配置的完整文件路径。
3. `log_save=false` 不创建目录或默认文件 Handler。
4. `log_enable=false` 禁用管理器创建的 Logger。
5. 缺失或类型错误的字段产生明确异常。
6. 日志模块不再导入或读取 `DEFAULT_BASE_CONFIG_PATH`。
7. 配置加载和 Live Download 聚焦回归保持通过。

## 非目标

- 不迁移 `DouyinConfig`、`DouyinPostConfig` 或 `DouyinPostDownloader`。
- 不删除 `config/base_config.yml` 或 `backend/src/base/default.py`。
- 不重新设计日志格式、轮转周期或现有公共 API。
