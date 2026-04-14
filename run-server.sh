#!/bin/bash

# ============================================
# SocialMediaStreamDownloader 启动脚本
# ============================================
# 功能：
# 1. 检查 Python 版本
# 2. 激活虚拟环境
# 3. 安装依赖
# 4. 检查配置文件
# 5. 检查端口占用
# 6. 防止重复启动
# 7. 启动服务并输出日志
# ============================================

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 项目根目录
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# ============================================
# 1. 检查 Python 版本
# ============================================
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
REQUIRED_VERSION="3.12"

if [[ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]]; then
    log_warn "Python 版本 $PYTHON_VERSION 低于要求版本 $REQUIRED_VERSION"
    log_warn "可能导致部分功能异常，建议升级 Python"
fi

log_info "Python 版本: $PYTHON_VERSION"

# ============================================
# 2. 激活虚拟环境
# ============================================
if [[ -n "$VIRTUAL_ENV" ]]; then
    log_info "已处于虚拟环境中: $VIRTUAL_ENV"
else
    if [[ ! -d "venv" ]]; then
        log_info "创建虚拟环境..."
        python3 -m venv venv
    fi

    log_info "激活虚拟环境..."
    source venv/bin/activate
    log_info "虚拟环境已激活: $VIRTUAL_ENV"
fi

# ============================================
# 3. 安装依赖（支持国内镜像源）
# ============================================
REQUIREMENTS_FILE="./requirements.txt"

# 国内镜像源列表（按优先级排序）
PIP_MIRRORS=(
    "https://pypi.tuna.tsinghua.edu.cn/simple/"
    "https://mirrors.aliyun.com/pypi/simple/"
    "https://pypi.mirrors.ustc.edu.cn/simple/"
    "https://mirrors.cloud.tencent.com/pypi/simple/"
    "https://pypi.org/simple/"
)

# 检测可用的镜像源
detect_pypi_mirror() {
    local timeout=3
    for mirror in "${PIP_MIRRORS[@]}"; do
        log_info "检测镜像源: $mirror"
        if curl -s -o /dev/null -w "%{http_code}" --connect-timeout "$timeout" "$mirror" | grep -q "200"; then
            echo "$mirror"
            return 0
        fi
    done
    return 1
}

if [[ -f "$REQUIREMENTS_FILE" ]]; then
    log_info "检查并安装依赖..."

    # 尝试检测镜像源
    MIRROR_URL=$(detect_pypi_mirror)

    if [[ -n "$MIRROR_URL" ]]; then
        log_info "使用镜像源: $MIRROR_URL"
        # 获取镜像源的主机名作为 trusted-host
        TRUSTED_HOST=$(echo "$MIRROR_URL" | sed -e 's|https\?://||' -e 's|/.*||')

        if pip install -q -r "$REQUIREMENTS_FILE" \
            -i "$MIRROR_URL" \
            --trusted-host "$TRUSTED_HOST" \
            --disable-pip-version-check; then
            log_info "依赖检查完成"
        else
            log_error "依赖安装失败，请检查网络或手动执行: pip install -r $REQUIREMENTS_FILE"
            exit 1
        fi
    else
        log_warn "所有镜像源均不可用，尝试使用默认源"
        if pip install -q -r "$REQUIREMENTS_FILE" --disable-pip-version-check; then
            log_info "依赖检查完成"
        else
            log_error "依赖安装失败，请检查网络连接"
            exit 1
        fi
    fi
else
    log_error "未找到 $REQUIREMENTS_FILE"
    exit 1
fi

# ============================================
# 4. 检查配置文件
# ============================================
if [[ ! -f ".env" ]]; then
    log_warn "未找到 .env 配置文件"
    log_warn "将从 .env.example 复制模板"
    if [[ -f ".env.example" ]]; then
        cp .env.example .env
        log_warn "已创建 .env，请编辑该文件填写实际配置"
        log_warn "按 Ctrl+C 取消启动，或等待 10 秒继续（使用默认配置可能失败）"
        sleep 10
    else
        log_error "未找到 .env.example 模板文件"
        exit 1
    fi
fi

# ============================================
# 5. 检查端口占用
# ============================================
SERVER_PORT=${SERVER_PORT:-5000}
if command -v lsof &> /dev/null; then
    if lsof -i ":$SERVER_PORT" &> /dev/null; then
        log_error "端口 $SERVER_PORT 已被占用"
        log_error "请关闭占用进程或修改 .env 中的 SERVER_PORT"
        exit 1
    fi
fi

# ============================================
# 6. 防止重复启动
# ============================================
PID_FILE="./.server.pid"
if [[ -f "$PID_FILE" ]]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        log_error "服务已在运行 (PID: $OLD_PID)"
        log_error "如需重启，请先执行: kill $OLD_PID"
        exit 1
    else
        log_warn "清理过期的 PID 文件"
        rm -f "$PID_FILE"
    fi
fi

# ============================================
# 7. 确保日志目录存在
# ============================================
LOG_DIR="./logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/smsd_boot.log"

# ============================================
# 8. 启动服务
# ============================================
log_info "启动服务..."
log_info "端口: $SERVER_PORT"
log_info "日志: $LOG_FILE"

nohup python3 ./server.py > "$LOG_FILE" 2>&1 &
SERVER_PID=$!

# 保存 PID
echo $SERVER_PID > "$PID_FILE"

# 等待服务启动
sleep 2

# 检查进程是否存活
if kill -0 $SERVER_PID 2>/dev/null; then
    log_info "服务启动成功 (PID: $SERVER_PID)"
    log_info "查看日志: tail -f $LOG_FILE"
    log_info "停止服务: kill $SERVER_PID"
else
    log_error "服务启动失败，请查看日志: $LOG_FILE"
    exit 1
fi
