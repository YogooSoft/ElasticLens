# ES Cluster Inspection System - Backend Service

RESTful API service based on Flask, providing data support for the frontend.

## 🚀 Quick Start

### Method 1: Traditional Deployment (Local Running)

#### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Core Dependency Description**:
- `Flask==3.0.0` - Web framework
- `Flask-CORS==4.0.0` - Cross-origin support
- `python-docx>=1.0.0` - Word report generation
- `loguru==0.7.2` - Log management
- `weasyprint>=60.0` - PDF rendering (optional)
- `pandas>=1.3.0` - Data processing
- `numpy>=1.20.0` - Numerical computation
- `pyyaml>=6.0` - YAML configuration parsing

#### 2. Start Service

```bash
python app.py
```

The service will run at `http://localhost:5000`

**Windows Users**: You can directly run the `start.ps1` script to automatically start the service.

---

### Method 2: Docker Deployment (Recommended)

Deploy frontend and backend services with one click using Docker Compose:

```bash
# Execute in project root directory
cd elasticlens

# Start all services (frontend + backend)
./start.sh

# Or execute manually
docker compose up -d
```

**Access Addresses**:
- Frontend Interface: http://localhost:8080
- Backend API: http://localhost:5001

**Advantages**:
- ✅ No need to install Python environment
- ✅ Automatically handle all dependencies
- ✅ Data persistence (database, uploaded files, reports)
- ✅ Health checks and automatic restarts
- ✅ Suitable for production environment deployment

For detailed deployment guide, please refer to: [内网离线Docker部署方案.md](../内网离线Docker部署方案.md)

## 📋 API Interfaces

### File Upload

**POST** `/api/v1/upload`

Upload ZIP diagnostic package file.

**Request Parameters**:
- `file`: multipart/form-data, ZIP file

**Response Example**:
```json
{
  "code": 200,
  "message": "Upload successful",
  "data": {
    "taskId": "uuid-string",
    "filename": "diagnostic.zip",
    "status": "pending"
  }
}
```

### Get Task List

**GET** `/api/v1/tasks`

Get list of all processing tasks (read from SQLite database, excluding deleted tasks).

**Response Example**:
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

### Get Task Details

**GET** `/api/v1/tasks/<task_id>`

Get detailed information of a specified task.

### Delete Task

**DELETE** `/api/v1/tasks/<task_id>`

Delete specified task and its related files (soft delete, data recoverable).

### Get Report List

**GET** `/api/v1/reports?page=1&per_page=20&cluster_name=test&min_health=80`

Get inspection report list, supporting filtering and pagination.

**Query Parameters**:
- `page`: Page number (default 1)
- `per_page`: Items per page (default 20)
- `cluster_name`: Cluster name (fuzzy match, optional)
- `min_health`: Minimum health score (optional)

**Response Example**:
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

### Get Report Statistics

**GET** `/api/v1/reports/statistics`

Get report statistics.

**Response Example**:
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

### Get Report Details

**GET** `/api/v1/reports/<report_id>`

Get detailed data of inspection report.

**Response Example**:
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

### Download Report

**GET** `/api/v1/reports/<report_id>/download?format=word|json|html`

Download report file, supporting three formats.

**Query Parameters**:
- `format`: Report format (`word`, `json`, or `html`, default `html`)

**Word Report Features**:
- Automatically generated and cached from JSON data on first request
- Contains complete cluster information, health assessment, check item details, alert list
- Professional layout with Chinese font support (Microsoft YaHei)
- Color coding: Green (pass), Red (fail), Orange (warning)

**Response**: Directly returns file download stream

### View HTML Report

**GET** `/api/v1/reports/<report_id>/view`

View HTML report directly in browser (for iframe embedding).

**Response**: Returns HTML content (text/html)

### Get Report HTML Content

**GET** `/api/v1/reports/<report_id>/html`

Get HTML content string of report (for frontend dynamic rendering).

**Response Example**:
```json
{
  "code": 200,
  "data": "<!DOCTYPE html>..."
}
```

### Health Check

**GET** `/api/v1/health`

Check if service is running normally.

## 🔧 Configuration

### Environment Variables

Can be configured through environment variables or by modifying the `Config` class in `app.py`:

- `UPLOAD_FOLDER`: Upload file directory (default: `uploads/`)
- `OUTPUT_FOLDER`: Output directory (default: `out/`)
- `REPORTS_FOLDER`: Report directory (default: `reports/`)
- `MAX_CONTENT_LENGTH`: Maximum upload size (default: 2GB)
- `CONFIG_FILE`: Threshold configuration file path (default: `configs/checkpoints_thresholds_complete.yaml`)

### Database Configuration

The system uses **SQLite** as persistent storage, with database file located at `backend/es_insight.db`.

**Database Table Structure**:
- `tasks`: Task record table (includes soft delete flag `is_deleted`)
- `reports`: Report metadata table (associated with tasks, includes soft delete flag)
- Index optimization: Indexes created for `status`, `created_at`, `cluster_name`, `health_score`

**Data Migration**:
- Database table structure automatically created on first startup
- Use `migrate_existing_reports.py` to import existing JSON reports into database
- Use `migrate_add_is_deleted.py` to add soft delete fields (for upgrades)

### Directory Structure

```
backend/
├── app.py                 # Main program (Flask application)
├── version.py             # Version configuration (v1.0.9)
├── Dockerfile             # Docker image build file
├── db_server/             # Database service module
│   ├── __init__.py        # Package initialization
│   ├── database.py        # Database connection management
│   └── models.py          # Data model operation encapsulation
├── es_insight.db          # SQLite database file (auto-generated)
├── migrate_*.py           # Data migration scripts
├── requirements.txt       # Python dependencies
├── start.ps1              # Windows startup script
├── uploads/               # Upload file directory (auto-created)
├── out/                   # Analysis output directory (auto-created)
└── reports/               # Report output directory (auto-created)
```

**Docker-related directories**:
```
elasticlens/
├── docker-compose.yml     # Docker Compose configuration file
├── start.sh               # One-click startup script
├── stop.sh                # One-click stop script
├── .dockerignore          # Docker build ignore file
├── volumes/               # Data persistence directory
│   ├── uploads/           # Uploaded files
│   ├── out/               # Analysis output
│   ├── reports/           # Report files
│   └── db/                # Database files
├── backend/Dockerfile     # Backend Docker image
└── frontend/Dockerfile    # Frontend Docker image
```

## 🌐 CORS Configuration

CORS support has been enabled, allowing cross-origin access from frontend.

Development environment: Frontend (http://localhost:3000) → Backend (http://localhost:5000)

## 📝 Task Processing Flow

1. **Upload File** → Create task record in database (status: pending)
2. **Asynchronous Processing** → Background thread extracts data (status: processing, progress: 0-100%)
   - Step 1: Extract ZIP file (10%)
   - Step 2: Extract diagnostic data (30%)
   - Step 3: Parse check results (60%)
   - Step 4: Generate JSON report (70%)
   - Step 5: Generate HTML report (80%)
   - Step 6: Save report to database (100%)
3. **Generate Report** → Complete task (status: completed), save report metadata
4. **Failure Handling** → Record error information (status: failed)

**Key Features**:
- ✅ Persistent storage using SQLite, data not lost after service restart
- ✅ Soft delete mechanism supported, avoiding accidental deletion of important data
- ✅ Asynchronous thread processing, not blocking API responses
- ✅ Real-time progress updates, frontend can poll for queries
- ✅ Lazy generation of Word reports, generated and cached on first request

## ⚠️ Notes

1. **File Size Limit**: Default maximum 2GB, can be modified through `MAX_CONTENT_LENGTH` configuration
2. **Asynchronous Processing**: Uses background threads for processing, does not block API responses
3. **Persistent Storage**: Tasks and report metadata stored in SQLite database, not lost after restart
4. **File Storage**: JSON/HTML/Word files saved in file system, database only stores metadata and paths
5. **Soft Delete Mechanism**: Deleting tasks will cascade soft delete associated reports, data recoverable
6. **Temporary Files**: Uploaded ZIP files saved in `uploads/` directory, recommended to clean regularly
7. **Word Generation**: First Word report download requires generation, may take longer, subsequent requests return cached file directly
8. **Chinese Paths**: python-docx may have compatibility issues with Chinese paths on Windows, English paths recommended

## 🐛 Troubleshooting

### Port Already in Use

**Error**: `Address already in use`

**Solution**: Modify port number in `app.py`
```python
app.run(host='0.0.0.0', port=5001)
```

### Dependency Installation Failed

**Error**: `Could not find a version that satisfies the requirement`

**Solution**: 
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Import Error

**Error**: `ModuleNotFoundError: No module named 'es_insight'`

**Solution**: Ensure running from project root directory:
```bash
cd elasticlens
python backend/app.py
```

### Word Report Generation Failed

**Error**: `Word generation function unavailable`

**Solution**: Check if python-docx is correctly installed
```bash
pip install python-docx>=1.0.0
```

### Database File Corrupted

**Solution**: Delete `es_insight.db` file, service will automatically rebuild on restart
```bash
rm es_insight.db
python app.py
```

Note: This will lose all historical data, please operate with caution!

## 📦 Production Deployment Recommendations

1. **Use Gunicorn**: `gunicorn -w 4 -b 0.0.0.0:5000 app:app`
2. **Use Nginx Reverse Proxy**: Configure static file service and API proxy
3. **Database Backup**: Regularly backup `es_insight.db` file
4. **Use Redis Cache**: Cache hot report data to improve query performance
5. **Add Authentication and Authorization**: Implement JWT or OAuth2 authentication mechanism
6. **Configure Log Rotation**: Use loguru's rotation feature to manage log files
7. **Monitoring and Alerts**: Integrate Prometheus + Grafana to monitor system health status
8. **File Cleanup Strategy**: Regularly clean expired upload files and report files
9. **HTTPS Support**: Configure SSL certificate, enable HTTPS encrypted transmission

---

## 🌍 Multilingual Support

This system comprehensively supports multilingual internationalization, backend report generation supports the following 7 languages:

- **Simplified Chinese** (zh-CN) - Default language
- **Traditional Chinese** (zh-TW)
- **English** (en-US)
- **Japanese** (ja-JP)
- **French** (fr-FR)
- **German** (de-DE)
- **Russian** (ru-RU)

### Translation Resource Management

All translation keys are defined in `backend/i18n/translations.py` file, including:
- **Static translation keys**: Approximately 927 per language (UI labels, titles, table column names, etc.)
- **Dynamic phrase mapping**: 46 common phrases (usage rate, size, average, etc.)
- **Smart translation function**: `translate_check_message()` supports dynamic message translation

### Usage

Specify language parameter when generating HTML or Word reports:

```python
from generate_html_report import generate_html_report

# Generate French report
html = generate_html_report(report_data, lang='fr-FR')

# Generate German report
html = generate_html_report(report_data, lang='de-DE')

# Generate Russian report
html = generate_html_report(report_data, lang='ru-RU')
```

### Translation Completeness

- **HTML Reports**: Untranslated text reduced from 99 to 34 (66% improvement)
- **Word Reports**: Synchronously support multilingual generation
- **Dynamic Messages**: Smart matching and automatic translation fallback mechanism

---

**Version**: v1.0.9  
**Last Updated**: 2026-05-06  
**Maintainer**: ES Insight Team