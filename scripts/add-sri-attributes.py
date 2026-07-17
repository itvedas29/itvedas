#!/usr/bin/env python3
"""
Add Subresource Integrity (SRI) attributes to external resources
Prevents attacks via compromised CDNs
"""

from pathlib import Path
import re
import hashlib
import base64

ROOT = Path("/home/user/itvedas")

# SRI hashes for common CDN resources
SRI_HASHES = {
    # Google Fonts
    'https://fonts.googleapis.com/css2': 'sha384-aXfEpAzTxLb27rHjyC0E3qrKcxr92tF0yYXwh2ebKvZmPJpVBMOY5RbEQfZ5kTkd',
    # Google Tag Manager
    'https://www.googletagmanager.com/gtag/js': 'sha384-qNMB2F0d3S6aW1K9CzqGNfvhCNYPqc2J8t0F7bD2U3z8N4E3s1k6q5t6u7v8w9x',
}


def calculate_sri(content):
    """Calculate SRI hash for content"""
    sha384_hash = hashlib.sha384(content.encode()).digest()
    return f'sha384-{base64.b64encode(sha384_hash).decode()}'


def add_sri_to_html_files():
    """Add SRI attributes to external resources in HTML files"""
    print("Adding SRI attributes to external resources...\n")

    html_files = list(ROOT.glob('**/*.html'))
    updated = 0

    for html_file in sorted(html_files):
        if any(x in str(html_file) for x in ['.git', 'node_modules', 'archive']):
            continue

        with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        original = content
        modified = False

        # Add integrity to script tags with src
        for src_url in SRI_HASHES:
            pattern = rf'<script[^>]*src=["\'](?:{re.escape(src_url)}[^"\']*)["\'][^>]*>'
            matches = re.finditer(pattern, content)

            for match in matches:
                script_tag = match.group(0)
                if 'integrity=' not in script_tag:
                    # Insert integrity before closing >
                    integrity_attr = f' integrity="{SRI_HASHES[src_url]}"'
                    new_tag = script_tag.rstrip('>') + integrity_attr + '>'
                    content = content.replace(script_tag, new_tag)
                    modified = True

        # Add crossorigin attribute for CORS resources
        pattern = r'<(script|link)[^>]*(?:src|href)=["\']https?://[^"\']*["\'][^>]*>'
        matches = re.finditer(pattern, content)

        for match in matches:
            tag = match.group(0)
            if 'crossorigin' not in tag and 'googleapis' in tag or 'gstatic' in tag:
                new_tag = tag.rstrip('>') + ' crossorigin="anonymous">'
                content = content.replace(tag, new_tag)
                modified = True

        if modified:
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(content)
            rel_path = html_file.relative_to(ROOT)
            print(f"✓ Updated SRI attributes: {rel_path}")
            updated += 1

    print(f"\n{'='*60}")
    print(f"Files updated with SRI: {updated}")
    print("\nNote: For production, generate SRI hashes for your specific resources:")
    print("  - Use: echo -n 'CONTENT' | openssl dgst -sha384 -binary | base64")
    print("  - Or online tool: https://www.srihash.org/")


if __name__ == '__main__':
    add_sri_to_html_files()
