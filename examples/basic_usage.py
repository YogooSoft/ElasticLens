"""
基本使用示例

这个脚本演示了如何使用 es-insight 工具的基本功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from es_insight.parsers import ClusterHealthParser, NodesParser, IndicesParser
from es_insight.analyzers.health_engine import HealthAssessmentEngine
from es_insight.analyzers.resource_engine import ResourceAnalyzer
from es_insight.rules.predefined import create_predefined_rules
from es_insight.rules.engine import RulesEngine
from es_insight.config import Config, ThresholdConfig
from es_insight.report_generator import ReportGenerator
from es_insight.official_report_generator import OfficialReportGenerator
from es_insight.word_style_report_generator import WordStyleHTMLReportGenerator
from es_insight.full_metrics_report_generator import FullMetricsHTMLReportGenerator


def main():
    """主函数"""
    # 诊断包路径（使用项目 data 目录下的文件）
    diagnostic_file = os.path.join(project_root, "data", "local-diagnostics-20250625-055003.zip")
    
    print("="*60)
    print("ES 集群巡检结果自动解读工具 - 使用示例")
    print("="*60)
    
    try:
        # 1. 初始化配置
        print("\n[1/6] 初始化配置...")
        app_config = Config()
        threshold_config = ThresholdConfig()
        
        # 2. 解析诊断包
        print(f"\n[2/6] 解析诊断包：{diagnostic_file}")
        
        # 解析集群健康
        print("  - 解析集群健康数据...")
        health_parser = ClusterHealthParser(diagnostic_file)
        health_data = health_parser.parse()
        print(f"    ✓ 集群名称：{health_data.cluster_name}")
        print(f"    ✓ 状态：{health_data.status.value}")
        print(f"    ✓ 节点数：{health_data.number_of_nodes}")
        
        # 解析节点信息
        print("  - 解析节点信息...")
        nodes_parser = NodesParser(diagnostic_file)
        nodes = nodes_parser.parse_short()
        print(f"    ✓ 解析了 {len(nodes)} 个节点")
        
        # 解析索引信息
        print("  - 解析索引信息...")
        indices_parser = IndicesParser(diagnostic_file)
        indices = indices_parser.parse()
        print(f"    ✓ 解析了 {len(indices)} 个索引")
        
        # 解析版本信息
        print("  - 解析版本信息...")
        from es_insight.parsers.base import DiagnosticFileParser
        version_parser = DiagnosticFileParser(diagnostic_file)
        version_parser.extract()  # 先解压
        version_info = version_parser.parse_json("version.json")
        print(f"    ✓ ES 版本：{version_info.get('version', {}).get('number', 'unknown')}")
        version_parser.cleanup()  # 清理临时文件
        
        # 3. 执行健康度评估
        print("\n[3/6] 执行健康度评估...")
        health_engine = HealthAssessmentEngine(app_config)
        health_result = health_engine.assess_cluster_health(health_data)
        print(f"    ✓ 健康度评分：{health_result.total_score}")
        print(f"    ✓ 健康等级：{health_result.health_level}")
        print(f"    ✓ 发现问题：{len(health_result.issues)} 个")
        
        # 4. 执行资源分析
        print("\n[4/6] 执行资源分析...")
        resource_analyzer = ResourceAnalyzer(threshold_config)
        resource_result = resource_analyzer.analyze_nodes(nodes)
        print(f"    ✓ 警告节点：{len(resource_result.warning_nodes)} 个")
        print(f"    ✓ 严重节点：{len(resource_result.critical_nodes)} 个")
        print(f"    ✓ 不均衡度：{resource_result.imbalance_score}")
        
        # 5. 执行规则检查
        print("\n[5/6] 执行规则检查...")
        # RulesEngine 会自动从配置文件加载规则，不需要传入 rules
        rule_engine = RulesEngine()
        
        # 构建集群数据字典
        # 将 NodeInfo 对象转换为字典
        nodes_dict = [node.to_dict() if hasattr(node, 'to_dict') else node for node in nodes]
        # 将 IndexInfo 对象转换为字典
        indices_dict = [idx.to_dict() if hasattr(idx, 'to_dict') else idx for idx in indices]
        
        cluster_data_dict = {
            'cluster_health': health_data.to_dict() if hasattr(health_data, 'to_dict') else vars(health_data),
            'nodes': nodes_dict,
            'indices': indices_dict
        }
        
        rule_result = rule_engine.check_all(cluster_data_dict)
        print(f"    ✓ 触发规则：{len(rule_result)} 条")
        
        # 统计告警级别
        critical_count = sum(1 for r in rule_result if r.get('level') == 'critical')
        warning_count = sum(1 for r in rule_result if r.get('level') == 'warning')
        info_count = sum(1 for r in rule_result if r.get('level') == 'info')
        
        print(f"      - 严重：{critical_count}")
        print(f"      - 警告：{warning_count}")
        print(f"      - 提示：{info_count}")
        
        # 6. 生成报告
        print("\n[6/7] 生成巡检报告...")
        
        # 6.1 生成标准格式报告
        print("  - 生成标准格式报告...")
        report_generator = ReportGenerator(output_dir='./reports')
        
        # 构建规则结果对象（模拟原来的 RuleResult）
        class RuleViolation:
            """规则违规对象"""
            def __init__(self, rule_dict):
                self.rule_id = rule_dict.get('rule_id', 'unknown')
                self.message = rule_dict.get('message', '')
                self.level = rule_dict.get('level', 'info')
                self.category = rule_dict.get('category', '')
                self.value = rule_dict.get('value', '')
                self.threshold = rule_dict.get('threshold', '')
        
        class RuleResult:
            def __init__(self, rules):
                self.triggered_rules = [RuleViolation(r) for r in rules]
                self.critical_count = sum(1 for r in rules if r.get('level') == 'critical')
                self.warning_count = sum(1 for r in rules if r.get('level') == 'warning')
                self.info_count = sum(1 for r in rules if r.get('level') == 'info')
        
        rule_result_obj = RuleResult(rule_result)
        
        # 构建集群数据对象（保持向后兼容）
        cluster_data = type('ClusterData', (), {
            'health': health_data,
            'nodes': nodes,
            'indices': indices
        })()
        
        generated_files = report_generator.generate_all(
            health_result=health_result,
            resource_result=resource_result,
            rule_result=rule_result_obj,
            cluster_data=cluster_data,
            formats=['html', 'markdown', 'json']
        )
        
        print(f"    ✓ 生成了 {len(generated_files)} 个标准报告文件:")
        for fmt, filepath in generated_files.items():
            print(f"      - {fmt.upper()}: {filepath}")
        
        # 6.2 生成官方格式报告
        print("\n  - 生成官方格式报告...")
        official_generator = OfficialReportGenerator(output_dir='./reports')
        official_report_path = official_generator.generate_official_report(
            health_data=health_data,
            nodes=nodes,
            indices_count=len(indices),
            version_info=version_info,
            health_result=health_result,
            resource_result=resource_result,
            rule_result=rule_result
        )
        print(f"    ✓ 官方格式报告：{official_report_path}")
        
        # 6.3 生成 Word 风格 HTML 报告
        print("\n  - 生成 Word 风格 HTML 报告...")
        word_generator = WordStyleHTMLReportGenerator(output_dir='./reports')
        word_report_path = word_generator.generate_report(
            health_data=health_data,
            nodes=nodes,
            indices_count=len(indices),
            version_info=version_info,
            health_result=health_result,
            resource_result=resource_result,
            rule_result=rule_result_obj
        )
        print(f"    ✓ Word 风格 HTML 报告：{word_report_path}")
        
        # 6.4 生成完整指标展示 HTML 报告
        print("\n  - 生成完整指标展示 HTML 报告...")
        full_metrics_generator = FullMetricsHTMLReportGenerator(output_dir='./reports')
        full_metrics_path = full_metrics_generator.generate_report(
            health_data=health_data,
            nodes=nodes,
            indices_count=len(indices),
            version_info=version_info,
            health_result=health_result,
            resource_result=resource_result,
            rule_result=rule_result
        )
        print(f"    ✓ 完整指标展示 HTML 报告：{full_metrics_path}")
        
        # 7. 输出摘要
        print("\n[7/7] 巡检摘要")
        print("="*60)
        print(f"健康度评分：{health_result.total_score} ({health_result.health_level})")
        print(f"发现问题：{len(health_result.issues)} 个")
        print(f"触发规则：{len(rule_result.triggered_rules)} 条")
        print(f"报告目录：./reports/")
        print(f"生成文件：{len(generated_files) + 3} 个 (包含官方格式、Word 风格和完整指标展示)")
        print("="*60)
        
        # 显示详细问题
        if health_result.issues:
            print("\n发现的问题:")
            for i, issue in enumerate(health_result.issues, 1):
                print(f"{i}. [{issue.severity.value.upper()}] {issue.title}")
                print(f"   描述：{issue.description}")
                print(f"   建议：{issue.suggestion}")
                print()
        
        # 显示优化建议
        if health_result.recommendations:
            print("优化建议:")
            for i, rec in enumerate(health_result.recommendations, 1):
                print(f"{i}. {rec}")
            print()
        
    except FileNotFoundError as e:
        print(f"\n错误：找不到诊断包文件 '{diagnostic_file}'")
        print("提示：请确保诊断包文件存在于当前目录中")
    except Exception as e:
        print(f"\n错误：处理失败 - {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
