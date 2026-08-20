import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('validate_data', ROOT/'scripts'/'unica'/'validate_data.py')
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
def test_unica_dataset_contract():
    mod.main()
def test_unica_frontend_contract():
    html=(ROOT/'unica'/'index.html').read_text(encoding='utf-8')
    js=(ROOT/'unica'/'app.js').read_text(encoding='utf-8')
    assert '../data/unica-dashboard.json' in js
    assert '/api/refresh' not in html+js
    assert '/api/export_pdf' not in html+js
    assert 'UNICA 中南部' in html
    assert '中南部乙醇总量' in js
    assert js.count('value=concise') == 1
    assert js.count('value=seasonal') == 1
    assert js.count('value=timeline') == 1
    assert js.count('south_central_') >= 18
