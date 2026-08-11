#!/usr/bin/env python3
"""Quality gate for generated ITVedas news pages.

Thin or near-duplicate stories are retained for visitors but marked
noindex,follow. Duplicate comparison is chronological by file modification
age so the oldest story in a cluster remains the canonical index candidate.
"""
import datetime, html, json, re
from pathlib import Path
ROOT=Path('news'); REPORT=Path('news-quality-report.json'); MIN_WORDS=350
STOP=set('the a an and or of to in on for with from by is are was were this that as at it its be has have had will can could would should into after before about over under new news update updates latest says said more most how why what when'.split())
def text(s): return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',s))).strip()
def tokens(s): return {w for w in re.findall(r'[a-z0-9]{3,}',s.lower()) if w not in STOP}
def sim(a,b):
    aa,bb=tokens(a),tokens(b); return len(aa&bb)/max(1,len(aa|bb))
def metadata(raw):
    title=re.search(r'<h1[^>]*>(.*?)</h1>',raw,re.I|re.S)
    canonical=re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)',raw,re.I)
    return text(title.group(1)) if title else '', canonical.group(1) if canonical else ''
def set_noindex(path):
    raw=path.read_text(encoding='utf-8',errors='ignore')
    if re.search(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex',raw,re.I): return False
    if re.search(r'<meta[^>]+name=["\']robots["\']',raw,re.I):
        new=re.sub(r'(<meta[^>]+name=["\']robots["\'][^>]+content=["\'])index,follow(["\'])',r'\1noindex,follow\2',raw,count=1,flags=re.I)
    else: new=raw.replace('<head>','<head>\n<meta name="robots" content="noindex,follow">',1)
    if new==raw: return False
    path.write_text(new,encoding='utf-8'); return True
def main():
    pages=[]
    for p in ROOT.rglob('*.html'):
        raw=p.read_text(encoding='utf-8',errors='ignore'); title,canonical=metadata(raw)
        pages.append({'path':p,'title':title,'canonical':canonical,'words':len(text(raw).split()),'mtime':p.stat().st_mtime})
    pages.sort(key=lambda x:x['mtime'])
    changed=[]; thin=[]; duplicate=[]; indexable=[]
    for i,p in enumerate(pages):
        if p['words']<MIN_WORDS:
            thin.append(str(p['path']));
            if set_noindex(p['path']): changed.append(str(p['path']))
            continue
        dup=any((older['words']>=MIN_WORDS and ((p['canonical'] and older['canonical'] and p['canonical']==older['canonical']) or sim(p['title'],older['title'])>=0.78)) for older in pages[:i])
        if dup:
            duplicate.append(str(p['path']));
            if set_noindex(p['path']): changed.append(str(p['path']))
        else: indexable.append(str(p['path']))
    report={'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'total_pages':len(pages),'indexable':len(indexable),'thin':thin,'duplicates':duplicate,'changed':changed,'min_words':MIN_WORDS}
    REPORT.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:(len(v) if isinstance(v,list) else v) for k,v in report.items() if k not in ('timestamp','min_words')},indent=2))
if __name__=='__main__': main()
