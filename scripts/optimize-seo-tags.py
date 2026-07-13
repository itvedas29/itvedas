#!/usr/bin/env python3
"""
Optimize SEO tags across all pages:
- Fix meta descriptions to optimal length (100-160 chars)
- Ensure OpenGraph tags on all pages
- Add Twitter Card tags
- Validate and improve structured data
"""

import pathlib
import re
from html.parser import HTMLParser

ROOT = pathlib.Path(".")
SITE_URL = "https://itvedas.com"

def truncate_description(desc, max_len=160, min_len=100):
    """Truncate description to optimal length."""
    if len(desc) <= max_len:
        return desc

    # Try to cut at word boundary
    trimmed = desc[:max_len]
    last_space = trimmed.rfind(' ')
    if last_space > min_len:
        return trimmed[:last_space].rstrip() + '...'
    return desc[:max_len]

def get_page_title(file_path, content):
    """Extract page title from content."""
    match = re.search(r'<title>([^<]+)</title>', content, re.IGNORECASE)
    return match.group(1) if match else None

def get_meta_description(content):
    """Extract meta description from content."""
    match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE)
    return match.group(1) if match else None

def fix_meta_descriptions(file_path, content):
    """Fix overly long meta descriptions."""
    desc = get_meta_description(content)
    if desc and len(desc) > 160:
        new_desc = truncate_description(desc)
        # Replace the meta description
        content = re.sub(
            r'(<meta\s+name=["\']description["\']\s+content=["\']).*?(["\'])',
            r'\1' + new_desc.replace('"', '&quot;') + r'\2',
            content,
            flags=re.IGNORECASE
        )
        return content, True
    return content, False

def ensure_og_tags(file_path, content):
    """Ensure OpenGraph tags are present."""
    # Check if OG tags exist
    has_og_title = 'property="og:title"' in content or "property='og:title'" in content

    if has_og_title:
        return content, False  # Already has OG tags

    # Extract information for OG tags
    title = get_page_title(file_path, content)
    desc = get_meta_description(content)

    if not title or not desc:
        return content, False

    # Prepare OG tags (without closing link tags since we're adding to head)
    og_tags = f'''<meta property="og:title" content="{title.replace('"', '&quot;')}">
<meta property="og:description" content="{desc.replace('"', '&quot;')}">
<meta property="og:image" content="{SITE_URL}/assets/og-default.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:type" content="article">
<meta property="og:url" content="{SITE_URL}{get_file_url(file_path)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title.replace('"', '&quot;')}">
<meta name="twitter:description" content="{desc.replace('"', '&quot;')}">
'''

    # Insert before </head>
    head_match = re.search(r'(</head>)', content, re.IGNORECASE)
    if head_match:
        insert_pos = head_match.start(1)
        content = content[:insert_pos] + og_tags + content[insert_pos:]
        return content, True

    return content, False

def get_file_url(file_path):
    """Convert file path to URL."""
    rel_path = file_path.relative_to(ROOT)
    if rel_path.name == "index.html":
        return '/' + str(rel_path.parent).replace('\\', '/') + '/'
    return '/' + str(rel_path).replace('\\', '/')

def process_file(file_path):
    """Process a single HTML file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        changed = False

        # Fix meta descriptions
        content, desc_fixed = fix_meta_descriptions(file_path, content)
        if desc_fixed:
            changed = True

        # Ensure OG tags (but not on category indexes or main navigation)
        if "/index.html" not in str(file_path) or "articles/" in str(file_path):
            content, og_added = ensure_og_tags(file_path, content)
            if og_added:
                changed = True

        if changed and content != original:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Process all HTML files for SEO optimization."""
    count = 0

    # Process articles
    for article_file in (ROOT / "articles").rglob("*.html"):
        if process_file(article_file):
            count += 1

    # Process chapters
    for chapter_file in (ROOT / "chapters").rglob("*.html"):
        if process_file(chapter_file):
            count += 1

    # Process news
    for news_file in (ROOT / "news").rglob("*.html"):
        if process_file(news_file):
            count += 1

    print(f"✓ SEO tags optimized: {count} files")
    return count

if __name__ == "__main__":
    count = main()
    exit(0)
