# ITVedas Brain

This folder is the dedicated home for ITVedas autonomous content-generation architecture.

## Current live components

The production autopilot currently runs from these repository paths:

- `itvedas-brain/content-writer.py` - evergreen article generation, review, rendering, catalog updates, state updates, and notifications
- `itvedas-brain/news-agent.py` - RSS ingestion and original news commentary generation
- `itvedas-brain/core/` - shared LLM call (`llm.py`) and logging (`log.py`) helpers used by all brain scripts
- `itvedas-brain/state/state.json` - evergreen article memory and content-calendar progress
- `itvedas-brain/state/news_state.json` - news deduplication and publication history
- `itvedas-brain/state/brain.log` - consolidated activity log shared by all brain scripts (component-prefixed lines)
- `.github/workflows/write-article.yml` - schedules, secrets, execution, commit, and push
- `.github/workflows/validate-static-site.yml` - post-publication validation

## Purpose

Use this directory for the next version of the brain as its configuration, prompts, templates, validation logic, and documentation are separated from the current monolithic scripts.

The legacy top-level `brain/` directory has been consolidated into `itvedas-brain/state/`. All scripts, workflows, and documentation now reference state files under `itvedas-brain/state/`.

See `docs/REPOSITORY_KNOWLEDGE_MAP.md` for the complete system map and migration recommendations.
