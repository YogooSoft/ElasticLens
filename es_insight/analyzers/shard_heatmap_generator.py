"""分片热力图数据生成器"""

from typing import List, Dict
from loguru import logger
from ..models.advanced_analysis import ShardHeatmapData


class ShardHeatmapGenerator:
    """分片热力图数据生成器"""
    
    def __init__(self, diagnostic_data: Dict):
        """
        初始化分片热力图生成器
        
        Args:
            diagnostic_data: 诊断数据字典
        """
        self.data = diagnostic_data
        # 负载指数权重配置
        self.shard_weight = 0.4
        self.cpu_weight = 0.35
        self.disk_weight = 0.25
    
    def generate_heatmap_data(self) -> List[ShardHeatmapData]:
        """
        生成分片热力图数据
        
        Returns:
            热力图数据列表
        """
        nodes = self.data.get('nodes', [])
        shards = self.data.get('shards', [])
        
        # 统计每个节点的分片信息
        node_shard_stats = self._aggregate_shard_by_node(shards)
        
        heatmap_data = []
        for node in nodes:
            try:
                node_name = node.get('name', '')
                stats = node_shard_stats.get(node_name, {})
                
                # 计算负载指数
                load_index = self._calculate_load_index(
                    shard_count=stats.get('total_shards', 0),
                    cpu=node.get('cpu_percent', 0),
                    disk=node.get('disk_used_percent', 0)
                )
                
                data = ShardHeatmapData(
                    node_name=node_name,
                    shard_count=stats.get('total_shards', 0),
                    primary_shard_count=stats.get('primary_shards', 0),
                    write_index_shards=stats.get('write_index_shards', 0),
                    load_index=load_index,
                    cpu_percent=node.get('cpu_percent', 0),
                    disk_percent=node.get('disk_used_percent', 0)
                )
                heatmap_data.append(data)
            except Exception as e:
                logger.warning(f"生成节点 {node.get('name', 'unknown')} 热力图数据失败: {e}")
                continue
        
        return heatmap_data
    
    def _aggregate_shard_by_node(self, shards: List[Dict]) -> Dict:
        """
        按节点聚合分片统计
        
        Args:
            shards: 分片数据列表
            
        Returns:
            按节点聚合的统计数据
        """
        stats = {}
        
        for shard in shards:
            node = shard.get('node', '')
            if not node:
                continue
                
            if node not in stats:
                stats[node] = {
                    'total_shards': 0,
                    'primary_shards': 0,
                    'write_index_shards': 0
                }
            
            stats[node]['total_shards'] += 1
            if shard.get('prirep') == 'p':
                stats[node]['primary_shards'] += 1
            
            # 简化处理: 假设所有分片都属于写索引
            # 实际应该从索引元数据判断是否为写索引
            stats[node]['write_index_shards'] += 1
        
        return stats
    
    def _calculate_load_index(self, shard_count: int, 
                             cpu: float, disk: float) -> float:
        """
        计算节点负载指数
        
        Args:
            shard_count: 分片数量
            cpu: CPU使用率百分比
            disk: 磁盘使用率百分比
            
        Returns:
            负载指数 (0-100)
        """
        # 归一化到 0-100
        # 假设1000个分片为满载
        normalized_shard = min(shard_count / 1000 * 100, 100)
        normalized_cpu = min(cpu, 100)
        normalized_disk = min(disk, 100)
        
        load_index = (normalized_shard * self.shard_weight + 
                     normalized_cpu * self.cpu_weight + 
                     normalized_disk * self.disk_weight)
        
        return round(load_index, 2)
