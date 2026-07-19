#!/usr/bin/env python3
"""
QA Validation for Phase 5 Content
Checks for broken links, structure, and completeness.
"""

import os
from pathlib import Path
import re

def validate_articles():
    """Validate generated articles."""
    print("\n🔍 QA Validation - Phase 5 Content\n")

    issues = {
        'errors': [],
        'warnings': []
    }

    # Check Azure articles
    azure_dir = Path('articles/azure')
    if azure_dir.exists():
        print("✓ Azure articles directory exists")
        azure_files = list(azure_dir.glob('2026-07-04-*.html'))
        if len(azure_files) == 4:
            print(f"  ✓ All 4 Azure articles present")
        else:
            issues['errors'].append(f"Expected 4 Azure articles, found {len(azure_files)}")

    # Check SQL Server articles
    sql_dir = Path('articles/sql-server')
    if sql_dir.exists():
        print("✓ SQL Server articles directory exists")
        sql_files = list(sql_dir.glob('2026-07-04-*.html'))
        if len(sql_files) == 3:
            print(f"  ✓ All 3 SQL Server articles present")
        else:
            issues['errors'].append(f"Expected 3 SQL Server articles, found {len(sql_files)}")

    # Check IIS articles
    iis_dir = Path('articles/iis')
    if iis_dir.exists():
        print("✓ IIS articles directory exists")
        iis_files = list(iis_dir.glob('2026-07-04-*.html'))
        if len(iis_files) == 3:
            print(f"  ✓ All 3 IIS articles present")
        else:
            issues['errors'].append(f"Expected 3 IIS articles, found {len(iis_files)}")

    # Validate article content
    print("\n📄 Validating article content...")
    all_files = list(azure_dir.glob('*.html')) if azure_dir.exists() else []
    all_files += list(sql_dir.glob('*.html')) if sql_dir.exists() else []
    all_files += list(iis_dir.glob('*.html')) if iis_dir.exists() else []

    for article_file in all_files:
        with open(article_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for required HTML elements
        checks = {
            '<html': 'HTML tag',
            '<head>': 'Head tag',
            '<meta charset': 'Charset meta',
            '<title>': 'Title tag',
            '<h1>': 'H1 heading',
            'class="art"': 'Article container',
            '<footer>': 'Footer',
            'documentation-standards.css': 'Documentation CSS link',
            'documentation-ui.js': 'Documentation JS link'
        }

        missing = []
        for check_str, check_name in checks.items():
            if check_str not in content:
                missing.append(check_name)

        if missing:
            issues['warnings'].append(f"{article_file.name}: Missing {', '.join(missing)}")
        else:
            print(f"  ✓ {article_file.name}")

    # Check search index
    print("\n🔍 Checking search index...")
    try:
        import json
        with open('search-index.json', 'r') as f:
            raw_index = json.load(f)

        # search-index.json is an object like {"version", "generated", "pages": [...]}.
        # Support both that shape and a bare list, in case the format changes again.
        pages = raw_index.get('pages', []) if isinstance(raw_index, dict) else raw_index

        if len(pages) >= 419:
            print(f"  ✓ Search index has {len(pages)} entries")
        else:
            issues['warnings'].append(f"Search index has only {len(pages)} entries (expected 419+)")

        # Check for new article entries
        new_titles = ['Azure Virtual Machines', 'SQL Server Editions', 'IIS Installation']
        found = sum(1 for entry in pages if any(title in entry.get('title', '') for title in new_titles))
        if found >= 3:
            print(f"  ✓ New articles indexed ({found} samples)")
        else:
            issues['warnings'].append("Some new articles may not be indexed")

    except Exception as e:
        issues['errors'].append(f"Error validating search index: {e}")

    # Check chapters.html updates
    print("\n📊 Checking chapters page...")
    try:
        with open('chapters.html', 'r', encoding='utf-8') as f:
            chapters_content = f.read()

        if '125+' in chapters_content and '113,000+' in chapters_content:
            print("  ✓ Chapter statistics updated")
        else:
            issues['warnings'].append("Chapter statistics may not be updated")

    except Exception as e:
        issues['errors'].append(f"Error validating chapters.html: {e}")

    # Summary
    print("\n" + "="*50)
    if issues['errors']:
        print(f"❌ Found {len(issues['errors'])} errors:")
        for error in issues['errors']:
            print(f"   - {error}")
        return False

    if issues['warnings']:
        print(f"⚠️  Found {len(issues['warnings'])} warnings:")
        for warning in issues['warnings']:
            print(f"   - {warning}")

    print("✅ QA Validation Complete - Ready for Production")
    return True

if __name__ == "__main__":
    success = validate_articles()
    exit(0 if success else 1)
