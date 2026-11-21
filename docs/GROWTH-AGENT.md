# Growth agent

`itvedas-brain/growth-agent.py` is the site's SEO / AEO manager. The content
writer and news agent publish; the growth agent decides what is worth
publishing and repairs what under-performs, from real Search Console and GA4
data. It runs every Tuesday (`.github/workflows/growth-agent.yml`) with no one
in the loop.

## What it does each week

| Step | Action | Goes live automatically? |
| --- | --- | --- |
| Measure | Reads 28 days of Search Console (clicks, impressions, CTR, position by page and query) and GA4 (sessions by channel, visits referred by ChatGPT, Perplexity, Gemini, Copilot, Claude and similar) and compares with the 28 days before. | n/a |
| Judge | Every title/description it rewrote 28+ days ago is re-measured. If CTR fell by 30%+ at a comparable ranking, the original tags are restored byte-for-byte. | Yes |
| Fix snippets | Pages ranking in the top ~12 with far fewer clicks than that position normally earns get a new `<title>` and meta description written by Claude (max 5 per run). | Yes |
| Plan topics | Searches Google already shows the site for, but only beyond position 12, become new article topics (max 2 per run) in `itvedas-brain/state/growth_queue.json`. | Written by `content-writer.py` on its Mon/Wed/Fri runs, through its existing review gate |
| Plan refreshes | Articles with queries stuck at positions 5-20 are queued for a rewrite that answers those queries directly (max 1 per run). | Same |
| AEO | Refresh prompts ask for a direct one-to-two sentence answer per query (what AI assistants quote), and `llms.txt` gets a "Most-read guides" list of the pages with the most clicks. | Yes |
| Report | Markdown report in the workflow run summary and the `itvedas-growth-report` artifact; emailed too if `NOTIFY_EMAIL` / `SMTP_FROM` / `SMTP_PASS` are set. | n/a |

## Guard rails

- **Read-only Google access.** Only the `webmasters.readonly` and
  `analytics.readonly` scopes are requested.
- **Small, reversible page edits.** Only `<title>`, the meta description and
  their `og:` / `twitter:` twins change. The H1, body, structured data and
  dates are never touched, and `dateModified` is not bumped (nothing the
  reader sees changed).
- **Limited reach.** Only pages under `articles/`, `chapters/`, `ai-tools/`
  and `software/`. The homepage, legal pages, tools and CVE pages are out of
  bounds.
- **Validated output.** A rewrite is discarded unless the title is 25-62
  characters, the description 110-160, it contains no markup, and it keeps at
  least half the words of the page's top search query.
- **One experiment per page.** A page is left alone while a change is being
  measured and for 60 days after any change.
- **No duplicate topics.** A proposed topic is dropped if it overlaps a
  keyword or page title the site already targets.
- **Bounded backlog.** At most 4 topics and 2 refreshes wait in the queue. A
  queued item that fails the writer's review twice is dropped.

## One-time setup

The agent stays switched off (the run logs a warning and exits cleanly) until
the first secret below exists.

1. **Create a service account.** In [Google Cloud Console](https://console.cloud.google.com/)
   create or pick a project, enable the **Google Search Console API** and the
   **Google Analytics Data API**, then *IAM & Admin > Service Accounts >
   Create service account* (no roles needed). Open it, *Keys > Add key > JSON*,
   and download the key file.
2. **Note the service account's email** (`...@...iam.gserviceaccount.com`).
3. **Search Console:** *Settings > Users and permissions > Add user*, paste
   that email, permission **Restricted**.
4. **GA4:** *Admin > Property access management > +*, paste that email, role
   **Viewer**. Copy the numeric **Property ID** from *Admin > Property details*
   (this is not the `G-...` measurement ID).
5. **GitHub:** in *Settings > Secrets and variables > Actions* add
   - secret `GOOGLE_SERVICE_ACCOUNT_JSON` = the whole contents of the key file
   - variable `GA4_PROPERTY_ID` = the numeric property ID
6. **Try it:** *Actions > ITVedas Growth Agent > Run workflow* with *dry run*
   ticked. Read the report in the run summary. Nothing is changed in a dry
   run. Scheduled runs are live.

`ANTHROPIC_API_KEY` is already set for the autopilot and is reused.

### Optional variables

| Variable | Default | Meaning |
| --- | --- | --- |
| `GSC_SITE_URL` | auto-detected | Search Console property, e.g. `sc-domain:itvedas.com` |
| `GROWTH_MAX_META_FIXES` | 5 | Title/description rewrites per run (0 turns them off) |
| `GROWTH_MAX_NEW_KEYWORDS` | 2 | New topics queued per run |
| `GROWTH_MAX_REFRESH` | 1 | Refreshes queued per run |

## State files

- `itvedas-brain/state/growth_state.json` - every rewrite (old and new text,
  baseline metrics, verdict) and a weekly traffic history.
- `itvedas-brain/state/growth_queue.json` - topics and refreshes waiting for
  the writer. Delete an entry to cancel it; add one by hand to request a topic:
  `{"keyword": "how to ...", "topic": "Networking"}`.

This repository is public, so the page-level click and impression figures
stored in `growth_state.json` are public too. Search queries are not stored
there except as the short lists attached to queued refreshes.

## Undoing a rewrite by hand

Find the entry in `growth_state.json`, restore `old_title` /
`old_description` in the page, and set the entry's `status` to `reverted`.

## What it does not do

Social media posting, newsletters, link building and paid ads are outside this
agent. It also cannot submit URLs to Google for indexing (Google offers no
such API for ordinary pages); Bing and Yandex are pinged through IndexNow.
