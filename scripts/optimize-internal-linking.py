#!/usr/bin/env python3
"""
Optimize internal linking strategy:
1. Add "Related Articles" section to all articles
2. Create content clusters
3. Link similar topics
4. Improve content discoverability
"""

import pathlib
import re
import json
from collections import defaultdict

ROOT = pathlib.Path(".")

def get_article_keywords(file_path, content):
    """Extract keywords from article."""
    keywords = []

    # Get from meta keywords
    keywords_match = re.search(r'<meta\s+name=["\']keywords["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE)
    if keywords_match:
        keywords = [k.strip() for k in keywords_match.group(1).split(',')]

    return keywords

def find_related_articles(file_path, all_articles_info, current_keywords):
    """Find related articles based on keyword overlap."""
    related = []

    for other_path, other_info in all_articles_info.items():
        if other_path == file_path:
            continue

        # Calculate keyword overlap
        other_keywords = set(other_info.get('keywords', []))
        current_keywords_set = set(current_keywords)

        overlap = len(other_keywords & current_keywords_set)
        if overlap >= 2:  # At least 2 keywords in common
            related.append({
                'path': other_path,
                'overlap': overlap,
                'title': other_info.get('title', ''),
                'url': other_info.get('url', '')
            })

    # Sort by relevance (keyword overlap) and limit to 5
    return sorted(related, key=lambda x: x['overlap'], reverse=True)[:5]

def add_related_section(content, related_articles):
    """Add related articles section to content."""
    if not related_articles or "<!-- Related Articles -->" in content:
        return content

    related_html = '\n<hr><div class="related-articles" style="margin-top:3rem;padding-top:2rem;border-top:1px solid #333;">\n'
    related_html += '<h2>Related Articles</h2>\n<ul style="list-style:none;padding:0;">\n'

    for article in related_articles:
        title = article['title'].replace('<', '&lt;').replace('>', '&gt;')
        url = article['url']
        related_html += f'<li style="margin:0.5rem 0;"><a href="{url}">{title}</a></li>\n'

    related_html += '</ul>\n</div>\n<!-- Related Articles -->'

    # Insert before </article> or </body>
    article_match = re.search(r'(</article>)', content, re.IGNORECASE)
    if article_match:
        insert_pos = article_match.start(1)
        return content[:insert_pos] + related_html + content[insert_pos:]

    body_match = re.search(r'(</body>)', content, re.IGNORECASE)
    if body_match:
        insert_pos = body_match.start(1)
        return content[:insert_pos] + related_html + content[insert_pos:]

    return content

def process_articles():
    """Process all articles and add internal linking."""
    # First pass: collect all article info
    all_articles = {}

    for article_file in (ROOT / "articles").rglob("*.html"):
        try:
            content = article_file.read_text(encoding='utf-8')
            title_match = re.search(r'<title>([^<]+)</title>', content, re.IGNORECASE)
            title = title_match.group(1) if title_match else article_file.stem

            url = f"/articles/{article_file.parent.name}/{article_file.name}"
            if article_file.name == "index.html":
                url = f"/articles/{article_file.parent.name}/"

            keywords = get_article_keywords(article_file, content)

            all_articles[article_file] = {
                'title': title,
                'url': url,
                'keywords': keywords
            }
        except Exception as e:
            pass

    # Second pass: add related articles
    updated_count = 0

    for article_file, article_info in all_articles.items():
        try:
            content = article_file.read_text(encoding='utf-8')

            # Find related articles
            related = find_related_articles(
                article_file,
                all_articles,
                article_info.get('keywords', [])
            )

            if related:
                # Add related section
                new_content = add_related_section(content, related)

                if new_content != content:
                    article_file.write_text(new_content, encoding='utf-8')
                    updated_count += 1
        except Exception as e:
            pass

    return updated_count

def main():
    """Optimize internal linking."""
    print("✓ Optimizing internal links...")
    count = process_articles()

    print(f"✓ Internal linking optimized: {count} pages updated")
    return count

if __name__ == "__main__":
    count = main()
    exit(0)
