# Docker 部署指南

## 概述

本项目提供了一个优化的 Docker 部署方案，用于快速部署 SocialMediaStreamDownloader 服务。

## 系统要求

- Docker Engine >= 20.10
- Docker Compose >= 2.0
- 至少 2GB 可用磁盘空间

## 快速部署

### 使用 Docker Compose (推荐)

```bash
# 启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 使用部署脚本

```bash
# 构建镜像并启动服务
./deploy-docker.sh build-and-start

# 查看服务状态
./deploy-docker.sh status

# 查看日志
./deploy-docker.sh logs

# 停止服务
./deploy-docker.sh stop

# 重启服务
./deploy-docker.sh restart

# 清理所有 (停止服务并删除容器和镜像)
./deploy-docker.sh remove-all
```

## 配置

### 端口映射

- 容器端口 5000 映射到主机端口 5000
- 如需修改，请编辑 `docker-compose.yml` 文件

### 数据卷映射

- `./downloads` → `/mnt/video` : 下载内容保存目录
- `./logs` → `/app/logs` : 日志文件目录  
- `./config` → `/app/config` : 配置文件目录

### 环境变量

- `SAVE_PATH` : 下载内容保存路径 (默认: /mnt/video)
- `LOG_PATH` : 日志保存路径 (默认: ./logs)

## 自定义配置

### 修改配置文件

在宿主机的 `./config` 目录中修改配置文件，这些更改会实时同步到容器中：

- `base_config.yml` : 基础配置
- `platforms.yml` : 平台配置

### 调整下载路径

修改 `docker-compose.yml` 中的卷映射：

```yaml
volumes:
  - /custom/download/path:/mnt/video  # 自定义下载目录
```

## 高级操作

### 构建自定义镜像

```bash
# 构建镜像
docker build -t social-media-downloader .

# 使用自定义标签
docker build -t social-media-downloader:latest .
```

### 运行自定义容器

```bash
docker run -d \
  --name social-media-downloader-custom \
  -p 5001:5000 \
  -v $(pwd)/downloads:/mnt/video \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/config:/app/config \
  -e SAVE_PATH=/mnt/video \
  social-media-downloader
```

## 故障排除

### 查看容器日志

```bash
docker logs social-media-downloader
```

### 进入容器调试

```bash
docker exec -it social-media-downloader /bin/bash
```

### 检查容器状态

```bash
docker ps
docker stats social-media-downloader
```

## 性能优化建议

1. **存储优化**: 使用 SSD 存储下载目录以提高下载速度
2. **内存分配**: 为 Docker 引擎分配至少 4GB 内存
3. **网络优化**: 确保网络连接稳定，避免下载中断

## 安全注意事项

1. **访问控制**: 限制对服务端口的访问，仅允许受信任的 IP 访问
2. **定期更新**: 定期更新 Docker 镜像以获取安全补丁
3. **权限管理**: 容器以非 root 用户运行，降低安全风险

## 更新服务

```bash
# 获取最新代码
git pull origin main

# 重新构建镜像
docker-compose build --no-cache

# 重启服务
docker-compose up -d
```

## 卸载

```bash
# 停止并删除容器
docker-compose down

# 删除镜像
docker rmi social-media-downloader

# 清理数据 (警告: 此操作不可逆)
rm -rf downloads logs config
```

## 支持

如遇到问题，请检查:

1. Docker 服务是否正常运行
2. 端口 5000 是否已被占用
3. 系统是否有足够磁盘空间
4. 防火墙设置是否允许相应端口通信

服务启动后，访问 `http://localhost:5000` 即可使用 SocialMediaStreamDownloader。