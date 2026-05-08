"""规则相关模型"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum


class RuleSeverity(Enum):
    """规则严重程度"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class RuleViolation:
    """规则违反记录"""
    rule_id: str
    rule_name: str
    message: str
    severity: RuleSeverity
    affected_items: List[str] = field(default_factory=list)
    suggestion: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RuleExecutionResult:
    """规则执行结果"""
    total_rules: int = 0
    triggered_rules: List[RuleViolation] = field(default_factory=list)
    passed_rules: List[str] = field(default_factory=list)
    
    @property
    def critical_count(self) -> int:
        """严重违规数量"""
        return sum(1 for v in self.triggered_rules if v.severity == RuleSeverity.CRITICAL)
    
    @property
    def warning_count(self) -> int:
        """警告违规数量"""
        return sum(1 for v in self.triggered_rules if v.severity == RuleSeverity.WARNING)
    
    @property
    def info_count(self) -> int:
        """提示违规数量"""
        return sum(1 for v in self.triggered_rules if v.severity == RuleSeverity.INFO)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "total_rules": self.total_rules,
            "triggered_count": len(self.triggered_rules),
            "passed_count": len(self.passed_rules),
            "critical_count": self.critical_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "violations": [
                {
                    "rule_id": v.rule_id,
                    "rule_name": v.rule_name,
                    "message": v.message,
                    "severity": v.severity.value,
                    "suggestion": v.suggestion
                }
                for v in self.triggered_rules
            ]
        }
