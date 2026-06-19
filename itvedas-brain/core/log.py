"""Shared logging helper for all ITVedas brain scripts.

Previously scripts/brain.py, scripts/news_agent_v2.py, and
scripts/self_improve.py each wrote to their own log file
(activity.log, self_improve.log respectively; news_agent_v2.py only
printed to stdout). This module consolidates all of that into a single
log file - itvedas-brain/state/brain.log - with each line prefixed by
the component name, so anyone debugging the pipeline only has to tail
one file.
"""
from __future__ import annotations

import datetime
import pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
STATE_DIR = BASE_DIR / "state"
LOG_FILE = STATE_DIR / "brain.log"


def log(component: str, msg: str) -> None:
    """Write a single timestamped, component-prefixed line.

    Prints to stdout (so it still shows up in GitHub Actions logs / PM2
    logs) and appends to the shared itvedas-brain/state/brain.log file.
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{component}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as handle:
        handle.write(line + "\n")
