"""全量提取文件解读日志生成器 - 记录每个文件的解读情况"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict


def generate_interpretation_log(extraction_json: str):
    """生成解读日志，记录每个文件的解读情况"""
    
    # 加载全量提取数据
    extraction_path = Path(extraction_json)
    with open(extraction_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    manifest = data.get('files_manifest', {})
    metadata = data.get('metadata', {})
    
    # 按类别分组文件
    file_categories = {
        'cluster_health': [
            'cluster_health.json',
            'cluster_stats.json',
            'cluster_state.json',
            'internal_health.json'
        ],
        'nodes_info': [
            'nodes.json',
            'nodes_short.json',
            'nodes_stats.json',
            'nodes_usage.json'
        ],
        'indices_info': [
            'indices.json',
            'indices_stats.json',
            'alias.json',
            'mapping.json',
            'templates.json',
            'index_templates.json',
            'component_templates.json'
        ],
        'shards_allocation': [
            'shards.json',
            'allocation.json',
            'allocation_explain.json',
            'allocation_explain_disk.json',
            'shard_stores.json',
            'recovery.json'
        ],
        'cluster_settings': [
            'cluster_settings.json',
            'cluster_settings_defaults.json',
            'settings.json',
            'plugins.json',
            'version.json',
            'licenses.json'
        ],
        'tasks_operations': [
            'tasks.json',
            'cluster_pending_tasks.json',
            'master.json'
        ],
        'statistics': [
            'count.json',
            'fielddata.json',
            'fielddata_stats.json',
            'segments.json',
            'geoip_stats.json'
        ],
        'snapshots_repositories': [
            'snapshot.json',
            'repositories.json',
            'remote_cluster_info.json'
        ],
        'security': [
            'commercial/security_users.json',
            'commercial/security_roles.json',
            'commercial/security_priv.json',
            'commercial/security_role_mappings.json'
        ],
        'ml_features': [
            'commercial/ml_anomaly_detectors.json',
            'commercial/ml_datafeeds.json',
            'commercial/ml_datafeeds_stats.json',
            'commercial/ml_dataframe.json',
            'commercial/ml_dataframe_stats.json',
            'commercial/ml_info.json',
            'commercial/ml_stats.json',
            'commercial/ml_trained_models.json',
            'commercial/ml_trained_models_stats.json'
        ],
        'ilm_lifecycle': [
            'commercial/ilm_policies.json',
            'commercial/ilm_status.json',
            'commercial/ilm_explain.json',
            'commercial/ilm_explain_only_errors.json'
        ],
        'ccr_cross_cluster': [
            'commercial/ccr_autofollow_patterns.json',
            'commercial/ccr_follower_info.json',
            'commercial/ccr_stats.json',
            'commercial/data_stream.json'
        ],
        'slm_snapshot_lifecycle': [
            'commercial/slm_policies.json',
            'commercial/slm_stats.json',
            'commercial/slm_status.json'
        ],
        'transform': [
            'commercial/transform.json',
            'commercial/transform_stats.json'
        ],
        'enrich': [
            'commercial/enrich_policies.json',
            'commercial/enrich_stats.json'
        ],
        'watcher_alerting': [
            'commercial/watcher_stack.json',
            'commercial/watcher_stats.json'
        ],
        'rollup': [
            'commercial/rollup_jobs.json'
        ],
        'autoscaling': [
            'commercial/autoscaling_capacity.json'
        ],
        'logstash': [
            'commercial/logstash_pipeline.json'
        ],
        'profiling': [
            'commercial/profiling_status.json'
        ],
        'searchable_snapshots': [
            'commercial/searchable_snapshots_cache_stats.json'
        ],
        'other': [
            'dangling_indices.json',
            'diagnostic_manifest.json',
            'manifest.json',
            'pipelines.json',
            'ssl_certs.json',
            'internal_desired_balance.json',
            'commercial/nodes_shutdown_status.json',
            'commercial/xpack.json'
        ]
    }
    
    # 统计信息
    total_files = len(manifest)
    interpreted_files = []
    not_found_files = []
    
    log_lines = []
    log_lines.append("="*100)
    log_lines.append("ES 集群全量诊断数据 - 文件解读日志")
    log_lines.append("="*100)
    log_lines.append("")
    log_lines.append(f"数据来源：{metadata.get('source', 'N/A')}")
    log_lines.append(f"提取时间：{metadata.get('extracted_at', 'N/A')}")
    log_lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_lines.append(f"总文件数：{total_files}")
    log_lines.append(f"原始大小：{metadata.get('total_size_mb', 0):.2f} MB")
    log_lines.append("")
    
    # 按类别输出
    log_lines.append("-"*100)
    log_lines.append("文件解读详情（按功能分类）")
    log_lines.append("-"*100)
    
    files_by_category = {}
    
    for category, expected_files in file_categories.items():
        category_files = []
        
        for filename in expected_files:
            # 在 manifest 中查找匹配的文件
            found = False
            actual_path = None
            
            for path in manifest.keys():
                if path.endswith(filename) or path == filename:
                    found = True
                    actual_path = path
                    file_info = manifest[path]
                    
                    size_kb = file_info.get('size', 0) / 1024
                    compressed_kb = file_info.get('compressed_size', 0) / 1024
                    
                    category_files.append({
                        'filename': filename,
                        'actual_path': actual_path,
                        'size_kb': size_kb,
                        'compressed_kb': compressed_kb,
                        'has_data': 'data' in file_info
                    })
                    interpreted_files.append(filename)
                    break
            
            if not found:
                # 记录未找到的文件
                not_found_files.append(filename)
        
        if category_files:
            files_by_category[category] = category_files
    
    # 输出每个类别的文件
    for category, files in files_by_category.items():
        category_name_cn = {
            'cluster_health': '集群健康',
            'nodes_info': '节点信息',
            'indices_info': '索引信息',
            'shards_allocation': '分片分配',
            'cluster_settings': '集群设置',
            'tasks_operations': '任务操作',
            'statistics': '统计数据',
            'snapshots_repositories': '快照和仓库',
            'security': '安全功能',
            'ml_features': '机器学习',
            'ilm_lifecycle': '索引生命周期管理',
            'ccr_cross_cluster': '跨集群复制',
            'slm_snapshot_lifecycle': '快照生命周期管理',
            'transform': '数据转换',
            'enrich': '数据丰富',
            'watcher_alerting': '监控告警',
            'rollup': '数据汇总',
            'autoscaling': '自动扩容',
            'logstash': 'Logstash',
            'profiling': '性能分析',
            'searchable_snapshots': '可搜索快照',
            'other': '其他'
        }.get(category, category)
        
        log_lines.append("")
        log_lines.append(f"【{category_name_cn}】 ({len(files)} 个文件)")
        log_lines.append("-"*50)
        
        for i, file_info in enumerate(files, 1):
            filename = file_info['filename']
            size_kb = file_info['size_kb']
            has_data = file_info['has_data']
            
            status = "✅ 已解读" if has_data else "⚠️ 仅元数据"
            log_lines.append(f"{i:2}. {status} - {filename:<50} ({size_kb:>8.1f} KB)")
    
    # 未找到的文件
    if not_found_files:
        log_lines.append("")
        log_lines.append("-"*100)
        log_lines.append("未在诊断包中找到的文件")
        log_lines.append("-"*50)
        for i, filename in enumerate(not_found_files, 1):
            log_lines.append(f"{i:2}. ❌ {filename}")
    
    # 统计总结
    log_lines.append("")
    log_lines.append("="*100)
    log_lines.append("解读统计总结")
    log_lines.append("="*100)
    log_lines.append(f"总文件数：{total_files}")
    log_lines.append(f"成功解读：{len(interpreted_files)} 个")
    log_lines.append(f"未找到：{len(not_found_files)} 个")
    log_lines.append(f"解读率：{len(interpreted_files)/total_files*100:.1f}%")
    log_lines.append("")
    
    # 按类别统计
    log_lines.append("按类别统计:")
    for category, files in files_by_category.items():
        category_name_cn = {
            'cluster_health': '集群健康',
            'nodes_info': '节点信息',
            'indices_info': '索引信息',
            'shards_allocation': '分片分配',
            'cluster_settings': '集群设置',
            'tasks_operations': '任务操作',
            'statistics': '统计数据',
            'snapshots_repositories': '快照和仓库',
            'security': '安全功能',
            'ml_features': '机器学习',
            'ilm_lifecycle': '索引生命周期管理',
            'ccr_cross_cluster': '跨集群复制',
            'slm_snapshot_lifecycle': '快照生命周期管理',
            'transform': '数据转换',
            'enrich': '数据丰富',
            'watcher_alerting': '监控告警',
            'rollup': '数据汇总',
            'autoscaling': '自动扩容',
            'logstash': 'Logstash',
            'profiling': '性能分析',
            'searchable_snapshots': '可搜索快照',
            'other': '其他'
        }.get(category, category)
        
        log_lines.append(f"  - {category_name_cn}: {len(files)} 个文件")
    
    log_lines.append("")
    log_lines.append("="*100)
    log_lines.append("详细文件列表（按字母顺序）")
    log_lines.append("="*100)
    
    # 根目录文件
    root_files = [f for f in manifest.keys() if '/' not in f or f.count('/') == 1]
    subdir_files = [f for f in manifest.keys() if '/' in f and f.count('/') > 1]
    
    log_lines.append("")
    log_lines.append(f"根目录文件 ({len(root_files)} 个):")
    log_lines.append("-"*50)
    for i, filename in enumerate(sorted(root_files), 1):
        size_kb = manifest[filename].get('size', 0) / 1024
        log_lines.append(f"{i:3}. {filename:<50} ({size_kb:>8.1f} KB)")
    
    log_lines.append("")
    log_lines.append(f"子目录文件 ({len(subdir_files)} 个):")
    log_lines.append("-"*50)
    for i, filename in enumerate(sorted(subdir_files), 1):
        size_kb = manifest[filename].get('size', 0) / 1024
        dirname = '/'.join(filename.split('/')[:-1])
        basename = filename.split('/')[-1]
        log_lines.append(f"{i:3}. [{dirname}] {basename:<45} ({size_kb:>8.1f} KB)")
    
    log_lines.append("")
    log_lines.append("="*100)
    log_lines.append("日志结束")
    log_lines.append("="*100)
    
    return '\n'.join(log_lines)


def main():
    """主函数"""
    from pathlib import Path
    
    # 查找最新的全量提取文件
    out_dir = Path("out")
    extraction_files = sorted(out_dir.glob("full_extraction_*.json"))
    
    if not extraction_files:
        print("❌ 未找到全量提取文件")
        print("请先运行：python -m es_insight.full_diagnostic_extractor")
        return
    
    latest_file = extraction_files[-1]
    print(f"使用文件：{latest_file.name}")
    
    # 生成解读日志
    log_content = generate_interpretation_log(str(latest_file))
    
    # 保存日志
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = out_dir / f"interpretation_log_{timestamp}.txt"
    
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(log_content)
    
    print(f"\n✅ 解读日志已生成：{log_path}")
    print(f"\n日志摘要:")
    print("="*60)
    
    # 打印前 50 行
    lines = log_content.split('\n')
    for line in lines[:50]:
        print(line)
    
    print("\n..." + "="*60)
    print(f"完整日志请查看：{log_path}")
    print(f"总行数：{len(lines)}")


if __name__ == '__main__':
    main()
