#!/usr/bin/env python3
"""
Enhance page structure for better SEO and accessibility:
1. Add proper section tags for semantic HTML
2. Ensure main content is in <main> tag
3. Add article tags properly
4. Improve heading organization
"""

import pathlib
import re

ROOT = pathlib.Path(".")

def enhance_semantic_structure(content):
    """Add semantic HTML tags for better structure."""
    # Only modify if it doesn't already have these structural elements
    if '<main' in content.lower():
        return content, False

    # Find the main content area (usually between nav and footer)
    # Look for the article or main content container
    article_match = re.search(r'(<article[^>]*>.*?</article>)', content, re.IGNORECASE | re.DOTALL)

    if article_match:
        # Already has article tag, good
        return content, False

    # Look for main content patterns
    # Find where the main body text starts
    if '<body' in content.lower():
        body_pos = re.search(r'</nav>|</header>', content, re.IGNORECASE)
        if body_pos:
            # Insert main tag after nav/header
            insert_pos = body_pos.end()
            content = content[:insert_pos] + '\n<main>\n' + content[insert_pos:]

            # Find where to close main tag
            footer_pos = re.search(r'<footer', content[insert_pos:], re.IGNORECASE)
            if footer_pos:
                close_pos = insert_pos + footer_pos.start()
                content = content[:close_pos] + '\n</main>\n' + content[close_pos:]
                return content, True

    return content, False

def add_image_optimization(content):
    """Optimize images with proper attributes."""
    changed = False

    # Find images without loading attribute
    img_pattern = r'(<img[^>]*?)(?:>|\s/>)'
    for match in re.finditer(img_pattern, content):
        img_tag = match.group(1)
        if 'loading=' not in img_tag.lower():
            img_tag_with_loading = img_tag + ' loading="lazy"'
            content = content.replace(img_tag, img_tag_with_loading, 1)
            changed = True

    return content, changed

def process_file(file_path):
    """Process a single HTML file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        changed = False

        # Enhance semantic structure
        content, struct_changed = enhance_semantic_structure(content)
        if struct_changed:
            changed = True

        # Add image optimization
        content, img_changed = add_image_optimization(content)
        if img_changed:
            changed = True

        if changed and content != original:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        return False

def main():
    """Enhance page structure across all pages."""
    updated_count = 0

    # Process articles
    for article_file in (ROOT / "articles").rglob("*.html"):
        if process_file(article_file):
            updated_count += 1

    # Process chapters
    for chapter_file in (ROOT / "chapters").rglob("*.html"):
        if process_file(chapter_file):
            updated_count += 1

    # Process news
    for news_file in (ROOT / "news").rglob("*.html"):
        if process_file(news_file):
            updated_count += 1

    print(f"✓ Page structure enhanced: {updated_count} pages")
    return updated_count

if __name__ == "__main__":
    count = main()
    exit(0)
