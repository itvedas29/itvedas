#!/usr/bin/env python3
"""
Add schema markup to main content pages.
"""

import json
import re
from pathlib import Path
from datetime import datetime


def add_article_schema_to_file(file_path, title, description, url_path):
    """Add ArticleSchema to a file"""
    html_content = file_path.read_text()

    # Skip if already has schema
    if 'application/ld+json' in html_content:
        return False

    url = f"https://www.itvedas.com{url_path}"

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
        "datePublished": "2026-07-17T00:00:00Z",
        "dateModified": datetime.now().isoformat()
    }

    schema_tag = f'<script type="application/ld+json">\n{json.dumps(article_schema, indent=2)}\n</script>'

    # Insert before closing body tag
    if '</body>' in html_content:
        html_content = html_content.replace('</body>', f'{schema_tag}\n</body>')
        file_path.write_text(html_content)
        return True

    return False


def add_breadcrumb_to_file(file_path, breadcrumbs):
    """Add BreadcrumbSchema to a file"""
    html_content = file_path.read_text()

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
        file_path.write_text(html_content)
        return True

    return False


# Main pages to update
pages_to_update = [
    {
        "file": "problems-solutions.html",
        "title": "IT Problems & Solutions — Complete Troubleshooting Guide",
        "description": "Find solutions to 200+ common IT problems across networking, security, cloud, DevOps, databases, Linux and more. Step-by-step fixes with commands and examples.",
        "url": "/problems-solutions.html",
        "breadcrumbs": [
            ("Home", "https://www.itvedas.com"),
            ("Problems & Solutions", "https://www.itvedas.com/problems-solutions.html")
        ]
    },
    {
        "file": "quiz.html",
        "title": "IT Career Path Quiz — Find Your Perfect Tech Job",
        "description": "Take the IT career path quiz to discover which technology career is right for you. Get personalized recommendations based on your interests and skills.",
        "url": "/quiz.html",
        "breadcrumbs": [
            ("Home", "https://www.itvedas.com"),
            ("Career Quiz", "https://www.itvedas.com/quiz.html")
        ]
    },
    {
        "file": "cve-database-complete.html",
        "title": "Complete CVE Vulnerability Database | IT Vedas",
        "description": "Complete CVE Vulnerability Database - Search and learn from thousands of documented vulnerabilities with detailed remediation guidance.",
        "url": "/cve-database-complete.html",
        "breadcrumbs": [
            ("Home", "https://www.itvedas.com"),
            ("CVE Database", "https://www.itvedas.com/cve-database-complete.html")
        ]
    },
    {
        "file": "cve-listing.html",
        "title": "CVE Vulnerability Database & Security Advisories",
        "description": "Browse and search the CVE vulnerability database with CVSS scores, severity ratings, and security advisories.",
        "url": "/cve-listing.html",
        "breadcrumbs": [
            ("Home", "https://www.itvedas.com"),
            ("CVE Listing", "https://www.itvedas.com/cve-listing.html")
        ]
    }
]

# Process main pages
updated = 0
for page_config in pages_to_update:
    file_path = Path(f"/home/user/itvedas/{page_config['file']}")

    if not file_path.exists():
        print(f"✗ Not found: {page_config['file']}")
        continue

    # Add article schema
    if add_article_schema_to_file(
        file_path,
        page_config['title'],
        page_config['description'],
        page_config['url']
    ):
        print(f"✓ Added schema to: {page_config['file']}")
        updated += 1
    else:
        print(f"- Already has schema: {page_config['file']}")

print(f"\n{updated} main pages updated with schema markup")
