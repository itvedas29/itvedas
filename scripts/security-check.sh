#!/bin/bash
# Security validation for ITVedas
# Run this as part of CI/CD to catch security issues

echo "=== ITVedas Security Check ==="

# Check for hardcoded secrets
echo "Checking for hardcoded secrets..."
if grep -r "password\|secret\|api_key\|token" --include="*.html" --include="*.js" --include="*.py" . 2>/dev/null | grep -v "node_modules\|.git\|.env.example" | grep -E "(password|secret|token).*="; then
    echo "⚠️  Potential hardcoded secrets found!"
    exit 1
fi

echo "✓ No hardcoded secrets detected"

# Check for dangerous patterns in HTML/JS
echo "Checking for XSS vulnerabilities..."
if grep -r "innerHTML\|eval(" --include="*.js" --include="*.html" . 2>/dev/null | grep -v "node_modules\|.git"; then
    echo "⚠️  Potentially dangerous patterns found!"
fi

echo "✓ Basic security checks passed"

# Check dependency versions if package.json exists
if [ -f "package.json" ]; then
    echo "Checking dependencies..."
    npm audit --production
fi

echo ""
echo "✓ Security check complete"
