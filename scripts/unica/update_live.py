import json,re,urllib.request,hashlib,statistics,math,sys,tempfile,subprocess
from pathlib import Path
from datetime import datetime
import pdfplumber

ROOT=Path(__file__).resolve().parents[2]
DB=ROOT/'data'/'unica-dashboard.json'; STATE=ROOT/'data'/'.unica-update-state.json'
PAGE='https://unicadata.com.br/listagem.php?idMn=63&idioma=2'
UA={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) UNICA-dashboard-updater/1.0'}
def fetch(url): return urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=60).read()
def pnum(s):
 s=s.strip()
 if s.count(',')>1: return float(s.replace(',',''))
 if s.count('.')>1: return float(s.replace('.',''))
 if ',' in s and len(s.rsplit(',',1)[1])==3: return float(s.replace(',',''))
 if '.' in s and len(s.rsplit('.',1)[1])==3: return float(s.replace('.',''))
 return float(s.replace(',','.'))
def pk(s): d,m=s.split('/'); return f'{m}-{d}'
def extract(path):
 with pdfplumber.open(path) as p: texts=[pg.extract_text() or '' for pg in p.pages]
 pages={}
 for i,t in enumerate(texts):
  for n in (6,7,8):
   if re.search(fr'(Tabela|Table)\s+{n}\.',t,re.I): pages[n]=i
 if any(n not in pages for n in (6,7,8)): raise RuntimeError('无法定位Table 6-8')
 tables={}
 for tno in (6,7):
  pi=pages[tno]
  rec={}
  for line in texts[pi].splitlines():
   m=re.match(r'(16/04|01/05|16/05|01/06|16/06|01/07|16/07|01/08|16/08|01/09|16/09|01/10|16/10|01/11|16/11|01/12|16/12|01/01|16/01|01/02|16/02|01/03|16/03|01/04)\s+(.+)',line)
   if m:
    nums=re.findall(r'-?\d[\d.,]*',m.group(2))
    if len(nums)>=9:
     v=[pnum(x) for x in nums[:9]]; rec[pk(m.group(1))]={'sp':v[1],'sc':v[4],'other':v[7]}
  tables[tno]=rec
 rec={}
 for line in texts[pages[8]].splitlines():
  m=re.match(r'(16/04|01/05|16/05|01/06|16/06|01/07|16/07|01/08|16/08|01/09|16/09|01/10|16/10|01/11|16/11|01/12|16/12|01/01|16/01|01/02|16/02|01/03|16/03|01/04)\s+(.+)',line)
  if m:
   nums=re.findall(r'\d[\d.,]*',m.group(2))
   if len(nums)>=6:
    v=[pnum(x) for x in nums[:6]]; rec[pk(m.group(1))]=dict(zip(['anh_bi','hyd_bi','total_bi','anh_acc','hyd_acc','total_acc'],v))
 tables[8]=rec
 pos=re.search(r'Posição até\s*(\d{2}/\d{2}/\d{4})',texts[0],re.I)
 if pos: position=pos.group(1)
 else:
  pos=re.search(r'Position until\s*(\d{2})/(\d{2})/(\d{4})',texts[0],re.I)
  position=f'{pos.group(2)}/{pos.group(1)}/{pos.group(3)}' if pos else None
 sm=re.search(r'(?:HARVEST|SAFRA)\s+(\d{4}/\d{4})',texts[0],re.I)
 return tables,position,(sm.group(1) if sm else None)
def upsert(m,season,vals): m['rows']=[r for r in m['rows'] if not(r['season']==season and r['period'] in vals)]+[{'period':p,'season':season,'value':v} for p,v in vals.items()]
def calc(m,season,vals): upsert(m,season,vals)
def enrich(metrics):
 for m in metrics:
  for r in m['rows']:
   for k in ['percentile','detrended_percentile','trend_applied','yoy_pct']: r.pop(k,None)
  by={}
  for r in m['rows']: by.setdefault(r['period'],[]).append(r)
  for rs in by.values():
   vals=[r['value'] for r in rs]; years=[int(r['season'][:4]) for r in rs]
   for r in rs:
    r['percentile']=sum(v<=r['value'] for v in vals)/len(vals); prev=next((x for x in rs if int(x['season'][:4])==int(r['season'][:4])-1),None); r['yoy_pct']=r['value']/prev['value']-1 if prev and prev['value'] else None
   apply=False; residuals=vals
   if len(rs)>=4:
    xm=statistics.mean(years); ym=statistics.mean(vals); den=sum((x-xm)**2 for x in years); slope=sum((x-xm)*(y-ym) for x,y in zip(years,vals))/den if den else 0; pred=[ym+slope*(x-xm) for x in years]; ss=sum((y-ym)**2 for y in vals); r2=1-sum((y-z)**2 for y,z in zip(vals,pred))/ss if ss else 0; apply=r2>=.35 and abs(slope*(max(years)-min(years)))/(abs(ym) or 1)>=.10; residuals=[y-z for y,z in zip(vals,pred)]
   for r,e in zip(rs,residuals): r['detrended_percentile']=sum(v<=e for v in residuals)/len(residuals) if apply else r['percentile']; r['trend_applied']=apply
def main():
 html=fetch(PAGE).decode('utf-8','ignore'); ids=re.findall(r'download_media\.php\?idM=(\d+)',html)
 if not ids: raise RuntimeError('未在UNICA页面找到下载链接')
 url='https://unicadata.com.br/download_media.php?idM='+ids[-1]; raw=fetch(url); sha=hashlib.sha256(raw).hexdigest(); old=json.loads(STATE.read_text('utf-8')) if STATE.exists() else {}
 if old.get('sha256')==sha: print('no change',url); return
 
 with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
  tmp.write(raw); pdf_path=tmp.name
 tables,pos,season=extract(pdf_path); d=json.loads(DB.read_text('utf-8')); ms={(m['region'],m['component'],m['kind']):m for m in d['metrics']}; season=season or d['meta'].get('season','2026/2027')
 for t,comp in [(6,'Anhydrous'),(7,'Hydrous')]:
  for region,key in [('São Paulo','sp'),('South-Central','sc'),('Other States','other')]: upsert(ms[(region,comp,'Accumulated')],season,{p:v[key] for p,v in tables[t].items()})
 for comp,k1,k2 in [('Corn Anhydrous','anh_bi','anh_acc'),('Corn Hydrous','hyd_bi','hyd_acc'),('Corn Total','total_bi','total_acc')]: upsert(ms[('South-Central',comp,'Biweekly')],season,{p:v[k1] for p,v in tables[8].items()}); upsert(ms[('South-Central',comp,'Accumulated')],season,{p:v[k2] for p,v in tables[8].items()})
 order=['04-16','05-01','05-16','06-01','06-16','07-01','07-16','08-01','08-16','09-01','09-16','10-01','10-16','11-01','11-16','12-01','12-16','01-01','01-16','02-01','02-16','03-01','03-16','04-01']
 for region in ['São Paulo','South-Central','Other States']:
  for comp in ['Anhydrous','Hydrous','Total']:
   if comp=='Total':
    a={r['period']:r['value'] for r in ms[(region,'Anhydrous','Accumulated')]['rows'] if r['season']==season}; b={r['period']:r['value'] for r in ms[(region,'Hydrous','Accumulated')]['rows'] if r['season']==season}; upsert(ms[(region,'Total','Accumulated')],season,{p:a[p]+b[p] for p in a.keys()&b.keys()})
   acc={r['period']:r['value'] for r in ms[(region,comp,'Accumulated')]['rows'] if r['season']==season}; prev=0; vals={}
   for p in order:
    if p in acc: vals[p]=acc[p]-prev; prev=acc[p]
   upsert(ms[(region,comp,'Biweekly')],season,vals)
 for kind in ['Biweekly','Accumulated']:
  for comp in ['Anhydrous','Hydrous','Total']:
   a={r['period']:r['value'] for r in ms[('South-Central',comp,kind)]['rows'] if r['season']==season}; b={r['period']:r['value'] for r in ms[('South-Central','Corn '+comp,kind)]['rows'] if r['season']==season}; upsert(ms[('South-Central','Cane '+comp,kind)],season,{p:a[p]-b[p] for p in a.keys()&b.keys()})
 enrich(d['metrics'])
 for m in d['metrics']:
  rz={'South-Central':'中南部','São Paulo':'圣保罗','Other States':'其他州'}.get(m.get('region'),m.get('region'))
  cz={'Anhydrous':'无水乙醇','Hydrous':'含水乙醇','Total':'乙醇合计','Corn Anhydrous':'玉米无水乙醇','Corn Hydrous':'玉米含水乙醇','Corn Total':'玉米乙醇合计','Cane Anhydrous':'甘蔗无水乙醇','Cane Hydrous':'甘蔗含水乙醇','Cane Total':'甘蔗乙醇合计'}.get(m.get('component'),m.get('component'))
  kz={'Biweekly':'双周','Accumulated':'累计'}.get(m.get('kind'),m.get('kind'))
  m['region_zh']=rz; m['component_zh']=cz; m['kind_zh']=kz; m['display_name']=f'{rz} {cz}{kz}产量'; m['name']=m['display_name']
 d['period_order']=order; d['season_order']=sorted({r['season'] for mm in d['metrics'] for r in mm['rows']})
 d['meta'].update({'scope_zh':'UNICA 中南部（South-Central）','frequency_zh':'双周，榨季口径','source_name':'UNICA Observatório da Cana / UNICAData','position_date':pos,'download_url':url,'generated_at':datetime.now().astimezone().isoformat()})
 DB.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
 subprocess.check_call([sys.executable, str(ROOT/'scripts'/'unica'/'validate_data.py')])
 STATE.write_text(json.dumps({'sha256':sha,'url':url,'updated_at':d['meta']['generated_at']},ensure_ascii=False,indent=2),encoding='utf-8')
 print('updated',pos,url)
if __name__=='__main__': main()
