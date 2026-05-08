"""示例脚本 - 演示如何读取和使用诊断数据提取器生成的 JSON 文件"""

import json
from pathlib import Path


def load_diagnostic_data(json_file: str) -> dict:
    """加载诊断数据 JSON 文件"""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def print_cluster_summary(data: dict):
    """打印集群摘要信息"""
    print("\n" + "="*60)
    print("📊 ES 集群诊断数据摘要")
    print("="*60)
    
    # 元数据
    meta = data['metadata']
    print(f"\n📁 数据来源：{meta['source']}")
    print(f"⏰ 提取时间：{meta['extracted_at']}")
    
    # 集群健康
    if data.get('cluster_health'):
        health = data['cluster_health']
        print(f"\n🏥 集群健康状态:")
        print(f"   集群名称：{health['cluster_name']}")
        
        # 状态带颜色
        status = health['status']
        status_emoji = {'green': '✅', 'yellow': '⚠️', 'red': '🔴'}.get(status, '❓')
        print(f"   状态：{status_emoji} {status}")
        print(f"   节点总数：{health['number_of_nodes']} (数据节点：{health['number_of_data_nodes']})")
        print(f"   活跃分片：{health['active_shards']} (主分片：{health['active_primary_shards']})")
        print(f"   活跃分片比例：{health['active_shards_percent']:.1f}%")
    
    # 节点统计
    if data.get('nodes'):
        nodes = data['nodes']
        master_nodes = [n for n in nodes if n.get('is_master')]
        print(f"\n💻 节点信息:")
        print(f"   节点总数：{len(nodes)}")
        print(f"   主节点数：{len(master_nodes)}")
        
        # 角色分布
        roles_count = {}
        for node in nodes:
            for role in node.get('roles', []):
                roles_count[role] = roles_count.get(role, 0) + 1
        
        print(f"   角色分布：{', '.join([f'{k}:{v}' for k, v in roles_count.items()])}")
    
    # 索引统计
    if data.get('indices'):
        indices = data['indices']
        green_indices = [i for i in indices if i.get('health') == 'green']
        yellow_indices = [i for i in indices if i.get('health') == 'yellow']
        red_indices = [i for i in indices if i.get('health') == 'red']
        
        print(f"\n📑 索引信息:")
        print(f"   索引总数：{len(indices)}")
        print(f"   ✅ 绿色：{len(green_indices)}  |  ⚠️ 黄色：{len(yellow_indices)}  |  🔴 红色：{len(red_indices)}")
        
        # 总文档数和存储大小
        total_docs = sum(i.get('docs_count', 0) for i in indices)
        total_size = sum(i.get('store_size_in_bytes', 0) for i in indices)
        print(f"   总文档数：{total_docs:,}")
        print(f"   总存储：{total_size / (1024**3):.2f} GB")
    
    # 其他数据
    if data.get('cluster_stats'):
        print(f"\n📈 集群统计：已包含")
    
    if data.get('shards'):
        shards = data['shards']
        if isinstance(shards, list):
            print(f"   分片总数：{len(shards)}")
    
    if data.get('allocation'):
        print(f"   分片分配信息：已包含")
    
    print("\n" + "="*60)


def analyze_resource_usage(data: dict):
    """分析资源使用情况"""
    if not data.get('nodes'):
        return
    
    nodes = data['nodes']
    
    print("\n💾 资源使用分析")
    print("="*60)
    
    # CPU 使用
    cpu_values = [n['cpu_percent'] for n in nodes if n.get('cpu_percent', 0) > 0]
    if cpu_values:
        avg_cpu = sum(cpu_values) / len(cpu_values)
        max_cpu = max(cpu_values)
        print(f"CPU 使用率:")
        print(f"   平均：{avg_cpu:.1f}% | 最高：{max_cpu:.1f}%")
    
    # 内存使用
    heap_values = [n['heap_used_percent'] for n in nodes if n.get('heap_used_percent', 0) > 0]
    if heap_values:
        avg_heap = sum(heap_values) / len(heap_values)
        max_heap = max(heap_values)
        print(f"内存使用率:")
        print(f"   平均：{avg_heap:.1f}% | 最高：{max_heap:.1f}%")
    
    # 磁盘使用
    disk_values = [n['disk_used_percent'] for n in nodes if n.get('disk_used_percent', 0) > 0]
    if disk_values:
        avg_disk = sum(disk_values) / len(disk_values)
        max_disk = max(disk_values)
        print(f"磁盘使用率:")
        print(f"   平均：{avg_disk:.1f}% | 最高：{max_disk:.1f}%")
    
    # 分片分布
    shard_values = [n['shard_count'] for n in nodes if n.get('shard_count', 0) > 0]
    if shard_values:
        avg_shards = sum(shard_values) / len(shard_values)
        max_shards = max(shard_values)
        min_shards = min(shard_values)
        print(f"分片分布:")
        print(f"   平均：{avg_shards:.0f} | 最多：{max_shards} | 最少：{min_shards}")
    
    print("="*60)


def find_high_load_nodes(data: dict, threshold: float = 70.0):
    """找出高负载节点"""
    if not data.get('nodes'):
        return
    
    high_load_nodes = []
    for node in data['nodes']:
        reasons = []
        
        if node.get('cpu_percent', 0) > threshold:
            reasons.append(f"CPU: {node['cpu_percent']:.1f}%")
        if node.get('heap_used_percent', 0) > threshold:
            reasons.append(f"内存：{node['heap_used_percent']:.1f}%")
        if node.get('disk_used_percent', 0) > threshold:
            reasons.append(f"磁盘：{node['disk_used_percent']:.1f}%")
        
        if reasons:
            high_load_nodes.append({
                'name': node['name'],
                'ip': node['ip'],
                'reasons': reasons
            })
    
    if high_load_nodes:
        print(f"\n⚠️ 高负载节点 (阈值 > {threshold}%):")
        print("-" * 60)
        for node_info in high_load_nodes:
            print(f"🔴 {node_info['name']} ({node_info['ip']})")
            for reason in node_info['reasons']:
                print(f"   - {reason}")
        print("-" * 60)
    else:
        print(f"\n✅ 未发现高负载节点 (所有节点资源使用率 < {threshold}%)")


def main():
    """主函数"""
    # 查找最新的输出文件
    out_dir = Path("out")
    if not out_dir.exists():
        print("❌ 输出目录不存在，请先运行 diagnostic_extractor")
        return
    
    json_files = sorted(out_dir.glob("diagnostic_data_*.json"))
    if not json_files:
        print("❌ 未找到诊断数据文件，请先运行 diagnostic_extractor")
        return
    
    latest_file = json_files[-1]
    print(f"读取文件：{latest_file.name}")
    
    # 加载数据
    try:
        data = load_diagnostic_data(str(latest_file))
    except Exception as e:
        print(f"❌ 加载文件失败：{e}")
        return
    
    # 打印摘要
    print_cluster_summary(data)
    
    # 资源分析
    analyze_resource_usage(data)
    
    # 高负载节点检测
    find_high_load_nodes(data, threshold=70.0)
    
    # 提示
    print("\n💡 提示:")
    print("   - 完整数据已保存至:", latest_file)
    print("   - 文件大小:", f"{latest_file.stat().st_size / 1024:.1f} KB")
    print("   - 可以使用 JSON 查看器或代码进一步分析\n")


if __name__ == '__main__':
    main()
