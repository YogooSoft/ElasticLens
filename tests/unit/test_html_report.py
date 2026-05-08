#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试 HTML 报告中的详细检查项展示"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from es_insight.rules.engine import RulesEngine
from es_insight.report_generator import ReportGenerator
from es_insight.models.health import HealthAssessmentResult
from es_insight.models.nodes import ResourceAnalysisResult, NodeInfo
from es_insight.models.rule import RuleExecutionResult
from es_insight.models.common import Issue, Severity
from es_insight.config import Config

# 准备测试数据
test_data = {
    'cluster_health': {
        'cluster_name': 'test-cluster',
        'status': 'green',
        'number_of_nodes': 3,
        'active_shards_percent': 100.0
    },
    'nodes': [
        {
            'name': 'node-1',
            'host': '192.168.1.1',
            'ip': '192.168.1.1',
            'transport_address': '192.168.1.1:9300',
            'roles': ['master', 'data']
        }
    ],
    'indices': [
        {
            'index': 'test-index',
            'health': 'green',
            'docs_count': 1000000,
            'store_size': '10gb'
        }
    ],
    'nodes_stats': {
        'nodes': {
            'node-1': {
                'name': 'node-1',
                'os': {'cpu': {'percent': 50}},
                'jvm': {'mem': {'heap_used_percent': 60}},
                'thread_pool': {
                    'search': {'queue': 100, 'rejected': 5},
                    'write': {'queue': 50, 'rejected': 2}
                }
            }
        }
    },
    'shards': [
        {
            'index': 'test-index',
            'shard': 0,
            'prirep': 'p',
            'state': 'STARTED',
            'docs': 500000,
            'store': '5gb'
        }
    ]
}


def test_html_report_with_alerts():
    """测试 HTML 报告中的详细检查项"""
    print("=" * 80)
    print("测试 HTML 报告中的详细检查项展示")
    print("=" * 80)
    
    # 1. 执行规则引擎检查
    print("\n1. 执行规则引擎检查...")
    config_path = Path(__file__).parent.parent.parent / "configs" / "default_thresholds.yaml"
    rules_engine = RulesEngine(config_path=str(config_path))
    alerts = rules_engine.check_all(test_data)
    print(f"   ✓ 生成 {len(alerts)} 个告警")
    
    # 2. 创建健康度评估结果
    print("\n2. 创建健康度评估结果...")
    health_result = HealthAssessmentResult(
        total_score=85.0,
        health_level='good',
        issues=[Issue(
            id="test_issue_1",
            title="测试问题",
            description="这是一个测试问题",
            suggestion="建议解决此问题",
            severity=Severity.WARNING
        )],
        recommendations=["保持良好运维习惯"],
        detailed_alerts=alerts  # 新增字段！
    )
    print(f"   ✓ 健康度评分：{health_result.total_score}")
    print(f"   ✓ 包含详细告警：{len(health_result.detailed_alerts)} 个")
    
    # 3. 创建资源分析结果
    print("\n3. 创建资源分析结果...")
    resource_result = ResourceAnalysisResult(
        node_rankings={},
        warning_nodes=[],
        critical_nodes=[],
        imbalance_score=0.15,
        cluster_disk_trend='stable'
    )
    
    # 4. 创建规则执行结果
    print("\n4. 创建规则执行结果...")
    rule_result = RuleExecutionResult(
        total_rules=0,
        triggered_rules=[],
        passed_rules=[]
    )
    
    # 5. 加载集群数据
    print("\n5. 加载集群数据...")
    # 使用简单的命名空间对象
    from types import SimpleNamespace
    from enum import Enum
    
    # 创建 Status 枚举
    class ClusterStatus(Enum):
        GREEN = 'green'
        YELLOW = 'yellow'
        RED = 'red'
    
    cluster_data = SimpleNamespace(
        health=SimpleNamespace(
            cluster_name='test-cluster',
            status=ClusterStatus.GREEN,  # 使用枚举
            number_of_nodes=3,
            active_shards_percent=100.0
        ),
        indices=[],
        nodes=[]
    )
    print(f"   ✓ 集群名称：{cluster_data.health.cluster_name}")
    
    # 6. 生成 HTML 报告
    print("\n6. 生成 HTML 报告...")
    report_gen = ReportGenerator(output_dir='reports/test_html')
    generated_files = report_gen.generate_all(
        health_result=health_result,
        resource_result=resource_result,
        rule_result=rule_result,
        cluster_data=cluster_data,
        formats=['html'],
        alerts=alerts
    )
    
    html_file = generated_files.get('html')
    print(f"   ✓ HTML 报告已生成：{html_file}")
    
    # 7. 验证 HTML 内容
    print("\n7. 验证 HTML 内容...")
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # 检查是否包含详细检查项章节
    if '🔍 详细检查项' in html_content:
        print("   ✅ HTML 报告包含「详细检查项」章节")
    else:
        print("   ❌ HTML 报告不包含「详细检查项」章节")
        return False
    
    # 检查各类检查项
    check_items = {
        '线程池': 'thread_pool',
        '分片检查': 'shard',
        '索引健康': 'index_health',
        'ILM': 'ilm',
        '快照备份': 'snapshot'
    }
    
    for name, category in check_items.items():
        if category in html_content:
            print(f"   ✅ 包含 {name} 检查项")
        else:
            print(f"   ⚠️  未包含 {name} 检查项")
    
    # 8. 显示 HTML 片段
    print("\n8. HTML 报告片段预览（详细检查项部分）:")
    print("=" * 80)
    
    # 查找详细检查项部分
    start_idx = html_content.find('🔍 详细检查项')
    if start_idx >= 0:
        # 显示后面的 2000 个字符
        snippet = html_content[start_idx:start_idx + 2000]
        print(snippet)
    else:
        print("未找到详细检查项部分")
    
    print("=" * 80)
    
    # 9. 检查 HTML 表格结构
    print("\n9. 检查 HTML 表格结构...")
    if '<table>' in html_content:
        print("   ✅ HTML 包含表格结构")
        
        # 检查表头
        if '<th>检查项</th>' in html_content:
            print("   ✅ 表格包含正确的表头")
        else:
            print("   ⚠️  表格表头可能不正确")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成！HTML 报告成功展示详细检查项")
    print("=" * 80)
    
    return True


if __name__ == '__main__':
    success = test_html_report_with_alerts()
    if not success:
        sys.exit(1)
