#!/usr/bin/env python3
"""Local setup helper for the Jekyll/Chirpy site.

This script keeps the setup commands in one place. It does not run sudo
commands for you; install system packages manually when they are missing.
Project gems are installed into ./vendor/bundle so the system Ruby directory is
not modified.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent

SYSTEM_COMMANDS = [
    "sudo apt update",
    "sudo apt install ruby-full ruby-dev build-essential zlib1g-dev ruby-bundler",
]

PROJECT_COMMANDS = [
    "bundle config set --local path vendor/bundle",
    "bundle install",
]

SERVE_COMMAND = "bundle exec jekyll serve --host 127.0.0.1 --port 4000"


def run(command: list[str]) -> int:
    print(f"\n$ {' '.join(command)}")
    return subprocess.run(command, cwd=ROOT, check=False).returncode


def command_version(command: str, version_args: list[str]) -> str:
    executable = shutil.which(command)
    if not executable:
        return "missing"

    result = subprocess.run(
        [command, *version_args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    first_line = result.stdout.strip().splitlines()[0] if result.stdout.strip() else "installed"
    return first_line


def print_commands() -> None:
    print("System packages, Ubuntu/WSL:")
    for command in SYSTEM_COMMANDS:
        print(f"  {command}")

    print("\nProject gems:")
    for command in PROJECT_COMMANDS:
        print(f"  {command}")

    print("\nServe locally:")
    print(f"  {SERVE_COMMAND}")


def check_environment() -> bool:
    checks = {
        "ruby": command_version("ruby", ["--version"]),
        "bundle": command_version("bundle", ["--version"]),
    }

    print("\nEnvironment:")
    ok = True
    for name, version in checks.items():
        print(f"  {name}: {version}")
        if version == "missing":
            ok = False

    if not ok:
        print("\nInstall the missing system packages first:")
        for command in SYSTEM_COMMANDS:
            print(f"  {command}")

    return ok


def install_project_gems() -> int:
    if not check_environment():
        return 1

    for command in PROJECT_COMMANDS:
        code = run(command.split())
        if code != 0:
            return code
    return 0


def serve() -> int:
    if not check_environment():
        return 1
    return run(SERVE_COMMAND.split())


def main() -> int:
    parser = argparse.ArgumentParser(description="Show or run local Jekyll setup commands.")
    parser.add_argument("--install", action="store_true", help="install project gems into vendor/bundle")
    parser.add_argument("--serve", action="store_true", help="serve the Jekyll site locally")
    parser.add_argument("--check", action="store_true", help="check Ruby and Bundler availability")
    args = parser.parse_args()

    print_commands()

    if args.install:
        return install_project_gems()
    if args.serve:
        return serve()
    if args.check:
        return 0 if check_environment() else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
