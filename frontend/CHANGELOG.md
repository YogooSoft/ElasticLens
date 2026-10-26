# ES Insight Frontend 变更日志

## 版本号修改位置
- 页面展示版本：`frontend/.env.development`、`.env.production` 中的 `VITE_APP_VERSION`
- 包版本：`frontend/package.json` 的 `version` 字段

## [1.0.10] - 2026-10-26
### Fixed
- **大文件上传过程无界面反馈**：进度已写入 `useUploadStore`，但上传区未渲染进度，用户在上传完成前看不到任何变化。

### Added
- **左侧上传进度展示**：`FileUploader` 在 Dragger 下方显示文件名、进度条、已传输/总大小；上传中禁用拖拽区防止重复提交
- **上传进度兜底**：`api/upload.ts` 在 `progressEvent.total` 缺失时使用 `file.size` 计算百分比
- **多语言**：各语言 `upload.json` 新增 `uploading`、`uploadProgress`、`uploadSize`

### Technical Details
- `src/components/Upload/FileUploader.tsx`
- `src/api/upload.ts`
- `src/i18n/locales/**/upload.json`

## [1.0.9] - 2026-05-06
### Added
- **新增 Docker 化部署支持**：实现前端容器化部署方案
  - 前端 Dockerfile：多阶段构建（Node 18 Alpine + Nginx Alpine）
  - 镜像体积优化：从 ~300MB 减小到 ~45MB
  - nginx.conf：Nginx 反向代理配置，自动代理 API 请求
  - 支持大文件上传（client_max_body_size: 2GB）
  
- **完善生产环境配置**：
  - 健康检查机制：每 30s 检查服务状态
  - 静态资源缓存优化
  - SPA 路由支持（try_files $uri $uri/ /index.html）

### Changed
- **优化 TypeScript 代码质量**：
  - 移除未使用的 Ant Design 组件导入
  - `AllocationFailureFlow.tsx`：移除 Empty
  - `JVMMemoryChart.tsx`：移除 Row, Col
  - `ShardHeatmap.tsx`：移除 Row, Col
  - 符合 TypeScript 严格模式要求，消除 TS6133 警告

- **改进 Docker 构建流程**：
  - 使用 npm ci 替代 npm install，确保依赖一致性
  - 配置国内 npm 镜像源（npmmirror.com）加速下载
  - 多阶段构建分离编译和运行环境

### Fixed
- **修复 TypeScript 编译错误**：
  - 问题：未使用的变量导致构建失败（TS6133）
  - 解决：清理所有未使用的导入语句
  - 影响：3 个可视化组件文件

### Technical Details
- 新增 3 个 Docker 相关文件：
  - `frontend/Dockerfile`：前端镜像构建
  - `frontend/nginx.conf`：Nginx 配置
  - `.dockerignore`：构建忽略文件
- 修改 3 个组件文件：
  - `src/components/Visualization/AllocationFailureFlow.tsx`
  - `src/components/Visualization/JVMMemoryChart.tsx`
  - `src/components/Visualization/ShardHeatmap.tsx`
- 代码行数：+约150行（Docker 配置）

## [1.0.8] - 2026-04-30
### Added
- **完善多语言国际化支持**：前端UI全面支持7种语言
  - 简体中文 (zh-CN)、繁體中文 (zh-TW)、English (en-US)
  - 日本語 (ja-JP)、Français (fr-FR)、Deutsch (de-DE)、Русский (ru-RU)
  - i18next 框架集成，支持动态语言切换
  
- **增强报告展示功能**：
  - HTML 报告 iframe 嵌入展示
  - 多格式下载支持（Word、JSON、HTML）
  - 实时进度条显示任务处理状态

### Changed
- **优化日语界面文本长度**：缩短标签避免布局溢出
  - Task 页面：スコア、アラート、L1/L2/L3
  - History 页面：スコア、アラート数
  - UI 布局优化：紧凑间距、自动换行

### Fixed
- **修复语言切换缓存问题**：切换语言后下载报告使用当前语言
- **补充日语翻译资源**：完善所有页面的日语翻译

## [1.0.7] - 2026-04-29
### Added
- **新增历史报告管理页面**：支持筛选、分页、删除操作
- **新增设置页面**：语言切换、主题配置

### Changed
- **优化任务列表展示**：增加健康评分仪表盘
- **改进错误提示**：更友好的用户提示信息

## [1.0.6] - 2026-04-27
### Added
- **初始版本发布**：基于 React 18 + TypeScript + Ant Design 5
- **核心功能**：
  - ZIP 诊断包上传（最大 2GB，支持拖拽）
  - 处理任务实时跟踪
  - 巡检报告可视化展示
  - 健康评分仪表盘
  - 告警列表展示

---

**最后更新**: 2026-05-06  
**维护者**: ES Insight Team
