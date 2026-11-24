#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Techulture and serve it locally.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=8021, help="Port to bind")
    parser.add_argument("--limit", type=int, default=5, help="Items to print per source during build")
    return parser.parse_args()


def run_build(limit: int) -> None:
    subprocess.run(
        [sys.executable, str(BASE_DIR / "techulture.py"), "--limit", str(limit)],
        check=True,
        cwd=BASE_DIR,
    )


def run_server(host: str, port: int) -> int:
    return subprocess.run(
        [sys.executable, str(BASE_DIR / "app.py"), "--host", host, "--port", str(port)],
        check=False,
        cwd=BASE_DIR,
    ).returncode


def main() -> int:
    args = parse_args()
    run_build(args.limit)
    return run_server(args.host, args.port)


if __name__ == "__main__":
    raise SystemExit(main())
