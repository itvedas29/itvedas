#!/usr/bin/env python3
"""
Add comprehensive schema markup for better SEO:
- FAQ Schema for FAQ pages
- Article Schema improvements
- Software Application Schema for tools
- Local Business Schema
- Event Schema where applicable
"""

import json
import pathlib
import re
from datetime import datetime

ROOT = pathlib.Path(".")
SITE_URL = "https://itvedas.com"

def get_page_info(file_path, content):
    """Extract page information for schema."""
    # Get title
    title_match = re.search(r'<title>([^<]+)</title>', content, re.IGNORECASE)
    title = title_match.group(1) if title_match else "ITVedas"

    # Get description
    desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE)
    description = desc_match.group(1) if desc_match else ""

    # Get image
    og_img = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE)
    image = og_img.group(1) if og_img else f"{SITE_URL}/assets/og-default.png"

    return {
        "title": title,
        "description": description,
        "image": image,
        "url": get_file_url(file_path)
    }

def get_file_url(file_path):
    """Convert file path to URL."""
    rel_path = file_path.relative_to(ROOT)
    if rel_path.name == "index.html":
        return SITE_URL + '/' + str(rel_path.parent).replace('\\', '/') + '/'
    return SITE_URL + '/' + str(rel_path).replace('\\', '/')

def add_faq_schema(file_path, content):
    """Add FAQ schema to FAQ pages."""
    if 'faq' not in str(file_path).lower():
        return content, False

    # Extract FAQs from content (look for Q&A structure)
    faqs = []

    # Pattern: <h3>Question</h3><p>Answer</p>
    qa_pattern = r'<h[34][^>]*>([^<]+)</h[34]>\s*<p[^>]*>([^<]+)</p>'
    for match in re.finditer(qa_pattern, content, re.IGNORECASE):
        question = match.group(1).strip()
        answer = match.group(2).strip()
        if len(question) > 10 and len(answer) > 20:  # Only valid FAQs
            faqs.append({"question": question, "answer": answer})

    if not faqs:
        return content, False

    # Create FAQ schema
    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": faq["question"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": faq["answer"]
                }
            }
            for faq in faqs[:10]  # Limit to 10 FAQs
        ]
    }

    schema_json = json.dumps(faq_schema, ensure_ascii=True, separators=(',', ':'))
    script_tag = f'\n<script type="application/ld+json">{schema_json}</script>'

    # Insert before </head>
    head_match = re.search(r'(</head>)', content, re.IGNORECASE)
    if head_match and '{"@type":"FAQPage"' not in content:
        insert_pos = head_match.start(1)
        return content[:insert_pos] + script_tag + content[insert_pos:], True

    return content, False

def add_article_schema(file_path, content):
    """Enhance Article schema for article pages."""
    if not (re.search(r'articles/.*\.html', str(file_path)) or
            re.search(r'chapters/.*\.html', str(file_path)) or
            re.search(r'news/.*\.html', str(file_path))):
        return content, False

    if '{"@type":"Article"' in content:
        return content, False  # Already has article schema

    info = get_page_info(file_path, content)

    # Extract author and publication date if available
    author = "ITVedas"
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', str(file_path))
    publication_date = date_match.group(1) if date_match else datetime.now().isoformat()

    article_schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": info["title"],
        "description": info["description"],
        "image": info["image"],
        "datePublished": publication_date,
        "dateModified": publication_date,
        "author": {
            "@type": "Organization",
            "name": author
        },
        "publisher": {
            "@type": "Organization",
            "name": "ITVedas",
            "logo": {
                "@type": "ImageObject",
                "url": f"{SITE_URL}/assets/logo.svg"
            }
        }
    }

    schema_json = json.dumps(article_schema, ensure_ascii=True, separators=(',', ':'))
    script_tag = f'\n<script type="application/ld+json">{schema_json}</script>'

    # Insert before </head>
    head_match = re.search(r'(</head>)', content, re.IGNORECASE)
    if head_match:
        insert_pos = head_match.start(1)
        return content[:insert_pos] + script_tag + content[insert_pos:], True

    return content, False

def add_organization_schema(file_path, content):
    """Ensure homepage has Organization schema."""
    if file_path.name != "index.html" or "articles" in str(file_path):
        return content, False

    if '{"@type":"Organization"' in content:
        return content, False

    org_schema = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "ITVedas",
        "url": SITE_URL,
        "logo": f"{SITE_URL}/assets/logo.svg",
        "description": "The complete IT knowledge hub covering networking, cloud, security, DevOps, databases, Linux, hardware, and compliance",
        "sameAs": [
            "https://github.com/itvedas29/itvedas"
        ]
    }

    schema_json = json.dumps(org_schema, ensure_ascii=True, separators=(',', ':'))
    script_tag = f'\n<script type="application/ld+json">{schema_json}</script>'

    # Insert before </head>
    head_match = re.search(r'(</head>)', content, re.IGNORECASE)
    if head_match:
        insert_pos = head_match.start(1)
        return content[:insert_pos] + script_tag + content[insert_pos:], True

    return content, False

def process_file(file_path):
    """Process a single HTML file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        changed = False

        # Add FAQ schema if applicable
        content, faq_added = add_faq_schema(file_path, content)
        if faq_added:
            changed = True

        # Add/enhance Article schema
        content, article_added = add_article_schema(file_path, content)
        if article_added:
            changed = True

        # Add Organization schema if applicable
        content, org_added = add_organization_schema(file_path, content)
        if org_added:
            changed = True

        if changed and content != original:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"Error: {file_path}: {e}")
        return False

def main():
    """Add comprehensive schema to all pages."""
    faq_count = 0
    article_count = 0
    org_count = 0

    # Process FAQ pages
    for faq_file in (ROOT / ".").glob("faq.html"):
        if process_file(faq_file):
            faq_count += 1

    # Process articles
    for article_file in (ROOT / "articles").rglob("*.html"):
        if process_file(article_file):
            article_count += 1

    # Process chapters
    for chapter_file in (ROOT / "chapters").rglob("*.html"):
        if process_file(chapter_file):
            article_count += 1

    # Process homepage
    if process_file(ROOT / "index.html"):
        org_count += 1

    print(f"✓ Schema markup added:")
    print(f"  FAQ pages: {faq_count}")
    print(f"  Article pages: {article_count}")
    print(f"  Organization: {org_count}")
    return faq_count + article_count + org_count

if __name__ == "__main__":
    count = main()
    exit(0)
