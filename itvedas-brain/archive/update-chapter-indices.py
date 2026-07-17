#!/usr/bin/env python3
"""Update chapter index pages with newly generated articles"""
from pathlib import Path
from datetime import datetime
import os

CHAPTERS_DIR = Path("/home/user/itvedas/chapters")

def get_chapter_articles(chapter_name):
    """Get all articles in a chapter"""
    chapter_dir = CHAPTERS_DIR / chapter_name
    if not chapter_dir.exists():
        return []
    
    articles = []
    for html_file in sorted(chapter_dir.glob("*.html")):
        if html_file.name != "index.html":
            # Extract title from HTML
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract title
                import re
                title_match = re.search(r'<h1[^>]*>([^<]+)<', content)
                title = title_match.group(1) if title_match else "Article"
                
                # Extract meta info
                difficulty_match = re.search(r'<span class="badge">(\w+)<', content)
                difficulty = difficulty_match.group(1) if difficulty_match else "Intermediate"
                
                reading_time_match = re.search(r'(\d+) min read', content)
                reading_time = reading_time_match.group(1) if reading_time_match else "10"
                
                date_str = html_file.stem.split('-', 1)[0]
                try:
                    date_obj = datetime.strptime(date_str, "%Y%m%d")
                except ValueError:
                    date_obj = datetime.now()
                
                articles.append({
                    "filename": html_file.name,
                    "title": title,
                    "difficulty": difficulty,
                    "reading_time": reading_time,
                    "date": date_obj,
                    "path": f"/chapters/{chapter_name}/{html_file.name}"
                })
    
    return sorted(articles, key=lambda x: x["date"], reverse=True)

def generate_index_html(chapter_name, title, description):
    """Generate chapter index HTML"""
    
    articles = get_chapter_articles(chapter_name)
    article_count = len(articles)
    
    # Generate articles list HTML
    articles_html = ""
    for article in articles:
        articles_html += f'''    <li><a href="{article['path']}"><span class="icon"><svg viewBox="0 0 24 24"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/></svg></span><span class="info"><span class="title">{article['title']}</span><span class="meta">{article['date'].strftime('%b %d, %Y')} &middot; {article['reading_time']} min</span></span><span class="arrow">&#8250;</span></a></li>
'''
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — ITVedas</title>
<meta name="description" content="{description}">
<meta property="og:title" content="{title} — ITVedas">
<meta property="og:description" content="{description}">
<meta property="og:type" content="website">
<meta property="og:url" content="https://itvedas.com/chapters/{chapter_name}/">
<link rel="canonical" href="https://itvedas.com/chapters/{chapter_name}/">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-D98BFZSJYP"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-D98BFZSJYP');</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{--bg:#0A0A0F;--card:#13131A;--orange:#FF6B35;--text:#E2E8F0;--muted:#94A3B8;--border:#1E1E2E}}
body{{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;line-height:1.6}}
nav{{background:#0D0D14;border-bottom:1px solid var(--border);padding:0 2rem;display:flex;align-items:center;gap:2rem;height:60px;position:sticky;top:0;z-index:100}}
nav a{{color:var(--muted);text-decoration:none;font-size:.9rem;transition:color .2s}}
nav a:hover,nav a.active{{color:var(--orange)}}
nav .brand{{color:var(--text);font-weight:700;font-size:1.1rem;margin-right:auto}}
.hero{{background:linear-gradient(135deg,#0D0D14 0%,#12121F 100%);border-bottom:1px solid var(--border);padding:3rem 2rem}}
.hero-inner{{max-width:860px;margin:0 auto}}
.breadcrumb{{font-size:.8rem;color:var(--muted);margin-bottom:1rem}}
.breadcrumb a{{color:var(--muted);text-decoration:none}}
.breadcrumb a:hover{{color:var(--orange)}}
h1{{font-size:2rem;font-weight:800;line-height:1.2;margin-bottom:.75rem}}
.hero-desc{{color:var(--muted);max-width:600px;font-size:1rem}}
main{{max-width:860px;margin:0 auto;padding:2rem}}
.section-header{{display:flex;align-items:center;justify-content:space-between;margin-bottom:1.5rem}}
.section-header h2{{font-size:1.1rem;font-weight:700;color:var(--text)}}
.count{{background:var(--card);border:1px solid var(--border);color:var(--muted);font-size:.75rem;padding:.2rem .6rem;border-radius:12px}}
ul#article-list{{list-style:none;display:grid;gap:.75rem}}
ul#article-list li a{{display:flex;align-items:center;gap:1rem;background:var(--card);border:1px solid var(--border);border-radius:10px;padding:1rem 1.25rem;text-decoration:none;color:var(--text);transition:border-color .2s,transform .15s}}
ul#article-list li a:hover{{border-color:var(--orange);transform:translateX(3px)}}
ul#article-list li a .icon{{width:36px;height:36px;background:rgba(255,107,53,.1);border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0}}
ul#article-list li a .icon svg{{width:18px;height:18px;stroke:var(--orange);fill:none;stroke-width:2}}
ul#article-list li a .info{{flex:1;min-width:0}}
ul#article-list li a .info .title{{font-size:.95rem;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
ul#article-list li a .info .meta{{font-size:.75rem;color:var(--muted);margin-top:.2rem}}
.arrow{{color:var(--muted);font-size:.8rem;flex-shrink:0}}
footer{{text-align:center;padding:3rem 2rem;color:var(--muted);font-size:.85rem;border-top:1px solid var(--border);margin-top:3rem}}
footer a{{color:var(--orange);text-decoration:none}}
</style>
</head>
<body>
<nav>
  <span class="brand"><a href="/" style="color:inherit;text-decoration:none">ITVedas</a></span>
  <a href="/chapters/networking/">Networking</a>
  <a href="/chapters/security/">Security</a>
  <a href="/chapters/cloud/">Cloud</a>
  <a href="/chapters/devops/">DevOps</a>
  <a href="/chapters/databases/">Databases</a>
  <a href="/chapters/linux/">Linux</a>
</nav>
<div class="hero">
  <div class="hero-inner">
    <div class="breadcrumb"><a href="/">Home</a> / Chapters / {chapter_name.replace('-', ' ').title()}</div>
    <h1>{title}</h1>
    <p class="hero-desc">{description}</p>
  </div>
</div>
<main>
  <div class="section-header">
    <h2>All Articles</h2>
    <span class="count">{article_count} articles</span>
  </div>
  <ul id="article-list">
{articles_html}  </ul>
</main>
<footer>
  <p>&copy; 2026 <a href="/">ITVedas</a> &mdash; IT Education for Everyone</p>
</footer>
</body>
</html>'''
    
    return html

def main():
    """Update all chapter indices"""
    
    chapters = [
        ("microsoft-365", "Microsoft 365 Enterprise Management", "Teams, SharePoint, Exchange governance and security at enterprise scale"),
        ("azure-certifications", "Azure Certification Paths", "Study guides for AZ-900, AZ-104, AZ-305 and Azure certifications"),
        ("cloud-security", "Advanced Cloud Security", "Defense in depth, threat modeling, compliance frameworks, incident response"),
        ("hybrid-multicloud", "Hybrid & Multi-Cloud Architecture", "Hybrid integration patterns, multi-cloud strategy, cross-platform operations"),
        ("aiml-operations", "AI/ML Operations", "MLOps, Azure ML, responsible AI, production machine learning"),
    ]
    
    print("Updating Chapter Index Pages...")
    print("=" * 60)
    
    for chapter_name, title, description in chapters:
        chapter_dir = CHAPTERS_DIR / chapter_name
        chapter_dir.mkdir(parents=True, exist_ok=True)
        
        html = generate_index_html(chapter_name, title, description)
        
        index_path = chapter_dir / "index.html"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        article_count = len(get_chapter_articles(chapter_name))
        print(f"✓ {chapter_name}: {article_count} articles")
    
    print("=" * 60)
    print("Chapter indices updated successfully!")

if __name__ == "__main__":
    main()
