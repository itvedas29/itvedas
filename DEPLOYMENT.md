# ITVedas Brain — Deployment Guide

This document describes how to run the ITVedas Brain pipeline (content
autopilot + Phase 2-7 brain scripts) on a self-hosted **Ubuntu 24.04**
DigitalOcean droplet, as a supplement/fallback to the GitHub Actions
workflows in `.github/workflows/`.

Every brain script (`scripts/brain.py`, `scripts/news_agent_v2.py`,
`itvedas-brain/*.py`) is pure Python 3 standard library — no third-party
packages are required to run them. The virtualenv and `requirements.txt`
below exist so the deployment is reproducible and isolated from system
Python, and so future scripts can add dependencies without changing this
process.

The goal: **the brain survives a server reboot automatically**, with no
manual intervention.

---

## 1. Server prerequisites

```bash
# As a non-root sudo user (recommended: create one if you only have root)
sudo adduser itvedas
sudo usermod -aG sudo itvedas
su - itvedas
```

Update the system and install Python 3.12:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.12 python3.12-venv python3-pip git curl
python3.12 --version   # confirm Python 3.12.x
```

Install Node.js (required for PM2) and PM2 itself:

```bash
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g pm2
node -v && pm2 -v
```

---

## 2. Clone the repository

```bash
sudo mkdir -p /opt/itvedas
sudo chown "$USER":"$USER" /opt/itvedas
git clone https://github.com/itvedas29/itvedas.git /opt/itvedas
cd /opt/itvedas
```

Keep deployments on a dedicated branch or `main` per your release process;
this guide assumes `/opt/itvedas` tracks `main`.

---

## 3. Virtualenv and requirements.txt

```bash
cd /opt/itvedas
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

`requirements.txt` (repo root) pins the runtime. All current brain
scripts use only the standard library, so this file is intentionally
minimal — add packages here (and re-run `pip install -r requirements.txt`)
the moment any script grows a real dependency:

```
# requirements.txt
# Brain scripts currently use only the Python standard library.
# Add pinned third-party packages here as the brain grows.
```

---

## 4. Environment configuration (`.env`)

Copy the template and fill in real secrets — never commit `.env`:

```bash
cp .env.example .env
chmod 600 .env
nano .env
```

`.env.example` (repo root):

```
# ── Content generation ──────────────────────────────────────────
# Claude = primary (decisions/QA/review/traffic control), OpenAI = secondary (article writing)
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
GA4_ID=G-XXXXXXXXXX

# ── Email notifications (optional) ──────────────────────────────
NOTIFY_EMAIL=
SMTP_FROM=
SMTP_PASS=

# ── GitHub Agent (Phase 5 github-agent.py) ───────────────────────
GITHUB_TOKEN=

# ── Runtime ───────────────────────────────────────────────────--
ITVEDAS_ENV=production
LOG_LEVEL=INFO
```

`.gitignore` must already exclude `.env` (verify, do not commit secrets):

```bash
grep -qxF '.env' .gitignore || echo '.env' >> .gitignore
```

All brain scripts read `os.environ` directly, so PM2/cron must be
configured to load `.env` before running them (see `run-brain.sh` below).

---

## 5. Logging

All scripts log to stdout/stderr today. Wrap every entry point in a
small runner script that timestamps and persists output, so PM2 and
cron both produce the same log trail:

`/opt/itvedas/scripts/run-brain.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd /opt/itvedas

# Load .env into the environment
set -a
source /opt/itvedas/.env
set +a

source /opt/itvedas/.venv/bin/activate

LOG_DIR="/opt/itvedas/logs"
mkdir -p "$LOG_DIR"
TS="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

TARGET="${1:?usage: run-brain.sh <script-path> [args...]}"
shift || true

{
  echo "==== $TS START $TARGET $* ===="
  python3.12 "$TARGET" "$@"
  echo "==== $(date -u +'%Y-%m-%dT%H:%M:%SZ') END $TARGET (exit $?) ===="
} >> "$LOG_DIR/brain.log" 2>&1
```

```bash
chmod +x /opt/itvedas/scripts/run-brain.sh
mkdir -p /opt/itvedas/logs
```

Rotate logs with `logrotate` so `brain.log` never grows unbounded:

`/etc/logrotate.d/itvedas`:

```
/opt/itvedas/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

---

## 6. PM2 service (primary scheduler)

PM2 keeps a long-running "brain daemon" alive and restarts it on crash;
a thin Python loop inside the daemon triggers each brain phase on its
own schedule (so PM2's job is process supervision, while the daemon
owns scheduling logic).

`/opt/itvedas/itvedas-brain/daemon.py`:

```python
#!/usr/bin/env python3
"""Long-running scheduler for the ITVedas brain pipeline under PM2.

Runs each phase on an in-process interval and logs to stdout, which PM2
captures. This is the primary scheduler; cron is the fallback in case
PM2/the daemon itself is down (see section 7).
"""
from __future__ import annotations

import datetime as dt
import subprocess
import sys
import time

REPO_ROOT = "/opt/itvedas"
PYTHON = f"{REPO_ROOT}/.venv/bin/python3.12"

# (script, interval_seconds)
JOBS = [
    (f"{REPO_ROOT}/itvedas-brain/repo-scanner.py", 6 * 3600),
    (f"{REPO_ROOT}/itvedas-brain/knowledge-builder.py", 6 * 3600),
    (f"{REPO_ROOT}/itvedas-brain/decision-engine.py", 6 * 3600),
    (f"{REPO_ROOT}/itvedas-brain/execution-engine.py", 6 * 3600),
    (f"{REPO_ROOT}/itvedas-brain/github-agent.py", 6 * 3600),
]

CHECK_INTERVAL = 60  # seconds between scheduler ticks


def log(message: str) -> None:
    print(f"[{dt.datetime.now(dt.timezone.utc).isoformat()}] {message}", flush=True)


def main() -> int:
    next_run = {script: 0.0 for script, _ in JOBS}
    log("Brain daemon started.")
    while True:
        now = time.time()
        for script, interval in JOBS:
            if now >= next_run[script]:
                log(f"Running {script}")
                result = subprocess.run([PYTHON, script], cwd=REPO_ROOT)
                if result.returncode != 0:
                    log(f"FAILED {script} (exit {result.returncode})")
                next_run[script] = now + interval
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    sys.exit(main())
```

`/opt/itvedas/ecosystem.config.js` (PM2 process file):

```js
module.exports = {
  apps: [
    {
      name: "itvedas-brain",
      script: "itvedas-brain/daemon.py",
      interpreter: "/opt/itvedas/.venv/bin/python3.12",
      cwd: "/opt/itvedas",
      env_file: "/opt/itvedas/.env",
      autorestart: true,
      restart_delay: 5000,
      max_restarts: 20,
      out_file: "/opt/itvedas/logs/pm2-out.log",
      error_file: "/opt/itvedas/logs/pm2-error.log",
      time: true
    }
  ]
};
```

> PM2 does not read `.env` files natively for plain scripts; `env_file`
> works with PM2 ≥ 5.3. If your PM2 version is older, source `.env` at
> the top of `daemon.py` instead (`load .env` via `os.environ` before
> importing anything that needs it).

Start it:

```bash
cd /opt/itvedas
pm2 start ecosystem.config.js
pm2 save
pm2 logs itvedas-brain
```

---

## 7. Cron fallback

If PM2 or the daemon process dies and isn't restarted in time, cron is
the safety net that guarantees the pipeline still runs at least once
per day.

```bash
crontab -e
```

Add:

```cron
# ITVedas brain — cron fallback (runs only if PM2 didn't already run
# the pipeline in the last interval; idempotent, safe to overlap).
SHELL=/bin/bash
15 0 * * * /opt/itvedas/scripts/run-brain.sh /opt/itvedas/itvedas-brain/repo-scanner.py
20 0 * * * /opt/itvedas/scripts/run-brain.sh /opt/itvedas/itvedas-brain/knowledge-builder.py
35 0 * * * /opt/itvedas/scripts/run-brain.sh /opt/itvedas/itvedas-brain/decision-engine.py
40 0 * * * /opt/itvedas/scripts/run-brain.sh /opt/itvedas/itvedas-brain/execution-engine.py
45 0 * * * /opt/itvedas/scripts/run-brain.sh /opt/itvedas/itvedas-brain/github-agent.py

# Article + news autopilot (mirrors .github/workflows/write-article.yml)
30 3 * * 1,3,5 /opt/itvedas/scripts/run-brain.sh /opt/itvedas/scripts/brain.py
30 2 * * *     /opt/itvedas/scripts/run-brain.sh /opt/itvedas/scripts/news_agent_v2.py
30 7 * * *     /opt/itvedas/scripts/run-brain.sh /opt/itvedas/scripts/news_agent_v2.py
30 12 * * *    /opt/itvedas/scripts/run-brain.sh /opt/itvedas/scripts/news_agent_v2.py

# PM2 self-heal: if the itvedas-brain process is gone, resurrect it
*/5 * * * * pm2 describe itvedas-brain > /dev/null 2>&1 || (cd /opt/itvedas && pm2 start ecosystem.config.js)
```

All brain scripts write idempotent state files (`itvedas-brain/memory/*.json`,
`itvedas-brain/state/*.json`) atomically, so running cron and PM2's daemon in the
same window is safe — duplicate runs just overwrite state with the same
(or fresher) data, they don't corrupt it.

---

## 8. Startup on reboot

Two independent layers ensure the brain restarts after any reboot,
power loss, or droplet resize:

**PM2 resurrection (primary):**

```bash
pm2 startup systemd
# Run the exact command pm2 prints, e.g.:
#   sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u itvedas --hp /home/itvedas
pm2 save
```

This installs a systemd unit (`pm2-itvedas`) that runs `pm2 resurrect`
on boot, bringing back every process saved with `pm2 save` — including
`itvedas-brain`.

**Cron (fallback, always active):** `cron` itself is enabled by default
on Ubuntu 24.04 and starts on boot via systemd; no extra step is needed
beyond confirming it:

```bash
systemctl is-enabled cron   # should print "enabled"
```

**Verification after every reboot:**

```bash
sudo reboot
# ... wait, then SSH back in ...
systemctl status pm2-itvedas --no-pager
pm2 list
crontab -l
```

If `pm2 list` doesn't show `itvedas-brain` as `online`, the cron
self-heal line in section 7 will restart it within 5 minutes without
any manual action.

---

## 9. Health checks

`itvedas-brain/healthcheck.py` — a lightweight script that verifies the
pipeline produced fresh output, and can be polled by cron, an external
uptime monitor, or a status page:

```python
#!/usr/bin/env python3
"""Health check: confirm brain state files exist and are recent."""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path("/opt/itvedas")
MAX_AGE_HOURS = 30  # generous margin over the 24h cron/PM2 cycle

CHECKS = [
    REPO_ROOT / "itvedas-brain" / "memory" / "repository.json",
    REPO_ROOT / "brain" / "daily-plan.json",
    REPO_ROOT / "brain" / "execution-plan.json",
    REPO_ROOT / "brain" / "github-actions.json",
]


def main() -> int:
    now = dt.datetime.now(dt.timezone.utc)
    problems = []

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
```

Run it from cron every 15 minutes and alert on failure (swap the `mail`
line for a webhook/Slack curl if you don't have local mail configured):

```cron
*/15 * * * * /opt/itvedas/.venv/bin/python3.12 /opt/itvedas/itvedas-brain/healthcheck.py || echo "ITVedas brain unhealthy on $(hostname)" | mail -s "ITVedas brain alert" you@example.com
```

PM2 also exposes its own process-level health:

```bash
pm2 status itvedas-brain   # process state, uptime, restart count
pm2 monit                  # live CPU/memory
```

---

## 10. Backup strategy

The brain's durable state lives in JSON files under `itvedas-brain/state/` and
`itvedas-brain/memory/`, plus the git history itself. Back up both the
state and the application code/secrets.

**1. State + repo, via git (primary):** the pipeline already commits
`itvedas-brain/state/*.json` and `itvedas-brain/memory/*.json` back to `main` (see
`.github/workflows/refresh-repository-memory.yml`), so every snapshot
is versioned in GitHub automatically — no extra step needed as long as
the droplet's checkout stays in sync (`git pull` before each run, or
let the GitHub Action be the writer and `git pull` on the droplet).

**2. Local tarball snapshots (defense in depth):**

`/opt/itvedas/scripts/backup-brain.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
BACKUP_DIR="/opt/itvedas-backups"
TS="$(date -u +'%Y%m%dT%H%M%SZ')"
mkdir -p "$BACKUP_DIR"

tar -czf "$BACKUP_DIR/itvedas-brain-$TS.tar.gz" \
  -C /opt/itvedas \
  itvedas-brain/state itvedas-brain/memory itvedas-brain/knowledge \
  itvedas-brain/repository_knowledge.json .env

# Keep the last 30 days of local backups
find "$BACKUP_DIR" -name 'itvedas-brain-*.tar.gz' -mtime +30 -delete
```

```bash
chmod +x /opt/itvedas/scripts/backup-brain.sh
mkdir -p /opt/itvedas-backups
crontab -e
# add:
0 1 * * * /opt/itvedas/scripts/backup-brain.sh
```

**3. Off-droplet copy:** ship the tarball to DigitalOcean Spaces (or any
S3-compatible bucket) so a backup survives droplet loss, not just disk
loss:

```bash
# one-time: doctl + s3cmd/rclone configured with Spaces credentials
rclone copy /opt/itvedas-backups spaces:itvedas-backups/brain --max-age 31d
```

Add that `rclone copy` line to the end of `backup-brain.sh` once
credentials are configured, so every nightly backup is also pushed
off-box automatically.

**4. Restore drill:** periodically verify backups are actually
restorable:

```bash
mkdir -p /tmp/restore-test
tar -xzf /opt/itvedas-backups/itvedas-brain-<timestamp>.tar.gz -C /tmp/restore-test
python3 -m json.tool /tmp/restore-test/itvedas-brain/state/daily-plan.json > /dev/null && echo "OK"
```

---

## 11. Operational summary

| Layer | Responsibility | Survives reboot? |
|---|---|---|
| `pm2-itvedas` systemd unit | Resurrects PM2 + `itvedas-brain` daemon on boot | Yes |
| `itvedas-brain` PM2 process | Primary scheduler, restarts on crash | Yes (via PM2 `autorestart`) |
| `cron` (system service) | Fallback scheduler + PM2 self-heal + backups + health checks | Yes (enabled by default on Ubuntu 24.04) |
| `logrotate` | Keeps `logs/brain.log` bounded | N/A |
| GitHub Actions (`refresh-repository-memory.yml`, `write-article.yml`) | Cloud-side source of truth, independent of droplet uptime | N/A (already cloud-hosted) |

With PM2 resurrection as primary and cron as fallback, the brain
restarts itself after any reboot without manual intervention, and a
stale/missing PM2 process is self-healed by cron within 5 minutes.
