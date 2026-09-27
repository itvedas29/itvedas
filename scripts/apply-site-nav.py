#!/usr/bin/env python3
"""Apply the shared site navigation (partials/site-nav.html) to every HTML page.

    python3 scripts/apply-site-nav.py            # update pages in place
    python3 scripts/apply-site-nav.py --check    # CI: fail if any page is out of date
    python3 scripts/apply-site-nav.py --dry-run  # list what would change

What it does on each page:
  * replaces the page's old top navigation bar (the first <nav> that links to "/")
    with the shared one, or inserts the shared one right after <body> when the page
    has no site navigation;
  * on later runs, replaces whatever sits between the site-nav:start/end markers,
    so editing the partial and re-running updates the whole site;
  * removes the old nav assets (nav-mega.css, nav-search.js, nav-mobile.js,
    nav-mega.js) and adds /css/site-nav.css and /js/site-nav.js.

Pages whose old bar was fixed to the top keep a fixed bar (their content is
already padded for it); pages that had a bar in the normal flow, or none,
get a sticky bar so nothing is hidden underneath it.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARTIAL = ROOT / "partials" / "site-nav.html"

SKIP_DIRS = {".git", "node_modules", "assets", "drafts", "docs", "itvedas-brain", "knowledge-imports",
             "deployment", "partials", "tests", "videos", ".github", "functions", "config", "scripts"}
SKIP_FILES = {"preview.html", "software/reviews-admin/index.html",
              "cve-data/cve-detail-template.html", "cve-data/cve-listing-template.html"}

START, END = "<!-- site-nav:start", "<!-- site-nav:end -->"
OLD_ASSETS = [
    re.compile(r'[ \t]*<link[^>]+href="/css/nav-mega\.css"[^>]*>\s*\n?', re.I),
    re.compile(r'[ \t]*<script[^>]+src="/js/nav-(?:search|mobile|mega)\.js"[^>]*>\s*</script>\s*\n?', re.I),
]
CSS_TAG = '<link rel="stylesheet" href="/css/site-nav.css">'
JS_TAG = '<script src="/js/site-nav.js" defer></script>'
NAV_RULE = re.compile(r'(?:^|[}\s,;])nav\s*\{([^}]*)\}', re.S)

_css_cache: dict[str, str] = {}


def pages():
    for p in sorted(ROOT.rglob("*.html")):
        rel = p.relative_to(ROOT).as_posix()
        if set(p.relative_to(ROOT).parts[:-1]) & SKIP_DIRS or rel in SKIP_FILES:
            continue
        yield p, rel


def masked(html: str) -> str:
    """Blank out scripts, styles and comments so we never match a <nav> inside them."""
    def blank(m):
        return " " * (m.end() - m.start())
    return re.sub(r"<script\b.*?</script>|<style\b.*?</style>|<!--.*?-->|<template\b.*?</template>", blank, html, flags=re.S | re.I)


def linked_css(html: str) -> str:
    out = []
    for href in re.findall(r'<link[^>]+rel="stylesheet"[^>]+href="(/[^"]+\.css)"', html) + \
                re.findall(r'<link[^>]+href="(/[^"]+\.css)"[^>]+rel="stylesheet"', html):
        if href not in _css_cache:
            f = ROOT / href.lstrip("/")
            _css_cache[href] = f.read_text(encoding="utf-8", errors="ignore") if f.is_file() else ""
        out.append(_css_cache[href])
    return "\n".join(out)


def old_bar_was_fixed(html: str) -> bool:
    css = "\n".join(re.findall(r"<style\b[^>]*>(.*?)</style>", html, re.S | re.I)) + "\n" + linked_css(html)
    rules = NAV_RULE.findall(css)
    return any(re.search(r"position\s*:\s*fixed", r) for r in rules)


def find_site_nav(html: str):
    """Return (start, end) of the first top-level <nav> that looks like the site bar."""
    m = masked(html)
    body = m.find("<body")
    if body == -1:
        return None
    for nav in re.finditer(r"<nav\b[^>]*>", m[body:], re.I):
        start = body + nav.start()
        depth, pos = 0, start
        for tag in re.finditer(r"<(/?)nav\b[^>]*>", m[start:], re.I):
            depth += -1 if tag.group(1) else 1
            if depth == 0:
                end = start + tag.end()
                break
        else:
            return None
        chunk = html[start:end]
        opening = chunk[:chunk.find(">") + 1].lower()
        if "breadcrumb" in opening:
            continue  # a breadcrumb trail, not the site bar: keep looking
        first_h1 = m.find("<h1", body)
        before_title = first_h1 == -1 or start < first_h1
        is_brand = re.search(r'class="[^"]*\blogo\b|IT\s*<span[^>]*>\s*Vedas|>\s*ITVedas\s*<', chunk)
        if before_title and is_brand:
            return start, end
        return None  # first nav is something else (tabs, table of contents): treat page as having no bar
    return None


def build(html: str, partial: str) -> str:
    if START in html and END in html:
        s = html.index(START)
        e = html.index(END) + len(END)
        mode = "sticky" if 'data-mode="sticky"' in html[s:e] else "fixed"
        html = html[:s] + partial.replace('data-mode="fixed"', f'data-mode="{mode}"') + html[e:]
    else:
        found = find_site_nav(html)
        if found:
            mode = "fixed" if old_bar_was_fixed(html) else "sticky"
            s, e = found
            html = html[:s] + partial.replace('data-mode="fixed"', f'data-mode="{mode}"') + html[e:]
        else:
            m = re.search(r"<body\b[^>]*>", html, re.I)
            if not m:
                return html
            html = html[:m.end()] + "\n" + partial.replace('data-mode="fixed"', 'data-mode="sticky"') + html[m.end():]

    for rx in OLD_ASSETS:
        html = rx.sub("", html)
    if CSS_TAG not in html:
        html = re.sub(r"</head>", CSS_TAG + "\n</head>", html, count=1, flags=re.I)
    if JS_TAG not in html:
        html = re.sub(r"</body>", JS_TAG + "\n</body>", html, count=1, flags=re.I)
    return html


def main(argv):
    check = "--check" in argv
    dry = "--dry-run" in argv
    partial = PARTIAL.read_text(encoding="utf-8").strip()
    changed = []
    for path, rel in pages():
        html = path.read_text(encoding="utf-8", errors="ignore")
        if "<body" not in html.lower():
            continue
        new = build(html, partial)
        if new != html:
            changed.append(rel)
            if not (check or dry):
                path.write_text(new, encoding="utf-8")
    if check:
        if changed:
            print(f"{len(changed)} page(s) do not have the current site navigation. Run: python3 scripts/apply-site-nav.py")
            for rel in changed[:30]:
                print("  -", rel)
            return 1
        print("OK: every page uses the current site navigation")
        return 0
    verb = "would update" if dry else "updated"
    print(f"Site navigation: {verb} {len(changed)} page(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
