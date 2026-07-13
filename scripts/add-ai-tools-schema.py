#!/usr/bin/env python3
"""
PHASE 6: Add schema markup for AI tools and knowledge hub.
Implement structured data for tool discovery and indexing.
"""

import pathlib
import json
import re

ROOT = pathlib.Path(".")

def add_ai_tools_collection_schema():
    """Add CollectionPage schema to AI tools index."""
    index_path = ROOT / "ai-tools" / "index.html"

    if not index_path.exists():
        return False

    try:
        content = index_path.read_text(encoding='utf-8')

        if '{"@type":"CollectionPage"' in content:
            return False

        schema = {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": "AI Tools & Frameworks Index",
            "description": "Comprehensive index of AI tools, machine learning frameworks, and data engineering platforms",
            "url": "https://itvedas.com/ai-tools/",
            "isPartOf": {
                "@type": "Website",
                "@id": "https://itvedas.com/"
            }
        }

        schema_json = json.dumps(schema, ensure_ascii=True, separators=(',', ':'))
        script_tag = f'\n<script type="application/ld+json">{schema_json}</script>'

        # Insert before </head>
        match = re.search(r'(</head>)', content, re.IGNORECASE)
        if match:
            insert_pos = match.start(1)
            new_content = content[:insert_pos] + script_tag + content[insert_pos:]
            index_path.write_text(new_content, encoding='utf-8')
            return True

        return False
    except Exception as e:
        return False

def add_tool_category_schema(file_path, category_title):
    """Add schema markup to individual tool category pages."""
    try:
        content = file_path.read_text(encoding='utf-8')

        if '{"@type":"CreativeWork"' in content:
            return False

        schema = {
            "@context": "https://schema.org",
            "@type": "CreativeWork",
            "name": category_title,
            "description": category_title,
            "mainEntity": {
                "@type": "ItemList",
                "itemListElement": []
            }
        }

        schema_json = json.dumps(schema, ensure_ascii=True, separators=(',', ':'))
        script_tag = f'\n<script type="application/ld+json">{schema_json}</script>'

        # Insert before </head>
        match = re.search(r'(</head>)', content, re.IGNORECASE)
        if match:
            insert_pos = match.start(1)
            new_content = content[:insert_pos] + script_tag + content[insert_pos:]
            file_path.write_text(new_content, encoding='utf-8')
            return True

        return False
    except Exception as e:
        return False

def main():
    """Add AI tools schema markup."""
    print("✓ Adding AI tools schema markup...")

    schema_count = 0

    # Add schema to main index
    if add_ai_tools_collection_schema():
        schema_count += 1
        print(f"  ✓ Collection schema added to AI tools index")

    # Add schema to category pages
    ai_tools_dir = ROOT / "ai-tools"
    if ai_tools_dir.exists():
        for tool_file in ai_tools_dir.glob("*.html"):
            if tool_file.name != "index.html":
                title = tool_file.stem.replace("-", " ").title()
                if add_tool_category_schema(tool_file, title):
                    schema_count += 1
                    print(f"  ✓ Schema added: {title}")

    print(f"\n✓ AI tools schema markup complete: {schema_count} pages")
    return schema_count

if __name__ == "__main__":
    count = main()
    exit(0)
