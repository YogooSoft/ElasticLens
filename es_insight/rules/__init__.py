"""规则引擎包"""

from .base import Rule, ThresholdRule, TriggeredRule, RuleExecutionResult
from .predefined import create_predefined_rules
from .engine import RulesEngine

# 兼容旧版本
RuleEngine = RulesEngine

__all__ = [
    "Rule",
    "ThresholdRule",
    "TriggeredRule",
    "RuleExecutionResult",
    "create_predefined_rules",
    "RulesEngine",
    "RuleEngine",  # 别名
]
