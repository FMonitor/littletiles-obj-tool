#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from littletiles_obj_tool.bootstrap import setup_local_deps


setup_local_deps()

from littletiles_obj_tool.web import main


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the LittleTiles OBJ Tool localhost Web UI")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8766, type=int)
    parser.add_argument("--debug", action="store_true")
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    main(host=args.host, port=args.port, debug=args.debug)
