#!/usr/bin/env python3
"""
PHASE 5: Audit information architecture and site structure.
Analyze:
1. Navigation depth and breadth
2. Content organization efficiency
3. Internal link topology
4. Category coverage and balance
5. Orphaned content identification
"""

import pathlib
import re
from collections import defaultdict

ROOT = pathlib.Path(".")

def extract_internal_links(content):
    """Extract all internal links from content."""
    links = set()
    for match in re.finditer(r'href=["\'](/[^"\']*)["\']', content):
        url = match.group(1).rstrip('/')
        links.add(url)
    return links

def analyze_category_structure():
    """Analyze category and content distribution."""
    print("PHASE 5: Information Architecture Audit\n")
    print("=" * 60)

    structure = defaultdict(lambda: {'count': 0, 'paths': []})

    # Analyze articles
    for article_file in (ROOT / "articles").rglob("*.html"):
        relative = article_file.relative_to(ROOT / "articles")
        parts = relative.parts

        if len(parts) > 1:
            category = parts[0]
            structure[f"articles/{category}"]['count'] += 1
            structure[f"articles/{category}"]['paths'].append(str(relative))
        else:
            structure['articles/root']['count'] += 1
            structure['articles/root']['paths'].append(str(relative))

    # Analyze chapters
    for chapter_file in (ROOT / "chapters").rglob("*.html"):
        relative = chapter_file.relative_to(ROOT / "chapters")
        parts = relative.parts

        if len(parts) > 1:
            category = parts[0]
            structure[f"chapters/{category}"]['count'] += 1
            structure[f"chapters/{category}"]['paths'].append(str(relative))
        else:
            structure['chapters/root']['count'] += 1
            structure['chapters/root']['paths'].append(str(relative))

    # Analyze news
    for news_file in (ROOT / "news").rglob("*.html"):
        relative = news_file.relative_to(ROOT / "news")
        parts = relative.parts

        if len(parts) > 1:
            category = parts[0]
            structure[f"news/{category}"]['count'] += 1
            structure[f"news/{category}"]['paths'].append(str(relative))
        else:
            structure['news/root']['count'] += 1
            structure['news/root']['paths'].append(str(relative))

    # Report structure
    print("📊 Content Distribution by Category:\n")

    articles_total = 0
    chapters_total = 0
    news_total = 0

    for category in sorted(structure.keys()):
        if category.startswith('articles/'):
            articles_total += structure[category]['count']
            cat_name = category.replace('articles/', '')
            print(f"📁 articles/{cat_name:30} {structure[category]['count']:3} pages")

    print()
    for category in sorted(structure.keys()):
        if category.startswith('chapters/'):
            chapters_total += structure[category]['count']
            cat_name = category.replace('chapters/', '')
            print(f"📁 chapters/{cat_name:29} {structure[category]['count']:3} pages")

    print()
    for category in sorted(structure.keys()):
        if category.startswith('news/'):
            news_total += structure[category]['count']
            cat_name = category.replace('news/', '')
            print(f"📁 news/{cat_name:37} {structure[category]['count']:3} pages")

    print(f"\n{'=' * 60}")
    print(f"📈 Summary Statistics:")
    print(f"  Articles total: {articles_total}")
    print(f"  Chapters total: {chapters_total}")
    print(f"  News total: {news_total}")
    print(f"  Overall total: {articles_total + chapters_total + news_total}")
    print(f"\n  Categories: {len(structure)}")
    print(f"  Average pages per category: {(articles_total + chapters_total + news_total) / len(structure):.1f}")

    # Find undersized categories
    print(f"\n⚠️  Undersized Categories (< 5 pages):")
    undersized = []
    for category in sorted(structure.keys()):
        if structure[category]['count'] < 5 and structure[category]['count'] > 0:
            undersized.append(category)
            print(f"  {category}: {structure[category]['count']} pages")

    return structure

def analyze_link_topology():
    """Analyze internal link topology and orphaned content."""
    print(f"\n{'=' * 60}")
    print("🔗 Link Topology Analysis:\n")

    all_files = set()
    linked_files = set()
    internal_links = defaultdict(set)

    # Collect all HTML files
    for file_path in (ROOT / "articles").rglob("*.html"):
        all_files.add(str(file_path.relative_to(ROOT)))

    for file_path in (ROOT / "chapters").rglob("*.html"):
        all_files.add(str(file_path.relative_to(ROOT)))

    for file_path in (ROOT / "news").rglob("*.html"):
        all_files.add(str(file_path.relative_to(ROOT)))

    # Analyze links
    for file_path in (ROOT).rglob("*.html"):
        try:
            content = file_path.read_text(encoding='utf-8')
            links = extract_internal_links(content)

            for link in links:
                # Normalize link
                if link.endswith('/'):
                    link_normalized = link.rstrip('/') + '/index.html'
                else:
                    link_normalized = link + '.html'

                linked_files.add(link_normalized)
        except Exception:
            pass

    orphaned = all_files - linked_files
    print(f"Total files: {len(all_files)}")
    print(f"Linked files: {len(linked_files)}")
    print(f"Orphaned files (not linked from anywhere): {len(orphaned)}")

    if orphaned:
        print(f"\n⚠️  Orphaned content files (not linked from anywhere):")
        for f in sorted(orphaned)[:10]:
            print(f"  - {f}")
        if len(orphaned) > 10:
            print(f"  ... and {len(orphaned) - 10} more")

    return len(orphaned)

def main():
    """Analyze site information architecture."""
    structure = analyze_category_structure()
    orphaned_count = analyze_link_topology()

    print(f"\n{'=' * 60}")
    print("✓ Information Architecture Audit Complete")
    return len(structure), orphaned_count

if __name__ == "__main__":
    categories, orphaned = main()
    exit(0)
