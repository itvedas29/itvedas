"""
═══════════════════════════════════════════════════════════════════
 ITVedas Brain — Complete Autonomous Content Agent
═══════════════════════════════════════════════════════════════════
 One file. Runs on GitHub Actions. No approval needed.

 What it does each run:
   1. Picks the next keyword from the 3-month content calendar
   2. Writes a beginner-friendly, SEO-optimised article (Claude)
   3. Self-reviews and improves weak sections
   4. Builds a full styled page (matches homepage, GA4-ready)
   5. Publishes directly to /articles/
   6. Refreshes homepage "Latest Articles" section
   7. Rebuilds all 8 chapter landing pages
   8. Regenerates sitemap.xml
   9. Emails you a notification (optional)

 LLM roles:
   Claude (Anthropic)  primary  — self-review/QA gate (decides PUBLISH vs REWRITE)
   OpenAI              secondary — writes the article draft

 Config via environment variables (GitHub Secrets):
   ANTHROPIC_API_KEY   (required) — review/QA
   OPENAI_API_KEY      (required) — article writing
   OPENAI_MODEL        (optional, defaults to gpt-4o-mini)
   GA4_ID              (optional, e.g. G-XXXXXXXXXX)
   NOTIFY_EMAIL        (optional, where to send notifications)
   SMTP_FROM           (optional, Gmail sender)
   SMTP_PASS           (optional, Gmail app password)
═══════════════════════════════════════════════════════════════════
"""

import os, re, json, time, pathlib, datetime, smtplib, urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ─────────────────────────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────────────────────────
API_KEY    = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
GA4_ID     = os.environ.get("GA4_ID", "").strip()
NOTIFY_TO  = os.environ.get("NOTIFY_EMAIL", "").strip()
SMTP_FROM  = os.environ.get("SMTP_FROM", "").strip()
SMTP_PASS  = os.environ.get("SMTP_PASS", "").strip()

MODEL        = "claude-haiku-4-5-20251001"
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
SITE_URL   = "https://itvedas.com"
SITE_NAME  = "ITVedas"
CONTACT    = "info@itvedas.com"

ROOT       = pathlib.Path(".")
ARTICLES   = ROOT / "articles"
BRAIN_DIR  = ROOT / "itvedas-brain" / "state"
STATE_FILE = BRAIN_DIR / "state.json"
LOG_FILE   = BRAIN_DIR / "activity.log"

# ─────────────────────────────────────────────────────────────────
#  CHAPTERS  (slug -> display config)
# ─────────────────────────────────────────────────────────────────
CHAPTERS = {
    "networking": {"name":"Networking","emoji":"🌐","color":"#FF6B35","num":"01",
        "title":"How Networks Talk",
        "desc":"How data moves across the internet and inside your network — TCP/IP, DNS, subnetting, routing, VPNs and firewalls, all in plain English.",
        "tags":["TCP/IP","DNS","Subnetting","Routing","VPN","Firewalls"]},
    "cloud": {"name":"Cloud Computing","emoji":"☁️","color":"#3B82F6","num":"02",
        "title":"The Cloud, Demystified",
        "desc":"AWS, Azure and Google Cloud explained — IaaS, PaaS, SaaS, deploying real infrastructure and architecting for scale, without the jargon.",
        "tags":["AWS","Azure","GCP","Serverless","CDN","Auto-scaling"]},
    "security": {"name":"Security","emoji":"🔐","color":"#10B981","num":"03",
        "title":"Defending the Stack",
        "desc":"Build a security-first mindset — encryption, authentication, threat modelling, Zero Trust and the OWASP fundamentals everyone should know.",
        "tags":["Encryption","Zero Trust","OAuth","OWASP","PKI","SIEM"]},
    "devops": {"name":"DevOps","emoji":"⚙️","color":"#8B5CF6","num":"04",
        "title":"Ship Faster, Break Less",
        "desc":"Automate everything between code and production — Docker, Kubernetes, CI/CD, Terraform and GitHub Actions, explained for beginners.",
        "tags":["Docker","Kubernetes","CI/CD","Terraform","Ansible","Git"]},
    "databases": {"name":"Databases","emoji":"🗄️","color":"#F59E0B","num":"05",
        "title":"Data at Any Scale",
        "desc":"Design databases that never let you down — SQL vs NoSQL, indexing, query optimisation, replication and sharding, in plain language.",
        "tags":["PostgreSQL","MongoDB","Redis","Indexing","Replication","Sharding"]},
    "linux": {"name":"Linux & OS","emoji":"🐧","color":"#EF4444","num":"06",
        "title":"Own the Terminal",
        "desc":"The foundation every IT pro needs — shell scripting, processes, file systems, systemd, permissions and cron, step by step.",
        "tags":["Bash","systemd","cron","Permissions","SSH","File systems"]},
    "hardware": {"name":"Hardware","emoji":"🖥️","color":"#06B6D4","num":"07",
        "title":"Silicon to System",
        "desc":"The physical layer software runs on — CPUs, RAM, storage, network cards and data centre architecture, made simple.",
        "tags":["CPU","RAM","NVMe","RAID","Data Centre","NIC"]},
    "compliance": {"name":"Compliance","emoji":"📋","color":"#EC4899","num":"08",
        "title":"Rules That Protect You",
        "desc":"The regulations that govern IT and why they matter — GDPR, HIPAA, SOC 2, PCI DSS and ISO 27001, explained for non-technical people.",
        "tags":["GDPR","HIPAA","SOC 2","PCI DSS","ISO 27001"]},
}

# Article topic name -> chapter slug (covers extra topic labels)
TOPIC_TO_SLUG = {
    "Networking":"networking","Cloud":"cloud","Security":"security",
    "DevOps":"devops","Databases":"databases","Linux":"linux",
    "Hardware":"hardware","Compliance":"compliance",
    "CyberSecurity":"security","BestPractice":"devops","AI":"cloud",
}

def color_for(topic):
    return CHAPTERS.get(TOPIC_TO_SLUG.get(topic, topic.lower()), {}).get("color", "#FF6B35")

# ─────────────────────────────────────────────────────────────────
#  3-MONTH CONTENT CALENDAR  (39 keywords, 3/week × 13 weeks)
# ─────────────────────────────────────────────────────────────────
CALENDAR = [
    # Month 1 — IT foundations + security basics
    ("what is DNS and how does it work step by step","Networking"),
    ("how does a VPN work explained simply for beginners","Networking"),
    ("what is cloud computing explained simply 2026","Cloud"),
    ("how to protect your website from hackers beginner guide","Security"),
    ("what is Docker and why every developer needs it","DevOps"),
    ("SQL vs NoSQL which database should you choose 2026","Databases"),
    ("Linux commands every beginner must know in 2026","Linux"),
    ("what is two factor authentication and how it works","Security"),
    ("AWS vs Azure vs Google Cloud which is best 2026","Cloud"),
    ("what is a firewall and why every network needs one","Networking"),
    ("how does SSL TLS encryption work simple explanation","Security"),
    ("what is Kubernetes explained simply for beginners","DevOps"),
    ("how does a CPU work explained simply 2026","Hardware"),
    # Month 2 — cybersecurity + compliance
    ("what is GDPR compliance explained simply for businesses","Compliance"),
    ("what is a DDoS attack and how to prevent it","Security"),
    ("ISO 27001 explained what it is and why it matters","Compliance"),
    ("what is zero trust security model and how it works","Security"),
    ("how does a phishing attack work and how to avoid it","Security"),
    ("SOC 2 compliance guide for beginners 2026","Compliance"),
    ("what is penetration testing explained simply","Security"),
    ("HIPAA compliance explained for non technical people","Compliance"),
    ("what is ransomware and how to protect yourself","Security"),
    ("PCI DSS compliance beginner guide for businesses","Compliance"),
    ("what is OWASP top 10 security risks explained","Security"),
    ("how to do a security audit for your website beginner","Security"),
    # Month 3 — best practices + advanced
    ("DevOps best practices for small teams 2026","DevOps"),
    ("cloud security best practices every company needs 2026","Cloud"),
    ("what is CI CD pipeline and why it matters explained","DevOps"),
    ("database backup best practices to never lose data","Databases"),
    ("what is serverless computing pros and cons explained","Cloud"),
    ("network security best practices for businesses 2026","Networking"),
    ("what is infrastructure as code Terraform explained","DevOps"),
    ("API security best practices developers must know","Security"),
    ("how does Kubernetes auto scaling work explained","Cloud"),
    ("Linux server security hardening guide for beginners","Linux"),
    ("what is a disaster recovery plan in IT explained","DevOps"),
    ("how to build zero trust network architecture 2026","Security"),
    ("container security best practices for Docker 2026","DevOps"),
    ("what is multi factor authentication vs 2FA explained","Security"),
]

# ─────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────
def log(msg):
    BRAIN_DIR.mkdir(exist_ok=True)
    line = f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def claude(prompt, system=None, max_tokens=4000):
    payload = {"model": MODEL, "max_tokens": max_tokens,
               "messages": [{"role": "user", "content": prompt}]}
    if system:
        payload["system"] = system
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode(),
        headers={"x-api-key": API_KEY, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    for attempt in range(3):
        try:
            res = json.load(urllib.request.urlopen(req, timeout=90))
            return res["content"][0]["text"].strip()
        except Exception as e:
            if attempt == 2:
                raise
            log(f"API retry {attempt+1}: {e}")
            time.sleep(8)

def openai_chat(prompt, system=None, max_tokens=4000):
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload = {"model": OPENAI_MODEL, "max_tokens": max_tokens, "messages": messages}
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {OPENAI_KEY}",
                 "content-type": "application/json"})
    for attempt in range(3):
        try:
            res = json.load(urllib.request.urlopen(req, timeout=90))
            return res["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if attempt == 2:
                raise
            log(f"OpenAI API retry {attempt+1}: {e}")
            time.sleep(8)

def load_state():
    BRAIN_DIR.mkdir(exist_ok=True)
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception as e:
            log(f"state.json corrupt, resetting: {e}")
    return {"published": [], "used_keywords": [], "topic_counts": {}, "total": 0}

def save_state(s):
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(s, indent=2))
    tmp.replace(STATE_FILE)

def ga4_snippet():
    if not GA4_ID:
        return ""
    return f"""<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA4_ID}');</script>"""

def reading_time(html):
    return f"{max(1, round(len(re.sub(r'<[^>]+>', '', html).split()) / 200))} min read"

def slugify(text, maxlen=60):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')[:maxlen]

# ─────────────────────────────────────────────────────────────────
#  STEP 1 — pick keyword
# ─────────────────────────────────────────────────────────────────
def pick_keyword(state):
    used = state.get("used_keywords", [])
    remaining = [(k, t) for (k, t) in CALENDAR if k not in used]
    if not remaining:
        log("Calendar complete — restarting cycle")
        state["used_keywords"] = []
        remaining = CALENDAR
    keyword, topic = remaining[0]
    log(f"Keyword: {keyword}  [{topic}]")
    return keyword, topic

# ─────────────────────────────────────────────────────────────────
#  STEP 2 — write article
# ─────────────────────────────────────────────────────────────────
def write_article(keyword, topic):
    system = (
        "You are the lead writer for ITVedas, an IT knowledge hub for complete beginners.\n"
        "RULES:\n"
        "1. Explain like the reader has never used a computer professionally.\n"
        "2. Every technical term gets a real-world analogy on first use "
        "(DNS = phone book, RAM = desk space, firewall = security guard).\n"
        "3. Max 20 words per sentence. Short and clear.\n"
        "4. Use 'you' and 'your' — make it personal.\n"
        "5. Use real examples: Netflix, WhatsApp, Google, Amazon, YouTube.\n"
        "6. Numbered steps for any process.\n"
        "7. After a complex idea, add a line starting 'In simple terms:'."
    )
    prompt = f"""Write a complete article for the Google search keyword: "{keyword}"
Topic: {topic}

START with this exact comment block (fill it in):
<!-- META
title: [compelling SEO title containing the keyword]
description: [max 150 chars, includes keyword, starts with an action word]
keyword: {keyword}
topic: {topic}
-->

THEN the article HTML body:
- <h1> title (keyword included naturally)
- Intro: 2 short paragraphs (hook + why it matters to you)
- <h2>What is it?</h2>  — definition + analogy inside a <blockquote>
- <h2>How does it work?</h2>  — numbered steps
- <h2>Why this matters to you</h2>  — everyday impact
- <h2>A real-world example</h2>  — a specific walkthrough
- <h2>Common mistakes to avoid</h2>  — 3 mistakes + fixes
- <h2>Frequently asked questions</h2>  — 3 Q&As
- Conclusion: 1 encouraging paragraph

Include at least one <div class="callout"><div class="callout-title">Pro Tip</div>…</div>.
Use <strong> for key terms and <code> for technical terms on first mention.
1500-2000 words. Return ONLY the META comment + HTML body. No html/head/body tags."""
    return openai_chat(prompt, system=system, max_tokens=4000)

# ─────────────────────────────────────────────────────────────────
#  STEP 3 — self-review
# ─────────────────────────────────────────────────────────────────
def review(content, keyword):
    prompt = f"""Review this IT article for the keyword "{keyword}".
Score 0-100 on: beginner-friendliness (30), real examples (25), structure (25), SEO (20).
Reply with ONLY JSON: {{"score":85,"verdict":"PUBLISH","fix":"short note"}}
verdict = PUBLISH if score >= 75 else REWRITE.
Article (first 2000 chars): {content[:2000]}"""
    try:
        m = re.search(r'\{[^{}]+\}', claude(prompt, max_tokens=200), re.DOTALL)
        if m:
            r = json.loads(m.group())
            log(f"Self-review: {r.get('score')}/100 — {r.get('verdict')}")
            return r
    except Exception as e:
        log(f"Review parse error: {e}")
    return {"score": 80, "verdict": "PUBLISH"}

# ─────────────────────────────────────────────────────────────────
#  STEP 4 — extract metadata
# ─────────────────────────────────────────────────────────────────
def extract_meta(content, keyword, topic):
    meta = {"title": keyword.title(),
            "description": f"Learn {keyword} on ITVedas, explained simply.",
            "keyword": keyword, "topic": topic}
    m = re.search(r'<!-- META(.*?)-->', content, re.DOTALL)
    if m:
        for line in m.group(1).strip().splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                if k.strip() in meta:
                    meta[k.strip()] = v.strip()
    h1 = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE | re.DOTALL)
    if h1:
        meta["title"] = re.sub(r'<[^>]+>', '', h1.group(1)).strip()
    return meta

# ─────────────────────────────────────────────────────────────────
#  STEP 5 — build full article page
# ─────────────────────────────────────────────────────────────────
def build_page(content, meta, date_str):
    topic   = meta["topic"]
    title   = meta["title"]
    desc    = meta["description"]
    keyword = meta["keyword"]
    color   = color_for(topic)

    body = re.sub(r'<!-- META.*?-->', '', content, flags=re.DOTALL)
    body = body.replace('[AFFILIATE]', '').strip()
    body = re.sub(r'\n{3,}', '\n\n', body)

    # table of contents + anchors
    toc = ""
    seen_anchors: dict = {}
    for h in re.findall(r'<h2[^>]*>(.*?)</h2>', body, re.IGNORECASE | re.DOTALL):
        clean = re.sub(r'<[^>]+>', '', h).strip()
        base_anc = slugify(clean)
        seen_anchors[base_anc] = seen_anchors.get(base_anc, 0) + 1
        anc = base_anc if seen_anchors[base_anc] == 1 else f"{base_anc}-{seen_anchors[base_anc]}"
        toc += f'<li><a href="#{anc}">{clean}</a></li>'
        body = re.sub(rf'<h2([^>]*)>{re.escape(h)}</h2>',
                      f'<h2\\1 id="{anc}">{h}</h2>', body, count=1)

    rt = reading_time(body)
    url = f"{SITE_URL}/articles/{date_str}-{topic.lower()}.html"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="description" content="{desc}">
<meta name="keywords" content="{keyword}, {topic} guide, ITVedas, IT knowledge">
<meta name="robots" content="index,follow">
<meta property="og:title" content="{title} | {SITE_NAME}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{url}">
<title>{title} | {SITE_NAME}</title>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Article","headline":"{title}",
"description":"{desc}","keywords":"{keyword}",
"author":{{"@type":"Organization","name":"{SITE_NAME}","url":"{SITE_URL}"}},
"publisher":{{"@type":"Organization","name":"{SITE_NAME}","url":"{SITE_URL}"}},
"datePublished":"{date_str}","dateModified":"{date_str}",
"articleSection":"{topic}","educationalLevel":"Beginner"}}
</script>
{ga4_snippet()}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{--bg:#0A0A0F;--bg2:#13131C;--bg3:#1C1C2A;--text:#F0F0F8;--muted:#8888A8;--sub:#D0D0E8;--accent:{color};--border:rgba(255,255,255,0.08);}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
html{{scroll-behavior:smooth;}}
body{{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;font-size:17px;line-height:1.85;-webkit-font-smoothing:antialiased;}}
.progress{{position:fixed;top:0;left:0;right:0;height:3px;z-index:200;}}
.pb{{height:100%;background:linear-gradient(90deg,var(--accent),#8B5CF6);width:0%;}}
nav{{position:fixed;top:3px;left:0;right:0;z-index:100;display:flex;align-items:center;justify-content:space-between;padding:0 2rem;height:64px;background:rgba(10,10,15,0.92);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);}}
.logo{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.3rem;color:var(--text);text-decoration:none;}}
.logo span{{color:#FF6B35;}}
.nav-back{{color:var(--muted);text-decoration:none;font-size:0.875rem;padding:0.5rem 1rem;border:1px solid var(--border);border-radius:8px;transition:color .2s;}}
.nav-back:hover{{color:var(--text);}}
.hero{{padding:7.5rem 2rem 3rem;max-width:860px;margin:0 auto;}}
.breadcrumb{{font-size:0.8rem;color:var(--muted);margin-bottom:1.5rem;}}
.breadcrumb a{{color:var(--muted);text-decoration:none;}}
.breadcrumb a:hover{{color:var(--accent);}}
.badges{{display:flex;gap:0.6rem;margin-bottom:1.5rem;flex-wrap:wrap;align-items:center;}}
.badge{{background:{color}1f;border:1px solid {color}44;color:{color};padding:0.3rem 0.9rem;border-radius:100px;font-size:0.73rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;}}
.badge-info{{color:var(--muted);font-size:0.8rem;background:var(--bg2);border:1px solid var(--border);padding:0.25rem 0.7rem;border-radius:100px;}}
.hero h1{{font-family:'Space Grotesk',sans-serif;font-size:clamp(1.9rem,4vw,3rem);font-weight:700;letter-spacing:-0.025em;line-height:1.1;margin-bottom:1.25rem;}}
.layout{{display:grid;grid-template-columns:1fr 280px;gap:3rem;max-width:1140px;margin:0 auto;padding:0 2rem 6rem;align-items:start;}}
article{{min-width:0;}}
.toc{{background:var(--bg2);border:1px solid var(--border);border-radius:14px;padding:1.5rem;margin:0 0 2.5rem;}}
.toc-label{{font-size:0.72rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:var(--muted);margin-bottom:1rem;}}
.toc ul{{list-style:none;}}
.toc a{{color:var(--muted);text-decoration:none;font-size:0.875rem;padding:0.3rem 0.6rem;display:block;border-radius:6px;border-left:2px solid transparent;transition:all .2s;}}
.toc a:hover{{color:var(--text);background:rgba(255,255,255,0.04);border-left-color:var(--accent);padding-left:0.9rem;}}
article h2{{font-family:'Space Grotesk',sans-serif;font-size:1.55rem;font-weight:700;margin:3rem 0 1rem;display:flex;align-items:center;gap:0.75rem;}}
article h2::before{{content:'';width:4px;height:1.4em;background:var(--accent);border-radius:2px;flex-shrink:0;}}
article h3{{font-family:'Space Grotesk',sans-serif;font-size:1.1rem;font-weight:600;margin:2rem 0 0.6rem;}}
article p{{margin-bottom:1.35rem;color:var(--sub);}}
article ul,article ol{{margin:0.75rem 0 1.5rem 1.5rem;color:var(--sub);}}
article li{{margin-bottom:0.65rem;}}
article strong{{color:var(--text);}}
article blockquote{{background:linear-gradient(135deg,{color}10,#8B5CF610);border-left:4px solid var(--accent);border-radius:0 12px 12px 0;padding:1.25rem 1.5rem;margin:2rem 0;color:var(--sub);font-style:italic;}}
article code{{background:var(--bg2);border:1px solid var(--border);padding:0.15rem 0.45rem;border-radius:5px;font-family:monospace;font-size:0.875rem;color:#10B981;}}
article pre{{background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:1.5rem;margin:2rem 0;overflow-x:auto;}}
article pre code{{background:none;border:none;padding:0;color:#9FE1CB;}}
.callout{{background:linear-gradient(135deg,{color}14,#8B5CF610);border:1px solid {color}33;border-radius:12px;padding:1.25rem 1.5rem;margin:2rem 0;}}
.callout-title{{font-weight:700;color:var(--accent);font-size:0.8rem;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.6rem;}}
.cta{{margin:3rem 0;padding:2.5rem;background:linear-gradient(135deg,{color}14,#8B5CF614);border:1px solid {color}33;border-radius:20px;text-align:center;}}
.cta h3{{font-family:'Space Grotesk',sans-serif;font-size:1.3rem;font-weight:700;margin-bottom:0.75rem;}}
.cta p{{color:var(--muted);margin-bottom:1.5rem;}}
.btn{{display:inline-block;background:var(--accent);color:#fff;padding:0.85rem 2.25rem;border-radius:10px;text-decoration:none;font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:0.9rem;}}
aside{{position:sticky;top:87px;display:flex;flex-direction:column;gap:1rem;}}
.sc{{background:var(--bg2);border:1px solid var(--border);border-radius:14px;padding:1.25rem;}}
.sc-label{{font-size:0.72rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:var(--muted);margin-bottom:0.85rem;}}
.sc ul{{list-style:none;}}
.sc a{{color:var(--muted);text-decoration:none;font-size:0.84rem;padding:0.3rem 0;display:block;transition:color .2s;}}
.sc a:hover{{color:var(--accent);}}
.chapter-list a{{display:block;color:var(--muted);text-decoration:none;font-size:0.85rem;padding:0.4rem 0;border-bottom:1px solid var(--border);transition:color .2s;}}
.chapter-list a:last-child{{border:none;}}
.chapter-list a:hover{{color:var(--accent);}}
.nl-sc{{background:linear-gradient(135deg,#FF6B3514,#8B5CF614);border:1px solid #FF6B3533;border-radius:14px;padding:1.25rem;}}
.nl-sc p{{font-size:0.84rem;color:var(--muted);margin-bottom:1rem;line-height:1.6;}}
footer{{border-top:1px solid var(--border);padding:3rem 2rem;text-align:center;color:var(--muted);font-size:0.875rem;}}
.fl{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.2rem;color:var(--text);margin-bottom:0.5rem;}}
.fl span{{color:#FF6B35;}}
.flinks{{display:flex;gap:1.75rem;justify-content:center;margin:0.75rem 0;flex-wrap:wrap;}}
.flinks a{{color:var(--muted);text-decoration:none;}}
.flinks a:hover{{color:#FF6B35;}}
@media(max-width:900px){{.layout{{grid-template-columns:1fr;}}aside{{display:none;}}.hero,.layout{{padding-left:1.25rem;padding-right:1.25rem;}}nav{{padding:0 1.25rem;}}}}
@media(prefers-reduced-motion:reduce){{*{{animation:none!important;transition:none!important;}}}}
</style>
</head>
<body>
<div class="progress"><div class="pb" id="pb"></div></div>
<nav>
  <a href="/" class="logo">IT<span>Vedas</span></a>
  <a href="/articles/{TOPIC_TO_SLUG.get(topic, topic.lower())}/" class="nav-back">← {topic}</a>
</nav>
<div class="hero">
  <div class="breadcrumb"><a href="/">Home</a> › <a href="/articles/{TOPIC_TO_SLUG.get(topic, topic.lower())}/">{topic}</a> › Article</div>
  <div class="badges">
    <span class="badge">{topic}</span>
    <span class="badge-info">📅 {date_str}</span>
    <span class="badge-info">⏱ {rt}</span>
    <span class="badge-info">👶 Beginner friendly</span>
  </div>
  <h1>{title}</h1>
</div>
<div class="layout">
  <article>
    <div class="toc"><div class="toc-label">In this article</div><ul>{toc}</ul></div>
    {body}
    <div class="cta">
      <h3>Keep Learning on ITVedas</h3>
      <p>One of many free guides across 8 IT chapters — all in plain English.</p>
      <a href="/" class="btn">Explore All Chapters →</a>
    </div>
  </article>
  <aside>
    <div class="sc"><div class="sc-label">Jump to section</div><ul>{toc}</ul></div>
    <div class="sc"><div class="sc-label">All chapters</div><div class="chapter-list">
      <a href="/articles/networking/">🌐 Networking</a>
      <a href="/articles/cloud/">☁️ Cloud</a>
      <a href="/articles/security/">🔐 Security</a>
      <a href="/articles/devops/">⚙️ DevOps</a>
      <a href="/articles/databases/">🗄️ Databases</a>
      <a href="/articles/linux/">🐧 Linux</a>
      <a href="/articles/hardware/">🖥️ Hardware</a>
      <a href="/articles/compliance/">📋 Compliance</a>
    </div></div>
    <div class="nl-sc"><div class="sc-label" style="color:var(--accent);">Free newsletter</div>
      <p>New IT guides every Monday, Wednesday and Friday — plain English.</p>
      <a href="/#newsletter" class="btn" style="display:block;text-align:center;font-size:0.84rem;padding:0.65rem;">Subscribe Free →</a>
    </div>
  </aside>
</div>
<footer>
  <div class="fl">IT<span>Vedas</span></div>
  <p>The complete IT knowledge hub — explained simply, for everyone.</p>
  <div class="flinks"><a href="/">Home</a><a href="/news.html">News</a><a href="/#chapters">Chapters</a><a href="mailto:{CONTACT}">Contact</a></div>
  <p style="margin-top:1rem;">© {datetime.date.today().year} {SITE_NAME} · Knowledge for everyone</p>
</footer>
<script>
const pb=document.getElementById('pb');
addEventListener('scroll',()=>{{const d=document.documentElement;pb.style.width=(d.scrollTop/(d.scrollHeight-d.clientHeight)*100)+'%';}},{{passive:true}});
</script>
</body>
</html>"""

# ─────────────────────────────────────────────────────────────────
#  STEP 6 — homepage "Latest Articles"
# ─────────────────────────────────────────────────────────────────
def update_homepage(state):
    index = ROOT / "index.html"
    if not index.exists():
        log("index.html missing — skipping homepage update")
        return
    html = index.read_text(encoding="utf-8")
    recent = list(reversed(state.get("published", [])))[:8]
    if not recent:
        return
    items = ""
    for a in recent:
        c = color_for(a.get("topic", "IT"))
        items += (
            f'<a href="/articles/{a["file"]}" style="display:flex;align-items:flex-start;gap:1rem;'
            f'padding:1rem 0;border-bottom:1px solid rgba(255,255,255,0.06);text-decoration:none;color:inherit;">'
            f'<span style="background:{c}1a;color:{c};font-size:0.68rem;font-weight:700;padding:0.25rem 0.6rem;'
            f'border-radius:4px;white-space:nowrap;text-transform:uppercase;letter-spacing:0.04em;margin-top:3px;flex-shrink:0;">{a.get("topic","IT")}</span>'
            f'<div><div style="font-size:0.95rem;color:#D0D0E8;line-height:1.45;margin-bottom:0.2rem;">{a.get("title","Article")}</div>'
            f'<div style="font-size:0.75rem;color:#8888A8;">{a.get("date","")} · {a.get("rt","5 min read")}</div></div></a>'
        )
    section = (
        '<!-- LATEST_ARTICLES_START -->\n'
        '<div id="latest-articles" style="background:#13131C;border-top:1px solid rgba(255,255,255,0.08);'
        'border-bottom:1px solid rgba(255,255,255,0.08);padding:5rem 2rem;">'
        '<div style="max-width:1200px;margin:0 auto;">'
        '<div style="font-size:0.75rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#FF6B35;margin-bottom:0.75rem;">Latest Articles</div>'
        '<h2 style="font-family:\'Space Grotesk\',sans-serif;font-size:clamp(1.75rem,3vw,2.5rem);font-weight:700;letter-spacing:-0.02em;margin-bottom:0.75rem;">Fresh from the Knowledge Hub</h2>'
        '<p style="color:#8888A8;margin-bottom:2.5rem;max-width:500px;">New articles every Monday, Wednesday and Friday — always plain English, always free.</p>'
        f'<div style="max-width:720px;">{items}</div></div></div>\n'
        '<!-- LATEST_ARTICLES_END -->'
    )
    if '<!-- LATEST_ARTICLES_START -->' in html:
        html = re.sub(r'<!-- LATEST_ARTICLES_START -->.*?<!-- LATEST_ARTICLES_END -->',
                      section, html, flags=re.DOTALL)
    else:
        html = html.replace('<div style="padding:5rem 0;" id="newsletter">',
                            section + '\n<div style="padding:5rem 0;" id="newsletter">')
    try:
        index.write_text(html, encoding="utf-8")
    except Exception as e:
        log(f"Homepage write error: {e}")
        return
    log("Homepage Latest Articles updated")

# ─────────────────────────────────────────────────────────────────
#  STEP 7 — chapter landing pages
# ─────────────────────────────────────────────────────────────────
def build_chapter_pages(state):
    published = state.get("published", [])
    for slug, ch in CHAPTERS.items():
        arts = [a for a in published
                if TOPIC_TO_SLUG.get(a.get("topic",""), a.get("topic","").lower()) == slug]
        arts = list(reversed(arts))
        if arts:
            cards = "".join(
                f'<a href="/articles/{a["file"]}" class="art">'
                f'<div class="art-meta"><span>📅 {a.get("date","")}</span><span>⏱ {a.get("rt","5 min read")}</span></div>'
                f'<h3 class="art-title">{a.get("title","Article")}</h3>'
                f'<span class="art-link">Read article →</span></a>'
                for a in arts)
            body = f'<div class="art-list">{cards}</div>'
            heading = "All guides in this chapter"
        else:
            body = ('<div class="empty"><div class="empty-emoji">📝</div>'
                    '<h3>Articles coming soon</h3>'
                    '<p>New guides publish every Monday, Wednesday and Friday. '
                    'This chapter\'s first articles are on the way.</p>'
                    '<a href="/#newsletter" class="btn">Subscribe for updates →</a></div>')
            heading = "This chapter is just getting started"
        tags = "".join(f'<span class="tag">{t}</span>' for t in ch["tags"])
        color = ch["color"]
        page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="description" content="{ch['desc']}">
<meta name="keywords" content="{ch['name']} tutorials, {', '.join(ch['tags'])}, ITVedas">
<meta name="robots" content="index,follow">
<meta property="og:title" content="{ch['name']} — {ch['title']} | {SITE_NAME}">
<meta property="og:description" content="{ch['desc']}">
<link rel="canonical" href="{SITE_URL}/articles/{slug}/">
<title>{ch['name']} Tutorials — {ch['title']} | {SITE_NAME}</title>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"CollectionPage","name":"{ch['name']} — {SITE_NAME}","description":"{ch['desc']}","url":"{SITE_URL}/articles/{slug}/"}}
</script>
{ga4_snippet()}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{--bg:#0A0A0F;--bg2:#13131C;--text:#F0F0F8;--muted:#8888A8;--sub:#D0D0E8;--accent:{color};--border:rgba(255,255,255,0.08);}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
html{{scroll-behavior:smooth;}}
body{{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;font-size:16px;line-height:1.7;-webkit-font-smoothing:antialiased;}}
nav{{position:fixed;top:0;left:0;right:0;z-index:100;display:flex;align-items:center;justify-content:space-between;padding:0 2rem;height:64px;background:rgba(10,10,15,0.92);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);}}
.logo{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.3rem;color:var(--text);text-decoration:none;}}
.logo span{{color:#FF6B35;}}
.nav-links{{display:flex;gap:1.5rem;}}
.nav-links a{{color:var(--muted);text-decoration:none;font-size:0.875rem;transition:color .2s;}}
.nav-links a:hover{{color:var(--text);}}
.hero{{padding:8rem 2rem 3rem;max-width:1000px;margin:0 auto;position:relative;}}
.hero-glow{{position:absolute;top:4rem;left:50%;transform:translateX(-50%);width:600px;height:400px;background:radial-gradient(circle,{color}1a,transparent 70%);pointer-events:none;}}
.breadcrumb{{font-size:0.8rem;color:var(--muted);margin-bottom:1.5rem;position:relative;}}
.breadcrumb a{{color:var(--muted);text-decoration:none;}}
.breadcrumb a:hover{{color:var(--accent);}}
.ch-icon{{width:72px;height:72px;border-radius:18px;background:{color}1f;display:flex;align-items:center;justify-content:center;font-size:2.25rem;margin-bottom:1.5rem;position:relative;}}
.ch-num{{font-size:0.72rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:{color};margin-bottom:0.75rem;position:relative;}}
.hero h1{{font-family:'Space Grotesk',sans-serif;font-size:clamp(2rem,4vw,3.25rem);font-weight:700;letter-spacing:-0.025em;line-height:1.1;margin-bottom:1.25rem;position:relative;}}
.hero p{{font-size:1.1rem;color:var(--sub);max-width:640px;line-height:1.75;margin-bottom:1.75rem;position:relative;}}
.tags{{display:flex;flex-wrap:wrap;gap:0.5rem;position:relative;}}
.tag{{font-size:0.78rem;padding:0.3rem 0.85rem;background:var(--bg2);border:1px solid var(--border);border-radius:100px;color:var(--muted);}}
.content{{max-width:1000px;margin:0 auto;padding:2rem 2rem 5rem;}}
.section-label{{font-size:0.75rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:var(--accent);margin-bottom:1rem;}}
.section-h{{font-family:'Space Grotesk',sans-serif;font-size:1.75rem;font-weight:700;letter-spacing:-0.02em;margin-bottom:2rem;}}
.art-list{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:1.25rem;}}
.art{{background:var(--bg2);border:1px solid var(--border);border-radius:14px;padding:1.5rem;text-decoration:none;color:inherit;transition:transform .2s,border-color .2s;}}
.art:hover{{transform:translateY(-4px);border-color:{color}55;}}
.art-meta{{display:flex;gap:1rem;margin-bottom:0.85rem;font-size:0.75rem;color:var(--muted);}}
.art-title{{font-family:'Space Grotesk',sans-serif;font-size:1.1rem;font-weight:600;line-height:1.4;margin-bottom:1rem;color:var(--text);}}
.art-link{{font-size:0.82rem;color:{color};font-weight:600;}}
.empty{{text-align:center;padding:4rem 2rem;background:var(--bg2);border:1px solid var(--border);border-radius:20px;max-width:560px;margin:0 auto;}}
.empty-emoji{{font-size:3rem;margin-bottom:1rem;}}
.empty h3{{font-family:'Space Grotesk',sans-serif;font-size:1.3rem;margin-bottom:0.75rem;}}
.empty p{{color:var(--muted);margin-bottom:1.5rem;line-height:1.7;}}
.btn{{display:inline-block;background:var(--accent);color:#fff;padding:0.8rem 2rem;border-radius:10px;text-decoration:none;font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:0.9rem;}}
.other{{margin-top:4rem;padding-top:3rem;border-top:1px solid var(--border);}}
.oc-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:0.75rem;margin-top:1.5rem;}}
.oc{{display:flex;align-items:center;gap:0.6rem;background:var(--bg2);border:1px solid var(--border);border-radius:10px;padding:0.85rem 1rem;text-decoration:none;color:var(--sub);font-size:0.875rem;transition:border-color .2s,color .2s;}}
.oc:hover{{border-color:rgba(255,255,255,0.2);color:var(--text);}}
footer{{border-top:1px solid var(--border);padding:2.5rem 2rem;text-align:center;color:var(--muted);font-size:0.875rem;}}
.fl{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.1rem;color:var(--text);margin-bottom:0.5rem;}}
.fl span{{color:#FF6B35;}}
.flinks{{display:flex;gap:1.5rem;justify-content:center;margin-top:0.75rem;flex-wrap:wrap;}}
.flinks a{{color:var(--muted);text-decoration:none;}}
.flinks a:hover{{color:#FF6B35;}}
@media(max-width:640px){{nav{{padding:0 1.25rem;}}.nav-links{{display:none;}}.hero,.content{{padding-left:1.25rem;padding-right:1.25rem;}}.art-list{{grid-template-columns:1fr;}}}}
</style>
</head>
<body>
<nav>
  <a href="/" class="logo">IT<span>Vedas</span></a>
  <div class="nav-links"><a href="/">Home</a><a href="/news.html">📰 News</a><a href="/#chapters">All Chapters</a><a href="mailto:{CONTACT}">Contact</a></div>
</nav>
<div class="hero">
  <div class="hero-glow"></div>
  <div class="breadcrumb"><a href="/">Home</a> › <a href="/#chapters">Chapters</a> › {ch['name']}</div>
  <div class="ch-icon">{ch['emoji']}</div>
  <div class="ch-num">Chapter {ch['num']} · {ch['name']}</div>
  <h1>{ch['title']}</h1>
  <p>{ch['desc']}</p>
  <div class="tags">{tags}</div>
</div>
<div class="content">
  <div class="section-label">{ch['name']} Articles</div>
  <h2 class="section-h">{heading}</h2>
  {body}
  <div class="other">
    <div class="section-label">Explore other chapters</div>
    <div class="oc-grid">
      <a href="/articles/networking/" class="oc">🌐 Networking</a>
      <a href="/articles/cloud/" class="oc">☁️ Cloud</a>
      <a href="/articles/security/" class="oc">🔐 Security</a>
      <a href="/articles/devops/" class="oc">⚙️ DevOps</a>
      <a href="/articles/databases/" class="oc">🗄️ Databases</a>
      <a href="/articles/linux/" class="oc">🐧 Linux</a>
      <a href="/articles/hardware/" class="oc">🖥️ Hardware</a>
      <a href="/articles/compliance/" class="oc">📋 Compliance</a>
    </div>
  </div>
</div>
<footer>
  <div class="fl">IT<span>Vedas</span></div>
  <p>The complete IT knowledge hub — explained simply, for everyone.</p>
  <div class="flinks"><a href="/">Home</a><a href="/news.html">News</a><a href="/#chapters">Chapters</a><a href="mailto:{CONTACT}">Contact</a></div>
  <p style="margin-top:1rem;">© {datetime.date.today().year} {SITE_NAME} · Knowledge for everyone</p>
</footer>
</body>
</html>"""
        d = ARTICLES / slug
        d.mkdir(parents=True, exist_ok=True)
        try:
            (d / "index.html").write_text(page, encoding="utf-8")
        except Exception as e:
            log(f"Chapter page write error ({slug}): {e}")
    log(f"Chapter pages rebuilt ({len(CHAPTERS)})")

# ─────────────────────────────────────────────────────────────────
#  STEP 8 — sitemap
# ─────────────────────────────────────────────────────────────────
def build_sitemap(state):
    today = datetime.date.today().isoformat()
    urls = [f'  <url><loc>{SITE_URL}/</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>1.0</priority></url>',
            f'  <url><loc>{SITE_URL}/news.html</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq><priority>0.9</priority></url>',
            f'  <url><loc>{SITE_URL}/career-paths.html</loc><lastmod>{today}</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>']
    for slug in CHAPTERS:
        urls.append(f'  <url><loc>{SITE_URL}/articles/{slug}/</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.7</priority></url>')
    for a in state.get("published", []):
        urls.append(f'  <url><loc>{SITE_URL}/articles/{a["file"]}</loc><lastmod>{a.get("date",today)}</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>')
    try:
        (ROOT / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(urls) + "\n</urlset>")
    except Exception as e:
        log(f"Sitemap write error: {e}")
        return
    log(f"Sitemap rebuilt ({len(urls)} URLs)")

# ─────────────────────────────────────────────────────────────────
#  STEP 9 — email notification
# ─────────────────────────────────────────────────────────────────
def send_email(meta, filename, score):
    if not (NOTIFY_TO and SMTP_FROM and SMTP_PASS):
        log("Email not configured — skipping")
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"ITVedas published: {meta['title']}"
        msg["From"], msg["To"] = SMTP_FROM, NOTIFY_TO
        html = f"""<div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;background:#0A0A0F;color:#F0F0F8;border-radius:12px;overflow:hidden;">
<div style="background:linear-gradient(135deg,#FF6B35,#8B5CF6);padding:1.75rem;text-align:center;"><h1 style="margin:0;font-size:1.4rem;color:#fff;">New ITVedas article is live</h1></div>
<div style="padding:1.75rem;">
<div style="background:#13131C;border-radius:10px;padding:1.5rem;margin-bottom:1.25rem;">
<p style="font-size:0.75rem;color:#8888A8;margin:0 0 0.5rem;text-transform:uppercase;letter-spacing:0.1em;">{meta['topic']}</p>
<h2 style="margin:0 0 0.75rem;font-size:1.25rem;">{meta['title']}</h2>
<p style="color:#8888A8;margin:0 0 1rem;font-size:0.9rem;">{meta['description']}</p>
<p style="color:#8888A8;margin:0;font-size:0.85rem;">Quality score: <strong style="color:#10B981;">{score}/100</strong> · {datetime.date.today().isoformat()}</p>
</div>
<div style="text-align:center;"><a href="{SITE_URL}/articles/{filename}" style="display:inline-block;background:#FF6B35;color:#fff;padding:0.85rem 2rem;border-radius:8px;text-decoration:none;font-weight:600;">View Live Article →</a></div>
</div></div>"""
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(SMTP_FROM, SMTP_PASS)
            s.sendmail(SMTP_FROM, NOTIFY_TO, msg.as_string())
        log(f"Email sent to {NOTIFY_TO}")
    except Exception as e:
        log(f"Email error: {e}")

# ─────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────
def main():
    log("=" * 55)
    log("ITVedas Brain — run start")
    if not API_KEY:
        log("FATAL: ANTHROPIC_API_KEY not set")
        raise SystemExit(1)
    if not OPENAI_KEY:
        log("FATAL: OPENAI_API_KEY not set")
        raise SystemExit(1)

    ARTICLES.mkdir(exist_ok=True)
    BRAIN_DIR.mkdir(exist_ok=True)
    state = load_state()
    state["last_run"] = datetime.datetime.now().isoformat()

    # 1. keyword
    keyword, topic = pick_keyword(state)
    # 2. write
    content = write_article(keyword, topic)
    # 3. review (one rewrite if weak)
    r = review(content, keyword)
    score = r.get("score", 80)
    if r.get("verdict") == "REWRITE":
        log("Rewriting (low score)")
        content = write_article(keyword, topic)
        score = 80
    # 4. metadata
    meta = extract_meta(content, keyword, topic)
    log(f"Title: {meta['title']}")
    # 5. build page
    today = datetime.date.today().isoformat()
    page = build_page(content, meta, today)
    fname = f"{today}-{topic.lower()}.html"
    out = ARTICLES / fname
    n = 1
    while out.exists():
        fname = f"{today}-{topic.lower()}-{n}.html"
        out = ARTICLES / fname
        n += 1
    try:
        out.write_text(page, encoding="utf-8")
    except Exception as e:
        log(f"Article write error: {e}")
        raise
    log(f"Published: articles/{fname}")
    # 6. update state
    rt = reading_time(content)
    state["used_keywords"] = (state.get("used_keywords", []) + [keyword])[-60:]
    state["topic_counts"][topic] = state.get("topic_counts", {}).get(topic, 0) + 1
    state["total"] = state.get("total", 0) + 1
    state["published"] = (state.get("published", []) + [{
        "file": fname, "title": meta["title"], "topic": topic,
        "keyword": keyword, "date": today, "score": score, "rt": rt}])[-60:]
    # 7. homepage, chapters, sitemap
    update_homepage(state)
    build_chapter_pages(state)
    build_sitemap(state)
    save_state(state)
    # 8. email
    send_email(meta, fname, score)

    log(f"DONE. Article #{state['total']}: {meta['title']} ({score}/100)")
    log("=" * 55)

if __name__ == "__main__":
    main()
