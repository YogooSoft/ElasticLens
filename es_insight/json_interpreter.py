"""ES 集群诊断数据深度解读器 - 将解析后的 JSON 数据进行智能分析并生成报告"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict
from loguru import logger


class DiagnosticDataInterpreter:
    """诊断数据深度解读器"""
    
    def __init__(self, json_file: str, output_dir: str = None):
        """
        初始化解读器
        
        Args:
            json_file: 输入的 JSON 文件路径
            output_dir: 输出目录（默认为 out/analysis）
        """
        self.json_file = Path(json_file)
        self.output_dir = Path(output_dir) if output_dir else Path("out/analysis")
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"解读器初始化完成，输出目录：{self.output_dir}")
        
        # 加载数据
        self.data = None
        self.load_data()
    
    def load_data(self):
        """加载 JSON 数据"""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            logger.info(f"成功加载数据：{self.json_file.name}")
        except Exception as e:
            logger.error(f"加载数据失败：{e}")
            raise
    
    def interpret_all(self) -> Dict[str, Any]:
        """
        执行完整解读
        
        Returns:
            包含所有解读结果的字典
        """
        results = {
            'metadata': self._interpret_metadata(),
            'cluster_health': self._interpret_cluster_health(),
            'nodes_analysis': self._interpret_nodes(),
            'indices_analysis': self._interpret_indices(),
            'resource_analysis': self._interpret_resources(),
            'shards_analysis': self._interpret_shards(),
            'issues': self._identify_issues(),
            'recommendations': self._generate_recommendations()
        }
        
        return results
    
    def _interpret_metadata(self) -> Dict:
        """解读元数据"""
        meta = self.data.get('metadata', {})
        return {
            'source': meta.get('source', '未知'),
            'extracted_at': meta.get('extracted_at', '未知'),
            'data_quality': '完整' if all(k in self.data for k in ['cluster_health', 'nodes', 'indices']) else '不完整'
        }
    
    def _interpret_cluster_health(self) -> Dict:
        """解读集群健康状态"""
        health = self.data.get('cluster_health', {})
        
        # 状态评估
        status = health.get('status', 'unknown')
        status_score = {'green': 100, 'yellow': 60, 'red': 0}.get(status, 0)
        
        # 分片健康度
        active_percent = health.get('active_shards_percent', 0)
        unassigned = health.get('unassigned_shards', 0)
        
        # 集群规模评估
        nodes_count = health.get('number_of_nodes', 0)
        data_nodes = health.get('number_of_data_nodes', 0)
        scale_level = '大型' if nodes_count > 30 else '中型' if nodes_count > 10 else '小型'
        
        return {
            'cluster_name': health.get('cluster_name', '未知'),
            'status': status,
            'status_score': status_score,
            'health_level': self._get_health_level(status_score),
            
            'scale': {
                'total_nodes': nodes_count,
                'data_nodes': data_nodes,
                'master_nodes': nodes_count - data_nodes,
                'scale_level': scale_level
            },
            
            'shards_overview': {
                'total_active': health.get('active_shards', 0),
                'primary_shards': health.get('active_primary_shards', 0),
                'replica_shards': health.get('active_shards', 0) - health.get('active_primary_shards', 0),
                'relocating': health.get('relocating_shards', 0),
                'initializing': health.get('initializing_shards', 0),
                'unassigned': unassigned,
                'active_percent': active_percent
            },
            
            'assessment': self._assess_health(health)
        }
    
    def _interpret_nodes(self) -> Dict:
        """解读节点信息"""
        nodes = self.data.get('nodes', [])
        
        if not nodes:
            return {'error': '无节点数据'}
        
        # 角色分布
        role_distribution = defaultdict(int)
        for node in nodes:
            for role in node.get('roles', []):
                role_distribution[role] += 1
        
        # 主节点识别
        master_nodes = [n for n in nodes if n.get('is_master')]
        
        # 资源统计（仅统计有数据的节点）
        cpu_values = [n['cpu_percent'] for n in nodes if n.get('cpu_percent', 0) > 0]
        heap_values = [n['heap_used_percent'] for n in nodes if n.get('heap_used_percent', 0) > 0]
        disk_values = [n['disk_used_percent'] for n in nodes if n.get('disk_used_percent', 0) > 0]
        shard_values = [n['shard_count'] for n in nodes if n.get('shard_count', 0) > 0]
        
        # 节点类型分类
        node_types = defaultdict(list)
        for node in nodes:
            roles = tuple(sorted(node.get('roles', [])))
            node_types[roles].append(node['name'])
        
        return {
            'total_count': len(nodes),
            'master_nodes': [n['name'] for n in master_nodes],
            'master_count': len(master_nodes),
            
            'role_distribution': dict(role_distribution),
            'node_types': {str(k): v for k, v in node_types.items()},
            
            'resource_statistics': {
                'cpu': {
                    'avg': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                    'max': max(cpu_values) if cpu_values else 0,
                    'min': min(cpu_values) if cpu_values else 0,
                    'sample_count': len(cpu_values)
                },
                'memory': {
                    'avg': sum(heap_values) / len(heap_values) if heap_values else 0,
                    'max': max(heap_values) if heap_values else 0,
                    'min': min(heap_values) if heap_values else 0,
                    'sample_count': len(heap_values)
                },
                'disk': {
                    'avg': sum(disk_values) / len(disk_values) if disk_values else 0,
                    'max': max(disk_values) if disk_values else 0,
                    'min': min(disk_values) if disk_values else 0,
                    'sample_count': len(disk_values)
                },
                'shards': {
                    'avg': sum(shard_values) / len(shard_values) if shard_values else 0,
                    'max': max(shard_values) if shard_values else 0,
                    'min': min(shard_values) if shard_values else 0,
                    'total': sum(shard_values),
                    'sample_count': len(shard_values)
                }
            },
            
            'load_analysis': self._analyze_node_load(nodes)
        }
    
    def _interpret_indices(self) -> Dict:
        """解读索引信息"""
        indices = self.data.get('indices', [])
        
        if not indices:
            return {'error': '无索引数据'}
        
        # 健康状态统计
        health_dist = defaultdict(int)
        for idx in indices:
            health = idx.get('health', 'unknown')
            health_dist[health] += 1
        
        # 文档统计
        total_docs = sum(idx.get('docs_count', 0) for idx in indices)
        deleted_docs = 0  # 数据中没有 docs_deleted 字段
        
        # 存储统计
        total_size = sum(idx.get('store_size_bytes', 0) for idx in indices)
        primary_size = total_size // 2  # 估算值
        
        # 分片统计
        total_shards = sum(idx.get('primary_shards', 0) for idx in indices)
        total_replicas = sum(idx.get('replica_shards', 0) for idx in indices)
        
        # 按大小排序的前 10 个索引
        top_indices_by_size = sorted(
            [{'name': idx.get('name', 'unknown'), 'size_gb': idx.get('store_size_bytes', 0) / (1024**3)} 
             for idx in indices],
            key=lambda x: x['size_gb'],
            reverse=True
        )[:10]
        
        return {
            'total_count': len(indices),
            'health_distribution': dict(health_dist),
            'health_rate': {
                'green': health_dist.get('green', 0) / len(indices) * 100 if indices else 0,
                'yellow': health_dist.get('yellow', 0) / len(indices) * 100 if indices else 0,
                'red': health_dist.get('red', 0) / len(indices) * 100 if indices else 0
            },
            
            'documents': {
                'total': total_docs,
                'deleted': deleted_docs,
                'deleted_rate': 0  # 无删除数据
            },
            
            'storage': {
                'total_size_gb': total_size / (1024**3),
                'primary_size_gb': primary_size / (1024**3),
                'replica_size_gb': (total_size - primary_size) / (1024**3),
                'replica_ratio': (total_size - primary_size) / primary_size if primary_size > 0 else 0
            },
            
            'shards': {
                'total_shards': total_shards,
                'avg_replicas': total_replicas / len(indices) if indices else 0
            },
            
            'top_indices': top_indices_by_size
        }
    
    def _interpret_resources(self) -> Dict:
        """解读资源使用情况"""
        nodes = self.data.get('nodes', [])
        
        if not nodes:
            return {'error': '无节点数据'}
        
        # 找出高负载节点
        high_cpu_nodes = []
        high_memory_nodes = []
        high_disk_nodes = []
        
        for node in nodes:
            if node.get('cpu_percent', 0) > 70:
                high_cpu_nodes.append({
                    'name': node['name'],
                    'value': node['cpu_percent']
                })
            if node.get('heap_used_percent', 0) > 70:
                high_memory_nodes.append({
                    'name': node['name'],
                    'value': node['heap_used_percent']
                })
            if node.get('disk_used_percent', 0) > 70:
                high_disk_nodes.append({
                    'name': node['name'],
                    'value': node['disk_used_percent']
                })
        
        # 资源均衡性分析
        cpu_values = [n['cpu_percent'] for n in nodes if n.get('cpu_percent', 0) > 0]
        heap_values = [n['heap_used_percent'] for n in nodes if n.get('heap_used_percent', 0) > 0]
        disk_values = [n['disk_used_percent'] for n in nodes if n.get('disk_used_percent', 0) > 0]
        
        def calc_imbalance(values):
            if not values:
                return 0
            avg = sum(values) / len(values)
            if avg == 0:
                return 0
            return max(abs(v - avg) / avg * 100 for v in values)
        
        return {
            'overall_status': '正常' if not (high_cpu_nodes or high_memory_nodes or high_disk_nodes) else '需关注',
            
            'cpu_usage': {
                'high_load_nodes': high_cpu_nodes,
                'count': len(high_cpu_nodes),
                'imbalance_rate': calc_imbalance(cpu_values)
            },
            
            'memory_usage': {
                'high_load_nodes': high_memory_nodes,
                'count': len(high_memory_nodes),
                'imbalance_rate': calc_imbalance(heap_values)
            },
            
            'disk_usage': {
                'high_load_nodes': high_disk_nodes,
                'count': len(high_disk_nodes),
                'imbalance_rate': calc_imbalance(disk_values)
            }
        }
    
    def _interpret_shards(self) -> Dict:
        """解读分片分布"""
        shards = self.data.get('shards', [])
        
        if not shards:
            return {'error': '无分片数据'}
        
        # 分片类型统计
        primary_count = 0
        replica_count = 0
        
        for shard in shards:
            if isinstance(shard, dict):
                if shard.get('prirep') == 'p':
                    primary_count += 1
                elif shard.get('prirep') == 'r':
                    replica_count += 1
        
        return {
            'total_shards': len(shards),
            'primary_shards': primary_count,
            'replica_shards': replica_count,
            'replica_ratio': replica_count / primary_count if primary_count > 0 else 0
        }
    
    def _identify_issues(self) -> List[Dict]:
        """识别潜在问题"""
        issues = []
        
        # 检查集群状态
        health = self.data.get('cluster_health', {})
        if health.get('status') == 'red':
            issues.append({
                'severity': 'critical',
                'category': '集群健康',
                'title': '集群状态为红色',
                'description': f"集群 {health.get('cluster_name')} 处于红色状态，存在未分配的主分片",
                'impact': '部分数据不可用，影响业务',
                'suggestion': '立即检查未分配分片原因并处理'
            })
        elif health.get('status') == 'yellow':
            issues.append({
                'severity': 'warning',
                'category': '集群健康',
                'title': '集群状态为黄色',
                'description': '副本分片未完全分配',
                'impact': '数据冗余度不足，存在风险',
                'suggestion': '检查集群容量和节点状态'
            })
        
        # 检查未分配分片
        unassigned = health.get('unassigned_shards', 0)
        if unassigned > 0:
            issues.append({
                'severity': 'warning',
                'category': '分片分配',
                'title': f'存在 {unassigned} 个未分配分片',
                'description': '分片未能分配到任何节点',
                'impact': '影响数据完整性和查询性能',
                'suggestion': '使用 _cluster/allocation/explain API 查看原因'
            })
        
        # 检查高负载节点
        nodes = self.data.get('nodes', [])
        high_load_count = 0
        for node in nodes:
            if (node.get('cpu_percent', 0) > 80 or 
                node.get('heap_used_percent', 0) > 80 or 
                node.get('disk_used_percent', 0) > 80):
                high_load_count += 1
        
        if high_load_count > 0:
            issues.append({
                'severity': 'warning',
                'category': '资源负载',
                'title': f'{high_load_count} 个节点负载较高',
                'description': '节点 CPU、内存或磁盘使用率超过 80%',
                'impact': '可能影响集群性能和稳定性',
                'suggestion': '考虑扩容或优化资源使用'
            })
        
        # 检查索引健康度
        indices = self.data.get('indices', [])
        unhealthy_indices = [i for i in indices if i.get('health') in ['yellow', 'red']]
        if unhealthy_indices:
            issues.append({
                'severity': 'warning',
                'category': '索引健康',
                'title': f'{len(unhealthy_indices)} 个索引状态异常',
                'description': '存在黄色或红色状态的索引',
                'impact': '部分索引数据可能不可用或冗余不足',
                'suggestion': '检查异常索引的分片分配情况'
            })
        
        return issues
    
    def _generate_recommendations(self) -> List[Dict]:
        """生成优化建议"""
        recommendations = []
        
        # 基于集群状态
        health = self.data.get('cluster_health', {})
        if health.get('status') == 'green':
            recommendations.append({
                'category': '日常运维',
                'priority': 'low',
                'title': '保持定期巡检',
                'description': '集群状态良好，建议继续保持定期监控和巡检'
            })
        
        # 基于资源使用
        nodes = self.data.get('nodes', [])
        avg_heap = sum(n.get('heap_used_percent', 0) for n in nodes) / len(nodes) if nodes else 0
        if avg_heap > 60:
            recommendations.append({
                'category': '内存优化',
                'priority': 'medium',
                'title': '优化 JVM 堆内存使用',
                'description': f'平均堆内存使用率 {avg_heap:.1f}%，建议关注 GC 情况',
                'action': '监控 GC 频率，必要时增加堆内存或优化查询'
            })
        
        # 基于分片数量
        if health.get('active_shards', 0) > 1000:
            recommendations.append({
                'category': '分片优化',
                'priority': 'medium',
                'title': '评估分片数量',
                'description': f'当前活跃分片数 {health.get("active_shards", 0)}，数量较大',
                'action': '定期评估分片大小，避免过多小分片'
            })
        
        # 基于索引健康
        indices = self.data.get('indices', [])
        if indices:
            avg_replicas = sum(i.get('replicas', 0) for i in indices) / len(indices)
            if avg_replicas < 1:
                recommendations.append({
                    'category': '数据安全',
                    'priority': 'high',
                    'title': '增加副本数量',
                    'description': f'平均副本数 {avg_replicas:.1f}，建议至少设置为 1',
                    'action': '为重要索引增加副本以提高容灾能力'
                })
        
        return recommendations
    
    def _assess_health(self, health: Dict) -> str:
        """评估健康等级"""
        score = 100
        
        # 状态扣分
        status = health.get('status', 'green')
        if status == 'yellow':
            score -= 30
        elif status == 'red':
            score -= 80
        
        # 未分配分片扣分
        unassigned = health.get('unassigned_shards', 0)
        if unassigned > 0:
            score -= min(unassigned * 2, 20)
        
        # 迁移中的分片扣分
        relocating = health.get('relocating_shards', 0)
        initializing = health.get('initializing_shards', 0)
        if relocating > 0 or initializing > 0:
            score -= 5
        
        if score >= 90:
            return '优秀'
        elif score >= 75:
            return '良好'
        elif score >= 60:
            return '一般'
        elif score >= 40:
            return '需关注'
        else:
            return '严重'
    
    def _analyze_node_load(self, nodes: List[Dict]) -> Dict:
        """分析节点负载"""
        load_categories = {
            'low': [],
            'medium': [],
            'high': [],
            'critical': []
        }
        
        for node in nodes:
            cpu = node.get('cpu_percent', 0)
            heap = node.get('heap_used_percent', 0)
            disk = node.get('disk_used_percent', 0)
            
            # 综合评分
            avg_load = (cpu + heap + disk) / 3
            
            if avg_load < 40:
                load_categories['low'].append(node['name'])
            elif avg_load < 60:
                load_categories['medium'].append(node['name'])
            elif avg_load < 80:
                load_categories['high'].append(node['name'])
            else:
                load_categories['critical'].append(node['name'])
        
        return load_categories
    
    def _get_health_level(self, score: int) -> str:
        """根据分数获取健康等级"""
        if score >= 90:
            return '优秀'
        elif score >= 75:
            return '良好'
        elif score >= 60:
            return '一般'
        elif score >= 40:
            return '需关注'
        else:
            return '严重'
    
    def save_interpretation(self, results: Dict[str, Any]):
        """保存解读结果"""
        # 保存为 JSON
        json_path = self.output_dir / f"interpretation_{self.timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"解读结果已保存：{json_path}")
        
        # 生成文本报告
        txt_path = self.output_dir / f"interpretation_report_{self.timestamp}.txt"
        self._generate_text_report(results, txt_path)
        
        return json_path, txt_path
    
    def _generate_text_report(self, results: Dict, output_path: Path):
        """生成文本格式的报告"""
        lines = []
        
        # 标题
        lines.append("="*80)
        lines.append("ES 集群诊断数据深度解读报告")
        lines.append("="*80)
        lines.append("")
        
        # 基本信息
        meta = results.get('metadata', {})
        lines.append(f"📁 数据来源：{meta.get('source', 'N/A')}")
        lines.append(f"⏰ 提取时间：{meta.get('extracted_at', 'N/A')}")
        lines.append(f"📊 数据质量：{meta.get('data_quality', 'N/A')}")
        lines.append("")
        
        # 集群健康
        health = results.get('cluster_health', {})
        lines.append("-"*80)
        lines.append("🏥 集群健康评估")
        lines.append("-"*80)
        lines.append(f"集群名称：{health.get('cluster_name', 'N/A')}")
        lines.append(f"状态：{health.get('status', 'N/A').upper()}")
        lines.append(f"健康等级：{health.get('health_level', 'N/A')}")
        lines.append(f"状态评分：{health.get('status_score', 0)}/100")
        lines.append("")
        
        scale = health.get('scale', {})
        lines.append(f"集群规模：{scale.get('scale_level', 'N/A')}")
        lines.append(f"  - 总节点数：{scale.get('total_nodes', 0)}")
        lines.append(f"  - 数据节点：{scale.get('data_nodes', 0)}")
        lines.append(f"  - 主节点：{scale.get('master_nodes', 0)}")
        lines.append("")
        
        shards = health.get('shards_overview', {})
        lines.append(f"分片概况:")
        lines.append(f"  - 活跃分片：{shards.get('total_active', 0)}")
        lines.append(f"  - 主分片：{shards.get('primary_shards', 0)}")
        lines.append(f"  - 副本分片：{shards.get('replica_shards', 0)}")
        lines.append(f"  - 未分配：{shards.get('unassigned', 0)}")
        lines.append("")
        
        # 节点分析
        nodes = results.get('nodes_analysis', {})
        lines.append("-"*80)
        lines.append("💻 节点分析")
        lines.append("-"*80)
        lines.append(f"节点总数：{nodes.get('total_count', 0)}")
        lines.append(f"主节点：{', '.join(nodes.get('master_nodes', [])) or 'N/A'}")
        lines.append("")
        
        lines.append("角色分布:")
        for role, count in nodes.get('role_distribution', {}).items():
            lines.append(f"  - {role}: {count} 个节点")
        lines.append("")
        
        resource_stats = nodes.get('resource_statistics', {})
        lines.append("资源统计:")
        
        cpu = resource_stats.get('cpu', {})
        lines.append(f"  CPU:  平均 {cpu.get('avg', 0):.1f}% | 最高 {cpu.get('max', 0):.1f}%")
        
        mem = resource_stats.get('memory', {})
        lines.append(f"  内存：平均 {mem.get('avg', 0):.1f}% | 最高 {mem.get('max', 0):.1f}%")
        
        disk = resource_stats.get('disk', {})
        lines.append(f"  磁盘：平均 {disk.get('avg', 0):.1f}% | 最高 {disk.get('max', 0):.1f}%")
        lines.append("")
        
        # 索引分析
        indices = results.get('indices_analysis', {})
        lines.append("-"*80)
        lines.append("📑 索引分析")
        lines.append("-"*80)
        lines.append(f"索引总数：{indices.get('total_count', 0)}")
        lines.append("")
        
        health_dist = indices.get('health_distribution', {})
        lines.append("健康分布:")
        lines.append(f"  ✅ 绿色：{health_dist.get('green', 0)} ({indices.get('health_rate', {}).get('green', 0):.1f}%)")
        lines.append(f"  ⚠️ 黄色：{health_dist.get('yellow', 0)} ({indices.get('health_rate', {}).get('yellow', 0):.1f}%)")
        lines.append(f"  🔴 红色：{health_dist.get('red', 0)} ({indices.get('health_rate', {}).get('red', 0):.1f}%)")
        lines.append("")
        
        docs = indices.get('documents', {})
        lines.append(f"文档统计:")
        lines.append(f"  - 总文档数：{docs.get('total', 0):,}")
        lines.append(f"  - 已删除：{docs.get('deleted', 0):,} ({docs.get('deleted_rate', 0):.1f}%)")
        lines.append("")
        
        storage = indices.get('storage', {})
        lines.append(f"存储统计:")
        lines.append(f"  - 总大小：{storage.get('total_size_gb', 0):.2f} GB")
        lines.append(f"  - 主分片：{storage.get('primary_size_gb', 0):.2f} GB")
        lines.append(f"  - 副本：{storage.get('replica_size_gb', 0):.2f} GB")
        lines.append("")
        
        # 发现的问题
        issues = results.get('issues', [])
        if issues:
            lines.append("-"*80)
            lines.append("⚠️ 发现的问题")
            lines.append("-"*80)
            for i, issue in enumerate(issues, 1):
                severity_icon = {'critical': '🔴', 'warning': '⚠️', 'info': 'ℹ️'}.get(issue.get('severity'), '•')
                lines.append(f"{i}. {severity_icon} [{issue.get('category', 'N/A')}] {issue.get('title', 'N/A')}")
                lines.append(f"   描述：{issue.get('description', 'N/A')}")
                lines.append(f"   影响：{issue.get('impact', 'N/A')}")
                lines.append(f"   建议：{issue.get('suggestion', 'N/A')}")
                lines.append("")
        
        # 优化建议
        recommendations = results.get('recommendations', [])
        if recommendations:
            lines.append("-"*80)
            lines.append("💡 优化建议")
            lines.append("-"*80)
            for i, rec in enumerate(recommendations, 1):
                priority_icon = {'high': '🔴', 'medium': '⚠️', 'low': '✅'}.get(rec.get('priority'), '•')
                lines.append(f"{i}. {priority_icon} [{rec.get('category', 'N/A')}] {rec.get('title', 'N/A')}")
                lines.append(f"   {rec.get('description', 'N/A')}")
                if rec.get('action'):
                    lines.append(f"   操作：{rec.get('action', 'N/A')}")
                lines.append("")
        
        lines.append("="*80)
        lines.append("报告结束")
        lines.append("="*80)
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"文本报告已保存：{output_path}")
    
    def interpret_and_save(self) -> tuple:
        """执行解读并保存"""
        results = self.interpret_all()
        return self.save_interpretation(results)


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
    
    # 查找最新的 JSON 文件
    out_dir = Path("out")
    if not out_dir.exists():
        logger.error("输出目录不存在，请先运行 diagnostic_extractor")
        sys.exit(1)
    
    json_files = sorted(out_dir.glob("diagnostic_data_*.json"))
    if not json_files:
        logger.error("未找到诊断数据文件，请先运行 diagnostic_extractor")
        sys.exit(1)
    
    latest_json = json_files[-1]
    logger.info(f"使用文件：{latest_json.name}")
    
    # 创建解读器并执行
    interpreter = DiagnosticDataInterpreter(str(latest_json))
    json_path, txt_path = interpreter.interpret_and_save()
    
    logger.info(f"✓ 解读完成!")
    logger.info(f"  JSON 结果：{json_path}")
    logger.info(f"  文本报告：{txt_path}")
    
    # 打印摘要
    print("\n" + "="*60)
    print("解读摘要")
    print("="*60)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    health = results.get('cluster_health', {})
    print(f"集群：{health.get('cluster_name', 'N/A')}")
    print(f"状态：{health.get('status', 'N/A').upper()}")
    print(f"健康等级：{health.get('health_level', 'N/A')}")
    print(f"发现问题：{len(results.get('issues', []))} 个")
    print(f"优化建议：{len(results.get('recommendations', []))} 条")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
