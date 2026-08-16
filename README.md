# Brazil Fuel Ethanol Monitor

A lightweight research dashboard for tracking the Brazilian fuel-ethanol complex and its implications for **corn, sugar and ethanol fundamentals**.

## V1 scope

The first version intentionally stays small and source-backed:

- Brazil ethanol production (ANP)
- Anhydrous production trend / E30 policy signal
- Hydrous ethanol sales signal
- Corn ethanol penetration (EPE)
- Research-oriented supply / demand signal cards
- Explicit reconciliation note where ANP and EPE statistical totals differ

Open `index.html` in a browser to view the dashboard. It is a static HTML prototype using Chart.js from a CDN.

## Research logic

The dashboard follows this chain:

`Ethanol supply -> anhydrous/hydrous mix -> fuel demand -> corn ethanol penetration -> corn/sugar implications`

## Next step (V2)

Connect monthly ANP open-data files and calculate:

- Hydrous vs Gasoline C sales
- Hydrous/Gasoline retail price parity
- Monthly and rolling-12-month ethanol production
- Ethanol imports / exports
- State-level exposure (MT, GO, MS, SP)

See `docs/DATA_SOURCES.md` for source definitions and caveats.
