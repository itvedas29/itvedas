#!/usr/bin/env bash
# Read-only disk usage diagnostic for the VPS.
# Run with: bash disk_usage_report.sh
# Nothing here deletes anything — it only reports.

set -uo pipefail

echo "================ DISK OVERVIEW ================"
df -h /

echo
echo "================ TOP-LEVEL DIRS BY SIZE (/) ================"
sudo du -h --max-depth=1 / 2>/dev/null | sort -rh | head -20

echo
echo "================ TOP 20 LARGEST FILES (whole system) ================"
sudo find / -xdev -type f -printf '%s %p\n' 2>/dev/null | sort -rn | head -20 | awk '{ printf "%.1f MB  %s\n", $1/1024/1024, $2 }'

echo
echo "================ APT CACHE ================"
du -sh /var/cache/apt/archives 2>/dev/null

echo
echo "================ JOURNAL LOGS ================"
journalctl --disk-usage 2>/dev/null

echo
echo "================ /var/log SIZE ================"
sudo du -sh /var/log 2>/dev/null
sudo find /var/log -type f -name "*.log" -printf '%s %p\n' 2>/dev/null | sort -rn | head -10 | awk '{ printf "%.1f MB  %s\n", $1/1024/1024, $2 }'

echo
echo "================ PM2 LOGS ================"
du -sh ~/.pm2/logs 2>/dev/null
pm2 list 2>/dev/null

echo
echo "================ NODE_MODULES DIRECTORIES ================"
find / -xdev -type d -name node_modules -prune -exec du -sh {} \; 2>/dev/null

echo
echo "================ OLD KERNELS (apt) ================"
dpkg -l 'linux-image*' 2>/dev/null | grep '^ii'

echo
echo "================ DOCKER (if installed) ================"
if command -v docker >/dev/null 2>&1; then
  docker system df 2>/dev/null
else
  echo "docker not installed"
fi

echo
echo "================ SNAP (if installed) ================"
if command -v snap >/dev/null 2>&1; then
  du -sh /var/lib/snapd/snaps 2>/dev/null
else
  echo "snap not installed"
fi

echo
echo "================ DONE — review above before deleting anything ================"
