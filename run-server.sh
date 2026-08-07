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
# 7. 启动服务
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

if [[ "${1:-}" == "--check-config" ]]; then
    exec "${PYTHON_BIN:-python3}" \
        "$PROJECT_DIR/scripts/runtime_config.py" validate
fi

# 最低 Python 版本要求
REQUIRED_VERSION="3.12"

# 比较版本号，判断是否满足最小版本
version_ge() {
    [[ "$(printf '%s\n' "$1" "$2" | sort -V | head -n1)" == "$2" ]]
}

# 选择可用的 Python 解释器（优先 3.12）
select_python_cmd() {
    local candidates=("python3.12" "python3.13" "python3.14" "python3")
    local cmd ver
    for cmd in "${candidates[@]}"; do
        if command -v "$cmd" >/dev/null 2>&1; then
            ver=$($cmd -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
            if version_ge "$ver" "$REQUIRED_VERSION"; then
                echo "$cmd"
                return 0
            fi
        fi
    done
    return 1
}

# ============================================
# 1. 检查 Python 版本
# ============================================
if ! PYTHON_CMD=$(select_python_cmd); then
    log_error "未找到 Python $REQUIRED_VERSION 或更高版本"
    log_error "请先安装 Python 3.12+，例如: sudo dnf install python3.12 python3.12-venv"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')

log_info "Python 解释器: $PYTHON_CMD"
log_info "Python 版本: $PYTHON_VERSION"

# ============================================
# 2. 激活虚拟环境
# ============================================
VENV_DIR="venv"
VENV_PYTHON="$VENV_DIR/bin/python"
NEED_RECREATE_VENV=false

if [[ -d "$VENV_DIR" ]]; then
    if [[ -x "$VENV_PYTHON" ]]; then
        VENV_PYTHON_VERSION=$($VENV_PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        if ! version_ge "$VENV_PYTHON_VERSION" "$REQUIRED_VERSION"; then
            log_warn "检测到现有虚拟环境 Python 版本为 $VENV_PYTHON_VERSION，低于 $REQUIRED_VERSION"
            NEED_RECREATE_VENV=true
        fi
    else
        log_warn "检测到虚拟环境目录损坏，准备重建"
        NEED_RECREATE_VENV=true
    fi
fi

if [[ ! -d "$VENV_DIR" || "$NEED_RECREATE_VENV" == true ]]; then
    if [[ "$NEED_RECREATE_VENV" == true ]]; then
        log_warn "重建虚拟环境: $VENV_DIR"
        rm -rf "$VENV_DIR"
    fi
    log_info "创建 Python $PYTHON_VERSION 虚拟环境..."
    "$PYTHON_CMD" -m venv "$VENV_DIR"
fi

if [[ -n "$VIRTUAL_ENV" && "$VIRTUAL_ENV" != "$PROJECT_DIR/$VENV_DIR" ]]; then
    log_warn "当前已激活其他虚拟环境: $VIRTUAL_ENV"
    log_warn "将切换到项目虚拟环境: $PROJECT_DIR/$VENV_DIR"
fi

log_info "激活虚拟环境..."
source "$VENV_DIR/bin/activate"

ACTIVE_PYTHON_VERSION=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if ! version_ge "$ACTIVE_PYTHON_VERSION" "$REQUIRED_VERSION"; then
    log_error "激活后的虚拟环境 Python 版本为 $ACTIVE_PYTHON_VERSION，未达到 $REQUIRED_VERSION"
    exit 1
fi

log_info "虚拟环境已激活: $VIRTUAL_ENV"
log_info "虚拟环境 Python 版本: $ACTIVE_PYTHON_VERSION"

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
        log_info "检测镜像源: $mirror" >&2
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

        if python -m pip install -q -r "$REQUIREMENTS_FILE" \
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
        if python -m pip install -q -r "$REQUIREMENTS_FILE" --disable-pip-version-check; then
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
# 4. 检查统一配置文件
# ============================================
if ! SERVER_PORT=$(python "$PROJECT_DIR/scripts/runtime_config.py" server-port); then
    exit 1
fi

# ============================================
# 5. 检查端口占用
# ============================================
if command -v lsof &> /dev/null; then
    if lsof -i ":$SERVER_PORT" &> /dev/null; then
        log_error "统一配置指定的服务端口已被占用"
        log_error "请关闭占用进程或修改 config/config.yml"
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
# 7. 启动服务
# ============================================
log_info "启动服务..."
log_info "日志由应用模块自行管理"

nohup python ./server.py >/dev/null 2>&1 &
SERVER_PID=$!

# 保存 PID
echo $SERVER_PID > "$PID_FILE"

# 等待服务启动
sleep 2

# 检查进程是否存活
if kill -0 $SERVER_PID 2>/dev/null; then
    log_info "服务启动成功 (PID: $SERVER_PID)"
    log_info "停止服务: kill $SERVER_PID"
else
    log_error "服务启动失败，请检查应用日志模块输出"
    exit 1
fi
