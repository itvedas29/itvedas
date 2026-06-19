#!/usr/bin/env python3
"""Health check: confirm brain state files exist and are recent.

Intended to run from cron on the deployment droplet (see DEPLOYMENT.md
section 9). Exits 0 when healthy, 1 when something is missing, stale,
or unreadable.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
MAX_AGE_HOURS = 30  # generous margin over the 24h cron/PM2 cycle

CHECKS = [
    REPO_ROOT / "itvedas-brain" / "memory" / "repository.json",
    REPO_ROOT / "itvedas-brain" / "state" / "daily-plan.json",
    REPO_ROOT / "itvedas-brain" / "state" / "execution-plan.json",
    REPO_ROOT / "itvedas-brain" / "state" / "github-actions.json",
]


def main() -> int:
    now = dt.datetime.now(dt.timezone.utc)
    problems: list[str] = []

    for path in CHECKS:
        if not path.is_file():
            problems.append(f"MISSING: {path}")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            generated_at = dt.datetime.fromisoformat(
                data["generated_at"].replace("Z", "+00:00")
            )
        except Exception as error:  # noqa: BLE001
            problems.append(f"UNREADABLE: {path} ({error})")
            continue
        age_hours = (now - generated_at).total_seconds() / 3600
        if age_hours > MAX_AGE_HOURS:
            problems.append(f"STALE ({age_hours:.1f}h old): {path}")

    if problems:
        print("UNHEALTHY")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print("HEALTHY: all brain state files present and fresh.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
