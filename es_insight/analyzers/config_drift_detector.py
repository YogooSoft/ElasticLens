"""配置漂移检测器"""

from typing import List, Dict, Any, Optional
from loguru import logger
from ..models.advanced_analysis import ConfigDrift


class ConfigurationDriftDetector:
    """配置漂移检测器"""
    
    # 需要检查的关键配置项
    CRITICAL_PARAMS = [
        'thread_pool.search.size',
        'thread_pool.write.size',
        'indices.queries.cache.size',
        'indices.fielddata.cache.size',
        'indices.memory.index_buffer_size',
        'cluster.routing.allocation.disk.watermark.low',
        'cluster.routing.allocation.disk.watermark.high',
        'cluster.routing.allocation.disk.watermark.flood_stage'
    ]
    
    def __init__(self, diagnostic_data: Dict):
        """
        初始化配置漂移检测器
        
        Args:
            diagnostic_data: 诊断数据字典
        """
        self.data = diagnostic_data
    
    def detect_drifts(self) -> List[ConfigDrift]:
        """
        检测配置漂移
        
        Returns:
            配置漂移列表
        """
        nodes = self.data.get('nodes', [])
        
        if not nodes:
            logger.warning("节点数据不存在或为空")
            return []
        
        drifts = []
        
        for param in self.CRITICAL_PARAMS:
            try:
                drift = self._check_parameter(param, nodes)
                if drift:
                    drifts.append(drift)
            except Exception as e:
                logger.warning(f"检查参数 {param} 时出错: {e}")
                continue
        
        return drifts
    
    def _check_parameter(self, param: str, 
                        nodes: List[Dict]) -> Optional[ConfigDrift]:
        """
        检查单个参数的配置一致性
        
        Args:
            param: 配置参数路径(点号分隔)
            nodes: 节点列表
            
        Returns:
            配置漂移对象,如果没有漂移则返回 None
        """
        values_by_node = {}
        
        for node in nodes:
            node_name = node.get('name', '')
            settings = node.get('settings', {})
            
            if not settings:
                continue
            
            # 从嵌套配置中提取参数值
            value = self._get_nested_value(settings, param)
            if value is not None:
                values_by_node[node_name] = value
        
        if len(values_by_node) <= 1:
            return None  # 只有一个值或没有值,不存在漂移
        
        # 找出主流值(出现次数最多的)
        value_counts = {}
        for value in values_by_node.values():
            # 将值转换为字符串以便比较
            value_str = str(value)
            value_counts[value_str] = value_counts.get(value_str, 0) + 1
        
        majority_value_str = max(value_counts, key=value_counts.get)
        
        # 找出不一致的节点
        drifted_nodes = [
            {'node_name': name, 'actual_value': value}
            for name, value in values_by_node.items()
            if str(value) != majority_value_str
        ]
        
        if not drifted_nodes:
            return None
        
        # 确定严重程度
        severity = self._determine_severity(param, len(drifted_nodes), len(nodes))
        
        return ConfigDrift(
            parameter_name=param,
            expected_value=majority_value_str,
            drifted_nodes=drifted_nodes,
            severity=severity
        )
    
    def _get_nested_value(self, config: Dict, path: str) -> Any:
        """
        从嵌套字典中获取值
        
        Args:
            config: 配置字典
            path: 点号分隔的路径,如 'thread_pool.search.size'
            
        Returns:
            配置值,如果路径不存在则返回 None
        """
        keys = path.split('.')
        current = config
        
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
                if current is None:
                    return None
            else:
                return None
        
        return current
    
    def _determine_severity(self, param: str, 
                           drifted_count: int, 
                           total_count: int) -> str:
        """
        确定漂移严重程度
        
        Args:
            param: 参数名
            drifted_count: 漂移节点数
            total_count: 总节点数
            
        Returns:
            严重程度: critical/warning/info
        """
        ratio = drifted_count / total_count if total_count > 0 else 0
        
        if ratio > 0.5:
            return 'critical'
        elif ratio > 0.2:
            return 'warning'
        else:
            return 'info'
