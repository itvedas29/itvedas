# ITVedas Brain

This folder is the dedicated home for ITVedas autonomous content-generation architecture.

## Current live components

The production autopilot currently runs from these repository paths:

- `scripts/brain.py` - evergreen article generation, review, rendering, catalog updates, state updates, and notifications
- `scripts/news_agent_v2.py` - RSS ingestion and original news commentary generation
- `brain/state.json` - evergreen article memory and content-calendar progress
- `brain/news_state.json` - news deduplication and publication history
- `brain/activity.log` - evergreen agent activity history
- `.github/workflows/write-article.yml` - schedules, secrets, execution, commit, and push
- `.github/workflows/validate-static-site.yml` - post-publication validation

## Purpose

Use this directory for the next version of the brain as its configuration, prompts, templates, validation logic, and documentation are separated from the current monolithic scripts.

The live files have not been moved yet. This avoids interrupting the existing scheduled autopilot while the new structure is introduced deliberately.

See `docs/REPOSITORY_KNOWLEDGE_MAP.md` for the complete system map and migration recommendations.
