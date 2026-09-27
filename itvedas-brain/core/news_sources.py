"""News discovery for ITVedas: many sources in, a few well-grounded stories out.

Pipeline (all standard library):
  1. fetch_all_feeds()  - parse RSS 2.0 and Atom properly (not regex), keep
                          items from the last FRESH_HOURS, record feed health.
  2. cluster_items()    - merge coverage of the same story across outlets
                          (shared CVE id, or similar headline wording).
  3. rank_clusters()    - importance: number of outlets, known exploitation,
                          CVSS from our own CVE database, security topic.
  4. fetch_article_text()/build_dossier() - read the actual source pages so
                          the writer has facts, not just a 300-char snippet.
  5. sanitize_html()    - model output is untrusted (source pages can carry
                          prompt injections); only a small tag allowlist
                          survives.
"""
from __future__ import annotations

import datetime as _dt
import email.utils
import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

USER_AGENT = "ITVedasNewsBot/2.0 (+https://www.itvedas.com/about)"
FRESH_HOURS = 48
MAX_ITEMS_PER_FEED = 20

# Curated, reputable sources. A feed that fails is logged and skipped, so a
# dead URL never breaks a run - check the "Feed health" lines in the log.
NEWS_FEEDS = [
    # Security news
    "https://feeds.feedburner.com/TheHackersNews",
    "https://www.bleepingcomputer.com/feed/",
    "https://feeds.feedburner.com/securityweek",
    "https://krebsonsecurity.com/feed/",
    "https://www.darkreading.com/rss.xml",
    "https://www.helpnetsecurity.com/feed/",
    "https://www.theregister.com/security/headlines.atom",
    "https://arstechnica.com/security/feed/",
    # Primary / research sources
    "https://www.cisa.gov/cybersecurity-advisories/all.xml",
    "https://isc.sans.edu/rssfeed_full.xml",
    "https://msrc.microsoft.com/blog/feed",
    "https://security.googleblog.com/feeds/posts/default",
    "https://blog.talosintelligence.com/rss/",
    "https://unit42.paloaltonetworks.com/feed/",
    # Cloud, DevOps, Linux, platforms
    "https://aws.amazon.com/blogs/aws/feed/",
    "https://cloudblogs.microsoft.com/feed/",
    "https://kubernetes.io/feed.xml",
    "https://github.blog/feed/",
    "https://lwn.net/headlines/rss",
]

# Vendors/projects announcing their own news - worth covering even when only
# one outlet has it (e.g. a Kubernetes release on kubernetes.io).
OFFICIAL_SOURCES = {"msrc.microsoft.com", "security.googleblog.com", "blog.talosintelligence.com",
                    "unit42.paloaltonetworks.com", "aws.amazon.com", "cloudblogs.microsoft.com",
                    "kubernetes.io", "github.blog", "lwn.net", "isc.sans.edu"}

# Stories scoring below this are skipped even if there is room under the cap:
# a single outlet's non-security item scores 3, so it needs another signal
# (second outlet, security relevance, official source, CVE severity).
MIN_SCORE = 4.0

_STOP = set("""a an the and or of to in on for with by from at as is are was were be been this that
these those it its into over after before new how why what who when your you we our their
says said report reports update updates via amid""".split())
CVE_RE = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.I)


# ── 1. feeds ──────────────────────────────────────────────────────────
def _text(el) -> str:
    return "".join(el.itertext()).strip() if el is not None else ""


def _strip_tags(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def _parse_date(s: str):
    if not s:
        return None
    try:
        d = email.utils.parsedate_to_datetime(s)          # RSS: RFC 822
    except (TypeError, ValueError):
        try:
            d = _dt.datetime.fromisoformat(s.strip().replace("Z", "+00:00"))  # Atom: ISO 8601
        except ValueError:
            return None
    return d if d.tzinfo else d.replace(tzinfo=_dt.timezone.utc)


def parse_feed(xml_text: str, feed_url: str) -> list[dict]:
    """Parse RSS 2.0 or Atom into [{title, link, desc, source, published}]."""
    root = ET.fromstring(xml_text)
    source = re.sub(r"^www\.", "", feed_url.split("/")[2])
    items = []
    atom = "{http://www.w3.org/2005/Atom}"
    for it in root.iter():
        tag = it.tag.split("}")[-1]
        if tag not in ("item", "entry"):
            continue
        get = lambda name: it.find(name) if it.find(name) is not None else it.find(atom + name)
        title = _strip_tags(_text(get("title")))
        link = ""
        link_el = get("link")
        if link_el is not None:
            link = (link_el.get("href") or _text(link_el)).strip()
        if it.tag.startswith(atom):  # Atom: prefer rel=alternate
            for l in it.findall(atom + "link"):
                if l.get("rel", "alternate") == "alternate" and l.get("href"):
                    link = l.get("href"); break
        desc = ""
        for name in ("description", "summary", "content"):
            el = get(name)
            if el is not None and _text(el):
                desc = _strip_tags(_text(el)); break
        date = None
        for name in ("pubDate", "published", "updated", "{http://purl.org/dc/elements/1.1/}date"):
            el = it.find(name) if name.startswith("{") else get(name)
            if el is not None and _text(el):
                date = _parse_date(_text(el)); break
        if title and len(title) > 10 and link.startswith("http"):
            items.append({"title": title, "link": link, "desc": desc[:600],
                          "source": source, "published": date})
        if len(items) >= MAX_ITEMS_PER_FEED:
            break
    return items


def _http_get(url: str, timeout: int = 15, limit: int = 3_000_000) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(limit).decode("utf-8", "ignore")


def fetch_all_feeds(feeds=None, now=None, log=print, fetch=None) -> list[dict]:
    fetch = fetch or _http_get
    now = now or _dt.datetime.now(_dt.timezone.utc)
    cutoff = now - _dt.timedelta(hours=FRESH_HOURS)
    out, health = [], []
    for url in feeds or NEWS_FEEDS:
        try:
            items = parse_feed(fetch(url), url)
            fresh = [i for i in items if i["published"] is None or i["published"] >= cutoff]
            out.extend(fresh)
            health.append(f"ok {len(fresh):>2}/{len(items):<2} {url}")
        except Exception as e:
            health.append(f"FAIL        {url} ({type(e).__name__}: {str(e)[:80]})")
    log("Feed health:\n  " + "\n  ".join(health))
    return out


# ── 2. clustering ─────────────────────────────────────────────────────
def title_tokens(title: str) -> set[str]:
    words = re.findall(r"[a-z0-9][a-z0-9.+-]*", title.lower())
    return {w for w in words if w not in _STOP and len(w) > 2}


def cves_in(*texts) -> set[str]:
    return {m.upper() for t in texts for m in CVE_RE.findall(t or "")}


def _similar(a: set, b: set) -> bool:
    if not a or not b:
        return False
    inter = len(a & b)
    return inter >= 3 and inter / min(len(a), len(b)) >= 0.6


def cluster_items(items: list[dict]) -> list[dict]:
    """Group items that report the same story. Returns clusters:
    {items, tokens, cves, sources, lead}."""
    clusters: list[dict] = []
    for it in items:
        toks = title_tokens(it["title"])
        cv = cves_in(it["title"], it["desc"])
        home = None
        for c in clusters:
            if (cv and cv & c["cves"]) or _similar(toks, c["tokens"]):
                home = c; break
        if home is None:
            clusters.append({"items": [it], "tokens": set(toks), "cves": set(cv)})
        elif all(x["link"] != it["link"] for x in home["items"]):
            home["items"].append(it); home["tokens"] |= toks; home["cves"] |= cv
    for c in clusters:
        c["sources"] = sorted({i["source"] for i in c["items"]})
        c["lead"] = max(c["items"], key=lambda i: len(i["desc"]))
    return clusters


def story_key(cluster: dict) -> str:
    """Stable identity used to avoid re-publishing a story on later days."""
    if cluster["cves"]:
        return "cve:" + ",".join(sorted(cluster["cves"]))
    return "t:" + " ".join(sorted(cluster["tokens"])[:12])


def already_published(cluster: dict, seen_keys: dict) -> bool:
    key = story_key(cluster)
    if key in seen_keys:
        return True
    if cluster["cves"]:
        return any(k.startswith("cve:") and set(k[4:].split(",")) & cluster["cves"] for k in seen_keys)
    for k in seen_keys:
        if k.startswith("t:") and _similar(set(k[2:].split()), cluster["tokens"]):
            return True
    return False


# ── 3. ranking ────────────────────────────────────────────────────────
_SEC = re.compile(r"hack|vuln|breach|ransomware|phish|malware|exploit|attack|zero-day|0-day|backdoor|leak|patch", re.I)


def rank_clusters(clusters: list[dict], cve_lookup=None) -> list[dict]:
    """Highest importance first. cve_lookup(id) -> record from our CVE DB."""
    for c in clusters:
        facts = [cve_lookup(x) for x in sorted(c["cves"])] if cve_lookup else []
        c["cve_facts"] = [f for f in facts if f]
        score = 3.0 * len(c["sources"])                                  # independent coverage
        if any(f.get("known_exploited") for f in c["cve_facts"]):
            score += 6                                                    # CISA KEV
        cvss = max((float(f.get("cvss") or 0) for f in c["cve_facts"]), default=0)
        score += 3 if cvss >= 9 else 1.5 if cvss >= 7 else 0
        if _SEC.search(" ".join(i["title"] for i in c["items"])):
            score += 1
        if any("cisa.gov" in s for s in c["sources"]):
            score += 2                                                    # government advisory
        elif any(s in OFFICIAL_SOURCES for s in c["sources"]):
            score += 1                                                    # vendor/project's own announcement
        c["score"] = score
    return sorted(clusters, key=lambda c: -c["score"])


# ── 4. grounding ──────────────────────────────────────────────────────
class _TextExtractor(HTMLParser):
    SKIP = {"script", "style", "nav", "footer", "header", "aside", "form", "noscript", "svg", "figure"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth_skip = 0; self.in_p = False; self.paras = []; self.buf = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP: self.depth_skip += 1
        elif tag in ("p", "li", "h2", "h3") and not self.depth_skip:
            self.in_p = True; self.buf = []

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.depth_skip: self.depth_skip -= 1
        elif tag in ("p", "li", "h2", "h3") and self.in_p:
            t = re.sub(r"\s+", " ", "".join(self.buf)).strip()
            if len(t) > 40: self.paras.append(t)
            self.in_p = False

    def handle_data(self, data):
        if self.in_p and not self.depth_skip: self.buf.append(data)


# Site chrome, not article content. Deliberately phrase-based: security
# articles legitimately discuss "cookies", "sign-up" flows, etc.
_BOILERPLATE = re.compile(
    r"(we use|accept|manage|our) cookies|cookie (policy|settings|preferences)|subscribe to (our|the)|"
    r"newsletter|sign up (for|to) (our|the)|all rights reserved|follow us on|share this article|"
    r"advertisement|sponsored content", re.I)


def extract_article_text(page_html: str, max_chars: int = 5000) -> str:
    p = _TextExtractor()
    try:
        p.feed(page_html)
    except Exception:
        pass
    text, seen = [], set()
    for para in p.paras:
        if para in seen or _BOILERPLATE.search(para):
            continue
        seen.add(para); text.append(para)
        if sum(map(len, text)) >= max_chars:
            break
    return "\n".join(text)[:max_chars]


def fetch_article_text(url: str, fetch=None) -> str:
    fetch = fetch or _http_get
    try:
        return extract_article_text(fetch(url, timeout=15, limit=2_000_000))
    except Exception:
        return ""


def build_dossier(cluster: dict, fetch=None, max_sources: int = 3) -> str:
    """Source material for the writer and the reviewer: full text from up to
    max_sources outlets (falling back to the feed summary), plus verified
    fields from our CVE database."""
    parts = []
    for it in sorted(cluster["items"], key=lambda i: -len(i["desc"]))[:max_sources]:
        body = fetch_article_text(it["link"], fetch) or it["desc"]
        parts.append(f"### SOURCE: {it['source']} - {it['title']}\nURL: {it['link']}\n{body}")
    for f in cluster.get("cve_facts", []):
        parts.append(
            "### VERIFIED CVE DATA (ITVedas CVE database, from NVD/CISA)\n"
            f"ID: {f.get('id')}\nCVSS: {f.get('cvss')} ({f.get('severity')})\n"
            f"Known exploited (CISA KEV): {'yes' if f.get('known_exploited') else 'no'}\n"
            f"Affected: {', '.join(f.get('affected_products') or []) or f.get('affected', 'Unknown')}\n"
            f"Weakness: {', '.join(f.get('cwe') or []) or 'n/a'}\n"
            f"Description: {f.get('description', '')}"
        )
    return "\n\n".join(parts)


# ── 5. output safety ──────────────────────────────────────────────────
_ALLOWED = {"h2", "h3", "p", "ul", "ol", "li", "strong", "em", "b", "i", "blockquote", "code", "pre", "a", "br", "table", "thead", "tbody", "tr", "th", "td"}


class _Sanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []; self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "iframe", "object", "embed", "svg", "math", "template"):
            self.skip += 1; return
        if self.skip or tag not in _ALLOWED:
            return
        if tag == "a":
            href = dict(attrs).get("href", "")
            if re.match(r"^(https?://|/)", href or ""):
                self.out.append(f'<a href="{html.escape(href, quote=True)}" rel="noopener nofollow" target="_blank">')
            else:
                self.out.append("<a>")
        else:
            self.out.append(f"<{tag}>")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "iframe", "object", "embed", "svg", "math", "template"):
            self.skip = max(0, self.skip - 1); return
        if not self.skip and tag in _ALLOWED and tag != "br":
            self.out.append(f"</{tag}>")

    def handle_data(self, data):
        if not self.skip:
            self.out.append(html.escape(data, quote=False))


def sanitize_html(fragment: str) -> str:
    """Keep only simple article markup; drop scripts, event handlers, styles,
    iframes and non-http(s) links. Model output must pass through this."""
    s = _Sanitizer()
    s.feed(fragment or "")
    s.close()
    return "".join(s.out)
