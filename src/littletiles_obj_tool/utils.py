from __future__ import annotations

import re

from littletiles_obj_tool.nbt_tags import signed_int32


def sanitize_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def normalize_argb(color: int) -> int:
    if 0 <= color <= 0xFFFFFF:
        return signed_int32(0xFF000000 | color)
    return signed_int32(color)


def color_to_rgba_bytes(color: int) -> tuple[int, int, int, int]:
    value = normalize_argb(color) & 0xFFFFFFFF
    a = (value >> 24) & 0xFF
    r = (value >> 16) & 0xFF
    g = (value >> 8) & 0xFF
    b = value & 0xFF
    return (r, g, b, a)


def color_to_rgb(color: int) -> tuple[float, float, float]:
    r, g, b, _ = color_to_rgba_bytes(color)
    return (r / 255.0, g / 255.0, b / 255.0)


def color_to_opacity(color: int) -> float:
    _, _, _, a = color_to_rgba_bytes(color)
    return a / 255.0


def rgb_hex_to_signed_argb(value: str) -> int:
    text = value.strip()
    if text.startswith("#"):
        text = text[1:]
    if len(text) != 6 or any(char not in "0123456789abcdefABCDEF" for char in text):
        raise ValueError(f"Invalid RGB hex color: {value}")
    return signed_int32(0xFF000000 | int(text, 16))


def rgb_triplet_to_signed_argb(r: int, g: int, b: int) -> int:
    channels = [r, g, b]
    if any(channel < 0 or channel > 255 for channel in channels):
        raise ValueError("RGB values must be between 0 and 255")
    return signed_int32(0xFF000000 | (r << 16) | (g << 8) | b)


def rgba_to_signed_argb(r: int, g: int, b: int, a: int) -> int:
    channels = [r, g, b, a]
    if any(channel < 0 or channel > 255 for channel in channels):
        raise ValueError("RGBA values must be between 0 and 255")
    return signed_int32((a << 24) | (r << 16) | (g << 8) | b)


def parse_color_value(color: int | None = None, color_hex: str | None = None) -> int:
    if color_hex:
        return rgb_hex_to_signed_argb(color_hex)
    if color is None:
        return -1
    return normalize_argb(color)
