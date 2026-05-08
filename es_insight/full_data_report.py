"""完整数据文本报告生成器 - 输出所有提取和解读的数据到文本文件"""

import json
from pathlib import Path
from datetime import datetime
from loguru import logger


class FullDataReportGenerator:
    """完整数据文本报告生成器"""
    
    def __init__(self, diagnostic_json: str, interpretation_json: str = None):
        """
        初始化报告生成器
        
        Args:
            diagnostic_json: 提取的原始 JSON 文件路径
            interpretation_json: 解读后的 JSON 文件路径（可选）
        """
        self.diagnostic_json = Path(diagnostic_json)
        self.interpretation_json = Path(interpretation_json) if interpretation_json else None
        self.output_dir = Path("out/analysis")
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载数据
        self.data = None
        self.interpretation = None
        self.load_data()
    
    def load_data(self):
        """加载 JSON 数据"""
        try:
            with open(self.diagnostic_json, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            logger.info(f"成功加载诊断数据：{self.diagnostic_json.name}")
            
            if self.interpretation_json and self.interpretation_json.exists():
                with open(self.interpretation_json, 'r', encoding='utf-8') as f:
                    self.interpretation = json.load(f)
                logger.info(f"成功加载解读数据：{self.interpretation_json.name}")
        except Exception as e:
            logger.error(f"加载数据失败：{e}")
            raise
    
    def generate_full_report(self) -> str:
        """
        生成完整数据文本报告
        
        Returns:
            输出文件路径
        """
        output_path = self.output_dir / f"full_data_report_{self.timestamp}.txt"
        
        lines = []
        
        # ========== 报告头部 ==========
        lines.append("="*100)
        lines.append("ES 集群诊断数据完整报告")
        lines.append("="*100)
        lines.append("")
        lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"数据来源：{self.data.get('metadata', {}).get('source', 'N/A')}")
        lines.append(f"提取时间：{self.data.get('metadata', {}).get('extracted_at', 'N/A')}")
        lines.append("")
        
        # ========== 1. 集群健康信息 ==========
        lines.append("="*100)
        lines.append("【1】集群健康信息 (cluster_health)")
        lines.append("="*100)
        health = self.data.get('cluster_health', {})
        lines.append(f"集群名称：{health.get('cluster_name', 'N/A')}")
        lines.append(f"集群状态：{health.get('status', 'N/A').upper()}")
        lines.append(f"节点总数：{health.get('number_of_nodes', 0)}")
        lines.append(f"数据节点数：{health.get('number_of_data_nodes', 0)}")
        lines.append(f"主节点数：{health.get('number_of_nodes', 0) - health.get('number_of_data_nodes', 0)}")
        lines.append("")
        lines.append("分片统计:")
        lines.append(f"  - 活跃分片总数：{health.get('active_shards', 0)}")
        lines.append(f"  - 主分片数量：{health.get('active_primary_shards', 0)}")
        lines.append(f"  - 副本分片数量：{health.get('active_shards', 0) - health.get('active_primary_shards', 0)}")
        lines.append(f"  - 迁移中分片：{health.get('relocating_shards', 0)}")
        lines.append(f"  - 初始化分片：{health.get('initializing_shards', 0)}")
        lines.append(f"  - 未分配分片：{health.get('unassigned_shards', 0)}")
        lines.append(f"  - 活跃分片比例：{health.get('active_shards_percent', 0)}%")
        lines.append(f"是否超时：{health.get('timed_out', False)}")
        lines.append("")
        
        # ========== 2. 节点信息 ==========
        lines.append("="*100)
        lines.append("【2】节点信息 (nodes)")
        lines.append("="*100)
        nodes = self.data.get('nodes', [])
        lines.append(f"节点总数：{len(nodes)}")
        lines.append("")
        
        # 角色分布统计
        role_count = {}
        master_nodes = []
        data_nodes = []
        client_nodes = []
        
        for node in nodes:
            roles = node.get('roles', [])
            for role in roles:
                role_count[role] = role_count.get(role, 0) + 1
            
            if node.get('is_master'):
                master_nodes.append(node['name'])
            if 'd' in roles or 'di' in roles or 'dilr' in roles:
                data_nodes.append(node['name'])
            if 'r' in roles and 'd' not in roles:
                client_nodes.append(node['name'])
        
        lines.append("角色分布:")
        for role, count in sorted(role_count.items()):
            lines.append(f"  - {role}: {count} 个节点")
        lines.append("")
        
        lines.append(f"主节点列表 ({len(master_nodes)} 个):")
        for name in master_nodes[:10]:  # 只显示前 10 个
            lines.append(f"  - {name}")
        if len(master_nodes) > 10:
            lines.append(f"  ... 还有 {len(master_nodes) - 10} 个")
        lines.append("")
        
        # 详细节点列表
        lines.append("节点详细列表:")
        lines.append("-"*100)
        lines.append(f"{'序号':<4} {'节点名称':<15} {'IP 地址':<16} {'角色':<10} {'主节点':<6} {'CPU%':<8} {'内存%':<8} {'磁盘%':<8} {'分片数':<8}")
        lines.append("-"*100)
        
        for i, node in enumerate(nodes, 1):
            name = node.get('name', 'N/A')[:15]
            ip = node.get('ip', 'N/A')[:16]
            roles = ','.join(node.get('roles', []))[:10]
            is_master = '是' if node.get('is_master') else '否'
            cpu = node.get('cpu_percent', 0)
            heap = node.get('heap_used_percent', 0)
            disk = node.get('disk_used_percent', 0)
            shards = node.get('shard_count', 0)
            
            lines.append(f"{i:<4} {name:<15} {ip:<16} {roles:<10} {is_master:<6} {cpu:<8.1f} {heap:<8.1f} {disk:<8.1f} {shards:<8}")
        
        lines.append("-"*100)
        lines.append("")
        
        # 资源统计汇总
        cpu_values = [n['cpu_percent'] for n in nodes if n.get('cpu_percent', 0) > 0]
        heap_values = [n['heap_used_percent'] for n in nodes if n.get('heap_used_percent', 0) > 0]
        disk_values = [n['disk_used_percent'] for n in nodes if n.get('disk_used_percent', 0) > 0]
        shard_values = [n['shard_count'] for n in nodes if n.get('shard_count', 0) > 0]
        
        lines.append("资源使用统计:")
        lines.append(f"  CPU 使用率:")
        if cpu_values:
            lines.append(f"    - 平均：{sum(cpu_values)/len(cpu_values):.1f}%")
            lines.append(f"    - 最高：{max(cpu_values):.1f}%")
            lines.append(f"    - 最低：{min(cpu_values):.1f}%")
        else:
            lines.append(f"    - 数据不可用")
        
        lines.append(f"  内存使用率:")
        if heap_values:
            lines.append(f"    - 平均：{sum(heap_values)/len(heap_values):.1f}%")
            lines.append(f"    - 最高：{max(heap_values):.1f}%")
            lines.append(f"    - 最低：{min(heap_values):.1f}%")
        else:
            lines.append(f"    - 数据不可用")
        
        lines.append(f"  磁盘使用率:")
        if disk_values:
            lines.append(f"    - 平均：{sum(disk_values)/len(disk_values):.1f}%")
            lines.append(f"    - 最高：{max(disk_values):.1f}%")
            lines.append(f"    - 最低：{min(disk_values):.1f}%")
        else:
            lines.append(f"    - 数据不可用")
        
        lines.append(f"  分片分布:")
        if shard_values:
            lines.append(f"    - 总数：{sum(shard_values)}")
            lines.append(f"    - 平均：{sum(shard_values)/len(shard_values):.1f}")
            lines.append(f"    - 最多：{max(shard_values)}")
            lines.append(f"    - 最少：{min(shard_values)}")
        else:
            lines.append(f"    - 数据不可用")
        lines.append("")
        
        # ========== 3. 索引信息 ==========
        lines.append("="*100)
        lines.append("【3】索引信息 (indices)")
        lines.append("="*100)
        indices = self.data.get('indices', [])
        lines.append(f"索引总数：{len(indices)}")
        lines.append("")
        
        # 健康状态统计
        health_dist = {}
        for idx in indices:
            h = idx.get('health', 'unknown')
            health_dist[h] = health_dist.get(h, 0) + 1
        
        lines.append("健康状态分布:")
        for status in ['green', 'yellow', 'red']:
            count = health_dist.get(status, 0)
            percentage = count / len(indices) * 100 if indices else 0
            emoji = {'green': '✅', 'yellow': '⚠️', 'red': '🔴'}.get(status, '')
            lines.append(f"  - {emoji} {status.upper()}: {count} 个 ({percentage:.1f}%)")
        lines.append("")
        
        # 文档和存储统计
        total_docs = sum(idx.get('docs_count', 0) for idx in indices)
        total_size = sum(idx.get('store_size_bytes', 0) for idx in indices)
        total_primary_shards = sum(idx.get('primary_shards', 0) for idx in indices)
        total_replica_shards = sum(idx.get('replica_shards', 0) for idx in indices)
        
        lines.append("文档统计:")
        lines.append(f"  - 总文档数：{total_docs:,}")
        lines.append(f"  - 平均每个索引：{total_docs/len(indices):,.0f}" if indices else "  - 平均每个索引：0")
        lines.append("")
        
        lines.append("存储统计:")
        lines.append(f"  - 总大小：{total_size / (1024**3):.2f} GB")
        lines.append(f"  - 平均每个索引：{total_size / len(indices) / (1024**2):.2f} MB" if indices else "  - 平均每个索引：0 MB")
        lines.append("")
        
        lines.append("分片统计:")
        lines.append(f"  - 主分片总数：{total_primary_shards}")
        lines.append(f"  - 副本分片总数：{total_replica_shards}")
        lines.append(f"  - 总副本比例：{total_replica_shards/total_primary_shards:.2f}" if total_primary_shards > 0 else "  - 总副本比例：N/A")
        lines.append("")
        
        # Top 20 大索引
        lines.append("Top 20 大索引（按存储大小）:")
        lines.append("-"*100)
        lines.append(f"{'排名':<4} {'索引名称':<40} {'健康':<8} {'文档数':<15} {'存储大小':<12} {'主分片':<8} {'副本':<6}")
        lines.append("-"*100)
        
        sorted_indices = sorted(indices, key=lambda x: x.get('store_size_bytes', 0), reverse=True)[:20]
        for i, idx in enumerate(sorted_indices, 1):
            name = idx.get('name', 'N/A')[:40]
            health_status = idx.get('health', 'N/A').upper()[:7]
            docs = idx.get('docs_count', 0)
            size_gb = idx.get('store_size_bytes', 0) / (1024**3)
            primary = idx.get('primary_shards', 0)
            replica = idx.get('replica_shards', 0)
            
            lines.append(f"{i:<4} {name:<40} {health_status:<8} {docs:<15,} {size_gb:<10.2f}GB {primary:<8} {replica:<6}")
        
        lines.append("-"*100)
        lines.append("")
        
        # ========== 4. 集群统计信息 ==========
        lines.append("="*100)
        lines.append("【4】集群统计信息 (cluster_stats)")
        lines.append("="*100)
        cluster_stats = self.data.get('cluster_stats', {})
        
        if cluster_stats:
            # 尝试提取关键统计信息
            if isinstance(cluster_stats, dict):
                lines.append("集群统计详情:")
                for key, value in list(cluster_stats.items())[:30]:  # 限制显示数量
                    if isinstance(value, (int, float, str)):
                        lines.append(f"  - {key}: {value}")
                    elif isinstance(value, dict):
                        lines.append(f"  - {key}: (嵌套数据，共{len(value)}项)")
                    elif isinstance(value, list):
                        lines.append(f"  - {key}: (列表，共{len(value)}项)")
            else:
                lines.append(f"数据类型：{type(cluster_stats)}")
                lines.append(f"数据内容：{str(cluster_stats)[:500]}...")
        else:
            lines.append("无集群统计数据")
        lines.append("")
        
        # ========== 5. 分片信息 ==========
        lines.append("="*100)
        lines.append("【5】分片信息 (shards)")
        lines.append("="*100)
        shards = self.data.get('shards', [])
        
        if shards and isinstance(shards, list):
            lines.append(f"分片总数：{len(shards)}")
            lines.append("")
            
            # 统计主分片和副本分片
            primary_count = sum(1 for s in shards if isinstance(s, dict) and s.get('prirep') == 'p')
            replica_count = sum(1 for s in shards if isinstance(s, dict) and s.get('prirep') == 'r')
            
            lines.append("分片类型统计:")
            lines.append(f"  - 主分片 (P): {primary_count}")
            lines.append(f"  - 副本分片 (R): {replica_count}")
            lines.append(f"  - 副本比例：{replica_count/primary_count:.2f}" if primary_count > 0 else "  - 副本比例：N/A")
            lines.append("")
            
            # 按索引分组统计
            index_shard_count = {}
            for shard in shards:
                if isinstance(shard, dict):
                    index_name = shard.get('index', 'unknown')
                    index_shard_count[index_name] = index_shard_count.get(index_name, 0) + 1
            
            lines.append(f"索引分片分布 (Top 20):")
            lines.append("-"*80)
            lines.append(f"{'排名':<4} {'索引名称':<40} {'分片数':<10}")
            lines.append("-"*80)
            
            sorted_index_shards = sorted(index_shard_count.items(), key=lambda x: x[1], reverse=True)[:20]
            for i, (index_name, count) in enumerate(sorted_index_shards, 1):
                name = index_name[:40]
                lines.append(f"{i:<4} {name:<40} {count:<10}")
            
            lines.append("-"*80)
        else:
            lines.append("无分片详细信息")
        lines.append("")
        
        # ========== 6. 分片分配信息 ==========
        lines.append("="*100)
        lines.append("【6】分片分配信息 (allocation)")
        lines.append("="*100)
        allocation = self.data.get('allocation', [])
        
        if allocation and isinstance(allocation, list):
            lines.append(f"分配记录数：{len(allocation)}")
            lines.append("")
            
            # 显示前 20 条分配记录
            lines.append("分片分配详情 (前 20 条):")
            lines.append("-"*100)
            lines.append(f"{'序号':<4} {'索引':<30} {'分片':<8} {'节点':<20} {'状态':<15}")
            lines.append("-"*100)
            
            for i, alloc in enumerate(allocation[:20], 1):
                if isinstance(alloc, dict):
                    index_name = alloc.get('index', 'N/A')[:30]
                    shard = alloc.get('shard', 'N/A')
                    node = alloc.get('node', 'N/A')[:20]
                    state = alloc.get('state', 'N/A')[:15]
                    lines.append(f"{i:<4} {index_name:<30} {shard:<8} {node:<20} {state:<15}")
            
            lines.append("-"*100)
            if len(allocation) > 20:
                lines.append(f"... 还有 {len(allocation) - 20} 条记录")
        else:
            lines.append("无分片分配详细信息")
        lines.append("")
        
        # ========== 7. 智能解读结果 ==========
        if self.interpretation:
            lines.append("="*100)
            lines.append("【7】智能解读结果")
            lines.append("="*100)
            
            # 健康评估
            health_analysis = self.interpretation.get('cluster_health', {})
            lines.append("健康度评估:")
            lines.append(f"  - 健康等级：{health_analysis.get('health_level', 'N/A')}")
            lines.append(f"  - 状态评分：{health_analysis.get('status_score', 0)}/100")
            lines.append("")
            
            # 发现的问题
            issues = self.interpretation.get('issues', [])
            lines.append(f"发现的问题：{len(issues)} 个")
            for i, issue in enumerate(issues, 1):
                severity = issue.get('severity', 'info').upper()
                category = issue.get('category', 'N/A')
                title = issue.get('title', 'N/A')
                description = issue.get('description', 'N/A')
                suggestion = issue.get('suggestion', 'N/A')
                
                lines.append(f"  {i}. [{severity}] {category} - {title}")
                lines.append(f"     描述：{description}")
                lines.append(f"     建议：{suggestion}")
            if not issues:
                lines.append("  ✅ 未发现明显问题")
            lines.append("")
            
            # 优化建议
            recommendations = self.interpretation.get('recommendations', [])
            lines.append(f"优化建议：{len(recommendations)} 条")
            for i, rec in enumerate(recommendations, 1):
                priority = rec.get('priority', 'info').upper()
                category = rec.get('category', 'N/A')
                title = rec.get('title', 'N/A')
                description = rec.get('description', 'N/A')
                action = rec.get('action', 'N/A')
                
                lines.append(f"  {i}. [{priority}] {category} - {title}")
                lines.append(f"     {description}")
                if action:
                    lines.append(f"     操作：{action}")
            lines.append("")
        
        # ========== 报告尾部 ==========
        lines.append("="*100)
        lines.append("报告结束")
        lines.append("="*100)
        lines.append("")
        lines.append(f"完整数据结构请查看 JSON 文件：{self.diagnostic_json}")
        if self.interpretation:
            lines.append(f"智能解读数据请查看 JSON 文件：{self.interpretation_json}")
        lines.append("")
        
        # 写入文件
        content = '\n'.join(lines)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"完整数据报告已生成：{output_path}")
        return str(output_path)


def main():
    """主函数"""
    import sys
    
    # 配置日志
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # 查找最新的诊断数据 JSON
    out_dir = Path("out")
    if not out_dir.exists():
        logger.error("输出目录不存在，请先运行 diagnostic_extractor")
        sys.exit(1)
    
    diagnostic_files = sorted(out_dir.glob("diagnostic_data_*.json"))
    if not diagnostic_files:
        logger.error("未找到诊断数据文件")
        sys.exit(1)
    
    latest_diagnostic = diagnostic_files[-1]
    logger.info(f"使用诊断数据：{latest_diagnostic.name}")
    
    # 查找对应的解读结果
    analysis_dir = out_dir / "analysis"
    interpretation_files = sorted(analysis_dir.glob("interpretation_*.json")) if analysis_dir.exists() else []
    latest_interpretation = interpretation_files[-1] if interpretation_files else None
    
    if latest_interpretation:
        logger.info(f"使用解读数据：{latest_interpretation.name}")
    else:
        logger.warning("未找到解读数据，仅生成原始数据报告")
    
    # 生成完整报告
    generator = FullDataReportGenerator(
        str(latest_diagnostic),
        str(latest_interpretation) if latest_interpretation else None
    )
    
    output_path = generator.generate_full_report()
    
    logger.info(f"✓ 完整数据报告已生成!")
    logger.info(f"  文件位置：{output_path}")
    
    # 打印摘要
    print("\n" + "="*60)
    print("报告生成摘要")
    print("="*60)
    
    with open(output_path, 'r', encoding='utf-8') as f:
        line_count = sum(1 for _ in f)
    
    print(f"报告文件：{output_path}")
    print(f"报告行数：{line_count}")
    print(f"报告大小：{Path(output_path).stat().st_size / 1024:.1f} KB")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
