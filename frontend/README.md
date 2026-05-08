# ES 集群巡检系统 - 前端

基于 React 18 + TypeScript + Ant Design 5 + Vite 的现代化 Web 应用。

## 📋 功能特性

- ✅ ZIP 诊断包上传（最大 2GB，支持拖拽）
- ✅ 处理任务实时跟踪（进度条展示）
- ✅ 巡检报告可视化展示（HTML 渲染）
- ✅ 健康评分仪表盘（圆形进度环）
- ✅ 告警列表展示（分级显示 Critical/Warning/Info）
- ✅ 历史报告管理（支持筛选和分页）
- ✅ 多格式报告下载（Word、JSON、HTML）
- ✅ 响应式设计（适配桌面和移动端）
- ✅ **多语言支持**（简体中文、繁體中文、English、日本語、Français、Deutsch、Русский）

## 🔧 环境要求

**必须安装**：
- Node.js >= 18.x
- npm >= 9.x

### 检查环境

```bash
node -v
npm -v
```

## 🚀 快速开始

### 方式一：传统部署（本地开发）

#### 1. 安装依赖

```bash
cd frontend
npm install
```

#### 2. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:5173

**Windows 用户**：可直接运行 `start.ps1` 脚本自动启动服务。

#### 3. 构建生产版本

```bash
npm run build
```

#### 4. 预览生产构建

```bash
npm run preview
```

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
- ✅ 无需安装 Node.js 环境
- ✅ 自动构建前端资源
- ✅ Nginx 反向代理配置
- ✅ 健康检查和自动重启
- ✅ 适合生产环境部署

详细部署指南请参考：[内网离线Docker部署方案.md](../内网离线Docker部署方案.md)

## 📁 项目结构

```
frontend/
├── src/
│   ├── api/              # API 接口层
│   │   ├── index.ts      # Axios 实例配置（拦截器、错误处理）
│   │   ├── upload.ts     # 文件上传接口
│   │   ├── task.ts       # 任务管理接口
│   │   └── report.ts     # 报告查询与下载接口
│   ├── components/       # 公共组件
│   │   ├── Upload/       # 文件上传组件（拖拽支持）
│   │   ├── Task/         # 任务状态展示组件
│   │   └── Report/       # 报告展示组件（iframe 嵌入）
│   ├── pages/            # 页面组件
│   │   ├── Home/         # 首页（上传 + 任务列表）
│   │   ├── Report/       # 报告详情页
│   │   ├── History/      # 历史报告管理页
│   │   └── Settings/     # 设置页
│   ├── store/            # 状态管理 (Zustand)
│   │   ├── useTaskStore.ts    # 任务状态管理
│   │   └── useReportStore.ts  # 报告状态管理
│   ├── hooks/            # 自定义 Hooks
│   │   ├── usePolling.ts      # 轮询 Hook（任务状态）
│   │   └── useDownload.ts     # 下载 Hook
│   ├── types/            # TypeScript 类型定义
│   │   ├── task.ts       # 任务相关类型
│   │   └── report.ts     # 报告相关类型
│   ├── utils/            # 工具函数
│   ├── App.tsx           # 根组件（路由配置）
│   └── main.tsx          # 入口文件
├── package.json
├── vite.config.ts
├── tsconfig.json
└── README.md
```

## 🛠️ 技术栈

### 核心框架
- **React 18** - UI 框架（使用 Hooks 和函数组件）
- **TypeScript 5.2** - 类型安全
- **Vite 4.x** - 构建工具（快速热更新）

### UI 组件
- **Ant Design 5.12** - UI 组件库
  - Table、Card、Progress、Alert、Button 等
  - Upload 组件（拖拽上传）
  - Modal、Drawer 弹窗组件
- **@ant-design/icons** - 图标库

### 状态管理与路由
- **Zustand 4.4** - 轻量级状态管理
- **React Router 6.21** - 路由管理

### 工具库
- **Axios 1.6** - HTTP 客户端（拦截器、错误处理）
- **Day.js 1.11** - 日期处理
- **Recharts 2.10** - 图表库（健康评分仪表盘）
- **i18next 26.0** - 国际化框架
- **react-i18next 17.0** - React 国际化集成
- **i18next-browser-languagedetector 8.2** - 浏览器语言检测

## ⚙️ 配置说明

### 环境变量

**.env.development** (开发环境):
```
VITE_API_BASE_URL=http://localhost:5000/api/v1
VITE_APP_TITLE=ES 集群巡检系统 - 开发环境
VITE_APP_VERSION=1.0.6
```

**.env.production** (生产环境):
```
VITE_API_BASE_URL=/api/v1
VITE_APP_TITLE=ES 集群巡检系统
VITE_APP_VERSION=1.0.6
```

### API 代理

开发环境下，Vite 配置了代理规则：
- `/api` 路径会代理到 `http://localhost:5000`
- 生产环境使用相对路径 `/api/v1`，通过 Nginx 反向代理

### 环境变量详细说明

**.env.development** (开发环境):
```
VITE_API_BASE_URL=http://localhost:5000/api/v1
VITE_APP_TITLE=ES 集群巡检系统 - 开发环境
VITE_APP_VERSION=1.0.6
```

**.env.production** (生产环境):
```
VITE_API_BASE_URL=/api/v1
VITE_APP_TITLE=ES 集群巡检系统
VITE_APP_VERSION=1.0.6
```

## 📝 开发命令

```bash
# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview

# 代码检查
npm run lint
```

## 🌐 部署

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name localhost;
    
    root /usr/share/nginx/html;
    index index.html;

    # SPA 路由支持
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api/ {
        proxy_pass http://backend:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Docker 部署

**使用 Docker Compose（推荐）**：

```bash
# 在项目根目录执行
cd elasticlens
./start.sh
```

**手动构建和运行**：

构建镜像：
```bash
docker build -t elasticlens-frontend:latest .
```

运行容器：
```bash
docker run -d -p 8080:80 --name elasticlens-frontend elasticlens-frontend:latest
```

**Docker 特性**：
- ✅ 多阶段构建，减小镜像体积（~45MB）
- ✅ Nginx Alpine 作为 Web 服务器
- ✅ 自动代理 API 请求到后端服务
- ✅ 支持大文件上传（最大 2GB）
- ✅ 健康检查机制

## ❗ 常见问题

### Q1: 跨域问题如何解决？
**A**: 
- 开发环境：使用 Vite Proxy 代理请求到后端
- 生产环境：使用 Nginx 反向代理，前后端同源部署
- 后端已启用 Flask-CORS，允许所有来源访问

### Q2: 大文件上传超时怎么办？
**A**: 
- Axios 已配置 5 分钟超时（300000ms）
- 可在 `frontend/src/api/index.ts` 中调整 `timeout` 参数
- 建议后端使用 Gunicorn 等多进程服务器提升性能

### Q3: 任务状态不更新？
**A**: 
- 检查 `usePolling` Hook 是否正常工作
- 确认后端服务正常运行（访问 `/api/v1/health`）
- 查看浏览器控制台是否有网络错误
- 轮询间隔默认为 2 秒，可在代码中调整

### Q4: TypeScript 报错怎么办？
**A**: 
- 检查类型定义文件（`src/types/` 目录）
- 确保接口与后端返回数据一致
- 运行 `npm run lint` 检查代码规范
- 必要时使用 `as any` 临时绕过类型检查

### Q5: Word 报告下载失败？
**A**: 
- 检查 Axios 响应拦截器是否正确处理 Blob 类型
- 确认后端 python-docx 库已正确安装
- 查看浏览器控制台是否有 CORS 错误
- 首次下载需要生成 Word 文件，可能耗时较长

### Q6: 前端页面空白或加载失败？
**A**: 
- 检查 Node.js 版本是否 >= 18
- 删除 `node_modules` 并重新运行 `npm install`
- 清除浏览器缓存并硬刷新（Ctrl+Shift+R）
- 检查 Vite 开发服务器是否正常启动

## 📄 相关文档

- [前端开发文档](../../doc/前端设计/前端开发文档.md)
- [API 接口文档](../../doc/后端设计/API 文档.md)

## 📚 参考资料

- [React 官方文档](https://react.dev)
- [Ant Design 文档](https://ant.design)
- [TypeScript 文档](https://www.typescriptlang.org)
- [Vite 文档](https://vitejs.dev)
- [Zustand 文档](https://github.com/pmndrs/zustand)

---

## 🌍 多语言支持

本系统前端UI全面支持7种语言，与后端报告生成语言同步：

### 支持的语言

- **简体中文** (zh-CN) - 默认语言
- **繁體中文** (zh-TW)
- **English** (en-US)
- **日本語** (ja-JP)
- **Français** (fr-FR) - 法语
- **Deutsch** (de-DE) - 德语
- **Русский** (ru-RU) - 俄语

### 技术实现

- **国际化框架**：react-i18next + i18next
- **翻译资源**：`frontend/src/i18n/locales/{lang}/*.json`
- **语言检测**：浏览器语言偏好 + 本地存储持久化
- **组件库支持**：Ant Design自动适配多语言

### 使用方法

在应用右上角的语言选择器中切换语言，所有UI文本将实时更新。

### 前后端一致性

- 前端UI语言与后端报告语言保持一致
- 切换语言后，生成的HTML和Word报告使用相同语言
- 语言偏好保存在localStorage，页面刷新后保持

---

**版本**: v1.0.9  
**创建日期**: 2025-01-15  
**最后更新**: 2026-05-06  
**维护者**: ES Insight Team
