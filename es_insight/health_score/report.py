"""健康评分报告数据生成模块

生成包含详细评分信息的报告数据结构
"""

from typing import Dict, Any, List
from datetime import datetime
from loguru import logger
from .config import HealthScoreConfig
from .metrics import MetricsCollector
from .calculator import HealthScoreCalculator


class HealthScoreReport:
    """健康评分报告生成器"""
    
    def __init__(self, config: HealthScoreConfig = None):
        """
        初始化报告生成器
        
        Args:
            config: 配置对象
        """
        self.config = config or HealthScoreConfig()
        self.calculator = HealthScoreCalculator(self.config)
    
    def generate_report(self, diagnostic_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成完整的健康评分报告
        
        Args:
            diagnostic_data: 诊断数据字典
            
        Returns:
            包含完整评分信息的报告数据
        """
        try:
            # 1. 采集指标
            collector = MetricsCollector(diagnostic_data)
            metrics = collector.collect_all_metrics()
            
            # 2. 计算评分
            score_result = self.calculator.calculate_total_score(metrics)
            
            # 3. 生成报告结构
            report = {
                'total_score': score_result['total_score'],
                'health_level': score_result['health_level'],
                'generated_at': datetime.now().isoformat(),
                'dimensions': self._format_dimension_report(
                    score_result['dimension_scores'],
                    score_result['metric_scores'],
                    metrics
                ),
                'issues': score_result['issues'],
                'recommendations': score_result['recommendations'],
                'summary': self._generate_summary(score_result)
            }
            
            logger.info(f"健康评分报告生成完成，总分: {report['total_score']}")
            return report
            
        except Exception as e:
            logger.error(f"生成健康评分报告失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # 返回默认报告
            return self._get_default_report()
    
    def _format_dimension_report(self, dimension_scores: Dict[str, float],
                                 metric_scores: Dict[str, Dict],
                                 metrics: Dict[str, Dict]) -> Dict[str, Any]:
        """
        格式化维度报告
        
        Args:
            dimension_scores: 各维度得分
            metric_scores: 各指标得分详情
            metrics: 原始指标数据
            
        Returns:
            格式化的维度报告
        """
        dimension_names = {
            'cluster_health': '集群健康',
            'node_performance': '节点性能',
            'index_status': '索引状态',
            'performance_metrics': '性能指标',
            'security_config': '安全配置',
            'operation_status': '运维状态'
        }
        
        result = {}
        for dimension, score in dimension_scores.items():
            dim_metrics = metric_scores.get(dimension, {})
            raw_metrics = metrics.get(dimension, {})
            
            formatted_metrics = []
            for metric_name, metric_score_info in dim_metrics.items():
                raw_value = raw_metrics.get(metric_name, {}).get('value', 0)
                unit = raw_metrics.get(metric_name, {}).get('unit', '')
                
                formatted_metrics.append({
                    'name': metric_name,
                    'display_name': self._get_metric_display_name(metric_name),
                    'score': metric_score_info['score'],
                    'value': raw_value,
                    'unit': unit,
                    'threshold': metric_score_info.get('threshold', {})
                })
            
            result[dimension] = {
                'name': dimension_names.get(dimension, dimension),
                'score': score,
                'weight': self.config.get_dimension_weight(dimension),
                'metrics': formatted_metrics
            }
        
        return result
    
    def _generate_summary(self, score_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成评分摘要
        
        Args:
            score_result: 评分计算结果
            
        Returns:
            摘要信息
        """
        total_score = score_result['total_score']
        health_level = score_result['health_level']
        
        # 确定颜色
        if total_score >= 90:
            color = '#28a745'  # 绿色
        elif total_score >= 75:
            color = '#5cb85c'  # 浅绿色
        elif total_score >= 60:
            color = '#ffc107'  # 黄色
        elif total_score >= 40:
            color = '#fd7e14'  # 橙色
        else:
            color = '#dc3545'  # 红色
        
        # 统计问题数量
        critical_issues = sum(1 for issue in score_result['issues'] 
                             if issue.get('severity') == 'critical')
        warning_issues = sum(1 for issue in score_result['issues'] 
                            if issue.get('severity') == 'warning')
        
        return {
            'score': total_score,
            'level': health_level,
            'color': color,
            'description': self._get_level_description(health_level),
            'critical_issues_count': critical_issues,
            'warning_issues_count': warning_issues,
            'total_issues_count': len(score_result['issues']),
            'recommendations_count': len(score_result['recommendations'])
        }
    
    def _get_metric_display_name(self, metric_name: str) -> str:
        """
        获取指标的显示名称
        
        Args:
            metric_name: 指标技术名称
            
        Returns:
            中文显示名称
        """
        display_names = {
            'status': '集群状态',
            'active_shards_percent': '活跃分片百分比',
            'unassigned_shards': '未分配分片数',
            'cluster_settings_consistency': '集群设置一致性',
            'cluster_version_consistency': '集群版本一致性',
            'disk_used_percent': '磁盘使用率',
            'heap_used_percent': 'JVM堆使用率',
            'cpu_percent': 'CPU使用率',
            'load_average_ratio': '负载平均值比率',
            'shards_per_node': '每节点分片数',
            'http_connections': 'HTTP连接数',
            'index_health_status': '索引健康状态',
            'index_size_gb': '索引大小',
            'doc_count': '文档数量',
            'deleted_docs_percent': '已删除文档比例',
            'shards_per_index': '每索引分片数',
            'segments_per_index': '每索引段数量',
            'search_thread_pool_queue': '搜索线程池队列',
            'write_thread_pool_queue': '写入线程池队列',
            'bulk_thread_pool_queue': '批量线程池队列',
            'search_rejection_rate': '搜索拒绝率',
            'write_rejection_rate': '写入拒绝率',
            'bulk_rejection_rate': '批量拒绝率',
            'xpack_security_enabled': 'X-Pack安全启用',
            'default_password_set': '默认密码设置',
            'anonymous_access': '匿名访问',
            'http_ssl_enabled': 'HTTP SSL',
            'transport_ssl_enabled': '传输层SSL',
            'snapshot_status': '快照状态',
            'snapshot_interval_hours': '快照间隔',
            'snapshot_retention_count': '快照保留数量',
            'ilm_status': 'ILM状态',
            'ilm_managed_ratio': 'ILM管理比例'
        }
        
        return display_names.get(metric_name, metric_name)
    
    def _get_level_description(self, level: str) -> str:
        """
        获取健康等级的描述
        
        Args:
            level: 健康等级
            
        Returns:
            描述文本
        """
        descriptions = {
            '优秀': '集群运行状态良好，无明显问题',
            '良好': '集群运行状态正常，存在少量轻微问题',
            '一般': '集群运行状态基本正常，但存在一些需要关注的问题',
            '警告': '集群存在较多问题，需要及时处理',
            '严重': '集群存在严重问题，需要立即处理'
        }
        
        return descriptions.get(level, '未知状态')
    
    def _get_default_report(self) -> Dict[str, Any]:
        """
        获取默认报告（出错时使用）
        
        Returns:
            默认报告数据
        """
        return {
            'total_score': 50,
            'health_level': '警告',
            'generated_at': datetime.now().isoformat(),
            'dimensions': {},
            'issues': [{
                'dimension': 'system',
                'metric': 'error',
                'severity': 'warning',
                'description': '健康评分计算过程中出现错误，使用默认评分',
                'value': 0,
                'score': 50
            }],
            'recommendations': ['检查系统日志，排查健康评分计算错误的原因'],
            'summary': {
                'score': 50,
                'level': '警告',
                'color': '#fd7e14',
                'description': '健康评分计算异常，请检查系统日志',
                'critical_issues_count': 0,
                'warning_issues_count': 1,
                'total_issues_count': 1,
                'recommendations_count': 1
            }
        }
