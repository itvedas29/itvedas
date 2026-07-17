# Archive

One-off / exploratory scripts that aren't wired into any GitHub Actions
workflow and have no other script depending on them (verified by grep
across the repo before moving anything here — see the audit that added
this folder). Moved out of the active `itvedas-brain/` script surface
so it's obvious at a glance which scripts are actually part of the live
pipeline (`content-writer.py`, `news-agent.py`, `cve-aggregator.py`)
versus historical/manual tooling.

- `batch-generate-phase6.py`, `generate-phase6-articles.py`,
  `generate-phase6-articles-local.py`, `phase6-content-generator.py`,
  `phase6-publisher.py` — five different one-off generators used
  interactively to hand-build the Phase 6 content calendar (see commit
  `ed0e1b6`, "Phase 6: Complete Enterprise Knowledge Library
  Implementation"). Not run since.
- `video-generator-2hourly.py` — never wired into a workflow.
- `gsc-monitoring-analyzer.py`, `update-chapter-indices.py`,
  `add-hreflang-tags.py` — standalone maintenance scripts, safe to run
  manually if needed, just not part of the automated pipeline.

Safe to delete entirely once you've confirmed you don't need any of
these for reference. Nothing in the active codebase imports or shells
out to anything in this folder.
