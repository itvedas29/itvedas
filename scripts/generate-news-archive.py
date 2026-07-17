#!/usr/bin/env python3
"""
Generate a paginated archive of every news/*.html post.

Why: news.html and security-news.html are live pages that only ever show
the most recent ~40/~17 stories (itvedas-brain/news-agent.py caps its
state file at 40 entries so the "latest news" pages stay a manageable
size). Every article file is kept permanently in news/, but once a
story ages out of that cap it has zero internal links pointing to it -
findable only via sitemap.xml/search, not by browsing the site. With
news-agent.py running hourly, that's the large majority of posts.

This script doesn't touch news-agent.py's "latest" behavior - it just
builds a separate, paginated archive of ALL news/*.html files (newest
first) so every post has at least one real on-site link pointing to it.
Safe to re-run any time; fully derived from the current news/*.html files.
"""

import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(".")
NEWS_DIR = ROOT / "news"
ARCHIVE_DIR = NEWS_DIR / "archive"
PER_PAGE = 60
SITE = "https://www.itvedas.com"

CARD_CSS = """
:root{--bg:#0A0A0F;--bg2:#13131C;--text:#F0F0F8;--muted:#8888A8;--accent:#FF6B35;--border:rgba(255,255,255,0.08);}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;-webkit-font-smoothing:antialiased;}
nav{position:fixed;top:0;left:0;right:0;z-index:100;display:flex;align-items:center;justify-content:space-between;padding:0 2rem;height:64px;background:rgba(10,10,15,0.92);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);}
.logo{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.3rem;color:var(--text);text-decoration:none;}
.logo span{color:var(--accent);}
.nav-links{display:flex;gap:1.5rem;}
.nav-links a{color:var(--muted);text-decoration:none;font-size:0.875rem;}
.nav-links a:hover,.nav-links a.active{color:var(--text);}
.main{max-width:1200px;margin:0 auto;padding:6rem 2rem 4rem;}
h1{font-family:'Space Grotesk',sans-serif;font-size:clamp(1.6rem,3vw,2.2rem);margin-bottom:0.5rem;}
.sub{color:var(--muted);margin-bottom:2rem;}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:1.25rem;}
.nc{background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:1.1rem 1.25rem;text-decoration:none;color:inherit;display:block;}
.nc:hover{border-color:rgba(255,255,255,0.2);}
.nc-time{font-size:0.72rem;color:var(--muted);}
.nc-title{font-family:'Space Grotesk',sans-serif;font-size:0.98rem;font-weight:600;line-height:1.4;margin:0.35rem 0 0.4rem;color:var(--text);}
.nc-sum{font-size:0.82rem;color:var(--muted);line-height:1.5;}
.pager{display:flex;gap:0.75rem;justify-content:center;margin-top:2.5rem;flex-wrap:wrap;}
.pager a,.pager span{padding:0.5rem 1rem;border:1px solid var(--border);border-radius:8px;color:var(--muted);text-decoration:none;font-size:0.85rem;}
.pager a:hover{color:var(--text);border-color:rgba(255,255,255,0.2);}
.pager .current{background:var(--accent);border-color:var(--accent);color:#fff;}
footer{border-top:1px solid var(--border);padding:2.5rem 2rem;text-align:center;color:var(--muted);font-size:0.875rem;margin-top:2rem;}
.flinks{display:flex;gap:1.5rem;justify-content:center;margin-top:0.75rem;flex-wrap:wrap;}
.flinks a{color:var(--muted);text-decoration:none;}
.flinks a:hover{color:var(--accent);}
"""


def extract_meta(path):
    content = path.read_text(encoding="utf-8", errors="ignore")

    ld_match = re.search(r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>', content, re.DOTALL)
    headline = description = date_published = None
    if ld_match:
        try:
            data = json.loads(ld_match.group(1))
            headline = data.get("headline")
            description = data.get("description")
            date_published = data.get("datePublished")
        except Exception:
            pass

    if not headline:
        m = re.search(r'<title>([^<]+)</title>', content)
        if m:
            headline = m.group(1).split(" | ")[0]
    if not description:
        m = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content)
        if m:
            description = m.group(1)
    if not date_published:
        # news/YYYY-MM-DD-slug.html
        m = re.match(r"(\d{4}-\d{2}-\d{2})-", path.stem)
        date_published = m.group(1) if m else "0000-00-00"

    return {
        "slug": path.stem,
        "url": f"/news/{path.stem}.html",
        "headline": headline or path.stem,
        "description": description or "",
        "date": date_published,
    }


def render_page(items, page_num, total_pages):
    cards = []
    for it in items:
        cards.append(f'''<a href="{it['url']}" class="nc">
  <div class="nc-time">{html.escape(it['date'])}</div>
  <div class="nc-title">{html.escape(it['headline'])}</div>
  <p class="nc-sum">{html.escape(it['description'][:160])}</p>
</a>''')

    pager_links = []
    if page_num > 1:
        prev_href = "index.html" if page_num == 2 else f"page-{page_num - 1}.html"
        pager_links.append(f'<a href="{prev_href}">&larr; Newer</a>')
    for p in range(1, total_pages + 1):
        if p == page_num:
            pager_links.append(f'<span class="current">{p}</span>')
        else:
            href = "index.html" if p == 1 else f"page-{p}.html"
            pager_links.append(f'<a href="{href}">{p}</a>')
    if page_num < total_pages:
        pager_links.append(f'<a href="page-{page_num + 1}.html">Older &rarr;</a>')

    canonical = f"{SITE}/news/archive/" + ("" if page_num == 1 else f"page-{page_num}.html")

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="description" content="Full archive of ITVedas original IT and cybersecurity news coverage, page {page_num} of {total_pages}.">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{canonical}">
<title>News Archive — Page {page_num} | ITVedas</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>{CARD_CSS}</style>
</head>
<body>
<nav>
  <a href="/" class="logo">IT<span>Vedas</span></a>
  <div class="nav-links"><a href="/">Home</a><a href="/news.html">News</a><a href="/security-news.html">Security News</a><a href="/news/archive/" class="active">Archive</a></div>
</nav>
<div class="main">
  <h1>News Archive</h1>
  <p class="sub">Every original story ITVedas has published — {len(items)} of them on this page, page {page_num} of {total_pages}.</p>
  <div class="grid">
    {''.join(cards)}
  </div>
  <div class="pager">{''.join(pager_links)}</div>
</div>
<footer>
  <div class="flinks"><a href="/">Home</a><a href="/news.html">Latest News</a><a href="/security-news.html">Security News</a><a href="/sitemap.xml">Sitemap</a></div>
  <p style="margin-top:1rem;">&copy; 2026 ITVedas &middot; Original reporting</p>
</footer>
</body>
</html>
'''


def main():
    if not NEWS_DIR.exists():
        print("x news/ directory not found")
        return 1

    files = sorted(NEWS_DIR.glob("*.html"))
    if not files:
        print("No news files found, nothing to archive.")
        return 0

    items = [extract_meta(f) for f in files]
    items.sort(key=lambda x: (x["date"], x["slug"]), reverse=True)

    total_pages = max(1, (len(items) + PER_PAGE - 1) // PER_PAGE)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    for p in range(1, total_pages + 1):
        chunk = items[(p - 1) * PER_PAGE : p * PER_PAGE]
        page_html = render_page(chunk, p, total_pages)
        out_name = "index.html" if p == 1 else f"page-{p}.html"
        (ARCHIVE_DIR / out_name).write_text(page_html, encoding="utf-8")

    print(f"Wrote {total_pages} archive page(s) covering {len(items)} news posts to {ARCHIVE_DIR}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
