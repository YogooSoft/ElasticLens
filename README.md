# ElasticLens - Elasticsearch Cluster Inspection System

<div align="center">

**Web-based Automated Interpretation Platform for Elasticsearch Cluster Inspection Results**

![alt text](asset/mian_web.png)

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-18.2-61dafb.svg)](https://react.dev/)
[![Flask](https://img.shields.io/badge/flask-3.0-black.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)



**Languages:** [简体中文](asset/README.zh.md) | [Deutsch](asset/README.de.md) | [Français](asset/README.fr.md) | [Русский](asset/README.ru.md) | [日本語](asset/README.ja.md)

</div>


---

## 📖 Introduction

ElasticLens is a **visualization and analysis platform** for Elasticsearch cluster inspection results. The system is designed to process diagnostic ZIP packages exported from the **official Elasticsearch diagnostic tool**, automatically parse the diagnostic data, perform deep cluster health analysis, and generate multi-dimensional inspection reports (HTML / Word / JSON).

This platform helps operations personnel quickly understand cluster health status, discover potential issues, and receive optimization recommendations through intuitive visual displays, eliminating the need to manually analyze complex diagnostic data.

**Official Elasticsearch Diagnostic Tool**: [elastic/support-diagnostics](https://github.com/elastic/support-diagnostics/)

### ✨ Key Features

- 🌐 **Web Platform** - Full-stack Web application based on React + Flask, supporting drag-and-drop upload of diagnostic packages
- 📊 **Multi-format Reports** - Automatically generate HTML and Word (.docx) format inspection reports
- 🔍 **Intelligent Parsing** - Automatically parse ES diagnostic ZIP packages, extract key metrics (cluster health, node resources, index details, ILM, snapshots, security, etc.)
- 🧠 **Deep Analysis** - Rule engine-based health assessment, resource analysis, and alert generation
- 🎯 **Health Scoring** - 0-100 quantitative scoring to intuitively display cluster health levels
- 🔔 **Graded Alerts** - Three-level/two-level/one-level alert mechanism (severity_level)
- ⚡ **Asynchronous Processing** - Background asynchronous task processing, supporting large file (2GB) uploads and long-running analysis
- 📈 **Visualization** - Circular health score dashboard, progress bars, cards, and other visual displays
- 📝 **Multi-language Support** - Full support for Simplified Chinese, Traditional Chinese, English, Japanese, French, German, Russian - seven languages, with automatic interface and report switching

### 🌍 Multi-language Support

The system comprehensively supports internationalization (i18n), providing the following 7 languages:

- 🇨🇳 **Simplified Chinese (zh-CN)** - Default language
- 🇹🇼 **Traditional Chinese (zh-TW)** - Complete translation
- 🇺🇸 **English (en-US)** - Complete translation
- 🇯🇵 **Japanese (ja-JP)** - Complete translation
- 🇫🇷 **French (fr-FR)** - Complete translation
- 🇩🇪 **German (de-DE)** - Complete translation
- 🇷🇺 **Russian (ru-RU)** - Complete translation

**Features:**
- ✅ Frontend UI interface dynamic language switching (homepage, task list, reports, upload, history, settings)
- ✅ Backend report generation supports multiple languages (HTML + Word format)
- ✅ Language preference auto-saved, automatically applied on next visit
- ✅ Ant Design component library automatically adapts to multiple languages
- ✅ Smart translation function handles dynamic content (e.g., "5 indices" → "5インデックス" → "5 indices")
- ✅ Dynamic message intelligent matching and automatic translation fallback mechanism

**Usage:**
Click the language switch button on the right side of the homepage title and select the desired language.

---

## 🏗️ System Architecture

```
┌─────────────────┐      REST API      ┌─────────────────┐
│   Frontend       │ ◄───────────────► │   Backend        │
│   (React)        │                    │   (Flask)        │
│                 │                    │                 │
│ - File Upload    │                    │ - Task Mgmt      │
│ - Task Tracking  │                    │ - Async Process  │
│ - Report Display │                    │ - Report Gen     │
│ - History        │                    │ - File Mgmt      │
└─────────────────┘                    └────────┬────────
                                                │
                                                ▼
                                    ┌────────────────────┐
                                    │  es_insight Core     │
                                    │                     │
                                    │ - Diagnostic Data   │
                                    │ - Rule Engine Check │
                                    │ - Health Score Calc │
                                    │ - HTML/Word Reports │
                                    └────────┬───────────┘
                                             │
                                             ▼
                                    ┌────────────────────┐
                                    │  SQLite Database     │
                                    │                     │
                                    │ - Task Metadata     │
                                    │ - Report Metadata   │
                                    │ - Query & Stats     │
                                    └────────┬───────────┘
                                             │
                                             ▼
                                    ┌────────────────────┐
                                    │  File System         │
                                    │                     │
                                    │ - Uploaded ZIPs     │
                                    │ - JSON Reports      │
                                    │ - HTML Reports      │
                                    │ - Word Reports      │
                                    └────────────────────┘
```

---

## 🚀 Quick Start

### Requirements

- **Python**: 3.9+
- **Node.js**: 18+ (frontend development/build)
- **npm**: 9+ (frontend package management)
- **OS**: Windows 10+/Linux/macOS

### Method 1: Web Platform (Recommended)

#### 🐳 Docker Deployment (Recommended for Production)

Use Docker Compose for one-click deployment of frontend and backend services:

```bash
# Execute in project root directory
cd elasticlens

# Start all services (frontend + backend)
./start.sh

# Or execute manually
docker compose up -d
```

**Access URLs:**
- Frontend Interface: http://localhost:8080
- Backend API: http://localhost:5001

**Advantages:**
- ✅ No need to install Python and Node.js environments
- ✅ Automatically handles all dependencies
- ✅ Data persistence (database, uploaded files, reports)
- ✅ Health checks and automatic restart
- ✅ Suitable for production environment deployment
- ✅ Supports intranet offline deployment

For detailed deployment guide, please refer to: [Intranet Offline Docker Deployment Guide.md](内网离线Docker部署方案.md)

---

#### Traditional Deployment (Local Development)

##### 1. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Backend dependencies include:
- Flask 3.0.0 - Web framework
- Flask-CORS 4.0.0 - Cross-origin support
- python-docx >= 1.0.0 - Word report generation
- loguru 0.7.2 - Log management
- weasyprint >= 60.0 - PDF rendering (optional)
- SQLite3 - Database (Python built-in, zero configuration)

#### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
```

Frontend dependencies include:
- React 18.2 + TypeScript
- Ant Design 5.12 - UI component library
- Vite 5.0 - Build tool
- Axios 1.6 - HTTP client
- Zustand 4.4 - State management
- Recharts 2.10 - Chart library

##### 3. Start Services

**Start Backend** (in project root directory):
```bash
cd backend
python app.py
```
Backend service runs on `http://localhost:5000`

**Start Frontend** (in project root directory):
```bash
cd frontend
npm run dev
```
Frontend service runs on `http://localhost:5173`

#### 4. Use Web Platform

1. Open browser to `http://localhost:5173`
2. Drag and drop or click to upload ES diagnostic ZIP file
3. Wait for asynchronous analysis to complete
4. View inspection report (HTML display)
5. Click "Download Word" button to export Word format report

### Method 2: Command Line Tool (CLI)

#### Installation

```bash
pip install -r requirements.txt
pip install -e .
```

#### Basic Usage

```bash
# Parse diagnostic package and generate report
es-insight data/local-diagnostics-*.zip

# Specify output directory
es-insight data/local-diagnostics-*.zip -o ./reports

# Specify output format
es-insight data/local-diagnostics-*.zip -f html,json

# Use custom configuration
es-insight data/local-diagnostics-*.zip -c configs/checkpoints_thresholds_complete.yaml
```

#### Using Python Script

```bash
# One-click process diagnostic ZIP package
python process_diagnostic_zip.py

# Generate HTML report
python generate_html_report.py data/local-diagnostics-*.zip
```

---

## 📁 Project Structure

```
Inspection Item Reading/
├── backend/                    # Flask backend service
│   ├── app.py                  # Main service file (file upload, task management, report generation API)
│   ├── version.py              # Version configuration (v1.0.9)
│   ├── db_server/              # Database service module
│   │   ├── __init__.py         # Package initialization
│   │   ├── database.py         # Database initialization and connection management
│   │   └── models.py           # Data model operation encapsulation (TaskModel, ReportModel)
│   ├── es_insight.db           # SQLite database file (auto-generated)
│   ├── migrate_*.py            # Data migration scripts
│   ├── requirements.txt        # Backend dependencies
│   └── DEPLOYMENT.md           # Deployment documentation
│
├── frontend/                   # React frontend application
│   ├── src/
│   │   ├── api/                # API interface encapsulation (Axios instance, interceptors)
│   │   ├── components/         # Common components (Upload, Task, Report)
│   │   ├── pages/              # Page components (Home, Report, History, Settings)
│   │   ├── store/              # Zustand state management
│   │   ├── hooks/              # Custom Hooks (usePolling, useDownload)
│   │   ├── types/              # TypeScript type definitions
│   │   └── utils/              # Utility functions
│   ├── .env.development        # Development environment variables
│   ├── .env.production         # Production environment variables
│   ├── package.json
│   └── vite.config.ts          # Vite configuration (proxy, plugins)
│
├── es_insight/                 # Core analysis engine
│   ├── parsers/                # Data parsers
│   │   ├── health_parser.py    # Cluster health parsing
│   │   ├── nodes_parser.py     # Node information parsing
│   │   └── indices_parser.py   # Index information parsing
│   ├── analyzers/              # Analysis engines
│   │   ├── health_engine.py    # Health assessment
│   │   └── resource_engine.py  # Resource analysis
│   ├── rules/                  # Rule engine
│   │   └── engine.py           # Threshold checking and alert generation (50+ rules)
│   ├── models/                 # Data models
│   ├── diagnostic_extractor.py # Diagnostic ZIP package extractor
│   ├── parse_check_result.py   # Check result parsing (health score calculation)
│   ├── report_generator.py     # Multi-format report generator
│   ├── generate_html_report.py # HTML report generation
│   └── cli.py                  # Command line interface
│
├── configs/                    # Configuration files
│   ├── checkpoints_thresholds_complete.yaml  # Check item threshold configuration (complete version)
│   ├── default_thresholds.yaml               # Default thresholds
│   ├── default_report.yaml                   # Report configuration
│   └── Testing Guide.md
│
├── data/                       # Test data directory
├── uploads/                    # Uploaded ZIP files (Web mode)
├── out/                        # Analysis intermediate output
├── reports/                    # Generated report files
├── doc/                        # Documentation directory
│   ├── Frontend Design/        # Frontend design documents
│   └── Backend Design/         # Backend design documents
└── tests/                      # Test cases
```

---

## 📊 Inspection Items Overview

The system covers **11 major categories** of inspection indicators, including **30+ specific checks**:

| Category | Weight | Check Items |
|----------|--------|-------------|
| **Cluster Health** | 30% | Cluster status, active shard ratio, unassigned shards, initializing shards, relocating shards |
| **Node Resources** | 25% | Disk usage, JVM heap usage, CPU usage, system load, shards per node |
| **Index Health** | 20% | Index health distribution, large index count, high segment count indexes, high shard count indexes, large document count indexes |
| **Shard Checks** | 5% | Single shard size, single shard document count, shard distribution balance |
| **Recovery Checks** | 5% | Recovering shard count, average recovery progress |
| **ILM Policy** | 3% | ILM status check |
| **Snapshot Check** | 3% | Snapshot configuration and status |
| **Security Check** | 2% | X-Pack security feature enablement |
| **Templates & Mappings** | 2% | Index templates, component templates, average field count |
| **Logs & Errors** | 2% | GC count, GC time statistics |
| **Performance Info** | - | Total cluster documents, total cluster storage size (information display, not included in scoring) |

---

## ⚙️ Configuration

### Threshold Configuration

Core threshold configuration file located at `configs/checkpoints_thresholds_complete.yaml`, main configuration items:

```yaml
# Cluster Health
cluster:
  status:
    green: none     # GREEN status no alert
    yellow: warning # YELLOW status warning
    red: critical   # RED status critical
  active_shards_percent:
    warning: 95     # Below 95% warning
    critical: 90    # Below 90% critical

# Node Resources
node:
  disk_usage_percent:
    warning: 70     # Disk 70% attention
    alert: 80       # Disk 80% watermark
    critical: 85    # Disk 85% reject writes
  heap_used_percent:
    warning: 70     # JVM 70% attention
    critical: 85    # JVM 85% OOM risk

# Index Health
index:
  size_gb:
    warning: 50     # Single index 50GB attention
    critical: 100   # Single index 100GB critical
  docs_count:
    warning: 100000000    # 100M documents attention
    critical: 500000000   # 500M documents critical
```

### Health Score Calculation

```python
Score = 100 - (Critical Alerts × 20) - (Warning Alerts × 5) - (Info Alerts × 1)
Score Range: 0-100
```

| Score Range | Health Level |
|-------------|--------------|
| 90-100 | 🌟 Excellent |
| 75-89 | 👍 Good |
| 60-74 | ⚠️ Fair |
| 40-59 | 🔴 Poor |
| 0-39 | 🚨 Critical |

---

## 📄 Report Output

### HTML Report

- Purple gradient theme design
- Circular health score visualization
- Responsive card layout
- Graded alert information display (Critical/Warning/Info)
- Complete check item details table

### Word Report (.docx)

- Professional layout format
- Cluster basic information table
- Health assessment and scoring
- Check item details (pass/fail status, values, thresholds)
- Graded alert details list
- Color coding (✅ Green pass, ❌ Red fail)

### JSON Report

- Structured data
- Includes complete `check_results` check item details
- Convenient for secondary development and data analysis

---

## 🔧 API Endpoints

Backend provides the following REST API endpoints:

### Task Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/upload` | Upload diagnostic ZIP file, create async task |
| GET | `/api/v1/tasks` | Get task list (paginated, exclude deleted) |
| GET | `/api/v1/tasks/<task_id>` | Get single task details |
| DELETE | `/api/v1/tasks/<task_id>` | Soft delete task (cascade delete reports) |

### Report Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/reports` | Get report list (supports filtering and pagination) |
| GET | `/api/v1/reports/statistics` | Get report statistics |
| GET | `/api/v1/reports/<report_id>` | Get report JSON data |
| GET | `/api/v1/reports/<report_id>/html` | Get HTML report content string |
| GET | `/api/v1/reports/<report_id>/view` | Directly view HTML report (iframe) |
| GET | `/api/v1/reports/<report_id>/download?format=word` | Download Word report |
| GET | `/api/v1/reports/<report_id>/download?format=json` | Download JSON report |
| GET | `/api/v1/reports/<report_id>/download?format=html` | Download HTML report |

### System Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check (returns version info) |

---

## 🧪 Testing

```bash
# Run unit tests
pytest tests/

# Run specific test
pytest tests/unit/test_health_parser.py

# With coverage report
pytest --cov=es_insight --cov-report=html
```

---

## 📦 Dependency List

### Backend Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Flask | 3.0.0 | Web framework |
| Flask-CORS | 4.0.0 | Cross-origin support |
| Werkzeug | 3.0.1 | WSGI toolkit |
| python-docx | >= 1.0.0 | Word report generation |
| click | 8.1.7 | CLI framework |
| pyyaml | >= 6.0 | YAML config parsing |
| loguru | 0.7.2 | Log management |
| orjson | >= 3.6.0 | High-performance JSON |
| weasyprint | >= 60.0 | PDF rendering (optional) |
| SQLite3 | Python built-in | Database storage |

### Frontend Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| React | 18.2 | UI framework |
| TypeScript | 5.2 | Type system |
| Ant Design | 5.12 | UI component library |
| Vite | 4.x | Build tool |
| Axios | 1.6 | HTTP client |
| Zustand | 4.4 | State management |
| React Router | 6.21 | Route management |
| Recharts | 2.10 | Chart library |
| Day.js | 1.11 | Date handling |

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Word Report Generation Failure
```bash
# Check if python-docx is installed
pip install python-docx>=1.0.0
```

#### 2. Frontend Startup Failure
```bash
# Ensure Node.js >= 18
node -v
npm -v

# Reinstall dependencies
cd frontend
rm -rf node_modules
npm install
```

#### 3. Backend Port Occupied
```bash
# Modify port number in backend/app.py
# Default port: 5000
```

#### 4. Frontend Port Occupied
```bash
# Modify port number in frontend/vite.config.ts
# Default port: 5173
```

#### 5. Windows Chinese Path Issues
- python-docx may have compatibility issues with Windows Chinese paths
- Recommend placing project in English path

#### 6. Database File Corruption
```bash
# Delete database file, restart service will rebuild automatically
cd backend
rm es_insight.db
python app.py
```
**Note**: This will lose all historical data, please operate with caution!

#### 7. Task Status Not Updating
- Check if backend service is running normally (access `http://localhost:5000/api/v1/health`)
- Check browser console for network errors
- Confirm frontend API address is correct (`.env.development`)

---

## 📚 Documentation

For detailed documentation, please check the `doc/` directory:

| Document | Description |
|----------|-------------|
| `doc/Frontend Design/README.md` | Frontend documentation navigation |
| `doc/Frontend Design/Frontend Design Plan.md` | Frontend technology selection and architecture design |
| `doc/Frontend Design/Frontend Implementation Guide.md` | Frontend detailed code implementation |
| `doc/Frontend Design/Backend Service Design.md` | Flask API design and deployment |
| `doc/Frontend Design/Frontend Requirements.md` | Detailed requirement specifications |
| `configs/Testing Guide.md` | Test cases and usage guide |

---

## 📜 Changelog

See [backend/CHANGELOG.md](backend/CHANGELOG.md) and [frontend/CHANGELOG.md](frontend/CHANGELOG.md) for details

### v1.0.9 (2026-05-06)

- 🐳 **Added Docker Deployment Support**: Implemented containerized deployment solution for frontend and backend
  - Backend Dockerfile: Based on Python 3.11-slim, optimized image size (~567MB)
  - Frontend Dockerfile: Multi-stage build, using Nginx Alpine (~45MB)
  - docker-compose.yml: Service orchestration, health checks, data persistence
  - start.sh / stop.sh: One-click start/stop scripts, compatible with Docker Compose V1/V2
  - Improved data persistence solution: Volume mounting for uploads, out, reports, db directories
  - Added intranet offline deployment documentation: Complete packaging, transfer, deployment process
  
- 🔧 **Optimized Dependency Management**: Added missing Python dependency packages
  - Added pandas>=1.3.0, numpy>=1.20.0, pyyaml>=6.0, jinja2>=3.0.0, orjson>=3.6.0
  
- 🐛 **Bug Fixes**:
  - Fixed Debian Trixie package name issue
  - Fixed TypeScript compilation errors (removed unused Ant Design component imports)
  - Fixed Docker volume mount conflicts

### v1.0.8 (2026-04-30)

- 🌍 **Added Multi-language Internationalization Support**: System comprehensively supports French, German, Russian
  - Backend report generation supports French (fr-FR), German (de-DE), Russian (ru-RU)
  - Added approximately 1065 translation keys in batches (927 static translations + 138 dynamic phrases)
  - Enhanced smart translation function `translate_check_message()`, supports 46 common phrase mappings
  - Reduced untranslated text in HTML reports from 99 to 34 (66% improvement)

### v1.0.7 (2026-04-30)

- 🇯🇵 **Improved Japanese Internationalization Support**: Thoroughly resolved remaining Chinese translation issues in reports
  - Supplemented 33 missing static translation keys in `translations.py`
  - Fixed duplicate definitions in `translations_map` causing missing Japanese translations
  - Implemented smart translation logic for dynamic value "unknown"
  
- 📊 **Optimized Index Data Source Configuration**: Improved accuracy and consistency of index statistics data
  - Replaced index basic information data source from `indices.json` to more accurate `indices_stats.json`
  - Unified use of `cat_shards.txt` as authoritative source for shard count and size statistics

### v1.0.6 (2026-04-29)

- 🇯🇵 **Added Japanese Internationalization Support**: System comprehensively supports Japanese (ja-JP)
  - Backend report generation supports Japanese translation (HTML + Word)
  - Added approximately 370 Japanese translation keys, covering all report content
  - Frontend UI fully supports 4 languages (Simplified Chinese, Traditional Chinese, English, Japanese)
  
- 🐛 **Fixed Word Report Language Switching Bug**: Downloaded Word reports after language switching use current language
  - Different languages use independent filenames: `{report_id}_{lang}.docx`
  - Resolved issue where downloads still used old language after switching

### v1.0.5 (2026-04-27)

- 🔔 **Added Three-level Alert Classification System**: Introduced severity_level validation level
  - 🔴 Level 3 Alert (Must Handle): severity_level=3, very serious issues
  - 🟡 Level 2 Alert (Recommended to Handle): severity_level=2, general issues
  - 🔵 Level 1 Alert (Optimization Suggestion): severity_level=1, non-serious issues
  - Added alert count statistics by level in health score reports
  
- 📊 **Refactored Alert Information Display**: Changed from "Critical/Warning" two-level to "Level 3/Level 2/Level 1" three-level classification
  - HTML and Word report alert information grouped and displayed by severity_level
  - List page displays alert counts by level (level_1_count, level_2_count, level_3_count)

### v1.0.4 (2026-04-27)

- 📈 **Added 5 Advanced Analysis Components**: Added deep analysis functionality in HTML and Word reports
  - ⚠️ Thread Pool Queue Accumulation Alert: Monitor thread pool queue size and rejection count
  - 🔥 Shard Distribution Hotspots: Calculate load index based on shard count, CPU%, disk%
  - 💾 JVM Memory Profile: Display JVM heap usage, used/max heap memory for each node
  - ⚙️ Configuration Drift Detection: Compare key configuration parameters across nodes, detect inconsistencies
  - ✅ Shard Allocation Status: Detect unassigned shards and display failure reasons

### v1.0.3 (2026-04-27)

- 🎯 **Added Weighted Dimension Scoring System**: Introduced 6 major dimension categories and weight mechanism
  - Cluster Health (25%), Node Performance (25%), Index Status (20%)
  - Performance Metrics (15%), Security Configuration (10%), Operational Status (5%)
  - Added three-level threshold linear interpolation algorithm: Support degree scoring, distinguish minor issues from serious issues
  - Added 4 configuration files: dimension_weights.yaml, indicator_weights.yaml, etc.
  
- 🐛 **Fixed Scoring Logic Issues**:
  - Fixed dictionary type value handling error
  - Fixed dimension weight configuration parsing issue
  - Fixed inconsistency between list page and report page scores

### v1.0.2 (2026-04-22)

- 💾 **Implemented Inspection Report Persistent Storage** (SQLite Database)
  - Created `backend/db_server/` module, including database management and data models
  - Implemented tasks table and reports table, supporting complete lifecycle management of tasks and reports
  - Added report list query interface, supporting filtering by cluster name and health score
  - Added report statistics interface, providing total report count, average health score, and other statistical data
  
- 📄 **Word Format Report Download Functionality**
  - Support exporting inspection reports to Microsoft Word (.docx) format
  - Adopted lazy generation strategy: Generate and cache from JSON data on first request

---

## 🤝 Contributing

Welcome to submit Issues and Pull Requests!

### Code Standards

```bash
# Backend code formatting
black es_insight/ backend/

# Frontend code checking
cd frontend
npm run lint
```

---

## 📄 License

MIT License

---

## 👥 Maintainers

ElasticLens Team

---

## 📞 Contact

For questions or suggestions, please contact via:

- **Issues**: GitHub Issues
- **Email**: support@yogoo.net

---

<div align="center">

**If this project helps you, please give it a ⭐ Star!**

Made with ❤️ by ElasticLens Team

**Current Version**: v1.0.9 | **Last Updated**: 2026-05-06

## Report Interface Display

![alt text](asset/report_1.png)

![alt text](asset/report_2.png)

![alt text](asset/report_3.png)

![alt text](asset/report_4.png)
</div>
