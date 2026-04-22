from __future__ import annotations

import math
import struct
from collections.abc import Iterable
from dataclasses import dataclass

from littletiles_obj_tool.block_map import old_block_name_to_new
from littletiles_obj_tool.models import LTBox, LTModel, LTTile
from littletiles_obj_tool.nbt_tags import (
    Compound,
    List,
    String,
    bool_tag,
    double_tag,
    float_tag,
    int_array,
    int_tag,
    long_array,
    string_tag,
)


_BASE_STRUCTURE_IDS = {
    "workbench",
    "importer",
    "exporter",
    "blankomatic",
    "particle_emitter",
    "signal_display",
    "structure_builder",
    "fixed",
    "ladder",
    "bed",
    "chair",
    "storage",
    "noclip",
    "message",
    "item_holder",
    "single_cable1",
    "single_cable4",
    "single_cable16",
    "single_input1",
    "single_input4",
    "single_input16",
    "single_output1",
    "single_output4",
    "single_output16",
    "signal_converter",
}

_CURVE_TYPE_TO_ID = {
    1: "cosine",
    2: "cubic",
    3: "hermite",
}

_OFF_KEY_BY_PART = {
    "OFFX": "oX",
    "OFFY": "oY",
    "OFFZ": "oZ",
    "ROTX": "rX",
    "ROTY": "rY",
    "ROTZ": "rZ",
}

_PARTS = ("OFFX", "OFFY", "OFFZ", "ROTX", "ROTY", "ROTZ")

_SLIDING_OFFSETS = {
    0: ("OFFY", -1.0),
    1: ("OFFY", 1.0),
    2: ("OFFZ", -1.0),
    3: ("OFFZ", 1.0),
    4: ("OFFX", -1.0),
    5: ("OFFX", 1.0),
}


@dataclass(frozen=True)
class _PhysicalPart:
    name: str
    old_key: str
    offset: bool


_PHYSICAL_PARTS = (
    _PhysicalPart("ROTX", "rotX", False),
    _PhysicalPart("ROTY", "rotY", False),
    _PhysicalPart("ROTZ", "rotZ", False),
    _PhysicalPart("OFFX", "offX", True),
    _PhysicalPart("OFFY", "offY", True),
    _PhysicalPart("OFFZ", "offZ", True),
)


def is_old_tag(tag: Compound) -> bool:
    return "t" not in tag and "tiles" in tag and isinstance(tag["tiles"], List)


def collect_old_boxes(tile_tag: Compound) -> list[list[int]]:
    if "boxes" in tile_tag:
        return [[int(v) for v in entry] for entry in tile_tag["boxes"]]
    if "bBox" in tile_tag:
        return [[int(v) for v in tile_tag["bBox"]]]
    if "box" in tile_tag:
        return [[int(v) for v in tile_tag["box"]]]
    return []


def _to_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_bool(value: object, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return bool(value)


def _int_list(value: object) -> list[int]:
    if value is None or isinstance(value, (str, bytes, bytearray, Compound)):
        return []
    if isinstance(value, (list, tuple, List, Iterable)):
        return [_to_int(v) for v in value]
    return []


def _new_physical_state() -> dict[str, float]:
    return {name: 0.0 for name in _PARTS}


def _save_physical_state(state: dict[str, float]) -> Compound:
    saved = Compound()
    for part, key in _OFF_KEY_BY_PART.items():
        value = state.get(part, 0.0)
        if value:
            saved[key] = double_tag(value)
    return saved


def _save_animation_state(name: str, state: dict[str, float], back_to_blockform: bool) -> Compound:
    saved = _save_physical_state(state)
    saved["n"] = string_tag(name)
    if back_to_blockform:
        saved["b"] = bool_tag(True)
    return saved


def _double_from_raw_parts(high: int, low: int) -> float:
    bits = ((high & 0xFFFFFFFF) << 32) | (low & 0xFFFFFFFF)
    return struct.unpack(">d", struct.pack(">Q", bits))[0]


def _double_to_raw_bits(value: float) -> int:
    return struct.unpack(">Q", struct.pack(">d", float(value)))[0]


def _grid_to_vanilla(value: float, grid: int) -> float:
    if grid <= 0:
        return value
    return value / grid


def _save_value_curve(curve_id: str, points: list[tuple[int, float]]) -> Compound | None:
    if not points:
        return None
    curve = Compound()
    curve["id"] = string_tag(curve_id)
    curve["time"] = int_array(tick for tick, _ in points)
    curve["data"] = long_array(_double_to_raw_bits(value) for _, value in points)
    return curve


def _prepare_value_curve(
    part: _PhysicalPart,
    curve_id: str,
    points: list[tuple[int, float]],
    start: dict[str, float],
    end: dict[str, float],
    grid: int,
    duration: int,
) -> Compound | None:
    if not points:
        return None

    if len(points) == 1:
        only_value = points[0][1]
        start[part.name] = only_value
        end[part.name] = only_value
        return None

    mutable_points = [[tick, value] for tick, value in points]

    first = mutable_points[0]
    if part.offset:
        first[1] = _grid_to_vanilla(first[1], grid)
    start[part.name] = first[1]
    if first[0] == 0:
        mutable_points.pop(0)

    if not mutable_points:
        return None

    last = mutable_points[-1]
    if part.offset:
        last[1] = _grid_to_vanilla(last[1], grid)
    end[part.name] = last[1]
    if last[0] == duration:
        mutable_points.pop()

    if not mutable_points:
        return None

    return _save_value_curve(curve_id, [(int(tick), float(value)) for tick, value in mutable_points])


def _load_value_timeline_and_prepare(
    part: _PhysicalPart,
    data: list[int],
    start: dict[str, float],
    end: dict[str, float],
    grid: int,
    duration: int,
) -> Compound | None:
    if not data:
        return None

    curve_id = _CURVE_TYPE_TO_ID.get(data[0], "linear")
    point_count = data[1] if len(data) > 1 else 0
    points: list[tuple[int, float]] = []
    for index in range(max(point_count, 0)):
        tick_index = 2 + index * 3
        high_index = tick_index + 1
        low_index = tick_index + 2
        if low_index >= len(data):
            break

        value = _double_from_raw_parts(data[high_index], data[low_index])
        if math.isnan(value):
            value = 0.0
        points.append((_to_int(data[tick_index]), value))

    return _prepare_value_curve(part, curve_id, points, start, end, grid, duration)


def _collect_events(structure: Compound, opening: bool) -> list[tuple[int, str, object]]:
    collected: list[tuple[int, str, object]] = []
    for entry in structure.get("events", List[Compound]()):
        if not isinstance(entry, Compound):
            continue

        event_id = str(entry.get("id", ""))
        tick = _to_int(entry.get("tick", 0))
        if event_id == "sound-event":
            if _to_bool(entry.get("opening", False)) != opening:
                continue
            data = Compound()
            data["s"] = string_tag(str(entry.get("sound", "")))
            data["v"] = float_tag(_to_float(entry.get("volume", 1.0), 1.0))
            data["p"] = float_tag(_to_float(entry.get("pitch", 1.0), 1.0))
            collected.append((tick, "s", data))
        elif event_id == "child":
            collected.append((tick, "c", int_tag(_to_int(entry.get("childId", 0)))))
    return collected


def _save_timeline(
    duration: int,
    events: list[tuple[int, str, object]],
    curves: dict[str, Compound] | None = None,
) -> Compound:
    timeline = Compound()
    timeline["d"] = int_tag(_to_int(duration))
    timeline["t"] = int_tag(0)
    timeline["eI"] = int_tag(0)

    event_list = List[Compound]()
    for tick, event_id, payload in sorted(events, key=lambda entry: entry[0]):
        event_entry = Compound()
        event_entry["t"] = int_tag(_to_int(tick))
        event_entry["a"] = bool_tag(False)
        event_entry["id"] = string_tag(event_id)
        event_entry["e"] = payload
        event_list.append(event_entry)
    timeline["e"] = event_list

    if curves:
        for part, curve in curves.items():
            timeline[part] = curve
    return timeline


def _save_transition(name: str, from_state: int, to_state: int, timeline: Compound) -> Compound:
    transition = Compound()
    transition["n"] = string_tag(name)
    transition["f"] = int_tag(_to_int(from_state))
    transition["t"] = int_tag(_to_int(to_state))
    transition["a"] = timeline
    return transition


def _save_door(
    converted: Compound,
    start: dict[str, float],
    end: dict[str, float],
    opening: Compound | None,
    closing: Compound | None,
) -> None:
    stay_animated = _to_bool(converted.get("stay", False))
    states = List[Compound]()
    states.append(_save_animation_state("closed", start, not stay_animated))
    states.append(_save_animation_state("opened", end, not stay_animated))
    converted["s"] = states

    transitions = List[Compound]()
    if opening is not None:
        transitions.append(_save_transition("opening", 0, 1, opening))
    if closing is not None:
        transitions.append(_save_transition("closing", 1, 0, closing))
    converted["t"] = transitions


def _convert_structure_palette(value: object, block_map: dict[str, str]) -> List[String]:
    converted = List[String]()
    for entry in _int_list(value):
        key = str(entry)
        converted.append(string_tag(block_map.get(key, key)))
    return converted


def _convert_structure_data_base(structure: Compound, block_map: dict[str, str]) -> Compound:
    converted = Compound()
    for key, value in structure.items():
        if key == "signal":
            converted["ex"] = value
        elif key == "name":
            converted["n"] = value
        elif key == "blocks":
            converted["b"] = _convert_structure_palette(value, block_map)
        elif key == "parent":
            converted["k"] = value
        elif key == "children":
            converted["c"] = value
        else:
            converted[key] = value
    return converted


def _convert_door_base_data(structure: Compound, converted: Compound) -> None:
    if "state" in structure:
        converted["state"] = structure["state"]

    converted["actP"] = bool_tag(_to_bool(structure.get("activateParent", False)))
    converted["hand"] = bool_tag(not _to_bool(structure.get("disableRightClick", False)))
    converted["stay"] = bool_tag(_to_bool(structure.get("stayAnimated", False)))
    converted["sound"] = bool_tag(_to_bool(structure.get("sounds"), True) if "sounds" in structure else True)
    converted["noClip"] = bool_tag(_to_bool(structure.get("noClip", False)))
    converted["du"] = int_tag(_to_int(structure.get("duration", 10), 10))
    converted["in"] = int_tag(_to_int(structure.get("interpolation", 0), 0))
    if "axisCenter" in structure:
        converted["center"] = int_array(_int_list(structure["axisCenter"]))
    converted["aS"] = int_tag(-1)


def _convert_door_structure(structure: Compound, converted: Compound, grid: int) -> None:
    _convert_door_base_data(structure, converted)

    start = _new_physical_state()
    end = _new_physical_state()
    axis = max(0, min(2, _to_int(structure.get("axis", 1))))
    rotation = Compound()
    rotation["a"] = int_tag(axis)

    if _to_int(structure.get("rot-type", 0)) == 1:
        degree = _to_float(structure.get("degree", 0.0))
        rotation["d"] = double_tag(degree)
        end[("ROTX", "ROTY", "ROTZ")[axis]] = degree
    else:
        clockwise = _to_bool(structure.get("clockwise", True), True)
        rotation["c"] = bool_tag(clockwise)
        end[("ROTX", "ROTY", "ROTZ")[axis]] = 90.0 if clockwise else -90.0

    converted["rot"] = rotation
    duration = _to_int(structure.get("duration", 10), 10)
    opening = _save_timeline(duration, _collect_events(structure, True))
    closing = _save_timeline(duration, _collect_events(structure, False))
    _save_door(converted, start, end, opening, closing)
    converted["id"] = string_tag("axis")


def _convert_sliding_door_structure(structure: Compound, converted: Compound, grid: int) -> None:
    _convert_door_base_data(structure, converted)

    start = _new_physical_state()
    end = _new_physical_state()
    direction = _to_int(structure.get("direction", 0))
    distance = _to_int(structure.get("distance", 0))
    converted["direction"] = int_tag(direction)
    converted["dis"] = int_tag(distance)
    converted["disG"] = int_tag(max(grid, 1))

    part, sign = _SLIDING_OFFSETS.get(direction, ("OFFY", -1.0))
    end[part] = sign * _grid_to_vanilla(distance, max(grid, 1))

    duration = _to_int(structure.get("duration", 10), 10)
    opening = _save_timeline(duration, _collect_events(structure, True))
    closing = _save_timeline(duration, _collect_events(structure, False))
    _save_door(converted, start, end, opening, closing)
    converted["id"] = string_tag("sliding")


def _convert_door_activator_structure(structure: Compound, converted: Compound) -> None:
    _convert_door_base_data(structure, converted)

    to_activate = _int_list(structure.get("activate", []))
    converted["act"] = int_array(to_activate)

    events = [(0, "c", int_tag(child)) for child in to_activate]
    start = _new_physical_state()
    end = _new_physical_state()
    timeline = _save_timeline(1, events)
    _save_door(converted, start, end, timeline, timeline)
    converted["id"] = string_tag("activator")


def _convert_advanced_door_structure(structure: Compound, converted: Compound, grid: int) -> None:
    _convert_door_base_data(structure, converted)

    duration = _to_int(structure.get("duration", 10), 10)
    animation = structure.get("animation") if isinstance(structure.get("animation"), Compound) else Compound()
    off_grid = _to_int(animation.get("offGrid", grid), grid)
    start = _new_physical_state()
    end = _new_physical_state()

    curves: dict[str, Compound] = {}
    for part in _PHYSICAL_PARTS:
        data = _int_list(animation.get(part.old_key, []))
        curve = _load_value_timeline_and_prepare(part, data, start, end, off_grid, duration)
        if curve is not None:
            curves[part.name] = curve

    opening = _save_timeline(duration, _collect_events(structure, True), curves)
    closing = _save_timeline(duration, _collect_events(structure, False), curves)
    _save_door(converted, start, end, opening, closing)
    converted["id"] = string_tag("door")


def _convert_structure_children(converted: Compound, block_map: dict[str, str], grid: int) -> None:
    children = converted.get("c")
    if not isinstance(children, List):
        return

    converted_children = List[Compound]()
    for child in children:
        if isinstance(child, Compound):
            converted_children.append(convert_old_structure_data(child, block_map, grid))
    converted["c"] = converted_children


def convert_old_structure_data(
    structure: Compound | None,
    block_map: dict[str, str],
    grid: int,
) -> Compound | None:
    if structure is None or not structure:
        return None

    converted = _convert_structure_data_base(structure, block_map)
    structure_id = str(converted.get("id", ""))

    if structure_id in _BASE_STRUCTURE_IDS:
        if structure_id == "item_holder":
            stack = converted.get("stack")
            if isinstance(stack, Compound) and "id" in stack:
                stack_id = str(stack.get("id", ""))
                stack["id"] = string_tag(block_map.get(stack_id, stack_id))
    elif structure_id == "light":
        converted["id"] = string_tag("light")
        converted["level"] = int_tag(_to_int(converted.get("level", 15), 15))
    elif structure_id == "door":
        _convert_door_structure(structure, converted, grid)
    elif structure_id == "slidingDoor":
        _convert_sliding_door_structure(structure, converted, grid)
    elif structure_id == "doorActivator":
        _convert_door_activator_structure(structure, converted)
    elif structure_id == "advancedDoor":
        _convert_advanced_door_structure(structure, converted, grid)

    _convert_structure_children(converted, block_map, grid)
    return converted


def convert_old_group(tag: Compound, block_map: dict[str, str]) -> LTModel:
    grid = int(tag.get("grid", 16))
    tiles: list[LTTile] = []

    for tile_entry in tag.get("tiles", List[Compound]()):
        tile_tag = tile_entry.get("tile", tile_entry)
        block = old_block_name_to_new(tile_tag, block_map)
        color = int(tile_tag.get("color", -1))
        boxes = [LTBox(array) for array in collect_old_boxes(tile_entry)]
        tiles.append(LTTile(block=block, color=color, boxes=boxes))

    children = [convert_old_group(child, block_map) for child in tag.get("children", List[Compound]())]
    return LTModel(
        grid=grid,
        tiles=tiles,
        structure=convert_old_structure_data(tag.get("structure"), block_map, grid),
        children=children or None,
    )
