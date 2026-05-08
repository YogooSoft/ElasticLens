"""线程池分析器"""

from typing import List, Dict
from loguru import logger
from ..models.advanced_analysis import ThreadPoolStatus


class ThreadPoolAnalyzer:
    """线程池分析器"""
    
    def __init__(self, diagnostic_data: Dict):
        """
        初始化线程池分析器
        
        Args:
            diagnostic_data: 诊断数据字典
        """
        self.data = diagnostic_data
        # 可配置的阈值
        self.queue_threshold = 1000
        self.rejection_threshold = 100
    
    def analyze_thread_pools(self) -> List[ThreadPoolStatus]:
        """
        分析所有节点的线程池状态
        
        Returns:
            线程池状态列表
        """
        thread_pools = self.data.get('thread_pools', [])
        
        # 兼容性处理: 如果 thread_pools 不存在,尝试从 nodes_stats 中提取
        if not thread_pools:
            thread_pools = self._extract_from_nodes_stats()
        
        results = []
        for pool in thread_pools:
            try:
                status = ThreadPoolStatus(
                    node_name=pool.get('node_name', ''),
                    pool_name=pool.get('name', ''),
                    queue_size=pool.get('queue_size', 0),
                    rejected_count=pool.get('rejected', 0),
                    active_threads=pool.get('active', 0),
                    completed_tasks=pool.get('completed', 0),
                    is_overloaded=self._is_overloaded(pool)
                )
                results.append(status)
            except Exception as e:
                logger.warning(f"解析线程池数据失败: {e}")
                continue
        
        return results
    
    def _is_overloaded(self, pool: Dict) -> bool:
        """
        判断线程池是否过载
        
        Args:
            pool: 线程池数据字典
            
        Returns:
            是否过载
        """
        queue_size = pool.get('queue_size', 0)
        rejected = pool.get('rejected', 0)
        
        return (queue_size > self.queue_threshold or 
                rejected > self.rejection_threshold)
    
    def get_critical_pools(self) -> List[ThreadPoolStatus]:
        """
        获取过载的线程池
        
        Returns:
            过载的线程池列表
        """
        all_pools = self.analyze_thread_pools()
        return [p for p in all_pools if p.is_overloaded]
    
    def _extract_from_nodes_stats(self) -> List[Dict]:
        """
        从 nodes_stats 中提取线程池数据(兼容性处理)
        
        Returns:
            线程池数据列表
        """
        thread_pools = []
        nodes_stats = self.data.get('nodes_stats', {})
        nodes = nodes_stats.get('nodes', {})
        
        for node_id, stats in nodes.items():
            node_name = stats.get('name', node_id)
            thread_pool_stats = stats.get('thread_pool', {})
            
            for pool_name, pool_data in thread_pool_stats.items():
                if isinstance(pool_data, dict):
                    thread_pools.append({
                        'node_name': node_name,
                        'name': pool_name,
                        'queue_size': pool_data.get('queue', 0),
                        'rejected': pool_data.get('rejected', 0),
                        'active': pool_data.get('active', 0),
                        'completed': pool_data.get('completed', 0)
                    })
        
        return thread_pools
