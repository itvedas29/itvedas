// functions/api/security-feed.js
//
// Cloudflare Pages Function — runs server-side on Cloudflare's edge.
// Fetches raw headlines directly from public security/CVE RSS feeds and
// returns them as JSON, so /security-news.html can show a "Live Threat
// Feed" that updates without waiting for the next scheduled content-pipeline
// run. This is intentionally NOT rewritten by an LLM — it's a straight
// aggregation of source headlines with a link back to the original
// reporting, distinct from ITVedas's own original-commentary articles
// (itvedas-brain/news-agent.py) shown elsewhere on the same page.
//
// GET /api/security-feed

const FEEDS = [
  "https://feeds.feedburner.com/TheHackersNews",
  "https://www.bleepingcomputer.com/feed/",
  "https://feeds.feedburner.com/securityweek",
  "https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss.xml",
];

const CVE_RE = /CVE-\d{4}-\d{4,7}/i;
const ATTACK_RE = /ransomware|breach|hack(ed|er|ing)?|phish|malware|exploit(ed)?|zero-day|ddos|leak(ed)?|attack/i;
const FEED_TIMEOUT_MS = 8000;
const MAX_PER_FEED = 8;
const MAX_TOTAL = 30;

function stripTags(html) {
  return (html || "").replace(/<[^>]+>/g, "").trim();
}

function sourceNameFor(url) {
  try {
    const host = new URL(url).hostname.replace(/^www\./, "");
    if (host === "feeds.feedburner.com") {
      if (url.includes("TheHackersNews")) return "thehackernews.com";
      if (url.includes("securityweek")) return "securityweek.com";
    }
    return host;
  } catch {
    return "source";
  }
}

function classify(title) {
  const cveMatch = title.match(CVE_RE);
  if (cveMatch) return { category: "CVE", cve_id: cveMatch[0].toUpperCase() };
  if (ATTACK_RE.test(title)) return { category: "Attack", cve_id: null };
  return { category: "General", cve_id: null };
}

function parseFeed(xml, feedUrl) {
  const source = sourceNameFor(feedUrl);
  const items = [];

  // <item>...</item> blocks (works for both RSS 2.0 and the Atom-ish
  // feeds in FEEDS above, which are all plain RSS).
  const blocks = xml.match(/<item\b[\s\S]*?<\/item>/gi) || [];

  for (const block of blocks.slice(0, MAX_PER_FEED)) {
    const titleMatch =
      block.match(/<title>\s*<!\[CDATA\[([\s\S]*?)\]\]>\s*<\/title>/i) ||
      block.match(/<title>([\s\S]*?)<\/title>/i);
    const linkMatch = block.match(/<link>\s*([\s\S]*?)\s*<\/link>/i);
    const descMatch =
      block.match(/<description>\s*<!\[CDATA\[([\s\S]*?)\]\]>\s*<\/description>/i) ||
      block.match(/<description>([\s\S]*?)<\/description>/i);
    const dateMatch = block.match(/<pubDate>([\s\S]*?)<\/pubDate>/i);

    const title = stripTags(titleMatch ? titleMatch[1] : "");
    const link = (linkMatch ? linkMatch[1] : "").trim();
    if (!title || !link || title.length < 8) continue;

    const description = stripTags(descMatch ? descMatch[1] : "").slice(0, 220);
    const pubDate = dateMatch ? new Date(dateMatch[1]).toISOString() : null;
    const { category, cve_id } = classify(title);

    items.push({ title, link, description, source, category, cve_id, pub_date: pubDate });
  }
  return items;
}

async function fetchFeed(url) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), FEED_TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      signal: controller.signal,
      headers: { "User-Agent": "ITVedas/1.0 (+https://itvedas.com)" },
    });
    if (!res.ok) return [];
    const xml = await res.text();
    return parseFeed(xml, url);
  } catch {
    return [];
  } finally {
    clearTimeout(timer);
  }
}

export async function onRequestGet() {
  const results = await Promise.allSettled(FEEDS.map(fetchFeed));
  let items = results.flatMap((r) => (r.status === "fulfilled" ? r.value : []));

  // Newest-first where we have a parsed date; feeds without one keep
  // their original (already newest-first) order relative to each other.
  items.sort((a, b) => {
    if (a.pub_date && b.pub_date) return new Date(b.pub_date) - new Date(a.pub_date);
    if (a.pub_date) return -1;
    if (b.pub_date) return 1;
    return 0;
  });

  // De-dupe near-identical titles across feeds (e.g. wire-service reprints).
  const seen = new Set();
  items = items.filter((item) => {
    const key = item.title.slice(0, 60).toLowerCase();
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });

  items = items.slice(0, MAX_TOTAL);

  return new Response(
    JSON.stringify({ generated_at: new Date().toISOString(), items }),
    {
      status: 200,
      headers: {
        "Content-Type": "application/json",
        // Edge-cache for 5 minutes so this stays "near-live" without
        // re-fetching every source feed on every single visitor.
        "Cache-Control": "public, max-age=300",
      },
    }
  );
}

export async function onRequestPost() {
  return new Response(JSON.stringify({ error: "Use GET" }), {
    status: 405,
    headers: { "Content-Type": "application/json" },
  });
}
