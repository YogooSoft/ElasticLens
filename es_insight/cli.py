"""命令行接口"""

import click
import os
from pathlib import Path
from loguru import logger

from es_insight.parsers import (
    ClusterHealthParser,
    NodesParser,
    IndicesParser
)
from es_insight.analyzers.health_engine import HealthAssessmentEngine
from es_insight.analyzers.resource_engine import ResourceAnalyzer
from es_insight.rules.predefined import create_predefined_rules
from es_insight.rules.engine import RulesEngine
from es_insight.config import Config, ThresholdConfig


@click.command()
@click.argument('diagnostic_file', type=click.Path(exists=True))
@click.option(
    '-o', '--output-dir',
    default='./reports',
    help='报告输出目录'
)
@click.option(
    '-f', '--formats',
    default='html',
    type=click.Choice(['html', 'pdf', 'markdown', 'json'], case_sensitive=False),
    help='输出格式 (逗号分隔)'
)
@click.option(
    '-c', '--config',
    type=click.Path(exists=True),
    help='配置文件路径'
)
@click.option(
    '-t', '--thresholds',
    type=click.Path(exists=True),
    help='阈值配置文件路径'
)
@click.option(
    '--no-chart',
    is_flag=True,
    help='不生成图表'
)
@click.option(
    '-v', '--verbose',
    is_flag=True,
    help='显示详细日志'
)
@click.option(
    '-q', '--quiet',
    is_flag=True,
    help='静默模式，只输出错误信息'
)
@click.version_option(version='0.1.0')
def cli(
    diagnostic_file: str,
    output_dir: str,
    formats: str,
    config: str,
    thresholds: str,
    no_chart: bool,
    verbose: bool,
    quiet: bool
):
    """ES 集群巡检结果自动解读工具"""
    
    # 配置日志
    _setup_logging(verbose, quiet)
    
    try:
        # 1. 初始化配置
        logger.info("初始化配置...")
        app_config = Config(config) if config else Config()
        threshold_config = ThresholdConfig(thresholds) if thresholds else ThresholdConfig()
        
        # 2. 解析诊断包
        logger.info(f"解析诊断包：{diagnostic_file}")
        
        # 解析集群健康
        health_parser = ClusterHealthParser(diagnostic_file)
        health_data = health_parser.parse()
        
        # 解析节点信息
        nodes_parser = NodesParser(diagnostic_file)
        nodes = nodes_parser.parse_short()
        
        # 解析索引信息
        indices_parser = IndicesParser(diagnostic_file)
        indices = indices_parser.parse()
        
        # 3. 执行分析
        logger.info("执行健康度评估...")
        health_engine = HealthAssessmentEngine(app_config)
        health_result = health_engine.assess_cluster_health(health_data)
        
        logger.info("执行资源分析...")
        resource_analyzer = ResourceAnalyzer(threshold_config)
        resource_result = resource_analyzer.analyze_nodes(nodes)
        
        # 4. 执行规则检查
        logger.info("执行规则检查...")
        rule_engine = RulesEngine()
        
        # 构建集群数据对象
        cluster_data = type('ClusterData', (), {
            'health': health_data,
            'nodes': nodes,
            'indices': indices,
            'to_dict': lambda self: {
                'cluster_health': {
                    **health_data.__dict__,
                    'status': health_data.status.value  # 转换为字符串
                },
                'nodes': [n.__dict__ for n in nodes],
                'indices': [i.__dict__ for i in indices]
            }
        })()
        
        rule_result = rule_engine.check_all(cluster_data.to_dict())
        
        # 5. 生成报告（简化版本，直接输出摘要）
        logger.info("生成报告...")
        
        # 6. 输出摘要
        _print_summary(health_result, rule_result)
        
    except Exception as e:
        logger.error(f"处理失败：{e}", exc_info=verbose)
        raise click.ClickException(str(e))


def _setup_logging(verbose: bool, quiet: bool):
    """配置日志"""
    if quiet:
        logger.remove()
        logger.add(lambda msg: print(msg, end=''), level="ERROR")
    elif verbose:
        logger.remove()
        logger.add(lambda msg: print(msg, end=''), level="DEBUG")
    else:
        logger.remove()
        logger.add(lambda msg: print(msg, end=''), level="INFO")


def _print_summary(health_result, rule_result):
    """打印摘要"""
    print("\n" + "="*60)
    print("巡检摘要")
    print("="*60)
    print(f"健康度评分：{health_result.total_score} ({health_result.health_level})")
    print(f"发现问题：{len(health_result.issues)} 个")
    
    # rule_result 是一个告警列表
    if isinstance(rule_result, list):
        print(f"触发规则：{len(rule_result)} 条")
        # 统计各级别告警
        critical_count = sum(1 for r in rule_result if r.get('severity') == 'critical')
        warning_count = sum(1 for r in rule_result if r.get('severity') == 'warning')
        info_count = sum(1 for r in rule_result if r.get('severity') == 'info')
        print(f"  - 严重：{critical_count}")
        print(f"  - 警告：{warning_count}")
        print(f"  - 提示：{info_count}")
    else:
        print(f"触发规则：{len(rule_result.triggered_rules)} 条")
        print(f"  - 严重：{rule_result.critical_count}")
        print(f"  - 警告：{rule_result.warning_count}")
        print(f"  - 提示：{rule_result.info_count}")
    
    print("="*60 + "\n")


def main():
    """入口函数"""
    cli()


if __name__ == '__main__':
    main()
