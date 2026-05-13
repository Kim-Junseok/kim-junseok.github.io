#!/usr/bin/env python3
"""Build and preview the Sphinx documentation locally."""
# Build: python scripts/preview_docs.py --clean --strict
from __future__ import annotations

import argparse
import functools
import http.server
import importlib.util
import shutil
import socketserver
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs"
SOURCE_DIR = DOCS_DIR / "source"
BUILD_DIR = DOCS_DIR / "build"
HTML_DIR = BUILD_DIR / "html"


class QuietHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler with concise logging."""

    def log_message(self, format: str, *args: object) -> None:
        print(f"[preview] {self.address_string()} - {format % args}")


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build Sphinx docs and serve the generated HTML locally."
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host interface for the preview server. Default: 127.0.0.1",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for the preview server. Default: 8000",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove docs/build before building.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat Sphinx warnings as errors.",
    )
    parser.add_argument(
        "--no-serve",
        action="store_true",
        help="Build only; do not start the preview server.",
    )
    return parser.parse_args()


def sphinx_command(strict: bool) -> list[str]:
    sphinx_build = shutil.which("sphinx-build")
    if sphinx_build:
        command = [sphinx_build]
    else:
        if importlib.util.find_spec("sphinx") is None:
            install_command = f"{sys.executable} -m pip install -r docs/requirements.txt"
            raise RuntimeError(f"Sphinx is not installed. Run: {install_command}")
        command = [sys.executable, "-m", "sphinx"]

    command.extend(["-M", "html", str(SOURCE_DIR), str(BUILD_DIR)])
    if strict:
        command.append("-W")
    return command


def build_docs(clean: bool, strict: bool) -> None:
    if clean and BUILD_DIR.exists():
        print(f"[preview] Removing {BUILD_DIR.relative_to(REPO_ROOT)}", flush=True)
        shutil.rmtree(BUILD_DIR)

    command = sphinx_command(strict)
    print(f"[preview] Building docs with: {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=DOCS_DIR, check=True)

    if not HTML_DIR.exists():
        raise RuntimeError(f"Sphinx build finished, but {HTML_DIR} was not created.")


def serve_docs(host: str, port: int) -> None:
    handler = functools.partial(QuietHTTPRequestHandler, directory=str(HTML_DIR))
    with ReusableTCPServer((host, port), handler) as server:
        print(f"[preview] Serving {HTML_DIR.relative_to(REPO_ROOT)}", flush=True)
        print(f"[preview] Open http://{host}:{port}/", flush=True)
        print("[preview] Press Ctrl+C to stop.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n[preview] Stopped.")


def main() -> int:
    args = parse_args()
    try:
        build_docs(clean=args.clean, strict=args.strict)
        if not args.no_serve:
            serve_docs(host=args.host, port=args.port)
    except subprocess.CalledProcessError as exc:
        return exc.returncode
    except Exception as exc:
        print(f"[preview] Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
