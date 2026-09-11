#!/usr/bin/env python3
"""
Add breadcrumb schema markup to article pages for better SEO.
Run this script to enhance structured data in articles.
"""

import json
import pathlib
import re

ROOT = pathlib.Path(".")
SITE_URL = "https://www.itvedas.com"

def get_page_title(content):
    """Extract a human-readable page title, stripping the site suffix."""
    match = re.search(r'<title>([^<]+)</title>', content, re.IGNORECASE)
    if match:
        title = match.group(1)
        title = re.sub(r'\s*[|—-]\s*IT ?Vedas\s*$', '', title, flags=re.IGNORECASE).strip()
        if title:
            return title
    return None

def get_breadcrumbs(file_path, content=""):
    """Generate breadcrumb structure for a given file path."""
    # Determine file type and location
    rel_path = file_path.relative_to(ROOT)
    parts = rel_path.parts
    page_title = get_page_title(content)

    breadcrumbs = []

    # Home is always first
    breadcrumbs.append({
        "position": 1,
        "@type": "ListItem",
        "name": "Home",
        "item": SITE_URL
    })

    if parts[0] == "articles":
        # Articles structure: articles/category/[file].html
        breadcrumbs.append({
            "position": 2,
            "@type": "ListItem",
            "name": parts[1].replace("-", " ").title(),
            "item": f"{SITE_URL}/articles/{parts[1]}/"
        })
        if len(parts) > 2 and parts[2] != "index.html":
            breadcrumbs.append({
                "position": 3,
                "@type": "ListItem",
                "name": page_title or parts[2].replace(".html", "").replace("-", " ").title(),
                "item": f"{SITE_URL}/articles/{parts[1]}/{parts[2]}"
            })
    elif parts[0] == "chapters":
        # Chapters structure: chapters/category/[subcategory]/[file].html
        breadcrumbs.append({
            "position": 2,
            "@type": "ListItem",
            "name": parts[1].replace("-", " ").title(),
            "item": f"{SITE_URL}/chapters/{parts[1]}/"
        })
        if len(parts) > 2 and parts[2] not in ["index.html", "articles"]:
            if parts[2] != "articles":
                breadcrumbs.append({
                    "position": len(breadcrumbs) + 1,
                    "@type": "ListItem",
                    "name": page_title or parts[2].replace("-", " ").title(),
                    "item": f"{SITE_URL}/chapters/{parts[1]}/{parts[2]}/"
                })

    return breadcrumbs

def add_breadcrumb_schema(file_path):
    """Add breadcrumb schema to an HTML file."""
    try:
        content = file_path.read_text(encoding='utf-8')

        # Check if breadcrumb schema already exists
        if '"@type":"BreadcrumbList"' in content or 'BreadcrumbList' in content:
            return False

        breadcrumbs = get_breadcrumbs(file_path, content)
        if not breadcrumbs:
            return False

        # Create schema
        schema = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": breadcrumbs
        }

        # Create JSON-LD script tag
        schema_json = json.dumps(schema, ensure_ascii=True, separators=(',', ':'))
        script_tag = f'<script type="application/ld+json">{schema_json}</script>'

        # Find insertion point - after other JSON-LD or at end of head
        # Look for the last </script> in head
        head_match = re.search(r'(</head>)', content, re.IGNORECASE)
        if not head_match:
            return False

        # Insert before </head>
        insert_pos = head_match.start(1)
        content = content[:insert_pos] + script_tag + '\n' + content[insert_pos:]

        file_path.write_text(content, encoding='utf-8')
        return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Add breadcrumb schema to all article and chapter pages."""
    count = 0
    skipped = 0

    # Process articles
    for article_file in (ROOT / "articles").rglob("*.html"):
        if article_file.name != "index.html":
            if add_breadcrumb_schema(article_file):
                count += 1
            else:
                skipped += 1

    # Process chapters
    for chapter_file in (ROOT / "chapters").rglob("*.html"):
        if chapter_file.name != "index.html":
            if add_breadcrumb_schema(chapter_file):
                count += 1
            else:
                skipped += 1

    print(f"✓ Breadcrumb schema added: {count} files")
    print(f"  Skipped (already exists): {skipped} files")
    return count

if __name__ == "__main__":
    count = main()
    exit(0 if count > 0 or count == 0 else 1)
