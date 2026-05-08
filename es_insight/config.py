"""配置管理模块"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

from es_insight.exceptions import ConfigurationError


class Config:
    """配置管理类"""
    
    DEFAULT_CONFIG = {
        "output": {
            "formats": ["html", "markdown", "json"],
            "directory": "./reports",
            "filename_pattern": "inspection_report_{timestamp}"
        },
        "html": {
            "include_charts": True,
            "chart_library": "echarts",
            "theme": "light"
        },
        "scoring": {
            "weights": {
                "cluster_status": 0.4,
                "shard_allocation": 0.3,
                "node_availability": 0.2,
                "shard_migration": 0.1
            },
            "levels": {
                "excellent": 90,
                "good": 75,
                "warning": 60
            }
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self.DEFAULT_CONFIG.copy()
        
        if config_path:
            self._load_from_file(config_path)
            
        logger.info("配置初始化完成")
    
    def _load_from_file(self, path: str):
        """从文件加载配置"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f)
                
            # 深度合并配置
            self._merge_config(file_config)
            logger.info(f"成功加载配置文件：{path}")
            
        except FileNotFoundError:
            raise ConfigurationError(f"配置文件不存在：{path}")
        except yaml.YAMLError as e:
            raise ConfigurationError(f"配置文件解析失败：{e}")
    
    def _merge_config(self, file_config: Dict):
        """合并配置"""
        for key, value in file_config.items():
            if isinstance(value, dict) and key in self.config:
                self.config[key].update(value)
            else:
                self.config[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
            
        config[keys[-1]] = value


class AssessmentConfig:
    """评估配置"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        
    @property
    def weights(self) -> Dict[str, float]:
        """获取权重配置"""
        return self.config.get("scoring.weights", {})
    
    @property
    def levels(self) -> Dict[str, float]:
        """获取等级阈值"""
        return self.config.get("scoring.levels", {})


class ThresholdConfig:
    """阈值配置类"""
    
    DEFAULT_THRESHOLDS = {
        "cluster": {
            "status": {
                "yellow": "warning",
                "red": "critical"
            },
            "unassigned_shards": {
                "warning": 1,
                "critical": 10
            },
            "active_shards_percent": {
                "warning": 95,
                "critical": 90
            }
        },
        "node": {
            "disk": {
                "warning": 75,
                "critical": 85
            },
            "heap": {
                "warning": 75,
                "critical": 90
            },
            "cpu": {
                "warning": 70,
                "critical": 90
            }
        }
    }
    
    def __init__(self, threshold_path: Optional[str] = None):
        """
        初始化阈值配置
        
        Args:
            threshold_path: 阈值配置文件路径
        """
        self.thresholds = self.DEFAULT_THRESHOLDS.copy()
        
        if threshold_path:
            self._load_from_file(threshold_path)
    
    def _load_from_file(self, path: str):
        """从文件加载阈值"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                file_thresholds = yaml.safe_load(f)
                
            # 合并阈值
            for category, items in file_thresholds.items():
                if category in self.thresholds:
                    self.thresholds[category].update(items)
                else:
                    self.thresholds[category] = items
                    
        except Exception as e:
            raise ConfigurationError(f"加载阈值配置失败：{e}")
    
    def get_threshold(self, category: str, metric: str, level: str) -> float:
        """
        获取阈值
        
        Args:
            category: 类别 (cluster/node/index)
            metric: 指标名
            level: 级别 (warning/critical)
            
        Returns:
            阈值
        """
        try:
            return self.thresholds[category][metric][level]
        except KeyError:
            logger.warning(f"未找到阈值配置：{category}.{metric}.{level}")
            return None
