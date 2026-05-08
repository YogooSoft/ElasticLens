"""JVM 内存分析器"""

from typing import List, Dict, Optional
from loguru import logger
from ..models.advanced_analysis import JVMMemoryProfile


class JVMMemoryAnalyzer:
    """JVM 内存分析器"""
    
    def __init__(self, diagnostic_data: Dict):
        """
        初始化 JVM 内存分析器
        
        Args:
            diagnostic_data: 诊断数据字典
        """
        self.data = diagnostic_data
    
    def analyze_all_nodes(self) -> List[JVMMemoryProfile]:
        """
        分析所有节点的 JVM 内存
        
        Returns:
            JVM 内存画像列表
        """
        nodes_stats = self.data.get('nodes_stats', {})
        nodes_dict = nodes_stats.get('nodes', {})
        
        if not nodes_dict:
            logger.warning("nodes_stats 数据不存在或为空")
            return []
        
        profiles = []
        for node_id, stats in nodes_dict.items():
            try:
                profile = self._analyze_node_jvm(node_id, stats)
                if profile:
                    profiles.append(profile)
            except Exception as e:
                logger.warning(f"分析节点 {node_id} JVM 内存失败: {e}")
                continue
        
        return profiles
    
    def _analyze_node_jvm(self, node_id: str, 
                         stats: Dict) -> Optional[JVMMemoryProfile]:
        """
        分析单个节点的 JVM 内存
        
        Args:
            node_id: 节点ID
            stats: 节点统计数据
            
        Returns:
            JVM 内存画像,如果数据不足则返回 None
        """
        jvm = stats.get('jvm', {})
        mem = jvm.get('mem', {})
        
        if not mem:
            logger.debug(f"节点 {node_id} 缺少 JVM 内存数据")
            return None
        
        node_name = stats.get('name', node_id)
        
        # 提取内存数据
        heap_used = mem.get('heap_used_in_bytes', 0)
        heap_max = mem.get('heap_max_in_bytes', 0)
        heap_percent = mem.get('heap_used_percent', 0)
        
        # 内存池数据
        pools = mem.get('pools', {})
        old_gen = pools.get('old', {}).get('used_in_bytes', 0)
        young_gen = pools.get('young', {}).get('used_in_bytes', 0)
        
        # 其他内存使用
        fielddata = mem.get('fielddata', {}).get('memory_size_in_bytes', 0)
        segments = stats.get('indices', {}).get('segments', {}).get('memory_in_bytes', 0)
        non_heap = mem.get('non_heap_used_in_bytes', 0)
        
        return JVMMemoryProfile(
            node_name=node_name,
            heap_used_bytes=heap_used,
            heap_max_bytes=heap_max,
            heap_used_percent=heap_percent,
            old_gen_bytes=old_gen,
            young_gen_bytes=young_gen,
            fielddata_bytes=fielddata,
            segments_bytes=segments,
            non_heap_bytes=non_heap
        )
