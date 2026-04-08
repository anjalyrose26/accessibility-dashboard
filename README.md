# Accessibility Checker Dashboard — WebYes

Chrome Web Store analytics dashboard tracking keyword rankings and install stats for the [WebYes Accessibility Checker](https://chromewebstore.google.com/detail/accessibility-checker-by/nidjdackonjofdcclfbdcapbkgghcdjf) and its competitors.

**Live dashboard:** `https://<your-org>.github.io/<this-repo>/`

---

## What it tracks

- **Installs / uninstalls** — manually entered from the CWS Developer Dashboard
- **Keyword rankings** — daily scraped positions for 15 keywords across 7 extensions
- **Competitors:** Silktide, Siteimprove, Accessible Web Helper, BrowserStack, Axe DevTools, WAVE

---

## Daily workflow

### 1. Rankings (automatic)
GitHub Actions runs `scripts/scrape_rankings.py` every day at **3:30 AM UTC**, commits the result to `data/rankings/YYYY-MM-DD.json`, and updates `data/rankings/index.json`. No manual steps needed.

You can also trigger it manually: **GitHub → Actions → Daily Rankings Scrape → Run workflow**.

### 2. Install data (manual — ~1 min)
Check your [CWS Developer Dashboard](https://chrome.google.com/webstore/developer/dashboard), then run:

```bash
python scripts/add_installs.py
```

Follow the prompts, then commit and push:

```bash
git add data/installs.json
git commit -m "chore: installs update $(date +%Y-%m-%d)"
git push
```

---

## First-time setup

### 1. Clone & enable GitHub Pages

1. Push this repo to GitHub (public).
2. Go to **Settings → Pages → Source → Deploy from a branch → `main` / `(root)`**.
3. Your dashboard will be live at `https://<org>.github.io/<repo>/`.

### 2. Local scraping (optional)

```bash
pip install -r requirements.txt
playwright install chromium
python scripts/scrape_rankings.py
```

### 3. First install entry

```bash
python scripts/add_installs.py
```

---

## File structure

```
├── index.html                  # Dashboard (served by GitHub Pages)
├── app.js                      # Dashboard logic + Chart.js
├── styles.css                  # Styling
├── data/
│   ├── installs.json           # Manual install history
│   └── rankings/
│       ├── index.json          # List of all dated ranking files
│       └── YYYY-MM-DD.json     # Daily ranking snapshots
├── scripts/
│   ├── scrape_rankings.py      # Playwright-based CWS scraper
│   └── add_installs.py        # CLI for manual install entry
├── .github/workflows/
│   └── daily.yml              # GitHub Actions — daily scrape + commit
└── requirements.txt
```

---

## Keywords tracked

| # | Keyword |
|---|---------|
| 1 | accessibility checker |
| 2 | web accessibility checker |
| 3 | WCAG checker |
| 4 | accessibility audit |
| 5 | ADA compliance checker |
| 6 | color contrast checker |
| 7 | accessibility testing |
| 8 | screen reader test |
| 9 | accessibility validator |
| 10 | ARIA checker |
| 11 | web accessibility tool |
| 12 | WCAG compliance checker |
| 13 | accessibility analyzer |
| 14 | accessibility extension |
| 15 | disability checker |

---

## Adding or removing keywords

Edit the `KEYWORDS` list in `scripts/scrape_rankings.py`. The dashboard will automatically pick up any keyword that appears in the ranking data files.
