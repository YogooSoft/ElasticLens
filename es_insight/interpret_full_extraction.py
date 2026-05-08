"""全量提取数据解读器 - 深度分析和解读全量提取的 JSON 数据"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from loguru import logger


class FullExtractionInterpreter:
    """全量提取数据解读器"""
    
    def __init__(self, extraction_json: str):
        """
        初始化解读器
        
        Args:
            extraction_json: 全量提取的 JSON 文件路径
        """
        self.extraction_json = Path(extraction_json)
        self.output_dir = Path("out/analysis")
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载数据
        self.data = None
        self.load_data()
    
    def load_data(self):
        """加载 JSON 数据"""
        try:
            file_size_mb = self.extraction_json.stat().st_size / (1024 * 1024)
            logger.info(f"开始加载全量数据：{self.extraction_json.name} ({file_size_mb:.2f} MB)")
            
            with open(self.extraction_json, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            logger.info(f"成功加载数据，包含 {len(self.data.get('files_manifest', {}))} 个文件")
        except Exception as e:
            logger.error(f"加载数据失败：{e}")
            raise
    
    def interpret_all(self) -> dict:
        """
        执行完整解读
        
        Returns:
            包含所有解读结果的字典
        """
        results = {
            'metadata': self._interpret_metadata(),
            'overview': self._generate_overview(),
            'cluster_health_analysis': self._analyze_cluster_health(),
            'nodes_deep_analysis': self._deep_analyze_nodes(),
            'indices_deep_analysis': self._deep_analyze_indices(),
            'performance_metrics': self._analyze_performance_metrics(),
            'security_analysis': self._analyze_security(),
            'ml_features_analysis': self._analyze_ml_features(),
            'ilm_analysis': self._analyze_ilm(),
            'key_findings': self._extract_key_findings(),
            'recommendations': self._generate_recommendations()
        }
        
        return results
    
    def _interpret_metadata(self) -> dict:
        """解读元数据"""
        meta = self.data.get('metadata', {})
        return {
            'source': meta.get('source', 'N/A'),
            'extracted_at': meta.get('extracted_at', 'N/A'),
            'total_files': meta.get('total_files', 0),
            'total_size_mb': meta.get('total_size_mb', 0),
            'extraction_mode': meta.get('extraction_mode', 'full')
        }
    
    def _generate_overview(self) -> dict:
        """生成数据概览"""
        manifest = self.data.get('files_manifest', {})
        
        # 按目录分组
        root_files = []
        subdirs = defaultdict(list)
        
        for path in manifest.keys():
            parts = path.split('/')
            if len(parts) == 1:
                root_files.append(path)
            else:
                subdirs[parts[0]].append('/'.join(parts[1:]))
        
        # 统计各类文件
        file_categories = {
            'cluster_info': ['cluster_health.json', 'cluster_stats.json', 'cluster_state.json'],
            'nodes': [f for f in root_files if f.startswith('nodes')],
            'indices': [f for f in root_files if f.startswith('indices') or f == 'indices.json'],
            'shards': [f for f in root_files if 'shard' in f],
            'settings': [f for f in root_files if 'settings' in f or 'config' in f],
            'templates': [f for f in root_files if 'template' in f],
            'security': [f for f in manifest.keys() if 'security' in f.lower()],
            'ml': [f for f in manifest.keys() if '/ml_' in f.lower()],
            'ilm': [f for f in manifest.keys() if '/ilm_' in f.lower()]
        }
        
        return {
            'total_files': len(manifest),
            'root_files_count': len(root_files),
            'subdirs_count': len(subdirs),
            'subdirs_details': {k: len(v) for k, v in subdirs.items()},
            'file_categories': {k: len(v) for k, v in file_categories.items()}
        }
    
    def _analyze_cluster_health(self) -> dict:
        """分析集群健康"""
        health_data = self._get_file_data('cluster_health.json')
        stats_data = self._get_file_data('cluster_stats.json')
        
        if not health_data:
            return {'error': '无集群健康数据'}
        
        return {
            'cluster_name': health_data.get('cluster_name', 'N/A'),
            'status': health_data.get('status', 'N/A'),
            'health_score': self._calculate_health_score(health_data),
            'nodes_summary': {
                'total': health_data.get('number_of_nodes', 0),
                'data_nodes': health_data.get('number_of_data_nodes', 0),
                'master_nodes': health_data.get('number_of_nodes', 0) - health_data.get('number_of_data_nodes', 0)
            },
            'shards_summary': {
                'active_shards': health_data.get('active_shards', 0),
                'primary_shards': health_data.get('active_primary_shards', 0),
                'unassigned': health_data.get('unassigned_shards', 0),
                'relocating': health_data.get('relocating_shards', 0),
                'initializing': health_data.get('initializing_shards', 0),
                'active_percent': health_data.get('active_shards_percent', 0)
            },
            'indices_summary': stats_data.get('indices', {}) if stats_data else {}
        }
    
    def _deep_analyze_nodes(self) -> dict:
        """深度分析节点信息"""
        nodes_short = self._get_file_data('nodes_short.json')
        nodes_stats = self._get_file_data('nodes_stats.json')
        nodes_usage = self._get_file_data('nodes_usage.json')
        
        result = {
            'basic_info': {
                'count': len(nodes_short) if nodes_short else 0,
                'nodes_list': nodes_short[:5] if nodes_short else []  # 只显示前 5 个
            },
            'stats_available': nodes_stats is not None,
            'usage_available': nodes_usage is not None
        }
        
        if nodes_stats:
            result['jvm_stats'] = self._extract_jvm_stats(nodes_stats)
            result['os_stats'] = self._extract_os_stats(nodes_stats)
        
        return result
    
    def _deep_analyze_indices(self) -> dict:
        """深度分析索引信息"""
        # 精确匹配 indices.json，避免匹配到 dangling_indices.json
        indices = None
        indices_stats = None
        
        manifest = self.data.get('files_manifest', {})
        for path in manifest.keys():
            if path == 'indices.json' or path.endswith('/indices.json'):
                indices = manifest[path].get('data')
                break
        
        # 查找 indices_stats.json
        for path in manifest.keys():
            if path == 'indices_stats.json' or path.endswith('/indices_stats.json'):
                indices_stats = manifest[path].get('data')
                break
        
        if not indices:
            return {'error': '无索引数据'}
        
        # indices.json 可能是字典格式（索引名->详情）或列表格式
        if isinstance(indices, dict):
            # 转换为列表格式
            indices_list = []
            for name, info in indices.items():
                if isinstance(info, dict):
                    info['name'] = name
                    indices_list.append(info)
            indices = indices_list
        elif not isinstance(indices, list):
            return {'error': '索引数据格式异常'}
        
        # 健康分布
        health_dist = defaultdict(int)
        for idx in indices:
            if isinstance(idx, dict):
                health = idx.get('health', 'unknown')
                health_dist[health] += 1
        
        # Top 10 大索引
        sorted_indices = sorted(
            [idx for idx in indices if isinstance(idx, dict)], 
            key=lambda x: x.get('docs_count', 0), 
            reverse=True
        )[:10]
        
        return {
            'total_count': len(indices),
            'health_distribution': dict(health_dist),
            'top_10_by_docs': [
                {
                    'name': idx.get('name', 'N/A'),
                    'docs': idx.get('docs_count', 0),
                    'size_gb': round(idx.get('store_size_bytes', 0) / (1024**3), 2)
                }
                for idx in sorted_indices
            ],
            'stats_available': indices_stats is not None
        }
    
    def _analyze_performance_metrics(self) -> dict:
        """分析性能指标"""
        result = {
            'available_files': [],
            'highlights': []
        }
        
        # 检查可用的性能相关文件
        perf_files = {
            'nodes_stats.json': '节点详细统计',
            'nodes_usage.json': '节点使用情况',
            'tasks.json': '任务执行情况',
            'fielddata_stats.json': '字段数据使用',
            'recovery.json': '恢复进度'
        }
        
        for filename, description in perf_files.items():
            if self._file_exists(filename):
                result['available_files'].append({
                    'file': filename,
                    'description': description
                })
        
        return result
    
    def _analyze_security(self) -> dict:
        """分析安全配置"""
        security_files = [f for f in self.data.get('files_manifest', {}).keys() 
                         if 'security' in f.lower()]
        
        if not security_files:
            return {'status': '未找到安全配置文件'}
        
        result = {
            'files_found': security_files,
            'users_count': 0,
            'roles_count': 0
        }
        
        # 尝试读取用户和角色
        users_data = self._get_file_data('commercial/security_users.json')
        roles_data = self._get_file_data('commercial/security_roles.json')
        
        if users_data and isinstance(users_data, list):
            result['users_count'] = len(users_data)
        
        if roles_data and isinstance(roles_data, list):
            result['roles_count'] = len(roles_data)
        
        return result
    
    def _analyze_ml_features(self) -> dict:
        """分析机器学习功能"""
        ml_files = [f for f in self.data.get('files_manifest', {}).keys() 
                   if '/ml_' in f.lower()]
        
        if not ml_files:
            return {'status': '未使用 ML 功能'}
        
        result = {
            'ml_files_count': len(ml_files),
            'detectors_count': 0,
            'datafeeds_count': 0,
            'models_count': 0
        }
        
        # 尝试读取 ML 统计
        ml_info = self._get_file_data('commercial/ml_info.json')
        if ml_info:
            result['detectors_count'] = ml_info.get('anomaly_detectors', {}).get('count', 0)
            result['datafeeds_count'] = ml_info.get('datafeeds', {}).get('count', 0)
        
        return result
    
    def _analyze_ilm(self) -> dict:
        """分析索引生命周期管理"""
        ilm_files = [f for f in self.data.get('files_manifest', {}).keys() 
                    if '/ilm_' in f.lower()]
        
        if not ilm_files:
            return {'status': '未配置 ILM'}
        
        result = {
            'ilm_files': ilm_files,
            'policies_count': 0,
            'managed_indices_count': 0
        }
        
        # 尝试读取 ILM 策略
        ilm_policies = self._get_file_data('commercial/ilm_policies.json')
        if ilm_policies and isinstance(ilm_policies, dict):
            result['policies_count'] = len(ilm_policies)
        
        return result
    
    def _extract_key_findings(self) -> list:
        """提取关键发现"""
        findings = []
        
        # 1. 集群状态
        health = self._get_file_data('cluster_health.json')
        if health:
            status = health.get('status', 'unknown')
            if status == 'green':
                findings.append({
                    'category': '集群健康',
                    'finding': '集群状态良好（GREEN）',
                    'severity': 'info'
                })
            elif status == 'yellow':
                findings.append({
                    'category': '集群健康',
                    'finding': '集群状态警告（YELLOW），可能存在副本未分配',
                    'severity': 'warning'
                })
            elif status == 'red':
                findings.append({
                    'category': '集群健康',
                    'finding': '集群状态严重（RED），主分片未分配',
                    'severity': 'critical'
                })
            
            # 未分配分片
            unassigned = health.get('unassigned_shards', 0)
            if unassigned > 0:
                findings.append({
                    'category': '分片分配',
                    'finding': f'存在 {unassigned} 个未分配分片',
                    'severity': 'warning'
                })
        
        # 2. 数据完整性
        manifest = self.data.get('files_manifest', {})
        total_files = len(manifest)
        if total_files >= 80:
            findings.append({
                'category': '数据完整性',
                'finding': f'完整提取了 {total_files} 个 JSON 文件（100%）',
                'severity': 'info'
            })
        
        # 3. 高级功能使用情况
        security_files = [f for f in manifest.keys() if 'security' in f.lower()]
        if security_files:
            findings.append({
                'category': '安全功能',
                'finding': '启用了 X-Pack 安全功能',
                'severity': 'info'
            })
        
        ml_files = [f for f in manifest.keys() if '/ml_' in f.lower()]
        if ml_files:
            findings.append({
                'category': '机器学习',
                'finding': '使用了 ML 功能进行异常检测或其他分析',
                'severity': 'info'
            })
        
        return findings
    
    def _generate_recommendations(self) -> list:
        """生成优化建议"""
        recommendations = []
        
        # 基于集群状态
        health = self._get_file_data('cluster_health.json')
        if health and health.get('status') == 'green':
            recommendations.append({
                'priority': 'low',
                'category': '日常运维',
                'recommendation': '继续保持定期巡检和监控',
                'action': '建议每周运行一次诊断'
            })
        
        # 基于数据完整性
        recommendations.append({
            'priority': 'medium',
            'category': '数据管理',
            'recommendation': '定期归档全量诊断数据',
            'action': '保留历史数据用于趋势分析'
        })
        
        # 基于可用的高级功能
        if self._file_exists('commercial/ilm_policies.json'):
            recommendations.append({
                'priority': 'low',
                'category': '索引管理',
                'recommendation': '审查 ILM 策略的有效性',
                'action': '确保热温架构合理配置'
            })
        
        return recommendations
    
    def _calculate_health_score(self, health_data: dict) -> int:
        """计算健康评分"""
        score = 100
        
        # 状态扣分
        status = health_data.get('status', 'green')
        if status == 'yellow':
            score -= 30
        elif status == 'red':
            score -= 80
        
        # 未分配分片扣分
        unassigned = health_data.get('unassigned_shards', 0)
        if unassigned > 0:
            score -= min(unassigned * 2, 20)
        
        return max(0, score)
    
    def _get_file_data(self, filename: str) -> dict:
        """获取指定文件的数据"""
        manifest = self.data.get('files_manifest', {})
        
        # 尝试不同路径
        possible_paths = [
            filename,
            f'local-diagnostics-*/{filename}',
            f'{filename}'
        ]
        
        for path in manifest.keys():
            if path.endswith(filename):
                return manifest[path].get('data')
        
        return None
    
    def _file_exists(self, filename: str) -> bool:
        """检查文件是否存在"""
        manifest = self.data.get('files_manifest', {})
        return any(path.endswith(filename) for path in manifest.keys())
    
    def _extract_jvm_stats(self, nodes_stats: dict) -> dict:
        """提取 JVM 统计"""
        # 简化处理，实际需要根据具体结构解析
        return {
            'note': 'JVM 详细统计需要进一步解析 nodes_stats.json 的具体结构'
        }
    
    def _extract_os_stats(self, nodes_stats: dict) -> dict:
        """提取 OS 统计"""
        return {
            'note': 'OS 详细统计需要进一步解析 nodes_stats.json 的具体结构'
        }
    
    def save_interpretation(self, results: dict):
        """保存解读结果"""
        # 保存为 JSON
        json_path = self.output_dir / f"full_extraction_interpretation_{self.timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"解读结果已保存：{json_path}")
        
        # 生成文本报告
        txt_path = self.output_dir / f"full_extraction_report_{self.timestamp}.txt"
        self._generate_text_report(results, txt_path)
        logger.info(f"文本报告已保存：{txt_path}")
        
        return json_path, txt_path
    
    def _generate_text_report(self, results: dict, output_path: Path):
        """生成文本报告"""
        lines = []
        
        lines.append("="*100)
        lines.append("ES 集群全量诊断数据深度解读报告")
        lines.append("="*100)
        lines.append("")
        
        # 元数据
        meta = results.get('metadata', {})
        lines.append(f"数据来源：{meta.get('source', 'N/A')}")
        lines.append(f"提取时间：{meta.get('extracted_at', 'N/A')}")
        lines.append(f"文件总数：{meta.get('total_files', 0)}")
        lines.append(f"数据大小：{meta.get('total_size_mb', 0):.2f} MB")
        lines.append("")
        
        # 概览
        overview = results.get('overview', {})
        lines.append("-"*100)
        lines.append("数据概览")
        lines.append("-"*100)
        lines.append(f"总文件数：{overview.get('total_files', 0)}")
        lines.append(f"根目录文件：{overview.get('root_files_count', 0)}")
        lines.append(f"子目录数：{overview.get('subdirs_count', 0)}")
        lines.append("")
        
        # 集群健康
        health = results.get('cluster_health_analysis', {})
        lines.append("-"*100)
        lines.append("集群健康分析")
        lines.append("-"*100)
        lines.append(f"集群名称：{health.get('cluster_name', 'N/A')}")
        lines.append(f"状态：{health.get('status', 'N/A').upper()}")
        lines.append(f"健康评分：{health.get('health_score', 0)}/100")
        lines.append(f"节点总数：{health.get('nodes_summary', {}).get('total', 0)}")
        lines.append(f"活跃分片：{health.get('shards_summary', {}).get('active_shards', 0)}")
        lines.append(f"未分配分片：{health.get('shards_summary', {}).get('unassigned', 0)}")
        lines.append("")
        
        # 关键发现
        findings = results.get('key_findings', [])
        if findings:
            lines.append("-"*100)
            lines.append("关键发现")
            lines.append("-"*100)
            for i, finding in enumerate(findings, 1):
                severity = finding.get('severity', 'info').upper()
                category = finding.get('category', 'N/A')
                text = finding.get('finding', 'N/A')
                lines.append(f"{i}. [{severity}] {category}: {text}")
            lines.append("")
        
        # 优化建议
        recs = results.get('recommendations', [])
        if recs:
            lines.append("-"*100)
            lines.append("优化建议")
            lines.append("-"*100)
            for i, rec in enumerate(recs, 1):
                priority = rec.get('priority', 'N/A').upper()
                category = rec.get('category', 'N/A')
                text = rec.get('recommendation', 'N/A')
                action = rec.get('action', '')
                lines.append(f"{i}. [{priority}] {category}: {text}")
                if action:
                    lines.append(f"   操作：{action}")
            lines.append("")
        
        lines.append("="*100)
        lines.append("报告结束")
        lines.append("="*100)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    def interpret_and_save(self) -> tuple:
        """执行解读并保存"""
        logger.info("开始解读全量数据...")
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
    
    # 查找最新的全量提取文件
    out_dir = Path("out")
    if not out_dir.exists():
        logger.error("输出目录不存在")
        sys.exit(1)
    
    extraction_files = sorted(out_dir.glob("full_extraction_*.json"))
    if not extraction_files:
        logger.error("未找到全量提取文件")
        sys.exit(1)
    
    latest_file = extraction_files[-1]
    logger.info(f"使用文件：{latest_file.name}")
    
    # 创建解读器并执行
    interpreter = FullExtractionInterpreter(str(latest_file))
    json_path, txt_path = interpreter.interpret_and_save()
    
    logger.info(f"✓ 解读完成!")
    logger.info(f"  JSON 结果：{json_path}")
    logger.info(f"  文本报告：{txt_path}")
    
    # 打印摘要
    print("\n" + "="*60)
    print("解读摘要")
    print("="*60)
    
    with open(txt_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # 打印前 30 行
        for line in content.split('\n')[:30]:
            print(line)
    
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
