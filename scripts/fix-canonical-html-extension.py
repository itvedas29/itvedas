#!/usr/bin/env python3
"""
One-time bulk fix: rewrite advertised URLs (canonical <link>, og:url meta,
hreflang alternates, and JSON-LD "url"/"@id" fields) on already-published
HTML pages to match what Cloudflare Pages actually serves.

Why: Cloudflare Pages serves "clean URLs" - a request to /articles/foo.html
is silently served/redirected to /articles/foo, with no way to disable this
from within the repo. Every page's canonical/og:url/schema still advertised
the .html version, and a chunk of them still advertised the bare apex
(itvedas.com) instead of the enforced www host - two different mismatches
between what pages *claim* their URL is and what the server actually
settles on, which confuses crawlers/indexers.

Scope: only rewrites itvedas.com / www.itvedas.com URLs found inside the
specific tags listed above. External URLs, on-page navigation links
(<a href="...">), and other content are left untouched. Directory index
pages (.../foo/index.html -> canonical ".../foo/") were already correct
before this script and are left as-is; only the trailing-slash-less
".../index" degenerate case is normalized to "/".

Safe to re-run - it's idempotent (already-clean URLs are left unchanged).
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(".")

HOST_RE = r'https?://(?:www\.)?itvedas\.com'


def normalize(url):
    """Strip .html and force the www host on an itvedas.com URL."""
    m = re.match(rf'^({HOST_RE})(.*)$', url)
    if not m:
        return url, False
    path = m.group(2)
    new_path = path
    if new_path == '/index.html':
        new_path = '/'
    elif new_path.endswith('/index.html'):
        new_path = new_path[:-len('index.html')]
    elif new_path.endswith('.html'):
        new_path = new_path[:-len('.html')]
    new_url = f'https://www.itvedas.com{new_path}'
    return new_url, new_url != url


def fix_attr(content, pattern, counters, key):
    """pattern must have exactly one capture group: the URL itself."""
    def repl(m):
        new_url, changed = normalize(m.group(1))
        if changed:
            counters[key] += 1
            return m.group(0).replace(m.group(1), new_url)
        return m.group(0)
    return re.sub(pattern, repl, content)


def fix_json_ld_blocks(content, counters):
    def fix_block(m):
        block = m.group(0)

        def repl_url(mm):
            new_url, changed = normalize(mm.group(2))
            if changed:
                counters['schema'] += 1
                return f'{mm.group(1)}{new_url}"'
            return mm.group(0)

        block = re.sub(rf'("url"\s*:\s*")({HOST_RE}[^"]*)"', repl_url, block)
        block = re.sub(rf'("@id"\s*:\s*")({HOST_RE}[^"]*)"', repl_url, block)
        # BreadcrumbList itemListElement entries use "item" (schema.org spec)
        # rather than "url"/"@id" for the page URL - same mismatch, same fix.
        block = re.sub(rf'("item"\s*:\s*")({HOST_RE}[^"]*)"', repl_url, block)
        return block

    return re.sub(
        r'<script type="application/ld\+json">.*?</script>',
        fix_block, content, flags=re.DOTALL,
    )


def fix_file(path, counters):
    text = path.read_text(encoding='utf-8')
    original = text

    text = fix_attr(
        text,
        r'<link rel="canonical" href="(' + HOST_RE + r'[^"]*)"',
        counters, 'canonical',
    )
    text = fix_attr(
        text,
        r'<meta property="og:url" content="(' + HOST_RE + r'[^"]*)"',
        counters, 'og_url',
    )
    text = fix_attr(
        text,
        r'<link rel="alternate" hreflang="[^"]*" href="(' + HOST_RE + r'[^"]*)"',
        counters, 'hreflang',
    )
    text = fix_json_ld_blocks(text, counters)

    if text != original:
        path.write_text(text, encoding='utf-8')
        return True
    return False


def main():
    counters = {'canonical': 0, 'og_url': 0, 'hreflang': 0, 'schema': 0}
    changed_files = 0
    total_files = 0

    for html_file in sorted(ROOT.rglob('*.html')):
        if '.git' in html_file.parts:
            continue
        total_files += 1
        if fix_file(html_file, counters):
            changed_files += 1
            print(f"fixed: {html_file.as_posix()}")

    print(f"\n{'='*60}")
    print(f"Files scanned: {total_files}")
    print(f"Files changed: {changed_files}")
    print(f"  canonical tags fixed: {counters['canonical']}")
    print(f"  og:url tags fixed:    {counters['og_url']}")
    print(f"  hreflang tags fixed:  {counters['hreflang']}")
    print(f"  JSON-LD url/@id fixed:{counters['schema']}")


if __name__ == '__main__':
    sys.exit(main())
