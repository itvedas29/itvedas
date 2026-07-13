#!/usr/bin/env python3
"""
PHASE 4: Detect duplicate and near-duplicate content.
Uses text similarity to identify pages with similar content.
"""

import pathlib
import re
from collections import defaultdict

ROOT = pathlib.Path(".")

def extract_text_content(html):
    """Extract plain text from HTML."""
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()

def get_text_hash(text):
    """Get unique words from text (signature)."""
    words = text.split()
    # Use first 50 words as signature (avoid hashing due to collisions)
    return frozenset(words[:50])

def calculate_similarity(text1, text2):
    """Calculate Jaccard similarity between two texts."""
    words1 = set(text1.split()[:100])
    words2 = set(text2.split()[:100])

    if not words1 or not words2:
        return 0

    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union > 0 else 0

def get_page_title(content):
    """Extract page title."""
    match = re.search(r'<title>([^<]+)</title>', content, re.IGNORECASE)
    return match.group(1) if match else "Unknown"

def scan_for_duplicates():
    """Scan all pages for duplicate content."""
    print("PHASE 4: Duplicate Content Detection\n")
    print("=" * 60)

    pages = {}
    duplicates = []

    # Collect all pages
    for file_path in sorted((ROOT / "articles").rglob("*.html")):
        try:
            content = file_path.read_text(encoding='utf-8')
            text = extract_text_content(content)
            title = get_page_title(content)
            if len(text.split()) > 100:  # Only track substantial pages
                pages[file_path] = {
                    'content': text,
                    'title': title,
                    'type': 'article'
                }
        except Exception:
            pass

    for file_path in sorted((ROOT / "chapters").rglob("*.html")):
        try:
            content = file_path.read_text(encoding='utf-8')
            text = extract_text_content(content)
            title = get_page_title(content)
            if len(text.split()) > 100:
                pages[file_path] = {
                    'content': text,
                    'title': title,
                    'type': 'chapter'
                }
        except Exception:
            pass

    # Compare pages for similarity
    paths = list(pages.keys())
    for i, path1 in enumerate(paths):
        for path2 in paths[i+1:]:
            similarity = calculate_similarity(
                pages[path1]['content'],
                pages[path2]['content']
            )

            if similarity > 0.7:  # 70% or higher similarity
                duplicates.append({
                    'path1': path1.relative_to(ROOT),
                    'title1': pages[path1]['title'],
                    'path2': path2.relative_to(ROOT),
                    'title2': pages[path2]['title'],
                    'similarity': similarity
                })

    # Report results
    if duplicates:
        print(f"\n⚠️  Found {len(duplicates)} potential duplicate content pairs:\n")
        for dup in sorted(duplicates, key=lambda x: x['similarity'], reverse=True):
            print(f"Similarity: {dup['similarity']:.1%}")
            print(f"  1. {dup['path1']}")
            print(f"     {dup['title1']}")
            print(f"  2. {dup['path2']}")
            print(f"     {dup['title2']}")
            print()
    else:
        print("\n✓ No duplicate content detected (similarity > 70%)")

    print(f"{'=' * 60}")
    print(f"Total pages analyzed: {len(pages)}")

    return len(duplicates)

if __name__ == "__main__":
    count = scan_for_duplicates()
    exit(0)
