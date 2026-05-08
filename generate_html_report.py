"""根据 check_result JSON 生成 HTML 巡检报告"""

import json
from pathlib import Path
from datetime import datetime


def _generate_advanced_analysis_html(json_data: dict, lang: str = 'zh-CN') -> str:
    """
    生成高级分析组件HTML（线程池、热力图、JVM、配置漂移、分配失败）
    
    Args:
        json_data: 完整的报告JSON数据
        lang: 语言代码 (zh-CN, zh-TW, en-US)，默认中文
        
    Returns:
        HTML字符串
    """
    from backend.i18n.translations import translate
    html_parts = []
    
    # 1. 线程池队列堆积告警
    thread_pools = json_data.get('thread_pools', [])
    
    # 找出过载的线程池
    critical_pools = [p for p in thread_pools if p.get('queue_size', 0) > 1000 or p.get('rejected', 0) > 100]
    
    html_parts.append('<div class="section" style="background: #f8f9fa; padding: 20px; margin-bottom: 20px;">')
    thread_pool_title = translate('report.html.thread_pool.title', lang)
    html_parts.append(f'<h2 class="section-title">⚠️ {thread_pool_title}</h2>')
    
    if critical_pools:
        node_name_label = translate('report.html.thread_pool.node_name', lang)
        pool_name_label = translate('report.html.thread_pool.pool_name', lang)
        queue_size_label = translate('report.html.thread_pool.queue_size', lang)
        rejected_label = translate('report.html.thread_pool.rejected', lang)
        status_label = translate('report.html.thread_pool.status', lang)
        html_parts.append(f'''
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                <thead>
                    <tr style="background: #ffc107; color: white;">
                        <th style="padding: 10px; text-align: left;">{node_name_label}</th>
                        <th style="padding: 10px; text-align: left;">{pool_name_label}</th>
                        <th style="padding: 10px; text-align: right;">{queue_size_label}</th>
                        <th style="padding: 10px; text-align: right;">{rejected_label}</th>
                        <th style="padding: 10px; text-align: center;">{status_label}</th>
                    </tr>
                </thead>
                <tbody>
        ''')
        
        for pool in critical_pools:
            queue_size = pool.get('queue_size', 0)
            rejected = pool.get('rejected', 0)
            overloaded_text = translate('report.html.thread_pool.overloaded', lang)
            normal_text = translate('report.html.thread_pool.normal', lang)
            status_color = '#dc3545' if (queue_size > 1000 or rejected > 100) else '#28a745'
            status_text = overloaded_text if (queue_size > 1000 or rejected > 100) else normal_text
            
            html_parts.append(f'''
                    <tr style="border-bottom: 1px solid #dee2e6;">
                        <td style="padding: 10px;">{pool.get('node_name', 'N/A')}</td>
                        <td style="padding: 10px;">{pool.get('name', 'N/A')}</td>
                        <td style="padding: 10px; text-align: right;">{queue_size:,}</td>
                        <td style="padding: 10px; text-align: right; color: {'red' if rejected > 0 else 'green'};">{rejected:,}</td>
                        <td style="padding: 10px; text-align: center;"><span style="color: {status_color}; font-weight: bold;">{status_text}</span></td>
                    </tr>
            ''')
        
        html_parts.append('''
                </tbody>
            </table>
        ''')
    else:
        if thread_pools:
            all_normal_text = translate('report.html.thread_pool.all_normal', lang)
            html_parts.append(f'<p style="color: #856404; margin-top: 10px;">✅ {all_normal_text}</p>')
        else:
            no_data_text = translate('report.html.thread_pool.no_data', lang)
            html_parts.append(f'<p style="color: #856404; margin-top: 10px;">ℹ️ {no_data_text}</p>')
    
    html_parts.append('</div>')
    
    # 2. 分片分布热点
    nodes_stats = json_data.get('nodes_stats', {})
    shards = json_data.get('shards', [])
    nodes = json_data.get('nodes', [])
    
    if nodes and shards:
        # 计算每个节点的负载指数
        node_shard_count = {}
        for shard in shards:
            node = shard.get('node', '')
            if node:
                node_shard_count[node] = node_shard_count.get(node, 0) + 1
        
        heatmap_data = []
        for node in nodes:
            node_name = node.get('name', '')
            shard_count = node_shard_count.get(node_name, 0)
            cpu = node.get('cpu_percent', 0)
            disk = node.get('disk_used_percent', 0)
            
            # 计算负载指数 (分片40% + CPU 35% + 磁盘25%)
            load_index = min(shard_count / 1000 * 100, 100) * 0.4 + min(cpu, 100) * 0.35 + min(disk, 100) * 0.25
            
            heatmap_data.append({
                'node_name': node_name,
                'load_index': round(load_index, 2),
                'cpu': cpu,
                'disk': disk,
                'shard_count': shard_count
            })
        
        # 按负载指数排序
        heatmap_data.sort(key=lambda x: x['load_index'], reverse=True)
        
        shard_heatmap_title = translate('report.shard_heatmap.title', lang)
        node_name_label = translate('report.nodes.headers.name', lang)
        load_index_label = translate('report.shard_heatmap.load_index', lang)
        cpu_label = translate('report.shard_heatmap.cpu', lang)
        disk_label = translate('report.shard_heatmap.disk', lang)
        shard_count_label = translate('report.nodes.headers.shards', lang)
        
        html_parts.append(f'''
        <div class="section" style="background: #f8f9fa; padding: 20px; margin-bottom: 20px;">
            <h2 class="section-title">🔥 {shard_heatmap_title}</h2>
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                <thead>
                    <tr style="background: #6c757d; color: white;">
                        <th style="padding: 10px; text-align: left;">{node_name_label}</th>
                        <th style="padding: 10px; text-align: right;">{load_index_label}</th>
                        <th style="padding: 10px; text-align: right;">{cpu_label}</th>
                        <th style="padding: 10px; text-align: right;">{disk_label}</th>
                        <th style="padding: 10px; text-align: right;">{shard_count_label}</th>
                    </tr>
                </thead>
                <tbody>
        ''')
        
        for data in heatmap_data[:10]:  # 只显示前10个
            load_index = data['load_index']
            color = '#dc3545' if load_index > 90 else ('#ffc107' if load_index > 70 else '#28a745')
            
            html_parts.append(f'''
                    <tr style="border-bottom: 1px solid #dee2e6;">
                        <td style="padding: 10px;">{data['node_name']}</td>
                        <td style="padding: 10px; text-align: right;">
                            <div style="background: #e9ecef; border-radius: 10px; overflow: hidden;">
                                <div style="width: {min(load_index, 100)}%; background: {color}; padding: 5px 10px; color: white; text-align: right; font-weight: bold;">
                                    {load_index:.1f}
                                </div>
                            </div>
                        </td>
                        <td style="padding: 10px; text-align: right;">{data['cpu']:.1f}%</td>
                        <td style="padding: 10px; text-align: right;">{data['disk']:.1f}%</td>
                        <td style="padding: 10px; text-align: right;">{data['shard_count']}</td>
                    </tr>
            ''')
        
        html_parts.append('''
                </tbody>
            </table>
        </div>
        ''')
    
    # 3. JVM 内存画像
    if nodes_stats and isinstance(nodes_stats, dict):
        jvm_profiles = []
        nodes_dict = nodes_stats.get('nodes', {})
        
        for node_id, stats in nodes_dict.items():
            jvm = stats.get('jvm', {})
            mem = jvm.get('mem', {})
            if mem:
                node_name = stats.get('name', node_id)
                heap_percent = mem.get('heap_used_percent', 0)
                heap_used = mem.get('heap_used_in_bytes', 0)
                heap_max = mem.get('heap_max_in_bytes', 0)
                
                # 格式化字节
                def format_bytes(b):
                    if b == 0: return '0 B'
                    k = 1024
                    sizes = ['B', 'KB', 'MB', 'GB']
                    i = int(__import__('math').floor(__import__('math').log(b) / __import__('math').log(k)))
                    return f"{b / pow(k, i):.2f} {sizes[i]}"
                
                jvm_profiles.append({
                    'node_name': node_name,
                    'heap_percent': heap_percent,
                    'heap_used': format_bytes(heap_used),
                    'heap_max': format_bytes(heap_max)
                })
        
        if jvm_profiles:
            jvm_profile_title = translate('report.jvm_profile.title', lang)
            node_name_label = translate('report.nodes.headers.name', lang)
            heap_usage_label = translate('report.jvm_profile.heap_usage', lang)
            heap_used_label = translate('report.jvm_profile.heap_used', lang)
            heap_max_label = translate('report.jvm_profile.heap_max', lang)
            
            html_parts.append(f'''
            <div class="section" style="background: #f8f9fa; padding: 20px; margin-bottom: 20px;">
                <h2 class="section-title">💾 {jvm_profile_title}</h2>
                <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                    <thead>
                        <tr style="background: #007bff; color: white;">
                            <th style="padding: 10px; text-align: left;">{node_name_label}</th>
                            <th style="padding: 10px; text-align: right;">{heap_usage_label}</th>
                            <th style="padding: 10px; text-align: right;">{heap_used_label}</th>
                            <th style="padding: 10px; text-align: right;">{heap_max_label}</th>
                        </tr>
                    </thead>
                    <tbody>
            ''')
            
            for profile in jvm_profiles:
                heap_percent = profile['heap_percent']
                color = '#dc3545' if heap_percent > 85 else ('#ffc107' if heap_percent > 75 else '#28a745')
                
                html_parts.append(f'''
                        <tr style="border-bottom: 1px solid #dee2e6;">
                            <td style="padding: 10px;">{profile['node_name']}</td>
                            <td style="padding: 10px; text-align: right;">
                                <div style="background: #e9ecef; border-radius: 10px; overflow: hidden;">
                                    <div style="width: {min(heap_percent, 100)}%; background: {color}; padding: 5px 10px; color: white; text-align: right; font-weight: bold;">
                                        {heap_percent:.1f}%
                                    </div>
                                </div>
                            </td>
                            <td style="padding: 10px; text-align: right;">{profile['heap_used']}</td>
                            <td style="padding: 10px; text-align: right;">{profile['heap_max']}</td>
                        </tr>
                ''')
            
            html_parts.append('''
                    </tbody>
                </table>
            </div>
            ''')
    
    # 4. 配置漂移检测
    # 从 nodes_raw 中获取完整的节点配置信息
    nodes_raw = json_data.get('nodes_raw', {})
    nodes_with_settings = []
    
    if nodes_raw and isinstance(nodes_raw, dict) and 'nodes' in nodes_raw:
        raw_nodes = nodes_raw.get('nodes', {})
        for node_id, node_data in raw_nodes.items():
            settings = node_data.get('settings', {})
            if settings:
                nodes_with_settings.append({
                    'name': node_data.get('name', node_id),
                    'settings': settings
                })
    
    html_parts.append('<div class="section" style="background: #f8f9fa; padding: 20px; margin-bottom: 20px;">')
    config_drift_title = translate('report.config_drift.title', lang)
    html_parts.append(f'<h2 class="section-title">⚙️ {config_drift_title}</h2>')
    
    if len(nodes_with_settings) > 1:
        # 简化的配置漂移检测（只检查几个关键参数）
        critical_params = [
            'thread_pool.search.size',
            'thread_pool.write.size',
            'indices.queries.cache.size'
        ]
        
        drifts_found = False
        
        for param in critical_params:
            values_by_node = {}
            for node in nodes_with_settings:
                node_name = node.get('name', '')
                settings = node.get('settings', {})
                
                # 从嵌套配置中提取值
                keys = param.split('.')
                current = settings
                for key in keys:
                    if isinstance(current, dict):
                        current = current.get(key)
                    else:
                        current = None
                        break
                
                if current is not None:
                    values_by_node[node_name] = str(current)
            
            if len(values_by_node) > 1:
                # 检查是否有不一致
                unique_values = set(values_by_node.values())
                if len(unique_values) > 1:
                    drifts_found = True
                    majority_value = max(set(values_by_node.values()), key=list(values_by_node.values()).count)
                    drifted_nodes = {k: v for k, v in values_by_node.items() if v != majority_value}
                    
                    html_parts.append(f'''
                    <div style="margin-top: 15px; padding: 10px; background: white; border-left: 3px solid #ffc107;">
                        <strong>{translate('report.common.index', lang)}:</strong> <code>{param}</code><br>
                        <strong>{translate('report.common.default_value', lang)}:</strong> <code>{majority_value}</code><br>
                        <strong>{translate('report.config_drift.inconsistent_nodes', lang)}:</strong>
                        <ul style="margin: 5px 0;">
                    ''')
                    
                    for node_name, actual_value in drifted_nodes.items():
                        html_parts.append(f'<li>{node_name}: <code>{actual_value}</code></li>')
                    
                    html_parts.append('''
                        </ul>
                    </div>
                    ''')
        
        if not drifts_found:
            all_consistent_text = translate('report.config_drift.all_consistent', lang)
            html_parts.append(f'<p style="color: #28a745; margin-top: 10px;">✅ {all_consistent_text}</p>')
    else:
        no_data_text = translate('report.config_drift.no_data', lang)
        html_parts.append(f'<p style="color: #856404; margin-top: 10px;">ℹ️ {no_data_text}</p>')
    
    html_parts.append('</div>')
    
    # 5. 分片分配状态
    allocation_explain = json_data.get('allocation_explain', {})
    
    html_parts.append('<div class="section" style="background: #f8f9fa; padding: 20px; margin-bottom: 20px;">')
    shard_allocation_title = translate('report.shard_allocation.title', lang)
    html_parts.append(f'<h2 class="section-title">✅ {shard_allocation_title}</h2>')
    
    # 检查是否有分配失败（有 index 字段表示有未分配的分片）
    has_failures = allocation_explain and isinstance(allocation_explain, dict) and 'index' in allocation_explain
    
    # 检查是否是错误响应（所有分片正常时ES会返回400错误）
    is_error_response = allocation_explain and isinstance(allocation_explain, dict) and 'error' in allocation_explain
    
    if has_failures:
        # 有分片分配失败
        index_name = allocation_explain.get('index', 'N/A')
        shard_id = allocation_explain.get('shard', 'N/A')
        
        reasons = []
        unassigned_info = allocation_explain.get('unassigned_info', {})
        if unassigned_info:
            unassigned_reason_label = translate('report.common.unassigned_reason', lang)
            unknown_text = translate('report.common.unknown', lang)
            reasons.append(f"{unassigned_reason_label}: {unassigned_info.get('reason', unknown_text)}")
        
        node_decisions = allocation_explain.get('node_allocation_decisions', [])
        for decision in node_decisions:
            node_name = decision.get('node_name', '')
            deciders = decision.get('deciders', [])
            for decider in deciders:
                if decider.get('decision') == 'NO':
                    node_label = translate('report.common.node', lang)
                    reasons.append(f"{node_label} {node_name}: {decider.get('explanation', '')}")
        
        if reasons:
            html_parts.append('<div style="background: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin-top: 10px; border-radius: 5px;">')
            index_label = translate('report.shard_allocation.index_label', lang)
            shard_label = translate('report.shard_allocation.shard_label', lang)
            html_parts.append(f'<p><strong>{index_label}:</strong> {index_name}, <strong>{shard_label}:</strong> {shard_id}</p>')
            failure_title = translate('report.shard_allocation.failure_title', lang)
            html_parts.append(f'<h4 style="margin-top: 10px;">{failure_title}:</h4>')
            html_parts.append('<ul>')
            
            for reason in reasons:
                html_parts.append(f'<li>{reason}</li>')
            
            html_parts.append('</ul>')
            html_parts.append('</div>')
        else:
            all_normal_text = translate('report.shard_allocation.all_normal', lang)
            html_parts.append(f'<p style="color: #155724; margin-top: 10px;">✅ {all_normal_text}</p>')
            html_parts.append('</div>')
    elif is_error_response:
        # 错误响应表示所有分片都已正常分配
        all_normal_text = translate('report.shard_allocation.all_normal', lang)
        html_parts.append(f'<p style="color: #155724; margin-top: 10px;">✅ {all_normal_text}</p>')
        html_parts.append('</div>')
    else:
        # 无 allocation_explain 数据
        all_normal_or_no_data = translate('report.shard_allocation.all_normal_or_no_data', lang)
        html_parts.append(f'<p style="color: #155724; margin-top: 10px;">✅ {all_normal_or_no_data}</p>')
        html_parts.append('</div>')
    
    return '\n'.join(html_parts)


def generate_issues_html(health_score_report: dict, lang: str = 'zh-CN') -> str:
    """生成健康评分问题清单HTML"""
    from backend.i18n.translations import translate, translate_check_message
    
    if not health_score_report:
        return ''
    
    issues = health_score_report.get('issues', [])
    if not issues:
        return ''
    
    # 按严重程度分组问题
    critical_issues = [issue for issue in issues if issue.get('severity') == 'critical']
    warning_issues = [issue for issue in issues if issue.get('severity') == 'warning']
    
    unknown_issue = translate('report.common.unknown_issue', lang)
    current_value_label = translate('report.common.current_value_label', lang)
    suggestion_label = translate('report.common.suggestion_label', lang)
    
    html = f'''
        <div class="section" style="padding: 30px; background: #f8f9fa; border-bottom: 3px solid #f0f0f0;">
            <h2 class="section-title">🔍 {translate('report.check_details.title', lang)}</h2>
    '''
    
    # 列出严重问题
    if critical_issues:
        html += f'''
            <div class="alert-box alert-critical">
                <h3>🔴 {translate('report.check_details.critical_issues', lang)}</h3>
                <ul style="margin-top: 10px; margin-left: 20px;">
        '''
        for issue in critical_issues:
            # 智能翻译 description 和 suggestion
            description = translate_check_message(issue.get('description', unknown_issue), lang)
            suggestion = translate_check_message(issue.get('suggestion', ''), lang) if issue.get('suggestion') else ''
            value_part = f" ({current_value_label}: {issue.get('value', '')})" if issue.get('value') is not None else ""
            suggestion_part = f"<br><strong>{suggestion_label}:</strong> {suggestion}" if suggestion else ""
            html += f'''
                    <li style="margin: 8px 0;">
                        <strong>{description}</strong>{value_part}{suggestion_part}
                    </li>
            '''
        html += '''
                </ul>
            </div>
        '''
    
    # 列出警告问题
    if warning_issues:
        html += f'''
            <div class="alert-box alert-warning">
                <h3>🟡 {translate('report.check_details.warning_issues', lang)}</h3>
                <ul style="margin-top: 10px; margin-left: 20px;">
        '''
        for issue in warning_issues:
            # 智能翻译 description 和 suggestion
            description = translate_check_message(issue.get('description', unknown_issue), lang)
            suggestion = translate_check_message(issue.get('suggestion', ''), lang) if issue.get('suggestion') else ''
            value_part = f" ({current_value_label}: {issue.get('value', '')})" if issue.get('value') is not None else ""
            suggestion_part = f"<br><strong>{suggestion_label}:</strong> {suggestion}" if suggestion else ""
            html += f'''
                    <li style="margin: 8px 0;">
                        <strong>{description}</strong>{value_part}{suggestion_part}
                    </li>
            '''
        html += '''
                </ul>
            </div>
        '''
    
    html += '''
        </div>
    '''
    
    return html


def generate_html_report(json_data: dict, lang: str = 'zh-CN') -> str:
    """生成 HTML 格式巡检报告
    
    Args:
        json_data: 完整的报告JSON数据
        lang: 语言代码 (zh-CN, zh-TW, en-US)，默认中文
    """
    from backend.i18n.translations import translate, translate_check_message
    
    basic_info = json_data.get('basic_info', {})
    alerts = json_data.get('alerts', {})
    check_results = json_data.get('check_results', {})  # 新增：所有检查项结果
    shard_summaries = json_data.get('shard_summaries', [])  # 新增：分片汇总信息
    
    cluster_info = basic_info.get('cluster_info', {})
    health_summary = basic_info.get('health_summary', {})
    node_summary = basic_info.get('node_summary', {})
    index_summary = basic_info.get('index_summary', {})
    check_metadata = basic_info.get('check_metadata', {})
    nodes_detail = basic_info.get('nodes_detail', [])  # 新增：节点详细信息
    
    alert_summary = alerts.get('summary', {})
    critical_alerts = alerts.get('critical_alerts', [])
    warning_alerts = alerts.get('warning_alerts', [])
    
    # 从健康评分详细报告中获取异常问题统计
    health_score_report = json_data.get('health_score_report', {})
    if health_score_report:
        summary_info = health_score_report.get('summary', {})
        critical_issues = summary_info.get('critical_issues_count', 0)
        warning_issues = summary_info.get('warning_issues_count', 0)
        total_issues = summary_info.get('total_issues_count', 0)
        level_1_count = summary_info.get('level_1_count', 0)
        level_2_count = summary_info.get('level_2_count', 0)
        level_3_count = summary_info.get('level_3_count', 0)
    else:
        # 如果没有详细报告，使用旧的告警数据
        critical_issues = alert_summary.get('critical', 0)
        warning_issues = alert_summary.get('warning', 0)
        total_issues = critical_issues + warning_issues
        level_1_count = 0
        level_2_count = 0
        level_3_count = 0
    
    # ===== 生成高级分析组件HTML =====
    advanced_analysis_html = _generate_advanced_analysis_html(json_data, lang=lang)
    
    # 生成状态标识
    status_emoji = "✅" if cluster_info.get('status') == 'GREEN' else ("⚠️" if cluster_info.get('status') == 'YELLOW' else "❌")
    
    # 优先使用健康评分报告中的评分（新算法），回退到旧算法
    if health_score_report:
        health_score = health_score_report.get('total_score', alert_summary.get('health_score', 0))
    else:
        health_score = alert_summary.get('health_score', 0)
    
    score_color = "#28a745" if health_score >= 90 else ("#ffc107" if health_score >= 70 else "#dc3545")
    
    # 翻译常用文本
    diagnosis_time_label = translate('report.html.diagnosis_time', lang)
    health_score_label = translate('report.html.health_score_label', lang)
    alerts_total_label = translate('report.html.alerts.total', lang)
    alerts_level_1_label = translate('report.html.alerts.level_1', lang)
    alerts_level_2_label = translate('report.html.alerts.level_2', lang)
    alerts_level_3_label = translate('report.html.alerts.level_3', lang)
    alerts_title = translate('report.html.alerts.title', lang)
    cluster_basic_info_title = translate('report.html.cluster.basic_info', lang)
    health_summary_title = translate('report.html.health_summary.title', lang)
    report_title = translate('report.title', lang)
    
    # 生成节点基本信息表格 HTML
    nodes_table_html = _generate_nodes_basic_table(nodes_detail, lang=lang)
    
    # 生成分片基本信息表格 HTML
    shard_distribution = json_data.get('shard_distribution', {})
    large_shards = json_data.get('large_shards', [])
    small_shards_info = json_data.get('small_shards_with_multiple_primaries', {})
    shards_table_html = _generate_shards_basic_table(shard_summaries, shard_distribution, large_shards, small_shards_info, lang=lang)
    
    # 生成告警部分 HTML - 只使用健康评分的问题清单
    alert_html_parts = []
    
    # 将健康评分问题清单添加到告警信息中
    if health_score_report:
        issues = health_score_report.get('issues', [])
        if issues:
            # 按严重程度分组问题
            # severity_level: 1=不严重(优化建议), 2=一般(建议处理), 3=非常严重(必须处理)
            level_3_issues = [issue for issue in issues if issue.get('severity_level') == 3]  # 最严重
            level_2_issues = [issue for issue in issues if issue.get('severity_level') == 2]
            level_1_issues = [issue for issue in issues if issue.get('severity_level') == 1]  # 不严重
            
            # 添加三级告警（最严重）
            if level_3_issues:
                unknown_issue = translate('report.common.unknown_issue', lang)
                critical_alert_label = translate('report.html.alerts.critical', lang)
                current_value_label = translate('report.html.alerts.current_value', lang)
                suggestion_label = translate('report.html.alerts.suggestion', lang)
                level_3_html = f'''
                <div class="alert-box alert-critical">
                    <strong>🔴 {critical_alert_label}</strong>
                    <ul style="margin-top: 10px; margin-left: 20px;">
                '''
                for issue in level_3_issues:
                    # 智能翻译 description、suggestion 和 value
                    description = translate_check_message(issue.get('description', unknown_issue), lang)
                    suggestion = translate_check_message(issue.get('suggestion', ''), lang) if issue.get('suggestion') else ''
                    value_translated = translate_check_message(str(issue.get('value', '')), lang) if issue.get('value') is not None else ''
                    value_part = f" ({current_value_label}: {value_translated})" if issue.get('value') is not None else ""
                    suggestion_part = f"<br><strong>{suggestion_label}:</strong> {suggestion}" if suggestion else ""
                    level_3_html += f'''
                        <li style="margin: 8px 0;">
                            <strong>{description}</strong>{value_part}{suggestion_part}
                        </li>
                    '''
                level_3_html += '''
                    </ul>
                </div>
                '''
                alert_html_parts.append(level_3_html)
            
            # 添加二级告警
            if level_2_issues:
                unknown_issue = translate('report.common.unknown_issue', lang)
                warning_alert_label = translate('report.html.alerts.warning', lang)
                current_value_label = translate('report.html.alerts.current_value', lang)
                suggestion_label = translate('report.html.alerts.suggestion', lang)
                level_2_html = f'''
                <div class="alert-box alert-warning">
                    <strong>🟠 {warning_alert_label}</strong>
                    <ul style="margin-top: 10px; margin-left: 20px;">
                '''
                for issue in level_2_issues:
                    # 智能翻译 description、suggestion 和 value
                    description = translate_check_message(issue.get('description', unknown_issue), lang)
                    suggestion = translate_check_message(issue.get('suggestion', ''), lang) if issue.get('suggestion') else ''
                    value_translated = translate_check_message(str(issue.get('value', '')), lang) if issue.get('value') is not None else ''
                    value_part = f" ({current_value_label}: {value_translated})" if issue.get('value') is not None else ""
                    suggestion_part = f"<br><strong>{suggestion_label}:</strong> {suggestion}" if suggestion else ""
                    level_2_html += f'''
                        <li style="margin: 8px 0;">
                            <strong>{description}</strong>{value_part}{suggestion_part}
                        </li>
                    '''
                level_2_html += '''
                    </ul>
                </div>
                '''
                alert_html_parts.append(level_2_html)
            
            # 添加一级告警（不严重）
            if level_1_issues:
                unknown_issue = translate('report.common.unknown_issue', lang)
                info_alert_label = translate('report.html.alerts.info', lang)
                current_value_label = translate('report.html.alerts.current_value', lang)
                suggestion_label = translate('report.html.alerts.suggestion', lang)
                level_1_html = f'''
                <div class="alert-box alert-info">
                    <strong>🔵 {info_alert_label}</strong>
                    <ul style="margin-top: 10px; margin-left: 20px;">
                '''
                for issue in level_1_issues:
                    # 智能翻译 description、suggestion 和 value
                    description = translate_check_message(issue.get('description', unknown_issue), lang)
                    suggestion = translate_check_message(issue.get('suggestion', ''), lang) if issue.get('suggestion') else ''
                    value_translated = translate_check_message(str(issue.get('value', '')), lang) if issue.get('value') is not None else ''
                    value_part = f" ({current_value_label}: {value_translated})" if issue.get('value') is not None else ""
                    suggestion_part = f"<br><strong>{suggestion_label}:</strong> {suggestion}" if suggestion else ""
                    level_1_html += f'''
                        <li style="margin: 8px 0;">
                            <strong>{description}</strong>{value_part}{suggestion_part}
                        </li>
                    '''
                level_1_html += '''
                    </ul>
                </div>
                '''
                alert_html_parts.append(level_1_html)
    
    # 合并所有告警
    if alert_html_parts:
        alert_html = "\n".join(alert_html_parts)
    else:
        no_alerts_text = translate('report.html.alerts.no_alerts', lang)
        alert_html = f'<div class="alert-box alert-success">✅ {no_alerts_text}</div>'
    
    # 生成所有检查项详情 HTML
    def generate_check_results_html(check_results: dict) -> str:
        """生成所有检查项详情的 HTML"""
        if not check_results:
            return f'<div class="alert-box alert-info">ℹ️ {translate("report.check_results.no_data", lang)}</div>'
        
        # 构建告警检查项集合，用于判断哪些检查项有告警
        critical_check_items = set()
        warning_check_items = set()
        
        for alert in critical_alerts:
            check_item = alert.get('check_item', '')
            if check_item:
                critical_check_items.add(check_item)
        
        for alert in warning_alerts:
            check_item = alert.get('check_item', '')
            if check_item:
                warning_check_items.add(check_item)
        
        html_parts = []
        
        # 为检查类别添加序号和标题
        category_order = [
            'cluster_health',
            'cluster_roles',
            'cluster_destructive',
            'jvm_consistency',
            'cluster_settings',
            'thread_pool_status',
            'performance_stability',
            'primary_shard_rationality',
            'replica_rationality',
            'write_optimization',
            'delayed_allocation',
            'mapping_count',
            'mapping_text_type',
            'segment_overload',
            'swap_partition',
            'index_rejection',
            'search_failure',
            'breaker_status',
            'empty_shards',
            'node_resources',
            'index_health',
            'shards',
            'recovery',
            'ilm',
            'snapshot',
            'security',
            'network',
            'license',
            'node_consistency',
            'index_settings',
            'thread_pools'
        ]
        
        category_titles = {
            'cluster_health': f"1、{translate('report.check_details.cluster_health', lang)}",
            'cluster_roles': f"2、{translate('report.check_details.cluster_role', lang)}",
            'cluster_destructive': f"3、{translate('report.check_details.delete_protection', lang)}",
            'jvm_consistency': f"4、{translate('report.check_details.jvm_consistency', lang)}",
            'cluster_settings': f"5、{translate('report.check_details.cluster_params', lang)}",
            'thread_pool_status': f"6、{translate('report.check_details.thread_pool_usage', lang)}",
            'performance_stability': f"7、{translate('report.check_details.gc_status', lang)}",
            'primary_shard_rationality': f"8、{translate('report.check_details.primary_shard_rationality', lang)}",
            'replica_rationality': f"9、{translate('report.check_details.replica_rationality', lang)}",
            'write_optimization': f"10、{translate('report.check_details.write_optimization', lang)}",
            'delayed_allocation': f"11、{translate('report.check_details.delayed_allocation', lang)}",
            'mapping_count': f"12、{translate('report.check_details.mapping_fields', lang)}",
            'mapping_text_type': f"13、{translate('report.check_details.mapping_string_type', lang)}",
            'segment_overload': f"14、{translate('report.check_details.segment_overload', lang)}",
            'swap_partition': f"15、{translate('report.check_details.swap_partition', lang)}",
            'index_rejection': f"16、{translate('report.check_details.index_rejection', lang)}",
            'search_failure': f"17、{translate('report.check_details.search_failure', lang)}",
            'breaker_status': f"18、{translate('report.check_details.parent_circuit_breaker', lang)}",
            'empty_shards': f"19、{translate('report.check_details.empty_shards', lang)}",
            'node_resources': f"20、{translate('report.check_details.node_resources', lang)}",
            'index_health': f"21、{translate('report.check_details.index_health', lang)}",
            'shards': f"22、{translate('report.check_details.shards_check', lang)}",
            'recovery': f"23、{translate('report.check_details.recovery', lang)}",
            'ilm': f"24、{translate('report.check_details.ilm', lang)}",
            'snapshot': f"25、{translate('report.check_details.snapshot', lang)}",
            'security': f"26、{translate('report.check_details.security', lang)}",
            'network': '27、网络配置',  # TODO: 添加翻译键
            'license': '28、许可证状态',  # TODO: 添加翻译键
            'node_consistency': '29、节点一致性',  # TODO: 添加翻译键
            'index_settings': '30、索引设置',  # TODO: 添加翻译键
            'thread_pools': '31、线程池状态'  # TODO: 添加翻译键
        }
        
        # 按照指定顺序处理检查类别
        for category_name in category_order:
            if category_name in check_results:
                # 添加带序号的类别标题
                cat_title = category_titles.get(category_name, category_name)
                html_parts.append(f'<h3 style="margin-top: 30px; margin-bottom: 15px;">{cat_title}</h3>')
                html_parts.append('<div class="info-grid">')
                
                category_data = check_results[category_name]
                
                if isinstance(category_data, dict):
                    # 处理扁平字典结构 {"check_key": {"value": ..., "passed": ..., "message": ...}}
                    for key, item in category_data.items():
                        if isinstance(item, dict):
                            # 判断是否有告警及告警级别
                            check_item_key = f"{category_name}.{key}"
                            is_critical = check_item_key in critical_check_items
                            is_warning = check_item_key in warning_check_items
                            
                            # 优先判断是否通过，通过时显示绿色，不通过时再根据告警级别显示颜色
                            if item.get('passed', True):
                                emoji = "✅"
                                border_color = "#28a745"
                            elif is_critical:
                                emoji = "❌"
                                border_color = "#dc3545"
                            elif is_warning:
                                emoji = "⚠️"
                                border_color = "#ffc107"
                            else:
                                emoji = "❌"
                                border_color = "#dc3545"
                            
                            # 使用 detail 字段作为详情，message 作为检查项名称
                            check_item_name = item.get('message', key)
                            # 智能翻译检查项名称
                            from backend.i18n.translations import translate_check_message
                            check_item_name = translate_check_message(check_item_name, lang)
                            
                            # 智能翻译 detail 和 value 字段
                            detail = translate_check_message(item.get('detail', ''), lang) if item.get('detail') else ''
                            
                            # 处理值中的换行符，将\n替换为<br>标签
                            value = item.get('value', 'N/A')
                            if isinstance(value, str):
                                value = translate_check_message(value, lang)
                                value = value.replace('\n', '<br>')
                            if category_name in["cluster_health","cluster_roles","cluster_destructive","cluster_settings","node_resources","index_health","shards","recovery","ilm","security"]:
                                html_parts.append(f"""
                                <div class="info-card" style="border-left-color: {border_color};">
                                    <h3>{emoji} {check_item_name}</h3>
                                    {'<div class="sub">' + detail + '</div>' if detail else ''}
                                    {'<div class="sub">' + translate('report.check_results.threshold', lang) + '：' + item.get('threshold', 'N/A') + '</div>' if 'threshold' in item else ''}
                                </div>
                                """)
                            else:
                                html_parts.append(f"""
                                <div class="info-card" style="border-left-color: {border_color};">
                                    <h3>{emoji} {check_item_name}</h3>
                                    <div class="value" style="font-size: 1.2em;">{value}</div>
                                    {'<div class="sub">' + detail + '</div>' if detail else ''}
                                    {'<div class="sub">' + translate('report.check_results.threshold', lang) + '：' + item.get('threshold', 'N/A') + '</div>' if 'threshold' in item else ''}
                                </div>
                                """)
                
                html_parts.append('</div>')
        
        return "\n".join(html_parts)
    
    html = f'''<!DOCTYPE html>
<html lang="{lang.replace('-', '_').lower()}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report_title} - {cluster_info.get('cluster_name', 'Unknown')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .score-section {{
            background: white;
            padding: 30px;
            text-align: center;
            border-bottom: 3px solid #f0f0f0;
        }}
        
        .score-circle {{
            display: inline-block;
            width: 150px;
            height: 150px;
            border-radius: 50%;
            background: conic-gradient({score_color} {health_score * 3.6}deg, #e0e0e0 0deg);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 20px;
            position: relative;
        }}
        
        .score-circle::before {{
            content: '';
            position: absolute;
            width: 130px;
            height: 130px;
            background: white;
            border-radius: 50%;
        }}
        
        .score-value {{
            position: relative;
            z-index: 1;
            font-size: 3em;
            font-weight: bold;
            color: {score_color};
        }}
        
        .score-label {{
            font-size: 1.2em;
            color: #666;
            margin-top: 10px;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section-title {{
            font-size: 1.8em;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
            font-weight: 600;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .info-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }}
        
        .info-card h3 {{
            font-size: 1.1em;
            color: #666;
            margin-bottom: 10px;
        }}
        
        .info-card .value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #333;
        }}
        
        .info-card .sub {{
            font-size: 0.9em;
            color: #888;
            margin-top: 5px;
        }}
        
        .alert-box {{
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 15px;
        }}
        
        .alert-critical {{
            background: #f8d7da;
            border-left: 4px solid #dc3545;
            color: #721c24;
        }}
        
        .alert-warning {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            color: #856404;
        }}
        
        .alert-success {{
            background: #d4edda;
            border-left: 4px solid #28a745;
            color: #155724;
        }}
        
        .alert-info {{
            background: #d1ecf1;
            border-left: 4px solid #17a2b8;
            color: #0c5460;
        }}
        
        .table-container {{
            overflow-x: auto;
            margin-top: 20px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 10px;
            overflow: hidden;
        }}
        
        th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        
        td {{
            padding: 15px;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        .badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
        }}
        
        .badge-green {{
            background: #d4edda;
            color: #155724;
        }}
                
        .badge-yellow {{
            background: #fff3cd;
            color: #856404;
        }}
                
        .badge-blue {{
            background: #d1ecf1;
            color: #0c5460;
        }}
                
        .badge-red {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        
        .stat-item {{
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }}
        
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .stat-label {{
            color: #666;
            margin-top: 5px;
            font-size: 0.9em;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e0e0e0;
        }}
        
        .progress-bar {{
            width: 100%;
            height: 20px;
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 10px;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s ease;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {translate('report.title', lang)}</h1>
            <p>{cluster_info.get('cluster_name', 'Unknown')} - {diagnosis_time_label}：{check_metadata.get('extracted_at', 'N/A')}</p>
        </div>
        
        <div class="score-section">
            <div class="score-circle">
                <span class="score-value">{health_score}</span>
            </div>
            <div class="score-label">{health_score_label}</div>
            <div style="margin-top: 20px;">
                <span class="badge badge-green">{alerts_total_label}：{total_issues}</span>
                <span class="badge badge-blue">{alerts_level_1_label}：{level_1_count}</span>
                <span class="badge badge-yellow">{alerts_level_2_label}：{level_2_count}</span>
                <span class="badge badge-red">{alerts_level_3_label}：{level_3_count}</span>
            </div>
        </div>
        
        <!-- 告警信息 -->
        <div class="content">
            <div class="section">
                <h2 class="section-title">🚨 {alerts_title}</h2>
                
                {alert_html}
            </div>
            
            {advanced_analysis_html}
            
            <!-- 集群基本信息 -->
            <div class="section">
                <h2 class="section-title">🏷️ {cluster_basic_info_title}</h2>
                <div class="info-grid">
                    <!-- 第1行：4个卡片 -->
                    <div class="info-card">
                        <h3>{translate('report.html.cluster.name', lang)}</h3>
                        <div class="value">{cluster_info.get('cluster_name', 'N/A')}</div>
                        <div class="sub">Cluster Name</div>
                    </div>
                    <div class="info-card">
                        <h3>{translate('report.html.cluster.status', lang)}</h3>
                        <div class="value">{status_emoji} {cluster_info.get('status', 'N/A')}</div>
                        <div class="sub">Cluster Status</div>
                    </div>
                    <div class="info-card">
                        <h3>{translate('report.html.cluster.version', lang)}</h3>
                        <div class="value">{cluster_info.get('es_version', 'N/A')}</div>
                        <div class="sub">ES Version</div>
                    </div>
                    <div class="info-card">
                        <h3>{translate('report.html.cluster.license', lang)}</h3>
                        <div class="value">{cluster_info.get('license_type', 'N/A')}</div>
                        <div class="sub">License Type</div>
                    </div>
                    
                    <!-- 第2行：4个卡片 -->
                    <div class="info-card">
                        <h3>{translate('report.html.cluster.nodes_total', lang)}</h3>
                        <div class="value">{node_summary.get('total', 0)}</div>
                        <div class="sub">{translate('report.html.cluster.data_nodes', lang)}：{cluster_info.get('data_nodes', 0)} | {translate('report.html.cluster.master_nodes', lang)}：{cluster_info.get('master_nodes', 0)}</div>
                    </div>
                    <div class="info-card">
                        <h3>{translate('report.html.cluster.shards', lang)}</h3>
                        <div class="value">{cluster_info.get('shards_total', 0):,}</div>
                        <div class="sub">Total Shards</div>
                    </div>
                    <div class="info-card">
                        <h3>{translate('report.html.cluster.indices', lang)}</h3>
                        <div class="value">{index_summary.get('total', 0)}</div>
                        <div class="sub">Total Indices</div>
                    </div>
                    <div class="info-card">
                        <h3>{translate('report.html.cluster.security', lang)}</h3>
                        <div class="value">{translate_check_message(cluster_info.get('security_enabled', 'N/A'), lang)}</div>
                        <div class="sub">Security Enabled</div>
                    </div>
                    
                    <!-- 第3行：2个卡片 -->
                    <div class="info-card">
                        <h3>{translate('report.html.cluster.hot_cold', lang)}</h3>
                        <div class="value">{'✅ ' + translate('report.html.cluster.has_hot_cold', lang) if cluster_info.get('has_hot_cold', False) else '❌ ' + translate('report.html.cluster.no_hot_cold', lang)}</div>
                        <div class="sub">Hot-Cold Architecture</div>
                    </div>
                    <div class="info-card">
                        <h3>{translate('report.html.cluster.hot_cold_ratio', lang)}</h3>
                        <div class="value">{translate_check_message(cluster_info.get('hot_cold_ratio', 'N/A'), lang)}</div>
                        <div class="sub">Hot-Cold Ratio</div>
                    </div>
                </div>
            </div>
            
            {nodes_table_html}
            
            <!-- 分片基本信息 -->
            {shards_table_html}
            
            <!-- 健康摘要 -->
            <div class="section">
                <h2 class="section-title">💚 {health_summary_title}</h2>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value">{health_summary.get('active_shards', 0):,}</div>
                        <div class="stat-label">{translate('report.html.health_summary.active_shards', lang)}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{health_summary.get('active_primary_shards', 0):,}</div>
                        <div class="stat-label">{translate('report.html.health_summary.active_primary', lang)}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{health_summary.get('unassigned_shards', 0):,}</div>
                        <div class="stat-label">{translate('report.html.health_summary.unassigned_shards', lang)}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{health_summary.get('active_shards_percent', 0):.1f}%</div>
                        <div class="stat-label">{translate('report.html.health_summary.active_ratio', lang)}</div>
                    </div>
                </div>
                
                <div style="margin-top: 20px;">
                    <strong>{translate('report.health_summary.active_shards_ratio', lang)}</strong>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {health_summary.get('active_shards_percent', 0)}%"></div>
                    </div>
                </div>
            </div>
            
            <!-- 资源使用 -->
            <div class="section">
                <h2 class="section-title">🖥️ {translate('report.resources.title', lang)}</h2>
                <div class="info-grid">
                    <div class="info-card">
                        <h3>{translate('report.resources.disk_usage', lang)}</h3>
                        <div class="value">{node_summary.get('avg_disk_usage', 0):.1f}%</div>
                        <div class="sub">{translate('report.resources.highest_node_label', lang)}：{node_summary.get('max_disk_node', 'N/A')}</div>
                    </div>
                    <div class="info-card">
                        <h3>{translate('report.resources.jvm_heap_usage', lang)}</h3>
                        <div class="value">{node_summary.get('avg_heap_usage', 0):.1f}%</div>
                        <div class="sub">{translate('report.resources.highest_node_label', lang)}：{node_summary.get('max_heap_node', 'N/A')}</div>
                    </div>
                    <div class="info-card">
                        <h3>{translate('report.resources.cpu_usage', lang)}</h3>
                        <div class="value">{node_summary.get('avg_cpu_usage', 0):.1f}%</div>
                        <div class="sub">CPU Usage</div>
                    </div>
                </div>
            </div>
            
            <!-- 索引统计 -->
            <div class="section">
                <h2 class="section-title">📁 {translate('report.indices.title', lang)}</h2>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value">{index_summary.get('total_docs', 0):,}</div>
                        <div class="stat-label">{translate('report.indices.total_docs', lang)}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{index_summary.get('total_size_gb', 0):.2f} GB</div>
                        <div class="stat-label">{translate('report.indices.total_storage', lang)}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" style="color: #28a745;">{index_summary.get('health_distribution', {}).get('green', 0)}</div>
                        <div class="stat-label">{translate('report.indices.healthy', lang)}</div>
                    </div>
                </div>
                
                <h3 style="margin-top: 30px; margin-bottom: 15px;">{translate('report.indices.top5_title', lang)}</h3>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>{translate('report.indices.headers.rank', lang)}</th>
                                <th>{translate('report.indices.headers.name', lang)}</th>
                                <th>{translate('report.indices.headers.size_gb', lang)}</th>
                                <th>{translate('report.indices.headers.docs', lang)}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join(f"""
                            <tr>
                                <td>{i+1}</td>
                                <td>{idx.get('name', 'N/A')}</td>
                                <td>{idx.get('size_gb', 0):.2f}</td>
                                <td>{idx.get('docs', 0):,}</td>
                            </tr>
                            """ for i, idx in enumerate(index_summary.get('top_5_indices', [])))}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- 所有检查项详情 -->
            <div class="section">
                <h2 class="section-title">📋 {translate('report.check_results.title', lang)}</h2>
                
                {generate_check_results_html(check_results)}
            </div>
            
            <!-- 检查详情 -->
            <div class="section">
                <h2 class="section-title">ℹ️ {translate('report.metadata.title', lang)}</h2>
                <div class="alert-box alert-info">
                    <strong>{translate('report.metadata.data_source_label', lang)}:</strong> {check_metadata.get('source', 'N/A')}<br>
                    <strong>{translate('report.metadata.extraction_time_label', lang)}:</strong> {check_metadata.get('extracted_at', 'N/A')}<br>
                    <strong>{translate('report.metadata.check_duration_label', lang)}:</strong> {check_metadata.get('check_duration_sec', 0)}{translate('report.common.seconds', lang)}
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>{translate('report.footer.generated_at', lang)}：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>{translate('report.footer.system_name', lang)} | {translate('report.footer.score_based_on', lang)} 12 {translate('report.footer.categories_count', lang)} 36 {translate('report.footer.indicators_count', lang)}</p>
        </div>
    </div>
</body>
</html>'''
    
    return html


def main():
    """主函数"""
    # 查找最新的 JSON 报告
    report_dir = Path('out/analysis')
    json_files = sorted(report_dir.glob('check_result_report_*.json'))
    
    if not json_files:
        print("❌ 未找到 check_result_report_*.json 文件")
        return
    
    latest_json = json_files[-1]
    print(f"📄 读取文件：{latest_json}")
    
    # 读取 JSON 数据
    with open(latest_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 生成 HTML
    html_content = generate_html_report(data)
    
    # 保存 HTML 文件到 reports 目录
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    reports_dir = Path('reports')
    reports_dir.mkdir(exist_ok=True)  # 确保目录存在
    html_path = reports_dir / f'es_inspection_report_{timestamp}.html'
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML 报告已生成：{html_path}")
    print(f"📊 集群：{data['basic_info']['cluster_info']['cluster_name']}")
    print(f"💯 健康评分：{data['alerts']['summary']['health_score']}/100")


def _generate_nodes_basic_table(nodes_detail: list, lang: str = 'zh-CN') -> str:
    """
    生成节点基本信息表格 HTML
    
    Args:
        nodes_detail: 节点详细信息列表
        lang: 语言代码 (zh-CN, zh-TW, en-US)，默认中文
        
    Returns:
        HTML 表格字符串
    """
    from backend.i18n.translations import translate
    
    if not nodes_detail:
        return f'<p style="text-align: center; color: #999;">{translate("report.common.na", lang)}</p>'
    
    # 生成表格行
    rows_html = ""
    for idx, node in enumerate(nodes_detail, 1):
        # 格式化角色显示
        roles = node.get('roles', [])
        if isinstance(roles, list):
            roles_display = ', '.join([str(r) for r in roles if r])
        else:
            roles_display = str(roles)
        if not roles_display:
            roles_display = translate('report.common.unknown', lang)
        
        # 处理可能的空值，提供默认值
        cpu_percent = f"{node.get('cpu_percent', 0):.1f}"
        heap_used_percent = f"{node.get('heap_used_percent', 0):.1f}"
        disk_used_percent = f"{node.get('disk_used_percent', 0):.1f}"
        shard_count = node.get('shards_count', 0)
        
        # 处理可能为"未知"的字段，进行翻译
        def translate_unknown(value, lang):
            """如果值是'未知'，则返回翻译后的文本"""
            if value == '未知':
                return translate('report.common.unknown', lang)
            return value
        
        name = translate_unknown(node.get('name'), lang) or translate('report.common.unknown', lang)
        version = translate_unknown(node.get('version'), lang) or translate('report.common.unknown', lang)
        mem_total = translate_unknown(node.get('mem_total'), lang) or translate('report.common.unknown', lang)
        jvm_heap_max = translate_unknown(node.get('jvm_heap_max'), lang) or translate('report.common.unknown', lang)
        uptime = translate_unknown(node.get('uptime'), lang) or translate('report.common.unknown', lang)
        disk_total = translate_unknown(node.get('disk_total'), lang) or translate('report.common.unknown', lang)
        
        rows_html += f'''
        <tr>
            <td>{idx}</td>
            <td>{name}</td>
            <td>{version}</td>
            <td>{cpu_percent}%</td>
            <td>{mem_total}</td>
            <td>{jvm_heap_max}</td>
            <td>{heap_used_percent}%</td>
            <td>{roles_display}</td>
            <td>{uptime}</td>
            <td>{shard_count}</td>
            <td>{disk_total}</td>
            <td>{disk_used_percent}%</td>
        </tr>'''
    
    # 生成完整表格
    table_html = f'''
    <div class="section">
        <h2 class="section-title">🖥️ {translate('report.sections.node_basic_info', lang)}</h2>
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                <thead>
                    <tr style="background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;">
                        <th style="padding: 12px 8px; text-align: center; border: 1px solid #dee2e6;">{translate('report.nodes.headers.seq', lang)}</th>
                        <th style="padding: 12px 8px; text-align: left; border: 1px solid #dee2e6;">{translate('report.nodes.headers.name', lang)}</th>
                        <th style="padding: 12px 8px; text-align: center; border: 1px solid #dee2e6;">{translate('report.nodes.headers.version', lang)}</th>
                        <th style="padding: 12px 8px; text-align: center; border: 1px solid #dee2e6;">{translate('report.nodes.headers.cpu', lang)}</th>
                        <th style="padding: 12px 8px; text-align: center; border: 1px solid #dee2e6;">{translate('report.nodes.headers.memory', lang)}</th>
                        <th style="padding: 12px 8px; text-align: center; border: 1px solid #dee2e6;">{translate('report.nodes.headers.jvm_heap', lang)}</th>
                        <th style="padding: 12px 8px; text-align: center; border: 1px solid #dee2e6;">{translate('report.nodes.headers.jvm_heap_usage', lang)}</th>
                        <th style="padding: 12px 8px; text-align: left; border: 1px solid #dee2e6;">{translate('report.nodes.headers.roles', lang)}</th>
                        <th style="padding: 12px 8px; text-align: center; border: 1px solid #dee2e6;">{translate('report.nodes.headers.uptime', lang)}</th>
                        <th style="padding: 12px 8px; text-align: center; border: 1px solid #dee2e6;">{translate('report.nodes.headers.shards', lang)}</th>
                        <th style="padding: 12px 8px; text-align: center; border: 1px solid #dee2e6;">{translate('report.nodes.headers.disk_space', lang)}</th>
                        <th style="padding: 12px 8px; text-align: center; border: 1px solid #dee2e6;">{translate('report.nodes.headers.disk_usage', lang)}</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
    </div>
    '''
    
    return table_html


def _generate_shards_basic_table(shard_summaries: list, shard_distribution: dict = None, large_shards: list = None, small_shards_info: dict = None, lang: str = 'zh-CN') -> str:
    """
    生成分片基本信息表格 HTML
    
    Args:
        shard_summaries: 索引分片汇总列表，每个元素包含 index_name, primary_shard_count, total_size_bytes
        shard_distribution: 主分片分布信息
        large_shards: 大分片索引列表
        small_shards_info: 小分片多主分片索引信息
        lang: 语言代码 (zh-CN, zh-TW, en-US)，默认中文
        
    Returns:
        HTML 表格字符串
    """
    from backend.i18n.translations import translate
    if not shard_summaries:
        return f'''
    <div class="section">
        <h2 class="section-title">📊 {translate('report.sections.shard_basic_info', lang)}</h2>
        <p style="text-align: center; color: #999;">{translate('report.common.no_data', lang)}</p>
    </div>
    '''
    
    # 导入format_size_human_readable函数
    try:
        from es_insight.parsers.shards_parser import format_size_human_readable
    except ImportError:
        # 如果导入失败，使用简单的GB显示
        def format_size_human_readable(bytes_value):
            gb_val = round(bytes_value / (1024 ** 3), 2)
            return f"{gb_val} GB"
    
    # 按照单个分片大小从大到小排序，只取前10个
    shard_summaries_sorted = sorted(shard_summaries, key=lambda x: x.get('avg_shard_size_bytes', 0), reverse=True)[:10]
    
    # 生成分片基本信息表格
    rows_html = ""
    for idx, summary in enumerate(shard_summaries_sorted, 1):
        # 使用人类可读的格式显示大小（单个分片的平均大小）
        size_display = format_size_human_readable(summary.get('avg_shard_size_bytes', 0))
        
        rows_html += f'''
        <tr>
            <td>{idx}</td>
            <td>{summary.get('index_name', translate('report.common.unknown', lang))}</td>
            <td>{summary.get('primary_shard_count', 0)}</td>
            <td>{size_display}</td>
        </tr>'''
    
    # 生成完整表格
    table_html = f'''
    <div class="section">
        <h2 class="section-title">📊 {translate('report.sections.shard_basic_info', lang)}</h2>
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                <thead>
                    <tr style="background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;">
                        <th style="padding: 12px 8px; text-align: center; border: 1px solid #dee2e6; width: 10%;">{translate('report.shards.headers.seq', lang)}</th>
                        <th style="padding: 12px 8px; text-align: left; border: 1px solid #dee2e6; width: 40%;">{translate('report.shards.headers.index_name', lang)}</th>
                        <th style="padding: 12px 8px; text-align: center; border: 1px solid #dee2e6; width: 20%;">{translate('report.shards.headers.shard_count', lang)}</th>
                        <th style="padding: 12px 8px; text-align: center; border: 1px solid #dee2e6; width: 30%;">{translate('report.shards.headers.shard_size', lang)}</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
    </div>
    '''
    
    # 添加主分片分布表格
    if shard_distribution:
        distribution = shard_distribution.get('distribution', {})
        if distribution:
            dist_rows_html = ""
            for shard_count, index_count in distribution.items():
                dist_rows_html += f'''
                <tr>
                    <td>{shard_count}</td>
                    <td>{index_count}</td>
                </tr>'''
            
            table_html += f'''
    <div class="section" style="margin-top: 20px;">
        <h3 class="section-subtitle">{translate('report.shard_detail.primary_distribution', lang)}</h3>
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                <thead>
                    <tr style="background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;">
                        <th style="padding: 12px 8px; text-align: center; border: 1px solid #dee2e6; width: 50;">{translate('report.shard_detail.headers.shard_count', lang)}</th>
                        <th style="padding: 12px 8px; text-align: center; border: 1px solid #dee2e6; width: 50;">{translate('report.shard_detail.headers.index_count', lang)}</th>
                    </tr>
                </thead>
                <tbody>
                    {dist_rows_html}
                </tbody>
            </table>
        </div>
    </div>
    '''
    
    # 添加单个分片大于40GB索引表格
    large_rows_html = ""
    if large_shards and len(large_shards) > 0:
        for idx, large_shard in enumerate(large_shards, 1):
            large_rows_html += f'''
            <tr>
                <td>{idx}</td>
                <td>{large_shard.get('index_name', translate('report.common.unknown', lang))}</td>
                <td>{large_shard.get('shard_size_gb', 0):.2f} GB</td>
            </tr>'''
    else:
        # 当没有大分片索引时，显示空行
        large_rows_html = f'''
        <tr>
            <td colspan="3" style="text-align: center; padding: 20px; color: #6c757d;">{translate('report.shard_detail.no_data', lang)}</td>
        </tr>'''
        
    table_html += f'''
    <div class="section" style="margin-top: 20px;">
        <h3 class="section-subtitle">{translate('report.shard_detail.large_shards', lang)}</h3>
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                <thead>
                    <tr style="background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;">
                        <th style="padding: 12px 8px; text-align: center; border: 1px solid #dee2e6; width: 10;">{translate('report.common.index', lang)}</th>
                        <th style="padding: 12px 8px; text-align: left; border: 1px solid #dee2e6; width: 60;">{translate('report.indices.headers.name', lang)}</th>
                        <th style="padding: 12px 8px; text-align: center; border: 1px solid #dee2e6; width: 30;">{translate('report.shard_detail.headers.shard_size', lang)}</th>
                    </tr>
                </thead>
                <tbody>
                    {large_rows_html}
                </tbody>
            </table>
        </div>
    </div>
    '''
    
    # 添加单个分片小于500MB并且主分片数大于1的索引数量展示
    if small_shards_info:
        count = small_shards_info.get('count', 0)
        table_html += f'''
    <div class="section" style="margin-top: 20px;">
        <h3 class="section-subtitle">{translate('report.shard_detail.small_shards_multi_primary', lang)}</h3>
        <p style="font-size: 14px; margin: 10px 0;">{translate('report.shard_detail.count_label', lang)}：{count}</p>
    </div>
    '''
    
    return table_html
if __name__ == '__main__':
    main()
