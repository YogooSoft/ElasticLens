# ElasticLens Docker 部署指南

## 快速开始

### 前置要求

- Docker >= 20.10
- Docker Compose >= 1.29

### 一键启动

```bash
# 赋予脚本执行权限
chmod +x start.sh stop.sh setup_db.sh

# 启动服务
./setup_db.sh # 首次部署需要初始化数据库
./start.sh
```

### 访问应用

- **前端界面**: http://localhost:8080
- **后端 API**: http://localhost:5001/api/v1

### 停止服务

```bash
./stop.sh
```

## 手动操作

### 构建镜像

```bash
docker-compose build
```

### 启动服务

```bash
docker-compose up -d
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 停止服务

```bash
docker-compose down
```

### 重新部署

```bash
docker-compose up -d --build
```

## 数据持久化

所有数据存储在 `volumes/` 目录下：

- `volumes/uploads/` - 上传的 ZIP 诊断包
- `volumes/out/` - 提取的分析数据
- `volumes/reports/` - 生成的报告文件
- `volumes/db/` - SQLite 数据库

### 备份数据

```bash
tar -czf elasticlens-backup-$(date +%Y%m%d).tar.gz volumes/
```

### 恢复数据

```bash
tar -xzf elasticlens-backup-20260506.tar.gz
```

## 生产环境部署

使用生产环境配置（包含资源限制和日志轮转）：

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 常见问题

### 端口冲突

如果端口 8080 或 5001 已被占用，修改 `docker-compose.yml` 中的端口映射：

```yaml
ports:
  - "8081:80"  # 修改前端端口
  - "5002:5000"  # 修改后端端口
```

### 权限问题

确保 volumes 目录有正确的权限：

```bash
mkdir -p volumes/uploads volumes/out volumes/reports volumes/db
chmod -R 777 volumes/
```

### 构建失败

清理 Docker 缓存后重试：

```bash
docker system prune -a
docker-compose build --no-cache
```

## 健康检查

查看容器健康状态：

```bash
docker inspect --format='{{.State.Health.Status}}' elasticlens-backend
docker inspect --format='{{.State.Health.Status}}' elasticlens-frontend
```

## 更多帮助

详细的设计文档请参考：`doc/Docker化部署设计文档.md`
