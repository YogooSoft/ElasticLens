"""主分片单分片大小检查（>40GB 等）的共享逻辑"""

from typing import Any, Dict, List, Optional

DEFAULT_OVERSIZED_PRIMARY_SHARD_GB = 40.0


def index_primary_shards(idx: dict) -> int:
    """兼容 diagnostic JSON（primary_shards）与 cat 风格（pri）。"""
    val = idx.get("primary_shards")
    if val is None:
        val = idx.get("pri")
    try:
        return int(val or 0)
    except (TypeError, ValueError):
        return 0


def index_replica_shards(idx: dict) -> int:
    val = idx.get("replica_shards")
    if val is None:
        val = idx.get("rep")
    try:
        return int(val or 0)
    except (TypeError, ValueError):
        return 0


def index_name_from_record(idx: dict) -> str:
    return idx.get("name") or idx.get("index") or "unknown"


def oversized_primary_shard_threshold_gb(config: Optional[Dict[str, Any]] = None) -> float:
    """从规则配置读取主分片过大阈值，默认 40GB。"""
    if not config:
        return DEFAULT_OVERSIZED_PRIMARY_SHARD_GB
    size_gb = config.get("shard", {}).get("size_gb", {})
    raw = size_gb.get("oversized_primary", DEFAULT_OVERSIZED_PRIMARY_SHARD_GB)
    try:
        return float(raw)
    except (TypeError, ValueError):
        return DEFAULT_OVERSIZED_PRIMARY_SHARD_GB


def oversized_single_shard_threshold_gb(config: Optional[Dict[str, Any]] = None) -> float:
    """物理分片 store 过大阈值（shards 检查），默认与 oversized_primary 一致。"""
    if not config:
        return DEFAULT_OVERSIZED_PRIMARY_SHARD_GB
    size_gb = config.get("shard", {}).get("size_gb", {})
    raw = size_gb.get(
        "oversized_single_shard",
        size_gb.get("oversized_primary", DEFAULT_OVERSIZED_PRIMARY_SHARD_GB),
    )
    try:
        return float(raw)
    except (TypeError, ValueError):
        return DEFAULT_OVERSIZED_PRIMARY_SHARD_GB


def count_physical_shards_over_size_gb(
    shards: List[dict], threshold_gb: float
) -> int:
    """统计 store 字节数严格大于 threshold_gb 的物理分片个数。"""
    limit = threshold_gb * (1024**3)
    count = 0
    for shard in shards:
        try:
            store = int(shard.get("store") or 0)
        except (TypeError, ValueError):
            store = 0
        if store > limit:
            count += 1
    return count


def avg_primary_shard_size_gb(store_size_bytes: int, primary_shards: int) -> float:
    if primary_shards <= 0 or store_size_bytes <= 0:
        return 0.0
    return store_size_bytes / primary_shards / (1024**3)


def find_oversized_primary_shard_indices(
    indices: List[dict], threshold_gb: float
) -> List[Dict[str, Any]]:
    """
    按 indices 数组检测单主分片平均大小超过阈值的索引。

    store_size_bytes 应为主分片存储合计（与 IndicesParser / indices_stats 一致）。
    """
    result: List[Dict[str, Any]] = []
    for idx in indices:
        if idx.get("status") != "open":
            continue
        pri = index_primary_shards(idx)
        store = int(idx.get("store_size_bytes") or 0)
        if pri <= 0 or store <= 0:
            continue
        shard_size_gb = avg_primary_shard_size_gb(store, pri)
        if shard_size_gb > threshold_gb:
            result.append(
                {
                    "index_name": index_name_from_record(idx),
                    "shard_size_gb": round(shard_size_gb, 2),
                }
            )
    result.sort(key=lambda x: x["shard_size_gb"], reverse=True)
    return result
