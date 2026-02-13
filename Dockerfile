FROM python:3.12-slim

LABEL maintainer="wangyan 16609932941@163.com"
LABEL description="SocialMediaStreamDownloader - A tool for downloading social media content"

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=server.py

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . .

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 创建非 root 用户
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# 创建日志目录
RUN mkdir -p logs

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "server.py"]