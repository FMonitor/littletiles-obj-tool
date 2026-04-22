from __future__ import annotations

from pathlib import Path
from typing import Iterable

from littletiles_obj_tool.bootstrap import setup_local_deps


setup_local_deps()

try:
    from nbtlib import Byte, Compound, Double, Float, Int, IntArray, List, Long, LongArray, String, parse_nbt
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependencies. Install them with:\n"
        "python3 -m pip install --target ./.deps nbtlib Flask"
    ) from exc


def bit_is(value: int, index: int) -> bool:
    return ((value >> index) & 1) == 1


def signed_short(value: int) -> int:
    return value - 0x10000 if value >= 0x8000 else value


def unpack_short(transform_data: list[int], index: int) -> int:
    real_index = index // 2 + 1
    packed = transform_data[real_index]
    if index % 2 == 1:
        return signed_short(packed & 0xFFFF)
    return signed_short((packed >> 16) & 0xFFFF)


def signed_int32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value >= 0x80000000 else value


def signed_int64(value: int) -> int:
    value &= 0xFFFFFFFFFFFFFFFF
    return value - 0x10000000000000000 if value >= 0x8000000000000000 else value


def int_array(values: Iterable[int]) -> IntArray:
    return IntArray([Int(signed_int32(int(v))) for v in values])


def long_array(values: Iterable[int]) -> LongArray:
    return LongArray([Long(signed_int64(int(v))) for v in values])


def int_tag(value: int) -> Int:
    return Int(signed_int32(int(value)))


def bool_tag(value: bool) -> Byte:
    return Byte(1 if value else 0)


def double_tag(value: float) -> Double:
    return Double(float(value))


def float_tag(value: float) -> Float:
    return Float(float(value))


def string_tag(value: str) -> String:
    return String(str(value))


def load_snbt(path: Path) -> Compound:
    return parse_nbt(path.read_text(encoding="utf-8"))


def save_snbt(path: Path, tag: Compound) -> None:
    path.write_text(tag.snbt(), encoding="utf-8")
