#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
ENTRYPOINT = SRC_ROOT / "littletiles_obj_tool" / "desktop.py"
TEMPLATE_DIR = SRC_ROOT / "littletiles_obj_tool" / "templates"
STATIC_DIR = SRC_ROOT / "littletiles_obj_tool" / "static"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a standalone desktop executable with PyInstaller")
    parser.add_argument("--name", default="LittleTilesOBJTool")
    parser.add_argument("--windowed", action="store_true", help="Hide the console window on Windows")
    parser.add_argument("--clean", action="store_true", help="Remove previous build artifacts before packaging")
    return parser


def ensure_pyinstaller() -> None:
    if shutil.which("pyinstaller"):
        return
    raise SystemExit(
        "PyInstaller is not installed.\n"
        "Run: python3 -m pip install -e .[build]"
    )


def main() -> None:
    args = build_parser().parse_args()
    ensure_pyinstaller()

    separator = ";" if sys.platform.startswith("win") else ":"
    data_arg = f"{TEMPLATE_DIR}{separator}templates"
    static_arg = f"{STATIC_DIR}{separator}static"

    if args.clean:
        for folder in (PROJECT_ROOT / "build", PROJECT_ROOT / "dist"):
            if folder.exists():
                shutil.rmtree(folder)

    command = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--name",
        args.name,
        "--add-data",
        data_arg,
        "--add-data",
        static_arg,
    ]

    if args.windowed:
        command.append("--windowed")

    command.append(str(ENTRYPOINT))

    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


if __name__ == "__main__":
    main()
