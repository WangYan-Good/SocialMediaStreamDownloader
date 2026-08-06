# 配置加载线路设计

## 目标

实现一条单一、可验证的配置加载线路：从项目根目录的 `config/config.yml` 读取 YAML，通过 `BaseConfig` 单例在进程内持有，并由 `configlib.load_config()` 返回完整配置字典。

## 范围

本次只实现配置加载，不修改任何消费端逻辑。

包含：

- 使用稳定的项目绝对路径定位 `config/config.yml`。
- 将配置文件解析为字典。
- `BaseConfig` 首次构造时加载配置，后续构造复用同一实例和配置。
- `BaseConfig.get_config()` 返回已加载的完整配置字典。
- `configlib.load_config()` 返回 `BaseConfig.get_config()` 的结果。
- 配置文件不存在、YAML 无法解析或根节点不是映射时，终止加载并抛出明确异常。

不包含：

- Flask 的 host、port、debug 配置切换。
- 日志配置切换。
- 配置更新、文件写回、热加载和数据库配置。
- 环境变量兼容或多配置源优先级。

## 数据流

```text
项目根目录/config/config.yml
          ↓
BaseConfig.__init_config()
          ↓
BaseConfig.__config（进程内单例状态）
          ↓
BaseConfig.get_config()
          ↓
configlib.load_config()
          ↓
完整配置 dict
```

## 接口行为

`BaseConfig()` 负责一次性初始化。加载成功后设置初始化标记；加载失败时不设置标记，使错误直接传递给调用方。

`BaseConfig.get_config()` 不触发额外读取，只返回单例已经持有的完整配置。

`configlib.load_config()` 是这条线路唯一的公共入口。它保留现有错误日志记录，并在成功时返回完整配置。

## 错误处理

底层文件读取或 YAML 解析异常统一包装为包含配置文件路径的 `RuntimeError`。如果 YAML 根节点不是字典，同样视为配置加载失败。异常继续向上传播，不提供默认配置或静默回退。

## 测试

聚焦测试通过临时 YAML 文件验证：

1. `configlib.load_config()` 能经过完整线路返回嵌套配置字典。
2. 非映射 YAML 会产生明确的加载异常。

测试只覆盖加载功能，不测试任何配置消费行为。
