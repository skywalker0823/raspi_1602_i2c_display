#!/bin/bash

# 停止並移除現有容器（如果存在）
echo "Stopping and removing existing container..."
docker stop weather-lcd 2>/dev/null
docker rm weather-lcd 2>/dev/null

# 拉取最新代碼
echo "Pulling latest code from repository..."
git pull --rebase

# 重新構建和啟動容器
echo "Building and starting the container..."
docker build -t weather-display .
docker run -d --name weather-lcd --restart unless-stopped --privileged --device=/dev/i2c-1 weather-display
docker ps -a