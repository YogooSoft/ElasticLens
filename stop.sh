#!/bin/bash

# 检测 Docker Compose 命令版本
if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo "❌ 错误: 未找到 Docker Compose，请先安装 Docker 和 Docker Compose"
    exit 1
fi

echo "🛑 停止 ElasticLens Docker 环境..."
echo "📌 使用命令: $DOCKER_COMPOSE"

$DOCKER_COMPOSE down

echo "✅ ElasticLens 已停止"
