#!/usr/bin/env bash
# VPS disk cleanup — run after reviewing disk_usage_report.sh output.
# Each step prints what it's doing. Safe to re-run.

set -euo pipefail

echo "=== Before ==="
df -h /

echo
echo "--- apt clean ---"
apt clean
apt autoremove -y --purge

echo
echo "--- journal vacuum (keep 7 days) ---"
journalctl --vacuum-time=7d

echo
echo "--- pip / npm caches ---"
rm -rf /root/.cache/pip
rm -rf /root/.npm/_cacache

echo
echo "--- pm2 log flush ---"
pm2 flush

echo
echo "--- playwright cached browsers ---"
rm -rf /root/.cache/ms-playwright

echo
echo "--- old dashboard backup ---"
rm -rf /root/itvedas/dashboard-backup-20260618-1735

echo
echo "--- /opt/itvedas ---"
echo "SKIPPED: DEPLOYMENT.md documents /opt/itvedas as the canonical,"
echo "PM2-managed production checkout on this droplet, not a duplicate."
echo "If it really is stale on this box, verify (check 'pm2 list' for a"
echo "process rooted there, and 'git -C /opt/itvedas remote -v') and"
echo "remove it manually -- this script won't do it automatically."

echo
echo "=== After ==="
df -h /
echo
echo "Done."
