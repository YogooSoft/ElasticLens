"""健康评分计算模块

实现多维度健康评分的核心算法
"""

from typing import Dict, Any, List, Tuple
from loguru import logger
from .config import HealthScoreConfig


class HealthScoreCalculator:
    """健康评分计算器"""
    
    def __init__(self, config: HealthScoreConfig = None):
        """
        初始化评分计算器
        
        Args:
            config: 配置对象，如果为None则使用默认配置
        """
        self.config = config or HealthScoreConfig()
        
        # 定义各维度内指标的权重
        self.metric_weights = {
            'cluster_health': {
                'status': 0.30,
                'active_shards_percent': 0.25,
                'unassigned_shards': 0.20,
                'cluster_settings_consistency': 0.15,
                'cluster_version_consistency': 0.10
            },
            'node_performance': {
                'disk_used_percent': 0.25,
                'heap_used_percent': 0.25,
                'cpu_percent': 0.20,
                'load_average_ratio': 0.15,
                'shards_per_node': 0.10,
                'http_connections': 0.05
            },
            'index_status': {
                'index_health_status': 0.30,
                'index_size_gb': 0.20,
                'doc_count': 0.15,
                'deleted_docs_percent': 0.15,
                'shards_per_index': 0.10,
                'segments_per_index': 0.10
            },
            'performance_metrics': {
                'search_thread_pool_queue': 0.20,
                'write_thread_pool_queue': 0.20,
                'bulk_thread_pool_queue': 0.15,
                'search_rejection_rate': 0.15,
                'write_rejection_rate': 0.15,
                'bulk_rejection_rate': 0.15
            },
            'security_config': {
                'xpack_security_enabled': 0.30,
                'default_password_set': 0.25,
                'anonymous_access': 0.20,
                'http_ssl_enabled': 0.15,
                'transport_ssl_enabled': 0.10
            },
            'operation_status': {
                'snapshot_status': 0.30,
                'snapshot_interval_hours': 0.25,
                'snapshot_retention_count': 0.20,
                'ilm_status': 0.15,
                'ilm_managed_ratio': 0.10
            }
        }
    
    def calculate_total_score(self, metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        计算总健康评分
        
        Args:
            metrics: 各维度的指标数据
            
        Returns:
            包含总评分、各维度评分和详细信息的字典
        """
        result = {
            'total_score': 0,
            'health_level': 'unknown',
            'dimension_scores': {},
            'metric_scores': {},
            'issues': [],
            'recommendations': [],
            'summary': {
                'critical_issues_count': 0,
                'warning_issues_count': 0,
                'total_issues_count': 0,
                'level_1_count': 0,
                'level_2_count': 0,
                'level_3_count': 0
            }
        }
        
        # 计算各维度评分
        dimension_scores = {}
        for dimension in ['cluster_health', 'node_performance', 'index_status', 
                         'performance_metrics', 'security_config', 'operation_status']:
            if dimension in metrics:
                dim_result = self._calculate_dimension_score(dimension, metrics[dimension])
                dimension_scores[dimension] = dim_result['score']
                result['metric_scores'][dimension] = dim_result['metric_scores']
                
                # 收集问题和推荐
                result['issues'].extend(dim_result.get('issues', []))
                result['recommendations'].extend(dim_result.get('recommendations', []))
        
        # 计算加权总分
        total_score = 0
        dimension_weights = self.config.weights.get('dimensions', {})
        
        for dimension, score in dimension_scores.items():
            weight = dimension_weights.get(dimension, 0)
            total_score += score * weight
        
        result['total_score'] = round(total_score, 2)
        result['dimension_scores'] = dimension_scores
        result['health_level'] = self._determine_health_level(result['total_score'])
        
        # 统计各级别问题数量
        for issue in result['issues']:
            severity = issue.get('severity', 'warning')
            level = issue.get('severity_level', 2)
            if severity == 'critical':
                result['summary']['critical_issues_count'] += 1
            elif severity == 'warning':
                result['summary']['warning_issues_count'] += 1
            
            # 修正：level 1 对应一级告警，level 3 对应三级告警
            if level == 1:
                result['summary']['level_1_count'] += 1
            elif level == 2:
                result['summary']['level_2_count'] += 1
            elif level == 3:
                result['summary']['level_3_count'] += 1
        
        result['summary']['total_issues_count'] = len(result['issues'])
        
        logger.info(f"健康评分计算完成: {result['total_score']}分, 等级: {result['health_level']}")
        
        return result
    
    def _calculate_dimension_score(self, dimension: str, 
                                   metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算单个维度的评分
        
        Args:
            dimension: 维度名称
            metrics: 该维度的指标数据
            
        Returns:
            维度评分结果
        """
        metric_scores = {}
        issues = []
        recommendations = []
        
        # 获取该维度的指标权重
        weights = self.metric_weights.get(dimension, {})
        
        # 计算每个指标的得分
        for metric_name, metric_data in metrics.items():
            if metric_name in weights:
                threshold = self.config.get_threshold(dimension, metric_name)
                value = metric_data.get('value', 0)
                
                # 处理None值
                if value is None:
                    logger.warning(f"指标 {dimension}.{metric_name} 的值为None，使用默认值0")
                    value = 0
                
                score = self._calculate_metric_score(value, threshold)
                metric_scores[metric_name] = {
                    'score': round(score, 2),
                    'value': value,
                    'threshold': threshold
                }
                
                # 识别问题和建议
                if score < 60:
                    issue = self._generate_issue(dimension, metric_name, value, score)
                    if issue:
                        issues.append(issue)
                
                if score < 80:
                    rec = self._generate_recommendation(dimension, metric_name, value, score)
                    if rec:
                        recommendations.append(rec)
        
        # 计算加权平均得分
        if not metric_scores:
            return {'score': 100, 'metric_scores': {}, 'issues': [], 'recommendations': []}
        
        total_weight = sum(weights.get(m, 0) for m in metric_scores.keys())
        if total_weight == 0:
            weighted_score = 100
        else:
            weighted_score = sum(
                metric_scores[m]['score'] * weights.get(m, 0) 
                for m in metric_scores.keys()
            ) / total_weight
        
        return {
            'score': round(weighted_score, 2),
            'metric_scores': metric_scores,
            'issues': issues,
            'recommendations': recommendations
        }
    
    def _calculate_metric_score(self, value: float, thresholds: Dict[str, Any]) -> float:
        """
        计算单个指标的得分（线性插值算法）
        
        Args:
            value: 指标实际值
            thresholds: 阈值配置
            
        Returns:
            指标得分（0-100）
        """
        if not thresholds:
            return 100
        
        # 特殊处理：状态类指标（直接映射）
        if 'green' in thresholds or 'enabled' in thresholds or 'success' in thresholds:
            return self._calculate_categorical_score(value, thresholds)
        
        # 获取阈值
        normal = thresholds.get('normal', 0)
        warning = thresholds.get('warning', 0)
        critical = thresholds.get('critical', 0)
        
        # 判断指标类型：越小越好 vs 越大越好
        # 如果 normal < warning < critical，则是"越小越好"（如未分配分片数、使用率等）
        # 如果 normal > warning > critical，则是"越大越好"（如活跃分片百分比）
        
        if normal < warning < critical:
            # "越小越好"类型：值越小得分越高
            if value <= normal:
                return 100.0
            elif value <= warning:
                # 警告范围：60-99分
                score = 60 + 40 * (warning - value) / (warning - normal)
                return max(60, min(99, score))
            else:
                # 严重范围：0-59分
                if critical > warning:
                    score = 60 * (critical - value) / (critical - warning)
                    return max(0, min(59, score))
                else:
                    return 0
        
        elif normal > warning > critical:
            # "越大越好"类型：值越大得分越高
            if value >= normal:
                return 100.0
            elif value >= warning:
                # 警告范围：60-99分
                score = 60 + 40 * (value - warning) / (normal - warning)
                return max(60, min(99, score))
            else:
                # 严重范围：0-59分
                if warning > critical:
                    score = 60 * (value - critical) / (warning - critical)
                    return max(0, min(59, score))
                else:
                    return 0
        
        else:
            # 阈值配置异常，返回中间值
            logger.warning(f"阈值配置异常: normal={normal}, warning={warning}, critical={critical}")
            return 50
    
    def _calculate_categorical_score(self, value: Any, thresholds: Dict[str, Any]) -> float:
        """
        计算分类指标的得分（状态、布尔值等）
        
        Args:
            value: 指标值
            thresholds: 阈值配置
            
        Returns:
            指标得分
        """
        # 字符串类型（如status: green/yellow/red）
        if isinstance(value, str):
            value_lower = value.lower()
            
            # 检查是否有精确匹配
            if value_lower in thresholds:
                return float(thresholds[value_lower])
            
            # 检查常见状态映射
            status_map = {
                'green': thresholds.get('green', 100),
                'yellow': thresholds.get('yellow', 60),
                'red': thresholds.get('red', 0),
                'enabled': thresholds.get('enabled', 100),
                'disabled': thresholds.get('disabled', 0),
                'success': thresholds.get('success', 100),
                'partial': thresholds.get('partial', 60),
                'failed': thresholds.get('failed', 0),
                'consistent': thresholds.get('consistent', 100),
                'inconsistent': thresholds.get('inconsistent', 0)
            }
            
            return float(status_map.get(value_lower, 50))
        
        # 数值类型但表示分类（如100/60/0）
        if isinstance(value, (int, float)):
            if value >= 90:
                return 100.0
            elif value >= 50:
                return 60.0
            else:
                return 0.0
        
        return 50.0
    
    def _determine_health_level(self, score: float) -> str:
        """
        根据评分确定健康等级
        
        Args:
            score: 健康评分
            
        Returns:
            健康等级字符串
        """
        if score >= 90:
            return '优秀'
        elif score >= 75:
            return '良好'
        elif score >= 60:
            return '一般'
        elif score >= 40:
            return '警告'
        else:
            return '严重'
    
    def _generate_issue(self, dimension: str, metric_name: str, 
                       value: float, score: float) -> Dict[str, Any]:
        """
        生成问题描述
        
        Args:
            dimension: 维度名称
            metric_name: 指标名称
            value: 指标值
            score: 指标得分
            
        Returns:
            问题描述字典
        """
        severity = 'critical' if score < 40 else 'warning'
        severity_level = 3 if score < 40 else (2 if score < 60 else 1)
        
        # 生成问题描述
        descriptions = {
            ('cluster_health', 'status'): "集群状态异常，当前状态影响数据可用性",
            ('cluster_health', 'unassigned_shards'): "存在未分配分片，可能影响集群性能",
            ('node_performance', 'disk_used_percent'): f"节点磁盘使用率过高: {float(value):.1f}%" if isinstance(value, (int, float)) else f"节点磁盘使用率过高: {value}",
            ('node_performance', 'heap_used_percent'): f"JVM堆内存使用率过高: {float(value):.1f}%" if isinstance(value, (int, float)) else f"JVM堆内存使用率过高: {value}",
            ('node_performance', 'cpu_percent'): f"CPU使用率过高: {float(value):.1f}%" if isinstance(value, (int, float)) else f"CPU使用率过高: {value}",
            ('index_status', 'deleted_docs_percent'): f"索引已删除文档比例过高: {float(value):.1f}%" if isinstance(value, (int, float)) else f"索引已删除文档比例过高: {value}",
            ('performance_metrics', 'search_rejection_rate'): f"搜索拒绝率过高: {float(value):.1f}%" if isinstance(value, (int, float)) else f"搜索拒绝率过高: {value}",
            ('security_config', 'xpack_security_enabled'): "X-Pack安全功能未启用",
        }
        
        description = descriptions.get((dimension, metric_name), 
                                      f"{dimension}.{metric_name} 指标异常: {value}")
        
        return {
            'dimension': dimension,
            'metric': metric_name,
            'severity': severity,
            'severity_level': severity_level,
            'description': description,
            'value': value,
            'score': score
        }
    
    def _generate_recommendation(self, dimension: str, metric_name: str,
                                value: float, score: float) -> str:
        """
        生成优化建议
        
        Args:
            dimension: 维度名称
            metric_name: 指标名称
            value: 指标值
            score: 指标得分
            
        Returns:
            建议文本
        """
        recommendations = {
            ('cluster_health', 'status'): "检查集群状态，优先解决红色或黄色状态的根本原因",
            ('cluster_health', 'unassigned_shards'): "检查未分配分片原因，考虑扩容或调整副本策略",
            ('node_performance', 'disk_used_percent'): "清理无用索引或扩容磁盘空间",
            ('node_performance', 'heap_used_percent'): "优化查询或增加JVM堆内存",
            ('node_performance', 'cpu_percent'): "优化查询语句或增加节点数量",
            ('index_status', 'deleted_docs_percent'): "执行force_merge操作清理已删除文档",
            ('performance_metrics', 'search_rejection_rate'): "增加搜索线程池队列大小或优化查询",
            ('security_config', 'xpack_security_enabled'): "启用X-Pack安全功能保护集群",
        }
        
        return recommendations.get((dimension, metric_name), 
                                  f"检查并优化 {dimension}.{metric_name} 指标")
    
    def calculate_severity_based_score(self, metrics: Dict[str, Dict[str, Any]], 
                                      severity_mapping: Dict[str, int] = None) -> Dict[str, Any]:
        """
        基于严重级别的评分算法（备选方案）
        
        Args:
            metrics: 各维度的指标数据
            severity_mapping: 指标到严重级别的映射 {(dimension, metric): level}
            
        Returns:
            包含总评分、各级别得分和详细信息的字典
        """
        # 默认权重配置
        severity_weights = {1: 0.20, 2: 0.30, 3: 0.50}
        
        result = {
            'total_score': 0,
            'health_level': 'unknown',
            'severity_level_scores': {},
            'metric_scores': {},
            'issues': [],
            'recommendations': []
        }
        
        # 计算每个指标的得分和严重级别
        indicator_scores = {}
        for dimension, dim_metrics in metrics.items():
            for metric_name, metric_data in dim_metrics.items():
                # 计算指标得分
                threshold = self.config.get_threshold(dimension, metric_name)
                value = metric_data.get('value', 0)
                
                if value is None:
                    value = 0
                
                score = self._calculate_metric_score(value, threshold)
                
                # 获取严重级别
                severity_level = 2  # 默认二级
                if severity_mapping:
                    severity_level = severity_mapping.get((dimension, metric_name), 2)
                
                indicator_key = f"{dimension}.{metric_name}"
                indicator_scores[indicator_key] = {
                    'score': score,
                    'severity_level': severity_level,
                    'dimension': dimension,
                    'metric': metric_name,
                    'value': value
                }
                
                # 收集问题
                if score < 60:
                    issue = self._generate_issue(dimension, metric_name, value, score)
                    if issue:
                        result['issues'].append(issue)
                
                if score < 80:
                    rec = self._generate_recommendation(dimension, metric_name, value, score)
                    if rec:
                        result['recommendations'].append(rec)
        
        # 按严重级别分组
        level_scores = {1: [], 2: [], 3: []}
        for key, info in indicator_scores.items():
            level = info['severity_level']
            if level in level_scores:
                level_scores[level].append(info['score'])
        
        # 计算各级别的平均分
        level_averages = {}
        for level in [1, 2, 3]:
            scores = level_scores[level]
            if scores:
                level_averages[level] = sum(scores) / len(scores)
            else:
                level_averages[level] = 100  # 没有该级别指标时视为满分
        
        # 按严重级别权重计算总分
        total_score = sum(
            level_averages[level] * severity_weights.get(level, 0)
            for level in [1, 2, 3]
        )
        
        result['total_score'] = round(total_score, 2)
        result['health_level'] = self._determine_health_level(result['total_score'])
        result['severity_level_scores'] = {
            level: {
                'average_score': round(avg, 2),
                'weight': severity_weights.get(level, 0),
                'indicator_count': len(level_scores[level]),
                'level_description': {
                    1: '优化建议',
                    2: '建议处理',
                    3: '必须处理'
                }.get(level, '')
            }
            for level, avg in level_averages.items()
        }
        result['metric_scores'] = indicator_scores
        
        logger.info(f"基于严重级别评分完成: {result['total_score']}分, 等级: {result['health_level']}")
        
        return result
