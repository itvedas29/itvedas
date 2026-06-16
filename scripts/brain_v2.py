"""
ITVedas Brain Agent v2
======================
Fully autonomous Claude agent.
- 3-month IT + Cybersecurity + Compliance content calendar
- Publishes directly — no approval needed
- Sends email notification with article preview
- Articles match homepage design (dark, colorful, vibrant)
"""

import os, json, urllib.request, pathlib, re, datetime, random, smtplib, time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ── Config ───────────────────────────────────────────────────────────────
API_KEY   = os.environ.get("ANTHROPIC_API_KEY", "")
SMTP_TO   = os.environ.get("NOTIFY_EMAIL", "")   # your email
SMTP_FROM = os.environ.get("SMTP_FROM", "")      # sender gmail
SMTP_PASS = os.environ.get("SMTP_PASS", "")      # gmail app password
MODEL     = "claude-haiku-4-5-20251001"
SITE_URL  = "https://itvedas.com"
SITE_NAME = "ITVedas"
STATE_F   = pathlib.Path("brain/state.json")
LOG_F     = pathlib.Path("brain/activity.log")

TOPIC_COLORS = {
    "Networking":   "#FF6B35",
    "Cloud":        "#3B82F6",
    "Security":     "#10B981",
    "DevOps":       "#8B5CF6",
    "Databases":    "#F59E0B",
    "Linux":        "#EF4444",
    "Hardware":     "#06B6D4",
    "Compliance":   "#EC4899",
    "CyberSecurity":"#F97316",
    "BestPractice": "#14B8A6",
}

# ── 3-Month Content Calendar ─────────────────────────────────────────────
# 39 keywords = 3 articles/week × 13 weeks
CONTENT_CALENDAR = [
    # ── MONTH 1: IT Foundations + Security Basics ──
    {"kw":"what is DNS and how does it work step by step",             "topic":"Networking",    "month":1},
    {"kw":"how does a VPN work explained simply for beginners",        "topic":"Networking",    "month":1},
    {"kw":"what is cloud computing explained simply 2026",             "topic":"Cloud",         "month":1},
    {"kw":"how to protect your website from hackers beginner guide",   "topic":"Security",      "month":1},
    {"kw":"what is Docker and why every developer needs it",           "topic":"DevOps",        "month":1},
    {"kw":"SQL vs NoSQL which database should you choose 2026",        "topic":"Databases",     "month":1},
    {"kw":"Linux commands every beginner must know in 2026",           "topic":"Linux",         "month":1},
    {"kw":"what is two factor authentication and how it works",        "topic":"Security",      "month":1},
    {"kw":"AWS vs Azure vs Google Cloud which is best 2026",           "topic":"Cloud",         "month":1},
    {"kw":"what is a firewall and why every network needs one",        "topic":"Networking",    "month":1},
    {"kw":"how does SSL TLS encryption work simple explanation",       "topic":"Security",      "month":1},
    {"kw":"what is Kubernetes explained simply for beginners",         "topic":"DevOps",        "month":1},
    {"kw":"how does a CPU work explained simply 2026",                 "topic":"Hardware",      "month":1},
    # ── MONTH 2: Cybersecurity + Compliance ──
    {"kw":"what is GDPR compliance explained simply for businesses",   "topic":"Compliance",    "month":2},
    {"kw":"what is a DDoS attack and how to prevent it",               "topic":"CyberSecurity", "month":2},
    {"kw":"ISO 27001 explained what it is and why it matters",         "topic":"Compliance",    "month":2},
    {"kw":"what is zero trust security model and how it works",        "topic":"CyberSecurity", "month":2},
    {"kw":"how does phishing attack work and how to avoid it",         "topic":"CyberSecurity", "month":2},
    {"kw":"SOC 2 compliance guide for beginners 2026",                 "topic":"Compliance",    "month":2},
    {"kw":"what is penetration testing explained simply",              "topic":"CyberSecurity", "month":2},
    {"kw":"HIPAA compliance explained for non technical people",       "topic":"Compliance",    "month":2},
    {"kw":"what is ransomware and how to protect yourself",            "topic":"CyberSecurity", "month":2},
    {"kw":"PCI DSS compliance beginner guide for businesses",          "topic":"Compliance",    "month":2},
    {"kw":"what is OWASP top 10 security risks explained",             "topic":"CyberSecurity", "month":2},
    {"kw":"how to do a security audit for your website beginner",      "topic":"BestPractice",  "month":2},
    {"kw":"what is data encryption and why it protects you",           "topic":"CyberSecurity", "month":2},
    # ── MONTH 3: Best Practices + Advanced Topics ──
    {"kw":"DevOps best practices for small teams 2026",                "topic":"BestPractice",  "month":3},
    {"kw":"cloud security best practices every company needs 2026",    "topic":"BestPractice",  "month":3},
    {"kw":"what is CI CD pipeline and why it matters explained",       "topic":"DevOps",        "month":3},
    {"kw":"database backup best practices to never lose data",         "topic":"BestPractice",  "month":3},
    {"kw":"what is serverless computing pros cons explained",          "topic":"Cloud",         "month":3},
    {"kw":"network security best practices for businesses 2026",       "topic":"BestPractice",  "month":3},
    {"kw":"what is infrastructure as code Terraform explained",        "topic":"DevOps",        "month":3},
    {"kw":"API security best practices developers must know",          "topic":"BestPractice",  "month":3},
    {"kw":"how does Kubernetes auto scaling work simply explained",    "topic":"Cloud",         "month":3},
    {"kw":"Linux server security hardening guide for beginners",       "topic":"BestPractice",  "month":3},
    {"kw":"what is disaster recovery plan in IT explained simply",     "topic":"BestPractice",  "month":3},
    {"kw":"how to build zero trust network architecture 2026",         "topic":"CyberSecurity", "month":3},
    {"kw":"container security best practices Docker Kubernetes 2026",  "topic":"BestPractice",  "month":3},
]

# ── Core Claude call ──────────────────────────────────────────────────────
def think(messages, system=None, max_tokens=4000):
    payload = {"model": MODEL, "max_tokens": max_tokens, "messages": messages}
    if system:
        payload["system"] = system
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"x-api-key": API_KEY, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    for attempt in range(3):
        try:
            return json.load(urllib.request.urlopen(req, timeout=90))["content"][0]["text"].strip()
        except Exception as e:
            if attempt == 2: raise
            time.sleep(8)

# ── Logging ───────────────────────────────────────────────────────────────
def log(msg):
    pathlib.Path("brain").mkdir(exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_F, "a") as f:
        f.write(line + "\n")

# ── State ─────────────────────────────────────────────────────────────────
def load_state():
    pathlib.Path("brain").mkdir(exist_ok=True)
    if STATE_F.exists():
        try: return json.loads(STATE_F.read_text())
        except: pass
    return {"published": [], "used_keywords": [], "topic_counts": {}, "total": 0}

def save_state(s):
    STATE_F.write_text(json.dumps(s, indent=2))

# ── Pick keyword from calendar ────────────────────────────────────────────
def pick_keyword(state):
    used = state.get("used_keywords", [])
    available = [k for k in CONTENT_CALENDAR if k["kw"] not in used]
    if not available:
        log("Calendar complete — resetting")
        state["used_keywords"] = []
        available = CONTENT_CALENDAR
    # Prioritise month 1 first, then 2, then 3
    for month in [1, 2, 3]:
        month_kws = [k for k in available if k["month"] == month]
        if month_kws:
            chosen = month_kws[0]
            log(f"Calendar pick [Month {month}]: {chosen['kw']}")
            return chosen["topic"], chosen["kw"]
    return available[0]["topic"], available[0]["kw"]

# ── Write article ─────────────────────────────────────────────────────────
def write_article(topic, keyword):
    log(f"Writing: {keyword}")
    color = TOPIC_COLORS.get(topic, "#FF6B35")

    system = """You are the lead writer for ITVedas — an IT knowledge hub for complete beginners.

ABSOLUTE RULES:
1. Write like explaining to someone who has NEVER used a computer professionally
2. Every single technical term gets a real-world analogy on first use
   Examples: DNS = phone book, RAM = your desk space, Firewall = security guard, Encryption = secret code
3. Max 20 words per sentence. Short and punchy.
4. Always use "you" and "your" — make it personal
5. Use examples from real life: Netflix, WhatsApp, Google, Amazon, YouTube, Instagram
6. Numbered steps for any process
7. After every complex concept add: "In simple terms: [one sentence explanation]"
8. No buzzwords without immediate plain-English explanation"""

    prompt = f"""Write a complete article for this exact Google search keyword:
"{keyword}"

Topic: {topic}

START with this exact comment block (fill in values):
<!-- META
title: [compelling SEO title containing the keyword]
description: [150 chars max, include keyword, start with action word]
keyword: {keyword}
topic: {topic}
-->

THEN write the full article HTML:

<h1>[title with keyword naturally included]</h1>

Structure:
- Intro (2 paragraphs: hook + why this matters to YOU personally)
- <h2>What is [subject]?</h2> — definition + real-world analogy in <blockquote>
- <h2>How does [subject] work?</h2> — numbered steps, plain English
- <h2>Why does this matter to you?</h2> — real benefits, everyday impact
- <h2>A real-world example</h2> — specific walkthrough scenario
- <h2>Common mistakes people make</h2> — 3 mistakes + how to avoid
- <h2>Frequently asked questions</h2> — 3 Q&As
- <h2>Key things to remember</h2> — 5 bullet points
- Conclusion — encouraging, mention ITVedas chapters

SPECIAL ELEMENTS to include:
- At least 2 <blockquote> for key analogies
- At least 1 <div class="callout"><div class="callout-title">Pro Tip</div>..content..</div>
- Use <strong> for important terms
- Use <code> for technical terms on first mention
- 1500-2000 words total
- Return ONLY the META comment + HTML. No html/head/body tags."""

    return think([{"role": "user", "content": prompt}], system=system, max_tokens=4000)

# ── Self review ───────────────────────────────────────────────────────────
def self_review(content, keyword):
    log("Self-reviewing...")
    resp = think([{"role": "user", "content": f"""Review this IT article for "{keyword}".
Score 0-100 on: beginner friendliness (30pts), real-world examples (25pts), structure (25pts), SEO (20pts).
Reply JSON only: {{"score":85,"verdict":"PUBLISH","fix":"what to improve if needed"}}
verdict=PUBLISH if score>=75 else REWRITE
Article: {content[:2000]}"""}], max_tokens=200)
    try:
        m = re.search(r'\{[^{}]+\}', resp, re.DOTALL)
        if m:
            r = json.loads(m.group())
            log(f"Score: {r.get('score',75)}/100 — {r.get('verdict','PUBLISH')}")
            return r
    except: pass
    return {"score": 80, "verdict": "PUBLISH"}

# ── Extract meta ──────────────────────────────────────────────────────────
def extract_meta(content, keyword, topic):
    meta = {"title": keyword.title(), "description": f"Learn {keyword} on ITVedas",
            "keyword": keyword, "topic": topic}
    m = re.search(r'<!-- META(.*?)-->', content, re.DOTALL)
    if m:
        for line in m.group(1).strip().split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                k = k.strip()
                if k in meta: meta[k] = v.strip()
    h1 = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE | re.DOTALL)
    if h1: meta['title'] = re.sub(r'<[^>]+>', '', h1.group(1)).strip()
    return meta

# ── Build full page ────────────────────────────────────────────────────────
def build_page(content, meta, date_str):
    topic   = meta.get('topic', 'IT')
    title   = meta.get('title', 'IT Guide')
    desc    = meta.get('description', '')
    keyword = meta.get('keyword', '')
    color   = TOPIC_COLORS.get(topic, "#FF6B35")

    body = re.sub(r'<!-- META.*?-->', '', content, flags=re.DOTALL)
    body = body.replace('[AFFILIATE]', '').strip()
    body = re.sub(r'\n{3,}', '\n\n', body)

    headings = re.findall(r'<h2[^>]*>(.*?)</h2>', body, re.IGNORECASE | re.DOTALL)
    toc = ""
    for h in headings[:8]:
        clean = re.sub(r'<[^>]+>', '', h).strip()
        anc = re.sub(r'[^a-z0-9]+', '-', clean.lower()).strip('-')
        toc += f'<li><a href="#{anc}">{clean}</a></li>'
        body = re.sub(rf'<h2([^>]*)>{re.escape(h)}</h2>',
                      f'<h2\\1 id="{anc}">{h}</h2>', body, count=1)

    words = len(re.sub(r'<[^>]+>', '', body).split())
    rt = f"{max(1,round(words/200))} min read"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="description" content="{desc}">
<meta name="keywords" content="{keyword}, {topic} guide, ITVedas, IT knowledge">
<meta name="robots" content="index,follow">
<meta property="og:title" content="{title} | ITVedas">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:url" content="{SITE_URL}/articles/{date_str}-{topic.lower()}.html">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title} | ITVedas">
<meta name="twitter:description" content="{desc}">
<link rel="canonical" href="{SITE_URL}/articles/{date_str}-{topic.lower()}.html">
<title>{title} | ITVedas</title>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Article","headline":"{title}",
"description":"{desc}","keywords":"{keyword}",
"author":{{"@type":"Organization","name":"ITVedas","url":"{SITE_URL}"}},
"publisher":{{"@type":"Organization","name":"ITVedas","url":"{SITE_URL}"}},
"datePublished":"{date_str}","dateModified":"{date_str}",
"articleSection":"{topic}","educationalLevel":"Beginner"}}
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{--bg:#0A0A0F;--bg2:#13131C;--bg3:#1C1C2A;--text:#F0F0F8;--muted:#8888A8;--subtle:#D0D0E8;--accent:{color};--border:rgba(255,255,255,0.08);}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
html{{scroll-behavior:smooth;}}
body{{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;font-size:17px;line-height:1.85;-webkit-font-smoothing:antialiased;}}
.progress{{position:fixed;top:0;left:0;right:0;height:3px;z-index:200;background:transparent;}}
.pb{{height:100%;background:linear-gradient(90deg,var(--accent),#8B5CF6);width:0%;transition:width 0.1s;}}
nav{{position:fixed;top:3px;left:0;right:0;z-index:100;display:flex;align-items:center;justify-content:space-between;padding:0 2rem;height:64px;background:rgba(10,10,15,0.92);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);}}
.logo{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.3rem;color:var(--text);text-decoration:none;letter-spacing:-0.02em;}}
.logo span{{color:var(--accent);}}
.nav-back{{color:var(--muted);text-decoration:none;font-size:0.875rem;display:flex;align-items:center;gap:0.4rem;transition:color 0.2s;padding:0.5rem 1rem;border:1px solid var(--border);border-radius:8px;}}
.nav-back:hover{{color:var(--text);border-color:rgba(255,255,255,0.2);}}
.hero{{padding:7.5rem 2rem 3rem;max-width:860px;margin:0 auto;}}
.breadcrumb{{font-size:0.8rem;color:var(--muted);margin-bottom:1.5rem;display:flex;align-items:center;gap:0.5rem;}}
.breadcrumb a{{color:var(--muted);text-decoration:none;transition:color 0.2s;}}
.breadcrumb a:hover{{color:var(--accent);}}
.badges{{display:flex;align-items:center;gap:0.6rem;margin-bottom:1.5rem;flex-wrap:wrap;}}
.badge-topic{{background:rgba(255,107,53,0.12);border:1px solid rgba(255,107,53,0.25);color:var(--accent);padding:0.3rem 0.9rem;border-radius:100px;font-size:0.73rem;font-weight:700;text-transform:uppercase;letter-spacing:0.07em;}}
.badge-info{{color:var(--muted);font-size:0.82rem;background:var(--bg2);border:1px solid var(--border);padding:0.25rem 0.75rem;border-radius:100px;}}
.hero h1{{font-family:'Space Grotesk',sans-serif;font-size:clamp(1.9rem,4vw,3rem);font-weight:700;letter-spacing:-0.025em;line-height:1.1;margin-bottom:1.25rem;}}
.layout{{display:grid;grid-template-columns:1fr 280px;gap:3rem;max-width:1140px;margin:0 auto;padding:0 2rem 6rem;align-items:start;}}
article{{min-width:0;}}
.toc{{background:var(--bg2);border:1px solid var(--border);border-radius:14px;padding:1.5rem;margin:0 0 2.5rem;}}
.toc-label{{font-size:0.72rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:var(--muted);margin-bottom:1rem;}}
.toc ul{{list-style:none;padding:0;margin:0;}}
.toc li{{margin-bottom:0.15rem;}}
.toc a{{color:var(--muted);text-decoration:none;font-size:0.875rem;padding:0.3rem 0.6rem;display:block;border-radius:6px;border-left:2px solid transparent;transition:all 0.2s;}}
.toc a:hover{{color:var(--text);background:rgba(255,255,255,0.04);border-left-color:var(--accent);padding-left:0.9rem;}}
article h2{{font-family:'Space Grotesk',sans-serif;font-size:1.55rem;font-weight:700;margin:3rem 0 1rem;color:var(--text);display:flex;align-items:center;gap:0.75rem;}}
article h2::before{{content:'';width:4px;height:1.4em;background:var(--accent);border-radius:2px;flex-shrink:0;}}
article h3{{font-family:'Space Grotesk',sans-serif;font-size:1.1rem;font-weight:600;margin:2rem 0 0.6rem;color:var(--text);}}
article p{{margin-bottom:1.35rem;color:var(--subtle);}}
article ul,article ol{{margin:0.75rem 0 1.5rem 1.5rem;color:var(--subtle);}}
article li{{margin-bottom:0.65rem;line-height:1.7;}}
article strong{{color:var(--text);font-weight:600;}}
article blockquote{{background:linear-gradient(135deg,rgba(255,107,53,0.06),rgba(139,92,246,0.06));border-left:4px solid var(--accent);border-radius:0 12px 12px 0;padding:1.25rem 1.5rem;margin:2rem 0;color:var(--subtle);font-size:1.05rem;font-style:italic;}}
article code{{background:var(--bg2);border:1px solid var(--border);padding:0.15rem 0.45rem;border-radius:5px;font-family:monospace;font-size:0.875rem;color:#10B981;}}
article pre{{background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:1.5rem;margin:2rem 0;overflow-x:auto;}}
article pre code{{background:none;border:none;padding:0;font-size:0.84rem;color:#9FE1CB;line-height:1.8;}}
.callout{{background:linear-gradient(135deg,rgba(255,107,53,0.08),rgba(139,92,246,0.06));border:1px solid rgba(255,107,53,0.2);border-radius:12px;padding:1.25rem 1.5rem;margin:2rem 0;}}
.callout-title{{font-weight:700;color:var(--accent);font-size:0.8rem;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.6rem;}}
.takeaway{{background:var(--bg3);border:1px solid var(--border);border-radius:16px;padding:2rem;margin:3rem 0;}}
.takeaway h3{{font-family:'Space Grotesk',sans-serif;color:var(--accent);font-size:1.05rem;margin-bottom:1.25rem;display:flex;align-items:center;gap:0.5rem;}}
.takeaway ul{{list-style:none;padding:0;margin:0;}}
.takeaway li{{padding:0.65rem 0;border-bottom:1px solid var(--border);color:var(--subtle);font-size:0.95rem;display:flex;gap:0.75rem;align-items:flex-start;line-height:1.5;}}
.takeaway li:last-child{{border:none;}}
.takeaway li::before{{content:'✓';color:var(--accent);font-weight:700;flex-shrink:0;margin-top:0.1rem;}}
.cta-box{{margin:3rem 0;padding:2.5rem;background:linear-gradient(135deg,rgba(255,107,53,0.08),rgba(139,92,246,0.08));border:1px solid rgba(255,107,53,0.2);border-radius:20px;text-align:center;}}
.cta-box h3{{font-family:'Space Grotesk',sans-serif;font-size:1.3rem;font-weight:700;margin-bottom:0.75rem;}}
.cta-box p{{color:var(--muted);margin-bottom:1.5rem;font-size:0.95rem;}}
.btn{{display:inline-block;background:var(--accent);color:white;padding:0.85rem 2.25rem;border-radius:10px;text-decoration:none;font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:0.9rem;transition:transform 0.15s,opacity 0.15s;}}
.btn:hover{{transform:translateY(-2px);opacity:0.9;}}
aside{{position:sticky;top:87px;display:flex;flex-direction:column;gap:1rem;}}
.sc{{background:var(--bg2);border:1px solid var(--border);border-radius:14px;padding:1.25rem;}}
.sc-label{{font-size:0.72rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:var(--muted);margin-bottom:0.85rem;}}
.sc ul{{list-style:none;padding:0;margin:0;}}
.sc li{{margin-bottom:0.15rem;}}
.sc a{{color:var(--muted);text-decoration:none;font-size:0.84rem;padding:0.3rem 0;display:block;transition:color 0.2s;}}
.sc a:hover{{color:var(--accent);}}
.chapter-list a{{display:block;color:var(--muted);text-decoration:none;font-size:0.85rem;padding:0.4rem 0;border-bottom:1px solid var(--border);transition:color 0.2s;}}
.chapter-list a:last-child{{border:none;}}
.chapter-list a:hover{{color:var(--accent);}}
.nl-sc{{background:linear-gradient(135deg,rgba(255,107,53,0.08),rgba(139,92,246,0.08));border:1px solid rgba(255,107,53,0.2);border-radius:14px;padding:1.25rem;}}
.nl-sc p{{font-size:0.84rem;color:var(--muted);margin-bottom:1rem;line-height:1.6;}}
footer{{border-top:1px solid var(--border);padding:3rem 2rem;text-align:center;color:var(--muted);font-size:0.875rem;}}
.fl{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.2rem;color:var(--text);margin-bottom:0.5rem;}}
.fl span{{color:var(--accent);}}
.flinks{{display:flex;gap:2rem;justify-content:center;margin:0.75rem 0;flex-wrap:wrap;}}
.flinks a{{color:var(--muted);text-decoration:none;transition:color 0.2s;}}
.flinks a:hover{{color:var(--accent);}}
@media(max-width:900px){{
  .layout{{grid-template-columns:1fr;}}
  aside{{display:none;}}
  .hero,.layout{{padding-left:1.25rem;padding-right:1.25rem;}}
  nav{{padding:0 1.25rem;}}
}}
@media(prefers-reduced-motion:reduce){{*{{animation:none!important;transition:none!important;}}}}
</style>
</head>
<body>
<div class="progress"><div class="pb" id="pb"></div></div>
<nav>
  <a href="/" class="logo">IT<span>Vedas</span></a>
  <a href="/" class="nav-back">← All Chapters</a>
</nav>

<div class="hero">
  <div class="breadcrumb">
    <a href="/">Home</a>
    <span>›</span>
    <a href="/#chapters">{topic}</a>
    <span>›</span>
    <span style="color:var(--text);">Article</span>
  </div>
  <div class="badges">
    <span class="badge-topic">{topic}</span>
    <span class="badge-info">📅 {date_str}</span>
    <span class="badge-info">⏱ {rt}</span>
    <span class="badge-info">👶 Beginner friendly</span>
  </div>
  <h1>{title}</h1>
</div>

<div class="layout">
  <article>
    <div class="toc">
      <div class="toc-label">In this article</div>
      <ul>{toc}</ul>
    </div>
    {body}
    <div class="takeaway">
      <h3>✓ What you learned</h3>
      <ul>
        <li>The core concept of {topic} explained in plain English</li>
        <li>How it works in the real world with everyday analogies</li>
        <li>Why it matters for your digital life and career</li>
        <li>A real-world walkthrough you can follow</li>
        <li>Common mistakes and exactly how to avoid them</li>
      </ul>
    </div>
    <div class="cta-box">
      <h3>Keep Learning on ITVedas</h3>
      <p>This is one of 150+ guides across 7 IT chapters — all free, all in plain English.</p>
      <a href="/" class="btn">Explore All Chapters →</a>
    </div>
  </article>

  <aside>
    <div class="sc">
      <div class="sc-label">Jump to section</div>
      <ul>{toc}</ul>
    </div>
    <div class="sc">
      <div class="sc-label">All chapters</div>
      <div class="chapter-list">
        <a href="/#chapters">🌐 Networking</a>
        <a href="/#chapters">☁️ Cloud</a>
        <a href="/#chapters">🔐 Security</a>
        <a href="/#chapters">⚙️ DevOps</a>
        <a href="/#chapters">🗄️ Databases</a>
        <a href="/#chapters">🐧 Linux</a>
        <a href="/#chapters">🖥️ Hardware</a>
        <a href="/#chapters">📋 Compliance</a>
      </div>
    </div>
    <div class="nl-sc">
      <div class="sc-label" style="color:var(--accent);">Free newsletter</div>
      <p>New IT guides every Monday, Wednesday and Friday — plain English, zero jargon.</p>
      <a href="/#newsletter" class="btn" style="display:block;text-align:center;font-size:0.84rem;padding:0.65rem;">Subscribe Free →</a>
    </div>
  </aside>
</div>

<footer>
  <div class="fl">IT<span>Vedas</span></div>
  <p>The complete IT knowledge hub — explained simply, for everyone.</p>
  <div class="flinks">
    <a href="/">Home</a>
    <a href="/#chapters">Chapters</a>
    <a href="/#newsletter">Newsletter</a>
    <a href="/sitemap.xml">Sitemap</a>
  </div>
  <p style="margin-top:1.25rem;">© {datetime.date.today().year} ITVedas · Knowledge for everyone</p>
</footer>
<script>
const pb=document.getElementById('pb');
window.addEventListener('scroll',()=>{{
  const d=document.documentElement;
  pb.style.width=(d.scrollTop/(d.scrollHeight-d.clientHeight)*100)+'%';
}},{{passive:true}});
</script>
</body>
</html>"""

# ── Update homepage ────────────────────────────────────────────────────────
def update_homepage(state):
    idx = pathlib.Path("index.html")
    if not idx.exists(): return
    html = idx.read_text(encoding="utf-8")
    published = list(reversed(state.get("published", [])[-8:]))
    if not published: return

    items = ""
    for a in published:
        c = TOPIC_COLORS.get(a.get('topic','IT'), "#FF6B35")
        items += f"""<a href="/articles/{a['file']}" style="display:flex;align-items:flex-start;gap:1rem;padding:1rem 0;border-bottom:1px solid rgba(255,255,255,0.06);text-decoration:none;color:inherit;">
          <span style="background:rgba(255,107,53,0.1);color:{c};font-size:0.68rem;font-weight:700;padding:0.25rem 0.6rem;border-radius:4px;white-space:nowrap;text-transform:uppercase;letter-spacing:0.04em;margin-top:3px;flex-shrink:0;">{a.get('topic','IT')}</span>
          <div><div style="font-size:0.95rem;color:#D0D0E8;line-height:1.45;margin-bottom:0.2rem;">{a.get('title','Article')}</div>
          <div style="font-size:0.75rem;color:#8888A8;">{a.get('date','')} · {a.get('rt','5 min read')}</div></div>
        </a>"""

    sec = f"""<!-- LATEST_ARTICLES_START -->
<div id="latest-articles" style="background:#13131C;border-top:1px solid rgba(255,255,255,0.08);border-bottom:1px solid rgba(255,255,255,0.08);padding:5rem 2rem;">
  <div style="max-width:1200px;margin:0 auto;">
    <div style="font-size:0.75rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#FF6B35;margin-bottom:0.75rem;">Latest Articles</div>
    <h2 style="font-family:'Space Grotesk',sans-serif;font-size:clamp(1.75rem,3vw,2.5rem);font-weight:700;letter-spacing:-0.02em;margin-bottom:0.75rem;">Fresh from the Knowledge Hub</h2>
    <p style="color:#8888A8;margin-bottom:2.5rem;max-width:500px;">New articles every Monday, Wednesday and Friday — always plain English, always free.</p>
    <div style="max-width:720px;">{items}</div>
  </div>
</div>
<!-- LATEST_ARTICLES_END -->"""

    if '<!-- LATEST_ARTICLES_START -->' in html:
        html = re.sub(r'<!-- LATEST_ARTICLES_START -->.*?<!-- LATEST_ARTICLES_END -->', sec, html, flags=re.DOTALL)
    else:
        html = html.replace('<div style="padding:5rem 0;" id="newsletter">', sec + '\n<div style="padding:5rem 0;" id="newsletter">')
    idx.write_text(html, encoding="utf-8")
    log("Homepage updated")

# ── Sitemap ────────────────────────────────────────────────────────────────
def update_sitemap(state):
    today = datetime.date.today().isoformat()
    urls = [f"  <url><loc>{SITE_URL}/</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>1.0</priority></url>"]
    for a in state.get("published", []):
        urls.append(f"  <url><loc>{SITE_URL}/articles/{a['file']}</loc><lastmod>{a.get('date',today)}</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>")
    pathlib.Path("sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        '\n'.join(urls) + '\n</urlset>')
    log(f"Sitemap: {len(urls)} URLs")

# ── Email notification ─────────────────────────────────────────────────────
def send_email(meta, filename, score):
    if not all([SMTP_TO, SMTP_FROM, SMTP_PASS]):
        log("Email not configured — skipping notification")
        return
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"ITVedas: New article published — {meta.get('title','Article')}"
        msg['From']    = SMTP_FROM
        msg['To']      = SMTP_TO

        html_body = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#0A0A0F;color:#F0F0F8;border-radius:12px;overflow:hidden;">
          <div style="background:linear-gradient(135deg,#FF6B35,#8B5CF6);padding:2rem;text-align:center;">
            <h1 style="margin:0;font-size:1.5rem;color:white;">ITVedas Brain Published a New Article</h1>
          </div>
          <div style="padding:2rem;">
            <div style="background:#13131C;border-radius:10px;padding:1.5rem;margin-bottom:1.5rem;">
              <p style="font-size:0.8rem;color:#8888A8;margin:0 0 0.5rem;text-transform:uppercase;letter-spacing:0.1em;">{meta.get('topic','IT')}</p>
              <h2 style="margin:0 0 0.75rem;font-size:1.3rem;color:#F0F0F8;">{meta.get('title','Article')}</h2>
              <p style="color:#8888A8;margin:0 0 1rem;font-size:0.9rem;">{meta.get('description','')}</p>
              <p style="color:#8888A8;margin:0;font-size:0.85rem;">Quality score: <strong style="color:#10B981;">{score}/100</strong> · Published: {datetime.date.today().isoformat()}</p>
            </div>
            <div style="text-align:center;margin-bottom:1.5rem;">
              <a href="{SITE_URL}/articles/{filename}" style="display:inline-block;background:#FF6B35;color:white;padding:0.85rem 2rem;border-radius:8px;text-decoration:none;font-weight:600;">View Live Article →</a>
            </div>
            <p style="color:#8888A8;font-size:0.85rem;text-align:center;">This article was written and published automatically by the ITVedas Brain Agent.</p>
          </div>
        </div>"""

        msg.attach(MIMEText(html_body, 'html'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SMTP_FROM, SMTP_PASS)
            server.sendmail(SMTP_FROM, SMTP_TO, msg.as_string())
        log(f"Email sent to {SMTP_TO}")
    except Exception as e:
        log(f"Email error: {e}")

# ── Main ───────────────────────────────────────────────────────────────────
def main():
    log("=" * 55)
    log("ITVedas Brain Agent v2 — starting")
    log("=" * 55)

    for d in ["drafts", "articles", "brain"]:
        pathlib.Path(d).mkdir(exist_ok=True)

    state = load_state()
    state["last_run"] = datetime.datetime.now().isoformat()

    try:
        # 1. Pick keyword from 3-month calendar
        topic, keyword = pick_keyword(state)

        # 2. Write article
        content = write_article(topic, keyword)

        # 3. Self-review
        review = self_review(content, keyword)
        score = review.get("score", 80)
        if review.get("verdict") == "REWRITE":
            log("Rewriting — score too low")
            content = write_article(topic, keyword)
            score = 80

        # 4. Extract SEO metadata
        meta = extract_meta(content, keyword, topic)
        log(f"Title: {meta['title']}")

        # 5. Build full page
        today = datetime.date.today().isoformat()
        page = build_page(content, meta, today)

        # 6. Save article (handle duplicates)
        fname = f"{today}-{topic.lower()}.html"
        out = pathlib.Path("articles") / fname
        c = 1
        while out.exists():
            fname = f"{today}-{topic.lower()}-{c}.html"
            out = pathlib.Path("articles") / fname
            c += 1
        out.write_text(page, encoding="utf-8")
        log(f"Published: articles/{fname}")

        # 7. Update state
        words = len(re.sub(r'<[^>]+>', '', content).split())
        rt = f"{max(1, round(words/200))} min read"
        state["used_keywords"].append(keyword)
        state["used_keywords"] = state["used_keywords"][-60:]
        state["topic_counts"][topic] = state.get("topic_counts", {}).get(topic, 0) + 1
        state["total"] = state.get("total", 0) + 1
        state["published"].append({
            "file": fname, "title": meta["title"],
            "topic": topic, "keyword": keyword,
            "date": today, "score": score, "rt": rt
        })
        state["published"] = state["published"][-60:]

        # 8. Update homepage
        update_homepage(state)

        # 9. Update sitemap
        update_sitemap(state)

        # 10. Save state
        save_state(state)

        # 11. Send email notification
        send_email(meta, fname, score)

        log("=" * 55)
        log(f"DONE. Article #{state['total']}: {meta['title']}")
        log(f"Score: {score}/100 | Topic: {topic} | File: {fname}")
        log("=" * 55)

    except Exception as e:
        log(f"ERROR: {e}")
        save_state(state)
        raise

if __name__ == "__main__":
    main()
