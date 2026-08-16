# Data sources and metric definitions

## Source hierarchy

### ANP — operational / regulatory series
Use ANP as the primary source for production, domestic fuel sales, prices, imports/exports and anhydrous inventory/contracting data.

- 2025 consolidated sector data: https://www.gov.br/anp/pt-br/canais_atendimento/imprensa/noticias-comunicados/anp-divulga-dados-consolidados-do-setor-regulado-em-2025
- Fuel sales open data: https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/vendas-de-derivados-de-petroleo-e-biocombustiveis
- Ethanol imports/exports: https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/importacoes-e-exportacoes
- Ethanol commercialisation / crop-year inventory: https://www.gov.br/anp/pt-br/assuntos/distribuicao-e-revenda/comercializacao-de-etanol

2025 anchor values used in dashboard v1:
- Ethanol production: 35.9 billion litres, -2.8% YoY.
- Anhydrous ethanol production: +3.1% YoY.
- Hydrous ethanol sales: -5.9% YoY.
- Mandatory anhydrous blend in gasoline C: 27% -> 30% from August 2025.

### EPE — energy balance / structural feedstock series
Use EPE for the structural split of ethanol feedstocks and longer-run energy-balance analysis.

- BEN 2026 summary: https://www.epe.gov.br/pt/imprensa/noticias/epe-publica-o-relatorio-sintese-do-balanco-energetico-nacional-2026
- BEN 2026 book: https://dashboard.epe.gov.br/apps/livro-ben/livro/pt/capitulo_1.html

Corn share in ethanol production used in dashboard v1:

| Year | Anhydrous | Hydrous |
|---|---:|---:|
| 2021 | 13.1% | 7.8% |
| 2022 | 15.1% | 11.4% |
| 2023 | 15.8% | 15.7% |
| 2024 | 19.5% | 20.2% |
| 2025 | 23.7% | 26.6% |

EPE reports roughly 9.4 billion litres of corn ethanol in 2025 and about 25% of total ethanol output.

## Important reconciliation note
ANP reports 35.9 billion litres of ethanol production for 2025, while EPE BEN 2026 reports 38.20 million m3 under its energy-balance methodology. These totals should **not** be merged without reconciling statistical boundaries and definitions. Dashboard v1 deliberately keeps ANP operational totals and EPE feedstock-structure indicators separate.

## Planned v2 derived metrics

1. `ethanol_total = anhydrous + hydrous`
2. `hydrous_gasoline_parity = hydrous_retail_price / gasoline_c_retail_price`
3. `hydrous_share_otto = hydrous_sales / (hydrous_sales + gasoline_c_sales)`
4. `corn_ethanol_share = corn_ethanol / total_ethanol`
5. Monthly YoY and rolling-12-month growth for production and sales.
6. Ethanol net exports.
7. Regional corn-ethanol exposure for MT / GO / MS.
