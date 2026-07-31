#!/usr/bin/env python3
"""Regenerates faq.html from itvedas-brain/knowledge/faq.json.

Run after any refresh-repository-memory.yml update so the on-site FAQ
page stays in sync with the knowledge base instead of drifting.
"""
import json
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FAQ_JSON = ROOT / "itvedas-brain" / "knowledge" / "faq.json"
OUT = ROOT / "faq.html"

CHAPTER_META = {
    "networking": ("🌐", "Networking", "var(--net)"),
    "cloud": ("☁️", "Cloud", "var(--cld)"),
    "security": ("🔐", "Security", "var(--sec)"),
    "devops": ("⚙️", "DevOps", "var(--dev)"),
    "databases": ("🗄️", "Databases", "var(--db)"),
    "linux": ("🐧", "Linux & OS", "var(--os)"),
    "hardware": ("🖥️", "Hardware", "var(--hw)"),
    "compliance": ("📋", "Compliance", "var(--comp)"),
}


def build():
    data = json.loads(FAQ_JSON.read_text())
    items = data["items"]

    groups = {}
    for item in items:
        chapter = item.get("related_course_id", "other")
        groups.setdefault(chapter, []).append(item)

    schema_entities = [
        {
            "@type": "Question",
            "name": item["question"],
            "acceptedAnswer": {"@type": "Answer", "text": item["answer"]},
        }
        for item in items
    ]

    sections_html = []
    chips_html = []
    for chapter, group_items in groups.items():
        emoji, label, color = CHAPTER_META.get(chapter, ("❓", chapter.title(), "var(--net)"))
        chips_html.append(f'<a href="#{chapter}" class="chip" style="border-color:{color};">{emoji} {label}</a>')
        qa_html = "\n".join(
            f"""    <div class="qa">
      <h3 class="q">{html.escape(item['question'])}</h3>
      <p class="a">{html.escape(item['answer'])}</p>
    </div>"""
            for item in group_items
        )
        sections_html.append(
            f"""  <section id="{chapter}" class="faq-group">
    <h2><span class="chip-icon" style="color:{color};">{emoji}</span> {label}</h2>
{qa_html}
  </section>"""
        )

    page = TEMPLATE.format(
        chips="\n    ".join(chips_html),
        sections="\n\n".join(sections_html),
        schema_json=json.dumps(
            {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": schema_entities,
            },
            ensure_ascii=False,
        ),
    )
    OUT.write_text(page)
    print(f"Wrote {OUT} with {len(items)} FAQs across {len(groups)} chapters")


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-D98BFZSJYP"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-D98BFZSJYP');</script>
<meta name="description" content="Frequently asked questions about networking, cloud, security, DevOps, databases, Linux and hardware — answered in plain English by ITVedas.">
<meta name="keywords" content="IT FAQ, networking FAQ, cloud FAQ, security FAQ, DevOps FAQ">
<meta name="robots" content="index,follow">
<meta property="og:title" content="FAQ — ITVedas">
<meta property="og:description" content="Quick answers to common IT questions across networking, cloud, security, DevOps, databases, Linux and hardware.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://itvedas.com/faq.html">
<link rel="canonical" href="https://itvedas.com/faq.html">
<title>FAQ — ITVedas</title>
<script type="application/ld+json">
{schema_json}
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{
  --bg:#EEF3FC;--bg2:#FFFFFF;--bg3:#F7F9FD;--text:#182238;--muted:#6B7A94;--sub:#4A5568;
  --net:#FF6B35;--cld:#3B82F6;--sec:#10B981;--dev:#8B5CF6;--db:#F59E0B;--os:#EF4444;--hw:#06B6D4;--comp:#EC4899;
  --border:rgba(24,34,56,0.12);--fd:'Space Grotesk',sans-serif;--fb:'Inter',sans-serif;
}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
html{{scroll-behavior:smooth;}}
body{{background:var(--bg);color:var(--text);font-family:var(--fb);font-size:17px;line-height:1.8;-webkit-font-smoothing:antialiased;}}
nav{{position:fixed;top:0;left:0;right:0;z-index:100;display:flex;align-items:center;justify-content:space-between;padding:0 2rem;height:64px;background:rgba(255,255,255,0.88);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);}}
.logo{{font-family:var(--fd);font-weight:700;font-size:1.3rem;color:var(--text);text-decoration:none;letter-spacing:-0.02em;}}
.logo span{{color:var(--net);}}
.nav-links{{display:flex;gap:1.5rem;align-items:center;list-style:none;}}
.nav-links a{{color:var(--muted);text-decoration:none;font-size:0.875rem;transition:color .2s;}}
.nav-links a:hover,.nav-links a.active{{color:var(--text);}}
.hero{{padding:8rem 2rem 3rem;max-width:820px;margin:0 auto;position:relative;}}
.hero-glow{{position:absolute;top:5rem;left:50%;transform:translateX(-50%);width:700px;height:380px;background:radial-gradient(ellipse,rgba(255,107,53,0.10),transparent 70%);pointer-events:none;}}
.eyebrow{{display:inline-block;font-size:0.72rem;font-weight:700;letter-spacing:0.14em;text-transform:uppercase;color:var(--net);margin-bottom:1.25rem;position:relative;}}
.hero h1{{font-family:var(--fd);font-size:clamp(2.2rem,5vw,3.5rem);font-weight:700;letter-spacing:-0.03em;line-height:1.08;margin-bottom:1.5rem;position:relative;}}
.lead{{font-size:1.2rem;color:var(--sub);line-height:1.75;position:relative;}}
.content{{max-width:820px;margin:0 auto;padding:1rem 2rem 4rem;}}
.chips{{display:flex;flex-wrap:wrap;gap:0.6rem;margin:1.5rem 0 0.5rem;}}
.chip{{display:inline-flex;align-items:center;gap:0.45rem;background:var(--bg2);border:1px solid var(--border);border-radius:100px;padding:0.45rem 1rem;font-size:0.85rem;color:var(--sub);text-decoration:none;transition:border-color .2s,transform .2s;}}
.chip:hover{{transform:translateY(-2px);}}
.faq-group{{margin-top:3rem;}}
.faq-group h2{{font-family:var(--fd);font-size:1.5rem;font-weight:700;letter-spacing:-0.02em;margin-bottom:1.25rem;display:flex;align-items:center;gap:0.6rem;}}
.chip-icon{{font-size:1.3rem;}}
.qa{{background:var(--bg2);border:1px solid var(--border);border-radius:14px;padding:1.25rem 1.5rem;margin-bottom:0.85rem;}}
.q{{font-family:var(--fd);font-size:1rem;font-weight:600;margin-bottom:0.5rem;}}
.a{{color:var(--sub);font-size:0.95rem;margin:0;}}
footer{{border-top:1px solid var(--border);padding:3rem 2rem 2rem;text-align:center;color:var(--muted);font-size:0.875rem;}}
.fl{{font-family:var(--fd);font-weight:700;font-size:1.2rem;color:var(--text);margin-bottom:0.5rem;}}
.fl span{{color:var(--net);}}
.flinks{{display:flex;gap:1.75rem;justify-content:center;margin:0.75rem 0;flex-wrap:wrap;}}
.flinks a{{color:var(--muted);text-decoration:none;transition:color .2s;}}
.flinks a:hover{{color:var(--net);}}
@media(max-width:640px){{
  nav{{padding:0 1.25rem;}}
  .nav-links{{gap:1rem;}}
  .nav-links a:not(.active){{display:none;}}
  .hero,.content{{padding-left:1.25rem;padding-right:1.25rem;}}
}}
</style>
</head>
<body>
<nav>
  <a href="/" class="logo">IT<span>Vedas</span></a>
  <ul class="nav-links">
    <li><a href="/">Home</a></li>
    <li><a href="/news.html">📰 News</a></li>
    <li><a href="/security-news.html" style="color:#10B981">🛡️ Security</a></li>
    <li><a href="/#chapters">Chapters</a></li>
    <li><a href="/career-paths.html">Career Paths</a></li>
    <li><a href="/faq.html" class="active">FAQ</a></li>
    <li><a href="/about.html">About</a></li>
  </ul>
</nav>

<section class="hero">
  <div class="hero-glow"></div>
  <div class="eyebrow">Frequently Asked Questions</div>
  <h1>Quick answers, no jargon</h1>
  <p class="lead">Common questions from across our networking, cloud, security, DevOps, databases, Linux and hardware guides — answered in plain English. Generated automatically from our published content.</p>
  <div class="chips">
    {chips}
  </div>
</section>

<div class="content">
{sections}
</div>

<footer>
  <div class="fl">IT<span>Vedas</span></div>
  <p>The complete IT knowledge hub — explained simply, for everyone.</p>
  <div class="flinks">
    <a href="/">Home</a>
    <a href="/news.html">News</a>
    <a href="/#chapters">Chapters</a>
    <a href="/career-paths.html">Career Paths</a>
    <a href="/faq.html">FAQ</a>
    <a href="/about.html">About</a>
  </div>
  <p style="margin-top:1rem;">© 2026 ITVedas · Knowledge for everyone</p>
</footer>

<script src="/js/nav-search.js" defer></script>
<script src="/js/nav-mobile.js" defer></script>
</body>
</html>
"""

if __name__ == "__main__":
    build()
