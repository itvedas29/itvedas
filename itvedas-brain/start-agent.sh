#!/bin/bash
# ITVedas AI Agent — quick start
# Usage: ./start-agent.sh
# Set your API keys as env vars or in a .env file

set -e

# Load .env if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Check keys
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "❌  ANTHROPIC_API_KEY not set"
  echo "    Set it: export ANTHROPIC_API_KEY=your_key"
  exit 1
fi

if [ -z "$GITHUB_TOKEN" ]; then
  echo "⚠   GITHUB_TOKEN not set — GitHub tools will be disabled"
fi

# Install deps if needed
pip install -q flask duckduckgo-search beautifulsoup4 2>/dev/null || true

# Run
python agent.py
