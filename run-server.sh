#!/bin/bash

# 激活虚拟环境
if test -n "$VIRTUAL_ENV"
then
    echo "你处于Python虚拟环境中，路径为：$VIRTUAL_ENV"
else
    # 检查是否存在虚拟环境
    # TODO

    # 激活虚拟环境
    echo "激活Python虚拟环境"
    if . venv/bin/activate  1
    then
        echo "激活成功！"
    else
        echo "激活失败！"
        # echo "创建虚拟环境"
        # python3 -m venv venv
        exit 1
    fi
fi

# 获取pip3的版本信息
pip3_version=$(pip3 --version 2>/dev/null | awk '{print $2}')

# 判断是否需要更新 pip
if [[ -z "$pip3_version" ]]; 
then
    echo "pip3 未安装或命令不存在。"
    exit 1
fi

echo "当前pip3的版本是：$pip3_version"

# 获取最新的pip3版本信息
latest_version=$(pip3 index versions --index-url https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn pip 2>&1 | grep -o 'LATEST:    [0-9.]*' | awk '{print $2}')
echo "最新的pip3版本是：$latest_version"

if [[ -z "$latest_version" ]]; then
    echo "获取最新pip3版本失败..."
else
    if [[ "$pip3_version" == "$latest_version" ]]; 
    then
        echo "当前pip3版本已是最新。"
    else
        echo "当前pip3版本不是最新，正在更新..."
        pip3 install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple/ --trusted-host pypi.tuna.tsinghua.edu.cn
        echo "pip3 更新完成，新版本为：$latest_version"
    fi
fi

# 安装项目环境依赖
. venv/bin/activate
# pip install -r ./requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/ --trusted-host pypi.tuna.tsinghua.edu.cn

# 定义变量
REQUIREMENTS_FILE="./requirements.txt"
CACHE_DIR="./.deps_cache"
CACHE_FILE="$CACHE_DIR/last_install.md5"
PYPI_MIRROR="https://pypi.tuna.tsinghua.edu.cn/simple/"
TRUSTED_HOST="pypi.tuna.tsinghua.edu.cn"

# 创建缓存目录
mkdir -p "$CACHE_DIR"

# 函数：检查所有依赖是否满足
check_all_deps() {
    while IFS= read -r line || [[ -n "$line" ]]; do
        line_clean=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        [[ -z "$line_clean" || "$line_clean" =~ ^# ]] && continue
        
        # 提取包名
        package=$(echo "$line_clean" | sed 's/[><!=].*//;s/[[:space:]]*$//')
        
        if ! pip3 show "$package" > /dev/null 2>&1; then
            return 1  # 有包未安装
        fi
    done < "$REQUIREMENTS_FILE"
    return 0  # 所有包都已安装
}

# 生成requirements文件的MD5
current_md5=$(md5sum "$REQUIREMENTS_FILE" 2>/dev/null | awk '{print $1}')
if [[ -z "$current_md5" ]]; then
    current_md5=$(md5 "$REQUIREMENTS_FILE" 2>/dev/null | awk '{print $NF}')
fi

# 检查缓存
need_install=true
if [[ -f "$CACHE_FILE" ]]; then
    cached_md5=$(cat "$CACHE_FILE")
    
    if [[ "$current_md5" == "$cached_md5" ]]; then
        echo "📋 检查已安装的依赖..."
        if check_all_deps; then
            echo "✅ 所有依赖已安装且requirements.txt未变化"
            need_install=false
        else
            echo "⚠️  requirements.txt未变化但有依赖缺失，重新检查..."
        fi
    fi
fi

if [[ "$need_install" == true ]]; then
    echo "🚀 安装/更新Python依赖..."
    
    # 执行安装
    if pip3 install -r "$REQUIREMENTS_FILE" -i "$PYPI_MIRROR" --trusted-host "$TRUSTED_HOST"; then
        # 更新缓存
        echo "$current_md5" > "$CACHE_FILE"
        echo "✅ 依赖安装完成"
        
        # 保存安装的版本信息
        pip3 freeze > "$CACHE_DIR/installed_versions.txt"
    else
        echo "❌ 依赖安装失败"
        exit 1
    fi
fi

# # 编译安装 F2 模块
# if [[ -x "$(command -v f2)" ]];
# then
#     echo "f2 已成功安装！"
# else
#     echo "未检测到安装 f2， 正在编译安装..."
#     WORKSPACE=${PWD}
#     cd ./f2
#     pip install -e .
#     cd ${WORKSPACE}
# fi

# 启动 docker 环境
# echo "cd Server"
# cd Server

# echo "检查安装依赖"
# pip install -r ./requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/ --trusted-host pypi.tuna.tsinghua.edu.cn

# echo "启动 docker 环境"

nohup python3 ./server.py > /dev/null 2>&1 &
echo -e "服务进入后台运行，可使用 tail -f ./logs/social_media_stream_downloader 查看日志\n"



# 检查是否安装 ffmpeg

# 编译安装 ffmpeg
# FFMPEG_REPO=./ffmpeg
# cd &(FFMPEG_REPO)
# ./configure --enable-shared --enable-swscale --enable-gpl --enable-nonfree --enable-pic --prefix=/usr/local/whkt/ffmpeg  --enable-postproc --enable-pthreads --enable-static --enable-libx264 --enable-libfdk-aac