import json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data'/'unica-dashboard.json'
ORDER=['04-16','05-01','05-16','06-01','06-16','07-01','07-16','08-01','08-16','09-01','09-16','10-01','10-16','11-01','11-16','12-01','12-16','01-01','01-16','02-01','02-16','03-01','03-16','04-01']
TOL=1e-6
def fail(x): raise AssertionError(x)
def rows(m): return {(r['season'],r['period']):r['value'] for r in m['rows']}
def close(a,b,msg):
    if abs(a-b)>TOL: fail(f'{msg}: {a} != {b}')
def main():
    d=json.loads(DATA.read_text(encoding='utf-8'))
    if len(d.get('metrics',[]))!=30: fail(f"expected 30 metrics, got {len(d.get('metrics',[]))}")
    if d.get('period_order')!=ORDER: fail('bad period_order')
    seen=set(); periods=set()
    for m in d['metrics']:
        if m.get('region')=='South-Central' and '中南部' not in m.get('display_name',''): fail('South-Central visible label missing 中南部: '+m['id'])
        for r in m['rows']:
            k=(m['id'],r['season'],r['period'])
            if k in seen: fail('duplicate '+repr(k))
            seen.add(k); periods.add(r['period'])
            for f in ['percentile','detrended_percentile']:
                v=r.get(f)
                if v is not None and not 0<=v<=1: fail(f'{f} out of range {k}')
    if periods!=set(ORDER): fail('period set mismatch')
    ms={(m['region'],m['component'],m['kind']):m for m in d['metrics']}
    for region in ['South-Central','São Paulo','Other States']:
      for kind in ['Biweekly','Accumulated']:
        a,h,t=rows(ms[(region,'Anhydrous',kind)]),rows(ms[(region,'Hydrous',kind)]),rows(ms[(region,'Total',kind)])
        for k,v in t.items():
          if k in a and k in h: close(a[k]+h[k],v,f'{region} total split {kind} {k}')
    for kind in ['Biweekly','Accumulated']:
      total,corn,cane=rows(ms[('South-Central','Total',kind)]),rows(ms[('South-Central','Corn Total',kind)]),rows(ms[('South-Central','Cane Total',kind)])
      for k,v in total.items():
        if k in corn and k in cane: close(corn[k]+cane[k],v,f'SC corn+cane {kind} {k}')
    combined='\n'.join(p.read_text(encoding='utf-8',errors='ignore') for p in list((ROOT/'unica').glob('*'))+[ROOT/'scripts'/'unica'/'update_live.py'] if p.is_file())
    for bad in ['/api/refresh','/api/export_pdf','C:\\Users\\lenovo']:
        if bad in combined: fail('forbidden string: '+bad)
    if re.search(r'巴西(无水|含水|玉米|甘蔗)?乙醇(双周|累计)?产量',combined): fail('UNICA visible title may still call South-Central Brazil')
    print(f'OK: {len(d["metrics"])} metrics, {len(seen)} rows, {len(d.get("season_order",[]))} seasons, {len(ORDER)} periods')
if __name__=='__main__':
    try: main()
    except Exception as e: print('VALIDATION FAILED:',e,file=sys.stderr); sys.exit(1)

