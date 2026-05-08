"""健康解析器单元测试"""

import pytest
from es_insight.parsers.health_parser import ClusterHealthParser
from es_insight.models import HealthStatus


class TestClusterHealthParser:
    
    def test_parse_valid_json(self):
        """测试解析有效的 JSON"""
        parser = ClusterHealthParser.__new__(ClusterHealthParser)
        
        sample_data = {
            "cluster_name": "test-cluster",
            "status": "green",
            "number_of_nodes": 3,
            "number_of_data_nodes": 2,
            "active_primary_shards": 10,
            "active_shards": 20,
            "relocating_shards": 0,
            "initializing_shards": 0,
            "unassigned_shards": 0,
            "active_shards_percent": 100.0,
            "timed_out": False
        }
        
        result = parser.parse_dict(sample_data)
        
        assert result.cluster_name == "test-cluster"
        assert result.status == HealthStatus.GREEN
        assert result.number_of_nodes == 3
        assert result.active_shards_percent == 100.0
    
    def test_parse_missing_fields(self):
        """测试解析缺失字段的 JSON"""
        parser = ClusterHealthParser.__new__(ClusterHealthParser)
        
        incomplete_data = {
            "cluster_name": "test-cluster",
            "status": "yellow"
            # 缺少其他字段
        }
        
        result = parser.parse_dict(incomplete_data)
        
        assert result.cluster_name == "test-cluster"
        assert result.status == HealthStatus.YELLOW
        assert result.number_of_nodes == 0  # 默认值
