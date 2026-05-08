"""通用数据模型"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional


class HealthStatus(Enum):
    """健康状态枚举"""
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class Severity(Enum):
    """严重程度枚举"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Issue:
    """问题描述"""
    id: str
    title: str
    description: str
    severity: Severity
    suggestion: str
    affected_items: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Recommendation:
    """优化建议"""
    title: str
    description: str
    priority: str  # high/medium/low
    estimated_impact: str
    steps: List[str] = field(default_factory=list)
