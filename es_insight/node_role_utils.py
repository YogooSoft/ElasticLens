"""节点角色识别（兼容 _cat/nodes 缩写与 nodes_stats 完整角色名）"""

from typing import Any, Iterable, List

# ES 7.x cat/nodes 常见 data 相关缩写（如 hot+ingest+… → his）
_DATA_CAT_ABBREVS = frozenset({"d", "his"})

_DATA_ROLE_PREFIXES = (
    "data_content",
    "data_hot",
    "data_warm",
    "data_cold",
    "data_frozen",
    "data",
)


def normalize_roles(roles: Any) -> List[str]:
    if roles is None:
        return []
    if isinstance(roles, str):
        return [roles] if roles.strip() else []
    return [str(r) for r in roles if r is not None and str(r).strip()]


def roles_concat_lower(roles: Any) -> str:
    return "".join(normalize_roles(roles)).lower()


def is_master_eligible_node(roles: Any) -> bool:
    roles_list = normalize_roles(roles)
    concat = roles_concat_lower(roles_list)
    if "master" in concat:
        return True
    if any(r.lower() in ("m", "master") for r in roles_list):
        return True
    return "m" in concat and concat not in ("-", "")


def is_data_node(roles: Any) -> bool:
    roles_list = normalize_roles(roles)
    for role in roles_list:
        r = role.lower().strip()
        if r in _DATA_CAT_ABBREVS:
            return True
        if r == "data" or r.startswith("data_"):
            return True
        if any(r == p or r.startswith(p + "_") for p in _DATA_ROLE_PREFIXES):
            return True
    concat = roles_concat_lower(roles_list)
    if "his" in concat:
        return True
    if "data" in concat:
        return True
    # 传统 cat 缩写：含字母 d（如 md、di），排除纯占位 "-"
    if concat and concat != "-" and "d" in concat:
        return True
    return False


def is_dedicated_coordinator_node(roles: Any) -> bool:
    """专用协调节点：非 master、非 data、非 ingest。"""
    if is_master_eligible_node(roles) or is_data_node(roles):
        return False
    roles_list = normalize_roles(roles)
    concat = roles_concat_lower(roles_list)
    if concat in ("", "-"):
        return True
    if "ingest" in concat or "i" in concat:
        return False
    return True
