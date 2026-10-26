"""
巡检检查项规则引擎
基于配置文件中的阈值进行自动检查和告警生成
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from loguru import logger


class RulesEngine:
    """规则引擎 - 从配置文件加载阈值并执行检查"""
    
    def __init__(self, config_path: str = None):
        """
        初始化规则引擎
        
        Args:
            config_path: 配置文件路径，默认使用 configs/checkpoints_thresholds_complete.yaml
        """
        if config_path is None:
            # 默认配置文件路径
            default_paths = [
                Path("configs/checkpoints_thresholds_complete.yaml"),
                Path(__file__).parent.parent / "configs" / "checkpoints_thresholds_complete.yaml"
            ]
            
            for path in default_paths:
                if path.exists():
                    config_path = str(path)
                    break
        
        if not config_path or not Path(config_path).exists():
            raise FileNotFoundError(f"配置文件不存在：{config_path}")
        
        self.config_path = config_path
        self.config = self._load_config()
        logger.info(f"✓ 规则引擎初始化完成，加载配置：{self.config_path}")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载 YAML 配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.debug(f"成功加载配置文件：{len(config)} 个顶级配置项")
            return config
        except Exception as e:
            logger.error(f"加载配置文件失败：{e}")
            raise
    
    def check_cluster_health(self, cluster_health: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        检查集群健康状态
        
        Args:
            cluster_health: 集群健康数据
            
        Returns:
            告警列表
        """
        alerts = []
        cluster_config = self.config.get('cluster', {})
        
        # 1. 检查集群状态
        status = cluster_health.get('status', 'unknown').upper()
        status_config = cluster_config.get('status', {})
        
        # 根据配置处理不同状态
        if status == 'RED':
            config_val = status_config.get('red', 'critical')
            severity_level = 3
            if isinstance(config_val, dict):
                severity = config_val.get('severity', 'critical')
                severity_level = config_val.get('severity_level', 3)
            else:
                severity = config_val
            alerts.append({
                'category': 'cluster_health',
                'check_item': 'cluster.status',
                'message': '集群状态为 RED，主分片未分配，数据不可用',
                'current_value': status,
                'threshold': 'GREEN',
                'severity': severity,
                'severity_level': severity_level,
                'recommendation': '立即检查节点可用性和分片分配情况'
            })
        elif status == 'YELLOW':
            config_val = status_config.get('yellow', 'warning')
            severity_level = 2
            if isinstance(config_val, dict):
                severity = config_val.get('severity', 'warning')
                severity_level = config_val.get('severity_level', 2)
            else:
                severity = config_val
            alerts.append({
                'category': 'cluster_health',
                'check_item': 'cluster.status',
                'message': '集群状态为 YELLOW，副本分片未分配',
                'current_value': status,
                'threshold': 'GREEN',
                'severity': severity,
                'severity_level': severity_level,
                'recommendation': '检查副本分片分配策略和节点资源'
            })
        elif status == 'GREEN':
            # 根据配置，GREEN 状态也显示为 warning 告警（提示信息）
            severity = status_config.get('green', 'info')
            if severity != 'none':  # 只有配置不为 'none' 时才显示
                alerts.append({
                    'category': 'cluster_health',
                    'check_item': 'cluster.status',
                    'message': '集群状态为 GREEN，运行正常',
                    'current_value': status,
                    'threshold': 'GREEN',
                    'severity': severity,
                    'recommendation': '集群运行正常，继续保持良好运维习惯'
                })
        
        # 2. 检查活跃分片比例
        active_percent = cluster_health.get('active_shards_percent', cluster_health.get('active_shards_percent_as_number', 0))
        percent_config = cluster_config.get('active_shards_percent', {})
        
        critical_threshold = percent_config.get('critical', 90)
        warning_threshold = percent_config.get('warning', 95)
        
        if active_percent < critical_threshold:
            alerts.append({
                'category': 'cluster_health',
                'check_item': 'cluster.active_shards_percent',
                'message': f'活跃分片比例为 {active_percent}%，低于 {critical_threshold}%',
                'current_value': active_percent,
                'threshold': critical_threshold,
                'severity': 'critical',
                'severity_level': percent_config.get('severity_level', 3),
                'recommendation': '检查节点连接性和分片恢复进度'
            })
        elif active_percent < warning_threshold:
            alerts.append({
                'category': 'cluster_health',
                'check_item': 'cluster.active_shards_percent',
                'message': f'活跃分片比例为 {active_percent}%，低于 {warning_threshold}%',
                'current_value': active_percent,
                'threshold': warning_threshold,
                'severity': 'warning',
                'severity_level': percent_config.get('severity_level', 2),
                'recommendation': '关注分片恢复进度'
            })
        
        # 3. 检查未分配分片
        unassigned = cluster_health.get('unassigned_shards', 0)
        unassigned_config = cluster_config.get('unassigned_shards', {})
        
        critical_threshold = unassigned_config.get('critical', 10)
        warning_threshold = unassigned_config.get('warning', 1)
        
        if unassigned >= critical_threshold:
            alerts.append({
                'category': 'shard_allocation',
                'check_item': 'cluster.unassigned_shards',
                'message': f'存在 {unassigned} 个未分配分片（严重）',
                'current_value': unassigned,
                'threshold': warning_threshold,
                'severity': 'critical',
                'severity_level': unassigned_config.get('severity_level', 3),
                'recommendation': '使用 _cluster/allocation/explain API 分析未分配原因'
            })
        elif unassigned > warning_threshold:  # 修改为 > ，避免 0 触发告警
            alerts.append({
                'category': 'shard_allocation',
                'check_item': 'cluster.unassigned_shards',
                'message': f'存在 {unassigned} 个未分配分片',
                'current_value': unassigned,
                'threshold': warning_threshold,
                'severity': 'warning',
                'severity_level': unassigned_config.get('severity_level', 2),
                'recommendation': '检查分片分配策略和节点可用性'
            })
        
        # 4. 检查初始化中分片
        initializing = cluster_health.get('initializing_shards', 0)
        init_config = cluster_config.get('initializing_shards', {})
        
        if initializing >= init_config.get('critical', 50):
            alerts.append({
                'category': 'cluster_health',
                'check_item': 'cluster.initializing_shards',
                'message': f'{initializing} 个分片正在初始化（严重）',
                'current_value': initializing,
                'threshold': init_config.get('critical'),
                'severity': 'critical',
                'recommendation': '检查节点负载和分片恢复速度'
            })
        elif initializing > init_config.get('warning', 10):  # 修改为 > ，避免 0 触发告警
            alerts.append({
                'category': 'cluster_health',
                'check_item': 'cluster.initializing_shards',
                'message': f'{initializing} 个分片正在初始化',
                'current_value': initializing,
                'threshold': init_config.get('warning'),
                'severity': 'warning',
                'recommendation': '关注分片恢复进度'
            })
        
        # 5. 检查迁移中分片
        relocating = cluster_health.get('relocating_shards', 0)
        relocate_config = cluster_config.get('relocating_shards', {})
        
        if relocating >= relocate_config.get('critical', 50):
            alerts.append({
                'category': 'shard_allocation',
                'check_item': 'cluster.relocating_shards',
                'message': f'{relocating} 个分片正在迁移（严重）',
                'current_value': relocating,
                'threshold': relocate_config.get('critical'),
                'severity': 'critical',
                'recommendation': '检查集群负载均衡情况'
            })
        elif relocating > relocate_config.get('warning', 10):  # 修改为 > ，避免 0 触发告警
            alerts.append({
                'category': 'shard_allocation',
                'check_item': 'cluster.relocating_shards',
                'message': f'{relocating} 个分片正在迁移',
                'current_value': relocating,
                'threshold': relocate_config.get('warning'),
                'severity': 'warning',
                'recommendation': '关注分片迁移进度'
            })
        
        # 6. 检查延迟未分配分片
        delayed = cluster_health.get('delayed_unassigned_shards', 0)
        delayed_config = cluster_config.get('delayed_unassigned_shards', {})
        
        if delayed >= delayed_config.get('critical', 10):
            alerts.append({
                'category': 'shard_allocation',
                'check_item': 'cluster.delayed_unassigned_shards',
                'message': f'{delayed} 个分片延迟未分配（严重）',
                'current_value': delayed,
                'threshold': delayed_config.get('critical'),
                'severity': 'critical',
                'recommendation': '检查分片分配延迟原因'
            })
        elif delayed > delayed_config.get('warning', 1):  # 修改为 > ，避免 0 触发告警
            alerts.append({
                'category': 'shard_allocation',
                'check_item': 'cluster.delayed_unassigned_shards',
                'message': f'{delayed} 个分片延迟未分配',
                'current_value': delayed,
                'threshold': delayed_config.get('warning'),
                'severity': 'warning',
                'recommendation': '关注分片分配延迟情况'
            })
        
        # 7. 检查集群任务队列
        pending_tasks = cluster_health.get('number_of_pending_tasks', 0)
        pending_config = cluster_config.get('pending_tasks', {})
        
        if pending_tasks >= pending_config.get('critical', 100):
            alerts.append({
                'category': 'cluster_health',
                'check_item': 'cluster.pending_tasks',
                'message': f'集群任务队列拥堵：{pending_tasks}（严重）',
                'current_value': pending_tasks,
                'threshold': pending_config.get('critical'),
                'severity': 'critical',
                'recommendation': '检查集群负载和主节点性能'
            })
        elif pending_tasks > pending_config.get('warning', 50):  # 修改为 > ，避免 0 触发告警
            alerts.append({
                'category': 'cluster_health',
                'check_item': 'cluster.pending_tasks',
                'message': f'集群任务队列较长：{pending_tasks}',
                'current_value': pending_tasks,
                'threshold': pending_config.get('warning'),
                'severity': 'warning',
                'recommendation': '关注集群任务处理速度'
            })
        
        # 8. 检查节点总数
        nodes_total = cluster_health.get('number_of_nodes', 0)
        nodes_data = cluster_health.get('number_of_data_nodes', 0)
        nodes_config = cluster_config.get('nodes', {})
        
        # 检查总节点数
        if nodes_total > nodes_config.get('total_warning', 100):
            alerts.append({
                'category': 'cluster_health',
                'check_item': 'cluster.nodes.total',
                'message': f'集群节点数过多：{nodes_total}',
                'current_value': nodes_total,
                'threshold': nodes_config.get('total_warning'),
                'severity': 'warning',
                'recommendation': '考虑集群拆分或优化节点管理'
            })
        
        # 检查数据节点数
        if nodes_data > nodes_config.get('data_nodes_warning', 50):
            alerts.append({
                'category': 'cluster_health',
                'check_item': 'cluster.nodes.data',
                'message': f'数据节点数过多：{nodes_data}',
                'current_value': nodes_data,
                'threshold': nodes_config.get('data_nodes_warning'),
                'severity': 'warning',
                'recommendation': '优化数据节点分布'
            })
        
        return alerts
    
    def check_node_resources(self, nodes: List[Dict[str, Any]], data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        检查节点资源使用情况
        
        Args:
            nodes: 节点列表
            data: 完整的诊断数据
            
        Returns:
            告警列表
        """
        alerts = []
        node_config = self.config.get('node', {})
        
        if not nodes:
            return alerts
        
        # 处理 nodes 可能是字典的情况
        if isinstance(nodes, dict):
            nodes_list = list(nodes.values())
        else:
            nodes_list = nodes
        
        # 统计资源使用
        total_nodes = len(nodes_list)
        total_disk = sum(node.get('disk_used_percent', 0) for node in nodes_list)
        total_heap = sum(node.get('heap_used_percent', 0) for node in nodes_list)
        total_cpu = sum(node.get('cpu_percent', 0) for node in nodes_list)
        
        avg_disk = total_disk / total_nodes
        avg_heap = total_heap / total_nodes
        avg_cpu = total_cpu / total_nodes
        
        max_disk = max(node.get('disk_used_percent', 0) for node in nodes_list)
        max_heap = max(node.get('heap_used_percent', 0) for node in nodes_list)
        max_cpu = max(node.get('cpu_percent', 0) for node in nodes_list)
        
        # 找出资源使用最高的节点
        max_disk_node = max(nodes_list, key=lambda n: n.get('disk_used_percent', 0)).get('name', 'N/A')
        max_heap_node = max(nodes_list, key=lambda n: n.get('heap_used_percent', 0)).get('name', 'N/A')
        
        # 1. 检查磁盘使用率
        disk_config = node_config.get('disk_usage_percent', {})
        
        if avg_disk >= disk_config.get('emergency', 90):
            alerts.append({
                'category': 'node_resources',
                'check_item': 'node.disk_usage_percent',
                'message': f'平均磁盘使用率 {avg_disk:.1f}%，已达紧急水位线',
                'current_value': round(avg_disk, 1),
                'threshold': disk_config.get('emergency'),
                'severity': 'critical',
                'severity_level': disk_config.get('severity_level', 3),
                'recommendation': '立即清理磁盘或扩容节点',
                'location': max_disk_node
            })
        elif avg_disk >= disk_config.get('critical', 85):
            alerts.append({
                'category': 'node_resources',
                'check_item': 'node.disk_usage_percent',
                'message': f'平均磁盘使用率 {avg_disk:.1f}%，超过临界值',
                'current_value': round(avg_disk, 1),
                'threshold': disk_config.get('critical'),
                'severity': 'critical',
                'recommendation': '立即清理磁盘或扩容',
                'location': max_disk_node
            })
        elif avg_disk >= disk_config.get('alert', 80):
            alerts.append({
                'category': 'node_resources',
                'check_item': 'node.disk_usage_percent',
                'message': f'平均磁盘使用率 {avg_disk:.1f}%，触发水位线警告',
                'current_value': round(avg_disk, 1),
                'threshold': disk_config.get('alert'),
                'severity': 'warning',
                'recommendation': '关注磁盘使用趋势，计划扩容',
                'location': max_disk_node
            })
        elif avg_disk >= disk_config.get('warning', 70):
            alerts.append({
                'category': 'node_resources',
                'check_item': 'node.disk_usage_percent',
                'message': f'平均磁盘使用率 {avg_disk:.1f}%，需要关注',
                'current_value': round(avg_disk, 1),
                'threshold': disk_config.get('warning'),
                'severity': 'warning',
                'recommendation': '监控磁盘使用增长趋势',
                'location': max_disk_node
            })
        
        # 2. 检查 JVM 堆使用率
        heap_config = node_config.get('heap_used_percent', {})
        
        if avg_heap >= heap_config.get('emergency', 90):
            alerts.append({
                'category': 'node_resources',
                'check_item': 'node.heap_used_percent',
                'message': f'平均 JVM 堆使用率 {avg_heap:.1f}%，OOM 风险极高',
                'current_value': round(avg_heap, 1),
                'threshold': heap_config.get('emergency'),
                'severity': 'critical',
                'recommendation': '立即增加堆内存或优化查询',
                'location': max_heap_node
            })
        elif avg_heap >= heap_config.get('critical', 85):
            alerts.append({
                'category': 'node_resources',
                'check_item': 'node.heap_used_percent',
                'message': f'平均 JVM 堆使用率 {avg_heap:.1f}%，OOM 风险高',
                'current_value': round(avg_heap, 1),
                'threshold': heap_config.get('critical'),
                'severity': 'critical',
                'recommendation': '考虑增加堆内存或优化 GC',
                'location': max_heap_node
            })
        elif avg_heap >= heap_config.get('alert', 75):
            alerts.append({
                'category': 'node_resources',
                'check_item': 'node.heap_used_percent',
                'message': f'平均 JVM 堆使用率 {avg_heap:.1f}%，GC 频繁',
                'current_value': round(avg_heap, 1),
                'threshold': heap_config.get('alert'),
                'severity': 'warning',
                'recommendation': '优化查询减少内存消耗',
                'location': max_heap_node
            })
        elif avg_heap >= heap_config.get('warning', 70):
            alerts.append({
                'category': 'node_resources',
                'check_item': 'node.heap_used_percent',
                'message': f'平均 JVM 堆使用率 {avg_heap:.1f}%，较高',
                'current_value': round(avg_heap, 1),
                'threshold': heap_config.get('warning'),
                'severity': 'warning',
                'recommendation': '关注堆内存使用趋势',
                'location': max_heap_node
            })
        
        # 3. 检查 CPU 使用率
        cpu_config = node_config.get('cpu_percent', {})
        
        if avg_cpu >= cpu_config.get('critical', 90):
            alerts.append({
                'category': 'node_resources',
                'check_item': 'node.cpu_percent',
                'message': f'平均 CPU 使用率 {avg_cpu:.1f}%，严重过载',
                'current_value': round(avg_cpu, 1),
                'threshold': cpu_config.get('critical'),
                'severity': 'critical',
                'recommendation': '立即降低负载或扩容',
                'location': max_cpu
            })
        elif avg_cpu >= cpu_config.get('alert', 75):
            alerts.append({
                'category': 'node_resources',
                'check_item': 'node.cpu_percent',
                'message': f'平均 CPU 使用率 {avg_cpu:.1f}%，高负载',
                'current_value': round(avg_cpu, 1),
                'threshold': cpu_config.get('alert'),
                'severity': 'warning',
                'recommendation': '优化查询或增加节点',
                'location': max_cpu
            })
        elif avg_cpu >= cpu_config.get('warning', 60):
            alerts.append({
                'category': 'node_resources',
                'check_item': 'node.cpu_percent',
                'message': f'平均 CPU 使用率 {avg_cpu:.1f}%，较高负载',
                'current_value': round(avg_cpu, 1),
                'threshold': cpu_config.get('warning'),
                'severity': 'warning',
                'recommendation': '关注 CPU 使用趋势',
                'location': max_cpu
            })
        
        # 4. 检查单节点分片数
        shards_config = node_config.get('shards_per_node', {})
        
        # 从 shards 数据中统计每个节点的分片数
        shards_data = data.get('shards', [])
        if shards_data:
            # 统计每个节点的分片数
            shards_per_node_count = {}
            for shard in shards_data:
                node_name = shard.get('node', '')
                if node_name:
                    shards_per_node_count[node_name] = shards_per_node_count.get(node_name, 0) + 1
            
            if shards_per_node_count:
                # 计算平均和最大
                avg_shards = sum(shards_per_node_count.values()) / len(shards_per_node_count)
                max_shards_node = max(shards_per_node_count, key=shards_per_node_count.get)
                max_shards = shards_per_node_count[max_shards_node]
                
                # 检查是否超过阈值
                if avg_shards >= shards_config.get('critical', 1000):
                    alerts.append({
                        'category': 'node_resources',
                        'check_item': 'node.shards_per_node',
                        'message': f'单节点分片数过多：{max_shards}（{max_shards_node}）',
                        'current_value': max_shards,
                        'threshold': shards_config.get('critical'),
                        'severity': 'critical',
                        'recommendation': '优化分片分布或增加节点'
                    })
                elif avg_shards >= shards_config.get('warning', 500):
                    alerts.append({
                        'category': 'node_resources',
                        'check_item': 'node.shards_per_node',
                        'message': f'单节点分片数偏多：{max_shards}（{max_shards_node}）',
                        'current_value': max_shards,
                        'threshold': shards_config.get('warning'),
                        'severity': 'warning',
                        'recommendation': '关注分片分布情况'
                    })
        
        # 5. 检查节点连接数
        connections_config = node_config.get('connections', {})
        
        # 从 nodes_stats 中统计连接数
        nodes_stats = data.get('nodes_stats', {})
        if nodes_stats and 'nodes' in nodes_stats:
            total_connections = 0
            max_connections = 0
            max_connections_node = 'N/A'
            
            for node_id, node_stats in nodes_stats['nodes'].items():
                # 使用 transport.server_open 作为连接数
                server_open = node_stats.get('transport', {}).get('server_open', 0)
                total_connections += server_open
                if server_open > max_connections:
                    max_connections = server_open
                    max_connections_node = node_stats.get('name', node_id)
            
            # 检查是否超过阈值
            if max_connections >= connections_config.get('critical', 5000):
                alerts.append({
                    'category': 'node_resources',
                    'check_item': 'node.connections',
                    'message': f'节点连接数过多：{max_connections}（{max_connections_node}）',
                    'current_value': max_connections,
                    'threshold': connections_config.get('critical'),
                    'severity': 'critical',
                    'recommendation': '检查连接来源，优化连接管理'
                })
            elif max_connections >= connections_config.get('warning', 1000):
                alerts.append({
                    'category': 'node_resources',
                    'check_item': 'node.connections',
                    'message': f'节点连接数较多：{max_connections}（{max_connections_node}）',
                    'current_value': max_connections,
                    'threshold': connections_config.get('warning'),
                    'severity': 'warning',
                    'recommendation': '关注连接数增长趋势'
                })
        
        return alerts
    
    def check_index_health(self, indices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        检查索引健康状况
        
        Args:
            indices: 索引列表
            
        Returns:
            告警列表
        """
        alerts = []
        index_config = self.config.get('index', {})
        
        if not indices:
            return alerts
        
        # 1. 检查索引健康分布
        health_config = index_config.get('health', {})
        red_indices = [idx for idx in indices if idx.get('health') == 'red']
        yellow_indices = [idx for idx in indices if idx.get('health') == 'yellow']
        green_indices = [idx for idx in indices if idx.get('health') == 'green']
        
        # 检查 RED 索引
        if red_indices:
            severity = health_config.get('red', 'critical')
            alerts.append({
                'category': 'index_health',
                'check_item': 'index.health',
                'message': f'{len(red_indices)} 个索引状态为 RED',
                'current_value': len(red_indices),
                'threshold': 0,
                'severity': severity,
                'recommendation': f'检查以下索引的主分片分配：{", ".join([idx.get("name", "N/A") for idx in red_indices[:3]])}'
            })
        
        # 检查 YELLOW 索引
        if yellow_indices:
            severity = health_config.get('yellow', 'warning')
            alerts.append({
                'category': 'index_health',
                'check_item': 'index.health',
                'message': f'{len(yellow_indices)} 个索引状态为 YELLOW',
                'current_value': len(yellow_indices),
                'threshold': 0,
                'severity': severity,
                'recommendation': f'检查以下索引的副本分片分配：{", ".join([idx.get("name", "N/A") for idx in yellow_indices[:3]])}'
            })
        
        # 检查 GREEN 索引（根据配置决定是否告警）
        green_severity = health_config.get('green', None)
        if green_indices and green_severity and green_severity != 'normal':
            alerts.append({
                'category': 'index_health',
                'check_item': 'index.health',
                'message': f'{len(green_indices)} 个索引状态为 GREEN',
                'current_value': len(green_indices),
                'threshold': '配置级别：' + green_severity,
                'severity': green_severity,
                'recommendation': '根据配置要求，GREEN 状态也需要关注'
            })
        
        # 2. 检查大索引（支持 warning 和 critical 两个级别）
        size_config = index_config.get('size_gb', {})
        warning_threshold = size_config.get('warning', 100) * (1024**3)
        critical_threshold = size_config.get('critical', 1000) * (1024**3)
        
        # 先检查 critical 级别的索引
        critical_large_indices = [idx for idx in indices if idx.get('store_size_bytes', 0) > critical_threshold]
        
        # 再检查 warning 级别的索引（排除已经达到 critical 的）
        warning_large_indices = [idx for idx in indices 
                                 if warning_threshold < idx.get('store_size_bytes', 0) <= critical_threshold]
        
        # 生成 critical 告警
        if critical_large_indices:
            alerts.append({
                'category': 'index_size',
                'check_item': 'index.size_gb',
                'message': f'{len(critical_large_indices)} 个索引超过 {size_config.get("critical")}GB',
                'current_value': f'{len(critical_large_indices)} 个索引',
                'threshold': f">{size_config.get('critical')}GB",
                'severity': 'critical',
                'recommendation': '考虑拆分索引或使用生命周期管理 (ILM) 进行数据归档'
            })
        
        # 生成 warning 告警
        if warning_large_indices:
            alerts.append({
                'category': 'index_size',
                'check_item': 'index.size_gb',
                'message': f'{len(warning_large_indices)} 个索引超过 {size_config.get("warning")}GB',
                'current_value': f'{len(warning_large_indices)} 个索引',
                'threshold': f">{size_config.get('warning')}GB",
                'severity': 'warning',
                'recommendation': '关注索引增长趋势，考虑优化策略'
            })
        
        # 3. 检查段数量（支持 warning 和 critical 两个级别）
        segments_config = index_config.get('segments_count', {})
        warning_threshold = segments_config.get('warning', 100)
        critical_threshold = segments_config.get('critical', 500)
        
        # 先检查 critical 级别的索引
        critical_high_segments = [idx for idx in indices if idx.get('segments_count', 0) >= critical_threshold]
        
        # 再检查 warning 级别的索引（排除已经达到 critical 的）
        warning_high_segments = [idx for idx in indices 
                                 if warning_threshold <= idx.get('segments_count', 0) < critical_threshold]
        
        # 生成 critical 告警
        if critical_high_segments:
            alerts.append({
                'category': 'index_health',
                'check_item': 'index.segments_count',
                'message': f'{len(critical_high_segments)} 个索引 segment 数量达到 {segments_config.get("critical")}',
                'current_value': len(critical_high_segments),
                'threshold': segments_config.get('critical'),
                'severity': 'critical',
                'recommendation': '在业务低峰期执行 force_merge'
            })
        
        # 生成 warning 告警
        if warning_high_segments:
            alerts.append({
                'category': 'index_health',
                'check_item': 'index.segments_count',
                'message': f'{len(warning_high_segments)} 个索引 segment 数量达到 {segments_config.get("warning")}',
                'current_value': len(warning_high_segments),
                'threshold': segments_config.get('warning'),
                'severity': 'warning',
                'recommendation': '关注 segment 增长趋势，考虑执行 force_merge'
            })
        
        # 4. 检查文档数（支持 warning 和 critical 两个级别）
        docs_config = index_config.get('docs_count', {})
        warning_threshold = docs_config.get('warning', 100000000)
        critical_threshold = docs_config.get('critical', 500000000)
        
        # 先检查 critical 级别的索引
        critical_large_docs_indices = [idx for idx in indices if idx.get('docs_count', 0) > critical_threshold]
        
        # 再检查 warning 级别的索引（排除已经达到 critical 的）
        warning_large_docs_indices = [idx for idx in indices 
                                      if warning_threshold < idx.get('docs_count', 0) <= critical_threshold]
        
        # 生成 critical 告警
        if critical_large_docs_indices:
            alerts.append({
                'category': 'index_health',
                'check_item': 'index.docs_count',
                'message': f'{len(critical_large_docs_indices)} 个索引文档数超过 {docs_config.get("critical")/1e8:.0f}亿',
                'current_value': len(critical_large_docs_indices),
                'threshold': docs_config.get('critical'),
                'severity': 'critical',
                'recommendation': '考虑拆分索引或滚动索引'
            })
        
        # 生成 warning 告警
        if warning_large_docs_indices:
            alerts.append({
                'category': 'index_health',
                'check_item': 'index.docs_count',
                'message': f'{len(warning_large_docs_indices)} 个索引文档数超过 {docs_config.get("warning")/1e8:.0f}亿',
                'current_value': len(warning_large_docs_indices),
                'threshold': docs_config.get('warning'),
                'severity': 'warning',
                'recommendation': '关注文档数增长趋势，考虑优化索引策略'
            })
        
        # 5. 检查删除文档比例（支持 warning 和 critical 两个级别）
        deleted_config = index_config.get('deleted_docs_ratio', {})
        warning_threshold = deleted_config.get('warning', 0.1)
        critical_threshold = deleted_config.get('critical', 0.2)
        
        # 先检查 critical 级别的索引
        critical_high_deleted = [idx for idx in indices if idx.get('deleted_docs_ratio', 0) > critical_threshold]
        
        # 再检查 warning 级别的索引（排除已经达到 critical 的）
        warning_high_deleted = [idx for idx in indices 
                                if warning_threshold < idx.get('deleted_docs_ratio', 0) <= critical_threshold]
        
        # 生成 critical 告警
        if critical_high_deleted:
            alerts.append({
                'category': 'index_health',
                'check_item': 'index.deleted_docs_ratio',
                'message': f'{len(critical_high_deleted)} 个索引删除文档比例超过 {deleted_config.get("critical")*100:.0f}%',
                'current_value': f'{len(critical_high_deleted)} 个索引',
                'threshold': deleted_config.get('critical'),
                'severity': 'critical',
                'recommendation': '执行 force_merge 清理删除文档'
            })
        
        # 生成 warning 告警
        if warning_high_deleted:
            alerts.append({
                'category': 'index_health',
                'check_item': 'index.deleted_docs_ratio',
                'message': f'{len(warning_high_deleted)} 个索引删除文档比例超过 {deleted_config.get("warning")*100:.0f}%',
                'current_value': f'{len(warning_high_deleted)} 个索引',
                'threshold': deleted_config.get('warning'),
                'severity': 'warning',
                'recommendation': '关注删除文档增长趋势，考虑执行 force_merge'
            })
        
        # 6. 检查单索引分片数
        shards_per_index_config = index_config.get('shards_per_index', {})
        high_shards_indices = [idx for idx in indices if idx.get('shards_count', 0) > shards_per_index_config.get('critical', 100)]
        
        if high_shards_indices:
            alerts.append({
                'category': 'index_health',
                'check_item': 'index.shards_per_index',
                'message': f'{len(high_shards_indices)} 个索引分片数超过 {shards_per_index_config.get("critical")}',
                'current_value': len(high_shards_indices),
                'threshold': shards_per_index_config.get('critical'),
                'severity': 'critical',
                'recommendation': '优化索引分片策略'
            })
        
        return alerts
    
    def check_shards(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        检查分片分布和大小
        
        Args:
            data: 完整的诊断数据
            
        Returns:
            告警列表
        """
        alerts = []
        shard_config = self.config.get('shard', {})
        
        shards_data = data.get('shards', [])
        if not shards_data:
            return alerts
        
        # 1. 检查分片大小（与报告 shards 检查阈值一致）
        from es_insight.shard_size_check import (
            count_physical_shards_over_size_gb,
            oversized_single_shard_threshold_gb,
        )

        single_gb = oversized_single_shard_threshold_gb(self.config)
        large_count = count_physical_shards_over_size_gb(shards_data, single_gb)

        if large_count:
            alerts.append({
                'category': 'shard',
                'check_item': 'shard.size_gb',
                'message': f'{large_count} 个分片超过 {single_gb}GB',
                'current_value': large_count,
                'threshold': single_gb,
                'severity': 'critical',
                'recommendation': (
                    '考虑拆分索引或使用更小的分片策略；'
                    '该数量为含主分片与副本的物理分片条数'
                ),
            })
        
        # 2. 检查分片文档数
        docs_config = shard_config.get('docs_count', {})
        critical_threshold = docs_config.get('critical', 200000000)
        # 如果阈值小于 1000，说明配置的是亿为单位，需要转换为实际数值
        if critical_threshold < 1000:
            critical_threshold = int(critical_threshold * 1e8)
        large_docs_shards = [s for s in shards_data if int(s.get('docs') or 0) > critical_threshold]
        
        if large_docs_shards:
            alerts.append({
                'category': 'shard',
                'check_item': 'shard.docs_count',
                'message': f'{len(large_docs_shards)} 个分片文档数超过 {docs_config.get("critical")/1e8:.0f}亿',
                'current_value': len(large_docs_shards),
                'threshold': docs_config.get('critical'),
                'severity': 'critical',
                'recommendation': '优化索引策略，使用更小的分片'
            })
        
        # 3. 检查分片平衡
        balance_config = shard_config.get('balance_std_dev', {})
        # 统计每个节点的分片数
        shards_per_node = {}
        for shard in shards_data:
            node_name = shard.get('node', '')
            if node_name:
                shards_per_node[node_name] = shards_per_node.get(node_name, 0) + 1
        
        if shards_per_node:
            import statistics
            shard_counts = list(shards_per_node.values())
            std_dev = statistics.stdev(shard_counts) if len(shard_counts) > 1 else 0
            
            if std_dev >= balance_config.get('critical', 30):
                alerts.append({
                    'category': 'shard',
                    'check_item': 'shard.balance_std_dev',
                    'message': f'分片分布标准差过大：{std_dev:.1f}',
                    'current_value': round(std_dev, 1),
                    'threshold': balance_config.get('critical'),
                    'severity': 'critical',
                    'recommendation': '执行 reroute 重新平衡分片'
                })
            elif std_dev >= balance_config.get('warning', 15):
                alerts.append({
                    'category': 'shard',
                    'check_item': 'shard.balance_std_dev',
                    'message': f'分片分布不均：{std_dev:.1f}',
                    'current_value': round(std_dev, 1),
                    'threshold': balance_config.get('warning'),
                    'severity': 'warning',
                    'recommendation': '关注分片分布情况'
                })
        
        return alerts
    
    def check_ilm(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        检查生命周期管理 (ILM) 状态
        
        Args:
            data: 完整的诊断数据
            
        Returns:
            告警列表
        """
        alerts = []
        ilm_config = self.config.get('ilm', {})
        
        # 从 ilm_status.json 中获取 ILM 状态
        ilm_status = data.get('ilm_status', {})
        if not ilm_status:
            return alerts
        
        # 检查 ILM 错误
        status_config = ilm_config.get('status', {})
        errors = ilm_status.get('errors', [])
        failures = ilm_status.get('failures', [])
        
        if errors:
            severity = status_config.get('error', 'critical')
            alerts.append({
                'category': 'ilm',
                'check_item': 'ilm.status',
                'message': f'ILM 存在 {len(errors)} 个错误',
                'current_value': len(errors),
                'threshold': 0,
                'severity': severity,
                'recommendation': '检查 ILM 策略配置和执行日志'
            })
        
        if failures:
            severity = status_config.get('failure', 'warning')
            alerts.append({
                'category': 'ilm',
                'check_item': 'ilm.failures',
                'message': f'ILM 存在 {len(failures)} 个失败',
                'current_value': len(failures),
                'threshold': 0,
                'severity': severity,
                'recommendation': '检查失败的 ILM 操作原因'
            })
        
        return alerts
    
    def check_snapshot(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        检查快照状态
        
        Args:
            data: 完整的诊断数据
            
        Returns:
            告警列表
        """
        alerts = []
        snapshot_config = self.config.get('snapshot', {})
        
        # 从 snapshot.json 中获取快照数据
        snapshot_data = data.get('snapshot', {})
        snapshots = snapshot_data.get('snapshots', []) if snapshot_data else []
        if not snapshots:
            return alerts
        
        # 检查最新快照状态
        latest_status_config = snapshot_config.get('latest_status', {})
        latest_snapshot = snapshots[-1] if snapshots else None
        
        if latest_snapshot:
            state = latest_snapshot.get('state', '').lower()
            
            if state == 'failed':
                severity = latest_status_config.get('failed', 'critical')
                alerts.append({
                    'category': 'snapshot',
                    'check_item': 'snapshot.latest_status',
                    'message': f'最新快照失败：{latest_snapshot.get("snapshot", "N/A")}',
                    'current_value': 'FAILED',
                    'threshold': 'SUCCESS',
                    'severity': severity,
                    'recommendation': '检查快照仓库和错误日志'
                })
            elif state == 'partial':
                severity = latest_status_config.get('partial', 'warning')
                alerts.append({
                    'category': 'snapshot',
                    'check_item': 'snapshot.latest_status',
                    'message': f'最新快照部分成功：{latest_snapshot.get("snapshot", "N/A")}',
                    'current_value': 'PARTIAL',
                    'threshold': 'SUCCESS',
                    'severity': severity,
                    'recommendation': '检查未成功备份的索引'
                })
        
        return alerts
    
    def check_security(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        检查安全配置
        
        Args:
            data: 完整的诊断数据
            
        Returns:
            告警列表
        """
        alerts = []
        security_config = self.config.get('security', {})
        
        # 检查 X-Pack 启用状态
        xpack_config = security_config.get('xpack_enabled', {})
        security_data = data.get('security', {})
        xpack_enabled = security_data.get('xpack_enabled', False) if security_data else False
        
        if not xpack_enabled:
            # 支持布尔值和字符串两种形式的 severity
            severity_value = xpack_config.get('required', xpack_config.get('critical', False))
            if isinstance(severity_value, bool):
                severity = 'critical' if severity_value else 'warning'
            elif isinstance(severity_value, str):
                severity = severity_value.lower()
            else:
                severity = 'warning'
            alerts.append({
                'category': 'security',
                'check_item': 'security.xpack_enabled',
                'message': 'X-Pack 安全功能未启用',
                'current_value': False,
                'threshold': True,
                'severity': severity,
                'recommendation': '建议启用 X-Pack 安全功能'
            })
        
        return alerts
    
    def check_all(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        执行所有检查
        
        Args:
            data: 完整的诊断数据
            
        Returns:
            所有告警列表
        """
        all_alerts = []
        
        # 1. 集群健康检查
        cluster_health = data.get('cluster_health', {})
        cluster_alerts = self.check_cluster_health(cluster_health)
        all_alerts.extend(cluster_alerts)
        
        # 2. 节点资源检查
        nodes = data.get('nodes', [])
        node_alerts = self.check_node_resources(nodes, data)
        all_alerts.extend(node_alerts)
        
        # 3. 索引健康检查
        indices = data.get('indices', [])
        index_alerts = self.check_index_health(indices)
        all_alerts.extend(index_alerts)
        
        # 4. 分片检查
        shard_alerts = self.check_shards(data)
        all_alerts.extend(shard_alerts)
        
        # 6. ILM 检查
        ilm_alerts = self.check_ilm(data)
        all_alerts.extend(ilm_alerts)
        
        # 7. 快照检查
        snapshot_alerts = self.check_snapshot(data)
        all_alerts.extend(snapshot_alerts)
        
        # 8. 安全检查
        security_alerts = self.check_security(data)
        all_alerts.extend(security_alerts)
        
        logger.info(f"✓ 完成所有检查，发现 {len(all_alerts)} 个告警")
        
        return all_alerts
