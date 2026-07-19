#!/usr/bin/env python3
"""
PHASE 4: Add missing meta descriptions to pages.
Generate descriptions from H1 heading and first paragraph.
"""

import pathlib
import re

ROOT = pathlib.Path(".")

def get_h1_text(content):
    """Extract H1 heading text."""
    match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE | re.DOTALL)
    if match:
        text = match.group(1)
        text = re.sub(r'<[^>]+>', '', text)
        return text.strip()
    return None

def get_first_paragraph_text(content):
    """Extract first paragraph text."""
    match = re.search(r'<p[^>]*>(.*?)</p>', content, re.IGNORECASE | re.DOTALL)
    if match:
        text = match.group(1)
        text = re.sub(r'<[^>]+>', '', text)
        return text.strip()
    return None

def generate_meta_description(content):
    """Generate meta description from H1 and first paragraph."""
    h1_text = get_h1_text(content)
    p_text = get_first_paragraph_text(content)

    if h1_text and p_text:
        description = f"{h1_text}. {p_text}"
    elif h1_text:
        description = h1_text
    elif p_text:
        description = p_text
    else:
        return None

    # Truncate to 150-160 chars
    if len(description) > 160:
        description = description[:157] + "..."

    return description

def has_meta_description(content):
    """Check if page already has meta description."""
    return bool(re.search(r'<meta\s+name=["\']description["\']\s+content=', content, re.IGNORECASE))

def add_meta_description(content, description):
    """Add meta description to head."""
    if has_meta_description(content):
        return content, False

    meta_tag = f'\n<meta name="description" content="{description}">'

    # Insert before </head>
    match = re.search(r'(</head>)', content, re.IGNORECASE)
    if match:
        insert_pos = match.start(1)
        return content[:insert_pos] + meta_tag + content[insert_pos:], True

    return content, False

def process_file(file_path):
    """Process a single HTML file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content

        description = generate_meta_description(content)
        if description:
            content, changed = add_meta_description(content, description)
            if changed and content != original:
                file_path.write_text(content, encoding='utf-8')
                return True

        return False
    except Exception as e:
        return False

def main():
    """Add missing meta descriptions."""
    added_count = 0

    # Process articles
    for article_file in (ROOT / "articles").rglob("*.html"):
        if process_file(article_file):
            added_count += 1

    # Process chapters
    for chapter_file in (ROOT / "chapters").rglob("*.html"):
        if process_file(chapter_file):
            added_count += 1

    # Process news
    for news_file in (ROOT / "news").rglob("*.html"):
        if process_file(news_file):
            added_count += 1

    print(f"✓ Meta descriptions added: {added_count} pages")
    return added_count

if __name__ == "__main__":
    count = main()
    exit(0)
