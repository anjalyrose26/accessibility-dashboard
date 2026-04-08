# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A Chrome Web Store analytics dashboard for the **WebYes Accessibility Checker** extension (`nidjdackonjofdcclfbdcapbkgghcdjf`). It tracks keyword rankings and user counts daily, compares against 6 competitor extensions, and posts a summary to Slack each morning.

## Running scripts locally

```bash
# Install dependencies (once)
pip3 install playwright
/Users/anjalyrose/Library/Python/3.9/bin/playwright install chromium

# Scrape keyword rankings + auto-update user count in data/installs.json
python3 scripts/scrape_rankings.py

# Manually add weekly install/uninstall data from CWS Developer Dashboard
python3 scripts/add_installs.py

# Send Slack notification from local data (requires env var)
SLACK_WEBHOOK_URL=https://hooks.slack.com/... python3 scripts/notify_slack.py

# Serve the dashboard locally (must run from project root)
python3 -m http.server 8765 --directory /path/to/accessibility-dashboard
# then open http://localhost:8765
```

## Data flow

1. `scripts/scrape_rankings.py` runs daily via GitHub Actions (`.github/workflows/daily.yml`)
2. It writes `data/rankings/YYYY-MM-DD.json` and appends the date to `data/rankings/index.json`
3. It also auto-writes `total_installs` into `data/installs.json` by scraping the public user count from the extension page
4. `scripts/notify_slack.py` runs after the scrape and posts to `#accessibility-checker-dashboard` via `SLACK_WEBHOOK_URL` (stored as a GitHub Actions secret)
5. The static dashboard (`index.html` + `app.js`) is served via GitHub Pages and loads all JSON files at runtime via `fetch()`

## Architecture

- **No build step.** The dashboard is plain HTML/JS. Chart.js is loaded from CDN.
- **Data lives in git.** All scraped data is committed to `data/` by the GitHub Actions bot. The dashboard reads it directly via HTTP — this means GitHub Pages serves both the app and its data.
- **`data/rankings/index.json`** is the critical index file. The dashboard fetches it first to know which daily files exist, then fetches each one. If this file is out of sync, rankings won't show.
- **`app.js`** handles all rendering: install stat cards, rankings overview table, WebYes day-over-day/week-over-week change table, and the per-keyword trend chart (Chart.js, y-axis inverted so rank #1 is at top).

## Extension registry

All tracked extensions are defined in two places — keep them in sync if adding/removing:
- `scripts/scrape_rankings.py` → `EXTENSIONS` dict (key → CWS extension ID)
- `app.js` → `EXTENSIONS` object (key → name, color, borderWidth)

## Keywords

The 15 tracked keywords live in `KEYWORDS` list in `scripts/scrape_rankings.py`. Adding a keyword there will automatically appear in the dashboard on the next scrape.

## GitHub Actions

- Runner: `ubuntu-22.04` (intentional — `ubuntu-latest` is 24.04 which breaks Playwright's `--with-deps` due to `libasound2` rename)
- Runs at 3:30 AM UTC daily + supports manual `workflow_dispatch`
- Requires `SLACK_WEBHOOK_URL` secret set in repo settings
- Commits scraped data as `github-actions[bot]`

## Deployment

GitHub Pages is enabled on `main` branch at root (`/`). Live URL: `https://anjalyrose26.github.io/accessibility-dashboard/`
