# ITVedas Brain — Status Audit

**Audit date:** 2026-06-18
**Scope:** `itvedas-brain/`, plus the production agents and workflows it depends on (`scripts/`, `brain/`, `.github/workflows/`, `functions/api/`)
**Method:** Static read of all source files, generated artifacts, and workflow definitions in this repository at the current revision.

---

## 1. Executive summary

ITVedas runs two separate automation generations side by side:

1. **Production autopilot** (`scripts/brain.py`, `scripts/news_agent_v2.py`, `brain/*.json`, `.github/workflows/write-article.yml`) — live, scheduled, publishing real content to `main` today.
2. **Brain v2 / knowledge layer** (`itvedas-brain/repo-scanner.py`, `itvedas-brain/knowledge-builder.py`, `.github/workflows/refresh-repository-memory.yml`) — live and scheduled, but it is a **read-only knowledge index**, not a content generator. It does not write articles, does not talk to visitors, and is not yet consumed by anything that touches a user.

Both lanes work end-to-end and are wired into CI. The biggest gap is not "does the brain work" — it does — but **the knowledge base it builds is not used anywhere yet**. It is a well-structured asset sitting unconnected to the career API, the quiz, the chatbot-shaped surfaces, or the content agents that could use it to avoid duplicate/contradictory content.

---

## 2. What exists (inventory)

| Component | Path | Status |
|---|---|---|
| Repository scanner | `itvedas-brain/repo-scanner.py` | ✅ Working — calls GitHub API, classifies files, writes `memory/repository.json` |
| Knowledge builder | `itvedas-brain/knowledge-builder.py` | ✅ Working — reads memory, extracts courses/certs/career paths/tech/personas/FAQs, writes `knowledge/*.json` + `repository_knowledge.json` |
| Repository memory snapshot | `itvedas-brain/memory/repository.json` | ✅ Present, fresh (generated 2026-06-18) |
| Knowledge collections | `itvedas-brain/knowledge/{courses,certifications,career_paths,technologies,student_personas,faq}.json` | ✅ Present — 8 courses, 8 certifications, 8 career paths, 31 technologies, 6 personas, 19 FAQs |
| Permanent knowledge base | `itvedas-brain/repository_knowledge.json` | ✅ Present — 146 relationship edges, summary block, source manifest with SHA-256 per source |
| Auto-refresh workflow | `.github/workflows/refresh-repository-memory.yml` | ✅ Working — triggers on push to content paths, nightly cron, manual dispatch; commits regenerated knowledge back to `main` |
| System documentation | `docs/REPOSITORY_KNOWLEDGE_MAP.md` | ✅ Present — independent architecture audit of the *production* autopilot (not this knowledge layer) |
| Brain v2 scaffold note | `itvedas-brain/README.md` | ✅ Present — explicitly states this folder is for "the next version of the brain" and that live files haven't moved yet |
| Evergreen article agent | `scripts/brain.py` (780 lines) | ✅ Working in production — Mon/Wed/Fri, 5 articles published so far |
| News agent | `scripts/news_agent_v2.py` (449 lines) | ✅ Working in production — 3x/day, 38 news pages published |
| Article/news state | `brain/state.json`, `brain/news_state.json`, `brain/activity.log` | ✅ Present, actively updated |
| Career advice API | `functions/api/career-advice.js` | ✅ Working — Cloudflare Pages Function, calls Claude directly with a hardcoded 8-chapter taxonomy |
| Production publishing workflow | `.github/workflows/write-article.yml` | ✅ Working |
| Post-publish validation | `.github/workflows/validate-static-site.yml` | ⚠️ Working but shallow — five fixed, hardcoded assertions; no general-purpose validation |

**Bottom line on "what exists":** Phase 1 (scanner) and Phase 2 (knowledge builder) of the brain v2 plan are both fully built, tested by their own outputs, and self-updating. That part of the assignment is done.

---

## 3. What is working

- **End-to-end automatic refresh.** Any push touching `articles/**`, `news/**`, `career-*.html`, `functions/**`, `docs/**`, `scripts/**`, or the brain scripts themselves triggers `repo-scanner.py` → `knowledge-builder.py` → validation → commit. A nightly cron (`15 0 * * *`) catches anything missed by path filters. This satisfies the "must update automatically" requirement from Phase 2.
- **Deterministic, auditable outputs.** Every write goes through `write_json_atomic` (temp file + rename) in both scanner and builder — no partial-write corruption risk. Every source file is hashed (SHA-256) in `source_manifest`, so content drift is detectable.
- **Real relationship graph.** `repository_knowledge.json` already encodes the exact examples requested in the Phase 2 spec (SOC Analyst → Cyber Security Course, CEH → Security course, AWS → Cloud course) plus 146 total edges spanning courses, certs, career paths, technologies, personas, and FAQs.
- **Independent content lanes.** The production article/news agents and the new knowledge layer don't collide — they read/write disjoint files — so turning on Phase 2 did not destabilize the live autopilot.
- **Idempotent, safe re-runs.** Both scanner and builder can be re-run any number of times with no side effects beyond regenerating their own output files.

---

## 4. What is missing

Functionally complete as a standalone knowledge index, but it is not yet *used*. Gaps below are described first, ranked by business impact in §5.

- **No consumer of the knowledge base.** Nothing reads `repository_knowledge.json` or `knowledge/*.json` at runtime. The career API (`functions/api/career-advice.js`) hardcodes its own 8-chapter taxonomy independently of `knowledge/courses.json` — two sources of truth for the same data.
- **No chatbot / on-site Q&A surface.** 19 FAQs exist with extracted answers but there is no widget, endpoint, or page that serves them to visitors.
- **No content-gap detection.** The builder knows which technologies/certs have zero matching content (`content_paths: []` would reveal this) but nothing surfaces that as an actionable list — e.g., "no content mentions CISSP" should generate a backlog item or even drive the article calendar in `scripts/brain.py`.
- **No feedback loop into the article calendar.** `scripts/brain.py`'s `CALENDAR` is a static, hand-written list. The knowledge base could tell the calendar which courses/technologies/certs are under-covered, but the two systems are not connected.
- **Course/cert/persona taxonomies are hardcoded in `knowledge-builder.py`**, not derived from any canonical product catalog (there is no real "courses" product data anywhere in the repo — these are inferred from content, not from an authoritative list of what ITVedas actually sells/teaches). If ITVedas's real course catalog diverges from these 8 inferred course buckets, the knowledge base will quietly drift from reality.
- **No search-index integration.** `search-index.json` (used by the homepage search box) is unrelated to and not updated by the knowledge base, despite both being "what content exists" indexes.
- **No validation/CI gate on the knowledge outputs beyond JSON-parseability.** `refresh-repository-memory.yml` checks the files parse as JSON but does not check schema shape, relationship referential integrity (e.g., every `related_course_id` actually exists in `courses.json`), or minimum coverage thresholds.
- **No API access to the knowledge base.** It's a static file in the repo; there's no Cloudflare Pages Function exposing it as `/api/knowledge` for the frontend or third parties to query.
- **No versioning/diffing of knowledge changes.** Each refresh overwrites the previous knowledge base; there's no changelog of "what got added/removed this run," making it hard to audit drift over time or notice regressions (e.g., a FAQ silently disappearing).
- **No deduplication/merge with the production agents' content metadata.** `brain/state.json` already tracks per-article chapter/keyword metadata; `knowledge-builder.py` re-derives similar information from scratch via text scanning instead of reading that structured state, so the two stores can disagree.
- **No tests.** Neither `repo-scanner.py` nor `knowledge-builder.py` has unit tests or fixtures; correctness currently depends entirely on eyeballing output JSON.
- **GitHub token scope/secret dependency undocumented for this workflow.** `repo-scanner.py` calls the public GitHub API and works token-less for public repos, but `refresh-repository-memory.yml` doesn't document what happens if rate-limited (no `GITHUB_TOKEN` is passed to the scanner step's env — only to checkout). Worth confirming this doesn't silently hit unauthenticated rate limits as repo size grows.

---

## 5. What should be built next, ranked by business impact

### Tier 1 — High impact (revenue/conversion-adjacent)

1. **Wire the career API to `knowledge/courses.json` and `career_paths.json`.** Right now the career-advice Cloudflare Function and the knowledge base maintain two independent, divergeable views of "which course matches which career path." Unifying them means every future course/cert/path the knowledge builder discovers automatically improves career-navigator recommendations — the single highest-leverage, lowest-effort change available, since the API already calls Claude and could simply pass the relevant knowledge-base slice as context instead of inline-hardcoding chapters.
2. **Build an on-site FAQ/Q&A surface from `knowledge/faq.json`.** 19 real, extracted FAQs are sitting unused. Serving them (a `/faq` page, or a widget on relevant article/course pages) is direct SEO value (FAQ schema markup, featured snippets) and direct visitor value, for near-zero new engineering — the data extraction is already done.
3. **Feed content-gap analysis into the article calendar.** Cross-reference `knowledge/technologies.json`/`certifications.json` entries with empty or thin `content_paths` against `scripts/brain.py`'s `CALENDAR`. This turns the brain from "writes whatever's next on a fixed list" into "writes what's actually missing," directly increasing organic search surface area for the certs/technologies prospective students search for.

### Tier 2 — Medium impact (trust, SEO compounding, ops efficiency)

4. **Expose the knowledge base via a `/api/knowledge` Cloudflare Function** so the frontend (search, quiz, career navigator) can query it live instead of each surface maintaining its own copy of course/tech/cert facts.
5. **Add schema validation + referential-integrity checks to `refresh-repository-memory.yml`** (every `related_course_id`/`recommended_course_id` resolves; no orphaned relationship edges). This is cheap insurance against the knowledge base silently shipping broken cross-links as content scales.
6. **Reconcile `knowledge-builder.py`'s inferred course/cert/persona taxonomy against ITVedas's actual product catalog** (if one exists outside the repo) so the "8 courses" aren't just an artifact of what the current 8 chapters happen to be.

### Tier 3 — Lower impact (engineering hygiene)

7. **Add unit tests/fixtures** for `repo-scanner.py` classification rules and `knowledge-builder.py` extraction logic (FAQ block matching, alias scoring) so future taxonomy edits don't silently regress coverage.
8. **Add a changelog/diff step** to the refresh workflow that comments on what changed between knowledge-base runs (new/removed FAQs, courses, relationships) for auditability.
9. **Merge `brain/state.json` article metadata into the knowledge-builder's source selection** instead of independently re-deriving chapter/topic via text scanning, to keep the two stores from disagreeing.

---

## 6. One-line verdict

The knowledge layer is built, correct, and auto-refreshing — the work now is **plumbing it into the surfaces that actually talk to visitors** (career navigator, FAQ, content calendar), not building more extraction logic.
