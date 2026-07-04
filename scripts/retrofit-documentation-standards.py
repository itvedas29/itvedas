#!/usr/bin/env python3
"""
Retrofit documentation standards to existing articles.
Adds: difficulty badges, reading time, prerequisites, copy buttons, collapsible sections.
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime

# Configuration
ARTICLES_DIR = Path("articles")
ARTICLE_METADATA = {
    # CVE articles - Advanced difficulty
    "cve": {
        "difficulty": "advanced",
        "prerequisites": ["Basic cybersecurity knowledge", "Understanding of vulnerabilities"]
    },
    # Cloud articles - Intermediate
    "cloud": {
        "difficulty": "intermediate",
        "prerequisites": ["Basic IT knowledge", "Understanding of networking"]
    },
    # Security articles - Intermediate to Advanced
    "security": {
        "difficulty": "intermediate",
        "prerequisites": ["Basic IT knowledge", "Familiarity with security concepts"]
    },
    # Networking articles - Intermediate
    "networking": {
        "difficulty": "intermediate",
        "prerequisites": ["Basic networking concepts", "Understanding of OSI model"]
    },
    # DevOps articles - Advanced
    "devops": {
        "difficulty": "advanced",
        "prerequisites": ["Linux fundamentals", "Understanding of CI/CD concepts"]
    },
    # Linux articles - Intermediate
    "linux": {
        "difficulty": "intermediate",
        "prerequisites": ["Basic command line knowledge"]
    },
    # Databases articles - Intermediate
    "databases": {
        "difficulty": "intermediate",
        "prerequisites": ["Understanding of SQL basics"]
    },
    # Compliance articles - Advanced
    "compliance": {
        "difficulty": "advanced",
        "prerequisites": ["Enterprise IT knowledge", "Regulatory framework familiarity"]
    },
    # Hardware articles - Beginner
    "hardware": {
        "difficulty": "beginner",
        "prerequisites": ["Basic computer knowledge"]
    }
}

CSS_LINK = '<link rel="stylesheet" href="/css/documentation-standards.css">'
JS_SCRIPT = '<script src="/js/documentation-ui.js"><\/script>'

def extract_reading_time(content):
    """Extract reading time from hero-meta or calculate from article content."""
    match = re.search(r'<span>(\d+)\s*min\s*read<\/span>', content)
    if match:
        return int(match.group(1))

    # Calculate from word count
    text = re.sub(r'<[^>]+>', '', content)
    words = len(text.split())
    return max(1, words // 200)  # ~200 words per minute

def get_difficulty(filepath):
    """Determine difficulty level based on article path."""
    path_str = str(filepath)
    for category, config in ARTICLE_METADATA.items():
        if f"/{category}/" in path_str:
            return config["difficulty"], config["prerequisites"]
    # Default for root articles
    return "intermediate", ["Basic IT knowledge"]

def inject_css(content):
    """Inject documentation standards CSS if not present."""
    if "documentation-standards.css" in content:
        return content

    # Find </head> and inject before it
    if "</head>" in content:
        return content.replace("</head>", f"  {CSS_LINK}\n</head>")
    return content

def inject_js(content):
    """Inject documentation standards JS if not present."""
    if "documentation-ui.js" in content:
        return content

    # Find </body> and inject before it
    if "</body>" in content:
        return content.replace("</body>", f"  {JS_SCRIPT}\n</body>")
    return content

def add_metadata_section(content, difficulty, prerequisites, reading_time):
    """Add documentation metadata section after hero section."""
    metadata_html = f"""  <div class="doc-metadata">
    <div class="difficulty-badge difficulty-{difficulty}">{difficulty.upper()}</div>
    <div class="reading-time">⏱ {reading_time} min read</div>
    <div class="prerequisites">
      <strong>Prerequisites:</strong>
      <ul>
        {"".join(f"<li>{p}</li>" for p in prerequisites)}
      </ul>
    </div>
  </div>"""

    # Insert after .hero div or after hero-meta
    if '<div class="wrap">' in content:
        return content.replace('<div class="wrap">', metadata_html + '\n<div class="wrap">', 1)

    return content

def add_copy_buttons_to_code(content):
    """Add copy-to-clipboard buttons to code blocks."""
    if ".copy-code-button" in content:
        return content  # Already has copy buttons

    # Wrap pre tags and add copy button
    def wrap_code_block(match):
        pre_content = match.group(0)
        wrapper = f'<div class="code-block-wrapper">{pre_content}<button class="copy-code-button" onclick="copyCode(this)">📋 Copy</button></div>'
        return wrapper

    content = re.sub(r'<pre>.*?<\/pre>', wrap_code_block, content, flags=re.DOTALL)
    return content

def create_reading_progress_bar(content):
    """Add reading progress bar if not present."""
    if 'id="prog"' in content or 'reading-progress-bar' in content:
        return content

    # Find first tag after <body> and inject progress bar
    body_match = re.search(r'<body[^>]*>', content)
    if body_match:
        insert_pos = body_match.end()
        bar = '<div class="reading-progress-bar" id="readingProgress"></div>'
        content = content[:insert_pos] + f'\n  {bar}\n' + content[insert_pos:]

    return content

def retrofit_article(filepath):
    """Retrofit a single article with documentation standards."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Skip if already retrofitted
        if "doc-metadata" in content and "documentation-standards.css" in content:
            return True, "Already retrofitted"

        # Get metadata
        difficulty, prerequisites = get_difficulty(filepath)
        reading_time = extract_reading_time(content)

        # Apply retrofits
        content = inject_css(content)
        content = inject_js(content)
        content = add_metadata_section(content, difficulty, prerequisites, reading_time)
        content = create_reading_progress_bar(content)

        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return True, f"✓ Retrofitted ({difficulty}, {reading_time}m)"

    except Exception as e:
        return False, f"✗ Error: {str(e)}"

def main():
    """Retrofit all articles in ARTICLES_DIR."""
    print("\n🔧 Retrofitting documentation standards to all articles...\n")

    article_files = sorted(ARTICLES_DIR.rglob("*.html"))
    hub_files = [f for f in article_files if f.name == "index.html"]
    article_files = [f for f in article_files if f.name != "index.html"]

    # Filter out hub pages
    article_files = [f for f in article_files if "/index.html" not in str(f)]

    print(f"Found {len(article_files)} articles to retrofit\n")

    success_count = 0
    failed_count = 0

    for i, filepath in enumerate(article_files, 1):
        relative_path = filepath.relative_to(".")
        success, message = retrofit_article(filepath)

        status = "✓" if success else "✗"
        print(f"[{i:2d}/{len(article_files)}] {status} {relative_path}: {message}")

        if success:
            success_count += 1
        else:
            failed_count += 1

    print(f"\n📊 Summary: {success_count} retrofitted, {failed_count} failed\n")
    return failed_count == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
