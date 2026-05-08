"""集群基本信息数据模型"""

from dataclasses import dataclass


@dataclass
class ClusterBasicInfo:
    """集群基本信息"""
    cluster_name: str = ""
    status: str = ""
    nodes_count: int = 0
    indices_count: int = 0
    shards_total: int = 0
    data_nodes_count: int = 0
    master_nodes_count: int = 0
    version: str = ""
    license_type: str = ""
    hot_cold_architecture: bool = False
    hot_cold_ratio: str = "N/A"
    security_enabled: bool = False
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'cluster_name': self.cluster_name,
            'status': self.status,
            'nodes_count': self.nodes_count,
            'indices_count': self.indices_count,
            'shards_total': self.shards_total,
            'data_nodes_count': self.data_nodes_count,
            'master_nodes_count': self.master_nodes_count,
            'version': self.version,
            'license_type': self.license_type,
            'hot_cold_architecture': '有' if self.hot_cold_architecture else '无',
            'hot_cold_ratio': self.hot_cold_ratio,
            'security_enabled': '开启' if self.security_enabled else '未开启'
        }
