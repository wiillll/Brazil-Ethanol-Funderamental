# Data sources and metric definitions

## Source hierarchy

### ANP — operational / regulatory monthly series
The main dashboard uses ANP as the primary source for monthly production, domestic fuel sales, retail fuel prices, imports and exports.

- Production: https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/producao-de-biocombustiveis
- Fuel sales: https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/vendas-de-derivados-de-petroleo-e-biocombustiveis
- Retail prices: https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/serie-historica-de-precos-de-combustiveis
- Ethanol imports/exports: https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/importacoes-e-exportacoes

Dashboard v2.2 keeps the last five calendar years from the available ANP files. As of the 2026-08-17 refresh, the generated file contains monthly data from 2022-01 to the latest ANP production month and price parity from 2022-07 onward. Price parity is calculated as the national simple average retail price of ETANOL divided by GASOLINA from ANP station observations.

Key derived metrics:

1. `ethanol_total = anhydrous + hydrous`
2. `hydrous_gasoline_parity = ethanol_retail_price / gasoline_retail_price`
3. `hydrous_share_otto = hydrous_sales / (hydrous_sales + gasoline_c_sales)`
4. Monthly YoY and rolling-12-month growth for production.
5. Ethanol net exports = exports - imports.

### UNEM / Imea / Conab — structural corn ethanol series
The new `capacity.html` page uses UNEM Dados Setoriais images and manually structured chart values for corn ethanol capacity, production, corn grinding and DDG/DDGS.

- UNEM Dados Setoriais: https://etanoldemilho.com.br/dados-setoriais/

Current UNEM expansion snapshot shown on the source page:

| Category | Count |
|---|---:|
| Biorrefineries in operation | 29 |
| Biorrefineries with ANP construction authorization | 13 |
| Projected / scheduled biorrefineries | 14 |

Selected UNEM structural values:

| Crop year | Corn ethanol production, million m3 | Corn grinding, million tons | DDG/DDGS, million tons |
|---|---:|---:|---:|
| 2023/24 | 6.30 | 14.06 | 3.11 |
| 2024/25 | 8.24 | 18.38 | 4.11 |
| 2025/26E | 9.97 | 22.20 | 4.83 |
| 2033/34 projection | 16.63 | n/a | n/a |

Important: UNEM crop-year structural data and ANP monthly operational data have different boundaries. They should not be merged without reconciling crop year/calendar year, reporting scope and methodology.

## Reconciliation note
ANP, EPE and UNEM/Imea may report different totals because they answer different questions. ANP is used for operational monthly monitoring; EPE is useful for energy-balance feedstock structure; UNEM/Imea/Conab is useful for corn ethanol capacity and crop-year structural expansion. The dashboard deliberately separates these views.
