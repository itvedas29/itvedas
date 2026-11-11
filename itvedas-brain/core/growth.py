"""Pure logic for the growth agent: turning Search Console / GA4 rows into
decisions, and editing a page's <title> and meta description safely.

Nothing in here talks to the network or to Claude, so it is all unit-tested
(tests/test_growth_agent.py). itvedas-brain/growth-agent.py wires it together.
"""
from __future__ import annotations

import datetime
import html
import json
import pathlib
import re
import urllib.parse

SITE_HOSTS = {"itvedas.com", "www.itvedas.com"}
SITE_URL = "https://www.itvedas.com"

# Only pages under these folders may have their title/description rewritten
# automatically. Homepage, legal pages, tools with hand-tuned copy and the
# CVE pages are deliberately out of reach.
EDITABLE_DIRS = ("articles", "chapters", "ai-tools", "software")

# Search Console data lags by 2-3 days; ignore the newest days.
GSC_LAG_DAYS = 3
WINDOW_DAYS = 28

# Rough organic click-through rate by average position (page one). Used only
# to rank which pages under-perform their position the most.
_EXPECTED_CTR = {1: 0.28, 2: 0.15, 3: 0.10, 4: 0.07, 5: 0.05, 6: 0.04,
                 7: 0.03, 8: 0.025, 9: 0.02, 10: 0.018}

AI_SOURCES = ("chatgpt", "openai", "perplexity", "claude.ai", "gemini.google",
              "copilot.microsoft", "copilot.com", "you.com", "phind", "poe.com",
              "deepseek", "meta.ai", "mistral", "grok")

WRITER_TOPICS = ("Networking", "Cloud", "Security", "DevOps", "Databases",
                 "Linux", "Hardware", "Compliance")

_STOPWORDS = {"the", "and", "for", "with", "what", "how", "does", "are", "you",
              "your", "why", "can", "from", "that", "this", "into", "vs", "is",
              "in", "of", "to", "a", "an", "on", "it", "do", "or", "be"}


# ── dates ────────────────────────────────────────────────────────────────
def windows(today: datetime.date) -> dict:
    """Current and previous 28-day windows, both ending before the GSC lag."""
    end = today - datetime.timedelta(days=GSC_LAG_DAYS)
    start = end - datetime.timedelta(days=WINDOW_DAYS - 1)
    prev_end = start - datetime.timedelta(days=1)
    prev_start = prev_end - datetime.timedelta(days=WINDOW_DAYS - 1)
    return {"current": (start.isoformat(), end.isoformat()),
            "previous": (prev_start.isoformat(), prev_end.isoformat())}


def after_window(applied: str, today: datetime.date) -> tuple[str, str] | None:
    """The 28 days after a change went live (skipping 3 days for recrawl), or
    None while that window has not fully passed in Search Console yet."""
    start = datetime.date.fromisoformat(applied) + datetime.timedelta(days=3)
    end = start + datetime.timedelta(days=WINDOW_DAYS - 1)
    if end > today - datetime.timedelta(days=GSC_LAG_DAYS):
        return None
    return start.isoformat(), end.isoformat()


# ── URL <-> file ─────────────────────────────────────────────────────────
def url_to_file(url: str, root: pathlib.Path) -> pathlib.Path | None:
    """Map a public URL to the HTML file that serves it, or None if it is not
    an editable page. Never returns a path outside `root`."""
    parts = urllib.parse.urlsplit(url)
    if parts.netloc.lower() not in SITE_HOSTS:
        return None
    path = urllib.parse.unquote(parts.path).strip("/")
    if not path or ".." in path.split("/"):
        return None
    if path.split("/")[0] not in EDITABLE_DIRS:
        return None
    root = root.resolve()
    for candidate in (path if path.endswith(".html") else path + ".html",
                      path + "/index.html"):
        f = (root / candidate).resolve()
        if f.is_file() and root in f.parents:
            return f
    return None


def file_to_path(f: pathlib.Path, root: pathlib.Path) -> str:
    """Site-relative URL path for IndexNow, e.g. /articles/foo.html."""
    return "/" + f.resolve().relative_to(root.resolve()).as_posix()


# ── opportunity detection ────────────────────────────────────────────────
def expected_ctr(position: float) -> float:
    return _EXPECTED_CTR.get(max(1, round(position)), 0.01)


def find_low_ctr(pages: list[dict], min_impressions: int = 150) -> list[dict]:
    """Pages that rank on page one-ish but get clicked far less than their
    position would predict - a better title/description is the likely fix."""
    out = []
    for p in pages:
        if p["impressions"] < min_impressions or p["position"] > 12:
            continue
        exp = expected_ctr(p["position"])
        if p["ctr"] < 0.6 * exp:
            out.append({**p, "expected_ctr": exp,
                        "missed_clicks": round(p["impressions"] * (exp - p["ctr"]), 1)})
    return sorted(out, key=lambda r: r["missed_clicks"], reverse=True)


def queries_by_page(page_query_rows: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for r in page_query_rows:
        grouped.setdefault(r["page"], []).append(r)
    for rows in grouped.values():
        rows.sort(key=lambda r: r["impressions"], reverse=True)
    return grouped


def find_striking(page_query_rows: list[dict], min_impressions: int = 30) -> list[dict]:
    """Pages with queries sitting at positions 5-20: close enough that a
    content refresh aimed at those queries can move them up."""
    grouped: dict[str, list[dict]] = {}
    for r in page_query_rows:
        if 5 <= r["position"] <= 20 and r["impressions"] >= min_impressions and not is_brand(r["query"]):
            grouped.setdefault(r["page"], []).append(r)
    out = []
    for page, rows in grouped.items():
        rows.sort(key=lambda r: r["impressions"], reverse=True)
        out.append({"page": page, "impressions": sum(r["impressions"] for r in rows),
                    "queries": [r["query"] for r in rows[:6]]})
    return sorted(out, key=lambda r: r["impressions"], reverse=True)


def is_brand(query: str) -> bool:
    q = query.lower().replace(" ", "")
    return "itvedas" in q


def find_gaps(page_query_rows: list[dict], min_impressions: int = 40) -> list[dict]:
    """Queries Google already shows the site for, but only deep in the results
    (best position worse than 12): demand exists and no page answers it well.
    These are candidates for brand-new articles."""
    agg: dict[str, dict] = {}
    for r in page_query_rows:
        q = r["query"]
        a = agg.setdefault(q, {"query": q, "impressions": 0, "clicks": 0,
                               "position": r["position"], "page": r["page"]})
        a["impressions"] += r["impressions"]
        a["clicks"] += r["clicks"]
        if r["position"] < a["position"]:
            a["position"], a["page"] = r["position"], r["page"]
    out = [a for a in agg.values()
           if a["impressions"] >= min_impressions and a["position"] > 12
           and len(a["query"].split()) >= 2 and not is_brand(a["query"])]
    return sorted(out, key=lambda r: r["impressions"], reverse=True)


def find_decliners(current: list[dict], previous: list[dict], min_prev_clicks: int = 20) -> list[dict]:
    prev = {p["page"]: p for p in previous}
    cur = {p["page"]: p for p in current}
    out = []
    for page, p in prev.items():
        if p["clicks"] < min_prev_clicks:
            continue
        now = cur.get(page, {"clicks": 0, "position": 0})["clicks"]
        if now <= 0.6 * p["clicks"]:
            out.append({"page": page, "clicks_before": p["clicks"], "clicks_now": now})
    return sorted(out, key=lambda r: r["clicks_before"] - r["clicks_now"], reverse=True)


def totals(rows: list[dict]) -> dict:
    clicks = sum(r["clicks"] for r in rows)
    impressions = sum(r["impressions"] for r in rows)
    return {"clicks": clicks, "impressions": impressions,
            "ctr": (clicks / impressions) if impressions else 0.0}


def is_ai_source(source: str) -> bool:
    s = source.lower()
    return any(tag in s for tag in AI_SOURCES)


# ── <head> editing ───────────────────────────────────────────────────────
_TITLE_RE = re.compile(r"(<title>)(.*?)(</title>)", re.IGNORECASE | re.DOTALL)
# " | ITVedas", " — ITVedas", " - ITVedas": kept as-is when a title is rewritten.
_SUFFIX_RE = re.compile(r"\s+[|\u2014\u2013-]\s*ITVedas\s*$")
_HEAD_METAS = (("name", "description"), ("property", "og:title"), ("property", "og:description"),
               ("name", "twitter:title"), ("name", "twitter:description"))


def _meta_re(attr: str, value: str) -> re.Pattern:
    return re.compile(r"<meta\b[^>]*\b%s=[\"']%s[\"'][^>]*>" % (attr, re.escape(value)), re.IGNORECASE)


_CONTENT_RE = re.compile(r"(\bcontent=)(\"[^\"]*\"|'[^']*')", re.IGNORECASE)


def _get_meta(text: str, attr: str, value: str) -> str | None:
    tag = _meta_re(attr, value).search(text)
    if not tag:
        return None
    content = _CONTENT_RE.search(tag.group(0))
    return html.unescape(content.group(2)[1:-1]) if content else None


def _set_meta(text: str, attr: str, value: str, new: str) -> str:
    def fix_tag(tag: re.Match) -> str:
        return _CONTENT_RE.sub(lambda c: c.group(1) + '"' + html.escape(new, quote=True) + '"',
                               tag.group(0), count=1)
    return _meta_re(attr, value).sub(fix_tag, text, count=1)


def read_head(text: str) -> dict | None:
    """{'title', 'description', 'suffix'} for a page, title without the
    ' | ITVedas' suffix. None when the page lacks either tag (not editable)."""
    t = _TITLE_RE.search(text)
    desc = _get_meta(text, "name", "description")
    if not t or desc is None:
        return None
    title = html.unescape(t.group(2)).strip()
    found = _SUFFIX_RE.search(title)
    suffix = found.group(0) if found else ""
    return {"title": title[: len(title) - len(suffix)] if suffix else title,
            "description": desc.strip(), "suffix": suffix}


def head_tags(text: str) -> dict[str, str]:
    """The raw <title> element and description/og/twitter meta tags exactly
    as written in the file, keyed by name. Saved before and after a rewrite
    so a revert restores the original bytes."""
    tags = {}
    t = _TITLE_RE.search(text)
    if t:
        tags["title"] = t.group(0)
    for attr, value in _HEAD_METAS:
        m = _meta_re(attr, value).search(text)
        if m:
            tags[value] = m.group(0)
    return tags


def revert_head(text: str, before: dict[str, str], after: dict[str, str]) -> str | None:
    """Undo a rewrite by swapping each tag back to its saved original. None
    if the page no longer carries the rewritten tags (someone or something
    has changed it since, so there is nothing of ours left to undo)."""
    if not after or any(raw not in text for raw in after.values()):
        return None
    for key, raw in after.items():
        if key in before:
            text = text.replace(raw, before[key], 1)
    return text


def apply_head(text: str, title: str, description: str, suffix: str = "") -> str:
    """Rewrite <title>, meta description and their og:/twitter: twins. The
    visible page (H1, body, structured data, dates) is left untouched."""
    full = title + suffix
    text = _TITLE_RE.sub(lambda m: m.group(1) + html.escape(full, quote=False) + m.group(3), text, count=1)
    text = _set_meta(text, "name", "description", description)
    for attr, key in _HEAD_METAS[1:]:
        text = _set_meta(text, attr, key, full if key.endswith("title") else description)
    return text


def _tokens(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) > 1 and w not in _STOPWORDS}


def validate_rewrite(old: dict, title: str, description: str, top_query: str) -> str | None:
    """None if the proposed title/description is safe to publish, otherwise
    the reason it was rejected."""
    title, description = title.strip(), description.strip()
    if title == old["title"] and description == old["description"]:
        return "no change"
    for label, value in (("title", title), ("description", description)):
        if re.search(r"[<>\n\r]", value):
            return f"{label} contains markup or line breaks"
    if title.lower().endswith("itvedas"):
        return "title repeats the site name (suffix is added automatically)"
    if not 25 <= len(title) <= 62:
        return f"title length {len(title)} outside 25-62"
    if not 110 <= len(description) <= 160:
        return f"description length {len(description)} outside 110-160"
    want = _tokens(top_query)
    if want:
        have = _tokens(title + " " + description)
        if len(want & have) < (len(want) + 1) // 2:
            return "drops the terms people search for"
    return None


def judge_change(baseline: dict, after: dict) -> str:
    """Verdict on a title/description change once 28 days of data exist:
    'kept', 'reverted' (clearly worse at a comparable position) or
    'inconclusive' (too little data or the ranking moved, so CTR can't be
    compared fairly - the change is left in place)."""
    if after.get("impressions", 0) < 80:
        return "inconclusive"
    if abs(after.get("position", 0) - baseline.get("position", 0)) > 3:
        return "inconclusive"
    if after.get("ctr", 0) < 0.7 * baseline.get("ctr", 0):
        return "reverted"
    return "kept"


# ── state files ──────────────────────────────────────────────────────────
def load_json(path: pathlib.Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def save_json(path: pathlib.Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def empty_state() -> dict:
    return {"changes": [], "history": [], "last_run": None}


def empty_queue() -> dict:
    return {"keywords": [], "refresh": []}


def in_cooldown(state: dict, file: str, today: datetime.date, days: int = 60) -> bool:
    """A page is left alone while an earlier change is still being measured,
    and for `days` after any change, so results stay attributable."""
    for c in state.get("changes", []):
        if c["file"] != file:
            continue
        if c.get("status") == "pending":
            return True
        if (today - datetime.date.fromisoformat(c["applied"])).days < days:
            return True
    return False


def normalise_keyword(k: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", k.lower()))


def is_duplicate_keyword(keyword: str, existing: list[str]) -> bool:
    """True when `keyword` is the same as, or mostly the same words as, a
    keyword/title already covered - avoids two pages fighting for one query."""
    new = _tokens(keyword)
    if not new:
        return True
    for other in existing:
        if normalise_keyword(other) == normalise_keyword(keyword):
            return True
        old = _tokens(other)
        if old and len(new & old) / len(new | old) >= 0.7:
            return True
    return False


# ── llms.txt ─────────────────────────────────────────────────────────────
LLMS_HEADING = "## Most-read guides"


def update_llms_txt(text: str, items: list[tuple[str, str]]) -> str:
    """Insert/replace a 'Most-read guides' section (title, url pairs) so AI
    assistants reading llms.txt are pointed at the pages people actually use."""
    if not items:
        return text
    block = LLMS_HEADING + "\n\n" + "\n".join(f"- [{t}]({u})" for t, u in items) + "\n"
    pattern = re.compile(re.escape(LLMS_HEADING) + r"\n.*?(?=\n## |\Z)", re.DOTALL)
    if pattern.search(text):
        return pattern.sub(lambda _m: block, text, count=1)
    marker = "\n## Reference"
    if marker in text:
        return text.replace(marker, "\n" + block + marker, 1)
    return text.rstrip("\n") + "\n\n" + block


# ── report ───────────────────────────────────────────────────────────────
def _pct(now: float, before: float) -> str:
    if not before:
        return "n/a"
    return f"{(now - before) / before * 100:+.0f}%"


def _short(url: str) -> str:
    return urllib.parse.urlsplit(url).path or "/"


def render_report(d: dict) -> str:
    """Markdown weekly report. `d` is the run summary built by growth-agent."""
    cur, prev = d["gsc_current"], d["gsc_previous"]
    lines = [
        f"# ITVedas growth report - {d['date']}",
        "",
        f"Search Console, {d['window'][0]} to {d['window'][1]} vs the 28 days before."
        + ("  **DRY RUN - nothing was changed.**" if d.get("dry_run") else ""),
        "",
        "| | Last 28 days | Previous 28 | Change |",
        "| --- | --- | --- | --- |",
        f"| Google clicks | {cur['clicks']:.0f} | {prev['clicks']:.0f} | {_pct(cur['clicks'], prev['clicks'])} |",
        f"| Google impressions | {cur['impressions']:.0f} | {prev['impressions']:.0f} | {_pct(cur['impressions'], prev['impressions'])} |",
        f"| Average CTR | {cur['ctr']*100:.2f}% | {prev['ctr']*100:.2f}% | |",
    ]
    ga = d.get("ga4")
    if ga:
        lines += [
            f"| All sessions (GA4) | {ga['sessions']:.0f} | {ga['sessions_prev']:.0f} | {_pct(ga['sessions'], ga['sessions_prev'])} |",
            f"| Organic search sessions | {ga['organic']:.0f} | {ga['organic_prev']:.0f} | {_pct(ga['organic'], ga['organic_prev'])} |",
            f"| Sessions from AI assistants | {ga['ai']:.0f} | {ga['ai_prev']:.0f} | {_pct(ga['ai'], ga['ai_prev'])} |",
        ]
        if ga.get("ai_sources"):
            lines += ["", "AI assistant referrals: " + ", ".join(f"{s} ({n:.0f})" for s, n in ga["ai_sources"])]
    else:
        lines += ["", "_GA4 data unavailable this run" + (f": {d['ga4_error']}" if d.get("ga4_error") else "") + "._"]

    def section(title: str, rows: list[str], empty: str) -> None:
        lines.extend(["", f"## {title}", ""])
        lines.extend(rows or [empty])

    section("Titles and descriptions rewritten",
            [f"- `{c['file']}` - \"{c['old_title']}\" -> \"{c['new_title']}\" ({c['reason']})" for c in d["applied"]],
            "None this run.")
    section("Earlier rewrites judged",
            [f"- `{c['file']}` - **{c['status']}** (CTR {c['baseline']['ctr']*100:.1f}% -> {c['after']['ctr']*100:.1f}%)"
             for c in d["judged"]],
            "None due yet (each change is measured for 28 days).")
    section("New article topics queued for the writer",
            [f"- **{k['keyword']}** [{k['topic']}] - {k['reason']}" for k in d["queued_keywords"]],
            "None this run.")
    section("Articles queued for a refresh",
            [f"- `{r['file']}` - to answer: {', '.join(r['queries'][:4])}" for r in d["queued_refresh"]],
            "None this run.")
    section("Pages losing clicks",
            [f"- {_short(r['page'])} - {r['clicks_before']:.0f} -> {r['clicks_now']:.0f} clicks" for r in d["decliners"][:10]],
            "None.")
    section("Top pages",
            [f"- {_short(p['page'])} - {p['clicks']:.0f} clicks, position {p['position']:.1f}" for p in d["top_pages"][:10]],
            "No data.")
    if d.get("skipped"):
        section("Skipped", [f"- {s}" for s in d["skipped"]], "")
    return "\n".join(lines) + "\n"
