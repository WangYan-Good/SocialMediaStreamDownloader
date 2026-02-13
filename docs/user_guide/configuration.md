# 用户配置指南

## 基本配置

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

## 平台配置

### 添加新平台支持

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