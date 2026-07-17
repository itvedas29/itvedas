#!/usr/bin/env python3
"""
PHASE 7: Generate comprehensive search index for site.
Create searchable JSON index of all content for client-side search.
"""

import pathlib
import re
import json
from datetime import datetime

ROOT = pathlib.Path(".")

def extract_text_content(html, max_length=500):
    """Extract plain text from HTML."""
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) > max_length:
        text = text[:max_length].rsplit(' ', 1)[0] + '...'
    return text

def get_page_metadata(file_path, content):
    """Extract page metadata for search index."""
    title_match = re.search(r'<title>([^<]+)</title>', content, re.IGNORECASE)
    title = title_match.group(1).replace(' — ITVedas', '') if title_match else file_path.stem

    desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE)
    description = desc_match.group(1) if desc_match else ""

    keywords_match = re.search(r'<meta\s+name=["\']keywords["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE)
    keywords = [k.strip() for k in keywords_match.group(1).split(',')] if keywords_match else []

    h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE | re.DOTALL)
    h1 = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip() if h1_match else ""

    p_match = re.search(r'<p[^>]*>(.*?)</p>', content, re.IGNORECASE | re.DOTALL)
    preview = re.sub(r'<[^>]+>', '', p_match.group(1)).strip() if p_match else description

    parts = file_path.relative_to(ROOT).parts
    category = ""
    if len(parts) >= 2:
        category = parts[1] if parts[0] in ['articles', 'chapters', 'news'] else parts[0]

    return {
        'title': title,
        'description': description,
        'keywords': keywords,
        'h1': h1,
        'preview': preview[:200] if preview else "",
        'category': category,
        'content': extract_text_content(content)
    }

def build_search_index():
    """Build comprehensive search index."""
    print("PHASE 7: Generating Search Index\n")

    index = {
        'version': '1.0',
        'generated': datetime.now().isoformat(),
        'pages': [],
        'categories': set(),
        'total_pages': 0
    }

    print("Indexing articles...")
    article_count = 0
    for article_file in (ROOT / "articles").rglob("*.html"):
        try:
            content = article_file.read_text(encoding='utf-8')
            url = f"/{article_file.relative_to(ROOT)}".replace('.html', '/') if article_file.name != 'index.html' else f"/{article_file.relative_to(ROOT)}"

            metadata = get_page_metadata(article_file, content)
            index['categories'].add(metadata['category'])

            page_entry = {
                'url': url,
                'type': 'article',
                'path': str(article_file.relative_to(ROOT)),
                **metadata
            }

            index['pages'].append(page_entry)
            article_count += 1
        except Exception as e:
            pass

    print(f"  ✓ {article_count} articles indexed")

    print("Indexing chapters...")
    chapter_count = 0
    for chapter_file in (ROOT / "chapters").rglob("*.html"):
        try:
            content = chapter_file.read_text(encoding='utf-8')
            url = f"/{chapter_file.relative_to(ROOT)}".replace('.html', '/') if chapter_file.name != 'index.html' else f"/{chapter_file.relative_to(ROOT)}"

            metadata = get_page_metadata(chapter_file, content)
            index['categories'].add(metadata['category'])

            page_entry = {
                'url': url,
                'type': 'chapter',
                'path': str(chapter_file.relative_to(ROOT)),
                **metadata
            }

            index['pages'].append(page_entry)
            chapter_count += 1
        except Exception as e:
            pass

    print(f"  ✓ {chapter_count} chapters indexed")

    print("Indexing news...")
    news_count = 0
    # Exclude news/archive/ paginated listing pages from the "50 most
    # recent" news scan — they're navigational (a paginated index of
    # every post), not standalone articles, and since they get
    # rewritten on every pipeline run their mtime would otherwise push
    # real articles out of the top 50.
    news_files = sorted(
        (f for f in (ROOT / "news").rglob("*.html") if f.parent.name != "archive"),
        key=lambda x: x.stat().st_mtime, reverse=True,
    )

    for news_file in news_files[:50]:
        try:
            content = news_file.read_text(encoding='utf-8')
            url = f"/{news_file.relative_to(ROOT)}".replace('.html', '/') if news_file.name != 'index.html' else f"/{news_file.relative_to(ROOT)}"

            metadata = get_page_metadata(news_file, content)

            page_entry = {
                'url': url,
                'type': 'news',
                'path': str(news_file.relative_to(ROOT)),
                **metadata
            }

            index['pages'].append(page_entry)
            news_count += 1
        except Exception as e:
            pass

    print(f"  ✓ {news_count} news items indexed")

    index['categories'] = sorted(list(index['categories']))
    index['total_pages'] = len(index['pages'])

    index_path = ROOT / "search-index.json"
    with open(index_path, 'w') as f:
        json.dump(index, f, ensure_ascii=True, separators=(',', ':'), indent=2)

    print(f"\n{'=' * 60}")
    print(f"📊 Search Index Summary:")
    print(f"  Total pages indexed: {index['total_pages']}")
    print(f"  Categories: {len(index['categories'])}")
    print(f"  Index file: {index_path.relative_to(ROOT)}")
    print(f"  File size: {index_path.stat().st_size / 1024:.1f} KB")

    return index['total_pages']

if __name__ == "__main__":
    count = build_search_index()
    exit(0)
