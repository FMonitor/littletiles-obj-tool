from __future__ import annotations

import math
from typing import Iterable

from littletiles_obj_tool.models import LTBox, LTModel, LTTile
from littletiles_obj_tool.nbt_tags import Compound, Int, IntArray, List, int_array


def parse_new_group(tag: Compound) -> LTModel:
    grid = int(tag.get("grid", 16))
    tiles: list[LTTile] = []
    for block, box_list in tag.get("t", Compound()).items():
        current_color: int | None = None
        current_boxes: list[LTBox] = []
        for entry in box_list:
            ints = [int(v) for v in entry]
            if len(ints) == 1:
                if current_color is not None and current_boxes:
                    tiles.append(LTTile(block=str(block), color=current_color, boxes=current_boxes))
                current_color = ints[0]
                current_boxes = []
            else:
                current_boxes.append(LTBox(ints))
        if current_color is not None and current_boxes:
            tiles.append(LTTile(block=str(block), color=current_color, boxes=current_boxes))

    children = [parse_new_group(child) for child in tag.get("c", List[Compound]())]
    return LTModel(
        grid=grid,
        tiles=tiles,
        structure=tag.get("s") if "s" in tag else None,
        children=children or None,
    )


def iter_boxes(model: LTModel) -> Iterable[tuple[LTTile, LTBox]]:
    for tile in model.tiles:
        for box in tile.boxes:
            yield tile, box
    for child in model.children or []:
        yield from iter_boxes(child)


def compute_model_bounds(model: LTModel) -> tuple[int, int, int, int, int, int]:
    mins = [math.inf, math.inf, math.inf]
    maxs = [-math.inf, -math.inf, -math.inf]
    any_box = False

    def visit(group: LTModel) -> None:
        nonlocal any_box
        for tile in group.tiles:
            for box in tile.boxes:
                any_box = True
                bounds = box.bounds
                mins[0] = min(mins[0], bounds[0])
                mins[1] = min(mins[1], bounds[1])
                mins[2] = min(mins[2], bounds[2])
                maxs[0] = max(maxs[0], bounds[3])
                maxs[1] = max(maxs[1], bounds[4])
                maxs[2] = max(maxs[2], bounds[5])
        for child in group.children or []:
            visit(child)

    visit(model)
    if not any_box:
        return (0, 0, 0, 0, 0, 0)
    return tuple(int(v) for v in (*mins, *maxs))


def count_tile_entries(model: LTModel) -> int:
    total = len(model.tiles)
    for child in model.children or []:
        total += count_tile_entries(child)
    return total


def tiles_to_compound(tiles: list[LTTile]) -> Compound:
    by_block: dict[str, list[LTTile]] = {}
    for tile in tiles:
        by_block.setdefault(tile.block, []).append(tile)

    compound = Compound()
    for block, tile_list in by_block.items():
        entries = []
        for tile in tile_list:
            entries.append(int_array((tile.color,)))
            for box in tile.boxes:
                entries.append(int_array(box.array))
        compound[block] = List[IntArray](entries)
    return compound


def lt_model_to_tag(model: LTModel, root: bool = True) -> Compound:
    tag = Compound()
    if model.structure:
        tag["s"] = model.structure
    tag["t"] = tiles_to_compound(model.tiles)
    if model.grid != 16:
        tag["grid"] = Int(model.grid)

    if model.children:
        tag["c"] = List[Compound]([lt_model_to_tag(child, root=False) for child in model.children])

    if root:
        min_x, min_y, min_z, max_x, max_y, max_z = compute_model_bounds(model)
        tag["min"] = int_array((min_x, min_y, min_z))
        tag["size"] = int_array((max_x - min_x, max_y - min_y, max_z - min_z))
        tag["tiles"] = Int(count_tile_entries(model))
        tag["boxes"] = Int(sum(1 for _ in iter_boxes(model)))
    return tag
