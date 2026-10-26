# ES Insight Backend 变更日志

## 版本号修改位置
- 版本号定义在 `version.py` 文件中
- 修改 `VERSION` 变量即可更新版本号

## [1.0.10] - 2026-10-26
### Fixed
- **主分片合理性检查与明细表不一致**：诊断 JSON 使用 `primary_shards` 字段；超大主分片统计与「单个分片大于 40GB 索引」表对齐（`shard_size_check` / `diagnostic_extractor`）
- **Segment 过载恒为通过**：补全索引 segment 字段解析，按主分片平均 segment 数判定（阈值 `per_primary_shard: 35`），与诊断脚本 3.16 一致
- **搜索失败检查恒为「未发现」**：修正 `nodes_stats` 赋值逻辑，正确读取 `missing_total` 等节点统计（`nodes_stats_utils`）
- **Shards 检查阈值与展示**：超大物理分片阈值由 50GB 统一为 40GB；节点分片数 `value` 改为全集群单节点最大分片数，而非违规节点个数（`shard_node_stats`）
- **JVM 内存一致性 data 为 `-`**：识别 `data_hot`、`his` 等数据节点 role（`node_role_utils`），仅对数据节点做 JVM 一致性比对
- **分片延迟分配未配置仍通过**：未配置延迟分配策略时判定为不通过（`passed: false`）

### Changed
- **超大分片检查说明**：HTML/Word 报告在 shards 尺寸类检查中补充 detail/suggestion——「含主分片与副本，按物理分片条数统计」，与索引级主分片统计口径区分
- **阈值配置**：`checkpoints_thresholds_complete.yaml` 中 `oversized_primary`、`oversized_single_shard` 等与产品 40GB 口径对齐

### Added
- **巡检逻辑模块**：`shard_size_check.py`、`segment_check.py`、`nodes_stats_utils.py`、`shard_node_stats.py`、`node_role_utils.py`
- **单元测试**：`test_oversized_primary_shards.py`、`test_problem2_checks.py`、`test_problem3_shards_check.py`、`test_delayed_allocation_check.py`、`test_node_role_utils.py`

### Technical Details
- 核心解析与规则：`es_insight/parse_check_result.py`、`es_insight/diagnostic_extractor.py`、`es_insight/parsers/indices_parser.py`
- 后端报告：`backend/app.py` 中 Word 报告 suggestion 字段读取路径与 HTML 一致

## [1.0.9] - 2026-05-06
### Added
- **新增 Docker 化部署支持**：实现前后端容器化部署方案
  - 后端 Dockerfile：基于 Python 3.11-slim，优化镜像大小（~567MB）
  - 前端 Dockerfile：多阶段构建，使用 Nginx Alpine（~45MB）
  - docker-compose.yml：服务编排、健康检查、数据持久化
  - start.sh / stop.sh：一键启停脚本，兼容 Docker Compose V1/V2
  
- **完善数据持久化方案**：
  - Volume 挂载：uploads、out、reports、db 目录
  - 数据库文件单独映射，避免覆盖代码文件
  - 支持离线部署和数据备份恢复
  
- **新增内网离线部署文档**：
  - `内网离线Docker部署方案.md`：完整的打包、传输、部署流程
  - 支持无外网环境下的快速部署
  - 包含故障排查和运维指南

### Changed
- **优化依赖管理**：补充缺失的 Python 依赖包
  - 添加 `pandas>=1.3.0`：数据处理必需
  - 添加 `numpy>=1.20.0`：数值计算基础库
  - 添加 `pyyaml>=6.0`：YAML 配置文件解析
  - 添加 `jinja2>=3.0.0`：模板引擎
  - 添加 `orjson>=3.6.0`：高性能 JSON 处理
  
- **改进 Docker 构建配置**：
  - 使用清华 PyPI 镜像源加速依赖下载
  - WORKDIR 设置为 `/app/backend`，简化模块导入
  - 增加健康检查启动等待时间（40s）
  - 启用 Python 无缓冲输出（-u），实时显示日志

### Fixed
- **修复 Debian Trixie 包名问题**：
  - 将 `libgdk-pixbuf2.0-0` 改为 `libgdk-pixbuf-xlib-2.0-0`
  - 适配最新 Debian 版本的包名变化
  
- **修复 TypeScript 编译错误**：
  - 移除未使用的 Ant Design 组件导入（Empty, Row, Col）
  - 符合 TypeScript 严格模式要求
  
- **修复 Docker volume 挂载冲突**：
  - 只映射数据库文件，不覆盖 db_server 目录
  - 确保 Python 模块文件不被隐藏
  - 解决 ImportError: cannot import name 'db_manager'

### Technical Details
- 新增 8 个 Docker 相关文件：
  - `backend/Dockerfile`：后端镜像构建
  - `frontend/Dockerfile`：前端镜像构建
  - `frontend/nginx.conf`：Nginx 反向代理配置
  - `docker-compose.yml`：服务编排配置
  - `docker-compose.prod.yml`：生产环境配置
  - `.dockerignore`：构建忽略文件
  - `start.sh` / `stop.sh`：启停脚本
- 修改 3 个前端组件文件：
  - `AllocationFailureFlow.tsx`：移除 Empty 导入
  - `JVMMemoryChart.tsx`：移除 Row, Col 导入
  - `ShardHeatmap.tsx`：移除 Row, Col 导入
- 代码行数：+约800行（包含 Docker 配置和文档）

## [1.0.8] - 2026-04-30
### Added
- **新增多语言国际化支持**：系统全面支持法语、德语、俄语
  - 后端报告生成支持法语 (fr-FR)、德语 (de-DE)、俄语 (ru-RU)
  - 分批添加约1065个翻译键（静态翻译927个 + 动态短语138个）
  - 智能翻译函数 `translate_check_message()` 增强，支持46个常见短语映射
  
- **完善动态消息翻译机制**：实现智能分段匹配和自动翻译兜底
  - 扩展 `translations.py` 中的 `common_phrases` 字典
  - 按长度降序替换，确保长模式优先匹配
  - 正则表达式处理动态内容（数字、节点名、索引名等）
  - 特殊处理英文空格和格式

### Changed
- **优化HTML报告多语言显示**：显著减少未翻译中文文本
  - HTML报告未翻译文本从99个减少到34个（不含注释，66%改进）
  - 移除HTML注释后，实际可见的未翻译文本仅34个
  - 覆盖UI标签、存储文档、节点索引、分片、JVM、资源使用、检查详情等

### Fixed
- **修复翻译键缺失问题**：补充fr-FR、de-DE、ru-RU中缺失的关键翻译键
  - 分批次添加239个/语言的翻译键（共8批）
  - 修复单引号转义问题（法语中的撇号）
  - 确保所有静态文本都使用translate()函数

### Technical Details
- 修改核心文件：
  - `backend/i18n/translations.py`：添加1065个新翻译键，增强动态消息翻译
  - `generate_html_report.py`：确保正确调用translate_check_message()函数
- 新增辅助脚本：
  - `batch_add_translations_*.py`：8批批量添加翻译脚本
  - `enhance_dynamic_translation.py`：动态消息翻译增强脚本
  - `check_missing_*.py`：多个检查缺失翻译键的脚本
- 代码行数：+约3500行（包含翻译数据和脚本）

## [1.0.7] - 2026-04-30
### Added
- **完善日文国际化支持**：彻底解决报告中残留的中文翻译问题
  - 补充 `translations.py` 中缺失的 33 个静态翻译键（如数据来源、资源使用情况等）
  - 修复 `translations_map` 中重复定义导致的日文翻译缺失
  - 实现动态值“未知”的智能翻译逻辑，确保表格数据也能正确切换语言
  
- **优化索引数据源配置**：提升索引统计数据的准确性与一致性
  - 将索引基础信息数据源由 `indices.json` 替换为更精准的 `indices_stats.json`
  - 统一使用 `cat_shards.txt` 作为分片数量和大小统计的权威来源
  - 修正节点分片数字段名为 `shard_count`，确保前后端数据对齐

### Fixed
- **修复 HTML/Word 报告多语言显示不全问题**：
  - 解决元数据标签（提取时间、检查耗时等）在日文环境下仍显示中文的问题
  - 解决大标题（全部检查项详情等）未应用翻译函数的问题
  - 解决表格中硬编码中文值（如“未知”）无法随语言切换的问题
- **修复翻译层兜底机制**：增强 `translate_check_message` 对复杂动态字符串的匹配能力

### Technical Details
- 修改核心文件：
  - `backend/i18n/translations.py`：补全日文翻译映射表
  - `generate_html_report.py`：增加局部翻译辅助函数处理硬编码值
  - `es_insight/parsers/indices_parser.py`：优化数据提取逻辑
- 新增验证脚本：
  - `check_translations_map_japanese.py`：自动化检查翻译完整性
  - `test_unknown_translation.py`：验证特殊值翻译逻辑

## [1.0.6] - 2026-04-29
### Added
- **新增日语国际化支持**：系统全面支持日本語（ja-JP）
  - 后端报告生成支持日语翻译（HTML + Word）
  - 添加约370个日语翻译键，覆盖所有报告内容
  - 智能翻译函数支持日语文本处理
  
- **完善前端界面多语言**：前端UI完整支持4种语言
  - 简体中文 (zh-CN)、繁體中文 (zh-TW)、English (en-US)、日本語 (ja-JP)
  - 所有页面组件支持动态语言切换
  - i18next框架集成与配置优化

### Changed
- **优化Word报告文件命名策略**：修复语言切换缓存问题
  - 不同语言使用独立文件名：`{report_id}_{lang}.docx`
  - 解决切换语言后下载仍为旧语言的问题
  - 简体中文保持默认命名 `{report_id}.docx`
  
- **优化日语列表页文本长度**：缩短标签文本避免布局溢出
  - Task页面：スコア、アラート、L1/L2/L3（简洁表达）
  - History页面：スコア、アラート数
  - UI布局优化：紧凑间距、自动换行、半角冒号

### Fixed
- **修复Word报告语言切换Bug**：切换语言后下载的Word报告使用当前语言
  - 问题：所有语言共享同一文件名导致缓存冲突
  - 解决：根据语言参数生成不同文件名
- **修复前端日语翻译不完整**：补充所有页面的日语翻译资源
  - 完善7个JSON翻译文件（home, task, report, upload, history, settings, common）
  - 更新i18n初始化配置导入并注册日语资源

### Technical Details
- 修改5个核心文件：
  - `backend/app.py`：Word文件路径逻辑 + 下载文件名
  - `backend/i18n/translations.py`：添加日语翻译字典 + 智能翻译规则
  - `frontend/src/i18n/index.ts`：导入并注册日语资源
  - `frontend/src/i18n/config.ts`：添加日语到支持的语言列表
  - `frontend/src/components/Task/TaskList.tsx`：优化Tag布局
- 新增7个前端翻译文件：`frontend/src/i18n/locales/ja-JP/*.json`
- 代码行数：+约500行（包含注释和空行）

## [1.0.5] - 2026-04-27
### Added
- **新增三级告警分级系统**：引入severity_level验证级别，提升告警准确性和可操作性
  - 🔴 三级告警（必须处理）：severity_level=3，非常严重的问题，影响集群稳定性
  -  二级告警（建议处理）：severity_level=2，一般问题，建议优化处理
  - 🔵 一级告警（优化建议）：severity_level=1，不严重问题，可作为优化参考
- **新增告警统计字段**：在健康评分报告中增加各级别告警数量统计
  - `level_1_count`：一级告警（优化建议）数量
  - `level_2_count`：二级告警（建议处理）数量
  - `level_3_count`：三级告警（必须处理）数量
- **新增配置文件**：`configs/severity_level_weights.yaml` - 告警级别权重配置

### Changed
- **重构告警信息展示**：从“严重/警告”两级改为“三级/二级/一级”三级分类
  - HTML报告：告警信息按severity_level分组显示，使用不同颜色标识
  - Word报告：告警信息按severity_level分组显示，标题更明确
  - 列表页：显示各级别告警数量（level_1_count、level_2_count、level_3_count）
- **优化告警信息位置**：将告警信息从报告末尾移至“健康评分”之后、“高级分析组件”之前
  - 逻辑更清晰：从宏观（评分）到微观（具体告警），再到深度分析（5个组件）
  - 阅读更顺畅：用户先看整体评分，再看具体问题，最后看深度分析
- **统一HTML和Word告警结构**：HTML和Word报告使用相同的告警分级逻辑和显示方式
  - 均使用severity_level字段进行分组
  - 均显示问题描述、当前值、建议三部分

### Fixed
- **修复告警分级逻辑**：使用severity_level替代severity字段进行告警分组
  - 旧逻辑：使用severity字段（critical/warning），无法区分问题严重程度
  - 新逻辑：使用severity_level字段（1/2/3），精确反映问题严重性
- **完善数据库查询**：在任务列表接口中增加level_1_count、level_2_count、level_3_count字段查询
- **优化Word告警样式**：三级告警使用不同颜色（红色/黄色/蓝色）区分严重程度

### Technical Details
- 新增1个辅助函数：`_add_alerts_to_word()` 生成Word格式告警信息
- 修改6个文件：
  - `backend/app.py`：Word报告告警生成 + 列表页数据返回
  - `backend/version.py`：版本号升级为1.0.5
  - `generate_html_report.py`：HTML报告告警分级 + 样式优化
  - `configs/severity_level_weights.yaml`：新增告警级别权重配置
  - `frontend/.env.development` 和 `frontend/.env.production`：前端版本号升级
- 代码行数：+约150行（包含注释和空行）

## [1.0.4] - 2026-04-27
### Added
- **新增5个高级分析组件**：在HTML和Word报告中增加深度分析功能
  - ⚠️ 线程池队列堆积告警：监控线程池队列大小和拒绝数，识别过载线程池
  - 🔥 分片分布热点：基于分片数、CPU%、磁盘%计算负载指数，识别热点节点
  - 💾 JVM 内存画像：展示各节点JVM堆使用率、已用/最大堆内存
  - ⚙️ 配置漂移检测：对比节点关键配置参数，发现配置不一致问题
  - ✅ 分片分配状态：检测未分配分片并显示失败原因

### Changed
- **优化数据提取**：扩展diagnostic_extractor保存原始数据供高级分析使用
  - 保存 `nodes_raw`：完整的nodes.json数据，包含节点settings配置
  - 保存 `thread_pools`：从nodes_stats提取的线程池详细数据
  - 保存 `allocation_explain`：分片分配解释数据
- **统一报告布局**：5个高级分析组件统一放置在"集群基本信息"之前
- **统一背景色风格**：所有组件块背景色统一为浅灰色(#f8f9fa)
- **统一HTML和Word列结构**：
  - 线程池：5列（节点名称、线程池、队列大小、拒绝数、状态）
  - 分片热点：5列（节点名称、负载指数、CPU%、磁盘%、分片数）
  - JVM画像：4列（节点名称、堆使用率、已用堆内存、最大堆内存）
- **统一数据源和计算逻辑**：HTML和Word报告使用相同的数据源和算法
  - 分片热点从shards数组统计分片数，而非node.shard_count
  - 负载指数计算：分片40% + CPU 35% + 磁盘25%
  - JVM数据从nodes_stats提取，自动格式化字节单位

### Fixed
- **修复配置漂移检测数据缺失**：从nodes_raw中提取settings，而非NodeInfo对象
- **优化分片分配状态显示**：正确处理ES返回的400错误响应（表示所有分片正常）
- **优化线程池状态判断**：根据拒绝数>100或队列大小>1000判断为过载
- **修复HTML报告组件显示不全**：所有组件始终显示容器，根据数据情况显示不同内容

### Technical Details
- 新增1个辅助函数：`_add_advanced_analysis_to_word()` 生成Word格式高级分析
- 修改4个文件：
  - `backend/app.py`：Word报告生成 + 数据合并
  - `backend/version.py`：版本号升级为1.0.4
  - `es_insight/diagnostic_extractor.py`：数据提取增强
  - `generate_html_report.py`：HTML报告增强 + 样式统一
- 代码行数：+约500行（包含注释和空行）

## [1.0.3] - 2026-04-27
### Added
- **新增加权维度评分系统**：引入6大维度分类和权重机制，提升评分精度
  - 集群健康 (25%)、节点性能 (25%)、索引状态 (20%)
  - 性能指标 (15%)、安全配置 (10%)、运维状态 (5%)
- **新增三级阈值线性插值算法**：支持程度评分，区分轻微问题和严重问题
  - 正常范围：100分
  - 警告范围：60-99分（线性计算）
  - 严重范围：0-59分（线性计算）
- **新增4个配置文件**：
  - `configs/dimension_weights.yaml` - 维度权重配置
  - `configs/indicator_weights.yaml` - 指标权重和阈值配置
  - `configs/category_to_dimension.yaml` - 类别到维度映射
  - 保留原有 `checkpoints_thresholds_complete.yaml`
- **新增评分报告详情**：API返回包含维度得分和55个指标的详细得分
- **新增评分方法标识**：通过 `scoring_method` 字段区分新旧算法
- **新增文档**：
  - `doc/健康评分标准.md` - 完整的评分标准说明
  - `doc/加权维度评分实施总结.md` - 实施过程总结
  - `doc/加权维度评分快速参考.md` - 快速查阅指南

### Changed
- **改进评分算法**：从简单的类别平均分升级为加权维度评分
  - 旧算法：二元判断（通过/未通过），无法区分问题严重程度
  - 新算法：程度评分（0-100连续值），能精确反映问题严重性
- **优化报告结构**：health_score_report 增加 dimension_scores 和 indicator_details 字段
- **增强可解释性**：用户可以查看每个维度和指标的得分及权重

### Fixed
- **保持向后兼容**：保留旧算法作为回退方案，确保系统稳定性
- **数据一致性保证**：评分完全基于 check_results，与报告展示的问题数量完全一致
- **异常处理完善**：配置加载失败时使用默认配置，评分失败时自动切换到旧算法
- **修复字典类型value处理**：修复 `index_health.health_distribution` 等检查项的 value 为字典时的类型错误
  - 问题：某些检查项的 value 是字典（如健康分布），导致数值计算时出现类型错误
  - 解决：在 `_calculate_single_indicator_score` 中增加字典类型检测，回退到布尔型评分
- **修复维度权重配置解析**：修复从 YAML 配置文件加载维度权重时的数据结构问题
  - 问题：YAML 配置中每个维度包含 `weight` 和 `description` 字段，但代码期望的是简单数值映射
  - 解决：在 `_load_dimension_weights` 中提取 `weight` 字段，转换为 `{dimension: weight}` 格式
- **修复评分逻辑导致所有评分都是100分的问题**：
  - 问题1：配置文件使用类别名称，但代码使用维度名称查找，导致找不到配置
  - 解决：修改 `_get_indicator_config` 方法，先尝试维度名称，再尝试类别名称
  - 问题2：无配置时默认评分逻辑不合理（未通过也得60分）
  - 解决：根据问题严重程度给予不同分数（严重问题0分，一般警告60分）
- **修复列表页面和报告页面评分不一致的问题**：
  - 问题：列表页面从数据库读取评分（旧算法97.33），报告页面从JSON文件读取评分（新算法79）
  - 解决：统一所有页面使用新算法评分（`health_score_report.total_score`）
  - 实现：
    - HTML报告生成器使用新算法评分
    - Word报告生成器使用新算法评分
    - 任务完成时数据库保存新算法评分
  - 优化：列表页面直接从数据库读取评分（性能好），不再频繁读取JSON文件

### Technical Details
- 新增9个辅助方法：配置加载、评分计算、线性插值等
- 核心方法：`_calculate_weighted_dimension_score()`
- 支持环境变量切换：`USE_WEIGHTED_SCORING` (默认true)
- 代码行数：+267行（parse_check_result.py）

## [1.0.2] - 2026-04-22
### Added
- 引入了sqllite数据库，增加了任务数据库保存功能
- 增加报告输出指标

### Changed
- 无

### Fixed
- 无

## [1.0.1] - 2026-04-16
### Added
- 添加版本号管理系统
- 在健康检查接口中返回版本信息

### Changed
- 无

### Fixed
- 无

## [1.0.0] - 2026-04-15
### Added
- 初始版本发布
- 基本的文件上传和处理功能
- 报告生成和查看功能