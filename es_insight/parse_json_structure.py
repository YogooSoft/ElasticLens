"""全量提取 JSON 结构解析器 - 深度分析 JSON 文件的内部结构"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import sys


class FullJSONStructureParser:
    """全量 JSON 结构深度解析器"""
    
    def __init__(self, extraction_json: str):
        """
        初始化解析器
        
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
            print(f"开始加载：{self.extraction_json.name} ({file_size_mb:.2f} MB)")
            
            with open(self.extraction_json, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            print(f"✓ 成功加载 {len(self.data.get('files_manifest', {}))} 个文件")
        except Exception as e:
            print(f"✗ 加载失败：{e}")
            raise
    
    def parse_all(self) -> dict:
        """
        解析所有文件的结构
        
        Returns:
            包含所有结构信息的字典
        """
        results = {
            'metadata': self._parse_metadata(),
            'structure_overview': self._analyze_structure_overview(),
            'file_structures': self._parse_each_file_structure(),
            'data_types': self._analyze_data_types(),
            'size_analysis': self._analyze_file_sizes(),
            'relationships': self._analyze_relationships()
        }
        
        return results
    
    def _parse_metadata(self) -> dict:
        """解析元数据结构"""
        meta = self.data.get('metadata', {})
        return {
            'source': meta.get('source', 'N/A'),
            'extracted_at': meta.get('extracted_at', 'N/A'),
            'total_files': meta.get('total_files', 0),
            'total_size_mb': meta.get('total_size_mb', 0),
            'extraction_mode': meta.get('extraction_mode', 'full')
        }
    
    def _analyze_structure_overview(self) -> dict:
        """分析整体结构概览"""
        manifest = self.data.get('files_manifest', {})
        
        # 按目录分组
        root_files = []
        subdir_files = defaultdict(list)
        
        for path in manifest.keys():
            parts = path.split('/')
            if len(parts) == 1:
                root_files.append(path)
            else:
                subdir = parts[0]
                filename = '/'.join(parts[1:])
                subdir_files[subdir].append(filename)
        
        # 数据结构类型统计
        data_types = defaultdict(int)
        for file_info in manifest.values():
            data = file_info.get('data')
            if isinstance(data, dict):
                data_types['object'] += 1
            elif isinstance(data, list):
                data_types['array'] += 1
            elif isinstance(data, (str, int, float, bool)):
                data_types['primitive'] += 1
            else:
                data_types['null'] += 1
        
        return {
            'total_files': len(manifest),
            'root_files_count': len(root_files),
            'subdir_count': len(subdir_files),
            'subdir_details': {
                subdir: len(files) for subdir, files in subdir_files.items()
            },
            'data_type_distribution': dict(data_types)
        }
    
    def _parse_each_file_structure(self) -> dict:
        """解析每个文件的详细结构"""
        manifest = self.data.get('files_manifest', {})
        structures = {}
        
        for i, (path, file_info) in enumerate(manifest.items(), 1):
            if i % 10 == 0:
                print(f"  解析中：{i}/{len(manifest)} - {path}")
            
            data = file_info.get('data')
            size = file_info.get('size', 0)
            
            structure = {
                'path': path,
                'size_kb': round(size / 1024, 2),
                'type': self._get_data_type(data),
                'depth': self._calculate_depth(data),
                'keys_count': self._count_keys(data),
                'items_count': self._count_items(data),
                'sample': self._get_sample(data)
            }
            
            structures[path] = structure
        
        return structures
    
    def _analyze_data_types(self) -> dict:
        """分析数据类型分布"""
        manifest = self.data.get('files_manifest', {})
        
        type_stats = {
            'object': [],
            'array': [],
            'string': [],
            'number': [],
            'boolean': [],
            'null': []
        }
        
        for path, file_info in manifest.items():
            data = file_info.get('data')
            dtype = self._get_data_type(data)
            
            if dtype == 'object':
                type_stats['object'].append({
                    'path': path,
                    'keys': self._count_keys(data),
                    'size_kb': round(file_info.get('size', 0) / 1024, 2)
                })
            elif dtype == 'array':
                type_stats['array'].append({
                    'path': path,
                    'items': len(data),
                    'size_kb': round(file_info.get('size', 0) / 1024, 2)
                })
        
        return type_stats
    
    def _analyze_file_sizes(self) -> dict:
        """分析文件大小分布"""
        manifest = self.data.get('files_manifest', {})
        
        sizes = []
        for path, file_info in manifest.items():
            size_kb = file_info.get('size', 0) / 1024
            sizes.append({
                'path': path,
                'size_kb': size_kb,
                'size_mb': size_kb / 1024
            })
        
        # 排序
        sorted_by_size = sorted(sizes, key=lambda x: x['size_mb'], reverse=True)
        
        # 统计
        total_size_mb = sum(f['size_mb'] for f in sizes)
        avg_size_kb = sum(f['size_kb'] for f in sizes) / len(sizes)
        
        return {
            'total_size_mb': round(total_size_mb, 2),
            'average_size_kb': round(avg_size_kb, 2),
            'largest_10': sorted_by_size[:10],
            'smallest_10': sorted_by_size[-10:],
            'distribution': {
                '> 1MB': len([f for f in sizes if f['size_mb'] > 1]),
                '100KB - 1MB': len([f for f in sizes if 0.1 <= f['size_mb'] <= 1]),
                '10KB - 100KB': len([f for f in sizes if 0.01 <= f['size_mb'] < 0.1]),
                '< 10KB': len([f for f in sizes if f['size_mb'] < 0.01])
            }
        }
    
    def _analyze_relationships(self) -> dict:
        """分析文件间的关系"""
        manifest = self.data.get('files_manifest', {})
        
        relationships = {
            'cluster_related': [],
            'nodes_related': [],
            'indices_related': [],
            'shards_related': [],
            'security_related': [],
            'ml_related': [],
            'ilm_related': [],
            'other': []
        }
        
        keywords_map = {
            'cluster_related': ['cluster', 'health', 'stats', 'state'],
            'nodes_related': ['nodes', 'node'],
            'indices_related': ['indices', 'index', 'mapping', 'alias', 'template'],
            'shards_related': ['shards', 'shard', 'allocation', 'recovery'],
            'security_related': ['security', 'user', 'role', 'priv'],
            'ml_related': ['ml_', 'machine_learning'],
            'ilm_related': ['ilm', 'lifecycle']
        }
        
        for path in manifest.keys():
            path_lower = path.lower()
            categorized = False
            
            for category, keywords in keywords_map.items():
                if any(kw in path_lower for kw in keywords):
                    relationships[category].append(path)
                    categorized = True
                    break
            
            if not categorized:
                relationships['other'].append(path)
        
        return relationships
    
    def _get_data_type(self, data) -> str:
        """获取数据类型"""
        if isinstance(data, dict):
            return 'object'
        elif isinstance(data, list):
            return 'array'
        elif isinstance(data, str):
            return 'string'
        elif isinstance(data, (int, float)):
            return 'number'
        elif isinstance(data, bool):
            return 'boolean'
        elif data is None:
            return 'null'
        else:
            return 'unknown'
    
    def _calculate_depth(self, data, current_depth=0) -> int:
        """计算嵌套深度"""
        if isinstance(data, dict):
            if not data:
                return current_depth
            return max(self._calculate_depth(v, current_depth + 1) for v in data.values())
        elif isinstance(data, list):
            if not data:
                return current_depth
            return max(self._calculate_depth(item, current_depth + 1) for item in data)
        else:
            return current_depth
    
    def _count_keys(self, data) -> int:
        """统计键的数量（递归）"""
        if isinstance(data, dict):
            count = len(data)
            for value in data.values():
                count += self._count_keys(value)
            return count
        elif isinstance(data, list):
            count = 0
            for item in data:
                count += self._count_keys(item)
            return count
        else:
            return 0
    
    def _count_items(self, data) -> int:
        """统计元素数量"""
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict):
            return len(data)
        else:
            return 1
    
    def _get_sample(self, data, max_depth=2) -> dict:
        """获取数据样本（前几层）"""
        if isinstance(data, dict):
            sample = {'type': 'object', 'keys': list(data.keys())[:10]}
            if max_depth > 0:
                sample['children'] = {}
                for key in list(data.keys())[:3]:
                    sample['children'][key] = self._get_sample(data[key], max_depth - 1)
            return sample
        elif isinstance(data, list):
            sample = {'type': 'array', 'length': len(data)}
            if max_depth > 0 and len(data) > 0:
                sample['first_item'] = self._get_sample(data[0], max_depth - 1)
            return sample
        else:
            return {'type': 'primitive', 'value': str(data)[:50]}
    
    def save_analysis(self, results: dict):
        """保存分析结果"""
        # 保存为 JSON
        json_path = self.output_dir / f"json_structure_analysis_{self.timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"✓ 结构分析已保存：{json_path}")
        
        # 生成文本报告
        txt_path = self.output_dir / f"json_structure_report_{self.timestamp}.txt"
        self._generate_text_report(results, txt_path)
        print(f"✓ 文本报告已保存：{txt_path}")
        
        return json_path, txt_path
    
    def _generate_text_report(self, results: dict, output_path: Path):
        """生成文本报告"""
        lines = []
        
        lines.append("="*100)
        lines.append("ES 集群全量诊断数据 - JSON 结构深度分析报告")
        lines.append("="*100)
        lines.append("")
        
        # 元数据
        meta = results.get('metadata', {})
        lines.append(f"数据来源：{meta.get('source', 'N/A')}")
        lines.append(f"提取时间：{meta.get('extracted_at', 'N/A')}")
        lines.append(f"文件总数：{meta.get('total_files', 0)}")
        lines.append(f"数据大小：{meta.get('total_size_mb', 0):.2f} MB")
        lines.append("")
        
        # 结构概览
        overview = results.get('structure_overview', {})
        lines.append("-"*100)
        lines.append("结构概览")
        lines.append("-"*100)
        lines.append(f"总文件数：{overview.get('total_files', 0)}")
        lines.append(f"根目录文件：{overview.get('root_files_count', 0)}")
        lines.append(f"子目录数：{overview.get('subdir_count', 0)}")
        lines.append(f"数据结构分布:")
        for dtype, count in overview.get('data_type_distribution', {}).items():
            lines.append(f"  - {dtype}: {count} 个文件")
        lines.append("")
        
        # 文件大小分析
        size_analysis = results.get('size_analysis', {})
        lines.append("-"*100)
        lines.append("文件大小分析")
        lines.append("-"*100)
        lines.append(f"总大小：{size_analysis.get('total_size_mb', 0):.2f} MB")
        lines.append(f"平均大小：{size_analysis.get('average_size_kb', 0):.2f} KB")
        lines.append("")
        
        lines.append("最大的 10 个文件:")
        for i, file in enumerate(size_analysis.get('largest_10', [])[:5], 1):
            lines.append(f"  {i}. {file['path']} ({file['size_mb']:.2f} MB)")
        lines.append("")
        
        lines.append("大小分布:")
        dist = size_analysis.get('distribution', {})
        lines.append(f"  - > 1MB: {dist.get('> 1MB', 0)} 个文件")
        lines.append(f"  - 100KB - 1MB: {dist.get('100KB - 1MB', 0)} 个文件")
        lines.append(f"  - 10KB - 100KB: {dist.get('10KB - 100KB', 0)} 个文件")
        lines.append(f"  - < 10KB: {dist.get('< 10KB', 0)} 个文件")
        lines.append("")
        
        # 数据类型分析
        data_types = results.get('data_types', {})
        lines.append("-"*100)
        lines.append("数据类型分析")
        lines.append("-"*100)
        lines.append(f"对象类型：{len(data_types.get('object', []))} 个文件")
        lines.append(f"数组类型：{len(data_types.get('array', []))} 个文件")
        lines.append("")
        
        # 文件关系分析
        relationships = results.get('relationships', {})
        lines.append("-"*100)
        lines.append("文件关系分类")
        lines.append("-"*100)
        for category, files in relationships.items():
            category_name = {
                'cluster_related': '集群相关',
                'nodes_related': '节点相关',
                'indices_related': '索引相关',
                'shards_related': '分片相关',
                'security_related': '安全相关',
                'ml_related': '机器学习',
                'ilm_related': '生命周期管理',
                'other': '其他'
            }.get(category, category)
            lines.append(f"{category_name}: {len(files)} 个文件")
        lines.append("")
        
        # 详细文件列表
        file_structures = results.get('file_structures', {})
        lines.append("-"*100)
        lines.append("详细文件结构（按类别）")
        lines.append("-"*100)
        
        # 按类别分组显示
        categories = {
            '核心巡检': ['cluster_health.json', 'nodes_short.json', 'indices.json', 'shards.json'],
            '节点详情': [f for f in file_structures.keys() if 'nodes' in f.lower()],
            '索引详情': [f for f in file_structures.keys() if 'indices' in f.lower() or 'index' in f.lower()],
            '高级功能': [f for f in file_structures.keys() if 'commercial/' in f]
        }
        
        for category, files in categories.items():
            if files:
                lines.append(f"\n【{category}】")
                for path in sorted(files)[:10]:  # 限制每个类别显示 10 个
                    struct = file_structures.get(path, {})
                    lines.append(f"  - {path}")
                    lines.append(f"    类型：{struct.get('type', 'N/A')}, "
                               f"大小：{struct.get('size_kb', 0):.1f} KB, "
                               f"深度：{struct.get('depth', 0)}, "
                               f"键数：{struct.get('keys_count', 0)}")
        
        lines.append("")
        lines.append("="*100)
        lines.append("报告结束")
        lines.append("="*100)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    def parse_and_save(self) -> tuple:
        """执行解析并保存"""
        print("\n开始解析 JSON 结构...")
        results = self.parse_all()
        return self.save_analysis(results)


def main():
    """主函数"""
    from pathlib import Path
    
    # 查找最新的全量提取文件
    out_dir = Path("out")
    extraction_files = sorted(out_dir.glob("full_extraction_*.json"))
    
    if not extraction_files:
        print("❌ 未找到全量提取文件")
        print("请先运行：python -m es_insight.full_diagnostic_extractor")
        return
    
    latest_file = extraction_files[-1]
    print(f"使用文件：{latest_file.name}")
    
    # 创建解析器并执行
    parser = FullJSONStructureParser(str(latest_file))
    json_path, txt_path = parser.parse_and_save()
    
    print(f"\n✅ 解析完成!")
    print(f"  JSON 结果：{json_path}")
    print(f"  文本报告：{txt_path}")
    
    # 打印摘要
    print("\n" + "="*60)
    print("解析摘要")
    print("="*60)
    
    with open(txt_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # 打印前 40 行
        for line in content.split('\n')[:40]:
            print(line)
    
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
