# ElasticLens 内网离线 Docker 部署方案

## 1. 概述

本方案用于在**无外网连接**的内网服务器上部署 ElasticLens Docker 服务。通过在有网络的机器上打包镜像和依赖，然后传输到内网服务器进行离线部署。

---

## 2. 准备工作

### 2.1 环境要求

**有网络的机器（打包机器）**：
- Docker 20.10+ 和 Docker Compose V2
- Git（可选，用于获取最新代码）
- 足够的磁盘空间（约 2GB）

**内网服务器（部署机器）**：
- Linux 操作系统（CentOS 7+/Ubuntu 18.04+/Debian 10+）
- Docker 20.10+ 和 Docker Compose V2
- 至少 4GB 可用内存
- 至少 10GB 可用磁盘空间
- 开放端口：8080（前端）、5001（后端）

### 2.2 检查 Docker 版本

```bash
# 检查 Docker 版本
docker --version

# 检查 Docker Compose 版本（支持 V1 和 V2）
docker compose version
# 或
docker-compose --version
```

如果未安装 Docker，请参考附录 A 进行离线安装。

---

## 3. 打包阶段（在有网络的机器上执行）

### 3.1 获取项目代码

```bash
# 克隆或复制项目代码
git clone <repository_url> elasticlens
cd elasticlens

# 或者直接使用已有的代码目录
cd /path/to/elasticlens
```

### 3.2 构建 Docker 镜像

```bash
# 确保在项目根目录
cd elasticlens

# 构建后端镜像
docker build -t elasticlens-backend:latest -f backend/Dockerfile .

# 构建前端镜像
docker build -t elasticlens-frontend:latest -f frontend/Dockerfile ./frontend

# 验证镜像
docker images | grep elasticlens
```

预期输出：
```
REPOSITORY            TAG       IMAGE ID       CREATED         SIZE
elasticlens-backend   latest    xxxxxxx        x minutes ago   567MB
elasticlens-frontend  latest    yyyyyyy        x minutes ago   45MB
```

### 3.3 导出 Docker 镜像

```bash
# 创建导出目录
mkdir -p ../elasticlens-offline-package

# 导出后端镜像
docker save elasticlens-backend:latest > ../elasticlens-offline-package/elasticlens-backend.tar

# 导出前端镜像
docker save elasticlens-frontend:latest > ../elasticlens-offline-package/elasticlens-frontend.tar

# 验证文件大小
ls -lh ../elasticlens-offline-package/*.tar
```

### 3.4 准备部署文件

```bash
# 复制必要的配置文件到打包目录
cd ..

# 复制 docker-compose.yml
cp elasticlens/docker-compose.yml elasticlens-offline-package/

# 复制启动脚本
cp elasticlens/start.sh elasticlens-offline-package/
cp elasticlens/stop.sh elasticlens-offline-package/

# 复制 nginx 配置（如果需要自定义）
cp elasticlens/frontend/nginx.conf elasticlens-offline-package/

# 创建数据目录结构
mkdir -p elasticlens-offline-package/volumes/{uploads,out,reports,db}

# 复制初始数据库文件（如果有）
if [ -f elasticlens/backend/es_insight.db ]; then
    cp elasticlens/backend/es_insight.db elasticlens-offline-package/volumes/db/
fi

# 压缩整个部署包
tar czf elasticlens-offline-package.tar.gz elasticlens-offline-package/

# 查看最终包大小
ls -lh elasticlens-offline-package.tar.gz
```

### 3.5 传输到内网服务器

```bash
# 方法1：使用 scp（需要 SSH 访问）
scp elasticlens-offline-package.tar.gz user@internal-server:/tmp/

# 方法2：使用 U 盘或其他物理介质拷贝
# 将 elasticlens-offline-package.tar.gz 拷贝到 U 盘

# 方法3：使用内网文件传输工具
# 根据实际环境选择合适的方式
```

---

## 4. 部署阶段（在内网服务器上执行）

### 4.1 解压部署包

```bash
# 切换到目标目录
cd /data  # 或你选择的部署目录

# 解压部署包
tar xzf /tmp/elasticlens-offline-package.tar.gz

# 进入部署目录
cd elasticlens-offline-package

# 验证文件结构
ls -la
```

预期目录结构：
```
elasticlens-offline-package/
├── docker-compose.yml
├── start.sh
├── stop.sh
├── nginx.conf (可选)
├── volumes/
│   ├── uploads/
│   ├── out/
│   ├── reports/
│   └── db/
│       └── es_insight.db (如果有)
├── elasticlens-backend.tar
└── elasticlens-frontend.tar
```

### 4.2 加载 Docker 镜像

```bash
# 加载后端镜像
docker load < elasticlens-backend.tar

# 加载前端镜像
docker load < elasticlens-frontend.tar

# 验证镜像已加载
docker images | grep elasticlens
```

预期输出：
```
REPOSITORY            TAG       IMAGE ID       CREATED         SIZE
elasticlens-backend   latest    xxxxxxx        x days ago      567MB
elasticlens-frontend  latest    yyyyyyy        x days ago      45MB
```

### 4.3 配置环境变量（可选）

如果需要自定义配置，编辑 `docker-compose.yml`：

```bash
# 编辑 docker-compose.yml
vim docker-compose.yml

# 主要可配置项：
# - 端口映射：修改 ports 部分
# - 日志级别：修改 environment 中的 LOG_LEVEL
# - 其他环境变量
```

常用配置示例：
```yaml
environment:
  - FLASK_ENV=production
  - PYTHONUNBUFFERED=1
  - LOG_LEVEL=INFO  # 可选: DEBUG, INFO, WARNING, ERROR
```

### 4.4 启动服务

```bash
# 给脚本添加执行权限
chmod +x start.sh stop.sh

# 启动服务
./start.sh

# 或使用 docker compose 命令
docker compose up -d
```

### 4.5 验证部署

```bash
# 1. 检查容器状态
docker compose ps

# 预期输出：
# NAME                     STATUS                   PORTS
# elasticlens-backend      Up (healthy)             0.0.0.0:5001->5000/tcp
# elasticlens-frontend     Up (healthy)             0.0.0.0:8080->80/tcp

# 2. 查看后端日志
docker compose logs backend

# 预期看到：
# - 数据库初始化完成
# - Flask 应用启动成功
# - Running on http://0.0.0.0:5000

# 3. 查看前端日志
docker compose logs frontend

# 预期看到：
# - Nginx 启动成功

# 4. 测试健康检查
curl http://localhost:5001/api/v1/health

# 预期输出：JSON 格式的健康状态

# 5. 测试前端访问
curl -I http://localhost:8080

# 预期输出：HTTP/1.1 200 OK
```

### 4.6 访问应用

在浏览器中访问：
- **前端界面**: `http://<服务器IP>:8080`
- **后端 API**: `http://<服务器IP>:5001/api/v1/health`

---

## 5. 日常运维

### 5.1 查看服务状态

```bash
# 查看所有容器状态
docker compose ps

# 查看实时日志
docker compose logs -f

# 仅查看后端日志
docker compose logs -f backend

# 仅查看前端日志
docker compose logs -f frontend
```

### 5.2 重启服务

```bash
# 重启所有服务
docker compose restart

# 仅重启后端
docker compose restart backend

# 仅重启前端
docker compose restart frontend
```

### 5.3 停止服务

```bash
# 停止服务（保留数据）
./stop.sh

# 或
docker compose down
```

### 5.4 完全清理（谨慎使用）

```bash
# 停止并删除容器、网络、卷
docker compose down -v

# 警告：这会删除所有持久化数据！
```

### 5.5 备份数据

```bash
# 备份数据库
cp volumes/db/es_insight.db /backup/es_insight.db.$(date +%Y%m%d)

# 备份上传文件
tar czf /backup/uploads.$(date +%Y%m%d).tar.gz volumes/uploads/

# 备份报告文件
tar czf /backup/reports.$(date +%Y%m%d).tar.gz volumes/reports/
```

### 5.6 恢复数据

```bash
# 停止服务
docker compose down

# 恢复数据库
cp /backup/es_insight.db.20260506 volumes/db/es_insight.db

# 恢复上传文件
tar xzf /backup/uploads.20260506.tar.gz -C volumes/

# 恢复报告文件
tar xzf /backup/reports.20260506.tar.gz -C volumes/

# 重新启动
docker compose up -d
```

---

## 6. 故障排查

### 6.1 容器无法启动

```bash
# 查看详细日志
docker compose logs backend

# 常见错误及解决方案：

# 错误1: 端口被占用
# 解决：修改 docker-compose.yml 中的端口映射
ports:
  - "8081:80"  # 改为其他可用端口

# 错误2: 权限问题
# 解决：确保 volumes 目录有正确的权限
chmod -R 755 volumes/

# 错误3: 磁盘空间不足
# 解决：清理磁盘空间
df -h
docker system prune -f
```

### 6.2 前端无法访问后端

```bash
# 检查网络连接
docker compose exec frontend ping backend

# 检查后端是否正常运行
docker compose logs backend | grep "Running on"

# 检查 nginx 配置
docker compose exec frontend cat /etc/nginx/conf.d/default.conf
```

### 6.3 数据库问题

```bash
# 检查数据库文件
ls -lh volumes/db/es_insight.db

# 进入容器检查数据库
docker compose exec backend ls -lh /app/backend/es_insight.db

# 重置数据库（会丢失所有数据！）
rm volumes/db/es_insight.db
docker compose restart backend
```

### 6.4 内存不足

```bash
# 查看资源使用情况
docker stats

# 限制容器内存（编辑 docker-compose.yml）
deploy:
  resources:
    limits:
      memory: 2G
```

---

## 7. 安全建议

### 7.1 防火墙配置

```bash
# CentOS/RHEL
firewall-cmd --permanent --add-port=8080/tcp
firewall-cmd --permanent --add-port=5001/tcp
firewall-cmd --reload

# Ubuntu/Debian
ufw allow 8080/tcp
ufw allow 5001/tcp
ufw reload
```

### 7.2 使用 HTTPS（推荐生产环境）

在前面的 Nginx 配置中添加 SSL 支持：

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # ... 其他配置
}
```

### 7.3 定期更新

```bash
# 定期检查 Docker 安全更新
# 在有网络的机器上重新构建镜像并传输
```

---

## 8. 性能优化

### 8.1 日志轮转

编辑 `docker-compose.yml`，添加日志配置：

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
  
  frontend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 8.2 资源限制

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

---

## 9. 附录

### 附录 A：Docker 离线安装

#### CentOS/RHEL

```bash
# 1. 在有网络的机器上下载 RPM 包
# 访问 https://download.docker.com/linux/centos/7/x86_64/stable/Packages/
# 下载以下文件：
# - containerd.io-*.rpm
# - docker-ce-*.rpm
# - docker-ce-cli-*.rpm
# - docker-compose-plugin-*.rpm

# 2. 传输到内网服务器
scp *.rpm user@internal-server:/tmp/

# 3. 在内网服务器上安装
cd /tmp
yum install -y *.rpm

# 4. 启动 Docker
systemctl enable docker
systemctl start docker

# 5. 验证安装
docker --version
```

#### Ubuntu/Debian

```bash
# 1. 在有网络的机器上下载 DEB 包
# 访问 https://download.docker.com/linux/ubuntu/dists/focal/stable/binary-amd64/
# 下载相应的 .deb 文件

# 2. 传输到内网服务器并安装
dpkg -i *.deb
apt-get install -f  # 解决依赖

# 3. 启动 Docker
systemctl enable docker
systemctl start docker
```

### 附录 B：Docker Compose 离线安装

```bash
# 1. 在有网络的机器上下载
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-linux-x86_64" -o docker-compose

# 2. 传输到内网服务器
scp docker-compose user@internal-server:/usr/local/bin/

# 3. 在内网服务器上设置权限
chmod +x /usr/local/bin/docker-compose

# 4. 验证安装
docker-compose --version
```

### 附录 C：快速部署脚本

创建 `deploy.sh` 一键部署脚本：

```bash
#!/bin/bash
set -e

echo "🚀 ElasticLens 离线部署脚本"
echo "=========================="

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: Docker 未安装"
    exit 1
fi

# 加载镜像
echo "📦 加载 Docker 镜像..."
docker load < elasticlens-backend.tar
docker load < elasticlens-frontend.tar

# 创建数据目录
echo "📁 创建数据目录..."
mkdir -p volumes/{uploads,out,reports,db}

# 启动服务
echo "▶️  启动服务..."
docker compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查状态
echo "✅ 检查服务状态..."
docker compose ps

echo ""
echo "🎉 部署完成！"
echo "前端地址: http://$(hostname -I | awk '{print $1}'):8080"
echo "后端地址: http://$(hostname -I | awk '{print $1}'):5001"
```

使用方法：
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 10. 联系与支持

如遇到问题，请提供以下信息：
1. Docker 版本：`docker --version`
2. Docker Compose 版本：`docker compose version`
3. 操作系统版本：`cat /etc/os-release`
4. 容器日志：`docker compose logs > logs.txt`
5. 容器状态：`docker compose ps`

---

**文档版本**: v1.0  
**最后更新**: 2026-05-06  
**适用版本**: ElasticLens v1.0.x
