"""检查项结果解析器 - 解析提取后的检查结果，输出基本信息和告警信息

基于配置文件中的阈值进行自动检查和告警生成
"""

import json
import yaml
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from loguru import logger
from es_insight.rules.engine import RulesEngine
from es_insight.health_score import HealthScoreConfig, HealthScoreReport
from es_insight.shard_size_check import (
    count_physical_shards_over_size_gb,
    find_oversized_primary_shard_indices,
    index_name_from_record,
    index_replica_shards,
    oversized_primary_shard_threshold_gb,
    oversized_single_shard_threshold_gb,
)
from es_insight.nodes_stats_utils import (
    find_nodes_with_search_missing,
    get_nodes_stats_payload,
)
from es_insight.segment_check import (
    find_indices_with_too_many_segments,
    per_primary_shard_threshold,
)
from es_insight.shard_node_stats import (
    count_shards_per_node,
    max_shards_on_single_node,
)
from es_insight.node_role_utils import (
    is_data_node,
    is_dedicated_coordinator_node,
    is_master_eligible_node,
    normalize_roles,
    roles_concat_lower,
)


class CheckResultParser:
    """检查项结果解析器"""
    
    def __init__(self, result_file: str = None, config_file: str = None):
        """
        初始化解析器
        
        Args:
            result_file: 检查结果文件路径（JSON 格式）
            config_file: 配置文件路径（YAML 格式），默认使用 configs/checkpoints_thresholds_complete.yaml
        """
        self.result_file = Path(result_file) if result_file else None
        self.output_dir = Path("out/analysis")
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.config_file = config_file
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载规则引擎
        self.rules_engine = None
        try:
            self.rules_engine = RulesEngine(config_file)
            logger.debug(f"✓ 规则引擎初始化成功：{self.rules_engine.config_path}")
        except Exception as e:
            logger.warning(f"规则引擎初始化失败：{e}")
        
        # 加载数据
        self.data = None
        if self.result_file and self.result_file.exists():
            self.load_data()
    
    def load_data(self):
        """加载 JSON 结果文件"""
        try:
            file_size_mb = self.result_file.stat().st_size / (1024 * 1024)
            logger.info(f"开始加载检查结果：{self.result_file.name} ({file_size_mb:.2f} MB)")
            
            with open(self.result_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            logger.info(f"✓ 成功加载检查结果")
        except Exception as e:
            logger.error(f"✗ 加载失败：{e}")
            raise
    
    def parse_basic_info(self) -> dict:
        """
        解析基本信息
        
        Returns:
            包含基本信息的字典
        """
        if not self.data:
            return {'error': '未加载数据'}
        
        basic_info = {
            'cluster_info': self._parse_cluster_info(),
            'health_summary': self._parse_health_summary(),
            'node_summary': self._parse_node_summary(),
            'nodes_detail': self._parse_nodes_detail(),  # 新增：节点详细信息
            'index_summary': self._parse_index_summary(),
            'check_metadata': self._parse_check_metadata()
        }
        
        return basic_info
    
    def parse_alerts(self) -> dict:
        """
        解析告警信息 - 增强版：使用规则引擎自动根据配置文件生成告警
        
        Returns:
            包含告警信息的字典
        """
        if not self.data:
            return {'error': '未加载数据'}
        
        # 1. 尝试从数据中获取已有告警
        issues = self.data.get('issues', [])
        alerts_list = self.data.get('alerts', [])
        checks = self.data.get('check_results', [])
        
        all_alerts = []
        if issues:
            all_alerts.extend(issues)
        if alerts_list:
            all_alerts.extend(alerts_list)
        if checks:
            for check in checks:
                if 'issues' in check:
                    all_alerts.extend(check['issues'])
        
        # 2. 如果没有已有告警，使用规则引擎生成告警
        if not all_alerts and self.rules_engine:
            logger.info("使用规则引擎执行检查...")
            all_alerts = self.rules_engine.check_all(self.data)
        elif not all_alerts:
            # 如果规则引擎未初始化，使用内置方法
            logger.warning("规则引擎未初始化，使用内置告警生成方法")
            all_alerts = self._generate_alerts_from_thresholds()
        
        # 3. 统计
        critical_count = sum(1 for a in all_alerts if self._is_critical(a))
        warning_count = sum(1 for a in all_alerts if self._is_warning(a))
        info_count = sum(1 for a in all_alerts if self._is_info(a))
        
        # 新增：按严重级别统计
        level_1_count = sum(1 for a in all_alerts if a.get('severity_level') == 1)
        level_2_count = sum(1 for a in all_alerts if a.get('severity_level') == 2)
        level_3_count = sum(1 for a in all_alerts if a.get('severity_level') == 3)
        
        return {
            'summary': {
                'total': len(all_alerts),
                'critical': critical_count,
                'warning': warning_count,
                'info': info_count,
                'level_1_count': level_1_count,
                'level_2_count': level_2_count,
                'level_3_count': level_3_count,
                'health_score': self._calculate_health_score(all_alerts)
            },
            'critical_alerts': [a for a in all_alerts if self._is_critical(a)],
            'warning_alerts': [a for a in all_alerts if self._is_warning(a)],
            'info_alerts': [a for a in all_alerts if self._is_info(a)],
            'by_category': self._group_alerts_by_category()
        }
    
    def _generate_alerts_from_thresholds(self) -> list:
        """
        根据阈值配置自动生成告警
        
        Returns:
            告警列表
        """
        alerts = []
        
        # 1. 检查集群健康
        cluster_health = self.data.get('cluster_health', {})
        status = cluster_health.get('status', 'unknown').upper()
        
        if status == 'RED':
            alerts.append({
                'category': 'cluster_health',
                'check_item': 'cluster.status',
                'message': f'集群状态为 RED，主分片未分配，数据不可用',
                'current_value': 'RED',
                'threshold': 'GREEN',
                'severity': 'critical',
                'recommendation': '立即检查节点可用性和分片分配情况'
            })
        elif status == 'YELLOW':
            alerts.append({
                'category': 'cluster_health',
                'check_item': 'cluster.status',
                'message': f'集群状态为 YELLOW，副本分片未分配',
                'current_value': 'YELLOW',
                'threshold': 'GREEN',
                'severity': 'warning',
                'recommendation': '检查副本分片分配策略和节点资源'
            })
        
        # 2. 检查未分配分片
        unassigned = cluster_health.get('unassigned_shards', 0)
        if unassigned > 0:
            severity = 'critical' if unassigned > 10 else 'warning'
            alerts.append({
                'category': 'shard_allocation',
                'check_item': 'cluster.unassigned_shards',
                'message': f'存在 {unassigned} 个未分配分片',
                'current_value': unassigned,
                'threshold': 0,
                'severity': severity,
                'recommendation': '使用 _cluster/allocation/explain API 分析未分配原因'
            })
        
        # 3. 检查活跃分片比例
        active_percent = cluster_health.get('active_shards_percent', cluster_health.get('active_shards_percent_as_number', 100))
        if active_percent < 90:
            alerts.append({
                'category': 'cluster_health',
                'check_item': 'cluster.active_shards_percent',
                'message': f'活跃分片比例为 {active_percent}%，低于 90%',
                'current_value': active_percent,
                'threshold': 90,
                'severity': 'critical',
                'recommendation': '检查节点连接性和分片恢复进度'
            })
        elif active_percent < 95:
            alerts.append({
                'category': 'cluster_health',
                'check_item': 'cluster.active_shards_percent',
                'message': f'活跃分片比例为 {active_percent}%，低于 95%',
                'current_value': active_percent,
                'threshold': 95,
                'severity': 'warning',
                'recommendation': '关注分片恢复进度'
            })
        
        # 4. 检查索引健康
        indices = self.data.get('indices', [])
        yellow_indices = [idx for idx in indices if idx.get('health') == 'yellow']
        red_indices = [idx for idx in indices if idx.get('health') == 'red']
        
        if red_indices:
            alerts.append({
                'category': 'index_health',
                'check_item': 'index.health',
                'message': f'{len(red_indices)} 个索引状态为 RED',
                'current_value': len(red_indices),
                'threshold': 0,
                'severity': 'critical',
                'recommendation': f'检查以下索引的主分片分配：{", ".join([idx.get("name", "N/A") for idx in red_indices[:3]])}'
            })
        
        if yellow_indices:
            alerts.append({
                'category': 'index_health',
                'check_item': 'index.health',
                'message': f'{len(yellow_indices)} 个索引状态为 YELLOW',
                'current_value': len(yellow_indices),
                'threshold': 0,
                'severity': 'warning',
                'recommendation': f'检查以下索引的副本分片分配：{", ".join([idx.get("name", "N/A") for idx in yellow_indices[:3]])}'
            })
        
        # 5. 检查大索引
        large_indices = [idx for idx in indices if idx.get('store_size_bytes', 0) > 50 * (1024**3)]
        if large_indices:
            alerts.append({
                'category': 'index_size',
                'check_item': 'index.size_gb',
                'message': f'{len(large_indices)} 个索引超过 50GB',
                'current_value': f'{len(large_indices)} 个索引',
                'threshold': '>50GB',
                'severity': 'warning',
                'recommendation': '考虑拆分索引或使用生命周期管理 (ILM) 进行数据归档'
            })
        
        # 6. 检查段数量过多
        high_segments = [idx for idx in indices if idx.get('segments_count', 0) > 500]
        if high_segments:
            alerts.append({
                'category': 'index_health',
                'check_item': 'index.segments_count',
                'message': f'{len(high_segments)} 个索引 segment 数量超过 500',
                'current_value': len(high_segments),
                'threshold': 500,
                'severity': 'warning',
                'recommendation': '在业务低峰期执行 force_merge'
            })
        
        return alerts
    
    def _parse_cluster_info(self) -> dict:
        """解析集群基本信息"""
        cluster_health = self.data.get('cluster_health', {})
        cluster_stats = self.data.get('cluster_stats', {})
        nodes = self.data.get('nodes', [])
        
        # 统计主节点数量（优先使用 is_master 字段，如果没有则检查 roles）
        # 注意：由于 nodes_short.json 只标记当前主节点为 '*'，其他候选主节点为 '-'
        # ES 中 master 角色简写为 'm'，所以要检查 'm' in roles
        master_nodes_count = sum(1 for node in nodes if isinstance(node, dict) and (
            node.get('is_master') or 
            (node.get('roles') and ('master' in str(node.get('roles')) or 'm' in str(node.get('roles'))))
        ))
        
        # 如果通过上述方法没有找到主节点，尝试从 cluster_health 推断
        if master_nodes_count == 0:
            # ES 集群至少有 1 个主节点
            master_nodes_count = 1
        
        # 从 cluster_stats 获取索引和分片信息
        indices_count = cluster_stats.get('indices', {}).get('count', 0)
        shards_total = cluster_stats.get('indices', {}).get('shards', {}).get('total', 0)
        
        # 从 version.json 获取版本信息（优先）
        version_data = self.data.get('version', {})
        es_version = version_data.get('version', {}).get('number', 'N/A')
        
        if es_version == 'N/A':
            # 回退到 cluster_stats 中的版本
            es_version = cluster_stats.get('version', {}).get('number', 'N/A')
        
        if es_version == 'N/A':
            # 回退到 nodes 中的版本
            versions = set()
            for node in nodes:
                if isinstance(node, dict) and node.get('version'):
                    versions.add(node.get('version'))
            es_version = ', '.join(versions) if versions else 'N/A'
        
        # 检测冷热架构
        has_hot_cold = False
        hot_nodes = 0
        cold_nodes = 0
        for node in nodes:
            if isinstance(node, dict):
                attributes = node.get('attributes', {})
                if 'box_type' in attributes or 'temp' in attributes:
                    has_hot_cold = True
                    if attributes.get('box_type') == 'cold' or attributes.get('temp') == 'cold':
                        cold_nodes += 1
                    else:
                        hot_nodes += 1
        
        if has_hot_cold and (hot_nodes + cold_nodes) > 0:
            total = hot_nodes + cold_nodes
            hot_cold_ratio = f"{hot_nodes}:{cold_nodes} ({round(hot_nodes/total*100, 1)}%:{round(cold_nodes/total*100, 1)}%)"
        elif has_hot_cold:
            hot_cold_ratio = "检测到但未统计到具体比例"
        else:
            hot_cold_ratio = "无"
        
        # 从 cluster_settings_defaults 获取许可证和安全配置
        settings_defaults = self.data.get('cluster_settings_defaults', {})
        defaults = settings_defaults.get('defaults', {})
        license_type = defaults.get('xpack.license.self_generated.type', '未知')
        security_enabled_raw = defaults.get('xpack.security.enabled', False)
        # 转换为中文显示
        if isinstance(security_enabled_raw, str):
            security_enabled = '开启' if security_enabled_raw.lower() in ['true', '1', 'yes'] else '未开启'
        else:
            security_enabled = '开启' if security_enabled_raw else '未开启'
        
        return {
            'cluster_name': cluster_health.get('cluster_name', 'N/A'),
            'status': cluster_health.get('status', 'unknown').upper(),
            'nodes_total': cluster_health.get('number_of_nodes', 0),
            'data_nodes': cluster_health.get('number_of_data_nodes', 0),
            'master_nodes': master_nodes_count,
            'indices_count': indices_count,
            'shards_total': shards_total,
            'es_version': es_version,
            'license_type': license_type,
            'has_hot_cold': has_hot_cold,
            'hot_cold_ratio': hot_cold_ratio,
            'security_enabled': security_enabled
        }
    
    def _parse_health_summary(self) -> dict:
        """解析健康摘要"""
        cluster_health = self.data.get('cluster_health', {})
        
        return {
            'active_shards': cluster_health.get('active_shards', 0),
            'active_primary_shards': cluster_health.get('active_primary_shards', 0),
            'unassigned_shards': cluster_health.get('unassigned_shards', 0),
            'initializing_shards': cluster_health.get('initializing_shards', 0),
            'relocating_shards': cluster_health.get('relocating_shards', 0),
            'delayed_unassigned_shards': cluster_health.get('delayed_unassigned_shards', 0),
            'active_shards_percent': cluster_health.get('active_shards_percent', cluster_health.get('active_shards_percent_as_number', 0))
        }
    
    def _parse_node_summary(self) -> dict:
        """解析节点摘要"""
        nodes = self.data.get('nodes', [])
        
        if not nodes:
            return {'total': 0}
        
        # 处理 nodes 可能是字典的情况
        if isinstance(nodes, dict):
            nodes_list = list(nodes.values())
        else:
            nodes_list = nodes
        
        # 统计资源使用
        total_disk_used = sum(node.get('disk_used_percent', 0) for node in nodes_list)
        total_heap_used = sum(node.get('heap_used_percent', 0) for node in nodes_list)
        total_cpu = sum(node.get('cpu_percent', 0) for node in nodes_list)
        
        return {
            'total': len(nodes_list),
            'avg_disk_usage': round(total_disk_used / len(nodes_list), 2) if nodes_list else 0,
            'avg_heap_usage': round(total_heap_used / len(nodes_list), 2) if nodes_list else 0,
            'avg_cpu_usage': round(total_cpu / len(nodes_list), 2) if nodes_list else 0,
            'max_disk_node': max(nodes_list, key=lambda x: x.get('disk_used_percent', 0), default={}).get('name', 'N/A'),
            'max_heap_node': max(nodes_list, key=lambda x: x.get('heap_used_percent', 0), default={}).get('name', 'N/A')
        }
    
    def _parse_nodes_detail(self) -> list:
        """解析节点详细信息"""
        nodes = self.data.get('nodes', [])
        
        if not nodes:
            return []
        
        # 处理 nodes 可能是字典的情况
        if isinstance(nodes, dict):
            nodes_list = list(nodes.values())
        else:
            nodes_list = nodes
        
        # 返回所有节点的详细信息
        nodes_detail = []
        for node in nodes_list:
            node_info = {
                'name': node.get('name', 'N/A'),
                'ip': node.get('ip', 'N/A'),
                'roles': node.get('roles', []),
                'version': node.get('version', 'N/A'),
                'disk_used_percent': round(node.get('disk_used_percent', 0), 2),
                'heap_used_percent': round(node.get('heap_used_percent', 0), 2),
                'cpu_percent': round(node.get('cpu_percent', 0), 2),
                'load_average': node.get('load_average', 0),
                'shards_count': node.get('shard_count', 0),  # 注意：源数据是 shard_count（单数）
                'connections': node.get('connections', 0),
                # 新增：节点基本信息所需字段
                'mem_total': node.get('mem_total', '未知'),
                'jvm_heap_max': node.get('jvm_heap_max', '未知'),
                'uptime': node.get('uptime', '未知'),
                'disk_total': node.get('disk_total', '未知')
            }
            nodes_detail.append(node_info)
        
        return nodes_detail
    
    def _parse_index_summary(self) -> dict:
        """解析索引摘要"""
        indices = self.data.get('indices', [])
        
        if not indices:
            return {'total': 0}
        
        # 统计
        total_docs = sum(idx.get('docs_count', 0) for idx in indices)
        total_size = sum(idx.get('store_size_bytes', 0) for idx in indices)
        health_dist = {}
        for idx in indices:
            health = idx.get('health', 'unknown')
            health_dist[health] = health_dist.get(health, 0) + 1
        
        # Top 5 大索引
        top_indices = sorted(indices, key=lambda x: x.get('store_size_bytes', 0), reverse=True)[:5]
        
        return {
            'total': len(indices),
            'total_docs': total_docs,
            'total_size_gb': round(total_size / (1024**3), 2),
            'health_distribution': health_dist,
            'top_5_indices': [
                {
                    'name': idx.get('name', 'N/A'),
                    'size_gb': round(idx.get('store_size_bytes', 0) / (1024**3), 2),
                    'docs': idx.get('docs_count', 0)
                }
                for idx in top_indices
            ]
        }
    
    def _parse_check_metadata(self) -> dict:
        """解析检查元数据"""
        metadata = self.data.get('metadata', {})
        check_info = self.data.get('check_metadata', {})
        source_info = metadata.get('source', 'N/A')
        source_info_file_name = source_info.split('\\')[-1]
        
        return {
            #'source': metadata.get('source', 'N/A'),
            'source': source_info_file_name,
            'extracted_at': metadata.get('extracted_at', 'N/A'),
            'checked_at': check_info.get('checked_at', 'N/A'),
            'check_duration_sec': check_info.get('duration_seconds', 0)
        }
    
    def _parse_alert_summary(self) -> dict:
        """解析告警摘要"""
        # 尝试从不同位置获取告警
        issues = self.data.get('issues', [])
        alerts_list = self.data.get('alerts', [])
        checks = self.data.get('check_results', [])
        
        # 合并所有来源
        all_alerts = []
        if issues:
            all_alerts.extend(issues)
        if alerts_list:
            all_alerts.extend(alerts_list)
        if checks:
            for check in checks:
                if 'issues' in check:
                    all_alerts.extend(check['issues'])
        
        # 统计
        critical_count = sum(1 for a in all_alerts if self._is_critical(a))
        warning_count = sum(1 for a in all_alerts if self._is_warning(a))
        info_count = sum(1 for a in all_alerts if self._is_info(a))
        
        return {
            'total': len(all_alerts),
            'critical': critical_count,
            'warning': warning_count,
            'info': info_count,
            'health_score': self._calculate_health_score(all_alerts)
        }
    
    def _get_critical_alerts(self) -> list:
        """获取严重告警"""
        all_alerts = self._get_all_alerts()
        return [a for a in all_alerts if self._is_critical(a)]
    
    def _get_warning_alerts(self) -> list:
        """获取警告告警"""
        all_alerts = self._get_all_alerts()
        return [a for a in all_alerts if self._is_warning(a)]
    
    def _get_info_alerts(self) -> list:
        """获取提示信息"""
        all_alerts = self._get_all_alerts()
        return [a for a in all_alerts if self._is_info(a)]
    
    def _get_all_alerts(self) -> list:
        """获取所有告警"""
        issues = self.data.get('issues', [])
        alerts_list = self.data.get('alerts', [])
        checks = self.data.get('check_results', [])
        
        all_alerts = []
        if issues:
            all_alerts.extend(issues)
        if alerts_list:
            all_alerts.extend(alerts_list)
        if checks:
            for check in checks:
                if 'issues' in check:
                    all_alerts.extend(check['issues'])
        
        return all_alerts
    
    def _group_alerts_by_category(self) -> dict:
        """按类别分组告警"""
        all_alerts = self._get_all_alerts()
        categories = {}
        
        for alert in all_alerts:
            category = alert.get('category', 'uncategorized')
            if category not in categories:
                categories[category] = []
            categories[category].append(alert)
        
        return categories
    
    def _is_critical(self, alert: dict) -> bool:
        """判断是否为严重告警"""
        severity = alert.get('severity', '')
        level = alert.get('level', '')
        
        # 处理 severity 可能是布尔值或其他类型的情况
        if isinstance(severity, bool):
            severity = 'critical' if severity else 'normal'
        elif isinstance(severity, str):
            severity = severity.lower()
        else:
            severity = str(severity).lower() if severity else ''
        
        # 处理 level 可能是布尔值或其他类型的情况
        if isinstance(level, bool):
            level = 'critical' if level else 'normal'
        elif isinstance(level, str):
            level = level.lower()
        else:
            level = str(level).lower() if level else ''
        
        return severity == 'critical' or level == 'critical'
    
    def _is_warning(self, alert: dict) -> bool:
        """判断是否为警告"""
        severity = alert.get('severity', '')
        level = alert.get('level', '')
        
        # 处理 severity 可能是布尔值或其他类型的情况
        if isinstance(severity, bool):
            severity = 'warning' if severity else 'normal'
        elif isinstance(severity, str):
            severity = severity.lower()
        else:
            severity = str(severity).lower() if severity else ''
        
        # 处理 level 可能是布尔值或其他类型的情况
        if isinstance(level, bool):
            level = 'warning' if level else 'normal'
        elif isinstance(level, str):
            level = level.lower()
        else:
            level = str(level).lower() if level else ''
        
        return severity == 'warning' or level == 'warning'
    
    def _is_info(self, alert: dict) -> bool:
        """判断是否为提示信息"""
        severity = alert.get('severity', '')
        level = alert.get('level', '')
        
        # 处理 severity 可能是布尔值或其他类型的情况
        if isinstance(severity, bool):
            severity = 'info' if severity else 'normal'
        elif isinstance(severity, str):
            severity = severity.lower()
        else:
            severity = str(severity).lower() if severity else ''
        
        # 处理 level 可能是布尔值或其他类型的情况
        if isinstance(level, bool):
            level = 'info' if level else 'normal'
        elif isinstance(level, str):
            level = level.lower()
        else:
            level = str(level).lower() if level else ''
        
        return severity == 'info' or level == 'info' or severity == 'normal'
    
    def _calculate_health_score(self, alerts: list) -> int:
        """
        计算健康评分 - 基于报告中已有的检查结果进行评分
        
        Args:
            alerts: 告警列表（保留参数以兼容旧代码，但不再使用）
            
        Returns:
            健康评分（0-100）
        """
        try:
            # 生成检查项结果（这是报告中实际展示的数据）
            check_results = self._generate_check_results()
            
            # 基于check_results中的数据进行评分
            score = self._calculate_score_from_check_results(check_results)
            
            logger.info(f"健康评分计算完成: {score}分（基于报告中的检查项）")
            return round(score)
            
        except Exception as e:
            logger.error(f"健康评分计算失败: {e}，回退到旧方法")
            import traceback
            logger.error(traceback.format_exc())
            
            # 回退到旧的简单计算方法
            if not alerts:
                return 100
            
            score = 100
            for alert in alerts:
                if self._is_critical(alert):
                    score -= 20
                elif self._is_warning(alert):
                    score -= 5
                elif self._is_info(alert):
                    score -= 1
            
            return max(0, min(100, score))
    
    def _calculate_score_from_check_results(self, check_results: dict) -> float:
        """
        基于报告中的检查结果计算健康评分
        
        Args:
            check_results: 检查项结果字典（与报告中展示的一致）
            
        Returns:
            健康评分（0-100）
        """
        # 直接使用所有检查项进行评分，不再限定维度
        # 这样可以确保评分和报告展示的问题数量一致
        
        total_checks = 0
        total_failed = 0
        category_scores = {}
        
        # 遍历所有类别，计算每个类别的得分
        for category, items in check_results.items():
            if not isinstance(items, dict):
                continue
            
            category_total = 0
            category_failed = 0
            
            # 遍历类别下的所有检查项
            for check_name, check_data in items.items():
                if not isinstance(check_data, dict):
                    continue
                
                category_total += 1
                passed = check_data.get('passed', True)
                
                if not passed:
                    category_failed += 1
            
            # 计算该类别的得分
            if category_total > 0:
                category_score = max(0, 100 - (category_failed / category_total * 100))
                total_checks += category_total
                total_failed += category_failed
            else:
                category_score = 100
            
            category_scores[category] = category_score
        
        # 计算总体评分（所有类别的平均分）
        if category_scores:
            total_score = sum(category_scores.values()) / len(category_scores)
        else:
            total_score = 100
        
        logger.info(f"健康评分: {total_checks}个检查项, {total_failed}个未通过, {len(category_scores)}个类别, 评分={total_score:.2f}")
        
        # 额外调整：根据总问题数进行微调
        if total_checks > 0:
            failure_rate = total_failed / total_checks
            # 失败率超过50%时，额外扣分
            if failure_rate > 0.5:
                extra_penalty = (failure_rate - 0.5) * 20  # 最多扣10分
                total_score = max(0, total_score - extra_penalty)
                logger.info(f"失败率{failure_rate:.2%} > 50%，额外扣分{extra_penalty:.2f}")
        
        return total_score
    
    def _get_health_level(self, score: float) -> str:
        """
        根据评分获取健康等级
        
        Args:
            score: 健康评分（0-100）
            
        Returns:
            健康等级字符串
        """
        if score >= 90:
            return '优秀'
        elif score >= 75:
            return '良好'
        elif score >= 60:
            return '一般'
        elif score >= 40:
            return '警告'
        else:
            return '严重'
    
    def _get_severity_level(self, category: str, check_name: str, check_data: dict) -> int:
        """
        根据检查项类别和名称获取严重级别
        
        Args:
            category: 检查类别（如 'cluster_health', 'cluster_roles'）
            check_name: 检查项名称（如 'status', 'destructive_requires_name'）
            check_data: 检查数据
            
        Returns:
            严重级别（1, 2, 3）
            1: 不严重，可选的优化项
            2: 一般，建议处理
            3: 非常严重，必须处理
        """
        # 根据指标严重级别.md 文档定义的映射关系
        severity_map = {
            # 集群状态：3（非常严重）
            ('cluster_health', 'status'): 3,
            
            # 集群角色分配：2（一般）
            ('cluster_roles', 'independent_master'): 2,
            ('cluster_roles', 'has_ingest'): 2,
            ('cluster_roles', 'has_coordinator'): 2,
            
            # 集群索引删除保护配置：1（不严重，优化项）
            ('cluster_destructive', 'destructive_requires_name'): 1,
            
            # 各同类型节点JVM堆大小设置一致性检查：2
            ('jvm_consistency', '*'): 2,
            
            # 集群参数配置：1
            ('cluster_settings', '*'): 1,
            
            # 集群线程池使用情况：2
            ('thread_pool_status', '*'): 2,
            
            # 各节点JVM垃圾回收情况：3
            ('jvm_gc', '*'): 3,
            
            # 主分片数合理性检查：2
            ('primary_shard_rationality', '*'): 2,
            
            # 副本数量合理性检查：2
            ('replica_rationality', '*'): 2,
            
            # 写优化基础配置检查：2
            ('write_optimization', '*'): 2,
            
            # 分片延迟分配设置合理性检查：1
            ('delayed_allocation', '*'): 1,
            
            # 索引字段mappings数合理性检查：2
            ('mapping_count', '*'): 2,
            
            # 索引mapping字符串类型设定检查：2
            ('mapping_text_type', '*'): 2,
            
            # Segment数量过载检查：1
            ('segment_overload', '*'): 1,
            
            # 服务器swap分区检查：3
            ('swap_partition', '*'): 3,
            
            # 索引拒绝情形检查：2
            ('index_rejection', '*'): 2,
            
            # 搜索失败情形检查：2
            ('search_failure', '*'): 2,
            
            # 父级熔断情形检查：2
            ('breaker_status', '*'): 2,
            
            # 空分片情形检查：1
            ('empty_shards', '*'): 1,
            
            # node_resources检查：2
            ('node_resources', '*'): 2,
            
            # index_health检查：2
            ('index_health', '*'): 2,
            
            # shards检查：2
            ('shards', '*'): 2,
            
            # recovery检查：2
            ('recovery', '*'): 2,
            
            # ilm检查：1
            ('ilm', '*'): 1,
            
            # snapshot检查：1
            ('snapshot', '*'): 1,
            
            # security检查：1
            ('security', 'xpack_enabled'): 1,
        }
        
        # 精确匹配
        key = (category, check_name)
        if key in severity_map:
            return severity_map[key]
        
        # 通配符匹配
        wildcard_key = (category, '*')
        if wildcard_key in severity_map:
            return severity_map[wildcard_key]
        
        # 默认返回二级告警
        logger.debug(f"未找到 {category}.{check_name} 的级别配置，使用默认级别 2")
        return 2
    
    # ==================== 加权维度评分系统辅助方法 ====================

    def _load_indicator_weights(self) -> dict:
        """加载指标权重配置"""
        config_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'configs', 
            'indicator_weights.yaml'
        )
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('indicators', {})
        except Exception as e:
            logger.error(f"加载指标权重配置失败: {e}")
            return {}

    def _load_severity_level_weights(self) -> dict:
        """加载严重级别权重配置"""
        config_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'configs', 
            'severity_level_weights.yaml'
        )
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                levels = config.get('severity_levels', {})
                # 转换为 {level: weight} 格式
                result = {
                    1: levels.get('level_1', {}).get('weight', 0.20),
                    2: levels.get('level_2', {}).get('weight', 0.30),
                    3: levels.get('level_3', {}).get('weight', 0.50)
                }
                logger.info(f"加载严重级别权重配置成功: {result}")
                return result
        except Exception as e:
            logger.error(f"加载严重级别权重配置失败: {e}")
            # 返回默认配置
            return {1: 0.20, 2: 0.30, 3: 0.50}

 
    def _get_indicator_config(self, dimension: str, category: str, check_name: str, indicator_weights: dict) -> dict:
        """
        获取指标配置
        
        先尝试使用维度名称查找，如果找不到，再使用类别名称查找
        这样可以兼容两种配置结构：
        1. 按维度组织：{dimension: {check_name: config}}
        2. 按类别组织：{category: {check_name: config}}
        
        Args:
            dimension: 维度名称（如 'cluster_health'）
            category: 类别名称（如 'cluster_roles'）
            check_name: 检查项名称
            indicator_weights: 指标权重配置
            
        Returns:
            指标配置字典，如果找不到则返回None
        """
        # 先尝试使用维度名称查找
        dim_config = indicator_weights.get(dimension, {})
        config = dim_config.get(check_name)
        if config:
            return config
        
        # 如果找不到，再尝试使用类别名称查找
        cat_config = indicator_weights.get(category, {})
        return cat_config.get(check_name)

    def _calculate_single_indicator_score(self, check_data: dict, config: dict) -> float:
        """
        计算单个指标的得分
        
        Args:
            check_data: 检查数据 {'value': ..., 'passed': ...}
            config: 指标配置
            
        Returns:
            得分（0-100）
        """
        indicator_type = config.get('type', 'boolean')
        
        if indicator_type == 'numeric':
            value = check_data.get('value', 0)
            # 如果 value 是字典，无法进行数值计算，使用布尔型评分
            if isinstance(value, dict):
                passed = check_data.get('passed', True)
                severity = config.get('severity', 'warning')
                logger.debug(f"字典类型value降级为布尔评分: passed={passed}, severity={severity}")
                return 100 if passed else (0 if severity == 'critical' else 60)
            
            thresholds = config.get('thresholds', {})
            direction = config.get('direction', 'lower')
            
            return self._calculate_numeric_score(value, thresholds, direction)
        
        elif indicator_type == 'enum':
            value = check_data.get('value', '')
            # 如果 value 是字典，无法进行枚举匹配，使用布尔型评分
            if isinstance(value, dict):
                passed = check_data.get('passed', True)
                severity = config.get('severity', 'warning')
                logger.debug(f"字典类型value降级为布尔评分: passed={passed}, severity={severity}")
                return 100 if passed else (0 if severity == 'critical' else 60)
            
            values_config = config.get('values', {})
            return values_config.get(str(value).upper(), 60)
        
        else:  # boolean
            passed = check_data.get('passed', True)
            severity = config.get('severity', 'warning')
            return 100 if passed else (0 if severity == 'critical' else 60)

    def _calculate_numeric_score(self, value: float, thresholds: dict, direction: str) -> float:
        """
        计算数值型指标得分（线性插值）
        
        Args:
            value: 实际值
            thresholds: {'normal': ..., 'warning': ..., 'critical': ...}
            direction: 'lower'（越小越好）或 'higher'（越大越好）
            
        Returns:
            得分（0-100）
        """
        normal = thresholds.get('normal', 0)
        warning = thresholds.get('warning', 0)
        critical = thresholds.get('critical', 0)
        
        if direction == 'lower':
            # 越小越好
            if value <= normal:
                return 100
            elif value <= warning:
                ratio = (warning - value) / (warning - normal) if warning != normal else 0
                return 60 + 40 * max(0, min(1, ratio))
            elif value <= critical:
                ratio = (critical - value) / (critical - warning) if critical != warning else 0
                return 60 * max(0, min(1, ratio))
            else:
                return 0
        else:
            # 越大越好
            if value >= normal:
                return 100
            elif value >= warning:
                ratio = (value - warning) / (normal - warning) if normal != warning else 0
                return 60 + 40 * max(0, min(1, ratio))
            elif value >= critical:
                ratio = (value - critical) / (warning - critical) if warning != critical else 0
                return 60 * max(0, min(1, ratio))
            else:
                return 0

    def _calculate_dimension_score(self, scores: dict, weights: dict) -> float:
        """计算维度得分（加权平均）"""
        total_weight = sum(weights.values())
        if total_weight == 0:
            return 100
        
        weighted_sum = sum(scores[k] * weights[k] for k in scores.keys() if k in weights)
        return weighted_sum / total_weight

    def _calculate_total_score(self, dimension_scores: dict, dimension_weights: dict) -> float:
        """计算总评分（维度加权平均）"""
        total_weight = sum(dimension_weights.values())
        if total_weight == 0:
            return 100
        
        weighted_sum = sum(dimension_scores[dim] * dimension_weights[dim] 
                          for dim in dimension_scores.keys() if dim in dimension_weights)
        return weighted_sum / total_weight
    

    def _calculate_severity_based_score(self, check_results: dict) -> dict:
        """
        基于严重级别的评分算法
        
        Args:
            check_results: 检查项结果字典
            
        Returns:
            包含总评分、各级别得分和详细信息的字典
        """
        try:
            # 加载配置
            severity_weights = self._load_severity_level_weights()
            indicator_weights = self._load_indicator_weights()
            
            logger.info(f"开始基于严重级别的评分，共{len(check_results)}个类别")
            
            # 步骤1：计算每个指标的得分和严重级别
            indicator_scores = {}
            for category, items in check_results.items():
                if not isinstance(items, dict):
                    continue
                
                for check_name, check_data in items.items():
                    if not isinstance(check_data, dict):
                        continue
                    
                    # 获取指标配置
                    config = self._get_indicator_config(None, category, check_name, indicator_weights)
                    
                    # 计算指标得分
                    try:
                        if not config:
                            # 无配置时使用默认评分
                            passed = check_data.get('passed', True)
                            score = 100 if passed else 60
                        else:
                            score = self._calculate_single_indicator_score(check_data, config)
                    except Exception as e:
                        logger.error(f"计算指标 {category}.{check_name} 得分失败: {e}")
                        score = 60
                    
                    # 获取严重级别
                    severity_level = self._get_severity_level(category, check_name, check_data)
                    
                    indicator_key = f"{category}.{check_name}"
                    indicator_scores[indicator_key] = {
                        'score': score,
                        'severity_level': severity_level,
                        'category': category,
                        'check_name': check_name,
                        'value': check_data.get('value'),
                        'passed': check_data.get('passed', True)
                    }
            
            logger.info(f"步骤1完成：计算了 {len(indicator_scores)} 个指标得分")
            
            # 步骤2：按严重级别分组
            level_scores = {1: [], 2: [], 3: []}
            for key, info in indicator_scores.items():
                level = info['severity_level']
                if level in level_scores:
                    level_scores[level].append(info['score'])
            
            # 步骤3：计算各级别的平均分
            level_averages = {}
            for level in [1, 2, 3]:
                scores = level_scores[level]
                if scores:
                    level_averages[level] = sum(scores) / len(scores)
                else:
                    level_averages[level] = 100  # 没有该级别指标时视为满分
            
            logger.info(f"步骤2完成：各级别平均分 - 一级:{level_averages[1]:.2f}, 二级:{level_averages[2]:.2f}, 三级:{level_averages[3]:.2f}")
            
            # 步骤4：按严重级别权重计算总分
            total_score = sum(
                level_averages[level] * severity_weights.get(level, 0)
                for level in [1, 2, 3]
            )
            
            logger.info(f"步骤3完成：总评分={total_score:.2f}")
            
            # 构建返回结果
            result = {
                'total_score': round(total_score, 2),
                'health_level': self._get_health_level(total_score),
                'severity_level_scores': {
                    level: {
                        'average_score': round(avg, 2),
                        'weight': severity_weights.get(level, 0),
                        'indicator_count': len(level_scores[level]),
                        'level_description': {
                            1: '优化建议',
                            2: '建议处理',
                            3: '必须处理'
                        }.get(level, '')
                    }
                    for level, avg in level_averages.items()
                },
                'indicator_details': indicator_scores
            }
            
            logger.info(f"基于严重级别评分: 总分={total_score:.2f}, 等级={result['health_level']}")
            
            return result
            
        except Exception as e:
            logger.error(f"基于严重级别评分过程中发生错误: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def _generate_check_results(self) -> dict:
        """生成所有检查项的详细结果（包含通过和未通过的项）"""
        cluster_health = self.data.get('cluster_health', {})
        nodes = self.data.get('nodes', [])
        indices = self.data.get('indices', [])
        thread_pools = self.data.get('thread_pools', [])
        shards = self.data.get('shards', [])
        recovery = self.data.get('recovery', {})
        cluster_stats = self.data.get('cluster_stats', {})
        nodes_stats = get_nodes_stats_payload(self.data)
        
        check_results = {}
        
        # 1. 集群健康检查
        # 从规则引擎配置中读取阈值
        cluster_config = self.rules_engine.config.get('cluster', {})
        index_config = self.rules_engine.config.get('index', {})  # 添加索引配置
        node_config = self.rules_engine.config.get('node', {})  # 添加节点配置
        
        check_results['cluster_health'] = {
            'status': {
                'value': cluster_health.get('status', 'unknown').upper(),
                'passed': cluster_health.get('status', '').upper() == 'GREEN',
                'message': f"集群状态：{cluster_health.get('status', 'unknown').upper()}"
            },
            'active_shards_percent': {
                'value': cluster_health.get('active_shards_percent_as_number', 
                                           cluster_health.get('active_shards_percent', 0)),
                'passed': cluster_health.get('active_shards_percent_as_number', 
                                           cluster_health.get('active_shards_percent', 0)) >= cluster_config.get('active_shards_percent', {}).get('warning', 95),
                'threshold': f">={cluster_config.get('active_shards_percent', {}).get('warning', 95)}%",
                'message': f"活跃分片比例：{cluster_health.get('active_shards_percent_as_number', cluster_health.get('active_shards_percent', 0))}%"
            },
            'unassigned_shards': {
                'value': cluster_health.get('unassigned_shards', 0),
                'passed': cluster_health.get('unassigned_shards', 0) < cluster_config.get('unassigned_shards', {}).get('warning', 1),
                'threshold': str(cluster_config.get('unassigned_shards', {}).get('warning', 1)),
                'message': f"未分配分片：{cluster_health.get('unassigned_shards', 0)}"
            },
            'initializing_shards': {
                'value': cluster_health.get('initializing_shards', 0),
                'passed': cluster_health.get('initializing_shards', 0) < cluster_config.get('initializing_shards', {}).get('warning', 10),
                'threshold': f"<{cluster_config.get('initializing_shards', {}).get('warning', 10)}",
                'message': f"初始化中分片：{cluster_health.get('initializing_shards', 0)}"
            },
            'relocating_shards': {
                'value': cluster_health.get('relocating_shards', 0),
                'passed': cluster_health.get('relocating_shards', 0) < cluster_config.get('relocating_shards', {}).get('warning', 10),
                'threshold': f"<{cluster_config.get('relocating_shards', {}).get('warning', 10)}",
                'message': f"迁移中分片：{cluster_health.get('relocating_shards', 0)}"
            },
            'delayed_unassigned_shards': {
                'value': cluster_health.get('delayed_unassigned_shards', 0),
                'passed': cluster_health.get('delayed_unassigned_shards', 0) < cluster_config.get('delayed_unassigned_shards', {}).get('warning', 1),
                'threshold': f"<{cluster_config.get('delayed_unassigned_shards', {}).get('warning', 1)}",
                'message': f"延迟未分配分片：{cluster_health.get('delayed_unassigned_shards', 0)}"
            },
            'pending_tasks': {
                'value': cluster_health.get('number_of_pending_tasks', 0),
                'passed': cluster_health.get('number_of_pending_tasks', 0) < cluster_config.get('pending_tasks', {}).get('warning', 50),
                'threshold': f"<{cluster_config.get('pending_tasks', {}).get('warning', 50)}",
                'message': f"集群任务队列：{cluster_health.get('number_of_pending_tasks', 0)}"
            },
            'nodes_total': {
                'value': cluster_health.get('number_of_nodes', 0),
                'passed': cluster_health.get('number_of_nodes', 0) < cluster_config.get('nodes', {}).get('total_warning', 100),
                'threshold': f"<{cluster_config.get('nodes', {}).get('total_warning', 100)}",
                'message': f"集群节点总数：{cluster_health.get('number_of_nodes', 0)}"
            },
            'nodes_data': {
                'value': cluster_health.get('number_of_data_nodes', 0),
                'passed': cluster_health.get('number_of_data_nodes', 0) < cluster_config.get('nodes', {}).get('data_nodes_warning', 50),
                'threshold': f"<{cluster_config.get('nodes', {}).get('data_nodes_warning', 50)}",
                'message': f"数据节点数：{cluster_health.get('number_of_data_nodes', 0)}"
            }
        }
        
        # 1.1 集群角色分配检查
        check_results['cluster_roles'] = {}
        if nodes:
            # 处理 nodes 可能是对象的情况
            node_list = []
            if isinstance(nodes, dict):
                # nodes 是对象，值是节点信息
                node_list = list(nodes.values())
            elif isinstance(nodes, list):
                # nodes 是数组
                node_list = nodes
            
            # 检查角色配置
            def has_role(node, role):
                """检查节点是否具有指定角色"""
                roles = node.get('roles', [])
                if isinstance(roles, list):
                    # 处理列表形式的 roles，如 ['dilmrt']
                    for r in roles:
                        if isinstance(r, str) and role in r:
                            return True
                elif isinstance(roles, str):
                    # 处理字符串形式的 roles，如 'dilmrt'
                    return role in roles
                return False

            has_independent_master = any(has_role(node, 'm') and not has_role(node, 'd') for node in node_list)
            has_ingest = any(has_role(node, 'i') for node in node_list)
            has_coordinator = any(not has_role(node, 'm') and not has_role(node, 'd') and not has_role(node, 'i') for node in node_list)
     
            check_results['cluster_roles']['independent_master'] = {
                'value': '是' if has_independent_master else '否',
                'passed': has_independent_master,
                'message': f"主节点为独立主节点：{'是' if has_independent_master else '否'}"
            }
            check_results['cluster_roles']['has_ingest'] = {
                'value': '是' if has_ingest else '否',
                'passed': has_ingest,
                'message': f"存在预处理节点：{'是' if has_ingest else '否'}"
            }
            check_results['cluster_roles']['has_coordinator'] = {
                'value': '是' if has_coordinator else '否',
                'passed': has_coordinator,
                'message': f"存在专用的协调节点：{'是' if has_coordinator else '否'}"
            }
        
        # 1.2 索引删除保护配置检查
        cluster_settings = self.data.get('cluster_settings_defaults', {})
        destructive_requires_name = False
        if cluster_settings:
            persistent = cluster_settings.get('persistent', {})
            transient = cluster_settings.get('transient', {})
            
            # 优先检查 persistent 配置
            if 'action.destructive_requires_name' in persistent:
                destructive_requires_name = str(persistent['action.destructive_requires_name']).lower() == 'true'
            elif 'action' in persistent and 'destructive_requires_name' in persistent['action']:
                destructive_requires_name = str(persistent['action']['destructive_requires_name']).lower() == 'true'
            # 其次检查 transient 配置
            elif 'action.destructive_requires_name' in transient:
                destructive_requires_name = str(transient['action.destructive_requires_name']).lower() == 'true'
            elif 'action' in transient and 'destructive_requires_name' in transient['action']:
                destructive_requires_name = str(transient['action']['destructive_requires_name']).lower() == 'true'
        
        check_results['cluster_destructive'] = {
            'destructive_requires_name': {
                'value': str(destructive_requires_name).lower(),
                'passed': destructive_requires_name,
                'message': f"关闭索引的模糊匹配删除行为：{'已开启' if destructive_requires_name else '未开启'} (值: {str(destructive_requires_name).lower()})"
            }
        }
        
        # 2.1 JVM 堆大小一致性检查（使用 cat/汇总 nodes，非 nodes_stats）
        jvm_nodes_source = self.data.get('nodes', [])
        
        # 初始化 jvm_consistency_results
        jvm_consistency_results = {
            'master': {
                'value': '-',
                'passed': True,
                'message': 'master'
            },
            'data': {
                'value': '-',
                'passed': True,
                'message': 'data'
            },
            'coordinator': {
                'value': '-',
                'passed': True,
                'message': '协调节点'
            }
        }
        
        # 调试：打印 nodes_stats 数据
        # print("===== JVM 一致性检查调试信息 =====")
        # print(f"nodes_stats 存在: {nodes_stats}")
        # print(f"nodes_stats 类型: {type(nodes_stats)}")
        
        # 处理 JVM 节点数据
        nodes_data = None
        if isinstance(jvm_nodes_source, list):
            nodes_data = jvm_nodes_source
        elif isinstance(jvm_nodes_source, dict):
            if 'nodes' in jvm_nodes_source:
                nodes_data = jvm_nodes_source['nodes']
            elif 'data' in jvm_nodes_source:
                nodes_data = jvm_nodes_source['data']
            elif 'items' in jvm_nodes_source:
                nodes_data = jvm_nodes_source['items']
        
        if nodes_data:
            # print(f"nodes_data 类型: {type(nodes_data)}")
            # print(f"nodes_data 长度: {len(nodes_data)}")
            
            roles_map = {'master': [], 'data': [], 'coordinator': []}
            
            # 直接从 nodes_data 中获取节点信息
            if isinstance(nodes_data, dict):
                # 节点数据是字典形式，键是节点 ID
                for node_id, stats in nodes_data.items():
                    # 从 stats 中获取节点角色
                    roles = stats.get('roles', [])
                    # 获取堆大小
                    heap_max = stats.get('jvm_heap_max', stats.get('jvm', {}).get('mem', {}).get('heap_max', 'N/A'))
                    
                    # 调试：打印每个节点的信息
                    # print(f"\n===== 节点 {node_id} =====")
                    # print(f"节点名称: {stats.get('name')}")
                    # print(f"节点角色: {roles}")
                    # print(f"Heap Max: {heap_max}")
                    
                    if is_master_eligible_node(roles):
                        roles_map['master'].append(heap_max)
                    if is_data_node(roles):
                        roles_map['data'].append(heap_max)
                    if is_dedicated_coordinator_node(roles):
                        roles_map['coordinator'].append(heap_max)
            elif isinstance(nodes_data, list):
                # 节点数据是列表形式
                for stats in nodes_data:
                    roles = stats.get('roles', [])
                    heap_max = stats.get('jvm_heap_max', stats.get('jvm', {}).get('mem', {}).get('heap_max', 'N/A'))
                    if is_master_eligible_node(roles):
                        roles_map['master'].append(heap_max)
                    if is_data_node(roles):
                        roles_map['data'].append(heap_max)
                    if is_dedicated_coordinator_node(roles):
                        roles_map['coordinator'].append(heap_max)
            
            # 调试：打印 roles_map
            # print("\n===== Roles Map =====")
            # print(roles_map)
            
            # 收集所有节点的详细信息（节点名称、角色、堆大小）
            all_nodes_info = []
            
            # 重新遍历节点数据，收集详细信息
            if isinstance(nodes_data, dict):
                # 节点数据是字典形式，键是节点 ID
                for node_id, stats in nodes_data.items():
                    roles = stats.get('roles', [])
                    heap_max = stats.get('jvm_heap_max', stats.get('jvm', {}).get('mem', {}).get('heap_max', 'N/A'))
                    node_name = stats.get('name', node_id)
                    all_nodes_info.append({
                        'name': node_name,
                        'roles': roles_concat_lower(roles),
                        'roles_list': normalize_roles(roles),
                        'heap': heap_max,
                    })
            elif isinstance(nodes_data, list):
                for stats in nodes_data:
                    roles = stats.get('roles', [])
                    heap_max = stats.get('jvm_heap_max', stats.get('jvm', {}).get('mem', {}).get('heap_max', 'N/A'))
                    node_name = stats.get('name', 'unknown')
                    all_nodes_info.append({
                        'name': node_name,
                        'roles': roles_concat_lower(roles),
                        'roles_list': normalize_roles(roles),
                        'heap': heap_max,
                    })
            
            # 按照需求文档格式输出
            role_display_names = {
                'master': 'master',
                'data': 'data',
                'coordinator': '协调节点'
            }
            
            for role_name, heaps in roles_map.items():
                unique_heaps = set()
                for heap in heaps:
                    # 确保 heap 值是字符串类型
                    if heap is not None:
                        unique_heaps.add(str(heap))
                
                is_consistent = len(unique_heaps) <= 1
                has_data = len(heaps) > 0
                
                # 根据需求文档格式：
                # 如果该角色下所有节点堆大小一致，显示该角色的堆大小
                # 如果该角色下有不一致的情况，显示该角色下所有节点的详细信息
                # 对于协调节点，只有当存在专用协调节点时才显示，否则显示‘-’
                if role_name == 'coordinator':
                    if has_data:
                        # 存在专用协调节点，检查一致性
                        if is_consistent:
                            # 该角色下所有节点堆大小一致，显示该角色的堆大小
                            status_passed = True
                            value = ', '.join(unique_heaps) if unique_heaps else ''
                        else:
                            # 该角色下有不一致的情况，显示该角色下所有节点的详细信息
                            status_passed = False
                            node_details = []
                            for node in all_nodes_info:
                                if is_dedicated_coordinator_node(
                                    node.get('roles_list', node.get('roles'))
                                ):
                                    node_details.append(
                                        f"{node['name']}({node['roles']}):{node['heap']}"
                                    )
                            value = '\n'.join(node_details) if node_details else ''
                    else:
                        # 不存在专用协调节点，显示‘-’
                        status_passed = True
                        value = '-'
                else:
                    # 对于 master 和 data 角色，正常检查
                    if has_data:
                        if is_consistent:
                            # 该角色下所有节点堆大小一致，显示该角色的堆大小
                            status_passed = True
                            value = ', '.join(unique_heaps) if unique_heaps else ''
                        else:
                            # 该角色下有不一致的情况，显示该角色下所有节点的详细信息
                            status_passed = False
                            node_details = []
                            for node in all_nodes_info:
                                roles_ref = node.get('roles_list', node.get('roles'))
                                if role_name == 'master' and is_master_eligible_node(
                                    roles_ref
                                ):
                                    node_details.append(
                                        f"{node['name']}({node['roles']}):{node['heap']}"
                                    )
                                elif role_name == 'data' and is_data_node(roles_ref):
                                    node_details.append(
                                        f"{node['name']}({node['roles']}):{node['heap']}"
                                    )
                            value = '\n'.join(node_details) if node_details else ''
                    else:
                        status_passed = True  # 无数据时默认为通过
                        value = '-'
                
                jvm_consistency_results[role_name] = {
                    'value': value,
                    'passed': status_passed,
                    'message': role_display_names.get(role_name, role_name)  # 只显示角色名称
                }
                # print(f"\n===== {role_name} 结果 =====")
                # print(f"值: {value}")
                # print(f"通过: {status_passed}")
        # 无论是否有数据，都添加 jvm_consistency 到 check_results
        check_results['jvm_consistency'] = jvm_consistency_results
        # print("\n===== 最终 JVM 一致性检查结果 =====")
        # print(jvm_consistency_results)

        # 2.2 集群参数配置检查
        cluster_settings = self.data.get('cluster_settings_defaults', {})
        if cluster_settings:
            persistent = cluster_settings.get('persistent', {})
            transient = cluster_settings.get('transient', {})
            settings = {**persistent, **transient}
            
            watermarks = {
                'low': settings.get('cluster.routing.allocation.disk.watermark.low', '默认值 85%'),
                'high': settings.get('cluster.routing.allocation.disk.watermark.high', '默认值 90%'),
                'flood': settings.get('cluster.routing.allocation.disk.watermark.flood_stage', '默认值 95%')
            }
            recoveries = {
                'concurrent': settings.get('cluster.routing.allocation.node_concurrent_recoveries', '默认值 2'),
                'initial': settings.get('cluster.routing.allocation.node_initial_primaries_recoveries', '默认值 4')
            }
            
            check_results['cluster_settings'] = {
                'watermarks': {
                    'value': f"Low: {watermarks['low']}, High: {watermarks['high']}, Flood: {watermarks['flood']}",
                    'passed': True,
                    'message': f"磁盘水位线配置 - Low: {watermarks['low']}, High: {watermarks['high']}, Flood: {watermarks['flood']}"
                },
                'recoveries': {
                    'value': f"并发: {recoveries['concurrent']}, 初始: {recoveries['initial']}",
                    'passed': True,
                    'message': f"分片恢复配置 - 并发数: {recoveries['concurrent']}, 初始主分片数: {recoveries['initial']}"
                }
            }

        # 2.3 线程池使用情况检查
        thread_pool_checks = {}
        has_rejection = False
        if nodes_stats and 'nodes' in nodes_stats:
            for node_id, stats in nodes_stats['nodes'].items():
                node_name = stats.get('name', node_id)
                pools = stats.get('thread_pool', {})
                for pool_name, pool_data in pools.items():
                    rejected = pool_data.get('rejected', 0)
                    if rejected > 0:
                        has_rejection = True
                        thread_pool_checks[f"{node_name}_{pool_name}"] = {
                            'value': rejected,
                            'passed': False,
                            'message': f"节点 {node_name} 的 {pool_name} 线程池存在拒绝：{rejected}"
                        }
        
        check_results['thread_pool_status'] = {
            'overall': {
                'value': '存在拒绝' if has_rejection else '正常',
                'passed': not has_rejection,
                'message': f"各节点的各个线程池使用情况：{'不存在线程池请求拒绝的节点' if not has_rejection else '部分节点存在拒绝，详见详情'}"
            }
        }
        if thread_pool_checks:
            check_results['thread_pool_status'].update(thread_pool_checks)

        # 2.4 性能与稳定性检查 (GC, Swap, Breakers, Missing)
        perf_stability = {}
        
        # GC 检查
        total_gc_count = 0
        gc_abnormal_nodes = []
        if nodes_stats and 'nodes' in nodes_stats:
            for node_id, stats in nodes_stats['nodes'].items():
                node_name = stats.get('name', node_id)
                jvm_mem = stats.get('jvm', {}).get('mem', {})
                old_gen_used = jvm_mem.get('pools', {}).get('old', {}).get('used_in_bytes', 0)
                heap_max = jvm_mem.get('heap_max_in_bytes', 1)
                
                if heap_max > 0 and old_gen_used / heap_max > 0.6:
                    gc_abnormal_nodes.append(node_name)
                
                collectors = stats.get('jvm', {}).get('gc', {}).get('collectors', {})
                for collector_name, collector_data in collectors.items():
                    total_gc_count += collector_data.get('collection_count', 0)
        
        perf_stability['gc_status'] = {
            'value': f"总次数: {total_gc_count}",
            'passed': len(gc_abnormal_nodes) == 0,
            'message': f"所有节点GC情况：{'不存在GC异常' if not gc_abnormal_nodes else f'{len(gc_abnormal_nodes)}个节点Old Gen使用率过高'}"
        }

        # 服务器swap分区检查 - 单独分类
        swap_enabled_nodes = []
        if nodes_stats and 'nodes' in nodes_stats:
            for node_id, stats in nodes_stats['nodes'].items():
                if stats.get('os', {}).get('swap', {}).get('total_in_bytes', 0) > 0:
                    swap_enabled_nodes.append(stats.get('name', node_id))
        
        check_results['swap_partition'] = {
            'swap_status': {
                'value': '已禁用' if not swap_enabled_nodes else '未禁用',
                'passed': len(swap_enabled_nodes) == 0,
                'message': f"服务器swap分区检查：{'所有节点服务器均已禁用swap交换分区' if not swap_enabled_nodes else f'{len(swap_enabled_nodes)}个节点未禁用swap'}"
            }
        }

        # 父级熔断情形检查 - 单独分类
        breaker_tripped_nodes = []
        if nodes_stats and 'nodes' in nodes_stats:
            for node_id, stats in nodes_stats['nodes'].items():
                breakers = stats.get('breakers', {})
                for b_name, b_data in breakers.items():
                    if b_data.get('tripped', 0) > 0:
                        breaker_tripped_nodes.append(f"{stats.get('name', node_id)}({b_name})")
        
        check_results['breaker_status'] = {
            'tripped': {
                'value': '未触发' if not breaker_tripped_nodes else '已触发',
                'passed': len(breaker_tripped_nodes) == 0,
                'message': f"父级熔断情形检查：{'未出现父级熔断' if not breaker_tripped_nodes else f'{len(breaker_tripped_nodes)}个节点/熔断器触发过熔断'}"
            }
        }

        # 搜索失败情形检查 - 单独分类
        missing_node_details = find_nodes_with_search_missing(nodes_stats)
        
        check_results['search_failure'] = {
            'missing': {
                'value': '未发现' if not missing_node_details else f"{len(missing_node_details)}个节点",
                'passed': len(missing_node_details) == 0,
                'missing_nodes': missing_node_details,
                'message': (
                    "搜索失败情形检查：未出现搜索失败"
                    if not missing_node_details
                    else f"搜索失败情形检查：{len(missing_node_details)}个节点存在搜索缺失"
                ),
            }
        }

        check_results['performance_stability'] = perf_stability

        # 2. 节点资源检查
        if nodes:
            # 处理 nodes 可能是对象的情况
            node_list = []
            if isinstance(nodes, dict):
                # nodes 是对象，值是节点信息
                node_list = list(nodes.values())
            elif isinstance(nodes, list):
                # nodes 是数组
                node_list = nodes
            
            avg_disk = sum(node.get('disk_used_percent', 0) for node in node_list) / len(node_list)
            avg_heap = sum(node.get('heap_used_percent', 0) for node in node_list) / len(node_list)
            avg_cpu = sum(node.get('cpu_percent', 0) for node in node_list) / len(node_list)
            avg_load = sum(node.get('load_1m', 0) for node in node_list) / len(node_list)
            
            # 统计 CPU 核心数（用于计算系统负载阈值）
            # 如果节点数据中没有 cpu_cores 字段或为 0，使用默认值 8（典型生产环境配置）
            cpu_cores_list = [node.get('cpu_cores', 0) for node in node_list]
            valid_cpu_cores = [c for c in cpu_cores_list if c and c > 0]
            
            if valid_cpu_cores:
                avg_cpu_cores = sum(valid_cpu_cores) / len(valid_cpu_cores)
            else:
                # 无法获取 CPU 核心数时，使用默认值 8
                avg_cpu_cores = 8
                logger.debug(f"无法获取 CPU 核心数，使用默认值：{avg_cpu_cores}")
            
            # 从规则引擎配置中读取阈值
            node_config = self.rules_engine.config.get('node', {})
            
            shards_data = self.data.get('shards', [])
            shards_per_node_count = count_shards_per_node(shards_data) if shards_data else {}
            max_shards, max_shards_node = max_shards_on_single_node(shards_data)
            avg_shards = (
                sum(shards_per_node_count.values()) / len(shards_per_node_count)
                if shards_per_node_count
                else 0
            )
            
            # 计算节点JVM堆大小阈值（用于分片数检查）
            nodes = self.data.get('nodes', [])
            node_jvm_map = {}
            if nodes:
                # 处理 nodes 可能是字典的情况
                if isinstance(nodes, dict):
                    nodes_list = list(nodes.values())
                else:
                    nodes_list = nodes
                
                # 构建节点名称到JVM堆大小的映射
                for node in nodes_list:
                    node_name = node.get('name', '')
                    if node_name:
                        # 尝试获取JVM堆大小
                        jvm_heap_max = node.get('jvm_heap_max', '')
                        if jvm_heap_max:
                            # 提取数字部分
                            import re
                            match = re.search(r'\d+', jvm_heap_max)
                            if match:
                                jvm_heap_gb = int(match.group())
                                node_jvm_map[node_name] = jvm_heap_gb
            
            # 计算分片数阈值（节点JVM堆大小*20）
            if node_jvm_map and max_shards_node != 'N/A' and max_shards_node in node_jvm_map:
                # 使用单节点最大分片数对应节点的阈值
                jvm_heap_gb = node_jvm_map[max_shards_node]
                shards_threshold = jvm_heap_gb * 20
            else:
                # 如果没有节点JVM堆大小信息，使用默认值
                shards_threshold = node_config.get('shards_per_node', {}).get('warning', 500)
            
            # 统计连接数
            total_connections = 0
            max_connections = 0
            max_connections_node = 'N/A'
            if nodes_stats and 'nodes' in nodes_stats:
                for node_id, node_stats in nodes_stats['nodes'].items():
                    server_open = node_stats.get('transport', {}).get('server_open', 0)
                    total_connections += server_open
                    if server_open > max_connections:
                        max_connections = server_open
                        max_connections_node = node_stats.get('name', node_id)
            
            # 计算负载阈值
            load_config = node_config.get('load_average', {})
            warning_multiplier = load_config.get('warning_multiplier', 1.5)
            warning_threshold = warning_multiplier * avg_cpu_cores if warning_multiplier > 0 else 0
            
            check_results['node_resources'] = {
                'disk_usage_percent': {
                    'value': round(avg_disk, 2),
                    'passed': avg_disk < node_config.get('disk_usage_percent', {}).get('warning', 70),
                    'threshold': f"<{node_config.get('disk_usage_percent', {}).get('warning', 70)}%",
                    'message': f"平均磁盘使用率：{avg_disk:.1f}%"
                },
                'heap_used_percent': {
                    'value': round(avg_heap, 2),
                    'passed': avg_heap < node_config.get('heap_used_percent', {}).get('warning', 70),
                    'threshold': f"<{node_config.get('heap_used_percent', {}).get('warning', 70)}%",
                    'message': f"平均 JVM 堆使用率：{avg_heap:.1f}%"
                },
                'cpu_percent': {
                    'value': round(avg_cpu, 2),
                    'passed': avg_cpu < node_config.get('cpu_percent', {}).get('warning', 60),
                    'threshold': f"<{node_config.get('cpu_percent', {}).get('warning', 60)}%",
                    'message': f"平均 CPU 使用率：{avg_cpu:.1f}%"
                },
                'load_average': {
                    'value': round(avg_load, 2),
                    'passed': avg_load < warning_threshold,
                    'threshold': f"<{warning_multiplier}x CPU cores ({warning_threshold:.1f})",
                    'message': f"平均系统负载 (1m): {avg_load:.2f}"
                },
                'shards_per_node': {
                    'value': max_shards,
                    'passed': max_shards < shards_threshold,
                    'threshold': f"<{shards_threshold}",
                    'message': f"单节点最大分片数：{max_shards}（{max_shards_node}）"
                },
                'connections': {
                    'value': max_connections,
                    'passed': max_connections < node_config.get('connections', {}).get('warning', 1000),
                    'threshold': f"<{node_config.get('connections', {}).get('warning', 1000)}",
                    'message': f"节点最大连接数：{max_connections}（{max_connections_node}）"
                }
            }
        
        # 3. 索引相关检查
        if indices:
            # 3.1 主分片数合理性检查（单主分片平均 > 配置阈值，默认 40GB）
            rules_config = self.rules_engine.config if self.rules_engine else {}
            oversized_threshold_gb = oversized_primary_shard_threshold_gb(rules_config)
            oversized_details = find_oversized_primary_shard_indices(
                indices, oversized_threshold_gb
            )
            oversized_names = [d["index_name"] for d in oversized_details]
            threshold_label = (
                int(oversized_threshold_gb)
                if oversized_threshold_gb == int(oversized_threshold_gb)
                else oversized_threshold_gb
            )
            if not oversized_names:
                shard_rationality_message = (
                    f"分片正常：集群中不存在过大(单分片>{threshold_label}GB)分片的索引"
                )
            else:
                shard_rationality_message = (
                    f"分片异常：{len(oversized_names)}个索引存在超大分片"
                    f"(单分片>{threshold_label}GB)"
                )

            # 主分片数合理性检查 - 单独分类
            check_results['primary_shard_rationality'] = {
                'shard_size_rationality': {
                    'value': f"{len(oversized_names)}个索引",
                    'passed': len(oversized_names) == 0,
                    'threshold_gb': oversized_threshold_gb,
                    'oversized_indices': oversized_details,
                    'message': shard_rationality_message,
                }
            }

            # 3.2 副本数量合理性检查
            zero_rep_indices = [
                index_name_from_record(idx)
                for idx in indices
                if index_replica_shards(idx) == 0
            ]
            # 副本数量合理性检查 - 单独分类
            check_results['replica_rationality'] = {
                'replica_count': {
                    'value': f"{len(zero_rep_indices)}个索引",
                    'passed': len(zero_rep_indices) == 0,
                    'message': f"副本正常：{'所有索引副本数大于 0' if not zero_rep_indices else f'{len(zero_rep_indices)}个索引副本数为 0'}"
                }
            }

            # 3.3 写优化基础配置检查 (refresh_interval != 1s)
            non_optimised_write = []
            index_settings = self.data.get('settings', {})
            for idx in indices:
                if idx.get('index', idx.get('name', '')).startswith('.'):
                    continue
                settings = index_settings.get(idx.get('index', idx.get('name', '')), {}).get('settings', {}).get('index', {})
                if "refresh_interval" not in settings or settings["refresh_interval"] == "1s":
                      non_optimised_write.append(idx.get('index', idx.get('name', 'unknown')))
            
            # 写优化基础配置检查 - 单独分类
            check_results['write_optimization'] = {
                'refresh_interval': {
                    'value': f"{len(non_optimised_write)}个索引",
                    'passed': len(non_optimised_write) == 0,
                    'message': f"完全配置：{'集群中全部索引均进行写入优化配置（修改refresh_interval）' if not non_optimised_write else f'{len(non_optimised_write)}个索引未优化'}"
                }
            }

            # 3.4 分片延迟分配设置合理性检查
            delayed_indices = []
            for idx in indices:
                settings = index_settings.get(idx.get('index', idx.get('name', '')), {}).get('settings', {}).get('index', {})
                if 'unassigned' in settings and 'node_left' in settings.get('unassigned', {}):
                    delayed_indices.append(idx.get('index', idx.get('name', 'unknown')))
            
            # 分片延迟分配设置合理性检查 - 单独分类（未配置视为不通过）
            has_delayed_setting = len(delayed_indices) > 0
            check_results['delayed_allocation'] = {
                'settings': {
                    'value': f"{len(delayed_indices)}个索引",
                    'passed': has_delayed_setting,
                    'message': (
                        f"分片延迟分配设置：已配置 ({len(delayed_indices)}个索引)"
                        if has_delayed_setting
                        else "分片延迟分配设置：未配置 (0个索引)"
                    ),
                    'suggestion': (
                        ''
                        if has_delayed_setting
                        else (
                            "建议为业务索引配置 index.unassigned.node_left.delayed_timeout，"
                            "减少节点短暂离线时的分片重分配开销"
                        )
                    ),
                }
            }

            # 3.5 mapping字段数合理性检查 (>100)
            mappings_data = self.data.get('mappings', {})
            def count_mappings(m):
                count = 0
                if 'properties' in m:
                    count += len(m['properties'])
                    for field in m['properties']:
                        if 'properties' in m['properties'][field]:
                            count += count_mappings(m['properties'][field]) - 1
                return count

            too_many_mappings = []
            for idx in indices:
                m_count = count_mappings(mappings_data.get(idx.get('index', idx.get('name', '')), {}).get('mappings', {}))
                if m_count > 100:
                    too_many_mappings.append(f"{idx.get('index', idx.get('name', 'unknown'))}({m_count})")
            
            # 索引字段mappings数合理性检查 - 单独分类
            check_results['mapping_count'] = {
                'field_count': {
                    'value': f"{len(too_many_mappings)}个索引",
                    'passed': len(too_many_mappings) == 0,
                    'message': f"mapping 字段合理",
                    'detail': f"所有索引的 mapping 字段数是否过多（>100）"
                }
            }

            # 3.6 mapping字符串类型设定检查 (text + keyword)
            default_text_mapping = {
                "type": "text",
                "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}
            }
            def is_default_text(m):
                if 'properties' not in m:
                    return True
                for f in m['properties']:
                    prop = m['properties'][f]
                    if 'properties' in prop:
                        if not is_default_text(prop):
                            return False
                    elif prop.get('type') == 'text' and prop != default_text_mapping:
                        return False
                return True

            default_text_indices = [idx.get('index', idx.get('name', 'unknown')) for idx in indices if is_default_text(mappings_data.get(idx.get('index', idx.get('name', '')), {}).get('mappings', {}))]
            # 索引mapping字符串类型设定检查 - 单独分类
            check_results['mapping_text_type'] = {
                'string_type': {
                    'value': f"{len(default_text_indices)}个索引",
                    'passed': len(default_text_indices) == 0,
                    'message': f"mapping 字符串类型设定合理",
                    'detail': f"所有索引的字符串类型字段是否采用的默认设定，即 text + keyword 的组合"
                }
            }

            # 3.7 Segment数量过载检查（对齐 diagnostic indices_too_many_segments）
            seg_per_shard = per_primary_shard_threshold(
                {'index': {'segments_count': index_config.get('segments_count', {})}}
            )
            overloaded_segments = find_indices_with_too_many_segments(
                indices, seg_per_shard
            )
            overloaded_names = [d["index_name"] for d in overloaded_segments]
            if not overloaded_names:
                segment_message = (
                    f"Segment数量正常：所有索引分片的 segments 均在合理范围"
                    f"(单分片≤{seg_per_shard})"
                )
            else:
                segment_message = (
                    f"Segment数量异常：{len(overloaded_names)}个索引存在过多 segments"
                    f"(单分片>{seg_per_shard})"
                )
            check_results['segment_overload'] = {
                'segment_count': {
                    'value': f"{len(overloaded_names)}个索引",
                    'passed': len(overloaded_names) == 0,
                    'per_primary_shard_threshold': seg_per_shard,
                    'overloaded_indices': overloaded_segments,
                    'message': segment_message,
                }
            }

            # 3.8 空分片情形检查
            empty_indices = [idx.get('index', idx.get('name', 'unknown')) for idx in indices if idx.get('docs_count', 0) == 0]
            # 空分片情形检查 - 单独分类
            check_results['empty_shards'] = {
                'empty_indices': {
                    'value': f"{len(empty_indices)}个索引",
                    'passed': len(empty_indices) == 0,
                    'message': f"未出现空白分片：{'所有索引均有数据' if not empty_indices else f'{len(empty_indices)}个索引为空'}"
                }
            }

            # 3.9 索引拒绝情形检查 (从 nodes_stats 聚合)
            write_rejected_nodes = []
            if nodes_stats and 'nodes' in nodes_stats:
                for node_id, stats in nodes_stats['nodes'].items():
                    rejected = stats.get('thread_pool', {}).get('write', {}).get('rejected', 0)
                    if rejected > 0:
                        write_rejected_nodes.append(stats.get('name', node_id))
            
            # 索引拒绝情形检查 - 单独分类
            check_results['index_rejection'] = {
                'write_rejected': {
                    'value': f"{len(write_rejected_nodes)}个节点",
                    'passed': len(write_rejected_nodes) == 0,
                    'message': f"未出现索引拒绝：{'未发现索引写入拒绝的节点' if not write_rejected_nodes else f'{len(write_rejected_nodes)}个节点存在写入拒绝'}"
                }
            }

        if indices:
            green_count = sum(1 for idx in indices if idx.get('health') == 'green')
            yellow_count = sum(1 for idx in indices if idx.get('health') == 'yellow')
            red_count = sum(1 for idx in indices if idx.get('health') == 'red')
            large_indices_count = sum(1 for idx in indices if idx.get('store_size_bytes', 0) > index_config.get('size_gb', {}).get('critical', 100) * (1024**3))
            high_segments_count = sum(1 for idx in indices if idx.get('segments_count', 0) > index_config.get('segments_count', {}).get('critical', 500))
            high_shards_count = sum(1 for idx in indices if idx.get('shards_count', 0) > index_config.get('shards_per_index', {}).get('critical', 100))  # 默认 critical 阈值
            large_docs_count = sum(1 for idx in indices if idx.get('docs_count', 0) > index_config.get('docs_count', {}).get('warning', 100000000))  # 使用 warning 阈值，与规则引擎保持一致
            high_deleted_docs_count = sum(1 for idx in indices if idx.get('deleted_docs_ratio', 0) > index_config.get('deleted_docs_ratio', {}).get('critical', 0.2))  # 默认 critical 阈值
            
            check_results['index_health'] = {
                'health_distribution': {
                    'value': {'green': green_count, 'yellow': yellow_count, 'red': red_count},
                    'passed': red_count == 0 and yellow_count == 0,
                    'check_item': 'index.health',  # 与规则引擎中的 check_item 保持一致
                    'message': f"索引健康分布：GREEN={green_count}, YELLOW={yellow_count}, RED={red_count}"
                },
                'large_indices': {
                    'value': large_indices_count,
                    'passed': large_indices_count == 0,
                    'check_item': 'index.size_gb',  # 与规则引擎中的 check_item 保持一致
                    'threshold': '=0',
                    'message': f"大索引数量 (>{index_config.get('size_gb', {}).get('critical', 100)}GB): {large_indices_count}"
                },
                'high_segments': {
                    'value': high_segments_count,
                    'passed': high_segments_count == 0,
                    'check_item': 'index.segments_count',  # 与规则引擎中的 check_item 保持一致
                    'threshold': '=0',
                    'message': f"高段数索引 (>{index_config.get('segments_count', {}).get('critical', 500)}): {high_segments_count}"
                },
                'high_shards_per_index': {
                    'value': high_shards_count,
                    'passed': high_shards_count == 0,
                    'check_item': 'index.shards_per_index',  # 与规则引擎中的 check_item 保持一致
                    'threshold': '=0',
                    'message': f"高分片数索引 (>{index_config.get('shards_per_index', {}).get('critical', 100)}): {high_shards_count}"
                },
                'large_docs_count': {
                    'value': large_docs_count,
                    'passed': large_docs_count == 0,
                    'check_item': 'index.docs_count',  # 与规则引擎中的 check_item 保持一致
                    'threshold': '=0',
                    'message': f"大文档数索引 (>{index_config.get('docs_count', {}).get('warning', 100000000)/1e8:.0f}亿): {large_docs_count}"
                },
                'high_deleted_docs_ratio': {
                    'value': high_deleted_docs_count,
                    'passed': high_deleted_docs_count == 0,
                    'check_item': 'index.deleted_docs_ratio',  # 与规则引擎中的 check_item 保持一致
                    'threshold': '=0',
                    'message': f"高删除文档比例索引 (>{index_config.get('deleted_docs_ratio', {}).get('critical', 0.2)*100:.0f}%): {high_deleted_docs_count}"
                }
            }
        
        # 5. 分片检查
        if shards:
            check_results['shards'] = {}
            
            # 检查分片大小（单物理分片 store，阈值与 oversized_single_shard 对齐）
            rules_config = self.rules_engine.config if self.rules_engine else {}
            single_shard_gb = oversized_single_shard_threshold_gb(rules_config)
            large_shard_count = count_physical_shards_over_size_gb(shards, single_shard_gb)
            threshold_label = (
                int(single_shard_gb)
                if single_shard_gb == int(single_shard_gb)
                else single_shard_gb
            )
            shard_size_note = "含主分片与副本，按物理分片条数统计"
            size_gb_message = (
                f"超大分片数量 (>{threshold_label}GB): {large_shard_count}"
                if large_shard_count
                else f"分片大小正常 (<={threshold_label}GB)"
            )
            check_results['shards']['size_gb'] = {
                'value': large_shard_count,
                'passed': large_shard_count == 0,
                'check_item': 'shard.size_gb',
                'threshold_gb': single_shard_gb,
                'threshold': f">{threshold_label}GB",
                'message': size_gb_message,
                'detail': shard_size_note if large_shard_count else '',
                'suggestion': (
                    f"{size_gb_message}（{shard_size_note}）"
                    if large_shard_count
                    else ''
                ),
            }
            
            # 检查分片文档数
            docs_config = self.rules_engine.config.get('shard', {}).get('docs_count', {})
            critical_threshold = docs_config.get('critical', 200000000)
            # 如果阈值小于 1000，说明配置的是亿为单位，需要转换为实际数值
            if critical_threshold < 1000:
                critical_threshold = int(critical_threshold * 1e8)
            large_docs_shards = [s for s in shards if int(s.get('docs') or 0) > critical_threshold]
            if large_docs_shards:
                check_results['shards']['docs_count'] = {
                    'value': len(large_docs_shards),
                    'passed': len(large_docs_shards) == 0,
                    'check_item': 'shard.docs_count',
                    'threshold': f">{critical_threshold/1e8:.0f}亿",
                    'message': f"大文档数分片 (>{critical_threshold/1e8:.0f}亿): {len(large_docs_shards)}"
                }
            else:
                # 即使没有大文档数分片，也显示正常信息
                check_results['shards']['docs_count'] = {
                    'value': 0,
                    'passed': True,
                    'check_item': 'shard.docs_count',
                    'threshold': f"<{critical_threshold/1e8:.0f}亿",
                    'message': f"分片文档数正常 (<{critical_threshold/1e8:.0f}亿)"
                }
            
            # 检查分片平衡
            balance_config = self.rules_engine.config.get('shard', {}).get('balance_std_dev', {})
            shards_per_node = count_shards_per_node(shards)

            if shards_per_node:
                import statistics
                shard_counts = list(shards_per_node.values())
                std_dev = statistics.stdev(shard_counts) if len(shard_counts) > 1 else 0
                
                if std_dev >= balance_config.get('critical', 30):
                    check_results['shards']['balance_std_dev'] = {
                        'value': round(std_dev, 1),
                        'passed': False,
                        'check_item': 'shard.balance_std_dev',
                        'threshold': f">{balance_config.get('critical', 30)}",
                        'message': f"分片分布标准差过大：{std_dev:.1f}"
                    }
                elif std_dev >= balance_config.get('warning', 15):
                    check_results['shards']['balance_std_dev'] = {
                        'value': round(std_dev, 1),
                        'passed': False,
                        'check_item': 'shard.balance_std_dev',
                        'threshold': f">{balance_config.get('warning', 15)}",
                        'message': f"分片分布不均：{std_dev:.1f}"
                    }
                else:
                    # 分片分布正常
                    check_results['shards']['balance_std_dev'] = {
                        'value': round(std_dev, 1),
                        'passed': True,
                        'check_item': 'shard.balance_std_dev',
                        'threshold': f"<{balance_config.get('warning', 15)}",
                        'message': f"分片分布均衡 (标准差：{std_dev:.1f})"
                    }
            
            # 检查节点分片数（value = 单节点最大分片数）
            import re

            max_node_shards, max_node_name = max_shards_on_single_node(shards)
            nodes = self.data.get('nodes', [])
            node_jvm_map = {}
            if nodes:
                nodes_list = list(nodes.values()) if isinstance(nodes, dict) else nodes
                for node in nodes_list:
                    node_name = node.get('name', '')
                    if not node_name:
                        continue
                    jvm_heap_max = node.get('jvm_heap_max', '')
                    if jvm_heap_max:
                        match = re.search(r'\d+', str(jvm_heap_max))
                        if match:
                            node_jvm_map[node_name] = int(match.group())

            node_config = self.rules_engine.config.get('node', {})
            if max_node_name in node_jvm_map:
                shards_threshold = node_jvm_map[max_node_name] * 20
            else:
                shards_threshold = node_config.get('shards_per_node', {}).get('warning', 500)

            high_shards_nodes = []
            node_thresholds = {}
            for node_name, shard_count in shards_per_node.items():
                if node_name in node_jvm_map:
                    threshold = node_jvm_map[node_name] * 20
                else:
                    threshold = shards_threshold
                node_thresholds[node_name] = threshold
                if shard_count > threshold:
                    high_shards_nodes.append(f"{node_name}: {shard_count} (> {threshold})")

            if node_thresholds:
                unique_thresholds = sorted(set(node_thresholds.values()))
                threshold_desc = (
                    str(unique_thresholds[0])
                    if len(unique_thresholds) == 1
                    else f"{min(unique_thresholds)}-{max(unique_thresholds)}"
                )
            else:
                threshold_desc = str(shards_threshold)

            passed_nodes = len(high_shards_nodes) == 0
            check_results['shards']['nodes_shards'] = {
                'value': max_node_shards,
                'passed': passed_nodes,
                'check_item': 'shard.nodes_shards',
                'threshold': f"<{shards_threshold}",
                'max_shards_node': max_node_name,
                'violating_node_count': len(high_shards_nodes),
                'message': (
                    f"节点分片数超过阈值：{'; '.join(high_shards_nodes)}"
                    if high_shards_nodes
                    else f"单节点最大分片数：{max_node_shards}（{max_node_name}），阈值 {shards_threshold}"
                ),
            }
        #         },
        #         'active_shards': {
        #             'value': sum(1 for s in shards if s.get('state') == 'STARTED'),
        #             'passed': True,
        #             'message': f"活跃分片：{sum(1 for s in shards if s.get('state') == 'STARTED')}"
        #         },
        #         'unassigned_shards': {
        #             'value': sum(1 for s in shards if s.get('state') == 'UNASSIGNED'),
        #             'passed': sum(1 for s in shards if s.get('state') == 'UNASSIGNED') == 0,
        #             'message': f"未分配分片：{sum(1 for s in shards if s.get('state') == 'UNASSIGNED')}"
        #         }
        #     }
        
        # 6. 恢复检查
        if isinstance(recovery, dict):
            recovering_shards_count = len(recovery.get('shards', []))
            avg_recovery_percent = recovery.get('average_recovery_percent', 100)
        else:
            recovering_shards_count = 0
            avg_recovery_percent = 100
        
        check_results['recovery'] = {
            'recovering_shards': {
                'value': recovering_shards_count,
                'passed': recovering_shards_count == 0,
                'threshold': '0',
                'message': f"正在恢复的分片：{recovering_shards_count}"
            },
            'average_recovery_percent': {
                'value': avg_recovery_percent,
                'passed': avg_recovery_percent == 100,
                'message': f"平均恢复进度：{avg_recovery_percent:.1f}%"
            }
        }
        
        # 7. 性能检查
        if cluster_stats:
            indices_stats = cluster_stats.get('indices', {})
            docs_count = indices_stats.get('count', 0)
            store_size = indices_stats.get('store', {}).get('size_in_bytes', 0)
            
            check_results['performance'] = {
                'total_docs': {
                    'value': docs_count,
                    'message': f"集群文档总数：{docs_count:,}"
                },
                'total_storage': {
                    'value': round(store_size / (1024**3), 2),
                    'message': f"集群总存储：{store_size / (1024**3):.2f} GB"
                }
            }
        
        # 8. ILM 管理检查
        ilm_data = self.data.get('ilm', {})
        if ilm_data:
            check_results['ilm'] = {
                'status': {
                    'value': ilm_data.get('ilm_status', 'unknown'),
                    'passed': ilm_data.get('ilm_status', '') == 'RUNNING',
                    'message': f"ILM 状态：{ilm_data.get('ilm_status', 'unknown')}"
                },
                # 已删除：failures_count - 配置名称不匹配 (failures vs failures_count)，规则引擎未使用
            }
        
        # 9. 快照备份检查
        snapshot_data = self.data.get('snapshot', {})
        if snapshot_data and snapshot_data.get('snapshots', []):
            # 从 snapshots 数组中获取最新快照
            snapshots = snapshot_data.get('snapshots', [])
            latest_snapshot = snapshots[-1] if snapshots else None
            latest_snapshot_name = latest_snapshot.get('snapshot', 'N/A') if latest_snapshot else 'N/A'
            latest_snapshot_state = latest_snapshot.get('state', 'N/A') if latest_snapshot else 'N/A'
            
            check_results['snapshot'] = {
                'latest_snapshot': {
                    'value': latest_snapshot_name,
                    'state': latest_snapshot_state,
                    'message': f"最新快照：{latest_snapshot_name} (状态：{latest_snapshot_state})"
                }
            }
        else:
            # 无快照数据
            check_results['snapshot'] = {
                'latest_snapshot': {
                    'value': '无快照数据',
                    'state': 'N/A',
                    'message': "未配置快照备份"
                }
            }
        
        # 已删除：repositories_count - 无阈值配置和校验逻辑，仅展示数字
        # 已删除：snapshot_count - 无阈值配置和校验逻辑，仅展示数字
        
        # 10. 安全配置检查
        security_data = self.data.get('security', {})
        if security_data:
            xpack_enabled = security_data.get('xpack_enabled', False)
            xpack_status = '已启用' if xpack_enabled else '未启用'
            
            check_results['security'] = {
                'xpack_enabled': {
                    'value': xpack_enabled,
                    'status': xpack_status,
                    'message': f"X-Pack 安全：{xpack_status}"
                }
            }
        
        # 已删除：users_count - 无阈值配置和校验逻辑，仅展示数字
        # 已删除：roles_count - 无阈值配置和校验逻辑，仅展示数字
        
        return check_results
    
    def generate_report(self, output_format: str = 'text') -> str:
        """
        生成报告
        
        Args:
            output_format: 输出格式 ('text', 'json', 'markdown')
        
        Returns:
            格式化的报告字符串
        """
        basic_info = self.parse_basic_info()
        alerts = self.parse_alerts()
        check_results = self._generate_check_results()  # 生成所有检查项结果
        
        # 生成健康评分详细报告（基于check_results）
        health_score_report = None
        try:
            # 使用基于严重级别的评分算法
            score_result = self._calculate_severity_based_score(check_results)
            score = score_result['total_score']
            
            # 从check_results中提取未通过的检查项作为问题
            issues = []
            
            for category, items in check_results.items():
                if isinstance(items, dict):
                    for check_name, check_data in items.items():
                        if isinstance(check_data, dict) and not check_data.get('passed', True):
                            # 根据检查项类别和名称确定严重级别
                            severity_level = self._get_severity_level(category, check_name, check_data)
                            severity = 'critical' if severity_level == 3 else ('warning' if severity_level == 2 else 'info')
                            
                            issues.append({
                                'dimension': category,
                                'metric': check_name,
                                'severity': severity,
                                'severity_level': severity_level,
                                'description': check_data.get('message', ''),
                                'value': check_data.get('value'),
                                'threshold': check_data.get('threshold', ''),
                                'suggestion': (
                                    check_data.get('suggestion')
                                    or check_data.get('detail')
                                    or check_data.get('message', '建议检查该项配置')
                                ),
                            })
            
            logger.info(f"从check_results提取问题: {len(issues)}个")
            
            # 统计问题数量
            critical_issues = sum(1 for issue in issues if issue['severity'] == 'critical')
            warning_issues = sum(1 for issue in issues if issue['severity'] == 'warning')
            level_1_count = sum(1 for issue in issues if issue.get('severity_level') == 1)
            level_2_count = sum(1 for issue in issues if issue.get('severity_level') == 2)
            level_3_count = sum(1 for issue in issues if issue.get('severity_level') == 3)
            
            # 构建详细的评分报告结构（包含严重级别得分）
            health_score_report = {
                'total_score': round(score, 2),
                'health_level': score_result['health_level'],
                'generated_at': datetime.now().isoformat(),
                'severity_level_scores': score_result['severity_level_scores'],  # 严重级别得分详情
                'indicator_details': score_result.get('indicator_details', {}),  # 指标详情
                'issues': issues,
                'recommendations': [],
                'summary': {
                    'score': round(score, 2),
                    'level': score_result['health_level'],
                    'critical_issues_count': critical_issues,
                    'warning_issues_count': warning_issues,
                    'total_issues_count': len(issues),
                    'level_1_count': level_1_count,
                    'level_2_count': level_2_count,
                    'level_3_count': level_3_count,
                    'recommendations_count': 0,
                    'scoring_method': 'severity_based'  # 标记评分方法为基于严重级别
                }
            }
            logger.info(f"基于严重级别评分报告生成完成: {score:.2f}分，等级={score_result['health_level']}，发现{len(issues)}个问题")
        except Exception as e:
            logger.warning(f"生成加权维度评分报告失败: {e}，回退到旧算法")
            import traceback
            logger.debug(traceback.format_exc())
            
            # 回退到旧算法
            try:
                score = self._calculate_score_from_check_results(check_results)
                
                # 从check_results中提取未通过的检查项作为问题
                issues = []
                
                for category, items in check_results.items():
                    if isinstance(items, dict):
                        for check_name, check_data in items.items():
                            if isinstance(check_data, dict) and not check_data.get('passed', True):
                                # 根据检查项类别和名称确定严重级别
                                severity_level = self._get_severity_level(category, check_name, check_data)
                                severity = 'critical' if severity_level == 3 else ('warning' if severity_level == 2 else 'info')
                                
                                issues.append({
                                    'dimension': category,
                                    'metric': check_name,
                                    'severity': severity,
                                    'severity_level': severity_level,
                                    'description': check_data.get('message', ''),
                                    'value': check_data.get('value'),
                                    'threshold': check_data.get('threshold', ''),
                                    'suggestion': (
                                        check_data.get('suggestion')
                                        or check_data.get('detail')
                                        or check_data.get('message', '建议检查该项配置')
                                    ),
                                })
                
                critical_issues = sum(1 for issue in issues if issue['severity'] == 'critical')
                warning_issues = sum(1 for issue in issues if issue['severity'] == 'warning')
                level_1_count = sum(1 for issue in issues if issue.get('severity_level') == 1)
                level_2_count = sum(1 for issue in issues if issue.get('severity_level') == 2)
                level_3_count = sum(1 for issue in issues if issue.get('severity_level') == 3)
                
                health_score_report = {
                    'total_score': round(score),
                    'health_level': self._get_health_level(score),
                    'generated_at': datetime.now().isoformat(),
                    'dimensions': {},
                    'issues': issues,
                    'recommendations': [],
                    'summary': {
                        'score': round(score),
                        'level': self._get_health_level(score),
                        'critical_issues_count': critical_issues,
                        'warning_issues_count': warning_issues,
                        'total_issues_count': len(issues),
                        'level_1_count': level_1_count,
                        'level_2_count': level_2_count,
                        'level_3_count': level_3_count,
                        'recommendations_count': 0,
                        'scoring_method': 'category_average'  # 标记为旧算法
                    }
                }
                logger.info(f"旧算法评分报告生成完成: {score}分，发现{len(issues)}个问题")
            except Exception as e2:
                logger.error(f"旧算法也失败: {e2}")
        
        # 提取分片汇总信息（如果有 diagnostic_path）
        shard_summaries = []
        shard_distribution = {}
        large_shards = []
        small_shards_with_multiple_primaries = {}
        if self.data and 'metadata' in self.data:
            try:
                from es_insight.diagnostic_extractor import DiagnosticDataExtractor
                source = self.data['metadata'].get('source', '')
                if source:
                    extractor = DiagnosticDataExtractor(source)
                    shard_summaries = extractor.extract_shard_summaries()
                    shard_distribution = extractor.extract_shard_distribution()
                    threshold_gb = oversized_primary_shard_threshold_gb(
                        self.rules_engine.config if self.rules_engine else {}
                    )
                    large_shards = extractor.extract_large_shards(
                        threshold_gb=threshold_gb
                    )
                    small_shards_with_multiple_primaries = extractor.extract_small_shards_with_multiple_primaries()
            except Exception as e:
                logger.warning(f"提取分片汇总信息失败：{e}")
        
        if output_format == 'json':
            report_data = {
                'basic_info': basic_info,
                'check_results': check_results,  # 新增：所有检查项详情
                'alerts': alerts
            }
            # 添加健康评分详细报告
            if health_score_report:
                report_data['health_score_report'] = health_score_report
            # 添加分片汇总信息
            if shard_summaries:
                report_data['shard_summaries'] = shard_summaries
            if shard_distribution:
                report_data['shard_distribution'] = shard_distribution
            if large_shards:
                report_data['large_shards'] = large_shards
            if small_shards_with_multiple_primaries:
                report_data['small_shards_with_multiple_primaries'] = small_shards_with_multiple_primaries
            return json.dumps(report_data, ensure_ascii=False, indent=2)
        
        elif output_format == 'markdown':
            return self._generate_markdown_report(basic_info, alerts)
        
        else:  # text
            return self._generate_text_report(basic_info, alerts)
    
    def _generate_text_report(self, basic_info: dict, alerts: dict) -> str:
        """生成文本报告"""
        lines = []
        
        lines.append("="*100)
        lines.append("ES 集群巡检检查结果报告")
        lines.append("="*100)
        lines.append("")
        
        # 基本信息 - 详细版
        lines.append("-"*100)
        lines.append("【基本信息】")
        lines.append("-"*100)
        
        # 1. 集群信息
        cluster = basic_info.get('cluster_info', {})
        lines.append("\n📊 集群信息:")
        lines.append(f"  集群名称：{cluster.get('cluster_name', 'N/A')}")
        lines.append(f"  状态：{cluster.get('status', 'N/A')}")
        lines.append(f"  ES 版本：{cluster.get('es_version', 'N/A')}")
        lines.append(f"  节点总数：{cluster.get('nodes_total', 0)}")
        lines.append(f"  数据节点数：{cluster.get('data_nodes', 0)}")
        lines.append(f"  主节点数：{cluster.get('master_nodes', 1)}")
        
        # 2. 健康摘要
        health = basic_info.get('health_summary', {})
        lines.append("\n💚 健康摘要:")
        lines.append(f"  活跃分片总数：{health.get('active_shards', 0)}")
        lines.append(f"  活跃主分片数：{health.get('active_primary_shards', 0)}")
        lines.append(f"  未分配分片数：{health.get('unassigned_shards', 0)}")
        lines.append(f"  初始化中分片：{health.get('initializing_shards', 0)}")
        lines.append(f"  迁移中分片：{health.get('relocating_shards', 0)}")
        lines.append(f"  延迟未分配：{health.get('delayed_unassigned_shards', 0)}")
        lines.append(f"  活跃分片比例：{health.get('active_shards_percent', health.get('active_shards_percent_as_number', 0))}%")
        
        # 3. 节点统计
        nodes = basic_info.get('node_summary', {})
        lines.append("\n🖥️ 节点统计:")
        lines.append(f"  节点总数：{nodes.get('total', 0)}")
        lines.append(f"  平均磁盘使用率：{nodes.get('avg_disk_usage', 0)}%")
        lines.append(f"  平均 JVM 堆使用率：{nodes.get('avg_heap_usage', 0)}%")
        lines.append(f"  平均 CPU 使用率：{nodes.get('avg_cpu_usage', 0)}%")
        if nodes.get('max_disk_node'):
            lines.append(f"  磁盘使用最高节点：{nodes.get('max_disk_node', 'N/A')}")
        if nodes.get('max_heap_node'):
            lines.append(f"  内存使用最高节点：{nodes.get('max_heap_node', 'N/A')}")
        
        # 4. 索引统计
        indices = basic_info.get('index_summary', {})
        lines.append("\n📁 索引统计:")
        lines.append(f"  索引总数：{indices.get('total', 0)}")
        lines.append(f"  总文档数：{indices.get('total_docs', 0):,}")
        lines.append(f"  总存储大小：{indices.get('total_size_gb', 0)} GB")
        health_dist = indices.get('health_distribution', {})
        lines.append(f"  健康状态分布:")
        for health_status, count in health_dist.items():
            lines.append(f"    - {health_status.upper()}: {count} 个索引")
        
        top_indices = indices.get('top_5_indices', [])
        if top_indices:
            lines.append("  Top 5 大索引:")
            for i, idx in enumerate(top_indices, 1):
                lines.append(f"    {i}. {idx.get('name', 'N/A')} - {idx.get('size_gb', 0)} GB ({idx.get('docs', 0):,} 文档)")
        
        # 5. 检查元数据
        metadata = basic_info.get('check_metadata', {})
        lines.append("\n⏰ 检查信息:")
        lines.append(f"  数据来源：{metadata.get('source', 'N/A')}")
        lines.append(f"  提取时间：{metadata.get('extracted_at', 'N/A')}")
        lines.append(f"  检查时间：{metadata.get('checked_at', 'N/A')}")
        lines.append(f"  检查耗时：{metadata.get('check_duration_sec', 0)}秒")
        
        # 6. 巡检项详细检查结果
        lines.append("\n📋 巡检项详细检查结果:")
        lines.append("-"*80)
        
        # 集群健康检查项
        cluster_health = self.data.get('cluster_health', {})
        lines.append("\n【集群健康检查】")
        
        # 1. 集群状态
        status = cluster_health.get('status', 'unknown').upper()
        status_emoji = "✅" if status == 'GREEN' else ("⚠️" if status == 'YELLOW' else "❌")
        lines.append(f"  {status_emoji} 集群状态：{status}")
        
        # 2. 活跃分片比例
        active_percent = cluster_health.get('active_shards_percent', cluster_health.get('active_shards_percent_as_number', 0))
        percent_emoji = "✅" if active_percent >= 95 else ("⚠️" if active_percent >= 90 else "❌")
        lines.append(f"  {percent_emoji} 活跃分片比例：{active_percent}% (阈值：>=95% ✅, <90% ❌)")
        
        # 3. 未分配分片
        unassigned = cluster_health.get('unassigned_shards', 0)
        unassigned_emoji = "✅" if unassigned == 0 else "⚠️"
        lines.append(f"  {unassigned_emoji} 未分配分片：{unassigned} (阈值：0)")
        
        # 4. 初始化中分片
        initializing = cluster_health.get('initializing_shards', 0)
        init_emoji = "✅" if initializing < 10 else "⚠️"
        lines.append(f"  {init_emoji} 初始化中分片：{initializing} (阈值：<10)")
        
        # 5. 迁移中分片
        relocating = cluster_health.get('relocating_shards', 0)
        relocate_emoji = "✅" if relocating < 10 else "⚠️"
        lines.append(f"  {relocate_emoji} 迁移中分片：{relocating} (阈值：<10)")
        
        # 节点资源检查项
        nodes = self.data.get('nodes', [])
        lines.append("\n【节点资源检查】")
        
        if nodes:
            avg_disk = sum(node.get('disk_used_percent', 0) for node in nodes) / len(nodes)
            avg_heap = sum(node.get('heap_used_percent', 0) for node in nodes) / len(nodes)
            avg_cpu = sum(node.get('cpu_percent', 0) for node in nodes) / len(nodes)
            max_disk = max(node.get('disk_used_percent', 0) for node in nodes)
            max_heap = max(node.get('heap_used_percent', 0) for node in nodes)
            
            disk_emoji = "✅" if avg_disk < 70 else ("⚠️" if avg_disk < 80 else "❌")
            heap_emoji = "✅" if avg_heap < 75 else ("⚠️" if avg_heap < 85 else "❌")
            cpu_emoji = "✅" if avg_cpu < 60 else ("⚠️" if avg_cpu < 75 else "❌")
            
            lines.append(f"  {disk_emoji} 平均磁盘使用率：{avg_disk:.1f}% (最高：{max_disk:.1f}%, 阈值：<70%)")
            lines.append(f"  {heap_emoji} 平均 JVM 堆使用率：{avg_heap:.1f}% (最高：{max_heap:.1f}%, 阈值：<75%)")
            lines.append(f"  {cpu_emoji} 平均 CPU 使用率：{avg_cpu:.1f}% (阈值：<60%)")
        
        # 索引健康检查项
        indices = self.data.get('indices', [])
        lines.append("\n【索引健康检查】")
        
        if indices:
            green_count = sum(1 for idx in indices if idx.get('health') == 'green')
            yellow_count = sum(1 for idx in indices if idx.get('health') == 'yellow')
            red_count = sum(1 for idx in indices if idx.get('health') == 'red')
            total = len(indices)
            
            health_emoji = "✅" if red_count == 0 and yellow_count == 0 else ("⚠️" if red_count == 0 else "❌")
            lines.append(f"  {health_emoji} 索引健康分布：GREEN={green_count}, YELLOW={yellow_count}, RED={red_count}")
            
            # 大索引检查（使用配置文件中的阈值 50GB）
            large_indices = [idx for idx in indices if idx.get('store_size_bytes', 0) > 50 * (1024**3)]
            large_emoji = "✅" if len(large_indices) == 0 else "⚠️"
            lines.append(f"  {large_emoji} 大索引数量 (>50GB): {len(large_indices)} (阈值：>50GB)")
            
            # 段数量检查
            high_segments = [idx for idx in indices if idx.get('segments_count', 0) > 500]
            segments_emoji = "✅" if len(high_segments) == 0 else "⚠️"
            lines.append(f"  {segments_emoji} 高段数索引 (>500): {len(high_segments)} (阈值：>500)")
        
        # 线程池检查项
        lines.append("\n【线程池检查】")
        if nodes:
            # 统计线程池拒绝情况
            search_rejected = sum(node.get('thread_pool', {}).get('search', {}).get('rejected', 0) for node in nodes)
            write_rejected = sum(node.get('thread_pool', {}).get('write', {}).get('rejected', 0) for node in nodes)
            bulk_rejected = sum(node.get('thread_pool', {}).get('bulk', {}).get('rejected', 0) for node in nodes)
            get_rejected = sum(node.get('thread_pool', {}).get('get', {}).get('rejected', 0) for node in nodes)
            
            search_emoji = "✅" if search_rejected == 0 else "❌"
            write_emoji = "✅" if write_rejected == 0 else "❌"
            bulk_emoji = "✅" if bulk_rejected == 0 else "❌"
            get_emoji = "✅" if get_rejected == 0 else "❌"
            
            lines.append(f"  {search_emoji} Search 线程池拒绝：{search_rejected} (阈值：0)")
            lines.append(f"  {write_emoji} Write 线程池拒绝：{write_rejected} (阈值：0)")
            lines.append(f"  {bulk_emoji} Bulk 线程池拒绝：{bulk_rejected} (阈值：0)")
            lines.append(f"  {get_emoji} Get 线程池拒绝：{get_rejected} (阈值：0)")
        else:
            lines.append("  ℹ️  无节点数据，跳过线程池检查")
        
        # 分片检查项
        shards = self.data.get('shards', [])
        lines.append("\n【分片检查】")
        if shards:
            total_shards = len(shards)
            active_shards = sum(1 for s in shards if s.get('state') == 'STARTED')
            relocating_shards = sum(1 for s in shards if s.get('relocating_node') is not None)
            initializing_shards = sum(1 for s in shards if s.get('primary') and s.get('state') == 'INITIALIZING')
            
            shard_health_emoji = "✅" if active_shards == total_shards else "⚠️"
            lines.append(f"  {shard_health_emoji} 分片总数：{total_shards}")
            lines.append(f"  ✅ 活跃分片：{active_shards}")
            lines.append(f"  {'✅' if relocating_shards == 0 else '⚠️'} 迁移中分片：{relocating_shards}")
            lines.append(f"  {'✅' if initializing_shards == 0 else '⚠️'} 初始化中分片：{initializing_shards}")
        else:
            lines.append("  ℹ️  无分片数据，跳过分片检查")
        
        # 恢复检查项
        recovery_data = self.data.get('recovery', {})
        lines.append("\n【恢复检查】")
        
        # recovery 是字典格式：{index_name: {shards: [...]}}
        if isinstance(recovery_data, dict) and recovery_data:
            # 提取所有分片
            all_shards = []
            for index_name, index_recovery in recovery_data.items():
                if isinstance(index_recovery, dict):
                    shards = index_recovery.get('shards', [])
                    all_shards.extend(shards)
            
            recovering_shards = len([s for s in all_shards if isinstance(s, dict) and s.get('stage') != 'DONE'])
            avg_percent = sum(s.get('recover_percent', 100) for s in all_shards if isinstance(s, dict)) / max(len(all_shards), 1)
            
            recovery_emoji = "✅" if recovering_shards == 0 else "⚠️"
            lines.append(f"  {recovery_emoji} 正在恢复的分片：{recovering_shards} (阈值：0)")
            lines.append(f"  ✅ 平均恢复进度：{avg_percent:.1f}%")
        else:
            lines.append("  ℹ️  无恢复任务")
        
        # 性能检查项（如果有实时数据）
        lines.append("\n【性能检查】")
        cluster_stats = self.data.get('cluster_stats', {})
        if cluster_stats:
            indices_stats = cluster_stats.get('indices', {})
            docs_count = indices_stats.get('count', 0)
            store_size = indices_stats.get('store', {}).get('size_in_bytes', 0)
            
            lines.append(f"  ℹ️  集群文档总数：{docs_count:,}")
            lines.append(f"  ℹ️  集群总存储：{store_size / (1024**3):.2f} GB")
            lines.append("  ⚪ 查询/写入延迟：需要实时监控数据")
        else:
            lines.append("  ℹ️  无性能统计数据")
        
        # ILM 策略检查
        ilm_policies = self.data.get('commercial', {}).get('ilm_policies', []) if isinstance(self.data.get('commercial'), dict) else []
        lines.append("\n【ILM 策略检查】")
        if ilm_policies:
            lines.append(f"  ℹ️  ILM 策略数量：{len(ilm_policies)}")
            lines.append("  ✅ ILM 状态：正常运行")
        else:
            lines.append("  ℹ️  未使用 ILM 策略")
        
        # 快照检查
        snapshot_data = self.data.get('snapshot', {})
        snapshots = snapshot_data.get('snapshots', []) if snapshot_data else []
        lines.append("\n【快照检查】")
        if snapshots:
            latest_snapshot = snapshots[-1] if snapshots else {}
            status = latest_snapshot.get('state', 'UNKNOWN')
            snapshot_emoji = "✅" if status == 'SUCCESS' else ("⚠️" if status == 'IN_PROGRESS' else "❌")
            snapshot_name = latest_snapshot.get('snapshot', 'N/A')
            lines.append(f"  {snapshot_emoji} 最新快照：{snapshot_name} (状态：{status})")
        else:
            lines.append("  ℹ️  未配置快照备份")
        
        # 安全检查
        security_data = self.data.get('security', {})
        xpack_enabled = security_data.get('xpack_enabled', False) if security_data else False
        users_count = len(security_data.get('users', [])) if security_data else 0
        
        lines.append("\n【安全检查】")
        if security_data:
            xpack_status = '已启用' if xpack_enabled else '未启用'
            lines.append(f"  ✅ X-Pack 安全功能：{xpack_status}")
            lines.append(f"  ℹ️  用户数量：{users_count}")
        else:
            lines.append("  ℹ️  未检测到 X-Pack 安全信息")
        
        # 模板和映射检查
        templates = self.data.get('index_templates', [])
        component_templates = self.data.get('component_templates', [])
        lines.append("\n【模板与映射检查】")
        lines.append(f"  ℹ️  索引模板数量：{len(templates)}")
        lines.append(f"  ℹ️  组件模板数量：{len(component_templates)}")
        if indices:
            avg_fields = sum(idx.get('fields_count', 50) for idx in indices) / len(indices)
            lines.append(f"  ℹ️  平均字段数：{avg_fields:.1f} (阈值：<100)")
        
        # 日志和错误检查（从节点数据推断）
        lines.append("\n【日志与错误检查】")
        
        # 优先使用 JVM GC 数据
        jvm_gc = self.data.get('jvm_gc', [])
        if jvm_gc:
            total_gc_count = sum(gc.get('gc_total_collection_count', 0) for gc in jvm_gc)
            total_gc_time_ms = sum(gc.get('gc_total_collection_time_in_millis', 0) for gc in jvm_gc)
            lines.append(f"  ℹ️  总 GC 次数：{total_gc_count:,}")
            lines.append(f"  ℹ️  总 GC 时间：{total_gc_time_ms / 1000:.1f} 秒")
            lines.append(f"  ⚪ GC 频率：需要实时监控数据")
        elif nodes:
            # 备用：从节点数据中读取（旧方式）
            total_gc_time = sum(node.get('jvm', {}).get('gc', {}).get('total_collection_time_in_millis', 0) for node in nodes)
            total_gc_count = sum(node.get('jvm', {}).get('gc', {}).get('total_collection_count', 0) for node in nodes)
            lines.append(f"  ℹ️  总 GC 次数：{total_gc_count:,}")
            lines.append(f"  ℹ️  总 GC 时间：{total_gc_time / 1000:.1f} 秒")
            lines.append(f"  ⚪ GC 频率：需要实时监控数据")
        else:
            lines.append("  ℹ️  无节点 GC 数据")
        
        lines.append("")
        
        # 告警信息 - 详细版
        lines.append("-"*100)
        lines.append("【告警信息】")
        lines.append("-"*100)
        
        alert_summary = alerts.get('summary', {})
        lines.append(f"\n🎯 健康评分：{alert_summary.get('health_score', 0)}/100")
        lines.append(f"📊 告警统计:")
        lines.append(f"  总告警数：{alert_summary.get('total', 0)}")
        lines.append(f"  🔴 严重告警：{alert_summary.get('critical', 0)}")
        lines.append(f"  🟡 警告告警：{alert_summary.get('warning', 0)}")
        lines.append(f"  ℹ️  提示信息：{alert_summary.get('info', 0)}")
        
        # 如果没有告警，显示正常提示和已执行的检查项列表
        if alert_summary.get('total', 0) == 0:
            lines.append("\n✅ 集群运行正常，未检测到任何异常！")
            lines.append("\n📋 已执行的检查项:")
            lines.append("  - cluster.status: 集群状态检查 ✅")
            lines.append("  - cluster.unassigned_shards: 未分配分片检查 ✅")
            lines.append("  - cluster.active_shards_percent: 活跃分片比例检查 ✅")
            lines.append("  - index.health: 索引健康状态检查 ✅")
            lines.append("  - index.size_gb: 索引大小检查 ✅")
            lines.append("  - index.segments_count: 段数量检查 ✅")
        
        # 严重告警详情
        critical_alerts = alerts.get('critical_alerts', [])
        if critical_alerts:
            lines.append("\n" + "="*80)
            lines.append("🔴 严重告警详情 (Critical)")
            lines.append("="*80)
            for i, alert in enumerate(critical_alerts, 1):
                lines.append(f"\n【严重告警 #{i}]")
                lines.append(f"  类别：{alert.get('category', 'N/A')}")
                lines.append(f"  检查项：{alert.get('check_item', 'N/A')}")
                lines.append(f"  消息：{alert.get('message', 'N/A')}")
                lines.append(f"  当前值：{alert.get('current_value', 'N/A')}")
                lines.append(f"  阈值：{alert.get('threshold', 'N/A')}")
                lines.append(f"  严重程度：{alert.get('severity', 'N/A')}")
                if alert.get('recommendation'):
                    lines.append(f"  💡 建议：{alert.get('recommendation', 'N/A')}")
                if alert.get('location'):
                    lines.append(f"  📍 位置：{alert.get('location', 'N/A')}")
        
        # 警告告警详情
        warning_alerts = alerts.get('warning_alerts', [])
        if warning_alerts:
            lines.append("\n" + "="*80)
            lines.append("🟡 警告告警详情 (Warning)")
            lines.append("="*80)
            for i, alert in enumerate(warning_alerts, 1):
                lines.append(f"\n【警告告警 #{i}]")
                lines.append(f"  类别：{alert.get('category', 'N/A')}")
                lines.append(f"  检查项：{alert.get('check_item', 'N/A')}")
                lines.append(f"  消息：{alert.get('message', 'N/A')}")
                lines.append(f"  当前值：{alert.get('current_value', 'N/A')}")
                lines.append(f"  阈值：{alert.get('threshold', 'N/A')}")
                lines.append(f"  严重程度：{alert.get('severity', 'N/A')}")
                if alert.get('recommendation'):
                    lines.append(f"  💡 建议：{alert.get('recommendation', 'N/A')}")
        
        # 提示信息详情
        info_alerts = alerts.get('info_alerts', [])
        if info_alerts:
            lines.append("\n" + "="*80)
            lines.append("ℹ️  提示信息详情 (Info)")
            lines.append("="*80)
            for i, alert in enumerate(info_alerts, 1):
                lines.append(f"\n【提示 #{i}]")
                lines.append(f"  类别：{alert.get('category', 'N/A')}")
                lines.append(f"  检查项：{alert.get('check_item', 'N/A')}")
                lines.append(f"  消息：{alert.get('message', 'N/A')}")
                lines.append(f"  当前值：{alert.get('current_value', 'N/A')}")
                if alert.get('recommendation'):
                    lines.append(f"  💡 建议：{alert.get('recommendation', 'N/A')}")
        
        # 按类别分组统计
        by_category = alerts.get('by_category', {})
        if by_category:
            lines.append("\n" + "-"*80)
            lines.append("📊 按类别统计")
            lines.append("-"*80)
            for category, category_alerts in sorted(by_category.items()):
                critical_count = sum(1 for a in category_alerts if self._is_critical(a))
                warning_count = sum(1 for a in category_alerts if self._is_warning(a))
                info_count = sum(1 for a in category_alerts if self._is_info(a))
                lines.append(f"  {category}:")
                lines.append(f"    总计：{len(category_alerts)} 个告警")
                lines.append(f"    - 🔴 严重：{critical_count}")
                lines.append(f"    - 🟡 警告：{warning_count}")
                lines.append(f"    - ℹ️  提示：{info_count}")
        
        lines.append("")
        lines.append("="*100)
        lines.append("报告结束")
        lines.append("="*100)
        
        return '\n'.join(lines)
    
    def _generate_markdown_report(self, basic_info: dict, alerts: dict) -> str:
        """生成 Markdown 报告"""
        lines = []
        
        lines.append("# ES 集群巡检检查结果报告\n")
        
        # 基本信息
        lines.append("## 📊 基本信息\n")
        
        cluster = basic_info.get('cluster_info', {})
        lines.append(f"**集群名称**: {cluster.get('cluster_name', 'N/A')}\n")
        lines.append(f"**状态**: {cluster.get('status', 'N/A')}\n")
        lines.append(f"**版本**: {cluster.get('es_version', 'N/A')}\n")
        lines.append(f"**节点**: {cluster.get('nodes_total', 0)} (数据节点：{cluster.get('data_nodes', 0)})\n\n")
        
        # 告警摘要
        lines.append("## 🚨 告警摘要\n")
        alert_summary = alerts.get('summary', {})
        lines.append(f"**健康评分**: {alert_summary.get('health_score', 0)}/100\n")
        lines.append(f"**总告警数**: {alert_summary.get('total', 0)}\n")
        lines.append(f"- 🔴 严重：{alert_summary.get('critical', 0)}")
        lines.append(f"- 🟡 警告：{alert_summary.get('warning', 0)}")
        lines.append(f"- ℹ️  提示：{alert_summary.get('info', 0)}\n\n")
        
        # 详细告警
        lines.append("## ⚠️ 详细告警\n")
        
        critical_alerts = alerts.get('critical_alerts', [])
        if critical_alerts:
            lines.append("### 🔴 严重告警\n")
            for alert in critical_alerts:
                lines.append(f"- **{alert.get('category', 'N/A')}**: {alert.get('message', 'N/A')}")
                lines.append(f"  - 检查项：{alert.get('check_item', 'N/A')}")
                lines.append(f"  - 当前值：{alert.get('current_value', 'N/A')}")
                lines.append(f"  - 建议：{alert.get('recommendation', 'N/A')}\n")
        
        return '\n'.join(lines)
    
    def save_report(self, output_format: str = 'text'):
        """保存报告到文件"""
        report = self.generate_report(output_format)
        
        ext_map = {'text': 'txt', 'json': 'json', 'markdown': 'md'}
        ext = ext_map.get(output_format, 'txt')
        
        output_path = self.output_dir / f"check_result_report_{self.timestamp}.{ext}"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"✓ 报告已保存：{output_path}")
        return output_path
    
    def print_summary(self):
        """打印摘要到控制台"""
        basic_info = self.parse_basic_info()
        alerts = self.parse_alerts()
        
        print("\n" + "="*60)
        print("检查结果摘要")
        print("="*60)
        
        # 基本信息
        cluster = basic_info.get('cluster_info', {})
        print(f"\n集群：{cluster.get('cluster_name', 'N/A')}")
        print(f"状态：{cluster.get('status', 'N/A')}")
        print(f"节点：{cluster.get('nodes_total', 0)} | 索引：{basic_info.get('index_summary', {}).get('total', 0)}")
        
        # 告警摘要
        alert_summary = alerts.get('summary', {})
        print(f"\n健康评分：{alert_summary.get('health_score', 0)}/100")
        print(f"告警：{alert_summary.get('total', 0)} = 🔴{alert_summary.get('critical', 0)} + 🟡{alert_summary.get('warning', 0)} + ℹ️{alert_summary.get('info', 0)}")
        
        # 显示前 3 个严重告警
        critical = alerts.get('critical_alerts', [])[:3]
        if critical:
            print("\n严重告警:")
            for alert in critical:
                print(f"  🔴 {alert.get('message', 'N/A')}")
        
        print("="*60 + "\n")


def main():
    """主函数"""
    import sys
    from pathlib import Path
    
    # 配置日志
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # 查找最新的检查结果文件
    out_dir = Path("out")
    if not out_dir.exists():
        logger.error("输出目录不存在")
        sys.exit(1)
    
    # 查找诊断数据文件
    result_files = sorted(out_dir.glob("diagnostic_data_*.json"))
    if not result_files:
        logger.error("未找到检查结果文件")
        logger.info("请先运行：python -m es_insight.diagnostic_extractor")
        sys.exit(1)
    
    latest_file = result_files[-1]
    logger.info(f"使用文件：{latest_file.name}")
    
    # 创建解析器
    parser = CheckResultParser(str(latest_file))
    
    # 打印摘要
    parser.print_summary()
    
    # 保存报告
    txt_path = parser.save_report('text')
    json_path = parser.save_report('json')
    
    logger.info(f"✓ 处理完成!")
    logger.info(f"  文本报告：{txt_path}")
    logger.info(f"  JSON 报告：{json_path}")


if __name__ == '__main__':
    main()
