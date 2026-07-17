#!/usr/bin/env python3
"""Add hreflang tags to all article HTML files for international SEO"""
import os
import re
from pathlib import Path

def get_relative_url(file_path):
    """Convert file path to relative URL"""
    # Remove /home/user/itvedas prefix
    rel_path = file_path.replace('/home/user/itvedas', '')
    return f"https://itvedas.com{rel_path}"

def add_hreflang_tags(file_path):
    """Add hreflang tags to an HTML file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Skip if already has hreflang tags
    if 'hreflang' in content:
        return False

    # Get the URL
    url = get_relative_url(file_path)

    # Create hreflang tags
    hreflang_tags = f'''<link rel="alternate" hreflang="x-default" href="{url}">
    <link rel="alternate" hreflang="en-US" href="{url}">
    <link rel="alternate" hreflang="en-GB" href="{url}">
    <link rel="alternate" hreflang="en-AU" href="{url}">
    <link rel="alternate" hreflang="en-CA" href="{url}">
    <link rel="alternate" hreflang="en-IN" href="{url}">
    <link rel="alternate" hreflang="en" href="{url}">'''

    # Look for canonical link or title tag to insert after
    # First try to find canonical link
    canonical_pattern = r'(<link rel="canonical"[^>]*>)'
    match = re.search(canonical_pattern, content)

    if match:
        # Insert after canonical link
        insert_pos = match.end()
        content = content[:insert_pos] + '\n    ' + hreflang_tags + '\n    ' + content[insert_pos:]
    else:
        # Try to insert before title tag or before </head>
        title_pattern = r'(<title>|</head>)'
        match = re.search(title_pattern, content)
        if match:
            insert_pos = match.start()
            content = content[:insert_pos] + hreflang_tags + '\n    ' + content[insert_pos:]
        else:
            return False

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return True

def main():
    """Main function"""
    base_path = '/home/user/itvedas'
    article_dirs = [
        'articles',
        'chapters',
    ]

    files_updated = 0
    files_skipped = 0

    for article_dir in article_dirs:
        dir_path = os.path.join(base_path, article_dir)
        if not os.path.exists(dir_path):
            continue

        # Find all .html files
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                if file.endswith('.html'):
                    file_path = os.path.join(root, file)
                    try:
                        if add_hreflang_tags(file_path):
                            files_updated += 1
                            print(f"✓ Updated: {file_path}")
                        else:
                            files_skipped += 1
                            print(f"⊘ Skipped (already has hreflang or missing head): {file_path}")
                    except Exception as e:
                        print(f"✗ Error: {file_path}: {e}")

    print(f"\nSummary: {files_updated} files updated, {files_skipped} skipped")

if __name__ == '__main__':
    main()
