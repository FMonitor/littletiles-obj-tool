from __future__ import annotations

from pathlib import Path

from littletiles_obj_tool.constants import DEFAULT_BLOCK_MAP_PATHS
from littletiles_obj_tool.nbt_tags import Compound


def load_block_map(explicit_path: Path | None = None) -> dict[str, str]:
    candidates = [explicit_path] if explicit_path else []
    candidates.extend(DEFAULT_BLOCK_MAP_PATHS)
    for path in candidates:
        if path and path.exists():
            mapping: dict[str, str] = {}
            for line in path.read_text(encoding="utf-8").splitlines():
                if "§" not in line:
                    continue
                old, new = line.split("§", 1)
                mapping[old] = new
            return mapping
    return {}


def old_block_name_to_new(tile_tag: Compound, block_map: dict[str, str]) -> str:
    name = str(tile_tag.get("block", "minecraft:air"))
    meta = int(tile_tag.get("meta", 0))
    if meta:
        name = f"{name}:{meta}"
    return block_map.get(name, name)
