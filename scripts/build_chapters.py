"""
ITVedas Chapter Page Builder
============================
Creates landing pages for all 8 chapters at /articles/<topic>/index.html
Each lists all published articles in that topic.
Run standalone now to create pages, OR import build_all_chapters()
into the brain so it runs after every publish.
"""
import pathlib, re, json, datetime

SITE = "https://itvedas.com"

CHAPTERS = {
    "networking": {
        "name":"Networking","emoji":"🌐","color":"#FF6B35","num":"01",
        "title":"How Networks Talk",
        "desc":"Everything about how data moves across the internet and inside your network — TCP/IP, DNS, subnetting, routing, VPNs and firewalls, all explained in plain English.",
        "tags":["TCP/IP","DNS","Subnetting","Routing","VPN","Firewalls"],
    },
    "cloud": {
        "name":"Cloud Computing","emoji":"☁️","color":"#3B82F6","num":"02",
        "title":"The Cloud, Demystified",
        "desc":"Understand AWS, Azure and Google Cloud — what IaaS, PaaS and SaaS really mean, how to deploy real infrastructure, and how to architect for scale without the jargon.",
        "tags":["AWS","Azure","GCP","Serverless","CDN","Auto-scaling"],
    },
    "security": {
        "name":"Security","emoji":"🔐","color":"#10B981","num":"03",
        "title":"Defending the Stack",
        "desc":"Build a security-first mindset from scratch — encryption, authentication, threat modelling, Zero Trust and the OWASP fundamentals every IT professional should know.",
        "tags":["Encryption","Zero Trust","OAuth","OWASP","PKI","SIEM"],
    },
    "devops": {
        "name":"DevOps","emoji":"⚙️","color":"#8B5CF6","num":"04",
        "title":"Ship Faster, Break Less",
        "desc":"Automate everything between writing code and running it in production — Docker, Kubernetes, CI/CD pipelines, Terraform and GitHub Actions, explained for beginners.",
        "tags":["Docker","Kubernetes","CI/CD","Terraform","Ansible","Git"],
    },
    "databases": {
        "name":"Databases","emoji":"🗄️","color":"#F59E0B","num":"05",
        "title":"Data at Any Scale",
        "desc":"Design and run databases that never let you down — SQL vs NoSQL, indexing, query optimisation, replication and sharding, all in plain language.",
        "tags":["PostgreSQL","MongoDB","Redis","Indexing","Replication","Sharding"],
    },
    "linux": {
        "name":"Linux & OS","emoji":"🐧","color":"#EF4444","num":"06",
        "title":"Own the Terminal",
        "desc":"Master the foundation every IT professional needs — shell scripting, process management, file systems, systemd, permissions and cron, explained step by step.",
        "tags":["Bash","systemd","cron","Permissions","SSH","File systems"],
    },
    "hardware": {
        "name":"Hardware","emoji":"🖥️","color":"#06B6D4","num":"07",
        "title":"Silicon to System",
        "desc":"Understand the physical layer that every piece of software runs on — CPUs, RAM, storage, networking cards and data centre architecture, made simple.",
        "tags":["CPU","RAM","NVMe","RAID","Data Centre","NIC"],
    },
    "compliance": {
        "name":"Compliance","emoji":"📋","color":"#EC4899","num":"08",
        "title":"Rules That Protect You",
        "desc":"Understand the regulations that govern IT and why they matter — GDPR, HIPAA, SOC 2, PCI DSS and ISO 27001, explained so non-technical people can actually follow.",
        "tags":["GDPR","HIPAA","SOC 2","PCI DSS","ISO 27001"],
    },
}

# Map article topic names (from brain state) to chapter slugs
TOPIC_TO_SLUG = {
    "Networking":"networking","Cloud":"cloud","Security":"security",
    "DevOps":"devops","Databases":"databases","Linux":"linux",
    "Hardware":"hardware","Compliance":"compliance",
    "CyberSecurity":"security","BestPractice":"devops","AI":"cloud",
}

def load_published():
    sf = pathlib.Path("brain/state.json")
    if sf.exists():
        try: return json.loads(sf.read_text()).get("published", [])
        except: pass
    return []

def articles_for_chapter(slug, published):
    out = []
    for a in published:
        atopic = a.get("topic","")
        if TOPIC_TO_SLUG.get(atopic, atopic.lower()) == slug:
            out.append(a)
    return out

def build_chapter_page(slug, ch, articles):
    color = ch["color"]
    # Article list HTML
    if articles:
        items = ""
        for a in articles:
            items += f"""<a href="/articles/{a['file']}" class="art">
              <div class="art-meta"><span class="art-date">📅 {a.get('date','')}</span><span class="art-rt">⏱ {a.get('rt','5 min read')}</span></div>
              <h3 class="art-title">{a.get('title','Article')}</h3>
              <span class="art-link">Read article →</span>
            </a>"""
        article_section = f'<div class="art-list">{items}</div>'
    else:
        article_section = """<div class="empty">
          <div class="empty-emoji">📝</div>
          <h3>Articles coming soon</h3>
          <p>Our AI writer publishes new guides every Monday, Wednesday and Friday. This chapter's first articles are on the way — check back soon or subscribe to get notified.</p>
          <a href="/#newsletter" class="btn">Subscribe for updates →</a>
        </div>"""

    tags_html = "".join(f'<span class="tag">{t}</span>' for t in ch["tags"])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="description" content="{ch['desc']}">
<meta name="keywords" content="{ch['name']} tutorials, {', '.join(ch['tags'])}, ITVedas, IT knowledge">
<meta name="robots" content="index,follow">
<meta property="og:title" content="{ch['name']} — {ch['title']} | ITVedas">
<meta property="og:description" content="{ch['desc']}">
<meta property="og:type" content="website">
<link rel="canonical" href="{SITE}/articles/{slug}/">
<title>{ch['name']} Tutorials — {ch['title']} | ITVedas</title>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"CollectionPage","name":"{ch['name']} — ITVedas",
"description":"{ch['desc']}","url":"{SITE}/articles/{slug}/"}}
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{--bg:#0A0A0F;--bg2:#13131C;--bg3:#1C1C2A;--text:#F0F0F8;--muted:#8888A8;--sub:#D0D0E8;--accent:{color};--border:rgba(255,255,255,0.08);}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
html{{scroll-behavior:smooth;}}
body{{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;font-size:16px;line-height:1.7;-webkit-font-smoothing:antialiased;}}
nav{{position:fixed;top:0;left:0;right:0;z-index:100;display:flex;align-items:center;justify-content:space-between;padding:0 2rem;height:64px;background:rgba(10,10,15,0.92);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);}}
.logo{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.3rem;color:var(--text);text-decoration:none;}}
.logo span{{color:#FF6B35;}}
.nav-links{{display:flex;gap:1.5rem;align-items:center;}}
.nav-links a{{color:var(--muted);text-decoration:none;font-size:0.875rem;transition:color 0.2s;}}
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
.art{{background:var(--bg2);border:1px solid var(--border);border-radius:14px;padding:1.5rem;text-decoration:none;color:inherit;transition:transform 0.2s,border-color 0.2s;display:block;}}
.art:hover{{transform:translateY(-4px);border-color:{color}55;}}
.art-meta{{display:flex;gap:1rem;margin-bottom:0.85rem;font-size:0.75rem;color:var(--muted);}}
.art-title{{font-family:'Space Grotesk',sans-serif;font-size:1.1rem;font-weight:600;line-height:1.4;margin-bottom:1rem;color:var(--text);}}
.art-link{{font-size:0.82rem;color:{color};font-weight:600;}}
.empty{{text-align:center;padding:4rem 2rem;background:var(--bg2);border:1px solid var(--border);border-radius:20px;max-width:560px;margin:0 auto;}}
.empty-emoji{{font-size:3rem;margin-bottom:1rem;}}
.empty h3{{font-family:'Space Grotesk',sans-serif;font-size:1.3rem;margin-bottom:0.75rem;}}
.empty p{{color:var(--muted);margin-bottom:1.5rem;line-height:1.7;}}
.btn{{display:inline-block;background:var(--accent);color:#fff;padding:0.8rem 2rem;border-radius:10px;text-decoration:none;font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:0.9rem;}}
.other-chapters{{margin-top:4rem;padding-top:3rem;border-top:1px solid var(--border);}}
.oc-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:0.75rem;margin-top:1.5rem;}}
.oc{{display:flex;align-items:center;gap:0.6rem;background:var(--bg2);border:1px solid var(--border);border-radius:10px;padding:0.85rem 1rem;text-decoration:none;color:var(--sub);font-size:0.875rem;transition:border-color 0.2s,color 0.2s;}}
.oc:hover{{border-color:rgba(255,255,255,0.2);color:var(--text);}}
footer{{border-top:1px solid var(--border);padding:2.5rem 2rem;text-align:center;color:var(--muted);font-size:0.875rem;}}
.fl{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.1rem;color:var(--text);margin-bottom:0.5rem;}}
.fl span{{color:#FF6B35;}}
.flinks{{display:flex;gap:1.5rem;justify-content:center;margin-top:0.75rem;flex-wrap:wrap;}}
.flinks a{{color:var(--muted);text-decoration:none;}}
.flinks a:hover{{color:#FF6B35;}}
@media(max-width:640px){{nav{{padding:0 1.25rem;}}.nav-links a:not(.logo){{display:none;}}.hero,.content{{padding-left:1.25rem;padding-right:1.25rem;}}.art-list{{grid-template-columns:1fr;}}}}
</style>
</head>
<body>
<nav>
  <a href="/" class="logo">IT<span>Vedas</span></a>
  <div class="nav-links">
    <a href="/">Home</a>
    <a href="/news.html">📰 News</a>
    <a href="/#chapters">All Chapters</a>
    <a href="mailto:info@itvedas.com">Contact</a>
  </div>
</nav>

<div class="hero">
  <div class="hero-glow"></div>
  <div class="breadcrumb"><a href="/">Home</a> › <a href="/#chapters">Chapters</a> › {ch['name']}</div>
  <div class="ch-icon">{ch['emoji']}</div>
  <div class="ch-num">Chapter {ch['num']} · {ch['name']}</div>
  <h1>{ch['title']}</h1>
  <p>{ch['desc']}</p>
  <div class="tags">{tags_html}</div>
</div>

<div class="content">
  <div class="section-label">{ch['name']} Articles</div>
  <h2 class="section-h">{"All guides in this chapter" if articles else "This chapter is just getting started"}</h2>
  {article_section}

  <div class="other-chapters">
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
  <div class="flinks"><a href="/">Home</a><a href="/news.html">News</a><a href="/#chapters">Chapters</a><a href="mailto:info@itvedas.com">Contact</a></div>
  <p style="margin-top:1rem;">© {datetime.date.today().year} ITVedas · Knowledge for everyone</p>
</footer>
</body>
</html>"""

def build_all_chapters():
    """Build all 8 chapter landing pages. Call from brain after publishing."""
    published = load_published()
    for slug, ch in CHAPTERS.items():
        arts = articles_for_chapter(slug, published)
        page = build_chapter_page(slug, ch, arts)
        chapter_dir = pathlib.Path("articles") / slug
        chapter_dir.mkdir(parents=True, exist_ok=True)
        (chapter_dir / "index.html").write_text(page, encoding="utf-8")
        print(f"Built /articles/{slug}/ ({len(arts)} articles)")

if __name__ == "__main__":
    build_all_chapters()
    print("All chapter pages built.")
