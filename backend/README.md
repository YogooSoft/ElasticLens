# ES 集群巡检系统 - 后端服务

基于 Flask 的 RESTful API 服务，为前端提供数据支持。

## 🚀 快速开始

### 方式一：传统部署（本地运行）

#### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

**核心依赖说明**：
- `Flask==3.0.0` - Web 框架
- `Flask-CORS==4.0.0` - 跨域支持
- `python-docx>=1.0.0` - Word 报告生成
- `loguru==0.7.2` - 日志管理
- `weasyprint>=60.0` - PDF 渲染（可选）
- `pandas>=1.3.0` - 数据处理
- `numpy>=1.20.0` - 数值计算
- `pyyaml>=6.0` - YAML 配置解析

#### 2. 启动服务

```bash
python app.py
```

服务将运行在 `http://localhost:5000`

**Windows 用户**：可直接运行 `start.ps1` 脚本自动启动服务。

---

### 方式二：Docker 部署（推荐）

使用 Docker Compose 一键部署前后端服务：

```bash
# 在项目根目录执行
cd elasticlens

# 启动所有服务（前端 + 后端）
./start.sh

# 或手动执行
docker compose up -d
```

**访问地址**：
- 前端界面：http://localhost:8080
- 后端 API：http://localhost:5001

**优势**：
- ✅ 无需安装 Python 环境
- ✅ 自动处理所有依赖
- ✅ 数据持久化（数据库、上传文件、报告）
- ✅ 健康检查和自动重启
- ✅ 适合生产环境部署

详细部署指南请参考：[内网离线Docker部署方案.md](../内网离线Docker部署方案.md)

## 📋 API 接口

### 文件上传

**POST** `/api/v1/upload`

上传 ZIP 诊断包文件。

**请求参数**:
- `file`: multipart/form-data, ZIP 文件

**响应示例**:
```json
{
  "code": 200,
  "message": "上传成功",
  "data": {
    "taskId": "uuid-string",
    "filename": "diagnostic.zip",
    "status": "pending"
  }
}
```

### 获取任务列表

**GET** `/api/v1/tasks`

获取所有处理任务的列表（从 SQLite 数据库读取，排除已删除任务）。

**响应示例**:
```json
{
  "code": 200,
  "data": [
    {
      "id": "uuid-string",
      "filename": "diagnostic.zip",
      "file_size": 1024000,
      "status": "completed",
      "progress": 100,
      "created_at": "2025-01-15T10:00:00",
      "updated_at": "2025-01-15T10:05:00",
      "result": {
        "reportId": "report_uuid",
        "healthScore": 85,
        "alertCount": 3
      }
    }
  ]
}
```

### 获取任务详情

**GET** `/api/v1/tasks/<task_id>`

获取指定任务的详细信息。

### 删除任务

**DELETE** `/api/v1/tasks/<task_id>`

删除指定的任务及其相关文件（软删除，数据可恢复）。

### 获取报告列表

**GET** `/api/v1/reports?page=1&per_page=20&cluster_name=test&min_health=80`

获取巡检报告列表，支持筛选和分页。

**查询参数**:
- `page`: 页码（默认 1）
- `per_page`: 每页数量（默认 20）
- `cluster_name`: 集群名称（模糊匹配，可选）
- `min_health`: 最低健康评分（可选）

**响应示例**:
```json
{
  "code": 200,
  "data": [
    {
      "id": "report_uuid",
      "task_id": "task_uuid",
      "cluster_name": "production-cluster",
      "health_score": 85,
      "alert_count": 3,
      "critical_count": 1,
      "warning_count": 2,
      "created_at": "2025-01-15T10:05:00",
      "metadata": {
        "nodes_count": 5,
        "indices_count": 120
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 50
  }
}
```

### 获取报告统计信息

**GET** `/api/v1/reports/statistics`

获取报告统计数据。

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "total_reports": 150,
    "avg_health_score": 82.5,
    "clusters": ["production", "staging", "development"]
  }
}
```

### 获取报告详情

**GET** `/api/v1/reports/<report_id>`

获取巡检报告的详细数据。

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "id": "report_uuid",
    "clusterName": "production-cluster",
    "healthScore": 85,
    "basicInfo": {...},
    "alerts": {...},
    "checkResults": {...}
  }
}
```

### 下载报告

**GET** `/api/v1/reports/<report_id>/download?format=word|json|html`

下载报告文件，支持三种格式。

**查询参数**:
- `format`: 报告格式（`word`、`json` 或 `html`，默认 `html`）

**Word 报告特性**:
- 首次请求时从 JSON 数据自动生成并缓存
- 包含完整的集群信息、健康评估、检查项详情、告警列表
- 采用专业排版，支持中文字体（微软雅黑）
- 颜色编码：绿色（通过）、红色（失败）、橙色（警告）

**响应**: 直接返回文件下载流

### 查看 HTML 报告

**GET** `/api/v1/reports/<report_id>/view`

直接在浏览器中查看 HTML 报告（用于 iframe 嵌入）。

**响应**: 返回 HTML 内容（text/html）

### 获取报告 HTML 内容

**GET** `/api/v1/reports/<report_id>/html`

获取报告的 HTML 内容字符串（用于前端动态渲染）。

**响应示例**:
```json
{
  "code": 200,
  "data": "<!DOCTYPE html>..."
}
```

### 健康检查

**GET** `/api/v1/health`

检查服务是否正常运行。

## 🔧 配置说明

### 环境变量

可以通过环境变量或修改 `app.py` 中的 `Config` 类配置：

- `UPLOAD_FOLDER`: 上传文件目录（默认：`uploads/`）
- `OUTPUT_FOLDER`: 输出目录（默认：`out/`）
- `REPORTS_FOLDER`: 报告目录（默认：`reports/`）
- `MAX_CONTENT_LENGTH`: 最大上传大小（默认：2GB）
- `CONFIG_FILE`: 阈值配置文件路径（默认：`configs/checkpoints_thresholds_complete.yaml`）

### 数据库配置

系统使用 **SQLite** 作为持久化存储，数据库文件位于 `backend/es_insight.db`。

**数据库表结构**:
- `tasks`: 任务记录表（包含软删除标记 `is_deleted`）
- `reports`: 报告元数据表（关联任务，包含软删除标记）
- 索引优化：针对 `status`、`created_at`、`cluster_name`、`health_score` 建立索引

**数据迁移**:
- 首次启动时自动创建数据库表结构
- 使用 `migrate_existing_reports.py` 可将现有 JSON 报告导入数据库
- 使用 `migrate_add_is_deleted.py` 可添加软删除字段（升级用）

### 目录结构

```
backend/
├── app.py                 # 主程序（Flask 应用）
├── version.py             # 版本配置（v1.0.9）
├── Dockerfile             # Docker 镜像构建文件
├── db_server/             # 数据库服务模块
│   ├── __init__.py        # 包初始化
│   ├── database.py        # 数据库连接管理
│   └── models.py          # 数据模型操作封装
├── es_insight.db          # SQLite 数据库文件（自动生成）
├── migrate_*.py           # 数据迁移脚本
├── requirements.txt       # Python 依赖
├── start.ps1              # Windows 启动脚本
├── uploads/               # 上传文件目录（自动创建）
├── out/                   # 分析输出目录（自动创建）
└── reports/               # 报告输出目录（自动创建）
```

**Docker 相关目录**：
```
elasticlens/
├── docker-compose.yml     # Docker Compose 配置文件
├── start.sh               # 一键启动脚本
├── stop.sh                # 一键停止脚本
├── .dockerignore          # Docker 构建忽略文件
├── volumes/               # 数据持久化目录
│   ├── uploads/           # 上传文件
│   ├── out/               # 分析输出
│   ├── reports/           # 报告文件
│   └── db/                # 数据库文件
├── backend/Dockerfile     # 后端 Docker 镜像
└── frontend/Dockerfile    # 前端 Docker 镜像
```

## 🌐 CORS 配置

已启用 CORS 支持，允许前端跨域访问。

开发环境：前端 (http://localhost:3000) → 后端 (http://localhost:5000)

## 📝 任务处理流程

1. **上传文件** → 创建任务记录到数据库（状态：pending）
2. **异步处理** → 后台线程提取数据（状态：processing，进度：0-100%）
   - 步骤 1: 解压 ZIP 文件（10%）
   - 步骤 2: 提取诊断数据（30%）
   - 步骤 3: 解析检查结果（60%）
   - 步骤 4: 生成 JSON 报告（70%）
   - 步骤 5: 生成 HTML 报告（80%）
   - 步骤 6: 保存报告到数据库（100%）
3. **生成报告** → 完成任务（状态：completed），保存报告元数据
4. **失败处理** → 记录错误信息（状态：failed）

**关键特性**:
- ✅ 使用 SQLite 持久化存储，服务重启后数据不丢失
- ✅ 支持软删除机制，避免误删重要数据
- ✅ 异步线程处理，不阻塞 API 响应
- ✅ 实时进度更新，前端可轮询查询
- ✅ 懒生成 Word 报告，首次请求时生成并缓存

## ⚠️ 注意事项

1. **文件大小限制**: 默认最大 2GB，可通过 `MAX_CONTENT_LENGTH` 配置修改
2. **异步处理**: 使用后台线程处理，不会阻塞 API 响应
3. **持久化存储**: 任务和报告元数据存储在 SQLite 数据库中，重启后不丢失
4. **文件存储**: JSON/HTML/Word 文件保存在文件系统，数据库仅存储元数据和路径
5. **软删除机制**: 删除任务时会级联软删除关联的报告，数据可恢复
6. **临时文件**: 上传的 ZIP 文件会保存在 `uploads/` 目录，建议定期清理
7. **Word 生成**: 首次下载 Word 报告时需要生成，可能耗时较长，后续请求直接返回缓存文件
8. **中文路径**: python-docx 在 Windows 中文路径下可能存在兼容性问题，建议使用英文路径

## 🐛 故障排除

### 端口被占用

**错误**: `Address already in use`

**解决**: 修改 `app.py` 中的端口号
```python
app.run(host='0.0.0.0', port=5001)
```

### 依赖安装失败

**错误**: `Could not find a version that satisfies the requirement`

**解决**: 
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 导入错误

**错误**: `ModuleNotFoundError: No module named 'es_insight'`

**解决**: 确保在项目根目录运行：
```bash
cd elasticlens
python backend/app.py
```

### Word 报告生成失败

**错误**: `Word 生成功能不可用`

**解决**: 检查 python-docx 是否正确安装
```bash
pip install python-docx>=1.0.0
```

### 数据库文件损坏

**解决**: 删除 `es_insight.db` 文件，重启服务会自动重建
```bash
rm es_insight.db
python app.py
```

注意：这会丢失所有历史数据，请谨慎操作！

## 📦 生产部署建议

1. **使用 Gunicorn**: `gunicorn -w 4 -b 0.0.0.0:5000 app:app`
2. **使用 Nginx 反向代理**: 配置静态文件服务和 API 代理
3. **数据库备份**: 定期备份 `es_insight.db` 文件
4. **使用 Redis 缓存**: 缓存热点报告数据，提升查询性能
5. **添加认证和授权**: 实现 JWT 或 OAuth2 认证机制
6. **配置日志轮转**: 使用 loguru 的 rotation 功能管理日志文件
7. **监控告警**: 集成 Prometheus + Grafana 监控系统健康状态
8. **文件清理策略**: 定期清理过期的上传文件和报告文件
9. **HTTPS 支持**: 配置 SSL 证书，启用 HTTPS 加密传输

---

## 🌍 多语言支持

本系统全面支持多语言国际化，后端报告生成支持以下7种语言：

- **简体中文** (zh-CN) - 默认语言
- **繁體中文** (zh-TW)
- **English** (en-US)
- **日本語** (ja-JP)
- **Français** (fr-FR) - 法语
- **Deutsch** (de-DE) - 德语
- **Русский** (ru-RU) - 俄语

### 翻译资源管理

所有翻译键定义在 `backend/i18n/translations.py` 文件中，包括：
- **静态翻译键**：约927个/语言（UI标签、标题、表格列名等）
- **动态短语映射**：46个常见短语（使用率、大小、平均等）
- **智能翻译函数**：`translate_check_message()` 支持动态消息翻译

### 使用方法

在生成HTML或Word报告时，指定语言参数即可：

```python
from generate_html_report import generate_html_report

# 生成法语报告
html = generate_html_report(report_data, lang='fr-FR')

# 生成德语报告
html = generate_html_report(report_data, lang='de-DE')

# 生成俄语报告
html = generate_html_report(report_data, lang='ru-RU')
```

### 翻译完整性

- **HTML报告**：未翻译文本从99个减少到34个（66%改进）
- **Word报告**：同步支持多语言生成
- **动态消息**：智能匹配和自动翻译兜底机制

---

**版本**: v1.0.9  
**最后更新**: 2026-05-06  
**维护者**: ES Insight Team
