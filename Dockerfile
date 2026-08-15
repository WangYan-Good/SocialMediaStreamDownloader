# ============================================
# 多阶段构建 - 优化镜像大小和性能
# ============================================

# ---------- 阶段1: 构建依赖 ----------
FROM python:3.12-slim AS builder

# 设置工作目录
WORKDIR /build

# 安装编译依赖（编译后删除）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 创建虚拟环境并安装依赖（使用 --no-cache-dir 减小体积）
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ---------- 阶段1b: 构建前端 ----------
#
# Node 24, matching frontend/app/package.json engines and the CI workflow.  One
# major across all three on purpose: a lockfile resolved under one runtime and
# installed under another is how a build passes locally and fails in the image.
#
FROM node:24-slim AS frontend-builder

WORKDIR /frontend

# 先复制依赖清单，让 npm 层可以被缓存：源码改动不应触发重新安装依赖
COPY frontend/app/package.json frontend/app/package-lock.json ./

# npm ci 而非 npm install：严格按 lock 安装，不允许解析出新版本
RUN npm ci --no-audit --no-fund

# 依赖就位后再复制源码，构建产物落在 /frontend/dist
COPY frontend/app/ ./
RUN npm run build

# ---------- 阶段2: 运行环境 ----------
FROM python:3.12-slim AS runtime

# 镜像元数据
LABEL maintainer="wangyan" \
      description="SocialMediaStreamDownloader" \
      version="1.0"

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    VIRTUAL_ENV="/opt/venv"

# 安装运行时依赖（仅 ffmpeg，其他依赖已在虚拟环境中）
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

# 设置工作目录
WORKDIR /app

# 复制项目文件；root 入口代码必须不可由 appuser 改写
COPY . .

# 前端产物来自 node 构建阶段，而不是宿主机
#
# 运行镜像里没有 Node/npm：Flask 只需要 dist 里的静态文件，把工具链留在
# builder 阶段是镜像体积和攻击面都更小的做法。
COPY --from=frontend-builder /frontend/dist ./frontend/app/dist

# 创建必要的目录
RUN mkdir -p /app/logs /app/downloads /app/config/build /app/config/export && \
    chown -R appuser:appuser /app/logs /app/downloads /app/config

# 入口仅以 root 复制只读挂载的配置，随后立即降权执行应用
USER root

# 启动命令；runtime_config 使用 initgroups/setgid/setuid 后 exec server
ENTRYPOINT ["python", "./scripts/runtime_config.py", "container-entrypoint", "/run/secrets/config.yml", "appuser"]
CMD ["python", "./server.py"]
