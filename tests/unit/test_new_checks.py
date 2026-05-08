"""
测试新增检查项
验证线程池、分片、ILM、快照、安全检查项的实现
"""

import json
from pathlib import Path
from es_insight.rules.engine import RulesEngine

# 模拟测试数据
test_data = {
    'cluster_health': {
        'status': 'green',
        'active_shards_percent': 100.0,
        'unassigned_shards': 0,
        'initializing_shards': 0,
        'relocating_shards': 0,
        'delayed_unassigned_shards': 0,
        'pending_tasks': 0,
        'number_of_nodes': 3,
        'number_of_data_nodes': 3
    },
    'nodes': [
        {
            'name': 'node-1',
            'disk_used_percent': 45.2,
            'heap_used_percent': 52.3,
            'cpu_percent': 25.5
        },
        {
            'name': 'node-2',
            'disk_used_percent': 48.1,
            'heap_used_percent': 55.1,
            'cpu_percent': 28.3
        }
    ],
    'nodes_stats': {
        'nodes': {
            'node-1': {
                'name': 'node-1',
                'thread_pool': {
                    'search': {'queue': 100, 'rejected': 5},
                    'write': {'queue': 50, 'rejected': 2},
                    'bulk': {'queue': 200, 'rejected': 10},
                    'get': {'queue': 30, 'rejected': 1},
                    'analyze': {'queue': 10, 'rejected': 0}
                },
                'transport': {'server_open': 500}
            },
            'node-2': {
                'name': 'node-2',
                'thread_pool': {
                    'search': {'queue': 150, 'rejected': 8},
                    'write': {'queue': 80, 'rejected': 3},
                    'bulk': {'queue': 250, 'rejected': 15},
                    'get': {'queue': 40, 'rejected': 2},
                    'analyze': {'queue': 15, 'rejected': 1}
                },
                'transport': {'server_open': 600}
            }
        }
    },
    'indices': [
        {
            'name': 'test-index-1',
            'health': 'green',
            'store_size_bytes': 10 * (1024**3),  # 10GB
            'docs_count': 50000000,  # 5000 万
            'deleted_docs_ratio': 0.05,
            'segments_count': 150,
            'shards_count': 10
        },
        {
            'name': 'test-index-2',
            'health': 'yellow',
            'store_size_bytes': 60 * (1024**3),  # 60GB - 超过阈值
            'docs_count': 600000000,  # 6 亿 - 超过阈值
            'deleted_docs_ratio': 0.25,  # 25% - 超过阈值
            'segments_count': 600,  # 超过阈值
            'shards_count': 120  # 超过阈值
        }
    ],
    'shards': [
        {'node': 'node-1', 'store_size_bytes': 20 * (1024**3), 'docs_count': 100000000},
        {'node': 'node-1', 'store_size_bytes': 25 * (1024**3), 'docs_count': 120000000},
        {'node': 'node-2', 'store_size_bytes': 22 * (1024**3), 'docs_count': 110000000},
        {'node': 'node-2', 'store_size_bytes': 55 * (1024**3), 'docs_count': 250000000}  # 大分片
    ],
    'ilm_status': {
        'errors': [{'index': 'old-index', 'error': 'policy not found'}],
        'failures': [{'index': 'test-index', 'failure': 'rollover failed'}]
    },
    'snapshots': [
        {
            'snapshot': 'snapshot-2024-01-01',
            'state': 'SUCCESS'
        },
        {
            'snapshot': 'snapshot-2024-01-02',
            'state': 'PARTIAL'  # 部分失败
        }
    ],
    'xpack': {
        'available': True,
        'enabled': True
    }
}

def test_new_checks():
    """测试新增检查项"""
    print("=" * 80)
    print("测试新增检查项")
    print("=" * 80)
    
    # 初始化规则引擎
    config_path = Path(__file__).parent.parent.parent / "configs" / "default_thresholds.yaml"
    engine = RulesEngine(config_path=str(config_path))
    
    # 执行检查
    alerts = engine.check_all(test_data)
    
    # 按类别分组显示
    categories = {}
    for alert in alerts:
        category = alert['category']
        if category not in categories:
            categories[category] = []
        categories[category].append(alert)
    
    print(f"\n共发现 {len(alerts)} 个告警\n")
    print("-" * 80)
    
    for category, category_alerts in categories.items():
        print(f"\n【{category}】 - {len(category_alerts)} 个告警")
        print("-" * 80)
        
        for i, alert in enumerate(category_alerts, 1):
            print(f"{i}. 检查项：{alert['check_item']}")
            print(f"   消息：{alert['message']}")
            print(f"   级别：{alert['severity']}")
            print(f"   当前值：{alert.get('current_value', 'N/A')}")
            print(f"   阈值：{alert.get('threshold', 'N/A')}")
            print(f"   建议：{alert.get('recommendation', 'N/A')}")
            print()
    
    print("=" * 80)
    print("测试完成")
    print("=" * 80)
    
    return alerts

if __name__ == '__main__':
    test_new_checks()
