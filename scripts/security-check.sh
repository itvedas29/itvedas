#!/bin/bash
# Security validation for ITVedas.
set -euo pipefail

echo "=== ITVedas Security Check ==="

python3 - <<'PY'
from pathlib import Path
import re, sys

# Only flag credential-shaped values, not ordinary variables such as
# password = user input or API_KEY = os.environ.get(...).
secret_patterns = [
    re.compile(r'\b(?:sk-[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{20,})\b'),
    re.compile(r'\b(?:AIza[0-9A-Za-z_-]{30,}|ya29\.[0-9A-Za-z_-]{30,})\b'),
    re.compile(r'\b(?:api[_-]?key|secret|access[_-]?token|auth[_-]?token)\s*[:=]\s*[\"\']([A-Za-z0-9+/=_-]{32,})[\"\']', re.I),
]
ignore_fragments=('os.environ','process.env','your_api_key','your-api-key','example','placeholder','changeme','test_','dummy_','password-generator')
hits=[]
for p in Path('.').rglob('*'):
    if not p.is_file() or '.git' in p.parts or 'node_modules' in p.parts or p.name=='security-check.sh': continue
    if p.suffix.lower() not in {'.html','.js','.py','.json','.yml','.yaml','.toml','.sh'}: continue
    try: lines=p.read_text(encoding='utf-8',errors='ignore').splitlines()
    except Exception: continue
    for n,line in enumerate(lines,1):
        low=line.lower()
        if any(x in low for x in ignore_fragments): continue
        if any(rx.search(line) for rx in secret_patterns): hits.append(f'{p}:{n}')
if hits:
    print('Potential hardcoded credentials found:')
    print('\n'.join(hits[:50]))
    sys.exit(1)
print('✓ No hardcoded credentials detected')
PY

echo "Checking dangerous DOM/eval patterns..."
python3 - <<'PY'
from pathlib import Path
import re
rx=re.compile(r'innerHTML|outerHTML|document\.write|eval\(',re.I); hits=[]
for p in Path('.').rglob('*'):
    if p.is_file() and p.suffix.lower() in {'.html','.js'} and '.git' not in p.parts:
        try:
            for n,line in enumerate(p.read_text(encoding='utf-8',errors='ignore').splitlines(),1):
                if rx.search(line): hits.append(f'{p}:{n}')
        except Exception: pass
if hits:
    print('⚠️ Potentially dangerous patterns require review:')
    print('\n'.join(hits[:100]))
else: print('✓ No dangerous DOM/eval patterns detected')
PY

if [ -f package.json ]; then
  echo "Checking dependencies..."
  npm audit --omit=dev
fi

echo "✓ Security check complete"
