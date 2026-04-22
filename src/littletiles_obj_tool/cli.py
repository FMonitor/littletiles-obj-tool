from __future__ import annotations

import argparse
from pathlib import Path

from littletiles_obj_tool.converters import (
    convert_obj_to_snbt,
    convert_old_to_new,
    convert_old_to_obj,
    convert_snbt_to_obj,
    inspect_file,
)
from littletiles_obj_tool.utils import parse_color_value


def handle_old_to_new(args: argparse.Namespace) -> None:
    convert_old_to_new(Path(args.input), Path(args.output), Path(args.block_map) if args.block_map else None)


def handle_old_to_obj(args: argparse.Namespace) -> None:
    convert_old_to_obj(Path(args.input), Path(args.output), Path(args.block_map) if args.block_map else None)


def handle_snbt_to_obj(args: argparse.Namespace) -> None:
    convert_snbt_to_obj(Path(args.input), Path(args.output), Path(args.block_map) if args.block_map else None)


def handle_obj_to_snbt(args: argparse.Namespace) -> None:
    convert_obj_to_snbt(
        Path(args.input),
        Path(args.output),
        grid=int(args.grid),
        max_size=int(args.max_size),
        block=args.block,
        color=parse_color_value(color=args.color, color_hex=args.color_hex),
    )


def handle_inspect(args: argparse.Namespace) -> None:
    data = inspect_file(Path(args.input), Path(args.block_map) if args.block_map else None)
    print(f"source_format={data['source_format']}")
    print(f"grid={data['grid']}")
    print(f"tile_entries={data['tile_entries']}")
    print(f"boxes={data['boxes']}")
    print(f"bounds=min{data['min']} max{data['max']}")
    print(f"structure={data['structure']}")


def handle_serve(args: argparse.Namespace) -> None:
    from littletiles_obj_tool.web import main as web_main

    web_main(host=args.host, port=args.port, debug=args.debug)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LittleTiles 1.12/1.20 SNBT and OBJ conversion helper")
    sub = parser.add_subparsers(dest="command", required=True)

    old_to_new = sub.add_parser("old-to-new", help="Convert 1.12-style LittleTiles SNBT to 1.20-style SNBT")
    old_to_new.add_argument("input")
    old_to_new.add_argument("output")
    old_to_new.add_argument("--block-map", help="Path to LittleTiles 1.12.2 block map")
    old_to_new.set_defaults(func=handle_old_to_new)

    old_to_obj = sub.add_parser("old-to-obj", help="Convert 1.12-style LittleTiles SNBT to OBJ/MTL")
    old_to_obj.add_argument("input")
    old_to_obj.add_argument("output")
    old_to_obj.add_argument("--block-map", help="Path to LittleTiles 1.12.2 block map")
    old_to_obj.set_defaults(func=handle_old_to_obj)

    snbt_to_obj = sub.add_parser("snbt-to-obj", help="Convert 1.20 LittleTiles SNBT to OBJ/MTL")
    snbt_to_obj.add_argument("input")
    snbt_to_obj.add_argument("output")
    snbt_to_obj.add_argument("--block-map", help="Path to LittleTiles 1.12.2 block map when input is old-format")
    snbt_to_obj.set_defaults(func=handle_snbt_to_obj)

    obj_to_snbt = sub.add_parser("obj-to-snbt", help="Convert OBJ to 1.20 LittleTiles SNBT")
    obj_to_snbt.add_argument("input")
    obj_to_snbt.add_argument("output")
    obj_to_snbt.add_argument("--grid", default=16, type=int)
    obj_to_snbt.add_argument("--max-size", default=16, type=int, help="Longest model side in LT grid units")
    obj_to_snbt.add_argument("--block", default="minecraft:white_concrete")
    obj_to_snbt.add_argument("--color", default=-1, type=int)
    obj_to_snbt.add_argument("--color-hex", help="Pure RGB color like #ff8844. Overrides --color.")
    obj_to_snbt.set_defaults(func=handle_obj_to_snbt)

    inspect = sub.add_parser("inspect", help="Print a short summary of a LittleTiles SNBT file")
    inspect.add_argument("input")
    inspect.add_argument("--block-map", help="Path to LittleTiles 1.12.2 block map when input is old-format")
    inspect.set_defaults(func=handle_inspect)

    serve = sub.add_parser("serve", help="Run the localhost Web UI")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", default=8765, type=int)
    serve.add_argument("--debug", action="store_true")
    serve.set_defaults(func=handle_serve)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
