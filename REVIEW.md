# ITVedas repository review

**Reviewed:** `itvedas29/itvedas` @ `88461d4` (`main`, 2026-10-31, "Autopilot update 2026-10-31 09:34 UTC"), shallow clone.
**Method:** static analysis of every file type, a custom scan of all 1,845 HTML pages (links, metadata, headings, images), a read of all 9 Pages Functions and all 6 workflows, and read-only `GET` requests against the live site to confirm what is publicly served.
**Not done:** the repo's own build, linter, and tests were **not executed** (the review was kept to static analysis). No files in the repo were changed apart from adding this report.

Severity key: **Critical** = active data exposure or integrity loss; **High** = real user or business impact, fix soon; **Medium** = correctness, cost, or maintainability risk; **Low** = hygiene.
Each finding is marked **Confirmed** (verified in code or on the live site) or **Suspected** (likely, but not verified).

---

## Overall verdict

ITVedas is a well-built static site. Its serverless handlers are careful: they validate input, escape output, compare tokens in constant time, and keep secrets server-side. Its CI is also more disciplined than most bot-driven repos. The main problem is deployment shape. Cloudflare Pages publishes the **whole repository root**, so pipeline code, tests, internal docs, Apps Script source, and an unrelated personal project are all downloadable from www.itvedas.com. The next problems are a Google Sheets formula-injection path in the quiz flow and a 26 MB CVE index that ships to every visitor of the CVE listing.

## Executive summary: top 5 to fix first

| # | Issue | Severity | Effort |
|---|---|---|---|
| 1 | Whole repo is served publicly (pipeline code, tests, docs, Apps Script, personal uploads) | High | Medium |
| 2 | Quiz names are written to Google Sheets unescaped, so formula injection is possible; `/api/quiz-submit` has no rate limit | High | Small |
| 3 | CVE listing and dashboard download a 26 MB JSON file (4 MB compressed) on every visit | High | Medium |
| 4 | Autopilot's `cancel-in-progress: true` shares a concurrency group with the CVE sync and can cancel it mid-run | Medium | Small |
| 5 | 115 `/ai-tools/` pages are missing from the sitemap, and 10 internal links are broken | Medium | Small |

---

## Project map

| Aspect | What it is |
|---|---|
| Framework | None. Hand-written and generated **static HTML** (1,845 pages), with no bundler and no `package.json` |
| Hosting | **Cloudflare Pages**, Git-connected to `main`, with **no build command and no output directory**, so the repo root is the site (`wrangler.toml:1-14`) |
| Server code | **Cloudflare Pages Functions** in `functions/api/*.js` (9 endpoints: subscribe, quiz-submit, quiz-questions, reviews, reviews-admin, career-advice (Gemini), dns-lookup, whois-lookup (RDAP), my-ip) |
| Routing | File-based clean URLs, plus `_redirects` (CVE rewrites `/cve/:id` → `/cve-detail`, consolidation 301s) and `_headers` (CSP, HSTS, caching) |
| Page layout | Root landing pages (`index.html`, `news.html`, `quiz.html`, CVE pages, …); content in `articles/` (160), `chapters/` (127), `news/` (1,330), `ai-tools/` (115), `tools/` (22 interactive tools), `software/`, `manageengine/`, `resources/`, `toolkit/` |
| Shared UI | `js/site-nav.js` + `css/site-nav.css` injected into 1,788 pages by `scripts/apply-site-nav.py`; `css/shared.css` for tokens |
| Styling | Plain CSS with custom properties, plus large amounts of inline `<style>` and `style=""` in generated pages |
| Content pipeline | Python in `itvedas-brain/` (Claude API via `anthropic==1.11.0`) writes articles and news on a schedule; 59 helper scripts in `scripts/` handle sitemap, search index, schema, nav, and CVE work |
| Data sources | `cve-data/cve-summary-index.json` (28.9 MB) and 1,648 detail shards, `cve-database-full.json.gz` (13.5 MB), `search-index.json` (2.5 MB), `quiz-data.json`, `data/*.json`; Google Sheets (via Apps Script) for newsletter and quiz; Cloudflare KV for reviews and rate limits |
| CI/CD | 6 GitHub Actions workflows: validation on push/PR, Autopilot content (daily, plus Mon/Wed/Fri), CVE sync (daily), SEO audit (weekly), and 2 manual ones |
| Tests | Python `unittest` suite in `tests/` (13 files); one test exercises `subscribe.js` through Node |
| Size | 3,997 files, 416 MB working tree; the full-history pack is **520 MB** |

---

## 1. Correctness & bugs

**C1 — 10 broken internal links. Medium, Confirmed.**
Found by resolving all 84,583 internal `href`/`src` values against files and `_redirects`:
- `chapters/cloud/2026-07-03-aws-s3-explained-object-storage-for-beginners.html:197`: four links to AWS chapter pages that don't exist (`2026-06-15-aws-cloudfront-cdn-explained`, `2026-05-20-aws-cloudtrail-logging`, `2026-06-01-aws-lambda-serverless-computing`, `2026-04-10-aws-ebs-explained`).
- `chapters/linux/2026-07-03-cron-jobs-explained-schedule-tasks-in-linux.html:308`: links to `shell-scripting-guide`, `linux-file-permissions-guide`, and `systemd-services-linux`, none of which exist.
- `chapters/hardware/index.html:119`: links to the old slug `…how-a-cpu-works-the-fetch-decode-execute-cycle-exp.html` (the live page is `…how-a-cpu-works-architecture-cores-and…`, `:146`). The `how-ram-works…` link has the same problem.
- `toolkit/it-onboarding-audit/index.html:488`: `/feedback`, a route that doesn't exist.

Why it matters: these are 404s for readers and wasted crawl budget. The links look LLM-invented, which suggests the article writer's link check doesn't cover chapter pages.

**C2 — The quiz "certificate" score is trusted from the client. Medium, Confirmed.**
`functions/api/quiz-submit.js:56-63` accepts whatever `score` (0–10) the browser sends. The answer key is also public: `quiz-data.json` holds the correct answer in every question tuple, and `/api/quiz-questions` returns it in full (`quiz-questions.js:70-75`). Anyone can `POST {"score":10}`. If results or certificates carry any weight, scoring has to happen server-side against question IDs.

**C3 — `quiz.html` has two `<h1>` elements and 68 articles have duplicate H1s. Low, Confirmed.**
`quiz.html:76,78` puts one `<h1>` on each screen. In articles, the H1 is emitted twice, for example `articles/2026-07-13-databases.html:136` and `:141`. 68 of the 160 files in `articles/` are affected, which points to a template bug in the generator, since the hero H1 and the body H1 are both kept.

**C4 — Unhandled KV failures return a raw 500. Low, Suspected.**
`quiz-questions.js:50` and `subscribe.js:55-58` call `KV.put` on every request outside any `try`. On Cloudflare's free tier (1,000 KV writes per day), heavy quiz traffic would exhaust the quota, and every later quiz start would throw. I couldn't verify the plan tier.

**C5 — Rate limiting uses non-atomic read-modify-write. Low, Confirmed (by design).**
`career-advice.js:171-188` does `get`, then `put` on eventually consistent KV, so parallel bursts can go past 5 per 10 minutes. This is acceptable for cost control, but it shouldn't be thought of as a hard limit. Cloudflare's Rate Limiting binding is the robust option.

**C6 — There is no subscriber ID in the newsletter sheet. Medium, Confirmed.**
No layer creates one. `Code.gs:46-47,63` writes exactly 5 columns (time, email, source, consent, status), always from column A. A manually added "Subscriber ID" column on the left therefore gets the timestamp, and the other columns shift. Fix: generate an ID under the existing lock, add it as the **last** column, and create a **new deployment version** of the Apps Script.

## 2. Security

**S1 — The entire repository is publicly downloadable. High, Confirmed on the live site.**
Pages deploys the repo root with no output directory (`wrangler.toml:5-8`). `robots.txt:15-21` only asks crawlers not to index these paths; it is not access control. Verified with HTTP 200 responses:
`/itvedas-brain/content-writer.py`, `/itvedas-brain/core/llm.py`, `/integrations/google-sheets-newsletter/Code.gs` (contains the production `SPREADSHEET_ID`, `Code.gs:1`), `/tests/test_api_subscribe.py`, `/scripts/security-check.sh`, `/docs/SECURITY-OPERATIONS.md`, `/wrangler.toml`, `/api-cve-server.js`, `/knowledge-imports/repos.json`.
`knowledge-imports/uploads/jcode/` is the owner's unrelated **personal Rust project** (its `AGENTS.md` describes local paths and workflows), and it is published on the website.
No credentials were found, so this isn't critical. But it exposes the security tooling, prompts, internal operations docs, and attack-surface details to anyone.
Fix: deploy from a dedicated output directory, either through a build step that copies only public assets into `public/` or by moving the site into `site/` and setting it as the Pages output directory. In the meantime, add `_redirects` 404 rules for `/itvedas-brain/*`, `/scripts/*`, `/tests/*`, `/docs/*`, `/integrations/*`, `/knowledge-imports/*`, `/*.py`, `/*.md`, and `/*.toml`, and remove `knowledge-imports/uploads/jcode` from the repo.

**S2 — Formula injection into Google Sheets via the quiz name. High, Confirmed in code (not exploited).**
`Code.gs:93` and `Code.gs:130` pass the user-supplied `name` (and `topics`, `:130`) straight to `appendRow`, which interprets strings beginning with `=`, `+`, `-` or `@` as formulas. Only the email column is forced to plain text (`Code.gs:92,129`). A quiz entrant named `=HYPERLINK("https://evil.example","Click")` or `=IMPORTXML(...)` puts a live formula in a sheet that staff open while logged in. The newsletter path is safe, because email is validated and column B is set to text first.
Fix: prefix any value starting with `= + - @ \t \r` with `'`, or set every written column to `@` format before appending.

**S3 — `/api/quiz-submit` has no rate limit and no dedupe. High, Confirmed.**
`quiz-submit.js:15-84` checks Origin and consent, then appends a row for **every** request. `stage: "start"` writes a "Quiz Participants" row every time a quiz begins (`Code.gs:73-101`). `/api/subscribe` (`subscribe.js:52-59`) and `/api/reviews` (`reviews.js:64-71`) both throttle; this endpoint doesn't. The Origin check is only a header, so a script can send arbitrary names and emails into the sheet indefinitely, which also creates false personal-data records.
Fix: reuse the hashed-IP KV throttle from `subscribe.js`.

**S4 — The CSP allows `'unsafe-inline'` scripts. Medium, Confirmed.**
`_headers:7` sets `script-src 'self' 'unsafe-inline' …`. 29 pages still use inline `on*=` handlers, and all generated pages have inline `<script>` blocks, so the CSP gives almost no XSS protection. The existing escaping discipline is good (see Strengths), so this is defence-in-depth. `connect-src 'self' https:` is also broad, but `_headers:2-4` documents why.
Fix: move inline handlers to `js/inline-handler-setup.js` (it already exists), then switch to hashes or nonces.

**S5 — Origin checks are inconsistent. Low, Confirmed.**
`reviews.js:48` and `career-advice.js:41` *allow requests with no Origin header* (so curl works), while `subscribe.js:20` and `quiz-submit.js:19` require one. The allowlist is copy-pasted four times with different localhost rules. The comment at `career-advice.js:33` correctly says this isn't a security boundary.

**S6 — Raw IP stored in a KV key. Low, Confirmed.**
`career-advice.js:172` uses `career-rate:${ip}`, while every other handler hashes the IP (`subscribe.js:54`, `reviews.js:66`, `quiz-questions.js:36`). That's inconsistent with the privacy approach of the rest of the site.

**S7 — The JWT decoder renders an error message with `innerHTML`. Low, Confirmed (self-XSS only).**
`tools/jwt-decoder.html:245` sets `innerHTML = \`…${e.message}…\``. The input is the visitor's own pasted token, so the impact is self-XSS. Use `textContent` instead.

**S8 — Actions pinned to mutable tags. Low, Confirmed.**
All workflows use `actions/checkout@v4`, `setup-python@v5`, and `upload-artifact@v4`. Three of them hold `contents: write` (`write-article.yml:19-20`, `cve-daily-sync.yml:13-14`, `fix-article-link-bugs.yml:19-20`). Pin to commit SHAs.

**S9 — DNS, WHOIS, and My-IP endpoints have no rate limit. Low, Confirmed.**
`dns-lookup.js`, `whois-lookup.js`, and `my-ip.js` are open relays to the Cloudflare DoH and RDAP servers. There's no SSRF risk, since the targets are fixed or come from IANA bootstrap data, but the site could be used to proxy lookup volume.

**No committed secrets found. Confirmed.** A grep for Anthropic, OpenAI, AWS, GitHub, Slack, Google, and private-key patterns came back clean outside data files. The IndexNow key file at the root is public by design (`README.md`).

## 3. Performance

**P1 — The CVE listing and dashboard ship the full CVE index. High, Confirmed on the live site.**
`cve-listing.html:550`, `cve-dashboard-advanced.html:677`, and `js/cve-loader.js` fetch `/cve-data/cve-summary-index.json`: **26.0 MB raw, 4.0 MB over the wire** (measured). It is then parsed and copied into IndexedDB on the main thread. On mid-range phones this takes seconds of parse time and a lot of memory. The detail page already uses 250-CVE shards (`cve-detail.html:713-725`), which shows the right pattern.
Fix: publish a slim listing index (id, severity, cvss, year, vendor) split by year, page or filter, or search through a Pages Function.

**P2 — Repository growth from bot commits. Medium, Confirmed.**
`cve-summary-index.json` has been rewritten in **57 commits since 2026-09-01**, about 4 MB compressed each. The full-history pack is already **520 MB**, and `assets/affiliate/manageengine/` holds about 100 MB of PDF/PPTX/GIF. The workflows work around this with `fetch-depth: 1`, but fresh clones and Pages build checkouts keep getting slower.
Fix: move generated CVE data to R2 or KV (or at least out of git), and keep affiliate binaries in R2.

**P3 — 11 unused JavaScript files (about 68 KB). Low, Confirmed.**
These aren't referenced by any HTML or JS: `accessibility-audit.js`, `accessibility-enhancements.js`, `advanced-search.js`, `analytics-tracker.js`, `brand-logos.js` (16.5 KB), `cache-optimizer.js`, `content-hierarchy.js`, `nav-mobile.js`, `nav-search.js`, `performance-optimization.js`, `related-content.js`. They aren't downloaded, but they're deployed and they confuse maintainers.

**P4 — Site search fetches the whole 2.5 MB `search-index.json`. Low, Confirmed.**
`js/site-nav.js:137-148` lazy-loads it only when search opens, which is good, but it's still large for a quick-find feature. `index.html:735` also loads it.

**P5 — Images missing `loading` and `width`. Low, Confirmed.**
Of 30 `<img>` tags, 19 have no `loading="lazy"` and 20 have no `width`/`height`, which causes layout shift. One 1.5 MB PNG, `chapters/networking/images/2026-08-12-what-is-an-ip-address-complete-guide.png`, should be WebP or AVIF.

**P6 — Short HTML cache. Low, Suspected.**
`_headers:13` gives every HTML page `max-age=3600, must-revalidate`. That's fine for a site updated daily; it's listed here only as a note.

## 4. Accessibility

**A1 — The focus ring is low contrast. Medium, Confirmed.**
`css/site-nav.css:9,46` uses a focus outline of `--sn-orange: #FF7A00` on a white header, a **2.61:1** ratio. WCAG 1.4.11 needs 3:1 for focus indicators, and this nav is on 1,788 pages. Use `--sn-orange-dark` (`#B35500`, already defined) for the outline.

**A2 — Muted text and placeholders fall below AA. Low, Confirmed.**
`#6B7A94` on white is 4.34:1 (AA needs 4.5:1), used inline on 101 pages. Placeholder colour `#94A3B8` (`css/shared.css:447`) is 2.56:1. `#FF6B35` appears as a text colour on 1,592 pages and is 2.84:1 on white. Whether it sits on a light or dark background is **Suspected, not verified page by page**.

**A3 — Heading order. Low, Confirmed.** 64 pages skip heading levels (for example h2 → h4). The 68 duplicate-H1 articles (C3) also hurt screen-reader navigation.

**A4 — Focus handling elsewhere is good. Confirmed.** Skip links are present (`css/shared.css:216`, `site-nav.css:52`), `:focus-visible` is used, and form inputs replace `outline:none` with a visible box-shadow (`shared.css:440-444`). 26 pages contain `outline:none` in inline styles and are worth a spot check.

**A5 — Alt text. Confirmed OK.** All 30 `<img>` tags have an `alt` attribute. All pages except the `partials/` fragment and the LinkedIn studio tool have `lang` and `viewport`.

## 5. SEO & metadata

**SEO1 — 115 `/ai-tools/` pages are missing from the sitemap. Medium, Confirmed.**
`scripts/generate-sitemap.py:39` builds its bucket list without `ai-tools`, so none of the 115 indexable pages under `ai-tools/` are submitted. `resources/*.html` (5 pages), `author/index.html`, and `cve-database.html` are also left out. Older news (1,186 pages) is excluded **on purpose** by `NEWS_SITEMAP_DAYS=60` (`generate-sitemap.py:5-7`). That's a deliberate choice, but it means most of the site's pages rely on internal links to be discovered.

**SEO2 — Titles longer than 65 characters. Low, Confirmed.** 1,397 of 1,845 pages, mostly news, where the slug-length headline is followed by `| ITVedas`. They'll be truncated in search results.

**SEO3 — Missing Open Graph tags. Low, Confirmed.** 59 pages, including `news.html`, `security-news.html`, `specs.html`, `ai-tools/comparisons/*`, and `articles/ai-models/*`.

**SEO4 — Missing canonical or description. Low, Confirmed.** No canonical on `specs.html` or 4 `software/manageengine-*/index.html` drafts. Those drafts also share the description "Draft spec sheet, not yet verified.", so either noindex them or finish them.

**SEO5 — Template pages are deployed and indexable. Low, Confirmed.** `cve-data/cve-listing-template.html` duplicates the title and description of `cve-listing.html`, and `cve-data/cve-detail-template.html` has no description. Note that `robots.txt:19` blocks `/cve-data/`, which also blocks crawling of the detail shards. That doesn't matter, because detail pages render client-side.

**SEO6 — Generally strong. Confirmed.** 1,788 pages carry JSON-LD and none failed to parse. Canonicals use the www host, and no canonical has a `.html` extension. The sitemap has 452 URLs, all of which resolve. `robots.txt` names the sitemap.

## 6. Code quality & maintainability

**Q1 — Overlapping one-off scripts. Medium, Confirmed.**
`scripts/` has 59 files, several of them one-time migrations doing similar jobs: `add-schema-markup.py`, `add-comprehensive-schema.py`, `add-remaining-schema.py`, `batch-add-schema-all.py`, `enhance-article-schemas.py`, `phase-9-15-comprehensive.py`; `fix-heading-hierarchy.py` and `auto-fix-heading-hierarchy.py`; `traffic-recovery-sitemap.py` and `generate-sitemap.py`. Nobody can tell which is canonical.
Fix: move finished migrations to `scripts/archive/` and document the live set in `scripts/README`.

**Q2 — Minified JS committed without source. Medium, Confirmed.**
`js/cve-loader.js`, `advanced-search.js`, `documentation-ui.js` (52 pages), `nav-search.js`, and others are single-line minified files with no unminified source in the repo, so they can't really be reviewed or changed.

**Q3 — Duplicated helpers across Functions. Low, Confirmed.**
`jsonResponse`, the origin allowlist, SHA-256 hashing, and `toArpaName` are copy-pasted. `toArpaName` is identical in `dns-lookup.js:129-155` and `my-ip.js:45-71`. Put them in `functions/_lib/`.

**Q4 — Dead or legacy code at the repo root. Low, Confirmed.**
`build.sh` never runs (`wrangler.toml:5-8` says there's no build). `api-cve-server.js` is a standalone Node server unrelated to Pages, yet it's deployed. `cve-database-complete.json` and `cve-enrichment-report.json` aren't referenced anywhere. `fix-article-link-bugs.yml` is a finished one-time workflow.

**Q5 — Stale comments and docs. Low, Confirmed.**
`career-advice.js:85` says it "matches itvedas-brain/core/llm.py", but `llm.py` is Claude-only. `README.md` lists `drafts/` in the site structure, but `.gitignore:31-33` excludes it.

**Q6 — Test gaps. Medium, Confirmed.**
Only `subscribe.js` has an executable handler test (`tests/test_api_subscribe.py`). `quiz-submit`, `quiz-questions`, `reviews`, `reviews-admin` (auth), `career-advice`, and `Code.gs` have none, and the injection and rate-limit gaps in S2/S3 are exactly what tests would have caught. CI runs `unittest` (`validate-static-site.yml:39-40`), while `tests/requirements-test.txt` lists `pytest`, `pytest-cov`, and `pytest-asyncio`, which CI never installs.

## 7. Config & deployment

**D1 — Concurrency groups can cancel the CVE sync. Medium, Confirmed in config.**
`write-article.yml:26-28` uses `group: repo-writer`, `cancel-in-progress: true`. `cve-daily-sync.yml:16-18` and `fix-article-link-bugs.yml:12-14` share that group with `cancel-in-progress: false`. In GitHub Actions, the newly queued run's setting decides, so an Autopilot run (scheduled or manual) **cancels an in-progress CVE sync**, possibly between commit and push. It also cancels an earlier Autopilot run that has already spent LLM tokens. Set Autopilot to `cancel-in-progress: false`.

**D2 — Validation regenerates files but never checks for drift. Low, Confirmed.**
`validate-static-site.yml:24-29` runs `normalize-ga4-tags.py`, `generate-sitemap.py`, and `generate-search-index.py`, then validates the *regenerated* output and throws it away. A stale committed sitemap or search index still passes. Add `git diff --exit-code` after regeneration.

**D3 — Unpinned pipeline dependencies. Low, Confirmed.**
`write-article.yml:47` installs `pytrends` and `"urllib3<2"` unpinned, and the CVE sync installs `requests` unpinned (`cve-daily-sync.yml:36`). Only `anthropic` is pinned (`requirements.txt:4`).

**D4 — No linter or formatter. Low, Confirmed.**
There's no ESLint, Prettier, Ruff, or HTML validator config. CI only runs `node --check` for syntax (`validate-static-site.yml:43-45`).

**D5 — Fresh clone and environment. Confirmed OK.**
The static site works from a fresh clone with no build. `.env.example` documents the pipeline variables. Cloudflare-side secrets (`GOOGLE_SHEETS_*`, `REVIEWS_ADMIN_TOKEN`, `GEMINI_API_KEY`, KV bindings) are documented in the handler headers and `docs/`, but not in `.env.example`.

## 8. Content & UX consistency

**U1 — Draft pages are live. Low, Confirmed.** Four `software/manageengine-*` pages say "Draft spec sheet, not yet verified." and have no canonical (SEO4).

**U2 — Possible LLM-invented links and content. Medium, Suspected.** The C1 broken links all have plausible but non-existent slugs, which suggests generated cross-links aren't checked against the file tree before publishing. Worth adding a link check to the publish gate in `itvedas-brain/content-writer.py`.

**U3 — Inconsistent styling. Low, Confirmed.** Generated pages use heavy inline `style=""` (for example `chapters/hardware/index.html:146`) alongside `css/shared.css` tokens, so the same component looks slightly different across sections. Responsive layouts were **not checked in a browser**.

---

## Strengths

- **Output escaping is consistent.** CVE pages, DNS, WHOIS, career-navigator, and software pages escape with `escapeHtml` or `textContent` (`cve-listing.html:643-690`, `cve-detail.html:810-836`), and the Markdown preview goes through a sanitizer that CI checks for regressions (`validate-static-site.yml:46-54`).
- **Secrets stay server-side.** The Gemini key goes in a header, not the URL (`career-advice.js:114-130`), the Sheets secret only travels server-to-server, and the reviews admin token is compared in constant time (`reviews-admin.js:76-86`).
- **Privacy is handled carefully.** IPs are hashed for throttles and quiz rotation, there are consent checks, and a honeypot on reviews.
- **The SSRF analysis is correct.** DNS and RDAP targets are fixed or come from IANA.
- **Security headers are good.** HSTS preload, `frame-ancestors 'none'`, `nosniff`, a strict `Permissions-Policy`, and `object-src 'none'`.
- **Bot workflows are well behaved.** Least-privilege `permissions`, `fetch-depth: 1`, rebase-and-retry on push, and freshness checks.

---

## Prioritized action plan

| Priority | Action | Findings | Effort |
|---|---|---|---|
| 1 | Escape formula characters in `Code.gs` for every written cell; add a hashed-IP throttle to `quiz-submit.js`; redeploy the Apps Script as a new version | S2, S3 | Small |
| 2 | Block non-site paths with `_redirects` 404 rules now; delete `knowledge-imports/uploads/jcode` | S1 | Small |
| 3 | Set `cancel-in-progress: false` in `write-article.yml` | D1 | Small |
| 4 | Fix the 10 broken links; add `ai-tools` (and `resources`, `author`) to `generate-sitemap.py`; noindex or finish the draft software pages | C1, SEO1, SEO4, U1 | Small |
| 5 | Change the focus-ring colour to `--sn-orange-dark`; fix the muted and placeholder colours | A1, A2 | Small |
| 6 | Add a Subscriber ID column (last column, generated under lock) | C6 | Small |
| 7 | Fix the duplicate-H1 template in the article generator and backfill the 68 articles | C3, A3 | Small–Medium |
| 8 | Move to a real Pages output directory (`public/`) built by a whitelist copy step | S1 | Medium |
| 9 | Replace the 26 MB CVE index with a slim, sharded listing index or a search Function | P1 | Medium |
| 10 | Score the quiz server-side; stop returning answers from `/api/quiz-questions` | C2 | Medium |
| 11 | Add handler tests for quiz-submit, reviews, reviews-admin, and career-advice; add `git diff --exit-code` drift checks; pin action SHAs and pipeline deps | Q6, D2, D3, S8 | Medium |
| 12 | Move inline handlers out of pages and tighten the CSP to remove `'unsafe-inline'` | S4 | Medium–Large |
| 13 | Archive one-off scripts, delete the 11 unused JS files and root orphans, commit unminified sources | Q1, Q2, Q4, P3 | Medium |
| 14 | Move generated CVE data and affiliate binaries out of git (R2/KV) to stop the repo growing | P2 | Large |

---

## What was not checked

- The repo's own tests, build, linter, and validators were **not run**. The results above are static analysis plus read-only live HTTP checks.
- `npm`/`pip` vulnerability scanning wasn't possible because there's no JS lockfile; only `anthropic==1.11.0` is pinned.
- Responsive layout, real colour contrast in rendered pages, and keyboard flow weren't tested in a browser.
- Cloudflare dashboard settings (KV bindings, secrets, plan tier) and the Google Sheet itself weren't accessible.
- News and article copy wasn't proofread for typos at scale; only structural issues were checked.
