#!/bin/bash

# 設定錯誤處理
set -e

# 檢查是否有更新
echo "檢查更新..."
git fetch
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse @{u})

# 只在有更新或映像不存在時重新構建
if [ "$LOCAL" != "$REMOTE" ] || ! docker images weather-display >/dev/null 2>&1; then
    echo "檢測到更新或映像不存在，開始重新構建..."
    
    # 拉取更新
    git pull --rebase

    # 停止並移除現有容器
    docker stop weather-lcd 2>/dev/null || true
    docker rm weather-lcd 2>/dev/null || true

    # 使用快取構建
    DOCKER_BUILDKIT=1 docker build --build-arg BUILDKIT_INLINE_CACHE=1 -t weather-display .
else
    echo "無更新且映像存在，使用現有映像..."
    
    # 僅重啟容器
    docker stop weather-lcd 2>/dev/null || true
    docker rm weather-lcd 2>/dev/null || true
fi

# 啟動容器
echo "啟動容器..."
docker run -d --name weather-lcd \
    --restart unless-stopped \
    --privileged \
    --device=/dev/i2c-1 \
    --device=/dev/gpiomem \
    weather-display

# 顯示狀態
echo "容器狀態："
docker ps -a | grep weather-lcd