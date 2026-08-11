#!/bin/bash
# Security validation for ITVedas
# Run this as part of CI/CD to catch actionable security issues.
set -euo pipefail

echo "=== ITVedas Security Check ==="

# Check for hardcoded secrets. Match assignment-like patterns and ignore
# documentation/examples so normal words such as "token" do not fail CI.
echo "Checking for hardcoded secrets..."
secret_hits=$(grep -RniE --include='*.html' --include='*.js' --include='*.py' \
  '(password|passwd|secret|api[_-]?key|access[_-]?token|auth[_-]?token)[[:space:]]*[:=][[:space:]]*["'"']?[A-Za-z0-9_./+=-]{12,}' \
  . 2>/dev/null \
  | grep -vE '(^|/)(node_modules|\.git)(/|$)|\.env\.example|security-check\.sh' \
  || true)

if [ -n "$secret_hits" ]; then
    echo "Potential hardcoded secrets found:"
    echo "$secret_hits"
    exit 1
fi

echo "✓ No hardcoded secrets detected"

# Report dangerous DOM/eval patterns for review, but do not fail merely because
# a safe, reviewed sanitizer or compatibility path legitimately uses them.
echo "Checking for dangerous patterns in HTML/JS..."
dangerous_hits=$(grep -RniE --include='*.js' --include='*.html' '(innerHTML|outerHTML|document\.write|eval\()' . 2>/dev/null \
  | grep -vE '(^|/)(node_modules|\.git)(/|$)' \
  || true)

if [ -n "$dangerous_hits" ]; then
    echo "⚠️  Potentially dangerous patterns require review:"
    echo "$dangerous_hits"
else
    echo "✓ No dangerous DOM/eval patterns detected"
fi

# Check dependency versions if package.json exists.
if [ -f "package.json" ]; then
    echo "Checking dependencies..."
    npm audit --omit=dev
fi

echo ""
echo "✓ Security check complete"
