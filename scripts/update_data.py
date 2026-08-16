import csv, io, json, urllib.request, zipfile
from collections import defaultdict
from datetime import datetime, timezone

MONTHS={'JAN':1,'FEV':2,'MAR':3,'ABR':4,'MAI':5,'JUN':6,'JUL':7,'AGO':8,'SET':9,'OUT':10,'NOV':11,'DEZ':12}
BASE='https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/arquivos'
URLS={
'production':f'{BASE}/arquivos-producao-de-biocombustiveis/producao-etanol-anidro-hidratado-m3-2012-2026.csv/@@download/file',
'sales':f'{BASE}/vdpb/vendas-derivados-petroleo-e-etanol/vendas-combustiveis-m3-1990-2025.csv/@@download/file',
'trade':f'{BASE}/ie/etanol/importacoes-exportacoes-etanol-2012-2025.csv/@@download/file',
'prices':f'{BASE}/shpc/dsas/ca/ca-2026-01.zip'}

def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
    return urllib.request.urlopen(req,timeout=90).read()

def rows(url):
    text=get(url).decode('utf-8-sig')
    return list(csv.DictReader(io.StringIO(text),delimiter=';'))

def num(v):
    if v is None:return 0.0
    return float(str(v).strip().replace('.','').replace(',','.'))

def key(y,m): return f'{int(y):04d}-{MONTHS[m.upper()]:02d}'

def pick(row, words):
    for k,v in row.items():
        n=k.upper().replace('Ç','C').replace('Ã','A').replace('É','E').replace('Ê','E').replace('Ó','O').replace('Í','I')
        if all(w in n for w in words): return v
    return None

prod=defaultdict(lambda:{'anhydrous_m3':0,'hydrous_m3':0,'states':defaultdict(float)})
for r in rows(URLS['production']):
    if int(r['ANO'])<2025: continue
    k=key(r['ANO'],r['MÊS']); p=r['PRODUTO'].upper(); v=num(list(r.values())[-1])
    if 'ANIDRO' in p: prod[k]['anhydrous_m3']+=v
    if 'HIDRATADO' in p: prod[k]['hydrous_m3']+=v
    prod[k]['states'][r['UNIDADE DA FEDERAÇÃO']]+=v

sales=defaultdict(lambda:{'hydrous_m3':0,'gasoline_c_m3':0})
for r in rows(URLS['sales']):
    if int(r['ANO'])<2025: continue
    p=r['PRODUTO'].upper()
    if p not in ('ETANOL HIDRATADO','GASOLINA C'): continue
    k=key(r['ANO'],r['MÊS']); v=num(r['VENDAS'])
    if p=='ETANOL HIDRATADO': sales[k]['hydrous_m3']+=v
    else: sales[k]['gasoline_c_m3']+=v

trade=defaultdict(lambda:{'imports_m3':0,'exports_m3':0})
for r in rows(URLS['trade']):
    if int(r['ANO'])<2025: continue
    k=key(r['ANO'],r['MÊS']); v=num(r['IMPORTADO / EXPORTADO']); op=r['OPERAÇÃO COMERCIAL'].upper()
    if 'IMPORT' in op: trade[k]['imports_m3']+=v
    if 'EXPORT' in op: trade[k]['exports_m3']+=v

prices=[]
try:
    z=zipfile.ZipFile(io.BytesIO(get(URLS['prices'])))
    for name in z.namelist():
        if not name.lower().endswith(('.csv','.txt')): continue
        raw=z.read(name)
        for enc in ('utf-8-sig','latin1'):
            try: text=raw.decode(enc); break
            except UnicodeDecodeError: pass
        sample=text[:4000]; delim=';' if sample.count(';')>sample.count(',') else ','
        rr=list(csv.DictReader(io.StringIO(text),delimiter=delim))
        grouped=defaultdict(dict)
        for r in rr:
            product=pick(r,['PRODUTO']); price=pick(r,['PRECO','MEDIO','REVENDA']) or pick(r,['PREÇO','MÉDIO','REVENDA']); month=pick(r,['MES']) or pick(r,['MÊS'])
            if not product or not price: continue
            p=product.upper(); m=str(month or '').upper()[:3]
            if m not in MONTHS: continue
            if 'ETANOL' in p: grouped[m]['ethanol']=num(price)
            if 'GASOLINA' in p: grouped[m]['gasoline']=num(price)
        for m,d in grouped.items():
            if d.get('ethanol') and d.get('gasoline'): prices.append({'month':f'2026-{MONTHS[m]:02d}','ethanol_brl_l':d['ethanol'],'gasoline_brl_l':d['gasoline'],'parity':d['ethanol']/d['gasoline']})
        if prices: break
except Exception:
    prices=[]

months=sorted(set(prod)|set(sales)|set(trade))
out=[]
for m in months:
    p=prod[m]; s=sales[m]; t=trade[m]
    out.append({'month':m,'anhydrous_m3':round(p['anhydrous_m3'],3),'hydrous_production_m3':round(p['hydrous_m3'],3),'total_production_m3':round(p['anhydrous_m3']+p['hydrous_m3'],3),'hydrous_sales_m3':round(s['hydrous_m3'],3),'gasoline_c_sales_m3':round(s['gasoline_c_m3'],3),'imports_m3':round(t['imports_m3'],3),'exports_m3':round(t['exports_m3'],3),'net_exports_m3':round(t['exports_m3']-t['imports_m3'],3)})

latest=max(prod) if prod else None
state_rank=[]
if latest:
    total=sum(prod[latest]['states'].values()) or 1
    for st,v in sorted(prod[latest]['states'].items(),key=lambda x:x[1],reverse=True):
        state_rank.append({'state':st,'production_m3':round(v,3),'share':v/total})

data={'generated_at':datetime.now(timezone.utc).isoformat(),'latest_production_month':latest,'monthly':out,'prices':sorted(prices,key=lambda x:x['month']),'latest_state_production':state_rank,'corn_ethanol_share_2025':0.25,'sources':URLS}
open('data/dashboard.json','w',encoding='utf-8').write(json.dumps(data,ensure_ascii=False,indent=2))
