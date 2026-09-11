# ITVedas Architecture

## Product surfaces

- **Learn** — chapters, articles, tutorials and problem/solution content.
- **Tools** — free IT/developer/security utilities, Career Navigator and CVE search.
- **News** — original ITVedas commentary generated from curated IT/security feeds.
- **Security intelligence** — canonical CVE dataset with NVD records, CISA KEV status and GitHub advisory enrichment.
- **Services** — IT service information and future marketplace entry point.
- **ManageEngine** — product/affiliate information pages.

## Runtime

ITVedas is primarily a static site deployed on Cloudflare Pages. Public APIs live under `functions/api/`. Secrets stay in Cloudflare/GitHub Actions environment variables and are never committed.

## Authoritative data flows

```text
NVD CVE API ─┐
CISA KEV ────┼──> scripts/cve_unified_sync.py ──> cve-database-full.json
GitHub GHSA ─┘                                      │
                                                    └─> cve-data/ detail files

RSS feeds ──> itvedas-brain/news-agent.py ──> news/*.html
                                      │
                                      └─> scripts/news-quality-gate.py
                                             │
                                             ├─ thin/duplicate -> noindex
                                             └─ indexable -> sitemap

AI topic demand ──> itvedas-brain/content-writer.py ──> articles/chapters

HTML sources ──> scripts/generate-search-index.py
HTML sources ──> scripts/generate-sitemap.py (indexable pages only)
```

## CI/CD

`validate-static-site.yml` runs on pull requests and main pushes. It validates JSON, JavaScript syntax, security patterns, Markdown sanitization, GA4 script hygiene, news quality and sitemap/noindex consistency.

The autopilot workflow runs deep articles three days a week and news once per day. News is gated before the archive/sitemap is rebuilt.

## CVE rules

`cve-database-full.json` is the single source of truth. NVD supplies canonical records and modified records are refreshed. CISA KEV alone determines `known_exploited`. GitHub advisories are supplemental references only.

The CVE sync uses overlapping modification windows so clock/API boundary delays do not create permanent gaps. The sync is idempotent by CVE ID.

## News quality rules

Generated news is not automatically assumed to be index-worthy. The quality gate marks pages with fewer than 350 words or high headline similarity to an older page as `noindex,follow`. `generate-sitemap.py` excludes all noindex pages.

This is intentionally a quality-first strategy: fewer useful pages are preferable to large clusters of near-duplicate URLs.

## Security principles

1. Never expose AI/provider keys to browser JavaScript.
2. Sanitize untrusted HTML before DOM insertion.
3. Public AI endpoints require input limits and should use Cloudflare rate limiting in production.
4. Mutable third-party scripts must not use stale SRI hashes.
5. CI permissions are read-only unless a workflow genuinely needs to publish.

## Change ownership

- CVE ingestion: `scripts/cve_unified_sync.py` + `cve-daily-sync.yml`
- News automation: `itvedas-brain/news-agent.py` + `scripts/news-quality-gate.py`
- Evergreen content: `itvedas-brain/content-writer.py`
- Search index: `scripts/generate-search-index.py`
- Sitemap: `scripts/generate-sitemap.py`
- Security validation: `scripts/security-check.sh` + `validate-static-site.yml`
- Cloudflare APIs: `functions/api/`
