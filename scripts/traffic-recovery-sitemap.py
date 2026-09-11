#!/usr/bin/env python3
"""Helpers for traffic-safe sitemap generation.

The main sitemap generator imports these rules so generated XML only advertises
URLs that are intended for search discovery.
"""
from pathlib import Path
import re

NOINDEX_RE = re.compile(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex', re.I)


def is_indexable_html(path: Path) -> bool:
    """Return True when an HTML page does not explicitly declare noindex."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return not NOINDEX_RE.search(text)


def iter_ai_tools(root: Path):
    """Yield AI-tool HTML pages, including the AI-tools hub."""
    directory = root / "ai-tools"
    if not directory.is_dir():
        return
    for path in sorted(directory.glob("*.html")):
        if is_indexable_html(path):
            yield path
