#!/usr/bin/env python3
"""Add schema markup to remaining 18 pages"""

import json
import re
from pathlib import Path
from datetime import datetime

ROOT = Path(".")

PAGES_TO_UPDATE = [
    ("cve-dashboard-advanced.html", "SoftwareApplication"),
    ("cve-database-complete.html", "DataCatalog"),
    ("cve-listing.html", "SearchResultsPage"),
    ("problems-solutions.html", "CollectionPage"),
    ("tools/base64-encoder.html", "SoftwareApplication"),
    ("tools/cidr-calculator.html", "SoftwareApplication"),
    ("tools/dns-lookup.html", "SoftwareApplication"),
    ("tools/hash-generator.html", "SoftwareApplication"),
    ("tools/http-header-analyzer.html", "SoftwareApplication"),
    ("tools/json-formatter.html", "SoftwareApplication"),
    ("tools/jwt-decoder.html", "SoftwareApplication"),
    ("tools/markdown-preview.html", "SoftwareApplication"),
    ("tools/password-generator.html", "SoftwareApplication"),
    ("tools/ssl-certificate-info.html", "SoftwareApplication"),
    ("tools/whois-lookup.html", "SoftwareApplication"),
    ("tools/xml-formatter.html", "SoftwareApplication"),
    ("tools/yaml-formatter.html", "SoftwareApplication"),
    ("tools/yara-rule-validator.html", "SoftwareApplication"),
]

def extract_title_and_desc(content):
    """Extract title and description from HTML"""
    title_match = re.search(r'<title>([^<]+)</title>', content)
    title = title_match.group(1) if title_match else "Page"
    
    desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content)
    description = desc_match.group(1) if desc_match else title
    
    return title, description

def add_schema(html_content, file_path, schema_type):
    """Add appropriate schema based on type"""
    if 'application/ld+json' in html_content:
        return html_content, False
    
    title, description = extract_title_and_desc(html_content)
    url = f"https://www.itvedas.com/{file_path}".replace('.html', '/')
    
    if schema_type == "SoftwareApplication":
        schema = {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": title,
            "description": description,
            "url": url,
            "applicationCategory": "UtilityApplication",
            "operatingSystem": "Web"
        }
    elif schema_type == "DataCatalog":
        schema = {
            "@context": "https://schema.org",
            "@type": "DataCatalog",
            "name": title,
            "description": description,
            "url": url
        }
    elif schema_type == "SearchResultsPage":
        schema = {
            "@context": "https://schema.org",
            "@type": "SearchResultsPage",
            "name": title,
            "description": description,
            "url": url
        }
    elif schema_type == "CollectionPage":
        schema = {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": title,
            "description": description,
            "url": url
        }
    else:
        schema = {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": title,
            "description": description,
            "url": url
        }
    
    schema_tag = f'<script type="application/ld+json">\n{json.dumps(schema, indent=2)}\n</script>'
    
    if '</body>' in html_content:
        html_content = html_content.replace('</body>', f'{schema_tag}\n</body>')
        return html_content, True
    
    return html_content, False

# Apply schema to remaining pages
updated = 0
skipped = 0

print("\n" + "="*70)
print("🔧 ADDING SCHEMA MARKUP TO REMAINING 18 PAGES")
print("="*70 + "\n")

for file_path, schema_type in PAGES_TO_UPDATE:
    full_path = ROOT / file_path
    
    if not full_path.exists():
        print(f"❌ {file_path} - FILE NOT FOUND")
        skipped += 1
        continue
    
    try:
        content = full_path.read_text(encoding='utf-8')
        new_content, was_added = add_schema(content, file_path, schema_type)
        
        if was_added:
            full_path.write_text(new_content, encoding='utf-8')
            print(f"✅ {file_path} - Added {schema_type}")
            updated += 1
        else:
            print(f"⏭️  {file_path} - Already has schema or no </body>")
            skipped += 1
    except Exception as e:
        print(f"❌ {file_path} - Error: {e}")
        skipped += 1

print("\n" + "="*70)
print(f"✅ Updated: {updated} pages")
print(f"⏭️  Skipped: {skipped} pages")
print(f"📊 Total: {updated + skipped} pages")
print("="*70 + "\n")
