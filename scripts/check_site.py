#!/usr/bin/env python3
"""Validate generated Jekyll output for common homepage quality regressions."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urlsplit


SKIP_SCHEMES = {
    "data",
    "mailto",
    "tel",
    "javascript",
    "sms",
    "irc",
    "skype",
}

URL_ATTRS = {
    "a": ("href",),
    "link": ("href",),
    "script": ("src",),
    "img": ("src",),
    "source": ("src",),
    "iframe": ("src",),
    "video": ("src", "poster"),
    "audio": ("src",),
    "form": ("action",),
}

REQUIRED_FILES = (
    "index.html",
    "about/index.html",
    "publications/index.html",
    "topics/index.html",
    "tags/index.html",
    "assets/img/profile/Junseok_Kim.jpg",
    "assets/img/home/home-intro.png",
)

REQUIRED_SNIPPETS = {
    "index.html": (
        'data-mode="dark"',
        'id="homepage-default-theme-mode"',
        'id="mode-toggle"',
        "home-profile-hero",
        "Junseok Kim",
    ),
    "about/index.html": (
        "about-intro-figure",
        "Advisor",
        "https://sites.google.com/netlab.snu.ac.kr/netlabhome/people/faculty?authuser=0",
        "https://sites.google.com/view/sunghyun-chois-home",
    ),
}

DEFAULT_THEME_MODE = "dark"
DEFAULT_THEME_MARKER = "homepage-default-theme-mode"


@dataclass(frozen=True)
class UrlRef:
    page: Path
    tag: str
    attr: str
    url: str


@dataclass(frozen=True)
class ExternalAnchor:
    page: Path
    href: str
    target: str
    rel: str


class PageParser(HTMLParser):
    def __init__(self, page: Path) -> None:
        super().__init__(convert_charrefs=True)
        self.page = page
        self.ids: set[str] = set()
        self.urls: list[UrlRef] = []
        self.external_anchors: list[ExternalAnchor] = []
        self.issues: list[str] = []

    def handle_starttag(self, tag: str, attrs_list: list[tuple[str, str | None]]) -> None:
        attrs = {key.lower(): value or "" for key, value in attrs_list}

        element_id = attrs.get("id")
        if element_id:
            self.ids.add(element_id)

        if tag == "a" and attrs.get("name"):
            self.ids.add(attrs["name"])

        for attr in URL_ATTRS.get(tag, ()):
            value = attrs.get(attr, "").strip()
            if value:
                self.urls.append(UrlRef(self.page, tag, attr, value))

        for attr in ("srcset", "imagesrcset"):
            value = attrs.get(attr, "").strip()
            if value:
                for candidate in parse_srcset(value):
                    self.urls.append(UrlRef(self.page, tag, attr, candidate))

        if tag == "img":
            alt = attrs.get("alt")
            if alt is None or not alt.strip():
                self.issues.append(f"{self.page}: img is missing meaningful alt text")

        if tag == "a":
            href = attrs.get("href", "").strip()
            if is_external_url(href):
                self.external_anchors.append(
                    ExternalAnchor(
                        page=self.page,
                        href=href,
                        target=attrs.get("target", "").strip(),
                        rel=attrs.get("rel", "").strip(),
                    )
                )


def parse_srcset(value: str) -> Iterable[str]:
    for item in value.split(","):
        candidate = item.strip()
        if not candidate:
            continue
        yield candidate.split()[0]


def is_external_url(url: str) -> bool:
    if url.startswith("//"):
        return True
    parts = urlsplit(url)
    return parts.scheme in {"http", "https"}


def should_skip_url(url: str) -> bool:
    if not url or url.startswith("//"):
        return True
    parts = urlsplit(url)
    return bool(parts.scheme and parts.scheme in SKIP_SCHEMES) or parts.scheme in {"http", "https"}


def display_path(path: Path, site_root: Path) -> str:
    try:
        return str(path.relative_to(site_root))
    except ValueError:
        return str(path)


def parse_html_pages(site_root: Path) -> tuple[dict[Path, PageParser], list[str]]:
    pages: dict[Path, PageParser] = {}
    issues: list[str] = []

    for page in sorted(site_root.rglob("*.html")):
        parser = PageParser(page)
        try:
            parser.feed(page.read_text(encoding="utf-8"))
        except UnicodeDecodeError as error:
            issues.append(f"{display_path(page, site_root)}: cannot decode as UTF-8 ({error})")
            continue
        except OSError as error:
            issues.append(f"{display_path(page, site_root)}: cannot read file ({error})")
            continue

        pages[page] = parser
        issues.extend(
            issue.replace(str(page), display_path(page, site_root)) for issue in parser.issues
        )

    return pages, issues


def resolve_site_path(url: str, page: Path, site_root: Path) -> tuple[Path, str] | None:
    if should_skip_url(url):
        return None

    parts = urlsplit(url)
    if parts.scheme:
        return None

    raw_path = unquote(parts.path)
    fragment = unquote(parts.fragment)

    if not raw_path:
        return page, fragment

    if raw_path.startswith("/"):
        base = site_root / raw_path.lstrip("/")
    else:
        base = (page.parent / raw_path).resolve()

    if raw_path.endswith("/"):
        return base / "index.html", fragment

    if base.exists() and base.is_file():
        return base, fragment

    if (base / "index.html").exists():
        return base / "index.html", fragment

    return base, fragment


def check_required_files(site_root: Path) -> list[str]:
    issues = []
    for rel_path in REQUIRED_FILES:
        if not (site_root / rel_path).exists():
            issues.append(f"{rel_path}: required generated file is missing")
    return issues


def check_required_snippets(site_root: Path) -> list[str]:
    issues = []
    for rel_path, snippets in REQUIRED_SNIPPETS.items():
        page = site_root / rel_path
        if not page.exists():
            continue
        content = page.read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in content:
                issues.append(f"{rel_path}: expected snippet not found: {snippet}")
    return issues


def check_default_theme_mode(site_root: Path, pages: dict[Path, PageParser]) -> list[str]:
    issues = []
    expected_mode = f'data-mode="{DEFAULT_THEME_MODE}"'

    for page in pages:
        content = page.read_text(encoding="utf-8")
        rel_path = display_path(page, site_root)

        if expected_mode not in content:
            issues.append(f"{rel_path}: expected default theme marker not found: {expected_mode}")

        if DEFAULT_THEME_MARKER not in content:
            issues.append(f"{rel_path}: default theme bootstrap script is missing")

    return issues


def check_local_urls(site_root: Path, pages: dict[Path, PageParser]) -> tuple[list[str], int]:
    issues = []
    checked_count = 0

    for parser in pages.values():
        for ref in parser.urls:
            resolved = resolve_site_path(ref.url, ref.page, site_root)
            if resolved is None:
                continue

            target, fragment = resolved
            checked_count += 1

            if not target.exists():
                issues.append(
                    f"{display_path(ref.page, site_root)}: {ref.tag}[{ref.attr}] points to "
                    f"missing local target: {ref.url}"
                )
                continue

            if fragment and not fragment.startswith(":~:") and target.suffix == ".html":
                target_parser = pages.get(target)
                if target_parser and fragment not in target_parser.ids:
                    issues.append(
                        f"{display_path(ref.page, site_root)}: {ref.tag}[{ref.attr}] points to "
                        f"missing anchor #{fragment}: {ref.url}"
                    )

    return issues, checked_count


def check_external_anchors(site_root: Path, pages: dict[Path, PageParser]) -> list[str]:
    issues = []

    for parser in pages.values():
        for anchor in parser.external_anchors:
            rel_values = {item.lower() for item in anchor.rel.split()}

            if anchor.target != "_blank":
                issues.append(
                    f"{display_path(anchor.page, site_root)}: external link must use "
                    f'target="_blank": {anchor.href}'
                )

            if "noopener" not in rel_values:
                issues.append(
                    f"{display_path(anchor.page, site_root)}: external link must include "
                    f'rel="noopener": {anchor.href}'
                )

            if "noreferrer" not in rel_values:
                issues.append(
                    f"{display_path(anchor.page, site_root)}: external link must include "
                    f'rel="noreferrer": {anchor.href}'
                )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--site",
        default="_site",
        type=Path,
        help="Path to generated Jekyll output. Defaults to _site.",
    )
    args = parser.parse_args()

    site_root = args.site.resolve()
    if not site_root.exists():
        print(f"error: generated site directory does not exist: {site_root}", file=sys.stderr)
        print("hint: run `bundle exec jekyll build` first", file=sys.stderr)
        return 2

    pages, issues = parse_html_pages(site_root)
    issues.extend(check_required_files(site_root))
    issues.extend(check_required_snippets(site_root))
    issues.extend(check_default_theme_mode(site_root, pages))
    url_issues, checked_urls = check_local_urls(site_root, pages)
    issues.extend(url_issues)
    issues.extend(check_external_anchors(site_root, pages))

    if issues:
        print("Site quality check failed:", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    print(
        f"Site quality check passed: {len(pages)} HTML pages, "
        f"{checked_urls} local URL references checked."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
