#!/usr/bin/env python3
"""
Add canonical URLs to all HTML pages to prevent duplicate content issues
"""

from pathlib import Path
import re

DOMAIN = "https://itvedas.com"
ROOT = Path("/home/user/itvedas")


def add_canonical_url(file_path, url_path):
    """Add canonical URL to HTML file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if canonical already exists
    if 'rel="canonical"' in content or "rel='canonical'" in content:
        return False

    canonical_url = f'{DOMAIN}{url_path}'
    canonical_tag = f'<link rel="canonical" href="{canonical_url}">\n'

    # Insert after other head meta tags
    head_match = re.search(r'(<meta[^>]*>\n)', content)
    if head_match:
        insert_pos = head_match.end()
        content = content[:insert_pos] + canonical_tag + content[insert_pos:]
    elif '<head>' in content:
        insert_pos = content.find('<head>') + len('<head>\n')
        content = content[:insert_pos] + canonical_tag + content[insert_pos:]
    else:
        return False

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return True


def get_url_for_file(file_path):
    """Convert file path to URL"""
    rel_path = file_path.relative_to(ROOT)
    url_path = '/' + str(rel_path).replace('\\', '/')

    # Remove index.html from URL
    if url_path.endswith('/index.html'):
        url_path = url_path[:-11]

    # Add trailing slash for directories
    if not url_path.endswith('.html') and not url_path.endswith('/'):
        url_path += '/'

    return url_path


def main():
    """Add canonical URLs to all HTML files"""
    print("Adding canonical URLs to HTML files...\n")

    html_files = list(ROOT.glob('**/*.html'))
    added = 0
    skipped = 0

    for html_file in sorted(html_files):
        # Skip certain files
        if any(x in str(html_file) for x in ['.git', 'node_modules', 'cve-data', 'archive']):
            continue

        url_path = get_url_for_file(html_file)
        rel_path = html_file.relative_to(ROOT)

        if add_canonical_url(html_file, url_path):
            print(f"✓ Added canonical: {rel_path}")
            print(f"  URL: {url_path}")
            added += 1
        else:
            skipped += 1

    print(f"\n{'='*60}")
    print(f"Canonical URLs added: {added}")
    print(f"Skipped (already had canonical): {skipped}")
    print(f"Total processed: {added + skipped}")


if __name__ == '__main__':
    main()
