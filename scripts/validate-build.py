#!/usr/bin/env python3
"""
IT Vedas Build Validation Script
Validates HTML, links, meta tags, and SEO compliance
"""

import json
import os
import sys
import re
from pathlib import Path
from urllib.parse import urljoin
from html.parser import HTMLParser

class MetaTagValidator(HTMLParser):
    """Validates meta tags and SEO elements"""
    def __init__(self):
        super().__init__()
        self.meta_tags = {}
        self.title = None
        self.canonical = None
        self.og_tags = {}
        self.twitter_tags = {}
        self.json_ld = []
        self.images = []
        self.links = []
        self.headings = []
        self.current_tag = None
        self.issues = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == 'title':
            self.current_tag = 'title'
        elif tag == 'meta':
            name = attrs_dict.get('name', '')
            prop = attrs_dict.get('property', '')
            content = attrs_dict.get('content', '')

            if name:
                self.meta_tags[name] = content
                if name.startswith('og:'):
                    self.og_tags[name] = content
                elif name.startswith('twitter:'):
                    self.twitter_tags[name] = content
            if prop:
                if prop.startswith('og:'):
                    self.og_tags[prop] = content
                if prop == 'og:image':
                    pass  # Track separately if needed
        elif tag == 'link':
            if attrs_dict.get('rel') == 'canonical':
                self.canonical = attrs_dict.get('href', '')
            if attrs_dict.get('rel') == 'stylesheet':
                self.links.append(attrs_dict.get('href', ''))
        elif tag == 'script':
            if attrs_dict.get('type') == 'application/ld+json':
                self.current_tag = 'json-ld'
        elif tag == 'img':
            self.images.append({
                'src': attrs_dict.get('src', ''),
                'alt': attrs_dict.get('alt', ''),
            })
        elif tag in ['a']:
            self.links.append(attrs_dict.get('href', ''))
        elif tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            self.current_tag = tag

    def handle_data(self, data):
        if self.current_tag == 'title':
            self.title = data.strip()
        elif self.current_tag == 'json-ld':
            try:
                self.json_ld.append(json.loads(data))
            except json.JSONDecodeError:
                self.issues.append(f"Invalid JSON-LD: {data[:50]}...")
        elif self.current_tag and self.current_tag.startswith('h'):
            self.headings.append({'tag': self.current_tag, 'text': data.strip()})

    def handle_endtag(self, tag):
        if tag == self.current_tag:
            self.current_tag = None

    def validate(self):
        """Perform SEO validations"""
        issues = []

        # Check title
        if not self.title:
            issues.append("❌ Missing <title> tag")
        elif len(self.title) < 30:
            issues.append(f"⚠️  Title too short ({len(self.title)}): '{self.title}'")
        elif len(self.title) > 60:
            issues.append(f"⚠️  Title too long ({len(self.title)}): '{self.title}'")
        else:
            issues.append(f"✓ Title OK ({len(self.title)} chars)")

        # Check description
        if 'description' not in self.meta_tags:
            issues.append("❌ Missing meta description")
        else:
            desc = self.meta_tags['description']
            if len(desc) < 50:
                issues.append(f"⚠️  Description too short ({len(desc)})")
            elif len(desc) > 160:
                issues.append(f"⚠️  Description too long ({len(desc)})")
            else:
                issues.append(f"✓ Description OK ({len(desc)} chars)")

        # Check canonical
        if self.canonical:
            if self.canonical.startswith('#') or self.canonical == '':
                issues.append("⚠️  Empty or placeholder canonical URL")
            else:
                issues.append(f"✓ Canonical URL present")
        else:
            issues.append("⚠️  Missing canonical URL")

        # Check OpenGraph
        og_required = ['og:title', 'og:description', 'og:image']
        for tag in og_required:
            if tag not in self.og_tags or not self.og_tags[tag]:
                issues.append(f"❌ Missing {tag}")
            else:
                issues.append(f"✓ {tag} present")

        # Check Twitter Card
        if self.twitter_tags.get('twitter:card'):
            issues.append(f"✓ Twitter card present")
        else:
            issues.append("⚠️  Missing twitter:card")

        # Check images have alt text
        images_without_alt = [img for img in self.images if not img['alt']]
        if images_without_alt:
            issues.append(f"❌ {len(images_without_alt)} images without alt text")
        else:
            if self.images:
                issues.append(f"✓ All {len(self.images)} images have alt text")

        # Check heading hierarchy
        if self.headings:
            first_h = self.headings[0]['tag'] if self.headings else None
            if first_h != 'h1':
                issues.append(f"⚠️  First heading is {first_h}, should be h1")
            else:
                issues.append("✓ Heading hierarchy starts with h1")

        # Check JSON-LD
        if self.json_ld:
            issues.append(f"✓ JSON-LD schema present ({len(self.json_ld)} schemas)")
        else:
            issues.append("⚠️  No JSON-LD schema found")

        return issues


def validate_file(filepath):
    """Validate a single HTML file"""
    print(f"\n📄 Validating: {filepath}")
    print("=" * 60)

    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check JSON validity
        json_blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
        for block in json_blocks:
            try:
                json.loads(block)
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON-LD: {e}")
                return False

        # Validate with MetaTagValidator
        validator = MetaTagValidator()
        validator.feed(content)
        issues = validator.validate()

        for issue in issues:
            print(issue)

        # Check for critical issues
        critical = [i for i in issues if i.startswith('❌')]
        if critical:
            print(f"\n❌ {len(critical)} critical issues found")
            return False

        print("✓ Validation passed")
        return True

    except Exception as e:
        print(f"❌ Error validating: {e}")
        return False


def validate_phase2_features():
    """Validate Phase 2 features: breadcrumbs, related content, image optimization"""
    print("\n🔧 Phase 2 Features Validation")
    print("=" * 60)

    issues = []

    # Check search index automation
    if os.path.exists('search-index.json'):
        try:
            with open('search-index.json', 'r') as f:
                index = json.load(f)
            if len(index) > 100:
                print(f"✓ Search index automation: {len(index)} entries")
            else:
                issues.append("⚠️  Search index has few entries (< 100)")
        except Exception as e:
            issues.append(f"❌ Search index error: {e}")
    else:
        issues.append("❌ Search index not found")

    # Check for Phase 2 JavaScript modules
    modules = [
        'js/breadcrumb-generator.js',
        'js/related-content.js',
        'js/image-optimizer.js'
    ]

    for module in modules:
        if os.path.exists(module):
            size = os.path.getsize(module)
            print(f"✓ {module} ({size} bytes)")
        else:
            issues.append(f"⚠️  Missing module: {module}")

    # Check CSS updates
    if os.path.exists('css/shared.css'):
        with open('css/shared.css', 'r') as f:
            css = f.read()
        if '.breadcrumb' in css and '.related-content' in css and 'lazy-image' in css:
            print("✓ CSS includes breadcrumb, related content, and image optimizer styles")
        else:
            issues.append("⚠️  CSS may be missing Phase 2 styles")

    if issues:
        for issue in issues:
            print(issue)
    else:
        print("✓ All Phase 2 features present")

    return len([i for i in issues if i.startswith('❌')]) == 0


def main():
    """Main validation runner"""
    print("🚀 IT Vedas Build Validation")
    print("=" * 60)

    # Files to validate
    files_to_check = [
        'index.html',
        'cve-listing.html',
        'cve-detail.html',
        'chapters.html',
        'about.html',
    ]

    passed = 0
    failed = 0

    for filename in files_to_check:
        # Skip dynamic pages that set meta tags via JavaScript
        if filename in ['cve-listing.html', 'cve-detail.html']:
            print(f"\n📄 Validating: {filename}")
            print("=" * 60)
            print("ℹ️  Skipping SEO validation (meta tags set dynamically via JavaScript)")
            print("✓ Validation passed (dynamic page)")
            passed += 1
            continue

        if validate_file(filename):
            passed += 1
        else:
            failed += 1

    # Check JSON files
    print("\n" + "=" * 60)
    print("📋 Checking JSON files...")
    json_files = ['search-index.json', 'quiz-data.json']

    for filename in json_files:
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    json.load(f)
                print(f"✓ {filename} is valid JSON")
            except json.JSONDecodeError as e:
                print(f"❌ {filename} has invalid JSON: {e}")
                failed += 1
        else:
            print(f"⚠️  {filename} not found")

    # Validate Phase 2 features
    phase2_ok = validate_phase2_features()
    if not phase2_ok:
        failed += 1
    else:
        passed += 1

    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Results: {passed} passed, {failed} failed")

    if failed > 0:
        print("❌ Validation failed!")
        sys.exit(1)
    else:
        print("✅ All validations passed!")
        sys.exit(0)


if __name__ == '__main__':
    main()
