# ES Insight Frontend Changelog

## Version Number Location
- UI display version: `VITE_APP_VERSION` in `frontend/.env.development` and `.env.production`
- Package version: `version` field in `frontend/package.json`

## [1.0.10] - 2026-10-26
### Fixed
- **No UI feedback during large file upload**: Progress was stored in `useUploadStore` but not rendered in the upload area, so nothing appeared to change until the request completed.

### Added
- **Left-side upload progress**: `FileUploader` shows file name, progress bar, and transferred/total size below the Dragger; the drop zone is disabled while uploading to prevent duplicate submissions
- **Upload progress fallback**: `api/upload.ts` uses `file.size` when `progressEvent.total` is missing
- **i18n**: Added `uploading`, `uploadProgress`, and `uploadSize` in all locale `upload.json` files

### Technical Details
- `src/components/Upload/FileUploader.tsx`
- `src/api/upload.ts`
- `src/i18n/locales/**/upload.json`

## [1.0.9] - 2026-05-06
### Added
- **Added Dockerized deployment support**: Implemented containerized frontend deployment solution
  - Frontend Dockerfile: Multi-stage build (Node 18 Alpine + Nginx Alpine)
  - Optimized image size: Reduced from ~300MB to ~45MB
  - nginx.conf: Nginx reverse proxy configuration with automatic API request proxying
  - Support for large file uploads (client_max_body_size: 2GB)
  
- **Enhanced production environment configuration**:
  - Health check mechanism: Service status checked every 30s
  - Static resource caching optimization
  - SPA routing support (try_files $uri $uri/ /index.html)

### Changed
- **Optimized TypeScript code quality**:
  - Removed unused Ant Design component imports
  - `AllocationFailureFlow.tsx`: Removed Empty import
  - `JVMMemoryChart.tsx`: Removed Row, Col imports
  - `ShardHeatmap.tsx`: Removed Row, Col imports
  - Compliant with TypeScript strict mode requirements, eliminating TS6133 warnings

- **Improved Docker build process**:
  - Used npm ci instead of npm install to ensure dependency consistency
  - Configured domestic npm mirror source (npmmirror.com) for faster downloads
  - Multi-stage build separates compilation and runtime environments

### Fixed
- **Fixed TypeScript compilation errors**:
  - Issue: Unused variables causing build failures (TS6133)
  - Solution: Cleaned up all unused import statements
  - Impact: 3 visualization component files

### Technical Details
- Added 3 Docker-related files:
  - `frontend/Dockerfile`: Frontend image build
  - `frontend/nginx.conf`: Nginx configuration
  - `.dockerignore`: Build ignore files
- Modified 3 component files:
  - `src/components/Visualization/AllocationFailureFlow.tsx`
  - `src/components/Visualization/JVMMemoryChart.tsx`
  - `src/components/Visualization/ShardHeatmap.tsx`
- Lines of code: +~150 lines (Docker configuration)

## [1.0.8] - 2026-04-30
### Added
- **Enhanced multilingual internationalization support**: Frontend UI fully supports 7 languages
  - Simplified Chinese (zh-CN), Traditional Chinese (zh-TW), English (en-US)
  - Japanese (ja-JP), French (fr-FR), German (de-DE), Russian (ru-RU)
  - i18next framework integration with dynamic language switching
  
- **Enhanced report display functionality**:
  - HTML report iframe embedding
  - Multi-format download support (Word, JSON, HTML)
  - Real-time progress bar showing task processing status

### Changed
- **Optimized Japanese interface text length**: Shortened labels to prevent layout overflow
  - Task page: スコア、アラート、L1/L2/L3
  - History page: スコア、アラート数
  - UI layout optimization: Compact spacing, automatic line wrapping

### Fixed
- **Fixed language switching cache issue**: Reports downloaded after language switch use current language
- **Supplemented Japanese translation resources**: Completed Japanese translations for all pages

## [1.0.7] - 2026-04-29
### Added
- **Added historical report management page**: Supports filtering, pagination, and deletion operations
- **Added settings page**: Language switching and theme configuration

### Changed
- **Optimized task list display**: Added health score dashboard
- **Improved error messages**: More user-friendly notification messages

## [1.0.6] - 2026-04-27
### Added
- **Initial release**: Based on React 18 + TypeScript + Ant Design 5
- **Core features**:
  - ZIP diagnostic package upload (up to 2GB, drag-and-drop supported)
  - Real-time tracking of processing tasks
  - Inspection report visualization
  - Health score dashboard
  - Alert list display

---

**Last Updated**: 2026-05-06  
**Maintainer**: ES Insight Team