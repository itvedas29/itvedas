#!/usr/bin/env python3
"""
PHASE 4: Fix multiple H1 headings by converting excess H1s to H2s.
Each page should have exactly one H1 heading.
"""

import pathlib
import re

ROOT = pathlib.Path(".")

def fix_multiple_h1s(content):
    """Convert all H1 headings after the first to H2."""
    h1_count = 0
    changed = False

    def replace_h1(match):
        nonlocal h1_count, changed
        h1_count += 1
        if h1_count == 1:
            return match.group(0)
        else:
            original = match.group(0)
            fixed = original.replace('<h1', '<h2').replace('</h1>', '</h2>')
            changed = True
            return fixed

    content = re.sub(r'<h1([^>]*)>(.*?)</h1>', replace_h1, content, flags=re.IGNORECASE | re.DOTALL)
    return content, changed

def process_file(file_path):
    """Process a single HTML file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content

        content, changed = fix_multiple_h1s(content)

        if changed and content != original:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        return False

def main():
    """Fix H1 headings in all files."""
    fixed_count = 0

    # Process articles
    for article_file in (ROOT / "articles").rglob("*.html"):
        if process_file(article_file):
            fixed_count += 1

    # Process chapters
    for chapter_file in (ROOT / "chapters").rglob("*.html"):
        if process_file(chapter_file):
            fixed_count += 1

    # Process news
    for news_file in (ROOT / "news").rglob("*.html"):
        if process_file(news_file):
            fixed_count += 1

    print(f"✓ H1 heading issues fixed: {fixed_count} files")
    return fixed_count

if __name__ == "__main__":
    count = main()
    exit(0)
