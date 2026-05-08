"""健康评分指标采集模块

从诊断数据中提取各维度的健康评分指标
"""

from typing import Dict, Any, List, Optional
from loguru import logger


class MetricsCollector:
    """指标采集器"""
    
    def __init__(self, diagnostic_data: Dict[str, Any]):
        """
        初始化指标采集器
        
        Args:
            diagnostic_data: 诊断数据字典，包含cluster_health, nodes, indices等
        """
        self.data = diagnostic_data
    
    def collect_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        采集所有维度的指标
        
        Returns:
            包含所有维度指标的字典
        """
        metrics = {
            'cluster_health': self._collect_cluster_health_metrics(),
            'node_performance': self._collect_node_performance_metrics(),
            'index_status': self._collect_index_status_metrics(),
            'performance_metrics': self._collect_performance_metrics(),
            'security_config': self._collect_security_config_metrics(),
            'operation_status': self._collect_operation_status_metrics()
        }
        
        return metrics
    
    def _collect_cluster_health_metrics(self) -> Dict[str, Any]:
        """采集集群健康指标"""
        cluster_health = self.data.get('cluster_health', {})
        cluster_stats = self.data.get('cluster_stats', {})
        
        # 处理status字段 - 转换为数值评分
        status = cluster_health.get('status', 'unknown').lower()
        status_score_map = {'green': 100, 'yellow': 60, 'red': 0}
        status_score = status_score_map.get(status, 0)
        
        # 计算未分配分片数
        unassigned_shards = cluster_health.get('unassigned_shards', 0)
        
        # 获取活跃分片百分比
        active_shards_percent = cluster_health.get(
            'active_shards_percent_as_number',
            cluster_health.get('active_shards_percent', 0)
        )
        
        # 检查集群设置一致性（简化：假设一致）
        settings_consistency = 100  # 默认认为一致
        
        # 检查版本一致性
        version_consistency = self._check_version_consistency()
        
        return {
            'status': {
                'value': status,
                'score': status_score,
                'raw_value': status
            },
            'active_shards_percent': {
                'value': active_shards_percent,
                'unit': '%'
            },
            'unassigned_shards': {
                'value': unassigned_shards,
                'unit': '个'
            },
            'cluster_settings_consistency': {
                'value': settings_consistency,
                'unit': '分'
            },
            'cluster_version_consistency': {
                'value': version_consistency,
                'unit': '分'
            }
        }
    
    def _collect_node_performance_metrics(self) -> Dict[str, Any]:
        """采集节点性能指标"""
        nodes = self.data.get('nodes', [])
        nodes_stats = self.data.get('nodes_stats', {})
        
        if not nodes:
            # 如果没有节点数据，返回默认值
            return self._get_default_node_metrics()
        
        # 计算各指标的平均值和最差值
        cpu_values = []
        heap_values = []
        disk_values = []
        load_values = []
        shards_counts = []
        http_connections = []
        
        for node in nodes:
            # CPU使用率
            cpu = node.get('cpu_percent')
            if cpu is not None:
                try:
                    cpu_values.append(float(cpu))
                except (ValueError, TypeError):
                    pass
            
            # JVM堆使用率
            heap = node.get('heap_used_percent')
            if heap is not None:
                try:
                    heap_values.append(float(heap))
                except (ValueError, TypeError):
                    pass
            
            # 磁盘使用率
            disk = node.get('disk_used_percent')
            if disk is not None:
                try:
                    disk_values.append(float(disk))
                except (ValueError, TypeError):
                    pass
            
            # 负载平均值（需要除以CPU核心数得到比率）
            load_avg = node.get('load_average_1m')
            cpu_cores = node.get('cpu_cores', 1)
            if load_avg is not None and cpu_cores > 0:
                try:
                    load_ratio = float(load_avg) / cpu_cores
                    load_values.append(load_ratio)
                except (ValueError, TypeError):
                    pass
            
            # 分片数
            shard_count = node.get('shards_count', 0)
            try:
                shards_counts.append(int(shard_count))
            except (ValueError, TypeError):
                pass
            
            # HTTP连接数
            connections = node.get('http_connections')
            if connections is not None:
                try:
                    http_connections.append(int(connections))
                except (ValueError, TypeError):
                    pass
        
        # 计算统计值（使用最大值，因为最差节点决定整体健康状况）
        result = {
            'disk_used_percent': {
                'value': max(disk_values) if disk_values else 0,
                'unit': '%',
                'avg': sum(disk_values) / len(disk_values) if disk_values else 0
            },
            'heap_used_percent': {
                'value': max(heap_values) if heap_values else 0,
                'unit': '%',
                'avg': sum(heap_values) / len(heap_values) if heap_values else 0
            },
            'cpu_percent': {
                'value': max(cpu_values) if cpu_values else 0,
                'unit': '%',
                'avg': sum(cpu_values) / len(cpu_values) if cpu_values else 0
            },
            'load_average_ratio': {
                'value': max(load_values) if load_values else 0,
                'unit': '倍',
                'avg': sum(load_values) / len(load_values) if load_values else 0
            },
            'shards_per_node': {
                'value': max(shards_counts) if shards_counts else 0,
                'unit': '个',
                'avg': sum(shards_counts) / len(shards_counts) if shards_counts else 0
            },
            'http_connections': {
                'value': max(http_connections) if http_connections else 0,
                'unit': '个',
                'avg': sum(http_connections) / len(http_connections) if http_connections else 0
            }
        }
        
        return result
    
    def _collect_index_status_metrics(self) -> Dict[str, Any]:
        """采集索引状态指标"""
        indices = self.data.get('indices', [])
        
        if not indices:
            return self._get_default_index_metrics()
        
        # 统计索引健康状态
        green_count = sum(1 for idx in indices if idx.get('health', '').lower() == 'green')
        yellow_count = sum(1 for idx in indices if idx.get('health', '').lower() == 'yellow')
        red_count = sum(1 for idx in indices if idx.get('health', '').lower() == 'red')
        total_count = len(indices)
        
        # 计算健康索引比例
        health_ratio = (green_count / total_count * 100) if total_count > 0 else 0
        
        # 计算平均索引大小（GB）
        sizes_gb = []
        doc_counts = []
        deleted_ratios = []
        shard_counts = []
        segment_counts = []
        
        for idx in indices:
            # 索引大小
            size_bytes = idx.get('store_size_in_bytes', 0)
            if size_bytes:
                try:
                    sizes_gb.append(float(size_bytes) / (1024 ** 3))
                except (ValueError, TypeError):
                    pass
            
            # 文档数量
            doc_count = idx.get('docs_count', 0)
            if doc_count:
                try:
                    doc_counts.append(int(doc_count))
                except (ValueError, TypeError):
                    pass
            
            # 已删除文档比例
            docs_deleted = idx.get('docs_deleted', 0)
            if doc_count and docs_deleted:
                try:
                    ratio = float(docs_deleted) / (float(doc_count) + float(docs_deleted)) * 100
                    deleted_ratios.append(ratio)
                except (ValueError, TypeError, ZeroDivisionError):
                    pass
            
            # 分片数
            primaries = idx.get('pri', 0)
            if primaries:
                try:
                    shard_counts.append(int(primaries))
                except (ValueError, TypeError):
                    pass
            
            # Segment数量（如果有）
            segments = idx.get('segments_count', 0)
            if segments:
                try:
                    segment_counts.append(int(segments))
                except (ValueError, TypeError):
                    pass
        
        return {
            'index_health_status': {
                'value': health_ratio,
                'unit': '%',
                'green_count': green_count,
                'yellow_count': yellow_count,
                'red_count': red_count,
                'total_count': total_count
            },
            'index_size_gb': {
                'value': max(sizes_gb) if sizes_gb else 0,
                'unit': 'GB',
                'avg': sum(sizes_gb) / len(sizes_gb) if sizes_gb else 0
            },
            'doc_count': {
                'value': max(doc_counts) if doc_counts else 0,
                'unit': '个',
                'avg': sum(doc_counts) / len(doc_counts) if doc_counts else 0
            },
            'deleted_docs_percent': {
                'value': max(deleted_ratios) if deleted_ratios else 0,
                'unit': '%',
                'avg': sum(deleted_ratios) / len(deleted_ratios) if deleted_ratios else 0
            },
            'shards_per_index': {
                'value': max(shard_counts) if shard_counts else 0,
                'unit': '个',
                'avg': sum(shard_counts) / len(shard_counts) if shard_counts else 0
            },
            'segments_per_index': {
                'value': max(segment_counts) if segment_counts else 0,
                'unit': '个',
                'avg': sum(segment_counts) / len(segment_counts) if segment_counts else 0
            }
        }
    
    def _collect_performance_metrics(self) -> Dict[str, Any]:
        """采集性能指标"""
        nodes_stats = self.data.get('nodes_stats', {})
        thread_pools = self.data.get('thread_pools', [])
        
        # 初始化结果
        result = {
            'search_thread_pool_queue': {'value': 0, 'unit': '个'},
            'write_thread_pool_queue': {'value': 0, 'unit': '个'},
            'bulk_thread_pool_queue': {'value': 0, 'unit': '个'},
            'search_rejection_rate': {'value': 0, 'unit': '%'},
            'write_rejection_rate': {'value': 0, 'unit': '%'},
            'bulk_rejection_rate': {'value': 0, 'unit': '%'}
        }
        
        # 从thread_pools中提取数据
        if thread_pools:
            search_queues = []
            write_queues = []
            bulk_queues = []
            
            search_completed = 0
            search_rejected = 0
            write_completed = 0
            write_rejected = 0
            bulk_completed = 0
            bulk_rejected = 0
            
            for pool in thread_pools:
                pool_name = pool.get('name', '').lower()
                queue_size = pool.get('queue_size', 0)
                completed = pool.get('completed', 0)
                rejected = pool.get('rejected', 0)
                
                try:
                    queue_size = int(queue_size) if queue_size else 0
                    completed = int(completed) if completed else 0
                    rejected = int(rejected) if rejected else 0
                except (ValueError, TypeError):
                    continue
                
                if 'search' in pool_name:
                    search_queues.append(queue_size)
                    search_completed += completed
                    search_rejected += rejected
                elif 'write' in pool_name or 'index' in pool_name:
                    write_queues.append(queue_size)
                    write_completed += completed
                    write_rejected += rejected
                elif 'bulk' in pool_name:
                    bulk_queues.append(queue_size)
                    bulk_completed += completed
                    bulk_rejected += rejected
            
            # 计算队列大小（取最大值）
            result['search_thread_pool_queue']['value'] = max(search_queues) if search_queues else 0
            result['write_thread_pool_queue']['value'] = max(write_queues) if write_queues else 0
            result['bulk_thread_pool_queue']['value'] = max(bulk_queues) if bulk_queues else 0
            
            # 计算拒绝率
            if search_completed + search_rejected > 0:
                result['search_rejection_rate']['value'] = (
                    search_rejected / (search_completed + search_rejected) * 100
                )
            
            if write_completed + write_rejected > 0:
                result['write_rejection_rate']['value'] = (
                    write_rejected / (write_completed + write_rejected) * 100
                )
            
            if bulk_completed + bulk_rejected > 0:
                result['bulk_rejection_rate']['value'] = (
                    bulk_rejected / (bulk_completed + bulk_rejected) * 100
                )
        
        return result
    
    def _collect_security_config_metrics(self) -> Dict[str, Any]:
        """采集安全配置指标"""
        # 优先从 cluster_settings_defaults 获取（与检查项保持一致）
        settings_defaults = self.data.get('cluster_settings_defaults', {})
        defaults = settings_defaults.get('defaults', {})
        
        # 如果 cluster_settings_defaults 不存在，回退到 settings
        if not defaults:
            settings = self.data.get('settings', {})
            cluster_settings = self.data.get('cluster_settings', {})
        else:
            settings = defaults
            cluster_settings = {}
        
        # 检查X-Pack安全是否启用
        xpack_security = settings.get('xpack.security.enabled', False)
        if isinstance(xpack_security, str):
            xpack_security = xpack_security.lower() in ['true', '1', 'yes']
        
        # 检查HTTP SSL
        http_ssl = settings.get('xpack.security.http.ssl.enabled', False)
        if isinstance(http_ssl, str):
            http_ssl = http_ssl.lower() in ['true', '1', 'yes']
        
        # 检查传输层SSL
        transport_ssl = settings.get('xpack.security.transport.ssl.enabled', False)
        if isinstance(transport_ssl, str):
            transport_ssl = transport_ssl.lower() in ['true', '1', 'yes']
        
        # 检查匿名访问
        anonymous_access = settings.get('xpack.security.authc.anonymous.roles', None)
        anonymous_disabled = anonymous_access is None
        
        # 检查默认密码（简化：如果启用了安全，则认为已设置）
        default_password_set = xpack_security
        
        return {
            'xpack_security_enabled': {
                'value': 100 if xpack_security else 0,
                'enabled': xpack_security
            },
            'default_password_set': {
                'value': 100 if default_password_set else 0,
                'set': default_password_set
            },
            'anonymous_access': {
                'value': 100 if anonymous_disabled else 0,
                'disabled': anonymous_disabled
            },
            'http_ssl_enabled': {
                'value': 100 if http_ssl else 0,
                'enabled': http_ssl
            },
            'transport_ssl_enabled': {
                'value': 100 if transport_ssl else 0,
                'enabled': transport_ssl
            }
        }
    
    def _collect_operation_status_metrics(self) -> Dict[str, Any]:
        """采集运维状态指标"""
        snapshots = self.data.get('snapshots', [])
        ilm_policies = self.data.get('ilm_policies', [])
        indices = self.data.get('indices', [])
        
        result = {
            'snapshot_status': {'value': 100, 'status': 'success'},
            'snapshot_interval_hours': {'value': 0, 'unit': '小时'},
            'snapshot_retention_count': {'value': 0, 'unit': '个'},
            'ilm_status': {'value': 100, 'status': 'normal'},
            'ilm_managed_ratio': {'value': 0, 'unit': '%'}
        }
        
        # 分析快照状态
        if snapshots:
            success_count = sum(1 for s in snapshots if s.get('state', '').lower() == 'success')
            partial_count = sum(1 for s in snapshots if s.get('state', '').lower() == 'partial')
            failed_count = sum(1 for s in snapshots if s.get('state', '').lower() == 'failed')
            
            total = len(snapshots)
            if failed_count > 0:
                result['snapshot_status'] = {'value': 0, 'status': 'failed'}
            elif partial_count > 0:
                result['snapshot_status'] = {'value': 60, 'status': 'partial'}
            else:
                result['snapshot_status'] = {'value': 100, 'status': 'success'}
            
            # 计算快照间隔（简化：假设有时间戳）
            # 这里需要根据实际数据结构调整
            result['snapshot_interval_hours']['value'] = 24  # 默认24小时
            result['snapshot_retention_count']['value'] = total
        
        # 分析ILM状态
        if indices:
            ilm_managed = sum(1 for idx in indices if idx.get('ilm_policy'))
            total_indices = len(indices)
            
            if total_indices > 0:
                managed_ratio = (ilm_managed / total_indices) * 100
                result['ilm_managed_ratio']['value'] = managed_ratio
            
            # ILM状态（简化：如果有策略则认为正常）
            if ilm_policies:
                result['ilm_status'] = {'value': 100, 'status': 'normal'}
            else:
                result['ilm_status'] = {'value': 60, 'status': 'no_policies'}
        
        return result
    
    def _check_version_consistency(self) -> int:
        """检查集群版本一致性"""
        nodes = self.data.get('nodes', [])
        
        if not nodes:
            return 100
        
        versions = set()
        for node in nodes:
            version = node.get('version')
            if version:
                versions.add(str(version))
        
        if len(versions) <= 1:
            return 100  # 版本一致
        elif len(versions) <= 2:
            return 60   # 部分不一致
        else:
            return 0    # 严重不一致
    
    def _get_default_node_metrics(self) -> Dict[str, Any]:
        """获取默认节点指标（无数据时）"""
        return {
            'disk_used_percent': {'value': 0, 'unit': '%'},
            'heap_used_percent': {'value': 0, 'unit': '%'},
            'cpu_percent': {'value': 0, 'unit': '%'},
            'load_average_ratio': {'value': 0, 'unit': '倍'},
            'shards_per_node': {'value': 0, 'unit': '个'},
            'http_connections': {'value': 0, 'unit': '个'}
        }
    
    def _get_default_index_metrics(self) -> Dict[str, Any]:
        """获取默认索引指标（无数据时）"""
        return {
            'index_health_status': {'value': 100, 'unit': '%'},
            'index_size_gb': {'value': 0, 'unit': 'GB'},
            'doc_count': {'value': 0, 'unit': '个'},
            'deleted_docs_percent': {'value': 0, 'unit': '%'},
            'shards_per_index': {'value': 0, 'unit': '个'},
            'segments_per_index': {'value': 0, 'unit': '个'}
        }
