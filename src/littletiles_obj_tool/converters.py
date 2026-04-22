from __future__ import annotations

from pathlib import Path

from littletiles_obj_tool.block_map import load_block_map
from littletiles_obj_tool.nbt_tags import load_snbt, save_snbt
from littletiles_obj_tool.new_format import compute_model_bounds, count_tile_entries, iter_boxes, lt_model_to_tag, parse_new_group
from littletiles_obj_tool.obj_codec import obj_to_model, write_obj
from littletiles_obj_tool.old_format import convert_old_group, is_old_tag


def load_model_from_path(path: Path, block_map_path: Path | None = None):
    block_map = load_block_map(block_map_path)
    tag = load_snbt(path)
    if is_old_tag(tag):
        return convert_old_group(tag, block_map), True
    return parse_new_group(tag), False


def convert_old_to_new(input_path: Path, output_path: Path, block_map_path: Path | None = None) -> None:
    model, is_old = load_model_from_path(input_path, block_map_path)
    if not is_old:
        raise ValueError("Input is not a 1.12-style LittleTiles SNBT file")
    save_snbt(output_path, lt_model_to_tag(model))


def convert_old_to_obj(input_path: Path, output_obj: Path, block_map_path: Path | None = None) -> None:
    model, is_old = load_model_from_path(input_path, block_map_path)
    if not is_old:
        raise ValueError("Input is not a 1.12-style LittleTiles SNBT file")
    write_obj(model, output_obj)


def convert_snbt_to_obj(input_path: Path, output_obj: Path, block_map_path: Path | None = None) -> None:
    model, _ = load_model_from_path(input_path, block_map_path)
    write_obj(model, output_obj)


def convert_obj_to_snbt(
    input_path: Path,
    output_path: Path,
    grid: int,
    max_size: int,
    block: str,
    color: int,
) -> None:
    model = obj_to_model(input_path, grid=grid, max_size=max_size, block=block, color=color)
    save_snbt(output_path, lt_model_to_tag(model))


def inspect_file(input_path: Path, block_map_path: Path | None = None) -> dict[str, object]:
    model, is_old = load_model_from_path(input_path, block_map_path)
    min_x, min_y, min_z, max_x, max_y, max_z = compute_model_bounds(model)
    return {
        "grid": model.grid,
        "source_format": "1.12" if is_old else "1.20",
        "tile_entries": count_tile_entries(model),
        "boxes": sum(1 for _ in iter_boxes(model)),
        "min": (min_x, min_y, min_z),
        "max": (max_x, max_y, max_z),
        "structure": model.structure.get("id") if model.structure else "none",
    }
