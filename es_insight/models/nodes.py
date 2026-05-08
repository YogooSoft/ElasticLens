"""节点相关模型"""

from dataclasses import dataclass
from typing import List, Dict
from .common import HealthStatus


@dataclass
class NodeInfo:
    """节点信息数据结构"""
    name: str
    id: str
    ip: str
    version: str
    roles: List[str]
    is_master: bool
    disk_used_percent: float
    heap_used_percent: float
    cpu_percent: float
    load_1m: float
    load_5m: float
    load_15m: float
    shard_count: int
    cpu_cores: int = 0  # CPU 核心数
    
    # 新增：节点基本信息所需字段
    mem_total: str = "未知"  # 总内存（格式化字符串，如 "15.5gb"）
    mem_total_bytes: int = 0  # 总内存字节数
    jvm_heap_max: str = "未知"  # JVM最大堆（格式化字符串，如 "1gb"）
    jvm_heap_max_bytes: int = 0  # JVM最大堆字节数
    uptime: str = "未知"  # 启动时长（格式化字符串，如 "4.9m"）
    uptime_millis: int = 0  # 启动时长毫秒数
    disk_total: str = "未知"  # 磁盘总量（格式化字符串，如 "35.1gb"）
    disk_total_bytes: int = 0  # 磁盘总量字节数
    available_processors: int = 0  # 可用CPU核心数
    allocated_processors: int = 0  # 分配的CPU核心数
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "name": self.name,
            "id": self.id,
            "ip": self.ip,
            "version": self.version,
            "roles": self.roles,
            "is_master": self.is_master,
            "disk_used_percent": self.disk_used_percent,
            "heap_used_percent": self.heap_used_percent,
            "cpu_percent": self.cpu_percent,
            "load_1m": self.load_1m,
            "load_5m": self.load_5m,
            "load_15m": self.load_15m,
            "shard_count": self.shard_count,
            "cpu_cores": self.cpu_cores,
            # 新增字段
            "mem_total": self.mem_total,
            "mem_total_bytes": self.mem_total_bytes,
            "jvm_heap_max": self.jvm_heap_max,
            "jvm_heap_max_bytes": self.jvm_heap_max_bytes,
            "uptime": self.uptime,
            "uptime_millis": self.uptime_millis,
            "disk_total": self.disk_total,
            "disk_total_bytes": self.disk_total_bytes,
            "available_processors": self.available_processors,
            "allocated_processors": self.allocated_processors
        }


@dataclass
class ResourceAnalysisResult:
    """资源分析结果"""
    node_rankings: Dict[str, List[NodeInfo]]
    warning_nodes: List[NodeInfo]
    critical_nodes: List[NodeInfo]
    cluster_disk_trend: float  # 磁盘增长趋势（每天 GB）
    imbalance_score: float  # 不均衡度分数
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "warning_nodes_count": len(self.warning_nodes),
            "critical_nodes_count": len(self.critical_nodes),
            "imbalance_score": self.imbalance_score,
            "disk_trend_gb_per_day": self.cluster_disk_trend
        }
