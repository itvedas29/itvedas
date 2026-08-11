#!/usr/bin/env python3
"""Compatibility wrapper for the unified CVE pipeline.

Use scripts/cve_unified_sync.py for all new automation. This wrapper remains
for older documentation/manual commands so there is only one implementation.
"""
import subprocess, sys
from pathlib import Path
script=Path(__file__).with_name('cve_unified_sync.py')
if len(sys.argv)>1 and sys.argv[1]=='--report':
    raise SystemExit(subprocess.call([sys.executable,str(script),'--report']))
if len(sys.argv)>1 and sys.argv[1]=='--sync':
    raise SystemExit(subprocess.call([sys.executable,str(script),'--sync']))
print('Usage: python3 scripts/cve_ingestion.py --sync|--report')
raise SystemExit(1)
