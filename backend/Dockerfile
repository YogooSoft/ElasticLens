# 使用 Python 3.11 slim 版本作为基础镜像
FROM python:3.11-slim

# 设置工作目录为 backend
WORKDIR /app/backend

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_ENV=production \
    FLASK_APP=app.py \
    PYTHONPATH=/app

# 安装系统依赖（weasyprint 需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装（相对于 /app）
COPY backend/requirements.txt /app/backend/
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目根目录的 es_insight 模块
COPY es_insight /app/es_insight

# 复制后端代码到当前工作目录（/app/backend）
COPY backend .

# 复制配置文件
COPY configs /app/configs

# 复制 HTML 报告生成脚本
COPY generate_html_report.py /app/generate_html_report.py

# 创建必要的目录
RUN mkdir -p /app/uploads /app/out /app/reports

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/v1/health')" || exit 1

# 启动命令（当前工作目录是 /app/backend）
CMD ["python", "-u", "app.py"]
