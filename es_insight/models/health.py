"""集群健康相关模型"""

from dataclasses import dataclass
from typing import List
from .common import HealthStatus


@dataclass
class ClusterHealthData:
    """集群健康数据结构"""
    cluster_name: str
    status: HealthStatus
    number_of_nodes: int
    number_of_data_nodes: int
    active_primary_shards: int
    active_shards: int
    relocating_shards: int
    initializing_shards: int
    unassigned_shards: int
    active_shards_percent: float
    timed_out: bool
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "cluster_name": self.cluster_name,
            "status": self.status.value,
            "number_of_nodes": self.number_of_nodes,
            "number_of_data_nodes": self.number_of_data_nodes,
            "active_primary_shards": self.active_primary_shards,
            "active_shards": self.active_shards,
            "relocating_shards": self.relocating_shards,
            "initializing_shards": self.initializing_shards,
            "unassigned_shards": self.unassigned_shards,
            "active_shards_percent": self.active_shards_percent,
            "timed_out": self.timed_out
        }


@dataclass
class HealthAssessmentResult:
    """健康度评估结果"""
    total_score: float  # 0-100
    health_level: str   # excellent/good/warning/critical
    issues: List
    recommendations: List[str]
    detailed_alerts: List[dict] = None  # 新增：详细告警列表（规则引擎生成）
    
    def __post_init__(self):
        """后处理，确保 detailed_alerts 不为 None"""
        if self.detailed_alerts is None:
            self.detailed_alerts = []
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "total_score": self.total_score,
            "health_level": self.health_level,
            "issues_count": len(self.issues),
            "recommendations_count": len(self.recommendations),
            "detailed_alerts_count": len(self.detailed_alerts)
        }
