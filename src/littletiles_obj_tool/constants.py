from __future__ import annotations

from pathlib import Path


CORNER_ORDER = (
    ("eun", True, True, False),
    ("eus", True, True, True),
    ("edn", True, False, False),
    ("eds", True, False, True),
    ("wun", False, True, False),
    ("wus", False, True, True),
    ("wdn", False, False, False),
    ("wds", False, False, True),
)

FACE_QUADS = {
    "east": (0, 1, 3, 2),
    "west": (4, 6, 7, 5),
    "up": (4, 5, 1, 0),
    "down": (6, 2, 3, 7),
    "north": (4, 0, 2, 6),
    "south": (5, 7, 3, 1),
}

DEFAULT_BLOCK_MAP_PATHS = (
    Path(__file__).resolve().parents[3] / "LittleTiles" / "src" / "main" / "resources" / "1.12.2.txt",
    Path(__file__).resolve().parents[3] / "LittleTiles-1.12" / "src" / "main" / "resources" / "1.12.2.txt",
)
