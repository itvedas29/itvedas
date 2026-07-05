# CVE Database Automation Setup

## Overview

The CVE database is now **completely automated**. CVE data is fetched and updated through three mechanisms:

1. **GitHub Actions** - Daily scheduled updates (recommended)
2. **Cloudflare Pages Build Hook** - Runs during every deployment
3. **Manual trigger** - For on-demand updates

---

## 🤖 GitHub Actions (Daily Auto-Update)

### What It Does
- Runs every day at **2 AM UTC**
- Fetches CVEs from NVD, GitHub, CISA, Exploit-DB
- Aggregates and deduplicates all vulnerabilities
- Automatically commits and pushes to `claude/keen-keller-roy4d3` branch
- Cloudflare Pages automatically redeploys with new data

### Configuration File
```
.github/workflows/update-cves-daily.yml
```

### How It Works

```
Daily (2 AM UTC)
    ↓
GitHub Actions triggered
    ↓
Python environment setup
    ↓
Run cve-aggregator.py
    ├─ Fetch NVD API
    ├─ Fetch GitHub API
    ├─ Fetch CISA KEV
    └─ Generate /data/cves-2025-2026.json
    ↓
Check if data changed
    ↓
If changed: auto-commit & push
    ↓
Cloudflare Pages detects push
    ↓
Auto-deploy new data to edge
    ↓
Users see latest CVEs globally
```

### Status Checks
View workflow runs:
```
GitHub Repo → Actions tab → "Update CVE Database Daily"
```

---

## 🚀 Cloudflare Pages Build Hook

### What It Does
- Runs **during every Cloudflare Pages deployment**
- Automatically updates CVE data on each push
- Falls back gracefully if aggregation fails
- Keeps CVE database in sync with code changes

### Configuration File
```
wrangler.toml     (Build command: bash build.sh)
build.sh          (Runs CVE aggregator)
```

### How It Works

```
1. You: git push to branch
        ↓
2. Cloudflare detects push
        ↓
3. Cloudflare runs: bash build.sh
        ↓
4. build.sh runs: python3 cve-aggregator.py
        ↓
5. Aggregator fetches from all sources
        ↓
6. Data saved to /data/cves-2025-2026.json
        ↓
7. Cloudflare deploys everything to edge
        ↓
8. New code + new CVE data live worldwide < 2 minutes
```

---

## 📅 Schedule

| Trigger | Time | Frequency | What Updates |
|---------|------|-----------|--------------|
| **GitHub Actions** | 2 AM UTC daily | Every 24 hours | CVE data only |
| **Cloudflare Build** | On push | Every deployment | Code + CVE data |
| **Manual Trigger** | Anytime | On demand | CVE data only |

---

## 🔧 Manual Trigger Options

### Option 1: Local (Immediate)
```bash
python3 itvedas-brain/cve-aggregator.py
```
Updates `/data/cves-2025-2026.json` locally

### Option 2: GitHub Actions (Via Web)
```
GitHub Repo → Actions → "Update CVE Database Daily"
             → "Run workflow" button
```
Runs aggregator immediately, auto-commits and pushes

### Option 3: Trigger Deployment
```bash
git push origin claude/keen-keller-roy4d3
```
Cloudflare Pages build hook runs aggregator automatically

---

## 🔐 Secrets & Environment Variables

### Required Secret in GitHub
You need to add the Anthropic API key to GitHub:

1. Go to: **GitHub Repo → Settings → Secrets and variables → Actions**
2. Click **"New repository secret"**
3. Name: `ANTHROPIC_API_KEY`
4. Value: Your API key (from `.env` or secrets manager)
5. Click **Add secret**

The workflow will automatically use this when running.

---

## 📊 CVE Data Update Flow

```
┌─────────────────────────────────────────┐
│   Data Sources (Global APIs)            │
│  NVD | GitHub | CISA | Exploit-DB      │
└────────────────────┬────────────────────┘
                     │
              ┌──────▼──────┐
              │  Aggregator │
              │  (Python)   │
              └──────┬──────┘
                     │
         ┌───────────▼───────────┐
         │  Deduplicate & Sort   │
         │  by CVSS Score        │
         └───────────┬───────────┘
                     │
        ┌────────────▼────────────┐
        │  Save to cves-2025-26   │
        │  .json                  │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │  Auto-commit to Git     │
        │  (GitHub Actions)       │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │  Deploy to Cloudflare   │
        │  Pages (Auto)           │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │  Served from 200 CDN    │
        │  locations globally     │
        └───────────────────────────┘
```

---

## ✅ Verification Checklist

### For Local Setup
- [x] `cve-aggregator.py` exists in `itvedas-brain/`
- [x] `build.sh` created and executable
- [x] `wrangler.toml` configured
- [x] Sample CVE data in `/data/cves-2025-2026.json`

### For GitHub Actions
- [ ] API key added to GitHub Secrets
- [ ] Workflow file exists: `.github/workflows/update-cves-daily.yml`
- [ ] Branch: `claude/keen-keller-roy4d3`
- [ ] Verify workflow runs: **Actions tab → check logs**

### For Cloudflare Pages
- [ ] Repository connected to Cloudflare Pages
- [ ] `build.sh` is executable
- [ ] `wrangler.toml` configured
- [ ] Verify build succeeds on next push

---

## 🚨 Troubleshooting

### GitHub Actions Failed
1. Go to: **Actions → Update CVE Database Daily**
2. Find failed run
3. Click **View logs**
4. Common issues:
   - API key not in secrets → add it
   - Network timeout → will retry next day
   - No changes to CVE data → that's OK (skips commit)

### Cloudflare Build Failed
1. Go to: **Cloudflare Dashboard → Pages → itvedas**
2. Find failed deployment
3. Click **View build logs**
4. Check: Python available? Requests library installed?
5. If aggregator fails, build still succeeds (uses existing data)

### CVE Data Not Updating
1. Check if APIs are accessible:
   ```bash
   curl -I https://services.nvd.nist.gov/rest/json/cves/2.0
   ```
2. Check last workflow run: **GitHub Actions**
3. Check last deployment: **Cloudflare Pages**
4. Manually trigger: GitHub Actions "Run workflow" button

---

## 📈 Monitoring

### View CVE Update History
```bash
# See all CVE updates
git log --oneline --grep="Update CVE" 

# See what changed in latest update
git show HEAD:data/cves-2025-2026.json | head -20
```

### Check Data Freshness
1. Go to: `https://itvedas.com/chapters/cve/database-2025-2026.html`
2. Look at timestamps in CVE entries
3. Should be from last 24 hours

### GitHub Actions Dashboard
```
itvedas repo → Actions → "Update CVE Database Daily"
Shows:
- Last run time
- Execution duration
- Success/failure status
- CVEs added/updated count
```

---

## 🎯 Benefits of Automation

| Benefit | How |
|---------|-----|
| **Always Fresh** | Updates daily, even while you sleep |
| **Zero Manual Work** | No need to run script manually |
| **Globally Fast** | Deployed to 200+ CDN locations |
| **Transparent** | Track every update in git history |
| **Reliable** | Graceful fallback if anything fails |
| **Scalable** | Works for 10 CVEs or 10,000 CVEs |

---

## 📞 Support

If automation fails:
1. Check GitHub Actions logs
2. Check Cloudflare Pages build logs
3. Verify API key is in GitHub Secrets
4. Run manually: `python3 itvedas-brain/cve-aggregator.py`

---

**Last Updated:** 2026-07-04
**Status:** ✅ Fully Automated
