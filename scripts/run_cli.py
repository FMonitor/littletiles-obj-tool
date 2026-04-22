#!/usr/bin/env python3
from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from littletiles_obj_tool.bootstrap import setup_local_deps


setup_local_deps()

from littletiles_obj_tool.cli import main


if __name__ == "__main__":
    main()
