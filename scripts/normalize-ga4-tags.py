#!/usr/bin/env python3
"""Remove stale SRI hashes from mutable Google gtag.js script tags.

GA4's gtag.js is a mutable third-party resource; a fixed SRI digest can
silently disable analytics after Google changes the resource. This script
keeps the remote tag but removes integrity attributes from that specific tag.
"""
from pathlib import Path
import re
changed=0
for path in Path('.').rglob('*.html'):
    if '.git' in path.parts: continue
    raw=path.read_text(encoding='utf-8',errors='ignore')
    new=re.sub(r'(<script\b(?=[^>]*googletagmanager\.com/gtag/js)[^>]*?)\s+integrity=["\'][^"\']+["\']([^>]*>)',r'\1\2',raw,flags=re.I)
    if new!=raw:
        path.write_text(new,encoding='utf-8'); changed+=1
print(f'Normalized GA4 tags in {changed} HTML files')
