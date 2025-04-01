#!/bin/bash

# 停止並移除現有容器（如果存在）
echo "停止並移除現有容器..."
docker stop weather-lcd 2>/dev/null
docker rm weather-lcd 2>/dev/null

# 拉取最新代碼
echo "拉取最新程式碼..."
git pull --rebase

# 重新構建和啟動容器
echo "重新建構並啟動容器..."
docker build -t weather-display .
docker run -d --name weather-lcd \
    --restart unless-stopped \
    --privileged \
    --device=/dev/i2c-1 \
    --device=/dev/gpiomem \  # 加入 GPIO 存取權限給 DHT11
    weather-display

# 顯示容器狀態
echo "容器狀態："
docker ps -a | grep weather-lcd