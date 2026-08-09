# ITVEDAS — Project Audit

**Date:** 2026-08-10
**Purpose:** Ground-truth snapshot of the repository before any Phase 1+ tool-platform work begins, per the ITVEDAS master build prompt (Stage 1). Everything below is verified against actual repo contents (`git log`, file reads, greps) — not taken at face value from existing docs, several of which are stale or aspirational. Discrepancies between docs and reality are called out explicitly.

---

## 1. Current architecture

Static HTML site — **no frontend framework, no build tool, no `package.json`**. ~866+ hand/agent-generated `.html` files with inline `<style>`/`<script>` per page. A shared but inconsistently-adopted design system exists (`css/shared.css`, dark-theme tokens; the homepage uses its own separate light-theme inline tokens — the two don't match).

- **Backend**: exactly two Cloudflare Pages Functions exist — `functions/api/career-advice.js` and `functions/api/subscribe.js`. Nothing else server-side.
- **Content pipeline**: `itvedas-brain/` — Python scripts run by GitHub Actions that write articles (OpenAI drafts, Claude reviews/QA-gates), generate news commentary (Claude), and sync CVE data. This is what the frequent "Autopilot update" commits are.
- **`ARCHITECTURE.md` is not a factual architecture doc** — it's a mission/role-prompt document with unverifiable "Phases 1–15 completed" claims. Treat as aspirational, not current-state.
- **`docs/REPOSITORY_KNOWLEDGE_MAP.md` is stale** (dated 2026-06-18) — describes `scripts/brain.py`/`scripts/news_agent_v2.py`, neither of which exists anymore. Superseded by the current `itvedas-brain/` pipeline.

## 2. Backend

Two Cloudflare Pages Functions only:
- `functions/api/career-advice.js` — powers the Career Navigator quiz. Server-side call to Anthropic (`claude-haiku-4-5-20251001`), origin-allowlist check, input capped at 6000 chars, output fields bounded. No rate limiting or fetch timeout.
- `functions/api/subscribe.js` — newsletter signup. Validates email, dedupes via a Cloudflare KV binding (`env.SUBSCRIBERS`) that **is not declared in `wrangler.toml`** — meaning in the current repo state, subscriptions likely aren't actually persisted anywhere (the endpoint no-ops gracefully and still returns success). The static `data/subscribers.json` (empty) is disconnected dead data.

No rate limiting, SSRF protection, or request-size limiting exists anywhere server-side (not currently needed — neither function proxies arbitrary user-controlled URLs).

## 3. Database

None. Everything is flat JSON/HTML files. No D1, KV bindings (declared), or R2 configured in `wrangler.toml`.

## 4. Deployment

**Cloudflare Pages** (confirmed: `wrangler.toml` with `itvedas.com` zone routing, `functions/api/`, `[build] command = "bash build.sh"`). A **Netlify config previously coexisted and was deleted** (`git log`: commit `ad2d82dd "Delete netlify.toml"`).

**⚠️ Critical, unresolved regression from that deletion**: all security response headers (CSP, HSTS, X-Frame-Options, etc.) were configured through Netlify's header mechanism. Deleting `netlify.toml` silently dropped them — `wrangler.toml` has no equivalent, and there is **no `_headers` file on `main`**. A fix exists but sits unmerged on branch `claude/itvedas-bugs-findings-2b2757`. **Production is very likely currently serving without CSP/HSTS/X-Frame-Options today.** `CHANGELOG.md` and `API.md` both still claim these headers are implemented — they are not, on `main`.

`DEPLOYMENT.md` also documents a self-hosted DigitalOcean droplet (PM2 + cron) as a fallback runner for the content pipeline — plausible but unverifiable from the repo, and its job list (`self-improve.py`, `decision-engine.py`, `execution-engine.py`, `github-agent.py`, `healthcheck.py`) references scripts that **do not currently exist** in `itvedas-brain/` (confirmed by directory listing). `itvedas-brain/README.md` states this class of automation "was removed in July 2026." Treat `DEPLOYMENT.md`'s job list as stale until re-verified.

## 5. Hosting

Cloudflare Pages, custom domain `itvedas.com`.

## 6. Existing routes

Flat, `.html`-suffixed URLs are the current convention: `/tools/json-formatter.html`, `/articles/...`, `/ai-tools/...`, etc. (some newer chapter pages had `.html` stripped from internal links in recent commits, suggesting a partial move toward extension-less URLs via `_redirects`/routing — not fully consistent yet). **This matters directly for Phase 1**: the master prompt specifies clean category URLs like `/developer-tools/json-formatter/`, which is a different pattern than the existing `/tools/*.html` flat structure. This is a real decision point — see recommendations.

## 7. Existing tools — already built (`/tools/`, 14 tools + hub)

| Tool | Real or simulated | Notes |
|---|---|---|
| JSON Formatter | Real, client-side | `JSON.parse`/`stringify`, works |
| Base64 Encoder | Real, client-side | Encode+decode in one page |
| JWT Decoder | Real, client-side | Decode/display only, no signature verification |
| Hash Generator | Real, client-side | — |
| Password Generator | Real, client-side | — |
| CIDR Calculator | Real, client-side | — |
| XML Formatter | Real, client-side | — |
| YAML Formatter | Real, client-side | — |
| HTTP Header Analyzer | Not verified in detail | — |
| SSL Certificate Info | Not verified in detail | — |
| YARA Rule Validator | Real, client-side | — |
| Markdown Preview | Real, client-side | — |
| **DNS Lookup** | **Simulated** | Hardcoded sample data for 2 domains only, explicit on-page disclaimer it's not real |
| **WHOIS Lookup** | **Simulated** | Same — hardcoded sample data, explicit disclaimer |

All 14 are single self-contained HTML files (own inline CSS/JS, no shared component library), each with meta description/OG tags/canonical/`SoftwareApplication` JSON-LD. None have the long-form SEO content sections (Quick Answer/FAQ/How-to/Related Tools) the master prompt's Section 20 template calls for — that's a real gap to close, not a "build from scratch" gap.

**This directly overlaps most of "Phase 1" and "Phase 2" tools in the master prompt.** JSON Formatter and Base64 Encoder already exist; DNS Checker and IP Checker do not exist as real tools (DNS is a simulator). Building these again from scratch would be wasted/duplicate work.

## 8. Existing content

~866+ HTML pages: articles (autopilot-generated, Mon/Wed/Fri + daily news), 8 "chapter" hub pages (guides organized by topic — PowerShell, Azure, IIS, SQL Server, etc.), AI tools directory (`/ai-tools/`, comparisons, tool profiles), career navigator + career paths, CVE database/dashboard, quiz, FAQ, problems-solutions page.

## 9. Existing SEO

Sitemap, robots.txt, canonical URLs, OG/Twitter tags, JSON-LD structured data, and `llms.txt` all exist and are reasonably mature. IndexNow integration pings Bing/Yandex on publish. Robots.txt deliberately **allows** AI crawlers (GPTBot, ClaudeBot, PerplexityBot, etc.) — intentional AI-search-visibility stance, consistent with the master prompt's AIO goals.

**Known live problem**: a 2026-08-06 internal audit (documented in `.github/workflows/write-article.yml`'s own comments) found 77% of the sitemap was autopilot `/news/` pages, with 861 of 1,478 URLs sitting "Discovered - currently not indexed" in Google Search Console. News-publishing cadence was cut from hourly to once/day and per-run article cap from 25→8 in response. `README.md` still incorrectly says news runs hourly — stale doc.

`SEO_OPTIMIZATION_GUIDE.md` and `GSC_GEO_TARGETING_SETUP.md` are dated (2026-07-04) action-plan checklists with unchecked boxes, not confirmation that the described GSC/hreflang work was completed.

## 10. Sitemap

`sitemap.xml` present at root, auto-regenerated by the content pipeline and by `scripts/generate-sitemap.py` in `validate-static-site.yml`.

## 11. Robots.txt

Present, reasonably well-configured (see §9). Blocks scraper bots (Ahrefs/Semrush/MJ12), disallows `/scripts/`, `/functions/`, `/itvedas-brain/`, `/cve-data/`, `.md`/`.json`/`.sh` files.

## 12. Analytics

**GA4 is live in production** (`G-D98BFZSJYP` hardcoded in `index.html`). Several docs (`MONITORING-SETUP.md`, `TRAFFIC-CAPACITY-GUIDE.md`, `CVE-COMPLETE-SOLUTION.md`) incorrectly describe GA4 as optional/pending or explicitly absent — all stale. Google AdSense is also live (`ads.txt` present, publisher ID configured, script loaded on homepage). No dedicated uptime monitor (Pingdom/UptimeRobot) exists; monitoring relies on Cloudflare's dashboard + GitHub Actions run history.

## 13. Existing APIs

Only the two Pages Functions listed in §2. No public/documented REST API beyond those.

## 14. OmniRoute

**No "OmniRoute" integration exists anywhere in this repository** — searched exhaustively (code, docs, config). If this is a system the team uses elsewhere, it has not yet been wired into ITVEDAS. The master prompt's Section 16/53 AI-tools-via-OmniRoute architecture would need to be introduced from scratch.

## 15. AI integrations

Two real integrations, both narrow in scope:
1. **Career Navigator** (`functions/api/career-advice.js`) — the only live, user-facing AI feature on the site. Calls Claude directly (not via OmniRoute).
2. **Content pipeline** (`itvedas-brain/`) — offline automation, not user-facing. OpenAI (`gpt-4o-mini`) drafts articles, Claude reviews/QA-gates and writes news commentary. `README.md` omits OpenAI's role entirely and describes Claude as the sole writer — stale/inaccurate.

## 16. Authentication

None. No accounts, no login, no sessions beyond an anonymous analytics session ID (crypto-random, tracking only, not auth). `SECURITY.md`'s claim of "no user accounts, no user-submitted data stored server-side" is accurate.

## 17. Environment variables

`ANTHROPIC_API_KEY` (required, career-advice + content QA), `OPENAI_API_KEY`/`OPENAI_MODEL` (required for article drafting but undocumented in README/API.md), `GA4_ID`, `NOTIFY_EMAIL`/`SMTP_FROM`/`SMTP_PASS`, `GITHUB_TOKEN`, `NVD_API_KEY` (CVE ingestion rate limit), `ITVEDAS_ENV`/`LOG_LEVEL`/`DEBUG`. `.env.example` also lists `analytics-agent.py`/`search-console-agent.py`/`github-agent.py` env vars for scripts **that no longer exist** — stale, should be pruned. The `env.SUBSCRIBERS` KV binding used in code is not declared in `wrangler.toml` (see §2/§4).

## 18. Tests

8 pytest files covering: subscribe API validation, email edge cases, search-index integrity, HTML structure validation, analytics session-ID entropy/security, QA script logic. No JS/browser-level tests, no E2E tests. Reasonable coverage for what exists, but nothing that would cover new interactive tool pages (JSON formatter logic, DNS lookups, etc.) — Phase 1+ tools will need their own test coverage per the master prompt's Section 37.

## 19. CI/CD

6 GitHub Actions workflows: CVE sync (×2, staggered, **writing to two different, undocumented-as-a-pair JSON files** — `cve-database-full.json` via `scripts/cve_ingestion.py` vs. `data/cves-2025-2026.json` via `itvedas-brain/cve-aggregator.py`, unclear if/how reconciled), static-site validation + sitemap regen on push to `main`, the main "Autopilot" content pipeline (articles + news), a **disabled** 2-hourly publisher workflow (confirmed dead — every run failed on missing `ANTHROPIC_API_KEY`, redundant with the working news-agent path, kept only for manual dispatch), and a one-off link-bug-fix workflow.

## 20. Monitoring

Cloudflare's built-in dashboard + GitHub Actions run history are the only real monitoring surfaces. No `/api/health` endpoint exists yet (master prompt Section 30 calls for one). No Sentry or error-tracking SDK. Search Console is referenced extensively in docs as an active decision input but that's unverifiable from the repo alone.

## 21. Security posture summary

- **Live gap**: security headers dropped in the Netlify→Cloudflare migration, fix unmerged (see §4). Highest-priority item.
- No rate limiting anywhere (honestly disclosed as a gap in `API.md`).
- CORS on `career-advice.js` is `origin`-allowlisted; `subscribe.js` wasn't checked for the same.
- No SSRF exposure currently exists because no tool actually makes user-controlled outbound network calls yet (DNS/WHOIS tools are simulators). **This changes the moment real DNS/IP/HTTP-checker tools are built per the master prompt's Phase 5/6/9** — SSRF protection needs to be designed in from the start for those, not retrofitted.
- `SECURITY.md`'s core claims (no accounts, no server-side user data) are accurate.

## 22. Documentation debt (relevant to future doc maintenance)

Several existing root-level docs are stale and should be corrected or archived rather than left as false ground truth: `ARCHITECTURE.md` (aspirational), `docs/REPOSITORY_KNOWLEDGE_MAP.md` (references deleted scripts), `README.md` (wrong on OpenAI's role and news cadence), `.env.example` (references deleted scripts), `CHANGELOG.md`/`API.md` (claim security headers that aren't live), `CVE-COMPLETE-SOLUTION.md` (claims "no Google Analytics," which is false), `MONITORING-SETUP.md`/`TRAFFIC-CAPACITY-GUIDE.md` (describe GA4 as pending when it's live).

---

## Recommended implementation plan

The master build prompt's Phase 1 tool list overlaps heavily with what already exists. Recommended sequencing:

1. **Fix the security header regression first** (§4/§21) — this is a real, live production gap, cheap to fix (merge or recreate the `_headers` file), and blocks nothing else. Independent of the tools platform work.
2. **Decide the URL/IA strategy before building any new tool page** (§6) — extend the existing `/tools/*.html` flat pattern, or migrate to the master prompt's `/developer-tools/`, `/security-tools/`, `/network-tools/` category structure with redirects from the old URLs. This is a one-way door for SEO (existing tool pages likely have some indexing/backlink equity) and should not be decided unilaterally.
3. **Retrofit the 14 existing tools** to the Section 20 SEO content template (Quick Answer/How-to/FAQ/Related Tools) and Section 17 completion checklist, rather than rebuilding them — they're functionally solid, just thin on content and lacking a related-tools ecosystem.
4. **Build only the genuinely missing Phase 1 tools**: real DNS Checker/Propagation (replacing the simulator, with SSRF protections designed in from the start per §21), real IP Address Checker, HTML Viewer, Regex Tester (with ReDoS protection), Unix Timestamp Converter. Base64 Decoder is already covered by the existing encoder page. JSON Validator/Beautifier/Viewer/Minifier can likely be variants or sections of the existing JSON Formatter rather than four separate near-duplicate pages (avoids the master prompt's own "no thin duplicate pages" rule).
5. Resolve the duplicate CVE pipeline question (§19) and the dead subscribe-KV binding (§2/§17) as smaller cleanup items alongside Phase 1, since they're pre-existing bugs the audit surfaced, not new work.
6. OmniRoute doesn't exist yet — deferred per the master prompt's own Section 53 ("implement later"), not needed for Phase 1 client-side tools.

Do not proceed with tool-building until the URL/IA decision (item 2) is made — it affects the routing and file structure of every subsequent tool page.
