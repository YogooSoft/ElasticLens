"""分片分配失败分析器"""

from typing import List, Dict, Optional
from loguru import logger
from ..models.advanced_analysis import ShardAllocationFailure


class ShardAllocationAnalyzer:
    """分片分配失败分析器"""
    
    def __init__(self, diagnostic_data: Dict):
        """
        初始化分片分配失败分析器
        
        Args:
            diagnostic_data: 诊断数据字典
        """
        self.data = diagnostic_data
    
    def analyze_failures(self) -> List[ShardAllocationFailure]:
        """
        分析分片分配失败
        
        Returns:
            分片分配失败列表
        """
        allocation_explain = self.data.get('allocation_explain', {})
        
        if not allocation_explain:
            logger.debug("allocation_explain 数据不存在或为空")
            return []
        
        failures = []
        
        try:
            # 处理单个分片的解释
            if 'index' in allocation_explain:
                failure = self._parse_single_failure(allocation_explain)
                if failure:
                    failures.append(failure)
            # 处理多个分片的解释
            elif isinstance(allocation_explain, list):
                for explain in allocation_explain:
                    failure = self._parse_single_failure(explain)
                    if failure:
                        failures.append(failure)
        except Exception as e:
            logger.error(f"解析分片分配失败数据时出错: {e}")
        
        return failures
    
    def _parse_single_failure(self, explain: Dict) -> Optional[ShardAllocationFailure]:
        """
        解析单个分片的分配失败原因
        
        Args:
            explain: 分片分配解释数据
            
        Returns:
            分片分配失败对象,如果没有失败原因则返回 None
        """
        index = explain.get('index', '')
        shard = explain.get('shard', 0)
        current_node = explain.get('current_node')
        
        # 提取失败原因
        reasons = []
        decision_path = []
        
        # 分析未分配原因
        unassigned_info = explain.get('unassigned_info', {})
        if unassigned_info:
            reason = unassigned_info.get('reason', '')
            if reason:
                reasons.append(f"未分配原因: {reason}")
        
        # 分析节点决策
        node_decisions = explain.get('node_allocation_decisions', [])
        if node_decisions:
            for decision in node_decisions:
                node_name = decision.get('node_name', '')
                deciders = decision.get('deciders', [])
                
                for decider in deciders:
                    if decider.get('decision') == 'NO':
                        explanation = decider.get('explanation', '')
                        if explanation:
                            reasons.append(f"节点 {node_name}: {explanation}")
                            
                            decision_path.append({
                                'node': node_name,
                                'decider': decider.get('decider', ''),
                                'decision': 'DENIED',
                                'reason': explanation
                            })
        
        if not reasons:
            return None
        
        return ShardAllocationFailure(
            index_name=index,
            shard_id=shard,
            current_node=current_node,
            failure_reasons=reasons,
            decision_path=decision_path
        )
