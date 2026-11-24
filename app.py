#!/usr/bin/env python3
from __future__ import annotations

import argparse
import http.server
import socketserver
from functools import partial
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


class ThreadingReusableTCPServer(socketserver.ThreadingMixIn, ReusableTCPServer):
    daemon_threads = True


class QuietRequestHandler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".css": "text/css; charset=utf-8",
        ".html": "text/html; charset=utf-8",
        ".js": "text/javascript; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".txt": "text/plain; charset=utf-8",
    }

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve Techulture locally.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=8021, help="Port to bind")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    handler = partial(QuietRequestHandler, directory=str(BASE_DIR))

    with ThreadingReusableTCPServer((args.host, args.port), handler) as httpd:
        print(f"Techulture server running on http://{args.host}:{args.port}/")
        httpd.serve_forever()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
