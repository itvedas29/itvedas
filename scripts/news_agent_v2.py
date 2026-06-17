"""
ITVedas News Agent v2 — Original Commentary Edition
===================================================
Reads real IT/cybersecurity headlines, then writes
COMPLETELY ORIGINAL news articles hosted on ITVedas.

Legal: transformative original content, not copying.
Each story = own headline, own words, own analysis,
own page on itvedas.com, with a source citation link.
"""
import os, json, urllib.request, pathlib, datetime, re, time, hashlib

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL   = "claude-haiku-4-5-20251001"
SITE    = "https://itvedas.com"

TOPIC_COLORS = {
    "Security":"#10B981","Cloud":"#3B82F6","DevOps":"#8B5CF6",
    "Networking":"#FF6B35","Databases":"#F59E0B","Linux":"#EF4444",
    "Hardware":"#06B6D4","Compliance":"#EC4899","AI":"#F97316","General":"#64748B"
}

TOPIC_EMOJI = {
    "Security":"🔐","Cloud":"☁️","DevOps":"⚙️","Networking":"🌐",
    "Databases":"🗄️","Linux":"🐧","Hardware":"🖥️","Compliance":"📋",
    "AI":"🤖","General":"📰"
}

NEWS_FEEDS = [
    "https://feeds.feedburner.com/TheHackersNews",
    "https://www.bleepingcomputer.com/feed/",
    "https://feeds.feedburner.com/securityweek",
    "https://aws.amazon.com/blogs/aws/feed/",
    "https://kubernetes.io/feed.xml",
    "https://cloudblogs.microsoft.com/feed/",
]

def think(prompt, max_tokens=2500):
    body = json.dumps({"model":MODEL,"max_tokens":max_tokens,
        "messages":[{"role":"user","content":prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages",
        data=body, headers={"x-api-key":API_KEY,"anthropic-version":"2023-06-01","content-type":"application/json"})
    for i in range(3):
        try:
            return json.load(urllib.request.urlopen(req,timeout=90))["content"][0]["text"].strip()
        except Exception as e:
            if i==2: raise
            print(f"API retry {i+1}: {e}")
            time.sleep(6)

def fetch_feed(url):
    items = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"ITVedas/1.0"})
        xml = urllib.request.urlopen(req,timeout=12).read().decode("utf-8","ignore")
        titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>|<title>(.*?)</title>', xml)
        links  = re.findall(r'<link>(https?://[^<]+)</link>', xml)
        descs  = re.findall(r'<description><!\[CDATA\[(.*?)\]\]></description>|<description>(.*?)</description>', xml, re.DOTALL)
        source = url.split('/')[2].replace('www.','').replace('feeds.feedburner.com','source')
        for i,(t1,t2) in enumerate(titles[1:6]):
            title = (t1 or t2).strip()
            link  = links[i+1] if i+1 < len(links) else url
            d1,d2 = descs[i] if i < len(descs) else ("","")
            desc  = re.sub(r'<[^>]+>','',(d1 or d2))[:300].strip()
            if title and len(title)>10:
                items.append({"title":title,"link":link,"desc":desc,"source":source})
    except Exception as e:
        print(f"Feed fetch error ({url}): {e}")
    return items

def classify(title):
    t = title.lower()
    if any(w in t for w in ["hack","vuln","breach","ransomware","phish","malware","cve","exploit","attack","cyber","threat"]): return "Security"
    if any(w in t for w in ["aws","azure","gcp","cloud","serverless","s3","ec2"]): return "Cloud"
    if any(w in t for w in ["kubernetes","docker","devops","ci/cd","terraform","deploy"]): return "DevOps"
    if any(w in t for w in ["linux","ubuntu","kernel","bash"]): return "Linux"
    if any(w in t for w in ["database","sql","mongodb","postgres"]): return "Databases"
    if any(w in t for w in ["network","dns","firewall","vpn"]): return "Networking"
    if any(w in t for w in ["gpu","cpu","chip","hardware","server"]): return "Hardware"
    if any(w in t for w in ["gdpr","hipaa","compliance","regulation","pci"]): return "Compliance"
    if any(w in t for w in ["ai","llm","gpt","machine learning"]): return "AI"
    return "General"

def write_original_article(item):
    """Claude writes a COMPLETELY ORIGINAL article about the news topic."""
    topic = classify(item['title'])
    prompt = f"""You are an IT news writer for ITVedas. A story is breaking on this topic:

HEADLINE SEEN: {item['title']}
CONTEXT: {item['desc']}
TOPIC: {topic}

Write a COMPLETELY ORIGINAL news article in YOUR OWN WORDS. Do NOT copy any phrasing.
This is your own reporting and analysis — transformative original content.

RULES:
- Write your OWN original headline (different wording from the source)
- 500-700 words, plain English for beginners
- Explain what happened, why it matters, and what readers should do
- Add YOUR OWN analysis and "what this means for you" perspective
- Use real-world analogies for any technical terms
- Never reproduce sentences from the source — explain the concept yourself

Output format — START with this meta block:
<!-- META
headline: [your original headline]
summary: [1 sentence, 140 chars max]
topic: {topic}
-->

Then the article body using h2, p, ul, li, blockquote, strong tags.
Structure:
- Opening paragraph: what happened (your words)
- <h2>What this means</h2>
- <h2>Why you should care</h2>
- <h2>What you can do</h2>
- Closing: 1 sentence

Return ONLY meta block + HTML body. No html/head/body tags."""

    return think(prompt, max_tokens=2000)

def parse_article(content, item):
    meta = {"headline":item['title'],"summary":item['desc'][:140],"topic":classify(item['title'])}
    m = re.search(r'<!-- META(.*?)-->', content, re.DOTALL)
    if m:
        for line in m.group(1).strip().split('\n'):
            if ':' in line:
                k,v = line.split(':',1)
                k=k.strip()
                if k in meta: meta[k]=v.strip()
    body = re.sub(r'<!-- META.*?-->','',content,flags=re.DOTALL).strip()
    return meta, body

def build_article_page(meta, body, item, date_str, slug, time_str=""):
    topic = meta['topic']
    color = TOPIC_COLORS.get(topic,"#64748B")
    emoji = TOPIC_EMOJI.get(topic,"📰")
    headline = meta['headline']
    summary = meta['summary']
    source = item.get('source','source')
    source_link = item.get('link','#')
    words = len(re.sub(r'<[^>]+>','',body).split())
    rt = f"{max(1,round(words/200))} min read"

    # TOC
    headings = re.findall(r'<h2[^>]*>(.*?)</h2>', body, re.IGNORECASE|re.DOTALL)
    for h in headings:
        clean = re.sub(r'<[^>]+>','',h).strip()
        anc = re.sub(r'[^a-z0-9]+','-',clean.lower()).strip('-')
        body = re.sub(rf'<h2([^>]*)>{re.escape(h)}</h2>', f'<h2\\1 id="{anc}">{h}</h2>', body, count=1)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="description" content="{summary}">
<meta name="keywords" content="{topic} news, IT news, {headline[:50]}">
<meta name="robots" content="index,follow">
<meta property="og:title" content="{headline} | ITVedas News">
<meta property="og:description" content="{summary}">
<meta property="og:type" content="article">
<link rel="canonical" href="{SITE}/news/{slug}.html">
<title>{headline} | ITVedas News</title>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"NewsArticle","headline":"{headline}",
"description":"{summary}","datePublished":"{date_str}","dateModified":"{date_str}",
"author":{{"@type":"Organization","name":"ITVedas"}},
"publisher":{{"@type":"Organization","name":"ITVedas","url":"{SITE}"}}}}
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{--bg:#0A0A0F;--bg2:#13131C;--bg3:#1C1C2A;--text:#F0F0F8;--muted:#8888A8;--sub:#D0D0E8;--accent:{color};--border:rgba(255,255,255,0.08);}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
html{{scroll-behavior:smooth;}}
body{{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;font-size:17px;line-height:1.85;-webkit-font-smoothing:antialiased;}}
nav{{position:fixed;top:0;left:0;right:0;z-index:100;display:flex;align-items:center;justify-content:space-between;padding:0 2rem;height:64px;background:rgba(10,10,15,0.92);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);}}
.logo{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.3rem;color:var(--text);text-decoration:none;}}
.logo span{{color:#FF6B35;}}
.nav-back{{color:var(--muted);text-decoration:none;font-size:0.875rem;padding:0.5rem 1rem;border:1px solid var(--border);border-radius:8px;transition:color 0.2s;}}
.nav-back:hover{{color:var(--text);}}
.hero-visual{{margin-top:64px;height:240px;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,{color}22,{color}08);border-bottom:1px solid var(--border);position:relative;overflow:hidden;}}
.hero-visual::before{{content:'';position:absolute;inset:0;background:radial-gradient(circle at 50% 50%,{color}18,transparent 70%);}}
.hero-emoji{{font-size:5rem;position:relative;z-index:1;filter:drop-shadow(0 8px 24px {color}44);}}
.hero{{max-width:780px;margin:0 auto;padding:2.5rem 2rem 1rem;}}
.breadcrumb{{font-size:0.8rem;color:var(--muted);margin-bottom:1.25rem;}}
.breadcrumb a{{color:var(--muted);text-decoration:none;}}
.breadcrumb a:hover{{color:var(--accent);}}
.badges{{display:flex;gap:0.6rem;margin-bottom:1.25rem;flex-wrap:wrap;align-items:center;}}
.badge{{background:{color}1f;border:1px solid {color}44;color:{color};padding:0.3rem 0.85rem;border-radius:100px;font-size:0.73rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;}}
.badge-info{{color:var(--muted);font-size:0.8rem;background:var(--bg2);border:1px solid var(--border);padding:0.25rem 0.7rem;border-radius:100px;}}
h1{{font-family:'Space Grotesk',sans-serif;font-size:clamp(1.7rem,3.5vw,2.5rem);font-weight:700;letter-spacing:-0.02em;line-height:1.15;margin-bottom:1rem;}}
.summary{{font-size:1.1rem;color:var(--sub);border-left:3px solid var(--accent);padding-left:1.25rem;margin-bottom:1rem;}}
.article{{max-width:780px;margin:0 auto;padding:1.5rem 2rem 4rem;}}
.article h2{{font-family:'Space Grotesk',sans-serif;font-size:1.4rem;font-weight:700;margin:2.5rem 0 1rem;padding-left:1rem;border-left:4px solid var(--accent);}}
.article p{{margin-bottom:1.3rem;color:var(--sub);}}
.article ul,.article ol{{margin:0.75rem 0 1.5rem 1.5rem;color:var(--sub);}}
.article li{{margin-bottom:0.6rem;}}
.article strong{{color:var(--text);}}
.article blockquote{{background:var(--bg2);border-left:4px solid var(--accent);border-radius:0 10px 10px 0;padding:1.2rem 1.5rem;margin:1.75rem 0;color:var(--sub);font-style:italic;}}
.source-box{{margin-top:2.5rem;padding:1.25rem 1.5rem;background:var(--bg2);border:1px solid var(--border);border-radius:12px;font-size:0.875rem;color:var(--muted);}}
.source-box a{{color:var(--accent);text-decoration:none;}}
.source-box a:hover{{text-decoration:underline;}}
.cta{{margin-top:2rem;padding:2rem;background:linear-gradient(135deg,{color}14,#8B5CF614);border:1px solid {color}33;border-radius:16px;text-align:center;}}
.cta p{{margin-bottom:1.25rem;color:var(--sub);}}
.btn{{display:inline-block;background:var(--accent);color:#fff;padding:0.8rem 2rem;border-radius:10px;text-decoration:none;font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:0.9rem;}}
footer{{border-top:1px solid var(--border);padding:2.5rem 2rem;text-align:center;color:var(--muted);font-size:0.875rem;}}
.fl{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.1rem;color:var(--text);margin-bottom:0.5rem;}}
.fl span{{color:#FF6B35;}}
.flinks{{display:flex;gap:1.5rem;justify-content:center;margin-top:0.75rem;flex-wrap:wrap;}}
.flinks a{{color:var(--muted);text-decoration:none;}}
.flinks a:hover{{color:#FF6B35;}}
@media(max-width:640px){{nav{{padding:0 1.25rem;}}.hero,.article{{padding-left:1.25rem;padding-right:1.25rem;}}}}
</style>
</head>
<body>
<nav>
  <a href="/" class="logo">IT<span>Vedas</span></a>
  <a href="/news.html" class="nav-back">← All News</a>
</nav>
<div class="hero-visual"><div class="hero-emoji">{emoji}</div></div>
<div class="hero">
  <div class="breadcrumb"><a href="/">Home</a> › <a href="/news.html">News</a> › {topic}</div>
  <div class="badges">
    <span class="badge">{topic}</span>
    <span class="badge-info">📅 {date_str}{(' · ' + time_str) if time_str else ''}</span>
    <span class="badge-info">⏱ {rt}</span>
  </div>
  <h1>{headline}</h1>
  <p class="summary">{summary}</p>
</div>
<div class="article">
  {body}
  <div class="source-box">
    📎 This is original ITVedas reporting. This story was inspired by coverage from <a href="{source_link}" target="_blank" rel="noopener nofollow">{source}</a>. Visit the source for their original reporting.
  </div>
  <div class="cta">
    <p>Want to understand the technology behind this story? ITVedas has beginner-friendly guides on every IT topic.</p>
    <a href="/#chapters" class="btn">Explore IT Chapters →</a>
  </div>
</div>
<footer>
  <div class="fl">IT<span>Vedas</span></div>
  <p>Original IT news and guides — explained simply, for everyone.</p>
  <div class="flinks">
    <a href="/">Home</a><a href="/news.html">News</a>
    <a href="/#chapters">Chapters</a><a href="mailto:info@itvedas.com">Contact</a>
  </div>
  <p style="margin-top:1rem;">© {datetime.date.today().year} ITVedas</p>
</footer>
</body>
</html>"""

def build_news_index(articles, update_time):
    today = datetime.date.today().strftime("%B %d, %Y")
    by_topic = {}
    for a in articles:
        by_topic.setdefault(a['topic'], []).append(a)

    filter_btns = '<button onclick="f(\'all\')" class="fb active" data-t="all">All</button>'
    for t in by_topic:
        c = TOPIC_COLORS.get(t,"#64748B")
        filter_btns += f'<button onclick="f(\'{t}\')" class="fb" data-t="{t}" style="--tc:{c}">{t}</button>'

    cards = ""
    for a in articles:
        c = TOPIC_COLORS.get(a['topic'],"#64748B")
        emoji = TOPIC_EMOJI.get(a['topic'],"📰")
        cards += f"""<a href="/news/{a['slug']}.html" class="nc" data-t="{a['topic']}">
          <div class="nc-vis" style="background:linear-gradient(135deg,{c}22,{c}08);"><span style="font-size:2.5rem;">{emoji}</span></div>
          <div class="nc-body">
            <div class="nc-top"><span class="nc-badge" style="background:{c}1f;color:{c};">{a['topic']}</span><span class="nc-time">{a['date']}{(' · ' + a['time']) if a.get('time') else ''}</span></div>
            <h3 class="nc-title">{a['headline']}</h3>
            <p class="nc-sum">{a['summary']}</p>
            <span class="nc-link">Read full story →</span>
          </div>
        </a>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="description" content="Original IT and cybersecurity news explained in plain English — written by ITVedas, updated throughout the day.">
<meta name="keywords" content="IT news, cybersecurity news, tech news today, cloud news, DevOps news">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{SITE}/news.html">
<title>IT News Today — {today} | ITVedas</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{--bg:#0A0A0F;--bg2:#13131C;--bg3:#1C1C2A;--text:#F0F0F8;--muted:#8888A8;--sub:#D0D0E8;--accent:#FF6B35;--border:rgba(255,255,255,0.08);}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
html{{scroll-behavior:smooth;}}
body{{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;-webkit-font-smoothing:antialiased;}}
nav{{position:fixed;top:0;left:0;right:0;z-index:100;display:flex;align-items:center;justify-content:space-between;padding:0 2rem;height:64px;background:rgba(10,10,15,0.92);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);}}
.logo{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.3rem;color:var(--text);text-decoration:none;}}
.logo span{{color:var(--accent);}}
.nav-links{{display:flex;gap:1.5rem;}}
.nav-links a{{color:var(--muted);text-decoration:none;font-size:0.875rem;transition:color 0.2s;}}
.nav-links a:hover,.nav-links a.active{{color:var(--text);}}
.hero{{padding:6rem 2rem 2.5rem;background:linear-gradient(180deg,rgba(255,107,53,0.05),transparent);border-bottom:1px solid var(--border);}}
.hero-in{{max-width:1200px;margin:0 auto;}}
.live{{display:inline-flex;align-items:center;gap:0.5rem;background:rgba(16,185,129,0.12);border:1px solid rgba(16,185,129,0.3);color:#10B981;padding:0.3rem 0.9rem;border-radius:100px;font-size:0.75rem;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:1.25rem;}}
.dot{{width:6px;height:6px;background:#10B981;border-radius:50%;animation:b 1.5s infinite;}}
@keyframes b{{0%,100%{{opacity:1}}50%{{opacity:0.3}}}}
.hero h1{{font-family:'Space Grotesk',sans-serif;font-size:clamp(2rem,4vw,3rem);font-weight:700;letter-spacing:-0.025em;margin-bottom:0.75rem;}}
.hero h1 span{{background:linear-gradient(135deg,#FF6B35,#8B5CF6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}}
.hero p{{color:var(--muted);max-width:560px;}}
.upd{{font-size:0.8rem;color:var(--muted);margin-top:0.75rem;}}
.main{{max-width:1200px;margin:0 auto;padding:2.5rem 2rem 5rem;}}
.filters{{display:flex;gap:0.5rem;flex-wrap:wrap;margin-bottom:2rem;}}
.fb{{background:var(--bg2);border:1px solid var(--border);color:var(--muted);padding:0.4rem 1rem;border-radius:100px;font-size:0.8rem;font-weight:600;cursor:pointer;transition:all 0.2s;font-family:'Inter',sans-serif;}}
.fb:hover{{color:var(--text);border-color:rgba(255,255,255,0.2);}}
.fb.active{{background:var(--accent);border-color:var(--accent);color:#fff;}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:1.5rem;}}
.nc{{background:var(--bg2);border:1px solid var(--border);border-radius:16px;overflow:hidden;text-decoration:none;color:inherit;transition:transform 0.2s,border-color 0.2s;display:flex;flex-direction:column;}}
.nc:hover{{transform:translateY(-4px);border-color:rgba(255,255,255,0.15);}}
.nc-vis{{height:140px;display:flex;align-items:center;justify-content:center;}}
.nc-body{{padding:1.35rem;}}
.nc-top{{display:flex;align-items:center;justify-content:space-between;margin-bottom:0.75rem;}}
.nc-badge{{font-size:0.68rem;font-weight:700;padding:0.25rem 0.65rem;border-radius:4px;text-transform:uppercase;letter-spacing:0.05em;}}
.nc-time{{font-size:0.75rem;color:var(--muted);}}
.nc-title{{font-family:'Space Grotesk',sans-serif;font-size:1.05rem;font-weight:600;line-height:1.4;margin-bottom:0.6rem;color:var(--text);}}
.nc-sum{{font-size:0.875rem;color:var(--muted);line-height:1.55;margin-bottom:1rem;}}
.nc-link{{font-size:0.8rem;color:var(--accent);font-weight:600;}}
.empty{{text-align:center;padding:3rem;color:var(--muted);}}
footer{{border-top:1px solid var(--border);padding:2.5rem 2rem;text-align:center;color:var(--muted);font-size:0.875rem;}}
.fl{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.1rem;color:var(--text);margin-bottom:0.5rem;}}
.fl span{{color:var(--accent);}}
.flinks{{display:flex;gap:1.5rem;justify-content:center;margin-top:0.75rem;flex-wrap:wrap;}}
.flinks a{{color:var(--muted);text-decoration:none;}}
.flinks a:hover{{color:var(--accent);}}
@media(max-width:768px){{nav{{padding:0 1.25rem;}}.nav-links{{display:none;}}.hero,.main{{padding-left:1.25rem;padding-right:1.25rem;}}.grid{{grid-template-columns:1fr;}}}}
</style>
</head>
<body>
<nav>
  <a href="/" class="logo">IT<span>Vedas</span></a>
  <div class="nav-links"><a href="/">Home</a><a href="/news.html" class="active">News</a><a href="/#chapters">Chapters</a><a href="mailto:info@itvedas.com">Contact</a></div>
</nav>
<div class="hero">
  <div class="hero-in">
    <div class="live"><span class="dot"></span>Live updates</div>
    <h1>IT & Cybersecurity <span>News Today</span></h1>
    <p>Original reporting on the latest tech, security and cloud news — written by ITVedas in plain English. Updated throughout the day.</p>
    <p class="upd">Last updated: {update_time} · {today}</p>
  </div>
</div>
<div class="main">
  <div class="filters">{filter_btns}</div>
  <div class="grid" id="grid">{cards}</div>
  <div class="empty" id="empty" style="display:none;">No stories in this category yet. Check back soon.</div>
</div>
<footer>
  <div class="fl">IT<span>Vedas</span></div>
  <p>Original IT news and guides — explained simply, for everyone.</p>
  <div class="flinks"><a href="/">Home</a><a href="/#chapters">Chapters</a><a href="mailto:info@itvedas.com">Contact</a><a href="/sitemap.xml">Sitemap</a></div>
  <p style="margin-top:1rem;">© {datetime.date.today().year} ITVedas · Original reporting</p>
</footer>
<script>
function f(t){{
  document.querySelectorAll('.fb').forEach(b=>b.classList.remove('active'));
  document.querySelector(`[data-t="${{t}}"]`).classList.add('active');
  let v=0;
  document.querySelectorAll('.nc').forEach(c=>{{
    const s=t==='all'||c.dataset.t===t;c.style.display=s?'':'none';if(s)v++;
  }});
  document.getElementById('empty').style.display=v===0?'block':'none';
}}
</script>
</body>
</html>"""

def slugify(text):
    s = re.sub(r'[^a-z0-9]+','-',text.lower()).strip('-')
    return s[:60]

def main():
    print("News Agent v2 — original commentary mode")
    pathlib.Path("news").mkdir(exist_ok=True)
    pathlib.Path("brain").mkdir(exist_ok=True)

    now = datetime.datetime.now()
    update_time = now.strftime("%I:%M %p IST")
    today = datetime.date.today().isoformat()

    # Load existing news state
    news_state_f = pathlib.Path("brain/news_state.json")
    published = []
    if news_state_f.exists():
        try:
            published = json.loads(news_state_f.read_text())
        except Exception as e:
            print(f"news_state.json corrupt, resetting: {e}")
            published = []

    # Fetch headlines
    raw = []
    for feed in NEWS_FEEDS:
        raw.extend(fetch_feed(feed))
        print(f"Fetched from {feed.split('/')[2]}")

    # Dedupe
    seen = set((p.get('orig_title') or p.get('headline', ''))[:50].lower() for p in published)
    new_items = []
    for item in raw:
        key = item['title'][:50].lower()
        if key not in seen:
            seen.add(key)
            new_items.append(item)

    # Write original articles for up to 4 fresh stories per run
    written = 0
    for item in new_items[:4]:
        print(f"Writing original article: {item['title'][:50]}...")
        content = write_original_article(item)
        meta, body = parse_article(content, item)
        slug = f"{today}-{slugify(meta['headline'])}"
        if any(p['slug']==slug for p in published):
            slug += "-" + hashlib.md5(item['title'].encode()).hexdigest()[:4]
        page = build_article_page(meta, body, item, today, slug, update_time)
        (pathlib.Path("news")/f"{slug}.html").write_text(page, encoding="utf-8")
        published.insert(0, {
            "slug": slug, "headline": meta['headline'],
            "summary": meta['summary'], "topic": meta['topic'],
            "date": today, "time": update_time, "orig_title": item['title']
        })
        written += 1
        print(f"  → news/{slug}.html")

    published = published[:40]  # keep last 40
    tmp = news_state_f.with_suffix(".tmp")
    tmp.write_text(json.dumps(published, indent=2))
    tmp.replace(news_state_f)

    # Build index page
    index = build_news_index(published, update_time)
    news_html = pathlib.Path("news.html")
    tmp2 = news_html.with_suffix(".tmp")
    tmp2.write_text(index, encoding="utf-8")
    tmp2.replace(news_html)
    print(f"Done. Wrote {written} new articles. Index has {len(published)} stories.")

if __name__ == "__main__":
    main()
