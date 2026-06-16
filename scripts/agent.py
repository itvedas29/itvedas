import os, json, urllib.request, pathlib, re, datetime

KEY = os.environ["ANTHROPIC_API_KEY"]

def claude(prompt, max_tokens=2000):
    body = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key": KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
    )
    res = json.load(urllib.request.urlopen(req))
    return res["content"][0]["text"].strip()

def extract_meta(content):
    meta = {"title": "IT Guide", "description": "", "keyword": "", "topic": "IT"}
    match = re.search(r'<!-- META(.*?)-->', content, re.DOTALL)
    if match:
        for line in match.group(1).strip().split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                meta[k.strip()] = v.strip()
    h1 = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE | re.DOTALL)
    if h1:
        meta['title'] = re.sub(r'<[^>]+>', '', h1.group(1)).strip()
    return meta

def extract_body(content):
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
    content = content.replace('[AFFILIATE]', '')
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content.strip()

def get_topic_color(topic):
    colors = {
        "Networking": "#FF6B35",
        "Cloud": "#3B82F6",
        "Security": "#10B981",
        "DevOps": "#8B5CF6",
        "Databases": "#F59E0B",
        "Linux": "#EF4444",
        "Hardware": "#06B6D4",
    }
    return colors.get(topic, "#FF6B35")

def get_reading_time(content):
    words = len(re.sub(r'<[^>]+>', '', content).split())
    minutes = max(1, round(words / 200))
    return f"{minutes} min read"

def wrap_article(body, meta, date_str):
    topic = meta.get('topic', 'IT')
    title = meta.get('title', 'IT Guide')
    description = meta.get('description', f'Learn about {title} on ITVedas')
    keyword = meta.get('keyword', title)
    color = get_topic_color(topic)
    reading_time = get_reading_time(body)

    # Generate table of contents from H2s
    headings = re.findall(r'<h2[^>]*>(.*?)</h2>', body, re.IGNORECASE | re.DOTALL)
    toc_items = ""
    for i, h in enumerate(headings[:6]):
        clean = re.sub(r'<[^>]+>', '', h).strip()
        anchor = re.sub(r'[^a-z0-9]+', '-', clean.lower()).strip('-')
        toc_items += f'<li><a href="#{anchor}" style="color:var(--muted);text-decoration:none;font-size:0.9rem;padding:0.3rem 0;display:block;transition:color 0.2s;" onmouseover="this.style.color=\'{color}\'" onmouseout="this.style.color=\'\'">→ {clean}</a></li>'
        body = body.replace(f'<h2', f'<h2 id="{anchor}"', 1)

    toc_html = f"""
    <div style="background:#13131C;border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:1.5rem;margin:2rem 0;">
      <div style="font-size:0.75rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:{color};margin-bottom:1rem;">In this article</div>
      <ul style="list-style:none;padding:0;margin:0;">{toc_items}</ul>
    </div>""" if toc_items else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="{description}">
<meta name="keywords" content="{keyword}, ITVedas, IT knowledge, {topic.lower()} tutorial">
<meta property="og:title" content="{title} | ITVedas">
<meta property="og:description" content="{description}">
<meta property="og:type" content="article">
<meta property="og:url" content="https://itvedas.com/articles/{date_str}-{topic.lower()}.html">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title} | ITVedas">
<meta name="twitter:description" content="{description}">
<link rel="canonical" href="https://itvedas.com/articles/{date_str}-{topic.lower()}.html">
<title>{title} | ITVedas — IT Knowledge Hub</title>
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{title}",
  "description": "{description}",
  "author": {{"@type": "Organization", "name": "ITVedas"}},
  "publisher": {{"@type": "Organization", "name": "ITVedas", "url": "https://itvedas.com"}},
  "datePublished": "{date_str}",
  "dateModified": "{date_str}",
  "mainEntityOfPage": {{"@type": "WebPage", "@id": "https://itvedas.com/articles/{date_str}-{topic.lower()}.html"}}
}}
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {{
  --bg:#0A0A0F; --bg2:#13131C; --bg3:#1C1C2A;
  --text:#F0F0F8; --muted:#8888A8; --subtle:#D0D0E8;
  --accent:{color}; --border:rgba(255,255,255,0.08);
}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
html{{scroll-behavior:smooth;}}
body{{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;font-size:17px;line-height:1.85;-webkit-font-smoothing:antialiased;}}
/* NAV */
nav{{position:fixed;top:0;left:0;right:0;z-index:100;display:flex;align-items:center;justify-content:space-between;padding:0 2rem;height:64px;background:rgba(10,10,15,0.92);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);}}
.nav-logo{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.3rem;color:var(--text);text-decoration:none;}}
.nav-logo span{{color:var(--accent);}}
.nav-back{{color:var(--muted);text-decoration:none;font-size:0.875rem;display:flex;align-items:center;gap:0.4rem;transition:color 0.2s;}}
.nav-back:hover{{color:var(--text);}}
/* HERO */
.article-hero{{padding:7rem 2rem 3rem;max-width:860px;margin:0 auto;}}
.breadcrumb{{font-size:0.8rem;color:var(--muted);margin-bottom:1.5rem;}}
.breadcrumb a{{color:var(--muted);text-decoration:none;}}
.breadcrumb a:hover{{color:var(--accent);}}
.article-badges{{display:flex;align-items:center;gap:0.75rem;margin-bottom:1.5rem;flex-wrap:wrap;}}
.badge-topic{{background:rgba(255,107,53,0.12);border:1px solid rgba(255,107,53,0.25);color:var(--accent);padding:0.3rem 0.85rem;border-radius:100px;font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;}}
.badge-meta{{color:var(--muted);font-size:0.82rem;display:flex;align-items:center;gap:0.3rem;}}
.article-hero h1{{font-family:'Space Grotesk',sans-serif;font-size:clamp(1.9rem,4vw,3rem);font-weight:700;letter-spacing:-0.025em;line-height:1.12;margin-bottom:1.25rem;}}
.hero-intro{{font-size:1.1rem;color:var(--subtle);line-height:1.75;max-width:700px;border-left:3px solid var(--accent);padding-left:1.25rem;}}
/* LAYOUT */
.article-layout{{display:grid;grid-template-columns:1fr 260px;gap:3rem;max-width:1100px;margin:0 auto;padding:0 2rem 5rem;align-items:start;}}
.article-body h2{{font-family:'Space Grotesk',sans-serif;font-size:1.55rem;font-weight:700;margin:2.75rem 0 1rem;color:var(--text);display:flex;align-items:center;gap:0.75rem;}}
.article-body h2::before{{content:'';display:inline-block;width:4px;height:1.4em;background:var(--accent);border-radius:2px;flex-shrink:0;}}
.article-body h3{{font-family:'Space Grotesk',sans-serif;font-size:1.15rem;font-weight:600;margin:2rem 0 0.6rem;color:var(--text);}}
.article-body p{{margin-bottom:1.35rem;color:var(--subtle);}}
.article-body ul,.article-body ol{{margin:0.75rem 0 1.5rem 1.25rem;color:var(--subtle);}}
.article-body li{{margin-bottom:0.6rem;padding-left:0.25rem;}}
.article-body strong{{color:var(--text);font-weight:600;}}
.article-body blockquote{{background:var(--bg2);border-left:4px solid var(--accent);border-radius:0 8px 8px 0;padding:1.25rem 1.5rem;margin:1.75rem 0;color:var(--subtle);font-style:italic;}}
.article-body code{{background:var(--bg2);border:1px solid var(--border);padding:0.15rem 0.45rem;border-radius:5px;font-family:monospace;font-size:0.875rem;color:#10B981;}}
.article-body pre{{background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:1.5rem;margin:1.75rem 0;overflow-x:auto;}}
.article-body pre code{{background:none;border:none;padding:0;font-size:0.84rem;color:#9FE1CB;line-height:1.7;}}
/* CALLOUT BOX */
.callout{{background:linear-gradient(135deg,rgba(255,107,53,0.08),rgba(139,92,246,0.08));border:1px solid rgba(255,107,53,0.2);border-radius:12px;padding:1.25rem 1.5rem;margin:2rem 0;}}
.callout-title{{font-weight:700;color:var(--accent);font-size:0.85rem;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:0.5rem;}}
/* SIDEBAR */
.article-sidebar{{position:sticky;top:84px;}}
.sidebar-card{{background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:1.25rem;margin-bottom:1rem;}}
.sidebar-title{{font-size:0.75rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:var(--muted);margin-bottom:1rem;}}
.sidebar-nav li{{list-style:none;margin-bottom:0.25rem;}}
.sidebar-nav a{{color:var(--muted);text-decoration:none;font-size:0.875rem;padding:0.3rem 0;display:block;transition:color 0.2s;border-left:2px solid transparent;padding-left:0.6rem;}}
.sidebar-nav a:hover{{color:var(--text);border-left-color:var(--accent);}}
.chapter-links a{{display:block;color:var(--muted);text-decoration:none;font-size:0.85rem;padding:0.35rem 0;border-bottom:1px solid var(--border);transition:color 0.2s;}}
.chapter-links a:last-child{{border-bottom:none;}}
.chapter-links a:hover{{color:var(--accent);}}
/* KEY TAKEAWAY */
.takeaway-box{{background:var(--bg3);border:1px solid var(--border);border-radius:16px;padding:2rem;margin:3rem 0;}}
.takeaway-box h3{{font-family:'Space Grotesk',sans-serif;font-size:1.1rem;font-weight:700;color:var(--accent);margin-bottom:1rem;}}
.takeaway-box ul{{margin:0;padding:0;list-style:none;}}
.takeaway-box li{{padding:0.5rem 0;border-bottom:1px solid var(--border);color:var(--subtle);font-size:0.95rem;display:flex;gap:0.6rem;}}
.takeaway-box li:last-child{{border-bottom:none;}}
.takeaway-box li::before{{content:'✓';color:var(--accent);font-weight:700;flex-shrink:0;}}
/* PROGRESS BAR */
.reading-progress{{position:fixed;top:64px;left:0;right:0;height:2px;background:transparent;z-index:99;}}
.reading-progress-bar{{height:100%;background:var(--accent);width:0%;transition:width 0.1s;}}
/* FOOTER */
footer{{border-top:1px solid var(--border);padding:2.5rem 2rem;text-align:center;color:var(--muted);font-size:0.875rem;}}
footer .footer-logo{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.1rem;margin-bottom:0.5rem;color:var(--text);}}
footer .footer-logo span{{color:var(--accent);}}
footer a{{color:var(--muted);text-decoration:none;}}
footer a:hover{{color:var(--accent);}}
@media(max-width:900px){{
  .article-layout{{grid-template-columns:1fr;}}
  .article-sidebar{{display:none;}}
  .article-hero,.article-layout{{padding-left:1.25rem;padding-right:1.25rem;}}
}}
@media(prefers-reduced-motion:reduce){{*{{animation:none!important;transition:none!important;}}}}
</style>
</head>
<body>
<div class="reading-progress"><div class="reading-progress-bar" id="progress"></div></div>
<nav>
  <a href="/" class="nav-logo">IT<span>Vedas</span></a>
  <a href="/" class="nav-back">← Back to Home</a>
</nav>

<div class="article-hero">
  <div class="breadcrumb">
    <a href="/">Home</a> → <a href="/#chapters">{topic}</a> → Article
  </div>
  <div class="article-badges">
    <span class="badge-topic">{topic}</span>
    <span class="badge-meta">📅 {date_str}</span>
    <span class="badge-meta">⏱ {reading_time}</span>
    <span class="badge-meta">👤 Beginner friendly</span>
  </div>
  <h1>{title}</h1>
</div>

<div class="article-layout">
  <article class="article-body">
    {toc_html}
    {body}
    <div class="takeaway-box">
      <h3>What you learned in this article</h3>
      <ul>
        <li>The core concept of {topic.lower()} explained simply</li>
        <li>How it works in the real world with everyday examples</li>
        <li>Why it matters for you and your digital life</li>
        <li>Practical knowledge you can use right now</li>
        <li>Where to go next on your IT learning journey</li>
      </ul>
    </div>
    <div style="margin-top:3rem;padding:1.5rem;background:var(--bg2);border-radius:12px;border:1px solid var(--border);text-align:center;">
      <p style="margin-bottom:1rem;font-weight:600;font-size:1rem;">Enjoyed this article? Explore more on ITVedas.</p>
      <a href="/" style="display:inline-block;background:var(--accent);color:white;padding:0.75rem 2rem;border-radius:8px;text-decoration:none;font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:0.9rem;">← Back to All Chapters</a>
    </div>
  </article>

  <aside class="article-sidebar">
    <div class="sidebar-card">
      <div class="sidebar-title">In this article</div>
      <ul class="sidebar-nav">{toc_items}</ul>
    </div>
    <div class="sidebar-card">
      <div class="sidebar-title">Explore chapters</div>
      <div class="chapter-links">
        <a href="/#chapters">🌐 Networking</a>
        <a href="/#chapters">☁️ Cloud</a>
        <a href="/#chapters">🔐 Security</a>
        <a href="/#chapters">⚙️ DevOps</a>
        <a href="/#chapters">🗄️ Databases</a>
        <a href="/#chapters">🐧 Linux</a>
        <a href="/#chapters">🖥️ Hardware</a>
      </div>
    </div>
    <div class="sidebar-card" style="background:linear-gradient(135deg,rgba(255,107,53,0.08),rgba(139,92,246,0.08));border-color:rgba(255,107,53,0.2);">
      <div class="sidebar-title" style="color:var(--accent);">Free newsletter</div>
      <p style="font-size:0.85rem;color:var(--muted);margin-bottom:1rem;">New IT guides every week — plain English, no jargon.</p>
      <a href="/#newsletter" style="display:block;text-align:center;background:var(--accent);color:white;padding:0.6rem;border-radius:8px;text-decoration:none;font-size:0.85rem;font-weight:600;">Subscribe Free</a>
    </div>
  </aside>
</div>

<footer>
  <div class="footer-logo">IT<span>Vedas</span></div>
  <p>The complete IT knowledge hub — explained simply, for everyone.</p>
  <div style="display:flex;gap:2rem;justify-content:center;margin:1rem 0;flex-wrap:wrap;">
    <a href="/">Home</a>
    <a href="/#chapters">Chapters</a>
    <a href="/#newsletter">Newsletter</a>
    <a href="/sitemap.xml">Sitemap</a>
  </div>
  <p style="margin-top:1rem;">© 2026 ITVedas. Built with purpose, powered by knowledge.</p>
</footer>

<script>
window.addEventListener('scroll', () => {{
  const doc = document.documentElement;
  const scrolled = (doc.scrollTop / (doc.scrollHeight - doc.clientHeight)) * 100;
  document.getElementById('progress').style.width = Math.min(100, scrolled) + '%';
}});
</script>
</body>
</html>"""

def update_homepage(articles):
    index_path = pathlib.Path("index.html")
    if not index_path.exists():
        print("index.html not found")
        return
    html = index_path.read_text(encoding="utf-8")
    items = ""
    for a in articles[:8]:
        color = get_topic_color(a['topic'])
        items += f"""
        <a href="/articles/{a['file']}" style="display:flex;align-items:flex-start;gap:1rem;padding:1rem 0;border-bottom:1px solid rgba(255,255,255,0.06);text-decoration:none;color:inherit;transition:background 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.02)'" onmouseout="this.style.background=''">
          <span style="background:rgba(255,107,53,0.1);color:{color};font-size:0.68rem;font-weight:700;padding:0.25rem 0.6rem;border-radius:4px;white-space:nowrap;text-transform:uppercase;letter-spacing:0.05em;margin-top:2px;">{a['topic']}</span>
          <div>
            <div style="font-size:0.95rem;color:#D0D0E8;line-height:1.4;margin-bottom:0.2rem;">{a['title']}</div>
            <div style="font-size:0.75rem;color:#8888A8;">{a['date']} · {a.get('reading_time','5 min read')}</div>
          </div>
        </a>"""

    latest = f"""
<!-- LATEST_ARTICLES_START -->
<div id="latest-articles" style="background:#13131C;border-top:1px solid rgba(255,255,255,0.08);border-bottom:1px solid rgba(255,255,255,0.08);padding:5rem 2rem;">
  <div style="max-width:1200px;margin:0 auto;">
    <div style="font-size:0.75rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#FF6B35;margin-bottom:0.75rem;">Latest Articles</div>
    <h2 style="font-family:'Space Grotesk',sans-serif;font-size:clamp(1.75rem,3vw,2.5rem);font-weight:700;letter-spacing:-0.02em;margin-bottom:0.75rem;">Fresh from the Knowledge Hub</h2>
    <p style="color:#8888A8;margin-bottom:2.5rem;max-width:500px;">New articles published every Monday, Wednesday and Friday — always in plain English.</p>
    <div style="max-width:720px;">{items}
    </div>
  </div>
</div>
<!-- LATEST_ARTICLES_END -->"""

    if '<!-- LATEST_ARTICLES_START -->' in html:
        html = re.sub(r'<!-- LATEST_ARTICLES_START -->.*?<!-- LATEST_ARTICLES_END -->', latest, html, flags=re.DOTALL)
    else:
        html = html.replace('<div style="padding:5rem 0;" id="newsletter">', latest + '\n<div style="padding:5rem 0;" id="newsletter">')
    index_path.write_text(html, encoding="utf-8")
    print("Homepage updated")

def get_published_articles():
    articles_dir = pathlib.Path("articles")
    articles = []
    if articles_dir.exists():
        for f in sorted(articles_dir.glob("*.html"), reverse=True):
            content = f.read_text(encoding="utf-8")
            meta = extract_meta(content)
            parts = f.stem.split("-")
            topic = parts[-1].capitalize() if len(parts) > 3 else meta.get('topic', 'IT')
            date_str = "-".join(parts[:3]) if len(parts) >= 3 else ""
            words = len(re.sub(r'<[^>]+>', '', content).split())
            articles.append({
                "file": f.name,
                "title": meta.get('title', f.stem),
                "topic": topic,
                "date": date_str,
                "reading_time": f"{max(1,round(words/200))} min read"
            })
    return articles

def main():
    drafts_dir = pathlib.Path("drafts")
    articles_dir = pathlib.Path("articles")
    articles_dir.mkdir(exist_ok=True)

    drafts = [f for f in drafts_dir.glob("*.html")] if drafts_dir.exists() else []
    if not drafts:
        print("No drafts to publish")
        return

    published = 0
    for draft_path in drafts:
        print(f"Publishing: {draft_path.name}")
        content = draft_path.read_text(encoding="utf-8")
        meta = extract_meta(content)
        body = extract_body(content)
        parts = draft_path.stem.split("-")
        date_str = "-".join(parts[:3]) if len(parts) >= 3 else str(datetime.date.today())
        full_page = wrap_article(body, meta, date_str)
        out = articles_dir / draft_path.name
        out.write_text(full_page, encoding="utf-8")
        draft_path.unlink()
        print(f"Live: articles/{draft_path.name}")
        published += 1

    if published > 0:
        all_articles = get_published_articles()
        update_homepage(all_articles)
        print(f"Published {published} articles. Homepage updated.")

if __name__ == "__main__":
    main()
