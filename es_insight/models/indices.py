"""索引相关模型"""

from dataclasses import dataclass
from datetime import datetime
from typing import List
from .common import HealthStatus


@dataclass
class IndexInfo:
    """索引信息数据结构"""
    name: str
    uuid: str
    health: HealthStatus
    status: str
    primary_shards: int
    replica_shards: int
    docs_count: int
    store_size_bytes: int
    created_time: datetime
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "name": self.name,
            "uuid": self.uuid,
            "health": self.health.value,
            "status": self.status,
            "primary_shards": self.primary_shards,
            "replica_shards": self.replica_shards,
            "docs_count": self.docs_count,
            "store_size_bytes": self.store_size_bytes,
            "created_time": self.created_time.isoformat() if self.created_time else None
        }
