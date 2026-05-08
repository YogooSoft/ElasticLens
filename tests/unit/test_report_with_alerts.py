"""测试报表逻辑修复 - 验证详细检查项能否在报表中展示"""

import json
from pathlib import Path
from es_insight.rules.engine import RulesEngine
from es_insight.report_generator import ReportGenerator
from es_insight.models.health import HealthAssessmentResult, ClusterHealthData, HealthStatus
from es_insight.models.nodes import ResourceAnalysisResult
from es_insight.models.rule import RuleExecutionResult
from es_insight.models.common import Issue, Severity

# 模拟数据
test_data = {
    'cluster_health': {
        'status': 'green',
        'active_shards_percent': 100.0,
        'unassigned_shards': 0,
        'number_of_nodes': 3,
        'number_of_data_nodes': 3
    },
    'nodes': [
        {'name': 'node-1', 'disk_used_percent': 45.2, 'heap_used_percent': 52.3, 'cpu_percent': 25.5},
        {'name': 'node-2', 'disk_used_percent': 48.1, 'heap_used_percent': 55.1, 'cpu_percent': 28.3}
    ],
    'nodes_stats': {
        'nodes': {
            'node-1': {
                'name': 'node-1',
                'thread_pool': {
                    'search': {'queue': 100, 'rejected': 5},
                    'bulk': {'queue': 200, 'rejected': 10}
                }
            },
            'node-2': {
                'name': 'node-2',
                'thread_pool': {
                    'search': {'queue': 150, 'rejected': 8},
                    'bulk': {'queue': 250, 'rejected': 15}
                }
            }
        }
    },
    'indices': [
        {'name': 'test-index-1', 'health': 'green', 'store_size_bytes': 10 * (1024**3), 'docs_count': 50000000, 'deleted_docs_ratio': 0.05, 'segments_count': 150, 'shards_count': 10},
        {'name': 'test-index-2', 'health': 'yellow', 'store_size_bytes': 60 * (1024**3), 'docs_count': 600000000, 'deleted_docs_ratio': 0.25, 'segments_count': 600, 'shards_count': 120}
    ],
    'shards': [
        {'node': 'node-1', 'store_size_bytes': 20 * (1024**3), 'docs_count': 100000000},
        {'node': 'node-2', 'store_size_bytes': 55 * (1024**3), 'docs_count': 250000000}
    ],
    'ilm_status': {
        'errors': [{'index': 'old-index', 'error': 'policy not found'}],
        'failures': [{'index': 'test-index', 'failure': 'rollover failed'}]
    },
    'snapshots': [
        {'snapshot': 'snapshot-2024-01-01', 'state': 'SUCCESS'},
        {'snapshot': 'snapshot-2024-01-02', 'state': 'PARTIAL'}
    ],
    'xpack': {'available': True, 'enabled': True}
}

def test_report_with_alerts():
    """测试带详细告警的报表生成"""
    print("=" * 80)
    print("测试报表逻辑修复 - 详细检查项展示")
    print("=" * 80)
    
    # 1. 执行规则引擎检查
    print("\n1. 执行规则引擎检查...")
    config_path = Path(__file__).parent.parent.parent / "configs" / "default_thresholds.yaml"
    rules_engine = RulesEngine(config_path=str(config_path))
    alerts = rules_engine.check_all(test_data)
    print(f"   ✓ 生成 {len(alerts)} 个告警")
    
    # 2. 创建模拟的健康度评估结果（包含 detailed_alerts）
    print("\n2. 创建健康度评估结果...")
    health_result = HealthAssessmentResult(
        total_score=85.0,
        health_level='good',
        issues=[
            Issue(
                id="TEST_001",
                title="测试问题",
                description="这是一个测试问题",
                severity=Severity.WARNING,
                suggestion="建议解决此问题"
            )
        ],
        recommendations=["保持良好运维习惯"],
        detailed_alerts=alerts  # 新增字段！
    )
    print(f"   ✓ 健康度评分：{health_result.total_score}")
    print(f"   ✓ 包含详细告警：{len(health_result.detailed_alerts)} 个")
    
    # 3. 创建其他必需对象
    resource_result = ResourceAnalysisResult(
        node_rankings={},
        warning_nodes=[],
        critical_nodes=[],
        imbalance_score=0.15,
        cluster_disk_trend='stable'
    )
    
    rule_result = RuleExecutionResult()
    
    cluster_data = type('ClusterData', (), {
        'health': ClusterHealthData(
            cluster_name='test-cluster',
            status=HealthStatus.GREEN,
            number_of_nodes=3,
            number_of_data_nodes=3,
            active_primary_shards=10,
            active_shards=20,
            relocating_shards=0,
            initializing_shards=0,
            unassigned_shards=0,
            active_shards_percent=100.0,
            timed_out=False
        ),
        'nodes': test_data['nodes'],
        'indices': test_data['indices']
    })()
    
    # 4. 生成报表
    print("\n3. 生成 Markdown 报表...")
    report_gen = ReportGenerator(output_dir='reports/test')
    
    # 使用新的 generate_all 方法（带 alerts 参数）
    generated_files = report_gen.generate_all(
        health_result=health_result,
        resource_result=resource_result,
        rule_result=rule_result,
        cluster_data=cluster_data,
        formats=['markdown'],
        alerts=alerts  # 新增参数！
    )
    
    print(f"   ✓ 报表已生成：{generated_files.get('markdown', 'N/A')}")
    
    # 5. 验证报表内容
    print("\n4. 验证报表内容...")
    md_file = generated_files.get('markdown')
    if md_file and Path(md_file).exists():
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否包含详细检查项章节
        if '## 🔍 详细检查项' in content:
            print("   ✅ 报表包含「详细检查项」章节")
        else:
            print("   ❌ 报表缺少「详细检查项」章节")
        
        # 检查是否包含各类检查项
        check_items = {
            '线程池': 'thread_pool',
            '分片检查': 'shard',
            '索引健康': 'index_health',
            'ILM': 'ilm',
            '快照备份': 'snapshot'
        }
        
        for name, key in check_items.items():
            if name in content:
                print(f"   ✅ 包含 {name} 检查项")
            else:
                print(f"   ❌ 缺少 {name} 检查项")
        
        # 显示报表前 100 行
        print("\n5. 报表预览（前 100 行）:")
        print("-" * 80)
        lines = content.split('\n')[:100]
        for line in lines:
            print(line)
        print("-" * 80)
        
        if len(content.split('\n')) > 100:
            line_count = len(content.split('\n'))
            print(f"... 还有 {line_count - 100} 行 ...")
    
    print("\\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)

if __name__ == '__main__':
    test_report_with_alerts()
