#!/bin/bash

# ============================================
# SocialMediaStreamDownloader 停止脚本
# ============================================
# 功能：
# 1. 读取 PID 文件并校验该进程确实是本项目的 server
# 2. 发送 SIGTERM，让服务取消下载任务后自行退出
# 3. 等待退出，超时后按需强制结束
# ============================================
#
# 为什么要校验：PID 会被系统复用。仅凭 .server.pid 里的数字就 kill，
# 有可能杀掉一个恰好复用了该 PID 的无关进程。
#
# 为什么默认不强杀：server.py 在 SIGTERM 上注册了 cancel_live_downloads，
# 直接 SIGKILL 会让正在录制的文件失去收尾机会。

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

PID_FILE="./.server.pid"
GRACE_SECONDS=30
FORCE=0

usage() {
    echo "用法: $0 [--force] [--pid PID]"
    echo "  --force      优雅退出超时后改用 SIGKILL（会中断正在录制的文件）"
    echo "  --pid PID    停止指定进程，而不是读取 $PID_FILE"
    exit 1
}

TARGET_PID=""
PID_FROM_FILE=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --force) FORCE=1; shift ;;
        --pid)   TARGET_PID="${2:-}"; [[ -z "$TARGET_PID" ]] && usage; shift 2 ;;
        *)       usage ;;
    esac
done

# PID 文件只在它确实是本次目标来源时才可清理。
# 若目标由 --pid 显式给出，PID 文件描述的是另一个（可能仍在运行的）实例，
# 删除它会让那个实例失去被管理的凭据。
clear_pid_file_if_owned() {
    [[ "$PID_FROM_FILE" -eq 1 && -f "$PID_FILE" ]] && rm -f "$PID_FILE"
    return 0
}

# ============================================
# 1. 取得目标 PID
# ============================================
if [[ -z "$TARGET_PID" ]]; then
    if [[ ! -f "$PID_FILE" ]]; then
        log_error "未找到 $PID_FILE，服务可能未通过 run-server.sh 启动"
        log_error "可用 'ss -ltnp | grep :\$(python scripts/runtime_config.py server-port)' 查找后配合 --pid 停止"
        exit 1
    fi
    TARGET_PID=$(cat "$PID_FILE")
    PID_FROM_FILE=1
fi

if ! [[ "$TARGET_PID" =~ ^[0-9]+$ ]]; then
    log_error "PID 不是合法数字: $TARGET_PID"
    exit 1
fi

# ============================================
# 2. 校验进程存在且确实是本项目的 server
# ============================================
if ! kill -0 "$TARGET_PID" 2>/dev/null; then
    log_warn "进程 $TARGET_PID 不存在"
    clear_pid_file_if_owned
    exit 0
fi

# 逐个参数比对，不在整条命令行上做子串匹配：
# 一个恰好把 "server.py" 写进自身参数的无关进程（例如这个脚本的调用者）
# 会让子串匹配误判成命中。
mapfile -d '' -t PROC_ARGV < "/proc/$TARGET_PID/cmdline" 2>/dev/null || PROC_ARGV=()
PROC_CMD="${PROC_ARGV[*]}"
PROC_CWD=$(readlink -f "/proc/$TARGET_PID/cwd" 2>/dev/null || echo "")

# 只认「解释器 + 第一个非选项参数」这一对，即真正被执行的脚本。
# 若改为在全部参数中搜索，形如 `python -c "..." server.py` 的进程
# 会因为参数里出现该文件名而被误认。
IS_PROJECT_SERVER=0
if [[ "${PROC_ARGV[0]:-}" == *python* ]]; then
    for arg in "${PROC_ARGV[@]:1}"; do
        [[ "$arg" == -* ]] && continue
        [[ "$(basename "$arg")" == "server.py" ]] && IS_PROJECT_SERVER=1
        break
    done
fi

if [[ "$IS_PROJECT_SERVER" -eq 0 ]]; then
    log_error "进程 $TARGET_PID 不是本项目的 server，拒绝停止"
    log_error "  命令行: $PROC_CMD"
    exit 1
fi
if [[ -n "$PROC_CWD" && "$PROC_CWD" != "$PROJECT_DIR" ]]; then
    log_error "进程 $TARGET_PID 的工作目录不是本项目，拒绝停止"
    log_error "  其工作目录: $PROC_CWD"
    log_error "  本项目目录: $PROJECT_DIR"
    exit 1
fi

# ============================================
# 3. 提示正在进行的录制
# ============================================
RECORDING=$(ls -l "/proc/$TARGET_PID/fd" 2>/dev/null | grep -cE '\.flv|\.ts' || true)
if [[ "${RECORDING:-0}" -gt 0 ]]; then
    log_warn "该进程正在写入 $RECORDING 个录制文件，停止会结束这些录制"
fi

# ============================================
# 4. 优雅停止
# ============================================
log_info "向 $TARGET_PID 发送 SIGTERM..."
kill -TERM "$TARGET_PID" 2>/dev/null || true

for ((elapsed = 0; elapsed < GRACE_SECONDS; elapsed++)); do
    if ! kill -0 "$TARGET_PID" 2>/dev/null; then
        log_info "服务已停止 (PID: $TARGET_PID)"
        clear_pid_file_if_owned
        exit 0
    fi
    sleep 1
done

# ============================================
# 5. 超时处理
# ============================================
if [[ "$FORCE" -eq 1 ]]; then
    log_warn "${GRACE_SECONDS}s 内未退出，发送 SIGKILL"
    kill -KILL "$TARGET_PID" 2>/dev/null || true
    sleep 1
    if kill -0 "$TARGET_PID" 2>/dev/null; then
        log_error "进程 $TARGET_PID 仍未结束"
        exit 1
    fi
    log_info "服务已强制停止 (PID: $TARGET_PID)"
    clear_pid_file_if_owned
    exit 0
fi

log_error "${GRACE_SECONDS}s 内未退出，仍在收尾下载任务"
log_error "确认可以中断录制后，执行: $0 --force"
exit 1
