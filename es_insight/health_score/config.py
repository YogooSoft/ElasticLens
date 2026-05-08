"""健康评分配置管理模块

负责加载和管理健康评分的阈值和权重配置
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger


class HealthScoreConfig:
    """健康评分配置管理器"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录路径，默认为项目configs目录
        """
        if config_dir is None:
            # 默认使用项目configs目录
            self.config_dir = Path(__file__).parent.parent.parent / 'configs'
        else:
            self.config_dir = Path(config_dir)
        
        self.thresholds = {}
        self.weights = {}
        
        # 加载默认配置
        self._load_default_config()
        
        # 尝试加载自定义配置
        self._load_custom_config()
    
    def _load_default_config(self):
        """加载默认配置"""
        # 默认维度权重（根据设计文档）
        self.weights = {
            'dimensions': {
                'cluster_health': 0.25,
                'node_performance': 0.25,
                'index_status': 0.20,
                'performance_metrics': 0.15,
                'security_config': 0.10,
                'operation_status': 0.05
            },
            # 各维度内指标的默认权重将在metrics.py中定义
        }
        
        # 默认阈值配置（根据设计文档）
        self.thresholds = {
            # 集群健康指标
            'cluster_health': {
                'status': {
                    'green': 100,
                    'yellow': 60,
                    'red': 0
                },
                'active_shards_percent': {
                    'normal': 95,
                    'warning': 90,
                    'critical': 0
                },
                'unassigned_shards': {
                    'normal': 0,
                    'warning': 9,
                    'critical': 10
                },
                'cluster_settings_consistency': {
                    'consistent': 100,
                    'partial': 60,
                    'inconsistent': 0
                },
                'cluster_version_consistency': {
                    'consistent': 100,
                    'partial': 60,
                    'inconsistent': 0
                }
            },
            # 节点性能指标
            'node_performance': {
                'disk_used_percent': {
                    'normal': 70,
                    'warning': 85,
                    'critical': 100
                },
                'heap_used_percent': {
                    'normal': 70,
                    'warning': 85,
                    'critical': 100
                },
                'cpu_percent': {
                    'normal': 60,
                    'warning': 90,
                    'critical': 100
                },
                'load_average_ratio': {
                    'normal': 1.5,
                    'warning': 3.0,
                    'critical': 10.0
                },
                'shards_per_node': {
                    'normal': 500,
                    'warning': 1000,
                    'critical': 2000
                },
                'http_connections': {
                    'normal': 1000,
                    'warning': 5000,
                    'critical': 10000
                }
            },
            # 索引状态指标
            'index_status': {
                'index_health_status': {
                    'green': 100,
                    'yellow': 60,
                    'red': 0
                },
                'index_size_gb': {
                    'normal': 50,
                    'warning': 100,
                    'critical': 500
                },
                'doc_count': {
                    'normal': 100000000,  # 1亿
                    'warning': 500000000,  # 5亿
                    'critical': 1000000000  # 10亿
                },
                'deleted_docs_percent': {
                    'normal': 10,
                    'warning': 20,
                    'critical': 50
                },
                'shards_per_index': {
                    'normal': 50,
                    'warning': 100,
                    'critical': 500
                },
                'segments_per_index': {
                    'normal': 100,
                    'warning': 500,
                    'critical': 1000
                }
            },
            # 性能指标
            'performance_metrics': {
                'search_thread_pool_queue': {
                    'normal': 1000,
                    'warning': 5000,
                    'critical': 10000
                },
                'write_thread_pool_queue': {
                    'normal': 500,
                    'warning': 2000,
                    'critical': 5000
                },
                'bulk_thread_pool_queue': {
                    'normal': 1000,
                    'warning': 5000,
                    'critical': 10000
                },
                'search_rejection_rate': {
                    'normal': 0,
                    'warning': 10,
                    'critical': 50
                },
                'write_rejection_rate': {
                    'normal': 0,
                    'warning': 10,
                    'critical': 50
                },
                'bulk_rejection_rate': {
                    'normal': 0,
                    'warning': 10,
                    'critical': 50
                }
            },
            # 安全配置指标
            'security_config': {
                'xpack_security_enabled': {
                    'enabled': 100,
                    'disabled': 0
                },
                'default_password_set': {
                    'set': 100,
                    'not_set': 0
                },
                'anonymous_access': {
                    'disabled': 100,
                    'enabled': 0
                },
                'http_ssl_enabled': {
                    'enabled': 100,
                    'disabled': 0
                },
                'transport_ssl_enabled': {
                    'enabled': 100,
                    'disabled': 0
                }
            },
            # 运维状态指标
            'operation_status': {
                'snapshot_status': {
                    'success': 100,
                    'partial': 60,
                    'failed': 0
                },
                'snapshot_interval_hours': {
                    'normal': 48,
                    'warning': 168,
                    'critical': 720
                },
                'snapshot_retention_count': {
                    'normal': 3,
                    'warning': 1,
                    'critical': 0
                },
                'ilm_status': {
                    'normal': 100,
                    'partial_failure': 60,
                    'critical_failure': 0
                },
                'ilm_managed_ratio': {
                    'normal': 50,
                    'warning': 10,
                    'critical': 0
                }
            }
        }
        
        logger.info("已加载默认健康评分配置")
    
    def _load_custom_config(self):
        """尝试加载自定义配置文件"""
        thresholds_file = self.config_dir / 'health_score_thresholds.yaml'
        weights_file = self.config_dir / 'health_score_weights.yaml'
        
        if thresholds_file.exists():
            try:
                with open(thresholds_file, 'r', encoding='utf-8') as f:
                    custom_thresholds = yaml.safe_load(f)
                    if custom_thresholds:
                        # 深度合并配置
                        self._deep_merge(self.thresholds, custom_thresholds)
                        logger.info(f"已加载自定义阈值配置: {thresholds_file}")
            except Exception as e:
                logger.warning(f"加载自定义阈值配置失败: {e}")
        
        if weights_file.exists():
            try:
                with open(weights_file, 'r', encoding='utf-8') as f:
                    custom_weights = yaml.safe_load(f)
                    if custom_weights:
                        self._deep_merge(self.weights, custom_weights)
                        logger.info(f"已加载自定义权重配置: {weights_file}")
            except Exception as e:
                logger.warning(f"加载自定义权重配置失败: {e}")
    
    def _deep_merge(self, base: dict, override: dict):
        """
        深度合并字典
        
        Args:
            base: 基础字典
            override: 覆盖字典
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def get_threshold(self, dimension: str, metric: str) -> Dict[str, Any]:
        """
        获取指定维度和指标的阈值配置
        
        Args:
            dimension: 维度名称
            metric: 指标名称
            
        Returns:
            阈值配置字典
        """
        return self.thresholds.get(dimension, {}).get(metric, {})
    
    def get_dimension_weight(self, dimension: str) -> float:
        """
        获取指定维度的权重
        
        Args:
            dimension: 维度名称
            
        Returns:
            权重值（0-1之间）
        """
        return self.weights.get('dimensions', {}).get(dimension, 0)
    
    def get_all_thresholds(self) -> Dict[str, Any]:
        """获取所有阈值配置"""
        return self.thresholds.copy()
    
    def get_all_weights(self) -> Dict[str, Any]:
        """获取所有权重配置"""
        return self.weights.copy()
    
    def validate_config(self) -> bool:
        """
        验证配置的有效性
        
        Returns:
            配置是否有效
        """
        # 检查维度权重总和是否为1
        dimension_weights = self.weights.get('dimensions', {})
        total_weight = sum(dimension_weights.values())
        
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"维度权重总和不为1: {total_weight}")
            return False
        
        # 检查必要的维度是否存在
        required_dimensions = [
            'cluster_health',
            'node_performance', 
            'index_status',
            'performance_metrics',
            'security_config',
            'operation_status'
        ]
        
        for dim in required_dimensions:
            if dim not in dimension_weights:
                logger.warning(f"缺少必要的维度权重: {dim}")
                return False
        
        return True
