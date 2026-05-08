"""资源分析引擎"""

from typing import List, Dict
from loguru import logger

from es_insight.models import NodeInfo, ResourceAnalysisResult
from es_insight.config import ThresholdConfig


class ResourceAnalyzer:
    """资源分析器"""
    
    def __init__(self, threshold_config: ThresholdConfig = None):
        """
        初始化资源分析器
        
        Args:
            threshold_config: 阈值配置
        """
        self.threshold_config = threshold_config or ThresholdConfig()
        logger.info("资源分析器初始化完成")
    
    def analyze_nodes(
        self, 
        nodes: List[NodeInfo]
    ) -> ResourceAnalysisResult:
        """分析节点资源使用情况"""
        logger.info(f"开始分析 {len(nodes)} 个节点的资源使用情况")
        
        # 1. 磁盘使用率排名
        disk_ranking = sorted(
            nodes, 
            key=lambda n: n.disk_used_percent, 
            reverse=True
        )
        
        # 2. 内存使用率排名
        heap_ranking = sorted(
            nodes,
            key=lambda n: n.heap_used_percent,
            reverse=True
        )
        
        # 3. CPU 使用率排名
        cpu_ranking = sorted(
            nodes,
            key=lambda n: n.cpu_percent,
            reverse=True
        )
        
        # 4. 识别警告和严重节点
        warning_nodes = []
        critical_nodes = []
        
        for node in nodes:
            is_warning = False
            is_critical = False
            
            # 检查磁盘
            disk_warn = self.threshold_config.get_threshold(
                'node', 'disk', 'warning')
            disk_crit = self.threshold_config.get_threshold(
                'node', 'disk', 'critical')
            
            if disk_crit and node.disk_used_percent >= disk_crit:
                is_critical = True
            elif disk_warn and node.disk_used_percent >= disk_warn:
                is_warning = True
            
            # 检查内存
            heap_warn = self.threshold_config.get_threshold(
                'node', 'heap', 'warning')
            heap_crit = self.threshold_config.get_threshold(
                'node', 'heap', 'critical')
            
            if heap_crit and node.heap_used_percent >= heap_crit:
                is_critical = True
            elif heap_warn and node.heap_used_percent >= heap_warn:
                is_warning = True
            
            if is_critical:
                critical_nodes.append(node)
            elif is_warning:
                warning_nodes.append(node)
        
        # 5. 计算不均衡度
        imbalance_score = self._calculate_imbalance(nodes)
        
        # 6. 磁盘趋势（简化版本，实际需要历史数据）
        cluster_disk_trend = 0.0
        
        result = ResourceAnalysisResult(
            node_rankings={
                'disk': disk_ranking,
                'heap': heap_ranking,
                'cpu': cpu_ranking
            },
            warning_nodes=warning_nodes,
            critical_nodes=critical_nodes,
            cluster_disk_trend=cluster_disk_trend,
            imbalance_score=imbalance_score
        )
        
        logger.info(
            f"资源分析完成：警告节点 {len(warning_nodes)} 个，"
            f"严重节点 {len(critical_nodes)} 个"
        )
        
        return result
    
    def _calculate_imbalance(self, nodes: List[NodeInfo]) -> float:
        """计算资源不均衡度"""
        if len(nodes) < 2:
            return 0.0
        
        # 计算磁盘使用率的标准差
        disk_values = [n.disk_used_percent for n in nodes]
        mean_disk = sum(disk_values) / len(disk_values)
        variance = sum((x - mean_disk) ** 2 for x in disk_values) / len(disk_values)
        std_dev = variance ** 0.5
        
        # 归一化到 0-1 范围
        imbalance = min(1.0, std_dev / 20)  # 假设 20% 标准差为完全不均衡
        
        return round(imbalance, 2)
