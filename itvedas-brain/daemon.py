#!/usr/bin/env python3
"""Long-running scheduler for the ITVedas brain pipeline under PM2.

Runs each phase on an in-process interval and logs to stdout, which PM2
captures. This is the primary scheduler; cron is the fallback in case
PM2 or this daemon itself is down (see DEPLOYMENT.md section 7).
"""
from __future__ import annotations

import datetime as dt
import pathlib
import subprocess
import sys
import time

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PYTHON = str(REPO_ROOT / ".venv" / "bin" / "python3.12")
BRAIN_DIR = REPO_ROOT / "itvedas-brain"

# (script, interval_seconds)
JOBS = [
    (BRAIN_DIR / "repo-scanner.py", 6 * 3600),
    (BRAIN_DIR / "knowledge-builder.py", 6 * 3600),
    (BRAIN_DIR / "decision-engine.py", 6 * 3600),
    (BRAIN_DIR / "execution-engine.py", 6 * 3600),
    (BRAIN_DIR / "github-agent.py", 6 * 3600),
]

CHECK_INTERVAL_SECONDS = 60


def log(message: str) -> None:
    print(f"[{dt.datetime.now(dt.timezone.utc).isoformat()}] {message}", flush=True)


def main() -> int:
    python = PYTHON if pathlib.Path(PYTHON).is_file() else sys.executable
    next_run = {str(script): 0.0 for script, _ in JOBS}
    log(f"Brain daemon started using interpreter: {python}")

    while True:
        now = time.time()
        for script, interval in JOBS:
            key = str(script)
            if now >= next_run[key]:
                log(f"Running {script}")
                result = subprocess.run([python, str(script)], cwd=str(REPO_ROOT))
                if result.returncode != 0:
                    log(f"FAILED {script} (exit {result.returncode})")
                next_run[key] = now + interval
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    sys.exit(main())
