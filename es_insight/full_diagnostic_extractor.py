"""ES 集群诊断数据全量提取器 - 提取 ZIP 包中的所有 JSON 文件"""

import os
import json
import zipfile
from pathlib import Path
from datetime import datetime
from loguru import logger


class FullDiagnosticExtractor:
    """全量诊断数据提取器"""
    
    def __init__(self, diagnostic_path: str):
        """
        初始化全量提取器
        
        Args:
            diagnostic_path: 诊断文件路径（zip 文件或已解压目录）
        """
        self.diagnostic_path = Path(diagnostic_path)
        self.output_dir = Path("out")
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"全量提取器初始化完成，输出目录：{self.output_dir}")
    
    def extract_all_json(self) -> dict:
        """
        提取 ZIP 包中的所有 JSON 文件
        
        Returns:
            包含所有 JSON 数据的字典
        """
        results = {
            'metadata': {
                'source': str(self.diagnostic_path),
                'extracted_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'timestamp': self.timestamp,
                'extraction_mode': 'full'
            },
            'files_manifest': {}  # 文件清单
        }
        
        total_files = 0
        total_size = 0
        
        try:
            if self.diagnostic_path.suffix == '.zip':
                # 从 ZIP 文件读取
                with zipfile.ZipFile(self.diagnostic_path, 'r') as z:
                    for file_info in z.infolist():
                        filename = file_info.filename
                        
                        # 只处理 JSON 文件
                        if not filename.endswith('.json'):
                            continue
                        
                        # 跳过目录
                        if filename.endswith('/'):
                            continue
                        
                        try:
                            with z.open(filename) as f:
                                data = json.load(f)
                                
                                # 规范化文件路径作为 key
                                normalized_path = filename.replace('\\', '/')
                                if normalized_path.startswith('local-diagnostics-'):
                                    normalized_path = '/'.join(normalized_path.split('/')[1:])
                                
                                results['files_manifest'][normalized_path] = {
                                    'original_path': filename,
                                    'size': file_info.file_size,
                                    'compressed_size': file_info.compress_size,
                                    'data': data
                                }
                                
                                total_files += 1
                                total_size += file_info.file_size
                                
                        except Exception as e:
                            logger.warning(f"解析文件 {filename} 失败：{e}")
                            continue
            
            elif self.diagnostic_path.is_dir():
                # 从已解压目录读取
                for root, dirs, files in os.walk(self.diagnostic_path):
                    for filename in files:
                        if not filename.endswith('.json'):
                            continue
                        
                        file_path = Path(root) / filename
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                
                                # 计算相对路径
                                rel_path = file_path.relative_to(self.diagnostic_path)
                                normalized_path = str(rel_path).replace('\\', '/')
                                
                                file_stat = file_path.stat()
                                
                                results['files_manifest'][normalized_path] = {
                                    'original_path': str(file_path),
                                    'size': file_stat.st_size,
                                    'compressed_size': file_stat.st_size,
                                    'data': data
                                }
                                
                                total_files += 1
                                total_size += file_stat.st_size
                                
                        except Exception as e:
                            logger.warning(f"解析文件 {filename} 失败：{e}")
                            continue
            
            # 更新元数据
            results['metadata']['total_files'] = total_files
            results['metadata']['total_size_bytes'] = total_size
            results['metadata']['total_size_mb'] = round(total_size / (1024 * 1024), 2)
            
            logger.info(f"成功提取 {total_files} 个 JSON 文件，总大小：{results['metadata']['total_size_mb']} MB")
            
        except Exception as e:
            logger.error(f"提取数据失败：{e}", exc_info=True)
            raise
        
        return results
    
    def generate_summary(self, results: dict) -> dict:
        """
        生成提取摘要
        
        Args:
            results: 提取结果
            
        Returns:
            摘要信息
        """
        manifest = results.get('files_manifest', {})
        
        # 按目录分组
        root_files = {}
        subdirs = {}
        
        for path, info in manifest.items():
            parts = path.split('/')
            if len(parts) == 1:
                # 根目录文件
                root_files[path] = info
            else:
                # 子目录文件
                subdir = parts[0]
                if subdir not in subdirs:
                    subdirs[subdir] = {}
                subdirs[subdir]['/'.join(parts[1:])] = info
        
        summary = {
            'total_files': len(manifest),
            'root_files_count': len(root_files),
            'subdirs_count': len(subdirs),
            'root_files': list(root_files.keys()),
            'subdirs': {}
        }
        
        for subdir_name, files in subdirs.items():
            summary['subdirs'][subdir_name] = {
                'file_count': len(files),
                'files': list(files.keys())[:20]  # 只显示前 20 个
            }
        
        return summary
    
    def save_full_extraction(self, results: dict) -> str:
        """
        保存全量提取结果
        
        Args:
            results: 提取结果
            
        Returns:
            输出文件路径
        """
        output_path = self.output_dir / f"full_extraction_{self.timestamp}.json"
        
        # 为了减小文件大小，保存时移除 metadata 中的冗余信息
        save_data = {
            'metadata': results['metadata'],
            'files_manifest': results['files_manifest']
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info(f"全量提取结果已保存：{output_path} ({file_size_mb:.2f} MB)")
        
        return str(output_path)
    
    def save_summary_report(self, results: dict) -> str:
        """
        保存摘要报告
        
        Args:
            results: 提取结果
            
        Returns:
            输出文件路径
        """
        summary = self.generate_summary(results)
        output_path = self.output_dir / f"extraction_summary_{self.timestamp}.txt"
        
        lines = []
        lines.append("="*100)
        lines.append("ES 集群诊断数据全量提取摘要")
        lines.append("="*100)
        lines.append("")
        lines.append(f"源文件：{results['metadata']['source']}")
        lines.append(f"提取时间：{results['metadata']['extracted_at']}")
        lines.append(f"提取模式：全量提取")
        lines.append("")
        lines.append("-"*100)
        lines.append("统计信息")
        lines.append("-"*100)
        lines.append(f"JSON 文件总数：{summary['total_files']}")
        lines.append(f"根目录文件数：{summary['root_files_count']}")
        lines.append(f"子目录数：{summary['subdirs_count']}")
        lines.append(f"原始数据大小：{results['metadata']['total_size_mb']} MB")
        lines.append("")
        
        lines.append("-"*100)
        lines.append("根目录文件列表")
        lines.append("-"*100)
        for i, filename in enumerate(sorted(summary['root_files']), 1):
            lines.append(f"{i:3}. {filename}")
        lines.append("")
        
        lines.append("-"*100)
        lines.append("子目录文件分布")
        lines.append("-"*100)
        for subdir_name, info in summary['subdirs'].items():
            lines.append(f"\n{subdir_name}/ ({info['file_count']} 个文件)")
            lines.append("-"*50)
            for j, filename in enumerate(sorted(info['files'])[:20], 1):
                lines.append(f"  {j:2}. {filename}")
            if info['file_count'] > 20:
                lines.append(f"  ... 还有 {info['file_count'] - 20} 个文件")
        
        lines.append("")
        lines.append("="*100)
        lines.append("完整数据请查看 JSON 文件")
        lines.append("="*100)
        
        content = '\n'.join(lines)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"提取摘要已保存：{output_path}")
        return str(output_path)
    
    def extract_and_save(self) -> tuple:
        """
        执行全量提取并保存
        
        Returns:
            (JSON 文件路径，摘要文件路径)
        """
        logger.info("开始全量提取...")
        results = self.extract_all_json()
        
        json_path = self.save_full_extraction(results)
        summary_path = self.save_summary_report(results)
        
        logger.info(f"✓ 全量提取完成!")
        logger.info(f"  JSON 数据：{json_path}")
        logger.info(f"  摘要报告：{summary_path}")
        
        return json_path, summary_path


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
    
    # 默认诊断文件路径
    default_diagnostic = Path("data/local-diagnostics-20250625-055003.zip")
    
    # 检查文件是否存在
    if not default_diagnostic.exists():
        # 尝试使用已解压的目录
        extracted_dir = Path("data/extracted/local-diagnostics-20250625-055003")
        if extracted_dir.exists():
            diagnostic_path = extracted_dir
        else:
            logger.error(f"未找到诊断文件：{default_diagnostic}")
            logger.error("请确保 data 目录下存在诊断文件或已解压的诊断目录")
            sys.exit(1)
    else:
        diagnostic_path = default_diagnostic
    
    logger.info(f"开始全量提取诊断数据：{diagnostic_path}")
    
    # 创建提取器并执行提取
    extractor = FullDiagnosticExtractor(str(diagnostic_path))
    json_path, summary_path = extractor.extract_and_save()
    
    logger.info(f"✓ 处理完成")
    
    # 打印摘要
    print("\n" + "="*60)
    print("全量提取摘要")
    print("="*60)
    
    with open(summary_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # 只打印统计部分
        for line in content.split('\n')[:20]:
            print(line)
    
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
