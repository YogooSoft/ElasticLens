"""规则引擎基础类"""

from dataclasses import dataclass
from typing import Callable, Any, Dict
from datetime import datetime


@dataclass
class Rule:
    """规则基类"""
    id: str
    name: str
    description: str
    severity: str  # critical/warning/info
    check_function: Callable[[Any], bool]
    suggestion_generator: Callable[[Any], str]


@dataclass
class ThresholdRule(Rule):
    """阈值规则"""
    metric_name: str
    threshold_value: float
    operator: str  # gt/lt/eq/ge/le
    comparison_type: str  # absolute/percentage


@dataclass
class TriggeredRule:
    """触发的规则"""
    rule: Rule
    triggered_at: datetime
    context: Dict[str, Any]
    suggestion: str
    actual_value: Any = None


@dataclass
class RuleExecutionResult:
    """规则执行结果"""
    triggered_rules: list
    total_rules: int
    critical_count: int
    warning_count: int
    info_count: int
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'triggered_count': len(self.triggered_rules),
            'total_rules': self.total_rules,
            'critical_count': self.critical_count,
            'warning_count': self.warning_count,
            'info_count': self.info_count
        }
