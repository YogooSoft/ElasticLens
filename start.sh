#!/bin/bash

set -e

# 检测 Docker Compose 命令版本
if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo "❌ 错误: 未找到 Docker Compose，请先安装 Docker 和 Docker Compose"
    exit 1
fi

echo "🚀 启动 ElasticLens Docker 环境..."
echo "📌 使用命令: $DOCKER_COMPOSE"

# 创建必要的目录
mkdir -p volumes/uploads volumes/out volumes/reports volumes/db

# 构建镜像
echo "📦 构建 Docker 镜像..."
$DOCKER_COMPOSE build

# 启动服务
echo "▶️  启动服务..."
$DOCKER_COMPOSE up -d

# 等待服务就绪
echo "⏳ 等待服务就绪..."
sleep 10

# 检查服务状态
echo "✅ 服务状态:"
$DOCKER_COMPOSE ps

echo ""
echo "🎉 ElasticLens 已成功启动！"
echo "📱 前端访问地址: http://localhost:8080"
echo "🔧 后端 API 地址: http://localhost:5001/api/v1"
echo ""
echo "📝 常用命令:"
echo "  查看日志: $DOCKER_COMPOSE logs -f"
echo "  停止服务: $DOCKER_COMPOSE down"
echo "  重启服务: $DOCKER_COMPOSE restart"
