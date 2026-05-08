"""节点信息解析器"""

from typing import List, Dict
from loguru import logger

from es_insight.models import NodeInfo
from es_insight.exceptions import ParseError
from .base import DiagnosticFileParser


class NodesParser(DiagnosticFileParser):
    """节点信息解析器"""
    
    def parse_short(self) -> List[NodeInfo]:
        """
        解析 nodes_short.json
        
        Returns:
            NodeInfo 列表
        """
        try:
            self.extract()
            data = self.parse_json("nodes_short.json")
            
            nodes = []
            # nodes_short.json 是列表格式，不是字典
            if isinstance(data, list):
                for node_data in data:
                    try:
                        node = NodeInfo(
                            name=node_data.get("name", "unknown"),
                            id=node_data.get("id", ""),
                            ip=node_data.get("ip", ""),
                            version="",  # nodes_short 中没有版本信息，后续从 nodes.json 补充
                            roles=[node_data.get("role", "")],  # 从 nodes.json 补充完整 roles
                            is_master=node_data.get("master", "") == "*",
                            disk_used_percent=0.0,  # nodes_short 中没有磁盘信息
                            heap_used_percent=0.0,  # nodes_short 中没有内存信息
                            cpu_percent=0.0,  # nodes_short 中没有 CPU 信息
                            load_1m=0.0,
                            load_5m=0.0,
                            load_15m=0.0,
                            shard_count=0,  # nodes_short 中没有分片数信息
                            mem_total="未知",
                            mem_total_bytes=0,
                            jvm_heap_max="未知",
                            jvm_heap_max_bytes=0,
                            uptime="未知",
                            uptime_millis=0,
                            disk_total="未知",
                            disk_total_bytes=0,
                            available_processors=0,
                            allocated_processors=0
                        )
                        nodes.append(node)
                    except Exception as e:
                        logger.warning(f"解析节点 {node_data.get('name', 'unknown')} 失败：{e}")
                        continue
            elif isinstance(data, dict):
                # 兼容旧的字典格式
                for node_id, node_data in data.items():
                    try:
                        node = NodeInfo(
                            name=node_data.get("name", "unknown"),
                            id=node_id,
                            ip=node_data.get("ip", ""),
                            version=node_data.get("version", ""),
                            roles=node_data.get("roles", []),
                            is_master="master" in node_data.get("roles", []),
                            disk_used_percent=float(node_data.get("fs", {}).get("total", {}).get("available_in_bytes", 0)),
                            heap_used_percent=float(node_data.get("jvm", {}).get("mem", {}).get("heap_used_percent", 0)),
                            cpu_percent=float(node_data.get("os", {}).get("cpu", {}).get("percent", 0)),
                            load_1m=float(node_data.get("os", {}).get("cpu", {}).get("load", {}).get("1", 0)),
                            load_5m=float(node_data.get("os", {}).get("cpu", {}).get("load", {}).get("5", 0)),
                            load_15m=float(node_data.get("os", {}).get("cpu", {}).get("load", {}).get("15", 0)),
                            shard_count=int(node_data.get("shards", 0)),
                            cpu_cores=int(node_data.get("os", {}).get("available_processors", 0)),
                            mem_total=node_data.get("os", {}).get("mem", {}).get("total", "未知"),
                            mem_total_bytes=node_data.get("os", {}).get("mem", {}).get("total_in_bytes", 0),
                            jvm_heap_max=node_data.get("jvm", {}).get("mem", {}).get("heap_max", "未知"),
                            jvm_heap_max_bytes=node_data.get("jvm", {}).get("mem", {}).get("heap_max_in_bytes", 0),
                            uptime=node_data.get("jvm", {}).get("uptime", "未知"),
                            uptime_millis=node_data.get("jvm", {}).get("uptime_in_millis", 0),
                            disk_total="未知",  # 需要从 allocation.json 获取
                            disk_total_bytes=0,
                            available_processors=node_data.get("os", {}).get("available_processors", 0),
                            allocated_processors=node_data.get("os", {}).get("allocated_processors", 0)
                        )
                        nodes.append(node)
                    except Exception as e:
                        logger.warning(f"解析节点 {node_id} 失败：{e}")
                        continue
            
            logger.info(f"成功解析 {len(nodes)} 个节点信息")
            return nodes
            
        except Exception as e:
            logger.error(f"解析节点信息失败：{e}")
            raise ParseError(f"解析节点信息失败：{str(e)}")
        finally:
            self.cleanup()
    
    def parse_nodes_json(self) -> Dict:
        """
        解析 nodes.json（包含节点的完整配置信息）
        
        Returns:
            原始 nodes.json 数据字典
        """
        try:
            self.extract()
            data = self.parse_json("nodes.json")
            logger.info("成功解析 nodes.json")
            return data
        except Exception as e:
            logger.error(f"解析 nodes.json 失败：{e}")
            raise ParseError(f"解析 nodes.json 失败：{str(e)}")
        finally:
            self.cleanup()
    
    def parse_stats(self) -> Dict:
        """
        解析 nodes_stats.json
        
        Returns:
            原始统计数据字典
        """
        try:
            self.extract()
            data = self.parse_json("nodes_stats.json")
            logger.info("成功解析节点统计数据")
            return data
        except Exception as e:
            logger.error(f"解析节点统计失败：{e}")
            raise ParseError(f"解析节点统计失败：{str(e)}")
        finally:
            self.cleanup()
