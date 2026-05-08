"""高级分析数据模型"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ThreadPoolStatus:
    """线程池状态"""
    node_name: str
    pool_name: str
    queue_size: int
    rejected_count: int
    active_threads: int
    completed_tasks: int
    is_overloaded: bool  # 是否过载


@dataclass
class ShardHeatmapData:
    """分片热力图数据"""
    node_name: str
    shard_count: int
    primary_shard_count: int
    write_index_shards: int
    load_index: float  # 负载指数 0-100
    cpu_percent: float
    disk_percent: float


@dataclass
class JVMMemoryProfile:
    """JVM 内存画像"""
    node_name: str
    heap_used_bytes: int
    heap_max_bytes: int
    heap_used_percent: float
    old_gen_bytes: int
    young_gen_bytes: int
    fielddata_bytes: int
    segments_bytes: int
    non_heap_bytes: int


@dataclass
class ConfigDrift:
    """配置漂移"""
    parameter_name: str
    expected_value: Any
    drifted_nodes: List[Dict[str, Any]] = field(default_factory=list)  # [{node_name, actual_value}]
    severity: str = "info"  # critical/warning/info


@dataclass
class ShardAllocationFailure:
    """分片分配失败原因"""
    index_name: str
    shard_id: int
    current_node: Optional[str] = None
    failure_reasons: List[str] = field(default_factory=list)
    decision_path: List[Dict[str, str]] = field(default_factory=list)  # 决策路径
