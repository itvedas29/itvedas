#!/usr/bin/env python3
"""
HTML Quality Validation Script
Validates HTML files for SEO, accessibility, and code quality issues.

Usage:
    python3 scripts/validate-html-quality.py
    python3 scripts/validate-html-quality.py --verbose
"""

import re
import sys
from pathlib import Path
from collections import defaultdict

ISSUES = defaultdict(list)

def validate_html_file(filepath):
    """Validate a single HTML file for quality issues."""
    content = filepath.read_text(encoding='utf-8', errors='ignore')
    relative_path = filepath.relative_to(Path('.'))

    # Check for DOCTYPE
    if not content.startswith('<!DOCTYPE'):
        ISSUES['missing-doctype'].append(str(relative_path))

    # Check for lang attribute
    if not re.search(r'<html[^>]*lang=', content):
        ISSUES['missing-lang-attr'].append(str(relative_path))

    # Check for charset
    if 'charset' not in content:
        ISSUES['missing-charset'].append(str(relative_path))

    # Check for viewport
    if 'viewport' not in content:
        ISSUES['missing-viewport'].append(str(relative_path))

    # Check for title
    if not re.search(r'<title>.*?</title>', content):
        ISSUES['missing-title'].append(str(relative_path))

    # Check for meta description
    if not re.search(r'<meta\s+name="description"', content):
        ISSUES['missing-description'].append(str(relative_path))

    # Check for proper link security
    target_blank_links = re.findall(r'<a[^>]*target="_blank"[^>]*>', content)
    for link in target_blank_links:
        if 'noopener' not in link or 'noreferrer' not in link:
            ISSUES['unsafe-external-links'].append(str(relative_path))
            break

    # Check for images without alt text
    images = re.findall(r'<img[^>]*>', content)
    for img in images:
        if 'alt=' not in img and 'src=' in img:
            ISSUES['missing-alt-text'].append(str(relative_path))
            break

    # Check for proper heading hierarchy
    headings = re.findall(r'<h([1-6])[^>]*>', content)
    if headings and headings[0] != '1':
        ISSUES['heading-hierarchy'].append(str(relative_path))

    # Check for duplicate IDs (basic check)
    ids = re.findall(r'id="([^"]*)"', content)
    if len(ids) != len(set(ids)):
        ISSUES['duplicate-ids'].append(str(relative_path))

    # Check for console.log statements in production
    if re.search(r'console\.log\s*\(', content):
        ISSUES['console-logs'].append(str(relative_path))

    # Check for inline styles (should use CSS)
    inline_styles = re.findall(r'<[^>]*style="[^"]*"', content)
    if len(inline_styles) > 5:
        ISSUES['excessive-inline-styles'].append(str(relative_path))

    # Check for malformed closing tags
    if re.search(r'</\s+[a-z]', content):
        ISSUES['malformed-closing-tags'].append(str(relative_path))

def main():
    """Main validation function."""
    # Find all HTML files
    html_files = list(Path('.').glob('**/*.html'))
    html_files = [f for f in html_files if '.git' not in str(f)]

    print(f"🔍 Validating {len(html_files)} HTML files...")

    for html_file in html_files:
        validate_html_file(html_file)

    # Print results
    if not ISSUES:
        print("✅ All HTML files passed validation!")
        return 0

    print(f"\n⚠️  Found {len(ISSUES)} types of issues:\n")

    total_files_affected = set()
    for issue_type, files in sorted(ISSUES.items()):
        print(f"  {issue_type}: {len(files)} file(s)")
        total_files_affected.update(files)
        if '--verbose' in sys.argv:
            for f in sorted(set(files))[:5]:
                print(f"    - {f}")
            if len(set(files)) > 5:
                print(f"    ... and {len(set(files)) - 5} more")

    print(f"\nTotal unique files affected: {len(total_files_affected)}")

    # Return non-zero if critical issues found
    critical_issues = [
        'unsafe-external-links',
        'missing-doctype',
        'missing-lang-attr',
        'duplicate-ids',
    ]

    has_critical = any(issue in ISSUES for issue in critical_issues)
    return 1 if has_critical else 0

if __name__ == '__main__':
    sys.exit(main())
