#!/bin/bash
# ITVedas AI Agent — Server Setup
# Run once as root on your server:  bash deploy/setup.sh
# ──────────────────────────────────────────────────────────

set -e
REPO_DIR="/root/itvedas"
BRAIN_DIR="$REPO_DIR/itvedas-brain"
VENV="$BRAIN_DIR/venv"

echo "═══════════════════════════════════════"
echo "  ITVedas AI Agent — Server Setup"
echo "═══════════════════════════════════════"

# 1. Create .env if missing
if [ ! -f "$BRAIN_DIR/.env" ]; then
  echo ""
  echo "⚙  Creating .env — enter your API keys:"
  read -rp "  ANTHROPIC_API_KEY: " ANT_KEY
  read -rp "  GITHUB_TOKEN: " GH_TOKEN
  read -rp "  AGENT_PASSWORD (default: itvedas): " AGENT_PW
  AGENT_PW="${AGENT_PW:-itvedas}"
  cat > "$BRAIN_DIR/.env" <<EOF
ANTHROPIC_API_KEY=$ANT_KEY
GITHUB_TOKEN=$GH_TOKEN
AGENT_PASSWORD=$AGENT_PW
GITHUB_REPOSITORY=itvedas29/itvedas
GITHUB_BRANCH=main
PORT=5001
EOF
  echo "  ✓ .env created"
else
  echo "  ✓ .env already exists"
fi

# 2. Create virtualenv + install deps
echo ""
echo "📦 Installing Python dependencies..."
python3 -m venv "$VENV"
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q flask duckduckgo-search beautifulsoup4
echo "  ✓ Dependencies installed"

# 3. Install systemd service
echo ""
echo "⚙  Installing systemd service..."
cp "$BRAIN_DIR/deploy/itvedas-agent.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable itvedas-agent
systemctl restart itvedas-agent
echo "  ✓ Service started (port 5001)"

# 4. Install nginx config
echo ""
echo "🌐 Installing nginx config for ai.itvedas.com..."
cp "$BRAIN_DIR/deploy/nginx-ai.itvedas.com.conf" /etc/nginx/sites-available/ai.itvedas.com
ln -sf /etc/nginx/sites-available/ai.itvedas.com /etc/nginx/sites-enabled/ai.itvedas.com
nginx -t && systemctl reload nginx
echo "  ✓ Nginx configured"

# 5. SSL with certbot (optional)
echo ""
echo "🔒 SSL certificate (optional):"
read -rp "  Set up HTTPS with Let's Encrypt? [y/N]: " SSL
if [[ "$SSL" =~ ^[Yy]$ ]]; then
  apt-get install -y certbot python3-certbot-nginx -q
  certbot --nginx -d ai.itvedas.com
  echo "  ✓ SSL enabled"
else
  echo "  Skipped — run later: certbot --nginx -d ai.itvedas.com"
fi

echo ""
echo "═══════════════════════════════════════"
echo "  ✅  Agent is live at http://ai.itvedas.com"
echo ""
echo "  Useful commands:"
echo "    systemctl status itvedas-agent   — check status"
echo "    journalctl -fu itvedas-agent      — live logs"
echo "    systemctl restart itvedas-agent   — restart"
echo "═══════════════════════════════════════"
