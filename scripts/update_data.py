import csv
import io
import json
import urllib.request
import zipfile
from collections import defaultdict
from datetime import datetime, timezone

MONTHS = {
    'JAN': 1, 'JANEIRO': 1,
    'FEV': 2, 'FEVEREIRO': 2,
    'MAR': 3, 'MARÇO': 3, 'MARCO': 3,
    'ABR': 4, 'ABRIL': 4,
    'MAI': 5, 'MAIO': 5,
    'JUN': 6, 'JUNHO': 6,
    'JUL': 7, 'JULHO': 7,
    'AGO': 8, 'AGOSTO': 8,
    'SET': 9, 'SETEMBRO': 9,
    'OUT': 10, 'OUTUBRO': 10,
    'NOV': 11, 'NOVEMBRO': 11,
    'DEZ': 12, 'DEZEMBRO': 12,
}
BASE = 'https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/arquivos'
URLS = {
    'production': f'{BASE}/arquivos-producao-de-biocombustiveis/producao-etanol-anidro-hidratado-m3-2012-2026.csv/@@download/file',
    'sales': f'{BASE}/vdpb/vendas-derivados-petroleo-e-etanol/vendas-combustiveis-m3-1990-2025.csv/@@download/file',
    'trade': f'{BASE}/ie/etanol/importacoes-exportacoes-etanol-2012-2025.csv/@@download/file',
    'prices_pattern': f'{BASE}/shpc/dsas/ca/ca-{{year}}-{{semester:02d}}.zip',
    'unem_sector': 'https://etanoldemilho.com.br/dados-setoriais/',
}

# UNEM Dados Setoriais, page extracted/checked 2026-08-17.
UNEM_IMAGES = {
    'refineries': 'https://etanoldemilho.com.br/wp-content/uploads/2026/06/WhatsApp-Image-2026-06-02-at-10.38.23.jpeg',
    'corn_area': 'https://etanoldemilho.com.br/wp-content/uploads/2025/09/2.jpg',
    'corn_grinding': 'https://etanoldemilho.com.br/wp-content/uploads/2025/09/3.jpg',
    'ethanol_output': 'https://etanoldemilho.com.br/wp-content/uploads/2025/09/4.jpg',
    'ddg_output': 'https://etanoldemilho.com.br/wp-content/uploads/2025/09/5.jpg',
}
UNEM_REFINERIES = {
    'updated_from': URLS['unem_sector'],
    'as_of': '2026-08-17',
    'operation': {'total': 29, 'states': {'Mato Grosso': 14, 'Goiás': 5, 'Mato Grosso do Sul': 3, 'Pará': 1, 'Bahia': 1, 'Paraná': 1, 'Alagoas': 1, 'São Paulo': 1, 'Maranhão': 1, 'Rio Grande do Sul': 1}},
    'authorized_construction': {'total': 13, 'states': {'Mato Grosso': 4, 'Rio Grande do Sul': 1, 'Tocantins': 1, 'Piauí': 1, 'Bahia': 1, 'Paraná': 2, 'São Paulo': 1, 'Goiás': 2}},
    'projected': {'total': 14, 'states': {'Mato Grosso': 6, 'Bahia': 2, 'São Paulo': 1, 'Goiás': 3, 'Rondônia': 1, 'Paraná': 1}},
}
UNEM_ETHANOL = [
    {'crop_year': '2013/14', 'hydrous_million_m3': 0.03, 'anhydrous_million_m3': 0.00, 'total_million_m3': 0.03},
    {'crop_year': '2014/15', 'hydrous_million_m3': 0.08, 'anhydrous_million_m3': 0.00, 'total_million_m3': 0.08},
    {'crop_year': '2015/16', 'hydrous_million_m3': 0.14, 'anhydrous_million_m3': 0.00, 'total_million_m3': 0.14},
    {'crop_year': '2016/17', 'hydrous_million_m3': 0.20, 'anhydrous_million_m3': 0.04, 'total_million_m3': 0.23},
    {'crop_year': '2017/18', 'hydrous_million_m3': 0.43, 'anhydrous_million_m3': 0.09, 'total_million_m3': 0.52},
    {'crop_year': '2018/19', 'hydrous_million_m3': 0.56, 'anhydrous_million_m3': 0.23, 'total_million_m3': 0.79},
    {'crop_year': '2019/20', 'hydrous_million_m3': 1.21, 'anhydrous_million_m3': 0.42, 'total_million_m3': 1.63},
    {'crop_year': '2020/21', 'hydrous_million_m3': 1.92, 'anhydrous_million_m3': 0.73, 'total_million_m3': 2.65},
    {'crop_year': '2021/22', 'hydrous_million_m3': 2.41, 'anhydrous_million_m3': 1.02, 'total_million_m3': 3.43},
    {'crop_year': '2022/23', 'hydrous_million_m3': 2.64, 'anhydrous_million_m3': 1.76, 'total_million_m3': 4.40},
    {'crop_year': '2023/24', 'hydrous_million_m3': 3.90, 'anhydrous_million_m3': 2.40, 'total_million_m3': 6.30},
    {'crop_year': '2024/25', 'hydrous_million_m3': 4.79, 'anhydrous_million_m3': 3.21, 'total_million_m3': 8.24},
    {'crop_year': '2025/26*', 'hydrous_million_m3': 6.31, 'anhydrous_million_m3': 3.66, 'total_million_m3': 9.97},
    {'crop_year': '2033/34 projection', 'hydrous_million_m3': None, 'anhydrous_million_m3': None, 'total_million_m3': 16.63},
]
UNEM_CORN_GRINDING = [
    {'crop_year': '2013/14', 'mato_grosso_mt': 0.03, 'mato_grosso_do_sul_mt': 0, 'goias_mt': 0, 'others_mt': 0},
    {'crop_year': '2014/15', 'mato_grosso_mt': 0.23, 'mato_grosso_do_sul_mt': 0, 'goias_mt': 0, 'others_mt': 0},
    {'crop_year': '2015/16', 'mato_grosso_mt': 0.31, 'mato_grosso_do_sul_mt': 0, 'goias_mt': 0, 'others_mt': 0},
    {'crop_year': '2016/17', 'mato_grosso_mt': 0.43, 'mato_grosso_do_sul_mt': 0.20, 'goias_mt': 0, 'others_mt': 0},
    {'crop_year': '2017/18', 'mato_grosso_mt': 0.94, 'mato_grosso_do_sul_mt': 0.32, 'goias_mt': 0, 'others_mt': 0},
    {'crop_year': '2018/19', 'mato_grosso_mt': 1.47, 'mato_grosso_do_sul_mt': 0.48, 'goias_mt': 0.02, 'others_mt': 0},
    {'crop_year': '2019/20', 'mato_grosso_mt': 2.95, 'mato_grosso_do_sul_mt': 0.89, 'goias_mt': 0.12, 'others_mt': 0},
    {'crop_year': '2020/21', 'mato_grosso_mt': 4.93, 'mato_grosso_do_sul_mt': 0.99, 'goias_mt': 0.05, 'others_mt': 0},
    {'crop_year': '2021/22', 'mato_grosso_mt': 6.85, 'mato_grosso_do_sul_mt': 0.91, 'goias_mt': 0.07, 'others_mt': 0},
    {'crop_year': '2022/23', 'mato_grosso_mt': 7.33, 'mato_grosso_do_sul_mt': 1.61, 'goias_mt': 0.89, 'others_mt': 0.06},
    {'crop_year': '2023/24', 'mato_grosso_mt': 10.11, 'mato_grosso_do_sul_mt': 2.21, 'goias_mt': 1.66, 'others_mt': 0.08},
    {'crop_year': '2024/25', 'mato_grosso_mt': 12.50, 'mato_grosso_do_sul_mt': 3.51, 'goias_mt': 2.07, 'others_mt': 0.30},
    {'crop_year': '2025/26*', 'mato_grosso_mt': 13.52, 'mato_grosso_do_sul_mt': 4.75, 'goias_mt': 2.11, 'others_mt': 1.82},
]
UNEM_DDG = [
    {'crop_year': '2017/18', 'mato_grosso_mt': 0.28, 'mato_grosso_do_sul_mt': 0, 'goias_mt': 0, 'others_mt': 0},
    {'crop_year': '2018/19', 'mato_grosso_mt': 0.44, 'mato_grosso_do_sul_mt': 0, 'goias_mt': 0.09, 'others_mt': 0},
    {'crop_year': '2019/20', 'mato_grosso_mt': 1.00, 'mato_grosso_do_sul_mt': 0, 'goias_mt': 0.18, 'others_mt': 0},
    {'crop_year': '2020/21', 'mato_grosso_mt': 1.11, 'mato_grosso_do_sul_mt': 0, 'goias_mt': 0.22, 'others_mt': 0},
    {'crop_year': '2021/22', 'mato_grosso_mt': 1.51, 'mato_grosso_do_sul_mt': 0, 'goias_mt': 0.24, 'others_mt': 0},
    {'crop_year': '2022/23', 'mato_grosso_mt': 1.60, 'mato_grosso_do_sul_mt': 0.37, 'goias_mt': 0.23, 'others_mt': 0.10},
    {'crop_year': '2023/24', 'mato_grosso_mt': 2.12, 'mato_grosso_do_sul_mt': 0.51, 'goias_mt': 0.47, 'others_mt': 0.01},
    {'crop_year': '2024/25', 'mato_grosso_mt': 2.72, 'mato_grosso_do_sul_mt': 0.84, 'goias_mt': 0.47, 'others_mt': 0.08},
    {'crop_year': '2025/26*', 'mato_grosso_mt': 2.90, 'mato_grosso_do_sul_mt': 1.03, 'goias_mt': 0.50, 'others_mt': 0.40},
]


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    return urllib.request.urlopen(req, timeout=120).read()


def rows(url):
    raw = get(url)
    for enc in ('utf-8-sig', 'latin1'):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode('utf-8', 'ignore')
    return list(csv.DictReader(io.StringIO(text), delimiter=';'))


def normalize_text(v):
    return str(v or '').strip().upper().replace('Ç', 'C').replace('Ã', 'A').replace('Á', 'A').replace('Â', 'A').replace('É', 'E').replace('Ê', 'E').replace('Ó', 'O').replace('Ô', 'O').replace('Í', 'I').replace('Ú', 'U')


def num(v):
    if v is None:
        return 0.0
    s = str(v).strip().replace('\ufeff', '')
    if not s:
        return 0.0
    # Brazilian CSVs mostly use 1.234,56. If both separators exist, remove thousand dots.
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return 0.0


def month_num(m):
    key = normalize_text(m)
    if key in MONTHS:
        return MONTHS[key]
    key3 = key[:3]
    if key3 in MONTHS:
        return MONTHS[key3]
    return None


def key(y, m):
    mm = month_num(m)
    if not mm:
        raise ValueError(f'Unknown month: {m}')
    return f'{int(y):04d}-{mm:02d}'


def first_matching_column(row, words):
    words = [normalize_text(w) for w in words]
    for k, v in row.items():
        nk = normalize_text(k)
        if all(w in nk for w in words):
            return v
    return None


def parse_prices(start_year, end_year, diagnostics):
    sums = defaultdict(lambda: {'ethanol_sum': 0.0, 'ethanol_n': 0, 'gasoline_sum': 0.0, 'gasoline_n': 0})
    for year in range(start_year, end_year + 1):
        for semester in (1, 2):
            url = URLS['prices_pattern'].format(year=year, semester=semester)
            try:
                raw_zip = get(url)
            except Exception as exc:
                diagnostics['price_files_skipped'].append({'url': url, 'reason': type(exc).__name__})
                continue
            try:
                zf = zipfile.ZipFile(io.BytesIO(raw_zip))
                names = [n for n in zf.namelist() if n.lower().endswith(('.csv', '.txt'))]
                for name in names:
                    raw = zf.read(name)
                    text = None
                    for enc in ('utf-8-sig', 'latin1'):
                        try:
                            text = raw.decode(enc)
                            break
                        except UnicodeDecodeError:
                            pass
                    if text is None:
                        text = raw.decode('utf-8', 'ignore')
                    sample = text[:4000]
                    delim = ';' if sample.count(';') >= sample.count(',') else ','
                    for row in csv.DictReader(io.StringIO(text), delimiter=delim):
                        product = normalize_text(first_matching_column(row, ['Produto']))
                        if product not in ('ETANOL', 'GASOLINA'):
                            continue
                        date = str(first_matching_column(row, ['Data', 'Coleta']) or '').strip()
                        price = num(first_matching_column(row, ['Valor', 'Venda']))
                        if not date or not price:
                            continue
                        parts = date.replace('-', '/').split('/')
                        if len(parts) < 3:
                            continue
                        if len(parts[0]) == 4:
                            yy, mm = int(parts[0]), int(parts[1])
                        else:
                            yy, mm = int(parts[2]), int(parts[1])
                        mk = f'{yy:04d}-{mm:02d}'
                        if product == 'ETANOL':
                            sums[mk]['ethanol_sum'] += price
                            sums[mk]['ethanol_n'] += 1
                        else:
                            sums[mk]['gasoline_sum'] += price
                            sums[mk]['gasoline_n'] += 1
                diagnostics['price_files_loaded'].append(url)
            except Exception as exc:
                diagnostics['price_files_failed'].append({'url': url, 'reason': repr(exc)})
    out = []
    for mk in sorted(sums):
        g = sums[mk]
        if g['ethanol_n'] and g['gasoline_n']:
            ethanol = g['ethanol_sum'] / g['ethanol_n']
            gasoline = g['gasoline_sum'] / g['gasoline_n']
            out.append({
                'month': mk,
                'ethanol_brl_l': round(ethanol, 3),
                'gasoline_brl_l': round(gasoline, 3),
                'parity': round(ethanol / gasoline, 4),
                'ethanol_observations': g['ethanol_n'],
                'gasoline_observations': g['gasoline_n'],
            })
    return out


def main():
    now = datetime.now(timezone.utc)
    end_year = now.year
    start_year = end_year - 4
    diagnostics = {'history_start_year': start_year, 'price_files_loaded': [], 'price_files_skipped': [], 'price_files_failed': []}

    prod = defaultdict(lambda: {'anhydrous_m3': 0.0, 'hydrous_m3': 0.0, 'states': defaultdict(float)})
    for r in rows(URLS['production']):
        y = int(r['ANO'])
        if y < start_year:
            continue
        k = key(r['ANO'], r['MÊS'])
        product = normalize_text(r.get('PRODUTO'))
        value = num(list(r.values())[-1])
        if 'ANIDRO' in product:
            prod[k]['anhydrous_m3'] += value
        elif 'HIDRATADO' in product:
            prod[k]['hydrous_m3'] += value
        prod[k]['states'][r.get('UNIDADE DA FEDERAÇÃO', 'Unknown')] += value

    sales = defaultdict(lambda: {'hydrous_m3': 0.0, 'gasoline_c_m3': 0.0})
    for r in rows(URLS['sales']):
        y = int(r['ANO'])
        if y < start_year:
            continue
        product = normalize_text(r.get('PRODUTO'))
        if product not in ('ETANOL HIDRATADO', 'GASOLINA C'):
            continue
        k = key(r['ANO'], r['MÊS'])
        value = num(r.get('VENDAS'))
        if product == 'ETANOL HIDRATADO':
            sales[k]['hydrous_m3'] += value
        else:
            sales[k]['gasoline_c_m3'] += value

    trade = defaultdict(lambda: {'imports_m3': 0.0, 'exports_m3': 0.0})
    for r in rows(URLS['trade']):
        y = int(r['ANO'])
        if y < start_year:
            continue
        k = key(r['ANO'], r['MÊS'])
        value = num(r.get('IMPORTADO / EXPORTADO'))
        op = normalize_text(r.get('OPERAÇÃO COMERCIAL'))
        if 'IMPORT' in op:
            trade[k]['imports_m3'] += value
        elif 'EXPORT' in op:
            trade[k]['exports_m3'] += value

    prices = parse_prices(start_year, end_year, diagnostics)

    months = sorted(set(prod) | set(sales) | set(trade))
    monthly = []
    for m in months:
        p, s, t = prod[m], sales[m], trade[m]
        total = p['anhydrous_m3'] + p['hydrous_m3']
        monthly.append({
            'month': m,
            'anhydrous_m3': round(p['anhydrous_m3'], 3),
            'hydrous_production_m3': round(p['hydrous_m3'], 3),
            'total_production_m3': round(total, 3),
            'hydrous_sales_m3': round(s['hydrous_m3'], 3),
            'gasoline_c_sales_m3': round(s['gasoline_c_m3'], 3),
            'imports_m3': round(t['imports_m3'], 3),
            'exports_m3': round(t['exports_m3'], 3),
            'net_exports_m3': round(t['exports_m3'] - t['imports_m3'], 3),
        })

    production_months = [m for m, v in prod.items() if v['anhydrous_m3'] + v['hydrous_m3'] > 0]
    latest = max(production_months) if production_months else None
    state_rank = []
    if latest:
        total = sum(prod[latest]['states'].values()) or 1
        for st, value in sorted(prod[latest]['states'].items(), key=lambda x: x[1], reverse=True):
            if value <= 0:
                continue
            state_rank.append({'state': st, 'production_m3': round(value, 3), 'share': round(value / total, 6)})

    corn = {
        'source': 'UNEM Dados Setoriais / Imea / Conab',
        'source_url': URLS['unem_sector'],
        'images': UNEM_IMAGES,
        'refineries': UNEM_REFINERIES,
        'ethanol_production': UNEM_ETHANOL,
        'corn_grinding': [dict(x, total_mt=round(x['mato_grosso_mt'] + x['mato_grosso_do_sul_mt'] + x['goias_mt'] + x['others_mt'], 2)) for x in UNEM_CORN_GRINDING],
        'ddg_ddgs_production': [dict(x, total_mt=round(x['mato_grosso_mt'] + x['mato_grosso_do_sul_mt'] + x['goias_mt'] + x['others_mt'], 2)) for x in UNEM_DDG],
        'notes': [
            '2025/26 values are estimates shown by UNEM/Imea as of the source page.',
            '2033/34 is a production projection and is not split into hydrous/anhydrous in the source image.',
            'UNEM crop-year structural data should be kept separate from ANP monthly operational statistics.'
        ]
    }

    data = {
        'generated_at': now.isoformat(),
        'history_start_year': start_year,
        'latest_production_month': latest,
        'monthly': monthly,
        'prices': prices,
        'latest_state_production': state_rank,
        'corn_ethanol_share_2025': 0.25,
        'corn_ethanol': corn,
        'diagnostics': diagnostics,
        'sources': URLS,
    }
    with open('data/dashboard.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
