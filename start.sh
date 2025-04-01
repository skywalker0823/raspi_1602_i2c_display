#!/bin/bash

# 停止並移除現有容器（如果存在）
docker stop weather-lcd 2>/dev/null
docker rm weather-lcd 2>/dev/null

# 拉取最新代碼
git pull --rebase

# 重新構建和啟動容器
docker build -t weather-display .
docker run -d --name weather-lcd --restart unless-stopped --privileged --device=/dev/i2c-1 weather-display