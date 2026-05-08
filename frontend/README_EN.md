# ES Cluster Inspection System - Frontend

A modern web application based on React 18 + TypeScript + Ant Design 5 + Vite.

## 📋 Features

- ✅ ZIP diagnostic package upload (up to 2GB, drag-and-drop supported)
- ✅ Real-time processing task tracking (progress bar display)
- ✅ Inspection report visualization (HTML rendering)
- ✅ Health score dashboard (circular progress ring)
- ✅ Alert list display (graded display: Critical/Warning/Info)
- ✅ Historical report management (supports filtering and pagination)
- ✅ Multi-format report download (Word, JSON, HTML)
- ✅ Responsive design (adapts to desktop and mobile devices)
- ✅ **Multilingual support** (Simplified Chinese, Traditional Chinese, English, Japanese, French, German, Russian)

## 🔧 Environment Requirements

**Required**:
- Node.js >= 18.x
- npm >= 9.x

### Check Environment

```bash
node -v
npm -v
```

## 🚀 Quick Start

### Method 1: Traditional Deployment (Local Development)

#### 1. Install Dependencies

```bash
cd frontend
npm install
```

#### 2. Start Development Server

```bash
npm run dev
```

Visit http://localhost:5173

**Windows Users**: You can directly run the `start.ps1` script to automatically start the service.

#### 3. Build Production Version

```bash
npm run build
```

#### 4. Preview Production Build

```bash
npm run preview
```

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
- ✅ No need to install Node.js environment
- ✅ Automatically builds frontend resources
- ✅ Nginx reverse proxy configuration
- ✅ Health checks and automatic restarts
- ✅ Suitable for production environment deployment

For detailed deployment guide, please refer to: [内网离线Docker部署方案.md](../内网离线Docker部署方案.md)

## 📁 Project Structure

```
frontend/
├── src/
│   ├── api/              # API interface layer
│   │   ├── index.ts      # Axios instance configuration (interceptors, error handling)
│   │   ├── upload.ts     # File upload interface
│   │   ├── task.ts       # Task management interface
│   │   └── report.ts     # Report query and download interface
│   ├── components/       # Public components
│   │   ├── Upload/       # File upload component (drag-and-drop support)
│   │   ├── Task/         # Task status display component
│   │   └── Report/       # Report display component (iframe embedding)
│   ├── pages/            # Page components
│   │   ├── Home/         # Homepage (upload + task list)
│   │   ├── Report/       # Report detail page
│   │   ├── History/      # Historical report management page
│   │   └── Settings/     # Settings page
│   ├── store/            # State management (Zustand)
│   │   ├── useTaskStore.ts    # Task state management
│   │   └── useReportStore.ts  # Report state management
│   ├── hooks/            # Custom Hooks
│   │   ├── usePolling.ts      # Polling Hook (task status)
│   │   └── useDownload.ts     # Download Hook
│   ├── types/            # TypeScript type definitions
│   │   ├── task.ts       # Task-related types
│   │   └── report.ts     # Report-related types
│   ├── utils/            # Utility functions
│   ├── App.tsx           # Root component (route configuration)
│   └── main.tsx          # Entry file
├── package.json
├── vite.config.ts
├── tsconfig.json
└── README.md
```

## 🛠️ Technology Stack

### Core Frameworks
- **React 18** - UI framework (using Hooks and functional components)
- **TypeScript 5.2** - Type safety
- **Vite 4.x** - Build tool (fast hot updates)

### UI Components
- **Ant Design 5.12** - UI component library
  - Table, Card, Progress, Alert, Button, etc.
  - Upload component (drag-and-drop upload)
  - Modal, Drawer popup components
- **@ant-design/icons** - Icon library

### State Management and Routing
- **Zustand 4.4** - Lightweight state management
- **React Router 6.21** - Route management

### Utility Libraries
- **Axios 1.6** - HTTP client (interceptors, error handling)
- **Day.js 1.11** - Date processing
- **Recharts 2.10** - Chart library (health score dashboard)
- **i18next 26.0** - Internationalization framework
- **react-i18next 17.0** - React internationalization integration
- **i18next-browser-languagedetector 8.2** - Browser language detection

## ⚙️ Configuration

### Environment Variables

**.env.development** (Development Environment):
```
VITE_API_BASE_URL=http://localhost:5000/api/v1
VITE_APP_TITLE=ES Cluster Inspection System - Development
VITE_APP_VERSION=1.0.6
```

**.env.production** (Production Environment):
```
VITE_API_BASE_URL=/api/v1
VITE_APP_TITLE=ES Cluster Inspection System
VITE_APP_VERSION=1.0.6
```

### API Proxy

In development environment, Vite is configured with proxy rules:
- `/api` path will be proxied to `http://localhost:5000`
- Production environment uses relative path `/api/v1`, proxied through Nginx reverse proxy

### Detailed Environment Variable Description

**.env.development** (Development Environment):
```
VITE_API_BASE_URL=http://localhost:5000/api/v1
VITE_APP_TITLE=ES Cluster Inspection System - Development
VITE_APP_VERSION=1.0.6
```

**.env.production** (Production Environment):
```
VITE_API_BASE_URL=/api/v1
VITE_APP_TITLE=ES Cluster Inspection System
VITE_APP_VERSION=1.0.6
```

## 📝 Development Commands

```bash
# Start development server
npm run dev

# Build production version
npm run build

# Preview production build
npm run preview

# Code linting
npm run lint
```

## 🌐 Deployment

### Nginx Configuration Example

```nginx
server {
    listen 80;
    server_name localhost;
    
    root /usr/share/nginx/html;
    index index.html;

    # SPA routing support
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://backend:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Docker Deployment

**Using Docker Compose (Recommended)**:

```bash
# Execute in project root directory
cd elasticlens
./start.sh
```

**Manual Build and Run**:

Build image:
```bash
docker build -t elasticlens-frontend:latest .
```

Run container:
```bash
docker run -d -p 8080:80 --name elasticlens-frontend elasticlens-frontend:latest
```

**Docker Features**:
- ✅ Multi-stage build, reducing image size (~45MB)
- ✅ Nginx Alpine as web server
- ✅ Automatically proxy API requests to backend service
- ✅ Support large file uploads (up to 2GB)
- ✅ Health check mechanism

## ❗ Common Issues

### Q1: How to solve cross-origin issues?
**A**: 
- Development environment: Use Vite Proxy to proxy requests to backend
- Production environment: Use Nginx reverse proxy, deploy frontend and backend on same origin
- Backend has enabled Flask-CORS, allowing access from all origins

### Q2: What to do if large file upload times out?
**A**: 
- Axios is configured with 5-minute timeout (300000ms)
- You can adjust the `timeout` parameter in `frontend/src/api/index.ts`
- It's recommended to use multi-process servers like Gunicorn on the backend to improve performance

### Q3: Task status not updating?
**A**: 
- Check if `usePolling` Hook is working properly
- Confirm backend service is running normally (access `/api/v1/health`)
- Check browser console for network errors
- Default polling interval is 2 seconds, adjustable in code

### Q4: What to do if TypeScript reports errors?
**A**: 
- Check type definition files (`src/types/` directory)
- Ensure interfaces match backend return data
- Run `npm run lint` to check code standards
- Use `as any` temporarily to bypass type checking if necessary

### Q5: Word report download failed?
**A**: 
- Check if Axios response interceptor correctly handles Blob type
- Confirm python-docx library is correctly installed on backend
- Check browser console for CORS errors
- First download requires generating Word file, which may take longer

### Q6: Frontend page blank or failed to load?
**A**: 
- Check if Node.js version is >= 18
- Delete `node_modules` and re-run `npm install`
- Clear browser cache and hard refresh (Ctrl+Shift+R)
- Check if Vite development server started normally

## 📄 Related Documentation

- [Frontend Development Documentation](../../doc/前端设计/前端开发文档.md)
- [API Interface Documentation](../../doc/后端设计/API 文档.md)

## 📚 References

- [React Official Documentation](https://react.dev)
- [Ant Design Documentation](https://ant.design)
- [TypeScript Documentation](https://www.typescriptlang.org)
- [Vite Documentation](https://vitejs.dev)
- [Zustand Documentation](https://github.com/pmndrs/zustand)

---

## 🌍 Multilingual Support

The system's frontend UI fully supports 7 languages, synchronized with backend report generation language:

### Supported Languages

- **Simplified Chinese** (zh-CN) - Default language
- **Traditional Chinese** (zh-TW)
- **English** (en-US)
- **Japanese** (ja-JP)
- **French** (fr-FR)
- **German** (de-DE)
- **Russian** (ru-RU)

### Technical Implementation

- **Internationalization Framework**: react-i18next + i18next
- **Translation Resources**: `frontend/src/i18n/locales/{lang}/*.json`
- **Language Detection**: Browser language preference + localStorage persistence
- **Component Library Support**: Ant Design automatically adapts to multilingual

### Usage

Switch language in the language selector at the top right corner of the application, all UI text will update in real-time.

### Frontend-Backend Consistency

- Frontend UI language remains consistent with backend report language
- After switching language, generated HTML and Word reports use the same language
- Language preference is saved in localStorage, maintained after page refresh

---

**Version**: v1.0.9  
**Created Date**: 2025-01-15  
**Last Updated**: 2026-05-06  
**Maintainer**: ES Insight Team