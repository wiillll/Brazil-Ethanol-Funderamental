import subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
for rel in ['unica/index.html','unica/styles.css','unica/app.js','assets/plotly-2.35.2.min.js','data/unica-dashboard.json']:
    p=ROOT/rel
    if not p.exists(): raise SystemExit('missing '+rel)
subprocess.check_call([sys.executable, str(ROOT/'scripts'/'unica'/'validate_data.py')])
print('UNICA static bundle ready:', ROOT)
