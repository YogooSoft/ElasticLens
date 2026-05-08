#!/bin/bash
# 复制数据库文件到 volumes/db 目录

set -e

echo "📋 检查并复制数据库文件..."

# 创建目标目录
mkdir -p volumes/db

# 检查源文件是否存在
if [ -f "backend/es_insight.db" ]; then
    echo "✅ 找到数据库文件: backend/es_insight.db"
    
    # 复制文件
    cp backend/es_insight.db volumes/db/es_insight.db
    
    echo "✅ 数据库文件已复制到: volumes/db/es_insight.db"
    echo "📊 文件大小: $(du -h volumes/db/es_insight.db | cut -f1)"
else
    echo "⚠️  未找到 backend/es_insight.db，将使用空数据库"
    echo "💡 首次启动时会自动创建数据库文件"
fi

# 列出 volumes/db 目录内容
echo ""
echo "📁 volumes/db 目录内容:"
ls -lh volumes/db/

echo ""
echo "✅ 准备完成！现在可以运行: docker compose up -d"
