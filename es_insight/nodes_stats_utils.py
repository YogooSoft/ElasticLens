"""nodes_stats.json 解析结果的辅助函数"""

from typing import Any, Dict, List


def get_nodes_stats_payload(data: dict) -> dict:
    """返回含 nodes 字典的 nodes_stats 根对象；无效时返回空 dict。"""
    raw = data.get("nodes_stats") or {}
    if isinstance(raw, dict) and "nodes" in raw and isinstance(raw["nodes"], dict):
        return raw
    return {}


def find_nodes_with_search_missing(nodes_stats_payload: dict) -> List[Dict[str, Any]]:
    """与 diagnostic_support nodes_missing() 一致：missing_total > 0 的节点。"""
    result: List[Dict[str, Any]] = []
    nodes = nodes_stats_payload.get("nodes") or {}
    for node_id, stats in nodes.items():
        missing_total = stats.get("indices", {}).get("get", {}).get("missing_total", 0)
        try:
            missing_total = int(missing_total or 0)
        except (TypeError, ValueError):
            missing_total = 0
        if missing_total > 0:
            result.append(
                {
                    "name": stats.get("name", node_id),
                    "missing_total": missing_total,
                }
            )
    result.sort(key=lambda x: x["missing_total"], reverse=True)
    return result
