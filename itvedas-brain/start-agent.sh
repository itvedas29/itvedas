#!/bin/bash
# ITVedas AI Agent — quick start
# Usage: ./start-agent.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load .env if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Check keys
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "❌  ANTHROPIC_API_KEY not set"
  echo "    Run: export ANTHROPIC_API_KEY=sk-ant-..."
  exit 1
fi

if [ -z "$GITHUB_TOKEN" ]; then
  echo "⚠   GITHUB_TOKEN not set — GitHub tools will be disabled"
fi

# Create virtualenv if it doesn't exist
if [ ! -d "venv" ]; then
  echo "🔧 Creating virtualenv..."
  python3 -m venv venv
fi

# Activate
source venv/bin/activate

# Install deps if needed
pip install -q flask duckduckgo-search beautifulsoup4

echo ""
echo "⚡ Starting ITVedas AI Agent..."
echo "   Open: http://localhost:5000"
echo "   Stop: Ctrl+C"
echo ""

python3 agent.py
