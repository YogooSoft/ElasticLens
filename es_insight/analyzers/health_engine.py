"""健康度评估引擎"""

from typing import List
from loguru import logger

from es_insight.models import (
    ClusterHealthData, 
    HealthAssessmentResult, 
    Issue, 
    Severity,
    HealthStatus
)
from es_insight.config import AssessmentConfig


class HealthAssessmentEngine:
    """健康度评估引擎"""
    
    def __init__(self, config: AssessmentConfig = None):
        """
        初始化评估引擎
        
        Args:
            config: 评估配置
        """
        self.config = config or AssessmentConfig()
        logger.info("健康度评估引擎初始化完成")
    
    def assess_cluster_health(
        self, 
        health_data: ClusterHealthData
    ) -> HealthAssessmentResult:
        """评估集群健康度"""
        logger.info("开始评估集群健康度")
        
        # 1. 计算集群状态得分 (40 分)
        status_score = self._calculate_status_score(health_data.status)
        
        # 2. 计算分片分配得分 (30 分)
        shard_score = self._calculate_shard_score(health_data)
        
        # 3. 计算节点在线率得分 (20 分)
        node_score = self._calculate_node_score(health_data)
        
        # 4. 计算分片迁移得分 (10 分)
        migration_score = self._calculate_migration_score(health_data)
        
        # 获取权重
        weights = self.config.get('scoring.weights', {
            'cluster_status': 0.4,
            'shard_allocation': 0.3,
            'node_availability': 0.2,
            'shard_migration': 0.1
        })
        
        # 总分
        total_score = (
            status_score * weights.get('cluster_status', 0.4) +
            shard_score * weights.get('shard_allocation', 0.3) +
            node_score * weights.get('node_availability', 0.2) +
            migration_score * weights.get('shard_migration', 0.1)
        )
        
        # 确定健康等级
        health_level = self._determine_health_level(total_score)
        
        # 识别问题
        issues = self._identify_issues(health_data)
        
        # 生成建议
        recommendations = self._generate_recommendations(health_data, issues)
        
        result = HealthAssessmentResult(
            total_score=round(total_score, 2),
            health_level=health_level,
            issues=issues,
            recommendations=recommendations
        )
        
        logger.info(f"健康度评估完成：{total_score}分，等级：{health_level}")
        return result
    
    def _calculate_status_score(self, status: HealthStatus) -> float:
        """计算集群状态得分"""
        if status == HealthStatus.GREEN:
            return 100.0
        elif status == HealthStatus.YELLOW:
            return 50.0
        else:  # RED
            return 0.0
    
    def _calculate_shard_score(self, health_data: ClusterHealthData) -> float:
        """计算分片分配得分"""
        if health_data.active_shards_percent >= 100:
            return 100.0
        elif health_data.active_shards_percent >= 95:
            return 80.0
        elif health_data.active_shards_percent >= 90:
            return 60.0
        else:
            return max(0, health_data.active_shards_percent)
    
    def _calculate_node_score(self, health_data: ClusterHealthData) -> float:
        """计算节点在线率得分（简化版）"""
        if health_data.number_of_nodes > 0:
            return 100.0
        return 0.0
    
    def _calculate_migration_score(self, health_data: ClusterHealthData) -> float:
        """计算分片迁移得分"""
        migrating = (
            health_data.relocating_shards +
            health_data.initializing_shards
        )
        
        if migrating == 0:
            return 100.0
        elif migrating <= 5:
            return 80.0
        elif migrating <= 10:
            return 60.0
        else:
            return max(0, 100 - migrating * 2)
    
    def _determine_health_level(self, score: float) -> str:
        """确定健康等级"""
        levels = self.config.get('scoring.levels', {
            'excellent': 90,
            'good': 75,
            'warning': 60
        })
        
        if score >= levels.get('excellent', 90):
            return 'excellent'
        elif score >= levels.get('good', 75):
            return 'good'
        elif score >= levels.get('warning', 60):
            return 'warning'
        else:
            return 'critical'
    
    def _identify_issues(self, health_data: ClusterHealthData) -> List[Issue]:
        """识别问题"""
        issues = []
        
        # 检查集群状态
        if health_data.status == HealthStatus.RED:
            issues.append(Issue(
                id="HEALTH_001",
                title="集群状态为红色",
                description="存在主分片未分配，可能导致数据不可用",
                severity=Severity.CRITICAL,
                suggestion="立即检查未分配分片原因，优先恢复主分片",
                metadata={
                    "unassigned_shards": health_data.unassigned_shards
                }
            ))
        elif health_data.status == HealthStatus.YELLOW:
            issues.append(Issue(
                id="HEALTH_002",
                title="集群状态为黄色",
                description="存在副本分片未分配",
                severity=Severity.WARNING,
                suggestion="检查副本分片未分配原因，考虑扩容或调整副本数"
            ))
        
        # 检查未分配分片
        if health_data.unassigned_shards > 0:
            severity = Severity.CRITICAL if health_data.unassigned_shards >= 10 else Severity.WARNING
            issues.append(Issue(
                id="HEALTH_003",
                title=f"存在 {health_data.unassigned_shards} 个未分配分片",
                description="分片未分配可能影响集群性能和数据冗余",
                severity=severity,
                suggestion="使用 _cluster/allocation/explain API 查看未分配原因"
            ))
        
        # 检查分片迁移
        if health_data.relocating_shards > 0:
            issues.append(Issue(
                id="HEALTH_004",
                title=f"有 {health_data.relocating_shards} 个分片正在迁移",
                description="分片迁移会消耗集群资源",
                severity=Severity.INFO,
                suggestion="监控迁移进度，避免在业务高峰期迁移"
            ))
        
        return issues
    
    def _generate_recommendations(
        self, 
        health_data: ClusterHealthData,
        issues: List[Issue]
    ) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # 基于问题生成建议
        critical_count = sum(1 for i in issues if i.severity == Severity.CRITICAL)
        if critical_count > 0:
            recommendations.append(
                f"发现 {critical_count} 个严重问题，建议立即处理"
            )
        
        # 常规建议
        if health_data.active_shards_percent < 100:
            recommendations.append(
                "分片未完全分配，建议检查磁盘空间和分片分配策略"
            )
        
        if not recommendations:
            recommendations.append("集群状态良好，继续保持定期巡检")
        
        return recommendations
