"""预定义规则库"""

from typing import Any
from .base import Rule, ThresholdRule


def create_predefined_rules() -> list:
    """创建预定义规则"""
    rules = []
    
    # 规则 1: 集群状态为红色
    rules.append(Rule(
        id="CLUSTER_STATUS_RED",
        name="集群状态为红色",
        description="存在主分片未分配",
        severity="critical",
        check_function=lambda data: data.health.status.value == "red",
        suggestion_generator=lambda data: "立即检查未分配分片原因，优先恢复主分片"
    ))
    
    # 规则 2: 集群状态为黄色
    rules.append(Rule(
        id="CLUSTER_STATUS_YELLOW",
        name="集群状态为黄色",
        description="存在副本分片未分配",
        severity="warning",
        check_function=lambda data: data.health.status.value == "yellow",
        suggestion_generator=lambda data: "检查副本分片未分配原因，考虑扩容或调整副本数"
    ))
    
    # 规则 3: 磁盘使用率过高
    rules.append(ThresholdRule(
        id="DISK_USAGE_HIGH",
        name="磁盘使用率过高",
        description="节点磁盘使用率超过阈值",
        severity="warning",
        metric_name="disk_used_percent",
        threshold_value=85.0,
        operator="gt",
        comparison_type="percentage",
        check_function=lambda data: any(
            n.disk_used_percent > 85.0 for n in data.nodes
        ),
        suggestion_generator=lambda data: "建议清理旧索引或扩容磁盘"
    ))
    
    # 规则 4: 未分配分片过多
    rules.append(ThresholdRule(
        id="UNASSIGNED_SHARDS_HIGH",
        name="未分配分片过多",
        description="未分配分片数量超过阈值",
        severity="critical",
        metric_name="unassigned_shards",
        threshold_value=10.0,
        operator="gt",
        comparison_type="absolute",
        check_function=lambda data: data.health.unassigned_shards > 10,
        suggestion_generator=lambda data: "立即调查分片未分配原因并修复"
    ))
    
    return rules
