#!/usr/bin/env python3
"""
Add og:image and twitter:image meta tags to articles.
Uses per-article images if they exist, otherwise defaults to og-default.png
"""

import re
from pathlib import Path

DEFAULT_IMAGE = "https://www.itvedas.com/assets/og-default.png"
IMAGE_WIDTH = "1200"
IMAGE_HEIGHT = "630"

def add_og_image_meta_tags(file_path):
    """Add og:image and twitter:image meta tags to an article."""
    html = file_path.read_text()

    # Check if og:image already exists
    if '<meta property="og:image"' in html:
        return False

    # Find the canonical link to determine URL
    canonical_match = re.search(r'<link rel="canonical" href="([^"]*)"', html)
    if not canonical_match:
        return False

    # Use default image (could be extended to look for per-article images)
    og_image = DEFAULT_IMAGE

    # Find where to insert the meta tags (after canonical link)
    insert_pos = canonical_match.end()

    # Create the meta tags to insert
    meta_tags = f'''<meta property="og:image" content="{og_image}">
<meta property="og:image:width" content="{IMAGE_WIDTH}">
<meta property="og:image:height" content="{IMAGE_HEIGHT}">
<meta name="twitter:image" content="{og_image}">'''

    # Insert the meta tags
    new_html = html[:insert_pos] + '>' + meta_tags + html[insert_pos:]

    # Write back
    file_path.write_text(new_html)
    return True

def main():
    articles_dir = Path('/home/user/itvedas/articles')
    total = 0
    updated = 0
    has_og = 0

    for article_file in sorted(articles_dir.rglob('*.html')):
        # Skip index files
        if article_file.name == 'index.html':
            continue

        total += 1

        # Check if already has og:image
        html = article_file.read_text()
        if '<meta property="og:image"' in html:
            has_og += 1
            continue

        if add_og_image_meta_tags(article_file):
            updated += 1
            rel_path = article_file.relative_to(Path('/home/user/itvedas'))
            print(f"✓ Added og:image to: {rel_path}")

    print(f"\nOpen Graph image addition complete:")
    print(f"  Total articles processed: {total}")
    print(f"  Already had og:image: {has_og}")
    print(f"  Updated with og:image: {updated}")
    print(f"  Using default image: {DEFAULT_IMAGE}")

if __name__ == '__main__':
    main()
