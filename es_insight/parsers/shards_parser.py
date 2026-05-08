"""分片数据解析器 - 解析 cat_shards.txt 并生成索引分片汇总信息"""

import re
from dataclasses import dataclass
from typing import List, Dict
from loguru import logger


@dataclass
class ShardInfo:
    """单个分片的信息"""
    index_name: str          # 索引名称
    shard_id: int            # 分片ID
    is_primary: bool         # 是否为主分片
    state: str               # 分片状态
    docs_count: int          # 文档数
    store_size_bytes: int    # 存储大小（字节）
    node_name: str           # 节点名称


@dataclass
class IndexShardSummary:
    """索引分片汇总信息"""
    index_name: str              # 索引名称
    primary_shard_count: int     # 主分片数量
    total_size_bytes: int        # 总存储大小（字节，仅主分片）
    total_size_gb: float         # 总存储大小（GB）
    avg_shard_size_bytes: int    # 单个分片平均大小（字节）
    avg_shard_size_gb: float     # 单个分片平均大小（GB）


def convert_size_to_bytes(size_str: str) -> int:
    """
    将带单位的字符串转换为字节数
    
    Args:
        size_str: 如 "23.3kb", "4.5gb", "208b"
        
    Returns:
        字节数
    """
    if not size_str:
        return 0
    
    unit_map = {
        'b': 1,
        'kb': 1024,
        'mb': 1024 ** 2,
        'gb': 1024 ** 3,
        'tb': 1024 ** 4,
        'pb': 1024 ** 5
    }
    
    # 使用正则表达式分离数字和单位
    match = re.match(r'(\d*\.?\d+)\s*([a-zA-Z]*)', size_str.strip())
    if not match:
        return 0
    
    size = float(match.group(1))
    unit = match.group(2).lower() if match.group(2) else 'b'
    
    multiplier = unit_map.get(unit, 1)
    return int(size * multiplier)


def bytes_to_gb(bytes_value: int) -> float:
    """
    将字节转换为GB
    
    Args:
        bytes_value: 字节数
        
    Returns:
        GB值（保留2位小数）
    """
    return round(bytes_value / (1024 ** 3), 2)


def format_size_human_readable(bytes_value: int) -> str:
    """
    将字节转换为人类可读的格式（自动选择单位）
    
    Args:
        bytes_value: 字节数
        
    Returns:
        格式化后的字符串，如 "1.5 GB", "256 MB", "30 KB"
    """
    if bytes_value == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    unit_index = 0
    size = float(bytes_value)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    # 根据大小决定小数位数
    if unit_index == 0:  # B
        return f"{int(size)} B"
    elif unit_index == 1:  # KB
        return f"{size:.1f} KB"
    else:  # MB, GB, TB, PB
        return f"{size:.2f} {units[unit_index]}"


def parse_cat_shards(content: str) -> List[ShardInfo]:
    """
    解析 cat_shards.txt 内容
    
    Args:
        content: cat_shards.txt 文件内容
        
    Returns:
        ShardInfo 列表
    """
    shards = []
    lines = content.strip().split('\n')
    
    if not lines:
        logger.warning("cat_shards.txt 内容为空")
        return shards
    
    logger.info(f"开始解析 cat_shards.txt，共 {len(lines)} 行")
    
    # 跳过表头
    for line_num, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        
        parts = line.split()
        if len(parts) >= 8:
            try:
                shard = ShardInfo(
                    index_name=parts[0],
                    shard_id=int(parts[1]),
                    is_primary=(parts[2] == 'p'),
                    state=parts[3],
                    docs_count=int(parts[4]) if parts[4].isdigit() else 0,
                    store_size_bytes=convert_size_to_bytes(parts[5]),
                    node_name=parts[7]
                )
                shards.append(shard)
            except (ValueError, IndexError) as e:
                logger.warning(f"解析第 {line_num} 行失败: {line}, 错误: {e}")
        else:
            logger.warning(f"第 {line_num} 行格式不正确: {line}")
    
    logger.info(f"成功解析 {len(shards)} 个分片记录")
    return shards


def aggregate_index_shards(shards: List[ShardInfo]) -> List[IndexShardSummary]:
    """
    按索引聚合分片信息
    
    Args:
        shards: 分片信息列表
        
    Returns:
        索引分片汇总列表（按索引名排序）
    """
    index_map: Dict[str, Dict[str, int]] = {}
    
    for shard in shards:
        if shard.index_name not in index_map:
            index_map[shard.index_name] = {
                'primary_count': 0,
                'total_size_bytes': 0
            }
        
        # 只统计主分片
        if shard.is_primary:
            index_map[shard.index_name]['primary_count'] += 1
            index_map[shard.index_name]['total_size_bytes'] += shard.store_size_bytes
    
    # 转换为汇总对象列表
    summaries = []
    for index_name, stats in index_map.items():
        primary_count = stats['primary_count']
        total_size_bytes = stats['total_size_bytes']
        # 计算平均分片大小
        avg_shard_size_bytes = int(total_size_bytes / primary_count) if primary_count > 0 else 0
        avg_shard_size_gb = bytes_to_gb(avg_shard_size_bytes)
        
        summary = IndexShardSummary(
            index_name=index_name,
            primary_shard_count=primary_count,
            total_size_bytes=total_size_bytes,
            total_size_gb=bytes_to_gb(total_size_bytes),
            avg_shard_size_bytes=avg_shard_size_bytes,
            avg_shard_size_gb=avg_shard_size_gb
        )
        summaries.append(summary)
    
    # 按索引名排序
    summaries.sort(key=lambda x: x.index_name)
    
    logger.info(f"聚合得到 {len(summaries)} 个索引的分片汇总信息")
    return summaries


class ShardsReportParser:
    """分片报告解析器 - 提供完整的分片数据解析和聚合功能"""
    
    def __init__(self):
        """初始化分片报告解析器"""
        self.shards: List[ShardInfo] = []
        self.summaries: List[IndexShardSummary] = []
    
    def parse_and_aggregate(self, content: str) -> List[IndexShardSummary]:
        """
        解析并聚合分片数据
        
        Args:
            content: cat_shards.txt 文件内容
            
        Returns:
            索引分片汇总列表
        """
        # 解析原始分片数据
        self.shards = parse_cat_shards(content)
        
        # 聚合为索引级别汇总
        self.summaries = aggregate_index_shards(self.shards)
        
        return self.summaries
    
    def get_summaries_as_dicts(self) -> List[Dict]:
        """
        获取汇总信息的字典表示（用于JSON序列化）
        
        Returns:
            字典列表，每个元素包含 index_name, primary_shard_count, total_size_bytes, total_size_gb
        """
        return [
            {
                'index_name': summary.index_name,
                'primary_shard_count': summary.primary_shard_count,
                'total_size_bytes': summary.total_size_bytes,
                'total_size_gb': summary.total_size_gb,
                'avg_shard_size_bytes': summary.avg_shard_size_bytes,
                'avg_shard_size_gb': summary.avg_shard_size_gb
            }
            for summary in self.summaries
        ]
