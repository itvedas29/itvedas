#!/usr/bin/env python3
"""
PHASE 5: Optimize navigation structure and content discovery.
1. Create comprehensive breadcrumb navigation
2. Add category context pages
3. Improve navigation menus
4. Create topic clusters
"""

import pathlib
import re

ROOT = pathlib.Path(".")

def get_page_title(content):
    """Extract page title."""
    match = re.search(r'<title>([^<]+)</title>', content, re.IGNORECASE)
    if match:
        title = match.group(1).replace(' — ITVedas', '').strip()
        return title
    return "Untitled"

def enhance_breadcrumb_navigation(content, file_path):
    """Enhance existing breadcrumb with better structure."""
    changed = False

    # Check if breadcrumb already exists
    if '<!-- Breadcrumb Navigation -->' in content:
        return content, False

    # Determine breadcrumb structure based on file path
    parts = file_path.relative_to(ROOT).parts

    if len(parts) >= 3:
        root_section = parts[0]  # articles, chapters, news
        category = parts[1]  # cloud, networking, etc.
        page_name = parts[2].replace('.html', '').replace('-', ' ').title()

        # Generate breadcrumb navigation
        breadcrumb = f"""<!-- Breadcrumb Navigation -->
<nav aria-label="Breadcrumb" style="margin-bottom:2rem;font-size:0.9rem;">
<ol style="list-style:none;padding:0;display:flex;gap:0.5rem;">
<li><a href="/">Home</a></li>
<li>/</li>
<li><a href="/{root_section}/">{root_section.title()}</a></li>
<li>/</li>
<li><a href="/{root_section}/{category}/">{category.replace('-', ' ').title()}</a></li>
<li>/</li>
<li>{page_name}</li>
</ol>
</nav>
"""

        # Insert after <h1>
        match = re.search(r'(</h1>)', content, re.IGNORECASE)
        if match:
            insert_pos = match.end()
            content = content[:insert_pos] + breadcrumb + content[insert_pos:]
            changed = True

    return content, changed

def add_category_context(content, file_path):
    """Add context about the current category."""
    parts = file_path.relative_to(ROOT).parts

    if len(parts) < 2 or parts[0] not in ['articles', 'chapters']:
        return content, False

    category = parts[1]

    context = f"""<!-- Category Context -->
<div style="background:#f5f5f5;padding:1rem;margin:1rem 0;border-left:4px solid #0066cc;border-radius:0.25rem;">
<strong>Category:</strong> <a href="/{parts[0]}/{category}/" style="color:#0066cc;">{category.replace('-', ' ').title()}</a>
<br/><small>Browse more articles and resources in this category</small>
</div>
"""

    if '<!-- Category Context -->' not in content:
        # Insert before related articles or at end
        insert_pos = content.find('<!-- Related Articles -->')
        if insert_pos == -1:
            insert_pos = content.find('</article>')
            if insert_pos == -1:
                insert_pos = content.find('</body>')

        if insert_pos != -1:
            content = content[:insert_pos] + context + content[insert_pos:]
            return content, True

    return content, False

def process_file(file_path):
    """Process a single HTML file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        changed = False

        # Enhance breadcrumb
        content, bc_changed = enhance_breadcrumb_navigation(content, file_path)
        if bc_changed:
            changed = True

        # Add category context
        content, ctx_changed = add_category_context(content, file_path)
        if ctx_changed:
            changed = True

        if changed and content != original:
            file_path.write_text(content, encoding='utf-8')
            return True

        return False
    except Exception as e:
        return False

def main():
    """Optimize navigation across all pages."""
    optimized_count = 0

    # Process articles
    for article_file in (ROOT / "articles").rglob("*.html"):
        if article_file.name != "index.html":
            if process_file(article_file):
                optimized_count += 1

    # Process chapters
    for chapter_file in (ROOT / "chapters").rglob("*.html"):
        if chapter_file.name != "index.html":
            if process_file(chapter_file):
                optimized_count += 1

    print(f"✓ Navigation structure optimized: {optimized_count} pages")
    return optimized_count

if __name__ == "__main__":
    count = main()
    exit(0)
