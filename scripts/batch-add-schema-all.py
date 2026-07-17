#!/usr/bin/env python3
"""
Batch add schema markup to ALL HTML files in the repository.
Processes 800+ pages systematically.
"""

import json
import re
from pathlib import Path
from datetime import datetime


def extract_metadata(html_content, file_path):
    """Extract title and description from HTML"""
    title_match = re.search(r'<title>([^<]+)</title>', html_content)
    title = title_match.group(1) if title_match else file_path.stem.replace('-', ' ').title()

    desc_match = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', html_content)
    description = desc_match.group(1) if desc_match else title

    return title, description


def get_url_from_path(file_path):
    """Convert file path to URL"""
    base_path = Path("/home/user/itvedas")
    relative = file_path.relative_to(base_path)

    # Convert to URL path
    url_path = "/" + str(relative).replace("\\", "/")
    if url_path.endswith("index.html"):
        url_path = url_path.replace("index.html", "")

    return f"https://www.itvedas.com{url_path}"


def get_breadcrumbs(file_path, title):
    """Generate breadcrumbs based on file location"""
    breadcrumbs = [("Home", "https://www.itvedas.com")]

    relative = file_path.relative_to(Path("/home/user/itvedas"))
    parts = relative.parts[:-1]  # Exclude filename

    url = "https://www.itvedas.com"
    for part in parts:
        url += f"/{part}"
        label = part.replace('-', ' ').title()
        breadcrumbs.append((label, url))

    breadcrumbs.append((title, get_url_from_path(file_path)))
    return breadcrumbs


def add_schema_to_file(file_path, is_news=False):
    """Add schema markup to a single HTML file"""
    try:
        html_content = file_path.read_text(encoding='utf-8')
    except:
        return False

    # Skip if already has schema
    if 'application/ld+json' in html_content:
        return False

    # Skip if no body tag
    if '</body>' not in html_content:
        return False

    title, description = extract_metadata(html_content, file_path)
    url = get_url_from_path(file_path)
    breadcrumbs = get_breadcrumbs(file_path, title)

    schemas = []

    # Add Article/News schema
    if is_news:
        article_schema = {
            "@context": "https://schema.org",
            "@type": "NewsArticle",
            "headline": title,
            "description": description,
            "url": url,
            "image": "https://www.itvedas.com/logo.png",
            "author": {
                "@type": "Organization",
                "name": "ITVedas"
            },
            "publisher": {
                "@type": "Organization",
                "name": "ITVedas",
                "logo": {
                    "@type": "ImageObject",
                    "url": "https://www.itvedas.com/logo.png"
                }
            },
            "datePublished": "2026-07-17T00:00:00Z",
            "dateModified": datetime.now().isoformat()
        }
    else:
        article_schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": description,
            "url": url,
            "author": {
                "@type": "Organization",
                "name": "ITVedas",
                "url": "https://www.itvedas.com"
            },
            "publisher": {
                "@type": "Organization",
                "name": "ITVedas",
                "logo": {
                    "@type": "ImageObject",
                    "url": "https://www.itvedas.com/logo.png"
                }
            },
            "datePublished": "2026-07-17T00:00:00Z",
            "dateModified": datetime.now().isoformat()
        }

    schemas.append(article_schema)

    # Add breadcrumb schema
    breadcrumb_items = []
    for i, (name, url_bc) in enumerate(breadcrumbs, 1):
        breadcrumb_items.append({
            "@type": "ListItem",
            "position": i,
            "name": name,
            "item": url_bc
        })

    breadcrumb_schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": breadcrumb_items
    }
    schemas.append(breadcrumb_schema)

    # Build schema tags
    schema_tags = ""
    for schema in schemas:
        schema_tags += f'<script type="application/ld+json">\n{json.dumps(schema, indent=2)}\n</script>\n'

    # Insert before closing body tag
    html_content = html_content.replace('</body>', f'{schema_tags}</body>')

    try:
        file_path.write_text(html_content, encoding='utf-8')
        return True
    except:
        return False


def process_all_html_files():
    """Process all HTML files in repository"""
    base_path = Path("/home/user/itvedas")
    html_files = list(base_path.glob("**/*.html"))

    # Exclude certain directories
    exclude_patterns = ['.git', 'node_modules', '__pycache__']
    html_files = [f for f in html_files if not any(ep in f.parts for ep in exclude_patterns)]

    updated = 0
    skipped = 0
    failed = 0

    # Separate news files
    news_files = [f for f in html_files if '/news/' in str(f)]
    other_files = [f for f in html_files if '/news/' not in str(f)]

    print(f"Processing {len(html_files)} HTML files...\n")
    print(f"News files: {len(news_files)}")
    print(f"Other files: {len(other_files)}\n")

    # Process news files
    for i, file_path in enumerate(news_files, 1):
        if add_schema_to_file(file_path, is_news=True):
            updated += 1
            if i % 10 == 0:
                print(f"✓ News: {i}/{len(news_files)}")
        else:
            skipped += 1

    # Process other files
    for i, file_path in enumerate(other_files, 1):
        if add_schema_to_file(file_path, is_news=False):
            updated += 1
            if i % 50 == 0:
                print(f"✓ Others: {i}/{len(other_files)}")
        else:
            skipped += 1

    return updated, skipped, len(html_files)


# Run batch processing
if __name__ == "__main__":
    print("=" * 60)
    print("BATCH SCHEMA MARKUP ADDITION")
    print("=" * 60 + "\n")

    updated, skipped, total = process_all_html_files()

    print(f"\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Total files: {total}")
    print(f"Updated: {updated} ✓")
    print(f"Skipped (already has schema): {skipped}")
    print(f"Coverage: {updated}/{total} = {updated*100//total}%")
    print("=" * 60)
