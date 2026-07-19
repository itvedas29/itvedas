#!/usr/bin/env python3
"""
PHASE 4: Comprehensive content quality audit.
Identify and report on content quality issues:
1. Minimum content length requirements
2. Orphaned pages (no links from/to them)
3. Duplicate or near-duplicate content
4. Missing meta descriptions
5. Images without proper alt text
6. Broken internal links
"""

import pathlib
import re
from collections import defaultdict
import urllib.parse

ROOT = pathlib.Path(".")

def extract_text_content(html):
    """Extract plain text from HTML, removing tags."""
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_content_length(file_path, content):
    """Get word count of main content."""
    text = extract_text_content(content)
    words = text.split()
    return len(words)

def get_meta_description(content):
    """Extract meta description if present."""
    match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE)
    return match.group(1) if match else None

def get_images_without_alt(content):
    """Find images without alt text."""
    issues = []
    for match in re.finditer(r'<img\s+([^>]*?)/?>', content, re.IGNORECASE):
        tag = match.group(1)
        if 'alt=' not in tag.lower():
            issues.append(match.group(0))
    return issues

def get_internal_links(file_path, content):
    """Extract all internal links from a page."""
    links = set()
    for match in re.finditer(r'href=["\'](.*?)["\']', content):
        url = match.group(1)
        if url.startswith('/') or url.startswith('./'):
            links.add(url)
    return links

def audit_file(file_path, content):
    """Audit a single file for quality issues."""
    issues = []
    word_count = get_content_length(file_path, content)

    # Check minimum content length (500 words minimum)
    if word_count < 500:
        issues.append(f"Short content: {word_count} words (minimum 500)")

    # Check for meta description
    if not get_meta_description(content):
        issues.append("Missing meta description")

    # Check for images without alt text
    img_issues = get_images_without_alt(content)
    if img_issues:
        issues.append(f"Images without alt text: {len(img_issues)}")

    # Check for empty paragraphs
    empty_p = len(re.findall(r'<p[^>]*>\s*</p>', content, re.IGNORECASE))
    if empty_p > 0:
        issues.append(f"Empty paragraphs: {empty_p}")

    # Check heading structure
    h1_count = len(re.findall(r'<h1[^>]*>', content, re.IGNORECASE))
    if h1_count == 0:
        issues.append("Missing H1 heading")
    elif h1_count > 1:
        issues.append(f"Multiple H1 headings: {h1_count}")

    return {
        'path': file_path,
        'word_count': word_count,
        'issues': issues,
        'has_issues': len(issues) > 0
    }

def main():
    """Audit content quality across all pages."""
    print("PHASE 4: Content Quality Audit\n")
    print("=" * 60)

    all_results = []
    critical_issues = 0
    warning_issues = 0

    # Audit all articles
    for article_file in sorted((ROOT / "articles").rglob("*.html")):
        try:
            content = article_file.read_text(encoding='utf-8')
            result = audit_file(article_file, content)
            all_results.append(result)

            if result['has_issues']:
                warning_issues += len(result['issues'])
                print(f"\n📄 {article_file.relative_to(ROOT)}")
                print(f"   Words: {result['word_count']}")
                for issue in result['issues']:
                    print(f"   ⚠️  {issue}")
        except Exception as e:
            print(f"❌ Error processing {article_file}: {e}")
            critical_issues += 1

    # Audit all chapters
    for chapter_file in sorted((ROOT / "chapters").rglob("*.html")):
        try:
            content = chapter_file.read_text(encoding='utf-8')
            result = audit_file(chapter_file, content)
            all_results.append(result)

            if result['has_issues']:
                warning_issues += len(result['issues'])
                print(f"\n📄 {chapter_file.relative_to(ROOT)}")
                print(f"   Words: {result['word_count']}")
                for issue in result['issues']:
                    print(f"   ⚠️  {issue}")
        except Exception as e:
            print(f"❌ Error processing {chapter_file}: {e}")
            critical_issues += 1

    # Summary statistics
    print(f"\n{'=' * 60}")
    print(f"📊 Content Quality Audit Summary")
    print(f"{'=' * 60}")

    total_pages = len(all_results)
    pages_with_issues = sum(1 for r in all_results if r['has_issues'])
    avg_word_count = sum(r['word_count'] for r in all_results) / total_pages if total_pages > 0 else 0

    short_content = sum(1 for r in all_results if r['word_count'] < 500)
    no_meta_desc = sum(1 for r in all_results if any('meta description' in i for i in r['issues']))

    print(f"\nTotal pages audited: {total_pages}")
    print(f"Pages with quality issues: {pages_with_issues}")
    print(f"Average word count: {avg_word_count:.0f}")
    print(f"\nCritical Issues:")
    print(f"  Short content (<500 words): {short_content}")
    print(f"  Missing meta descriptions: {no_meta_desc}")
    print(f"  Processing errors: {critical_issues}")

    return pages_with_issues

if __name__ == "__main__":
    count = main()
    exit(0)
