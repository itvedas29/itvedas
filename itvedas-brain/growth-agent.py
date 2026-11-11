#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════
 ITVedas Brain - growth agent (SEO / AEO manager)
 Runs weekly on GitHub Actions (.github/workflows/growth-agent.yml)

 The content writer and news agent publish; this agent decides WHAT is
 worth publishing and fixes what under-performs, using real data:

   1. Reads Google Search Console (clicks, impressions, CTR, position per
      page and query) and GA4 (sessions by channel, visits sent by AI
      assistants such as ChatGPT / Perplexity / Gemini).
   2. Judges the title/description rewrites it made 28+ days ago and
      reverts any that clearly lowered click-through rate.
   3. Rewrites the <title> and meta description of pages that rank well
      but rarely get clicked (small, reversible, published automatically).
   4. Queues new article topics for content-writer.py from searches Google
      already shows the site for but no page answers well.
   5. Queues existing articles for a refresh aimed at the queries where
      they sit just off the top results.
   6. Keeps the "Most-read guides" list in llms.txt current for AI
      assistants, and writes a weekly report.

 Config via environment variables (GitHub Secrets / Variables):
   GOOGLE_SERVICE_ACCOUNT_JSON  (required) service-account key, read-only
   GSC_SITE_URL                 (optional) property to read; auto-detected if unset
   GA4_PROPERTY_ID              (optional) numeric GA4 property id
   ANTHROPIC_API_KEY            (required for steps 3 and 4)
   GROWTH_DRY_RUN               (optional) 1 = analyse and report only
   GROWTH_MAX_META_FIXES        (optional) default 5 per run
   GROWTH_MAX_NEW_KEYWORDS      (optional) default 2 per run
   GROWTH_MAX_REFRESH           (optional) default 1 per run
   NOTIFY_EMAIL, SMTP_FROM, SMTP_PASS  (optional) email the report

 Setup and operating notes: docs/GROWTH-AGENT.md
═══════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import datetime
import os
import pathlib
import re
import smtplib
import sys
from email.mime.text import MIMEText

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from core import growth as G
from core.log import log as _core_log

COMPONENT = "growth-agent"
ROOT = pathlib.Path(__file__).resolve().parent.parent

TITLE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "reason": {"type": "string"},
    },
    "required": ["title", "description", "reason"],
    "additionalProperties": False,
}

KEYWORD_SCHEMA = {
    "type": "object",
    "properties": {
        "keywords": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string"},
                    "topic": {"type": "string", "enum": list(G.WRITER_TOPICS)},
                    "reason": {"type": "string"},
                },
                "required": ["keyword", "topic", "reason"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["keywords"],
    "additionalProperties": False,
}

# Backlog caps: the writer publishes three times a week, so a longer queue
# would only go stale before it is written.
MAX_KEYWORD_BACKLOG = 4
MAX_REFRESH_BACKLOG = 2


def log(msg: str) -> None:
    _core_log(COMPONENT, msg)


def _int_env(name: str, default: int) -> int:
    try:
        return max(0, int(os.environ.get(name, "") or default))
    except ValueError:
        return default


def state_paths(root: pathlib.Path) -> dict:
    d = root / "itvedas-brain" / "state"
    return {"growth": d / "growth_state.json", "queue": d / "growth_queue.json",
            "writer": d / "state.json"}


def page_excerpt(text: str, limit: int = 1200) -> tuple[str, str]:
    """(h1, opening body text) so a rewrite describes what is really on the page."""
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.IGNORECASE | re.DOTALL)
    body = text[h1.end():] if h1 else text
    body = re.sub(r"<(script|style)\b.*?</\1>", " ", body, flags=re.IGNORECASE | re.DOTALL)
    body = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).strip()
    return (re.sub(r"<[^>]+>", "", h1.group(1)).strip() if h1 else ""), body[:limit]


def existing_coverage(root: pathlib.Path, writer_state: dict, queue: dict) -> list[str]:
    """Every keyword and page title the site already targets."""
    covered = list(writer_state.get("used_keywords", []))
    covered += [a.get("keyword", "") for a in writer_state.get("published", [])]
    covered += [k["keyword"] for k in queue.get("keywords", [])]
    for folder in ("articles", "chapters"):
        for f in sorted((root / folder).rglob("*.html")):
            head = G.read_head(f.read_text(encoding="utf-8", errors="ignore"))
            if head:
                covered.append(head["title"])
    return [c for c in covered if c]


# ── step 2: judge earlier rewrites ───────────────────────────────────────
def judge_pending(root, state, today, gsc, dry_run) -> tuple[list[dict], list[str]]:
    judged, touched = [], []
    for change in state["changes"]:
        if change.get("status") != "pending":
            continue
        window = G.after_window(change["applied"], today)
        if not window:
            continue
        rows = gsc(window[0], window[1], ["page"], page_filter=change["url"])
        after = ({"clicks": rows[0]["clicks"], "impressions": rows[0]["impressions"],
                  "ctr": rows[0]["ctr"], "position": rows[0]["position"]}
                 if rows else {"clicks": 0, "impressions": 0, "ctr": 0.0, "position": 0.0})
        verdict = G.judge_change(change["baseline"], after)
        f = root / change["file"]
        if verdict == "reverted":
            text = f.read_text(encoding="utf-8") if f.is_file() else ""
            restored = G.revert_head(text, change.get("tags_before", {}), change.get("tags_after", {}))
            if restored is None:
                verdict = "superseded"  # the page was rewritten since; nothing to undo
            elif not dry_run:
                f.write_text(restored, encoding="utf-8")
                touched.append(G.file_to_path(f, root))
        if not dry_run:
            change.update(status=verdict, after=after, judged=today.isoformat())
        judged.append({**change, "status": verdict, "after": after})
        log(f"Judged {change['file']}: {verdict} "
            f"(CTR {change['baseline']['ctr']*100:.1f}% -> {after['ctr']*100:.1f}%)")
    return judged, touched


# ── step 3: title / description rewrites ─────────────────────────────────
def rewrite_prompt(head: dict, h1: str, excerpt: str, page: dict, queries: list[dict]) -> str:
    query_lines = "\n".join(
        f"- \"{q['query']}\" - {q['impressions']:.0f} impressions, position {q['position']:.1f}"
        for q in queries[:8]) or "- (no query detail available)"
    return f"""You manage search snippets for ITVedas, a free IT knowledge site for beginners.

This page ranks at average position {page['position']:.1f} on Google with {page['impressions']:.0f} impressions in 28 days, but only {page['ctr']*100:.1f}% of searchers click it (about {page['expected_ctr']*100:.0f}% is normal at that position). Write a better search title and meta description.

Current title: {head['title']}
Current description: {head['description']}
Page H1: {h1}
What the page says: {excerpt}

Searches that show this page:
{query_lines}

Rules:
- Title: 30-60 characters. Lead with the words people actually search for. Do NOT add the site name; it is appended automatically.
- Description: 120-155 characters. Say plainly what the reader gets, in the page's own terms.
- Promise only what the page delivers. No clickbait, no invented numbers, no "ultimate", "best ever" or similar.
- Keep a year only if the current title already has one.
- Plain text only: no quotes around the text, no HTML, no emoji.

Reply with JSON: title, description, and reason (one short sentence on what you changed and why)."""


def fix_low_ctr(root, state, today, pages, by_page, llm, limit, dry_run):
    applied, skipped, touched = [], [], []
    for page in G.find_low_ctr(pages):
        if len(applied) >= limit:
            break
        f = G.url_to_file(page["page"], root)
        if not f:
            continue
        rel = f.relative_to(root).as_posix()
        # Search Console can list one page under several URLs (/x and /x.html).
        if G.in_cooldown(state, rel, today) or any(c["file"] == rel for c in applied):
            continue
        text = f.read_text(encoding="utf-8")
        head = G.read_head(text)
        if not head:
            continue
        queries = by_page.get(page["page"], [])
        h1, excerpt = page_excerpt(text)
        try:
            reply = llm(rewrite_prompt(head, h1, excerpt, page, queries), TITLE_SCHEMA)
        except Exception as e:  # one bad call must not sink the whole run
            skipped.append(f"{rel}: Claude call failed ({e})")
            continue
        if not reply:
            skipped.append(f"{rel}: no rewrite returned")
            continue
        title, description = reply["title"].strip(), reply["description"].strip()
        problem = G.validate_rewrite(head, title, description, queries[0]["query"] if queries else "")
        if problem:
            skipped.append(f"{rel}: rewrite rejected - {problem}")
            continue
        new_text = G.apply_head(text, title, description, head["suffix"])
        if not dry_run:
            f.write_text(new_text, encoding="utf-8")
            touched.append(G.file_to_path(f, root))
        change = {
            "file": rel, "url": page["page"], "applied": today.isoformat(), "status": "pending",
            "old_title": head["title"], "old_description": head["description"],
            "new_title": title, "new_description": description, "reason": reply["reason"].strip(),
            "baseline": {k: page[k] for k in ("clicks", "impressions", "ctr", "position")},
            "tags_before": G.head_tags(text), "tags_after": G.head_tags(new_text),
        }
        applied.append(change)
        log(f"Rewrote head of {rel}: \"{head['title']}\" -> \"{title}\"")
    if not dry_run:
        state["changes"].extend(applied)
    return applied, skipped, touched


# ── step 4: new article topics ───────────────────────────────────────────
def keyword_prompt(gaps: list[dict], covered: list[str], want: int) -> str:
    gap_lines = "\n".join(f"- \"{g['query']}\" - {g['impressions']:.0f} impressions, best position {g['position']:.0f}"
                          for g in gaps[:40])
    covered_lines = "\n".join(f"- {c}" for c in sorted(set(covered))[:400])
    return f"""You plan content for ITVedas, a free IT knowledge site that explains IT to beginners in plain English (networking, cloud, security, DevOps, databases, Linux, hardware, compliance).

Google already shows ITVedas for the searches below, but only far down the results - people want these answers and no page gives them well:
{gap_lines}

The site already has pages targeting:
{covered_lines}

Choose up to {want} NEW article topics that would win the most of this demand.
- Each must be a clear beginner-level question or task that deserves its own 1,500-word guide.
- Never pick something an existing page already targets, even reworded; a duplicate splits ranking between two pages.
- Group near-identical searches into one topic. Skip navigational, brand, product-support or off-topic searches.
- Write `keyword` as the natural search phrase a person would type, 4-10 words, lower case except proper nouns.
- `topic` is the site section it belongs in.
- `reason` names the searches it answers.
Return fewer than {want}, or none, if nothing here is worth a new page.

Reply with JSON: keywords (array of keyword, topic, reason)."""


def plan_keywords(gaps, covered, queue, llm, limit, today, dry_run):
    room = min(limit, MAX_KEYWORD_BACKLOG - len(queue["keywords"]))
    if room <= 0 or not gaps:
        return []
    reply = llm(keyword_prompt(gaps, covered, room), KEYWORD_SCHEMA)
    added = []
    for item in (reply or {}).get("keywords", [])[:room]:
        keyword = " ".join(item["keyword"].split())
        if not 3 <= len(keyword.split()) <= 12 or re.search(r"[<>\"]", keyword):
            continue
        if item["topic"] not in G.WRITER_TOPICS:
            continue
        if G.is_duplicate_keyword(keyword, covered + [a["keyword"] for a in added]):
            log(f"Dropped duplicate topic: {keyword}")
            continue
        added.append({"keyword": keyword, "topic": item["topic"], "reason": item["reason"].strip(),
                      "added": today.isoformat()})
        log(f"Queued new topic: {keyword} [{item['topic']}]")
    if not dry_run:
        queue["keywords"].extend(added)
    return added


# ── step 5: refresh queue ────────────────────────────────────────────────
def plan_refresh(root, state, queue, writer_state, striking, limit, today, dry_run):
    room = min(limit, MAX_REFRESH_BACKLOG - len(queue["refresh"]))
    known = {a["file"] for a in writer_state.get("published", [])}
    queued = {r["file"] for r in queue["refresh"]}
    added = []
    for s in striking:
        if len(added) >= room:
            break
        f = G.url_to_file(s["page"], root)
        if not f or f.parent != root / "articles":
            continue
        # The writer can only refresh articles it has a record of.
        if f.name not in known or f.name in queued:
            continue
        if G.in_cooldown(state, f"articles/{f.name}", today):
            continue
        added.append({"file": f.name, "queries": s["queries"], "added": today.isoformat()})
        log(f"Queued refresh: articles/{f.name} for {s['queries'][:3]}")
    if not dry_run:
        queue["refresh"].extend(added)
    return added


# ── GA4 summary ──────────────────────────────────────────────────────────
def ga4_summary(ga4, w) -> dict:
    def channels(start, end):
        rows = ga4(start, end, ["sessionDefaultChannelGroup"], ["sessions"])
        total = sum(r["sessions"] for r in rows)
        organic = sum(r["sessions"] for r in rows if r["sessionDefaultChannelGroup"] == "Organic Search")
        return total, organic

    def ai(start, end):
        rows = ga4(start, end, ["sessionSource"], ["sessions"])
        hits = [(r["sessionSource"], r["sessions"]) for r in rows if G.is_ai_source(r["sessionSource"])]
        return sum(n for _, n in hits), sorted(hits, key=lambda h: h[1], reverse=True)[:6]

    sessions, organic = channels(*w["current"])
    sessions_prev, organic_prev = channels(*w["previous"])
    ai_now, ai_sources = ai(*w["current"])
    ai_prev, _ = ai(*w["previous"])
    return {"sessions": sessions, "sessions_prev": sessions_prev, "organic": organic,
            "organic_prev": organic_prev, "ai": ai_now, "ai_prev": ai_prev, "ai_sources": ai_sources}


def refresh_llms_txt(root, pages, dry_run) -> bool:
    llms = root / "llms.txt"
    if not llms.is_file():
        return False
    items = []
    for p in sorted(pages, key=lambda r: r["clicks"], reverse=True):
        if len(items) >= 12 or p["clicks"] <= 0:
            break
        f = G.url_to_file(p["page"], root)
        if not f:
            continue
        rel = f.relative_to(root)
        head = G.read_head(f.read_text(encoding="utf-8", errors="ignore"))
        if head and rel.parts[0] in ("articles", "chapters"):
            items.append((head["title"], G.SITE_URL + "/" + rel.as_posix().removesuffix(".html")))
    old = llms.read_text(encoding="utf-8")
    new = G.update_llms_txt(old, items)
    if new != old and not dry_run:
        llms.write_text(new, encoding="utf-8")
    return new != old


# ── orchestration ────────────────────────────────────────────────────────
def run(root: pathlib.Path, today: datetime.date, gsc, ga4=None, llm=None,
        dry_run: bool = False, limits: dict | None = None) -> dict:
    """One full agent run. `gsc(start, end, dimensions, page_filter=None)`,
    `ga4(start, end, dimensions, metrics)` and `llm(prompt, schema)` are
    injected so tests can run the whole flow without any network."""
    root = root.resolve()
    limits = {"meta": 5, "keywords": 2, "refresh": 1, **(limits or {})}
    paths = state_paths(root)
    state = {**G.empty_state(), **G.load_json(paths["growth"], {})}
    queue = {**G.empty_queue(), **G.load_json(paths["queue"], {})}
    writer_state = G.load_json(paths["writer"], {})
    w = G.windows(today)

    pages = gsc(*w["current"], ["page"])
    pages_prev = gsc(*w["previous"], ["page"])
    page_query = gsc(*w["current"], ["page", "query"])
    by_page = G.queries_by_page(page_query)
    log(f"Search Console: {len(pages)} pages, {len(page_query)} page/query rows "
        f"({w['current'][0]} to {w['current'][1]})")

    skipped: list[str] = []
    judged, touched = judge_pending(root, state, today, gsc, dry_run)

    applied, queued_keywords = [], []
    if llm:
        applied, skip, t = fix_low_ctr(root, state, today, pages, by_page, llm, limits["meta"], dry_run)
        skipped += skip
        touched += t
        try:
            queued_keywords = plan_keywords(G.find_gaps(page_query),
                                            existing_coverage(root, writer_state, queue),
                                            queue, llm, limits["keywords"], today, dry_run)
        except Exception as e:
            skipped.append(f"New-topic planning failed: {e}")
    else:
        skipped.append("ANTHROPIC_API_KEY not set - no rewrites or new topics this run")

    queued_refresh = plan_refresh(root, state, queue, writer_state, G.find_striking(page_query),
                                  limits["refresh"], today, dry_run)

    ga, ga_error = None, None
    if ga4:
        try:
            ga = ga4_summary(ga4, w)
        except Exception as e:
            ga_error = str(e)[:200]
            log(f"GA4 unavailable: {ga_error}")
    else:
        ga_error = "GA4_PROPERTY_ID not set"

    if refresh_llms_txt(root, pages, dry_run):
        touched.append("/llms.txt")

    cur, prev = G.totals(pages), G.totals(pages_prev)
    summary = {
        "date": today.isoformat(), "window": w["current"], "dry_run": dry_run,
        "gsc_current": cur, "gsc_previous": prev, "ga4": ga, "ga4_error": ga_error,
        "applied": applied, "judged": judged, "queued_keywords": queued_keywords,
        "queued_refresh": queued_refresh, "decliners": G.find_decliners(pages, pages_prev),
        "top_pages": sorted(pages, key=lambda r: r["clicks"], reverse=True)[:10],
        "skipped": skipped, "touched": touched,
    }
    if not dry_run:
        state["history"] = (state["history"] + [{
            "date": today.isoformat(), "clicks": cur["clicks"], "impressions": cur["impressions"],
            "sessions": ga["sessions"] if ga else None, "ai_sessions": ga["ai"] if ga else None,
        }])[-104:]
        state["last_run"] = today.isoformat()
        G.save_json(paths["growth"], state)
        G.save_json(paths["queue"], queue)
    return summary


def deliver_report(report: str) -> None:
    out_dir = pathlib.Path(os.environ.get("GROWTH_REPORT_DIR", "/tmp/itvedas-growth"))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "growth-report.md").write_text(report, encoding="utf-8")
    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with open(step_summary, "a", encoding="utf-8") as handle:
            handle.write(report)
    to, sender, password = (os.environ.get(k, "").strip() for k in ("NOTIFY_EMAIL", "SMTP_FROM", "SMTP_PASS"))
    if not (to and sender and password):
        log("Email not configured - report is in the workflow run summary")
        return
    try:
        msg = MIMEText(report, "plain", "utf-8")
        msg["Subject"] = report.splitlines()[0].lstrip("# ")
        msg["From"], msg["To"] = sender, to
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(sender, password)
            s.sendmail(sender, to, msg.as_string())
        log(f"Report emailed to {to}")
    except Exception as e:
        log(f"Email error: {e}")


def main() -> int:
    from core import google_data
    log("=" * 55)
    log("Growth agent - run start")
    dry_run = os.environ.get("GROWTH_DRY_RUN", "").strip() == "1"

    try:
        info = google_data.load_service_account_info()
    except google_data.GoogleDataError as e:
        log(f"FATAL: {e}")
        return 1
    if not info:
        # Not a failure: the agent is simply not switched on yet.
        print("::warning::Growth agent skipped - GOOGLE_SERVICE_ACCOUNT_JSON secret is not set. "
              "See docs/GROWTH-AGENT.md.")
        log("GOOGLE_SERVICE_ACCOUNT_JSON not set - nothing to do")
        return 0

    session = google_data.make_session(info)
    site = os.environ.get("GSC_SITE_URL", "").strip()
    if not site:
        try:
            site = google_data.gsc_find_site(session)
        except google_data.GoogleDataError as e:
            log(f"FATAL: {e}")
            return 1
        if not site:
            log(f"FATAL: {info['client_email']} has no access to an itvedas.com Search Console property")
            print("::error::The service account is not a user on the itvedas.com Search Console property. "
                  "See docs/GROWTH-AGENT.md step 3.")
            return 1
    log(f"Search Console property: {site}")
    prop = os.environ.get("GA4_PROPERTY_ID", "").strip()

    def gsc(start, end, dimensions, page_filter=None):
        return google_data.gsc_query(session, site, start, end, dimensions, page_filter=page_filter)

    ga4 = (lambda start, end, dims, metrics: google_data.ga4_report(session, prop, start, end, dims, metrics)) if prop else None

    llm = None
    if os.environ.get("ANTHROPIC_API_KEY", "").strip():
        from core.llm import claude_json

        def llm(prompt, schema):
            return claude_json(prompt, schema, max_tokens=2000, effort="medium", log_fn=log)

    try:
        summary = run(ROOT, datetime.date.today(), gsc, ga4, llm, dry_run, {
            "meta": _int_env("GROWTH_MAX_META_FIXES", 5),
            "keywords": _int_env("GROWTH_MAX_NEW_KEYWORDS", 2),
            "refresh": _int_env("GROWTH_MAX_REFRESH", 1),
        })
    except google_data.GoogleDataError as e:
        log(f"FATAL: Search Console request failed: {e}")
        print(f"::error::Search Console request failed - check the service account has access to {site}.")
        return 1

    deliver_report(G.render_report(summary))
    pings = [p for p in summary["touched"] if p.endswith(".html")]
    if pings and not dry_run:
        from core.indexnow import submit
        submit(pings, log_fn=log)
    log(f"DONE. {len(summary['applied'])} rewrites, {len(summary['judged'])} judged, "
        f"{len(summary['queued_keywords'])} topics and {len(summary['queued_refresh'])} refreshes queued"
        + (" (dry run)" if dry_run else ""))
    log("=" * 55)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
