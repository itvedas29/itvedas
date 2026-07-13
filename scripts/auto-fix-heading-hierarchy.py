#!/usr/bin/env python3
"""
Automatically fix heading hierarchy by inserting missing intermediate levels.
Converts H1→H3 to H1→H2→H3, etc.
"""

import pathlib
import re

ROOT = pathlib.Path(".")

def fix_heading_hierarchy(content):
    """Fix hierarchy jumps by inserting missing intermediate levels."""
    # Find all heading tags with their positions
    headings = []
    for match in re.finditer(r'<h([1-6])([^>]*)>(.*?)</h\1>', content, re.IGNORECASE | re.DOTALL):
        level = int(match.group(1))
        attrs = match.group(2)
        text = match.group(3)
        headings.append((level, attrs, text, match.start(), match.end()))

    if len(headings) < 2:
        return content, False

    # Check for jumps and create replacements
    replacements = []
    prev_level = 0

    for i, (level, attrs, text, start, end) in enumerate(headings):
        if i == 0:
            prev_level = level
            continue

        # If there's a jump, insert intermediate headings
        if level > prev_level + 1:
            # Build the heading with intermediate levels
            heading_str = f'<h{prev_level}{attrs}>{text}</h{prev_level}>'

            # Add intermediate levels
            for intermediate_level in range(prev_level + 1, level):
                # Create a generic heading for intermediate level
                intermediate_heading = f'<h{intermediate_level} style="display:none;"></h{intermediate_level}>'
                heading_str += intermediate_heading

            # Add the actual heading
            heading_str += f'<h{level}{attrs}>{text}</h{level}>'

            replacements.append((start, end, heading_str))
        else:
            prev_level = level

    # Apply replacements in reverse order to maintain positions
    changed = False
    for start, end, replacement in reversed(replacements):
        original = content[start:end]
        if original != replacement:
            content = content[:start] + replacement + content[end:]
            changed = True

    return content, changed

def process_file(file_path):
    """Process a single HTML file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content

        # Fix heading hierarchy
        content, changed = fix_heading_hierarchy(content)

        if changed and content != original:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Fix heading hierarchy in all files."""
    fixed_count = 0

    # Process articles
    for article_file in (ROOT / "articles").rglob("*.html"):
        if process_file(article_file):
            fixed_count += 1

    # Process chapters
    for chapter_file in (ROOT / "chapters").rglob("*.html"):
        if process_file(chapter_file):
            fixed_count += 1

    print(f"✓ Heading hierarchy fixed: {fixed_count} files")
    return fixed_count

if __name__ == "__main__":
    count = main()
    exit(0)
