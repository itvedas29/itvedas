# Knowledge Imports (staging)

A separate, not-yet-live staging area for building a new knowledge base.

- `repos.json` — list of external repository links to pull in (url, description, date added).
- `uploads/` — extracted contents of any zip files you provide go here.

This folder is independent of `itvedas-brain/` (the existing live bot's
knowledge/memory/state) and is **not wired into the bot or site**. Nothing
here goes live until it's reviewed and explicitly merged in.
