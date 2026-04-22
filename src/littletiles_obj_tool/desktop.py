from __future__ import annotations

import argparse
import socket
import threading
import time
import webbrowser

from littletiles_obj_tool.web import create_app


def find_free_port(host: str, preferred_port: int) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, preferred_port))
        except OSError:
            sock.bind((host, 0))
        return int(sock.getsockname()[1])


def open_browser_when_ready(url: str, delay_seconds: float = 0.8) -> None:
    time.sleep(delay_seconds)
    webbrowser.open(url)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch the LittleTiles OBJ Tool desktop web app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Start the local web server without opening the default browser",
    )
    return parser


def main(host: str = "127.0.0.1", port: int = 8765, debug: bool = False, open_browser: bool = True) -> None:
    chosen_port = find_free_port(host, port)
    url = f"http://{host}:{chosen_port}/"
    app = create_app()

    if open_browser:
        browser_thread = threading.Thread(target=open_browser_when_ready, args=(url,), daemon=True)
        browser_thread.start()

    app.run(host=host, port=chosen_port, debug=debug)


if __name__ == "__main__":
    args = build_parser().parse_args()
    main(host=args.host, port=args.port, debug=args.debug, open_browser=not args.no_browser)
