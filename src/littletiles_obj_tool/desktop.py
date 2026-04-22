from __future__ import annotations

import argparse
import os
import socket
import threading
import time
import webbrowser

from littletiles_obj_tool.web import create_app


class DesktopSessionMonitor:
    def __init__(self, startup_timeout_seconds: float = 90.0, heartbeat_timeout_seconds: float = 6.0) -> None:
        self.startup_timeout_seconds = startup_timeout_seconds
        self.heartbeat_timeout_seconds = heartbeat_timeout_seconds
        self.started_at = time.monotonic()
        self.last_heartbeat_at: float | None = None
        self.lock = threading.Lock()

    def note_heartbeat(self) -> None:
        with self.lock:
            self.last_heartbeat_at = time.monotonic()

    def should_exit(self) -> bool:
        now = time.monotonic()
        with self.lock:
            if self.last_heartbeat_at is None:
                return now - self.started_at > self.startup_timeout_seconds
            return now - self.last_heartbeat_at > self.heartbeat_timeout_seconds


def run_auto_exit_monitor(session_monitor: DesktopSessionMonitor, poll_interval_seconds: float = 1.0) -> None:
    while True:
        time.sleep(poll_interval_seconds)
        if session_monitor.should_exit():
            os._exit(0)


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
    session_monitor = DesktopSessionMonitor()
    app.config["AUTO_EXIT_ON_BROWSER_CLOSE"] = True
    app.extensions["desktop_session_monitor"] = session_monitor

    auto_exit_thread = threading.Thread(target=run_auto_exit_monitor, args=(session_monitor,), daemon=True)
    auto_exit_thread.start()

    if open_browser:
        browser_thread = threading.Thread(target=open_browser_when_ready, args=(url,), daemon=True)
        browser_thread.start()

    app.run(host=host, port=chosen_port, debug=debug)


if __name__ == "__main__":
    args = build_parser().parse_args()
    main(host=args.host, port=args.port, debug=args.debug, open_browser=not args.no_browser)
