#!/bin/bash
# Security validation for ITVedas.
set -euo pipefail

echo "=== ITVedas Security Check ==="

python3 - <<'PY'
from pathlib import Path
import re, sys

provider_patterns = [
    re.compile(r'\b(?:sk-[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{20,})\b'),
    re.compile(r'\b(?:AIza[0-9A-Za-z_-]{30,}|ya29\.[0-9A-Za-z_-]{30,})\b'),
]
assignment_pattern = re.compile(
    r'\b(?:api[_-]?key|secret|access[_-]?token|auth[_-]?token)\s*[:=]\s*[\"\']([A-Za-z0-9+/=_-]{32,})[\"\']',
    re.I,
)
ignore_fragments = (
    'os.environ', 'process.env', 'your_api_key', 'your-api-key',
    'example', 'placeholder', 'changeme', 'test_', 'dummy_',
    'password-generator', 'your_client_id', 'your_client_secret',
    'your_access_token', 'your_refresh_token',
)
hits = []
warnings = []
for p in Path('.').rglob('*'):
    if not p.is_file() or '.git' in p.parts or 'node_modules' in p.parts or p.name == 'security-check.sh':
        continue
    if p.suffix.lower() not in {'.html', '.js', '.py', '.json', '.yml', '.yaml', '.toml', '.sh'}:
        continue
    try:
        lines = p.read_text(encoding='utf-8', errors='ignore').splitlines()
    except Exception:
        continue
    is_documentation = bool(p.parts and p.parts[0] in {'articles', 'chapters', 'docs'})
    for n, line in enumerate(lines, 1):
        low = line.lower()
        if any(x in low for x in ignore_fragments):
            continue
        if any(rx.search(line) for rx in provider_patterns):
            if is_documentation:
                warnings.append(f'{p}:{n}')
            else:
                hits.append(f'{p}:{n}')
            continue
        if not is_documentation and assignment_pattern.search(line):
            hits.append(f'{p}:{n}')

if warnings:
    print('⚠️ Credential-shaped examples found in documentation (reviewed, non-blocking):')
    print('\n'.join(warnings[:50]))
if hits:
    print('Potential hardcoded credentials found outside documentation:')
    print('\n'.join(hits[:50]))
    sys.exit(1)
print('✓ No hardcoded credentials detected outside documentation')
PY

echo "Checking dangerous DOM/eval patterns..."
python3 - <<'PY'
from pathlib import Path
import re
rx = re.compile(r'innerHTML|outerHTML|document\.write|eval\(', re.I)
hits = []
for p in Path('.').rglob('*'):
    if p.is_file() and p.suffix.lower() in {'.html', '.js'} and '.git' not in p.parts:
        try:
            for n, line in enumerate(p.read_text(encoding='utf-8', errors='ignore').splitlines(), 1):
                if rx.search(line): hits.append(f'{p}:{n}')
        except Exception:
            pass
if hits:
    print('⚠️ Potentially dangerous patterns require review:')
    print('\n'.join(hits[:100]))
else:
    print('✓ No dangerous DOM/eval patterns detected')
PY

if [ -f package.json ]; then
  echo "Checking dependencies..."
  npm audit --omit=dev
fi

echo "✓ Security check complete"
