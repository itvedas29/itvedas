#!/usr/bin/env python3
"""Unified, idempotent CVE sync for ITVedas.

NVD is the canonical CVE record source. CISA KEV is the authoritative
known-exploited flag. GitHub Global Security Advisories are supplemental
references. Existing CVEs are replaced when NVD's lastModified changes.
"""
import json, os, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
import requests

NVD='https://services.nvd.nist.gov/rest/json/cves/2.0'
KEV='https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json'
GHA='https://api.github.com/security-advisories'
DB=Path('cve-database-full.json'); REPORT=Path('cve-ingestion-report.json'); CHECKPOINT=Path('.cve_last_sync')
HEADERS={'Accept':'application/json'}

def now(): return datetime.now(timezone.utc)
def get(url, params=None, headers=None):
    for attempt in range(4):
        r=requests.get(url, params=params, headers=headers or HEADERS, timeout=30)
        if r.status_code==200: return r.json(), r
        if r.status_code in (429,500,502,503,504): time.sleep(5*(attempt+1)); continue
        r.raise_for_status()
    raise RuntimeError(f'Unable to fetch {url}')

def load():
    if not DB.exists(): return {}
    raw=json.loads(DB.read_text())
    if isinstance(raw,dict): raw=raw.get('cves',[])
    return {x['id']:x for x in raw if isinstance(x,dict) and x.get('id')}

def score(metrics):
    for key in ('cvssMetricV40','cvssMetricV31','cvssMetricV30','cvssMetricV2'):
        vals=metrics.get(key) or []
        if vals:
            try: return float(vals[0].get('cvssData',{}).get('baseScore',0)),key.replace('cvssMetric','')
            except (TypeError,ValueError): pass
    return 0.0,''

def sev(s): return 'Critical' if s>=9 else 'High' if s>=7 else 'Medium' if s>=4 else 'Low'

def normalize(cve, kev):
    cid=cve.get('id',''); desc=next((x.get('value','') for x in cve.get('descriptions',[]) if x.get('lang')=='en'),'')
    s,ver=score(cve.get('metrics',{})); vendors=set(); products=set()
    for cfg in cve.get('configurations',[]):
      for node in cfg.get('nodes',[]):
       for m in node.get('cpeMatch',[]):
        p=m.get('criteria','').split(':')
        if len(p)>=5 and p[0]=='cpe' and p[2]=='2.3': vendors.add(p[3].replace('_',' ').title()); products.add(p[4].replace('_',' ').title())
    cwes=[]
    for w in cve.get('weaknesses',[]):
      for x in w.get('description',[]):
       v=x.get('value');
       if v and v not in cwes: cwes.append(v)
    refs=[x.get('url') for x in cve.get('references',[]) if x.get('url')]
    published=cve.get('published',''); modified=cve.get('lastModified',published)
    year=int(cid.split('-')[1]) if len(cid.split('-'))>1 and cid.split('-')[1].isdigit() else now().year
    return {'id':cid,'name':desc[:100] or cid,'affected':next(iter(vendors),'Unknown'),'affected_products':sorted(products)[:20],
      'year':year,'severity':sev(s),'cvss':round(s,1),'cvss_version':ver,'type':'Security Vulnerability','description':desc[:500] or 'No description available',
      'remediation':'Apply vendor security updates and follow NVD/vendor mitigation guidance.','published_date':published.split('T')[0] if published else now().date().isoformat(),
      'last_modified_date':modified,'cwe':cwes,'known_exploited':cid in kev,'references':refs[:50],'source':'nvd','withdrawn':cve.get('vulnStatus')=='Rejected'}

def main():
    db=load(); before={k:json.dumps(v,sort_keys=True) for k,v in db.items()}
    report={'timestamp':now().isoformat(),'new_cves':[],'updated_cves':[],'kev_updates':[],'github_advisories':0,'errors':[]}
    try: kev={x['cveID'] for x in get(KEV)[0].get('vulnerabilities',[]) if x.get('cveID')}
    except Exception as e: kev={k for k,v in db.items() if v.get('known_exploited')}; report['errors'].append('CISA KEV: '+str(e))
    gh={}
    token=os.getenv('GITHUB_TOKEN')
    if token:
      try:
       page=1
       while True:
        data,resp=get(GHA,{'per_page':100,'page':page},{'Accept':'application/vnd.github+json','Authorization':f'Bearer {token}'})
        for a in data:
         for ident in a.get('identifiers',[]):
          if ident.get('type')=='CVE' and ident.get('value'): gh[ident['value']]={'ghsa':a.get('ghsa_id'),'url':a.get('html_url'),'summary':a.get('summary')}
        if len(data)<100 or 'rel="next"' not in resp.headers.get('Link',''): break
        page+=1
      except Exception as e: report['errors'].append('GitHub advisories: '+str(e))
    report['github_advisories']=len(gh)
    checkpoint=now()-timedelta(hours=2)
    if CHECKPOINT.exists():
      try: checkpoint=datetime.fromisoformat(CHECKPOINT.read_text().strip())-timedelta(hours=2)
      except Exception: pass
    start=0
    while True:
      params={'resultsPerPage':100,'startIndex':start,'lastModStartDate':checkpoint.strftime('%Y-%m-%dT%H:%M:%S.000Z'),'lastModEndDate':now().strftime('%Y-%m-%dT%H:%M:%S.000Z')}
      h={'apiKey':os.getenv('NVD_API_KEY')} if os.getenv('NVD_API_KEY') else HEADERS
      data,_=get(NVD,params,h); items=data.get('vulnerabilities',[])
      for wrap in items:
       item=normalize(wrap.get('cve',{}),kev)
       if not item: continue
       old=db.get(item['id']); adv=gh.get(item['id'])
       if adv: item['github_advisory']=adv; item['references']=list(dict.fromkeys(item['references']+[adv['url']])) if adv.get('url') else item['references']
       db[item['id']]=item
       if old is None: report['new_cves'].append(item['id'])
       elif before.get(item['id'])!=json.dumps(item,sort_keys=True): report['updated_cves'].append(item['id'])
      start+=100
      if start>=int(data.get('totalResults',0)) or not items: break
    for cid,item in db.items():
      flag=cid in kev
      if item.get('known_exploited')!=flag: item['known_exploited']=flag; report['kev_updates'].append(cid)
    ordered=sorted(db.values(),key=lambda x:(-x.get('year',0),x.get('id','')))
    DB.write_text(json.dumps(ordered,indent=2,ensure_ascii=False)+'\n')
    CHECKPOINT.write_text(now().isoformat())
    report['summary']={'total':len(db),'new':len(report['new_cves']),'updated':len(report['updated_cves']),'kev_updates':len(report['kev_updates']),'errors':len(report['errors'])}
    REPORT.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['summary'],indent=2))
    return 1 if report['errors'] else 0
if __name__=='__main__': raise SystemExit(main())
