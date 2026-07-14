#!/usr/bin/env python3
"""
Enhance Article JSON-LD schemas to include description and image.
Extracts from meta tags and ensures all required fields are present.
"""

import json
import re
from pathlib import Path

def extract_meta_content(html, meta_name):
    """Extract content from meta tag."""
    pattern = f'<meta name="{meta_name}" content="([^"]*)"'
    match = re.search(pattern, html)
    return match.group(1) if match else None

def extract_og_property(html, property_name):
    """Extract content from og: property."""
    pattern = f'<meta property="og:{property_name}" content="([^"]*)"'
    match = re.search(pattern, html)
    return match.group(1) if match else None

def update_article_schema(file_path):
    """Update Article schema in a single article file."""
    html = file_path.read_text()

    # Get metadata from meta tags
    description = extract_meta_content(html, 'description')
    og_image = extract_og_property(html, 'image')

    if not description and not og_image:
        return False  # No metadata to add

    # Find and update Article schema
    def replace_article_schema(match):
        try:
            schema_text = match.group(1)
            schema = json.loads(schema_text)

            if schema.get('@type') != 'Article':
                return match.group(0)

            # Add missing fields
            changed = False
            if description and 'description' not in schema:
                schema['description'] = description
                changed = True

            if og_image and 'image' not in schema:
                schema['image'] = og_image
                changed = True

            if not changed:
                return match.group(0)

            # Format back to JSON
            new_json = json.dumps(schema, separators=(',', ':'))
            return f'<script type="application/ld+json">{new_json}</script>'
        except:
            return match.group(0)

    # Replace in HTML
    pattern = r'<script type="application/ld\+json">({[^<]*?})</script>'
    new_html = re.sub(pattern, replace_article_schema, html)

    if new_html != html:
        file_path.write_text(new_html)
        return True

    return False

def main():
    articles_dir = Path('/home/user/itvedas/articles')
    total = 0
    updated = 0

    for article_file in sorted(articles_dir.rglob('*.html')):
        total += 1
        if update_article_schema(article_file):
            updated += 1
            rel_path = article_file.relative_to(Path('/home/user/itvedas'))
            print(f"✓ Updated: {rel_path}")

    print(f"\nSchema enhancement complete:")
    print(f"  Total articles: {total}")
    print(f"  Updated: {updated}")
    print(f"  Added description and/or image fields to Article schemas")

if __name__ == '__main__':
    main()
