"""ES 集群诊断数据解析器 - 读取并解析诊断数据为 JSON 格式"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict
from loguru import logger

from es_insight.parsers import (
    ClusterHealthParser,
    NodesParser,
    IndicesParser
)
from es_insight.parsers.shards_parser import ShardsReportParser
from es_insight.models.common import Issue, Severity as IssueSeverity
from es_insight.models.cluster_info import ClusterBasicInfo


class DiagnosticDataExtractor:
    """诊断数据提取器"""
    
    def __init__(self, diagnostic_path: str):
        """
        初始化数据提取器
        
        Args:
            diagnostic_path: 诊断文件路径（zip 文件或已解压目录）
        """
        self.diagnostic_path = Path(diagnostic_path)
        self.output_dir = Path("out")
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"数据提取器初始化完成，输出目录：{self.output_dir}")
    
    def extract_all(self) -> dict:
        """
        提取所有诊断数据
        
        Returns:
            包含所有解析结果的字典
        """
        results = {
            'metadata': {
                'source': str(self.diagnostic_path),
                'extracted_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'timestamp': self.timestamp
            },
            'cluster_health': None,
            'nodes': [],
            'indices': [],
            'cluster_stats': None,
            'shards': None,
            'allocation': None,
            'version': None,  # 新增：版本信息
            'cluster_settings_defaults': None,  # 新增：集群配置默认值
            'nodes_stats': None,  # 新增：节点统计数据（供高级分析器使用）
            'thread_pools': None,  # 新增：线程池数据
            'allocation_explain': None  # 新增：分片分配解释
        }
        
        try:
            # 1. 解析集群健康
            logger.info("解析集群健康数据...")
            health_parser = ClusterHealthParser(str(self.diagnostic_path))
            health_data = health_parser.parse()
            results['cluster_health'] = self._serialize_object(health_data)
            
            # 2. 解析节点信息
            logger.info("解析节点信息...")
            nodes_parser = NodesParser(str(self.diagnostic_path))
            nodes = nodes_parser.parse_short()
            
            # 2.1 尝试从 nodes.json 补充 version 和 roles 信息，并保存原始配置
            nodes_json_data = None  # 保存原始数据
            try:
                nodes_json_data = nodes_parser.parse_nodes_json()
                # 保存原始 nodes.json 数据供配置漂移检测使用
                if nodes_json_data:
                    results['nodes_raw'] = nodes_json_data
                    logger.info(f"已保存 nodes.json 原始数据")
                
                if isinstance(nodes_json_data, dict) and 'nodes' in nodes_json_data:
                    json_nodes = nodes_json_data.get('nodes', {})
                    logger.info(f"开始从 nodes.json 补充 {len(json_nodes)} 个节点的版本和角色信息")
                    for node in nodes:
                        if node.id in json_nodes:
                            node_data = json_nodes[node.id]
                            # 补充 version
                            if not node.version and node_data.get('version'):
                                node.version = node_data.get('version', '')
                            # 补充 roles
                            if node.roles == [''] or len(node.roles) == 0:
                                node.roles = node_data.get('roles', [])
                            # 补充 CPU 核心数
                            os_info = node_data.get('os', {})
                            if os_info:
                                node.available_processors = os_info.get('available_processors', 0)
                                node.allocated_processors = os_info.get('allocated_processors', 0)
                                node.cpu_cores = node.available_processors  # 兼容旧字段
                    logger.info(f"成功从 nodes.json 补充节点信息")
            except Exception as e:
                logger.warning(f"解析 nodes.json 失败：{e}")
            
            # 2.2 尝试从 nodes_stats.json 补充资源使用数据
            nodes_stats = None  # 初始化变量
            try:
                nodes_stats = nodes_parser.parse_stats()
                # 保存原始 nodes_stats 数据供高级分析器使用
                if nodes_stats:
                    results['nodes_stats'] = nodes_stats
                    logger.info(f"已保存 nodes_stats 原始数据")
                
                # nodes_stats 包含各节点的统计数据
                if isinstance(nodes_stats, dict) and 'nodes' in nodes_stats:
                    stats_nodes = nodes_stats.get('nodes', {})
                    logger.info(f"开始从 {len(stats_nodes)} 个节点补充资源数据")
                    updated_count = 0
                    for node in nodes:
                        node_id = node.id
                        if node_id in stats_nodes:
                            stats = stats_nodes[node_id]
                            
                            # 更新磁盘使用率
                            fs_total = stats.get('fs', {}).get('total', {})
                            if fs_total:
                                total_bytes = fs_total.get('total_in_bytes', 0)
                                available_bytes = fs_total.get('available_in_bytes', 0)
                                if total_bytes > 0:
                                    used_bytes = total_bytes - available_bytes
                                    old_disk = node.disk_used_percent
                                    node.disk_used_percent = round(used_bytes / total_bytes * 100, 1)
                                    logger.debug(f"{node.name}: disk {old_disk}% -> {node.disk_used_percent}%")
                                    updated_count += 1
                            
                            # 更新 JVM 堆使用率（直接使用 heap_used_percent）
                            jvm_mem = stats.get('jvm', {}).get('mem', {})
                            if jvm_mem:
                                heap_used_percent = jvm_mem.get('heap_used_percent', 0)
                                if heap_used_percent:
                                    old_heap = node.heap_used_percent
                                    node.heap_used_percent = float(heap_used_percent)
                                
                                # 补充 JVM 堆最大值
                                node.jvm_heap_max = jvm_mem.get('heap_max', '未知')
                                node.jvm_heap_max_bytes = jvm_mem.get('heap_max_in_bytes', 0)
                                logger.debug(f"{node.name}: jvm_heap_max={node.jvm_heap_max}")
                            
                            # 补充总内存
                            os_mem = stats.get('os', {}).get('mem', {})
                            if os_mem:
                                node.mem_total = os_mem.get('total', '未知')
                                node.mem_total_bytes = os_mem.get('total_in_bytes', 0)
                                logger.debug(f"{node.name}: mem_total={node.mem_total}")
                            
                            # 补充启动时长
                            jvm_uptime = stats.get('jvm', {})
                            if jvm_uptime:
                                node.uptime = jvm_uptime.get('uptime', '未知')
                                node.uptime_millis = jvm_uptime.get('uptime_in_millis', 0)
                                logger.debug(f"{node.name}: uptime={node.uptime}")
                            
                            # 更新 CPU 使用率
                            os_stats = stats.get('os', {})
                            if os_stats:
                                cpu_percent = os_stats.get('cpu', {}).get('percent', 0)
                                # ES 返回的是 0-100 的值，直接使用
                                if cpu_percent is not None:
                                    old_cpu = node.cpu_percent
                                    node.cpu_percent = float(cpu_percent)
                                    logger.debug(f"{node.name}: cpu {old_cpu}% -> {node.cpu_percent}%")
                    
                    logger.info(f"成功更新 {updated_count} 个节点的资源数据")
            except Exception as e:
                logger.warning(f"解析节点统计数据失败：{e}")
            
            # 2.3 从 cat_shards.txt 统计分片数（优先级最高）
            try:
                shard_count_map = self._parse_cat_shards()
                if shard_count_map:
                    logger.info(f"开始从 cat_shards.txt 为 {len(nodes)} 个节点补充分片数")
                    matched_count = 0
                    for node in nodes:
                        if node.name in shard_count_map:
                            old_shard_count = node.shard_count
                            node.shard_count = shard_count_map[node.name]
                            if old_shard_count != node.shard_count:
                                logger.debug(f"{node.name}: shards {old_shard_count} -> {node.shard_count}")
                            matched_count += 1
                    logger.info(f"成功从 cat_shards.txt 匹配 {matched_count} 个节点的分片数")
            except Exception as e:
                logger.warning(f"解析 cat_shards.txt 失败：{e}")
            
            # 2.4 从 allocation.json 补充磁盘信息
            try:
                allocation_data = self._parse_json_file('allocation.json')
                if allocation_data and isinstance(allocation_data, list):
                    # 构建节点名称到分配信息的映射
                    allocation_map = {}
                    for alloc in allocation_data:
                        node_name = alloc.get('node', '')
                        if node_name:
                            allocation_map[node_name] = alloc
                    
                    logger.info(f"开始从 allocation.json 为 {len(nodes)} 个节点补充磁盘信息")
                    matched_count = 0
                    for node in nodes:
                        alloc = allocation_map.get(node.name, {})
                        if alloc:
                            # 注意：分片数已从 cat_shards.txt 获取，这里不再覆盖
                            # node.shard_count = int(alloc.get('shards', 0))  # 已注释
                            node.disk_total = alloc.get('disk.total', '未知')
                            node.disk_total_bytes = self._convert_size_to_bytes(alloc.get('disk.total', '0b'))
                            # disk.percent 是字符串，需要转换
                            disk_pct = alloc.get('disk.percent', '0')
                            if disk_pct:
                                try:
                                    node.disk_used_percent = float(disk_pct)
                                except (ValueError, TypeError):
                                    node.disk_used_percent = 0.0
                            matched_count += 1
                            logger.debug(f"{node.name}: disk_total={node.disk_total}, disk_percent={node.disk_used_percent}%")
                    
                    logger.info(f"成功从 allocation.json 匹配 {matched_count} 个节点的磁盘信息")
            except Exception as e:
                logger.warning(f"解析 allocation.json 失败：{e}")
            
            results['nodes'] = [self._serialize_object(node) for node in nodes]
            
            # 4. 提取 JVM GC 数据（从 nodes_stats 中）
            try:
                if isinstance(nodes_stats, dict) and 'nodes' in nodes_stats:
                    stats_nodes = nodes_stats.get('nodes', {})
                    jvm_gc_data = []
                    for node_id, stats in stats_nodes.items():
                        jvm = stats.get('jvm', {})
                        gc = jvm.get('gc', {})
                        collectors = gc.get('collectors', {})
                        
                        # 统计所有 GC 收集器的总次数和总时间
                        total_count = 0
                        total_time_ms = 0
                        for collector_name, collector_data in collectors.items():
                            total_count += collector_data.get('collection_count', 0)
                            total_time_ms += collector_data.get('collection_time_in_millis', 0)
                        
                        if collectors:  # 只要有收集器数据就记录
                            jvm_gc_data.append({
                                'node_id': node_id,
                                'node_name': stats.get('name', ''),
                                'gc_total_collection_count': total_count,
                                'gc_total_collection_time_in_millis': total_time_ms
                            })
                    
                    results['jvm_gc'] = jvm_gc_data
                    logger.info(f"提取到 {len(jvm_gc_data)} 个节点的 JVM GC 数据")
            except Exception as e:
                logger.warning(f"提取 JVM GC 数据失败：{e}")
            
            # 3. 解析索引信息
            logger.info("解析索引信息...")
            indices_parser = IndicesParser(str(self.diagnostic_path))
            indices = indices_parser.parse()
            results['indices'] = [self._serialize_object(idx) for idx in indices]
            
            # 4. 解析其他关键数据（直接从 JSON 文件读取）
            logger.info("解析集群统计信息...")
            results['cluster_stats'] = self._parse_json_file('cluster_stats.json')
            
            logger.info("解析版本信息...")
            results['version'] = self._parse_json_file('version.json')
            
            logger.info("解析集群配置默认值...")
            results['cluster_settings_defaults'] = self._parse_json_file('cluster_settings_defaults.json')
            
            logger.info("解析分片信息...")
            results['shards'] = self._parse_json_file('shards.json')
            
            logger.info("解析分片分配信息...")
            results['allocation'] = self._parse_json_file('allocation.json')
            
            logger.info("解析恢复信息...")
            results['recovery'] = self._parse_json_file('recovery.json')
            
            # 5. 解析 ILM 数据（商业版功能）
            logger.info("提取 ILM 数据...")
            try:
                results['ilm'] = self._extract_ilm()
                if results['ilm']:
                    logger.info(f"✓ 提取了 {len(results['ilm'].get('policies', []))} 个 ILM 策略")
            except Exception as e:
                logger.warning(f"ILM 数据提取失败：{e}")
                results['ilm'] = {}
            
            # 6. 解析快照数据
            logger.info("提取快照数据...")
            try:
                results['snapshot'] = self._extract_snapshot()
                if results['snapshot']:
                    logger.info(f"✓ 提取了 {results['snapshot'].get('snapshot_count', 0)} 个快照")
            except Exception as e:
                logger.warning(f"快照数据提取失败：{e}")
                results['snapshot'] = {}
            
            # 7. 解析安全数据（商业版功能）
            logger.info("提取安全数据...")
            try:
                results['security'] = self._extract_security()
                if results['security']:
                    logger.info(f"✓ 提取了 {len(results['security'].get('users', []))} 个安全用户")
            except Exception as e:
                logger.warning(f"安全数据提取失败：{e}")
                results['security'] = {}
            
            # 8. 提取线程池数据（从 nodes_stats.json）
            try:
                if results.get('nodes_stats') and isinstance(results['nodes_stats'], dict):
                    thread_pools_data = []
                    nodes_dict = results['nodes_stats'].get('nodes', {})
                    for node_id, node_stats in nodes_dict.items():
                        node_name = node_stats.get('name', node_id)
                        thread_pool_stats = node_stats.get('thread_pool', {})
                        for pool_name, pool_data in thread_pool_stats.items():
                            if isinstance(pool_data, dict):
                                thread_pools_data.append({
                                    'node_name': node_name,
                                    'node_id': node_id,
                                    'name': pool_name,
                                    'queue_size': pool_data.get('queue', 0),
                                    'rejected': pool_data.get('rejected', 0),
                                    'active': pool_data.get('active', 0),
                                    'completed': pool_data.get('completed', 0),
                                    'largest': pool_data.get('largest', 0),
                                    'threads': pool_data.get('threads', 0)
                                })
                    results['thread_pools'] = thread_pools_data
                    logger.info(f"✓ 提取了 {len(thread_pools_data)} 个线程池数据")
            except Exception as e:
                logger.warning(f"线程池数据提取失败：{e}")
                results['thread_pools'] = []
            
            # 9. 提取分片分配解释数据
            try:
                allocation_explain = self._parse_json_file('allocation_explain.json')
                if allocation_explain:
                    results['allocation_explain'] = allocation_explain
                    logger.info("✓ 提取了 allocation_explain 数据")
                else:
                    results['allocation_explain'] = {}
            except Exception as e:
                logger.warning(f"allocation_explain 数据提取失败：{e}")
                results['allocation_explain'] = {}
            
            logger.info(f"成功提取所有诊断数据")
            
        except Exception as e:
            logger.error(f"提取数据失败：{e}", exc_info=True)
            raise
        
        return results
    
    def _parse_json_file(self, filename: str) -> dict:
        """
        从诊断包中解析 JSON 文件
        
        Args:
            filename: 文件名
            
        Returns:
            解析后的字典数据
        """
        try:
            # 尝试从 zip 文件中读取
            if self.diagnostic_path.suffix == '.zip':
                import zipfile
                with zipfile.ZipFile(self.diagnostic_path, 'r') as z:
                    # 查找文件（可能在根目录或子目录）
                    for name in z.namelist():
                        if name.endswith(filename):
                            with z.open(name) as f:
                                return json.load(f)
            
            # 尝试从已解压目录读取
            elif self.diagnostic_path.is_dir():
                # 在目录中查找文件
                for root, dirs, files in os.walk(self.diagnostic_path):
                    if filename in files:
                        file_path = Path(root) / filename
                        with open(file_path, 'r', encoding='utf-8') as f:
                            return json.load(f)
            
            logger.warning(f"未找到文件：{filename}")
            return {}
        except Exception as e:
            logger.warning(f"解析 {filename} 失败：{e}")
            return {}
    
    def _parse_text_file(self, filename: str) -> str:
        """
        从诊断包中解析文本文件
        
        Args:
            filename: 文件名
            
        Returns:
            文本文件内容
        """
        try:
            # 尝试从 zip 文件中读取
            if self.diagnostic_path.suffix == '.zip':
                import zipfile
                with zipfile.ZipFile(self.diagnostic_path, 'r') as z:
                    # 查找文件（可能在根目录或子目录）
                    for name in z.namelist():
                        if name.endswith(filename):
                            return z.read(name).decode('utf-8')
            
            # 尝试从已解压目录读取
            elif self.diagnostic_path.is_dir():
                # 在目录中查找文件
                for root, dirs, files in os.walk(self.diagnostic_path):
                    if filename in files:
                        file_path = Path(root) / filename
                        with open(file_path, 'r', encoding='utf-8') as f:
                            return f.read()
            
            logger.warning(f"未找到文件：{filename}")
            return ""
        except Exception as e:
            logger.warning(f"解析 {filename} 失败：{e}")
            return ""
    
    def _load_json(self, filename: str) -> dict:
        """
        加载 JSON 文件（辅助方法，用于提取集群基本信息）
        
        Args:
            filename: 文件名
            
        Returns:
            解析后的字典数据，失败返回空字典
        """
        try:
            file_path = self.diagnostic_path / filename
            if not file_path.exists():
                # 尝试在子目录中查找
                for root, dirs, files in os.walk(self.diagnostic_path):
                    if filename in files:
                        file_path = Path(root) / filename
                        break
            
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"加载文件 {filename} 失败: {e}")
        
        return {}
    
    def extract_cluster_basic_info(self) -> ClusterBasicInfo:
        """
        提取集群基本信息
        
        Returns:
            ClusterBasicInfo 对象
        """
        info = ClusterBasicInfo()
        
        # 1. 从 cluster_health.json 获取基础信息
        health_data = self._load_json('cluster_health.json')
        if health_data:
            info.cluster_name = health_data.get('cluster_name', '未知')
            info.status = health_data.get('status', 'unknown')
            info.nodes_count = health_data.get('number_of_nodes', 0)
            info.data_nodes_count = health_data.get('number_of_data_nodes', 0)
        
        # 2. 从 cluster_stats.json 获取索引和分片信息
        stats_data = self._load_json('cluster_stats.json')
        if stats_data:
            if not info.cluster_name:
                info.cluster_name = stats_data.get('cluster_name', '未知')
            if not info.status:
                info.status = stats_data.get('status', 'unknown')
            
            indices_info = stats_data.get('indices', {})
            info.indices_count = indices_info.get('count', 0)
            
            shards_info = indices_info.get('shards', {})
            info.shards_total = shards_info.get('total', 0)
            
            # 获取版本信息
            versions = stats_data.get('nodes', {}).get('versions', [])
            if versions:
                info.version = versions[0]
        
        # 3. 从 nodes.json 统计主节点数量和检测冷热架构
        nodes_data = self._load_json('nodes.json')
        if nodes_data:
            nodes = nodes_data.get('nodes', {})
            
            # 统计主节点数量（roles 包含 "master"）
            master_count = 0
            has_hot_cold = False
            hot_nodes = 0
            cold_nodes = 0
            
            for node_id, node_info in nodes.items():
                roles = node_info.get('roles', [])
                if 'master' in roles:
                    master_count += 1
                
                # 检测冷热架构（通过 attributes 或 role 判断）
                attributes = node_info.get('attributes', {})
                if 'box_type' in attributes or 'temp' in attributes:
                    has_hot_cold = True
                    if attributes.get('box_type') == 'cold' or attributes.get('temp') == 'cold':
                        cold_nodes += 1
                    else:
                        hot_nodes += 1
            
            info.master_nodes_count = master_count
            info.hot_cold_architecture = has_hot_cold
            
            if has_hot_cold and (hot_nodes + cold_nodes) > 0:
                total = hot_nodes + cold_nodes
                info.hot_cold_ratio = f"{hot_nodes}:{cold_nodes} ({round(hot_nodes/total*100, 1)}%:{round(cold_nodes/total*100, 1)}%)"
            elif has_hot_cold:
                info.hot_cold_ratio = "检测到但未统计到具体比例"
            else:
                info.hot_cold_ratio = "无"
        
        # 4. 从 cluster_settings_defaults.json 获取许可证和安全配置
        settings_data = self._load_json('cluster_settings_defaults.json')
        if settings_data:
            defaults = settings_data.get('defaults', {})
            info.license_type = defaults.get('xpack.license.self_generated.type', '未知')
            security_enabled = defaults.get('xpack.security.enabled', False)
            # 处理字符串类型的布尔值
            if isinstance(security_enabled, str):
                info.security_enabled = security_enabled.lower() in ['true', '1', 'yes']
            else:
                info.security_enabled = bool(security_enabled)
        
        return info
    
    def _convert_size_to_bytes(self, size_str: str) -> int:
        """
        将磁盘大小字符串转换为字节数
        
        Args:
            size_str: 大小字符串，如 "35.1gb", "1.6tb", "15.5gb"
            
        Returns:
            字节数
        """
        if not size_str or not isinstance(size_str, str):
            return 0
        
        try:
            # 去除空格
            size_str = size_str.strip().lower()
            
            # 定义单位映射
            unit_map = {
                'b': 1,
                'kb': 1024,
                'mb': 1024 ** 2,
                'gb': 1024 ** 3,
                'tb': 1024 ** 4,
                'pb': 1024 ** 5
            }
            
            # 使用正则表达式匹配数字和单位
            pattern = re.compile(r'(\d*\.?\d+)\s*([a-z]*)')
            match = pattern.match(size_str)
            
            if not match:
                return 0
            
            size = float(match.group(1))
            unit = match.group(2)
            
            # 如果没有单位，默认是字节
            if not unit:
                return int(size)
            
            multiplier = unit_map.get(unit, 1)
            return int(size * multiplier)
            
        except Exception as e:
            logger.debug(f"转换大小字符串失败：{size_str}, 错误：{e}")
            return 0
    
    def _parse_cat_shards(self) -> Dict[str, int]:
        """
        解析 cat_shards.txt 并统计每个节点的分片数
        
        Returns:
            节点名称到分片数的映射字典，如 {"node-1": 3, "node-2": 5}
        """
        shard_count_map = {}
        
        try:
            # 读取 cat_shards.txt 文件
            content = self._parse_text_file('cat/cat_shards.txt')
            if not content:
                logger.warning("未找到 cat_shards.txt 文件")
                return shard_count_map
            
            lines = content.strip().split('\n')
            if not lines:
                return shard_count_map
            
            logger.info(f"开始解析 cat_shards.txt，共 {len(lines)} 行")
            
            # 跳过表头行（第一行）
            for line in lines[1:]:
                if not line.strip():
                    continue
                
                # 分割列（空格分隔）
                parts = line.split()
                if len(parts) >= 8:
                    # cat_shards.txt 格式：
                    # index shard prirep state docs store ip node
                    # 0     1     2      3     4    5     6  7
                    node_name = parts[7] if len(parts) > 7 else ''
                    
                    if node_name:
                        shard_count_map[node_name] = shard_count_map.get(node_name, 0) + 1
            
            logger.info(f"成功从 cat_shards.txt 统计 {len(shard_count_map)} 个节点的分片数")
            for node_name, count in shard_count_map.items():
                logger.debug(f"  {node_name}: {count} shards")
            
        except Exception as e:
            logger.warning(f"解析 cat_shards.txt 失败：{e}")
        
        return shard_count_map
    
    def extract_shard_summaries(self) -> list:
        """
        提取索引分片汇总信息
        
        Returns:
            索引分片汇总列表，每个元素包含：
            - index_name: 索引名称
            - primary_shard_count: 主分片数量
            - total_size_bytes: 总大小（字节）
            - total_size_gb: 总大小（GB）
        """
        try:
            # 读取 cat_shards.txt 文件（尝试多种路径）
            content = None
            for filename in ['cat/cat_shards.txt', 'cat_shards.txt']:
                content = self._parse_text_file(filename)
                if content:
                    break
            
            if not content:
                logger.warning("未找到 cat_shards.txt 文件，返回空的分片汇总")
                return []
            
            # 使用 ShardsReportParser 解析和聚合
            parser = ShardsReportParser()
            summaries = parser.parse_and_aggregate(content)
            
            # 转换为字典格式
            result = parser.get_summaries_as_dicts()
            logger.info(f"成功提取 {len(result)} 个索引的分片汇总信息")
            
            return result
            
        except Exception as e:
            logger.error(f"提取分片汇总信息失败：{e}")
            import traceback
            logger.debug(traceback.format_exc())
            return []
    
    def extract_shard_distribution(self) -> dict:
        """
        提取主分片分布信息
        
        Returns:
            包含主分片分布信息的字典：
            - distribution: 分片数到索引数的映射
            - total_indices: 总索引数
        """
        try:
            # 读取 cat_shards.txt 文件
            content = None
            for filename in ['cat/cat_shards.txt', 'cat_shards.txt']:
                content = self._parse_text_file(filename)
                if content:
                    logger.info(f"成功读取文件：{filename}")
                    break
            
            if not content:
                logger.warning("未找到 cat_shards.txt 文件，返回空的分片分布")
                return {'distribution': {}, 'total_indices': 0}
            
            # 使用 ShardsReportParser 解析和聚合
            parser = ShardsReportParser()
            summaries = parser.parse_and_aggregate(content)
            
            # 统计主分片分布
            distribution = {}
            for summary in summaries:
                shard_count = summary.primary_shard_count
                if shard_count not in distribution:
                    distribution[shard_count] = 0
                distribution[shard_count] += 1
            
            # 按分片数排序
            sorted_distribution = {k: v for k, v in sorted(distribution.items())}
            
            logger.info(f"成功提取主分片分布信息：{sorted_distribution}")
            return {
                'distribution': sorted_distribution,
                'total_indices': len(summaries)
            }
            
        except Exception as e:
            logger.error(f"提取主分片分布信息失败：{e}")
            import traceback
            logger.debug(traceback.format_exc())
            return {'distribution': {}, 'total_indices': 0}
    
    def extract_large_shards(self, threshold_gb: float = 40) -> list:
        """
        提取单个分片大于指定阈值的索引
        
        Args:
            threshold_gb: 阈值（GB），默认40GB
            
        Returns:
            大分片索引列表，每个元素包含：
            - index_name: 索引名称
            - shard_size_gb: 分片大小（GB）
        """
        try:
            # 读取 cat_shards.txt 文件
            content = None
            for filename in ['cat/cat_shards.txt', 'cat_shards.txt']:
                content = self._parse_text_file(filename)
                if content:
                    logger.info(f"成功读取文件：{filename}")
                    break
            
            if not content:
                logger.warning("未找到 cat_shards.txt 文件，返回空的大分片列表")
                return []
            
            from es_insight.parsers.shards_parser import (
                parse_cat_shards,
                aggregate_index_shards,
            )

            shards = parse_cat_shards(content)
            summaries = aggregate_index_shards(shards)

            large_shards_indices = []
            for summary in summaries:
                if summary.avg_shard_size_gb > threshold_gb:
                    logger.debug(
                        f"索引 {summary.index_name} 的主分片平均大小："
                        f"{summary.avg_shard_size_gb:.2f} GB"
                    )
                    large_shards_indices.append(
                        {
                            "index_name": summary.index_name,
                            "shard_size_gb": summary.avg_shard_size_gb,
                        }
                    )
            
            # 按分片大小排序
            large_shards_indices.sort(key=lambda x: x['shard_size_gb'], reverse=True)
            
            logger.info(f"成功提取 {len(large_shards_indices)} 个大分片索引")
            return large_shards_indices
            
        except Exception as e:
            logger.error(f"提取大分片索引失败：{e}")
            import traceback
            logger.debug(traceback.format_exc())
            return []
    
    def extract_small_shards_with_multiple_primaries(self, threshold_gb: float = 0.5, min_primaries: int = 2) -> dict:
        """
        提取单个分片小于指定阈值且主分片数大于指定值的索引
        
        Args:
            threshold_gb: 阈值（GB），默认0.5GB
            min_primaries: 最小主分片数，默认2
            
        Returns:
            包含小分片多主分片索引信息的字典：
            - count: 索引数量
            - indices: 索引名称列表
        """
        try:
            # 读取 cat_shards.txt 文件
            content = None
            for filename in ['cat/cat_shards.txt', 'cat_shards.txt']:
                content = self._parse_text_file(filename)
                if content:
                    logger.info(f"成功读取文件：{filename}")
                    break
            
            if not content:
                logger.warning("未找到 cat_shards.txt 文件，返回空的小分片多主分片索引信息")
                return {'count': 0, 'indices': []}
            
            # 解析分片数据
            from es_insight.parsers.shards_parser import parse_cat_shards, bytes_to_gb
            shards = parse_cat_shards(content)
            
            # 计算每个索引的分片大小和主分片数
            index_shard_sizes = {}
            index_primary_counts = {}
            
            for shard in shards:
                if shard.is_primary:
                    if shard.index_name not in index_shard_sizes:
                        index_shard_sizes[shard.index_name] = 0
                        index_primary_counts[shard.index_name] = 0
                    index_shard_sizes[shard.index_name] += shard.store_size_bytes
                    index_primary_counts[shard.index_name] += 1
            
            # 找出符合条件的索引
            small_shards_indices = []
            for index_name, total_size in index_shard_sizes.items():
                primary_count = index_primary_counts.get(index_name, 1)
                if primary_count >= min_primaries:
                    avg_shard_size_gb = bytes_to_gb(total_size / primary_count)
                    logger.debug(f"索引 {index_name} 的平均分片大小：{avg_shard_size_gb:.2f} GB，主分片数：{primary_count}")
                    if avg_shard_size_gb < threshold_gb:
                        small_shards_indices.append(index_name)
            
            logger.info(f"成功提取 {len(small_shards_indices)} 个小分片多主分片索引")
            return {
                'count': len(small_shards_indices),
                'indices': small_shards_indices
            }
            
        except Exception as e:
            logger.error(f"提取小分片多主分片索引失败：{e}")
            import traceback
            logger.debug(traceback.format_exc())
            return {'count': 0, 'indices': []}
    
    def _serialize_object(self, obj) -> dict:
        """
        序列化对象为字典
        
        Args:
            obj: 要序列化的对象
            
        Returns:
            字典格式的序列化结果
        """
        if hasattr(obj, '__dict__'):
            result = {}
            for key, value in obj.__dict__.items():
                if isinstance(value, (Issue, IssueSeverity)):
                    result[key] = self._serialize_object(value)
                elif hasattr(value, 'value'):  # Enum 类型
                    result[key] = value.value
                elif isinstance(value, (list, tuple)):
                    result[key] = [self._serialize_object(item) for item in value]
                elif isinstance(value, dict):
                    result[key] = {k: self._serialize_object(v) for k, v in value.items()}
                else:
                    result[key] = value
            return result
        elif isinstance(obj, Issue):
            return {
                'severity': obj.severity.value if hasattr(obj.severity, 'value') else str(obj.severity),
                'title': obj.title,
                'description': obj.description,
                'suggestion': obj.suggestion
            }
        elif isinstance(obj, IssueSeverity):
            return obj.value if hasattr(obj, 'value') else str(obj)
        elif isinstance(obj, dict):
            return {k: self._serialize_object(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._serialize_object(item) for item in obj]
        else:
            return obj
    
    def _find_file(self, filename: str) -> Path:
        """
        在诊断包中查找文件
        
        Args:
            filename: 要查找的文件名
            
        Returns:
            文件路径，如果未找到则返回 None
        """
        import zipfile
        import tempfile
        
        # 将 diagnostic_path 转换为字符串
        diagnostic_path_str = str(self.diagnostic_path)
        
        if diagnostic_path_str.endswith('.zip'):
            # 从 ZIP 文件中查找
            try:
                with zipfile.ZipFile(self.diagnostic_path, 'r') as zip_ref:
                    # 在所有目录中查找
                    for file_path in zip_ref.namelist():
                        if file_path.endswith(filename):
                            # 创建临时目录
                            if not hasattr(self, '_temp_dir'):
                                self._temp_dir = tempfile.mkdtemp(prefix='es_insight_')
                            # 提取到临时目录
                            temp_path = zip_ref.extract(file_path, self._temp_dir)
                            return Path(temp_path)
            except Exception as e:
                logger.debug(f"在 ZIP 中查找 {filename} 失败：{e}")
        else:
            # 从目录中查找
            diagnostic_dir = Path(self.diagnostic_path)
            # 使用 rglob 递归查找
            for file_path in diagnostic_dir.rglob(filename):
                if file_path.is_file():
                    return file_path
        
        return None
    
    def _extract_ilm(self) -> dict:
        """
        提取 ILM（索引生命周期管理）数据
        
        Returns:
            ILM 数据字典
        """
        ilm_data = {
            'ilm_enabled': False,
            'ilm_status': None,
            'policies': [],
            'failed_indices': []
        }
        
        # 1. 读取 ILM 状态
        ilm_status_file = self._find_file('ilm_status.json')
        if ilm_status_file and ilm_status_file.exists():
            try:
                with open(ilm_status_file, 'r', encoding='utf-8') as f:
                    ilm_status = json.load(f)
                    # 修复：使用正确的字段名 operation_mode，值应为 RUNNING
                    ilm_data['ilm_enabled'] = ilm_status.get('operation_mode', '') == 'RUNNING'
                    ilm_data['ilm_status'] = ilm_status.get('operation_mode', 'UNKNOWN')
            except Exception as e:
                logger.debug(f"读取 ILM 状态失败：{e}")
        
        # 2. 读取 ILM 策略
        ilm_policies_file = self._find_file('ilm_policies.json')
        if ilm_policies_file and ilm_policies_file.exists():
            try:
                with open(ilm_policies_file, 'r', encoding='utf-8') as f:
                    policies = json.load(f)
                    if isinstance(policies, dict):
                        ilm_data['policies'] = [
                            {'name': name, **policy}
                            for name, policy in policies.items()
                        ]
            except Exception as e:
                logger.debug(f"读取 ILM 策略失败：{e}")
        
        # 3. 读取 ILM 失败的索引
        ilm_explain_file = self._find_file('ilm_explain_only_errors.json')
        if ilm_explain_file and ilm_explain_file.exists():
            try:
                with open(ilm_explain_file, 'r', encoding='utf-8') as f:
                    explain_data = json.load(f)
                    indices = explain_data.get('indices', {})
                    ilm_data['failed_indices'] = [
                        {'index': index_name, **info}
                        for index_name, info in indices.items()
                    ]
            except Exception as e:
                logger.debug(f"读取 ILM 失败索引失败：{e}")
        
        return ilm_data
    
    def _extract_snapshot(self) -> dict:
        """
        提取快照备份数据
        
        Returns:
            快照数据字典
        """
        snapshot_data = {
            'repositories': [],
            'snapshots': [],
            'snapshot_count': 0
        }
        
        # 读取快照数据
        snapshot_file = self._find_file('snapshot.json')
        if snapshot_file and snapshot_file.exists():
            try:
                with open(snapshot_file, 'r', encoding='utf-8') as f:
                    snapshot_info = json.load(f)
                    
                    # 提取仓库信息
                    repositories = snapshot_info.get('repositories', [])
                    snapshot_data['repositories'] = [
                        {
                            'name': repo.get('name', 'N/A'),
                            'type': repo.get('type', 'N/A'),
                            'settings': repo.get('settings', {})
                        }
                        for repo in repositories
                    ]
                    
                    # 提取快照列表
                    snapshots = snapshot_info.get('snapshots', [])
                    snapshot_data['snapshots'] = [
                        {
                            'snapshot': snap.get('snapshot', 'N/A'),
                            'repository': snap.get('repository', 'N/A'),
                            'state': snap.get('state', 'N/A'),
                            'start_time': snap.get('start_time', ''),
                            'end_time': snap.get('end_time', ''),
                            'shards': snap.get('shards', {}).get('total', 0),
                            'failed_shards': snap.get('shards', {}).get('failed', 0)
                        }
                        for snap in snapshots
                    ]
                    snapshot_data['snapshot_count'] = len(snapshots)
            except Exception as e:
                logger.debug(f"读取快照数据失败：{e}")
        
        return snapshot_data
    
    def _extract_security(self) -> dict:
        """
        提取安全配置数据
        
        Returns:
            安全数据字典
        """
        security_data = {
            'xpack_enabled': False,
            'security_enabled': False,
            'users': [],
            'roles': [],
            'license_type': None
        }
        
        # 1. 读取 X-Pack 配置
        xpack_file = self._find_file('xpack.json')
        if xpack_file and xpack_file.exists():
            try:
                with open(xpack_file, 'r', encoding='utf-8') as f:
                    xpack_info = json.load(f)
                    # xpack.json 结构：直接是扁平结构，security 在顶层
                    # 例如：{"security": {"enabled": true, ...}, "ml": {...}}
                    security_data['xpack_enabled'] = xpack_info.get('security', {}).get('enabled', False)
                    security_data['security_enabled'] = security_data['xpack_enabled']
            except Exception as e:
                logger.debug(f"读取 X-Pack 配置失败：{e}")
        
        # 2. 读取用户列表
        security_users_file = self._find_file('security_users.json')
        if security_users_file and security_users_file.exists():
            try:
                with open(security_users_file, 'r', encoding='utf-8') as f:
                    users = json.load(f)
                    # security_users.json 格式：{"username": {user_info}, ...}
                    # 例如：{"elastic": {"username": "elastic", "roles": ["superuser"], ...}}
                    if isinstance(users, dict):
                        security_data['users'] = [
                            {
                                'username': user_info.get('username', username),
                                'realm': user_info.get('realm', 'N/A'),
                                'roles': user_info.get('roles', []),
                                'full_name': user_info.get('full_name', ''),
                                'email': user_info.get('email', ''),
                                'enabled': user_info.get('enabled', True)
                            }
                            for username, user_info in users.items()
                        ]
                    elif isinstance(users, list):
                        # 兼容列表格式
                        security_data['users'] = [
                            {
                                'username': user.get('username', 'N/A'),
                                'realm': user.get('realm', 'N/A'),
                                'roles': user.get('roles', []),
                                'full_name': user.get('full_name', ''),
                                'email': user.get('email', ''),
                                'enabled': user.get('enabled', True)
                            }
                            for user in users
                        ]
            except Exception as e:
                logger.debug(f"读取安全用户失败：{e}")
        
        # 3. 读取角色列表
        security_roles_file = self._find_file('security_roles.json')
        if security_roles_file and security_roles_file.exists():
            try:
                with open(security_roles_file, 'r', encoding='utf-8') as f:
                    roles = json.load(f)
                    if isinstance(roles, dict):
                        security_data['roles'] = [
                            {'name': role_name, **role_info}
                            for role_name, role_info in roles.items()
                        ]
            except Exception as e:
                logger.debug(f"读取安全角色失败：{e}")
        
        # 4. 读取许可证信息
        licenses_file = self._find_file('licenses.json')
        if licenses_file and licenses_file.exists():
            try:
                with open(licenses_file, 'r', encoding='utf-8') as f:
                    licenses = json.load(f)
                    if isinstance(licenses, list) and len(licenses) > 0:
                        # 获取活动许可证
                        active_license = next(
                            (lic for lic in licenses if lic.get('status') == 'active'),
                            licenses[0]
                        )
                        security_data['license_type'] = active_license.get('type', 'UNKNOWN')
            except Exception as e:
                logger.debug(f"读取许可证信息失败：{e}")
        
        return security_data
    
    def save_to_json(self, data: dict, output_filename: str = None):
        """
        保存数据到 JSON 文件
        
        Args:
            data: 要保存的数据
            output_filename: 输出文件名（可选）
        """
        if output_filename is None:
            output_filename = f"diagnostic_data_{self.timestamp}.json"
        
        output_path = self.output_dir / output_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"数据已保存到：{output_path}")
        return str(output_path)
    
    def extract_and_save(self, output_filename: str = None) -> str:
        """
        提取并保存数据到 JSON 文件
        
        Args:
            output_filename: 输出文件名（可选）
            
        Returns:
            输出文件路径
        """
        data = self.extract_all()
        return self.save_to_json(data, output_filename)


def main():
    """主函数"""
    import sys
    
    # 配置日志
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
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
    
    logger.info(f"开始处理诊断数据：{diagnostic_path}")
    
    # 创建提取器并执行提取
    extractor = DiagnosticDataExtractor(str(diagnostic_path))
    output_path = extractor.extract_and_save()
    
    logger.info(f"✓ 处理完成，输出文件：{output_path}")
    
    # 打印摘要信息
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("\n" + "="*60)
        print("数据提取摘要")
        print("="*60)
        print(f"源文件：{data['metadata']['source']}")
        print(f"提取时间：{data['metadata']['extracted_at']}")
        
        if data.get('cluster_health'):
            health = data['cluster_health']
            print(f"\n集群信息:")
            print(f"  - 集群名称：{health.get('cluster_name', 'N/A')}")
            print(f"  - 状态：{health.get('status', 'N/A')}")
            print(f"  - 节点数：{health.get('number_of_nodes', 0)}")
            print(f"  - 活跃分片比例：{health.get('active_shards_percent', 0)}%")
        
        if data.get('nodes'):
            print(f"\n节点数量：{len(data['nodes'])}")
        
        if data.get('indices'):
            print(f"索引数量：{len(data['indices'])}")
        
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"读取输出文件失败：{e}")


if __name__ == '__main__':
    main()
