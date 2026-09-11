#!/usr/bin/env python3
"""Generate sitemap.xml from indexable HTML pages."""
import pathlib, datetime, re, xml.etree.ElementTree as ET
SITE_URL='https://www.itvedas.com'; ROOT=pathlib.Path('.')

def indexable(path):
    try: raw=path.read_text(encoding='utf-8',errors='ignore')
    except Exception: return True
    m=re.search(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\']([^"\']+)',raw,re.I)
    return not (m and 'noindex' in m.group(1).lower())

def get_html_files():
    files={'main':[],'chapters':[],'articles':[],'news':[],'chapter_content':[],'chapter_hubs':[],'manageengine':[],'tools':[]}
    for f in ROOT.glob('*.html'):
        if f.name not in ['cve-database.html','cve-database-complete.html','index.html','404.html'] and indexable(f): files['main'].append(f)
    for d in (ROOT/'articles').glob('*/'):
        if d.is_dir() and (d/'index.html').exists() and indexable(d/'index.html'): files['chapters'].append(d/'index.html')
    for f in (ROOT/'articles').rglob('*.html'):
        if f.name!='index.html' and indexable(f): files['articles'].append(f)
    for d in (ROOT/'chapters').glob('*/'):
        if d.is_dir() and (d/'index.html').exists() and indexable(d/'index.html'): files['chapter_hubs'].append(d/'index.html')
    for f in (ROOT/'chapters').rglob('*.html'):
        if f.name!='index.html' and indexable(f): files['chapter_content'].append(f)
    for f in (ROOT/'news').rglob('*.html'):
        if f.name!='index.html' and indexable(f): files['news'].append(f)
    d=ROOT/'manageengine'
    if d.is_dir(): files['manageengine']=[f for f in d.glob('*.html') if indexable(f)]
    d=ROOT/'tools'
    if d.is_dir(): files['tools']=[f for f in d.glob('*.html') if indexable(f)]
    return files

def url(f):
    r=f.relative_to(ROOT).as_posix()
    if r=='index.html': r=''
    elif r.endswith('/index.html'): r=r[:-10]
    elif r.endswith('.html'): r=r[:-5]
    return f'{SITE_URL}/{r}'
def modified(f): return datetime.datetime.fromtimestamp(f.stat().st_mtime).date().isoformat()
def build():
    files=get_html_files(); today=datetime.date.today().isoformat(); root=ET.Element('urlset',{'xmlns':'http://www.sitemaps.org/schemas/sitemap/0.9'})
    def add(f,freq,prio):
        u=ET.SubElement(root,'url'); ET.SubElement(u,'loc').text=url(f); ET.SubElement(u,'lastmod').text=modified(f); ET.SubElement(u,'changefreq').text=freq; ET.SubElement(u,'priority').text=str(prio)
    ET.SubElement(root,'url')
    root.remove(root[-1]); u=ET.SubElement(root,'url'); ET.SubElement(u,'loc').text=SITE_URL; ET.SubElement(u,'lastmod').text=today; ET.SubElement(u,'changefreq').text='weekly'; ET.SubElement(u,'priority').text='1.0'
    priority={'news.html':(.9,'daily'),'security-news.html':(.9,'daily'),'career-paths.html':(.8,'monthly'),'career-navigator.html':(.8,'monthly'),'chapters.html':(.8,'weekly'),'quiz.html':(.7,'monthly'),'faq.html':(.7,'weekly'),'problems-solutions.html':(.7,'monthly')}
    for f in sorted(files['main']): p,fr=priority.get(f.name,(.6,'monthly')); add(f,fr,p)
    for key,fr,p in [('chapters','weekly',.7),('chapter_hubs','weekly',.8),('chapter_content','monthly',.7),('articles','monthly',.8),('news','weekly',.7),('manageengine','monthly',.6),('tools','monthly',.7)]:
        for f in sorted(files[key]): add(f,fr,p)
    ET.indent(root,space='  '); ET.ElementTree(root).write(ROOT/'sitemap.xml',encoding='utf-8',xml_declaration=True)
    total=sum(map(len,files.values()))+1
    print(f'Sitemap generated: {total} indexable URLs (noindex pages excluded)')
    for k,v in files.items(): print(f'  - {k}: {len(v)}')
    return total
if __name__=='__main__':
    try: build()
    except Exception as e: print(f'Error generating sitemap: {e}'); raise
