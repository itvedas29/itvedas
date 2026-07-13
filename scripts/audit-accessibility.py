#!/usr/bin/env python3
"""
Accessibility audit for ITVedas
Checks for WCAG 2.1 AA compliance issues
"""

import pathlib
import re
from collections import defaultdict

ROOT = pathlib.Path(".")

def check_alt_text(content):
    """Check for images without alt text."""
    missing = []
    img_pattern = r'<img[^>]*src=["\']([^"\']+)["\'][^>]*>'
    for match in re.finditer(img_pattern, content, re.IGNORECASE):
        img_tag = match.group(0)
        if 'alt=' not in img_tag.lower():
            missing.append(match.group(1))
    return missing

def check_heading_hierarchy(content):
    """Check for proper heading hierarchy."""
    headings = []
    for match in re.finditer(r'<h([1-6]).*?>(.*?)</h\1>', content, re.IGNORECASE | re.DOTALL):
        level = int(match.group(1))
        text = match.group(2)[:50]  # First 50 chars
        headings.append((level, text))

    issues = []
    for i, (level, text) in enumerate(headings):
        if i == 0 and level != 1:
            issues.append(f"Page doesn't start with H1 (starts with H{level})")
            break
        if i > 0:
            prev_level = headings[i-1][0]
            if level > prev_level + 1:
                issues.append(f"Heading level jump from H{prev_level} to H{level}")

    return issues

def check_link_text(content):
    """Check for links with poor accessibility."""
    issues = []
    # Find links with only generic text
    generic_texts = ['click here', 'read more', 'link', 'here', 'more']
    for match in re.finditer(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', content, re.IGNORECASE | re.DOTALL):
        link_text = match.group(2).strip().lower()
        if link_text in generic_texts:
            issues.append(f"Generic link text: '{link_text}'")

    return issues

def check_form_labels(content):
    """Check for form inputs without labels."""
    issues = []
    # Find input elements
    for match in re.finditer(r'<input[^>]*(?:name|id)=["\']([^"\']*)["\'][^>]*>', content, re.IGNORECASE):
        name = match.group(1)
        # Check if there's an associated label
        if f'for="{name}"' not in content and f"for='{name}'" not in content:
            issues.append(f"Input '{name}' has no associated label")

    return issues

def check_color_contrast_mentions(content):
    """Look for potential color contrast issues (basic check)."""
    # This is a simplified check - real contrast checking requires visual rendering
    if 'color: #fff' in content or 'color: white' in content.lower():
        if 'background: #' in content or 'background-color: #' in content:
            return ["Potential color contrast issue detected (manual review needed)"]
    return []

def audit_file(file_path):
    """Audit a single HTML file for accessibility."""
    try:
        content = file_path.read_text(encoding='utf-8')
        issues = {}

        # Check various accessibility aspects
        alt_missing = check_alt_text(content)
        if alt_missing:
            issues['missing_alt_text'] = alt_missing

        heading_issues = check_heading_hierarchy(content)
        if heading_issues:
            issues['heading_issues'] = heading_issues

        link_issues = check_link_text(content)
        if link_issues:
            issues['generic_links'] = link_issues

        form_issues = check_form_labels(content)
        if form_issues:
            issues['form_labels'] = form_issues

        contrast_issues = check_color_contrast_mentions(content)
        if contrast_issues:
            issues['contrast'] = contrast_issues

        return issues if issues else None
    except Exception as e:
        return {'error': str(e)}

def main():
    """Audit all HTML files for accessibility."""
    results = defaultdict(list)
    total_files = 0
    issues_found = 0

    # Audit articles
    for article_file in (ROOT / "articles").rglob("*.html"):
        total_files += 1
        audit_result = audit_file(article_file)
        if audit_result:
            results[str(article_file)] = audit_result
            issues_found += 1

    # Audit chapters
    for chapter_file in (ROOT / "chapters").rglob("*.html"):
        total_files += 1
        audit_result = audit_file(chapter_file)
        if audit_result:
            results[str(chapter_file)] = audit_result
            issues_found += 1

    # Report results
    print(f"=== Accessibility Audit Results ===")
    print(f"Total files audited: {total_files}")
    print(f"Files with potential issues: {issues_found}")
    print()

    if issues_found > 0:
        print("Top issues to address:")
        issue_counts = defaultdict(int)
        for file_issues in results.values():
            for issue_type in file_issues.keys():
                issue_counts[issue_type] += 1

        for issue_type, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {issue_type}: {count} files")

    return {
        'total_files': total_files,
        'files_with_issues': issues_found,
        'details': results
    }

if __name__ == "__main__":
    result = main()
    exit(0)
