"""Public RSS/Atom discovery. No credentials, article scraping or invented deal facts."""
import argparse, concurrent.futures, datetime as dt, email.utils, hashlib, html, json, os, re, sys, time
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo
ROOT = Path(__file__).resolve().parents[1]
UTC = dt.timezone.utc
MAX_BYTES = 5_000_000

def read(path, default):
    return json.loads(path.read_text()) if path.exists() else default

def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    tmp.replace(path)

def clean(value):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', value or ''))).strip()

def canonical(url):
    p = urlsplit(url.strip())
    if p.scheme not in ('https', 'http') or not p.hostname or p.username or p.password:
        raise ValueError('Expected public HTTP(S) URL')
    q = [(k,v) for k,v in parse_qsl(p.query) if not k.lower().startswith('utm_') and k not in ('fbclid','gclid')]
    return urlunsplit((p.scheme, p.netloc.lower(), p.path.rstrip('/'), urlencode(sorted(q)), ''))

def parsedate(value):
    if not value: return None
    try:
        d = email.utils.parsedate_to_datetime(value)
    except (ValueError, TypeError):
        try: d = dt.datetime.fromisoformat(value.replace('Z','+00:00'))
        except ValueError: return None
    if not d.tzinfo: d = d.replace(tzinfo=UTC)
    return d.astimezone(UTC).isoformat()

def classify(title, source):
    t = title.lower()
    innovation = bool(re.search(r'automat|electrif|digital twin|hydrogen|shore power|robot|autonom|battery|decarbon|innovation|人工智能|数字孪生', t))
    deal = bool(re.search(r'acquir|acquis|invest|concession|financ|stake|loan|merger|buyout|sale|divest|fund|收购|投资|استثمار|تمويل', t))
    kind = 'Innovation' if innovation else 'Deal lead' if deal else 'Industry'
    sector = source.get('sector','Infrastructure')
    if re.search(r'\bport\b|ports|terminal|puerto|hafen|porto|ميناء|موانئ|港口',t): sector='Ports & logistics'
    if re.search(r'data cent(?:er|re)|fibre|fiber|telecom|数据中心',t): sector='Digital infrastructure'
    score = 40 + (25 if sector=='Ports & logistics' else 0) + (15 if deal else 0) + (10 if innovation else 0) + (5 if source.get('primary') else 0)
    return kind, sector, min(score,99)

def parse_feed(body, source, now):
    root = ET.fromstring(body)
    entries = root.findall('.//item') + root.findall('.//{http://www.w3.org/2005/Atom}entry')
    if not entries and root.tag.split('}')[-1] not in ('rss','feed','RDF'): raise ValueError('Response is not RSS/Atom')
    rows=[]
    for item in entries[:100]:
        def val(name):
            el=item.find(name)
            if el is None: el=item.find('{http://www.w3.org/2005/Atom}'+name)
            return ''.join(el.itertext()).strip() if el is not None else ''
        title=clean(val('title'))
        link=val('link')
        if not link:
            for el in item.findall('{http://www.w3.org/2005/Atom}link'):
                if el.get('rel','alternate')=='alternate': link=el.get('href',''); break
        try: link=canonical(link)
        except ValueError: continue
        if not title: continue
        published=parsedate(val('pubDate') or val('published') or val('updated'))
        # Preserve unknown dates, exclude future-dated and old discovery items.
        if published:
            age=(now-dt.datetime.fromisoformat(published)).total_seconds()/86400
            if age < -1 or age > 45: continue
        publisher=clean(val('source')) or source['name']
        # Google News appends the publisher, which must not become a technology keyword.
        suffix=' - '+publisher
        if title.endswith(suffix): title=title[:-len(suffix)].strip()
        kind,sector,score=classify(title,source)
        rows.append({'id':hashlib.sha256(link.encode()).hexdigest()[:20], 'title':title[:400], 'url':link,
            'publishedAt':published, 'firstSeen':now.isoformat(), 'lastSeen':now.isoformat(),
            'publisher':publisher, 'channels':[source['id']], 'region':source.get('region','Global'),
            'sector':sector,'kind':kind,'score':score,'evidence':'Feed lead — not independently verified',
            'primaryFeed':source.get('primary',False), 'status':'Unverified', 'value':None})
    return rows

def fetch(source, now):
    last=None
    for attempt in range(3):
        try:
            req=Request(source['url'],headers={'User-Agent':'PoseidonIntelligence/1.0 (+public RSS research; github.com/wassimibrahim/laith)', 'Accept':'application/rss+xml, application/atom+xml, application/xml, text/xml'})
            with urlopen(req,timeout=22) as response:
                body=response.read(MAX_BYTES+1)
                if len(body)>MAX_BYTES: raise ValueError('Feed exceeds size limit')
            items=parse_feed(body,source,now)
            return items, {**source,'state':'ok','count':len(items),'checkedAt':now.isoformat(),'error':None}
        except Exception as exc:
            last=f'{type(exc).__name__}: {exc}'[:240]
            if attempt<2: time.sleep(1+attempt)
    return [], {**source,'state':'error','count':0,'checkedAt':now.isoformat(),'error':last}

def merge(existing, new):
    by_url={canonical(x['url']):dict(x) for x in existing}
    # Exact normalized titles collapse syndication, but distinct follow-up headlines remain separate.
    title_urls={clean(x['title']).casefold():url for url,x in by_url.items()}
    for row in new:
        url=canonical(row['url'])
        key=url if url in by_url else title_urls.get(clean(row['title']).casefold(),url)
        if key in by_url:
            old=by_url[key]
            old['lastSeen']=row['lastSeen']
            for field in ('title','kind','sector','score'):
                if field in row: old[field]=row[field]
            old['channels']=sorted(set(old.get('channels',[])+row.get('channels',[])))
        else:
            by_url[key]=row
            title_urls[clean(row['title']).casefold()]=key
    return sorted(by_url.values(),key=lambda x:x.get('publishedAt') or x['firstSeen'],reverse=True)

def finance_lens(row):
    """Transparent educational prompts; no financial facts inferred."""
    sector=row.get('sector','Infrastructure')
    lenses={
      'Ports & logistics': 'Translate throughput and tariffs into revenue; test concession life, maintenance capex, customer concentration and debt coverage.',
      'Digital infrastructure': 'Separate operating from contracted future EBITDA; test power availability, remaining construction capex and tenant concentration.',
      'Energy transition': 'Separate contracted from merchant revenue; test resource, curtailment, construction, counterparty and refinancing risks.',
      'Transport': 'Test traffic and tariff assumptions, concession expiry, maintenance obligations and demand sensitivity.',
      'Utilities': 'Identify regulated versus contracted income, allowed returns, customer growth, maintenance needs and the funding gap.',
      'Infrastructure': 'Identify the asset perimeter, transaction stage, enterprise versus equity value, capital structure and cash-flow duration.'
    }
    return lenses.get(sector,lenses['Infrastructure'])

def make_report(rows, health, now):
    day=now.astimezone(ZoneInfo('Europe/Madrid')).date().isoformat()
    fresh=[x for x in rows if x.get('publishedAt') and 0 <= (now-dt.datetime.fromisoformat(x['publishedAt'])).total_seconds() <= 86400]
    new=[x for x in rows if dt.datetime.fromisoformat(x['firstSeen']).astimezone(ZoneInfo('Europe/Madrid')).date().isoformat()==day]
    ranked=sorted(fresh,key=lambda x:x['score'],reverse=True)
    report={'date':day,'generatedAt':now.isoformat(),'published24h':len(fresh),'discoveredToday':len(new),
      'sourceSuccess':sum(x['state']=='ok' for x in health),'sourceTotal':len(health),
      'topIds':[x['id'] for x in ranked[:20]], 'caseIndex':int(now.strftime('%j'))%6,
      'note':'Automated headline screening. These are research leads, not a verified census of transactions. Rankings use sector and keyword relevance; they are not confidence scores.'}
    lines=[f'# Poseidon | {day}', '',report['note'],'', f"Collection: {report['sourceSuccess']}/{len(health)} channels responding. {len(fresh)} items published in the last 24 hours.",'','## Today’s research queue','']
    if not ranked: lines.append('No dated items published in the last 24 hours were collected. Check coverage; older items remain in the archive.')
    for x in ranked[:20]:
        lines.extend([f"- [{x['title']}]({x['url']}) — {x['publisher']} | {x['sector']} | {x['evidence']}"])
    lines+=['','## Sector map (last 24 hours)','']
    for sector in sorted({x['sector'] for x in fresh}):
        group=[x for x in fresh if x['sector']==sector]
        lines.append(f"- {sector}: {len(group)} headlines. Finance lens: {finance_lens(group[0])}")
    reviewed=read(ROOT/'data/curated.json',[])
    lines+=['','## Reviewed primary-source context','']
    for x in sorted(reviewed,key=lambda x:x['publishedAt'],reverse=True)[:5]:
        lines += [f"### {x['title']}",f"Source date: {x['publishedAt']} | Review: {x['verifiedAt']} | Stage at source date: {x['status']}",'',*['- '+f for f in x['facts']],f"\nSource: [{x['publisher']}]({x['url']})",f"\nAnalytical interpretation: {x['analysis']}",f"\nUndisclosed / to verify: {', '.join(x['unknown'])}.",'']
    lines+=['','## Interview drill','','Pick one announcement. Identify what is being purchased or financed, the stage of the transaction, the value basis, the cash-flow drivers, and two undisclosed inputs. Never treat a project budget as an acquisition enterprise value.','','## Coverage gaps','']
    lines += [f"- {x['name']}: {x['error']}" for x in health if x['state']=='error'] or ['All configured channels responded; this does not establish exhaustive market coverage.']
    lines+=['','## Full 24-hour headline register','', 'This includes potential duplicates, false positives and unverified leads. Multiple headlines may describe one transaction.','']
    for x in sorted(fresh,key=lambda x:x.get('publishedAt') or '',reverse=True):
        lines.append(f"- [{x['title']}]({x['url']}) — {x['publisher']} | {x['sector']}")
    path=ROOT/'reports'/f'{day}.md'; path.write_text('\n'.join(lines)+'\n')
    atomic(ROOT/'data/daily.json',report)
    index=read(ROOT/'data/report-index.json',[])
    index=[x for x in index if x['date']!=day]+[{'date':day,'path':f'reports/{day}.md'}]
    atomic(ROOT/'data/report-index.json',sorted(index,key=lambda x:x['date'],reverse=True))

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--limit',type=int); args=parser.parse_args()
    now=dt.datetime.now(UTC)
    sources=[s for s in read(ROOT/'data/sources.json',[]) if s.get('enabled',True)]
    if args.limit: sources=sources[:args.limit]
    rows=[]; health=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for items,status in pool.map(lambda s:fetch(s,now),sources):
            rows.extend(items); health.append(status)
            print(f"{status['state']:5} {status['name']}: {len(items)} items",flush=True)
    existing=read(ROOT/'data/feed.json',[])
    merged=merge(existing,rows)
    atomic(ROOT/'data/health.json',{'checkedAt':now.isoformat(),'sources':health,'successful':sum(x['state']=='ok' for x in health),'total':len(health)})
    if rows: atomic(ROOT/'data/feed.json',merged)
    elif not (ROOT/'data/feed.json').exists(): atomic(ROOT/'data/feed.json',[])
    make_report(merged,health,now)
    if not any(x['state']=='ok' for x in health):
        print('All sources failed. Previous records retained.',file=sys.stderr); return 2
    print(f'{len(rows)} observations; {len(merged)} unique archive items.')
    return 0
if __name__=='__main__': sys.exit(main())
