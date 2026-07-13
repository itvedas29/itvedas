#!/usr/bin/env python3
"""
Fix heading hierarchy issues across all pages.
Ensures proper H1-H6 hierarchy and structure for accessibility.
"""

import pathlib
import re
from collections import defaultdict

ROOT = pathlib.Path(".")

def analyze_headings(content):
    """Analyze heading structure and return issues."""
    headings = []
    for match in re.finditer(r'<h([1-6])[^>]*>(.*?)</h\1>', content, re.IGNORECASE | re.DOTALL):
        level = int(match.group(1))
        text = match.group(2).strip()[:50]
        headings.append((level, text))

    issues = []

    if not headings:
        return ["No headings found"]

    # Check if starts with H1
    if headings[0][0] != 1:
        issues.append(f"Page doesn't start with H1 (starts with H{headings[0][0]})")

    # Check for hierarchy jumps
    for i in range(1, len(headings)):
        prev_level = headings[i-1][0]
        curr_level = headings[i][0]

        if curr_level > prev_level + 1:
            issues.append(f"Level jump from H{prev_level} to H{curr_level} at position {i}")

    return issues if issues else ["No issues"]

def fix_heading_start(content):
    """Ensure page starts with H1 by adding one if missing."""
    # Check if content has H1
    if '<h1' not in content.lower():
        # Look for title in page for reference
        title_match = re.search(r'<title>([^<]+)</title>', content, re.IGNORECASE)
        if title_match:
            title = title_match.group(1)
            # Extract main title (before pipe or dash)
            main_title = title.split('|')[0].split('-')[0].strip()

            # Insert H1 after header opening or before first content
            body_match = re.search(r'(<body[^>]*>)', content, re.IGNORECASE)
            if body_match:
                insert_pos = body_match.end()
                # Find a good insertion point (after nav if exists)
                nav_match = re.search(r'</nav>', content[insert_pos:], re.IGNORECASE)
                if nav_match:
                    insert_pos = insert_pos + nav_match.end()

                h1_tag = f'\n<h1>{main_title}</h1>\n'
                content = content[:insert_pos] + h1_tag + content[insert_pos:]
                return content, True

    return content, False

def fix_hierarchy_jumps(content):
    """Fix heading hierarchy jumps."""
    # This is complex because we need to adjust many H tags
    # For now, just report them
    return content, False

def process_file(file_path):
    """Process a single HTML file for heading issues."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        changed = False

        # Analyze issues
        issues = analyze_headings(content)

        # Fix missing H1
        if any('no h1' in issue.lower() or "doesn't start with h1" in issue.lower() for issue in issues):
            content, fixed = fix_heading_start(content)
            if fixed:
                changed = True

        if changed and content != original:
            file_path.write_text(content, encoding='utf-8')
            return True, issues

        return False, issues
    except Exception as e:
        return False, [f"Error: {e}"]

def main():
    """Process all HTML files for heading hierarchy."""
    total = 0
    fixed = 0
    issues_found = defaultdict(list)

    # Process articles
    for article_file in (ROOT / "articles").rglob("*.html"):
        total += 1
        was_fixed, issues = process_file(article_file)
        if was_fixed:
            fixed += 1
        if any('no issue' not in str(i).lower() for i in issues):
            for issue in issues:
                if 'no issue' not in str(issue).lower():
                    issues_found[str(issue)].append(str(article_file))

    # Process chapters
    for chapter_file in (ROOT / "chapters").rglob("*.html"):
        total += 1
        was_fixed, issues = process_file(chapter_file)
        if was_fixed:
            fixed += 1
        if any('no issue' not in str(i).lower() for i in issues):
            for issue in issues:
                if 'no issue' not in str(issue).lower():
                    issues_found[str(issue)].append(str(chapter_file))

    print(f"✓ Heading hierarchy analysis complete")
    print(f"  Total files: {total}")
    print(f"  Fixed: {fixed}")
    print(f"\nRemaining issues to address manually:")
    for issue, files in sorted(issues_found.items()):
        print(f"  - {issue}: {len(files)} files")

    return fixed

if __name__ == "__main__":
    count = main()
    exit(0)
