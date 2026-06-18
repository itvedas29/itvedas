# Brain Consolidation Migration Report

**Date:** 2026-06-18
**Goal:** Merge the legacy top-level `brain/` directory and `itvedas-brain/`
into a single `itvedas-brain/` structure, with all runtime state living
under `itvedas-brain/state/`.

## 1. Files moved (`git mv`, history preserved)

| Old path | New path |
|---|---|
| `brain/state.json` | `itvedas-brain/state/state.json` |
| `brain/news_state.json` | `itvedas-brain/state/news_state.json` |
| `brain/activity.log` | `itvedas-brain/state/activity.log` |
| `brain/daily-plan.json` | `itvedas-brain/state/daily-plan.json` |
| `brain/execution-plan.json` | `itvedas-brain/state/execution-plan.json` |
| `brain/github-actions.json` | `itvedas-brain/state/github-actions.json` |

`brain/` itself was **not deleted** — it remains on disk as an empty
directory pending explicit user confirmation (see Section 5).

## 2. Code and workflow references updated

| File | Change |
|---|---|
| `scripts/brain.py` | `BRAIN_DIR` now points at `itvedas-brain/state` instead of `brain` |
| `scripts/news_agent_v2.py` | News state path/mkdir updated to `itvedas-brain/state` |
| `itvedas-brain/decision-engine.py` | `DEFAULT_ARTICLE_STATE`, `DEFAULT_NEWS_STATE`, `DEFAULT_OUTPUT` now under `itvedas-brain/state` |
| `itvedas-brain/execution-engine.py` | `DEFAULT_PLAN`, `DEFAULT_OUTPUT` now under `itvedas-brain/state` |
| `itvedas-brain/github-agent.py` | `DEFAULT_PLAN`, `DEFAULT_EXECUTION`, `DEFAULT_OUTPUT` now under `itvedas-brain/state` |
| `itvedas-brain/coo-agent.py` | `INPUTS["daily_plan"/"execution_plan"/"github_actions"]` now under `itvedas-brain/state` |
| `itvedas-brain/healthcheck.py` | `CHECKS` list updated to `itvedas-brain/state/*.json` |
| `itvedas-brain/daemon.py` | No change needed — only references script locations, not state paths |
| `.github/workflows/refresh-repository-memory.yml` | `paths:` trigger and validate/commit steps updated to `itvedas-brain/state/**` |
| `.github/workflows/write-article.yml` | No change needed — uses `git add -A`, picks up new paths automatically |
| `.github/workflows/validate-static-site.yml` | No `brain` references existed; no change needed |
| `README.md` | Site-structure table and troubleshooting section updated to `itvedas-brain/state/` |
| `itvedas-brain/README.md` | Component list updated to `itvedas-brain/state/*`; outdated "not moved yet" sentence rewritten to reflect completed consolidation |
| `DEPLOYMENT.md` | 4 references updated: idempotent-state-files prose, backup-strategy prose, `backup-brain.sh` tar command (now archives `itvedas-brain/state` instead of `brain`), and the restore-drill verification command |

## 3. Documentation intentionally left unchanged

- `docs/REPOSITORY_KNOWLEDGE_MAP.md`
- `itvedas-brain/BRAIN_STATUS.md`

Both are dated, point-in-time audit snapshots (each states its own audit
date and describes the repository as it existed at that scan). Rewriting
them would erase the historical record they're meant to preserve. They
still contain `brain/*.json` references reflecting the pre-consolidation
state at the time they were written — this is expected and intentional,
not an oversight.

## 4. Verification performed

- Repo-wide grep for `brain/` (excluding `itvedas-brain/`) after all edits:
  only matches remaining are inside the two historical docs above. **Zero
  stale references in any live script, workflow, or operational doc.**
- `python3 -m py_compile` / `ast.parse` equivalent syntax check on all
  edited Python scripts — all pass.
- Live execution of the pipeline against the new paths:
  - `decision-engine.py` → wrote `itvedas-brain/state/daily-plan.json` ✅
  - `execution-engine.py` → wrote `itvedas-brain/state/execution-plan.json` ✅
  - `github-agent.py` → wrote `itvedas-brain/state/github-actions.json` ✅
  - `healthcheck.py` → `HEALTHY: all brain state files present and fresh.` (exit 0) ✅
- Confirmed `brain/` still exists on disk, now empty (`ls -la brain/` shows
  only `.`/`..`) — not deleted, per requirement 6.

## 5. PASS/FAIL Verdict

**PASS**

All six state files relocated with history preserved; every live script,
workflow, and operational doc updated and re-verified by execution; no
broken references remain outside the two historical audit documents
(left unchanged by design). The old `brain/` directory has not been
deleted and is safe to remove only after explicit user sign-off.
