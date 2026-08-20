# UNICA integration notes

This local bundle prepares the static GitHub Pages integration for `/unica/`.

- UNICA page is South-Central Brazil only; every visible South-Central metric is labeled `中南部`.
- ANP national monthly/calendar data remains on `index.html`.
- `capacity.html` keeps its old URL and belongs under `基本面 · 产能与项目`, not UNICA.
- Raw UNICA PDFs, XLS/XLSX files, logs, local paths and tokens are not included.
- GitHub Pages refresh uses `.github/workflows/update-unica.yml`; the browser page does not call `/api/refresh` or `/api/export_pdf`.

Suggested existing-page nav edits before publishing: add a link to `./unica/index.html` in both `index.html` and `capacity.html`; label the fundamentals page as ANP 全国月度/日历口径.
