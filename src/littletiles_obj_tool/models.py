from __future__ import annotations

from dataclasses import dataclass

from littletiles_obj_tool.constants import CORNER_ORDER
from littletiles_obj_tool.nbt_tags import Compound, bit_is, unpack_short


@dataclass
class LTBox:
    array: list[int]

    @property
    def bounds(self) -> tuple[int, int, int, int, int, int]:
        return tuple(self.array[:6])

    @property
    def transform_data(self) -> list[int]:
        return self.array[6:]

    @property
    def is_transformable(self) -> bool:
        return len(self.array) > 6 and self.array[6] < 0

    def corners(self) -> list[tuple[int, int, int]]:
        min_x, min_y, min_z, max_x, max_y, max_z = self.bounds
        base = []
        for _, east, up, south in CORNER_ORDER:
            base.append(
                (
                    max_x if east else min_x,
                    max_y if up else min_y,
                    max_z if south else min_z,
                )
            )

        if not self.is_transformable:
            return base

        data = self.transform_data
        indicator = data[0]
        active_bits = 0
        tilted: list[tuple[int, int, int]] = []
        for i, (x0, y0, z0) in enumerate(base):
            dx = dy = dz = 0
            index = i * 3
            if bit_is(indicator, index):
                dx = unpack_short(data, active_bits)
                active_bits += 1
            if bit_is(indicator, index + 1):
                dy = unpack_short(data, active_bits)
                active_bits += 1
            if bit_is(indicator, index + 2):
                dz = unpack_short(data, active_bits)
                active_bits += 1
            tilted.append((x0 + dx, y0 + dy, z0 + dz))
        return tilted


@dataclass
class LTTile:
    block: str
    color: int
    boxes: list[LTBox]


@dataclass
class LTModel:
    grid: int
    tiles: list[LTTile]
    structure: Compound | None = None
    children: list["LTModel"] | None = None
