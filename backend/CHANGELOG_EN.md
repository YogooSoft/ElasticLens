# ES Insight Backend Changelog

## Version Number Location
- Version number is defined in the `version.py` file
- Modify the `VERSION` variable to update the version number

## [1.0.9] - 2026-05-06
### Added
- **Added Dockerized deployment support**: Implemented containerized frontend and backend deployment solution
  - Backend Dockerfile: Based on Python 3.11-slim, optimized image size (~567MB)
  - Frontend Dockerfile: Multi-stage build using Nginx Alpine (~45MB)
  - docker-compose.yml: Service orchestration, health checks, data persistence
  - start.sh / stop.sh: One-click start/stop scripts, compatible with Docker Compose V1/V2
  
- **Enhanced data persistence solution**:
  - Volume mounting: uploads, out, reports, db directories
  - Database file mapped separately to avoid overwriting code files
  - Supports offline deployment and data backup/restore
  
- **Added internal network offline deployment documentation**:
  - `内网离线Docker部署方案.md`: Complete packaging, transfer, and deployment process
  - Supports rapid deployment in environments without external network access
  - Includes troubleshooting and operations guide

### Changed
- **Optimized dependency management**: Supplemented missing Python dependency packages
  - Added `pandas>=1.3.0`: Required for data processing
  - Added `numpy>=1.20.0`: Foundation library for numerical computation
  - Added `pyyaml>=6.0`: YAML configuration file parsing
  - Added `jinja2>=3.0.0`: Template engine
  - Added `orjson>=3.6.0`: High-performance JSON processing
  
- **Improved Docker build configuration**:
  - Used Tsinghua PyPI mirror source to accelerate dependency downloads
  - WORKDIR set to `/app/backend`, simplifying module imports
  - Increased health check startup wait time (40s)
  - Enabled Python unbuffered output (-u), displaying logs in real-time

### Fixed
- **Fixed Debian Trixie package name issue**:
  - Changed `libgdk-pixbuf2.0-0` to `libgdk-pixbuf-xlib-2.0-0`
  - Adapted to package name changes in the latest Debian version
  
- **Fixed TypeScript compilation errors**:
  - Removed unused Ant Design component imports (Empty, Row, Col)
  - Compliant with TypeScript strict mode requirements
  
- **Fixed Docker volume mount conflict**:
  - Only map database file, not covering the db_server directory
  - Ensures Python module files are not hidden
  - Resolved ImportError: cannot import name 'db_manager'

### Technical Details
- Added 8 Docker-related files:
  - `backend/Dockerfile`: Backend image build
  - `frontend/Dockerfile`: Frontend image build
  - `frontend/nginx.conf`: Nginx reverse proxy configuration
  - `docker-compose.yml`: Service orchestration configuration
  - `docker-compose.prod.yml`: Production environment configuration
  - `.dockerignore`: Build ignore files
  - `start.sh` / `stop.sh`: Start/stop scripts
- Modified 3 frontend component files:
  - `AllocationFailureFlow.tsx`: Removed Empty import
  - `JVMMemoryChart.tsx`: Removed Row, Col imports
  - `ShardHeatmap.tsx`: Removed Row, Col imports
- Lines of code: +~800 lines (including Docker configuration and documentation)

## [1.0.8] - 2026-04-30
### Added
- **Added multilingual internationalization support**: System comprehensively supports French, German, and Russian
  - Backend report generation supports French (fr-FR), German (de-DE), Russian (ru-RU)
  - Batch added approximately 1065 translation keys (927 static translations + 138 dynamic phrases)
  - Enhanced smart translation function `translate_check_message()`, supporting 46 common phrase mappings
  
- **Enhanced dynamic message translation mechanism**: Implemented intelligent segmented matching and automatic translation fallback
  - Extended `common_phrases` dictionary in `translations.py`
  - Replaced by length in descending order, ensuring long patterns match first
  - Regular expressions handle dynamic content (numbers, node names, index names, etc.)
  - Special handling for English spaces and formatting

### Changed
- **Optimized HTML report multilingual display**: Significantly reduced untranslated Chinese text
  - Untranslated text in HTML reports reduced from 99 to 34 (excluding comments, 66% improvement)
  - After removing HTML comments, only 34 untranslated texts remain visible
  - Covers UI labels, storage documents, node indexes, shards, JVM, resource usage, check details, etc.

### Fixed
- **Fixed missing translation key issues**: Supplemented key translation keys missing in fr-FR, de-DE, ru-RU
  - Added 239 translation keys per language in batches (8 batches total)
  - Fixed single quote escaping issues (apostrophes in French)
  - Ensured all static text uses the translate() function

### Technical Details
- Modified core files:
  - `backend/i18n/translations.py`: Added 1065 new translation keys, enhanced dynamic message translation
  - `generate_html_report.py`: Ensured correct calling of translate_check_message() function
- Added auxiliary scripts:
  - `batch_add_translations_*.py`: 8 batches of batch translation addition scripts
  - `enhance_dynamic_translation.py`: Dynamic message translation enhancement script
  - `check_missing_*.py`: Multiple scripts for checking missing translation keys
- Lines of code: +~3500 lines (including translation data and scripts)

## [1.0.7] - 2026-04-30
### Added
- **Enhanced Japanese internationalization support**: Thoroughly resolved remaining Chinese translation issues in reports
  - Supplemented 33 missing static translation keys in `translations.py` (such as data source, resource usage status, etc.)
  - Fixed missing Japanese translations caused by duplicate definitions in `translations_map`
  - Implemented smart translation logic for dynamic value "unknown", ensuring table data can also switch languages correctly
  
- **Optimized index data source configuration**: Improved accuracy and consistency of index statistical data
  - Replaced index basic information data source from `indices.json` to more precise `indices_stats.json`
  - Unified use of `cat_shards.txt` as authoritative source for shard count and size statistics
  - Corrected node shard count field name to `shard_count`, ensuring frontend-backend data alignment

### Fixed
- **Fixed HTML/Word report multilingual display incompleteness**:
  - Resolved issue where metadata labels (extraction time, check duration, etc.) still displayed in Chinese in Japanese environment
  - Resolved issue where major titles (all check item details, etc.) did not apply translation functions
  - Resolved issue where hardcoded Chinese values in tables (such as "unknown") could not switch with language
- **Enhanced translation layer fallback mechanism**: Improved `translate_check_message` matching capability for complex dynamic strings

### Technical Details
- Modified core files:
  - `backend/i18n/translations.py`: Completed Japanese translation mapping table
  - `generate_html_report.py`: Added local translation helper functions to handle hardcoded values
  - `es_insight/parsers/indices_parser.py`: Optimized data extraction logic
- Added verification scripts:
  - `check_translations_map_japanese.py`: Automated check for translation completeness
  - `test_unknown_translation.py`: Verified special value translation logic

## [1.0.6] - 2026-04-29
### Added
- **Added Japanese internationalization support**: System comprehensively supports 日本語 (ja-JP)
  - Backend report generation supports Japanese translation (HTML + Word)
  - Added approximately 370 Japanese translation keys, covering all report content
  - Smart translation function supports Japanese text processing
  
- **Enhanced frontend interface multilingual support**: Frontend UI fully supports 4 languages
  - Simplified Chinese (zh-CN), Traditional Chinese (zh-TW), English (en-US), Japanese (ja-JP)
  - All page components support dynamic language switching
  - i18next framework integration and configuration optimization

### Changed
- **Optimized Word report file naming strategy**: Fixed language switching cache issue
  - Different languages use independent filenames: `{report_id}_{lang}.docx`
  - Resolved issue where downloading after language switch still showed old language
  - Simplified Chinese maintains default naming `{report_id}.docx`
  
- **Optimized Japanese list page text length**: Shortened label text to prevent layout overflow
  - Task page: スコア、アラート、L1/L2/L3 (concise expression)
  - History page: スコア、アラート数
  - UI layout optimization: Compact spacing, automatic line wrapping, half-width colons

### Fixed
- **Fixed Word report language switching bug**: Downloaded Word reports after language switch use current language
  - Issue: All languages shared the same filename causing cache conflicts
  - Solution: Generate different filenames based on language parameter
- **Fixed incomplete frontend Japanese translations**: Supplemented Japanese translation resources for all pages
  - Completed 7 JSON translation files (home, task, report, upload, history, settings, common)
  - Updated i18n initialization configuration to import and register Japanese resources

### Technical Details
- Modified 5 core files:
  - `backend/app.py`: Word file path logic + download filename
  - `backend/i18n/translations.py`: Added Japanese translation dictionary + smart translation rules
  - `frontend/src/i18n/index.ts`: Imported and registered Japanese resources
  - `frontend/src/i18n/config.ts`: Added Japanese to supported language list
  - `frontend/src/components/Task/TaskList.tsx`: Optimized Tag layout
- Added 7 frontend translation files: `frontend/src/i18n/locales/ja-JP/*.json`
- Lines of code: +~500 lines (including comments and blank lines)

## [1.0.5] - 2026-04-27
### Added
- **Added three-level alert classification system**: Introduced severity_level validation level, improving alert accuracy and operability
  - 🔴 Level 3 Alert (Must Handle): severity_level=3, very serious issues affecting cluster stability
  - 🟡 Level 2 Alert (Recommended to Handle): severity_level=2, general issues, recommended for optimization
  - 🔵 Level 1 Alert (Optimization Suggestion): severity_level=1, non-serious issues, can be used as optimization reference
- **Added alert statistics fields**: Added statistics for each level of alerts in health score reports
  - `level_1_count`: Count of Level 1 alerts (optimization suggestions)
  - `level_2_count`: Count of Level 2 alerts (recommended to handle)
  - `level_3_count`: Count of Level 3 alerts (must handle)
- **Added configuration file**: `configs/severity_level_weights.yaml` - Alert level weight configuration

### Changed
- **Refactored alert information display**: Changed from two-level "Critical/Warning" to three-level "Level 3/Level 2/Level 1" classification
  - HTML report: Alert information grouped by severity_level, identified with different colors
  - Word report: Alert information grouped by severity_level, with clearer titles
  - List page: Displays counts for each alert level (level_1_count, level_2_count, level_3_count)
- **Optimized alert information position**: Moved alert information from end of report to after "Health Score" and before "Advanced Analysis Components"
  - Clearer logic: From macro (score) to micro (specific alerts), then to in-depth analysis (5 components)
  - Smoother reading: Users first see overall score, then specific issues, finally in-depth analysis
- **Unified HTML and Word alert structure**: HTML and Word reports use the same alert classification logic and display method
  - Both use severity_level field for grouping
  - Both display problem description, current value, and recommendations

### Fixed
- **Fixed alert classification logic**: Used severity_level instead of severity field for alert grouping
  - Old logic: Used severity field (critical/warning), unable to distinguish problem severity
  - New logic: Used severity_level field (1/2/3), accurately reflecting problem severity
- **Enhanced database queries**: Added level_1_count, level_2_count, level_3_count field queries in task list interface
- **Optimized Word alert styling**: Three alert levels use different colors (red/yellow/blue) to distinguish severity

### Technical Details
- Added 1 auxiliary function: `_add_alerts_to_word()` to generate Word format alert information
- Modified 6 files:
  - `backend/app.py`: Word report alert generation + list page data return
  - `backend/version.py`: Version number upgraded to 1.0.5
  - `generate_html_report.py`: HTML report alert classification + style optimization
  - `configs/severity_level_weights.yaml`: Added alert level weight configuration
  - `frontend/.env.development` and `frontend/.env.production`: Frontend version number upgrade
- Lines of code: +~150 lines (including comments and blank lines)

## [1.0.4] - 2026-04-27
### Added
- **Added 5 advanced analysis components**: Added in-depth analysis functionality to HTML and Word reports
  - ⚠️ Thread Pool Queue Backlog Alert: Monitor thread pool queue size and rejection count, identify overloaded thread pools
  - 🔥 Shard Distribution Hotspots: Calculate load index based on shard count, CPU%, disk%, identify hotspot nodes
  - 💾 JVM Memory Profile: Display JVM heap usage rate, used/max heap memory for each node
  - ⚙️ Configuration Drift Detection: Compare key configuration parameters across nodes, discover configuration inconsistencies
  - ✅ Shard Allocation Status: Detect unallocated shards and display failure reasons

### Changed
- **Optimized data extraction**: Extended diagnostic_extractor to save raw data for advanced analysis
  - Save `nodes_raw`: Complete nodes.json data, including node settings configuration
  - Save `thread_pools`: Detailed thread pool data extracted from nodes_stats
  - Save `allocation_explain`: Shard allocation explanation data
- **Unified report layout**: 5 advanced analysis components uniformly placed before "Cluster Basic Information"
- **Unified background color style**: All component block background colors unified to light gray (#f8f9fa)
- **Unified HTML and Word column structure**:
  - Thread Pool: 5 columns (Node Name, Thread Pool, Queue Size, Rejection Count, Status)
  - Shard Hotspot: 5 columns (Node Name, Load Index, CPU%, Disk%, Shard Count)
  - JVM Profile: 4 columns (Node Name, Heap Usage Rate, Used Heap Memory, Max Heap Memory)
- **Unified data sources and calculation logic**: HTML and Word reports use the same data sources and algorithms
  - Shard hotspots count shards from shards array, not node.shard_count
  - Load index calculation: Shards 40% + CPU 35% + Disk 25%
  - JVM data extracted from nodes_stats, automatically formatting byte units

### Fixed
- **Fixed configuration drift detection data missing**: Extract settings from nodes_raw, not NodeInfo object
- **Optimized shard allocation status display**: Properly handle ES returned 400 error response (indicating all shards are normal)
- **Optimized thread pool status judgment**: Determine overload based on rejection count > 100 or queue size > 1000
- **Fixed HTML report component display incompleteness**: All components always display containers, showing different content based on data conditions

### Technical Details
- Added 1 auxiliary function: `_add_advanced_analysis_to_word()` to generate Word format advanced analysis
- Modified 4 files:
  - `backend/app.py`: Word report generation + data merging
  - `backend/version.py`: Version number upgraded to 1.0.4
  - `es_insight/diagnostic_extractor.py`: Data extraction enhancement
  - `generate_html_report.py`: HTML report enhancement + style unification
- Lines of code: +~500 lines (including comments and blank lines)

## [1.0.3] - 2026-04-27
### Added
- **Added weighted dimension scoring system**: Introduced 6 major dimension categories and weight mechanisms, improving scoring precision
  - Cluster Health (25%), Node Performance (25%), Index Status (20%)
  - Performance Metrics (15%), Security Configuration (10%), Operations Status (5%)
- **Added three-level threshold linear interpolation algorithm**: Support degree scoring, distinguishing minor issues from serious issues
  - Normal range: 100 points
  - Warning range: 60-99 points (linear calculation)
  - Critical range: 0-59 points (linear calculation)
- **Added 4 configuration files**:
  - `configs/dimension_weights.yaml` - Dimension weight configuration
  - `configs/indicator_weights.yaml` - Indicator weight and threshold configuration
  - `configs/category_to_dimension.yaml` - Category to dimension mapping
  - Retained original `checkpoints_thresholds_complete.yaml`
- **Added scoring report details**: API returns detailed scores including dimension scores and 55 indicators
- **Added scoring method identification**: Distinguish new and old algorithms through `scoring_method` field
- **Added documentation**:
  - `doc/健康评分标准.md` - Complete scoring standard description
  - `doc/加权维度评分实施总结.md` - Implementation process summary
  - `doc/加权维度评分快速参考.md` - Quick reference guide

### Changed
- **Improved scoring algorithm**: Upgraded from simple category average to weighted dimension scoring
  - Old algorithm: Binary judgment (pass/fail), unable to distinguish problem severity
  - New algorithm: Degree scoring (0-100 continuous values), precisely reflecting problem severity
- **Optimized report structure**: health_score_report adds dimension_scores and indicator_details fields
- **Enhanced interpretability**: Users can view scores and weights for each dimension and indicator

### Fixed
- **Maintained backward compatibility**: Retained old algorithm as fallback plan, ensuring system stability
- **Data consistency guarantee**: Scoring completely based on check_results, fully consistent with problem counts displayed in reports
- **Comprehensive exception handling**: Use default configuration when configuration loading fails, automatically switch to old algorithm when scoring fails
- **Fixed dictionary type value handling**: Fixed type error when value of check items like `index_health.health_distribution` is a dictionary
  - Issue: Some check items have dictionary values (like health distribution), causing type errors during numerical calculations
  - Solution: Added dictionary type detection in `_calculate_single_indicator_score`, falling back to boolean scoring
- **Fixed dimension weight configuration parsing**: Fixed data structure issue when loading dimension weights from YAML configuration files
  - Issue: Each dimension in YAML configuration contains `weight` and `description` fields, but code expected simple numeric mapping
  - Solution: Extract `weight` field in `_load_dimension_weights`, convert to `{dimension: weight}` format
- **Fixed scoring logic causing all scores to be 100 points**:
  - Issue 1: Configuration file used category names, but code used dimension names for lookup, resulting in configuration not found
  - Solution: Modified `_get_indicator_config` method, try dimension name first, then category name
  - Issue 2: Default scoring logic unreasonable when no configuration (60 points even when failed)
  - Solution: Give different scores based on problem severity (0 points for serious issues, 60 points for general warnings)
- **Fixed inconsistency between list page and report page scores**:
  - Issue: List page read scores from database (old algorithm 97.33), report page read scores from JSON file (new algorithm 79)
  - Solution: Unified all pages to use new algorithm scores (`health_score_report.total_score`)
  - Implementation:
    - HTML report generator uses new algorithm scores
    - Word report generator uses new algorithm scores
    - Database saves new algorithm scores when task completes
  - Optimization: List page reads scores directly from database (good performance), no longer frequently reads JSON files

### Technical Details
- Added 9 auxiliary methods: Configuration loading, scoring calculation, linear interpolation, etc.
- Core method: `_calculate_weighted_dimension_score()`
- Support environment variable switching: `USE_WEIGHTED_SCORING` (default true)
- Lines of code: +267 lines (parse_check_result.py)

## [1.0.2] - 2026-04-22
### Added
- Introduced SQLite database, added task database saving functionality
- Added report output metrics

### Changed
- None

### Fixed
- None

## [1.0.1] - 2026-04-16
### Added
- Added version number management system
- Returned version information in health check interface

### Changed
- None

### Fixed
- None

## [1.0.0] - 2026-04-15
### Added
- Initial release
- Basic file upload and processing functionality
- Report generation and viewing functionality