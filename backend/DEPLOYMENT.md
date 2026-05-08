# ES 集群巡检系统 - 后端部署指南

## 📋 前提条件

### 1. Python 环境

需要 Python >= 3.8

检查 Python 版本：
```powershell
python --version
```

### 2. 安装依赖

由于网络问题，建议使用离线安装包或国内镜像。

#### 方法一：使用国内镜像（推荐）

```powershell
# 配置 pip 使用阿里云镜像
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 安装 Flask 和相关依赖
pip install Flask==3.0.0 Flask-CORS==4.0.0 loguru==0.7.2 click==8.1.7
```

#### 方法二：手动下载安装包

如果在线安装失败，可以：

1. 在有网络的机器下载 whl 包
2. 拷贝到目标机器离线安装

下载地址：
- Flask: https://pypi.org/project/Flask/#files
- Flask-CORS: https://pypi.org/project/Flask-CORS/#files

## 🚀 启动步骤

### 步骤 1: 进入项目目录

```powershell
cd "c:\Users\flyqx\Desktop\银河\巡检项读取"
```

### 步骤 2: 安装依赖（如果还未安装）

```powershell
pip install Flask Flask-CORS loguru click
```

### 步骤 3: 启动后端服务

```powershell
python backend\app.py
```

成功启动后会显示：
```
2025-01-15 10:00:00.000 | INFO     | Starting ES Insight Backend Service...
2025-01-15 10:00:00.000 | INFO     | Upload folder: uploads
2025-01-15 10:00:00.000 | INFO     | Output folder: out
2025-01-15 10:00:00.000 | INFO     | Reports folder: reports
 * Running on http://0.0.0.0:5000
 * Running on http://127.0.0.1:5000
```

### 步骤 4: 测试服务

打开浏览器访问：http://localhost:5000/api/v1/health

应该看到：
```json
{
  "code": 200,
  "message": "服务运行正常",
  "timestamp": "2025-01-15T10:00:00"
}
```

## 🔧 常见问题

### Q1: pip 安装失败 - SSL 错误

**错误**: `SSLError(SSLEOFError(8, 'EOF occurred in violation of protocol'))`

**解决方案**:

1. **使用 HTTP 而非 HTTPS**:
   ```powershell
   pip install Flask --trusted-host pypi.org --trusted-host files.pythonhosted.org
   ```

2. **使用国内镜像**:
   ```powershell
   pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
   pip install Flask Flask-CORS
   ```

3. **临时禁用 SSL 验证**:
   ```powershell
   pip install Flask --trusted-host mirrors.aliyun.com
   ```

### Q2: 端口 5000 被占用

**错误**: `Address already in use`

**解决方案**:

修改 app.py 中的端口号：
```python
app.run(host='0.0.0.0', port=5001)
```

### Q3: ModuleNotFoundError

**错误**: `No module named 'flask'`

**解决方案**:

确保在当前项目目录安装依赖：
```powershell
cd "c:\Users\flyqx\Desktop\银河\巡检项读取"
pip install -r backend\requirements.txt
```

### Q4: es_insight 模块找不到

**错误**: `No module named 'es_insight'`

**解决方案**:

确保在项目根目录运行，app.py 会自动添加路径：
```powershell
cd "c:\Users\flyqx\Desktop\银河\巡检项读取"
python backend\app.py
```

## 🌐 前后端联调

### 开发环境配置

1. **前端配置** (`.env.development`):
   ```
   VITE_API_BASE_URL=http://localhost:5000/api/v1
   ```

2. **后端运行**: http://localhost:5000

3. **前端运行**: http://localhost:3000

### CORS 配置

后端已启用 CORS，允许前端跨域访问。

## 📝 完整启动流程

### 方式一：分别启动

**终端 1 - 后端**:
```powershell
cd "c:\Users\flyqx\Desktop\银河\巡检项读取"
pip install Flask Flask-CORS loguru click
python backend\app.py
```

**终端 2 - 前端**:
```powershell
cd "c:\Users\flyqx\Desktop\银河\巡检项读取\frontend"
npm run dev
```

### 方式二：使用启动脚本

**启动后端**:
```powershell
cd "c:\Users\flyqx\Desktop\银河\巡检项读取\backend"
.\start.ps1
```

**启动前端**:
```powershell
cd "c:\Users\flyqx\Desktop\银河\巡检项读取\frontend"
.\start.ps1
```

## ✅ 验证清单

- [ ] Python 已安装且版本 >= 3.8
- [ ] Flask 及相关依赖已安装
- [ ] 后端服务可以正常启动
- [ ] 可以访问 http://localhost:5000/api/v1/health
- [ ] 前端可以访问 http://localhost:3000
- [ ] 前后端可以正常通信

## 📦 目录结构

```
c:\Users\flyqx\Desktop\银河\巡检项读取\
├── backend/
│   ├── app.py              # Flask 主程序
│   ├── requirements.txt    # Python 依赖
│   ├── README.md          # 后端文档
│   └── start.ps1          # 启动脚本
├── frontend/
│   ├── src/               # 前端源码
│   ├── package.json       # Node 依赖
│   └── ...
├── uploads/               # 上传文件目录（自动创建）
├── out/                   # 分析输出目录（自动创建）
└── reports/               # 报告输出目录（自动创建）
```

## 🆘 获取帮助

如果遇到问题：

1. 查看后端日志输出
2. 检查 Python 版本和依赖
3. 确认端口未被占用
4. 查看 README.md 文档

---

**版本**: v1.0.0  
**最后更新**: 2025-01-15
