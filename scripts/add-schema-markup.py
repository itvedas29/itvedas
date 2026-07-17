#!/usr/bin/env python3
"""
Add structured data (schema.org) markup to HTML files for SEO.
Adds ArticleSchema, NewsArticleSchema, and BreadcrumbSchema.
"""

import json
import re
from pathlib import Path
from datetime import datetime


def add_article_schema(html_content, file_path, title, description):
    """Add ArticleSchema markup to HTML"""
    url = f"https://www.itvedas.com{file_path.relative_to('/home/user/itvedas').as_posix()}"

    article_schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "url": url,
        "author": {
            "@type": "Organization",
            "name": "ITVedas",
            "url": "https://www.itvedas.com"
        },
        "publisher": {
            "@type": "Organization",
            "name": "ITVedas",
            "logo": {
                "@type": "ImageObject",
                "url": "https://www.itvedas.com/logo.png"
            }
        },
        "datePublished": datetime.now().isoformat(),
        "dateModified": datetime.now().isoformat()
    }

    schema_tag = f'<script type="application/ld+json">\n{json.dumps(article_schema, indent=2)}\n</script>'

    # Insert before closing body tag
    if '</body>' in html_content:
        html_content = html_content.replace('</body>', f'{schema_tag}\n</body>')

    return html_content


def add_breadcrumb_schema(html_content, breadcrumbs):
    """Add BreadcrumbSchema markup"""
    items = []
    for i, (name, url) in enumerate(breadcrumbs, 1):
        items.append({
            "@type": "ListItem",
            "position": i,
            "name": name,
            "item": url
        })

    breadcrumb_schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items
    }

    schema_tag = f'<script type="application/ld+json">\n{json.dumps(breadcrumb_schema, indent=2)}\n</script>'

    if '</body>' in html_content:
        html_content = html_content.replace('</body>', f'{schema_tag}\n</body>')

    return html_content


def add_news_article_schema(html_content, file_path, title, description, news_date=None):
    """Add NewsArticleSchema for news items"""
    url = f"https://www.itvedas.com{file_path.relative_to('/home/user/itvedas').as_posix()}"

    news_schema = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": title,
        "description": description,
        "url": url,
        "image": "https://www.itvedas.com/logo.png",
        "author": {
            "@type": "Organization",
            "name": "ITVedas"
        },
        "publisher": {
            "@type": "Organization",
            "name": "ITVedas",
            "logo": {
                "@type": "ImageObject",
                "url": "https://www.itvedas.com/logo.png"
            }
        },
        "datePublished": news_date or datetime.now().isoformat(),
        "dateModified": datetime.now().isoformat()
    }

    schema_tag = f'<script type="application/ld+json">\n{json.dumps(news_schema, indent=2)}\n</script>'

    if '</body>' in html_content:
        html_content = html_content.replace('</body>', f'{schema_tag}\n</body>')

    return html_content


def add_organization_schema(html_content):
    """Add OrganizationSchema to homepage"""
    org_schema = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "ITVedas",
        "url": "https://www.itvedas.com",
        "logo": "https://www.itvedas.com/logo.png",
        "description": "Complete IT knowledge base with tutorials, CVE database, career guidance, and problem solutions",
        "sameAs": [
            "https://github.com/itvedas29/itvedas"
        ],
        "address": {
            "@type": "PostalAddress",
            "addressCountry": "Global"
        }
    }

    schema_tag = f'<script type="application/ld+json">\n{json.dumps(org_schema, indent=2)}\n</script>'

    if '</body>' in html_content:
        html_content = html_content.replace('</body>', f'{schema_tag}\n</body>')

    return html_content


def process_articles():
    """Add schema to article files"""
    articles_dir = Path("/home/user/itvedas/articles")
    if not articles_dir.exists():
        return 0

    count = 0
    for article_file in articles_dir.glob("*.html"):
        content = article_file.read_text()

        # Extract title from <title> tag
        title_match = re.search(r'<title>([^<]+)</title>', content)
        title = title_match.group(1) if title_match else article_file.stem

        # Extract description
        desc_match = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', content)
        description = desc_match.group(1) if desc_match else title

        # Check if schema already exists
        if 'application/ld+json' in content:
            continue

        # Add article schema
        content = add_article_schema(content, article_file, title, description)
        # Add breadcrumb
        content = add_breadcrumb_schema(content, [
            ("Home", "https://www.itvedas.com"),
            ("Articles", "https://www.itvedas.com/articles"),
            (title, f"https://www.itvedas.com/articles/{article_file.name}")
        ])

        article_file.write_text(content)
        count += 1

    return count


def process_chapters():
    """Add schema to chapter files"""
    chapters_dir = Path("/home/user/itvedas/chapters")
    if not chapters_dir.exists():
        return 0

    count = 0
    for chapter_file in chapters_dir.glob("**/*.html"):
        content = chapter_file.read_text()

        # Skip if already has schema
        if 'application/ld+json' in content:
            continue

        title_match = re.search(r'<title>([^<]+)</title>', content)
        title = title_match.group(1) if title_match else chapter_file.stem

        desc_match = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', content)
        description = desc_match.group(1) if desc_match else title

        # Add article schema
        content = add_article_schema(content, chapter_file, title, description)
        # Add breadcrumb
        relative_path = chapter_file.relative_to(chapters_dir)
        content = add_breadcrumb_schema(content, [
            ("Home", "https://www.itvedas.com"),
            ("Chapters", "https://www.itvedas.com/chapters"),
            (title, f"https://www.itvedas.com/chapters/{relative_path}")
        ])

        chapter_file.write_text(content)
        count += 1

    return count


def process_news():
    """Add schema to news items"""
    news_dir = Path("/home/user/itvedas/news")
    if not news_dir.exists():
        return 0

    count = 0
    for news_file in news_dir.glob("*.html"):
        content = news_file.read_text()

        if 'application/ld+json' in content:
            continue

        title_match = re.search(r'<title>([^<]+)</title>', content)
        title = title_match.group(1) if title_match else news_file.stem

        desc_match = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', content)
        description = desc_match.group(1) if desc_match else title

        # Add news schema
        content = add_news_article_schema(content, news_file, title, description)
        # Add breadcrumb
        content = add_breadcrumb_schema(content, [
            ("Home", "https://www.itvedas.com"),
            ("News", "https://www.itvedas.com/news"),
            (title, f"https://www.itvedas.com/news/{news_file.name}")
        ])

        news_file.write_text(content)
        count += 1

    return count


def process_homepage():
    """Add org schema to homepage"""
    homepage = Path("/home/user/itvedas/index.html")
    if not homepage.exists():
        return 0

    content = homepage.read_text()

    if 'application/ld+json' in content:
        return 0

    content = add_organization_schema(content)
    homepage.write_text(content)
    return 1


# Run schema markup additions
if __name__ == "__main__":
    print("Adding structured data (schema.org) markup...\n")

    article_count = process_articles()
    print(f"✓ Articles: {article_count} files updated")

    chapter_count = process_chapters()
    print(f"✓ Chapters: {chapter_count} files updated")

    news_count = process_news()
    print(f"✓ News: {news_count} files updated")

    homepage_count = process_homepage()
    print(f"✓ Homepage: {homepage_count} files updated")

    total = article_count + chapter_count + news_count + homepage_count
    print(f"\n{total} files updated with schema markup")
