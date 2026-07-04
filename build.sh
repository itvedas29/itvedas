#!/bin/bash
# Build script for Cloudflare Pages
# Runs CVE aggregator before deployment

set -e

echo "🔍 Starting Cloudflare Pages build process..."
echo "⏱️  Timestamp: $(date)"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "⚠️  Python3 not found, skipping CVE aggregation"
    echo "✅ Build will proceed without CVE update"
    exit 0
fi

# Check if aggregator script exists
if [ ! -f "itvedas-brain/cve-aggregator.py" ]; then
    echo "⚠️  CVE aggregator script not found"
    echo "✅ Build will proceed without CVE update"
    exit 0
fi

echo "📥 Installing Python dependencies..."
python3 -m pip install --quiet requests 2>/dev/null || true

echo "🔄 Running CVE aggregator..."
python3 itvedas-brain/cve-aggregator.py || {
    echo "⚠️  CVE aggregation failed, but build continues"
    echo "ℹ️  Using existing CVE data"
}

echo "✅ Build preparation complete"
echo "📊 CVE database: $([ -f data/cves-2025-2026.json ] && echo 'Ready' || echo 'Using fallback')"

# Cloudflare Pages will automatically serve the static files
exit 0
