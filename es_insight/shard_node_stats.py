"""分片按节点聚合统计"""

from typing import Dict, List, Tuple


def count_shards_per_node(shards: List[dict]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for shard in shards:
        node_name = shard.get("node") or shard.get("node_name") or ""
        if node_name:
            counts[node_name] = counts.get(node_name, 0) + 1
    return counts


def max_shards_on_single_node(shards: List[dict]) -> Tuple[int, str]:
    """返回 (单节点最大分片数, 节点名)。"""
    counts = count_shards_per_node(shards)
    if not counts:
        return 0, "N/A"
    node_name = max(counts, key=counts.get)
    return counts[node_name], node_name
