# ============================================
# 多阶段构建 - 优化镜像大小和性能
# ============================================

# ---------- 阶段1: 构建依赖 ----------
FROM python:3.12.14-slim-trixie@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea AS builder

# 设置工作目录
WORKDIR /build

# 复制依赖文件
COPY requirements.txt .

# 所有依赖都有 wheel；无需漂移的编译工具链。基础镜像自带的 pip 是固定输入。
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --require-hashes -r requirements.txt

# ---------- 阶段1b: 构建前端 ----------
#
# Node 24, matching frontend/app/package.json engines and the CI workflow.  One
# major across all three on purpose: a lockfile resolved under one runtime and
# installed under another is how a build passes locally and fails in the image.
#
FROM node:24.20.0-bookworm-slim@sha256:ba849c60be29959425b8734d57b8b4b7d56f98edd9504c9af091d5281095a71e AS frontend-builder

WORKDIR /frontend

# 先复制依赖清单，让 npm 层可以被缓存：源码改动不应触发重新安装依赖
COPY frontend/app/package.json frontend/app/package-lock.json ./

# npm ci 而非 npm install：严格按 lock 安装，不允许解析出新版本
RUN npm ci --no-audit --no-fund

# 依赖就位后再复制源码，构建产物落在 /frontend/dist
COPY frontend/app/ ./
RUN npm run build

# ---------- 阶段2: 运行环境 ----------
FROM python:3.12.14-slim-trixie@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea AS runtime

ARG SOURCE_COMMIT=unknown
ARG SOURCE_TREE=unknown
ARG SOURCE_URL=unknown
ARG REQUIREMENTS_SHA256=unknown

# 镜像元数据
LABEL maintainer="wangyan" \
      description="SocialMediaStreamDownloader" \
      version="1.0" \
      org.opencontainers.image.revision="$SOURCE_COMMIT" \
      org.opencontainers.image.source="$SOURCE_URL" \
      io.smsd.source.tree="$SOURCE_TREE" \
      io.smsd.requirements.sha256="$REQUIREMENTS_SHA256"

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    VIRTUAL_ENV="/opt/venv"

# 固定 Debian snapshot 与直接 apt 版本；禁止 live mirror fallback。
COPY docker/debian-snapshot.sources /etc/apt/sources.list.d/debian.sources
COPY docker/apt-snapshot.conf /etc/apt/apt.conf.d/99snapshot
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg=7:7.1.5-0+deb13u1 \
    curl=8.14.1-2+deb13u4 \
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

# Named volumes inherit these ownership/mode bits on first mount. Keep the
# preparation explicit and narrow: never recursively chown application or
# captured-media trees during startup.
RUN install -d -o appuser -g appuser -m 0750 \
    /app/logs \
    /app/downloads \
    /app/config/build \
    /app/config/export

# 入口仅以 root 复制只读挂载的配置，随后立即降权执行应用
USER root

# 启动命令；runtime_config 使用 initgroups/setgid/setuid 后 exec server
ENTRYPOINT ["python", "./scripts/runtime_config.py", "container-entrypoint", "/run/secrets/config.yml", "appuser"]
CMD ["python", "./server.py"]
