# ElasticLens - Elasticsearch 集群巡检系统

<div align="center">

**Web 化 Elasticsearch 集群巡检结果自动解读平台**

![alt text](mian_web.png)

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-18.2-61dafb.svg)](https://react.dev/)
[![Flask](https://img.shields.io/badge/flask-3.0-black.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)


**语言 / Languages:** [English](../README.md) | [Deutsch](README.de.md) | [Français](README.fr.md) | [Русский](README.ru.md) | [日本語](README.ja.md)
</div>


---

## 📖 简介

ElasticLens 是一个 **Elasticsearch 集群巡检结果可视化与分析平台**。该系统专门用于处理从 **Elasticsearch 官方诊断工具**导出的诊断 ZIP 包，自动解析诊断数据、深度分析集群健康状态，并生成多维度巡检报告（HTML / Word / JSON）。

通过直观的可视化展示，帮助运维人员快速了解集群健康状况，发现潜在问题，并获得优化建议，无需手动分析复杂的诊断数据。

**Elasticsearch 官方诊断工具**: [elastic/support-diagnostics](https://github.com/elastic/support-diagnostics/)

### ✨ 主要特性

- 🌐 **Web 平台** - 基于 React + Flask 的全栈 Web 应用，支持拖拽上传诊断包
- 📊 **多格式报告** - 自动生成 HTML 和 Word (.docx) 格式巡检报告
- 🔍 **智能解析** - 自动解析 ES 诊断 ZIP 包，提取关键指标（集群健康、节点资源、索引详情、ILM、快照、安全等）
- 🧠 **深度分析** - 基于规则引擎的健康度评估、资源分析和告警生成
- 🎯 **健康评分** - 0-100 分量化评分，直观展示集群健康等级
- 🔔 **分级告警** - 三级/二级/一级 告警机制（severity_level）
- ⚡ **异步处理** - 后台异步任务处理，支持大文件（2GB）上传和长时间分析
- 📈 **可视化** - 圆形健康评分仪表盘、进度条、卡片等多种可视化展示
- 📝 **多语言支持** - 完整支持简体中文、繁體中文、English、日本語、Français、Deutsch、Русский 七种语言，界面和报告自动切换

### 🌍 多语言支持

系统全面支持国际化（i18n），提供以下7种语言：

- 🇨🇳 **简体中文 (zh-CN)** - 默认语言
- 🇹🇼 **繁體中文 (zh-TW)** - 完整翻译
- 🇺🇸 **English (en-US)** - 完整翻译
- 🇯🇵 **日本語 (ja-JP)** - 完整翻译
- 🇫🇷 **Français (fr-FR)** - 法语，完整翻译
- 🇩🇪 **Deutsch (de-DE)** - 德语，完整翻译
- 🇷🇺 **Русский (ru-RU)** - 俄语，完整翻译

**功能特点：**
- ✅ 前端UI界面动态语言切换（首页、任务列表、报告、上传、历史、设置）
- ✅ 后端报告生成支持多语言（HTML + Word格式）
- ✅ 语言偏好自动保存，下次访问自动应用
- ✅ Ant Design组件库自动适配多语言
- ✅ 智能翻译函数处理动态内容（如"5个索引"→"5インデックス"→"5 indices"等）
- ✅ 动态消息智能匹配和自动翻译兜底机制

**使用方式：**
在首页标题右侧点击语言切换按钮，选择所需语言即可。

---

## 🏗️ 系统架构

```
┌─────────────────┐      REST API      ┌─────────────────┐
│   前端 (React)   │ ◄───────────────► │   后端 (Flask)   │
│                 │                    │                 │
│ - 文件上传       │                    │ - 任务管理       │
│ - 任务跟踪       │                    │ - 异步处理       │
│ - 报告展示       │                    │ - 报告生成       │
│ - 历史记录       │                    │ - 文件管理       │
└─────────────────┘                    └────────┬────────
                                                │
                                                ▼
                                    ┌────────────────────┐
                                    │  es_insight 核心模块  │
                                    │                     │
                                    │ - 诊断数据提取       │
                                    │ - 规则引擎检查       │
                                    │ - 健康评分计算       │
                                    │ - HTML/Word 报告生成 │
                                    └────────┬───────────┘
                                             │
                                             ▼
                                    ┌────────────────────┐
                                    │  SQLite 数据库       │
                                    │                     │
                                    │ - 任务元数据         │
                                    │ - 报告元数据         │
                                    │ - 查询与统计         │
                                    └────────┬───────────┘
                                             │
                                             ▼
                                    ┌────────────────────┐
                                    │  文件系统            │
                                    │                     │
                                    │ - 上传的 ZIP 文件    │
                                    │ - JSON 报告          │
                                    │ - HTML 报告          │
                                    │ - Word 报告          │
                                    └────────────────────┘
```

---

## 🚀 快速开始

### 环境要求

- **Python**: 3.9+
- **Node.js**: 18+ (前端开发/构建)
- **npm**: 9+ (前端包管理)
- **操作系统**: Windows 10+/Linux/macOS

### 方式一：Web 平台（推荐）

#### 🐳 Docker 部署（推荐用于生产环境）

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
- ✅ 无需安装 Python 和 Node.js 环境
- ✅ 自动处理所有依赖
- ✅ 数据持久化（数据库、上传文件、报告）
- ✅ 健康检查和自动重启
- ✅ 适合生产环境部署
- ✅ 支持内网离线部署

详细部署指南请参考：[内网离线Docker部署方案.md](内网离线Docker部署方案.md)

---

#### 传统部署（本地开发）

##### 1. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

后端依赖包括：
- Flask 3.0.0 - Web 框架
- Flask-CORS 4.0.0 - 跨域支持
- python-docx >= 1.0.0 - Word 报告生成
- loguru 0.7.2 - 日志管理
- weasyprint >= 60.0 - PDF 渲染（可选）
- SQLite3 - 数据库（Python 内置，零配置）

#### 2. 安装前端依赖

```bash
cd frontend
npm install
```

前端依赖包括：
- React 18.2 + TypeScript
- Ant Design 5.12 - UI 组件库
- Vite 5.0 - 构建工具
- Axios 1.6 - HTTP 客户端
- Zustand 4.4 - 状态管理
- Recharts 2.10 - 图表库

##### 3. 启动服务

**启动后端**（在项目根目录）：
```bash
cd backend
python app.py
```
后端服务运行在 `http://localhost:5000`

**启动前端**（在项目根目录）：
```bash
cd frontend
npm run dev
```
前端服务运行在 `http://localhost:5173`

#### 4. 使用 Web 平台

1. 浏览器打开 `http://localhost:5173`
2. 拖拽或点击上传 ES 诊断 ZIP 文件
3. 等待异步分析完成
4. 查看巡检报告（HTML 展示）
5. 点击"下载 Word"按钮导出 Word 格式报告

### 方式二：命令行工具（CLI）

#### 安装

```bash
pip install -r requirements.txt
pip install -e .
```

#### 基本用法

```bash
# 解析诊断包并生成报告
es-insight data/local-diagnostics-*.zip

# 指定输出目录
es-insight data/local-diagnostics-*.zip -o ./reports

# 指定输出格式
es-insight data/local-diagnostics-*.zip -f html,json

# 使用自定义配置
es-insight data/local-diagnostics-*.zip -c configs/checkpoints_thresholds_complete.yaml
```

#### 使用 Python 脚本

```bash
# 一键处理诊断 ZIP 包
python process_diagnostic_zip.py

# 生成 HTML 报告
python generate_html_report.py data/local-diagnostics-*.zip
```

---

## 📁 项目结构

```
巡检项读取/
├── backend/                    # Flask 后端服务
│   ├── app.py                  # 主服务文件（文件上传、任务管理、报告生成 API）
│   ├── version.py              # 版本配置（v1.0.9）
│   ├── db_server/              # 数据库服务模块
│   │   ├── __init__.py         # 包初始化
│   │   ├── database.py         # 数据库初始化和连接管理
│   │   └── models.py           # 数据模型操作封装（TaskModel, ReportModel）
│   ├── es_insight.db           # SQLite 数据库文件（自动生成）
│   ├── migrate_*.py            # 数据迁移脚本
│   ├── requirements.txt        # 后端依赖
│   └── DEPLOYMENT.md           # 部署文档
│
├── frontend/                   # React 前端应用
│   ├── src/
│   │   ├── api/                # API 接口封装（Axios 实例、拦截器）
│   │   ├── components/         # 通用组件（Upload、Task、Report）
│   │   ├── pages/              # 页面组件（Home、Report、History、Settings）
│   │   ├── store/              # Zustand 状态管理
│   │   ├── hooks/              # 自定义 Hooks（usePolling、useDownload）
│   │   ├── types/              # TypeScript 类型定义
│   │   └── utils/              # 工具函数
│   ├── .env.development        # 开发环境变量
│   ├── .env.production         # 生产环境变量
│   ├── package.json
│   └── vite.config.ts          # Vite 配置（代理、插件）
│
├── es_insight/                 # 核心分析引擎
│   ├── parsers/                # 数据解析器
│   │   ├── health_parser.py    # 集群健康解析
│   │   ├── nodes_parser.py     # 节点信息解析
│   │   └── indices_parser.py   # 索引信息解析
│   ├── analyzers/              # 分析引擎
│   │   ├── health_engine.py    # 健康度评估
│   │   └── resource_engine.py  # 资源分析
│   ├── rules/                  # 规则引擎
│   │   └── engine.py           # 阈值检查与告警生成（50+ 规则）
│   ├── models/                 # 数据模型
│   ├── diagnostic_extractor.py # 诊断 ZIP 包提取器
│   ├── parse_check_result.py   # 检查结果解析（健康评分计算）
│   ├── report_generator.py     # 多格式报告生成器
│   ├── generate_html_report.py # HTML 报告生成
│   └── cli.py                  # 命令行接口
│
├── configs/                    # 配置文件
│   ├── checkpoints_thresholds_complete.yaml  # 检查项阈值配置（完整版）
│   ├── default_thresholds.yaml               # 默认阈值
│   ├── default_report.yaml                   # 报告配置
│   └── 测试指南.md
│
├── data/                       # 测试数据目录
├── uploads/                    # 上传的 ZIP 文件（Web 模式）
├── out/                        # 分析中间输出
├── reports/                    # 生成的报告文件
├── doc/                        # 文档目录
│   ├── 前端设计/               # 前端设计文档
│   └── 后端设计/               # 后端设计文档
└── tests/                      # 测试用例
```

---

## 📊 检查项概览

系统覆盖 **11 大类** 巡检指标，包含 **30+ 项** 具体检查：

| 类别 | 权重 | 检查项 |
|------|------|--------|
| **集群健康** | 30% | 集群状态、活跃分片比例、未分配分片、初始化分片、迁移分片 |
| **节点资源** | 25% | 磁盘使用率、JVM 堆使用率、CPU 使用率、系统负载、单节点分片数 |
| **索引健康** | 20% | 索引健康分布、大索引数量、高段数索引、高分片数索引、大文档数索引 |
| **分片检查** | 5% | 单分片大小、单分片文档数、分片分布均衡度 |
| **恢复检查** | 5% | 正在恢复分片数、平均恢复进度 |
| **ILM 策略** | 3% | ILM 状态检查 |
| **快照检查** | 3% | 快照配置与状态 |
| **安全检查** | 2% | X-Pack 安全功能启用情况 |
| **模板与映射** | 2% | 索引模板、组件模板、平均字段数 |
| **日志与错误** | 2% | GC 次数、GC 时间统计 |
| **性能信息** | - | 集群文档总数、集群总存储大小（信息展示，不参与评分） |

---

## ⚙️ 配置说明

### 阈值配置

核心阈值配置文件位于 `configs/checkpoints_thresholds_complete.yaml`，主要配置项：

```yaml
# 集群健康
cluster:
  status:
    green: none     # GREEN 状态不告警
    yellow: warning # YELLOW 状态警告
    red: critical   # RED 状态严重
  active_shards_percent:
    warning: 95     # 低于 95% 警告
    critical: 90    # 低于 90% 严重

# 节点资源
node:
  disk_usage_percent:
    warning: 70     # 磁盘 70% 关注
    alert: 80       # 磁盘 80% 水位线
    critical: 85    # 磁盘 85% 拒绝写入
  heap_used_percent:
    warning: 70     # JVM 70% 关注
    critical: 85    # JVM 85% OOM 风险

# 索引健康
index:
  size_gb:
    warning: 50     # 单索引 50GB 关注
    critical: 100   # 单索引 100GB 严重
  docs_count:
    warning: 100000000    # 1 亿文档关注
    critical: 500000000   # 5 亿文档严重
```

### 健康评分计算

```python
评分 = 100 - (严重告警数 × 20) - (警告数 × 5) - (信息数 × 1)
评分范围：0-100
```

| 分数范围 | 健康等级 |
|----------|----------|
| 90-100 | 🌟 优秀 |
| 75-89 | 👍 良好 |
| 60-74 | ⚠️ 一般 |
| 40-59 | 🔴 较差 |
| 0-39 | 🚨 严重 |

---

## 📄 报告输出

### HTML 报告

- 紫色渐变主题设计
- 圆形健康评分可视化
- 响应式卡片布局
- 告警信息分级展示（Critical/Warning/Info）
- 全部检查项详情表格

### Word 报告 (.docx)

- 专业排版格式
- 集群基本信息表格
- 健康评估与评分
- 检查项详情（通过/失败状态、值、阈值）
- 告警详情分级列表
- 颜色编码（✅ 绿色通过、❌ 红色失败）

### JSON 报告

- 结构化数据
- 包含 `check_results` 完整检查项详情
- 便于二次开发和数据分析

---

## 🔧 API 接口

后端提供以下 REST API 接口：

### 任务管理

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/v1/upload` | 上传诊断 ZIP 文件，创建异步任务 |
| GET | `/api/v1/tasks` | 获取任务列表（分页，排除已删除） |
| GET | `/api/v1/tasks/<task_id>` | 获取单个任务详情 |
| DELETE | `/api/v1/tasks/<task_id>` | 软删除任务（级联删除报告） |

### 报告管理

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/v1/reports` | 获取报告列表（支持筛选和分页） |
| GET | `/api/v1/reports/statistics` | 获取报告统计信息 |
| GET | `/api/v1/reports/<report_id>` | 获取报告 JSON 数据 |
| GET | `/api/v1/reports/<report_id>/html` | 获取 HTML 报告内容字符串 |
| GET | `/api/v1/reports/<report_id>/view` | 直接查看 HTML 报告（iframe） |
| GET | `/api/v1/reports/<report_id>/download?format=word` | 下载 Word 报告 |
| GET | `/api/v1/reports/<report_id>/download?format=json` | 下载 JSON 报告 |
| GET | `/api/v1/reports/<report_id>/download?format=html` | 下载 HTML 报告 |

### 系统接口

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/v1/health` | 健康检查（返回版本信息） |

---

## 🧪 测试

```bash
# 运行单元测试
pytest tests/

# 运行特定测试
pytest tests/unit/test_health_parser.py

# 带覆盖率报告
pytest --cov=es_insight --cov-report=html
```

---

## 📦 依赖清单

### 后端核心依赖

| 包 | 版本 | 用途 |
|-----|------|------|
| Flask | 3.0.0 | Web 框架 |
| Flask-CORS | 4.0.0 | 跨域支持 |
| Werkzeug | 3.0.1 | WSGI 工具库 |
| python-docx | >= 1.0.0 | Word 报告生成 |
| click | 8.1.7 | CLI 框架 |
| pyyaml | >= 6.0 | YAML 配置解析 |
| loguru | 0.7.2 | 日志管理 |
| orjson | >= 3.6.0 | 高性能 JSON |
| weasyprint | >= 60.0 | PDF 渲染（可选） |
| SQLite3 | Python 内置 | 数据库存储 |

### 前端核心依赖

| 包 | 版本 | 用途 |
|-----|------|------|
| React | 18.2 | UI 框架 |
| TypeScript | 5.2 | 类型系统 |
| Ant Design | 5.12 | UI 组件库 |
| Vite | 4.x | 构建工具 |
| Axios | 1.6 | HTTP 客户端 |
| Zustand | 4.4 | 状态管理 |
| React Router | 6.21 | 路由管理 |
| Recharts | 2.10 | 图表库 |
| Day.js | 1.11 | 日期处理 |

---

## 🐛 故障排查

### 常见问题

#### 1. Word 报告生成失败
```bash
# 检查 python-docx 是否安装
pip install python-docx>=1.0.0
```

#### 2. 前端启动失败
```bash
# 确保 Node.js >= 18
node -v
npm -v

# 重新安装依赖
cd frontend
rm -rf node_modules
npm install
```

#### 3. 后端端口被占用
```bash
# 修改 backend/app.py 中的端口号
# 默认端口：5000
```

#### 4. 前端端口被占用
```bash
# 修改 frontend/vite.config.ts 中的端口号
# 默认端口：5173
```

#### 5. Windows 中文路径问题
- python-docx 在 Windows 中文路径下可能存在兼容性问题
- 建议将项目放置在英文路径下

#### 6. 数据库文件损坏
```bash
# 删除数据库文件，重启服务会自动重建
cd backend
rm es_insight.db
python app.py
```
**注意**：这会丢失所有历史数据，请谨慎操作！

#### 7. 任务状态不更新
- 检查后端服务是否正常运行（访问 `http://localhost:5000/api/v1/health`）
- 查看浏览器控制台是否有网络错误
- 确认前端配置的 API 地址正确（`.env.development`）

---

## 📚 文档

详细文档请查看 `doc/` 目录：

| 文档 | 描述 |
|------|------|
| `doc/前端设计/README.md` | 前端文档导航 |
| `doc/前端设计/前端设计方案.md` | 前端技术选型与架构设计 |
| `doc/前端设计/前端实现指南.md` | 前端详细代码实现 |
| `doc/前端设计/后端服务设计.md` | Flask API 设计与部署 |
| `doc/前端设计/前端需求.md` | 详细需求规格 |
| `configs/测试指南.md` | 测试案例与使用指南 |

---

## 📜 变更日志

详见 [backend/CHANGELOG.md](backend/CHANGELOG.md) 和 [frontend/CHANGELOG.md](frontend/CHANGELOG.md)

### v1.0.9 (2026-05-06)

- 🐳 **新增 Docker 化部署支持**：实现前后端容器化部署方案
  - 后端 Dockerfile：基于 Python 3.11-slim，优化镜像大小（~567MB）
  - 前端 Dockerfile：多阶段构建，使用 Nginx Alpine（~45MB）
  - docker-compose.yml：服务编排、健康检查、数据持久化
  - start.sh / stop.sh：一键启停脚本，兼容 Docker Compose V1/V2
  - 完善数据持久化方案：Volume 挂载 uploads、out、reports、db 目录
  - 新增内网离线部署文档：完整的打包、传输、部署流程
  
- 🔧 **优化依赖管理**：补充缺失的 Python 依赖包
  - 添加 pandas>=1.3.0、numpy>=1.20.0、pyyaml>=6.0、jinja2>=3.0.0、orjson>=3.6.0
  
- 🐛 **修复问题**：
  - 修复 Debian Trixie 包名问题
  - 修复 TypeScript 编译错误（移除未使用的 Ant Design 组件导入）
  - 修复 Docker volume 挂载冲突

### v1.0.8 (2026-04-30)

- 🌍 **新增多语言国际化支持**：系统全面支持法语、德语、俄语
  - 后端报告生成支持法语 (fr-FR)、德语 (de-DE)、俄语 (ru-RU)
  - 分批添加约1065个翻译键（静态翻译927个 + 动态短语138个）
  - 智能翻译函数 `translate_check_message()` 增强，支持46个常见短语映射
  - HTML报告未翻译文本从99个减少到34个（66%改进）

### v1.0.7 (2026-04-30)

- 🇯🇵 **完善日文国际化支持**：彻底解决报告中残留的中文翻译问题
  - 补充 `translations.py` 中缺失的 33 个静态翻译键
  - 修复 `translations_map` 中重复定义导致的日文翻译缺失
  - 实现动态值“未知”的智能翻译逻辑
  
- 📊 **优化索引数据源配置**：提升索引统计数据的准确性与一致性
  - 将索引基础信息数据源由 `indices.json` 替换为更精准的 `indices_stats.json`
  - 统一使用 `cat_shards.txt` 作为分片数量和大小统计的权威来源

### v1.0.6 (2026-04-29)

- 🇯🇵 **新增日语国际化支持**：系统全面支持日本語（ja-JP）
  - 后端报告生成支持日语翻译（HTML + Word）
  - 添加约370个日语翻译键，覆盖所有报告内容
  - 前端UI完整支持4种语言（简体中文、繁體中文、English、日本語）
  
- 🐛 **修复Word报告语言切换Bug**：切换语言后下载的Word报告使用当前语言
  - 不同语言使用独立文件名：`{report_id}_{lang}.docx`
  - 解决切换语言后下载仍为旧语言的问题

### v1.0.5 (2026-04-27)

- 🔔 **新增三级告警分级系统**：引入severity_level验证级别
  - 🔴 三级告警（必须处理）：severity_level=3，非常严重的问题
  - 🟡 二级告警（建议处理）：severity_level=2，一般问题
  - 🔵 一级告警（优化建议）：severity_level=1，不严重问题
  - 在健康评分报告中增加各级别告警数量统计
  
- 📊 **重构告警信息展示**：从“严重/警告”两级改为“三级/二级/一级”三级分类
  - HTML和Word报告告警信息按severity_level分组显示
  - 列表页显示各级别告警数量（level_1_count、level_2_count、level_3_count）

### v1.0.4 (2026-04-27)

- 📈 **新增5个高级分析组件**：在HTML和Word报告中增加深度分析功能
  - ⚠️ 线程池队列堆积告警：监控线程池队列大小和拒绝数
  - 🔥 分片分布热点：基于分片数、CPU%、磁盘%计算负载指数
  - 💾 JVM 内存画像：展示各节点JVM堆使用率、已用/最大堆内存
  - ⚙️ 配置漂移检测：对比节点关键配置参数，发现配置不一致
  - ✅ 分片分配状态：检测未分配分片并显示失败原因

### v1.0.3 (2026-04-27)

- 🎯 **新增加权维度评分系统**：引入6大维度分类和权重机制
  - 集群健康 (25%)、节点性能 (25%)、索引状态 (20%)
  - 性能指标 (15%)、安全配置 (10%)、运维状态 (5%)
  - 新增三级阈值线性插值算法：支持程度评分，区分轻微问题和严重问题
  - 新增4个配置文件：dimension_weights.yaml、indicator_weights.yaml等
  
- 🐛 **修复评分逻辑问题**：
  - 修复字典类型value处理错误
  - 修复维度权重配置解析问题
  - 修复列表页面和报告页面评分不一致的问题

### v1.0.2 (2026-04-22)

- 💾 **实现巡检报告持久化存储功能**（SQLite 数据库）
  - 创建 `backend/db_server/` 模块，包含数据库管理和数据模型
  - 实现 tasks 表和 reports 表，支持任务和报告的完整生命周期管理
  - 新增报告列表查询接口，支持按集群名称和健康评分筛选
  - 新增报告统计接口，提供总报告数、平均健康评分等统计数据
  
- 📄 **Word 格式报告下载功能**
  - 支持将巡检报告导出为 Microsoft Word (.docx) 格式
  - 采用懒生成策略：首次请求时从 JSON 数据生成并缓存

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 代码规范

```bash
# 后端代码格式化
black es_insight/ backend/

# 前端代码检查
cd frontend
npm run lint
```

---

## 📄 许可证

MIT License

---

## 👥 维护者

ElasticLens Team

---

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- **Issues**: GitHub Issues
- **Email**: support@yogoo.net

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐ Star！**

Made with ❤️ by ElasticLens Team

**当前版本**: v1.0.9 | **最后更新**: 2026-05-06

## 报告界面展示

![alt text](report_1.png)

![alt text](report_2.png)

![alt text](report_3.png)

![alt text](report_4.png)
</div>
