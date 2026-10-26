"""Segment 数量检查（对齐 ES diagnostic_support indices_too_many_segments）"""

from typing import Any, Dict, List, Optional

from es_insight.shard_size_check import index_name_from_record

DEFAULT_PER_PRIMARY_SHARD_SEGMENTS = 35


def per_primary_shard_threshold(config: Optional[Dict[str, Any]] = None) -> int:
    if not config:
        return DEFAULT_PER_PRIMARY_SHARD_SEGMENTS
    seg = config.get("index", {}).get("segments_count", {})
    raw = seg.get("per_primary_shard", DEFAULT_PER_PRIMARY_SHARD_SEGMENTS)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return DEFAULT_PER_PRIMARY_SHARD_SEGMENTS


def find_indices_with_too_many_segments(
    indices: List[dict], per_shard_threshold: int
) -> List[Dict[str, Any]]:
    """
    任一分片 segments.count > per_shard_threshold 的索引（与 diagnostic_support 一致）。
    依赖 indices 上的 max_primary_shard_segments（解析自 indices_stats.json）。
    """
    result: List[Dict[str, Any]] = []
    for idx in indices:
        if idx.get("status") != "open":
            continue
        max_primary = int(idx.get("max_primary_shard_segments") or 0)
        if max_primary <= per_shard_threshold:
            continue
        result.append(
            {
                "index_name": index_name_from_record(idx),
                "segments_count": int(idx.get("segments_count") or 0),
                "max_primary_shard_segments": max_primary,
            }
        )
    result.sort(key=lambda x: x["max_primary_shard_segments"], reverse=True)
    return result


def find_indices_segment_count_over(
    indices: List[dict], critical: int
) -> List[Dict[str, Any]]:
    """索引级 segments_count >= critical（规则引擎 / 索引健康）。"""
    result: List[Dict[str, Any]] = []
    for idx in indices:
        count = int(idx.get("segments_count") or 0)
        if count >= critical:
            result.append(
                {
                    "index_name": index_name_from_record(idx),
                    "segments_count": count,
                }
            )
    result.sort(key=lambda x: x["segments_count"], reverse=True)
    return result
