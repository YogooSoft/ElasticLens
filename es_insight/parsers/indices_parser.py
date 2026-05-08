"""索引信息解析器"""

from typing import List, Dict
from datetime import datetime
from loguru import logger

from es_insight.models import IndexInfo, HealthStatus
from es_insight.exceptions import ParseError
from .base import DiagnosticFileParser


class IndicesParser(DiagnosticFileParser):
    """索引信息解析器"""
    
    def parse(self) -> List[IndexInfo]:
        """
        解析索引信息（优先使用 indices_stats.json，降级使用 indices.json）
        
        Returns:
            IndexInfo 列表
        """
        try:
            self.extract()
            
            # 优先尝试 indices_stats.json（数据更准确）
            data = None
            source_file = None
            
            try:
                stats_data = self.parse_json("indices_stats.json")
                data = stats_data.get("indices", {})
                source_file = "indices_stats.json"
                logger.info("使用 indices_stats.json 作为数据源（优先）")
            except ParseError:
                # 如果 indices_stats.json 不存在，降级使用 indices.json
                try:
                    data = self.parse_json("indices.json")
                    source_file = "indices.json"
                    logger.info("indices_stats.json 不存在，降级使用 indices.json")
                except ParseError:
                    logger.warning("indices_stats.json 和 indices.json 都不存在")
                    return []
            
            # 根据数据源选择解析逻辑
            if source_file == "indices_stats.json":
                return self._parse_from_indices_stats_json(data)
            else:
                return self._parse_from_indices_json(data)
            
        except Exception as e:
            logger.error(f"解析索引信息失败：{e}")
            raise ParseError(f"解析索引信息失败：{str(e)}")
        finally:
            self.cleanup()
    
    def _parse_from_indices_json(self, data) -> List[IndexInfo]:
        """
        从 indices.json 解析（原有逻辑）
        
        Args:
            data: indices.json 的数据（列表或字典格式）
            
        Returns:
            IndexInfo 列表
        """
        indices = []
        
        # indices.json 是分片级别的列表，需要聚合成索引级别
        if isinstance(data, list):
            indices_dict = {}
            
            for shard_data in data:
                index_name = shard_data.get("index", "unknown")
                
                # 如果索引还没创建，创建新条目
                if index_name not in indices_dict:
                    indices_dict[index_name] = {
                        'uuid': shard_data.get("id", ""),
                        'health': 'green',  # 默认健康
                        'status': 'open',   # 默认打开
                        'primaries': 0,
                        'replicas': 0,
                        'docs_count': 0,
                        'store_size_bytes': 0,
                        'created_time': None
                    }
                
                # 统计主分片和副本分片
                if shard_data.get("prirep") == "p":
                    indices_dict[index_name]['primaries'] += 1
                elif shard_data.get("prirep") == "r":
                    indices_dict[index_name]['replicas'] += 1
                
                # 累加文档数和存储大小（只计算主分片避免重复）
                if shard_data.get("prirep") == "p":
                    try:
                        indices_dict[index_name]['docs_count'] += int(shard_data.get("docs", 0))
                        indices_dict[index_name]['store_size_bytes'] += int(shard_data.get("store", 0))
                    except:
                        pass
                
                # 检查分片状态
                if shard_data.get("state") != "STARTED":
                    indices_dict[index_name]['health'] = 'yellow'
            
            # 转换为 IndexInfo 对象
            for index_name, index_data in indices_dict.items():
                try:
                    index_info = IndexInfo(
                        name=index_name,
                        uuid=index_data['uuid'],
                        health=HealthStatus(index_data['health']),
                        status=index_data['status'],
                        primary_shards=index_data['primaries'],
                        replica_shards=index_data['replicas'],
                        docs_count=index_data['docs_count'],
                        store_size_bytes=index_data['store_size_bytes'],
                        created_time=index_data['created_time']
                    )
                    indices.append(index_info)
                except Exception as e:
                    logger.warning(f"处理索引 {index_name} 失败：{e}")
                    continue
        
        # 兼容旧的字典格式
        elif isinstance(data, dict):
            for index_name, index_data in data.items():
                try:
                    # 计算文档数和存储大小
                    docs_count = int(index_data.get("docs", {}).get("count", 0))
                    store_size = int(index_data.get("store", {}).get("size_in_bytes", 0))
                    
                    # 解析创建时间
                    created_str = index_data.get("settings", {}).get(
                        "index", {}).get("creation_date")
                    created_time = None
                    if created_str:
                        try:
                            created_time = datetime.fromtimestamp(
                                int(created_str) / 1000)
                        except:
                            pass
                    
                    index_info = IndexInfo(
                        name=index_name,
                        uuid=index_data.get("uuid", ""),
                        health=HealthStatus(
                            index_data.get("health", "red")),
                        status=index_data.get("status", "open"),
                        primary_shards=int(
                            index_data.get("primaries", 0)),
                        replica_shards=int(
                            index_data.get("replicas", 0)),
                        docs_count=docs_count,
                        store_size_bytes=store_size,
                        created_time=created_time
                    )
                    indices.append(index_info)
                except Exception as e:
                    logger.warning(f"解析索引 {index_name} 失败：{e}")
                    continue
        
        logger.info(f"成功从 indices.json 解析 {len(indices)} 个索引信息")
        return indices
    
    def _parse_from_indices_stats_json(self, data) -> List[IndexInfo]:
        """
        从 indices_stats.json 解析（新增逻辑）
        
        Args:
            data: indices_stats.json 中的 indices 字段（字典格式）
            
        Returns:
            IndexInfo 列表
        """
        indices = []
        
        for index_name, index_data in data.items():
            try:
                # 1. 基本信息
                uuid = index_data.get("uuid", "")
                
                # 2. 文档数和存储大小（使用 primaries 避免重复计算）
                docs_count = index_data.get("primaries", {}).get("docs", {}).get("count", 0)
                store_size_bytes = index_data.get("primaries", {}).get("store", {}).get("size_in_bytes", 0)
                
                # 3. 统计主分片和副本分片数量
                shards_info = index_data.get("shards", {})
                primary_count = 0
                replica_count = 0
                has_unhealthy_shard = False
                
                for shard_num, shard_copies in shards_info.items():
                    if isinstance(shard_copies, list):
                        for shard_copy in shard_copies:
                            routing = shard_copy.get("routing", {})
                            is_primary = routing.get("primary", False)
                            state = routing.get("state", "")
                            
                            if is_primary:
                                primary_count += 1
                            else:
                                replica_count += 1
                            
                            # 检查分片状态
                            if state != "STARTED":
                                has_unhealthy_shard = True
                
                # 4. 推断健康状态
                health = "yellow" if has_unhealthy_shard else "green"
                
                # 5. 索引状态（默认 open）
                status = "open"
                
                # 6. 创建时间（暂不支持）
                created_time = None
                
                # 7. 创建 IndexInfo 对象
                index_info = IndexInfo(
                    name=index_name,
                    uuid=uuid,
                    health=HealthStatus(health),
                    status=status,
                    primary_shards=primary_count,
                    replica_shards=replica_count,
                    docs_count=docs_count,
                    store_size_bytes=store_size_bytes,
                    created_time=created_time
                )
                indices.append(index_info)
                
            except Exception as e:
                logger.warning(f"解析索引 {index_name} 失败：{e}")
                continue
        
        logger.info(f"成功从 indices_stats.json 解析 {len(indices)} 个索引信息")
        return indices
