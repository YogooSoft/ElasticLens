# 前端项目安装指南

## 📋 前提条件

### 1. 安装 Node.js

前端项目需要 Node.js >= 18.x 和 npm >= 9.x

#### Windows 系统安装：

1. 访问 Node.js 官网：https://nodejs.org/
2. 下载 LTS（长期支持）版本（推荐 v18.x 或更高）
3. 运行下载的安装程序
4. 按照安装向导完成安装

#### 验证安装：

打开 PowerShell，执行：
```powershell
node -v
npm -v
```

应该显示类似：
```
v18.19.0
10.2.3
```

## 🚀 安装步骤

### 步骤 1：进入前端目录

```powershell
cd "c:\Users\flyqx\Desktop\银河\巡检项读取\frontend"
```

### 步骤 2：安装依赖

```powershell
npm install
```

这将安装以下主要依赖包：
- react, react-dom
- antd (Ant Design)
- axios
- react-router-dom
- zustand
- dayjs
- recharts
- @ant-design/icons
- 以及所有 TypeScript 类型定义

**预计时间**: 2-5 分钟（取决于网络速度）

### 步骤 3：启动开发服务器

```powershell
npm run dev
```

成功启动后，会显示：
```
  VITE v5.0.8  ready in 500 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
  ➜  press h to show help
```

### 步骤 4：访问应用

打开浏览器，访问：**http://localhost:3000**

## 🔧 故障排除

### 问题 1：npm install 失败

**错误信息**: `npm ERR! code ENOTFOUND`

**解决方案**: 
- 检查网络连接
- 切换 npm 镜像源：
  ```powershell
  npm config set registry https://registry.npmmirror.com
  npm install
  ```

### 问题 2：端口 3000 被占用

**错误信息**: `Error: listen EADDRINUSE: address already in use :::3000`

**解决方案**:
- 使用其他端口：
  ```powershell
  npm run dev -- --port 3001
  ```
- 或者关闭占用 3000 端口的程序

### 问题 3：Node.js 版本过低

**错误信息**: `Unsupported engine` 或 `ERR_UNSUPPORTED_NODE_VERSION`

**解决方案**:
- 升级 Node.js 到 v18 或更高版本
- 或使用 nvm 管理 Node.js 版本

### 问题 4：TypeScript 报错

这些是正常的编译警告，因为依赖还未安装。执行 `npm install` 后会自动消失。

## 📦 生产构建

如果需要部署到生产环境：

### 构建项目

```powershell
npm run build
```

构建完成后，会在 `dist/` 目录生成静态文件。

### 预览构建结果

```powershell
npm run preview
```

访问 http://localhost:4173

## 🌐 后端服务要求

前端需要后端 API 支持。确保后端服务运行在：
- 开发环境：`http://localhost:5000`
- 生产环境：通过 Nginx 反向代理

### 后端 API 端点：

- `POST /api/v1/upload` - 文件上传
- `GET /api/v1/tasks` - 获取任务列表
- `GET /api/v1/tasks/:id` - 获取任务详情
- `DELETE /api/v1/tasks/:id` - 删除任务
- `GET /api/v1/reports/:id` - 获取报告详情
- `GET /api/v1/reports/:id/download` - 下载报告

## ✅ 验证清单

- [ ] Node.js 已安装且版本 >= 18.x
- [ ] npm 已安装且版本 >= 9.x
- [ ] 依赖已成功安装（node_modules 目录存在）
- [ ] 开发服务器可以正常启动
- [ ] 浏览器可以访问 http://localhost:3000
- [ ] 页面显示正常，无 JavaScript 错误

## 📝 下一步

安装完成后，可以：

1. 上传 ES 集群诊断 ZIP 包
2. 查看任务处理进度
3. 查看生成的巡检报告
4. 查看历史报告记录

## 🆘 获取帮助

如果遇到问题：

1. 查看控制台错误信息
2. 检查浏览器开发者工具
3. 参考 README.md 文档
4. 查看常见问题部分

---

**文档版本**: v1.0  
**最后更新**: 2025-01-15
