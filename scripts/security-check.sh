#!/bin/bash
# Security validation for ITVedas.
set -euo pipefail

echo "=== ITVedas Security Check ==="

python3 - <<'PY'
from pathlib import Path
import re, sys

secret_pattern = re.compile(r"(?:password|passwd|secret|api[_-]?key|access[_-]?token|auth[_-]?token)\s*[:=]\s*['\"]?([A-Za-z0-9_./+=-]{12,})", re.I)
files=[]
for root in (Path('.'),):
    for p in root.rglob('*'):
        if not p.is_file() or '.git' in p.parts or 'node_modules' in p.parts:
            continue
        if p.suffix.lower() in {'.html','.js','.py','.json','.yml','.yaml','.toml','.sh'}:
            files.append(p)
hits=[]
for p in files:
    try: text=p.read_text(encoding='utf-8',errors='ignore')
    except Exception: continue
    if p.name == 'security-check.sh' or p.name.endswith('.example'): continue
    for line_no,line in enumerate(text.splitlines(),1):
        if secret_pattern.search(line) and not any(x in line.lower() for x in ('your_api_key','example','placeholder','changeme')):
            hits.append(f'{p}:{line_no}')
if hits:
    print('Potential hardcoded secrets found:')
    print('\n'.join(hits[:50]))
    sys.exit(1)
print('✓ No hardcoded secrets detected')
PY

echo "Checking dangerous DOM/eval patterns..."
python3 - <<'PY'
from pathlib import Path
import re
patterns=re.compile(r'innerHTML|outerHTML|document\.write|eval\(',re.I)
hits=[]
for p in Path('.').rglob('*'):
    if p.is_file() and p.suffix.lower() in {'.html','.js'} and '.git' not in p.parts:
        try:
            for n,line in enumerate(p.read_text(encoding='utf-8',errors='ignore').splitlines(),1):
                if patterns.search(line): hits.append(f'{p}:{n}')
        except Exception: pass
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
