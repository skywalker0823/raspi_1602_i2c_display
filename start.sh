#!/bin/bash

echo "停止並移除現有容器..."
docker-compose down

echo "拉取最新程式碼..."
git pull --rebase

echo "啟動所有服務..."
docker-compose up -d --build

echo "顯示容器狀態："
docker-compose ps