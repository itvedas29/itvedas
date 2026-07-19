#!/usr/bin/env python3
"""
One-time repair for two broken-link bugs found during the 2026-07-20 site audit:

1. scripts/optimize-internal-linking.py built "Related Articles" hrefs as
   f"/articles/{article_file.parent.name}/{article_file.name}". For articles
   stored directly under articles/ (not in a category subfolder), parent.name
   is "articles" itself, producing a doubled path like
   /articles/articles/2026-07-07-cloud.html, which 404s.

2. scripts/optimize-navigation-structure.py built a "Category:" link (and a
   matching breadcrumb JSON-LD "item" URL) as f"/{parts[0]}/{category}/".
   For the same top-level articles, "category" ended up being the article's
   own filename (e.g. "2026-07-07-cloud.html"), producing a self-link with a
   trailing slash like /articles/2026-07-07-cloud.html/, which also 404s
   (the real URL has no trailing slash).

This script scans every article HTML file and fixes both patterns in place.
It is idempotent and safe to re-run.
"""
import pathlib

ROOT = pathlib.Path(".")
changed = []

for f in (ROOT / "articles").rglob("*.html"):
    text = f.read_text(encoding="utf-8")
    original = text

    # Bug 1: doubled /articles/articles/ path
    text = text.replace('href="/articles/articles/', 'href="/articles/')

    # Bug 2: self-referencing link/breadcrumb with erroneous trailing slash
    if f.name != "index.html":
        text = text.replace(f'/articles/{f.name}/"', f'/articles/{f.name}"')

    if text != original:
        f.write_text(text, encoding="utf-8")
        changed.append(str(f))

print(f"Fixed {len(changed)} file(s):")
for c in changed:
    print(" -", c)
