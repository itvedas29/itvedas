#!/usr/bin/env python3
"""
IT Vedas Search Index Generator
Automatically generates search-index.json from HTML files
Extracts metadata, keywords, and structured data for search functionality
"""

import json
import os
import re
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import quote

class SearchIndexExtractor(HTMLParser):
    """Extracts SEO metadata and structured data from HTML"""
    def __init__(self):
        super().__init__()
        self.title = None
        self.description = None
        self.keywords = None
        self.og_title = None
        self.og_description = None
        self.json_ld = []
        self.topic = None
        self.article_section = None
        self.current_script_type = None
        self.in_script = False
        self.script_content = ""
        self.current_tag = None

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == 'title':
            self.current_tag = 'title'
        elif tag == 'meta':
            name = attrs_dict.get('name', '').lower()
            prop = attrs_dict.get('property', '').lower()
            content = attrs_dict.get('content', '').strip()

            if name == 'description':
                self.description = content
            elif name == 'keywords':
                self.keywords = content
            elif prop == 'og:title':
                self.og_title = content
            elif prop == 'og:description':
                self.og_description = content
        elif tag == 'script':
            script_type = attrs_dict.get('type', '')
            if script_type == 'application/ld+json':
                self.in_script = True
                self.current_script_type = 'json-ld'
                self.script_content = ""

    def handle_data(self, data):
        if self.current_tag == 'title' and hasattr(self, 'current_tag'):
            self.title = data.strip()
        elif self.in_script:
            self.script_content += data

    def handle_endtag(self, tag):
        if tag == 'title' and hasattr(self, 'current_tag'):
            self.current_tag = None
        elif tag == 'script' and self.in_script:
            if self.script_content.strip():
                try:
                    data = json.loads(self.script_content)
                    self.json_ld.append(data)

                    # Extract topic from Article schema
                    if isinstance(data, dict):
                        if data.get('@type') == 'Article':
                            self.article_section = data.get('articleSection')
                except json.JSONDecodeError:
                    pass
            self.in_script = False
            self.current_script_type = None
            self.script_content = ""

    def extract_topic(self):
        """Extract topic from various sources"""
        if self.article_section:
            return self.article_section

        # Try to infer from title keywords
        keywords_map = {
            'networking': 'Networking',
            'cloud': 'Cloud',
            'security': 'Security',
            'devops': 'DevOps',
            'databases': 'Databases',
            'linux': 'Linux',
            'hardware': 'Hardware',
            'active directory': 'Active Directory',
            'kubernetes': 'Kubernetes',
            'docker': 'Docker',
            'aws': 'AWS',
            'azure': 'Azure',
            'firewall': 'Security',
            'encryption': 'Security',
            'cve': 'CVE Database',
            'vulnerability': 'CVE Database',
        }

        search_text = (self.title or '') + ' ' + (self.keywords or '')
        search_text_lower = search_text.lower()

        for keyword, topic in keywords_map.items():
            if keyword in search_text_lower:
                return topic

        return "General"


def extract_metadata_from_html(filepath):
    """Extract metadata from a single HTML file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        extractor = SearchIndexExtractor()
        extractor.feed(content)

        title = extractor.og_title or extractor.title or ""
        description = extractor.og_description or extractor.description or ""
        keywords = extractor.keywords or ""
        topic = extractor.extract_topic()

        if not title or not description:
            return None

        # Get relative file path
        rel_path = os.path.relpath(filepath, '/home/user/itvedas')

        return {
            'title': title,
            'description': description,
            'topic': topic,
            'file': rel_path,
            'keyword': keywords,
        }
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return None


def should_include_file(filepath):
    """Determine if file should be indexed"""
    # Exclude certain directories
    exclude_patterns = [
        'venv/',
        'node_modules/',
        'dashboard/',
        '__pycache__',
        '.git/',
        'dist/',
    ]

    for pattern in exclude_patterns:
        if pattern in filepath:
            return False

    # Only include main content directories and root HTML files
    include_patterns = [
        'articles/',
        'news/',
        'chapters/',
        'cve-listing.html',
        'cve-detail.html',
        'chapters.html',
        'about.html',
        'index.html',
    ]

    return any(pattern in filepath for pattern in include_patterns)


def generate_search_index():
    """Generate search index from all HTML files"""
    root_path = '/home/user/itvedas'
    entries = []

    print("🔍 Scanning HTML files for search index...")

    # Scan all HTML files
    for filepath in Path(root_path).rglob('*.html'):
        filepath_str = str(filepath)

        if not should_include_file(filepath_str):
            continue

        print(f"  Processing: {filepath_str}")
        metadata = extract_metadata_from_html(filepath_str)

        if metadata:
            entries.append(metadata)

    # Sort entries: index first, then other pages, then articles, then news
    def sort_key(entry):
        file = entry['file']
        if file == 'index.html':
            return (0, file)
        elif 'chapters' in file or 'about' in file or 'cve-' in file:
            return (1, file)
        elif 'articles/' in file:
            return (2, file)
        else:
            return (3, file)

    entries.sort(key=sort_key)

    # Write search index
    index_path = os.path.join(root_path, 'search-index.json')
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Search index generated: {len(entries)} entries")
    print(f"   Saved to: {index_path}")

    return entries


if __name__ == '__main__':
    generate_search_index()
