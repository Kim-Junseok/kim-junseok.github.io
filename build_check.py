#!/usr/bin/env python3
"""Build and smoke-check this Jekyll/Chirpy site.

The script intentionally has no third-party Python dependencies. It tries the
real Jekyll build when Ruby/Bundler are available, then inspects the generated
site for the pieces that have recently been fragile: theme mode toggle, search
assets, and the Google Scholar icon stylesheet.

Build Command: python3 build_check.py --serve --port 4000
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parent
DEFAULT_DESTINATION = ROOT / "docs" / "build" / "jekyll-site"
FALLBACK_DESTINATION = ROOT / "docs" / "build" / "python-smoke"


@dataclass
class Check:
    name: str
    status: str
    detail: str = ""


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def print_check(check: Check) -> None:
    label = {"pass": "PASS", "warn": "WARN", "fail": "FAIL", "skip": "SKIP"}[check.status]
    line = f"[{label}] {check.name}"
    if check.detail:
        line += f" - {check.detail}"
    print(line)


def run(command: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def front_matter_and_body(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text

    end = text.find("\n---", 4)
    if end == -1:
        return {}, text

    raw = text[4:end].strip()
    body = text[text.find("\n", end + 4) + 1 :]
    data: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data, body


def parse_simple_yaml(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in read_text(path).splitlines():
        if not line or line.lstrip().startswith("#") or line.startswith(" "):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def strip_markdown(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_>#\-\[\]():]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def markdown_to_html(text: str) -> str:
    blocks: list[str] = []
    list_items: list[str] = []

    def flush_list() -> None:
        nonlocal list_items
        if list_items:
            blocks.append("<ul>\n" + "\n".join(list_items) + "\n</ul>")
            list_items = []

    def inline(value: str) -> str:
        escaped = html.escape(value)
        escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
        escaped = re.sub(
            r"\[([^\]]+)\]\(([^)]+)\)",
            lambda match: f'<a href="{html.escape(match.group(2), quote=True)}">{match.group(1)}</a>',
            escaped,
        )
        return escaped

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line:
            flush_list()
            continue
        if line.startswith("### "):
            flush_list()
            blocks.append(f"<h3>{inline(line[4:])}</h3>")
        elif line.startswith("## "):
            flush_list()
            blocks.append(f"<h2>{inline(line[3:])}</h2>")
        elif line.startswith("# "):
            flush_list()
            blocks.append(f"<h1>{inline(line[2:])}</h1>")
        elif line.startswith("- "):
            list_items.append(f"<li>{inline(line[2:].rstrip())}</li>")
        elif line.startswith("  ") and list_items:
            list_items[-1] = list_items[-1][:-5] + "<br>" + inline(line.strip()) + "</li>"
        else:
            flush_list()
            blocks.append(f"<p>{inline(line.rstrip())}</p>")
    flush_list()
    return "\n".join(blocks)


def collect_documents() -> list[dict[str, str]]:
    documents: list[dict[str, str]] = []

    index_path = ROOT / "index.md"
    if index_path.exists():
        meta, body = front_matter_and_body(read_text(index_path))
        title = meta.get("title") or "Home"
        documents.append(
            {
                "title": title,
                "url": "index.html",
                "source": rel(index_path),
                "body": body or "# Home\n",
            }
        )

    for path in sorted((ROOT / "_tabs").glob("*.md")):
        meta, body = front_matter_and_body(read_text(path))
        title = meta.get("title") or path.stem.replace("-", " ").title()
        documents.append(
            {
                "title": title,
                "url": f"{path.stem}.html",
                "source": rel(path),
                "body": body,
            }
        )

    for path in sorted((ROOT / "_posts").glob("*.md")):
        meta, body = front_matter_and_body(read_text(path))
        title = meta.get("title") or path.stem[11:].replace("-", " ").title()
        slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem)
        documents.append(
            {
                "title": title,
                "url": f"posts/{slug}/index.html",
                "source": rel(path),
                "body": body,
            }
        )

    return documents


def site_href(url: str) -> str:
    return "/" + url.lstrip("/")


def render_page(title: str, body_html: str, nav: Iterable[dict[str, str]], search_index: str) -> str:
    nav_html = "\n".join(
        f'<a href="{html.escape(site_href(item["url"]), quote=True)}">{html.escape(item["title"])}</a>' for item in nav
    )
    return f"""<!doctype html>
<html lang="en" data-mode="dark">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/academicons@1.9.4/css/academicons.min.css">
  <style>
    :root {{ color-scheme: light dark; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    body {{ margin: 0; background: #101418; color: #f1f5f9; line-height: 1.6; }}
    body[data-mode="light"] {{ background: #f8fafc; color: #111827; }}
    header {{ display: flex; gap: 1rem; align-items: center; justify-content: space-between; padding: 1rem clamp(1rem, 4vw, 3rem); border-bottom: 1px solid #334155; }}
    nav {{ display: flex; gap: .8rem; flex-wrap: wrap; }}
    a {{ color: #38bdf8; }}
    main {{ max-width: 860px; margin: 0 auto; padding: 2rem clamp(1rem, 4vw, 3rem); }}
    button, input {{ font: inherit; }}
    button {{ border: 1px solid #64748b; background: transparent; color: inherit; border-radius: 6px; padding: .35rem .6rem; cursor: pointer; }}
    input {{ width: min(100%, 28rem); padding: .55rem .7rem; border-radius: 6px; border: 1px solid #64748b; margin: 1rem 0; }}
    .results {{ display: grid; gap: .6rem; margin: 0; padding: 0; list-style: none; }}
    .results li {{ border: 1px solid #334155; border-radius: 8px; padding: .75rem; }}
    .source {{ color: #94a3b8; font-size: .9rem; }}
  </style>
</head>
<body data-mode="dark">
  <header>
    <nav>{nav_html}</nav>
    <button id="mode-toggle" type="button" aria-label="Theme mode">dark</button>
  </header>
  <main>
    <section aria-label="Search">
      <input id="search-input" type="search" placeholder="Search" autocomplete="off">
      <ul id="search-results" class="results"></ul>
    </section>
    {body_html}
  </main>
  <script id="search-data" type="application/json">{search_index}</script>
  <script>
    const body = document.body;
    const button = document.getElementById('mode-toggle');
    const modes = ['light', 'dark', 'system'];
    let mode = 'dark';
    function applyMode(next) {{
      mode = next;
      const effective = next === 'system'
        ? (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
        : next;
      body.dataset.mode = effective;
      button.textContent = next;
      document.documentElement.dataset.mode = next;
    }}
    button.addEventListener('click', () => applyMode(modes[(modes.indexOf(mode) + 1) % modes.length]));
    applyMode(mode);

    const index = JSON.parse(document.getElementById('search-data').textContent);
    const input = document.getElementById('search-input');
    const results = document.getElementById('search-results');
    input.addEventListener('input', () => {{
      const q = input.value.trim().toLowerCase();
      results.innerHTML = '';
      if (!q) return;
      index
        .filter(item => item.text.toLowerCase().includes(q) || item.title.toLowerCase().includes(q))
        .slice(0, 8)
        .forEach(item => {{
          const li = document.createElement('li');
          li.innerHTML = `<a href="${{item.url}}">${{item.title}}</a><div class="source">${{item.source}}</div>`;
          results.appendChild(li);
        }});
    }});
  </script>
</body>
</html>
"""


def clean_destination(destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)


def write_python_smoke_site(destination: Path) -> list[Check]:
    clean_destination(destination)
    documents = collect_documents()
    index_data = [
        {
            "title": doc["title"],
            "url": site_href(doc["url"]),
            "source": doc["source"],
            "text": strip_markdown(doc["body"]),
        }
        for doc in documents
    ]
    search_json = json.dumps(index_data, ensure_ascii=False)

    for doc in documents:
        output = destination / doc["url"]
        output.parent.mkdir(parents=True, exist_ok=True)
        body = markdown_to_html(doc["body"])
        output.write_text(render_page(doc["title"], body, documents, search_json), encoding="utf-8")

    (destination / "search-index.json").write_text(json.dumps(index_data, indent=2, ensure_ascii=False), encoding="utf-8")
    return [
        Check("Python smoke build", "pass", f"wrote {len(documents)} pages to {rel(destination)}"),
        Check("Python smoke search index", "pass", f"{len(index_data)} documents in search-index.json"),
    ]


def preflight_checks() -> list[Check]:
    checks: list[Check] = []
    config = parse_simple_yaml(ROOT / "_config.yml")
    contact = read_text(ROOT / "_data" / "contact.yml")
    head_custom = read_text(ROOT / "_includes" / "head-custom.html")

    checks.append(
        Check(
            "Jekyll theme",
            "pass" if config.get("theme") == "jekyll-theme-chirpy" else "fail",
            config.get("theme", "missing theme"),
        )
    )
    checks.append(
        Check(
            "baseurl",
            "pass" if config.get("baseurl", "") == "" else "warn",
            "empty baseurl is correct for kim-junseok.github.io user site",
        )
    )
    checks.append(
        Check(
            "theme_mode",
            "pass" if config.get("theme_mode", "") == "" else "warn",
            "empty value lets Chirpy expose light/dark/system mode controls",
        )
    )
    checks.append(
        Check(
            "mode-toggle contact item",
            "pass" if "type: mode-toggle" in contact else "fail",
            "_data/contact.yml",
        )
    )
    checks.append(
        Check(
            "Google Scholar icon class",
            "pass" if "ai ai-google-scholar" in contact else "fail",
            "_data/contact.yml",
        )
    )
    checks.append(
        Check(
            "Academicons stylesheet",
            "pass" if "academicons" in head_custom.lower() else "fail",
            "_includes/head-custom.html",
        )
    )

    legacy_sphinx_workflow = ROOT / ".github" / "workflows" / "deploy.yml"
    if legacy_sphinx_workflow.exists() and "sphinx-build" in read_text(legacy_sphinx_workflow):
        checks.append(
            Check(
                "legacy Sphinx workflow",
                "warn",
                "deploy.yml still runs sphinx-build; remove/disable it for Jekyll-only deploys",
            )
        )

    gitignore = read_text(ROOT / ".gitignore")
    if re.search(r"(?m)^\*\.md$", gitignore):
        checks.append(
            Check(
                ".gitignore Markdown rule",
                "warn",
                "*.md ignores future Jekyll pages/posts even though existing tracked files still work",
            )
        )

    return checks


def jekyll_build(destination: Path) -> tuple[list[Check], bool]:
    checks: list[Check] = []
    bundle = shutil.which("bundle")
    if not bundle:
        return [Check("Jekyll build", "fail", "Bundler is not installed or not on PATH")], False

    env = os.environ.copy()
    env["JEKYLL_ENV"] = "production"
    result = run(["bundle", "exec", "jekyll", "build", "--source", ".", "--destination", str(destination)], env=env)
    log_path = destination.parent / "jekyll-build.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(result.stdout, encoding="utf-8")

    if result.returncode != 0:
        tail = "\n".join(result.stdout.splitlines()[-12:])
        detail = f"exit {result.returncode}; log: {rel(log_path)}"
        checks.append(Check("Jekyll build", "fail", detail))
        if tail:
            print("\nLast build lines:\n" + textwrap.indent(tail, "  "))
        return checks, False

    checks.append(Check("Jekyll build", "pass", f"wrote site to {rel(destination)}; log: {rel(log_path)}"))
    return checks, True


def local_asset_exists(destination: Path, current_file: Path, value: str) -> bool:
    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc or value.startswith("#") or value.startswith("mailto:"):
        return True
    if "${" in value:
        return True

    path = unquote(parsed.path)
    if not path:
        return True

    if path.startswith("/"):
        candidate = destination / path.lstrip("/")
    else:
        candidate = current_file.parent / path

    if candidate.is_dir():
        candidate = candidate / "index.html"
    return candidate.exists()


def inspect_generated_site(destination: Path) -> list[Check]:
    checks: list[Check] = []
    html_files = sorted(destination.rglob("*.html"))
    all_files = sorted(path for path in destination.rglob("*") if path.is_file())
    combined_html = "\n".join(read_text(path) for path in html_files)

    checks.append(
        Check(
            "generated HTML",
            "pass" if html_files else "fail",
            f"{len(html_files)} html files under {rel(destination)}",
        )
    )
    checks.append(
        Check(
            "theme toggle markup",
            "pass" if re.search(r"mode-toggle|data-mode|theme-mode", combined_html, re.I) else "warn",
            "looked for mode-toggle/data-mode/theme-mode in generated HTML",
        )
    )
    checks.append(
        Check(
            "Academicons in generated HTML",
            "pass" if "academicons" in combined_html.lower() else "warn",
            "needed for ai ai-google-scholar",
        )
    )

    search_files = [
        path
        for path in all_files
        if "search" in path.name.lower() and path.suffix.lower() in {".json", ".js", ".html"}
    ]
    checks.append(
        Check(
            "search assets",
            "pass" if search_files else "fail",
            ", ".join(rel(path) for path in search_files[:8]) or "no search assets found",
        )
    )

    missing_assets: list[str] = []
    attr_pattern = re.compile(r"""(?:href|src)=["']([^"']+)["']""", re.I)
    for html_file in html_files:
        for value in attr_pattern.findall(read_text(html_file)):
            if not local_asset_exists(destination, html_file, value):
                missing_assets.append(f"{rel(html_file)} -> {value}")
                if len(missing_assets) >= 8:
                    break
        if len(missing_assets) >= 8:
            break

    checks.append(
        Check(
            "local asset links",
            "pass" if not missing_assets else "fail",
            "all local href/src targets exist" if not missing_assets else "; ".join(missing_assets),
        )
    )

    return checks


def serve(destination: Path, port: int) -> None:
    os.chdir(destination)
    server = ThreadingHTTPServer(("127.0.0.1", port), SimpleHTTPRequestHandler)
    print(f"\nServing {rel(destination)} at http://127.0.0.1:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


def clean_legacy_python_artifacts() -> list[Check]:
    checks: list[Check] = []
    for path in [ROOT / ".venv", ROOT / "docs" / "build" / "html"]:
        if path.exists():
            shutil.rmtree(path)
            checks.append(Check("removed legacy Python artifact", "pass", rel(path)))
        else:
            checks.append(Check("legacy Python artifact", "skip", f"{rel(path)} not present"))
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and smoke-check the Jekyll site.")
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION, help="Jekyll build output directory")
    parser.add_argument("--fallback-destination", type=Path, default=FALLBACK_DESTINATION, help="Python smoke output directory")
    parser.add_argument("--no-fallback", action="store_true", help="do not write the Python smoke site when Jekyll cannot run")
    parser.add_argument("--serve", action="store_true", help="serve the successful build output on localhost")
    parser.add_argument("--port", type=int, default=4000, help="port for --serve")
    parser.add_argument(
        "--clean-legacy-python",
        action="store_true",
        help="remove .venv and old docs/build/html Sphinx output before building",
    )
    args = parser.parse_args()

    checks: list[Check] = []
    if args.clean_legacy_python:
        checks.extend(clean_legacy_python_artifacts())

    checks.extend(preflight_checks())

    destination = args.destination.resolve()
    clean_destination(destination)
    build_checks, built = jekyll_build(destination)
    checks.extend(build_checks)

    inspected_destination: Path | None = destination if built else None
    if built:
        checks.extend(inspect_generated_site(destination))
    elif not args.no_fallback:
        fallback_destination = args.fallback_destination.resolve()
        checks.extend(write_python_smoke_site(fallback_destination))
        checks.extend(inspect_generated_site(fallback_destination))
        inspected_destination = fallback_destination
        checks.append(
            Check(
                "fallback note",
                "warn",
                "Python smoke build checks content/search wiring only; install Ruby/Bundler for real Chirpy output",
            )
        )

    print("\nBuild check results")
    print("===================")
    for check in checks:
        print_check(check)

    failed = [check for check in checks if check.status == "fail"]
    if args.serve and inspected_destination:
        serve(inspected_destination, args.port)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
