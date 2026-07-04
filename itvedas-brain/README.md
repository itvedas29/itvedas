# ITVedas Publishing Scripts

Automated content publishing for itvedas.com, run by the GitHub Actions
workflow `.github/workflows/write-article.yml` (ITVedas Autopilot):

- **content-writer.py** — writes and publishes a full SEO-optimised article
  Mon / Wed / Fri (9:00 AM IST) into the correct chapter folder.
- **news-agent.py** — refreshes IT & security news hourly and updates the
  homepage Live Security Watch and news pages.
- **core/** — shared helpers (LLM client, logging, IndexNow submission).
- **state/** — publish state (`news_state.json`, `heartbeat.json`).

Both scripts use only the Python standard library. Secrets
(`ANTHROPIC_API_KEY`, etc.) come from GitHub Actions secrets.

The interactive chat bot / agent, COO dashboard, and self-improve
automation were removed in July 2026.
