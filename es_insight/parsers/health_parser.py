"""集群健康数据解析器"""

from typing import Dict
from loguru import logger

from es_insight.models import ClusterHealthData, HealthStatus
from es_insight.exceptions import ParseError
from .base import DiagnosticFileParser


class ClusterHealthParser(DiagnosticFileParser):
    """集群健康文件解析器"""
    
    def parse(self) -> ClusterHealthData:
        """
        解析 cluster_health.json
        
        Returns:
            ClusterHealthData 对象
        """
        try:
            # 解压文件
            self.extract()
            
            # 解析 JSON
            data = self.parse_json("cluster_health.json")
            
            # 构建数据对象
            health_data = ClusterHealthData(
                cluster_name=data.get("cluster_name", "unknown"),
                status=HealthStatus(data.get("status", "red")),
                number_of_nodes=data.get("number_of_nodes", 0),
                number_of_data_nodes=data.get("number_of_data_nodes", 0),
                active_primary_shards=data.get("active_primary_shards", 0),
                active_shards=data.get("active_shards", 0),
                relocating_shards=data.get("relocating_shards", 0),
                initializing_shards=data.get("initializing_shards", 0),
                unassigned_shards=data.get("unassigned_shards", 0),
                active_shards_percent=data.get("active_shards_percent_as_number", data.get("active_shards_percent", 0.0)),
                timed_out=data.get("timed_out", False)
            )
            
            logger.info(f"成功解析集群健康数据：{health_data.cluster_name}, "
                       f"状态：{health_data.status.value}")
            
            return health_data
            
        except Exception as e:
            logger.error(f"解析集群健康数据失败：{e}")
            raise ParseError(f"解析集群健康数据失败：{str(e)}")
        finally:
            self.cleanup()
    
    def parse_dict(self, data: Dict) -> ClusterHealthData:
        """
        从字典直接解析（用于测试）
        
        Args:
            data: 健康数据字典
            
        Returns:
            ClusterHealthData 对象
        """
        return ClusterHealthData(
            cluster_name=data.get("cluster_name", "unknown"),
            status=HealthStatus(data.get("status", "red")),
            number_of_nodes=data.get("number_of_nodes", 0),
            number_of_data_nodes=data.get("number_of_data_nodes", 0),
            active_primary_shards=data.get("active_primary_shards", 0),
            active_shards=data.get("active_shards", 0),
            relocating_shards=data.get("relocating_shards", 0),
            initializing_shards=data.get("initializing_shards", 0),
            unassigned_shards=data.get("unassigned_shards", 0),
            active_shards_percent=data.get("active_shards_percent_as_number", data.get("active_shards_percent", 0.0)),
            timed_out=data.get("timed_out", False)
        )
